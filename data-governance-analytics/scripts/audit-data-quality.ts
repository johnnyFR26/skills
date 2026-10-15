#!/usr/bin/env tsx
/**
 * audit-data-quality.ts
 * 
 * Script de auditoria de qualidade de dados para atendimentos.
 * Executa o ciclo VCAT (Validade, Completude, Atualidade, Traçabilidade).
 *
 * Uso: tsx scripts/audit-data-quality.ts [--from YYYY-MM-DD] [--to YYYY-MM-DD]
 *
 * Saída: relatório de qualidade em stdout + exit code 1 se falhas críticas
 */

import { parseArgs } from 'node:util'
import { format, subDays } from 'date-fns'

// --- Tipos ---
interface Attendance {
  id: number
  userId: number
  externalAttendeeId: number | null
  externalCustomerId: number | null
  title: string
  description: string
  controls?: { attendee_name?: string | null }
  createdAt: string
  updatedAt: string
  reasons: Array<{ id: number; name: string; weight?: number }>
}

interface AuditResult {
  total: number
  checks: AuditCheck[]
  criticalFailures: number
  warnings: number
  passed: number
}

interface AuditCheck {
  name: string
  severity: 'critical' | 'warning' | 'info'
  passed: boolean
  affectedCount: number
  percentage: string
  details: string
}

// --- Helpers ---
const pct = (count: number, total: number) =>
  total === 0 ? '0.0' : ((count / total) * 100).toFixed(1)

// --- Checks VCAT ---

function checkValidity(attendances: Attendance[]): AuditCheck[] {
  const checks: AuditCheck[] = []

  // Datas válidas
  const invalidDates = attendances.filter((a) => {
    return isNaN(Date.parse(a.createdAt)) || isNaN(Date.parse(a.updatedAt))
  })
  checks.push({
    name: 'Validade: Datas em formato válido',
    severity: 'critical',
    passed: invalidDates.length === 0,
    affectedCount: invalidDates.length,
    percentage: pct(invalidDates.length, attendances.length),
    details: invalidDates.length > 0
      ? `IDs afetados: ${invalidDates.slice(0, 5).map((a) => a.id).join(', ')}`
      : 'OK',
  })

  // updatedAt >= createdAt
  const invertedDates = attendances.filter((a) => {
    return new Date(a.updatedAt) < new Date(a.createdAt)
  })
  checks.push({
    name: 'Validade: updatedAt >= createdAt',
    severity: 'critical',
    passed: invertedDates.length === 0,
    affectedCount: invertedDates.length,
    percentage: pct(invertedDates.length, attendances.length),
    details: invertedDates.length > 0
      ? `IDs afetados: ${invertedDates.slice(0, 5).map((a) => a.id).join(', ')}`
      : 'OK',
  })

  return checks
}

function checkCompleteness(attendances: Attendance[]): AuditCheck[] {
  const checks: AuditCheck[] = []

  const nullAttendee = attendances.filter((a) => a.externalAttendeeId === null)
  checks.push({
    name: 'Completude: externalAttendeeId não nulo',
    severity: 'warning',
    passed: nullAttendee.length === 0,
    affectedCount: nullAttendee.length,
    percentage: pct(nullAttendee.length, attendances.length),
    details: nullAttendee.length > 0
      ? `${nullAttendee.length} atendimentos sem atendente vinculado`
      : 'OK',
  })

  const noReasons = attendances.filter((a) => a.reasons.length === 0)
  checks.push({
    name: 'Completude: Ao menos 1 motivo por atendimento',
    severity: 'warning',
    passed: noReasons.length === 0,
    affectedCount: noReasons.length,
    percentage: pct(noReasons.length, attendances.length),
    details: noReasons.length > 0
      ? `${noReasons.length} atendimentos sem motivo registrado`
      : 'OK',
  })

  const emptyTitle = attendances.filter((a) => !a.title?.trim())
  checks.push({
    name: 'Completude: Título não vazio',
    severity: 'info',
    passed: emptyTitle.length === 0,
    affectedCount: emptyTitle.length,
    percentage: pct(emptyTitle.length, attendances.length),
    details: emptyTitle.length > 0
      ? `${emptyTitle.length} atendimentos sem título`
      : 'OK',
  })

  return checks
}

function checkCurrency(attendances: Attendance[], from: Date, to: Date): AuditCheck[] {
  const checks: AuditCheck[] = []

  const outOfRange = attendances.filter((a) => {
    const d = new Date(a.createdAt)
    return d < from || d > to
  })
  checks.push({
    name: 'Atualidade: Registros dentro do período solicitado',
    severity: 'critical',
    passed: outOfRange.length === 0,
    affectedCount: outOfRange.length,
    percentage: pct(outOfRange.length, attendances.length),
    details: outOfRange.length > 0
      ? `${outOfRange.length} registros fora do período ${format(from, 'dd/MM/yyyy')}–${format(to, 'dd/MM/yyyy')}`
      : 'OK',
  })

  return checks
}

function checkTraceability(attendances: Attendance[]): AuditCheck[] {
  const checks: AuditCheck[] = []

  const ids = attendances.map((a) => a.id)
  const uniqueIds = new Set(ids)
  const duplicates = ids.length - uniqueIds.size
  checks.push({
    name: 'Traçabilidade: IDs únicos (sem duplicatas)',
    severity: 'critical',
    passed: duplicates === 0,
    affectedCount: duplicates,
    percentage: pct(duplicates, attendances.length),
    details: duplicates > 0
      ? `${duplicates} IDs duplicados detectados`
      : 'OK',
  })

  return checks
}

// --- Runner ---

function runAudit(attendances: Attendance[], from: Date, to: Date): AuditResult {
  const checks = [
    ...checkValidity(attendances),
    ...checkCompleteness(attendances),
    ...checkCurrency(attendances, from, to),
    ...checkTraceability(attendances),
  ]

  return {
    total: attendances.length,
    checks,
    criticalFailures: checks.filter((c) => !c.passed && c.severity === 'critical').length,
    warnings: checks.filter((c) => !c.passed && c.severity === 'warning').length,
    passed: checks.filter((c) => c.passed).length,
  }
}

function printReport(result: AuditResult) {
  console.log('\n========================================')
  console.log('  DATA QUALITY AUDIT REPORT (VCAT)')
  console.log('========================================')
  console.log(`  Total de registros auditados: ${result.total}`)
  console.log(`  Checks passados: ${result.passed}/${result.checks.length}`)
  console.log(`  Falhas críticas: ${result.criticalFailures}`)
  console.log(`  Avisos: ${result.warnings}`)
  console.log('========================================\n')

  for (const check of result.checks) {
    const icon = check.passed ? '✓' : check.severity === 'critical' ? '✗' : '⚠'
    const line = `${icon} [${check.severity.toUpperCase()}] ${check.name}`
    console.log(line)
    if (!check.passed) {
      console.log(`    → Afetados: ${check.affectedCount} (${check.percentage}%)`)
      console.log(`    → ${check.details}`)
    }
  }

  console.log('\n========================================')
  const status = result.criticalFailures > 0 ? 'FAILED' : result.warnings > 0 ? 'WARNINGS' : 'PASSED'
  console.log(`  STATUS: ${status}`)
  console.log('========================================\n')
}

// --- Main ---

async function main() {
  const { values } = parseArgs({
    options: {
      from: { type: 'string' },
      to: { type: 'string' },
      url: { type: 'string', default: process.env['GROVE_API_URL'] ?? 'http://localhost:3333' },
    },
  })

  const now = new Date()
  const from = values.from ? new Date(values.from) : subDays(now, 30)
  const to = values.to ? new Date(values.to) : now

  console.log(`Buscando atendimentos de ${format(from, 'yyyy-MM-dd')} a ${format(to, 'yyyy-MM-dd')}...`)

  const response = await fetch(`${values.url}/attendances/time-range`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from: format(from, 'yyyy-MM-dd HH:mm:ss'),
      to: format(to, 'yyyy-MM-dd HH:mm:ss'),
    }),
  })

  if (!response.ok) {
    console.error(`Erro ao buscar dados: ${response.status} ${response.statusText}`)
    process.exit(1)
  }

  const { attendances } = await response.json() as { attendances: Attendance[] }
  const result = runAudit(attendances, from, to)
  printReport(result)

  process.exit(result.criticalFailures > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error('Erro fatal:', err)
  process.exit(1)
})
