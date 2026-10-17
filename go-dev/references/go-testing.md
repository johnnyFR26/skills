# Testes em Go

## Fundamentos

```bash
go test ./...                     # Todos os testes
go test -v ./...                  # Verbose (mostra nomes dos testes)
go test -run TestUser ./...       # Filtro por nome
go test -run TestUser/create      # Sub-teste específico
go test -race ./...               # Com detector de race conditions
go test -cover ./...              # Cobertura básica
go test -coverprofile=c.out ./... # Cobertura detalhada
go tool cover -html=c.out         # Abre relatório no browser
go test -bench=. ./...            # Todos os benchmarks
go test -bench=BenchmarkSort -benchmem ./...  # Com alocações
```

---

## Table-Driven Tests (Padrão Idiomático)

```go
func TestParseEmail(t *testing.T) {
    t.Parallel()
    
    tests := []struct {
        name    string
        input   string
        want    string
        wantErr bool
    }{
        {
            name:  "email válido",
            input: "user@example.com",
            want:  "user@example.com",
        },
        {
            name:    "sem @",
            input:   "invalido",
            wantErr: true,
        },
        {
            name:    "vazio",
            input:   "",
            wantErr: true,
        },
        {
            name:  "com maiúsculas normaliza",
            input: "User@Example.COM",
            want:  "user@example.com",
        },
    }
    
    for _, tc := range tests {
        tc := tc  // Go < 1.22
        t.Run(tc.name, func(t *testing.T) {
            t.Parallel()
            
            got, err := ParseEmail(tc.input)
            
            if tc.wantErr {
                if err == nil {
                    t.Errorf("ParseEmail(%q) = %q, queria erro", tc.input, got)
                }
                return
            }
            
            if err != nil {
                t.Fatalf("ParseEmail(%q) erro inesperado: %v", tc.input, err)
            }
            
            if got != tc.want {
                t.Errorf("ParseEmail(%q) = %q, quer %q", tc.input, got, tc.want)
            }
        })
    }
}
```

---

## Helpers e Assertions

```go
// ✅ Helper para verificações comuns — evita import de biblioteca externa
func assertEqual[T comparable](t *testing.T, got, want T) {
    t.Helper()  // Mostra linha do CALLER, não desta função
    if got != want {
        t.Errorf("got %v, want %v", got, want)
    }
}

func assertNoError(t *testing.T, err error) {
    t.Helper()
    if err != nil {
        t.Fatalf("erro inesperado: %v", err)
    }
}

func assertError(t *testing.T, err error) {
    t.Helper()
    if err == nil {
        t.Fatal("esperava erro, mas não recebeu")
    }
}

func assertErrorIs(t *testing.T, err, target error) {
    t.Helper()
    if !errors.Is(err, target) {
        t.Errorf("erro %v não é %v", err, target)
    }
}

// ✅ Uso
func TestGetUser(t *testing.T) {
    user, err := svc.GetUser(ctx, "123")
    assertNoError(t, err)
    assertEqual(t, user.Name, "João")
}
```

### Bibliotecas Populares

```go
// testify — mais comum (github.com/stretchr/testify)
import (
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestUser(t *testing.T) {
    user, err := svc.GetUser(ctx, "123")
    require.NoError(t, err)           // require: falha e para o teste
    assert.Equal(t, "João", user.Name) // assert: falha mas continua
    assert.NotNil(t, user.CreatedAt)
    assert.True(t, user.Active)
    
    // Verificação de erro específico
    _, err = svc.GetUser(ctx, "inexistente")
    require.ErrorIs(t, err, ErrNotFound)
}
```

---

## Mocks e Test Doubles

### Mock Manual (preferível para interfaces pequenas)

```go
// Interface sendo testada
type EmailSender interface {
    Send(ctx context.Context, to, subject, body string) error
}

// Mock manual
type mockEmailSender struct {
    calls []emailCall
    err   error
}

type emailCall struct {
    to, subject, body string
}

func (m *mockEmailSender) Send(ctx context.Context, to, subject, body string) error {
    m.calls = append(m.calls, emailCall{to, subject, body})
    return m.err
}

func (m *mockEmailSender) CalledTimes() int { return len(m.calls) }
func (m *mockEmailSender) LastCall() emailCall {
    if len(m.calls) == 0 {
        panic("nenhuma chamada registrada")
    }
    return m.calls[len(m.calls)-1]
}

// Uso no teste
func TestRegisterUser(t *testing.T) {
    mailer := &mockEmailSender{}
    svc := NewUserService(repo, mailer)
    
    err := svc.Register(ctx, "user@example.com")
    require.NoError(t, err)
    
    assert.Equal(t, 1, mailer.CalledTimes())
    assert.Equal(t, "user@example.com", mailer.LastCall().to)
}

// ✅ Com erro configurável
func TestRegisterUser_EmailFails(t *testing.T) {
    mailer := &mockEmailSender{err: errors.New("SMTP down")}
    svc := NewUserService(repo, mailer)
    
    err := svc.Register(ctx, "user@example.com")
    assert.ErrorContains(t, err, "enviar email")
}
```

### mockery (geração de mocks)

```bash
# Instala
go install github.com/vektra/mockery/v2@latest

# Gera mock para interface
mockery --name=UserRepository --output=./mocks --outpkg=mocks
```

```go
// Uso de mock gerado
import "myapp/mocks"

func TestUserService(t *testing.T) {
    repo := mocks.NewUserRepository(t)
    
    repo.On("FindByID", mock.Anything, "123").
        Return(&User{ID: "123", Name: "João"}, nil)
    
    svc := NewUserService(repo)
    user, err := svc.Get(ctx, "123")
    
    require.NoError(t, err)
    assert.Equal(t, "João", user.Name)
    repo.AssertExpectations(t)
}
```

---

## Testes de Integração

```go
//go:build integration

package repository_test

import (
    "testing"
    "os"
    
    "github.com/jackc/pgx/v5/pgxpool"
)

func TestMain(m *testing.M) {
    // Setup: banco de teste
    pool := setupTestDB()
    defer pool.Close()
    
    os.Exit(m.Run())
}

func setupTestDB() *pgxpool.Pool {
    dsn := os.Getenv("TEST_DATABASE_URL")
    if dsn == "" {
        dsn = "postgres://postgres:postgres@localhost:5432/testdb?sslmode=disable"
    }
    
    pool, err := pgxpool.New(context.Background(), dsn)
    if err != nil {
        log.Fatalf("conectar banco de teste: %v", err)
    }
    
    runMigrations(pool)
    return pool
}

func TestUserRepo_SaveAndFind(t *testing.T) {
    t.Parallel()
    
    // Cada teste usa seu próprio schema para isolamento
    db := newTestDB(t)
    repo := NewUserRepo(db)
    
    user := &User{Name: "João", Email: "joao@test.com"}
    
    err := repo.Save(context.Background(), user)
    require.NoError(t, err)
    require.NotEmpty(t, user.ID)
    
    found, err := repo.FindByID(context.Background(), user.ID)
    require.NoError(t, err)
    assert.Equal(t, user.Name, found.Name)
}

// Helper: cria banco isolado por teste
func newTestDB(t *testing.T) *pgxpool.Pool {
    t.Helper()
    schema := fmt.Sprintf("test_%s", strings.ReplaceAll(t.Name(), "/", "_"))
    // ... cria schema, roda migrations, registra cleanup
    t.Cleanup(func() { dropSchema(schema) })
    return pool
}
```

```bash
# Executar apenas testes de integração
go test -tags=integration -v ./...

# Executar todos
go test -tags=integration -race ./...
```

---

## Benchmarks

```go
func BenchmarkSort(b *testing.B) {
    data := generateData(1000)
    
    b.ResetTimer()  // Zera timer após setup
    
    for i := 0; i < b.N; i++ {
        input := make([]int, len(data))
        copy(input, data)
        sort.Ints(input)
    }
}

// Com -benchmem: mostra alocações por operação
func BenchmarkJSON(b *testing.B) {
    user := &User{ID: "123", Name: "João", Email: "joao@example.com"}
    
    b.Run("marshal", func(b *testing.B) {
        b.ReportAllocs()
        for i := 0; i < b.N; i++ {
            _, err := json.Marshal(user)
            if err != nil {
                b.Fatal(err)
            }
        }
    })
    
    b.Run("unmarshal", func(b *testing.B) {
        data, _ := json.Marshal(user)
        b.ResetTimer()
        b.ReportAllocs()
        for i := 0; i < b.N; i++ {
            var u User
            if err := json.Unmarshal(data, &u); err != nil {
                b.Fatal(err)
            }
        }
    })
}
```

```bash
# Roda benchmark 3 vezes para consistência
go test -bench=BenchmarkJSON -benchmem -count=3 ./...

# Comparação com benchstat
go test -bench=. -benchmem -count=5 ./... > old.txt
# (após mudanças)
go test -bench=. -benchmem -count=5 ./... > new.txt
benchstat old.txt new.txt
```

---

## Fuzz Testing (Go 1.18+)

```go
func FuzzParseJSON(f *testing.F) {
    // Corpus inicial — casos conhecidos
    f.Add(`{"name":"João","age":30}`)
    f.Add(`{}`)
    f.Add(`{"name":""}`)
    
    f.Fuzz(func(t *testing.T, data string) {
        // Deve nunca panic — apenas retornar erro
        var result map[string]any
        if err := json.Unmarshal([]byte(data), &result); err != nil {
            return  // Erro esperado para inputs inválidos
        }
        
        // Re-serialização deve ser idempotente
        encoded, err := json.Marshal(result)
        if err != nil {
            t.Fatalf("marshal falhou após unmarshal bem-sucedido: %v", err)
        }
        
        var result2 map[string]any
        if err := json.Unmarshal(encoded, &result2); err != nil {
            t.Fatalf("segundo unmarshal falhou: %v", err)
        }
    })
}
```

```bash
# Modo fuzz ativo (busca inputs que causam falha)
go test -fuzz=FuzzParseJSON -fuzztime=60s ./...

# Corpus de bugs encontrados fica em testdata/fuzz/
# Testes normais re-rodam o corpus automaticamente
```

---

## httptest — Testando Handlers HTTP

```go
func TestUserHandler_Get(t *testing.T) {
    // Setup
    mockSvc := &mockUserService{
        user: &User{ID: "123", Name: "João"},
    }
    handler := NewUserHandler(mockSvc)
    
    // Cria servidor de teste
    srv := httptest.NewServer(handler.Routes())
    defer srv.Close()
    
    // Faz requisição
    resp, err := http.Get(srv.URL + "/users/123")
    require.NoError(t, err)
    defer resp.Body.Close()
    
    assert.Equal(t, http.StatusOK, resp.StatusCode)
    
    var got User
    require.NoError(t, json.NewDecoder(resp.Body).Decode(&got))
    assert.Equal(t, "João", got.Name)
}

// Para testes unitários de handler sem servidor TCP
func TestUserHandler_Get_Unit(t *testing.T) {
    mockSvc := &mockUserService{user: &User{ID: "123", Name: "João"}}
    handler := NewUserHandler(mockSvc)
    
    req := httptest.NewRequest("GET", "/users/123", nil)
    w := httptest.NewRecorder()
    
    handler.ServeHTTP(w, req)
    
    resp := w.Result()
    assert.Equal(t, http.StatusOK, resp.StatusCode)
    
    var got User
    json.NewDecoder(resp.Body).Decode(&got)
    assert.Equal(t, "João", got.Name)
}
```

---

## Golden Files

Para outputs grandes ou complexos (HTML, JSON, SQL):

```go
func TestGenerateReport(t *testing.T) {
    got := GenerateReport(testData)
    
    golden := filepath.Join("testdata", t.Name()+".golden")
    
    if *update {  // go test -update atualiza os golden files
        os.WriteFile(golden, []byte(got), 0644)
    }
    
    want, err := os.ReadFile(golden)
    require.NoError(t, err)
    
    assert.Equal(t, string(want), got)
}

var update = flag.Bool("update", false, "atualiza golden files")
```

```bash
go test -run TestGenerateReport -update ./...  # Atualiza expected
go test -run TestGenerateReport ./...          # Verifica
```

---

## testcontainers — Dependências Reais

```go
import "github.com/testcontainers/testcontainers-go/modules/postgres"

func TestWithRealPostgres(t *testing.T) {
    ctx := context.Background()
    
    container, err := postgres.RunContainer(ctx,
        testcontainers.WithImage("postgres:16"),
        postgres.WithDatabase("testdb"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready to accept connections").
                WithOccurrence(2),
        ),
    )
    require.NoError(t, err)
    defer container.Terminate(ctx)
    
    dsn, err := container.ConnectionString(ctx, "sslmode=disable")
    require.NoError(t, err)
    
    db, err := sql.Open("postgres", dsn)
    require.NoError(t, err)
    
    // Testes com banco real
    repo := NewUserRepo(db)
    // ...
}
```

---

## Cobertura — Metas e Interpretação

```bash
# Gera relatório detalhado
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out   # Por função
go tool cover -html=coverage.out   # No browser

# Exige cobertura mínima (CI)
go test -cover ./... | grep -E "coverage: [0-9]+\.[0-9]+%" | \
  awk '{if ($2+0 < 80) exit 1}'
```

**Metas realistas:**
- Domínio/lógica de negócio: 90%+
- Handlers e integrações: 70%+
- `main.go` e `cmd/`: ignorar
- Gerado por código: ignorar

**Cobertura 100% não é objetivo** — foque em testar comportamentos, não linhas.