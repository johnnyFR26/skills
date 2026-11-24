# 04 — Tool Calling, Interrupts e Fluxos de Aprovação

## Sumário
- [Anatomia de uma tool](#anatomia-de-uma-tool)
- [Padrões de tool por categoria](#padrões-de-tool-por-categoria)
- [Interrupts — aprovação humana no fluxo](#interrupts--aprovação-humana-no-fluxo)
- [Padrão de fluxo de aprovação completo](#padrão-de-fluxo-de-aprovação-completo)
- [Tool com retry e fallback](#tool-com-retry-e-fallback)
- [Executar tools em paralelo](#executar-tools-em-paralelo)
- [Tool que chama API externa autenticada](#tool-que-chama-api-externa-autenticada)

---

## Anatomia de uma tool

```typescript
// Estrutura completa de uma tool institucional
export const minhaFerramenta = ai.defineTool(
  {
    name: 'minhaFerramenta',                // camelCase, sem espaços
    description:                             // ← CRÍTICO: o LLM usa isso para decidir quando chamar
      'Descrição clara do que a tool faz, quando usar, e o que retorna. ' +
      'Inclua exemplos de quando chamar: "Use quando o usuário perguntar sobre X ou Y". ' +
      'Seja específico — descrições vagas fazem o modelo não chamar a tool.',
    inputSchema: z.object({
      parametro: z.string().describe('O que é esse parâmetro e valores aceitos'),
      opcional: z.string().optional().describe('Parâmetro opcional com valor padrão'),
    }),
    outputSchema: z.object({
      resultado: z.string(),
      sucesso: z.boolean(),
    }),
  },
  async (input, context) => {
    // `context.session` — acesso à sessão atual (opcional, disponível apenas em agentes)
    // `context.auth`    — dados de autenticação do request

    // Implemente a lógica aqui
    return { resultado: 'valor', sucesso: true };
  }
);
```

> **Regra de ouro para `description`:** se você consegue imaginar o LLM perguntando "quando devo usar isso?", a descrição precisa responder essa pergunta de forma inequívoca.

---

## Padrões de tool por categoria

### Tool de consulta a banco de dados

```typescript
// src/tools/database.ts
import { z } from 'genkit';
import { ai } from '../index';
import { db } from '../lib/database';

export const queryEmployeeData = ai.defineTool(
  {
    name: 'queryEmployeeData',
    description:
      'Consulta dados do funcionário: saldo de férias, cargo, salário, histórico de tickets. ' +
      'Use quando o usuário perguntar sobre seus dados pessoais, férias disponíveis ou situação funcional.',
    inputSchema: z.object({
      employeeId: z.string().describe('ID do funcionário (disponível na sessão)'),
      fields: z
        .array(z.enum(['vacation_balance', 'position', 'department', 'tickets', 'payroll']))
        .describe('Campos a consultar'),
    }),
    outputSchema: z.object({
      data: z.record(z.unknown()),
      found: z.boolean(),
    }),
  },
  async ({ employeeId, fields }) => {
    const employee = await db.employees.findById(employeeId, { select: fields });
    if (!employee) return { data: {}, found: false };
    return { data: employee, found: true };
  }
);
```

### Tool de integração com sistema legado (SOAP/REST)

```typescript
// src/tools/erp.ts
export const getERPData = ai.defineTool(
  {
    name: 'getERPData',
    description:
      'Consulta o sistema ERP para dados de pedidos, estoque, fornecedores e notas fiscais. ' +
      'Use para perguntas sobre status de pedido, disponibilidade de produto ou dados fiscais.',
    inputSchema: z.object({
      entity: z.enum(['order', 'stock', 'supplier', 'invoice']),
      id: z.string().describe('ID da entidade a consultar'),
    }),
    outputSchema: z.object({
      data: z.record(z.unknown()).nullable(),
      error: z.string().optional(),
    }),
  },
  async ({ entity, id }) => {
    try {
      const response = await fetch(`${process.env.ERP_BASE_URL}/api/${entity}/${id}`, {
        headers: { Authorization: `Bearer ${process.env.ERP_API_KEY}` },
      });
      if (!response.ok) throw new Error(`ERP error: ${response.status}`);
      const data = await response.json();
      return { data };
    } catch (err) {
      return { data: null, error: String(err) };
    }
  }
);
```

### Tool de envio de e-mail / notificação

```typescript
// src/tools/notifications.ts
export const sendNotification = ai.defineTool(
  {
    name: 'sendNotification',
    description:
      'Envia e-mail ou notificação para o funcionário ou equipe de RH. ' +
      'Use APENAS quando o usuário pedir explicitamente para enviar ou notificar alguém.',
    inputSchema: z.object({
      to: z.string().email().describe('E-mail do destinatário'),
      subject: z.string().describe('Assunto do e-mail'),
      body: z.string().describe('Corpo da mensagem em texto simples'),
      cc: z.array(z.string().email()).optional().describe('Cópias'),
    }),
    outputSchema: z.object({
      sent: z.boolean(),
      messageId: z.string().optional(),
    }),
  },
  async ({ to, subject, body, cc }) => {
    const result = await emailService.send({ to, subject, body, cc });
    return { sent: result.ok, messageId: result.id };
  }
);
```

---

## Interrupts — aprovação humana no fluxo

Interrupts pausam a execução do agente e aguardam input humano antes de continuar.
São ideais para: aprovações de RH, confirmações financeiras, revisões de compliance.

```typescript
// src/tools/approval.ts
import { interrupt } from 'genkit/beta';
import { z } from 'genkit';
import { ai } from '../index';

// Schema de dados enviados ao aprovador
const ApprovalRequest = z.object({
  action: z.string(),
  requester: z.string(),
  details: z.record(z.unknown()),
  estimatedImpact: z.string(),
});

// Schema da resposta do aprovador
const ApprovalResponse = z.object({
  approved: z.boolean(),
  approverComment: z.string().optional(),
  approvedBy: z.string(),
});

export const requestHumanApproval = ai.defineTool(
  {
    name: 'requestHumanApproval',
    description:
      'Solicita aprovação de um gestor ou RH antes de executar ações sensíveis como: ' +
      'adiantamento salarial, aprovação de licença, alteração de dados cadastrais, ' +
      'compras acima do limite ou cancelamento de contratos. ' +
      'SEMPRE use esta tool antes de qualquer ação irreversível ou que envolva dinheiro.',
    inputSchema: ApprovalRequest,
    outputSchema: ApprovalResponse,
  },
  async (approvalRequest) => {
    // `interrupt()` pausa o agente e envia `approvalRequest` para o cliente
    // O cliente deve chamar `chat.resume(response)` com a resposta do aprovador
    const approverDecision = await interrupt<ApprovalResponse>({
      type: 'human-approval',
      payload: approvalRequest,
      // Metadados para o frontend renderizar a UI de aprovação
      metadata: {
        urgency: 'normal',
        notifyEmails: ['gestor@empresa.com', 'rh@empresa.com'],
      },
    });

    return approverDecision;
  }
);
```

---

## Padrão de fluxo de aprovação completo

```
Usuário ──────────────────────────────────────────────────────────────
  │  "Quero solicitar adiantamento salarial de R$1000"
  ▼
Agente
  │  1. Chama searchKnowledgeBase → verifica política de adiantamento
  │  2. Chama queryEmployeeData → verifica elegibilidade
  │  3. Chama requestHumanApproval → ⏸️ INTERRUPT
  │
  ▼  (agente pausa, retorna InterruptEvent ao frontend)
Frontend / Gestor
  │  Exibe UI de aprovação com os dados
  │  Gestor clica "Aprovar" ou "Recusar"
  │
  ▼  chat.resume({ approved: true, approvedBy: 'João Silva', approverComment: '...' })
Agente retoma
  │  4. Se aprovado → chama processPayrollAdvance
  │  5. Chama sendNotification → notifica funcionário
  │
  ▼
Resposta final ao usuário
```

**Implementação do servidor — interrupt e resume:**
```typescript
// src/server.ts

// Enviar mensagem — pode resultar em interrupt
app.post('/chat', requireAuth, async (req: AuthRequest, res) => {
  const { message } = req.body;
  const chat = await institutionalAgent.loadChat(req.userId!);

  const response = await chat.send(message);

  // Verificar se houve interrupt
  if (response.interrupt) {
    return res.json({
      type: 'interrupt',
      interruptType: response.interrupt.type,
      payload: response.interrupt.payload,
      metadata: response.interrupt.metadata,
      resumeToken: response.interrupt.resumeToken,  // token para retomar
    });
  }

  res.json({ type: 'message', text: response.text });
});

// Retomar após aprovação humana
app.post('/chat/resume', requireAuth, async (req: AuthRequest, res) => {
  const { resumeToken, approvalResponse } = req.body;
  const chat = await institutionalAgent.loadChat(req.userId!);

  const response = await chat.resume(resumeToken, approvalResponse);
  res.json({ type: 'message', text: response.text });
});
```

---

## Tool com retry e fallback

```typescript
// src/lib/tool-utils.ts
export function withRetry<T>(
  fn: () => Promise<T>,
  options: { retries?: number; delayMs?: number; fallback?: T } = {}
): Promise<T> {
  const { retries = 2, delayMs = 500, fallback } = options;

  return fn().catch(async (err) => {
    if (retries <= 0) {
      if (fallback !== undefined) return fallback;
      throw err;
    }
    await new Promise((r) => setTimeout(r, delayMs));
    return withRetry(fn, { retries: retries - 1, delayMs: delayMs * 2, fallback });
  });
}

// Uso:
export const fetchExternalData = ai.defineTool(
  { name: 'fetchExternalData', /* ... */ },
  async (input) => {
    return withRetry(
      () => externalAPI.fetch(input.id),
      { retries: 3, delayMs: 300, fallback: { data: null, error: 'Serviço indisponível' } }
    );
  }
);
```

---

## Executar tools em paralelo

Quando múltiplas tools são independentes, o modelo pode chamá-las em paralelo:

```typescript
// O Genkit executa tools paralelas automaticamente quando o modelo retorna
// múltiplas tool_use na mesma resposta.
// Para forçar paralelismo em flows customizados:
const [kbResults, dbData] = await Promise.all([
  ai.retrieve({ retriever: institutionalRetriever, query: input.question, options: { k: 3 } }),
  employeeAPI.getProfile(input.employeeId),
]);
```

---

## Tool que chama API externa autenticada

```typescript
// src/lib/api-client.ts — cliente autenticado compartilhado
import { createRemoteJWKSet, jwtVerify } from 'jose';

class InstitutionalAPIClient {
  private baseUrl = process.env.INTERNAL_API_URL!;
  private serviceToken: string | null = null;
  private tokenExpiry = 0;

  private async getToken(): Promise<string> {
    if (this.serviceToken && Date.now() < this.tokenExpiry) {
      return this.serviceToken;
    }
    // Buscar token de serviço (client_credentials flow)
    const res = await fetch(`${process.env.AUTH_URL}/token`, {
      method: 'POST',
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: process.env.SERVICE_CLIENT_ID!,
        client_secret: process.env.SERVICE_CLIENT_SECRET!,
        scope: 'internal-api',
      }),
    });
    const { access_token, expires_in } = await res.json();
    this.serviceToken = access_token;
    this.tokenExpiry = Date.now() + (expires_in - 60) * 1000;
    return access_token;
  }

  async get<T>(path: string): Promise<T> {
    const token = await this.getToken();
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`API ${path} returned ${res.status}`);
    return res.json() as Promise<T>;
  }
}

export const apiClient = new InstitutionalAPIClient();

// Uso em tool:
export const getPolicy = ai.defineTool(
  { name: 'getPolicy', description: '...', inputSchema: z.object({ policyId: z.string() }), outputSchema: z.unknown() },
  async ({ policyId }) => apiClient.get(`/policies/${policyId}`)
);
```

---

## Checklist de tools

- [ ] `description` explica **quando** e **por que** chamar, não apenas *o quê*
- [ ] `inputSchema` tem `.describe()` em cada campo
- [ ] Erros são capturados e retornados no `outputSchema` (nunca deixe throw não tratado)
- [ ] Tools de ação irreversível usam `interrupt()` para aprovação humana
- [ ] Tools externas têm retry + fallback configurados
- [ ] Logs de chamadas de tool para auditoria (ver `07-deploy-observability.md`)
- [ ] Tools testadas individualmente no Dev UI antes de integrar ao agente
