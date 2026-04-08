# v0.2.0 Summary — "Self-Hosting"

**Released:** March 2026
**Theme:** Self-hosted compiler modules, LLVM codegen improvements, C runtime

---

## What shipped

- **LLVM string/list codegen:** native string operations (`concat`, `eq`, `len`, `slice`, `index`) and list operations (`new`, `push`, `get`, `set`, `len`)
- **C runtime:** lock-free SPSC ring buffers, thread pool with work stealing, core primitives header
- **Self-hosted compiler:** 5,800+ lines of `.mn` — lexer, parser, semantic checker, LLVM emitter
- **Builtins on LLVM:** `str()`, `int()`, `float()` conversion functions
- **Grammar additions:** `while` loops, map literals, implicit top-level statements

## What didn't ship

- No memory management (strings still leak)
- No module resolution
- No traits
- Self-hosted compiler cannot yet produce a working binary (emitter gaps)
- LLVM backend still missing agents, signals, streams
- CHANGELOG still empty

## Key decisions

- Self-hosted compiler uses recursive descent (not Lark) for independence from Python tooling
- Constructor pattern: `let r: T = first_field; return r` (no struct literal syntax yet)
- State-threading pattern for parser (functions thread `pos: Int`)
- C runtime chosen over Rust for minimal dependencies and LLVM interop

## Metrics

| Metric | Value |
|--------|-------|
| Self-hosted compiler LOC | 5,800+ |
| Self-hosted modules | 4 (lexer, parser, semantic, emit_llvm) |
| C runtime files | 2 (mapanare_core.h, mapanare_core.c) |
