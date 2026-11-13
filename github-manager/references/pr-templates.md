# Templates de Pull Requests

Templates por tipo de mudança. Usar com `gh pr create --body-file /tmp/pr-body.md`.

## Convenção de Título (Conventional Commits)

```
<type>(<scope>): <descrição imperativa curta>

type: feat | fix | chore | docs | refactor | perf | test | ci | revert
scope: módulo afetado (opcional)
descrição: presente, minúscula, sem ponto final, máx 72 chars

Exemplos:
feat(auth): add JWT refresh token rotation
fix(cart): prevent double submission on slow connections
chore(deps): upgrade Next.js 14 → 15
docs(api): document pagination parameters
perf(search): add Redis cache for autocomplete queries
```

## Convenção de Branch

```
<type>/<issue-número>-<slug-curto>

feat/42-jwt-refresh-token
fix/87-cart-double-submit
chore/101-upgrade-nextjs
docs/55-api-pagination
```

---

## 🚀 Feature

```markdown
## 🎯 O que foi implementado
<!-- Descrição objetiva da mudança — o que, onde, como -->

## 🔗 Issue relacionada
Closes #<número>

## 🧪 Como testar
1. Configure: `...`
2. Execute: `...`
3. Verifique: `...`

**Happy path:**
- Faça X → espere Y

**Edge cases cobertos:**
- Input vazio → mensagem de erro Z
- Timeout → retry automático

## 📸 Screenshots / Gravação
| Antes | Depois |
|-------|--------|
| ![before](url) | ![after](url) |

## 🏗️ Decisões Técnicas
<!-- Por que você fez assim e não de outra forma? -->

## ⚠️ Riscos e Pontos de Atenção
<!-- O que os revisores devem olhar com atenção extra? -->

## ✅ Checklist
- [ ] Self-review realizado (li o diff inteiro antes de abrir)
- [ ] Testes unitários adicionados/atualizados
- [ ] Testes de integração (se aplicável)
- [ ] Sem `console.log`, `debugger` ou código comentado esquecido
- [ ] Sem secrets, tokens ou dados sensíveis
- [ ] Documentação atualizada (README, Storybook, API docs)
- [ ] Variáveis de ambiente documentadas em `.env.example`
- [ ] Feature flag adicionada (se necessário para rollout gradual)
- [ ] CI passando localmente (`npm test`, `npm run lint`)
```

---

## 🐛 Bug Fix

```markdown
## 🐛 Problema
<!-- Descrição do bug que está sendo corrigido -->

## 🔗 Issue relacionada
Fixes #<número>

## 🔍 Causa Raiz
<!-- Por que o bug acontecia? O que estava errado? -->

## 🛠️ Solução
<!-- O que foi mudado e por quê esta abordagem foi escolhida -->

## 🧪 Como verificar a correção
1. Reproduza o bug **antes** do fix: `git checkout main` → ...
2. Aplique o fix: `git checkout <esta-branch>` → ...
3. Confirme que o comportamento esperado ocorre

## 🔁 Testes de Regressão
<!-- Quais testes foram adicionados para garantir que não volta? -->

## ⚠️ Impacto Potencial
<!-- Alguma outra parte do sistema pode ser afetada? -->

## ✅ Checklist
- [ ] Bug reproduzido e confirmado antes do fix
- [ ] Teste de regressão adicionado (esse bug nunca volta sem ser detectado)
- [ ] Outros casos similares verificados no codebase
- [ ] CI passando
- [ ] Self-review realizado
```

---

## 🔧 Chore / Refactor

```markdown
## 🔧 O que foi feito
<!-- Descreva as mudanças — o quê e por quê agora -->

## 🔗 Issue relacionada
Closes #<número>

## 💡 Motivação
<!-- Qual problema técnico isso resolve? Qual risco reduz? -->

## 📐 Escopo das mudanças
- **Arquivos modificados:** X arquivos
- **Linhas alteradas:** +Y / -Z
- **Módulos afetados:** `auth/`, `api/`

## ✅ Garantias de Não-Regressão
- [ ] Todos os testes existentes passando sem modificação
- [ ] Cobertura de testes mantida ou melhorada
- [ ] Nenhuma mudança de comportamento observável externamente
- [ ] Build de produção testado localmente

## 🧪 Como verificar
<!-- Como o revisor pode confirmar que nada quebrou? -->

## ✅ Checklist
- [ ] Nenhuma mudança funcional acidental
- [ ] Linting sem novos warnings
- [ ] Self-review realizado
```

---

## ⬆️ Atualização de Dependência

```markdown
## ⬆️ Dependências Atualizadas

| Pacote | Antes | Depois | Tipo |
|--------|-------|--------|------|
| `next` | 14.2.1 | 15.0.0 | major |
| `zod` | 3.22.0 | 3.23.0 | minor |

## 🔗 Issue relacionada
Closes #<número>

## 📋 Changelogs Revisados
- [next 15.0.0](https://github.com/vercel/next.js/releases/tag/v15.0.0)
- [zod 3.23.0](...)

## ⚠️ Breaking Changes Identificadas
<!-- Liste qualquer breaking change e como foi mitigada -->
- `next 15`: App Router mudou X → mitigado em `app/layout.tsx`

## 🧪 Verificação
- [ ] `npm install` sem conflitos de peer deps
- [ ] Build de produção: `npm run build` ✅
- [ ] Suite de testes: `npm test` ✅
- [ ] Testado em ambiente de staging/preview

## ✅ Checklist
- [ ] Apenas as dependências necessárias foram atualizadas
- [ ] `package-lock.json` / `yarn.lock` atualizado e commitado
- [ ] Nenhuma dependência de desenvolvimento vazou para produção
```

---

## 📚 Documentação

```markdown
## 📚 O que foi documentado
<!-- Descreva o que foi adicionado ou corrigido na documentação -->

## 🔗 Issue relacionada
Closes #<número>

## 🎯 Público-alvo
<!-- Quem vai ler isso? Desenvolvedores, usuários, ops? -->

## 🔍 Como revisar
<!-- Onde ver o resultado? Link para preview se houver -->

## ✅ Checklist
- [ ] Linguagem clara e objetiva
- [ ] Exemplos de código testados e funcionando
- [ ] Links verificados (nenhum 404)
- [ ] Sem informação sensível ou credenciais de exemplo reais
```

---

## 🔒 Segurança / Hotfix

```markdown
## 🔒 Natureza da Mudança
<!-- Descrição não-sensível do que foi corrigido -->

## 🔗 Advisory / Issue
<!-- Se tiver Security Advisory criado: -->
Ref: GHSA-xxxx-xxxx-xxxx

## ⚡ Urgência
- [ ] Crítica — explorada ativamente em produção
- [ ] Alta — vetor conhecido, não explorada
- [ ] Média/Baixa — exposição teórica

## 🧪 Verificação de Segurança
- [ ] Correção valida input no lado servidor
- [ ] Nenhum dado sensível no log ou no body da resposta
- [ ] Teste específico de segurança adicionado
- [ ] SAST/scanner de dependências passou

## 📢 Comunicação
- [ ] Security Advisory atualizado
- [ ] Usuários/clientes afetados notificados (se aplicável)
- [ ] CVE solicitado (se aplicável)

## ✅ Checklist
- [ ] CI completo passando
- [ ] Deploy em staging testado
- [ ] Plano de rollback documentado
```
