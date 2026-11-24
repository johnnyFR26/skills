# 02 — RAG e Base de Conhecimento Institucional

## Sumário
- [Visão geral da pipeline RAG](#visão-geral-da-pipeline-rag)
- [Estratégias de chunking](#estratégias-de-chunking)
- [Configuração do Vector Store](#configuração-do-vector-store)
- [Flow de indexação](#flow-de-indexação)
- [Retriever na tool do agente](#retriever-na-tool-do-agente)
- [Retrieval avançado com reranking](#retrieval-avançado-com-reranking)
- [Metadados e filtros](#metadados-e-filtros)
- [Estratégias por tipo de conteúdo](#estratégias-por-tipo-de-conteúdo)

---

## Visão geral da pipeline RAG

```
 Documentos brutos
      │
      ▼
 ┌─────────────┐    chunk()     ┌──────────────┐
 │  Extração   │───────────────▶│  Chunks de   │
 │  de texto   │                │  texto       │
 └─────────────┘                └──────┬───────┘
                                       │  embed()
                                       ▼
                               ┌──────────────┐
                               │  Embeddings  │──▶ Vector DB (Pinecone, Firestore…)
                               └──────────────┘

 Consulta do usuário
      │
      ▼
 embed(query) ──▶ similaritySearch(k=5) ──▶ [docs relevantes] ──▶ LLM
```

---

## Estratégias de chunking

### Chunking por sentença (documentos de política/RH)
```typescript
// src/lib/chunking.ts
export const policyChunkingConfig = {
  minLength: 800,
  maxLength: 1500,
  splitter: 'sentence',   // respeita fronteiras de frase
  overlap: 150,            // garante contexto entre chunks vizinhos
  delimiters: '',
};
```

### Chunking por parágrafo (manuais técnicos)
```typescript
export const manualChunkingConfig = {
  minLength: 500,
  maxLength: 2000,
  splitter: 'paragraph',
  overlap: 200,
};
```

### Chunking hierárquico (melhor recall)
Indexe em dois níveis: resumo (parent) + chunk detalhado (child).
Na recuperação, busque no nível child e retorne o parent inteiro para o LLM.

```typescript
// Estratégia parent-child chunk
async function indexWithParentChild(text: string, metadata: Record<string, string>) {
  // Nível 1 — resumo amplo (parent)
  const parentChunks = chunk(text, { minLength: 2000, maxLength: 4000, splitter: 'paragraph', overlap: 0 });

  // Nível 2 — chunks pequenos para busca precisa (child)
  const childChunks: Document[] = [];
  for (let pIdx = 0; pIdx < parentChunks.length; pIdx++) {
    const children = chunk(parentChunks[pIdx], { minLength: 300, maxLength: 800, splitter: 'sentence', overlap: 50 });
    children.forEach((c) =>
      childChunks.push(Document.fromText(c, { ...metadata, parentIndex: String(pIdx), parent: parentChunks[pIdx] }))
    );
  }

  await ai.index({ indexer: institutionalIndexer, documents: childChunks });
}
```

---

## Configuração do Vector Store

### Desenvolvimento — Dev Local Vector Store
```typescript
// src/lib/vector-store.ts
import { devLocalVectorstore, devLocalIndexerRef, devLocalRetrieverRef } from '@genkit-ai/dev-local-vectorstore';
import { googleAI } from '@genkit-ai/google-genai';

export const vectorStorePlugins = [
  googleAI(),  // fornece o embedder
  devLocalVectorstore([
    {
      indexName: 'institutional-kb',
      embedder: googleAI.embedder('gemini-embedding-001'),
    },
  ]),
];

export const institutionalIndexer   = devLocalIndexerRef('institutional-kb');
export const institutionalRetriever = devLocalRetrieverRef('institutional-kb');
```

### Produção — Pinecone
```typescript
import { pinecone } from '@genkit-ai/pinecone';

export const vectorStorePlugins = [
  googleAI(),
  pinecone([
    {
      indexId: 'institutional-kb',
      embedder: googleAI.embedder('gemini-embedding-001'),
    },
  ]),
];
```

### Produção — Firestore Vector Search
```typescript
import { firebase, firestoreVectorstore } from '@genkit-ai/firebase';

export const vectorStorePlugins = [
  googleAI(),
  firebase(),
  firestoreVectorstore([
    {
      indexId: 'institutional-kb',
      collection: 'knowledge_chunks',
      embedder: googleAI.embedder('gemini-embedding-001'),
      vectorSize: 768,  // dimensão do gemini-embedding-001
    },
  ]),
];
```

---

## Flow de indexação

```typescript
// src/flows/indexer.ts
import { z } from 'genkit';
import { ai } from '../index';
import { institutionalIndexer } from '../lib/vector-store';
import { Document } from 'genkit/retriever';
import { chunk } from 'llm-chunk';
import pdf from 'pdf-parse';
import fs from 'fs/promises';
import path from 'path';

const SUPPORTED_EXTENSIONS = ['.pdf', '.md', '.txt'];

// Schema de entrada — suporte a arquivo único ou pasta inteira
const IndexInput = z.object({
  source: z.string().describe('Caminho de arquivo ou diretório'),
  department: z.string().optional().describe('Departamento dono do documento'),
  tags: z.array(z.string()).optional().describe('Tags para filtro posterior'),
  replaceExisting: z.boolean().default(false),
});

export const indexDocuments = ai.defineFlow(
  {
    name: 'indexDocuments',
    inputSchema: IndexInput,
    outputSchema: z.object({
      success: z.boolean(),
      filesProcessed: z.number(),
      chunksIndexed: z.number(),
      errors: z.array(z.string()),
    }),
  },
  async ({ source, department, tags, replaceExisting }) => {
    const errors: string[] = [];
    let filesProcessed = 0;
    let chunksIndexed = 0;

    // Resolver arquivos a processar
    const stat = await fs.stat(source);
    const files = stat.isDirectory()
      ? (await fs.readdir(source))
          .filter((f) => SUPPORTED_EXTENSIONS.includes(path.extname(f).toLowerCase()))
          .map((f) => path.join(source, f))
      : [source];

    for (const filePath of files) {
      try {
        const text = await extractText(filePath);
        const fileChunks = chunk(text, {
          minLength: 800,
          maxLength: 1800,
          splitter: 'sentence',
          overlap: 150,
        });

        const documents = fileChunks.map((content, idx) =>
          Document.fromText(content, {
            source: path.basename(filePath),
            filePath,
            chunkIndex: String(idx),
            department: department ?? 'geral',
            tags: JSON.stringify(tags ?? []),
            indexedAt: new Date().toISOString(),
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

async function extractText(filePath: string): Promise<string> {
  const ext = path.extname(filePath).toLowerCase();
  const buffer = await fs.readFile(filePath);

  if (ext === '.pdf') {
    const data = await pdf(buffer);
    return data.text;
  }
  return buffer.toString('utf-8');
}
```

---

## Retriever na tool do agente

```typescript
// src/tools/rag.ts
import { z } from 'genkit';
import { ai } from '../index';
import { institutionalRetriever } from '../lib/vector-store';

export const searchKnowledgeBase = ai.defineTool(
  {
    name: 'searchKnowledgeBase',
    description:
      'Busca documentos institucionais: políticas, procedimentos, normas, FAQs, manuais e ' +
      'regulamentos da empresa. Use SEMPRE antes de responder questões sobre regras internas, ' +
      'benefícios, processos ou procedimentos.',
    inputSchema: z.object({
      query: z.string().describe('Pergunta ou termos de busca em linguagem natural'),
      department: z.string().optional().describe('Filtrar por departamento (RH, Financeiro, TI…)'),
      k: z.number().default(4).describe('Número de documentos a recuperar'),
    }),
    outputSchema: z.object({
      results: z.array(
        z.object({
          content: z.string(),
          source: z.string(),
          department: z.string(),
          relevanceNote: z.string().optional(),
        })
      ),
      found: z.boolean(),
    }),
  },
  async ({ query, department, k }) => {
    const docs = await ai.retrieve({
      retriever: institutionalRetriever,
      query,
      options: { k, where: department ? { department } : undefined },
    });

    if (!docs || docs.length === 0) {
      return { results: [], found: false };
    }

    return {
      results: docs.map((doc) => ({
        content: doc.text,
        source: String(doc.metadata?.source ?? 'desconhecido'),
        department: String(doc.metadata?.department ?? 'geral'),
      })),
      found: true,
    };
  }
);
```

---

## Retrieval avançado com reranking

Use reranking quando a precisão importa mais que a latência (ex: compliance, jurídico).

```typescript
// src/lib/advanced-retriever.ts
import { ai } from '../index';
import { institutionalRetriever } from './vector-store';
import { z } from 'genkit';
import { CommonRetrieverOptionsSchema } from 'genkit/retriever';

const AdvancedOptionsSchema = CommonRetrieverOptionsSchema.extend({
  preRerankK: z.number().default(20),
  department: z.string().optional(),
});

export const advancedInstitutionalRetriever = ai.defineRetriever(
  {
    name: 'institutional/advanced',
    configSchema: AdvancedOptionsSchema,
  },
  async (query, options) => {
    // 1. Busca ampla com k alto
    const broadDocs = await ai.retrieve({
      retriever: institutionalRetriever,
      query,
      options: {
        k: options.preRerankK,
        where: options.department ? { department: options.department } : undefined,
      },
    });

    // 2. Reranking semântico (Vertex AI ou custom)
    const reranked = await ai.rerank({
      reranker: 'vertexai/semantic-ranker-512',
      query: { content: query.text },
      documents: broadDocs.map((d) => ({ content: d.text, metadata: d.metadata })),
    });

    // 3. Retorna top-k após reranking
    const finalK = options.k ?? 4;
    return {
      documents: reranked.slice(0, finalK).map((r) => ({
        text: r.content,
        metadata: r.metadata,
      })),
    };
  }
);
```

---

## Metadados e filtros

Projete metadados no momento da indexação para permitir filtros na recuperação:

```typescript
// Metadados recomendados para base de conhecimento institucional
const metadata = {
  source: 'politica-ferias-2024.pdf',       // nome do arquivo
  filePath: '/docs/rh/politica-ferias.pdf', // caminho completo
  department: 'rh',                          // departamento
  documentType: 'policy',                    // policy | faq | manual | norm
  validFrom: '2024-01-01',                   // vigência (filtrar docs desatualizados)
  validUntil: '2025-12-31',
  tags: JSON.stringify(['férias', 'benefícios', 'licença']),
  language: 'pt-BR',
  chunkIndex: '0',
  indexedAt: new Date().toISOString(),
};
```

**Uso no retrieval com filtros:**
```typescript
const docs = await ai.retrieve({
  retriever: institutionalRetriever,
  query: 'quantos dias de férias tenho direito',
  options: {
    k: 5,
    where: {
      department: 'rh',
      documentType: 'policy',
    },
  },
});
```

---

## Estratégias por tipo de conteúdo

| Tipo de documento | Chunking recomendado | Chunk size | Overlap |
|---|---|---|---|
| Políticas / Normas | `sentence` | 1000–1800 chars | 150 |
| FAQs | 1 Q&A por chunk | — | 0 |
| Manuais técnicos | `paragraph` | 800–2000 chars | 200 |
| Tabelas / dados | 1 linha por chunk + header | — | 0 |
| E-mails / comunicados | `sentence` | 500–1000 chars | 100 |

**FAQ indexing — 1 par Q&A por chunk:**
```typescript
// Para FAQ, pré-processe antes de indexar
function parseFaqChunks(faqText: string): Document[] {
  const qaPairs = faqText.split(/\n\n(?=P:|Q:)/); // separador de Q&A
  return qaPairs.map((pair) =>
    Document.fromText(pair, { documentType: 'faq', source: 'faq-geral.md' })
  );
}
```

---

## Checklist de base de conhecimento

- [ ] Documentos limpos (sem headers/footers repetidos, sem scans não-OCR)
- [ ] Metadados ricos definidos (department, type, validFrom, validUntil)
- [ ] Chunking testado — chunks não cortam frases no meio
- [ ] Indexador em produção usa vector store persistente (não `devLocal`)
- [ ] `searchKnowledgeBase` tool testada no Dev UI com queries reais
- [ ] Pipeline de re-indexação quando documentos são atualizados
- [ ] Docs desatualizados têm `validUntil` para filtro automático
