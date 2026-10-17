# Padrões Go Idiomáticos

## Tratamento de Erros

### Wrapping e Desempacotamento

```go
// ✅ Wrap com %w para manter a cadeia
func GetUser(ctx context.Context, id string) (*User, error) {
    u, err := repo.FindByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("GetUser(%s): %w", id, err)
    }
    return u, nil
}

// ✅ Verificação com errors.Is (percorre a cadeia)
if errors.Is(err, sql.ErrNoRows) { ... }
if errors.Is(err, context.DeadlineExceeded) { ... }

// ✅ Extração com errors.As
var pgErr *pgconn.PgError
if errors.As(err, &pgErr) && pgErr.Code == "23505" {
    return ErrDuplicate
}
```

### Erros Customizados

```go
// Erro estruturado
type APIError struct {
    Code    int
    Message string
    Cause   error
}

func (e *APIError) Error() string {
    if e.Cause != nil {
        return fmt.Sprintf("API %d: %s: %v", e.Code, e.Message, e.Cause)
    }
    return fmt.Sprintf("API %d: %s", e.Code, e.Message)
}

func (e *APIError) Unwrap() error { return e.Cause }

// Constructors semânticos
func NotFound(resource string) *APIError {
    return &APIError{Code: 404, Message: resource + " não encontrado"}
}

func Unauthorized() *APIError {
    return &APIError{Code: 401, Message: "não autorizado"}
}
```

### Multi-Erro

```go
// Go 1.20+: errors.Join
func validateAll(fields ...Field) error {
    var errs []error
    for _, f := range fields {
        if err := f.Validate(); err != nil {
            errs = append(errs, err)
        }
    }
    return errors.Join(errs...)
}

// Verificação de multi-erro
err := validateAll(fields...)
if err != nil {
    // errors.Is e errors.As percorrem todos os erros joined
    if errors.Is(err, ErrRequired) { ... }
}
```

---

## Interfaces

### Pequenas e Focadas

```go
// ✅ Interface mínima — fácil de mockar e implementar
type Reader interface {
    Read(ctx context.Context, id string) (*Record, error)
}

type Writer interface {
    Write(ctx context.Context, r *Record) error
}

type ReadWriter interface {
    Reader
    Writer
}

// ❌ Interface gigante — difícil de mockar
type UserRepository interface {
    Find(id string) (*User, error)
    FindAll() ([]*User, error)
    FindByEmail(email string) (*User, error)
    Save(u *User) error
    Update(u *User) error
    Delete(id string) error
    Count() (int, error)
    // ... 20 métodos mais
}
```

### Interface no Consumidor

```go
// ✅ O pacote que consome define a interface que precisa
package service

// Definida aqui, implementada em outro pacote (repository)
type UserStore interface {
    FindByID(ctx context.Context, id string) (*User, error)
    Save(ctx context.Context, u *User) error
}

type UserService struct {
    store UserStore
}
```

### Verificação de Implementação em Compilação

```go
// Garante que *PostgresRepo implementa UserStore em tempo de compilação
var _ UserStore = (*PostgresRepo)(nil)

// Ou para interfaces da stdlib
var _ io.Reader = (*MyReader)(nil)
var _ fmt.Stringer = (*User)(nil)
```

---

## Functional Options Pattern

Ideal para structs com muitas configurações opcionais:

```go
type Client struct {
    baseURL    string
    timeout    time.Duration
    maxRetries int
    httpClient *http.Client
    logger     *slog.Logger
}

type ClientOption func(*Client)

func WithTimeout(d time.Duration) ClientOption {
    return func(c *Client) { c.timeout = d }
}

func WithMaxRetries(n int) ClientOption {
    return func(c *Client) { c.maxRetries = n }
}

func WithHTTPClient(hc *http.Client) ClientOption {
    return func(c *Client) { c.httpClient = hc }
}

func NewClient(baseURL string, opts ...ClientOption) *Client {
    c := &Client{
        baseURL:    baseURL,
        timeout:    30 * time.Second,
        maxRetries: 3,
        httpClient: http.DefaultClient,
        logger:     slog.Default(),
    }
    for _, opt := range opts {
        opt(c)
    }
    return c
}

// Uso
client := NewClient("https://api.example.com",
    WithTimeout(10*time.Second),
    WithMaxRetries(5),
)
```

---

## Generics (Go 1.18+)

### Quando usar generics

```go
// ✅ Coleções e algoritmos genéricos
func Map[T, U any](slice []T, f func(T) U) []U {
    result := make([]U, len(slice))
    for i, v := range slice {
        result[i] = f(v)
    }
    return result
}

func Filter[T any](slice []T, pred func(T) bool) []T {
    var result []T
    for _, v := range slice {
        if pred(v) {
            result = append(result, v)
        }
    }
    return result
}

func Reduce[T, U any](slice []T, initial U, f func(U, T) U) U {
    acc := initial
    for _, v := range slice {
        acc = f(acc, v)
    }
    return acc
}

// ✅ Constraints com tipos numéricos
type Number interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64 |
    ~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 |
    ~float32 | ~float64
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}

// ✅ Result type genérico
type Result[T any] struct {
    Value T
    Err   error
}

func (r Result[T]) Unwrap() (T, error) { return r.Value, r.Err }

// ❌ Não use generics apenas para evitar repetição trivial
// ❌ Não use generics quando interface{} com type assertion é mais claro
```

### Constraints da stdlib (golang.org/x/exp/constraints)

```go
import "golang.org/x/exp/constraints"

func Min[T constraints.Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}
```

---

## Builder Pattern

```go
type QueryBuilder struct {
    table      string
    conditions []string
    orderBy    string
    limit      int
    args       []any
}

func NewQuery(table string) *QueryBuilder {
    return &QueryBuilder{table: table}
}

func (q *QueryBuilder) Where(condition string, args ...any) *QueryBuilder {
    q.conditions = append(q.conditions, condition)
    q.args = append(q.args, args...)
    return q
}

func (q *QueryBuilder) OrderBy(col string) *QueryBuilder {
    q.orderBy = col
    return q
}

func (q *QueryBuilder) Limit(n int) *QueryBuilder {
    q.limit = n
    return q
}

func (q *QueryBuilder) Build() (string, []any) {
    sql := fmt.Sprintf("SELECT * FROM %s", q.table)
    if len(q.conditions) > 0 {
        sql += " WHERE " + strings.Join(q.conditions, " AND ")
    }
    if q.orderBy != "" {
        sql += " ORDER BY " + q.orderBy
    }
    if q.limit > 0 {
        sql += fmt.Sprintf(" LIMIT %d", q.limit)
    }
    return sql, q.args
}

// Uso encadeado
query, args := NewQuery("users").
    Where("active = $1", true).
    Where("age > $2", 18).
    OrderBy("created_at DESC").
    Limit(10).
    Build()
```

---

## Padrão Repository

```go
// Domain — sem dependência de infraestrutura
package domain

type User struct {
    ID        string
    Email     string
    Name      string
    CreatedAt time.Time
}

// Repositório definido no domínio
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*User, error)
    FindByEmail(ctx context.Context, email string) (*User, error)
    Save(ctx context.Context, u *User) error
    Delete(ctx context.Context, id string) error
}

// Implementação — em package infrastructure/postgres
package postgres

type userRepo struct {
    db *sql.DB
}

func NewUserRepo(db *sql.DB) domain.UserRepository {
    return &userRepo{db: db}
}

func (r *userRepo) FindByID(ctx context.Context, id string) (*domain.User, error) {
    const q = `SELECT id, email, name, created_at FROM users WHERE id = $1`
    
    var u domain.User
    err := r.db.QueryRowContext(ctx, q, id).Scan(&u.ID, &u.Email, &u.Name, &u.CreatedAt)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, domain.ErrUserNotFound
        }
        return nil, fmt.Errorf("FindByID: %w", err)
    }
    return &u, nil
}
```

---

## Iteradores (Go 1.23+)

```go
import "iter"

// Produz um iterador sobre páginas de resultados
func (r *userRepo) All(ctx context.Context) iter.Seq2[*User, error] {
    return func(yield func(*User, error) bool) {
        rows, err := r.db.QueryContext(ctx, "SELECT * FROM users")
        if err != nil {
            yield(nil, err)
            return
        }
        defer rows.Close()
        
        for rows.Next() {
            var u User
            if err := rows.Scan(&u.ID, &u.Email); err != nil {
                if !yield(nil, err) {
                    return
                }
                continue
            }
            if !yield(&u, nil) {
                return
            }
        }
    }
}

// Uso com range (Go 1.23+)
for user, err := range repo.All(ctx) {
    if err != nil {
        return err
    }
    process(user)
}
```

---

## Middleware HTTP

```go
type Middleware func(http.Handler) http.Handler

// Compose aplica middlewares da esquerda para direita
func Compose(h http.Handler, middlewares ...Middleware) http.Handler {
    for i := len(middlewares) - 1; i >= 0; i-- {
        h = middlewares[i](h)
    }
    return h
}

// Middleware de logging
func LoggingMiddleware(logger *slog.Logger) Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()
            
            wrapped := &responseWriter{ResponseWriter: w, status: http.StatusOK}
            next.ServeHTTP(wrapped, r)
            
            logger.InfoContext(r.Context(), "request",
                slog.String("method", r.Method),
                slog.String("path", r.URL.Path),
                slog.Int("status", wrapped.status),
                slog.Duration("duration", time.Since(start)),
            )
        })
    }
}

type responseWriter struct {
    http.ResponseWriter
    status int
}

func (rw *responseWriter) WriteHeader(status int) {
    rw.status = status
    rw.ResponseWriter.WriteHeader(status)
}

// Middleware de autenticação
func AuthMiddleware(secret string) Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            token := r.Header.Get("Authorization")
            if token == "" {
                http.Error(w, "unauthorized", http.StatusUnauthorized)
                return
            }
            
            claims, err := validateToken(token, secret)
            if err != nil {
                http.Error(w, "invalid token", http.StatusUnauthorized)
                return
            }
            
            ctx := context.WithValue(r.Context(), claimsKey, claims)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

// Composição
handler := Compose(
    mux,
    LoggingMiddleware(logger),
    AuthMiddleware(cfg.JWTSecret),
    RecoveryMiddleware(),
)
```

---

## Padrão de Retry com Backoff

```go
type RetryConfig struct {
    MaxAttempts int
    InitialWait time.Duration
    MaxWait     time.Duration
    Multiplier  float64
}

func Retry(ctx context.Context, cfg RetryConfig, fn func() error) error {
    wait := cfg.InitialWait
    
    for attempt := 1; attempt <= cfg.MaxAttempts; attempt++ {
        err := fn()
        if err == nil {
            return nil
        }
        
        // Não retry em erros não-recuperáveis
        var permErr *PermanentError
        if errors.As(err, &permErr) {
            return err
        }
        
        if attempt == cfg.MaxAttempts {
            return fmt.Errorf("após %d tentativas: %w", attempt, err)
        }
        
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(wait):
            wait = time.Duration(float64(wait) * cfg.Multiplier)
            if wait > cfg.MaxWait {
                wait = cfg.MaxWait
            }
        }
    }
    return nil
}
```