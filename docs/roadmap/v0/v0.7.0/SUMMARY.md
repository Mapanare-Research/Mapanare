# v0.7.0 Summary — "Self-Standing"

**Released:** March 2026
**Test count:** 2,983
**Theme:** Self-hosting completion, observability, developer tools, deployment infrastructure

---

## What shipped

- **v0.6.0 release close:** VERSION bumped, CHANGELOG written, SPEC updated with MIR appendix, bootstrap snapshot updated (22 files), all 2,538 tests passing through MIR pipeline
- **Self-hosted MIR lowering:** `lower.mn` (2,629 lines) — AST → MIR lowering in Mapanare, completing 7-module self-hosted compiler (8,288+ lines total)
- **Self-hosted emitter rewrite:** `emit_llvm.mn` rewritten to consume MIR instead of AST (~1,050 lines), `main.mn` wired to AST → MIR → LLVM pipeline
- **Built-in test runner:** `mapanare test` discovers `@test` functions, `assert` statement in grammar/AST/MIR/emitters, `--filter` flag; 26 test runner tests
- **Agent observability:** OpenTelemetry-compatible tracing (`--trace` flag, console + OTLP HTTP export), Prometheus metrics (`--metrics :PORT`), 33 structured error codes (`MN-X0000` format), C runtime trace hooks; 47 tests
- **DWARF debug info:** `mapanare build -g` emits compile units, functions, line numbers, variables, struct types for gdb/lldb debugging; 40 tests
- **Deployment infrastructure:** `mapanare deploy init` scaffolds Dockerfile, health/readiness endpoints (`/health`, `/ready`, `/status`), supervision trees (one-for-one, one-for-all, rest-for-one), `@supervised` decorator, SIGTERM graceful shutdown; 38 tests

## What didn't ship

- Self-hosted binary compilation (Phase 3) blocked by LLVM struct type identity across multi-module compilation — three-stage bootstrap verification deferred to v1.0.0
- `lldb` verification of DWARF info requires WSL setup

## Key metrics

| Metric | Value |
|--------|-------|
| Tests | 2,983 |
| Self-hosted compiler LOC | 8,288+ |
| Self-hosted modules | 7 |
| `lower.mn` LOC | 2,629 |
| `emit_llvm.mn` LOC | 1,497 |
| Error codes defined | 33 |
| Phases completed | 7/8 (Phase 3 partial) |
