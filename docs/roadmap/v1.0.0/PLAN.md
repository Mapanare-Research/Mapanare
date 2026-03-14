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

| Phase | Name | Status | Effort | Platform |
|-------|------|--------|--------|----------|
| 1 | Language Specification Freeze | `Complete` | Large | Windows |
| 2 | Emitter Hardening | `In Progress` | Large | Windows |
| 3 | Stage 1 Native Compiler | `In Progress` | Large | WSL/Linux |
| 4 | Self-Hosted Fixed Point | `Not Started` | X-Large | WSL/Linux |
| 5 | Formal Memory Model | `Not Started` | Large | Windows + WSL |
| 6 | Stability Guarantees & Policy | `Not Started` | Small | Windows |
| 7 | Final Hardening | `Not Started` | Large | WSL/Linux |
| 8 | Validation & Release | `Not Started` | Medium | Both |

---

## Phase 1 — Language Specification Freeze
**Status:** `Complete`
**Priority:** CRITICAL — the spec becomes the contract; everything else depends on a frozen language

Audit every language construct, document it exhaustively in `SPEC.md`, and promote the
spec from "Working Draft" to "1.0 Final". After this phase, any syntax or semantic
change requires an RFC.

### Spec Audit

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Audit all grammar rules in `mapanare.lark` against SPEC.md — find undocumented syntax | `[x]` | Found: `new` keyword, `while`, `break`, `assert`, `extern`, `trait`, turbofish, doc comments, char literals, tuple exprs. All now documented. |
| 2 | Document all 25 `TypeKind` variants with semantics, constructors, and examples | `[x]` | Sections 3.1-3.4: Primitives, Generic Containers, Compound/User-Defined, Special types |
| 3 | Document type inference rules: what is inferred, what must be annotated | `[x]` | Section 3.5: let bindings, list/map element types, lambdas, generics, turbofish |
| 4 | Document pattern matching: exhaustiveness rules, destructuring, guard clauses | `[x]` | Section 5: constructor, literal, identifier, wildcard patterns; exhaustiveness rules; nested destructuring. Guard clauses not implemented — not documented. |
| 5 | Document trait system: declaration, implementation, bounds, builtin traits | `[x]` | Section 7: Display, Eq, Ord, Hash; impl Trait for Type; trait bounds on generics |
| 6 | Document generics: declaration, instantiation, constraints, monomorphization | `[x]` | Section 13: declaration, turbofish `::<T>`, trait bounds, monomorphization |
| 7 | Document module system: imports, `pub` visibility, circular dependency rules, `self::` | `[x]` | Section 8: file-based modules, import syntax, pub visibility, export, self::, circular deps |
| 8 | Document agent lifecycle: spawn, channels, send/receive, sync, supervision | `[x]` | Section 9: lifecycle states, typed channels, SPSC ring buffers, backpressure, supervision |
| 9 | Document signal semantics: creation, computed, subscribers, batched updates | `[x]` | Section 10: signal(), signal{}, subscribers, batched updates, propagation order |
| 10 | Document stream operators: map, filter, take, skip, collect, fold, `\|>` pipe | `[x]` | Section 11: 14 operators, backpressure strategies, fusion, lazy evaluation |
| 11 | Document control flow: if/else, for..in, while, match, early return, break/continue | `[x]` | Section 4: if/else, for, while, break, return, match, assert |
| 12 | Document all builtin functions: `print`, `println`, `len`, `str`, `int`, `float`, `Some`, `Ok`, `Err`, `signal`, `stream` | `[x]` | Section 14: all 12 builtins with signatures |
| 13 | Document string methods: all 12+ methods with signatures and examples | `[x]` | Section 15: all 15 methods (len, char_at, byte_at, substr, find, contains, starts_with, ends_with, split, trim, trim_start, trim_end, to_upper, to_lower, replace) |
| 14 | Document list/map operations: literals, indexing, push, pop, length, iteration | `[x]` | Sections 16-17: list literals, indexing, push, len, iteration; map #{}, indexing, contains, delete, iteration |
| 15 | Document `Result<T, E>` and `Option<T>`: construction, unwrapping, pattern matching | `[x]` | Section 3.8: construction, pattern matching, ? operator, error propagation |
| 16 | Document closures and lambdas: capture semantics, environment struct model | `[x]` | Section 6.3: lambda syntax, capture by value, environment struct, no-capture optimization |
| 17 | Document FFI: `extern "C"`, `--link-lib`, calling conventions | `[x]` | Section 18: C FFI, Python interop (legacy), type mappings |
| 18 | Document error model: structured diagnostics, error codes (`MN-X0000`), spans | `[x]` | Section 19 + Appendix D: error code format, categories, Rust-style reporting, error code registry |

### Spec Finalization

| # | Task | Status | Notes |
|---|------|--------|-------|
| 19 | Update SPEC.md version to `1.0.0`, status to "1.0 Final" | `[x]` | Header updated: Version 1.0.0, Status 1.0 Final |
| 20 | Add "Stability" section: what is frozen, what can still change (stdlib), RFC process | `[x]` | Section 24: frozen areas, changeable areas, RFC/deprecation process |
| 21 | Add "Reserved Keywords" section — list all keywords, reserved for future use | `[x]` | Appendix C: 20 reserved keywords (async, await, yield, macro, where, etc.) |
| 22 | Cross-reference SPEC.md against grammar, semantic checker, and emitters for consistency | `[x]` | `tests/spec/test_spec_crossref.py`: 32 keywords, 25 TypeKinds, 28 operators, all sections validated |
| 23 | Mark Python backend as "legacy, for reference only" in all relevant docs | `[x]` | SPEC.md, ROADMAP.md, README.md updated. CLAUDE.md already marks it. |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 24 | Spec compliance tests: one test per grammar rule verifying parse → compile → expected output | `[x]` | `tests/spec/test_spec_compliance.py`: 85 tests covering all grammar rules (parse + semantic + LLVM) |
| 25 | Negative spec tests: one test per documented error case verifying correct diagnostic | `[x]` | `tests/spec/test_spec_negative.py`: 20 tests for undefined vars, type mismatch, immutable assign, parse errors, scope errors |

**Done when:** SPEC.md is complete, version 1.0 Final, and every documented construct has a passing
spec compliance test on the LLVM backend.

---

## Phase 2 — Emitter Hardening
**Status:** `In Progress`
**Priority:** CRITICAL — the LLVM emitter must generate correct native code for any `.mn` program
**Platform:** Windows (all Python code)

The Python bootstrap compiler's LLVM emitter (`emit_llvm_mir.py`) has fundamental bugs
that prevent correct native code generation for complex programs — especially the 8,288-line
self-hosted compiler. This phase fixes those bugs systematically.

This phase exists because the original plan assumed the emitter was correct and just needed
"compilation + linking". Reality: 4 sessions, 12+ bugs found. Each fix reveals deeper issues.

### Already Fixed (from previous sessions)

| # | Bug | Fix | Files |
|---|-----|-----|-------|
| — | Cross-module enum variant resolution (101 constructors) | Call→EnumInit conversion via `{Enum}_{Variant}` lookup | `multi_module.py` |
| — | Cross-dep function refs (tokenize, mir_string, Program_start) | Namespace-aware remapping in multi_module.py | `multi_module.py` |
| — | Empty `List<String>` elem_size 8 instead of 16 | Propagate type annotation args to ListInit.elem_type | `lower.py` |
| — | IndexGet dest type always UNKNOWN | Infer element type from container's type_info.args | `lower.py` |
| — | `_unescape()` not called on non-interpolated strings | Call on all strings so `\n` = 0x0A for LLVM backend | `parser.py` |
| — | Heap string pointer tagging in mnc_main.c | Untag (clear bit 0) before fwrite | `mnc_main.c` |
| — | i8* → LLVM_LIST coercion missing | Added in `_emit_index_get` and `len()` call paths | `emit_llvm_mir.py` |
| — | String constants at byte alignment | `gv.align = 2` on all GlobalVariable string constants | `emit_llvm_mir.py`, `emit_llvm.py` |
| — | `lexer.mn` missing `tokens.push(tok)` | Added in all 5 scan branches | `lexer.mn` |
| — | ListPush not writing back to root alloca | `_list_roots` tracking + write-back | `emit_llvm_mir.py` |
| — | Range/iterator C runtime functions missing | Added `__range`, `__iter_has_next`, `__iter_next` | `mapanare_core.c` |
| — | jit.py incompatible with newer llvmlite API | Updated API calls | `jit.py` |

### Remaining Bugs

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Fix mutable variable alloca write-back in loops | `[ ]` | **CRITICAL.** The parser uses `defs = defs + [item]` (reassignment, not push). Each reassignment creates a new MIR value with a new alloca, but the loop header reads the stale original alloca. Need general mutable-variable write-back: track var→root_alloca mapping for all `_update_var` calls, or use single alloca per source variable. Same class of bug as ListPush fix but for ALL reassignment. |
| 2 | Verify emitter output matches Python bootstrap for 10+ test programs | `[ ]` | Compare `mnc-stage1` IR output vs `mapanare emit-llvm` output for: hello, fib, factorial, if/else, for loop, match, struct, enum, list ops, string ops. |
| 3 | Fix any additional emitter bugs surfaced by Task 2 | `[ ]` | Unknown unknowns — budget 2-5 more bugs based on rate so far. |
| 4 | Verify all 7 self-hosted modules compile to correct IR after fixes | `[ ]` | Rebuild `main.ll`, verify with llvmlite, check function bodies present. |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 5 | Test: mutable variable reassignment in loops produces correct values | `[ ]` | `let mut x = 0; for i in 0..5 { x = x + 1 }; assert x == 5` |
| 6 | Test: list accumulation via reassignment in loops | `[ ]` | `let mut xs = []; for i in 0..3 { xs = xs + [i] }; assert len(xs) == 3` |
| 7 | Test: emitter output comparison suite (10+ programs) | `[ ]` | Compare Python bootstrap vs mnc-stage1 IR output |

**Done when:** The LLVM emitter generates correct native code for all test programs AND for
the full self-hosted compiler (7 modules, 8,288+ lines). No known emitter bugs remain.

---

## Phase 3 — Stage 1 Native Compiler
**Status:** `In Progress`
**Priority:** CRITICAL — proves the self-hosted compiler actually works as a native binary
**Platform:** WSL/Linux (C runtime + linking)

Build `mnc-stage1` (Python bootstrap → native binary), then validate it can compile
arbitrary `.mn` programs correctly.

### Build

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Compile `mapanare/self/*.mn` → LLVM IR → object code → `mnc-stage1` binary | `[x]` | 51K-line LLVM IR → 4.9MB ELF. Build script: `scripts/build_stage1.py`. `mnc_main.c` wrapper. |
| 2 | Verify `mnc-stage1` can lex, parse, and type-check a simple `.mn` program | `[x]` | Exit code 0 on valid, 1 on errors. Full pipeline runs. |
| 3 | Verify `mnc-stage1` emits correct LLVM IR for simple programs | `[~]` | Blocked on Phase 2 Task 1 (alloca write-back). Currently emits declarations but no function bodies. |

### Validation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4 | `mnc-stage1` produces correct IR for 10+ programs (hello, fib, agents, signals, streams) | `[ ]` | After Phase 2 fixes, rebuild and validate. |
| 5 | Run bootstrap test suite (264 tests) against `mnc-stage1` | `[ ]` | All must pass. |
| 6 | Rebuild `mnc-stage1` after every Phase 2 fix and re-test | `[ ]` | Iterative: fix on Windows → rebuild on WSL → test → repeat. |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7 | Bootstrap compilation tests (IR generation, verification, object code) | `[x]` | 17/17 pass in `tests/bootstrap/test_stage1_compile.py`. |
| 8 | Stage 1 output correctness tests (compare mnc-stage1 vs Python bootstrap) | `[ ]` | For each test program: both produce identical IR (modulo metadata). |

**Done when:** `mnc-stage1` is a working native compiler that produces correct output for
the full test suite. 17+ bootstrap tests pass, 264+ validation tests pass.

---

## Phase 4 — Self-Hosted Fixed Point
**Status:** `Not Started`
**Priority:** HIGH — the compiler compiling itself proves correctness
**Platform:** WSL/Linux

The self-hosted compiler (`mnc-stage1`) compiles itself → `mnc-stage2`, which compiles
itself → `mnc-stage3`. If `mnc-stage2 == mnc-stage3` (byte-identical), the compiler has
reached a fixed point — it can sustain itself without Python.

### Self-Compilation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Use `mnc-stage1` to compile `mapanare/self/*.mn` → `mnc-stage2` | `[ ]` | The self-hosted compiler compiling itself. |
| 2 | Run bootstrap test suite against `mnc-stage2` | `[ ]` | All must pass — stage 2 is as capable as stage 1. |
| 3 | Diff LLVM IR: `mnc-stage1` vs `mnc-stage2` for test corpus | `[ ]` | Must be identical (modulo metadata). |

### Fixed Point Verification

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4 | Use `mnc-stage2` to compile `mapanare/self/*.mn` → `mnc-stage3` | `[ ]` | |
| 5 | Binary diff: `mnc-stage2` vs `mnc-stage3` | `[ ]` | Must be byte-identical — THIS is the fixed point. |
| 6 | Script the 3-stage pipeline: `scripts/verify_fixed_point.sh` | `[ ]` | Automate Stage 1→2→3 + diff. |

### CI Integration

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7 | Add fixed-point verification to CI (GitHub Actions, Linux x64) | `[ ]` | Runs on push to `dev`. |
| 8 | Gate release on fixed-point passing | `[ ]` | CI must green before version bump. |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 9 | Test: Stage 2 IR matches Stage 1 IR for all test programs | `[ ]` | |
| 10 | Test: Stage 3 binary is byte-identical to Stage 2 binary | `[ ]` | |

**Done when:** `mnc-stage2 == mnc-stage3` (byte-identical binaries) and CI enforces this
on every push. The compiler can compile itself without Python.

---

## Phase 5 — Formal Memory Model
**Status:** `Not Started`
**Priority:** HIGH — production users need guarantees about when memory is freed
**Platform:** Windows (docs) + WSL/Linux (sanitizers)

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

### Verification (WSL/Linux)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 10 | Run AddressSanitizer on full test suite | `[ ]` | Catch use-after-free, buffer overflow, double-free |
| 11 | Run ThreadSanitizer on agent/concurrency tests | `[ ]` | Catch data races in ring buffers, thread pool |
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

## Phase 6 — Stability Guarantees & Policy
**Status:** `Not Started`
**Priority:** MEDIUM — defines the contract with users
**Platform:** Windows

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

## Phase 7 — Final Hardening
**Status:** `Not Started`
**Priority:** HIGH — production readiness gate
**Platform:** WSL/Linux (native tests, sanitizers) + Windows (docs, benchmarks)

### Test Coverage (WSL/Linux)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Build I/O runtime on Linux: `python runtime/native/build_io.py` | `[ ]` | Unlocks 30 skipped tests |
| 2 | Pass all event loop tests (`tests/native/test_event_loop.py`) | `[ ]` | 7 tests |
| 3 | Pass all file I/O tests (`tests/native/test_file_io.py`) | `[ ]` | 12 tests |
| 4 | Pass all TCP tests (`tests/native/test_tcp.py`) | `[ ]` | 7 tests |
| 5 | Pass all TLS tests (`tests/native/test_tls.py`) | `[ ]` | 4 tests |
| 6 | Pass ASan hardening tests (`tests/native/test_c_hardening.py`) | `[ ]` | 2 tests, Linux-only |
| 7 | Audit remaining skips — only platform-specific skips allowed | `[ ]` | Target: ≤6 structural bootstrap skips |
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

## Phase 8 — Validation & Release
**Status:** `Not Started`
**Priority:** GATE — nothing ships until this phase completes
**Platform:** Both

### Pre-Release Checklist

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Full test suite green: `make test` — target 3,500+ tests, ≤6 skips | `[ ]` | |
| 2 | Lint clean: `make lint` (ruff + black + mypy) | `[ ]` | |
| 3 | Fixed-point verification passing in CI | `[ ]` | From Phase 4 |
| 4 | SPEC.md at "1.0 Final" | `[ ]` | From Phase 1 |
| 5 | MEMORY_MODEL.md complete | `[ ]` | From Phase 5 |
| 6 | STABILITY.md published | `[ ]` | From Phase 6 |
| 7 | All security audit findings resolved | `[ ]` | From Phase 7 |
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

| Date | Phase | Last Task | Next Task | Notes |
|------|-------|-----------|-----------|-------|
| 2026-03-14 | 2 | Phase 2 created (emitter hardening) | Phase 2 Task 1: mutable variable alloca write-back | **12+ bugs fixed across 4 sessions.** See 2026-03-14b entry. |
| 2026-03-14b | 2 | Task 6: mnc-stage1 correct IR emission | Task 6 continued: fix double-free crash in tokenizer | **4 bugs fixed prev session.** See full notes in memory. |
| 2026-03-14c | 2+3 | Double-free crash fixed | Fix struct return value from tokenize | **Bug #17 fixed this session:** ListPush stale intermediate alloca — `_emit_list_push` read from chain-predecessor allocas (a.t95, a.t103…) that were uninitialized in mutually-exclusive if/else branches. Fixed by reading from root alloca (`a.t0`) via `_list_roots` tracking. ASan-verified: zero memory errors. **Current state:** mnc-stage1 builds (5MB), no crash, 10+ test programs compile (hello, fib, if/else, for, match, struct, enum, list, string, function). **Remaining blocker:** tokenize() pushes tokens correctly (confirmed: 10+ pushes with debug), but returned `{i8*, i64, i64, i64}` struct arrives at parser with len=0. Parser sees `DBG tokens=0`, produces IR with only declarations, no function bodies. **Root cause hypothesis:** 32-byte struct return value ABI mismatch. LLVM returns `{i8*, i64, i64, i64}` via hidden sret pointer on x86-64. The caller may not be reading the sret correctly. Check: (1) how `parser__parse` calls `lexer__tokenize` and reads the return — does it use sret? (2) Compare calling convention between the two functions. (3) Try returning the list via pointer parameter instead of by value. **Key files:** `emit_llvm_mir.py:_emit_list_push` (fixed), `emit_llvm_mir.py:_emit_return` and `_emit_call` (next investigation target), `mapanare/self/main.ll` lines around `lexer__tokenize` call in `parser__parse`. |

---

## Phase Dependencies

```
Phase 1 (Spec Freeze)  ─────────────────────────────────┐
                                                         ├──→ Phase 6 (Stability Policy)
Phase 2 (Emitter Hardening) ──→ Phase 3 (Stage 1) ──┐   │
                                                     ├───┤
                                                     │   ├──→ Phase 7 (Hardening) ──→ Phase 8 (Release)
Phase 4 (Fixed Point) ←── Phase 3                    │   │
                                                     │   │
Phase 5 (Memory Model) ─────────────────────────────────┘
```

- **Phase 1** — Complete
- **Phase 2 → 3** — sequential (fix emitter, then build/test binary)
- **Phase 3 → 4** — sequential (need working stage 1 before self-compilation)
- **Phase 5** — independent (can run in parallel with 2/3)
- **Phase 6** — depends on Phase 1
- **Phase 7** — depends on Phase 3 (need native binary) + Phase 5 (need memory model for security audit)
- **Phase 8** — depends on all

### Priority order

1. **Phase 2** — Emitter Hardening (unblocks everything, active bugs)
2. **Phase 3** — Stage 1 Compiler (validates Phase 2 fixes, needs WSL)
3. **Phase 5** — Memory Model (independent, can parallel with 2/3)
4. **Phase 4** — Fixed Point (high risk, depends on Phase 3)
5. **Phase 6** — Stability Policy (small, can parallel with anything)
6. **Phase 7** — Hardening (depends on 3 + 5)
7. **Phase 8** — Release (after everything)

### Workflow

Phases 2 and 3 iterate together: fix bugs on Windows (Phase 2) → rebuild/test on WSL (Phase 3) → find new bugs → repeat. Phase 5 and 6 can run on Windows in parallel during WSL sessions.
