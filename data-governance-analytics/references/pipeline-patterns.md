# Pipeline Patterns — Padrões de Implementação Analítica

## Padrão ETC (Extract → Transform → Consume)

```
[DB / External API]
       ↓ Extract
[Validação DQA]
       ↓ Transform
[Agregação / Normalização]
       ↓ Store (opcional: cache)
       ↓ Consume
[Dashboard / API Response / Report]
```

---

## Padrões por Camada

### Extract (Backend — AdonisJS / API)

**Filtro temporal server-side (recomendado):**

```typescript
// ✅ Correto — filtro no banco
const attendances = await Attendance.query()
  .whereBetween('created_at', [from, to])
  .preload('reasons')

// ❌ Errado — retorna tudo e filtra no cliente
const attendances = await Attendance.all()
// então filtra no frontend com .filter(...)
```

**Endpoint analítico dedicado:**

```typescript
// POST /attendances/time-range
// Body: { from: string, to: string }
// Retorna: { attendances: Attendance[], meta: { total, from, to } }
```

**Regras:**
- Sempre receber `from` e `to` explícitos (nunca inferir "últimos 30 dias" no backend)
- Validar que `from <= to`
- Retornar `meta` com total para sanity check no cliente
- Limitar resultado máximo (ex: 10.000 registros) com aviso se exceder

---

### Transform (Backend ou Hook dedicado)

**Normalização:**

```typescript
const normalizeAttendeeName = (name?: string | null): string =>
  name?.trim().toLowerCase() ?? ''

// Aplicar antes de agrupar por atendente
const groupByAttendee = (attendances: Attendance[]) => {
  const map = new Map<string, number>()
  for (const a of attendances) {
    const name = normalizeAttendeeName(a.controls?.attendee_name)
    if (!name) continue
    map.set(name, (map.get(name) ?? 0) + 1)
  }
  return map
}
```

**Regras:**
- Normalizar strings antes de agrupar (trim + lowercase)
- Tratar valores null/undefined explicitamente
- Não usar lógica de transformação dentro de JSX/template

---

### Consume (Frontend — Next.js / React)

**Hook analítico dedicado (separar fetch de render):**

```typescript
// hooks/use-analytics.ts
export function useAnalytics(dateRange: DateRange) {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    fetchAnalytics(dateRange)
      .then((result) => { if (!cancelled) setData(result) })
      .catch((err) => { if (!cancelled) setError(err) })
      .finally(() => { if (!cancelled) setIsLoading(false) })
    return () => { cancelled = true }
  }, [dateRange])

  return { data, isLoading, error }
}
```

**useMemo para derivações:**

```typescript
// ✅ Derivar dados de chart em useMemo, não em render
const chartData = useMemo(() => {
  return computeChartData(attendances, usersMap)
}, [attendances, usersMap])
```

---

## Padrões de Agregação

### Série Temporal (Line Chart)

```typescript
// Agrupar por dia — chave: "dd/MM"
const dailyCounts = new Map<string, number>()
attendances.forEach((a) => {
  const key = format(new Date(a.createdAt), 'dd/MM')
  dailyCounts.set(key, (dailyCounts.get(key) ?? 0) + 1)
})

// Ordenar cronologicamente
const lineData = Array.from(dailyCounts.entries())
  .map(([date, count]) => ({ date, count }))
  .sort((a, b) => {
    const [dA, mA] = a.date.split('/').map(Number)
    const [dB, mB] = b.date.split('/').map(Number)
    return mA - mB || dA - dB
  })
```

### Distribuição (Pie / Bar)

```typescript
// Frequência por categoria
const categoryCounts = new Map<string, number>()
attendances.forEach((a) => {
  a.reasons.forEach((r) => {
    categoryCounts.set(r.name, (categoryCounts.get(r.name) ?? 0) + 1)
  })
})

// Calcular percentual
const total = attendances.length
const pieData = Array.from(categoryCounts.entries()).map(([name, count]) => ({
  name,
  value: count,
  percentage: total > 0 ? ((count / total) * 100).toFixed(1) : '0.0',
}))
```

---

## Cache e Performance

| Estratégia | Quando Usar | Implementação |
|------------|------------|---------------|
| Client-side (useState) | Dados da sessão atual | Re-fetch ao mudar filtros |
| SWR / React Query | Dados com revalidação | `stale-while-revalidate` |
| Server cache (Redis) | Relatórios históricos estáticos | TTL proporcional ao período |
| Streaming | Grandes volumes | `ReadableStream` + chunked response |

**Regra geral:** períodos passados (ex: mês anterior completo) → cacheável. Período atual → sem cache ou TTL curto (5 min).
