# Templates de Issues por Tipo

Templates completos e prontos para uso com `gh issue create --body-file /tmp/issue-body.md`.

---

## 🐛 Bug Report

```markdown
## 🐛 Descrição do Bug
<!-- Resumo claro e objetivo do problema -->

## 🔁 Passos para Reproduzir
1. Acesse `...`
2. Clique em `...`
3. Observe `...`

## ✅ Comportamento Esperado
<!-- O que deveria acontecer -->

## ❌ Comportamento Atual
<!-- O que está acontecendo de fato -->

## 🌍 Ambiente
- **OS:** macOS 14 / Ubuntu 22.04 / Windows 11
- **Browser:** Chrome 130 / Firefox 121
- **Versão da App:** v2.4.1
- **Node / Runtime:** v20.11.0

## 📸 Evidências
<!-- Screenshots, screen recordings, logs de erro -->
```
Error: Cannot read properties of undefined (reading 'email')
  at AuthController.login (auth.controller.ts:42)
```

## 🔗 Contexto Adicional
<!-- Workaround conhecido? Frequência? Impacto em usuários? -->

## 📌 Sugestão de Causa Raiz
<!-- Se tiver palpite técnico, compartilhe aqui -->
```

**Labels:** `bug`, `priority:<nível>`  
**Assignee:** quem investigará  
**Milestone:** sprint atual ou `triage`

---

## ✨ Feature Request

```markdown
## 🎯 Objetivo
<!-- Que problema de usuário ou de negócio essa feature resolve? -->

## 👤 User Story
Como **[persona]**, eu quero **[ação]** para **[benefício]**.

## ✅ Critérios de Aceite (DoD)
- [ ] Dado que [contexto], quando [ação], então [resultado]
- [ ] Dado que [contexto], quando [ação], então [resultado]
- [ ] Testes unitários e de integração cobrindo os fluxos principais
- [ ] Documentação atualizada (README / Storybook / API docs)

## 🔧 Escopo Técnico (opcional)
<!-- Componentes afetados, APIs envolvidas, dependências -->
- [ ] Tarefa 1
- [ ] Tarefa 2
- [ ] Tarefa 3

## 🚫 Fora do Escopo
<!-- O que explicitamente NÃO será feito nessa issue -->

## 📐 Mockups / Wireframes
<!-- Links para Figma, Miro, screenshots de referência -->

## 🔗 Referências
- Relacionado a #<número>
- Epic: #<número>
- Decisão técnica: [link para ADR ou discussão]

## 📊 Métricas de Sucesso
<!-- Como saberemos que isso funcionou? -->
```

**Labels:** `feature`, `priority:<nível>`  
**Assignee:** owner da feature  
**Milestone:** sprint planejada  
**Project:** adicionar ao board

---

## 🔧 Chore / Tech Debt

```markdown
## 🔧 Descrição
<!-- O que precisa ser feito e por quê é necessário agora -->

## 💡 Motivação
<!-- Qual dívida técnica isso resolve? Qual risco mitiga? -->
- [ ] Reduz acoplamento em `...`
- [ ] Elimina dependência deprecated (`lib` v1.x → v2.x)
- [ ] Melhora performance em `...` (baseline atual: Xms)

## 📋 Tarefas
- [ ] ...
- [ ] ...
- [ ] ...

## ✅ Critérios de Conclusão
- [ ] Todos os testes existentes passando (sem regressões)
- [ ] Cobertura mantida ou melhorada
- [ ] PR aprovado por 1+ revisor com contexto do módulo

## 🚦 Risco / Impacto
- **Risco de regressão:** baixo / médio / alto
- **Módulos afetados:** `...`
- **Necessita feature flag?** Sim / Não

## 🔗 Referências
<!-- ADR, issue original que gerou a dívida, benchmark -->
```

**Labels:** `chore`, `priority:<nível>`

---

## 📚 Documentação

```markdown
## 📚 O que precisa ser documentado
<!-- Descreva o que está faltando ou desatualizado -->

## 🎯 Público-alvo
- [ ] Desenvolvedores internos
- [ ] Contribuidores externos
- [ ] Usuários finais
- [ ] Time de operações

## 📝 Tipo de Documentação
- [ ] README
- [ ] Guia de contribuição (CONTRIBUTING.md)
- [ ] Documentação de API (OpenAPI / JSDoc / docstring)
- [ ] Runbook operacional
- [ ] Architecture Decision Record (ADR)
- [ ] Changelog

## ✅ Tarefas
- [ ] Rascunho inicial
- [ ] Revisão técnica
- [ ] Revisão de linguagem / clareza
- [ ] Publicar / atualizar links

## 🔗 Referências
<!-- Código, PR, issue que originou a necessidade -->
```

**Labels:** `docs`

---

## 🔒 Segurança

> ⚠️ **Vulnerabilidades críticas** devem ser reportadas via Security Advisory privado:  
> `gh api repos/{owner}/{repo}/security-advisories --method POST`  
> Ou via: `Settings → Security → Advisories → New draft security advisory`

```markdown
## 🔒 Descrição do Problema de Segurança
<!-- Sem detalhes sensíveis em issues públicas -->

## 📊 Severidade (CVSS aproximado)
- [ ] Crítica (9.0–10.0)
- [ ] Alta (7.0–8.9)
- [ ] Média (4.0–6.9)
- [ ] Baixa (0.1–3.9)

## 🎯 Vetor de Ataque
- [ ] Rede (remoto)
- [ ] Local
- [ ] Físico

## 📋 Componentes Afetados
<!-- Quais módulos, endpoints, dependências -->

## 🛠️ Mitigação Proposta
<!-- Correção sugerida, se houver -->

## ✅ Tarefas
- [ ] Confirmar e reproduzir
- [ ] Avaliar impacto e superfície de ataque
- [ ] Implementar fix
- [ ] Teste de regressão de segurança
- [ ] Deploy + comunicação (se necessário)
- [ ] Publicar CVE / advisory (se aplicável)
```

**Labels:** `security`, `priority:critical`  
**Assignee:** security lead ou maintainer principal  
**Milestone:** hotfix imediato

---

## ⚡ Performance

```markdown
## ⚡ Problema de Performance
<!-- Descreva o gargalo observado -->

## 📊 Métricas Atuais (baseline)
| Métrica | Valor Atual | Meta |
|---------|------------|------|
| Tempo de resposta (p95) | Xms | <Yms |
| Throughput | X req/s | >Y req/s |
| Uso de memória | XMB | <YMB |

## 🔍 Profiling / Evidências
<!-- Flamegraphs, queries lentas, traces, Lighthouse report -->

## 🔧 Hipóteses e Plano
- [ ] Hipótese 1: [ex: N+1 query em `UserService.findAll`]
- [ ] Hipótese 2: ...

## ✅ Critérios de Aceite
- [ ] Métrica X reduzida em Y% (medida com ferramenta Z)
- [ ] Nenhuma regressão em outros endpoints
- [ ] Benchmark documentado no PR

## 🔗 Referências
<!-- Traces, dashboards de APM, issues relacionadas -->
```

**Labels:** `performance`, `priority:<nível>`
