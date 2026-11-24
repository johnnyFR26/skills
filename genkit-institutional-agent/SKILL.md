---
name: genkit-institutional-agent
description: >
  Guia completo para desenvolvimento de agentes institucionais baseados em LLM usando o framework
  Genkit (genkit.dev). Use esta skill SEMPRE que o usuário mencionar: Genkit, agente institucional,
  RAG corporativo, base de conhecimento empresarial, controle de sessão em agente, tool calling com
  Genkit, agente conversacional com persistência, fluxo de aprovação com LLM, multi-agente Genkit,
  deploy de agente em Cloud Run / Firebase, dotprompt, guardrails de LLM, proteção de PII em agente,
  testes de agente, evals de LLM, ou qualquer desenvolvimento de assistente virtual institucional.
  Inclui padrões de arquitetura, code samples prontos para produção e decisões de design para cada
  camada do agente.
triggers:
  - genkit
  - agente institucional
  - RAG corporativo
  - base de conhecimento LLM
  - tool calling genkit
  - sessão de agente
  - multi-agent genkit
  - interrupt human-in-the-loop
  - dotprompt
  - deploy agente cloud run
  - guardrails LLM
  - evals agente
---

# Skill: Agente Institucional com Genkit

Framework: **Genkit** (`genkit.dev`) — SDK open-source do Google para TypeScript, Go e Python.

> **Regra:** leia este SKILL.md inteiro antes de escrever qualquer código.
> Em seguida leia apenas o(s) arquivo(s) de referência relevantes para a tarefa.

---

## Estrutura da skill

```
genkit-institutional-agent/
├── SKILL.md                        ← você está aqui (leia sempre primeiro)
└── references/
    ├── 01-setup.md                 ← instalação, plugins, estrutura de projeto
    ├── 02-rag-knowledge-base.md    ← indexers, embedders, retrievers, chunking
    ├── 03-session-state.md         ← sessão, histórico, stores, custom state
    ├── 04-tool-calling.md          ← tools, interrupts, fluxos de aprovação
    ├── 05-multi-agent.md           ← orquestrador, especialistas, roteamento
    ├── 06-dotprompt.md             ← templates, partials, versionamento de prompt
    ├── 07-deploy-observability.md  ← Cloud Run, Firebase, OTel, alertas
    ├── 08-testing.md               ← unitários, integração, evals de qualidade
    ├── 09-security-guardrails.md   ← guardrails, PII, rate limiting, LGPD
    └── 10-complete-example.md      ← projeto completo de ponta a ponta
```

**Qual referência ler para cada tarefa:**

| Tarefa | Arquivo |
|---|---|
| Novo projeto / instalação | `01-setup.md` |
| Base de conhecimento, documentos, FAQ, políticas | `02-rag-knowledge-base.md` |
| Chat persistente, histórico entre sessões | `03-session-state.md` |
| Ferramentas externas, APIs, aprovações humanas | `04-tool-calling.md` |
| Múltiplos agentes especializados, orquestrador | `05-multi-agent.md` |
| Prompts com templates, versionamento de prompt | `06-dotprompt.md` |
| Deploy em produção, Cloud Run, logs, traces | `07-deploy-observability.md` |
| Testes unitários, integração, evals de LLM | `08-testing.md` |
| Segurança, guardrails, PII, rate limiting, LGPD | `09-security-guardrails.md` |
| Projeto completo, ver tudo conectado | `10-complete-example.md` |

---

## Arquitetura de referência

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND / CLIENTE                            │
│            Browser · App Mobile · Slack · Microsoft Teams            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  HTTPS  POST /chat
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SERVIDOR (Express / Cloud Run)                  │
│                                                                      │
│  Auth JWT ──► Rate Limit ──► Input Guardrail ──► Output Guardrail   │
│                                    │                                 │
│        ┌───────────────────────────▼──────────────────────────┐     │
│        │           CAMADA DE AGENTE (Genkit)                   │     │
│        │                                                        │     │
│        │  ┌─────────────────────┐   ┌────────────────────────┐│     │
│        │  │  Orquestrador       │──►│  Especialistas (HR, TI) ││     │
│        │  └────────┬────────────┘   └────────────────────────┘│     │
│        │           │                                            │     │
│        │  ┌────────▼────────────────────────────────────────┐  │     │
│        │  │               TOOL LAYER                        │  │     │
│        │  │  searchKB · queryDB · createTicket · interrupt  │  │     │
│        │  └────────────────────────────────────────────────┘  │     │
│        └───────────────────────────────────────────────────────┘     │
│                          │               │                            │
│                 ┌─────────┘               └──────────┐               │
└─────────────────┼─────────────────────────────────────┼─────────────┘
                  ▼                                       ▼
         ┌─────────────────┐                   ┌──────────────────┐
         │  Firestore      │                   │  Vector DB       │
         │  Session Store  │                   │  (RAG / Docs)    │
         └─────────────────┘                   └──────────────────┘
```

---

## Decisões de design rápidas

| Necessidade | Primitivo Genkit | Referência |
|---|---|---|
| Resposta única sem histórico | `ai.generate()` + `ai.defineFlow()` | `01-setup.md` |
| Chat persistente multi-turno | `ai.defineAgent()` + Session Store | `03-session-state.md` |
| Resposta baseada em documentos | `ai.index()` + `ai.retrieve()` | `02-rag-knowledge-base.md` |
| Chamar API externa / banco | `ai.defineTool()` | `04-tool-calling.md` |
| Aprovação humana no fluxo | `interrupt()` dentro de tool | `04-tool-calling.md` |
| Especialistas por domínio | `agents()` middleware | `05-multi-agent.md` |
| Prompt versionado e testável | Dotprompt (`.prompt` files) | `06-dotprompt.md` |
| Bloquear conteúdo malicioso | Input/Output Guardrails | `09-security-guardrails.md` |
| Detectar regressão de qualidade | Evals com dataset fixo | `08-testing.md` |
| Produção com observabilidade | Cloud Run + OpenTelemetry | `07-deploy-observability.md` |

---

## Quick-start mínimo funcional

```typescript
// src/index.ts
import { genkit } from 'genkit/beta';
import { googleAI } from '@genkit-ai/google-genai';

export const ai = genkit({
  plugins: [googleAI()],
  model: 'googleai/gemini-flash-latest',
  promptDir: './src/prompts',
});
```

```typescript
// src/agents/institutional.ts
import { ai } from '../index';
import { searchKnowledgeBase } from '../tools/rag';
import { createSessionStore } from '../lib/session-store';

export const institutionalAgent = ai.defineAgent({
  name: 'institutional-assistant',
  system: `Você é o assistente da [Empresa].
Sempre use a ferramenta de busca antes de responder sobre políticas internas.
Se não souber, diga claramente e ofereça abrir um ticket.`,
  tools: [searchKnowledgeBase],
  sessionStore: createSessionStore(),
});
```

```typescript
// src/server.ts — endpoint mínimo
import express from 'express';
import { institutionalAgent } from './agents/institutional';

const app = express();
app.use(express.json());

app.post('/chat', async (req, res) => {
  const { sessionId, message } = req.body;
  const chat = await institutionalAgent.loadChat(sessionId);
  const { text } = await chat.send(message);
  res.json({ text });
});

app.listen(8080, () => console.log('Agent on :8080'));
```

---

## Fluxo de desenvolvimento recomendado

```
1. Setup           → 01-setup.md       (instalar, configurar, rodar Dev UI)
       │
2. Base de         → 02-rag-knowledge  (indexar docs, testar retriever)
   conhecimento       -base.md
       │
3. Agente +        → 03-session-       (defineAgent, session store, estado)
   sessão             state.md
       │
4. Tools           → 04-tool-calling.  (APIs externas, approvals, interrupts)
                       md
       │
5. Multi-agent     → 05-multi-agent.   (orquestrador + especialistas, se necessário)
   (opcional)         md
       │
6. Refinar         → 06-dotprompt.md  (migrar prompts para .prompt files)
   prompts
       │
7. Segurança       → 09-security-      (guardrails, rate limiting, auditoria)
                       guardrails.md
       │
8. Testes          → 08-testing.md    (unitários, integração, evals)
       │
9. Deploy          → 07-deploy-        (Cloud Run, OTel, alertas, rollback)
                       observability.md
```

---

## Comandos CLI essenciais

```bash
# Instalar CLI globalmente
npm install -g genkit-cli

# Dev UI com hot-reload (http://localhost:4000)
npx genkit start -- npx tsx --watch src/index.ts

# Executar flow de indexação
npx genkit flow:run indexDocuments '{"source":"./docs","department":"rh"}' \
  -- npx tsx src/index.ts

# Executar evals de qualidade
npx genkit flow:run runRagEval '{"sessionPrefix":"eval-prod"}' \
  -- npx tsx src/index.ts

# Listar todos os agentes e flows registrados
npx genkit flow:list -- npx tsx src/index.ts
```

---

## Variáveis de ambiente obrigatórias

```bash
# .env.local
GOOGLE_GENAI_API_KEY=          # ou GOOGLE_APPLICATION_CREDENTIALS para Vertex AI
FIREBASE_PROJECT_ID=           # sessão + auditoria (Firestore)
PINECONE_API_KEY=              # vector store em produção
JWT_SECRET=                    # autenticação dos usuários
ALLOWED_ORIGINS=               # CORS: https://app.empresa.com
PORT=8080
NODE_ENV=development           # development | production
LOG_LEVEL=info                 # debug | info | warn | error
GENKIT_ENV=dev                 # dev | prod
```

---

## Erros mais comuns e correções

| Erro | Causa | Correção |
|---|---|---|
| `Cannot find module 'genkit/beta'` | Agents API ainda em beta | `npm i genkit@latest` e importar de `genkit/beta` |
| Sessão perdida entre deploys | `InMemorySessionStore` em uso | Trocar por Firestore store |
| Tool nunca chamada pelo modelo | Descrição da tool vaga | Adicionar exemplos explícitos em `description` |
| Respostas alucinadas / inventadas | RAG retorna docs irrelevantes | Aumentar `k`, revisar chunking, adicionar reranker |
| Timeout em tool calls | API externa sem timeout | Configurar `AbortSignal.timeout()` + fallback |
| PII vazando nas respostas | Output guardrail ausente | Aplicar `sanitizeOutput()` antes de retornar |
| Prompt injection bem-sucedido | System prompt sem defesa | Seguir padrão em `09-security-guardrails.md` |
| Evals falhando após mudança de modelo | Regressão de qualidade | Ajustar prompts ou reverter modelo |

---

## Próximos passos

Para um projeto do zero: comece por `01-setup.md`.
Para ver tudo conectado de uma vez: vá direto para `10-complete-example.md`.
