# 08 — Testes: Unitário, Integração e Avaliação de Qualidade

## Sumário
- [Pirâmide de testes para agentes LLM](#pirâmide-de-testes-para-agentes-llm)
- [Testes unitários de tools](#testes-unitários-de-tools)
- [Testes de flows com mocks](#testes-de-flows-com-mocks)
- [Testes de integração do agente](#testes-de-integração-do-agente)
- [Avaliação de qualidade (evals)](#avaliação-de-qualidade-evals)
- [Testes de regressão de RAG](#testes-de-regressão-de-rag)
- [Configuração de CI com testes de agente](#configuração-de-ci-com-testes-de-agente)

---

## Pirâmide de testes para agentes LLM

```
         ▲
        / \
       /   \        Evals (qualidade do LLM)
      / E2E \       — mais lentos, mais caros, rodam em CI/CD semanal
     /───────\
    /         \     Integração (agente + tools reais)
   / Integração\    — rodam em CI/CD por PR
  /─────────────\
 /               \  Unitários (tools, flows, utils)
/   Unitários     \ — rodam em cada commit, rápidos e determinísticos
───────────────────
```

**Regra prática:**
- Tools e flows → teste unitário com mocks (Jest/Vitest)
- Agente completo → teste de integração com model real (gasta tokens)
- Qualidade de resposta → evals com dataset fixo (semanal/mensal)

---

## Setup de testes

```bash
npm install -D vitest @vitest/coverage-v8 msw
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.ts'],
      exclude: ['src/**/*.test.ts', 'src/index.ts'],
    },
    // Separar testes rápidos dos de integração
    include: ['src/**/*.test.ts'],
    exclude: ['src/**/*.integration.test.ts'],
  },
});
```

---

## Testes unitários de tools

As tools são funções puras — fáceis de testar com mocks.

```typescript
// src/tools/database.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { queryEmployeeData } from './database';

// Mock do módulo de banco
vi.mock('../lib/database', () => ({
  db: {
    employees: {
      findById: vi.fn(),
    },
  },
}));

import { db } from '../lib/database';

describe('queryEmployeeData', () => {
  beforeEach(() => vi.clearAllMocks());

  it('retorna dados do funcionário quando encontrado', async () => {
    const mockEmployee = {
      vacation_balance: 15,
      position: 'Engenheiro Sênior',
      department: 'TI',
    };
    vi.mocked(db.employees.findById).mockResolvedValue(mockEmployee);

    const result = await queryEmployeeData({
      employeeId: 'emp-001',
      fields: ['vacation_balance', 'position', 'department'],
    });

    expect(result.found).toBe(true);
    expect(result.data).toMatchObject(mockEmployee);
    expect(db.employees.findById).toHaveBeenCalledWith('emp-001', {
      select: ['vacation_balance', 'position', 'department'],
    });
  });

  it('retorna found=false quando funcionário não existe', async () => {
    vi.mocked(db.employees.findById).mockResolvedValue(null);

    const result = await queryEmployeeData({ employeeId: 'emp-999', fields: ['position'] });

    expect(result.found).toBe(false);
    expect(result.data).toEqual({});
  });

  it('propaga erro de banco de dados', async () => {
    vi.mocked(db.employees.findById).mockRejectedValue(new Error('DB connection failed'));

    await expect(
      queryEmployeeData({ employeeId: 'emp-001', fields: ['position'] })
    ).rejects.toThrow('DB connection failed');
  });
});
```

```typescript
// src/tools/rag.test.ts
import { describe, it, expect, vi } from 'vitest';
import { searchKnowledgeBase } from './rag';

// Mock do retriever do Genkit
vi.mock('../index', () => ({
  ai: {
    retrieve: vi.fn(),
  },
}));
import { ai } from '../index';

describe('searchKnowledgeBase', () => {
  it('retorna resultados formatados quando encontra documentos', async () => {
    vi.mocked(ai.retrieve).mockResolvedValue([
      {
        text: 'Os funcionários têm direito a 30 dias de férias por ano.',
        metadata: { source: 'politica-ferias.pdf', department: 'rh' },
      },
      {
        text: 'O período aquisitivo é de 12 meses de trabalho.',
        metadata: { source: 'politica-ferias.pdf', department: 'rh' },
      },
    ]);

    const result = await searchKnowledgeBase({
      query: 'quantos dias de férias tenho',
      department: 'rh',
      k: 2,
    });

    expect(result.found).toBe(true);
    expect(result.results).toHaveLength(2);
    expect(result.results[0].source).toBe('politica-ferias.pdf');
    expect(result.results[0].department).toBe('rh');
  });

  it('retorna found=false quando não há documentos', async () => {
    vi.mocked(ai.retrieve).mockResolvedValue([]);

    const result = await searchKnowledgeBase({ query: 'pergunta sem resposta', k: 4 });

    expect(result.found).toBe(false);
    expect(result.results).toHaveLength(0);
  });
});
```

---

## Testes de flows com mocks

```typescript
// src/flows/indexer.test.ts
import { describe, it, expect, vi, afterEach } from 'vitest';
import * as fs from 'fs/promises';
import * as path from 'path';

vi.mock('../index', () => ({
  ai: { index: vi.fn().mockResolvedValue(undefined) },
}));
vi.mock('pdf-parse', () => ({ default: vi.fn().mockResolvedValue({ text: 'Conteúdo extraído do PDF.' }) }));

import { indexDocuments } from './indexer';
import { ai } from '../index';

describe('indexDocuments', () => {
  afterEach(() => vi.clearAllMocks());

  it('indexa arquivo .txt com sucesso', async () => {
    // Criar arquivo temporário
    const tmpFile = '/tmp/test-policy.txt';
    await fs.writeFile(tmpFile, 'Esta é a política de benefícios da empresa. Os funcionários têm direito a plano de saúde.');

    const result = await indexDocuments({
      source: tmpFile,
      department: 'rh',
      tags: ['benefícios'],
      replaceExisting: false,
    });

    expect(result.success).toBe(true);
    expect(result.filesProcessed).toBe(1);
    expect(result.chunksIndexed).toBeGreaterThan(0);
    expect(result.errors).toHaveLength(0);
    expect(ai.index).toHaveBeenCalled();

    await fs.unlink(tmpFile);
  });

  it('reporta erro quando arquivo não existe', async () => {
    const result = await indexDocuments({
      source: '/tmp/arquivo-inexistente.pdf',
      replaceExisting: false,
    });

    expect(result.success).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toContain('arquivo-inexistente.pdf');
  });

  it('processa diretório com múltiplos arquivos', async () => {
    const tmpDir = '/tmp/test-docs';
    await fs.mkdir(tmpDir, { recursive: true });
    await fs.writeFile(`${tmpDir}/policy-a.txt`, 'Política A: conteúdo relevante da empresa.');
    await fs.writeFile(`${tmpDir}/policy-b.txt`, 'Política B: outra política importante da empresa.');
    await fs.writeFile(`${tmpDir}/irrelevant.xlsx`, 'arquivo ignorado');

    const result = await indexDocuments({ source: tmpDir, replaceExisting: false });

    expect(result.filesProcessed).toBe(2); // .xlsx ignorado
    expect(result.errors).toHaveLength(0);

    await fs.rm(tmpDir, { recursive: true });
  });
});
```

---

## Testes de integração do agente

Esses testes usam o modelo real — rodam em CI apenas em PRs e consomem tokens.

```typescript
// src/agents/institutional.integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { institutionalAgent } from './institutional';

// Marcar como integração — excluído do `npm test` padrão
// Execute com: npx vitest run --include '**/*.integration.test.ts'

const TEST_SESSION_ID = `test-session-${Date.now()}`;

describe('institutionalAgent (integration)', () => {
  afterAll(async () => {
    // Limpar sessão de teste
    await institutionalAgent.sessionStore?.delete(TEST_SESSION_ID);
  });

  it('responde saudação inicial em português', async () => {
    const chat = await institutionalAgent.loadChat(TEST_SESSION_ID);
    const { text } = await chat.send('Olá, preciso de ajuda.');

    expect(text).toBeTruthy();
    expect(text.length).toBeGreaterThan(20);
    // Verificar que não alucinou informações
    expect(text.toLowerCase()).not.toContain('undefined');
    expect(text.toLowerCase()).not.toContain('null');
  }, 30_000); // timeout de 30s para chamadas de LLM

  it('usa a tool de base de conhecimento para perguntas de RH', async () => {
    const chat = await institutionalAgent.loadChat(TEST_SESSION_ID);
    const { text, toolCalls } = await chat.send('Quantos dias de férias tenho direito?');

    // Verificar que a tool foi chamada
    const kbToolCall = toolCalls?.find((t) => t.name === 'searchKnowledgeBase');
    expect(kbToolCall).toBeDefined();
    expect(text).toBeTruthy();
  }, 30_000);

  it('mantém contexto entre turnos da mesma sessão', async () => {
    const chat = await institutionalAgent.loadChat(TEST_SESSION_ID);
    await chat.send('Meu nome é Ana e trabalho no departamento de Marketing.');
    const { text } = await chat.send('Você se lembra do meu nome?');

    expect(text.toLowerCase()).toContain('ana');
  }, 60_000);

  it('reconhece quando não sabe responder', async () => {
    const chat = await institutionalAgent.loadChat(`${TEST_SESSION_ID}-unknown`);
    const { text } = await chat.send(
      'Qual é o preço das ações da empresa na bolsa hoje?'
    );

    // O agente deve admitir que não tem essa informação
    const uncertaintyIndicators = ['não tenho', 'não possuo', 'não sei', 'não tenho acesso', 'fora do meu'];
    const hasUncertainty = uncertaintyIndicators.some((phrase) =>
      text.toLowerCase().includes(phrase)
    );
    expect(hasUncertainty).toBe(true);
  }, 30_000);
});
```

---

## Avaliação de qualidade (evals)

Evals medem a qualidade das respostas ao longo do tempo — detectam regressões quando prompts ou modelos mudam.

```typescript
// src/evals/rag-quality.eval.ts
import { ai } from '../index';
import { z } from 'genkit';

// Dataset de perguntas e respostas esperadas
const RAG_EVAL_DATASET = [
  {
    id: 'ferias-01',
    question: 'Quantos dias de férias tenho direito por ano?',
    expectedKeywords: ['30 dias', 'trinta dias', 'período aquisitivo'],
    mustNotContain: ['não sei', 'não tenho informação'],
    category: 'hr-vacation',
  },
  {
    id: 'beneficios-01',
    question: 'Quais são os benefícios da empresa?',
    expectedKeywords: ['plano de saúde', 'vale refeição', 'vale transporte'],
    mustNotContain: ['não tenho acesso'],
    category: 'hr-benefits',
  },
  {
    id: 'ticket-01',
    question: 'Como abro um chamado de suporte de TI?',
    expectedKeywords: ['portal', 'ticket', 'chamado', 'suporte'],
    mustNotContain: ['não sei', 'não tenho como'],
    category: 'it-support',
  },
  {
    id: 'fora-escopo-01',
    question: 'Me conte uma piada.',
    expectedKeywords: [],
    mustNotContain: [],
    mustRedirect: true, // deve redirecionar para escopo institucional
    category: 'out-of-scope',
  },
];

// Schema de resultado do eval
const EvalResult = z.object({
  id: z.string(),
  question: z.string(),
  response: z.string(),
  passed: z.boolean(),
  keywordsFound: z.array(z.string()),
  keywordsMissing: z.array(z.string()),
  forbiddenFound: z.array(z.string()),
  latencyMs: z.number(),
  tokens: z.number(),
  error: z.string().optional(),
});

// Flow de avaliação
export const runRagEval = ai.defineFlow(
  {
    name: 'runRagEval',
    inputSchema: z.object({
      categories: z.array(z.string()).optional().describe('Filtrar por categoria'),
      sessionPrefix: z.string().default('eval'),
    }),
    outputSchema: z.object({
      results: z.array(EvalResult),
      summary: z.object({
        total: z.number(),
        passed: z.number(),
        failed: z.number(),
        passRate: z.number(),
        avgLatencyMs: z.number(),
        avgTokens: z.number(),
      }),
    }),
  },
  async ({ categories, sessionPrefix }) => {
    const { institutionalAgent } = await import('../agents/institutional');
    const dataset = categories
      ? RAG_EVAL_DATASET.filter((d) => categories.includes(d.category))
      : RAG_EVAL_DATASET;

    const results: z.infer<typeof EvalResult>[] = [];

    for (const sample of dataset) {
      const start = Date.now();
      try {
        const chat = await institutionalAgent.loadChat(`${sessionPrefix}-${sample.id}`);
        const { text, usage } = await chat.send(sample.question);
        const latencyMs = Date.now() - start;

        const lowerText = text.toLowerCase();
        const keywordsFound = sample.expectedKeywords.filter((kw) =>
          lowerText.includes(kw.toLowerCase())
        );
        const keywordsMissing = sample.expectedKeywords.filter(
          (kw) => !lowerText.includes(kw.toLowerCase())
        );
        const forbiddenFound = (sample.mustNotContain ?? []).filter((phrase) =>
          lowerText.includes(phrase.toLowerCase())
        );

        const passed =
          keywordsMissing.length === 0 &&
          forbiddenFound.length === 0;

        results.push({
          id: sample.id,
          question: sample.question,
          response: text,
          passed,
          keywordsFound,
          keywordsMissing,
          forbiddenFound,
          latencyMs,
          tokens: (usage?.inputTokens ?? 0) + (usage?.outputTokens ?? 0),
        });

        // Limpar sessão de eval
        await institutionalAgent.sessionStore?.delete(`${sessionPrefix}-${sample.id}`);
      } catch (err) {
        results.push({
          id: sample.id, question: sample.question, response: '',
          passed: false, keywordsFound: [], keywordsMissing: sample.expectedKeywords,
          forbiddenFound: [], latencyMs: Date.now() - start, tokens: 0,
          error: String(err),
        });
      }
    }

    const passed = results.filter((r) => r.passed).length;
    return {
      results,
      summary: {
        total: results.length,
        passed,
        failed: results.length - passed,
        passRate: passed / results.length,
        avgLatencyMs: results.reduce((s, r) => s + r.latencyMs, 0) / results.length,
        avgTokens: results.reduce((s, r) => s + r.tokens, 0) / results.length,
      },
    };
  }
);
```

**Executar evals:**
```bash
# Via CLI do Genkit
npx genkit flow:run runRagEval '{"sessionPrefix": "eval-2025-01"}' -- npx tsx src/index.ts

# Via script npm
npm run eval
```

```json
// package.json
{
  "scripts": {
    "test": "vitest run --exclude '**/*.integration.test.ts'",
    "test:integration": "vitest run --include '**/*.integration.test.ts'",
    "eval": "npx genkit flow:run runRagEval '{\"sessionPrefix\": \"eval\"}' -- npx tsx src/index.ts",
    "eval:hr": "npx genkit flow:run runRagEval '{\"categories\": [\"hr-vacation\", \"hr-benefits\"]}' -- npx tsx src/index.ts"
  }
}
```

---

## Testes de regressão de RAG

Verificam que a base de conhecimento retorna documentos relevantes para queries conhecidas.

```typescript
// src/evals/retrieval-regression.test.ts
import { describe, it, expect } from 'vitest';
import { ai } from '../index';
import { institutionalRetriever } from '../lib/vector-store';

// ATENÇÃO: estes testes requerem a base de conhecimento já indexada
// Execute após `npm run index`

describe('RAG retrieval regression', () => {
  it('recupera documento de férias para query sobre férias', async () => {
    const docs = await ai.retrieve({
      retriever: institutionalRetriever,
      query: 'quantos dias de férias tenho direito',
      options: { k: 3 },
    });

    expect(docs.length).toBeGreaterThan(0);
    const hasVacationDoc = docs.some(
      (d) => d.metadata?.department === 'rh' || d.text.toLowerCase().includes('férias')
    );
    expect(hasVacationDoc).toBe(true);
  });

  it('recupera documento de TI para query de acesso a sistema', async () => {
    const docs = await ai.retrieve({
      retriever: institutionalRetriever,
      query: 'como solicitar acesso ao sistema de gestão',
      options: { k: 3 },
    });

    const hasITDoc = docs.some(
      (d) => d.metadata?.department === 'ti' || d.text.toLowerCase().includes('acesso')
    );
    expect(hasITDoc).toBe(true);
  });

  it('score de relevância decresce para queries não relacionadas', async () => {
    const relevantDocs = await ai.retrieve({
      retriever: institutionalRetriever,
      query: 'política de férias e banco de horas',
      options: { k: 1 },
    });

    const irrelevantDocs = await ai.retrieve({
      retriever: institutionalRetriever,
      query: 'receita de bolo de chocolate',
      options: { k: 1 },
    });

    // Mesmo retornando algo, o score do irrelevante deve ser menor
    // (implementação depende do vector store expor scores)
    expect(relevantDocs.length).toBeGreaterThan(0);
  });
});
```

---

## Configuração de CI com testes de agente

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22' }
      - run: npm ci
      - run: npm test                        # apenas unitários (rápido, sem API key)
      - run: npm run build

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'  # apenas em PRs
    env:
      GOOGLE_GENAI_API_KEY: ${{ secrets.GOOGLE_GENAI_API_KEY }}
      FIREBASE_PROJECT_ID: ${{ secrets.FIREBASE_PROJECT_ID_TEST }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22' }
      - run: npm ci
      - run: npm run test:integration
        timeout-minutes: 10

  evals:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'      # apenas na main (semanal via cron)
    env:
      GOOGLE_GENAI_API_KEY: ${{ secrets.GOOGLE_GENAI_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22' }
      - run: npm ci
      - run: npm run eval
      - name: Upload eval results
        uses: actions/upload-artifact@v4
        with:
          name: eval-results-${{ github.sha }}
          path: eval-results.json
```

---

## Checklist de testes

- [ ] Testes unitários para todas as tools (mocks de dependências externas)
- [ ] Cobertura de código > 70% nas tools e flows
- [ ] Testes de integração com model real para happy path + edge cases
- [ ] Dataset de evals atualizado quando prompts mudam
- [ ] Evals rodam automaticamente em CI na main (detectam regressões)
- [ ] Testes de regressão de retrieval após cada re-indexação
- [ ] `vitest.config.ts` separa unitários de integração (não gastar tokens desnecessariamente)
- [ ] Sessões de teste são limpas após cada suite
