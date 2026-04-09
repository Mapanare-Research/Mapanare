# v0.4.0 Summary — "Ready for the World"

**Released:** March 2026
**Theme:** Scope cleanup, C runtime hardening, diagnostics, FFI, self-hosted verification, LSP improvements

---

## What shipped

- **Scope reduction:** moved `gpu.py`, `model.py`, `tensor.py` to `experimental/`; core compiler has zero experimental dependencies
- **VS Code extension extracted:** separate repo (`mapanare-vscode`) with marketplace CI
- **C runtime hardening:** 45 C runtime tests, AddressSanitizer + ThreadSanitizer in CI, SIGTERM/SIGINT graceful shutdown (POSIX + Windows), native CI job
- **Structured diagnostics:** source spans on all AST nodes, `diagnostics.py` with Rust-style colored errors, multi-error recovery in parser, underline spans and fix suggestions
- **C FFI:** `extern "C"` function declarations in grammar, semantic checker, and LLVM emitter; `--link-lib` linker flag passthrough; 20 FFI tests
- **Self-hosted verification:** 75 bootstrap tests (pipeline integrity, LLVM emission, coverage, fixed-point, CLI), enum type registration, two-pass struct registration, `docs/BOOTSTRAP.md`
- **LSP improvements:** incremental parsing, cross-module go-to-definition, semantic-aware autocomplete (trait methods, module exports), inline diagnostics with fix suggestions
- **Discord seeding:** channel copy prepared

## What didn't ship

- MIR deferred to v0.6.0
- Package registry deferred to v0.5.0
- WASM playground deferred to v0.5.0

## Key metrics

| Metric | Value |
|--------|-------|
| C runtime tests | 45 |
| FFI tests | 20 |
| Bootstrap tests | 75 |
| Phases completed | 6/6 |
