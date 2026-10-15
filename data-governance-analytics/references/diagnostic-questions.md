# Perguntas de Diagnóstico de Contexto

Use este checklist antes de iniciar qualquer análise ou implementação orientada a dados.

## Bloco 1 — Pergunta de Negócio

- [ ] Qual é a pergunta de negócio central? (escreva em uma frase)
- [ ] Quem toma a decisão com base nessa análise? (gestor, dev, cliente)
- [ ] Qual ação concreta essa análise vai suportar?
- [ ] Há um prazo ou urgência associada?

## Bloco 2 — Disponibilidade de Dados

- [ ] Quais entidades estão disponíveis? (ex: `Attendance`, `User`, `Reason`)
- [ ] Qual é a granularidade mínima? (por evento, por dia, por semana)
- [ ] Qual é o volume estimado de registros no período?
- [ ] Os dados históricos estão disponíveis ou apenas recentes?
- [ ] Há dados faltantes conhecidos?

## Bloco 3 — Qualidade e Confiança

- [ ] Os dados são brutos (raw) ou já processados?
- [ ] Existe validação na ingestão dos dados?
- [ ] Há registros duplicados conhecidos?
- [ ] Campos obrigatórios sempre preenchidos?
- [ ] Timezone documentado e consistente?

## Bloco 4 — Contexto Técnico

- [ ] Onde os dados residem? (banco relacional, API, planilha)
- [ ] Existe endpoint analítico dedicado ou usa-se o CRUD genérico?
- [ ] Filtros são aplicados server-side ou client-side?
- [ ] Há limite de registros por request (paginação)?
- [ ] Existe cache de resultados analíticos?

## Bloco 5 — Definição de Sucesso

- [ ] Como saber se a análise está correta? (sanity check)
- [ ] Qual é o valor baseline esperado?
- [ ] Existe uma fonte de verdade alternativa para validação cruzada?

---

## Saída Esperada

Ao responder esse diagnóstico, você deve ter clareza sobre:
1. **O que analisar** — entidade e métrica
2. **De onde vem** — fonte e qualidade
3. **Para quem** — consumidor e ação esperada
4. **Como validar** — critério de correção
