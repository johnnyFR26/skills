# Go Project Structure

## Layout Padrão — Projeto de Aplicação

```
myapp/
├── cmd/
│   ├── api/
│   │   └── main.go          # Entry point da API
│   └── worker/
│       └── main.go          # Entry point do worker
├── internal/                # Código não exportável fora do módulo
│   ├── domain/              # Entidades e regras de negócio
│   │   ├── user.go
│   │   └── user_test.go
│   ├── repository/          # Acesso a dados
│   │   ├── user_postgres.go
│   │   └── user_postgres_test.go
│   ├── service/             # Lógica de aplicação
│   │   └── user_service.go
│   └── handler/             # HTTP handlers / gRPC handlers
│       └── user_handler.go
├── pkg/                     # Código reutilizável por outros módulos
│   └── httputil/
│       └── response.go
├── configs/                 # Arquivos de configuração
├── migrations/              # Migrações de banco de dados
├── scripts/                 # Scripts de build/deploy
├── docs/                    # Documentação
├── go.mod
├── go.sum
├── Makefile
└── README.md
```

## Layout Padrão — Biblioteca/Pacote

```
mylib/
├── mylib.go                 # API principal exportada
├── mylib_test.go
├── internal/                # Implementação privada
│   └── ...
├── example_test.go          # Exemplos na documentação
├── go.mod
└── README.md
```

## Regras de Organização

### `cmd/`
- Cada subdiretório = um binário
- `main.go` deve ser mínimo: parsing de flags + injeção de dependências + start
- Toda lógica vai em `internal/`

```go
// cmd/api/main.go — mínimo e limpo
func main() {
    cfg := config.MustLoad()
    
    db := postgres.MustConnect(cfg.DatabaseURL)
    defer db.Close()
    
    repo := repository.NewUserRepo(db)
    svc := service.NewUserService(repo)
    hdl := handler.NewUserHandler(svc)
    
    srv := server.New(cfg, hdl)
    
    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()
    
    if err := srv.Run(ctx); err != nil {
        log.Fatalf("server error: %v", err)
    }
}
```

### `internal/`
- **Inacessível** fora do módulo — use para tudo que não é API pública
- Organizado por **camada** (domain, service, repository) ou por **feature** (user, order, payment)
- Camada por feature é preferível para projetos grandes

### `pkg/`
- Somente para código genuinamente reutilizável e estável
- Evite colocar lógica de negócio aqui
- Mantenha pequeno — a maioria das coisas pertence a `internal/`

## Injeção de Dependências

Go favorece **injeção manual** (sem framework):

```go
// Defina interfaces no pacote consumidor
package service

type UserRepository interface {
    FindByID(ctx context.Context, id string) (*User, error)
    Save(ctx context.Context, u *User) error
}

type UserService struct {
    repo   UserRepository
    cache  Cache
    logger *slog.Logger
}

func NewUserService(repo UserRepository, cache Cache, logger *slog.Logger) *UserService {
    return &UserService{repo: repo, cache: cache, logger: logger}
}
```

Para projetos maiores, considere [wire](https://github.com/google/wire) para geração de código de DI.

## Configuração

```go
// internal/config/config.go
type Config struct {
    Server   ServerConfig
    Database DatabaseConfig
    Log      LogConfig
}

type ServerConfig struct {
    Host         string        `env:"HOST" envDefault:"0.0.0.0"`
    Port         int           `env:"PORT" envDefault:"8080"`
    ReadTimeout  time.Duration `env:"READ_TIMEOUT" envDefault:"10s"`
    WriteTimeout time.Duration `env:"WRITE_TIMEOUT" envDefault:"10s"`
}

// Use env + envDefault via github.com/caarlos0/env
func MustLoad() *Config {
    cfg := &Config{}
    if err := env.Parse(cfg); err != nil {
        log.Fatalf("config: %v", err)
    }
    return cfg
}
```

## Logging com slog (Go 1.21+)

```go
// Preferir slog ao invés de fmt.Println ou log.Printf
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))

// Contextual logging
logger.InfoContext(ctx, "usuário criado",
    slog.String("user_id", user.ID),
    slog.String("email", user.Email),
)

// Com atributos agrupados
logger.With(
    slog.String("service", "user"),
    slog.String("request_id", requestID),
).ErrorContext(ctx, "falha ao salvar usuário", slog.Any("error", err))
```

## Makefile Recomendado

```makefile
.PHONY: build test lint clean run

build:
	go build -ldflags="-s -w" -o bin/api ./cmd/api

test:
	go test -race -cover ./...

test-integration:
	go test -race -tags=integration ./...

lint:
	golangci-lint run ./...
	go vet ./...

clean:
	rm -rf bin/

run:
	go run ./cmd/api

tidy:
	go mod tidy
	go mod verify

generate:
	go generate ./...
```

## Inicialização Graciosa (Graceful Shutdown)

```go
func run(ctx context.Context, cfg *Config) error {
    srv := &http.Server{
        Addr:    fmt.Sprintf(":%d", cfg.Port),
        Handler: routes(cfg),
    }
    
    // Inicia servidor em goroutine
    errCh := make(chan error, 1)
    go func() {
        if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
            errCh <- err
        }
    }()
    
    // Aguarda sinal de encerramento ou erro
    select {
    case err := <-errCh:
        return fmt.Errorf("server: %w", err)
    case <-ctx.Done():
        // Graceful shutdown com timeout
        shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()
        return srv.Shutdown(shutdownCtx)
    }
}
```