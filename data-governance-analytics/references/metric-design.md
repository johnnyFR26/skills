# Metric Design — Templates e Guia

## Framework SMART para Métricas

Toda métrica deve ser:

- **S**pecific — mede exatamente um comportamento
- **M**easurable — calculável com os dados disponíveis
- **A**ctionable — mudanças nela implicam ação concreta
- **R**elevant — ligada a um objetivo de negócio
- **T**ime-bound — definida em relação a uma janela temporal

---

## Template de Definição de Métrica

```markdown
## [Nome da Métrica]

**Descrição:** O que essa métrica mede em linguagem de negócio.

**Fórmula:**
  [numerador] / [denominador]  (para razões)
  COUNT([entidade]) WHERE [condição]  (para contagens)

**Granularidade:** por dia | por semana | por mês | por atendimento

**Dimensões disponíveis:**
  - Por atendente (externalAttendeeId)
  - Por motivo (reason.name)
  - Por período (createdAt)

**Frequência de atualização:** tempo real | horária | diária

**Fonte de dados:** tabela/endpoint

**Filtros padrão:**
  - Período: últimos 30 dias
  - Excluir: registros sem atendente vinculado

**Critério de alerta:** quando [condição] → notificar [quem]

**Baseline atual:** [valor]

**Dono:** [time ou papel responsável]
```

---

## Catálogo de Métricas Comuns (Domínio de Atendimentos)

### Volume

| Métrica | Fórmula | Dimensão Primária |
|---------|---------|-------------------|
| Total de atendimentos | COUNT(id) | Período |
| Atendimentos por atendente | COUNT(id) GROUP BY externalAttendeeId | Atendente |
| Atendimentos por motivo | COUNT(id) GROUP BY reason.name | Motivo |
| Taxa de crescimento | (atual - anterior) / anterior * 100 | Período comparativo |

### Qualidade

| Métrica | Fórmula | Sinal |
|---------|---------|-------|
| % sem motivo | COUNT(sem reason) / total | ↓ desejável |
| % sem atendente | COUNT(externalAttendeeId NULL) / total | ↓ desejável |
| Tempo médio entre criação e update | AVG(updatedAt - createdAt) | Contexto |

### Eficiência

| Métrica | Fórmula | Sinal |
|---------|---------|-------|
| Motivos por atendimento | SUM(reasons.length) / COUNT(id) | Contexto |
| Concentração de atendimentos | top-1 atendente / total | ↓ desejável para distribuição |

---

## Hierarquia de Métricas

```
Métricas Estratégicas (Negócio)
  └── Métricas Táticas (Produto)
        └── Métricas Operacionais (Engenharia)
              └── Logs e Eventos (Dados brutos)
```

Exemplo:
- Estratégica: "Satisfação do cliente"
- Tática: "Tempo de resolução de atendimento"
- Operacional: "Tempo médio de updatedAt - createdAt por atendente"
- Dado bruto: `attendance.updatedAt`, `attendance.createdAt`

---

## Armadilhas Comuns

- **Vanity metrics**: números que crescem sempre mas não indicam saúde (ex: total de registros desde o início)
- **Métricas sem baseline**: impossível saber se é bom ou ruim sem referência
- **Denominador errado**: razões calculadas sobre populações diferentes
- **Dupla contagem**: atendimentos com múltiplos motivos contados várias vezes sem intenção
