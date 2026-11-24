# 07 — Deploy e Observabilidade em Produção

## Sumário
- [Checklist pré-deploy](#checklist-pré-deploy)
- [Deploy no Cloud Run](#deploy-no-cloud-run)
- [Deploy no Firebase Functions](#deploy-no-firebase-functions)
- [Configuração de autenticação e autorização](#configuração-de-autenticação-e-autorização)
- [Observabilidade com OpenTelemetry](#observabilidade-com-opentelemetry)
- [Logs estruturados para auditoria](#logs-estruturados-para-auditoria)
- [Métricas e alertas](#métricas-e-alertas)
- [Estratégia de rollback](#estratégia-de-rollback)

---

## Checklist pré-deploy

- [ ] `InMemorySessionStore` substituído por Firestore ou Redis
- [ ] `devLocalVectorstore` substituído por Pinecone, Firestore ou pgvector
- [ ] Variáveis de ambiente em Secret Manager (nunca hardcoded)
- [ ] `GENKIT_ENV=prod` configurado
- [ ] `LOG_LEVEL=info` (nunca `debug` em produção — expõe dados sensíveis)
- [ ] Rate limiting configurado na camada HTTP
- [ ] Autenticação JWT validada em todos os endpoints
- [ ] Health check endpoint (`/health`) implementado
- [ ] `maxOutputTokens` configurado para evitar respostas gigantescas
- [ ] Tool timeouts configurados (evitar hanging requests)
- [ ] Testes de integração passando localmente

---

## Deploy no Cloud Run

### `Dockerfile`

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS production
WORKDIR /app
COPY --from=builder /app/lib ./lib
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
COPY --from=builder /app/src/prompts ./src/prompts  # dotprompt files

ENV NODE_ENV=production
ENV PORT=8080
EXPOSE 8080
CMD ["node", "lib/server.js"]
```

### `cloudbuild.yaml` — CI/CD automatizado

```yaml
steps:
  # 1. Testes
  - name: 'node:22'
    entrypoint: npm
    args: ['test']

  # 2. Build da imagem
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agents/institutional-agent:$COMMIT_SHA'
      - '.'

  # 3. Push para Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agents/institutional-agent:$COMMIT_SHA'

  # 4. Deploy no Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'institutional-agent'
      - '--image=us-central1-docker.pkg.dev/$PROJECT_ID/agents/institutional-agent:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--memory=2Gi'
      - '--cpu=2'
      - '--concurrency=80'
      - '--min-instances=1'           # nunca escalar para zero (latência)
      - '--max-instances=10'
      - '--set-secrets=GOOGLE_GENAI_API_KEY=genai-api-key:latest'
      - '--set-secrets=FIREBASE_PROJECT_ID=firebase-project:latest'
      - '--no-allow-unauthenticated'  # autenticação obrigatória
```

### Configurar secrets no Secret Manager

```bash
# Criar secrets
echo -n "sua-api-key" | gcloud secrets create genai-api-key --data-file=-
echo -n "meu-projeto" | gcloud secrets create firebase-project --data-file=-

# Conceder acesso à conta de serviço do Cloud Run
gcloud secrets add-iam-policy-binding genai-api-key \
  --member="serviceAccount:CLOUD_RUN_SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Deploy no Firebase Functions

```typescript
// src/firebase-functions.ts
import { onRequest } from 'firebase-functions/v2/https';
import { institutionalAgent } from './agents/institutional';

// Função HTTP para o agente
export const chatAgent = onRequest(
  {
    region: 'us-central1',
    memory: '2GiB',
    timeoutSeconds: 60,
    minInstances: 1,          // evita cold start
    secrets: ['GOOGLE_GENAI_API_KEY'],
    cors: ['https://meuapp.empresa.com'],
  },
  async (req, res) => {
    if (req.method !== 'POST') {
      return res.status(405).json({ error: 'Method not allowed' });
    }

    const { sessionId, message } = req.body;
    const chat = await institutionalAgent.loadChat(sessionId);
    const response = await chat.send(message);

    res.json({ text: response.text });
  }
);

// Flow de indexação como função agendada (re-indexação diária)
import { onSchedule } from 'firebase-functions/v2/scheduler';
export const dailyReindex = onSchedule(
  { schedule: '0 2 * * *', region: 'us-central1', memory: '4GiB', timeoutSeconds: 540 },
  async () => {
    const { indexDocuments } = await import('./flows/indexer');
    await indexDocuments({ source: './docs', replaceExisting: true });
  }
);
```

---

## Configuração de autenticação e autorização

```typescript
// src/middleware/auth.ts — middleware completo com RBAC
import { auth as firebaseAuth } from 'firebase-admin';

export interface AuthContext {
  userId: string;
  email: string;
  department: string;
  roles: string[];        // ['employee', 'manager', 'hr', 'admin']
}

export async function authenticateRequest(req: Request): Promise<AuthContext> {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) throw new Error('Missing authorization token');

  // Verificar token Firebase ou JWT customizado
  const decoded = await firebaseAuth().verifyIdToken(token);

  // Buscar claims customizados (roles, department) do token
  const { uid, email = '', department = 'unknown', roles = ['employee'] } = decoded as any;

  return { userId: uid, email, department, roles };
}

// Verificar permissão por papel
export function requireRole(allowedRoles: string[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const ctx = await authenticateRequest(req);
      if (!allowedRoles.some((r) => ctx.roles.includes(r))) {
        return res.status(403).json({ error: 'Insufficient permissions' });
      }
      (req as any).authContext = ctx;
      next();
    } catch (err) {
      res.status(401).json({ error: 'Authentication failed' });
    }
  };
}

// Uso:
app.post('/chat', requireRole(['employee', 'manager', 'admin']), chatHandler);
app.post('/admin/reindex', requireRole(['admin']), reindexHandler);
```

---

## Observabilidade com OpenTelemetry

```typescript
// src/lib/telemetry.ts — configuração de telemetria
import { NodeSDK } from '@opentelemetry/sdk-node';
import { Resource } from '@opentelemetry/resources';
import { TraceExporter } from '@google-cloud/opentelemetry-cloud-trace-exporter';
import { MetricExporter } from '@google-cloud/opentelemetry-cloud-monitoring-exporter';

const sdk = new NodeSDK({
  resource: new Resource({
    'service.name': 'institutional-agent',
    'service.version': process.env.npm_package_version ?? '0.0.0',
    environment: process.env.NODE_ENV ?? 'development',
  }),
  traceExporter: process.env.NODE_ENV === 'production'
    ? new TraceExporter()         // Google Cloud Trace
    : undefined,                   // local → Dev UI
  metricReader: process.env.NODE_ENV === 'production'
    ? new MetricExporter({ projectId: process.env.GCP_PROJECT_ID! })
    : undefined,
});

sdk.start();

// Garantir graceful shutdown
process.on('SIGTERM', () => sdk.shutdown().then(() => process.exit(0)));
```

**Plugin Google Cloud no Genkit:**
```typescript
// src/index.ts
import { googleCloud } from '@genkit-ai/google-cloud';

export const ai = genkit({
  plugins: [
    googleAI(),
    ...(process.env.NODE_ENV === 'production' ? [googleCloud()] : []),
  ],
});
```

---

## Logs estruturados para auditoria

```typescript
// src/lib/audit-logger.ts
import { logger } from 'genkit/logging';

export const auditLogger = {
  chatTurn: (data: {
    sessionId: string;
    userId: string;
    input: string;
    output: string;
    toolsUsed: string[];
    latencyMs: number;
    model: string;
    tokens: { input: number; output: number };
  }) => {
    logger.info('chat_turn', {
      ...data,
      timestamp: new Date().toISOString(),
      // Mascarar dados sensíveis antes de logar
      input: maskPII(data.input),
      output: maskPII(data.output),
    });
  },

  toolCall: (data: {
    sessionId: string;
    toolName: string;
    input: unknown;
    output: unknown;
    latencyMs: number;
    success: boolean;
    error?: string;
  }) => {
    logger.info('tool_call', {
      ...data,
      timestamp: new Date().toISOString(),
    });
  },

  interrupt: (data: {
    sessionId: string;
    type: string;
    approver?: string;
    approved?: boolean;
  }) => {
    logger.warn('human_interrupt', {
      ...data,
      timestamp: new Date().toISOString(),
    });
  },
};

// Mascara básica de PII (CPF, e-mail, telefone)
function maskPII(text: string): string {
  return text
    .replace(/\d{3}\.\d{3}\.\d{3}-\d{2}/g, '***.***.***-**')   // CPF
    .replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '***@***.***')  // e-mail
    .replace(/\(\d{2}\)\s?\d{4,5}-\d{4}/g, '(**) *****-****');  // telefone
}
```

**Integrar auditLogger no servidor:**
```typescript
// src/server.ts
app.post('/chat', requireRole(['employee', 'manager']), async (req, res) => {
  const ctx = (req as any).authContext as AuthContext;
  const start = Date.now();
  const chat = await institutionalAgent.loadChat(ctx.userId);

  const response = await chat.send(req.body.message);

  auditLogger.chatTurn({
    sessionId: ctx.userId,
    userId: ctx.userId,
    input: req.body.message,
    output: response.text,
    toolsUsed: response.toolCalls?.map((t) => t.name) ?? [],
    latencyMs: Date.now() - start,
    model: response.usage?.model ?? 'unknown',
    tokens: {
      input: response.usage?.inputTokens ?? 0,
      output: response.usage?.outputTokens ?? 0,
    },
  });

  res.json({ text: response.text });
});
```

---

## Métricas e alertas

```typescript
// src/lib/metrics.ts — métricas customizadas via OpenTelemetry
import { metrics } from '@opentelemetry/api';

const meter = metrics.getMeter('institutional-agent');

export const agentMetrics = {
  chatTurns: meter.createCounter('agent.chat_turns', { description: 'Total de turnos de chat' }),
  toolCalls: meter.createCounter('agent.tool_calls', { description: 'Total de chamadas de tools' }),
  interrupts: meter.createCounter('agent.interrupts', { description: 'Total de interrupts (aprovações)' }),
  latency: meter.createHistogram('agent.latency_ms', {
    description: 'Latência de resposta em ms',
    unit: 'ms',
  }),
  tokenUsage: meter.createHistogram('agent.tokens', {
    description: 'Tokens consumidos por turno',
  }),
};

// Uso:
agentMetrics.chatTurns.add(1, { domain: 'hr', model: 'gemini-flash-latest' });
agentMetrics.latency.record(latencyMs, { domain: 'hr' });
```

**Alertas recomendados (Google Cloud Monitoring):**

| Métrica | Condição de alerta | Ação |
|---|---|---|
| `agent.latency_ms` p99 > 10s | Alerta crítico | Verificar tool calls lentas |
| Taxa de erro HTTP 5xx > 1% | Alerta crítico | Verificar logs, possível falha de API |
| `agent.tokens` médio > 3000/turno | Alerta de atenção | Revisar chunking e prompt size |
| `agent.interrupts` sem resolução > 1h | Alerta | Notificar gestores pendentes |
| Custo de modelo > limite diário | Alerta crítico | Ativar rate limiting |

---

## Estratégia de rollback

```bash
# Listar revisões do Cloud Run
gcloud run revisions list --service institutional-agent --region us-central1

# Reverter para revisão anterior (tráfego 100% para a revisão estável)
gcloud run services update-traffic institutional-agent \
  --region us-central1 \
  --to-revisions institutional-agent-00010-abc=100

# Deploy gradual (canary) — 10% para nova versão
gcloud run services update-traffic institutional-agent \
  --region us-central1 \
  --to-revisions \
    institutional-agent-00011-xyz=10,institutional-agent-00010-abc=90
```

**Health check endpoint:**
```typescript
app.get('/health', async (_req, res) => {
  const checks = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version,
    checks: {
      database: 'unknown',
      vectorStore: 'unknown',
      model: 'unknown',
    },
  };

  try {
    // Verificar conexão com Firestore
    await db.collection('health').doc('ping').get();
    checks.checks.database = 'ok';
  } catch { checks.checks.database = 'error'; checks.status = 'degraded'; }

  try {
    // Verificar modelo com chamada mínima
    await ai.generate({ prompt: 'ping', maxOutputTokens: 5 });
    checks.checks.model = 'ok';
  } catch { checks.checks.model = 'error'; checks.status = 'degraded'; }

  const statusCode = checks.status === 'ok' ? 200 : 503;
  res.status(statusCode).json(checks);
});
```

---

## Checklist de deploy

- [ ] Dockerfile otimizado (multi-stage build, imagem < 500MB)
- [ ] CI/CD configurado (Cloud Build ou GitHub Actions)
- [ ] Secrets em Secret Manager (nunca no código ou `.env` em produção)
- [ ] `minInstances: 1` para evitar cold start (paga sempre)
- [ ] Rate limiting configurado (ex: 100 req/min por IP)
- [ ] Health check respondendo antes de aceitar tráfego
- [ ] Alertas configurados para latência, erros e custo
- [ ] Logs de auditoria exportados para BigQuery ou Cloud Logging
- [ ] Estratégia de canary/rollback documentada e testada
- [ ] CORS configurado apenas para origens conhecidas
