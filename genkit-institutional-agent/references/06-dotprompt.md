# 06 — Dotprompt: Templates e Versionamento de Prompts

## Sumário
- [O que é Dotprompt](#o-que-é-dotprompt)
- [Estrutura de um arquivo .prompt](#estrutura-de-um-arquivo-prompt)
- [Variáveis e schemas no prompt](#variáveis-e-schemas-no-prompt)
- [Partials — componentes reutilizáveis](#partials--componentes-reutilizáveis)
- [Versionamento de prompts](#versionamento-de-prompts)
- [Testando prompts no Dev UI](#testando-prompts-no-dev-ui)
- [Usando prompts em agentes e flows](#usando-prompts-em-agentes-e-flows)

---

## O que é Dotprompt

Dotprompt é o sistema de templates de prompts do Genkit. Permite:
- Separar prompts do código TypeScript (arquivos `.prompt`)
- Definir schemas de entrada/saída diretamente no prompt
- Reutilizar blocos de texto com partials
- Testar e versionar prompts independente do código
- Validar inputs/outputs com Zod automaticamente

---

## Estrutura de um arquivo .prompt

```handlebars
---
# Metadados YAML no frontmatter
name: institutional-assistant
model: googleai/gemini-flash-latest
config:
  temperature: 0.3        # Baixa temperatura para respostas mais determinísticas
  maxOutputTokens: 1024

# Schema de entrada (Picoschema — subset de JSON Schema)
input:
  schema:
    employeeName: string, "Nome do funcionário"
    department: string, "Departamento do funcionário"
    language?: string, "Idioma preferido (padrão: pt-BR)"
    context?: string, "Contexto adicional da conversa"

# Schema de saída (opcional — ativa structured output)
output:
  schema:
    response: string, "Resposta ao funcionário"
    confidence: number, "Nível de confiança 0-1"
    requiresEscalation: boolean, "Se precisa de atendimento humano"
    sources?: string[], "Fontes consultadas"
---

Você é o assistente virtual da Empresa XYZ.

{{#if language}}Responda em {{language}}.{{else}}Responda em português do Brasil.{{/if}}

**Funcionário:** {{employeeName}} — {{department}}

{{#if context}}
**Contexto da conversa:**
{{context}}
{{/if}}

**Instruções:**
- Seja preciso e objetivo
- Use as ferramentas disponíveis para buscar informações atualizadas
- Sempre indique a fonte quando citar políticas ou procedimentos
- Se não tiver certeza, diga isso claramente e ofereça abrir um ticket
```

---

## Variáveis e schemas no prompt

### Picoschema — tipos suportados

```yaml
input:
  schema:
    # Tipos primitivos
    name: string               # string simples
    age: integer               # número inteiro
    score: number              # número decimal
    active: boolean            # booleano

    # Com descrição
    department: string, "Departamento do funcionário"

    # Opcional (sufixo ?)
    nickname?: string, "Apelido (opcional)"

    # Enum
    priority: "low" | "medium" | "high", "Prioridade do chamado"

    # Array
    tags(array, string): string[], "Lista de tags"

    # Objeto aninhado
    address:
      street: string
      city: string
      zip?: string
```

### Handlebars — lógica no template

```handlebars
{{! Comentário — não aparece no prompt gerado }}

{{! Variável simples }}
Olá, {{employeeName}}!

{{! Condicional }}
{{#if isManager}}
Você tem acesso ao painel gerencial.
{{else}}
Para acessar relatórios, entre em contato com seu gestor.
{{/if}}

{{! Loop }}
Documentos disponíveis:
{{#each documents}}
- {{this.title}} ({{this.type}})
{{/each}}

{{! Helper — capitalização }}
{{uppercase department}}

{{! Bloco com partial }}
{{> company-footer}}
```

---

## Partials — componentes reutilizáveis

```handlebars
{{! src/prompts/partials/company-footer.prompt }}
---
# Partial — sem name no frontmatter significa que é um partial
---
---
*Este assistente é fornecido pela Empresa XYZ.*
*Para atendimento humano: rh@empresa.com | ramal 1234*
*Em caso de emergência: 0800-000-0000*
```

```handlebars
{{! src/prompts/hr-specialist.prompt — usa o partial }}
---
name: hr-specialist
model: googleai/gemini-pro-latest
---
Você é o especialista de RH da Empresa XYZ.

[conteúdo do prompt...]

{{> company-footer}}
```

**Registrar e carregar partials no código:**
```typescript
// src/index.ts
import { genkit } from 'genkit/beta';
import { googleAI } from '@genkit-ai/google-genai';

export const ai = genkit({
  plugins: [googleAI()],
  promptDir: './src/prompts',      // Genkit descobre .prompt automaticamente
});
```

---

## Versionamento de prompts

```
src/prompts/
├── institutional.prompt            ← versão atual (produção)
├── institutional.v2.prompt         ← nova versão em teste A/B
├── hr-specialist.prompt
├── it-specialist.prompt
└── partials/
    └── company-footer.prompt
```

**Carregando versão específica:**
```typescript
// Versão padrão (produção)
const { output } = await ai.prompt('institutional')({ employeeName: 'Ana' });

// Versão experimental (A/B test)
const { output: v2Output } = await ai.prompt('institutional', { variant: 'v2' })({ employeeName: 'Ana' });
```

**A/B testing de prompts:**
```typescript
// src/lib/prompt-ab.ts
export async function runWithABTest(input: { employeeName: string; question: string }) {
  const variant = Math.random() < 0.2 ? 'v2' : undefined; // 20% vão para v2

  const prompt = await ai.prompt('institutional', variant ? { variant } : undefined);
  const { output } = await prompt(input);

  // Registrar qual variante foi usada para análise
  await analytics.track('prompt_variant', { variant: variant ?? 'default', employeeName: input.employeeName });

  return { output, variant: variant ?? 'default' };
}
```

---

## Testando prompts no Dev UI

No Dev UI (`localhost:4000`), você pode:

1. Ver todos os arquivos `.prompt` na lista
2. Preencher os campos de input diretamente na UI
3. Ver o prompt completo renderizado antes de enviar ao modelo
4. Comparar outputs entre variantes

**Executar prompt via CLI:**
```bash
# Testar prompt com input JSON
npx genkit prompt:run institutional '{"employeeName": "João", "department": "TI"}' -- npx tsx src/index.ts
```

---

## Usando prompts em agentes e flows

### Agente baseado em Dotprompt (`definePromptAgent`)

```typescript
// src/agents/hr-prompt-agent.ts
import { ai } from '../index';
import { searchKnowledgeBase, queryEmployeeData } from '../tools';

// definePromptAgent lê o arquivo hr-specialist.prompt automaticamente
export const hrPromptAgent = ai.definePromptAgent({
  name: 'hr-specialist',           // corresponde ao `name` no frontmatter
  promptFile: 'hr-specialist',     // nome do arquivo sem extensão
  tools: [searchKnowledgeBase, queryEmployeeData],
  sessionStore: createFirestoreSessionStore(),
});
```

### Flow que usa um prompt como etapa

```typescript
// src/flows/classify-intent.ts
export const classifyIntent = ai.defineFlow(
  {
    name: 'classifyIntent',
    inputSchema: z.object({ message: z.string() }),
    outputSchema: z.object({ domain: z.string(), confidence: z.number() }),
  },
  async ({ message }) => {
    // Carregar o prompt de classificação do arquivo
    const classifyPrompt = ai.prompt('intent-classifier');
    const { output } = await classifyPrompt({ message });
    return output!;
  }
);
```

```handlebars
{{! src/prompts/intent-classifier.prompt }}
---
name: intent-classifier
model: googleai/gemini-flash-latest
config:
  temperature: 0.1
input:
  schema:
    message: string, "Mensagem do usuário para classificar"
output:
  schema:
    domain: "hr" | "it" | "finance" | "general" | "unknown"
    confidence: number, "Confiança 0-1"
    reasoning: string, "Explicação da classificação"
---
Classifique a mensagem abaixo no domínio mais adequado:

- hr: Recursos Humanos (férias, benefícios, treinamentos, contratos de trabalho)
- it: TI (sistemas, acesso, equipamentos, senha, suporte técnico)
- finance: Financeiro (reembolso, adiantamento, nota fiscal, fornecedor, compras)
- general: Questões gerais, políticas da empresa, procedimentos
- unknown: Fora do escopo ou não identificado

Mensagem: "{{message}}"

Seja criterioso. Apenas classifique como "hr", "it" ou "finance" quando houver clara relação com esses domínios.
```

---

## Checklist Dotprompt

- [ ] Arquivos `.prompt` em `src/prompts/` com `promptDir` configurado
- [ ] Frontmatter YAML válido (name, model, config, input/output schema)
- [ ] Partials para texto repetido (footer, disclaimers, instruções padrão)
- [ ] Versões em teste com sufixo `.v2.prompt` etc.
- [ ] Prompts testados no Dev UI com inputs reais
- [ ] `temperature` baixa (0.1–0.4) para respostas factuais e determinísticas
- [ ] `temperature` alta (0.7–1.0) apenas para respostas criativas ou sugestões
