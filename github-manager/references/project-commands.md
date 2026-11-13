# GitHub Projects v2 — Comandos Avançados

## Visão Geral dos Projects v2

GitHub Projects v2 usa GraphQL internamente. O `gh` CLI abstrai a maioria dos casos;
para operações avançadas, use `gh api graphql`.

---

## Setup Inicial de Projeto

```bash
# Criar projeto para organização
gh project create --owner "minha-org" --title "Roadmap Q4 2026"

# Obter o número do projeto (use este em outros comandos)
gh project list --owner "minha-org" --format json \
  --jq '.projects[] | "\(.number): \(.title)"'

# Exibir detalhes do projeto
gh project view 1 --owner "minha-org"
```

---

## Gerenciar Campos do Projeto

```bash
PROJECT_NUM=1
OWNER="minha-org"

# Listar campos existentes
gh project field-list $PROJECT_NUM --owner $OWNER

# Criar campo de texto customizado
gh project field-create $PROJECT_NUM --owner $OWNER \
  --name "Sprint Goal" \
  --data-type "TEXT"

# Criar campo de número (story points)
gh project field-create $PROJECT_NUM --owner $OWNER \
  --name "Story Points" \
  --data-type "NUMBER"

# Criar campo de data
gh project field-create $PROJECT_NUM --owner $OWNER \
  --name "Due Date" \
  --data-type "DATE"

# Criar campo de single select (Status customizado)
gh project field-create $PROJECT_NUM --owner $OWNER \
  --name "Priority" \
  --data-type "SINGLE_SELECT" \
  --single-select-options "P0 - Critical,P1 - High,P2 - Medium,P3 - Low"
```

---

## Adicionar e Mover Items

```bash
# Adicionar issue pelo URL
gh project item-add $PROJECT_NUM --owner $OWNER \
  --url "https://github.com/$OWNER/repo/issues/42"

# Adicionar PR pelo URL
gh project item-add $PROJECT_NUM --owner $OWNER \
  --url "https://github.com/$OWNER/repo/pull/88"

# Adicionar nota (rascunho) diretamente ao projeto
gh project item-create $PROJECT_NUM --owner $OWNER \
  --title "Spike: Avaliar migração para Turso DB" \
  --body "Investigar latência e custo vs PlanetScale"

# Listar todos os items do projeto
gh project item-list $PROJECT_NUM --owner $OWNER

# Listar com filtro por tipo
gh project item-list $PROJECT_NUM --owner $OWNER --format json \
  --jq '.items[] | select(.type=="ISSUE") | "\(.id): \(.content.number) \(.content.title)"'
```

---

## Atualizar Campos de um Item

```bash
# 1. Obter IDs necessários
ITEM_ID=$(gh project item-list $PROJECT_NUM --owner $OWNER --format json \
  --jq '.items[] | select(.content.number==42) | .id')

# 2. Obter o ID do campo "Status"
STATUS_FIELD_ID=$(gh project field-list $PROJECT_NUM --owner $OWNER --format json \
  --jq '.fields[] | select(.name=="Status") | .id')

# 3. Obter IDs das opções do campo Status
gh project field-list $PROJECT_NUM --owner $OWNER --format json \
  --jq '.fields[] | select(.name=="Status") | .options[]'

# 4. Atualizar status do item
OPTION_ID="<id-da-opcao-in-progress>"
gh project item-edit \
  --project-id $(gh project list --owner $OWNER --format json \
    --jq ".projects[] | select(.number==$PROJECT_NUM) | .id") \
  --id $ITEM_ID \
  --field-id $STATUS_FIELD_ID \
  --single-select-option-id $OPTION_ID

# 5. Atualizar campo numérico (story points)
POINTS_FIELD_ID=$(gh project field-list $PROJECT_NUM --owner $OWNER --format json \
  --jq '.fields[] | select(.name=="Story Points") | .id')

gh project item-edit \
  --project-id $PROJECT_ID \
  --id $ITEM_ID \
  --field-id $POINTS_FIELD_ID \
  --number 5

# 6. Atualizar campo de texto
TEXT_FIELD_ID=$(gh project field-list $PROJECT_NUM --owner $OWNER --format json \
  --jq '.fields[] | select(.name=="Sprint Goal") | .id')

gh project item-edit \
  --project-id $PROJECT_ID \
  --id $ITEM_ID \
  --field-id $TEXT_FIELD_ID \
  --text "Entregar fluxo de autenticação completo"
```

---

## Queries de Relatório via GraphQL

Para operações que o CLI não suporta diretamente:

```bash
# Listar todos os items com status (via GraphQL)
gh api graphql -f query='
  query($org: String!, $number: Int!) {
    organization(login: $org) {
      projectV2(number: $number) {
        title
        items(first: 50) {
          nodes {
            id
            fieldValues(first: 10) {
              nodes {
                ... on ProjectV2ItemFieldSingleSelectValue {
                  name
                  field { ... on ProjectV2SingleSelectField { name } }
                }
              }
            }
            content {
              ... on Issue {
                number
                title
                state
                assignees(first: 3) {
                  nodes { login }
                }
              }
              ... on PullRequest {
                number
                title
                state
              }
            }
          }
        }
      }
    }
  }
' -f org="minha-org" -F number=$PROJECT_NUM

# Contar issues por status
gh api graphql -f query='...' | \
  jq '.data.organization.projectV2.items.nodes |
      group_by(.fieldValues.nodes[] | select(.field.name=="Status") | .name) |
      map({status: .[0].fieldValues.nodes[].name, count: length})'
```

---

## Sprint Planning — Fluxo Completo

```bash
# 1. Criar iteração de sprint (via API — Projects v2 Iteration fields)
gh api graphql -f query='
  mutation($projectId: ID!, $title: String!, $startDate: String!, $duration: Int!) {
    addProjectV2DraftIssue(input: {projectId: $projectId, title: $title}) {
      projectItem { id }
    }
  }
' -f projectId=$PROJECT_ID -f title="Sprint Planning Item"

# 2. Listar issues do backlog ordenadas por prioridade
gh issue list \
  --label "backlog" \
  --state open \
  --json number,title,labels,milestone \
  --jq 'sort_by(.labels[].name) | .[] | "  #\(.number): \(.title)"'

# 3. Adicionar issues selecionadas ao sprint
for ISSUE_NUM in 42 55 61 73; do
  ISSUE_URL="https://github.com/$OWNER/repo/issues/$ISSUE_NUM"
  gh project item-add $PROJECT_NUM --owner $OWNER --url $ISSUE_URL
  gh issue edit $ISSUE_NUM \
    --add-label "in-sprint" \
    --remove-label "backlog" \
    --milestone "Sprint 42"
  echo "✅ Issue #$ISSUE_NUM adicionada ao sprint"
done
```

---

## Sprint Review — Relatório de Encerramento

```bash
#!/bin/bash
# sprint-review.sh — Gerar relatório de sprint

MILESTONE="Sprint 42"
OWNER="minha-org"
REPO="meu-repo"

echo "# 📊 Sprint Review: $MILESTONE"
echo ""

echo "## ✅ Issues Fechadas"
gh issue list \
  --repo "$OWNER/$REPO" \
  --milestone "$MILESTONE" \
  --state closed \
  --json number,title,labels,closedAt \
  --jq '.[] | "- #\(.number) \(.title)"'

echo ""
echo "## 🔄 Issues em Aberto (carry-over)"
gh issue list \
  --repo "$OWNER/$REPO" \
  --milestone "$MILESTONE" \
  --state open \
  --json number,title,labels,assignees \
  --jq '.[] | "- #\(.number) \(.title) [@\(.assignees[0].login // "unassigned")]"'

echo ""
echo "## 📌 PRs Mergeados"
gh pr list \
  --repo "$OWNER/$REPO" \
  --state merged \
  --json number,title,mergedAt,author \
  --jq '.[] | "- #\(.number) \(.title) (\(.author.login))"'
```

---

## Automações e Webhooks

```bash
# Configurar regra de auto-add: issues com label "bug" → projeto automaticamente
# (Feito via UI: Project Settings → Workflows → Auto-add to project)
# Via API:
gh api repos/$OWNER/$REPO/actions/variables \
  --method POST \
  --field name="PROJECT_ID" \
  --field value="$PROJECT_ID"
```

### GitHub Actions — Auto-add ao Project

```yaml
# .github/workflows/project-automation.yml
name: Add to Project Board
on:
  issues:
    types: [opened]
  pull_request:
    types: [opened]

jobs:
  add-to-project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v1
        with:
          project-url: https://github.com/orgs/minha-org/projects/1
          github-token: ${{ secrets.PROJECT_TOKEN }}
          labeled: "bug,feature,chore"
```
