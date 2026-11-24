# 10 — Exemplo Completo: Agente Institucional de Ponta a Ponta

Este arquivo mostra a estrutura completa de um projeto real, com todos os módulos
conectados e prontos para produção. Use como ponto de partida de um novo projeto.

## Estrutura final do projeto

```
institutional-agent/
├── src/
│   ├── index.ts                    ← instância Genkit + exports
│   ├── server.ts                   ← servidor Express completo
│   ├── agents/
│   │   ├── orchestrator.ts         ← agente orquestrador
│   │   ├── hr.ts                   ← agente RH
│   │   └── it.ts                   ← agente TI
│   ├── tools/
│   │   ├── rag.ts                  ← searchKnowledgeBase
│   │   ├── database.ts             ← queryEmployeeData
│   │   ├── tickets.ts              ← createSupportTicket
│   │   └── approval.ts             ← requestHumanApproval (interrupt)
│   ├── flows/
│   │   └── indexer.ts              ← indexDocuments flow
│   ├── prompts/
│   │   ├── orchestrator.prompt     ← dotprompt principal
│   │   └── partials/
│   │       └── footer.prompt       ← partial reutilizável
│   ├── middleware/
│   │   ├── auth.ts                 ← JWT + RBAC
│   │   ├── input-guardrails.ts     ← validação e sanitização
│   │   ├── output-guardrails.ts    ← sanitização de output
│   │   └── rate-limiter.ts         ← rate limiting por usuário
│   └── lib/
│       ├── session-store.ts        ← Firestore session store
│       ├── vector-store.ts         ← configuração do retriever
│       ├── audit.ts                ← log de auditoria
│       └── telemetry.ts            ← OpenTelemetry
├── docs/                           ← documentos para indexar
│   ├── rh/
│   │   ├── politica-ferias.pdf
│   │   └── beneficios.pdf
│   └── ti/
│       └── solicitacao-acesso.md
├── Dockerfile
├── .env.example
├── package.json
└── tsconfig.json
```

---

## `src/index.ts` — instância global

```typescript
import { genkit } from 'genkit/beta';
import { googleAI }  from '@genkit-ai/google-genai';
import { firebase }  from '@genkit-ai/firebase';
import { googleCloud } from '@genkit-ai/google-cloud';

export const ai = genkit({
  plugins: [
    googleAI({ apiKey: process.env.GOOGLE_GENAI_API_KEY }),
    firebase({ projectId: process.env.FIREBASE_PROJECT_ID }),
    ...(process.env.NODE_ENV === 'production' ? [googleCloud()] : []),
  ],
  model: 'googleai/gemini-flash-latest',
  promptDir: './src/prompts',
  logLevel: (process.env.LOG_LEVEL as any) ?? 'info',
});

// Re-exportar para o servidor HTTP
export { orchestratorAgent } from './agents/orchestrator';
export { indexDocuments }    from './flows/indexer';
```

---

## `src/lib/vector-store.ts`

```typescript
import { ai } from '../index';
import {
  devLocalVectorstore,
  devLocalIndexerRef,
  devLocalRetrieverRef,
} from '@genkit-ai/dev-local-vectorstore';
import { pinecone } from '@genkit-ai/pinecone';
import { googleAI } from '@genkit-ai/google-genai';

const isProd = process.env.NODE_ENV === 'production';
const EMBEDDER = googleAI.embedder('gemini-embedding-001');
const INDEX_NAME = 'institutional-kb';

// Registrar o plugin correto na instância
export const vectorStorePlugin = isProd
  ? pinecone([{ indexId: INDEX_NAME, embedder: EMBEDDER }])
  : devLocalVectorstore([{ indexName: INDEX_NAME, embedder: EMBEDDER }]);

// Referências usadas em indexer.ts e rag.ts
export const institutionalIndexer = isProd
  ? pinecone.indexer(INDEX_NAME, EMBEDDER)
  : devLocalIndexerRef(INDEX_NAME);

export const institutionalRetriever = isProd
  ? pinecone.retriever(INDEX_NAME, EMBEDDER)
  : devLocalRetrieverRef(INDEX_NAME);
```

---

## `src/lib/session-store.ts`

```typescript
import { getFirestore, Timestamp } from 'firebase-admin/firestore';
import { initializeApp, getApps } from 'firebase-admin/app';

if (!getApps().length) {
  initializeApp({ projectId: process.env.FIREBASE_PROJECT_ID });
}

const COLLECTION = 'agent_sessions';
const db = getFirestore();

export function createSessionStore<S = unknown>() {
  return {
    async get(sessionId: string) {
      const snap = await db.collection(COLLECTION).doc(sessionId).get();
      return snap.exists ? snap.data() : null;
    },
    async set(sessionId: string, data: unknown) {
      await db.collection(COLLECTION).doc(sessionId).set(
        { ...data as object, updatedAt: Timestamp.now() },
        { merge: false }
      );
    },
    async delete(sessionId: string) {
      await db.collection(COLLECTION).doc(sessionId).delete();
    },
  };
}
```

---

## `src/tools/rag.ts`

```typescript
import { z } from 'genkit';
import { ai } from '../index';
import { institutionalRetriever } from '../lib/vector-store';

export const searchKnowledgeBase = ai.defineTool(
  {
    name: 'searchKnowledgeBase',
    description:
      'Busca documentos institucionais: políticas, benefícios, procedimentos e normas da empresa. ' +
      'Use SEMPRE antes de responder questões sobre regras internas, férias, benefícios ou processos.',
    inputSchema: z.object({
      query:      z.string().describe('Pergunta em linguagem natural'),
      department: z.string().optional().describe('Filtrar por departamento (rh, ti, financeiro)'),
      k:          z.number().default(4).describe('Quantidade de documentos a recuperar'),
    }),
    outputSchema: z.object({
      results: z.array(z.object({
        content:    z.string(),
        source:     z.string(),
        department: z.string(),
      })),
      found: z.boolean(),
    }),
  },
  async ({ query, department, k }) => {
    const docs = await ai.retrieve({
      retriever: institutionalRetriever,
      query,
      options: { k, ...(department ? { where: { department } } : {}) },
    });
    if (!docs?.length) return { results: [], found: false };
    return {
      found: true,
      results: docs.map((d) => ({
        content:    d.text,
        source:     String(d.metadata?.source ?? 'desconhecido'),
        department: String(d.metadata?.department ?? 'geral'),
      })),
    };
  }
);
```

---

## `src/tools/approval.ts`

```typescript
import { interrupt } from 'genkit/beta';
import { z } from 'genkit';
import { ai } from '../index';

const ApprovalPayload = z.object({
  action:          z.string(),
  requester:       z.string(),
  details:         z.record(z.unknown()),
  estimatedImpact: z.string(),
});

const ApprovalResponse = z.object({
  approved:        z.boolean(),
  approvedBy:      z.string(),
  approverComment: z.string().optional(),
});

export const requestHumanApproval = ai.defineTool(
  {
    name: 'requestHumanApproval',
    description:
      'Solicita aprovação de gestor ou RH antes de executar ações sensíveis: ' +
      'adiantamento salarial, aprovação de licença, alteração cadastral, compras acima do limite. ' +
      'OBRIGATÓRIO para qualquer ação irreversível ou financeira.',
    inputSchema: ApprovalPayload,
    outputSchema: ApprovalResponse,
  },
  async (payload) => {
    // Pausa o agente e retorna o payload ao frontend
    const decision = await interrupt<z.infer<typeof ApprovalResponse>>({
      type: 'human-approval',
      payload,
      metadata: { notifyEmails: ['rh@empresa.com'] },
    });
    return decision;
  }
);
```

---

## `src/tools/tickets.ts`

```typescript
import { z } from 'genkit';
import { ai } from '../index';

export const createSupportTicket = ai.defineTool(
  {
    name: 'createSupportTicket',
    description:
      'Abre um ticket de suporte no sistema de chamados (Jira/ServiceNow). ' +
      'Use quando o usuário pedir abertura de chamado, ou quando o problema ' +
      'não puder ser resolvido diretamente pelo assistente.',
    inputSchema: z.object({
      title:       z.string().describe('Título resumido do chamado'),
      description: z.string().describe('Descrição detalhada do problema'),
      category:    z.enum(['rh', 'ti', 'financeiro', 'geral']),
      priority:    z.enum(['low', 'medium', 'high']).default('medium'),
      requesterId: z.string().describe('ID do funcionário solicitante'),
    }),
    outputSchema: z.object({
      ticketId: z.string(),
      url:      z.string(),
      sla:      z.string().describe('Prazo de atendimento conforme SLA'),
    }),
  },
  async ({ title, description, category, priority, requesterId }) => {
    // Integração com Jira Service Management
    const res = await fetch(`${process.env.JIRA_URL}/rest/api/3/issue`, {
      method: 'POST',
      headers: {
        Authorization: `Basic ${Buffer.from(`${process.env.JIRA_EMAIL}:${process.env.JIRA_TOKEN}`).toString('base64')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        fields: {
          project: { key: process.env.JIRA_PROJECT_KEY },
          summary: title,
          description: { type: 'doc', version: 1, content: [{ type: 'paragraph', content: [{ type: 'text', text: description }] }] },
          issuetype: { name: 'Service Request' },
          priority: { name: priority === 'high' ? 'High' : priority === 'medium' ? 'Medium' : 'Low' },
          labels: [category, `requester-${requesterId}`],
        },
      }),
    });
    const data = await res.json() as { id: string; key: string };
    const slaMap = { high: '4 horas', medium: '1 dia útil', low: '3 dias úteis' };
    return {
      ticketId: data.key,
      url:      `${process.env.JIRA_URL}/browse/${data.key}`,
      sla:      slaMap[priority],
    };
  }
);
```

---

## `src/agents/hr.ts`

```typescript
import { ai } from '../index';
import { searchKnowledgeBase } from '../tools/rag';
import { createSupportTicket } from '../tools/tickets';
import { requestHumanApproval } from '../tools/approval';
import { createSessionStore } from '../lib/session-store';
import { z } from 'genkit';

const HRState = z.object({
  employeeId:  z.string().optional(),
  department:  z.string().optional(),
  openTickets: z.array(z.string()).default([]),
});

export const hrAgent = ai.defineAgent({
  name: 'hr-specialist',
  system: `Você é o especialista de Recursos Humanos da Empresa XYZ.

Domínio: férias, banco de horas, benefícios (plano de saúde, VR, VT), treinamentos,
admissão, demissão, contratos de trabalho e legislação trabalhista.

Regras:
- Consulte SEMPRE a base de conhecimento antes de responder sobre políticas
- Ações que alteram dados (solicitação de férias, mudanças cadastrais) requerem aprovação humana
- Para problemas não resolvidos em até 2 turnos, abra um ticket de suporte
- Cite a fonte (nome do documento) ao responder sobre políticas
- Nunca invente dados — se não souber, diga claramente`,
  tools: [searchKnowledgeBase, createSupportTicket, requestHumanApproval],
  stateSchema: HRState,
  model: 'googleai/gemini-pro-latest',  // modelo mais capaz para questões trabalhistas
  sessionStore: createSessionStore<z.infer<typeof HRState>>(),
});
```

---

## `src/agents/orchestrator.ts`

```typescript
import { agents } from 'genkit/beta';
import { ai } from '../index';
import { hrAgent } from './hr';
import { itAgent } from './it';
import { searchKnowledgeBase } from '../tools/rag';
import { createSessionStore } from '../lib/session-store';
import { z } from 'genkit';

const OrchestratorState = z.object({
  employeeId:    z.string().optional(),
  employeeName:  z.string().optional(),
  department:    z.string().optional(),
  language:      z.string().default('pt-BR'),
  lastTopics:    z.array(z.string()).default([]),
});

export const orchestratorAgent = ai.defineAgent({
  name: 'institutional-orchestrator',
  system: `Você é o assistente principal da Empresa XYZ, responsável por orientar funcionários.

Capacidades diretas:
- Responder questões gerais sobre a empresa com base na base de conhecimento
- Informar sobre políticas, procedimentos e comunicados

Delegação para especialistas (use o agente correto):
- Questões de RH → hr-specialist (férias, benefícios, treinamentos, contratos)
- Questões de TI → it-specialist (acesso, sistemas, equipamentos, senha)

Fluxo de delegação:
1. Entenda completamente o que o funcionário precisa
2. Se for escopo de especialista, delegue informando: "Vou conectar você com nosso especialista de [área]."
3. Passe o contexto completo no handoff (nome, departamento, o que foi dito)

Regras gerais:
- Sempre use a base de conhecimento antes de responder sobre políticas
- Se não souber, diga claramente — nunca invente
- Seja cordial, objetivo e cite fontes quando possível`,

  tools: [searchKnowledgeBase],
  use: [
    agents([hrAgent, itAgent], {
      description: 'Especialistas para questões de RH e TI',
    }),
  ],
  stateSchema: OrchestratorState,
  sessionStore: createSessionStore<z.infer<typeof OrchestratorState>>(),
});
```

---

## `src/flows/indexer.ts`

```typescript
import { z } from 'genkit';
import { ai } from '../index';
import { institutionalIndexer } from '../lib/vector-store';
import { Document } from 'genkit/retriever';
import { chunk } from 'llm-chunk';
import pdf from 'pdf-parse';
import fs from 'fs/promises';
import path from 'path';

const EXTENSIONS = ['.pdf', '.md', '.txt'];

export const indexDocuments = ai.defineFlow(
  {
    name: 'indexDocuments',
    inputSchema: z.object({
      source:          z.string().describe('Arquivo ou diretório'),
      department:      z.string().optional(),
      tags:            z.array(z.string()).optional(),
      replaceExisting: z.boolean().default(false),
    }),
    outputSchema: z.object({
      success:        z.boolean(),
      filesProcessed: z.number(),
      chunksIndexed:  z.number(),
      errors:         z.array(z.string()),
    }),
  },
  async ({ source, department, tags }) => {
    const errors: string[] = [];
    let filesProcessed = 0, chunksIndexed = 0;

    const stat = await fs.stat(source);
    const files = stat.isDirectory()
      ? (await fs.readdir(source))
          .filter((f) => EXTENSIONS.includes(path.extname(f).toLowerCase()))
          .map((f) => path.join(source, f))
      : [source];

    for (const filePath of files) {
      try {
        const buf = await fs.readFile(filePath);
        const text = path.extname(filePath) === '.pdf'
          ? (await pdf(buf)).text
          : buf.toString('utf-8');

        const chunks = chunk(text, { minLength: 800, maxLength: 1800, splitter: 'sentence', overlap: 150 });
        const documents = chunks.map((content, idx) =>
          Document.fromText(content, {
            source:     path.basename(filePath),
            filePath,
            chunkIndex: String(idx),
            department: department ?? 'geral',
            tags:       JSON.stringify(tags ?? []),
            indexedAt:  new Date().toISOString(),
          })
        );

        await ai.index({ indexer: institutionalIndexer, documents });
        filesProcessed++;
        chunksIndexed += documents.length;
      } catch (err) {
        errors.push(`${filePath}: ${String(err)}`);
      }
    }

    return { success: errors.length === 0, filesProcessed, chunksIndexed, errors };
  }
);
```

---

## `src/server.ts` — servidor completo

```typescript
import 'dotenv/config';
import './lib/telemetry';          // inicializar OTel antes de tudo
import express from 'express';
import helmet from 'helmet';
import { orchestratorAgent } from './agents/orchestrator';
import { validateInput }     from './middleware/input-guardrails';
import { sanitizeOutput }    from './middleware/output-guardrails';
import { applyRateLimits }   from './middleware/rate-limiter';
import { requireRole, authenticateRequest } from './middleware/auth';
import { writeAuditEvent }   from './lib/audit';

const app = express();

// Segurança HTTP
app.use(helmet());
app.use(express.json({ limit: '50kb' }));

// CORS restrito
app.use((req, res, next) => {
  const allowed = (process.env.ALLOWED_ORIGINS ?? '').split(',');
  const origin = req.headers.origin ?? '';
  if (allowed.includes(origin)) res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// ─── Health check ────────────────────────────────────────────────
app.get('/health', async (_req, res) => {
  res.json({ status: 'ok', version: process.env.npm_package_version, ts: new Date().toISOString() });
});

// ─── Chat ────────────────────────────────────────────────────────
app.post('/chat', async (req, res) => {
  let ctx: Awaited<ReturnType<typeof authenticateRequest>>;

  // 1. Autenticação
  try {
    ctx = await authenticateRequest(req);
  } catch {
    return res.status(401).json({ error: 'Não autenticado' });
  }

  // 2. Rate limiting
  const rl = await applyRateLimits(ctx.userId, req.ip ?? '0.0.0.0');
  if (!rl.allowed) {
    return res.status(429).json({ error: 'Muitas requisições. Aguarde e tente novamente.', retryAfterMs: rl.retryAfterMs });
  }

  // 3. Guardrail de input
  const guard = validateInput(req.body?.message ?? '');
  if (guard.blocked) {
    return res.status(400).json({ error: 'Mensagem inválida.', reason: guard.reason });
  }

  const start = Date.now();
  try {
    // 4. Carregar sessão e enviar mensagem
    const chat = await orchestratorAgent.loadChat(ctx.userId, {
      initialState: {
        employeeName: ctx.email.split('@')[0],
        department:   ctx.department,
        language:     'pt-BR',
        lastTopics:   [],
      },
    });

    const response = await chat.send(guard.sanitized);

    // 5. Interrupt — aguarda aprovação humana
    if (response.interrupt) {
      await writeAuditEvent({
        eventType: 'interrupt', sessionId: ctx.userId, userId: ctx.userId,
        userDepartment: ctx.department,
        inputSummary: guard.sanitized.slice(0, 100),
        outputSummary: `Interrupt: ${response.interrupt.type}`,
        latencyMs: Date.now() - start, ipAddress: req.ip ?? '',
      });
      return res.json({
        type: 'interrupt',
        interruptType: response.interrupt.type,
        payload: response.interrupt.payload,
        resumeToken: response.interrupt.resumeToken,
      });
    }

    // 6. Sanitizar output
    const { sanitized: safeOutput, hadSensitiveData } = sanitizeOutput(response.text);

    // 7. Auditoria
    await writeAuditEvent({
      eventType: 'chat_turn', sessionId: ctx.userId, userId: ctx.userId,
      userDepartment: ctx.department,
      inputSummary: guard.sanitized.slice(0, 100),
      outputSummary: safeOutput.slice(0, 100),
      toolsUsed: response.toolCalls?.map((t) => t.name),
      latencyMs: Date.now() - start,
      tokens: (response.usage?.inputTokens ?? 0) + (response.usage?.outputTokens ?? 0),
      ipAddress: req.ip ?? '',
    });

    res.json({
      type: 'message',
      text: safeOutput,
      ...(hadSensitiveData ? { notice: 'Dados sensíveis foram omitidos da resposta.' } : {}),
    });

  } catch (err) {
    console.error('Chat error:', err);
    res.status(500).json({ error: 'Erro interno. Tente novamente em instantes.' });
  }
});

// ─── Resume (após aprovação humana) ──────────────────────────────
app.post('/chat/resume', async (req, res) => {
  let ctx: Awaited<ReturnType<typeof authenticateRequest>>;
  try { ctx = await authenticateRequest(req); }
  catch { return res.status(401).json({ error: 'Não autenticado' }); }

  const { resumeToken, approvalResponse } = req.body;
  const chat = await orchestratorAgent.loadChat(ctx.userId);
  const response = await chat.resume(resumeToken, approvalResponse);

  await writeAuditEvent({
    eventType: 'approval', sessionId: ctx.userId, userId: ctx.userId,
    inputSummary: 'resume after approval',
    outputSummary: response.text.slice(0, 100),
    approved: approvalResponse?.approved,
    approvedBy: approvalResponse?.approvedBy,
    latencyMs: 0, ipAddress: req.ip ?? '',
  });

  res.json({ type: 'message', text: response.text });
});

// ─── LGPD: exportar dados ────────────────────────────────────────
app.get('/my-data', async (req, res) => {
  let ctx: Awaited<ReturnType<typeof authenticateRequest>>;
  try { ctx = await authenticateRequest(req); }
  catch { return res.status(401).json({ error: 'Não autenticado' }); }

  const session = await orchestratorAgent.sessionStore?.get(ctx.userId);
  res.json({ userId: ctx.userId, email: ctx.email, session, exportedAt: new Date().toISOString() });
});

// ─── LGPD: deletar dados ─────────────────────────────────────────
app.delete('/my-data', async (req, res) => {
  let ctx: Awaited<ReturnType<typeof authenticateRequest>>;
  try { ctx = await authenticateRequest(req); }
  catch { return res.status(401).json({ error: 'Não autenticado' }); }

  await orchestratorAgent.sessionStore?.delete(ctx.userId);
  res.json({ success: true });
});

// ─── Admin: re-indexar documentos ────────────────────────────────
app.post('/admin/index', async (req, res) => {
  let ctx: Awaited<ReturnType<typeof authenticateRequest>>;
  try { ctx = await authenticateRequest(req); }
  catch { return res.status(401).json({ error: 'Não autenticado' }); }

  if (!ctx.roles.includes('admin')) return res.status(403).json({ error: 'Acesso negado' });

  const { indexDocuments } = await import('./flows/indexer');
  const result = await indexDocuments({ source: './docs', replaceExisting: true });
  res.json(result);
});

const PORT = process.env.PORT ?? 8080;
app.listen(PORT, () => console.log(`🤖 Institutional Agent running on :${PORT}`));
```

---

## `src/prompts/orchestrator.prompt`

```handlebars
---
name: institutional-orchestrator
model: googleai/gemini-flash-latest
config:
  temperature: 0.3
  maxOutputTokens: 1024
input:
  schema:
    employeeName?: string, "Nome do funcionário"
    department?: string, "Departamento"
    language?: string, "Idioma preferido"
---
Você é o assistente da Empresa XYZ.
{{#if employeeName}}Funcionário: {{employeeName}}{{#if department}} ({{department}}){{/if}}.{{/if}}
{{#if language}}Responda em {{language}}.{{/if}}

Use as ferramentas disponíveis antes de responder sobre políticas internas.
Seja preciso, cordial e cite fontes quando possível.

{{> footer}}
```

```handlebars
{{! src/prompts/partials/footer.prompt }}
---
Atendimento humano: rh@empresa.com | Suporte TI: ti@empresa.com | Ramal: 1234
```

---

## `.env.example`

```bash
# Modelos
GOOGLE_GENAI_API_KEY=
GOOGLE_APPLICATION_CREDENTIALS=        # alternativa para Vertex AI

# Sessão e dados
FIREBASE_PROJECT_ID=
GCP_PROJECT_ID=

# Indexação
PINECONE_API_KEY=                       # produção
PINECONE_ENVIRONMENT=us-east-1-aws

# Tickets
JIRA_URL=https://empresa.atlassian.net
JIRA_EMAIL=agente@empresa.com
JIRA_TOKEN=
JIRA_PROJECT_KEY=SUPORTE

# Auth
JWT_SECRET=
ALLOWED_ORIGINS=https://app.empresa.com

# App
PORT=8080
NODE_ENV=development                    # development | production
LOG_LEVEL=info                          # debug | info | warn | error
GENKIT_ENV=dev                          # dev | prod
```

---

## Sequência de primeiros passos em um novo projeto

```bash
# 1. Clonar/criar o projeto
mkdir institutional-agent && cd institutional-agent
npm init -y

# 2. Instalar dependências
npm install genkit @genkit-ai/google-genai @genkit-ai/firebase \
            @genkit-ai/google-cloud express helmet zod \
            llm-chunk pdf-parse firebase-admin \
            rate-limiter-flexible jsonwebtoken dotenv
npm install -D tsx typescript vitest @types/node @types/express \
            @types/pdf-parse @types/jsonwebtoken genkit-cli

# 3. Configurar variáveis de ambiente
cp .env.example .env.local
# editar .env.local com as chaves reais

# 4. Indexar documentos
npx tsx src/flows/indexer.ts
# ou via CLI:
npx genkit flow:run indexDocuments '{"source":"./docs"}' -- npx tsx src/index.ts

# 5. Testar no Dev UI
npm run dev
# Abrir http://localhost:4000 — testar o agente visualmente

# 6. Executar testes unitários
npm test

# 7. Build de produção
npm run build

# 8. Deploy no Cloud Run
gcloud run deploy institutional-agent \
  --source . \
  --region us-central1 \
  --memory 2Gi \
  --min-instances 1
```

---

## Contrato da API (para o frontend)

```typescript
// Tipos compartilhados frontend ↔ backend

// POST /chat
interface ChatRequest  { message: string }
interface ChatResponse {
  type: 'message' | 'interrupt';
  text?: string;                   // presente quando type === 'message'
  interruptType?: string;          // presente quando type === 'interrupt'
  payload?: unknown;               // dados para o aprovador renderizar
  resumeToken?: string;            // token para chamar /chat/resume
  notice?: string;                 // aviso de dado sensível omitido
}

// POST /chat/resume
interface ResumeRequest  { resumeToken: string; approvalResponse: { approved: boolean; approvedBy: string; approverComment?: string } }
interface ResumeResponse { type: 'message'; text: string }

// GET /my-data   → dados LGPD do usuário autenticado
// DELETE /my-data → exclusão de dados LGPD
// POST /admin/index → re-indexar documentos (role: admin)
// GET /health     → { status, version, ts }
```
