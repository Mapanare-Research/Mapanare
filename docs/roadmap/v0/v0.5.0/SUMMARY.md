# v0.5.0 Summary — "The Ecosystem"

**Released:** March 2026
**Test count:** 2,200+
**Theme:** String interpolation, linter, Python interop, WASM playground, package registry, documentation

---

## What shipped

- **String interpolation:** `"Hello, ${name}!"` syntax in grammar, parser, semantic, both emitters; multi-line strings (`"""..."""`); 25 tests
- **Linter:** `mapanare lint` with 8 rules (unused variables/imports, shadowing, unreachable code, mutable-never-mutated, empty match arm, unchecked Result); `--fix` for auto-fixable rules; LSP integration; `@allow(W001)` suppression; 35 tests
- **Python interop:** `extern "Python"` with module qualifier, type marshalling, `Result<T,String>` error wrapping, `--python-path` flag; tested with `math.sqrt`, `json.loads`, numpy; 37 tests
- **WASM playground:** Vite + CodeMirror 6, Pyodide-based in-browser execution, `.mn` syntax highlighting, share-via-URL, 7 pre-loaded examples, GitHub Pages deploy
- **Package registry:** FastAPI backend in `mapanare-website`, SQLite storage, `mapanare publish`/`search`/`install` CLI commands, semver resolution, package browser React UI, 3 example packages
- **Documentation:** language reference (`docs/reference.md`), cookbook (14 recipes), `mapanare doc` generator from `///` doc comments, stdlib docs, "for X developers" guides (Python/Rust/TypeScript)

## What didn't ship

- Self-hosted compiler does not yet use string interpolation (needs grammar update in self-hosted lexer)
- MIR deferred to v0.6.0

## Key metrics

| Metric | Value |
|--------|-------|
| Tests | 2,200+ |
| Lint rules | 8 |
| Cookbook recipes | 14 |
| Playground examples | 7 |
| Python interop tests | 37 |
| Phases completed | 6/6 |
