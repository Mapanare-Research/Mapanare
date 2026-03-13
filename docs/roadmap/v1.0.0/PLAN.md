# Mapanare v1.0.0 — "Stable"

> v0.9.0 gave Mapanare a full native stdlib — JSON, CSV, HTTP, WebSocket, crypto,
> regex — all written in `.mn`, compiled via LLVM, no Python at runtime.
> v1.0.0 freezes the language, achieves self-hosted fixed point, formalizes the
> memory model, and hardens everything for production.
>
> Core theme: **No new features. Freeze, verify, document, harden.**

---

## Scope Rules

1. **No new language features** — syntax, semantics, and type system are frozen after this release
2. **Breaking changes require RFC + deprecation cycle** — enforced from v1.0.0 onward
3. **Python backend = legacy** — marked as "for reference only", no new investment
4. **Self-hosted fixed point is the gate** — the compiler must compile itself and produce identical output
5. **Every test must pass** — no skips except platform-specific (Linux-only on Windows, etc.)
6. **SPEC.md is the contract** — promoted from "Working Draft" to "1.0 Final"

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

| Phase | Name | Status | Estimated Effort |
|-------|------|--------|-----------------|
| 1 | Language Specification Freeze | `Not Started` | Large — audit and finalize SPEC.md |
| 2 | Self-Hosted Fixed Point | `Not Started` | X-Large — cross-module native compilation, 3-stage verification |
| 3 | Formal Memory Model | `Not Started` | Large — document and verify arena, ownership, lifetimes |
| 4 | Stability Guarantees & Policy | `Not Started` | Small — policy docs, semver contract |
| 5 | Final Hardening | `Not Started` | Large — test coverage, security audit, perf sweep |
| 6 | Validation & Release | `Not Started` | Medium — CI, docs, changelog, release |

---

## Phase 1 — Language Specification Freeze
**Priority:** CRITICAL — the spec becomes the contract; everything else depends on a frozen language

Audit every language construct, document it exhaustively in `SPEC.md`, and promote the
spec from "Working Draft" to "1.0 Final". After this phase, any syntax or semantic
change requires an RFC.

### Spec Audit

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Audit all grammar rules in `mapanare.lark` against SPEC.md — find undocumented syntax | `[ ]` | Turbofish `::<T>`, pipe definitions, namespace access, etc. |
| 2 | Document all 25 `TypeKind` variants with semantics, constructors, and examples | `[ ]` | INT, FLOAT, BOOL, STRING, LIST, MAP, OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc. |
| 3 | Document type inference rules: what is inferred, what must be annotated | `[ ]` | Let bindings, function returns, generic instantiation, turbofish |
| 4 | Document pattern matching: exhaustiveness rules, destructuring, guard clauses | `[ ]` | Enums, structs, literals, wildcards |
| 5 | Document trait system: declaration, implementation, bounds, builtin traits | `[ ]` | `Display`, `Eq`, `Ord`, `Hash`, method resolution order |
| 6 | Document generics: declaration, instantiation, constraints, monomorphization | `[ ]` | Including turbofish `::<T>` syntax |
| 7 | Document module system: imports, `pub` visibility, circular dependency rules, `self::` | `[ ]` | Cross-module compilation from v0.9.0 Phase 8 |
| 8 | Document agent lifecycle: spawn, channels, send/receive, sync, supervision | `[ ]` | Typed channels, `<-` operator, supervisor policies |
| 9 | Document signal semantics: creation, computed, subscribers, batched updates | `[ ]` | Dependency tracking, propagation order |
| 10 | Document stream operators: map, filter, take, skip, collect, fold, `\|>` pipe | `[ ]` | Backpressure, fusion, lazy vs eager |
| 11 | Document control flow: if/else, for..in, while, match, early return, break/continue | `[ ]` | |
| 12 | Document all builtin functions: `print`, `println`, `len`, `str`, `int`, `float`, `Some`, `Ok`, `Err`, `signal`, `stream` | `[ ]` | Signatures, return types, edge cases |
| 13 | Document string methods: all 12+ methods with signatures and examples | `[ ]` | `length`, `find`, `substring`, `contains`, `split`, `trim`, `replace`, `to_upper`, `to_lower`, etc. |
| 14 | Document list/map operations: literals, indexing, push, pop, length, iteration | `[ ]` | Map literal syntax `#{}`, key types |
| 15 | Document `Result<T, E>` and `Option<T>`: construction, unwrapping, pattern matching | `[ ]` | `Ok`, `Err`, `Some`, `None`, `?` operator if applicable |
| 16 | Document closures and lambdas: capture semantics, environment struct model | `[ ]` | Move vs borrow (arena model) |
| 17 | Document FFI: `extern "C"`, `--link-lib`, calling conventions | `[ ]` | From v0.4.0 |
| 18 | Document error model: structured diagnostics, error codes (`MN-X0000`), spans | `[ ]` | |

### Spec Finalization

| # | Task | Status | Notes |
|---|------|--------|-------|
| 19 | Update SPEC.md version to `1.0.0`, status to "1.0 Final" | `[ ]` | |
| 20 | Add "Stability" section: what is frozen, what can still change (stdlib), RFC process | `[ ]` | |
| 21 | Add "Reserved Keywords" section — list all keywords, reserved for future use | `[ ]` | Prevent user code from using future keywords |
| 22 | Cross-reference SPEC.md against grammar, semantic checker, and emitters for consistency | `[ ]` | Automated: parse grammar rules and check spec coverage |
| 23 | Mark Python backend as "legacy, for reference only" in all relevant docs | `[ ]` | SPEC.md, ROADMAP.md, CLAUDE.md, README |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 24 | Spec compliance tests: one test per grammar rule verifying parse → compile → expected output | `[ ]` | Use LLVM backend |
| 25 | Negative spec tests: one test per documented error case verifying correct diagnostic | `[ ]` | Error codes, spans, messages |

**Done when:** SPEC.md is complete, version 1.0 Final, and every documented construct has a passing
spec compliance test on the LLVM backend.

---

## Phase 2 — Self-Hosted Fixed Point
**Priority:** CRITICAL — the compiler must compile itself

The self-hosted compiler (8,288+ lines across 7 `.mn` modules) must compile itself
via LLVM and produce identical output — the fixed-point property. This proves the
compiler is correct enough to sustain itself.

### Prerequisites

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Audit enum lowering gaps in self-hosted `emit_llvm.mn` | `[ ]` | Known blocker from v0.9.0 |
| 2 | Audit cross-module compilation for `self::` imports between the 7 compiler modules | `[ ]` | Phase 8 of v0.9.0 added cross-module; verify it works for `mapanare/self/*.mn` |
| 3 | Identify and fix any self-hosted codegen gaps (missing AST nodes, MIR ops, LLVM patterns) | `[ ]` | Compare bootstrap Python emitter output vs self-hosted emitter output |

### Stage 1 — Bootstrap Compilation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4 | Compile `mapanare/self/*.mn` (all 7 modules) using the Python bootstrap compiler → native binary | `[ ]` | `mapanare build mapanare/self/main.mn -o mnc-stage1` |
| 5 | Verify `mnc-stage1` can lex, parse, and type-check a simple `.mn` program | `[ ]` | Smoke test: hello world, fibonacci, struct + enum |
| 6 | Verify `mnc-stage1` can emit LLVM IR for a simple `.mn` program | `[ ]` | Output IR should match bootstrap emitter output |
| 7 | Run the bootstrap test suite (264 tests) against `mnc-stage1` | `[ ]` | All must pass |

### Stage 2 — Self-Compilation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 8 | Use `mnc-stage1` to compile `mapanare/self/*.mn` → `mnc-stage2` | `[ ]` | The self-hosted compiler compiling itself |
| 9 | Run the bootstrap test suite against `mnc-stage2` | `[ ]` | All must pass |
| 10 | Diff LLVM IR output: `mnc-stage1` vs `mnc-stage2` for a corpus of test programs | `[ ]` | Must be identical (modulo metadata) |

### Stage 3 — Fixed Point Verification

| # | Task | Status | Notes |
|---|------|--------|-------|
| 11 | Use `mnc-stage2` to compile `mapanare/self/*.mn` → `mnc-stage3` | `[ ]` | |
| 12 | Binary diff: `mnc-stage2` vs `mnc-stage3` | `[ ]` | Must be identical — this IS the fixed point |
| 13 | Script the 3-stage pipeline: `scripts/verify_fixed_point.sh` | `[ ]` | Automate Stage 1→2→3 + diff |

### CI Integration

| # | Task | Status | Notes |
|---|------|--------|-------|
| 14 | Add fixed-point verification to CI (GitHub Actions) | `[ ]` | Runs on push to `dev`, Linux x64 |
| 15 | Gate release on fixed-point passing | `[ ]` | CI must green before version bump |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 16 | Test: Stage 1 binary produces correct output for 10+ programs (hello, fib, agents, signals, streams) | `[ ]` | |
| 17 | Test: Stage 2 IR matches Stage 1 IR for all test programs | `[ ]` | |
| 18 | Test: Stage 3 binary is byte-identical to Stage 2 binary | `[ ]` | |

**Done when:** `mnc-stage2 == mnc-stage3` (byte-identical binaries) and CI enforces this
on every push. The compiler can compile itself without Python.

---

## Phase 3 — Formal Memory Model
**Priority:** HIGH — production users need guarantees about when memory is freed

Document and verify the memory model. The C runtime uses arena-based allocation with
scope-level cleanup — this phase turns implicit patterns into explicit guarantees.

### Documentation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Document arena lifecycle: creation, allocation, scope cleanup, nested arenas | `[ ]` | `__mn_arena_new()`, `__mn_arena_alloc()`, `__mn_arena_destroy()` |
| 2 | Document string ownership: tag-bit system (bit 0: heap vs constant), when strings are freed | `[ ]` | Arena-allocated strings freed on scope exit |
| 3 | Document struct/enum ownership: allocation, field access, deallocation | `[ ]` | Stack vs arena, move semantics |
| 4 | Document list/map ownership: element lifecycle, resizing, freeing | `[ ]` | Arena-backed arrays, Robin Hood hash table |
| 5 | Document agent message passing: ownership transfer rules for channel send/receive | `[ ]` | Does `send` move or copy? What happens to the sender's reference? |
| 6 | Document signal value lifecycle: when signal values are freed, update propagation | `[ ]` | Subscription cleanup, computed signal dependencies |
| 7 | Document stream element lifecycle: per-element allocation, backpressure impact | `[ ]` | |
| 8 | Document closure environment lifecycle: when captured variables are freed | `[ ]` | Environment struct allocation, escape analysis |
| 9 | Write `docs/MEMORY_MODEL.md` consolidating all of the above | `[ ]` | Single reference document |

### Verification

| # | Task | Status | Notes |
|---|------|--------|-------|
| 10 | Run AddressSanitizer on full test suite (Linux/WSL) | `[ ]` | Catch use-after-free, buffer overflow, double-free |
| 11 | Run ThreadSanitizer on agent/concurrency tests (Linux/WSL) | `[ ]` | Catch data races in ring buffers, thread pool |
| 12 | Fix all ASan/TSan findings | `[ ]` | Zero tolerance for memory bugs at v1.0 |
| 13 | Add runtime debug mode: arena bounds checking, double-free detection | `[ ]` | `mapanare build --debug-memory` flag |
| 14 | Verify no leaks in long-running agent programs (spawn 10K agents, measure RSS) | `[ ]` | |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 15 | Test: arena scoping — allocations freed at scope exit, not before | `[ ]` | |
| 16 | Test: string tag-bit — constant strings not freed, heap strings freed | `[ ]` | |
| 17 | Test: agent message ownership — sender cannot access value after send | `[ ]` | |
| 18 | Test: closure environment freed when closure goes out of scope | `[ ]` | |

**Done when:** `MEMORY_MODEL.md` documents all ownership rules, ASan/TSan report zero issues,
and every ownership rule has a test.

---

## Phase 4 — Stability Guarantees & Policy
**Priority:** MEDIUM — defines the contract with users

### Policy Documents

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Write backwards compatibility policy: what is guaranteed stable (syntax, semantics, stdlib API) | `[ ]` | `docs/STABILITY.md` |
| 2 | Define deprecation cycle: warn for one minor version, remove in next major | `[ ]` | Include compiler warning mechanism |
| 3 | Publish semantic versioning contract: what constitutes major/minor/patch | `[ ]` | |
| 4 | Create migration guide template: how to communicate breaking changes | `[ ]` | `docs/MIGRATION_TEMPLATE.md` |
| 5 | Define RFC process: template, review criteria, acceptance threshold | `[ ]` | `docs/rfcs/RFC_PROCESS.md` |
| 6 | Document what is NOT frozen: stdlib additions, optimizer improvements, new targets | `[ ]` | |

### Compiler Support

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7 | Implement deprecation warnings in semantic checker | `[ ]` | `@deprecated("use X instead")` attribute on functions |
| 8 | Add `--edition` flag (future-proofing for language editions) | `[ ]` | Default: `2026`, no-op for now |
| 9 | Version-stamp compiled binaries: embed compiler version in LLVM IR metadata | `[ ]` | |

**Done when:** Policy documents published, deprecation warning mechanism works in compiler,
and semver contract is clear.

---

## Phase 5 — Final Hardening
**Priority:** HIGH — production readiness gate

### Test Coverage

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Build I/O runtime on Linux (WSL): `python runtime/native/build_io.py` | `[ ]` | Unlocks 30 skipped tests |
| 2 | Pass all event loop tests (`tests/native/test_event_loop.py`) | `[ ]` | 7 tests |
| 3 | Pass all file I/O tests (`tests/native/test_file_io.py`) | `[ ]` | 12 tests |
| 4 | Pass all TCP tests (`tests/native/test_tcp.py`) | `[ ]` | 7 tests |
| 5 | Pass all TLS tests (`tests/native/test_tls.py`) | `[ ]` | 4 tests |
| 6 | Pass ASan hardening tests (`tests/native/test_c_hardening.py`) | `[ ]` | 2 tests, Linux-only |
| 7 | Audit remaining skips — only platform-specific skips allowed (e.g., ASan on Windows) | `[ ]` | Target: ≤6 structural bootstrap skips |
| 8 | Add LLVM backend tests for every stdlib module: json, csv, http, server, websocket, crypto, regex | `[ ]` | End-to-end: compile `.mn` → run native binary → verify output |

### Performance

| # | Task | Status | Notes |
|---|------|--------|-------|
| 9 | Run full benchmark suite: fib, streams, matrix, agents | `[ ]` | Baseline for v1.0 |
| 10 | Check for performance regressions vs v0.8.0 baselines | `[ ]` | No regression > 10% allowed |
| 11 | Benchmark cross-module compilation overhead: single file vs multi-file | `[ ]` | Ensure linking doesn't blow up compile time |
| 12 | Profile and optimize MIR optimizer passes if compile time > 5s for stdlib modules | `[ ]` | |

### Security Audit

| # | Task | Status | Notes |
|---|------|--------|-------|
| 13 | Audit C runtime for buffer overflows: all `memcpy`, `strcpy`, array access | `[ ]` | `runtime/native/mapanare_core.c` |
| 14 | Audit C runtime for use-after-free: arena destroy + dangling pointer access | `[ ]` | |
| 15 | Audit C runtime for integer overflows: size calculations, index arithmetic | `[ ]` | |
| 16 | Audit ring buffer for thread safety: SPSC guarantees, memory ordering | `[ ]` | `__mn_ringbuf_*` functions |
| 17 | Audit TLS integration: certificate validation, protocol version, cipher suites | `[ ]` | OpenSSL dlopen path |
| 18 | Audit TCP socket handling: connection limits, timeout enforcement, cleanup | `[ ]` | |
| 19 | Fix all findings from security audit | `[ ]` | Zero critical/high findings at release |

### Documentation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 20 | Update README.md: current feature table, performance numbers, getting started | `[ ]` | |
| 21 | Update CLAUDE.md: version bump, current status, any new conventions | `[ ]` | |
| 22 | Update getting started guide with stdlib examples (HTTP client, JSON parsing) | `[ ]` | |
| 23 | Verify all doc links: SPEC, ROADMAP, RFCs, getting started, CONTRIBUTING | `[ ]` | No dead links |

**Done when:** All native tests pass on Linux, zero security audit findings, performance
baselines established, documentation current.

---

## Phase 6 — Validation & Release
**Priority:** GATE — nothing ships until this phase completes

### Pre-Release Checklist

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Full test suite green: `make test` — target 3,500+ tests, ≤6 skips | `[ ]` | |
| 2 | Lint clean: `make lint` (ruff + black + mypy) | `[ ]` | |
| 3 | Fixed-point verification passing in CI | `[ ]` | From Phase 2 |
| 4 | SPEC.md at "1.0 Final" | `[ ]` | From Phase 1 |
| 5 | MEMORY_MODEL.md complete | `[ ]` | From Phase 3 |
| 6 | STABILITY.md published | `[ ]` | From Phase 4 |
| 7 | All security audit findings resolved | `[ ]` | From Phase 5 |
| 8 | CHANGELOG.md updated with all v1.0.0 changes | `[ ]` | |
| 9 | VERSION file bumped to `1.0.0` | `[ ]` | |

### Release

| # | Task | Status | Notes |
|---|------|--------|-------|
| 10 | Tag `v1.0.0` on `main` | `[ ]` | After all checks pass |
| 11 | GitHub Release with release notes | `[ ]` | Highlight: language freeze, fixed point, memory model |
| 12 | PyPI release: `pip install mapanare==1.0.0` | `[ ]` | |
| 13 | Update `mapanare.dev` website: v1.0 announcement, updated docs | `[ ]` | In `mapanare-website` repo |
| 14 | Update ROADMAP.md: v1.0.0 row in release history table | `[ ]` | |

**Done when:** `v1.0.0` tagged, released on GitHub and PyPI, website updated,
and the compiler can compile itself.

---

## Context Recovery

If context is interrupted mid-phase, add a handoff entry here:

| Date | Phase | Last Completed Task | Next Task | Notes |
|------|-------|--------------------:|-----------|-------|
| — | — | — | — | — |

---

## Phase Dependencies

```
Phase 1 (Spec Freeze) ──────┬──→ Phase 4 (Stability Policy)
                             │
Phase 2 (Fixed Point) ───────┤
                             │
Phase 3 (Memory Model) ──────┤
                             │
                             └──→ Phase 5 (Hardening) ──→ Phase 6 (Release)
```

- Phase 1, 2, 3 are independent — can run in parallel
- Phase 4 depends on Phase 1 (need frozen spec to define stability)
- Phase 5 depends on Phase 2 (need native binary for full test pass) and Phase 3 (need memory model for security audit)
- Phase 6 depends on all other phases

### Priority order

1. **Phase 2** — Fixed Point (highest risk, longest lead time, proves the compiler works)
2. **Phase 1** — Spec Freeze (foundation for everything else)
3. **Phase 3** — Memory Model (blocks security audit in Phase 5)
4. **Phase 5** — Hardening (blocks release)
5. **Phase 4** — Stability Policy (can be done while hardening)
6. **Phase 6** — Release (ceremony, after everything else)
