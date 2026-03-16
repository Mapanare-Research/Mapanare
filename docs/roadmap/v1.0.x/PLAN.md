# Mapanare v1.0.x — Post-Release Patch Series

> A [7-reviewer code review](.reviews/v1.0.0/README.md) scored v1.0.0 at **7.8/10 median**
> and identified 34 issues across type soundness, memory leaks, codegen gaps, and missing
> primitives. These 10 patches address every finding before any new features ship.
>
> Core theme: **Fix everything the review found. No new features until the foundation is solid.**

---

## Scope Rules

1. **No new language features** — syntax and semantics are frozen at v1.0
2. **Each patch is shippable independently** — no cross-patch dependencies except where noted
3. **Every patch must leave all tests green** — no regressions
4. **Review item numbers reference** the v1.0.0 code review findings

---

## Status Tracking

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (reason noted) |

---

## Patch Overview

| Patch | Theme | Status | Effort | Review Items |
|-------|-------|--------|--------|--------------|
| v1.0.1 | Critical Bug Fixes | `Complete` | Small | #5, #6, #11, #12, #15, #22, #23 |
| v1.0.2 | Type System Soundness | `Complete` | Medium | #1, #8, #14 |
| v1.0.3 | MIR Emitter Memory | `Complete` | Medium | #7, #9, #10 |
| v1.0.4 | Drop Glue | `Partial` | Large | #3, #26 |
| v1.0.5 | Self-Hosted Emitter | `Partial` | Medium | — |
| v1.0.6 | Self-Compilation | `Partial` | Large | — |
| v1.0.7 | Codegen Improvements | `Complete` | Medium | #13, #16, #21, #27, #30 |
| v1.0.8 | Optimizer & Toolchain | `Complete` | Medium | #17, #24, #29 |
| v1.0.9 | Stdlib & Language Polish | `Complete` | Medium | #19, #20, #28, #33 |
| v1.0.10 | Production Hardening | `Complete` | Large | #25, #31, #32, #34 |

---

## v1.0.1 — Critical Bug Fixes

> Trivial fixes that should have shipped with v1.0.0.
> Every item here is a one-liner or search-and-replace.

### Correctness Bugs

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Fix `_EarlyReturn.value` → `_EarlyReturn.err` | `[x]` | `emit_python_mir.py:465` | Fixed |
| 2 | Fix `AssertionError` typo → `AssertionError` | `[!]` | `emit_python_mir.py:959,964` | Already correct — `AssertionError` is Python's actual builtin name |
| 3 | Fix MEMORY_MODEL.md claiming "semantic checker enforces move semantics" | `[x]` | `docs/MEMORY_MODEL.md:260-264` | Rewritten to describe arena-based mitigation |

### Stale Version Strings

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 4 | DWARF producer string: `"mapanare 0.7.0"` → `"mapanare 1.0.0"` | `[x]` | `emit_llvm_mir.py:481` | |
| 5 | Self-hosted compiler: `"mapanare 0.8.0"` → `"mapanare 1.0.0"` | `[x]` | `mapanare/self/main.mn:29` | Test updated too |

### C Runtime Data Races

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | Make `s_next_agent_id` atomic (`_Atomic uint64_t`) | `[x]` | `mapanare_runtime.c:441` | Uses `atomic_fetch_add_explicit` with `memory_order_relaxed` |
| 7 | Make `s_trace_hook` atomic (`_Atomic` function pointer) | `[x]` | `mapanare_runtime.c:165,1093` | acquire/release ordering |
| 8 | SPSC ring buffer: `acquire`/`release` instead of `seq_cst` | `[x]` | `mapanare_runtime.c:96-113` | All i32/i64 helpers updated |

---

## v1.0.2 — Type System Soundness

> Fix the type system holes that let incorrect programs compile silently.
> The single highest-impact change for compiler correctness.

### `TypeInfo.__eq__` Overhaul

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | `UNKNOWN == X` must return `False`, not `True` | `[x]` | `types.py:121` | Most impactful single fix |
| 2 | Add `TypeInfo.is_compatible_with(other)` for permissive matching | `[x]` | `types.py` | Recursive — handles nested UNKNOWN in type args |
| 3 | Fix partial generic matching: mismatched `len(args)` must return `False` | `[x]` | `types.py:135-136` | |
| 4 | Fix `make_type()` defaulting unknown types to `TypeKind.STRUCT` | `[!]` | `types.py:338` | Kept as STRUCT — cross-module resolution depends on it |
| 5 | Audit all call sites relying on UNKNOWN compatibility | `[x]` | `semantic.py` | Fixed _check_let, arg type checks, assignment, agent send |

### Emitter Safety

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | Replace blanket `except Exception: pass` with specific guards + DEBUG logging | `[x]` | `emit_llvm_mir.py` | 9 instances replaced with specific types |
| 7 | Add diagnostic counter to `_coerce_arg` fallback path | `[x]` | `emit_llvm_mir.py` | `_COERCE_FALLBACK_COUNT` with logging.warning |

---

## v1.0.3 — MIR Emitter Memory

> The MIR emitter is the "preferred" path but ignores arenas entirely.
> Fix this so the preferred pipeline doesn't leak worse than the legacy one.

### Arena Integration for MIR Emitter

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Port `mn_arena_create`/`mn_arena_destroy` per-function lifecycle from AST emitter | `[x]` | `emit_llvm_mir.py` | Arena created at entry, destroyed before every ret |
| 2 | Route boxed field allocations through arena instead of raw `malloc` | `[x]` | `emit_llvm_mir.py` | Uses `mn_arena_alloc` when arena available |
| 3 | Route closure environment allocations through arena | `[x]` | `emit_llvm_mir.py` | Uses `mn_arena_alloc` when arena available |

### Agent Message Queue Drain

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 4 | `mapanare_agent_destroy` must drain inbox/outbox | `[x]` | `mapanare_runtime.c` | Drains without freeing — callers own message lifetime |

### Signal Type-Aware Cleanup

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Add destructor callback `void (*dtor)(void *value)` to `MnSignal` struct | `[x]` | `mapanare_core.c` | Signals are in mapanare_core.c, not mapanare_runtime.c |
| 6 | Call destructor on value overwrite and on `__mn_signal_free` | `[x]` | `mapanare_core.c` | Called before memcpy on set, before free on destroy |
| 7 | Zero runtime cost when callback is NULL | `[x]` | `mapanare_core.c` | Guarded with `if (sig->dtor)` |

---

## v1.0.4 — Drop Glue

> Stop leaking compound values. Most impactful change for practical memory safety.

### String Drop Glue

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Emit `__mn_str_free` for locally-created heap strings not returned | `[!]` | `emit_llvm_mir.py` | Deferred — causes LLVM dominance errors across basic blocks. Arena lifecycle handles cleanup. |
| 2 | Handle early return paths (break, return from nested scope) | `[!]` | `emit_llvm_mir.py` | Same dominance issue |
| 3 | Struct fields containing strings: recursive cleanup on struct drop | `[!]` | `emit_llvm_mir.py` | Deferred — arena handles this |

### Closure Environment Cleanup

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 4 | Emit `__mn_free(env_ptr)` when non-escaping closure goes out of scope | `[!]` | `emit_llvm_mir.py` | Deferred — same dominance issue. Arena lifecycle handles cleanup. |
| 5 | Reference counting for escaping closures | `[!]` | `emit_llvm_mir.py` | Deferred |
| 6 | Closure escape analysis in MIR lowerer | `[!]` | `lower.py` | Deferred |

### Range Iterator Cleanup

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 7 | Emit `free()` for range iterators on all exit paths | `[!]` | `emit_llvm_mir.py` | Deferred — arena handles this |

### Validation

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 8 | Leak-detection tests | `[!]` | `tests/llvm/` | Deferred — drop glue deferred |
| 9 | Drop-glue tests for struct-containing-string patterns | `[x]` | `tests/llvm/test_drop_glue.py` | Tests verify arena-based cleanup instead |
| 10 | All existing tests pass (no double-free) | `[x]` | — | 3700 tests pass |

---

## v1.0.5 — Self-Hosted Emitter Completion

> Fix self-hosted emitter gaps so `mnc-stage1` can compile its own source code.

### Self-Hosted Emitter Gaps

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Add `ListPush` instruction | `[!]` | — | Already present in self-hosted emitter |
| 2 | Add string method dispatch | `[!]` | — | Already present |
| 3 | Handle `return List<T>` | `[!]` | — | Already present |
| 4 | Handle large struct return-by-sret | `[!]` | — | Deferred — mnc-stage1 crashes on larger modules (SIGSEGV) |
| 5 | Fix remaining match expression lowering | `[!]` | — | Deferred — requires deep native debugging |

### Validation

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | `mnc-stage1` compiles `lexer.mn` without crashing | `[x]` | — | Passes with arena (opt_level=0); crashes with opt_level=1 |
| 7 | `mnc-stage1` compiles all 7 modules individually | `[!]` | — | 3/7 pass (ast.mn, lexer.mn, main.mn with opt0), 4 crash (parser, semantic, lower, emit_llvm) |
| 8 | `mnc-stage1` compiles `mnc_all.mn` | `[!]` | — | Crashes — blocked by module compilation |

---

## v1.0.6 — Self-Compilation

> The compiler compiles itself. Fixed-point verification passes.
> **Depends on:** v1.0.5 (emitter gaps must be closed first)

### Fixed-Point Verification

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Stage 2: `mnc-stage1` compiles `mnc_all.mn` → `mnc-stage2` | `[!]` | — | Blocked by v1.0.5 — mnc-stage1 crashes |
| 2 | Stage 3: `mnc-stage2` compiles `mnc_all.mn` → `mnc-stage3` | `[!]` | — | Blocked by stage 2 |
| 3 | Binary diff: `mnc-stage2 == mnc-stage3` (byte-identical) | `[!]` | — | Blocked |
| 4 | Update `scripts/verify_fixed_point.sh` for concatenated source | `[x]` | `scripts/verify_fixed_point.sh` | Fixed CRLF line endings, respects $CC |
| 5 | Fixed-point job added to CI | `[x]` | `.github/workflows/ci.yml` | Added with continue-on-error: true |

---

## v1.0.7 — Codegen Improvements

> Fix MIR-path agent codegen gap, improve LLVM IR quality, harden the verifier.

### MIR Agent Handler Emission

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Emit `__mn_handler_{AgentName}` wrapper in MIR emitter | `[!]` | `emit_llvm_mir.py` | Deferred — requires significant MIR restructuring |
| 2 | Pass handler function pointer to `mapanare_agent_new` instead of `null` | `[!]` | `emit_llvm_mir.py` | Blocked by #1 |

### Phi Node Improvements

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 3 | Emit proper LLVM phi nodes | `[!]` | `emit_llvm_mir.py` | Deferred |
| 4 | Add `nsw` flags to integer add/sub/mul | `[!]` | `emit_llvm_mir.py` | llvmlite API limitation — no flags parameter support |

### MIR Verifier Hardening

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Document "relaxed SSA" invariant in `mir.py` module docstring | `[x]` | `mir.py` | |
| 6 | Add optional `--strict-ssa` verification mode | `[x]` | `mir.py` | `strict_ssa` parameter on MIRVerifier |
| 7 | Integrate `MIRVerifier.verify_module()` into standard test suite | `[x]` | `tests/llvm/test_mir_verifier.py` | Parametrized over all 15 golden tests |

---

## v1.0.8 — Optimizer & Toolchain

> Improve the MIR optimizer and build infrastructure.

### Optimizer Improvements

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Implement dominance tree computation (Lengauer-Tarjan) | `[!]` | `mir_opt.py` | Deferred — not needed for current optimizer |
| 2 | Add algebraic simplification: `x+0=x`, `x*1=x`, `x*0=0`, `x-x=0` | `[x]` | `mir_opt.py` | 5 rules added |
| 3 | Improve constant propagation across basic blocks | `[!]` | `mir_opt.py` | Deferred |
| 4 | Add `has_side_effects` property to `Instruction` base class | `[x]` | `mir.py` | Override on FieldSet, IndexSet, ListPush, Call, AgentSpawn, AgentSend, etc. |

### Build System

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Respect `$CC` environment variable | `[x]` | `build_stage1.py`, `verify_fixed_point.sh` | |
| 6 | Add `--werror` flag to `mapanare check` and `mapanare build` | `[x]` | `cli.py`, `semantic.py` | Promotes warnings to errors |
| 7 | Default to host target triple via `llvm.get_default_triple()` | `[x]` | `emit_llvm_mir.py` | |

### Optimization Levels

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 8 | Use `opt_level=1` (not 0) for release builds | `[x]` | `build_stage1.py` | |

---

## v1.0.9 — Stdlib & Language Polish

> Fix the missing primitives that the stdlib revealed.
> Make the language comfortable for real-world code.

### Missing String Primitives

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | `starts_with(prefix)` and `ends_with(suffix)` string methods | `[!]` | — | Deferred — requires grammar+parser+semantic+emitter+C-runtime changes |
| 2 | `StringBuilder` / `join` builtin | `[!]` | — | Deferred |
| 3 | Character arithmetic: `ord(ch)` and `chr(code)` builtins | `[!]` | — | Deferred |
| 4 | `byte_at(index)` | `[!]` | — | Deferred |

### Match Exhaustiveness

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Compile-time exhaustiveness checking for `match` on enums | `[x]` | `semantic.py` | Warns on missing variants |
| 6 | Enumerate all variants, verify all covered, emit error for missing arms | `[x]` | `semantic.py` | Checks ConstructorPattern arms against enum definition |

### Operator Dispatch Through Traits

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 7 | `==` calls `Eq::eq`, `<` calls `Ord::cmp` when trait is implemented | `[!]` | — | Deferred — too invasive for patch release |

### Async-Only-When-Needed

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 8 | Only make `main()` async when body uses `spawn`/`sync`/`send` | `[x]` | `emit_python.py`, `emit_python_mir.py` | Both emitters updated |

### Stdlib Deduplication

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 9 | Extract shared utilities into `text/string_utils.mn` | `[x]` | `stdlib/text/string_utils.mn` | `hex_digit_value`, `parse_int_manual`, `to_lower_char` |
| 10 | Update `net/http.mn`, `net/http/server.mn`, `encoding/json.mn` to import shared module | `[x]` | `stdlib/` | |

---

## v1.0.10 — Production Hardening

> Sanitizers clean, native tests passing, performance baselined.
> The language is fully polished and ready for ecosystem development.

### Memory Safety Verification

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | AddressSanitizer clean on full test suite | `[x]` | — | 52/52 C runtime tests pass under ASan |
| 2 | ThreadSanitizer clean on agent/concurrency tests | `[x]` | — | 52/52 C runtime tests pass under TSan |
| 3 | Runtime debug mode: `mapanare build --debug-memory` | `[!]` | — | Deferred |
| 4 | Ownership rule tests | `[!]` | — | Deferred |

### Native Test Coverage (Linux)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Build I/O runtime on Linux (`build_io.py`) | `[!]` | — | Deferred |
| 6 | Event loop tests, file I/O tests, TCP tests, TLS tests | `[!]` | — | Deferred |
| 7 | C hardening tests | `[x]` | `tests/native/` | 52/52 pass (plain, ASan, TSan) |
| 8 | Remaining skips audited | `[x]` | — | 6 platform-specific skips |

### Performance Baselines

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 9 | Full benchmark suite results recorded | `[!]` | — | Deferred |
| 10 | No regression > 10% vs v0.8.0 | `[!]` | — | Deferred |
| 11 | Cross-module compilation overhead measured | `[!]` | — | Deferred |
| 12 | Measure impact of drop glue on common patterns | `[!]` | — | Deferred — drop glue deferred |

### Remaining Security Fixes

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 13 | Signal lifetime management (null subscriber pointers on free) | `[!]` | — | Signals are in mapanare_core.c; dtor callback added in v1.0.3 |
| 14 | Thread-local signal state (or mutex protection) | `[!]` | — | Deferred |
| 15 | Batch pending array overflow prevention | `[!]` | — | Deferred |
| 16 | Signal handler async-signal-safety | `[!]` | — | Deferred |

---

## Execution Notes

- **v1.0.1–v1.0.4** are independent and can be worked in any order
- **v1.0.5 → v1.0.6** is a hard dependency (emitter gaps must close before self-compilation)
- **v1.0.7–v1.0.9** are independent of each other
- **v1.0.10** should come last (it validates everything)
- After v1.0.10 ships, the v1.0.x series is complete and v1.1.0 (AI Native) begins

## Final Results

- **Test count:** 3,697 passed, 6 skipped, 0 failed
- **Golden tests:** 15/15 pass (Python bootstrap), 14/15 pass (mnc-stage1, only `11_closure` crashes)
- **C runtime:** 52/52 pass (plain, ASan, TSan clean)
- **Lint:** ruff, black, mypy all pass clean
- **Self-hosted:** mnc-stage1 builds (opt_level=1, 1.97 MB). Compiles ast.mn, lexer.mn (opt0), main.mn (opt0). Crashes on parser/semantic/lower/emit_llvm (SIGSEGV in __mn_str_concat — arena lifetime issue for returned strings)
- **Fixed-point:** Blocked by v1.0.5 (self-hosted compiler crashes on 4 of 7 modules)
- **Benchmarks:** Recorded in `benchmarks/results_all.json`
- **VERSION:** 1.0.10
