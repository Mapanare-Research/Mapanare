# Mapanare v0.5.0 — "The Ecosystem"

> v0.4.0 hardened the compiler and opened the door to the outside world.
> v0.5.0 must build the **infrastructure around it** — so others can adopt,
> share, and contribute.
>
> Core theme: **ecosystem, interop, and reach.**

---

## Scope Rules

1. **Ship the deferred ecosystem items** — linter, Python interop, playground, registry
2. **Add string interpolation** — the most-requested missing syntax feature
3. **No new language primitives** — agents/signals/streams are stable, don't touch semantics
4. **Every item must have a clear "done when" criterion**
5. **Separate deploys** — playground on GitHub Pages (static); registry in `mapanare-website` (Flask + React)

---

## Status Tracking

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (reason noted) |

---

## Phase Overview

| Phase | Name | Status | Sub-phases |
|-------|------|--------|------------|
| 1 | String Interpolation & Language Polish | Complete | — |
| 2 | Linter | Complete | — |
| 3 | Python Interop | Complete | — |
| 4 | WASM Playground | Complete | — |
| 5 | Package Registry | Complete | — |
| 6 | Documentation & Ecosystem | Complete | — |

---

## Phase 1 — String Interpolation & Language Polish
**Priority:** HIGH — most-requested syntax gap; `${expr}` noted as unimplemented in SPEC.md

String interpolation is listed in the spec but never implemented. It's a small
feature with outsized impact on ergonomics and first impressions.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add `${ expr }` interpolation syntax to grammar (`mapanare.lark`) | [x] | Interpolation handled in parser transformer; TRIPLE_STRING added for multi-line |
| 2 | Add `InterpString` AST node (list of literal parts + expression parts) | [x] | `InterpString.parts: list[Expr]` — mix of StringLiteral and Expr |
| 3 | Implement in parser transformer | [x] | Detects `${...}`, splits, re-parses expressions |
| 4 | Implement in semantic checker (type-check interpolated expressions) | [x] | Infers each part; result is always String |
| 5 | Emit for Python backend (f-string or `str.format`) | [x] | Emits as f-string |
| 6 | Emit for LLVM backend (string concatenation of `str()` calls) | [x] | Converts parts to MnString, concatenates via __mn_str_concat |
| 7 | Add multi-line string literals (`"""..."""`) to grammar | [x] | TRIPLE_STRING terminal with priority 4 |
| 8 | Update self-hosted compiler sources to use interpolation where beneficial | [!] | Self-hosted lexer/parser don't support ${} yet; needs self-hosted grammar update first |
| 9 | Add tests: parser, semantic, Python emit, LLVM emit, e2e | [x] | 25 tests in tests/interpolation/ |
| 10 | Update SPEC.md — remove "planned / not yet implemented" label | [x] | Updated string literals section and appendix |

**Done when:** `println("Hello, ${name}!")` compiles and runs on both backends.
Multi-line strings work. SPEC.md is accurate.

---

## Phase 2 — Linter
**Priority:** HIGH — deferred from v0.4.0; essential for code quality at scale

A linter catches mistakes the type system doesn't — unused variables, shadowing,
unreachable code, anti-patterns. Integrated into LSP for real-time feedback.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design lint rule categories and severity levels (error, warning, info) | [x] | LintRule enum W001-W008, all warnings; Severity via diagnostics.py |
| 2 | Create `mapanare/linter.py` — lint pass over AST | [x] | Runs after semantic check; full AST walker with scope tracking |
| 3 | Implement rule: unused variables (`W001`) | [x] | Tracks usage across scopes; _ prefix to suppress |
| 4 | Implement rule: unused imports (`W002`) | [x] | Tracks import items; auto-fixable (line removal) |
| 5 | Implement rule: variable shadowing (`W003`) | [x] | Warns when inner scope shadows outer variable |
| 6 | Implement rule: unreachable code after `return` (`W004`) | [x] | Detects statements after return in same block |
| 7 | Implement rule: mutable variable never mutated (`W005`) | [x] | Tracks mutations; auto-fixable (remove mut) |
| 8 | Implement rule: empty `match` arm body (`W006`) | [x] | Detects empty Block bodies in match arms |
| 9 | Implement rule: agent `handle` without `send` response (`W007`) | [x] | Checks handle methods in agents with outputs |
| 10 | Implement rule: `Result` not checked / `?` not used (`W008`) | [x] | Heuristic: result-producing call names used as bare statements |
| 11 | Add `mapanare lint` CLI command | [x] | Uses diagnostics system from v0.4.0 |
| 12 | Add `mapanare lint --fix` for auto-fixable rules (unused imports, mut removal) | [x] | W002 removes import lines; W005 removes `mut` keyword |
| 13 | Integrate lint warnings into LSP (real-time, as-you-type) | [x] | analyze_document runs linter when no semantic errors |
| 14 | Add `#[allow(rule)]` attribute to suppress individual warnings | [x] | Uses `@allow(W001)` decorator syntax (existing grammar); clears per-definition |
| 15 | Add lint tests (one test per rule + auto-fix tests) | [x] | 35 tests in tests/linter/test_linter.py |

**Done when:** `mapanare lint` reports unused variables, unused imports,
unreachable code, and shadowing. `--fix` removes unused imports automatically.
LSP shows lint warnings in real time.

---

## Phase 3 — Python Interop
**Priority:** HIGH — deferred from v0.4.0; unlocks the entire Python ecosystem

v0.4.0 shipped `extern "C"` for native FFI. Python interop does the same for
the Python backend — call any Python function from Mapanare.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add `extern "Python"` function declarations to grammar | [x] | Added optional `DOUBLE_COLON NAME` to extern_fn_def for module::name syntax |
| 2 | Add `ExternPythonFnDef` AST node | [x] | Extended ExternFnDef with `module: str \| None` field (cleaner than separate node) |
| 3 | Implement in semantic checker (signature validation, no body) | [x] | Accepts "Python" ABI; requires module qualifier |
| 4 | Implement in Python emitter (generate direct `import` + call) | [x] | Generates import + wrapper fn; Result return → try/except |
| 5 | Type marshalling: Mapanare types ↔ Python types | [x] | Natural via transpiler: List→list, Map→dict, String→str already work |
| 6 | Add `--python-path` flag for custom Python module search paths | [x] | Added to compile and run subcommands |
| 7 | Error handling: wrap Python exceptions in `Result<T, String>` | [x] | Return type Result<T,String> → try/except wrapper in emitter |
| 8 | Test: call `math.sqrt` from Mapanare | [x] | Compiles and executes; sqrt(16.0) → 4.0 |
| 9 | Test: call `json.loads` / `json.dumps` from Mapanare | [x] | Result<T,String> wrapping tested; invalid JSON → Err |
| 10 | Test: call numpy array operations from Mapanare | [x] | Compilation tested; runtime skipped (numpy optional) |
| 11 | Add Python interop section to Getting Started guide | [x] | Added to SPEC.md |
| 12 | Add e2e tests for Python interop | [x] | 37 tests in tests/ffi/test_python_interop.py |

**Done when:** `extern "Python" fn sqrt(x: Float) -> Float` from `math` works.
Mapanare programs can call arbitrary Python functions with type-safe wrappers.

---

## Phase 4 — WASM Playground
**Priority:** MEDIUM — high visibility, static deploy

A browser-based playground lets anyone try Mapanare without installing anything.
This is the single highest-impact marketing asset. Runs entirely client-side via
Pyodide — no backend required.

**Deploy:** GitHub Pages (static site, separate from main website)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create playground project structure in `playground/` | [x] | Vite + CodeMirror 6; lives in main repo, deploys independently via GitHub Pages |
| 2 | Set up Pyodide to run Python transpiler backend in browser | [x] | Web Worker loads Pyodide 0.26.4, installs lark, mounts compiler modules |
| 3 | Bundle Lark grammar + compiler modules for Pyodide | [x] | `scripts/bundle-compiler.sh` copies 16 files to `public/compiler/` |
| 4 | Build web UI: code editor (CodeMirror/Monaco), output panel, run button | [x] | CodeMirror 6 editor + resizable output panel, Ctrl+Enter to run |
| 5 | Add syntax highlighting for `.mn` in the editor | [x] | StreamLanguage-based highlighting: keywords, types, builtins, strings, comments |
| 6 | Add share button — encode program in URL hash | [x] | Base64-encoded source in `#code=` URL hash; clipboard copy with toast |
| 7 | Pre-load 7 examples from Getting Started guide | [x] | Hello World, Interpolation, Fibonacci, Structs/Enums, Option/Result, HOF, Pipes |
| 8 | Add error display using diagnostic system (spans, underlines) | [x] | Worker catches ParseError/SemanticErrors and displays in output panel |
| 9 | Set up deploy pipeline to GitHub Pages | [x] | GitHub Actions workflow: bundle compiler, npm build, deploy to GitHub Pages |
| 10 | Add link to playground from README and docs | [x] | Links added to README.md |

**Done when:** Playground loads, lets you write Mapanare code,
run it, and see output. Share links work. At least 5 pre-loaded examples.

---

## Phase 5 — Package Registry
**Priority:** MEDIUM — deferred from v0.4.0; completes the package manager story

`mapanare install` already works (git-based). The registry adds discoverability,
versioning, and `mapanare publish`.

**Repo:** `mapanare-website` (existing, migrating from PHP to Python/Flask API + React frontend)

The registry backend and package browser UI will be part of the main Mapanare
website — not a separate repo. The website is being migrated from PHP to
Python/Flask (API) with a React frontend.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design registry API (REST: search, publish, download, versions) | [x] | FastAPI in `mapanare-website/registry.py` — POST/GET/DELETE /api/packages endpoints |
| 2 | Set up Flask backend with database (SQLite initially, PostgreSQL for prod) | [x] | SQLite with WAL mode; tables: packages, package_versions, api_tokens |
| 3 | Implement package upload endpoint (tarball + `mapanare.toml` metadata) | [x] | POST /api/packages with Bearer auth; validates name, version, extracts metadata |
| 4 | Implement package search endpoint (by name, keyword, category) | [x] | GET /api/packages with q, keyword, page, per_page params |
| 5 | Implement version resolution (semver ranges, conflict detection) | [x] | SemVer parser, satisfies() with ^, ~, >=, <, =, *, resolve_best_version() |
| 6 | Add `mapanare publish` CLI command (authenticate + upload) | [x] | Builds tarball, uploads via multipart; token in ~/.mapanare/token or MAPANARE_TOKEN |
| 7 | Add `mapanare search` CLI command (query registry) | [x] | Queries registry API; displays name, version, description, keywords |
| 8 | Update `mapanare install` to check registry before git fallback | [x] | Registry-first resolution: registry → git fallback; version constraint matching |
| 9 | Add package browser page in website React frontend (`/packages/{name}`) | [x] | Packages.tsx (search/browse) + PackageDetail.tsx (per-package); navbar link added |
| 10 | Add CI for registry API (tests, deploy) | [x] | GitHub Actions: pytest registry tests + frontend lint/build; Python 3.11/3.12 matrix |
| 11 | Publish 3+ example packages (stdlib extensions, utilities) | [x] | mn_http, mn_collections, mn_json in examples/packages/ with manifests |

**Done when:** `mapanare publish` uploads a package. `mapanare search` finds it.
`mapanare install` resolves from the registry. Package pages visible at `mapanare.dev/packages/`.

---

## Phase 6 — Documentation & Ecosystem
**Priority:** MEDIUM — essential for adoption beyond early users

(The website and blog live in the `mapanare-website` repo.)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Write language reference (all keywords, syntax, types, builtins) | [x] | `docs/reference.md` — comprehensive reference covering all types, keywords, operators, syntax, builtins, CLI, lint rules |
| 2 | Write cookbook with 10+ real-world examples | [x] | `docs/cookbook.md` — 14 recipes: fibonacci, error handling, structs, agents, pipelines, signals, streams, Python interop, traits, etc. |
| 3 | Add doc comment syntax (`///` or `/** */`) to grammar | [x] | `///` doc comments captured as DOC_COMMENT tokens; DocComment AST node wraps definitions; handled in parser, semantic, emitters, optimizer, linter, LSP |
| 4 | Implement `mapanare doc` — generate HTML docs from doc comments | [x] | `mapanare/docgen.py` extracts DocComment items, generates styled HTML; `mapanare doc <file>` CLI command added |
| 5 | Document all stdlib modules with examples | [x] | `docs/stdlib.md` — all 7 modules: math, text, time, io, http, log, pkg with API tables and examples |
| 6 | Add "Mapanare for X developers" guides (Python, Rust, TypeScript) | [x] | `docs/for-python-devs.md`, `docs/for-rust-devs.md`, `docs/for-typescript-devs.md` — side-by-side comparisons |
| 7 | Update README with v0.5.0 features and playground link | [x] | Version badge, CLI commands (lint/doc/publish/search/login), roadmap status, stdlib link, nav links to reference/cookbook |
| 8 | Write CHANGELOG entry for v0.5.0 | [x] | Added to CHANGELOG.md with all v0.5.0 features: interpolation, linter, Python interop, playground, registry, docs |

**Done when:** Language reference covers all syntax. Cookbook has 10+ examples.
`mapanare doc` generates docs from comments. Migration guides exist for Python/Rust/TS developers.

---

## What v0.5.0 Does NOT Include

| Item | Deferred To | Reason |
|------|-------------|--------|
| MIR (intermediate representation) | v0.6.0 | Major compiler refactor; needs dedicated version |
| Freeze Python bootstrap | v0.6.0 | Self-hosted compiler must handle all features first |
| Agent tracing (OpenTelemetry) | v0.7.0 | Production observability concern |
| Deployment infrastructure (Docker, health checks) | v0.7.0 | Production concern |
| Built-in test runner (`mapanare test`) | v0.7.0 | Developer tool, not ecosystem blocker |
| Debug info (DWARF) | v0.7.0 | Needs MIR for clean implementation |
| GPU kernel dispatch | Post-1.0 | FFI + MIR must work first |
| Autograd / computation graphs | Post-1.0 | Research-level feature |
| Effect typing for agents | Post-1.0 | Research-level |
| Session types for channels | Post-1.0 | Research-level |
| SPIR-V backend | Post-1.0 | Needs MIR |

---

## Success Criteria for v0.5.0

v0.5.0 ships when ALL of the following are true:

1. **Interpolation:** `"Hello, ${name}!"` compiles and runs on both backends.
2. **Linter:** `mapanare lint` reports unused variables, imports, and unreachable code. Integrated into LSP.
3. **Python Interop:** `extern "Python"` lets Mapanare call Python functions with type-safe signatures.
4. **Playground:** `play.mapanare.dev` is live with editor, output, and share links.
5. **Registry:** `mapanare publish` + `mapanare search` + `mapanare install` work end-to-end against the registry.
6. **Docs:** Language reference exists. Cookbook has 10+ examples. `mapanare doc` generates docs.
7. **Tests:** All existing tests pass + new tests for interpolation, linter, Python interop, and registry CLI.

---

## Priority Order

If time is limited, ship in this order:

1. Phase 1 (string interpolation — quick win, high visibility, unblocks better error messages)
2. Phase 2 (linter — developer experience, catches real bugs)
3. Phase 3 (Python interop — unlocks entire Python ecosystem for Mapanare users)
4. Phase 6 (documentation — adoption depends on it)
5. Phase 4 (playground — marketing and discoverability)
6. Phase 5 (registry — completes ecosystem, but git-based install works as stopgap)

---

*"A language without an ecosystem is a toy. An ecosystem without a language is a framework."*
