# Mapanare v3.31.0 — "Tonina" (Go Transpiler)

> Compile Go to native code via Mapanare. `mapanare compile main.go`
> tokenizes Go, translates to Mapanare AST, and runs the full compilation
> pipeline. Go's concurrency model maps naturally to Mapanare's agents
> and streams.

**Status:** DONE
**Estimated scope:** Large (2-3 sessions)
**Breaking:** No
**Prerequisite:** v3.30.0 (TypeScript transpiler completes the high-level language set)

---

## Motivation

Go is the dominant language for cloud infrastructure, microservices, and
concurrent systems. Its concurrency model (goroutines + channels) maps
directly to Mapanare's agent model (agents + streams):

| Go | Mapanare |
|----|----------|
| `go func()` | `spawn agent` |
| `ch <- value` | `agent <- message` |
| `<-ch` | `sync agent` |
| `chan T` | `Stream<T>` |
| `select { case ... }` | `match` on multiple streams |
| `interface{}` | `any` type |
| `error` return | `Result<T, E>` |
| `defer` | drop glue (automatic) |
| `struct` | `struct` (direct mapping) |
| `interface` | `trait` |

Go developers writing concurrent systems get identical semantics with
Mapanare's native compilation pipeline. The transpiler framework from v3.27.0
handles shared patterns; this module implements only Go-specific syntax.

The name "Tonina" (Venezuelan river dolphin) swims between currents —
like Go's goroutines flowing into Mapanare's agent streams.

---

## Items

### 1. Go tokenizer in `.mn` [HIGH]

**File:** `mapanare/self/from_go.mn` (new)
**Reporter:** roadmap
**Fix:** Character-by-character tokenizer for Go 1.21+ syntax:
- Keywords: `break`, `case`, `chan`, `const`, `continue`, `default`, `defer`,
  `else`, `fallthrough`, `for`, `func`, `go`, `goto`, `if`, `import`,
  `interface`, `map`, `package`, `range`, `return`, `select`, `struct`,
  `switch`, `type`, `var`, `nil`, `true`, `false`, `iota`
- Operators: `:=`, `<-`, `...`, `&&`, `||`, `==`, `!=`, `<=`, `>=`, `<<`,
  `>>`, `&^`, `+=`, `-=`, `*=`, `/=`, `%=`
- String literals: `"..."`, `` `...` `` (raw strings)
- Rune literals: `'c'`
- Comments: `//`, `/* ... */`
- Automatic semicolon insertion (Go spec: after identifier, literal, or
  closing `)`/`]`/`}` at end of line)
- No type annotation syntax needed (Go uses `name Type`, not `name: Type`)

### 2. Go AST data structures [HIGH]

**File:** `mapanare/self/from_go.mn`
**Reporter:** roadmap
**Fix:** Go-specific AST nodes:

```mn
enum GoExpr {
    IntLit(Int), FloatLit(Float), StrLit(String), RuneLit(String),
    BoolLit(Bool), NilLit, Name(String),
    BinOp(GoExpr, String, GoExpr), UnaryOp(String, GoExpr),
    Call(GoExpr, List<GoExpr>), MethodCall(GoExpr, String, List<GoExpr>),
    Selector(GoExpr, String), Index(GoExpr, GoExpr),
    SliceExpr(GoExpr, GoExpr, GoExpr),
    CompositeLit(String, List<GoExpr>),
    FuncLit(List<GoParam>, List<GoStmt>),
    TypeAssert(GoExpr, String),
    ChanSend(GoExpr, GoExpr), ChanRecv(GoExpr),
    AddressOf(GoExpr), Deref(GoExpr),
}

enum GoStmt {
    FuncDecl(String, GoExpr, List<GoParam>, List<GoResult>, List<GoStmt>),
    TypeDecl(String, GoType),
    VarDecl(String, String, GoExpr),
    ShortVarDecl(String, GoExpr),
    If(GoStmt, GoExpr, List<GoStmt>, List<GoStmt>),
    For(GoStmt, GoExpr, GoStmt, List<GoStmt>),
    ForRange(String, String, GoExpr, List<GoStmt>),
    Switch(GoExpr, List<GoCase>),
    Select(List<GoCase>),
    Return(List<GoExpr>),
    Assign(List<GoExpr>, List<GoExpr>),
    ExprStmt(GoExpr),
    GoStmt(GoExpr),       // go f()
    DeferStmt(GoExpr),    // defer f()
    Import(List<GoImport>),
    Block(List<GoStmt>),
    Break, Continue,
}
```

### 3. Go parser [HIGH]

**File:** `mapanare/self/from_go.mn`
**Reporter:** roadmap
**Fix:** Recursive descent parser for Go's syntax:
- Function declarations with receivers: `func (p *Person) Name() string`
- Short variable declaration: `x := 5` → `let x = 5`
- Multiple return values: `func div(a, b int) (int, error)` →
  `fn div(a: Int, b: Int) -> Result<Int, String>`
- Composite literals: `Person{Name: "Alice", Age: 30}` →
  constructor call
- Slice expressions: `arr[1:3]` → `arr.substr(1, 3)` or list slice
- Channel operations: `ch <- val` and `<-ch`
- Select statements → match on multiple agent results
- for/range: `for i, v := range items` → `for v in items` (with index)
- Go's if-init pattern: `if err := f(); err != nil` → let + if
- Type assertions: `x.(string)` → typeof check
- Defer: `defer f()` → warn (Mapanare has drop glue instead)

### 4. Walk: goroutines → agents [HIGH]

**File:** `mapanare/self/from_go.mn`
**Reporter:** roadmap
**Fix:** Go's concurrency primitives map to Mapanare agents:
- `go func() { ... }()` → `spawn agent { ... }`
- `ch := make(chan int)` → `let ch: Stream<Int> = stream()`
- `ch <- value` → `ch <- value` (same syntax!)
- `result := <-ch` → `let result = sync ch`
- `select { case v := <-ch1: ... case v := <-ch2: ... }` →
  `match { sync ch1 => ..., sync ch2 => ... }`
- `sync.WaitGroup` → agent sync barriers
- `sync.Mutex` → warn (agents don't need mutexes)

### 5. Walk: interfaces → traits [HIGH]

**File:** `mapanare/self/from_go.mn`
**Reporter:** roadmap
**Fix:**
- `type Stringer interface { String() string }` →
  `trait Stringer { fn to_string(self) -> String }`
- Implicit interface satisfaction → explicit `impl Trait for Type`
  (detect methods on struct that match interface, generate impl block)
- `interface{}` / `any` → Mapanare `any` type
- Embedding: `type ReadWriter interface { Reader; Writer }` →
  combined trait

### 6. Walk: error returns → Result [HIGH]

**File:** `mapanare/self/from_go.mn`
**Reporter:** roadmap
**Fix:** Go's error pattern maps to Mapanare's Result:
- `func f() (int, error)` → `fn f() -> Result<Int, String>`
- `return 0, fmt.Errorf("msg")` → `return Err("msg")`
- `return val, nil` → `return Ok(val)`
- `if err != nil { return 0, err }` → `let val = f()?` (error propagation)
- `errors.New("msg")` → `Err("msg")`

### 7. Walk: structs → structs [MEDIUM]

**File:** `mapanare/self/from_go.mn`
**Reporter:** roadmap
**Fix:** Go structs map almost directly:
- `type Person struct { Name string; Age int }` →
  `struct Person { name: String, age: Int }`
- Methods with receiver: `func (p *Person) Greet()` →
  `impl Person { fn greet(self) }`
- Exported fields (capitalized) → `pub` (note in comment)
- Struct embedding: `type Employee struct { Person; Title string }` →
  flattened fields with forwarded methods
- Tags: `json:"name"` → comment preservation

### 8. Go type mapping [MEDIUM]

**File:** `mapanare/self/from_go.mn`
**Reporter:** roadmap
**Fix:** Register Go type mappings:
| Go | Mapanare |
|----|----------|
| `int`, `int64` | `Int` |
| `int32`, `int16`, `int8` | `Int` (with precision warning) |
| `float64`, `float32` | `Float` |
| `string` | `String` |
| `bool` | `Bool` |
| `byte` / `uint8` | `Int` |
| `rune` / `int32` | `String` (single char) |
| `[]T` (slice) | `List<T>` |
| `[N]T` (array) | `List<T>` (with size warning) |
| `map[K]V` | `Map<K, V>` |
| `chan T` | `Stream<T>` |
| `*T` (pointer) | `T` (value semantics, warn on pointer arithmetic) |
| `interface{}` / `any` | `any` |
| `error` | `String` (or `Result` return type) |
| `func(...)` | `Fn(...)` |

### 9. Go stdlib mapping [LOW]

**File:** `mapanare/self/from_go.mn`
**Reporter:** roadmap
**Fix:** Register Go stdlib shims:
- `fmt`: `Println→print`, `Printf→print(format)`, `Sprintf→format`,
  `Errorf→Err`
- `strings`: `Contains→.contains()`, `HasPrefix→.starts_with()`,
  `HasSuffix→.ends_with()`, `ToLower→.to_lower()`,
  `ToUpper→.to_upper()`, `TrimSpace→.trim()`, `Split→.split()`,
  `Join→.join()`, `Replace→.replace()`, `Index→.index_of()`
- `strconv`: `Atoi→int()`, `Itoa→str()`, `ParseFloat→float()`
- `math`: `Sqrt→math.sqrt`, `Abs→math.abs`, `Floor→math.floor`,
  `Ceil→math.ceil`
- `sort`: `Ints→.sort()`, `Strings→.sort()`, `Slice→.sort_by()`
- `len(s)→len(s)`, `append→.push()`, `make([]T, n)→List<T>`
- `os.Args→sys.args`, `os.Exit→sys.exit`

### 10. Test suite [MEDIUM]

**File:** `tests/go_compat/test_from_go.py` (new, ~500 lines)
**Reporter:** roadmap
**Fix:** 50+ compatibility tests across 15+ test classes:
- Functions with multiple return values
- Structs with methods (value + pointer receivers)
- Interfaces → traits
- Goroutines → agents
- Channels → streams
- Error returns → Result
- for/range loops
- Switch statements
- Short variable declarations
- Composite literals
- Slice operations
- Import statements
- Select statements
- Defer → warning
- End-to-end programs (fizzbuzz, fibonacci, HTTP server sketch)

---

## What's NOT in This Release

- **No generics.** Go generics (`[T any]`) are deferred to a future release.
  Diagnosed with warning.
- **No cgo.** C interop through Go is not supported.
- **No goroutine scheduling semantics.** Mapanare agents are OS threads,
  not green threads. The mapping is semantic, not behavioral.
- **No `reflect` package.** Runtime reflection is not supported.
- **No `unsafe` package.** Pointer arithmetic is not supported.
- **No build tags or conditional compilation.**
- **No package/module system.** Only single-file Go programs are supported
  in this version. Multi-file support is a future item.

---

## Verification

- [ ] `from_go.mn` compiles through the Python bootstrap emitter
- [ ] `mnc compile fizzbuzz.go` produces correct native binary
- [ ] `go func() { ch <- 42 }()` → spawn agent with message send
- [ ] `<-ch` → sync on agent/stream
- [ ] `func f() (int, error)` → `fn f() -> Result<Int, String>`
- [ ] `if err != nil { return 0, err }` → error propagation
- [ ] `type Stringer interface { String() string }` → trait
- [ ] `type Person struct { Name string }` → struct + impl
- [ ] `for _, v := range items` → `for v in items`
- [ ] 50+ compatibility tests pass
- [ ] `bash scripts/rebuild.sh` — golden tests still pass
