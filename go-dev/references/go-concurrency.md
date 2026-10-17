# Concorrência em Go

## Princípios

> "Don't communicate by sharing memory; share memory by communicating."
> "If in doubt, use a mutex."

**Regras de ouro:**
1. Toda goroutine deve ter caminho de saída determinístico
2. Nunca vaze goroutines — use context ou done channel
3. Prefira canais para transferência de dados, mutex para estado compartilhado
4. Race detector é obrigatório: `go test -race ./...`

---

## Context

O mecanismo central de controle de ciclo de vida:

```go
// ✅ Propagação correta de context
func ProcessBatch(ctx context.Context, items []Item) error {
    // Context com timeout para a operação inteira
    ctx, cancel := context.WithTimeout(ctx, 5*time.Minute)
    defer cancel()
    
    for _, item := range items {
        // Verifica cancelamento antes de cada iteração cara
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
        }
        
        if err := processItem(ctx, item); err != nil {
            return fmt.Errorf("item %v: %w", item.ID, err)
        }
    }
    return nil
}

// ✅ Valores no contexto — tipagem segura
type contextKey string

const (
    requestIDKey contextKey = "requestID"
    userIDKey    contextKey = "userID"
)

func WithRequestID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, requestIDKey, id)
}

func RequestIDFrom(ctx context.Context) (string, bool) {
    id, ok := ctx.Value(requestIDKey).(string)
    return id, ok
}
```

---

## Goroutines com WaitGroup

```go
// ✅ Padrão fan-out com controle de erro
func processAll(ctx context.Context, items []Item) error {
    var (
        wg   sync.WaitGroup
        mu   sync.Mutex
        errs []error
    )
    
    for _, item := range items {
        wg.Add(1)
        go func(item Item) {
            defer wg.Done()
            
            if err := process(ctx, item); err != nil {
                mu.Lock()
                errs = append(errs, fmt.Errorf("item %v: %w", item.ID, err))
                mu.Unlock()
            }
        }(item)  // ✅ Captura item por valor — essencial!
    }
    
    wg.Wait()
    return errors.Join(errs...)
}

// ✅ Com semáforo para limitar concorrência
func processLimited(ctx context.Context, items []Item, concurrency int) error {
    sem := make(chan struct{}, concurrency)
    var wg sync.WaitGroup
    errCh := make(chan error, len(items))
    
    for _, item := range items {
        wg.Add(1)
        sem <- struct{}{}  // Adquire slot
        
        go func(item Item) {
            defer wg.Done()
            defer func() { <-sem }()  // Libera slot
            
            if err := process(ctx, item); err != nil {
                errCh <- err
            }
        }(item)
    }
    
    wg.Wait()
    close(errCh)
    
    var errs []error
    for err := range errCh {
        errs = append(errs, err)
    }
    return errors.Join(errs...)
}
```

---

## Canais

### Padrões Fundamentais

```go
// ✅ Pipeline: produtor → transformador → consumidor
func producer(ctx context.Context, nums []int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)  // Sempre feche o canal no produtor
        for _, n := range nums {
            select {
            case out <- n:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}

func square(ctx context.Context, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            select {
            case out <- n * n:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}

// Uso
ctx := context.Background()
for result := range square(ctx, producer(ctx, []int{1, 2, 3, 4, 5})) {
    fmt.Println(result)
}

// ✅ Fan-out + Fan-in
func merge(ctx context.Context, channels ...<-chan int) <-chan int {
    out := make(chan int)
    var wg sync.WaitGroup
    
    output := func(c <-chan int) {
        defer wg.Done()
        for v := range c {
            select {
            case out <- v:
            case <-ctx.Done():
                return
            }
        }
    }
    
    wg.Add(len(channels))
    for _, c := range channels {
        go output(c)
    }
    
    go func() {
        wg.Wait()
        close(out)
    }()
    
    return out
}
```

### Done Channel Pattern

```go
// ✅ Encerramento limpo com done channel
type Worker struct {
    done chan struct{}
    wg   sync.WaitGroup
}

func NewWorker() *Worker {
    return &Worker{done: make(chan struct{})}
}

func (w *Worker) Start(jobs <-chan Job) {
    w.wg.Add(1)
    go func() {
        defer w.wg.Done()
        for {
            select {
            case job, ok := <-jobs:
                if !ok {
                    return  // Canal fechado
                }
                w.process(job)
            case <-w.done:
                return  // Encerramento solicitado
            }
        }
    }()
}

func (w *Worker) Stop() {
    close(w.done)
    w.wg.Wait()
}
```

---

## errgroup — O Padrão Preferido

```go
import "golang.org/x/sync/errgroup"

// ✅ errgroup: cancela tudo ao primeiro erro
func fetchParallel(ctx context.Context, urls []string) ([]*Response, error) {
    g, ctx := errgroup.WithContext(ctx)
    results := make([]*Response, len(urls))
    
    for i, url := range urls {
        i, url := i, url  // Captura em Go < 1.22
        g.Go(func() error {
            resp, err := fetch(ctx, url)
            if err != nil {
                return fmt.Errorf("fetch %s: %w", url, err)
            }
            results[i] = resp
            return nil
        })
    }
    
    if err := g.Wait(); err != nil {
        return nil, err
    }
    return results, nil
}

// ✅ Com limite de concorrência
func fetchLimited(ctx context.Context, urls []string) ([]*Response, error) {
    g, ctx := errgroup.WithContext(ctx)
    g.SetLimit(10)  // Máximo 10 goroutines simultâneas
    
    results := make([]*Response, len(urls))
    
    for i, url := range urls {
        i, url := i, url
        g.Go(func() error {
            resp, err := fetch(ctx, url)
            if err != nil {
                return err
            }
            results[i] = resp
            return nil
        })
    }
    
    return results, g.Wait()
}
```

---

## sync — Primitivos de Sincronização

### Mutex

```go
// ✅ Encapsula estado mutável com seu mutex
type SafeCounter struct {
    mu    sync.Mutex
    count map[string]int
}

func (c *SafeCounter) Inc(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count[key]++
}

func (c *SafeCounter) Value(key string) int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count[key]
}

// ✅ RWMutex para leituras frequentes
type Cache struct {
    mu    sync.RWMutex
    items map[string]any
}

func (c *Cache) Set(key string, val any) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = val
}

func (c *Cache) Get(key string) (any, bool) {
    c.mu.RLock()          // Lock de leitura — múltiplos leitores simultâneos OK
    defer c.mu.RUnlock()
    v, ok := c.items[key]
    return v, ok
}
```

### sync.Once

```go
// ✅ Singleton/inicialização única thread-safe
type DB struct {
    once     sync.Once
    conn     *sql.DB
    initErr  error
}

func (d *DB) Connection() (*sql.DB, error) {
    d.once.Do(func() {
        d.conn, d.initErr = sql.Open("postgres", dsn)
    })
    return d.conn, d.initErr
}
```

### sync.Map

```go
// ✅ Para casos específicos: muitas goroutines, chaves estáveis
var cache sync.Map

cache.Store("key", value)

if val, ok := cache.Load("key"); ok {
    // val é interface{}, cast necessário
    data := val.(*MyType)
}

// LoadOrStore — atômico
actual, loaded := cache.LoadOrStore("key", newValue)

// Para casos gerais, prefira map + RWMutex (mais performático e type-safe)
```

### sync.Pool

```go
// ✅ Reutilização de objetos caros de alocar
var bufPool = sync.Pool{
    New: func() any {
        return new(bytes.Buffer)
    },
}

func process(data []byte) string {
    buf := bufPool.Get().(*bytes.Buffer)
    buf.Reset()
    defer bufPool.Put(buf)
    
    // Use buf sem preocupação com alocação
    buf.Write(data)
    return buf.String()
}
```

---

## Padrões de Timeout

```go
// ✅ Timeout em operação única
func withTimeout(ctx context.Context, timeout time.Duration, fn func(context.Context) error) error {
    ctx, cancel := context.WithTimeout(ctx, timeout)
    defer cancel()
    return fn(ctx)
}

// ✅ Select com timeout
func readWithTimeout(ch <-chan Data, timeout time.Duration) (Data, error) {
    select {
    case data := <-ch:
        return data, nil
    case <-time.After(timeout):
        return Data{}, errors.New("timeout")
    }
}

// ✅ Ticker periódico com shutdown limpo
func startHealthCheck(ctx context.Context, interval time.Duration) {
    ticker := time.NewTicker(interval)
    defer ticker.Stop()
    
    for {
        select {
        case <-ticker.C:
            if err := checkHealth(ctx); err != nil {
                log.Printf("health check: %v", err)
            }
        case <-ctx.Done():
            return
        }
    }
}
```

---

## Detecção de Race Conditions

```bash
# Sempre rode com -race em desenvolvimento e CI
go test -race ./...
go run -race main.go
go build -race -o bin/app-race ./cmd/app
```

### Padrões que causam races

```go
// ❌ Race: closure captura variável de loop por referência (Go < 1.22)
for _, item := range items {
    go func() {
        process(item)  // item pode ter mudado!
    }()
}

// ✅ Go < 1.22: capture por valor
for _, item := range items {
    item := item  // shadow a variável
    go func() {
        process(item)
    }()
}

// ✅ Go 1.22+: semântica de loop corrigida (nova variável por iteração)
for _, item := range items {
    go func() {
        process(item)  // item é nova variável em cada iteração
    }()
}

// ❌ Race: mapa compartilhado sem lock
m := map[string]int{}
go func() { m["a"] = 1 }()
go func() { _ = m["a"] }()  // RACE!

// ✅ Use sync.RWMutex ou sync.Map
```

---

## Worker Pool Pattern

```go
type WorkerPool struct {
    workers int
    jobs    chan func()
    wg      sync.WaitGroup
}

func NewWorkerPool(workers int) *WorkerPool {
    p := &WorkerPool{
        workers: workers,
        jobs:    make(chan func(), workers*2),
    }
    
    for i := 0; i < workers; i++ {
        p.wg.Add(1)
        go func() {
            defer p.wg.Done()
            for job := range p.jobs {
                job()
            }
        }()
    }
    
    return p
}

func (p *WorkerPool) Submit(fn func()) {
    p.jobs <- fn
}

func (p *WorkerPool) Shutdown() {
    close(p.jobs)
    p.wg.Wait()
}

// Uso
pool := NewWorkerPool(runtime.NumCPU())
defer pool.Shutdown()

for _, task := range tasks {
    task := task
    pool.Submit(func() {
        process(task)
    })
}
```

---

## atomic — Operações Atômicas

```go
import "sync/atomic"

// ✅ Contadores e flags sem mutex
type Metrics struct {
    requests  atomic.Int64
    errors    atomic.Int64
    latencyNs atomic.Int64
}

func (m *Metrics) RecordRequest(latency time.Duration, err error) {
    m.requests.Add(1)
    m.latencyNs.Add(int64(latency))
    if err != nil {
        m.errors.Add(1)
    }
}

func (m *Metrics) ErrorRate() float64 {
    reqs := m.requests.Load()
    if reqs == 0 {
        return 0
    }
    return float64(m.errors.Load()) / float64(reqs)
}

// ✅ Flag de shutdown
type Service struct {
    stopping atomic.Bool
}

func (s *Service) IsRunning() bool {
    return !s.stopping.Load()
}

func (s *Service) Stop() {
    s.stopping.Store(true)
}
```