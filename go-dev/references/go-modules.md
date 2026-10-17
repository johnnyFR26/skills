# Módulos e Dependências Go

## go.mod — Anatomia Completa

```
module github.com/empresa/meuapp

go 1.22

require (
    github.com/jackc/pgx/v5          v5.5.4
    github.com/redis/go-redis/v9     v9.4.0
    golang.org/x/sync                v0.6.0
    github.com/stretchr/testify      v1.9.0
)

require (
    // Dependências indiretas (gerenciadas pelo go mod tidy)
    github.com/jackc/pgpassfile       v1.0.0 // indirect
    github.com/kr/pretty              v0.3.1 // indirect
)

// Para substituir uma dependência por fork local
replace github.com/original/lib => ../minha-lib

// Para excluir versão com bug conhecido
exclude github.com/problematica/lib v1.2.3
```

---

## Comandos Essenciais

```bash
# Inicializar módulo
go mod init github.com/empresa/meuapp

# Adicionar dependência
go get github.com/gin-gonic/gin@latest      # Última versão
go get github.com/gin-gonic/gin@v1.9.1      # Versão específica
go get github.com/gin-gonic/gin@main         # Branch

# Atualizar dependências
go get -u ./...                              # Atualiza todas (minor/patch)
go get -u=patch ./...                        # Apenas patches
go get github.com/pkg/errors@latest          # Dependência específica

# Limpar e verificar
go mod tidy          # Remove não usados, adiciona faltantes
go mod verify        # Verifica integridade do cache
go mod download      # Baixa para cache (CI)
go mod vendor        # Copia deps para ./vendor

# Inspecionar
go mod graph         # Grafo de dependências
go list -m all       # Lista todos os módulos
go list -m -json all # Em JSON
go mod why github.com/pkg    # Por que esta dep existe?

# Upgrade seletivo
go get $(go list -m -u -f '{{if (and (not (or .Main .Indirect)) .Update)}}{{.Path}}{{end}}' all)
```

---

## Versionamento Semântico

```
v1.2.3
│ │ └── Patch: bugfix, sem mudança de API
│ └──── Minor: novas features, retrocompatível
└────── Major: mudanças de API incompatíveis
```

### Major Versions (v2+)

```go
// v2 ou superior exige mudança no module path
// go.mod
module github.com/empresa/lib/v2

// Import path deve incluir /v2
import "github.com/empresa/lib/v2/client"

// v1 e v2 podem coexistir no mesmo projeto
import (
    clientv1 "github.com/empresa/lib/client"
    clientv2 "github.com/empresa/lib/v2/client"
)
```

### Tags de versão

```bash
# Criar e publicar versão
git tag v1.2.3
git push origin v1.2.3

# Pre-release
git tag v1.3.0-rc.1
git push origin v1.3.0-rc.1

# Major version
git tag v2.0.0
git push origin v2.0.0
```

---

## Workspaces (Go 1.18+)

Para desenvolvimento simultâneo de múltiplos módulos:

```bash
# Estrutura
workspace/
├── go.work
├── myapp/
│   ├── go.mod
│   └── ...
└── mylib/
    ├── go.mod
    └── ...

# Criar workspace
go work init
go work use ./myapp ./mylib

# go.work
go 1.22

use (
    ./myapp
    ./mylib
)

# No workspace, myapp usa mylib local automaticamente
# sem precisar de replace directive
cd myapp && go build ./...  # Usa mylib local
```

---

## Private Modules

```bash
# Configurar GONOSUMCHECK para módulos privados
export GONOSUMDB="gitlab.empresa.com/*,github.empresa.com/*"
export GOFLAGS="-mod=mod"
export GONOSUMCHECK="gitlab.empresa.com/*"
export GOPRIVATE="gitlab.empresa.com/*"

# Ou no .gitconfig para autenticação
git config --global \
  url."https://TOKEN@gitlab.empresa.com/".insteadOf \
  "https://gitlab.empresa.com/"

# GOPROXY com fallback
export GOPROXY="https://proxy.empresa.com,https://proxy.golang.org,direct"

# Desabilitar proxy para módulos privados
export GONOPROXY="gitlab.empresa.com/*"
```

---

## Vendoring

```bash
# Criar diretório vendor
go mod vendor

# Estrutura
vendor/
├── github.com/pkg/errors/
│   └── ...
├── golang.org/x/sync/
│   └── ...
└── modules.txt          # Metadados

# Build com vendor
go build -mod=vendor ./...
go test -mod=vendor ./...
```

**Quando usar vendor:**
- Ambientes sem acesso à internet (CI corporativo)
- Reprodutibilidade total (go.sum já garante isso na maioria dos casos)
- Quando precisar fazer patch em dependência sem fork

---

## Dependências de Ferramentas (tools.go)

```go
//go:build tools

// tools.go — rastreia ferramentas de desenvolvimento como dependências
package tools

import (
    _ "github.com/vektra/mockery/v2"
    _ "golang.org/x/tools/cmd/goimports"
    _ "honnef.co/go/tools/cmd/staticcheck"
    _ "github.com/golangci/golangci-lint/cmd/golangci-lint"
)
```

```bash
# Instalar ferramentas rastreadas
go install github.com/vektra/mockery/v2@$(go list -m -f '{{.Version}}' github.com/vektra/mockery/v2)

# Ou via Makefile
tools:
    go install $(shell go list -f '{{range .Imports}}{{.}} {{end}}' tools.go)
```

---

## go.sum — Segurança e Integridade

```bash
# go.sum armazena hashes criptográficos de cada módulo
# NÃO edite manualmente

# Verificar consistência com sum database
go mod verify

# Se go.sum está incorreto
rm go.sum
go mod tidy

# GONOSUMCHECK desativa verificação para módulos privados
export GONOSUMCHECK="gitlab.empresa.com/*"
```

---

## Dependências Selecionadas por Categoria

### HTTP
```bash
go get github.com/go-chi/chi/v5          # Router leve e idiomático
go get github.com/gin-gonic/gin          # Framework completo popular
go get github.com/labstack/echo/v4       # Performance-focused
```

### Banco de Dados
```bash
go get github.com/jackc/pgx/v5          # PostgreSQL (preferido)
go get github.com/go-sql-driver/mysql   # MySQL
go get github.com/mattn/go-sqlite3      # SQLite (CGO)
go get modernc.org/sqlite               # SQLite (pure Go, sem CGO)

# Query builders / ORMs
go get github.com/jmoiron/sqlx          # Extensão do database/sql
go get github.com/sqlc-dev/sqlc         # Geração de código a partir de SQL
go get gorm.io/gorm                     # ORM completo
go get github.com/uptrace/bun           # ORM moderno e rápido
```

### Testes
```bash
go get github.com/stretchr/testify      # Assertions
go get github.com/vektra/mockery/v2     # Geração de mocks
go get github.com/testcontainers/testcontainers-go  # Containers em testes
```

### Observabilidade
```bash
go get go.opentelemetry.io/otel         # OpenTelemetry
go get github.com/prometheus/client_golang  # Prometheus
go get go.uber.org/zap                  # Logging estruturado de alta performance
```

### Configuração
```bash
go get github.com/caarlos0/env/v11      # Env vars para structs
go get github.com/spf13/viper           # Configuração multi-fonte
```

### CLI
```bash
go get github.com/spf13/cobra           # CLI framework completo
go get github.com/urfave/cli/v2         # Alternativa simples
go get github.com/charmbracelet/bubbletea  # TUI moderno
```

### Utilitários
```bash
go get golang.org/x/sync               # errgroup, semaphore, singleflight
go get golang.org/x/exp               # Experimental (slices, maps, etc.)
go get github.com/google/uuid          # UUID
go get golang.org/x/crypto             # Criptografia
```

---

## Boas Práticas

```bash
# 1. Sempre rode tidy após adicionar/remover deps
go mod tidy

# 2. Commite go.mod E go.sum no git
git add go.mod go.sum

# 3. No CI, use -mod=readonly para detectar go.mod desatualizado
go build -mod=readonly ./...
go test -mod=readonly ./...

# 4. GOFLAGS no CI
export GOFLAGS="-mod=readonly"

# 5. Verifique segurança de dependências
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```