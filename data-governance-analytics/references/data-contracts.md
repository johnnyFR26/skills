# Data Contracts — Exemplos e Padrões

## O que é um Data Contract

Um Data Contract é um acordo explícito sobre a estrutura, semântica e garantias dos dados trocados entre serviços ou camadas. Funciona como um "contrato de API" aplicado especificamente à camada analítica.

---

## Template de Data Contract

```typescript
/**
 * DATA CONTRACT v1
 * Endpoint: POST /attendances/time-range
 * Owner: backend team
 * Consumers: web/analytics dashboard
 * Last updated: YYYY-MM-DD
 */

// --- REQUEST ---
interface AttendanceTimeRangeRequest {
  from: string  // ISO 8601, ex: "2024-01-01 00:00:00" (UTC implícito documentado)
  to: string    // ISO 8601, ex: "2024-01-31 23:59:00" (UTC implícito documentado)
  // Restrição: from <= to, máximo 365 dias de diferença
}

// --- RESPONSE ---
interface AttendanceTimeRangeResponse {
  attendances: AttendanceItem[]
  meta: {
    total: number           // Total de registros retornados (para sanity check)
    from: string            // Eco do filtro aplicado
    to: string              // Eco do filtro aplicado
    generatedAt: string     // ISO 8601 — quando a query foi executada
    truncated: boolean      // true se limite máximo foi atingido
    limit: number           // Limite máximo aplicado (ex: 10000)
  }
}

interface AttendanceItem {
  id: number
  userId: number
  externalAttendeeId: number
  externalCustomerId: number
  title: string
  description: string
  controls?: {
    attendee_name?: string  // Pode ser null/undefined — tratar explicitamente
  }
  createdAt: string         // ISO 8601
  updatedAt: string         // ISO 8601
  reasons: ReasonItem[]
}

interface ReasonItem {
  id: number
  name: string
  weight?: number           // Opcional — pode não existir em registros antigos
}
```

---

## Princípios de Versionamento

1. **Nunca remover campos** — marcar como `@deprecated` e documentar prazo
2. **Nunca alterar tipo de campo** — criar campo novo com nome diferente
3. **Novos campos obrigatórios** exigem nova versão major (`v1` → `v2`)
4. **Novos campos opcionais** podem ser adicionados na versão corrente
5. **Versão na URL**: `/v1/attendances/time-range`

```
v1  →  v1.1 (campo opcional adicionado: sem quebra)
v1  →  v2   (campo obrigatório adicionado ou tipo alterado: quebra)
```

---

## Contrato de Usuários (Exemplo)

```typescript
/**
 * DATA CONTRACT v1
 * Endpoint: GET /users
 * Retorna lista de usuários com mapeamento de IDs externos
 */
interface UsersResponse {
  users: {
    data: UserItem[]
    meta?: {
      total: number
      page: number
      perPage: number
    }
  }
}

interface UserItem {
  id: number
  name: string | null               // Pode ser null — normalizar antes de usar
  externalAttendeeId: number | null // Pode ser null — excluir de mapeamentos se null
}
```

---

## Validações no Limite do Sistema

### Backend (entrada)

```typescript
// AdonisJS — validação de request analítico
import vine from '@vinejs/vine'

const analyticsRequestSchema = vine.object({
  from: vine.string().regex(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/),
  to: vine.string().regex(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/),
})
```

### Frontend (saída para gráficos)

```typescript
// Validar antes de passar para o gráfico
const safePieData = chartData.pieData.filter(
  (item) => item.name && item.value > 0
)
```

---

## Checklist de Data Contract

Ao criar ou modificar um endpoint analítico:

- [ ] Request schema documentado com tipos e restrições
- [ ] Response schema documentado com todos os campos
- [ ] Campos nullable/optional explicitamente marcados
- [ ] Timezone documentado (UTC ou local)
- [ ] Limite de registros documentado
- [ ] Campo `meta` com `total` e `generatedAt`
- [ ] Versão no path da URL
- [ ] `@deprecated` em campos removidos com data de remoção
- [ ] Consumidores conhecidos listados no contrato
