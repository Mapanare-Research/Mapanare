# v0.1.0 Summary — "Foundation"

**Released:** March 2026
**Test count:** 1,400+
**Theme:** Bootstrap compiler, dual backends, usable toolchain

---

## What shipped

- **Full compiler pipeline:** Lark LALR parser → AST → semantic checker → Python emitter + LLVM emitter
- **All core language features:** functions, structs, enums, pattern matching, generics, agents, signals, streams, pipes
- **Python runtime:** asyncio agents, reactive signals, async streams, Result/Option
- **LLVM backend (basic):** functions, structs, enums, arithmetic, control flow — no agents/signals/streams yet
- **Developer tools:** CLI (run/build/check/fmt/jit), LSP server, VS Code extension, formatter
- **Standard library:** 6 modules (math, text, time, io, http, log) — Python only
- **Binary distribution:** PyInstaller builds, install scripts for Unix + Windows
- **1,400+ tests** across the full pipeline

## What didn't ship

- No memory management strategy (strings leak in LLVM backend)
- No module resolution (imports parse but don't resolve)
- No traits/interfaces
- No FFI
- String-based type comparisons in semantic checker
- LLVM backend missing headline features (agents, signals, streams)
- Empty CHANGELOG

## Key decisions

- Chose Lark LALR over hand-written parser for bootstrap speed
- Chose llvmlite over raw LLVM C API for Python interop
- Agent model based on Erlang actors with typed channels
- Python transpiler as primary backend; LLVM as aspirational target

## Metrics

| Metric | Value |
|--------|-------|
| Tests | 1,400+ |
| Grammar rules | ~150 |
| Python emitter LOC | ~800 |
| LLVM emitter LOC | ~600 |
