---
name: go-dev
description: >
  Guia completo para desenvolvimento em Go (Golang). Use esta skill sempre que o usuário estiver
  escrevendo, revisando ou depurando código Go; criando projetos, pacotes ou módulos Go; trabalhando
  com goroutines, canais, interfaces ou tratamento de erros Go; configurando go.mod e dependências;
  escrevendo testes, benchmarks ou fuzz tests em Go; otimizando performance de aplicações Go;
  construindo CLIs, APIs HTTP, serviços gRPC ou ferramentas com Go; ou seguindo idiomas e
  boas práticas da linguagem. Triggers: "Go", "Golang", "goroutine", "go.mod", "channel", "interface{}",
  "error handling Go", "go test", "go build", "net/http", "context.Context", ou qualquer arquivo .go.
---

# Go Development Skill

Guia completo para escrever código Go idiomático, eficiente e bem testado.

## Referências Rápidas

Leia o arquivo de referência apropriado antes de responder:

| Tópico | Arquivo | Quando ler |
|--------|---------|------------|
| Estrutura de projetos | `references/go-project-structure.md` | Novo projeto, organização de pacotes |
| Padrões idiomáticos | `references/go-patterns.md` | Errors, interfaces, options pattern, funcional |
| Concorrência | `references/go-concurrency.md` | Goroutines, canais, sync, context |
| Testes | `references/go-testing.md` | Unit tests, benchmarks, fuzz, mocks |
| Módulos e deps | `references/go-modules.md` | go.mod, versioning, workspaces |
| Performance | `references/go-performance.md` | Profiling, alocações, otimizações |

---

## Princípios Go

### A Filosofia Go
- **Simplicidade explícita** — Prefira código direto a abstrações inteligentes
- **Composição via interfaces** — Pequenas interfaces, fáceis de implementar
- **Erros são valores** — Trate-os, não os ignore
- **Concorrência comunicativa** — "Não comunique compartilhando memória; compartilhe memória comunicando"
- **Legibilidade acima de tudo** — Código é lido muito mais do que escrito

### Regras de Ouro
1. `gofmt` **sempre** — sem discussão de estilo
2. Rode `go vet` antes de commitar
3. Erros retornados **sempre** verificados (use `errcheck` ou `staticcheck`)
4. Goroutines precisam de caminho de saída claro
5. Contextos propagam-se do topo para baixo, nunca armazenados em structs
6. Interfaces são definidas pelo **consumidor**, não pelo produtor

---

## Estrutura de Código

### Convenções de Nomenclatura

```go
// ✅ Exportado — começa com maiúscula
type UserRepository interface { ... }
func NewUserService() *UserService { ... }

// ✅ Não exportado — começa com minúscula
type userCache struct { ... }
func parseToken(s string) (*Claims, error) { ... }

// ✅ Acrônimos: ID, URL, HTTP sempre maiúsculos
type UserID string
func GetHTTPClient() *http.Client { ... }

// ✅ Receivers curtos e consistentes
func (u *User) Validate() error { ... }    // não "user", não "this"
func (s *Server) Start() error { ... }

// ✅ Pacotes: singular, sem underscores
package user   // não "users", não "user_service"
package httputil
```

### Declaração de Variáveis

```go
// ✅ Use := para inferência clara
conn, err := db.Connect(dsn)

// ✅ var para zero-value intencional
var buf bytes.Buffer
var mu sync.Mutex

// ✅ Agrupamento com var block
var (
    defaultTimeout = 30 * time.Second
    maxRetries     = 3
    baseURL        = "https://api.example.com"
)

// ❌ Evite _ como nome de variável significativa
_, err = io.Copy(dst, src)  // ok — descarte explícito
x, _ := someFunc()          // ❌ — ignora erro silenciosamente
```

---

## Tratamento de Erros — Quick Reference

> Para padrões avançados, leia `references/go-patterns.md`

```go
// ✅ Erro básico
if err != nil {
    return fmt.Errorf("operação falhou: %w", err)
}

// ✅ Erros sentinela
var ErrNotFound = errors.New("não encontrado")
var ErrUnauthorized = errors.New("não autorizado")

// ✅ Verificação com errors.Is / errors.As
if errors.Is(err, ErrNotFound) { ... }

var valErr *ValidationError
if errors.As(err, &valErr) { ... }

// ✅ Erro customizado
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("validação: campo %q: %s", e.Field, e.Message)
}
```

---

## Context — Quick Reference

> Para padrões avançados de concorrência, leia `references/go-concurrency.md`

```go
// ✅ Sempre aceite context como primeiro parâmetro
func FetchUser(ctx context.Context, id string) (*User, error) {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    ...
}

// ✅ Timeout e cancelamento
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

// ✅ Valores no contexto — apenas dados de request-scoped
type ctxKey string
const requestIDKey ctxKey = "requestID"
ctx = context.WithValue(ctx, requestIDKey, requestID)
```

---

## Estruturas e Inicialização

```go
// ✅ Constructor com opções funcionais (para APIs públicas)
type Server struct {
    host    string
    port    int
    timeout time.Duration
}

type Option func(*Server)

func WithPort(port int) Option {
    return func(s *Server) { s.port = port }
}

func NewServer(host string, opts ...Option) *Server {
    s := &Server{host: host, port: 8080, timeout: 30 * time.Second}
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// ✅ Uso
srv := NewServer("localhost", WithPort(9090))

// ✅ Struct literal para tipos internos simples
cfg := Config{Host: "localhost", Port: 5432}
```

---

## HTTP Server — Quick Reference

```go
// ✅ Handler funcional idiomático
func handleUser(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    
    id := r.PathValue("id")  // Go 1.22+
    
    user, err := svc.GetUser(ctx, id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            http.Error(w, "não encontrado", http.StatusNotFound)
            return
        }
        http.Error(w, "erro interno", http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(user)
}

// ✅ Roteamento Go 1.22+
mux := http.NewServeMux()
mux.HandleFunc("GET /users/{id}", handleUser)
mux.HandleFunc("POST /users", handleCreateUser)

srv := &http.Server{
    Addr:         ":8080",
    Handler:      mux,
    ReadTimeout:  10 * time.Second,
    WriteTimeout: 10 * time.Second,
    IdleTimeout:  120 * time.Second,
}
```

---

## Ferramentas Essenciais

```bash
# Formatação (obrigatório)
gofmt -w .
goimports -w .          # também organiza imports

# Análise estática
go vet ./...
staticcheck ./...        # go install honnef.co/go/tools/cmd/staticcheck@latest
golangci-lint run        # suite completa

# Testes
go test ./...
go test -race ./...      # detector de race conditions
go test -cover ./...     # cobertura
go test -bench=. ./...   # benchmarks

# Build e execução
go build -o bin/app ./cmd/app
go run ./cmd/app

# Dependências
go mod tidy
go mod download
go mod verify

# Geração de código
go generate ./...

# Documentação
godoc -http=:6060
go doc fmt.Println
```

---

## Checklist de Code Review Go

- [ ] Todos os erros verificados e tratados adequadamente
- [ ] Goroutines têm caminho de saída (context, done channel, ou WaitGroup)
- [ ] Interfaces no pacote consumidor, não no produtor
- [ ] Sem `interface{}` desnecessário — use generics (Go 1.18+) ou tipos concretos
- [ ] Context propagado corretamente (primeiro parâmetro, não em struct)
- [ ] Mutexes protegendo exatamente o que devem (nem mais, nem menos)
- [ ] `defer` usado para cleanup (Close, Unlock, cancel)
- [ ] Testes com `t.Parallel()` onde seguro
- [ ] `go vet` e `staticcheck` passando
- [ ] Sem `panic` em código de produção (exceto em `init` ou casos de invariante)

---

## Versões e Compatibilidade

| Feature | Versão mínima |
|---------|---------------|
| Módulos | Go 1.11 |
| `errors.Is/As` | Go 1.13 |
| `embed` | Go 1.16 |
| Generics | Go 1.18 |
| Fuzz testing | Go 1.18 |
| `any` (alias `interface{}`) | Go 1.18 |
| `http.ServeMux` com método+path | Go 1.22 |
| Range over integers | Go 1.22 |
| `iter` package | Go 1.23 |

Use sempre `go 1.X` no `go.mod` compatível com sua equipe.