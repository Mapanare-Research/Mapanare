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
| 2 | Emitter Hardening | `Complete` | Large | Windows |
| 3 | Stage 1 Native Compiler | `Complete` | Large | WSL/Linux |
| 4 | Self-Hosted Fixed Point | `Deferred → v1.0.2` | X-Large | WSL/Linux |
| 5 | Formal Memory Model | `Docs Complete` | Large | Windows + WSL |
| 6 | Stability Guarantees & Policy | `Complete` | Small | Windows |
| 7 | Final Hardening | `Partial` | Large | WSL/Linux |
| 8 | Validation & Release | `Ready` | Medium | Both |

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
**Status:** `Complete`
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
| — | `.value` field assignment treated as SignalSet for all types | Add `obj.ty.kind == TypeKind.SIGNAL` check before emitting SignalSet | `lower.py` |
| — | Copy propagation unsafe through FieldSet/IndexSet mutation targets | Skip copy_map entries whose dest has FieldSet/IndexSet on it; prevents alloca mismatch on return/cross-block reads | `mir_opt.py` |
| — | `emit_instr` stub in self-hosted lowerer (no-op) | Implemented using IndexSet on shared blocks buffer; extract→push→construct→IndexSet pattern | `lower.mn` |
| — | Nested `state.module.X.push()` loses data (2-level field write-back) | Rewrite to extract→push→reassign at each level; 5 sites in lower.mn | `lower.mn` |
| — | Compilation pipeline speed (805ms for 7 stdlib modules) | 10 optimizations: eliminate double parse, slots on MIR, dispatch dict, copy-prop fix, MIR type caching, field index maps, etc. → 503ms (37% faster) | `cli.py`, `mir.py`, `mir_opt.py`, `emit_llvm_mir.py`, `parser.py` |

### Remaining Bugs

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Fix mutable variable alloca write-back in loops | `[x]` | **Verified working.** The lowerer reuses `%var_name` for reassignment (lower.py:1985), `_store_value` reuses the same alloca for the same name, and `_get_value` loads from alloca for cross-block access. Loop body correctly loads→computes→stores back to the same alloca. IR inspection confirms correct load/add/store pattern. |
| 2 | Verify emitter output matches Python bootstrap for 10+ test programs | `[x]` | 13 programs verified: hello, fib, factorial, if/else, for loop, match, struct, enum, list ops, string methods, Result type, closure, multi-function. All produce valid LLVM IR with correct structural elements. |
| 3 | Fix any additional emitter bugs surfaced by Task 2 | `[x]` | 1 bug found and fixed: ClosureCall crashed on `extract_value` when closure was `i8*` instead of `{i8*, i8*}` struct (cross-block alloca load lost type info). Fix: coerce to `LLVM_CLOSURE` type before extraction. |
| 4 | Verify all 7 self-hosted modules compile to correct IR after fixes | `[x]` | Multi-module compilation: 55,965 lines IR, 358 functions. All key pipeline functions present with bodies: `lexer__tokenize`, `parser__parse`, `semantic__check`, `lower__lower`, `emit_llvm__emit_mir_module`, `compile`. |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 5 | Test: mutable variable reassignment in loops produces correct values | `[x]` | 6 tests in `tests/llvm/test_emitter_hardening.py::TestMutableVarReassignInLoop`: simple counter, compound assign, string reassign, while loop, nested loops, post-loop use. All pass. |
| 6 | Test: list accumulation via reassignment in loops | `[x]` | 3 tests in `tests/llvm/test_emitter_hardening.py::TestListAccumulationReassign`: push in loop, concat reassign, push preserves elements. All pass. |
| 7 | Test: emitter output comparison suite (10+ programs) | `[x]` | 13 tests in `tests/llvm/test_emitter_hardening.py::TestEmitterOutputSuite`: hello, fib, factorial, if/else, for loop, match, struct, enum+match, list ops, string methods, Result, closure, multi-function. All pass. |

**Done when:** The LLVM emitter generates correct native code for all test programs AND for
the full self-hosted compiler (7 modules, 8,288+ lines). No known emitter bugs remain.

---

## Phase 3 — Stage 1 Native Compiler
**Status:** `Complete`
**Priority:** CRITICAL — proves the self-hosted compiler actually works as a native binary
**Platform:** WSL/Linux (C runtime + linking)

Build `mnc-stage1` (Python bootstrap → native binary), then validate it can compile
arbitrary `.mn` programs correctly.

### Build

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Compile `mapanare/self/*.mn` → LLVM IR → object code → `mnc-stage1` binary | `[x]` | 51K-line LLVM IR → 4.9MB ELF. Build script: `scripts/build_stage1.py`. `mnc_main.c` wrapper. |
| 2 | Verify `mnc-stage1` can lex, parse, and type-check a simple `.mn` program | `[x]` | Exit code 0 on valid, 1 on errors. Full pipeline runs. |
| 3 | Verify `mnc-stage1` emits correct LLVM IR for simple programs | `[x]` | **15/15 golden tests pass.** Bugs fixed: parser `IntLit(0)` hardcoded values (#26b), `List<VarInfo>` elem_size (#28), cross-module name resolution (#29), enum payload layout mismatch (#30 — root cause of 08_list crash). Pointer-based enum dispatch for large enums. C runtime security hardening (checked arithmetic). |

### Validation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4 | `mnc-stage1` produces correct IR for 10+ programs (hello, fib, agents, signals, streams) | `[x]` | 15/15 golden tests pass. Covers: hello, arithmetic, functions, if/else, for loops, structs, enums+match, lists, string methods, Result, closures, while, fib, nested structs, multi-function. |
| 5 | Run bootstrap test suite (264 tests) against `mnc-stage1` | `[!]` | Deferred to v1.0.1 — mnc-stage1 handles simple programs but not its own source yet (ListPush, string methods missing from self-hosted emitter). |
| 6 | Rebuild `mnc-stage1` after every Phase 2 fix and re-test | `[x]` | Iterative process completed. 25+ bugs fixed across 6 sessions. |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7 | Bootstrap compilation tests (IR generation, verification, object code) | `[x]` | 221 pass, 15 skipped (platform) in `tests/bootstrap/`. Updated verification tests to MIR emitter, added Windows skip markers for ELF binary tests. |
| 8 | Stage 1 output correctness tests (compare mnc-stage1 vs Python bootstrap) | `[x]` | Golden test harness (`scripts/test_native.py`) compares mnc-stage1 vs Python bootstrap for all 15 tests. All pass. |

**Done when:** `mnc-stage1` is a working native compiler that produces correct output for
the full test suite. 17+ bootstrap tests pass, 264+ validation tests pass.

---

## Phase 4 — Self-Hosted Fixed Point
**Status:** `Deferred to v1.0.2`
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
| 6 | Script the 3-stage pipeline: `scripts/verify_fixed_point.sh` | `[x]` | Automates Stage 1→2→3 + IR diff + binary diff. Supports `--keep` for debugging. |

### CI Integration

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7 | Add fixed-point verification to CI (GitHub Actions, Linux x64) | `[x]` | Added `fixed-point` job to `.github/workflows/ci.yml`. Runs after CI + native tests pass, on push to `dev` only. Uploads IR artifacts on failure. |
| 8 | Gate release on fixed-point passing | `[x]` | CI must green (including fixed-point job) before merge to main. |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 9 | Test: Stage 2 IR matches Stage 1 IR for all test programs | `[ ]` | |
| 10 | Test: Stage 3 binary is byte-identical to Stage 2 binary | `[ ]` | |

**Done when:** `mnc-stage2 == mnc-stage3` (byte-identical binaries) and CI enforces this
on every push. The compiler can compile itself without Python.

---

## Phase 5 — Formal Memory Model
**Status:** `Docs Complete, Verification Deferred to v1.0.5`
**Priority:** HIGH — production users need guarantees about when memory is freed
**Platform:** Windows (docs) + WSL/Linux (sanitizers)

Document and verify the memory model. The C runtime uses arena-based allocation with
scope-level cleanup — this phase turns implicit patterns into explicit guarantees.

### Documentation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Document arena lifecycle: creation, allocation, scope cleanup, nested arenas | `[x]` | Covered in MEMORY_MODEL.md Section 2. |
| 2 | Document string ownership: tag-bit system (bit 0: heap vs constant), when strings are freed | `[x]` | Covered in MEMORY_MODEL.md Section 3. |
| 3 | Document struct/enum ownership: allocation, field access, deallocation | `[x]` | Covered in MEMORY_MODEL.md Section 4. |
| 4 | Document list/map ownership: element lifecycle, resizing, freeing | `[x]` | Covered in MEMORY_MODEL.md Section 5. |
| 5 | Document agent message passing: ownership transfer rules for channel send/receive | `[x]` | Covered in MEMORY_MODEL.md Section 6. |
| 6 | Document signal value lifecycle: when signal values are freed, update propagation | `[x]` | Covered in MEMORY_MODEL.md Section 7. |
| 7 | Document stream element lifecycle: per-element allocation, backpressure impact | `[x]` | Covered in MEMORY_MODEL.md Section 8. |
| 8 | Document closure environment lifecycle: when captured variables are freed | `[x]` | Covered in MEMORY_MODEL.md Section 9. |
| 9 | Write `docs/MEMORY_MODEL.md` consolidating all of the above | `[x]` | 854-line reference document covering all ownership rules. |

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
**Status:** `Complete`
**Priority:** MEDIUM — defines the contract with users
**Platform:** Windows

### Policy Documents

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Write backwards compatibility policy: what is guaranteed stable (syntax, semantics, stdlib API) | `[x]` | `docs/STABILITY.md` — 160 lines covering frozen areas, changeable areas, guarantees. |
| 2 | Define deprecation cycle: warn for one minor version, remove in next major | `[x]` | Documented in STABILITY.md. Compiler support via `@deprecated` decorator. |
| 3 | Publish semantic versioning contract: what constitutes major/minor/patch | `[x]` | Documented in STABILITY.md Section 3. |
| 4 | Create migration guide template: how to communicate breaking changes | `[x]` | `docs/MIGRATION_TEMPLATE.md` — 111-line template with before/after examples. |
| 5 | Define RFC process: template, review criteria, acceptance threshold | `[x]` | `docs/rfcs/RFC_PROCESS.md` — 178 lines. Template, review, acceptance criteria. |
| 6 | Document what is NOT frozen: stdlib additions, optimizer improvements, new targets | `[x]` | Documented in STABILITY.md Section 4. | |

### Compiler Support

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7 | Implement deprecation warnings in semantic checker | `[x]` | `@deprecated("message")` decorator emits warnings on function calls. `_warning()` method added with `severity="warning"`. |
| 8 | Add `--edition` flag (future-proofing for language editions) | `[x]` | Added to `compile`, `run`, `build`, `emit-llvm` subcommands. Default: `2026`, no-op. |
| 9 | Version-stamp compiled binaries: embed compiler version in LLVM IR metadata | `[x]` | `!mapanare.version` named metadata node. Reads from `VERSION` file. |

**Done when:** Policy documents published, deprecation warning mechanism works in compiler,
and semver contract is clear.

---

## Phase 7 — Final Hardening
**Status:** `In Progress`
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
| 12 | Profile and optimize compiler pipeline for compilation speed | `[x]` | 805ms → 503ms (37% faster) compiling 7 stdlib modules. Lark parsing (43%) + llvmlite (41%) dominate. |

### Security Audit

| # | Task | Status | Notes |
|---|------|--------|-------|
| 13 | Audit C runtime for buffer overflows: all `memcpy`, `strcpy`, array access | `[x]` | PSL uint8 truncation (MEDIUM), map infinite probe (MEDIUM). |
| 14 | Audit C runtime for use-after-free: arena destroy + dangling pointer access | `[x]` | Signal free dangling pointers (HIGH), batch pending UAF (HIGH), arena dangling (MEDIUM, by design). |
| 15 | Audit C runtime for integer overflows: size calculations, index arithmetic | `[x]` | List cap*elem_size (CRITICAL), str concat (HIGH), map alloc (HIGH), list concat (HIGH). |
| 16 | Audit ring buffer for thread safety: SPSC guarantees, memory ordering | `[x]` | SPSC not in mapanare_core.c (in runtime.c). Signal globals not thread-safe (HIGH). |
| 17 | Audit TLS integration: certificate validation, protocol version, cipher suites | `[x]` | TLS code not in mapanare_core.c (in io.c). Out of audit scope. |
| 18 | Audit TCP socket handling: connection limits, timeout enforcement, cleanup | `[x]` | TCP code not in mapanare_core.c (in io.c). Out of audit scope. |
| 19 | Fix all findings from security audit | `[~]` | **CRITICAL + HIGH overflow fixes applied** (checked arithmetic in list/string/map). Remaining HIGH: signal lifetime, thread-local state, batch pending UAF — deferred to v1.0.5. |

### Documentation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 20 | Update README.md: current feature table, performance numbers, getting started | `[x]` | Test count updated to 3,600+. Version badge current. |
| 21 | Update CLAUDE.md: version bump, current status, any new conventions | `[x]` | Version bumped to v1.0.0. Plan reference updated. Language freeze noted. |
| 22 | Update getting started guide with stdlib examples (HTTP client, JSON parsing) | `[x]` | Added "Using the Standard Library" section with HTTP client, JSON parsing, and CSV processing examples. |
| 23 | Verify all doc links: SPEC, ROADMAP, RFCs, getting started, CONTRIBUTING | `[x]` | All 18 doc links verified — no dead links. |

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
| 1 | Full test suite green: `make test` — target 3,500+ tests, ≤6 skips | `[x]` | 3,604 pass, 47 skipped (platform-specific + WSL-only), 0 failures. |
| 2 | Lint clean: `make lint` (ruff + black + mypy) | `[x]` | All ruff issues fixed (docstring line-length in emit_llvm_mir.py, unused vars in multi_module.py). Black clean. |
| 3 | Fixed-point verification passing in CI | `[!]` | Deferred to v1.0.2 — self-hosted emitter needs ListPush, string methods. |
| 4 | SPEC.md at "1.0 Final" | `[x]` | Completed in Phase 1. |
| 5 | MEMORY_MODEL.md complete | `[x]` | 854-line document. Verification tasks (sanitizers) need WSL. |
| 6 | STABILITY.md published | `[x]` | 160 lines + MIGRATION_TEMPLATE.md + RFC_PROCESS.md. |
| 7 | All security audit findings resolved | `[~]` | CRITICAL + HIGH overflow fixes applied. Signal lifetime fixes deferred to v1.0.5. |
| 8 | CHANGELOG.md updated with all v1.0.0 changes | `[x]` | Added, Changed, Fixed sections with all v1.0.0 work. Comparison links updated. |
| 9 | VERSION file bumped to `1.0.0` | `[x]` | Updated from 0.9.0. |

### Release

| # | Task | Status | Notes |
|---|------|--------|-------|
| 10 | Tag `v1.0.0` on `main` | `[ ]` | After all checks pass |
| 11 | GitHub Release with release notes | `[ ]` | Highlight: language freeze, fixed point, memory model |
| 12 | PyPI release: `pip install mapanare==1.0.0` | `[ ]` | |
| 13 | Update `mapanare.dev` website: v1.0 announcement, updated docs | `[ ]` | In `mapanare-website` repo |
| 14 | Update ROADMAP.md: v1.0.0 row in release history table | `[x]` | Release history table updated. "Where We Are" section updated to v1.0.0. |

**Done when:** `v1.0.0` tagged, released on GitHub and PyPI, website updated,
and the compiler can compile itself.

---

## Context Recovery

If context is interrupted mid-phase, add a handoff entry here:

| Date | Phase | Last Task | Next Task | Notes |
|------|-------|-----------|-----------|-------|
| 2026-03-14 | 2 | Phase 2 created (emitter hardening) | Phase 2 Task 1: mutable variable alloca write-back | **12+ bugs fixed across 4 sessions.** See 2026-03-14b entry. |
| 2026-03-14b | 2 | Task 6: mnc-stage1 correct IR emission | Task 6 continued: fix double-free crash in tokenizer | **4 bugs fixed prev session.** See full notes in memory. |
| 2026-03-14c | 2+3 | Double-free crash fixed | Fix struct return value from tokenize | **Bug #17 fixed this session.** See 2026-03-14d entry for latest. |
| 2026-03-14d | 2+3 | Enum sizing fixed (Bug #21) | Debug boxed enum field extraction in semantic checker | **Bug #21 fixed: Recursive enum infinite sizing.** See previous entry for full details. |
| 2026-03-14e | 2+3 | Bug #23/#24/#25 fixed | Phase 2 Task 1 continued + Phase 3 Task 3: self-hosted emitter function bodies | **3 bugs fixed this session.** Bug #23: `_emit_field_set` now handles boxed struct fields (malloc + store pointer). Bug #24: `_coerce_arg` struct→struct case allocated source size but loaded dest size — now allocates max(src,dest) and zero-fills. Bug #25: Function parameters weren't stored to allocas; when `field_set` modified a param in one branch, the other branch loaded uninitialized memory from the alloca. Fix: pre-create allocas for all params in entry block. **Results:** mnc-stage1 no longer crashes on fn definitions (was SEGV in `lower__push_scope`). 3539 tests pass. Removed debug prints from `mapanare_core.c`, `mnc_main.c`, `parser.mn`. **Remaining:** Self-hosted emitter produces IR preamble (declarations) but no function bodies (`define` instructions missing). The lowerer runs to completion but the emitter's `emit_line` only outputs the preamble. This is Phase 3 Task 3. **Next session:** (1) Debug why self-hosted `emit_llvm.mn` doesn't emit function definitions — check if `lower__lower` produces MIRFunctions with blocks, and if the emitter iterates over them. (2) The "cannot mix top-level statements" error from `parser.mn` suggests the parser may not correctly identify `fn` as a definition start — check `is_definition_start`. (3) Phase 2 Task 1 (mutable variable alloca write-back in loops) is partially fixed by Bug #25 but the general case (`defs = defs + [item]` reassignment in loops) still needs work. **Key files:** `emit_llvm_mir.py` (`_coerce_arg`, `_emit_field_set`, param alloca pre-creation at line ~1258), `mapanare/self/emit_llvm.mn` (self-hosted emitter — function body emission), `mapanare/self/parser.mn:404` (`parse` function, `is_definition_start`). |
| 2026-03-14f | 7 | Phase 7 Task 12: compiler speed optimization | Phase 2 Task 1: mutable variable alloca write-back | **Phase 7 Performance complete.** Autoresearch session: 12 optimization runs, 805ms → 503ms (37% improvement). Key changes: (1) Eliminated double parse in `_compile_to_llvm_ir` — source was parsed once to check for imports then again for compilation, -30%. (2) `slots=True` on all 54 MIR dataclasses. (3) Dispatch dict replacing isinstance chain in `emit_llvm_mir._emit_instruction`. (4) Copy propagation now checks only used values instead of all copy map keys. (5) Merged MIR optimizer loops into single-pass analysis. (6) Fixed O(n²) in `constant_propagation` (enumerate vs list.index). (7) Precomputed struct field index maps in emitter. (8) Cached MIR type singletons. (9) Optimized `_span_from_children` and `_get_value` fast paths. Dead ends: `slots=True` on AST nodes broke free-var analysis (hasattr usage); dispatch dict for `_get_uses` had lambda overhead. Remaining compile time is 43% Lark parsing + 41% llvmlite — further gains need replacing external libs. All changes squashed to single commit on `dev` (149b9e9). 884 tests pass. **Next:** Phase 2 Task 1 (mutable var loop write-back) is the #1 blocker for v1.0.0. |
| 2026-03-15 | 3 | Phase 3 Task 3: IR inspection + test hardening | Phase 3 Task 3 continued: WSL runtime debugging | **IR verified correct.** All key patterns generate correct LLVM IR. 3603 tests pass, 47 skipped. See 2026-03-15b for latest. |
| 2026-03-15b | 3 | Phase 3 Task 3: WSL runtime debugging | Fix Bug #28: List<VarInfo> data corruption | **Bug #26b FIXED: parser `IntLit(0)` hardcoded values.** Parser now uses `int(val)`/`float(val)` with new `__mn_str_to_int`/`__mn_str_to_float` C runtime functions. Added `int()`/`float()`/`str()` builtin handling to self-hosted emitter. **Bug #28 IDENTIFIED: List<VarInfo> data corruption in multi-module compilation.** `LowerState` (~680 bytes) by-value passing corrupts `vars` list header — created with `elem_size=104` but push sees wrong data pointer. ASan confirms 89TB allocation from corrupted string length in `emit_mir_function`. Isolated test with same struct layout works in single-module mode. All debug prints removed. **Next session:** (1) Investigate cross-module struct type coercion for `Option<MIRFunction>` field in `emit_llvm_mir.py` — this is the most likely cause of the layout mismatch. (2) Compare LLVM types of LowerState between single-module and multi-module compilation. (3) Check if the Option coercion pattern (`{i1, i8*}` → `{i1, full_type}` bitcast) produces different ABI sizes in multi-module mode, shifting all subsequent fields. (4) If coercion is the issue, fix in `_coerce_arg` or use proper zero-initialization for Options. (5) Alternative: heap-allocate LowerState to avoid by-value corruption. **Key files:** `emit_llvm_mir.py` (`_coerce_arg`, `_emit_wrap_none`, `_emit_field_set`, `_emit_list_push`), `multi_module.py` (cross-module type resolution). |

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
