---
name: github-manager
description: >
  Manage GitHub issues, pull requests, and projects using the `gh` CLI with full governance best practices.
  ALWAYS use this skill when the user wants to: create or update a GitHub issue, open or review a pull request,
  manage a GitHub Project board, triage issues, write PR descriptions, set up labels/milestones, link issues to PRs,
  or run any `gh` CLI workflow. Trigger on phrases like "abrir issue", "criar PR", "adicionar ao projeto",
  "fechar issue", "revisar PR", "etiquetar", "milestone", "project board", "gh issue", "gh pr", "gh project",
  or any request to organize, track, or govern work via GitHub.
argument-hint: "[issue | pr | project | triage | label | milestone]"
compatibility: "Requires bash tool and gh CLI authenticated (gh auth status)"
---

# GitHub Manager

Gerenciamento completo de issues, pull requests e projects do GitHub usando o `gh` CLI com boas práticas de governança.

---

## Comandos Rápidos de Diagnóstico

Sempre verificar o ambiente antes de qualquer operação:

```bash
gh auth status                        # autenticação ok?
gh repo view --json name,owner        # repo atual
gh label list                         # labels disponíveis
gh milestone list                     # milestones abertas
gh project list --owner @me           # projects do usuário
```

---

## ISSUES

> Leia `references/issue-templates.md` para templates completos por tipo (bug, feature, chore, docs, security).

### Anatomia de uma Issue Completa

Uma issue bem governada tem:

| Campo | Por quê importa |
|-------|----------------|
| **Título** | Curto, imperativo, descritivo (`[tipo] O quê - Onde`) |
| **Corpo** | Contexto, critérios de aceite, tarefas, referências |
| **Labels** | Tipo + prioridade + status para filtragem/automação |
| **Assignee** | Responsabilidade clara desde o início |
| **Milestone** | Vincula a uma entrega / sprint |
| **Project** | Visibilidade no board de planejamento |
| **Linked PR** | Rastreabilidade automática (fecha issue no merge) |

### Criar Issue — Fluxo Completo

```bash
# 1. Criar com editor interativo (recomendado para issues complexas)
gh issue create \
  --title "[feat] Título descritivo da feature" \
  --body-file /tmp/issue-body.md \
  --label "feature,priority:high" \
  --assignee "@me" \
  --milestone "Sprint 42" \
  --project "Roadmap Q4"

# 2. Criar direto pelo terminal (issues simples)
gh issue create \
  --title "[bug] Formulário não valida email em branco" \
  --body "$(cat /tmp/bug-body.md)" \
  --label "bug,priority:critical" \
  --assignee "username"

# 3. Abrir no editor web após criar
gh issue create --web
```

**Sempre** escrever o `--body` em um arquivo temporário antes de passar ao comando, para controlar a formatação.

### Gerar corpo da issue

```bash
# Criar arquivo de corpo baseado no template
cat > /tmp/issue-body.md << 'EOF'
## 📋 Contexto
<!-- Por que isso é necessário? Qual problema resolve? -->

## ✅ Critérios de Aceite
- [ ] ...
- [ ] ...
- [ ] ...

## 🔧 Tarefas Técnicas
- [ ] ...
- [ ] ...

## 🔗 Referências
- Relacionado a #<número>
- Documentação: [link]

## 📸 Evidências / Mockups
<!-- screenshots, logs, wireframes -->
EOF
```

### Listar, Filtrar e Atualizar Issues

```bash
# Listar issues abertas por label
gh issue list --label "bug,priority:critical" --state open

# Listar por assignee e milestone
gh issue list --assignee "@me" --milestone "Sprint 42"

# Busca por texto no título
gh issue list --search "auth login" --state open

# Atualizar label, milestone e assignee
gh issue edit 123 \
  --add-label "in-progress" \
  --remove-label "backlog" \
  --milestone "Sprint 42" \
  --add-assignee "username"

# Adicionar comentário com update de status
gh issue comment 123 \
  --body "🔄 Iniciando implementação. Branch: \`feat/auth-login-fix\`"

# Fechar com motivo
gh issue close 123 --comment "✅ Resolvido via PR #456. Deploy em produção realizado."

# Reabrir com contexto
gh issue reopen 123 --comment "🔁 Reabrindo — regressão identificada em staging."
```

### Triagem de Issues

```bash
# Ver issues sem label de tipo
gh issue list --state open --json number,title,labels \
  --jq '.[] | select(.labels | length == 0) | "\(.number): \(.title)"'

# Issues antigas sem assignee (> 7 dias)
gh issue list --state open --json number,title,assignees,createdAt \
  --jq '.[] | select(.assignees | length == 0) | "\(.number): \(.title)"'

# Issues por prioridade
gh issue list --label "priority:critical" --state open
```

---

## PULL REQUESTS

> Leia `references/pr-templates.md` para templates de descrição por tipo de mudança.

### Anatomia de um PR Bem Governado

| Campo | Por quê importa |
|-------|----------------|
| **Título** | Convencional Commits: `type(scope): descrição` |
| **Corpo** | O quê, por quê, como testar, screenshots |
| **Closes #N** | Fecha issue automaticamente no merge |
| **Reviewers** | Pelo menos 1 revisor obrigatório |
| **Labels** | Tipo de mudança + tamanho (xs/s/m/l/xl) |
| **Draft** | Indica WIP, bloqueia merge acidental |
| **Checks** | CI/CD deve passar antes do review |
| **Branch** | Nomenclatura: `type/issue-número-slug` |

### Criar PR — Fluxo Completo

```bash
# 1. Preparar corpo do PR
cat > /tmp/pr-body.md << 'EOF'
## 🎯 O que foi feito
<!-- Descrição clara e objetiva das mudanças -->

## 🔗 Issue relacionada
Closes #<número>

## 🧪 Como testar
1. ...
2. ...
3. ...

## 📸 Screenshots
<!-- Antes / Depois para mudanças visuais -->

## ✅ Checklist
- [ ] Testes passando localmente
- [ ] Documentação atualizada
- [ ] Sem secrets ou dados sensíveis
- [ ] Self-review realizado
EOF

# 2. Criar PR (inicia como draft)
gh pr create \
  --title "feat(auth): implement JWT refresh token rotation" \
  --body-file /tmp/pr-body.md \
  --draft \
  --label "feature,size:m" \
  --reviewer "username1,username2" \
  --assignee "@me" \
  --milestone "Sprint 42" \
  --project "Roadmap Q4"

# 3. Quando pronto para revisão
gh pr ready <número>
```

### Gerenciar PRs Existentes

```bash
# Ver status dos seus PRs
gh pr status

# Listar PRs por estado
gh pr list --state open --author "@me"
gh pr list --state open --reviewer "@me"

# Ver PR com checks e reviews
gh pr view 456 --json title,state,reviews,statusCheckRollup

# Adicionar reviewers
gh pr edit 456 --add-reviewer "username"

# Mergear (squash por padrão — melhor para histórico limpo)
gh pr merge 456 --squash --delete-branch

# Mergear com rebase (histórico linear)
gh pr merge 456 --rebase --delete-branch

# Ver diff
gh pr diff 456

# Checkout local para testar
gh pr checkout 456

# Verificar CI/CD
gh pr checks 456
```

### Fazer Review via CLI

```bash
# Aprovar
gh pr review 456 --approve --body "LGTM 🚀"

# Pedir mudanças com comentário
gh pr review 456 \
  --request-changes \
  --body "Precisa de testes unitários para o caso de email inválido."

# Comentar sem decisão
gh pr review 456 --comment --body "Podemos considerar extrair isso para um hook?"

# Ver reviews existentes
gh pr view 456 --json reviews
```

---

## PROJECTS (GitHub Projects v2)

> Leia `references/project-commands.md` para workflows avançados de automação de projeto.

### Criar e Configurar Projeto

```bash
# Criar novo projeto
gh project create --owner "@me" --title "Roadmap Q4 2026"
gh project create --owner "org-name" --title "Sprint Board" --format "table"

# Listar projetos
gh project list --owner "@me"
gh project list --owner "org-name"
```

### Adicionar e Mover Items

```bash
# Obter ID do projeto
PROJECT_ID=$(gh project list --owner "@me" --format json \
  --jq '.projects[] | select(.title=="Roadmap Q4 2026") | .id')

# Adicionar issue ao projeto
gh project item-add $PROJECT_ID --owner "@me" --url \
  "https://github.com/owner/repo/issues/123"

# Adicionar PR ao projeto
gh project item-add $PROJECT_ID --owner "@me" --url \
  "https://github.com/owner/repo/pull/456"

# Listar items do projeto
gh project item-list $PROJECT_ID --owner "@me"

# Ver campos disponíveis
gh project field-list $PROJECT_ID --owner "@me"
```

### Atualizar Status de Item no Projeto

```bash
# Obter ITEM_ID e FIELD_ID do status
ITEM_ID=$(gh project item-list $PROJECT_ID --owner "@me" --format json \
  --jq '.items[] | select(.content.number==123) | .id')

STATUS_FIELD_ID=$(gh project field-list $PROJECT_ID --owner "@me" --format json \
  --jq '.fields[] | select(.name=="Status") | .id')

# Atualizar status (valor deve existir como opção no campo)
gh project item-edit \
  --project-id $PROJECT_ID \
  --id $ITEM_ID \
  --field-id $STATUS_FIELD_ID \
  --single-select-option-id "In Progress"
```

---

## LABELS — Taxonomia Recomendada

Configure labels uma vez por repositório. Leia `references/governance.md` para o script completo.

```bash
# Criar labels (exemplo)
gh label create "bug"           --color "d73a4a" --description "Algo não está funcionando"
gh label create "feature"       --color "0075ca" --description "Nova funcionalidade"
gh label create "chore"         --color "e4e669" --description "Manutenção técnica"
gh label create "docs"          --color "0075ca" --description "Documentação"
gh label create "priority:critical" --color "b60205" --description "Bloqueia produção"
gh label create "priority:high"     --color "e11d48" --description "Alta prioridade"
gh label create "priority:medium"   --color "f97316" --description "Média prioridade"
gh label create "priority:low"      --color "84cc16" --description "Baixa prioridade"
gh label create "status:blocked"    --color "6e40c9" --description "Bloqueado por dependência"
gh label create "size:xs"           --color "c5def5" --description "< 50 linhas"
gh label create "size:s"            --color "bfd4f2" --description "50-150 linhas"
gh label create "size:m"            --color "9ecbff" --description "150-500 linhas"
gh label create "size:l"            --color "6ea6d8" --description "500+ linhas — considere dividir"
```

---

## MILESTONES

```bash
# Criar milestone com data
gh api repos/{owner}/{repo}/milestones \
  --method POST \
  --field title="Sprint 42" \
  --field description="Sprint de 2 semanas — 01/12 a 14/12/2026" \
  --field due_on="2026-12-14T23:59:59Z"

# Listar milestones
gh milestone list

# Ver progresso
gh api repos/{owner}/{repo}/milestones \
  --jq '.[] | "\(.title): \(.closed_issues)/\(.open_issues + .closed_issues) (\(.state))"'
```

---

## Referências

| Arquivo | Quando ler |
|---------|-----------|
| `references/issue-templates.md` | Criar issue — templates por tipo (bug, feat, chore, docs, security) |
| `references/pr-templates.md` | Criar PR — templates por tipo de mudança |
| `references/project-commands.md` | Automação e queries avançadas de Projects |
| `references/governance.md` | Setup inicial: labels, branch protection, templates |

---

## Fluxo de Trabalho Padrão (do zero à entrega)

```
1. Criar issue completa com contexto e critérios de aceite
        ↓
2. Adicionar ao Project Board na coluna "Backlog"
        ↓
3. Atribuir assignee + milestone ao iniciar a tarefa
        ↓
4. Criar branch: git checkout -b feat/42-auth-refresh-token
        ↓
5. Abrir PR como Draft vinculando "Closes #42"
        ↓
6. Mover issue para "In Progress" no board
        ↓
7. Marcar PR como Ready + solicitar review
        ↓
8. CI ✅ + Approval ✅ → Squash merge + delete branch
        ↓
9. Issue fecha automaticamente. Mover para "Done" no board.
```
