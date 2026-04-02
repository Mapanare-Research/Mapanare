# Mapanare v3.0.0 — "La Culebra Se Muerde La Cola"

> The snake bites its own tail. The compiler compiles itself — through C.
> The syntax sheds its skin — no braces, no noise, every token earns its place.

**Status:** DRAFT
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** YES (syntax overhaul + backend change)
**Codename:** Culebra

---

## Why v3.0.0

Two problems have been eating us alive:

**Problem 1: LLVM IR is the wrong bootstrap target.** The self-hosted compiler (9,400+
lines of .mn) has been stuck at 99% for months. 137 PHI mismatches, 158 dropped else
branches, 60 break-inside-nested-control bugs. Every LLM we consulted independently
said the same thing: emit C instead.

**Problem 2: The syntax wastes tokens.** Mapanare's thesis is "AI-native." If an LLM
is reading, writing, and reasoning about this language, every unnecessary character
burns context window for zero semantic value. Curly braces, closing brackets,
redundant `return` statements, verbose keywords — all of it is noise.

v3.0.0 fixes both. C backend for the compiler. Indentation-based syntax for the language.

---

## The Token Argument

This is not a style preference. This is a measurable engineering decision.

A fibonacci function in current Mapanare:

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

**198 characters. 13 lines. 6 brace tokens. 2 return keywords (12 chars).**

The same function in v3.0.0:

```
fn fibonacci(n: Int) -> Int:
    si n <= 1:
        da n
    pon a = 0
    pon b = 1
    for i en range(2, n + 1):
        pon temp = b
        b = a + b
        a = temp
    b
```

**~165 characters. 10 lines. 0 brace tokens. `da` instead of `return` (8 chars saved).**

That's roughly **17% fewer characters** on a small function. On the self-hosted
compiler (9,400 lines), the savings compound:

| Metric | v2.0 (braces) | v3.0 (indentation) | Savings |
|--------|---------------|-------------------|---------|
| Lines | 9,400 | ~7,800 | ~17% fewer lines |
| Characters | ~280K est. | ~225K est. | ~20% fewer chars |
| LLM tokens | ~70K est. | ~58K est. | ~12-15% fewer tokens |
| Closing-brace-only lines | ~1,400 | 0 | Eliminated |

**12-15% fewer tokens means the LLM can hold more of your program in context at once.**
That's not aesthetics. That's the LLM seeing 15% more code in a single pass, catching
15% more bugs, understanding 15% more of the program structure.

For a language that claims to be AI-native, this is table stakes.

---

## The Three Changes

In priority order:

1. **C emit backend** — bootstrap through C, not LLVM IR
2. **Indentation-based syntax** — colons + indentation, no braces
3. **Bilingual keywords** — Spanglish primary, English accepted. Every keyword has both forms.

---

## Part 1: Syntax Overhaul

### Design Principles

1. **Every token must carry meaning.** If a token exists only for the parser's benefit
   and an LLM/human can infer it from structure, remove it.
2. **Indentation IS the structure.** Like Python, like Haskell, like Nim. Whitespace
   is not decoration, it's syntax. Colons open blocks. Dedent closes them.
3. **Implicit returns.** The last expression in a block is its value. `da` (return)
   is only needed for early returns.
4. **No semicolons.** One statement per line. Newline is the terminator.
5. **No parentheses on control flow.** `si x > 0:` not `si (x > 0):`.
6. **Minimal punctuation overall.** Parentheses only for function calls and grouping math.

### Syntax Changes

| Feature | v2.0 (current) | v3.0 (new) | Tokens saved |
|---------|----------------|------------|-------------|
| Block delimiters | `{ ... }` | `:` + indentation | 2 per block |
| Function body | `fn foo() { ... }` | `fn foo():` + indent | 2 |
| If/else | `si x { ... } sino { ... }` | `si x:` ... `sino:` | 4 |
| For loop | `cada i en list { ... }` | `cada i en list:` + indent | 2 |
| While loop | `mien x > 0 { ... }` | `mien x > 0:` + indent | 2 |
| Match arms | `Ok(v) => { ... }` | `Ok(v) =>` + indent (or single line) | 2 per arm |
| Agent body | `agent Foo { ... }` | `agent Foo:` + indent | 2 |
| Trait body | `trait Foo { ... }` | `trait Foo:` + indent | 2 |
| Impl body | `impl Foo for Bar { ... }` | `impl Foo for Bar:` + indent | 2 |
| Return | `return value` / `da value` | Last expression is implicit. `da` for early return only. | 1 per function |
| Print | `di(value)` | `di value` (keyword, not function call) | 2 (parens) |
| Main | `fn main() { ... }` | `fn main:` | 4 (`()` + `{}`) |

### Syntax Reference

#### Functions

```
fn add(a: Int, b: Int) -> Int:
    a + b

fn greet(name: String) -> String:
    "Hello, " + name + "!"

fn fibonacci(n: Int) -> Int:
    si n <= 1:
        da n
    pon a = 0
    pon b = 1
    for i en range(2, n + 1):
        pon temp = b
        b = a + b
        a = temp
    b
```

No braces. No explicit return for the last expression. `da` only for early returns.
`fn main:` has no `()` because main takes no arguments.

#### Control Flow

```
si temperature > 100:
    di "too hot"
sino si temperature < 0:
    di "freezing"
sino:
    di "just right"

for item en inventory:
    si item.quantity == 0:
        di item.name + " is out of stock"
        sigue
    process(item)

mien queue.length() > 0:
    pon task = queue.pop()
    si task == nada:
        sal
    execute(task)
```

`si`/`sino` = if/else. `for`/`en` = for/in (or `cada`/`en`). `mien` = while. `sal` = break.
`sigue` = continue. `nada` = null/none. No parentheses around conditions.

#### Structs and Enums

```
struct Point:
    x: Float
    y: Float

enum Shape:
    Circle(Float)
    Rect(Float, Float)

fn area(s: Shape) -> Float:
    match s:
        Circle(r) => 3.14159 * r * r
        Rect(w, h) => w * h
```

Match arms use `=>` for single expressions. Multi-line arms use indentation:

```
match result:
    Ok(value) =>
        di "got: " + str(value)
        process(value)
    Err(e) =>
        di "error: " + e
        da nada
```

#### Agents

```
agent Classifier:
    input text: String
    output label: String

    fn handle(yo, text: String) -> String:
        si text.contains("bueno"):
            da "positive"
        "negative"

fn main:
    pon cls = spawn Classifier()
    cls.text <- "Mapanare es bueno"
    pon result = sync cls.label
    di result
```

`yo` = self. Agents use `:` + indentation like everything else.

#### Signals and Streams

```
pon mut count = signal(0)
pon doubled = signal:
    count * 2

pon data = stream([1, 2, 3, 4, 5])
pon result = data
    |> filter fn(x): x > 2
    |> map fn(x): x * 10
    |> collect
```

Inline lambdas: `fn(params): expression`. Multi-line lambdas use indentation:

```
pon result = data |> map fn(x):
    pon processed = transform(x)
    validate(processed)
    processed
```

#### Traits and Impl

```
trait Display:
    fn show(yo) -> String

trait Eq:
    fn equals(yo, other: Self) -> Bool

impl Display for Point:
    fn show(yo) -> String:
        "(" + str(yo.x) + ", " + str(yo.y) + ")"

impl Eq for Point:
    fn equals(yo, other: Point) -> Bool:
        yo.x == other.x and yo.y == other.y
```

#### Imports

```
usa net::http
usa encoding::json de parse, encode
usa ai::llm de LLMDriver
```

`usa` = import/use. `de` = from.

#### Error Handling

```
fn divide(a: Float, b: Float) -> Result<Float, String>:
    si b == 0.0:
        da Err("division by zero")
    Ok(a / b)

fn main:
    pon value = divide(10.0, 3.0)?
    di str(value)
```

`?` operator unchanged. `try`/`catch` if we add them later also use `:` + indent.

#### GPU and WASM (unchanged semantics, new syntax)

```
@gpu
fn matmul(a: Tensor<Float>[M, K], b: Tensor<Float>[K, N]) -> Tensor<Float>[M, N]:
    a @ b
```

#### Complete Example: HTTP Server

```
usa net::http::server de Server, route
usa encoding::json

agent ApiHandler:
    input request: Request
    output response: Response

    fn handle(yo, req: Request) -> Response:
        match req.path:
            "/health" => Response.ok("alive")
            "/api/users" =>
                pon users = fetch_users()
                Response.json(json.encode(users))
            _ => Response.not_found("nope")

fn main:
    pon server = Server.new(":8080")
    server.route("/", ApiHandler)
    di "listening on :8080"
    server.run()
```

### Indentation Rules

1. **One indent level = 4 spaces.** Tabs are a syntax error.
2. **Colon opens a block.** The next line must be indented.
3. **Dedent closes a block.** No explicit closing token.
4. **Blank lines are allowed** anywhere and don't affect indentation.
5. **Line continuation:** A line ending with an operator (`+`, `|>`, `and`, `or`, etc.)
   continues on the next line at the current or deeper indentation.
6. **Single-line blocks** are allowed: `si x > 0: da x` (everything on one line after the colon).

### What About `match` Arms?

Match is the one place where indentation-only gets slightly verbose. Two options:

**Option A: Indentation (chosen)**

```
match shape:
    Circle(r) => 3.14 * r * r
    Rect(w, h) => w * h
```

Single-expression arms stay on one line after `=>`. Multi-line arms indent:

```
match result:
    Ok(v) =>
        di v
        process(v)
    Err(e) =>
        log_error(e)
        nada
```

**Option B: Was considered and rejected** — using `|` like Haskell/OCaml.
Too unfamiliar, adds a new sigil for no savings.

---

## Part 2: Bilingual Keywords

### The Big Idea

Every keyword has two forms: Spanglish (primary, used in official docs/examples) and
English (accepted, for developers who prefer it). The compiler treats both identically.
Same AST, same MIR, same binary. Write whichever feels natural.

```
# These compile to the exact same thing:

pon x = 42          let x = 42
si x > 0:           if x > 0:
    di x                print x
sino:               else:
    di "nope"           print "nope"
```

### Grammar Rule

For the parser, each bilingual keyword is just an OR:

```
var_decl:  ("pon" | "let") IDENT "=" expr
if_stmt:   ("si" | "if") expr ":" block [("sino" | "else") ":" block]
for_stmt:  ("for" | "cada") IDENT ("en" | "in") expr ":" block
while_stmt: ("mien" | "while") expr ":" block
...
```

One line per keyword in the grammar. Zero runtime cost. The lexer emits the same
token type regardless of which spelling was used.

### The Keyword Table

| Spanglish (primary) | English (alias) | Chars | Notes |
|---------------------|-----------------|-------|-------|
| `pon` | `let` | 3 | "Put." `pon x = 0` / `let x = 0` |
| `da` | `return` | 2 | "Gives." Only for early returns. |
| `si` | `if` | 2 | |
| `sino` | `else` | 4 | `sino si` / `else if` both work for elif |
| `for` | `cada` | 3/4 | `for` is primary because it's shorter. `cada` accepted as alias. |
| `en` | `in` | 2 | Pairs with both `for` and `cada` |
| `mien` | `while` | 4 | Abbrev "mientras" |
| `sal` | `break` | 3 | "Get out" |
| `sigue` | `continue` | 5 | "Keep going" |
| `nada` | `null` | 4 | "Nothing" |
| `no` | `not` | 2 | Universal |
| `usa` | `import` | 3 | "Use" |
| `de` | `from` | 2 | "From/of" |
| `yo` | `self` | 2 | "I/me" |
| `di` | `print` | 2 | "Say/tell." Keyword: `di value` not `di(value)` |

### Unchanged Keywords (no alias needed)

These are already short, universal, or identical in both languages:

```
fn  mut  true  false  and  or  struct  enum  match  trait  impl  pub
agent  spawn  sync  signal  stream  pipe  try  catch  throw  tipo
```

### Rejected Single-Character Keywords

| Proposed | Rejected Because |
|----------|-----------------|
| `v` for true | Collides with variable names |
| `f` for false | Collides with variable names |
| `n` for null | Collides with variable names |
| `o` for or | Parser ambiguity with identifiers |
| `y` for and | Parser ambiguity with identifiers |

### Style Modes (optional, via `mapanare fmt`)

The formatter can normalize to a preferred style:

```bash
mapanare fmt --style=spanglish src/    # pon, si, da, di, mien, sal, usa
mapanare fmt --style=english src/      # let, if, return, print, while, break, import
mapanare fmt --style=mixed src/        # No changes, accept whatever is written
```

Default is `mixed` (accept anything). The linter does NOT enforce consistency within
a file. People can mix freely. This is a feature, not a bug: it means an LLM can
write whichever keyword is shortest in context, and a human can write whichever
keyword they think in.

### Before and After

**Spanglish style (primary, used in docs):**

```
usa ai::llm de LLMDriver

fn main:
    pon driver = LLMDriver.new("anthropic")
    pon response = driver.complete("que es mapanare?")?
    di response.text
```

**English style (accepted, same AST):**

```
import ai::llm from LLMDriver

fn main:
    let driver = LLMDriver.new("anthropic")
    let response = driver.complete("que es mapanare?")?
    print response.text
```

**Mixed style (also valid, LLMs will naturally do this):**

```
usa ai::llm de LLMDriver

fn main:
    let driver = LLMDriver.new("anthropic")
    pon response = driver.complete("que es mapanare?")?
    di response.text
```

All three compile to the same binary.

---

## Part 3: C Emit Backend

### The Problem (Numbers)

| Issue | Count | Why C Fixes It |
|-------|-------|----------------|
| PHI node mismatches | 137 | C has no PHI nodes. Assign in predecessor blocks. |
| Dropped else branches | 158 | `if/else` in C is just `if/else`. No block terminators. |
| Break inside nested control | 60 | `break` in C is just `break`. LLVM blocks don't nest. |
| Stage2 runtime crashes | 1 | Tagged unions in C are explicit. No GEP-on-null. |
| main.ll size | 53K lines | main.c will be ~15K lines |

### Backend Roles After v3.0.0

| Backend | Role | CLI |
|---------|------|-----|
| `emit_c.py` | Default builds, bootstrap | `mapanare build` |
| `emit_c.mn` | Self-hosted bootstrap target | Fixed-point |
| `emit_llvm_mir.py` | Optimized release builds | `mapanare build --release` |
| `emit_wasm.py` | WebAssembly (unchanged) | `mapanare emit-wasm` |
| `emit_llvm.py` | Archived (AST-based) | Removed |
| `emit_python*.py` | Archived | Already gone |

### MIR to C Mapping

| MIR Construct | C Output |
|---------------|----------|
| `MIRFunction` | `ReturnType func_name(params) { ... }` |
| `MIRBlock` | `label: { ... }` or sequential statements |
| `MIRAlloca` | Local variable declaration |
| `MIRStore`/`MIRLoad` | Assignment / variable read |
| `MIRCall` | Function call |
| `MIRBranch` | `if (cond) goto t; else goto f;` |
| `MIRJump` | `goto label;` |
| `MIRReturn` | `return value;` |
| `MIRPhi` | **Eliminated** — assign in predecessor blocks |
| `MIRGetField`/`MIRSetField` | `value.field` / `value->field` |
| `MIRSwitch` | `switch (tag) { case 0: ...; }` |
| Struct types | `typedef struct { ... } TypeName;` |
| Enum types | `typedef struct { int tag; union { ... } data; } EnumName;` |
| String literals | `(MnString){.ptr = "...", .len = N}` |
| Closures | Struct with function pointer + environment pointer |

### Emitted C Quality Checklist

Five things that determine whether gcc/clang can optimize our output well:

1. **Stack locals for non-escaping values.** Emit `int x = ...;` not `int* x = malloc(...)`.
2. **Direct function calls.** When MIR knows the exact target, emit `mn_add(a, b)` not a function pointer.
3. **Clean loops.** When MIR has loop structure, emit `for`/`while` in C, not goto webs.
4. **Small structs by value.** Under 16 bytes = pass by value. Larger = pass by pointer.
5. **`restrict` on non-aliasing pointers.** Tells the C compiler it can vectorize.

Everything else (register allocation, instruction selection, SIMD, inlining) gcc/clang handles.

### Bootstrap Path

```
Stage 0: Python compiler compiles .mn --> C --> gcc --> mnc-stage1
Stage 1: mnc-stage1 compiles .mn --> C --> gcc --> mnc-stage2
Stage 2: mnc-stage2 compiles .mn --> C (compare to Stage 1 C output)

diff stage1-output.c stage2-output.c  ==>  EMPTY  ==>  FIXED POINT
```

Compare C source, not binaries. C text is deterministic and human-diffable.

### Build Modes

| Command | Backend | Compiler | Use Case |
|---------|---------|----------|----------|
| `mapanare run file.mn` | C | `gcc -O0` (or TCC) | Dev iteration |
| `mapanare build file.mn` | C | `gcc -O1` | Default builds |
| `mapanare build --release file.mn` | LLVM | `clang -O2 -flto` | Production |
| `mapanare build --release --backend=c` | C | `gcc -O3` | Fast release without LLVM |

---

## Part 4: Runtime Consolidation

### Memory Model

| Category | Strategy | Example |
|----------|----------|---------|
| Stack-local values | Stack allocation | `pon x = 42` |
| Escaping values | Arena + automatic free | Closures, returned structs |
| Shared values (across agents) | Reference counting (ARC) | Agent messages |
| Collections | Arena-backed, COW on mutation | Lists, maps, strings |
| FFI values | Manual | C interop pointers |

No tracing GC. The C runtime already uses arenas. ARC is injected by the emitter
for values that cross agent boundaries. Same strategy as Swift and Nim.

### Concurrency Model (already implemented, needs docs)

- **Agents:** Cooperative scheduling on thread pool with work stealing
- **Signals:** Reactive dependency graph with batched updates
- **Streams:** Async iterators with backpressure (SPSC ring buffer)
- **Channels:** Lock-free SPSC for agent-to-agent messaging

---

## Part 5: Migration

### Automated Tool

```
mapanare migrate --to=v3 src/         # Rewrites .mn files in-place
mapanare migrate --to=v3 --dry src/   # Preview changes
mapanare migrate --to=v3 --check src/ # CI gate: fail if old syntax found
```

The migration handles:

1. **Keyword replacement:** `let` -> `pon`, `return` -> `da`, `if` -> `si`, etc.
   (English keywords still compile, but migration converts to Spanglish primary style.)
2. **Brace removal:** `{` at end of line becomes `:`. Closing `}` lines deleted.
   Indentation preserved (it's already there in properly formatted code).
3. **Implicit return insertion:** Final `da value` at end of function body where
   it's the last expression becomes just `value`.
4. **`di` parenthesis removal:** `di(x)` becomes `di x`.
5. **`fn main()` simplification:** `fn main()` becomes `fn main`.
6. **`for...in` to `for...en`:** Updates the preposition (optional, since `in` still works).

Deterministic and reversible. `mapanare migrate --style=english` migrates only the
syntax (braces, implicit returns) while keeping English keywords. Estimated ~400 lines.

### What Breaks

Everything. Every `.mn` file, VS Code extension, llms.txt, all documentation, AI agent
skills, tree-sitter grammar. This is acceptable because the community is small (2 GitHub
stars) and the migration tool makes it a one-command fix. Better to break now than after adoption.

---

## Part 6: Culebra Updates (v2.0.0 — DONE)

- [x] `culebra scan output.c` — scan generated C for issues (8 C templates)
- [x] `culebra diff stage2.c stage3.c` — structural diff for C files
- [x] `culebra compare stage1.c stage2.c` — metric comparison for C
- [x] `culebra summary stage2.c` — full diagnostic for C (auto-detected)
- [x] `culebra triage stage2.c --brief` — one-line summary for C
- [x] C parser (`c_parser.rs`) — extracts functions, structs, enums, metrics
- [x] 8 C-specific templates: switch-no-break, missing-typedef, null-deref-pattern,
      goto-dead-label, union-tag-mismatch, large-struct-by-value, missing-return,
      buffer-overflow-pattern
- [x] Auto-detect .c vs .ll — zero configuration
- [ ] Generates test cases using both Spanglish and English keyword forms
- [ ] Validates that both keyword forms produce identical AST/MIR/output
- [ ] `culebra fixedpoint ./mnc mnc_all.mn --backend=c` — automated convergence
- [ ] Migration validation: v2 code -> migrate -> compile -> identical semantics

---

## Phase Summary

| Phase | Description | Est. Lines | Weeks |
|-------|-------------|-----------|-------|
| 1.1 | Indentation parser (replace brace grammar) | ~600 | 2 |
| 1.2 | Bilingual lexer (dual keywords, both forms accepted) | ~200 | 0.5 |
| 1.3 | Semantic checker updates | ~100 | 0.5 |
| 2.1 | `emit_c.py` — Python C emitter | ~1,500 | 3 |
| 2.2 | `emit_c.mn` — self-hosted C emitter | ~1,200 | 2 |
| 2.3 | Bootstrap verification (3-stage) | ~300 | 1 |
| 2.4 | LLVM as optional | ~200 | 0.5 |
| 3.1 | Migration tool | ~400 | 1 |
| 3.2 | Migrate all sources | Automated | 0.5 |
| 3.3 | Docs, llms.txt, VS Code extension | Docs | 1 |
| 3.4 | Culebra updates | ~200 | 0.5 |
| 3.5 | Runtime docs | ~300 (docs) | 0.5 |
| **Total** | | **~5,000** | **~13** |

### Dependency Chain

```
Phase 1.1 (indentation parser)
    |
    +-- Phase 1.2 (bilingual lexer)
    |       |
    |       +-- Phase 1.3 (semantic updates)
    |               |
    |               +-- Phase 3.1 (migration tool)
    |                       |
    |                       +-- Phase 3.2 (migrate all sources)
    |
    +-- Phase 2.1 (emit_c.py)  [can start in parallel with 1.1]
            |
            +-- Phase 2.2 (emit_c.mn)
            |       |
            |       +-- Phase 2.3 (bootstrap verification)
            |               |
            |               +-- Phase 2.4 (LLVM optional)
            |
            +-- Phase 3.4 (Culebra updates)

Phase 3.3 (docs) -- parallel
Phase 3.5 (runtime docs) -- parallel
```

Critical path: **1.1 -> 2.1 -> 2.2 -> 2.3** (~8 weeks)

---

## Success Criteria

### Must Ship

- [ ] Indentation parser handles all language features
- [ ] All 15 golden tests pass with new syntax + keywords
- [ ] `emit_c.py` produces correct output for all golden tests
- [ ] `emit_c.mn` exists and compiles through `emit_c.py`
- [ ] 3-stage bootstrap reaches fixed point
- [ ] `pip install mapanare` works without llvmlite
- [ ] `mapanare migrate --to=v3` correctly converts v2 code
- [ ] VS Code extension updated
- [ ] CI passes: golden tests, bootstrap, migration

### Nice-to-Have (v3.1)

- [ ] TCC integration for sub-100ms dev builds
- [ ] Benchmark comparison: C vs LLVM backend
- [ ] Cranelift / QBE evaluation
- [ ] Playground updated with new syntax

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Indentation parsing harder than braces | Parser rewrite takes longer | Python/Nim solved this. INDENT/DEDENT token approach is well-documented. |
| Spanglish keywords reduce adoption | Fewer English-only devs | Bilingual: English keywords always accepted. Zero friction. Spanglish is the brand, not a requirement. |
| C backend perf gap vs LLVM | Slower programs | C -O2 is ~90% of LLVM -O2. Keep LLVM as `--release`. |
| Migration tool misses edge cases | Some .mn files break | Test on 9,400-line self-hosted compiler. If that works, everything works. |
| Indentation annoys some devs | Preference war | Language is for LLMs first. LLMs have token budgets, not brace preferences. |

---

## What Dies

| Component | Action |
|-----------|--------|
| Curly brace block delimiters | Replaced by `:` + indentation |
| `emit_llvm.py` (AST-based) | Archived |
| `emit_llvm.mn` (self-hosted LLVM emitter) | Replaced by `emit_c.mn` |
| English-only keywords | Replaced by bilingual system (Spanglish primary + English accepted) |
| llvmlite as hard dependency | Optional (`mapanare[llvm]`) |
| `main.ll` (53K lines) | Replaced by `main.c` (~15K lines) |
| Explicit return at function end | Implicit last expression |
| Parentheses on `di()` | `di` is a keyword |
| `fn main()` empty parens | `fn main:` |

## What Lives

| Component | Role |
|-----------|------|
| `emit_llvm_mir.py` | Optimized release builds |
| `emit_wasm.py` | WebAssembly (unchanged) |
| `emit_c.py` + `emit_c.mn` | Primary bootstrap + default |
| C runtime | Foundation (unchanged) |
| Culebra | Validation for C + LLVM |
| MIR pipeline | Unchanged (backend-agnostic) |

---

## Open Questions

| Question | Leaning | Notes |
|----------|---------|-------|
| Allow optional braces for one-liners? | No | Clean break. One style. |
| Tab vs spaces? | 4 spaces. Tabs = error. | No ambiguity. |
| `sino si` or `sinosi` for elif? | `sino si` (two words) | Reads naturally. `else if` also works. |
| Empty blocks? | `...` (like Python's `pass`) | `si debug: ...` |
| Trailing colon on `fn main:`? | Yes, always | Consistency. |
| Enforce keyword consistency per file? | No | Let people mix. LLMs will optimize naturally. |
| `mapanare fmt` default style? | `mixed` (no normalization) | `--style=spanglish` and `--style=english` available. |
| `pon mut` or just `mut`? | `pon mut` | Consistent with `let mut` pattern. `mut x = 0` alone is too implicit. |

---

## The Punchline

Mapanare v2.0 looks like Rust with Spanish variable names.
Mapanare v3.0 looks like nothing else. And it speaks both languages.

**Spanglish (official style):**

```
usa ai::llm de LLMDriver

agent Analyst:
    input question: String
    output answer: String

    fn handle(yo, q: String) -> String:
        pon driver = LLMDriver.new("anthropic")
        pon response = driver.complete(q)?
        response.text

fn main:
    pon bot = spawn Analyst()
    bot.question <- "que es mapanare?"
    di sync bot.answer
```

**English (same program, same binary):**

```
import ai::llm from LLMDriver

agent Analyst:
    input question: String
    output answer: String

    fn handle(self, q: String) -> String:
        let driver = LLMDriver.new("anthropic")
        let response = driver.complete(q)?
        response.text

fn main:
    let bot = spawn Analyst()
    bot.question <- "que es mapanare?"
    print sync bot.answer
```

9 lines either way. Zero braces. Zero semicolons. Zero wasted tokens.
Every character carries meaning. Write in the language you think in.

La culebra se muerde la cola — through C, bilingual, without the noise.