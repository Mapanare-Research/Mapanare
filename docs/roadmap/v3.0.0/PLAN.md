# Mapanare v3.0.0 — "La Culebra Se Muerde La Cola"

> The snake bites its own tail. The compiler compiles itself — through C.
> The syntax sheds everything that doesn't earn its place.

**Status:** IN PROGRESS
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** YES (full syntax overhaul + backend change)
**Codename:** Culebra
**Philosophy:** RADICAL. Zero users, zero backwards compatibility concerns. Every
token must justify its existence or die.

---

## Why v3.0.0

Two problems:

**Problem 1: LLVM IR is the wrong bootstrap target.** 137 PHI mismatches, 158 dropped
else branches, 60 break-inside-nested-control. Emit C instead.

**Problem 2: The syntax is bloated.** Mapanare claims to be AI-native but looks like
Rust with Spanish variables. Every `fn`, every `{`, every `struct`, every `impl X for Y`
is a token an LLM pays for and gets nothing back. We have 2 GitHub stars. No users to
break. This is the one moment we can burn it all down and rebuild from scratch.

---

## The Token Argument

Current Mapanare (v2.0):

```
fn fibonacci(n: Int) -> Int {
    if n <= 1 {
        return n
    }
    let a = 0
    let b = 1
    for i in range(2, n + 1) {
        let temp = b
        b = a + b
        a = temp
    }
    return b
}
```

**198 characters. 13 lines.**

Radical Mapanare (v3.0):

```
fibonacci(n: Int) -> Int:
    si n <= 1: da n
    pon a = 0
    pon b = 1
    for i en range(2, n + 1):
        pon temp = b
        b = a + b
        a = temp
    b
```

**~148 characters. 9 lines.**

That's **25% fewer characters** and **30% fewer lines**. At scale (9,400 line compiler),
that's ~2,350 lines eliminated. ~17,500 tokens freed up for the LLM.

---

## The Changes

1. **C emit backend** — bootstrap through C, not LLVM IR
2. **Indentation syntax** — colons + indentation, no braces
3. **Radical keyword reduction** — kill every keyword that can be inferred
4. **Bilingual** — Spanglish primary, English accepted

---

## Part 1: Syntax Overhaul

### What Dies

| Killed | Replacement | Why |
|--------|-------------|-----|
| `struct` keyword | `tipo` for both structs and enums | One keyword for all type definitions. `tipo` is 4 chars vs 6. |
| `enum` keyword | `tipo` with variants | If a `tipo` has variant syntax, it's an enum. No separate keyword needed. |
| `trait` keyword | `modo` (Spanish "way/manner") | 4 chars vs 5. "A modo is a way types can behave." |
| `impl X for Y` | `Y + Modo:` | `+` means "add this capability." 1 char vs 8 (`impl for`). |
| `match` keyword | Overload `si` | Pattern matching IS conditional checking. `si value:` with arms = match. |
| `agent X` keyword | `@X:` | `@` prefix = concurrent. Shorter, visually distinct. |
| `spawn X()` | `@X()` | Spawning is just calling an `@` type. |
| `fn main() {}` | `fn main:` | Entry point. No parens, no braces. |
| Mandatory parens on calls | Optional when unambiguous | `di "hello"` not `di("hello")`. `server.run` not `server.run()`. |
| `pub` keyword | `+` prefix on name | `+name` = public. Shorter than `pub name`. |
| `input`/`output` in agents | `->` and `<-` | Arrow direction = data flow direction. Already used for send. |

### Design Principles

1. **One keyword per concept.** Not `struct` + `enum`. Just `tipo`.
   Not `if` + `match`. Just `si`. But `fn` stays — it's 2 chars and every language has one.
2. **Indentation IS structure.** Colons open blocks. Dedent closes them.
3. **Last expression = return value.** `da`/`return` only for early exits.
4. **Symbols over words when shorter.** `@` for agents, `+` for pub/impl.
5. **Parens only when needed.** Function calls with a single argument or no arguments
   don't need them.

### Syntax Reference

#### Functions

```
fn add(a: Int, b: Int) -> Int:
    a + b

fn greet(name: String) -> String:
    "Hello, " + name + "!"

fn fibonacci(n: Int) -> Int:
    si n <= 1: da n
    pon a = 0
    pon b = 1
    for i en range(2, n + 1):
        pon temp = b
        b = a + b
        a = temp
    b

fn main:
    di "Hello, Mapanare!"
```

`fn` stays — it's 2 characters and every language has a function keyword.
`fn main:` has no `()` because main takes no arguments. No braces — colon + indentation.

#### Types (`tipo` unifies struct + enum)

**Structs** (tipo with fields):

```
tipo Point:
    x: Float
    y: Float

tipo Config:
    host: String
    port: Int
    debug: Bool
```

**Enums** (tipo with variants using `|`):

```
tipo Shape:
    | Circle(Float)
    | Rect(Float, Float)
    | Triangle(Float, Float, Float)

tipo Option<T>:
    | Some(T)
    | None

tipo Result<T, E>:
    | Ok(T)
    | Err(E)
```

The `|` prefix on lines inside a `tipo` means "this is a variant." No `|` means
"this is a field." You can even mix them if you need a base struct with variants
(tagged union with shared fields):

```
tipo Event:
    timestamp: Int
    | Click(x: Int, y: Int)
    | Keypress(key: String)
    | Scroll(delta: Float)
```

#### Control Flow (`si` handles both if/else AND match)

**Simple conditionals:**

```
si temperature > 100:
    di "too hot"
sino si temperature < 0:
    di "freezing"
sino:
    di "just right"
```

**Pattern matching** (si + arms with `=>`):

```
si shape:
    Circle(r) => 3.14159 * r * r
    Rect(w, h) => w * h
    Triangle(a, b, c) => heron(a, b, c)

si result:
    Ok(value) =>
        di "got: " + str(value)
        process value
    Err(e) =>
        di "error: " + e
        da nada
```

How does the parser tell the difference? If the block after `si expr:` contains
`=>` arms, it's a pattern match. Otherwise it's a conditional. Simple.

**Loops:**

```
for item en inventory:
    si item.quantity == 0:
        di item.name + " is out of stock"
        sigue
    process item

mien queue.length > 0:
    pon task = queue.pop
    si task == nada: sal
    execute task
```

#### Agents (`@` prefix)

```
@Classifier:
    text -> String
    label <- String

    fn handle(yo, text: String) -> String:
        si text.contains "bueno":
            da "positive"
        "negative"

fn main:
    pon cls = @Classifier()
    cls.text <- "Mapanare es bueno"
    pon result = sync cls.label
    di result
```

`@Name:` defines a concurrent agent. `->` = input channel. `<-` = output channel.
`@Name()` spawns an instance (replaces `spawn`). The `@` is the visual signal that
says "this thing runs concurrently."

`sync` stays as a keyword because it's a blocking operation that deserves to be visible.

#### Traits (`modo`) and Impl (`+`)

```
modo Display:
    fn show(yo) -> String

modo Eq:
    fn equals(yo, other: Self) -> Bool

Point + Display:
    fn show(yo) -> String:
        "(" + str(yo.x) + ", " + str(yo.y) + ")"

Point + Eq:
    fn equals(yo, other: Point) -> Bool:
        yo.x == other.x and yo.y == other.y
```

`modo` = "way" (a modo defines a way types can behave). `Point + Display:` means
"add the Display capability to Point." Reads naturally.

#### Visibility (`+` prefix instead of `pub`)

```
tipo Server:
    +host: String          # public field
    +port: Int             # public field
    secret_key: String     # private (default)

    +fn new(host: String, port: Int) -> Server:   # public method
        Server { host, port, secret_key: "" }

    fn validate(yo) -> Bool:                     # private method
        yo.secret_key.length > 0
```

`+` before a name = public. No `+` = private. One character vs three (`pub`).

#### Imports

```
usa net::http
usa encoding::json de parse, encode
usa ai::llm de LLMDriver
```

Unchanged from before. `usa`/`import` and `de`/`from` both work.

#### Signals and Streams

```
pon mut count = signal 0
pon doubled = signal:
    count * 2

pon data = stream [1, 2, 3, 4, 5]
pon result = data
    |> filter fn(x): x > 2
    |> map fn(x): x * 10
    |> collect
```

**Lambdas** use `fn(params): expr` inline:

```
pon result = data |> map fn(x):
    pon processed = transform x
    validate processed
    processed
```

#### Error Handling

```
fn divide(a: Float, b: Float) -> Result<Float, String>:
    si b == 0.0:
        da Err "division by zero"
    Ok(a / b)

fn main:
    pon value = divide(10.0, 3.0)?
    di str value
```

`?` operator unchanged. `try`/`catch` use `:` + indent if we add them.

#### GPU

```
@gpu
fn matmul(a: Tensor<Float>[M, K], b: Tensor<Float>[K, N]) -> Tensor<Float>[M, N]:
    a @ b
```

`@gpu` is a decorator on a function.

#### Complete Example: HTTP Server

```
usa net::http::server de Server, route
usa encoding::json

@ApiHandler:
    request -> Request
    response <- Response

    fn handle(yo, req: Request) -> Response:
        si req.path:
            "/health" => Response.ok "alive"
            "/api/users" =>
                pon users = fetch_users()
                Response.json(json.encode users)
            _ => Response.not_found "nope"

fn main:
    pon server = Server.new ":8080"
    server.route "/", @ApiHandler
    di "listening on :8080"
    server.run
```

#### Complete Example: AI Agent Pipeline

```
usa ai::llm de LLMDriver

@Analyst:
    question -> String
    answer <- String

    fn handle(yo, q: String) -> String:
        pon driver = LLMDriver.new "anthropic"
        pon response = driver.complete(q)?
        response.text

@Translator:
    text -> String
    translated <- String

    fn handle(yo, text: String) -> String:
        pon driver = LLMDriver.new "anthropic"
        driver.complete("translate to Spanish: " + text)?
            .text

fn main:
    pon analyst = @Analyst()
    pon translator = @Translator()

    analyst.question <- "what is mapanare?"
    pon answer = sync analyst.answer

    translator.text <- answer
    di sync translator.translated
```

### Indentation Rules

1. **4 spaces per indent level.** Tabs = syntax error.
2. **Colon opens a block.** Next line must be indented.
3. **Dedent closes a block.** No explicit closing token.
4. **Blank lines** don't affect indentation.
5. **Line continuation:** lines ending with an operator (`+`, `|>`, `and`, `or`, `<-`)
   continue on the next line.
6. **Single-line blocks:** `si x > 0: da x` (everything after colon on same line).

### Optional Parentheses Rules

Parens are optional when:

1. **Single-argument function calls:** `di "hello"` = `di("hello")`
2. **Zero-argument method calls:** `server.run` = `server.run()`
3. **String/literal arguments:** `Err "not found"` = `Err("not found")`

Parens are required when:

1. **Multiple arguments:** `add(1, 2)` (need comma separation)
2. **Nested calls:** `di(str(x))` (ambiguity without parens)
3. **Chained after result:** `driver.complete(q)?.text` (need to mark call boundary)

**Rule of thumb:** if removing parens creates ambiguity, keep them.

---

## Part 2: Bilingual Keywords

Every keyword has two forms. Both compile identically. Official docs use Spanglish.

### The Keyword Table

| Spanglish (primary) | English (alias) | Chars | Role |
|---------------------|-----------------|-------|------|
| `pon` | `let` | 3 | Variable declaration |
| `da` | `return` | 2 | Early return only |
| `si` | `if` | 2 | Conditionals AND pattern matching |
| `sino` | `else` | 4 | Else branch |
| `for` | `cada` | 3/4 | Loop (`for` is primary, `cada` is alias) |
| `en` | `in` | 2 | Loop iteration |
| `mien` | `while` | 4 | While loop |
| `sal` | `break` | 3 | Break |
| `sigue` | `continue` | 5 | Continue |
| `nada` | `null` | 4 | Null/none |
| `no` | `not` | 2 | Negation |
| `usa` | `import` | 3 | Import |
| `de` | `from` | 2 | From |
| `yo` | `self` | 2 | Self reference |
| `di` | `print` | 2 | Print (keyword, not function call) |
| `tipo` | `type` | 4 | Type definition (structs + enums) |
| `modo` | `way` | 4 | Trait/interface definition |

### Unchanged Keywords (no alias needed)

```
fn  mut  true  false  and  or  sync  signal  stream  pipe
try  catch  throw  pub
```

### Symbols (no aliases, universal)

| Symbol | Meaning |
|--------|---------|
| `@Name` | Agent definition or spawn |
| `+name` | Public visibility |
| `->` | Input channel / return type arrow |
| `<-` | Output channel / send operator |
| `\|>` | Pipe operator |
| `=>` | Pattern match arm |
| `?` | Error propagation |
| `...` | Empty block (like Python's `pass`) |

### Style Modes (`mapanare fmt`)

```bash
mapanare fmt --style=spanglish src/    # pon, si, da, di, mien, sal, usa, tipo, modo
mapanare fmt --style=english src/      # let, if, return, print, while, break, import, type, way
mapanare fmt --style=mixed src/        # No changes (default)
```

### Both Styles Side by Side

**Spanglish:**

```
usa ai::llm de LLMDriver

@Analyst:
    question -> String
    answer <- String

    fn handle(yo, q: String) -> String:
        pon driver = LLMDriver.new "anthropic"
        pon response = driver.complete(q)?
        response.text

fn main:
    pon bot = @Analyst()
    bot.question <- "que es mapanare?"
    di sync bot.answer
```

**English:**

```
import ai::llm from LLMDriver

@Analyst:
    question -> String
    answer <- String

    fn handle(self, q: String) -> String:
        let driver = LLMDriver.new "anthropic"
        let response = driver.complete(q)?
        response.text

fn main:
    let bot = @Analyst()
    bot.question <- "que es mapanare?"
    print sync bot.answer
```

Same AST. Same binary.

---

## Part 3: C Emit Backend

### The Problem

| Issue | Count | Why C Fixes It |
|-------|-------|----------------|
| PHI node mismatches | 137 | C has no PHI nodes |
| Dropped else branches | 158 | `if/else` in C is just `if/else` |
| Break inside nested control | 60 | `break` in C is just `break` |
| Stage2 runtime crashes | 1 | Tagged unions in C are explicit |
| main.ll size | 53K lines | main.c will be ~15K lines |

### Backend Roles

| Backend | Role | CLI |
|---------|------|-----|
| `emit_c.py` | Default builds, bootstrap | `mapanare build` |
| `emit_c.mn` | Self-hosted bootstrap | Fixed-point target |
| `emit_llvm_mir.py` | Optimized release | `mapanare build --release` |
| `emit_wasm.py` | WebAssembly | `mapanare emit-wasm` |
| Everything else | Archived | Gone |

### MIR to C Mapping

| MIR Construct | C Output |
|---------------|----------|
| `MIRFunction` | `ReturnType func_name(params) { ... }` |
| `MIRBlock` | Sequential statements or `label:` with goto |
| `MIRAlloca` | Local variable declaration |
| `MIRStore`/`MIRLoad` | Assignment / read |
| `MIRCall` | Function call |
| `MIRBranch` | `if (cond) goto t; else goto f;` |
| `MIRJump` | `goto label;` |
| `MIRReturn` | `return value;` |
| `MIRPhi` | **Eliminated** — assign in predecessors |
| `MIRGetField`/`MIRSetField` | `value.field` / `value->field` |
| `MIRSwitch` | `switch (tag) { case 0: ...; }` |
| Struct types | `typedef struct { ... } TypeName;` |
| Enum types | `typedef struct { int tag; union { ... } } EnumName;` |
| String literals | `(MnString){.ptr = "...", .len = N}` |
| Closures | Struct with fn pointer + env pointer |

### Emitted C Quality Checklist

1. **Stack locals for non-escaping values.** `int x = ...` not `malloc`.
2. **Direct function calls.** When target is known, emit `mn_add(a, b)` directly.
3. **Clean loops.** Emit `for`/`while`, not goto webs.
4. **Small structs by value.** Under 16 bytes = by value.
5. **`restrict` on non-aliasing pointers.** Enables vectorization.

### Bootstrap

```
Stage 0: Python compiler --> .mn to C --> gcc --> mnc-stage1
Stage 1: mnc-stage1      --> .mn to C --> gcc --> mnc-stage2
Stage 2: mnc-stage2      --> .mn to C --> diff stage2.c stage3.c --> FIXED POINT
```

### Build Modes

| Command | Backend | Compiler | Use Case |
|---------|---------|----------|----------|
| `mapanare run file.mn` | C | `gcc -O0` / TCC | Dev |
| `mapanare build file.mn` | C | `gcc -O1` | Default |
| `mapanare build --release` | LLVM | `clang -O2 -flto` | Production |
| `mapanare build --release --backend=c` | C | `gcc -O3` | Fast release |

---

## Part 4: Runtime

### Memory Model

| Category | Strategy |
|----------|----------|
| Stack locals | Stack allocation |
| Escaping values | Arena + auto free |
| Shared (across agents) | ARC (reference counting) |
| Collections | Arena-backed, COW on mutation |
| FFI | Manual |

No GC. Arenas + ARC. Same as Swift and Nim.

### Concurrency

Agents = cooperative scheduling on thread pool. Signals = reactive dependency graph.
Streams = async iterators with backpressure. Channels = lock-free SPSC ring buffers.
All already implemented in the C runtime.

---

## Part 5: Migration

```
mapanare migrate --to=v3 src/
mapanare migrate --to=v3 --dry src/
mapanare migrate --to=v3 --check src/
```

Handles: `struct`/`enum` -> `tipo`, `trait` -> `modo`, `impl X for Y` -> `Y + X`,
`match` -> `si`, `agent` -> `@`, `spawn` -> `@`, brace removal, keyword replacement,
implicit return insertion, `pub` -> `+`, paren removal where safe, `fn main()` -> `fn main`.

~600 lines of Python (more complex now due to structural changes, not just keywords).

---

## Part 6: Culebra Updates

- [ ] Generate tests using radical syntax
- [ ] Validate both Spanglish and English keyword forms produce identical output
- [ ] `culebra scan output.c` — generated C analysis
- [ ] `culebra compare stage2.c stage3.c` — structural diff
- [ ] `culebra fixedpoint` — automated bootstrap convergence
- [ ] Migration validation: v2 -> migrate -> compile -> identical semantics

---

## Phase Summary

| Phase | Description | Est. Lines | Weeks |
|-------|-------------|-----------|-------|
| 1.1 | Radical parser rewrite (indentation, tipo, modo, @agents, si-as-match) | ~1,200 | 3 |
| 1.2 | Bilingual lexer | ~300 | 1 |
| 1.3 | Semantic checker updates | ~400 | 1 |
| 2.1 | `emit_c.py` | ~1,500 | 3 |
| 2.2 | `emit_c.mn` | ~1,200 | 2 |
| 2.3 | Bootstrap verification | ~300 | 1 |
| 2.4 | LLVM as optional | ~200 | 0.5 |
| 3.1 | Migration tool | ~600 | 1.5 |
| 3.2 | Migrate all sources | Automated | 0.5 |
| 3.3 | Docs, llms.txt, VS Code extension | Docs | 1.5 |
| 3.4 | Culebra updates | ~300 | 1 |
| 3.5 | Runtime docs | ~300 | 0.5 |
| **Total** | | **~6,300** | **~16** |

### Dependency Chain

```
Phase 1.1 (radical parser)
    |
    +-- Phase 1.2 (bilingual lexer)
    |       |
    |       +-- Phase 1.3 (semantic updates)
    |               |
    |               +-- Phase 3.1 (migration tool)
    |                       |
    |                       +-- Phase 3.2 (migrate all sources)
    |
    +-- Phase 2.1 (emit_c.py)  [parallel with 1.1]
            |
            +-- Phase 2.2 (emit_c.mn)
            |       |
            |       +-- Phase 2.3 (bootstrap)
            |               |
            |               +-- Phase 2.4 (LLVM optional)
            |
            +-- Phase 3.4 (Culebra)

Phase 3.3 (docs) -- parallel
Phase 3.5 (runtime docs) -- parallel
```

Critical path: **1.1 -> 1.2 -> 1.3 -> 2.1 -> 2.2 -> 2.3** (~11 weeks)

---

## Success Criteria

### Must Ship

- [x] Radical parser handles all language features (indent, tipo, modo, @agent — 2026-04-02)
- [x] All golden tests pass with new syntax (15/15 survive migration — 2026-04-02)
- [x] `emit_c.py` correct for all golden tests (15/15 — 2026-04-01)
- [ ] `emit_c.mn` compiles through `emit_c.py`
- [ ] 3-stage bootstrap reaches fixed point
- [x] `pip install mapanare` works without llvmlite (2026-04-02)
- [x] `mapanare migrate --to=v3` converts v2 code (2026-04-02)
- [x] Both Spanglish and English keywords produce identical output (2026-04-01)
- [ ] VS Code extension updated
- [ ] CI green

### Nice-to-Have (v3.1)

- [ ] TCC integration for sub-100ms dev builds
- [ ] Benchmark: C vs LLVM backend
- [ ] Playground updated
- [ ] Cranelift / QBE evaluation

---

## Risks

| Risk | Mitigation |
|------|------------|
| `si` overloaded (if + match) confuses people | Arms with `=>` = match. No arms = if. LLMs handle this fine. Humans learn in 5 min. |
| `@` for agents looks like decorators | It IS a decorator-like concept. Python devs already understand `@` as "special behavior." |
| `+` for pub is unfamiliar | One-time learning cost. 2 chars saved on every public declaration. |
| `tipo` unifying struct+enum is weird | `|` prefix on variants makes it unambiguous. Algebraic data types work this way in ML/Haskell. |
| Optional parens cause ambiguity | Strict rules: optional only for 0-1 args with literals/strings. Required for multi-arg and nesting. |
| Parser rewrite takes longer (3 weeks) | More radical = more parser work. But we're rewriting anyway for indentation. Marginal cost. |
| Migration tool is harder (~600 lines) | Structural transforms (not just keyword swap). But still mechanical and testable. |

---

## What Dies

| Killed | Replacement |
|--------|-------------|
| `struct` keyword | `tipo` |
| `enum` keyword | `tipo` with `\|` variants |
| `trait` keyword | `modo` |
| `impl X for Y` | `Y + X:` |
| `match` keyword | `si` with `=>` arms |
| `agent` keyword | `@Name:` |
| `spawn` keyword | `@Name()` |
| `pub` keyword | `+` prefix |
| `input`/`output` in agents | `->` / `<-` |
| Curly braces | `:` + indentation |
| Mandatory parens | Optional for 0-1 args |
| `fn main()` | `fn main:` |
| English-only keywords | Bilingual (both accepted) |
| llvmlite hard dependency | Optional |
| LLVM as bootstrap | C backend |

## What Lives

| Component | Role |
|-----------|------|
| `emit_c.py` + `emit_c.mn` | Primary backend |
| `emit_llvm_mir.py` | Release builds |
| `emit_wasm.py` | WebAssembly |
| C runtime | Foundation |
| MIR pipeline | Backend-agnostic IR |
| Culebra | Validation |

---

## Open Questions

| Question | Leaning | Notes |
|----------|---------|-------|
| Tab vs spaces? | 4 spaces. Tabs = error. | No ambiguity. |
| `sino si` or `sinosi`? | `sino si` / `else if` | Two words. No new keyword. |
| Empty blocks? | `...` | Like Python's `pass`. |
| `pon mut` or just `mut`? | `pon mut` / `let mut` | Explicit declaration keyword always required. |
| Enforce keyword consistency per file? | No | Mix freely. |
| Keep `spawn` as alias for `@Name()`? | Yes | Bilingual: `spawn` works too. |
| Keep `agent` as alias for `@Name:`? | Yes | Bilingual: `agent Name:` works too. |
| Keep `pub` as alias for `+`? | Yes | Bilingual: `pub` works too. |
| Keep `struct`/`enum` as aliases for `tipo`? | Yes | Bilingual: all old keywords still compile. |
| Keep `trait` as alias for `modo`? | Yes | Bilingual: `trait` still compiles. |
| Keep `impl X for Y` as alias? | Yes | Bilingual: old syntax still compiles. |
| Keep `match` as alias for `si`-with-arms? | Yes | Bilingual: `match` still compiles. |

**The bilingual rule applies to EVERYTHING.** Every radical change has the old syntax
as an accepted alias. The radical syntax is primary (used in docs, examples, `fmt --style=spanglish`).
The conservative syntax always works. Nobody is forced. But the default is radical.

---

## The Punchline

v2.0 Mapanare (conservative):

```
import ai::llm

agent Analyst {
    input question: String
    output answer: String

    fn handle(self, q: String) -> String {
        let driver = LLMDriver.new("anthropic")
        let response = driver.complete(q)?
        return response.text
    }
}

fn main() {
    let bot = spawn Analyst()
    bot.question <- "what is mapanare?"
    print(sync bot.answer)
}
```

**17 lines. 411 characters.**

v3.0 Mapanare (radical):

```
usa ai::llm

@Analyst:
    question -> String
    answer <- String

    fn handle(yo, q: String) -> String:
        pon driver = LLMDriver.new "anthropic"
        pon response = driver.complete(q)?
        response.text

fn main:
    pon bot = @Analyst()
    bot.question <- "que es mapanare?"
    di sync bot.answer
```

**14 lines. ~310 characters. ~25% shorter.**

Both compile. Both produce the same binary. The old syntax is an alias.
The new syntax is the identity.

La culebra se muerde la cola — through C, bilingual, stripped to the bone.

---

## Progress Log

| Date | Milestone | Details |
|------|-----------|---------|
| 2026-04-01 | Phase 2.1: `emit_c.py` complete | 15/15 golden tests pass through C backend. ~1,700 lines. Handles all 45 MIR instructions. CLI: `mapanare emit-c`. |
| 2026-04-01 | Phase 1.2: Bilingual keywords | 17 keyword pairs (pon/let, si/if, da/return, etc.). Regex terminals with word-boundary lookahead. New `continue`/`sigue` keyword. 878 tests pass. Both forms produce identical output. |
| 2026-04-01 | Phase 1.1 (partial): `tipo` + `modo` | `tipo Name { fields }` → StructDef, `tipo Name { \| variants }` → EnumDef. `modo`/`way` accepted as trait keyword. BAR terminal added. Works end-to-end through C backend. |
| 2026-04-02 | Phase 1.1 (partial): `@Agent` + channels | `@Name { ... }` agent syntax, `name -> Type` / `name <- Type` arrow channels. |
| 2026-04-02 | Phase 1.1: Indentation preprocessor | Source-level colon+indent → brace converter. `fn main:`, `si x > 0:`, `sino:`, `cada i en:`, `mien:`, `tipo:`. Full backward compat with braces. Mixed syntax works. |
| 2026-04-02 | Phase 2.4: LLVM optional | llvmlite moved to `[llvm]` extras. `mapanare run` defaults to C backend. `--release` for LLVM. `pip install mapanare` works without llvmlite. |
| 2026-04-02 | Phase 3.1: Migration tool | `mapanare migrate --to=v3`. struct→tipo, enum→tipo with \|, trait→modo, keywords→spanglish. Keeps braces (robust). |
| 2026-04-02 | Phase 3.2: Migrate 93 files | Golden tests, examples, stdlib, crawl, dato, scan, fuzz. Bilingual keywords applied. Self-hosted files fixed (si→si_idx, en→en_idx). |
| 2026-04-02 | Phase 2.2: `emit_c.mn` | Self-hosted C emitter — 770 lines of Mapanare (replaces 3,248 lines LLVM emitter). 32 functions, parses clean. |
| 2026-04-02 | Keyword conflict fixes | Fixed si/da/en variable name conflicts across stdlib, self-hosted, crawl, dato. 129 YAML tests recovered. |