# Governança de Repositório — Setup Completo

Guia para configurar um repositório GitHub com todas as boas práticas desde o início.

---

## 1. Labels — Taxonomia Completa

Execute este script para criar todas as labels recomendadas:

```bash
#!/bin/bash
# setup-labels.sh

REPO="owner/repo"

# Remover labels default do GitHub (opcional)
# for label in "bug" "documentation" "duplicate" "enhancement" "good first issue" \
#              "help wanted" "invalid" "question" "wontfix"; do
#   gh label delete "$label" --repo $REPO --yes 2>/dev/null
# done

# TIPO
gh label create "bug"           --repo $REPO --color "d73a4a" --description "Algo não está funcionando corretamente" --force
gh label create "feature"       --repo $REPO --color "0075ca" --description "Nova funcionalidade ou melhoria" --force
gh label create "chore"         --repo $REPO --color "e4e669" --description "Manutenção técnica, refactor, dívida técnica" --force
gh label create "docs"          --repo $REPO --color "0075ca" --description "Melhorias ou adições à documentação" --force
gh label create "test"          --repo $REPO --color "0e8a16" --description "Relacionado a testes automatizados" --force
gh label create "ci"            --repo $REPO --color "5319e7" --description "Mudanças em CI/CD pipelines" --force
gh label create "security"      --repo $REPO --color "b60205" --description "Correção ou melhoria de segurança" --force
gh label create "performance"   --repo $REPO --color "f9d0c4" --description "Melhoria de performance" --force

# PRIORIDADE
gh label create "priority:critical" --repo $REPO --color "b60205" --description "Bloqueia produção — atender imediatamente" --force
gh label create "priority:high"     --repo $REPO --color "e11d48" --description "Alta prioridade — próxima sprint" --force
gh label create "priority:medium"   --repo $REPO --color "f97316" --description "Média prioridade" --force
gh label create "priority:low"      --repo $REPO --color "84cc16" --description "Baixa prioridade — backlog" --force

# STATUS
gh label create "status:needs-triage"   --repo $REPO --color "ededed" --description "Aguardando triagem e priorização" --force
gh label create "status:blocked"        --repo $REPO --color "6e40c9" --description "Bloqueado por dependência externa" --force
gh label create "status:in-progress"    --repo $REPO --color "1d76db" --description "Em desenvolvimento ativo" --force
gh label create "status:needs-review"   --repo $REPO --color "e99695" --description "Aguardando revisão de código" --force
gh label create "status:needs-info"     --repo $REPO --color "d4c5f9" --description "Aguardando mais informações" --force
gh label create "status:wontfix"        --repo $REPO --color "ffffff" --description "Não será corrigido nesta release" --force
gh label create "backlog"               --repo $REPO --color "c2e0c6" --description "No backlog para próximas sprints" --force
gh label create "in-sprint"             --repo $REPO --color "0052cc" --description "Comprometido para a sprint atual" --force

# TAMANHO DE PR
gh label create "size:xs"  --repo $REPO --color "c5def5" --description "< 50 linhas" --force
gh label create "size:s"   --repo $REPO --color "bfd4f2" --description "50–150 linhas" --force
gh label create "size:m"   --repo $REPO --color "9ecbff" --description "150–500 linhas" --force
gh label create "size:l"   --repo $REPO --color "6ea6d8" --description "500–1000 linhas — considere dividir" --force
gh label create "size:xl"  --repo $REPO --color "2188ff" --description "> 1000 linhas — dividir obrigatório" --force

# ESPECIAIS
gh label create "good first issue"  --repo $REPO --color "7057ff" --description "Boa para contribuidores iniciantes" --force
gh label create "help wanted"       --repo $REPO --color "008672" --description "Precisa de ajuda da comunidade" --force
gh label create "breaking change"   --repo $REPO --color "d93f0b" --description "Introduz mudança incompatível com versão anterior" --force
gh label create "needs-migration"   --repo $REPO --color "fbca04" --description "Requer migração de banco de dados" --force
gh label create "hotfix"            --repo $REPO --color "b60205" --description "Correção urgente em produção" --force

echo "✅ Labels criadas com sucesso!"
```

---

## 2. Proteção de Branches

```bash
OWNER="minha-org"
REPO="meu-repo"

# Proteger branch main
gh api repos/$OWNER/$REPO/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci/tests","ci/lint"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_review":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field required_linear_history=true

echo "✅ Branch protection configurada para main"
```

---

## 3. Templates de Issue (`.github/ISSUE_TEMPLATE/`)

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

### `.github/ISSUE_TEMPLATE/bug_report.yml`

```yaml
name: 🐛 Bug Report
description: Reporte um bug ou comportamento inesperado
title: "[bug] "
labels: ["bug", "status:needs-triage"]
body:
  - type: markdown
    attributes:
      value: "Obrigado por reportar! Preencha com o máximo de detalhes possível."

  - type: textarea
    id: description
    attributes:
      label: Descrição do Bug
      description: Uma descrição clara e objetiva do problema.
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Passos para Reproduzir
      description: Como reproduzir o problema.
      placeholder: |
        1. Acesse '...'
        2. Clique em '...'
        3. Observe '...'
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Comportamento Esperado
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Ambiente
      placeholder: |
        - OS: macOS 14
        - Browser: Chrome 130
        - Versão: v2.4.1
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Logs / Screenshots
      description: Cole logs de erro ou screenshots relevantes.
```

### `.github/ISSUE_TEMPLATE/feature_request.yml`

```yaml
name: ✨ Feature Request
description: Sugerir uma nova funcionalidade
title: "[feat] "
labels: ["feature", "status:needs-triage"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Qual problema você está tentando resolver?
      description: Descreva o problema ou necessidade de negócio.
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Solução Proposta
      description: Descreva o que você quer que aconteça.
    validations:
      required: true

  - type: textarea
    id: acceptance
    attributes:
      label: Critérios de Aceite
      placeholder: |
        - [ ] Dado que..., quando..., então...
        - [ ] ...
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternativas Consideradas
```

### `.github/ISSUE_TEMPLATE/config.yml`

```yaml
blank_issues_enabled: false
contact_links:
  - name: 🔒 Vulnerabilidade de Segurança
    url: https://github.com/owner/repo/security/advisories/new
    about: Reporte vulnerabilidades de forma privada via Security Advisory
  - name: 💬 Discussão
    url: https://github.com/owner/repo/discussions
    about: Dúvidas gerais, ideias e discussões
```

---

## 4. Template de Pull Request

### `.github/pull_request_template.md`

```markdown
## 🎯 O que foi feito
<!-- Descrição objetiva das mudanças -->

## 🔗 Issue relacionada
Closes #

## 🧪 Como testar
1. ...
2. ...

## ✅ Checklist
- [ ] Self-review realizado
- [ ] Testes passando (`npm test`)
- [ ] Lint sem erros (`npm run lint`)
- [ ] Sem secrets ou dados sensíveis
- [ ] Documentação atualizada (se necessário)
- [ ] PR vinculado à issue (`Closes #N`)
```

---

## 5. CODEOWNERS

### `.github/CODEOWNERS`

```
# Owners globais — revisão obrigatória em qualquer mudança
*                   @owner-username @tech-lead

# Backend
/api/               @backend-team
/lib/db/            @backend-team @dba-team

# Frontend
/app/               @frontend-team
/components/        @frontend-team

# CI/CD e Infra
/.github/           @devops-team
/terraform/         @devops-team
/docker/            @devops-team

# Segurança
/lib/auth/          @security-team @backend-team
/lib/crypto/        @security-team
```

---

## 6. Milestones por Convenção

```bash
# Sprint bi-semanal
gh api repos/$OWNER/$REPO/milestones --method POST \
  --field title="Sprint 42" \
  --field description="02/12/2026 – 15/12/2026 | Objetivo: Entregar fluxo de checkout" \
  --field due_on="2026-12-15T23:59:59Z"

# Release version
gh api repos/$OWNER/$REPO/milestones --method POST \
  --field title="v3.0.0" \
  --field description="Próxima major release — breaking changes documentados" \
  --field due_on="2026-12-31T23:59:59Z"

# Bucket especial
gh api repos/$OWNER/$REPO/milestones --method POST \
  --field title="Backlog Técnico" \
  --field description="Dívida técnica sem sprint definida"
```

---

## 7. Checklist de Governança — Auditoria de Repositório

```bash
#!/bin/bash
# audit-repo.sh — Verificar estado de governança

echo "=== AUDITORIA DE GOVERNANÇA ==="

# Branch protection
echo ""
echo "🔒 Branch protection:"
gh api repos/$OWNER/$REPO/branches/main/protection \
  --jq '{
    required_reviews: .required_pull_request_reviews.required_approving_review_count,
    dismiss_stale: .required_pull_request_reviews.dismiss_stale_reviews,
    codeowners: .required_pull_request_reviews.require_code_owner_reviews,
    linear_history: .required_linear_history.enabled,
    no_force_push: (.allow_force_pushes.enabled | not)
  }' 2>/dev/null || echo "  ⚠️ Branch protection não configurada!"

# Labels
echo ""
echo "🏷️ Labels ($( gh label list --repo $OWNER/$REPO --limit 100 --json name | jq length) total):"
for required in "bug" "feature" "priority:critical" "priority:high" "status:blocked"; do
  if gh label list --repo $OWNER/$REPO --json name --jq ".[].name" | grep -q "^$required$"; then
    echo "  ✅ $required"
  else
    echo "  ❌ $required FALTANDO"
  fi
done

# Issues sem label
UNLABELED=$(gh issue list --repo $OWNER/$REPO --state open \
  --json labels --jq '[.[] | select(.labels | length == 0)] | length')
echo ""
echo "🏷️ Issues sem label: $UNLABELED"

# Issues sem assignee
UNASSIGNED=$(gh issue list --repo $OWNER/$REPO --state open \
  --json assignees --jq '[.[] | select(.assignees | length == 0)] | length')
echo "👤 Issues sem assignee: $UNASSIGNED"

# PRs sem review
UNREVIEWED=$(gh pr list --repo $OWNER/$REPO --state open \
  --json reviewRequests --jq '[.[] | select(.reviewRequests | length == 0)] | length')
echo "👁️ PRs sem reviewer: $UNREVIEWED"

# Milestones expiradas
echo ""
echo "📅 Milestones:"
gh api repos/$OWNER/$REPO/milestones \
  --jq '.[] | "  \(if .state == "open" then "🟢" else "⚪" end) \(.title): \(.open_issues) abertas, \(.closed_issues) fechadas"'

echo ""
echo "=== FIM DA AUDITORIA ==="
```

---

## 8. GitHub Actions — Automações Recomendadas

### Auto-label por tamanho de PR

```yaml
# .github/workflows/label-size.yml
name: Label PR size
on: [pull_request]
jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - uses: codelytv/pr-size-labeler@v1
        with:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          xs_max_size: 50
          s_max_size: 150
          m_max_size: 500
          l_max_size: 1000
          fail_if_xl: false
```

### Stale issues

```yaml
# .github/workflows/stale.yml
name: Mark stale issues
on:
  schedule:
    - cron: '0 9 * * 1'  # toda segunda às 9h UTC
jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          stale-issue-message: >
            Esta issue ficou inativa por 30 dias e foi marcada como stale.
            Se ainda for relevante, comente para manter aberta.
          close-issue-message: "Fechada por inatividade. Reabra se necessário."
          days-before-stale: 30
          days-before-close: 7
          stale-issue-label: "stale"
          exempt-issue-labels: "in-sprint,status:blocked,priority:critical"
```
