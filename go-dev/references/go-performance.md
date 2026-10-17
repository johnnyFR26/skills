# Performance em Go

## Profiling — Primeiro Passo Sempre

> "Measure, don't guess." — Nunca otimize sem dados.

```go
import _ "net/http/pprof"

// Em aplicações HTTP, adicione o endpoint de pprof
func main() {
    // Servidor de profiling em porta separada
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()
    
    // Seu servidor principal...
}
```

```bash
# CPU profiling (30 segundos)
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Heap (alocações de memória)
go tool pprof http://localhost:6060/debug/pprof/heap

# Goroutines
go tool pprof http://localhost:6060/debug/pprof/goroutine

# Block profiling (locks, channel ops)
go tool pprof http://localhost:6060/debug/pprof/block

# Mutex profiling
go tool pprof http://localhost:6060/debug/pprof/mutex

# Análise interativa
(pprof) top 10       # Top 10 funções por uso de CPU
(pprof) web          # Visualização em browser
(pprof) list func    # Análise linha a linha
(pprof) disasm func  # Disassembly

# Geração de relatório SVG
go tool pprof -svg http://localhost:6060/debug/pprof/profile?seconds=10 > cpu.svg
```

### Profiling em Testes

```bash
# Perfil de CPU em teste específico
go test -cpuprofile=cpu.prof -run TestHeavy ./...
go tool pprof cpu.prof

# Perfil de memória
go test -memprofile=mem.prof -run TestHeavy ./...
go tool pprof mem.prof

# Benchmarks com profiling
go test -bench=BenchmarkJSON -cpuprofile=cpu.prof ./...
```

---

## Análise de Alocações

### escape analysis

```bash
# Ver o que escapa para o heap
go build -gcflags="-m" ./...
go build -gcflags="-m=2" ./...  # Mais detalhado

# Exemplo de output:
# ./main.go:42:13: &User{} escapes to heap
# ./main.go:15:10: moved to heap: buf
```

### benchmarks com -benchmem

```go
func BenchmarkProcess(b *testing.B) {
    data := makeTestData()
    b.ReportAllocs()  // Ou use -benchmem flag
    b.ResetTimer()
    
    for i := 0; i < b.N; i++ {
        _ = process(data)
    }
}
```

```
BenchmarkProcess-8    1000000    1234 ns/op    256 B/op    4 allocs/op
                                               ↑           ↑
                                               bytes/op    allocs/op
```

---

## Estratégias de Redução de Alocações

### Pre-alocação de slices

```go
// ❌ Cresce dinamicamente — muitas re-alocações
var result []User
for _, id := range ids {
    result = append(result, getUser(id))
}

// ✅ Pre-aloca com capacidade conhecida
result := make([]User, 0, len(ids))
for _, id := range ids {
    result = append(result, getUser(id))
}

// ✅ Quando o tamanho final é exato
result := make([]User, len(ids))
for i, id := range ids {
    result[i] = getUser(id)
}
```

### strings.Builder e bytes.Buffer

```go
// ❌ Concatenação — N alocações
var s string
for _, part := range parts {
    s += part  // Nova string a cada iteração
}

// ✅ Builder — uma alocação
var sb strings.Builder
sb.Grow(estimatedSize)  // Opcional: pré-aloca
for _, part := range parts {
    sb.WriteString(part)
}
result := sb.String()

// ✅ bytes.Buffer com sync.Pool para reutilização
var bufPool = sync.Pool{
    New: func() any { return new(bytes.Buffer) },
}

func buildResponse(data any) ([]byte, error) {
    buf := bufPool.Get().(*bytes.Buffer)
    buf.Reset()
    defer bufPool.Put(buf)
    
    if err := json.NewEncoder(buf).Encode(data); err != nil {
        return nil, err
    }
    return buf.Bytes(), nil
}
```

### Evitar alocações em hot paths

```go
// ❌ fmt.Sprintf aloca
key := fmt.Sprintf("user:%s", id)

// ✅ strings.Builder sem alocação extra
var key strings.Builder
key.WriteString("user:")
key.WriteString(id)

// ✅ Para operações simples, concatenação é OK se o compilador otimizar
key := "user:" + id  // Frequentemente otimizado pelo compilador

// ❌ Interface boxing — aloca
func process(v interface{}) { ... }
process(42)  // int "boxed" em interface{}

// ✅ Generics eliminam boxing (Go 1.18+)
func process[T any](v T) { ... }
process(42)  // sem boxing
```

---

## Estruturas de Dados

### Slice vs Map vs Struct

```go
// Para lookup frequente com chave string — use map
index := make(map[string]*User, len(users))
for _, u := range users {
    index[u.ID] = u
}
user := index["123"]

// Para iteração sequencial frequente — use slice
// Slices têm melhor cache locality que maps

// Para campos fixos e conhecidos — use struct (zero alocação)
type Metrics struct {
    Requests int64
    Errors   int64
    Latency  int64
}
// vs map[string]int64 — struct é ~5x mais rápido

// ✅ Cache-friendly: arrays de structs vs struct de arrays
// Cache-friendly (dados usados juntos ficam próximos na memória):
type Particles struct {
    X, Y, Z []float64  // struct of arrays
}

// Menos cache-friendly (campos raramente usados polui cache):
type Particle struct {
    X, Y, Z float64
    Name     string    // raramente usado
    Tags     []string  // raramente usado
}
type Particles2 []Particle  // array of structs
```

### sync.Map vs Map + Mutex

```go
// sync.Map: melhor para chaves estáveis, muitas leituras, poucas escritas
var m sync.Map
m.Store("key", value)
v, _ := m.Load("key")

// map + RWMutex: melhor para a maioria dos casos (mais rápido)
type SafeMap struct {
    mu sync.RWMutex
    m  map[string]Value
}

// Benchmark: sync.Map geralmente 2-4x mais lento que mutex para casos gerais
```

---

## JSON Performance

```go
// ✅ json.Encoder/Decoder em vez de Marshal/Unmarshal para streams
json.NewEncoder(w).Encode(data)      // Não aloca buffer extra
json.NewDecoder(r.Body).Decode(&dst) // Streaming

// ✅ Reutilize encoder/decoder quando possível
enc := json.NewEncoder(w)
enc.SetIndent("", "  ")
enc.Encode(data)

// ✅ jsoniter — drop-in replacement 2-6x mais rápido
import jsoniter "github.com/json-iterator/go"
var json = jsoniter.ConfigCompatibleWithStandardLibrary

// ✅ sonic — JSON ultra-rápido (x86/arm64)
import "github.com/bytedance/sonic"

// Para zero-alloc JSON: encoding/json.RawMessage para passthrough
type Response struct {
    Data json.RawMessage `json:"data"`  // Não re-decodifica
}
```

---

## HTTP Client Performance

```go
// ✅ Reutilize http.Client com transport configurado
var httpClient = &http.Client{
    Timeout: 30 * time.Second,
    Transport: &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        IdleConnTimeout:     90 * time.Second,
        DisableCompression:  false,
        // TLS handshake timeout
        TLSHandshakeTimeout: 10 * time.Second,
    },
}

// ❌ Nunca crie http.Client por request — sem connection pooling
resp, err := (&http.Client{}).Get(url)  // NUNCA FAÇA ISSO

// ✅ Leia e feche o body sempre (para reúso de conexão)
resp, err := httpClient.Do(req)
if err != nil { return err }
defer resp.Body.Close()
io.Copy(io.Discard, resp.Body)  // Esgota o body antes de fechar
```

---

## Compilação e Build

```bash
# Binary menor (strip debug info)
go build -ldflags="-s -w" -o bin/app ./cmd/app

# Verificar tamanho do binário
go build -v ./...
du -sh bin/app

# Inlining info
go build -gcflags="-m" ./...

# Desabilitar otimizações para debug
go build -gcflags="all=-N -l" ./...

# Build para produção com PIE
CGO_ENABLED=0 go build -ldflags="-s -w" -trimpath ./...

# Cross-compilation
GOOS=linux GOARCH=amd64 go build -o bin/app-linux ./cmd/app
GOOS=darwin GOARCH=arm64 go build -o bin/app-mac-arm ./cmd/app
GOOS=windows GOARCH=amd64 go build -o bin/app.exe ./cmd/app
```

---

## Runtime Tuning

```bash
# GOMAXPROCS: número de threads OS (padrão = núcleos da CPU)
export GOMAXPROCS=4

# GOMEMLIMIT (Go 1.19+): limite de memória para o GC
export GOMEMLIMIT=1GiB  # ou em bytes: 1073741824

# GOGC: frequência do GC (padrão = 100, ou seja, dobro da memória viva)
export GOGC=200   # GC menos frequente (mais memória, menos CPU)
export GOGC=off   # Desabilita GC (risco: memória ilimitada)
```

```go
import "runtime/debug"

func init() {
    // Soft memory limit (Go 1.19+) — preferível ao GOMEMLIMIT env
    debug.SetMemoryLimit(1 << 30)  // 1GB
    
    // GC target percentage
    debug.SetGCPercent(200)
}
```

---

## Ferramentas de Análise

```bash
# trace: análise de goroutines, GC, syscalls
go test -trace=trace.out ./...
go tool trace trace.out

# pprof web UI
go tool pprof -http=:8080 cpu.prof

# benchstat: comparação estatística de benchmarks
go install golang.org/x/perf/cmd/benchstat@latest
go test -bench=. -count=10 ./... > before.txt
# (faça suas mudanças)
go test -bench=. -count=10 ./... > after.txt
benchstat before.txt after.txt

# perf (Linux): para análise a nível de hardware
go build -o bin/app && perf record ./bin/app && perf report

# Detector de vazamento de goroutines (testes)
go install github.com/uber-go/goleak@latest
func TestMain(m *testing.M) {
    goleak.VerifyTestMain(m)
}
```

---

## Checklist de Performance

**Antes de otimizar:**
- [ ] Identifiquei o gargalo com profiling (não achismo)
- [ ] Tenho benchmark que reproduz o problema
- [ ] Sei a meta de performance (latência P99, throughput, etc.)

**Técnicas comuns:**
- [ ] Pre-alocação de slices com `make([]T, 0, cap)`
- [ ] `strings.Builder` para concatenação
- [ ] `sync.Pool` para objetos de vida curta e cara alocação
- [ ] `json.Encoder/Decoder` em vez de `Marshal/Unmarshal`
- [ ] HTTP Transport configurado com pool de conexões
- [ ] `atomic` para contadores em vez de mutex
- [ ] `GOMEMLIMIT` configurado em produção
- [ ] `-benchmem` para monitorar alocações
- [ ] Race detector em CI (`-race`)

**Armadilhas comuns:**
- [ ] Não usar `defer` em loops quentes (overhead de defer)
- [ ] Não usar `fmt.Sprintf` para keys de cache em hot paths
- [ ] Não criar `http.Client` por request
- [ ] Não ignorar `defer body.Close()` + `io.Copy(io.Discard, body)`