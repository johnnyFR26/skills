# 03 — Controle de Sessão e Estado

## Sumário
- [Conceitos de sessão no Genkit](#conceitos-de-sessão-no-genkit)
- [Session Stores disponíveis](#session-stores-disponíveis)
- [Configuração do Firestore Store](#configuração-do-firestore-store)
- [Custom State — estado tipado por usuário](#custom-state--estado-tipado-por-usuário)
- [Padrão: sessão ligada ao usuário autenticado](#padrão-sessão-ligada-ao-usuário-autenticado)
- [Snapshots e branching](#snapshots-e-branching)
- [Gestão de janela de contexto](#gestão-de-janela-de-contexto)
- [Encerramento e limpeza de sessão](#encerramento-e-limpeza-de-sessão)

---

## Conceitos de sessão no Genkit

```
Session (ID único por usuário)
  │
  ├── Messages []          ← histórico completo de turnos
  ├── State {}             ← dados customizados (perfil, preferências…)
  └── Snapshots []         ← pontos de restauração (branching)
```

- **Session ID** = identificador opaco — use o `userId` da sua auth (ex: JWT `sub`).
- **Turn** = um par user→assistant. Cada `chat.send()` cria um turno.
- **Store** = backend que persiste sessões (Firestore, Redis, memória).
- O agente carrega o histórico automaticamente em cada turno — o LLM "lembra" da conversa.

---

## Session Stores disponíveis

| Store | Uso | Produção? |
|---|---|---|
| `InMemorySessionStore` | Testes locais | ❌ (volátil) |
| Firestore Store | GCP / Firebase | ✅ |
| Redis Store (custom) | Alta performance | ✅ |
| File Store (Dart/Python) | Prototipagem | ❌ |

> **Regra:** nunca use `InMemorySessionStore` em produção — sessões são perdidas a cada restart.

---

## Configuração do Firestore Store

```typescript
// src/lib/session-store.ts
import { getFirestore } from 'firebase-admin/firestore';
import { initializeApp, getApps } from 'firebase-admin/app';

// Inicializar Firebase Admin uma vez
if (!getApps().length) {
  initializeApp({ projectId: process.env.FIREBASE_PROJECT_ID });
}

// Store que usa a coleção 'agent_sessions' no Firestore
export function createFirestoreSessionStore<S = unknown>() {
  const db = getFirestore();
  return {
    async get(sessionId: string) {
      const doc = await db.collection('agent_sessions').doc(sessionId).get();
      return doc.exists ? (doc.data() as any) : null;
    },
    async set(sessionId: string, data: any) {
      await db.collection('agent_sessions').doc(sessionId).set(data, { merge: false });
    },
    async delete(sessionId: string) {
      await db.collection('agent_sessions').doc(sessionId).delete();
    },
  };
}
```

> **Alternativa pronta:** `@genkit-ai/firebase` já exporta `firestoreSessionStore()` — prefira-o se estiver usando o plugin Firebase.

---

## Custom State — estado tipado por usuário

Custom state permite guardar dados do usuário dentro da sessão (perfil, preferências, contexto).

```typescript
// src/agents/institutional.ts
import { z } from 'genkit';
import { ai } from '../index';
import { searchKnowledgeBase } from '../tools/rag';
import { createFirestoreSessionStore } from '../lib/session-store';

// Zod schema para o estado customizado da sessão
const UserSessionState = z.object({
  employeeId: z.string().optional(),
  department: z.string().optional(),
  language: z.string().default('pt-BR'),
  openTicketIds: z.array(z.string()).default([]),
  lastTopics: z.array(z.string()).default([]),       // tópicos recentes para contexto
  preferredName: z.string().optional(),
});
type UserSessionState = z.infer<typeof UserSessionState>;

export const institutionalAgent = ai.defineAgent({
  name: 'institutional-assistant',
  system: `Você é o assistente virtual da Empresa XYZ.
Você tem acesso ao perfil do funcionário e pode personalizar suas respostas.
Sempre use as ferramentas disponíveis antes de responder sobre políticas internas.`,
  tools: [searchKnowledgeBase],
  stateSchema: UserSessionState,
  sessionStore: createFirestoreSessionStore<UserSessionState>(),
});
```

**Lendo e atualizando o estado durante o chat:**
```typescript
// src/server.ts — endpoint de chat com atualização de estado
app.post('/chat', async (req, res) => {
  const { userId, message, employeeProfile } = req.body;

  // Carregar sessão existente ou criar nova
  const chat = await institutionalAgent.loadChat(userId, {
    // Estado inicial no primeiro acesso
    initialState: {
      employeeId: employeeProfile?.id,
      department: employeeProfile?.department,
      preferredName: employeeProfile?.firstName,
      language: 'pt-BR',
      openTicketIds: [],
      lastTopics: [],
    },
  });

  // Envia mensagem — o agente pode chamar tools que atualizam o state
  const response = await chat.send(message);

  // Ler estado atualizado após o turno
  const state = chat.state;
  console.log('Tópicos discutidos:', state?.lastTopics);

  res.json({
    text: response.text,
    sessionId: userId,
    state,
  });
});
```

**Atualizando estado dentro de uma tool:**
```typescript
// src/tools/tickets.ts — tool que salva ID do ticket no state
export const createSupportTicket = ai.defineTool(
  {
    name: 'createSupportTicket',
    description: 'Cria um ticket de suporte para o funcionário',
    inputSchema: z.object({
      title: z.string(),
      description: z.string(),
      priority: z.enum(['low', 'medium', 'high']),
    }),
    outputSchema: z.object({ ticketId: z.string(), url: z.string() }),
  },
  async ({ title, description, priority }, { session }) => {
    const ticket = await ticketingAPI.create({ title, description, priority });

    // Atualizar estado da sessão com o novo ticket
    if (session) {
      const current = session.state ?? {};
      await session.updateState({
        ...current,
        openTicketIds: [...(current.openTicketIds ?? []), ticket.id],
      });
    }

    return { ticketId: ticket.id, url: ticket.url };
  }
);
```

---

## Padrão: sessão ligada ao usuário autenticado

```typescript
// src/middleware/auth.ts
import jwt from 'jsonwebtoken';
import { Request, Response, NextFunction } from 'express';

export interface AuthRequest extends Request {
  userId?: string;
  userDepartment?: string;
}

export function requireAuth(req: AuthRequest, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'Token required' });

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as {
      sub: string;
      department: string;
    };
    req.userId = payload.sub;           // ← vira o sessionId
    req.userDepartment = payload.department;
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
}
```

```typescript
// src/server.ts
import { requireAuth, AuthRequest } from './middleware/auth';

app.post('/chat', requireAuth, async (req: AuthRequest, res) => {
  const { message } = req.body;
  const sessionId = req.userId!;  // sessionId = userId do JWT

  const chat = await institutionalAgent.loadChat(sessionId, {
    initialState: {
      department: req.userDepartment,
      language: 'pt-BR',
      openTicketIds: [],
      lastTopics: [],
    },
  });

  const { text } = await chat.send(message);
  res.json({ text, sessionId });
});
```

---

## Snapshots e branching

Snapshots permitem salvar um ponto no histórico e restaurar ou criar branches.

```typescript
// Criar snapshot antes de operação crítica
const snapshot = await chat.snapshot();

// Tentar operação arriscada
try {
  await chat.send('Cancelar todas as férias do departamento');
} catch (err) {
  // Restaurar para o ponto seguro se algo der errado
  await chat.restore(snapshot);
}
```

**Branching — explorar caminhos alternativos:**
```typescript
const baseSnapshot = await chat.snapshot();

// Branch A — resposta formal
const chatA = await institutionalAgent.loadChat(`${sessionId}-branch-a`);
await chatA.restore(baseSnapshot);
const resA = await chatA.send('Responda de forma formal e detalhada');

// Branch B — resposta resumida
const chatB = await institutionalAgent.loadChat(`${sessionId}-branch-b`);
await chatB.restore(baseSnapshot);
const resB = await chatB.send('Responda de forma resumida e informal');

// Apresentar opções ao usuário e continuar com a escolhida
```

---

## Gestão de janela de contexto

Modelos têm limite de tokens. Históricos longos podem exceder o limite.

```typescript
// Estratégia 1: janela deslizante — mantém apenas N turnos recentes
const institutionalAgent = ai.defineAgent({
  name: 'institutional-assistant',
  system: '...',
  tools: [...],
  // Mantém apenas os últimos 20 turnos no contexto enviado ao modelo
  maxTurns: 20,
  sessionStore: createFirestoreSessionStore(),
});
```

```typescript
// Estratégia 2: sumarização periódica — condensa histórico antigo
const summarizeHistory = ai.defineTool(
  {
    name: 'summarizeCurrentContext',
    description: 'Resumir o histórico da conversa quando ficar muito longo',
    inputSchema: z.object({}),
    outputSchema: z.object({ summary: z.string() }),
  },
  async (_, { session }) => {
    const history = session?.messages ?? [];
    if (history.length < 30) return { summary: 'Histórico ainda curto' };

    const { text } = await ai.generate({
      prompt: `Resuma os pontos principais desta conversa em até 300 palavras:\n\n${
        history.map((m) => `${m.role}: ${m.text}`).join('\n')
      }`,
    });

    // Salvar resumo no state e limpar histórico
    await session?.updateState({ ...session.state, historySummary: text });
    return { summary: text };
  }
);
```

---

## Encerramento e limpeza de sessão

```typescript
// Encerrar sessão ao logout
app.delete('/session', requireAuth, async (req: AuthRequest, res) => {
  const sessionId = req.userId!;
  await institutionalAgent.sessionStore?.delete(sessionId);
  res.json({ success: true });
});

// Limpeza automática de sessões expiradas (cron job / Cloud Scheduler)
export const cleanupExpiredSessions = ai.defineFlow(
  {
    name: 'cleanupExpiredSessions',
    inputSchema: z.object({ maxAgeHours: z.number().default(72) }),
    outputSchema: z.object({ deleted: z.number() }),
  },
  async ({ maxAgeHours }) => {
    const db = getFirestore();
    const cutoff = new Date(Date.now() - maxAgeHours * 60 * 60 * 1000);
    const snapshot = await db
      .collection('agent_sessions')
      .where('updatedAt', '<', cutoff)
      .get();

    const batch = db.batch();
    snapshot.docs.forEach((doc) => batch.delete(doc.ref));
    await batch.commit();

    return { deleted: snapshot.size };
  }
);
```

---

## Checklist de sessão

- [ ] `sessionStore` configurado com Firestore (nunca `InMemorySessionStore` em produção)
- [ ] `sessionId` derivado do `userId` autenticado (JWT `sub`)
- [ ] `stateSchema` definido com Zod para estado customizado
- [ ] Estado inicial populado com perfil do usuário no primeiro acesso
- [ ] `maxTurns` configurado para controlar contexto enviado ao modelo
- [ ] Rota de logout deleta a sessão do store
- [ ] Cron job de limpeza de sessões expiradas configurado
