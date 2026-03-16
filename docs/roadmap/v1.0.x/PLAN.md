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
| v1.0.1 | Critical Bug Fixes | `Not started` | Small | #5, #6, #11, #12, #15, #22, #23 |
| v1.0.2 | Type System Soundness | `Not started` | Medium | #1, #8, #14 |
| v1.0.3 | MIR Emitter Memory | `Not started` | Medium | #7, #9, #10 |
| v1.0.4 | Drop Glue | `Not started` | Large | #3, #26 |
| v1.0.5 | Self-Hosted Emitter | `Not started` | Medium | — |
| v1.0.6 | Self-Compilation | `Not started` | Large | — |
| v1.0.7 | Codegen Improvements | `Not started` | Medium | #13, #16, #21, #27, #30 |
| v1.0.8 | Optimizer & Toolchain | `Not started` | Medium | #17, #24, #29 |
| v1.0.9 | Stdlib & Language Polish | `Not started` | Medium | #19, #20, #28, #33 |
| v1.0.10 | Production Hardening | `Not started` | Large | #25, #31, #32, #34 |

---

## v1.0.1 — Critical Bug Fixes

> Trivial fixes that should have shipped with v1.0.0.
> Every item here is a one-liner or search-and-replace.

### Correctness Bugs

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Fix `_EarlyReturn.value` → `_EarlyReturn.err` | `[ ]` | `emit_python_mir.py:465` | Crashes every MIR `?` error path |
| 2 | Fix `AssertionError` typo → `AssertionError` | `[ ]` | `emit_python_mir.py:959,964`, `bootstrap/emit_python_mir.py`, `docs/SPEC.md`, `test_test_runner.py` | Search-and-replace |
| 3 | Fix MEMORY_MODEL.md claiming "semantic checker enforces move semantics" | `[ ]` | `docs/MEMORY_MODEL.md:260-264` | Update docs to match reality (it does not) |

### Stale Version Strings

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 4 | DWARF producer string: `"mapanare 0.7.0"` → `"mapanare 1.0.0"` | `[ ]` | `emit_llvm_mir.py:483` | |
| 5 | Self-hosted compiler: `"mapanare 0.8.0"` → `"mapanare 1.0.0"` | `[ ]` | `mapanare/self/main.mn:29` | |

### C Runtime Data Races

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | Make `s_next_agent_id` atomic (`_Atomic uint64_t`) | `[ ]` | `mapanare_runtime.c:441` | |
| 7 | Make `s_trace_hook` atomic (`_Atomic` function pointer) | `[ ]` | `mapanare_runtime.c:165,1093` | |
| 8 | SPSC ring buffer: `acquire`/`release` instead of `seq_cst` | `[ ]` | `mapanare_runtime.c:96-113` | |

---

## v1.0.2 — Type System Soundness

> Fix the type system holes that let incorrect programs compile silently.
> The single highest-impact change for compiler correctness.

### `TypeInfo.__eq__` Overhaul

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | `UNKNOWN == X` must return `False`, not `True` | `[ ]` | `types.py:121` | Most impactful single fix |
| 2 | Add `TypeInfo.is_compatible_with(other)` for permissive matching | `[ ]` | `types.py` | New method |
| 3 | Fix partial generic matching: mismatched `len(args)` must return `False` | `[ ]` | `types.py:135-136` | |
| 4 | Fix `make_type()` defaulting unknown types to `TypeKind.STRUCT` | `[ ]` | `types.py:338` | Should error instead |
| 5 | Audit all call sites relying on UNKNOWN compatibility | `[ ]` | `semantic.py` | MethodCallExpr, SyncExpr, ErrorPropExpr, FieldAccessExpr, for-loop variables |

### Emitter Safety

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | Replace blanket `except Exception: pass` with specific guards + DEBUG logging | `[ ]` | `emit_llvm_mir.py:1503,1728,1730,2782` | |
| 7 | Add diagnostic counter to `_coerce_arg` fallback path | `[ ]` | `emit_llvm_mir.py` | Log warnings when memory reinterpretation fires |

---

## v1.0.3 — MIR Emitter Memory

> The MIR emitter is the "preferred" path but ignores arenas entirely.
> Fix this so the preferred pipeline doesn't leak worse than the legacy one.

### Arena Integration for MIR Emitter

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Port `mn_arena_create`/`mn_arena_destroy` per-function lifecycle from AST emitter | `[ ]` | `emit_llvm_mir.py` | Reference: `emit_llvm.py:844-891` |
| 2 | Route boxed field allocations through arena instead of raw `malloc` | `[ ]` | `emit_llvm_mir.py:2525,2637,2959` | |
| 3 | Route closure environment allocations through arena | `[ ]` | `emit_llvm_mir.py:3470` | |

### Agent Message Queue Drain

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 4 | `mapanare_agent_destroy` must drain inbox/outbox and free remaining messages | `[ ]` | `mapanare_runtime.c:405-408` | Match pool destroy behavior |

### Signal Type-Aware Cleanup

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Add destructor callback `void (*dtor)(void *value)` to `MnSignal` struct | `[ ]` | `mapanare_runtime.h`, `mapanare_runtime.c` | |
| 6 | Call destructor on value overwrite and on `__mn_signal_free` | `[ ]` | `mapanare_runtime.c` | |
| 7 | Zero runtime cost when callback is NULL | `[ ]` | `mapanare_runtime.c` | Guard with `if (sig->dtor)` |

---

## v1.0.4 — Drop Glue

> Stop leaking compound values. Most impactful change for practical memory safety.

### String Drop Glue

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Emit `__mn_str_free` for locally-created heap strings not returned | `[ ]` | `emit_llvm_mir.py` | At function exit |
| 2 | Handle early return paths (break, return from nested scope) | `[ ]` | `emit_llvm_mir.py` | |
| 3 | Struct fields containing strings: recursive cleanup on struct drop | `[ ]` | `emit_llvm_mir.py` | |

### Closure Environment Cleanup

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 4 | Emit `__mn_free(env_ptr)` when non-escaping closure goes out of scope | `[ ]` | `emit_llvm_mir.py` | Simple case |
| 5 | Reference counting for escaping closures (increment on copy, decrement on exit) | `[ ]` | `emit_llvm_mir.py` | |
| 6 | Closure escape analysis in MIR lowerer | `[ ]` | `lower.py` | |

### Range Iterator Cleanup

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 7 | Emit `free()` for range iterators on all exit paths (normal, break, return) | `[ ]` | `emit_llvm_mir.py` | |

### Validation

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 8 | Leak-detection tests: closures in a loop, verify RSS doesn't grow | `[ ]` | `tests/llvm/` | |
| 9 | Drop-glue tests for struct-containing-string patterns | `[ ]` | `tests/llvm/` | |
| 10 | All existing tests pass (no double-free) | `[ ]` | — | Gate |

---

## v1.0.5 — Self-Hosted Emitter Completion

> Fix self-hosted emitter gaps so `mnc-stage1` can compile its own source code.
> Each fix is small (20-30 lines of `.mn`) but there are many.

### Self-Hosted Emitter Gaps

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Add `ListPush` instruction to `Instruction` enum, lowerer, and emitter | `[ ]` | `mapanare/self/lower.mn`, `mapanare/self/emit_llvm.mn` | |
| 2 | Add string method dispatch in `emit_mir_call` | `[ ]` | `mapanare/self/emit_llvm.mn` | char_at, substr, contains, split, etc. |
| 3 | Handle `return List<T>` from functions (list built with push in loops) | `[ ]` | `mapanare/self/emit_llvm.mn` | |
| 4 | Handle large struct return-by-sret in self-hosted emitter | `[ ]` | `mapanare/self/emit_llvm.mn` | |
| 5 | Fix remaining match expression lowering for complex patterns | `[ ]` | `mapanare/self/lower.mn` | |

### Validation

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | `mnc-stage1` compiles `lexer.mn` without crashing | `[ ]` | — | Gate |
| 7 | `mnc-stage1` compiles all 7 modules individually | `[ ]` | — | Gate |
| 8 | `mnc-stage1` compiles `mnc_all.mn` (concatenated 8,632 lines) | `[ ]` | — | Gate |

---

## v1.0.6 — Self-Compilation

> The compiler compiles itself. Fixed-point verification passes.
> **Depends on:** v1.0.5 (emitter gaps must be closed first)

### Fixed-Point Verification

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Stage 2: `mnc-stage1` compiles `mnc_all.mn` → `mnc-stage2` | `[ ]` | — | |
| 2 | Stage 3: `mnc-stage2` compiles `mnc_all.mn` → `mnc-stage3` | `[ ]` | — | |
| 3 | Binary diff: `mnc-stage2 == mnc-stage3` (byte-identical) | `[ ]` | — | Fixed point achieved |
| 4 | Update `scripts/verify_fixed_point.sh` for concatenated source | `[ ]` | `scripts/verify_fixed_point.sh` | |
| 5 | Fixed-point job added to CI | `[ ]` | `.github/workflows/ci.yml` | Gate for future releases |

---

## v1.0.7 — Codegen Improvements

> Fix MIR-path agent codegen gap, improve LLVM IR quality, harden the verifier.

### MIR Agent Handler Emission

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Emit `__mn_handler_{AgentName}` wrapper in MIR emitter | `[ ]` | `emit_llvm_mir.py` | Currently only AST emitter does this |
| 2 | Pass handler function pointer to `mapanare_agent_new` instead of `null` | `[ ]` | `emit_llvm_mir.py:3293` | |

### Phi Node Improvements

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 3 | Emit proper LLVM phi nodes for clean SSA values (not mutated via field_set) | `[ ]` | `emit_llvm_mir.py` | Keep alloca demotion only for genuinely mutable vars |
| 4 | Add `nsw` flags to integer add/sub/mul | `[ ]` | `emit_llvm_mir.py` | Better LLVM optimization |

### MIR Verifier Hardening

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Document "relaxed SSA" invariant in `mir.py` module docstring | `[ ]` | `mir.py` | Mutable variables may be redefined |
| 6 | Add optional `--strict-ssa` verification mode | `[ ]` | `mir.py` | |
| 7 | Integrate `MIRVerifier.verify_module()` into standard test suite | `[ ]` | `tests/` | Run on all 15 golden tests after lowering and after optimization |

---

## v1.0.8 — Optimizer & Toolchain

> Improve the MIR optimizer and build infrastructure.

### Optimizer Improvements

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Implement dominance tree computation (Lengauer-Tarjan) | `[ ]` | `mir_opt.py` | ~100 lines |
| 2 | Add algebraic simplification: `x+0=x`, `x*1=x`, `x*0=0`, `x-x=0` | `[ ]` | `mir_opt.py` | |
| 3 | Improve constant propagation across basic blocks | `[ ]` | `mir_opt.py` | Not just Copy-of-Const |
| 4 | Add `has_side_effects` property to `Instruction` base class | `[ ]` | `mir.py` | Replace fragile `_SIDE_EFFECT_TYPES` tuple |

### Build System

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Respect `$CC` environment variable | `[ ]` | `build_stage1.py`, `verify_fixed_point.sh` | `os.environ.get("CC", "gcc")` / `${CC:-gcc}` |
| 6 | Add `--werror` flag to `mapanare check` and `mapanare build` | `[ ]` | `cli.py`, `semantic.py` | Treat warnings as errors |
| 7 | Default to host target triple via `llvm.get_default_triple()` | `[ ]` | `emit_llvm_mir.py` | |

### Optimization Levels

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 8 | Use `opt_level=1` (not 0) for release builds | `[ ]` | `build_stage1.py` | Enables mem2reg, instcombine, simplifycfg, sroa |

---

## v1.0.9 — Stdlib & Language Polish

> Fix the missing primitives that the stdlib revealed.
> Make the language comfortable for real-world code.

### Missing String Primitives

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | `starts_with(prefix)` and `ends_with(suffix)` string methods | `[ ]` | Grammar, parser, semantic, emitters, C runtime | |
| 2 | `StringBuilder` type or `join(separator, parts: List<String>)` builtin | `[ ]` | — | Eliminate O(n^2) concat |
| 3 | Character arithmetic: `ord(ch) -> Int` and `chr(code) -> String` builtins | `[ ]` | — | |
| 4 | `byte_at(index)` → integer value for byte-level operations | `[ ]` | — | |

### Match Exhaustiveness

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Compile-time exhaustiveness checking for `match` on enums | `[ ]` | `semantic.py` | Spec promises this |
| 6 | Enumerate all variants, verify all covered, emit error for missing arms | `[ ]` | `semantic.py` | |

### Operator Dispatch Through Traits

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 7 | `==` calls `Eq::eq`, `<` calls `Ord::cmp` when trait is implemented | `[ ]` | `semantic.py`, emitters | Makes user-defined types work with generic algorithms |

### Async-Only-When-Needed

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 8 | Only make `main()` async when body uses `spawn`/`sync`/`send` | `[ ]` | `emit_python.py`, `emit_python_mir.py` | ~1-2ms startup savings |

### Stdlib Deduplication

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 9 | Extract shared utilities into `text/string_utils.mn` | `[ ]` | `stdlib/text/string_utils.mn` | `to_lower_char`, `hex_digit_value`, `parse_int_manual`, `to_upper` |
| 10 | Update `net/http.mn`, `net/http/server.mn`, `encoding/json.mn` to import shared module | `[ ]` | `stdlib/` | |

---

## v1.0.10 — Production Hardening

> Sanitizers clean, native tests passing, performance baselined.
> The language is fully polished and ready for ecosystem development.

### Memory Safety Verification

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | AddressSanitizer clean on full test suite | `[ ]` | — | |
| 2 | ThreadSanitizer clean on agent/concurrency tests | `[ ]` | — | |
| 3 | Runtime debug mode: `mapanare build --debug-memory` for bounds checking | `[ ]` | `cli.py`, `emit_llvm_mir.py` | |
| 4 | Ownership rule tests (arena scoping, string tag-bit, agent message, closure env, drop glue) | `[ ]` | `tests/` | |

### Native Test Coverage (Linux)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Build I/O runtime on Linux (`build_io.py`) | `[ ]` | `runtime/native/build_io.py` | |
| 6 | Event loop tests (7), file I/O tests (12), TCP tests (7), TLS tests (4) | `[ ]` | `tests/native/` | |
| 7 | C hardening tests (2) | `[ ]` | `tests/native/` | |
| 8 | Remaining skips audited — target ≤6 platform-specific skips | `[ ]` | — | |

### Performance Baselines

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 9 | Full benchmark suite results recorded as v1.0 baselines | `[ ]` | `benchmarks/` | |
| 10 | No regression > 10% vs v0.8.0 | `[ ]` | — | Gate |
| 11 | Cross-module compilation overhead measured | `[ ]` | — | |
| 12 | Measure impact of drop glue on common patterns | `[ ]` | — | |

### Remaining Security Fixes

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 13 | Signal lifetime management (null subscriber pointers on free) | `[ ]` | `mapanare_runtime.c` | |
| 14 | Thread-local signal state (or mutex protection) | `[ ]` | `mapanare_runtime.c` | |
| 15 | Batch pending array overflow prevention (grow beyond 256, or error) | `[ ]` | `mapanare_runtime.c` | |
| 16 | Signal handler async-signal-safety (set flag, handle in main thread) | `[ ]` | `mapanare_runtime.c` | |

---

## Execution Notes

- **v1.0.1–v1.0.4** are independent and can be worked in any order
- **v1.0.5 → v1.0.6** is a hard dependency (emitter gaps must close before self-compilation)
- **v1.0.7–v1.0.9** are independent of each other
- **v1.0.10** should come last (it validates everything)
- After v1.0.10 ships, the v1.0.x series is complete and v1.1.0 (AI Native) begins
