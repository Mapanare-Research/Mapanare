# Mapanare v0.1.0 — "Foundation"

> Build the initial compiler and prove the language concept works end-to-end.
>
> Core theme: **Bootstrap compiler, dual backends, and a usable toolchain.**

---

## Scope

1. **Lark-based parser** — LALR grammar with precedence climbing
2. **Semantic checker** — two-pass type checker with inference
3. **Python transpiler** — agents → asyncio, signals → reactive, streams → async generators
4. **LLVM backend** — basic function/struct/enum codegen via llvmlite
5. **Runtime library** — agents, signals, streams, Result/Option in Python
6. **CLI** — `mapanare run`, `build`, `check`, `fmt`
7. **LSP server** — diagnostics, hover, go-to-definition
8. **VS Code extension** — syntax highlighting, LSP integration
9. **Standard library** — math, text, time, io, http, log
10. **Benchmarks** — fibonacci, concurrency, streams, matrix multiply
11. **Tests** — 1,400+ tests across parser, semantic, emitters, runtime

---

## What Shipped

### Compiler Pipeline

- Lark LALR grammar (`mapanare.lark`) with 13-level precedence climbing
- Parser transformer: parse tree → AST dataclass nodes
- Two-pass semantic checker with type inference and generics
- Python emitter (transpilation to asyncio-based Python)
- LLVM IR emitter via llvmlite (basic: functions, structs, enums, arithmetic, control flow)

### Language Features

- Functions, closures, lambdas
- Structs with methods, enums with variants
- Pattern matching (`match` expressions with destructuring)
- `if`/`else`, `for..in`, `while` loops
- Type inference, generics with `Option<T>`, `Result<T, E>`
- Agent system: `agent`, `spawn`, `send` (`<-`), `sync`
- Reactive signals: `signal()`, `.value`, computed signals
- Stream processing: `stream()`, `map`, `filter`, `take`, `collect`, `|>` pipe operator
- `print`/`println`, `str`/`int`/`float`/`len` builtins

### Runtime

- `runtime/agent.py` — asyncio-based agent lifecycle
- `runtime/signal.py` — reactive signal graph with subscriber notification
- `runtime/stream.py` — async stream operators with fusion and backpressure
- `runtime/result.py` — Result/Option types

### Developer Tools

- CLI: `run`, `build`, `check`, `fmt`, `jit`, `compile`, `emit-llvm`
- LSP server: diagnostics, hover, go-to-definition, find-references, autocomplete
- VS Code extension: syntax highlighting, LSP integration, snippets
- Formatter: `mapanare fmt`
- Binary distribution: PyInstaller builds, install scripts

### Standard Library

- `std::math`, `std::text`, `std::time`, `std::io`, `std::http`, `std::log`
- Python-only (stdlib rewrite to `.mn` planned for v0.9.0)

### Tests & Benchmarks

- 1,400+ tests: parser, semantic checker, Python emitter, LLVM emitter, runtime
- Benchmarks: fibonacci, concurrency, stream pipeline, matrix multiply

---

## Success Criteria (met)

1. A `.mn` file compiles and runs via `mapanare run`
2. Agents spawn, send messages, and sync correctly
3. LLVM backend produces working native binaries for basic programs
4. LSP provides real-time diagnostics in VS Code
5. 1,400+ tests pass

---

*"The hardest part of building a language is building the first version that works."*
