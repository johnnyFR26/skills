# Dashboard Checklist — Implementação Analítica

Use este checklist antes de considerar um componente de dashboard completo e pronto para produção.

---

## Bloco 1 — Dados e Filtros

- [ ] Filtros temporais aplicados server-side (não client-side)
- [ ] Parâmetros `from` e `to` validados antes do fetch
- [ ] Resposta da API inclui `meta.total` para sanity check
- [ ] Dados normalizados (trim, lowercase) antes de agrupar
- [ ] Tipos TypeScript explícitos para todas as interfaces de dados
- [ ] Nenhuma lógica de transformação dentro de JSX/template
- [ ] Dados derivados em `useMemo` com dependências corretas

## Bloco 2 — Estados da UI

- [ ] Loading state implementado (spinner ou skeleton)
- [ ] Estado de erro implementado (mensagem clara ao usuário)
- [ ] Estado vazio implementado (zero dados no período)
- [ ] Estado de carregamento parcial tratado (dados de um endpoint chegam antes)

## Bloco 3 — Visualização

- [ ] Títulos dos gráficos em linguagem de negócio (não técnica)
- [ ] Labels dos eixos com unidade explícita quando necessário
- [ ] Tooltips com: valor + dimensão + unidade + percentual (quando aplicável)
- [ ] Legenda visível para gráficos com múltiplas séries
- [ ] Cores distintas e acessíveis (mínimo WCAG AA — contraste 3:1)
- [ ] Paleta de cores consistente em todos os gráficos do dashboard
- [ ] Gráficos responsivos (`ResponsiveContainer` ou equivalente)

## Bloco 4 — Métricas de Resumo (Cards)

- [ ] Cada card tem: valor principal + label descritivo + ícone contextual
- [ ] Valores formatados adequadamente (milhares com separador, percentuais com %)
- [ ] Comparativo com período anterior exibido quando relevante
- [ ] Valores zero exibidos explicitamente (não omitidos)

## Bloco 5 — Filtros e Controles

- [ ] Filtro de período com opções rápidas (7d, 30d, 90d) e seleção manual
- [ ] Seleção de range de datas exibe datas formatadas para o usuário
- [ ] Mudança de filtro dispara novo fetch (não refiltra dados já carregados)
- [ ] Estado dos filtros refletido na URL (opcional mas recomendado)

## Bloco 6 — Performance

- [ ] Sem re-renders desnecessários (`useMemo`, `useCallback` onde relevante)
- [ ] Limite de registros exibidos em listas (ex: Top 5, Top 10)
- [ ] Dados históricos não re-fetched sem mudança de filtro
- [ ] Tamanho de response razoável (< 1MB por requisição analítica)

## Bloco 7 — Acessibilidade

- [ ] Cores não são o único indicador de informação (usar formas ou labels)
- [ ] Gráficos têm `aria-label` descritivo
- [ ] Tabelas de detalhamento com headers semânticos `<th>`
- [ ] Interações de filtro acessíveis via teclado

## Bloco 8 — Qualidade de Código

- [ ] Componente separado do hook de dados (separação de concerns)
- [ ] Constantes (cores, limites) extraídas do JSX
- [ ] Sem `console.log` de debug em produção
- [ ] Tipos `any` eliminados ou justificados com comentário

---

## Checklist de Review Rápido (antes de PR)

```
[ ] Dados filtrados server-side?
[ ] Todos os estados (loading/error/empty) implementados?
[ ] Sem lógica de negócio no JSX?
[ ] Labels em linguagem de negócio?
[ ] Testei com zero dados no período?
[ ] Testei com volume alto (1000+ registros)?
```
