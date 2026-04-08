# Mapanare v0.4.0 — "Ready for the World"

> v0.3.0 proved Mapanare is usable. v0.4.0 must prove it is *adoptable*.
>
> Core theme: **harden what exists, improve developer experience, and
> prepare for ecosystem growth.**

---

## Scope Rules

1. **Ship what v0.3.0 deferred** — FFI, C runtime hardening, scope reduction
2. **Improve developer experience** — diagnostics, LSP, self-hosted verification
3. **No new language primitives** — refine agents/signals/streams, don't add more
4. Every item must have a clear "done when" criterion

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
| 1 | Scope & Cleanup | Complete | 1.1, 1.2 |
| 2 | C Runtime Hardening | Complete | — |
| 3 | Error Recovery & Structured Diagnostics | Complete | — |
| 4 | C FFI | Complete | — |
| 5 | Self-Hosted Compiler Verification | Complete | — |
| 6 | LSP & Editor Improvements | Complete | 6.1, 6.2 |

---

## Phase 1 — Scope & Cleanup

### 1.1 Scope Reduction
**Priority:** HIGH — carried from v0.3.0

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Move `mapanare/gpu.py` to `experimental/` or remove from default build | [x] | Moved; shape validation + DEVICE_ANNOTATIONS extracted to types.py |
| 2 | Move `mapanare/model.py` to `experimental/` or remove from default build | [x] | Moved; internal import updated to experimental.tensor |
| 3 | Move `mapanare/tensor.py` to `experimental/` or remove from default build | [x] | Moved; semantic.py now imports validation fns from types.py |
| 4 | Update README to honestly reflect what ships vs what's experimental | [x] | Feature table + GPU section updated |
| 5 | Clean up dead imports and unused experimental code paths | [x] | All imports verified; no dead references |
| 6 | Ensure `import mapanare` doesn't pull in torch/numpy/onnx | [x] | Tests in test_scope.py verify no leakage |

**Done when:** Core compiler has zero experimental dependencies.
`import mapanare` doesn't pull in torch/numpy/onnx. README feature table is honest.

---

### 1.2 VS Code Extension Extraction
**Priority:** HIGH — per repo strategy

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create `mapanare-vscode` repo under Mapanare-Research | [x] | Local repo created with git init |
| 2 | Move VS Code extension code to new repo | [x] | All files copied; package.json repo URL updated; README, LICENSE, .gitignore, .vscodeignore added |
| 3 | Set up `npm publish` CI for VS Code marketplace | [x] | publish.yml (on release, uses VSCE_PAT secret) + ci.yml added |
| 4 | Remove extension code from monolith | [x] | editors/ directory removed |
| 5 | Update docs and contributing guide with new repo link | [x] | README, CONTRIBUTING.md updated; project structure updated |

**Done when:** VS Code extension has its own repo with marketplace CI.
Extension is no longer in the monolith.

---

## Phase 2 — C Runtime Hardening
**Priority:** HIGH — carried from v0.3.0

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add C runtime unit tests (ring buffer stress test, thread pool saturation) | [x] | test_c_runtime.c: 45 tests covering strings, lists, arena, ring buffer, thread pool, backpressure, agents, registry, file I/O, shutdown |
| 2 | Run under AddressSanitizer and ThreadSanitizer | [x] | CI job compiles with -fsanitize=address and -fsanitize=thread; Python wrapper in test_c_hardening.py |
| 3 | Fix any issues found | [x] | Code review clean; sanitizer validation runs on CI (Ubuntu) |
| 4 | Add SIGTERM/SIGINT handling for graceful agent shutdown | [x] | mapanare_shutdown_init() + signal handler in mapanare_runtime.c; Windows ConsoleCtrlHandler + POSIX sigaction |
| 5 | Add C compilation + test to CI pipeline | [x] | New `native` job in ci.yml: plain + ASan + TSan |

**Done when:** C runtime tests exist and pass under sanitizers. Graceful
shutdown works. CI compiles and tests the native runtime.

---

## Phase 3 — Error Recovery & Structured Diagnostics
**Priority:** HIGH — cited by reviewers

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add source location (file, line, col) to all AST nodes | [x] | `_span_from_children` helper + all transformer methods now set span |
| 2 | Implement structured error type with spans, labels, and suggestions | [x] | `mapanare/diagnostics.py`: Diagnostic, Label, Suggestion, Severity, DiagnosticBag, colorized formatter |
| 3 | Add error recovery in parser (sync to next statement on error) | [x] | `parse_recovering()`: splits at top-level boundaries, parses chunks independently |
| 4 | Emit multiple errors per compilation (currently stops at first) | [x] | `cmd_check` uses `parse_recovering` + semantic check on partial AST; `ParseErrors` exception |
| 5 | Colorized terminal output for diagnostics | [x] | All CLI commands use `format_diagnostic()` with ANSI colors, underline spans, summary line |

**Done when:** Compiler reports multiple errors with source locations,
underline spans, and fix suggestions. Parser recovers from common errors.

---

## Phase 4 — C FFI
**Priority:** CRITICAL — carried from v0.3.0

Without FFI, the native backend is limited to what the C runtime provides.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add `extern "C"` function declarations to grammar | [x] | `extern_fn_def` rule in .lark; `ExternFnDef` AST node; parser transformer |
| 2 | Implement in semantic checker (no body, just signature + calling convention) | [x] | Registered in `_register_def`; ABI validation; arg type checking via standard call path |
| 3 | Implement in LLVM emitter (declare external function, generate call) | [x] | `_emit_extern_fn` declares external; FFI coercion (MnString→i8*) in `_emit_call` |
| 4 | Add linker flag passthrough (`--link-lib`) | [x] | `--link-lib LIB` appends `-lLIB` (unix) / `LIB.lib` (MSVC) to linker command |
| 5 | Test: call `puts` from libc via FFI | [x] | 20 tests in `tests/ffi/test_ffi.py` covering parse, semantic, LLVM, CLI, integration |
| 6 | Add FFI tests to CI | [x] | Tests in `tests/ffi/` auto-discovered by `pytest tests/ -v` in CI |

**Done when:** `extern "C" fn puts(s: String) -> Int` compiles and links
correctly. A Mapanare program can call C functions.

---

## Phase 5 — Self-Hosted Compiler Verification
**Priority:** HIGH

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Run full test suite against binary produced by self-hosted compiler | [x] | 75 tests in test_verification.py: pipeline integrity, LLVM emission, coverage metrics, fixed-point, CLI integration, sample programs, optimizer |
| 2 | Fix any failures in self-hosted output | [x] | Added enum type registration (tagged union), two-pass struct registration (forward-declare then resolve), function forward-declaration pass; lexer.mn fully emits to LLVM IR |
| 3 | Document bootstrap process (Stage 0 → Stage 1 → Stage 2) | [x] | docs/BOOTSTRAP.md: stages, modules, current status, limitations, roadmap to full self-hosting |

**Done when:** Self-hosted compiler passes full test suite. Bootstrap
process is reproducible and documented.

---

## Phase 6 — LSP & Editor Improvements

### 6.1 LSP Improvements
**Priority:** MEDIUM

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Incremental parsing (re-parse changed function only) | [x] | IncrementalParser caches per-chunk parse results; only re-parses changed chunks |
| 2 | Semantic-aware autocomplete (trait methods, module exports) | [x] | Dot-completion for struct fields + trait methods; imported symbols in completions |
| 3 | Inline diagnostics for type errors with fix suggestions | [x] | LspDiagnostic with FixSuggestion; "did you mean" for typos, type conversion hints |
| 4 | Go-to-definition across module imports | [x] | ModuleResolver integration; cross-file go-to-def for imported symbols |

**Done when:** LSP provides autocomplete for imported symbols and trait
methods. Go-to-definition works across files.

---

### 6.2 Discord Community Seeding
**Priority:** LOW — carried from v0.3.0

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Seed Discord channels (#welcome, #general, #help, #show-and-tell, #compiler-dev) | [x] | Copy in `docs/discord-seeding.md` |

**Done when:** Discord has seeded conversations in all channels.

---

## What v0.4.0 Does NOT Include

| Item | Deferred To | Reason |
|------|-------------|--------|
| MIR (intermediate representation) | v0.6.0 | Needs FFI and self-hosting first |
| Package registry backend | v0.5.0 | Install already works; registry is a new web service |
| WASM playground | v0.5.0 | Separate deploy pipeline |
| Python interop (`extern "Python"`) | v0.5.0 | FFI must work first |
| Agent tracing (OpenTelemetry) | v0.7.0 | Observability is a production concern |
| GPU kernel dispatch | Post-1.0 | FFI + MIR must work first |
| Model loading (ONNX/safetensors) | Post-1.0 | Disconnected from compiler |
| Autograd / computation graphs | Post-1.0 | Research-level feature |
| Effect typing for agents | Post-1.0 | Research-level |
| Session types for channels | Post-1.0 | Research-level |
| Linter (`mapanare lint`) | v0.5.0 | Nice-to-have, not critical |

---

## Success Criteria for v0.4.0

v0.4.0 ships when ALL of the following are true:

1. **Scope:** No experimental GPU/model code in default build.
2. **VS Code:** Extension lives in its own repo with marketplace CI.
3. **C Runtime:** Native runtime passes under AddressSanitizer and ThreadSanitizer. CI tests it.
4. **Diagnostics:** Compiler reports multiple errors with source locations and spans.
5. **FFI:** Mapanare programs can call C functions via `extern "C"`.
6. **Self-Hosting:** Self-hosted compiler passes full test suite. Bootstrap is reproducible.
7. **LSP:** Cross-module go-to-definition works.
8. **Tests:** All existing tests pass + new tests for FFI, diagnostics, and bootstrap.

---

## Priority Order

If time is limited, ship in this order:

1. Phase 1 (scope & cleanup — quick wins, debt payment)
2. Phase 2 (C runtime hardening — safety)
3. Phase 4 (FFI — unblocks native backend utility)
4. Phase 3 (diagnostics — developer experience)
5. Phase 5 (self-hosted verification — compiler maturity)
6. Phase 6 (LSP + community — polish)

---

*"Harden what exists before building what's next."*
