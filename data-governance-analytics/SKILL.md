---
name: data-governance-analytics
description: "Governança e análise de dados para desenvolvimento data-driven. Use quando: projetar métricas e KPIs; criar dashboards e analytics; definir estratégia de dados; auditar qualidade de dados; implementar pipelines de análise; tomar decisões orientadas por dados; analisar padrões em atendimentos, usuários ou eventos; otimizar features com base em dados; definir data contracts; revisar implementações analíticas."
argument-hint: "Descreva o contexto: qual dado analisar, qual decisão tomar, ou qual problema de qualidade resolver"
---

# Data Governance & Analytics

Skill para governança de dados e desenvolvimento orientado por dados (D3 — Data-Driven Development). Cobre desde a definição de métricas até a implementação de pipelines analíticos e dashboards.

## Quando Usar

- Projetar ou revisar métricas e KPIs de negócio
- Criar ou refatorar dashboards e componentes de analytics
- Auditar qualidade, consistência e integridade de dados
- Definir estratégias de coleta, transformação e visualização
- Tomar decisões de produto/feature com base em evidências
- Implementar filtros temporais, agregações e análises de tendência
- Avaliar se uma implementação respeita os princípios de dados

---

## Procedimento Principal

### 1. Diagnóstico de Contexto

Antes de qualquer análise, responda:

1. **Qual é a pergunta de negócio?** (ex: "Qual atendente tem mais atendimentos?")
2. **Quais dados estão disponíveis?** (entidades, campos, granularidade)
3. **Qual é o nível de confiança dos dados?** (dados brutos vs. processados)
4. **Quem consome essa análise?** (dev, gestor, cliente final)

Consulte [./references/diagnostic-questions.md](./references/diagnostic-questions.md) para o checklist completo.

---

### 2. Definição de Métricas (Metric Design)

Aplique o framework **SMART + Dimensionalidade**:

```
Métrica = { nome, fórmula, granularidade, dimensões, frequência_de_atualização }
```

| Tipo         | Exemplo                                | Quando Usar                       |
|--------------|----------------------------------------|-----------------------------------|
| **Contagem** | Total de atendimentos                  | Volume e frequência               |
| **Razão**    | Atendimentos por atendente             | Eficiência e distribuição         |
| **Tendência**| Variação % semana a semana             | Crescimento e sazonalidade        |
| **Funil**    | Taxa de conversão por etapa            | Jornada e drop-off                |
| **Coorte**   | Retenção de clientes por mês de início | Comportamento ao longo do tempo   |

Consulte [./references/metric-design.md](./references/metric-design.md) para templates de definição.

---

### 3. Auditoria de Qualidade de Dados (DQA)

Execute o ciclo **VCAT**:

- **V**alidade — os valores estão dentro dos domínios esperados?
- **C**ompletude — há campos nulos ou registros faltantes?
- **A**tualidade — os dados estão dentro da janela temporal correta?
- **T**raçabilidade — é possível rastrear a origem e transformação?

Checklist rápido para qualquer dataset ou endpoint:

```
[ ] Campos obrigatórios nunca nulos
[ ] Datas em formato consistente (ISO 8601)
[ ] IDs externos mapeados corretamente
[ ] Ausência de duplicatas por chave primária
[ ] Agregações somam ao total esperado (sanity check)
[ ] Timezone padronizado (UTC ou local documentado)
```

---

### 4. Design de Pipeline Analítico

Siga o padrão **ETC (Extract → Transform → Consume)**:

```
[Fonte de Dados] → Extract → Transform → Store → Consume
                                  ↓
                          [Validações DQA]
```

**Boas práticas de implementação:**

- Filtros temporais aplicados na **fonte** (server-side), não no cliente
- Agregações pesadas em backend; frontend apenas renderiza
- Paginação e limites explícitos em todas as queries analíticas
- Cache de resultados para períodos históricos estáveis
- Tipagem estrita das entidades de dados (interfaces TypeScript)

Consulte [./references/pipeline-patterns.md](./references/pipeline-patterns.md) para exemplos por stack.

---

### 5. Implementação de Dashboard/Componente Analítico

Siga a checklist antes de considerar qualquer componente analytics completo:

```
[ ] Filtros de período funcionam server-side
[ ] Loading states implementados
[ ] Estados vazios (zero data) tratados graciosamente
[ ] Tooltips com contexto suficiente (valor + dimensão + unidade)
[ ] Cores acessíveis (WCAG AA) e com legenda explícita
[ ] Dados normalizados antes de renderizar (trim, lowercase, etc.)
[ ] Títulos e labels em linguagem de negócio, não técnica
[ ] Responsividade (mobile e desktop)
[ ] Sem lógica de transformação no JSX/template
```

Consulte [./references/dashboard-checklist.md](./references/dashboard-checklist.md) para o checklist expandido.

---

### 6. Data-Driven Decision Framework (D3F)

Antes de tomar qualquer decisão baseada em dados:

1. **Hipótese**: Formule a hipótese de negócio explicitamente
2. **Baseline**: Qual é o comportamento atual (linha de base)?
3. **Evidência**: Que dado confirma ou refuta a hipótese?
4. **Confiança**: O volume de dados é estatisticamente representativo?
5. **Ação**: Qual mudança concreta os dados suportam?
6. **Acompanhamento**: Qual métrica monitora o impacto pós-mudança?

> Regra: uma decisão baseada em dados precisa ter **hipótese explícita + evidência quantitativa + critério de sucesso**.

Consulte [./references/d3-decision-template.md](./references/d3-decision-template.md) para o template de decisão.

---

### 7. Data Contracts

Ao expor ou consumir dados entre serviços:

```typescript
// Exemplo de Data Contract explícito
interface AttendanceAnalyticsContract {
  period: {
    from: string; // ISO 8601, UTC
    to: string;   // ISO 8601, UTC
  };
  aggregation: 'daily' | 'weekly' | 'monthly';
  filters: {
    attendeeIds?: number[];
    reasonIds?: number[];
  };
  response: {
    total: number;
    items: AttendanceMetric[];
    generatedAt: string; // ISO 8601
  };
}
```

Princípios:
- Versione contratos explicitamente (`/v1/analytics/...`)
- Nunca altere campos existentes; adicione novos opcionais
- Documente unidades e timezone em todos os campos temporais
- Valide entrada e saída nos limites do sistema

---

## Anti-padrões a Evitar

| Anti-padrão                        | Problema                                      | Solução                                    |
|------------------------------------|-----------------------------------------------|---------------------------------------------|
| Filtros temporais client-side      | Performance e inconsistência                  | Filtrar na query/API                        |
| Métricas sem definição formal      | Ambiguidade e discordância                    | Documento de definição de métricas          |
| Dashboard sem estado vazio         | UX quebrada com zero dados                    | Componente de empty state                   |
| Nomes técnicos em labels de gráfico| Incompreensão pelo usuário final              | Usar linguagem de negócio                   |
| Dados brutos no frontend           | Duplicação de lógica e inconsistência         | Transformar no backend ou em hooks dedicados|
| Timezone implícito                 | Erros sutis e difíceis de debugar             | Documentar e padronizar explicitamente      |
| Decisão por anedota                | Viés de confirmação                           | Exigir dados quantitativos e hipótese formal|

---

## Recursos Adicionais

- [Diagnostic Questions](./references/diagnostic-questions.md)
- [Metric Design Templates](./references/metric-design.md)
- [Pipeline Patterns](./references/pipeline-patterns.md)
- [Dashboard Checklist](./references/dashboard-checklist.md)
- [D3 Decision Template](./references/d3-decision-template.md)
- [Data Contract Examples](./references/data-contracts.md)
