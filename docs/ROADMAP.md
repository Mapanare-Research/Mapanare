# Mapanare Roadmap

> **Mapanare** is an AI-native compiled programming language.
> Agents, signals, streams, and tensors are first-class primitives — not libraries.
>
> [mapanare.dev](https://mapanare.dev) · [GitHub](https://github.com/Mapanare-Research/Mapanare)

---

## Where We Are (v0.3.1)

Mapanare is real, compiled, and tested. The bootstrap compiler ships with two backends
(Python transpiler + LLVM native) and a self-hosted compiler written in Mapanare itself.
**1,960+ tests pass** across the full pipeline.

### What works today

- **Full compiler pipeline** — Lexer, parser, semantic checker, optimizer (O0–O3), code emitter
- **Two compilation targets** — Python transpilation and native binaries via LLVM IR
- **Agent system** — Spawn concurrent actors with typed channels, message passing, supervision policies
- **Reactive signals** — Automatic dependency tracking and recomputation
- **Stream processing** — Async iterables with fusion, backpressure, and `|>` pipe operator
- **Pattern matching** — Exhaustive `match` expressions with destructuring
- **Type system** — Static typing with inference, generics, `Option<T>`, `Result<T, E>`, `TypeKind` enum (25 kinds)
- **Traits** — `trait` / `impl Trait for Type`, trait bounds on generics, builtin traits (`Display`, `Eq`, `Ord`, `Hash`)
- **Module system** — File-based imports with `pub` visibility, circular dependency detection, multi-file compilation
- **Self-hosted compiler** — 5,802 lines of `.mn` across 6 modules, Stage 2 fixed-point verified
- **Native C runtime** — Arena-based memory, lock-free SPSC ring buffers, thread pool, semaphore-based scheduling
- **LLVM agent codegen** — `spawn`, `send` (`<-`), `sync` targeting C runtime with OS threads
- **Cross-compilation** — Linux x64, macOS ARM64, Windows x64
- **Optimization passes** — Constant folding, DCE, agent inlining, stream fusion
- **LSP server** — Diagnostics, hover, go-to-definition, find-references, autocomplete
- **VS Code extension** — Syntax highlighting, LSP integration, snippets, commands
- **Package manager** — Project manifests (`mapanare.toml`), git-based installation, dependency resolution
- **Standard library** — I/O, HTTP, time, math, text, structured logging
- **Formatter** — `mapanare fmt` for consistent code style
- **Binary distribution** — PyInstaller builds, install scripts (Unix + Windows), GitHub Releases CI
- **Getting Started guide** — 12-section tutorial from install to streams

### Performance (LLVM native vs Python)

| Workload | Speedup |
|----------|---------|
| Fibonacci (recursive) | **22–26x faster** |
| Stream pipeline (1M items) | **62.8x faster** |
| Matrix multiply (100x100) | **22.9x faster** |
| Agent message passing (10K) | On par |

---

## Release History

| Version | Theme | Highlights |
|---------|-------|------------|
| **v0.1.0** ✅ | Foundation | Bootstrap compiler, Lark parser, semantic checker, Python emitter, LLVM backend (basic), runtime, LSP, VS Code extension, CLI, stdlib, benchmarks, 1,400+ tests |
| **v0.2.0** ✅ | Self-Hosting | LLVM string/list codegen, C runtime (ring buffers, thread pool), self-hosted lexer + parser + semantic + emitter (5,800+ lines .mn), REPL, `str`/`int`/`float` builtins |
| **v0.3.0** ✅ | Depth Over Breadth | Traits, module resolution, LLVM agent codegen, arena memory, `TypeKind` enum, getting started guide, governance, 110+ e2e tests, benchmarks rewrite, 1,960+ tests |
| **v0.3.1** ✅ | Release Polish | Dynamic versioning from `VERSION` file, documentation tests |

---

## The Road Ahead

### v0.4.0 — "Ready for the World"

> Harden what exists, expose it to the outside world, build ecosystem infrastructure.
> No new language primitives — refine agents/signals/streams, don't add more.

#### Phase 1: Scope & Cleanup

| # | Task | Priority |
|---|------|----------|
| 1.1 | Move `gpu.py`, `model.py`, `tensor.py` to `experimental/`, remove from default build | HIGH |
| 1.2 | Clean up dead imports and unused experimental code paths | HIGH |
| 1.3 | Ensure `import mapanare` doesn't pull in torch/numpy/onnx | HIGH |
| 1.4 | Extract VS Code extension to [`mapanare-vscode`](#organization--repo-strategy) repo | HIGH |

**Done when:** Core compiler has zero experimental dependencies. VS Code extension has its own repo with marketplace CI. README feature table is honest.

#### Phase 2: C Runtime Hardening

| # | Task | Priority |
|---|------|----------|
| 2.1 | Add C runtime unit tests (ring buffer stress, thread pool saturation) | HIGH |
| 2.2 | Run under AddressSanitizer and ThreadSanitizer | HIGH |
| 2.3 | Fix any issues found | HIGH |
| 2.4 | Add SIGTERM/SIGINT handling for graceful agent shutdown | HIGH |
| 2.5 | Add C compilation + test to CI pipeline | HIGH |

**Done when:** C runtime passes under sanitizers. CI compiles and tests native runtime.

#### Phase 3: Error Recovery & Structured Diagnostics

| # | Task | Priority |
|---|------|----------|
| 3.1 | Add source location (file, line, col) to all AST nodes | HIGH |
| 3.2 | Implement structured error type with spans, labels, and suggestions | HIGH |
| 3.3 | Add error recovery in parser (sync to next statement on error) | HIGH |
| 3.4 | Emit multiple errors per compilation (currently stops at first) | MEDIUM |
| 3.5 | Colorized terminal output for diagnostics | MEDIUM |

**Done when:** Compiler reports multiple errors with source locations and fix suggestions.

#### Phase 4: C FFI

| # | Task | Priority |
|---|------|----------|
| 4.1 | Add `extern "C"` function declarations to grammar | CRITICAL |
| 4.2 | Implement in semantic checker (signature + calling convention, no body) | CRITICAL |
| 4.3 | Implement in LLVM emitter (declare external, generate call) | CRITICAL |
| 4.4 | Add linker flag passthrough (`--link-lib`) | HIGH |
| 4.5 | Test: call `puts` from libc via FFI | HIGH |
| 4.6 | Add FFI tests to CI | HIGH |

**Done when:** `extern "C" fn puts(s: String) -> Int` compiles and links. Mapanare programs can call C functions.

#### Phase 5: Self-Hosted Compiler Verification

| # | Task | Priority |
|---|------|----------|
| 5.1 | Run full test suite against binary produced by self-hosted compiler | HIGH |
| 5.2 | Fix any failures in self-hosted output | HIGH |
| 5.3 | Document bootstrap process (Stage 0 → Stage 1 → Stage 2) | MEDIUM |

**Done when:** Self-hosted compiler passes full test suite. Bootstrap is reproducible.

#### Phase 6: LSP & Editor Improvements

| # | Task | Priority |
|---|------|----------|
| 6.1 | Incremental parsing (re-parse changed function only) | MEDIUM |
| 6.2 | Semantic-aware autocomplete (trait methods, module exports) | MEDIUM |
| 6.3 | Inline diagnostics for type errors with fix suggestions | MEDIUM |
| 6.4 | Go-to-definition across module imports | MEDIUM |

**Done when:** LSP autocompletes imported symbols and trait methods. Go-to-def works across files.

#### v0.4.0 Success Criteria

1. No experimental GPU/model code in default build
2. C runtime passes under sanitizers, CI tests it
3. Compiler reports multiple errors with source locations and spans
4. `extern "C"` FFI works — Mapanare can call C functions
5. Self-hosted compiler passes full test suite
6. LSP provides cross-module go-to-definition
7. All existing tests pass + new tests for FFI, diagnostics, bootstrap

---

### v0.5.0 — "The Ecosystem"

> Build the infrastructure that turns Mapanare from a compiler into a platform.

#### Package Registry (new repo: [`mapanare-registry`](#organization--repo-strategy))

- Registry backend at `mapanare.dev/packages`
- `mapanare search`, `mapanare publish` (install already works in monolith)
- Semantic versioning with conflict resolution
- Package categories and discoverability

#### WASM Playground (new repo: [`mapanare-playground`](#organization--repo-strategy))

- Compile Python transpiler backend to WASM (via Pyodide)
- Minimal web UI: editor, output panel, share button
- Pre-loaded getting-started examples
- Deploy to `play.mapanare.dev`

#### Python Interop (Stretch)

- `extern "Python"` calling convention
- Direct Python function calls from Mapanare
- Test: call numpy from Mapanare via Python backend

#### Linter

- `mapanare lint` — common mistakes and anti-patterns
- Integrated into LSP for real-time feedback

---

### v0.6.0 — "Compiler Infrastructure"

> Replace ad-hoc patterns with principled compiler architecture.

#### Intermediate Representation (MIR)

- SSA-based, typed IR between AST and emission
- AST → MIR lowering pass
- Move optimizer passes to work on MIR instead of AST
- MIR → Python and MIR → LLVM emission
- Enables future backends (WASM native, SPIR-V) without duplicating logic

#### Freeze Python Bootstrap

- Self-hosted compiler becomes the primary compiler
- Python bootstrap preserved in `bootstrap/` for reference
- All development moves to `.mn` sources

---

### v0.7.0 — "Production Ready"

> Make Mapanare deployable and observable in production.

#### Agent Observability

- Distributed tracing with OpenTelemetry export (OTLP)
- `--trace` flag on CLI
- Structured error codes
- Agent metrics exposition (Prometheus format)

#### Deployment Infrastructure

- Dockerfile and container image
- SIGTERM graceful shutdown (v0.4.0) → health checks, readiness probes
- Supervision trees (cascading failure, one-for-all/rest-for-one strategies)

#### Developer Tools

- `mapanare test` — built-in test runner
- Debug info in LLVM output (DWARF)
- Documentation generator from doc comments

---

### v1.0.0 — "Stable"

> The language is stable. Breaking changes require an RFC and deprecation cycle.

- Language specification frozen
- Formal memory model documented
- All headline features (agents, signals, streams) work natively at production quality
- Complete language reference documentation
- Backwards compatibility guarantees

---

## Future (Post-1.0)

These are aspirational features that require research or depend on ecosystem maturity.

| Feature | Description | Depends On |
|---------|-------------|------------|
| GPU kernel dispatch | `@gpu` / `@cpu` annotations → CUDA/Metal/Vulkan | FFI, MIR |
| Tensor autograd | Automatic differentiation for ML training loops | MIR, tensor codegen |
| Effect typing | Compile-time tracking of agent side effects | Formal type system |
| Session types | Static protocol verification for channels | Formal type system |
| SPIR-V backend | GPU compute via Vulkan shader compilation | MIR |
| Formal semantics | Core calculus with soundness proofs | Type system maturity |
| Hot code reload | Swap agent code without restart | Native runtime, supervision |

---

## Self-Hosted Compiler Status

The compiler is written in Mapanare itself — 5,802 lines across six modules.

| Component | Lines | Status |
|-----------|------:|--------|
| Lexer (`lexer.mn`) | 498 | ✅ Complete |
| AST definitions (`ast.mn`) | 255 | ✅ Complete |
| Parser (`parser.mn`) | 1,721 | ✅ Complete |
| Semantic checker (`semantic.mn`) | 1,607 | ✅ Complete |
| LLVM IR emitter (`emit_llvm.mn`) | 1,644 | ✅ Complete |
| Compiler driver (`main.mn`) | 77 | ✅ Complete |
| Fixed-point verification | — | ✅ Stage 2 = Stage 1 |
| Bootstrap test suite (96 tests) | — | ✅ All passing |

---

## Architecture

```
yourfile.mn
    │
    ▼
┌─────────────────────────────────────────┐
│       mapanare compiler                 │
│  Lexer → Parser → AST → Semantic Check │
│              │                          │
│     Optimizer → IR Generator            │
└─────────────┬───────────────────────────┘
              │
         ┌────┴────┐
         ▼         ▼
    Python      LLVM IR
   (transpile)     │
              ┌────┴────┐
              ▼         ▼
         Native x86  Native ARM
```

---

## Organization & Repo Strategy

Mapanare is a monolith-first project. The compiler, runtime, stdlib, LSP, and C runtime
all change together and share one test suite — splitting them would mean coordinating
multiple PRs and version bumps for every change. Only split when a component has a
**different language, different build system, and never changes in the same PR** as the compiler.

### Current (`Mapanare-Research`)

| Repo | Purpose |
|------|---------|
| [`Mapanare`](https://github.com/Mapanare-Research/Mapanare) | Compiler, runtime, stdlib, LSP, C runtime, benchmarks, packaging |
| [`tree-sitter-mapanare`](https://github.com/Mapanare-Research/tree-sitter-mapanare) | Tree-sitter grammar for editors |
| [`skills`](https://github.com/Mapanare-Research/skills) | AI coding agent skills (Claude Code, Cursor, Windsurf) |
| [`.github`](https://github.com/Mapanare-Research/.github) | Org profile and default community health files |

### Planned New Repos

| Repo | When | Why Split |
|------|------|-----------|
| `mapanare-vscode` | v0.4.0 | TypeScript project, `npm publish` to VS Code marketplace, completely different language and build — never changes in same PR as compiler |
| `mapanare-registry` | v0.5.0 | New web backend (different stack entirely, separate deploy) |
| `mapanare-playground` | v0.5.0 | New web app (Pyodide/WASM, separate deploy pipeline) |

### What Stays in the Monolith (and why)

| Component | Why it stays |
|-----------|-------------|
| Compiler (`mapanare/`) | Core — everything depends on it |
| LSP (`mapanare/lsp/`) | Imports compiler directly, changes with it |
| C runtime (`runtime/native/`) | Tightly coupled to LLVM emitter |
| Python runtime (`runtime/`) | Tested with compiler, same release |
| Stdlib (`stdlib/`) | Tested with compiler, same release |
| Self-hosted sources (`mapanare/self/`) | Compiled by the bootstrap, same test suite |
| Bootstrap (`bootstrap/`) | Frozen reference, no independent changes |

---

## Review Panel Response

In March 2026, a panel of 7 expert reviewers scored Mapanare at **6.6/10** (range: 5.5–8.2).
Their top concerns and what we did about them:

| Concern | Severity | Resolution |
|---------|----------|------------|
| Memory management undefined / leaking | CRITICAL | ✅ Arena-based memory in v0.3.0 |
| LLVM backend missing headline features | CRITICAL | ✅ Agent codegen in v0.3.0 |
| No module resolution | CRITICAL | ✅ File-based imports in v0.3.0 |
| No traits / interfaces | HIGH | ✅ Trait system in v0.3.0 |
| String-based type comparisons | HIGH | ✅ TypeKind enum in v0.3.0 |
| Benchmark integrity issues | HIGH | ✅ Benchmarks rewritten in v0.3.0 |
| Empty CHANGELOG | HIGH | ✅ Populated in v0.3.0 |
| No Getting Started tutorial | HIGH | ✅ 12-section guide in v0.3.0 |
| No end-to-end tests | HIGH | ✅ 110+ e2e tests in v0.3.0 |
| No governance / templates | HIGH | ✅ COC, SECURITY, templates in v0.3.0 |
| Scope too broad (GPU/model) | MEDIUM | 🔜 v0.4.0 scope reduction |
| No FFI | MEDIUM | 🔜 v0.4.0 FFI |
| No intermediate representation | MEDIUM | 🔜 v0.6.0 MIR |
| No metrics / tracing | MEDIUM | 🔜 v0.7.0 observability |
| No browser playground | MEDIUM | 🔜 v0.5.0 playground |

---

## Contributing

1. Read [`SPEC.md`](SPEC.md) to understand the language design
2. Browse [open issues](https://github.com/Mapanare-Research/Mapanare/issues) for something that interests you
3. All PRs require tests
4. Language changes require an [RFC](rfcs/) first

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for full guidelines.

---

*Built by [Mapanare Research](https://github.com/Mapanare-Research) · [mapanare.dev](https://mapanare.dev)*
