# 05 — Multi-Agent: Orquestração e Delegação

## Sumário
- [Quando usar multi-agent](#quando-usar-multi-agent)
- [Padrão Orquestrador + Especialistas](#padrão-orquestrador--especialistas)
- [Configuração com middleware `agents()`](#configuração-com-middleware-agents)
- [Agentes especializados por domínio](#agentes-especializados-por-domínio)
- [Delegação com handoff de contexto](#delegação-com-handoff-de-contexto)
- [Subagente em background (tarefas longas)](#subagente-em-background-tarefas-longas)
- [Roteamento semântico](#roteamento-semântico)

---

## Quando usar multi-agent

| Cenário | Usar multi-agent? |
|---|---|
| Assistente único com 5–10 tools | ❌ — um agente único basta |
| Domínios muito diferentes (RH, TI, Financeiro) | ✅ — especialistas por domínio |
| Tarefas longas que rodam em background | ✅ — subagente background |
| Precisão alta por domínio (prompts especializados) | ✅ — especialistas |
| Pipeline com etapas sequenciais | Considere `ai.defineFlow()` em vez disso |

---

## Padrão Orquestrador + Especialistas

```
Usuário
  │
  ▼
┌──────────────────────────────┐
│   Agente Orquestrador        │  ← rota para o especialista certo
│   (classificação + handoff)  │
└──────┬───────────────────────┘
       │
  ┌────┼────────────────┐
  ▼    ▼                ▼
┌──┐ ┌────┐          ┌────┐
│HR│ │ TI │   ...    │Fin │   ← agentes especializados
└──┘ └────┘          └────┘
  │    │                │
  └────┴────────────────┘
            │
       Resposta final
         ao usuário
```

---

## Configuração com middleware `agents()`

```typescript
// src/agents/orchestrator.ts
import { agents } from 'genkit/beta';
import { ai } from '../index';
import { hrAgent }      from './hr';
import { itAgent }      from './it';
import { financeAgent } from './finance';
import { searchKnowledgeBase } from '../tools/rag';

export const orchestratorAgent = ai.defineAgent({
  name: 'institutional-orchestrator',
  system: `Você é o assistente principal da Empresa XYZ.

Sua função é entender a necessidade do funcionário e:
1. Responder diretamente questões gerais usando a base de conhecimento
2. Delegar para especialistas quando necessário:
   - RH: férias, benefícios, contratação, demissão, treinamentos, ponto
   - TI: acesso, sistemas, equipamentos, suporte técnico, senhas
   - Financeiro: reembolsos, adiantamentos, notas fiscais, fornecedores

Sempre confirme ao usuário qual especialista está sendo acionado.`,

  tools: [searchKnowledgeBase],

  // Middleware que registra os subagentes como ferramentas de delegação
  use: [
    agents([hrAgent, itAgent, financeAgent], {
      // Descrição do conjunto de agentes para o orchestrador
      description: 'Especialistas para questões específicas de RH, TI e Financeiro',
    }),
  ],

  sessionStore: createFirestoreSessionStore(),
});
```

---

## Agentes especializados por domínio

```typescript
// src/agents/hr.ts
import { ai } from '../index';
import { searchKnowledgeBase } from '../tools/rag';
import { queryEmployeeData }   from '../tools/database';
import { createSupportTicket } from '../tools/tickets';
import { requestHumanApproval } from '../tools/approval';

export const hrAgent = ai.defineAgent({
  name: 'hr-specialist',
  system: `Você é o especialista de Recursos Humanos da Empresa XYZ.

Domínio de atuação:
- Consulta e gestão de férias, banco de horas e folgas
- Benefícios: plano de saúde, vale refeição, vale transporte
- Treinamentos e desenvolvimento profissional
- Abertura de processos de contratação ou desligamento
- Políticas de RH e legislação trabalhista

Regras:
- Sempre consulte a base de conhecimento para confirmar políticas atuais
- Ações que alteram dados (solicitação de férias, mudanças cadastrais) requerem aprovação
- Para solicitações não resolvidas, abra um ticket de suporte no JIRA`,

  tools: [
    searchKnowledgeBase,
    queryEmployeeData,
    createSupportTicket,
    requestHumanApproval,
  ],

  // HR usa modelo mais capaz para questões trabalhistas complexas
  model: 'googleai/gemini-pro-latest',
});
```

```typescript
// src/agents/it.ts
export const itAgent = ai.defineAgent({
  name: 'it-specialist',
  system: `Você é o especialista de TI da Empresa XYZ.

Domínio de atuação:
- Acesso a sistemas, VPN, e-mail corporativo
- Suporte a hardware e software
- Redefinição de senhas e MFA
- Solicitação de equipamentos
- Incidentes de segurança

Regras:
- Nunca forneça credenciais ou senhas diretamente
- Problemas de segurança devem ser escalados imediatamente
- Sempre abra um ticket para registrar o atendimento`,

  tools: [
    searchKnowledgeBase,
    createSupportTicket,
    // tools de ITSM, ex: ServiceNow, Jira Service Management
    checkSystemStatus,
    resetUserPassword,
  ],

  model: 'googleai/gemini-flash-latest',
});
```

---

## Delegação com handoff de contexto

Ao delegar, passe contexto relevante para o subagente não precisar repetir perguntas:

```typescript
// src/agents/orchestrator.ts — sistema prompt com instrução de handoff
system: `Ao delegar para um especialista, inclua no handoff:
1. O que o usuário quer (reformulado de forma clara)
2. O que já foi tentado ou respondido
3. Dados do funcionário relevantes (departamento, cargo)
4. Urgência indicada pelo usuário

Exemplo de handoff correto:
"Encaminhando para o especialista de RH: o funcionário João Silva (Engenharia) quer solicitar
15 dias de férias a partir de 01/03/2025. Ele já verificou que tem saldo disponível.
Urgência: normal."`
```

---

## Subagente em background (tarefas longas)

Para tarefas que levam segundos/minutos (gerar relatório, enviar e-mails em lote):

```typescript
// src/agents/report-generator.ts
import { background } from 'genkit/beta';

export const reportGeneratorAgent = ai.defineAgent({
  name: 'report-generator',
  system: 'Você gera relatórios detalhados de RH, financeiro e operacional.',
  tools: [queryDatabase, generatePDF, sendNotification],
});

// Tool no orquestrador que dispara o relatório em background
export const generateReport = ai.defineTool(
  {
    name: 'generateReport',
    description:
      'Gera relatório analítico em background. Use quando o usuário pedir relatórios ' +
      'que levam mais de 30 segundos para processar.',
    inputSchema: z.object({
      reportType: z.enum(['hr-monthly', 'finance-quarterly', 'headcount']),
      period: z.string().describe('Período no formato YYYY-MM'),
      deliverTo: z.string().email(),
    }),
    outputSchema: z.object({
      jobId: z.string(),
      estimatedMinutes: z.number(),
    }),
  },
  async ({ reportType, period, deliverTo }) => {
    // Disparar tarefa em background — não bloqueia o chat
    const job = await background.run(reportGeneratorAgent, {
      input: { reportType, period, deliverTo },
      sessionId: `report-${Date.now()}`,
    });

    return {
      jobId: job.id,
      estimatedMinutes: 5,
    };
  }
);

// Polling do status do job
app.get('/report-status/:jobId', async (req, res) => {
  const status = await background.status(req.params.jobId);
  res.json(status);
});
```

---

## Roteamento semântico

Para organizações com muitos domínios, adicione uma etapa de classificação antes do orquestrador:

```typescript
// src/lib/router.ts — classifica intenção antes de rotear
const RouteResult = z.object({
  domain: z.enum(['hr', 'it', 'finance', 'general', 'unknown']),
  confidence: z.number().min(0).max(1),
  reasoning: z.string(),
});

export const semanticRouter = ai.defineFlow(
  {
    name: 'semanticRouter',
    inputSchema: z.object({ message: z.string() }),
    outputSchema: RouteResult,
  },
  async ({ message }) => {
    const { output } = await ai.generate({
      prompt: `Classifique a mensagem abaixo em um dos domínios:
- hr: Recursos Humanos (férias, benefícios, treinamentos, admissão, demissão)
- it: Tecnologia da Informação (sistemas, acesso, equipamentos, senha)
- finance: Financeiro (reembolso, adiantamento, nota fiscal, fornecedor)
- general: Questões gerais sobre a empresa, políticas, procedimentos
- unknown: Não se aplica ou fora do escopo

Mensagem: "${message}"

Responda APENAS com JSON no formato { "domain": "...", "confidence": 0.0, "reasoning": "..." }`,
      output: { schema: RouteResult },
    });

    return output!;
  }
);

// Uso no servidor — roteia antes de chamar o agente principal
app.post('/chat', requireAuth, async (req, res) => {
  const { message } = req.body;
  const route = await semanticRouter({ message });

  // Baixa confiança → sempre vai para o orquestrador
  if (route.confidence < 0.7 || route.domain === 'general') {
    const chat = await orchestratorAgent.loadChat(req.userId!);
    return res.json({ text: (await chat.send(message)).text });
  }

  // Alta confiança → vai direto para o especialista (menor latência)
  const specialistMap = { hr: hrAgent, it: itAgent, finance: financeAgent };
  const specialist = specialistMap[route.domain as keyof typeof specialistMap];
  if (specialist) {
    const chat = await specialist.loadChat(req.userId!);
    return res.json({ text: (await chat.send(message)).text, routed: route.domain });
  }

  const chat = await orchestratorAgent.loadChat(req.userId!);
  res.json({ text: (await chat.send(message)).text });
});
```

---

## Checklist multi-agent

- [ ] Orquestrador tem system prompt que explica claramente quando delegar
- [ ] Cada especialista tem system prompt focado apenas no seu domínio
- [ ] Handoff inclui contexto suficiente (não repete perguntas ao usuário)
- [ ] Background execution configurada para tarefas longas
- [ ] Roteador semântico testado com queries reais de cada domínio
- [ ] Fallback para orquestrador quando confiança do roteador < 70%
- [ ] Session store compartilhada entre agentes (mesmo `sessionId` = mesmo histórico)
