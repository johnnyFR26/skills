# 01 — Setup e Configuração

## Instalação

```bash
# Dependências core
npm install genkit @genkit-ai/google-genai zod

# Se usar Claude (Anthropic) como modelo
npm install @genkit-ai/anthropic

# Se usar Vertex AI (produção Google Cloud)
npm install @genkit-ai/vertexai

# Session stores prontos para produção
npm install @genkit-ai/firebase    # Firestore
npm install ioredis                # Redis (store customizado)

# Utilitários para RAG
npm install llm-chunk pdf-parse @genkit-ai/dev-local-vectorstore
npm install --save-dev @types/pdf-parse

# Dev tools
npm install -D tsx typescript @types/node genkit-cli
```

## Configuração TypeScript (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "lib",
    "rootDir": "src",
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "lib"]
}
```

## Estrutura de pastas recomendada

```
my-institutional-agent/
├── src/
│   ├── index.ts              ← instância global do Genkit + exports
│   ├── server.ts             ← servidor HTTP (Express/Fastify)
│   ├── agents/
│   │   ├── institutional.ts  ← agente principal
│   │   ├── hr.ts             ← subagente de RH
│   │   └── finance.ts        ← subagente financeiro
│   ├── tools/
│   │   ├── rag.ts            ← searchKnowledgeBase tool
│   │   ├── database.ts       ← queryDatabase tool
│   │   ├── tickets.ts        ← createTicket tool
│   │   └── approval.ts       ← approveAction tool (interrupt)
│   ├── flows/
│   │   ├── indexer.ts        ← fluxo de indexação de documentos
│   │   └── onboarding.ts     ← fluxo de onboarding de novo usuário
│   ├── prompts/
│   │   ├── institutional.prompt   ← dotprompt file
│   │   └── hr-specialist.prompt
│   └── lib/
│       ├── session-store.ts  ← configuração do session store
│       └── vector-store.ts   ← configuração do vector store
├── docs/                     ← documentos a indexar (PDFs, MDs)
├── .env.local
├── package.json
└── tsconfig.json
```

## Instância global do Genkit (`src/index.ts`)

```typescript
import { genkit } from 'genkit/beta';
import { googleAI } from '@genkit-ai/google-genai';

// Instância singleton — importada por todos os módulos
export const ai = genkit({
  plugins: [
    googleAI({
      apiKey: process.env.GOOGLE_GENAI_API_KEY,
    }),
  ],
  // Modelo padrão — pode ser sobrescrito por agente/flow
  model: googleAI.model('gemini-flash-latest'),
});
```

## Configuração com múltiplos provedores

```typescript
// src/index.ts — setup multi-provider (produção)
import { genkit } from 'genkit/beta';
import { googleAI }  from '@genkit-ai/google-genai';
import { anthropic } from '@genkit-ai/anthropic';
import { vertexAI }  from '@genkit-ai/vertexai';

export const ai = genkit({
  plugins: [
    // Google AI (dev) ou Vertex AI (prod)
    process.env.NODE_ENV === 'production'
      ? vertexAI({ projectId: process.env.GCP_PROJECT_ID, location: 'us-central1' })
      : googleAI({ apiKey: process.env.GOOGLE_GENAI_API_KEY }),

    // Anthropic Claude como alternativa
    anthropic({ apiKey: process.env.ANTHROPIC_API_KEY }),
  ],

  // Modelo padrão configurável via variável de ambiente
  model: process.env.DEFAULT_MODEL ?? 'googleai/gemini-flash-latest',
});
```

## Servidor HTTP com Express (`src/server.ts`)

```typescript
import express from 'express';
import { institutionalAgent } from './agents/institutional';

const app = express();
app.use(express.json());

// Rota de chat — recebe mensagem, retorna resposta do agente
app.post('/chat', async (req, res) => {
  const { sessionId, message } = req.body as {
    sessionId: string;
    message: string;
  };

  try {
    const chat = await institutionalAgent.loadChat(sessionId);
    const response = await chat.send(message);
    res.json({ text: response.text, sessionId });
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

// Health check
app.get('/health', (_req, res) => res.json({ status: 'ok' }));

const PORT = process.env.PORT ?? 8080;
app.listen(PORT, () => console.log(`Agent server listening on :${PORT}`));
```

## `package.json` — scripts

```json
{
  "scripts": {
    "dev":   "npx genkit start -- npx tsx --watch src/index.ts",
    "build": "tsc",
    "start": "node lib/server.js",
    "index": "npx tsx src/flows/indexer.ts",
    "lint":  "eslint src --ext .ts"
  }
}
```

## Validação da instalação

```bash
# Iniciar Dev UI — acesse http://localhost:4000
npm run dev

# Se aparecerem os agents/flows listados no Dev UI, o setup está correto.
# Teste enviando uma mensagem diretamente no Dev UI antes de conectar o frontend.
```

## Checklist de setup

- [ ] `GOOGLE_GENAI_API_KEY` ou `GOOGLE_APPLICATION_CREDENTIALS` configurado
- [ ] `genkit start` abre o Dev UI em `localhost:4000`
- [ ] Agente aparece na lista do Dev UI
- [ ] Consegue enviar mensagem e receber resposta no Dev UI
- [ ] Session store configurado (nunca use `InMemorySessionStore` em produção)
- [ ] Vector store configurado antes de indexar documentos
