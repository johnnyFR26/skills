# D3 Decision Template — Data-Driven Decision Framework

Use este template para documentar e estruturar qualquer decisão orientada por dados.

---

## Template de Decisão

```markdown
## Decisão: [Título da Decisão]

**Data:** YYYY-MM-DD
**Responsável:** [Nome / Time]
**Status:** [ ] Rascunho  [ ] Em análise  [ ] Aprovada  [ ] Implementada

---

### 1. Contexto
Descreva brevemente o problema ou oportunidade que motivou essa análise.

### 2. Hipótese
> "Acreditamos que [ação/mudança] vai resultar em [resultado esperado]
> porque [evidência ou raciocínio de suporte]."

### 3. Baseline
| Métrica | Valor Atual | Período de Referência | Fonte |
|---------|------------|----------------------|-------|
| [métrica] | [valor] | [período] | [endpoint/tabela] |

### 4. Evidência

**Dados coletados:**
- [Métrica 1]: [valor] — [interpretação]
- [Métrica 2]: [valor] — [interpretação]

**Visualizações:**
- [ ] Gráfico de tendência temporal
- [ ] Distribuição por dimensão relevante
- [ ] Comparativo de segmentos

**Confiança estatística:**
- Volume de dados: [n registros]
- Período analisado: [de → até]
- Representatividade: [% do total ou sazonalidade considerada]

### 5. Análise

**A hipótese é suportada pelos dados?**
[ ] Sim, fortemente  [ ] Sim, parcialmente  [ ] Não  [ ] Inconclusivo

**Alternativas consideradas:**
1. [Alternativa A] — descartada porque [motivo]
2. [Alternativa B] — mantida como backup

### 6. Decisão

**Ação escolhida:** [descrição clara da ação]

**Impacto esperado:**
- [Métrica de sucesso 1]: de [X] para [Y] em [prazo]
- [Métrica de sucesso 2]: de [X] para [Y] em [prazo]

**Riscos identificados:**
- [Risco]: [mitigação]

### 7. Acompanhamento

**Métricas de acompanhamento pós-implementação:**
| Métrica | Baseline | Meta | Prazo de avaliação |
|---------|----------|------|--------------------|
| [métrica] | [valor] | [meta] | [data] |

**Critério de rollback:** se [condição] → reverter porque [impacto]

**Revisão agendada:** [data]
```

---

## Escala de Confiança

| Nível | Volume de dados | Recomendação |
|-------|----------------|--------------|
| Alto | > 500 eventos no período | Decidir com confiança |
| Médio | 100–500 eventos | Decidir com ressalva, monitorar de perto |
| Baixo | < 100 eventos | Coletar mais dados antes de decidir |
| Insuficiente | < 30 eventos | Não decidir com base nesses dados |

---

## Armadilhas de Decisão por Dados

| Viés | Descrição | Como Evitar |
|------|-----------|-------------|
| Confirmação | Buscar dados que confirmam a crença prévia | Definir hipótese ANTES de olhar os dados |
| Sobretaxação | Agir sobre variações normais (ruído) | Verificar se a diferença é > 10% do baseline |
| Correlação como causalidade | Assumir que correlação implica causa | Identificar variável de confusão possível |
| Período não representativo | Analisar período atípico (feriados, eventos) | Ampliar janela ou excluir período explicitamente |
| Seleção de amostra | Filtro que exclui parte relevante da população | Documentar todos os filtros aplicados |

---

## Exemplos de Hipóteses Bem Formuladas

✅ **Boa hipótese:**
> "Acreditamos que atendentes com mais de 50 atendimentos/mês têm taxa de motivos ausentes maior que 15%, porque estão sobrecarregados. Isso nos levaria a redistribuir carga de trabalho."

❌ **Hipótese vaga:**
> "Queremos ver como estão indo os atendentes."

✅ **Boa hipótese:**
> "Acreditamos que o motivo 'Dúvida sobre produto' representa mais de 30% dos atendimentos, o que justifica criar uma seção de FAQ para reduzir volume."

❌ **Hipótese vaga:**
> "Vamos ver quais motivos aparecem mais."
