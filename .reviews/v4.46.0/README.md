# Mapanare v4.46.0 Panel — Arc 3 Close (Tensor Completeness)

**Date:** 2026-04-12
**Reviewers:** 7 (independent, parallel)
**Previous Review:** v4.41.0 (9.36/10 aggregate, 4 PASS + 3 PASS WITH NOTES)
**Arc Under Review:** Arc 3 — Tensor Completeness (v4.42.0-v4.45.0)

---

## Verdict Table

| # | Reviewer | Domain | Verdict | Score | Delta vs v4.41.0 | Top 3 observations |
|---|----------|--------|---------|-------|-------------------|---------------------|
| 01 | **Viper** | Rust / memory safety | PASS WITH NOTES | 9.4 | -0.1 | Tensor get/shape attrs repeat P1 pattern (MEDIUM); slice stride recomputation (MEDIUM); sum_i64 overflow UB (LOW) |
| 02 | **Boa** | Python / DX | PASS | 9.4 | +0.2 | Silent default to FLOAT_TYPE for unknown element types (HIGH); shape annotation mismatch ignored (MEDIUM); beautiful broadcasting errors |
| 03 | **Cobra** | C++ / ABI | PASS | 9.45 | -0.35 | **Scalar-tensor sub/div operand swap bug** (MEDIUM); broadcast O(ndim) per-element decomposition (LOW); real primitive surface over opaque-ptr internals |
| 04 | **Mamba** | C / runtime | PASS | 8.5 | -1.0 | Tensor alloc uses malloc not arena (MEDIUM); 9 dead functions (LOW); no view support means ABI break ahead (LOW) |
| 05 | **Anaconda** | toolchain | PASS | 9.2 | +0.3 | **Scalar-tensor sub/div bug** (MEDIUM); self-hosted emit_tensor_init still null-ptr stub (MEDIUM); 167 tensor tests found (more than claimed 100) |
| 06 | **Rattler** | LLVM / codegen | PASS WITH RESERVATIONS | 8.0 | -1.4 | **Slicing inttoptr i64→ptr bug** (CRITICAL); **scalar-tensor sub/div** (MEDIUM); loop-body tensor temporaries leak (MEDIUM) |
| 07 | **Coral** | Language design | PASS WITH NOTES | 9.0 | -0.2 | SPEC §3.10 CLOSED (5-cycle carry-forward resolved); **scalar-tensor sub/div** (MEDIUM); examples/ showcase gap (5th cycle HIGH) |

---

## Aggregate

**Aggregate score: 8.99/10** (down from 9.36 at v4.41.0, -0.37 delta)

**Verdicts: 3 PASS + 3 PASS WITH NOTES + 0 explicit NEEDS WORK**

**Arc 3 termination gate: BORDERLINE** — aggregate is 0.01 below the 9.0 threshold. Zero explicit NEEDS WORK verdicts, but Rattler's "PASS WITH RESERVATIONS" (8.0) pulls the aggregate below the line. The three bugs found are specific and fixable.

---

## Consensus

The panel agrees that Arc 3 delivered a **real tensor primitive** — not syntactic sugar. The four-release layered approach (literals → indexing → broadcasting → reductions/slicing) was clean and disciplined. The linear regression demo is the strongest proof-of-concept the language has shipped.

**Three bugs found by multiple reviewers prevent a clean PASS:**

### BUG 1: Slicing inttoptr (CRITICAL) — Rattler

`_lower_tensor_slice` in `lower.py` passes individual `i64` start/end values where the C runtime `__mn_tensor_slice` expects `int64_t*` array pointers. The LLVM emitter's `_coerce(i64 → ptr)` emits `inttoptr`, converting index values like 0 or 2 into memory addresses. This will segfault at runtime. The IR passes `llvm-as` because `inttoptr` is syntactically valid LLVM IR.

**Fix:** Allocate starts/ends arrays on the stack, store indices into them, pass array pointers.

### BUG 2: Scalar-tensor sub/div operand swap (MEDIUM) — Cobra, Anaconda, Rattler, Coral

`_lower_tensor_binop` in `lower.py:2558-2563` swaps operands for `scalar - tensor` and `scalar / tensor`, computing `tensor[i] - scalar` instead of `scalar - tensor[i]`. This is a correctness bug shipping since v4.44.0 with zero test coverage for non-commutative scalar-tensor ops.

**Fix:** Add `_scalar_*` runtime variants or negate/reciprocal after the swap.

### BUG 3: Loop-body tensor temporaries leak (MEDIUM) — Rattler

The linear regression demo allocates ~40 tensors across 10 loop iterations but only frees ~6 at function exit. Intermediate tensors created inside the loop body (`pred`, `error`, broadcast results) are tracked in `_tensor_vars` but only freed once at return, not per-iteration.

**Fix:** Insert drop glue at loop-body exit or implement a tensor scope stack.

---

## Post-Production Health

**Is the language still healthy 46 minors after v4.0.0?** YES, with caveats.

The tensor surface is well-designed and properly integrated across all compiler phases. The bugs found are implementation errors in the lowering layer, not architectural problems. The SPEC §3.10 status is truthful. The test infrastructure caught the tensor happy paths but missed edge cases (non-commutative scalar ops, array-vs-value pointer semantics in slicing).

---

## Prioritized Action Items

### CRITICAL (must fix before Arc 3 can close)

| # | Item | Source |
|---|------|--------|
| 1 | Slicing inttoptr: allocate starts/ends arrays, pass pointers not values | Rattler BUG-2 |
| 2 | Scalar-tensor sub/div: correct non-commutative operand handling | Cobra M1, Anaconda M1, Rattler BUG-3, Coral |

### HIGH (fix in v4.47.0)

| # | Item | Source |
|---|------|--------|
| 3 | Loop-body tensor temporaries: per-iteration drop glue or scope stack | Rattler BUG-1 |
| 4 | `examples/` showcase gap (5th cycle) — add agent/signal/stream/tensor demos | Coral, P5 |
| 5 | `_check_tensor_literal` silent FLOAT_TYPE default for unknown element types | Boa H1 |

### MEDIUM

| # | Item | Source |
|---|------|--------|
| 6 | Tensor get/shape `readonly+willreturn` repeat P1 misannotation pattern | Viper V1 |
| 7 | Self-hosted `emit_tensor_init` still null-ptr stub (4 releases) | Anaconda M2 |
| 8 | Tensor alloc uses raw malloc, not arena allocator | Mamba |
| 9 | SPEC shape annotations silently ignored vs literal shapes | Boa M4 |
| 10 | Slice stride recomputation inside inner loop | Viper V2, Cobra L2 |

### LOW

| # | Item | Source |
|---|------|--------|
| 11 | `__mn_tensor_sum_i64` signed overflow UB | Viper V3 |
| 12 | i64_div returns 0 on divide-by-zero (inconsistent with abort elsewhere) | Viper V4 |
| 13 | 9 dead/redundant tensor runtime functions | Mamba |
| 14 | Flat store silently drops OOB writes (inconsistent with N-D abort) | Viper V5 |
| 15 | `__mn_tensor_mean_i64` missing (11 reductions, not 12 as claimed) | Pre-panel audit, Coral |

---

## Disagreements

No fundamental disagreements. All reviewers agree:
- The tensor surface is well-designed
- Copy-based slicing (not views) is the right choice for v4.x
- The three bugs are real and must be fixed
- Arc 3 delivered what it promised

Mamba and Rattler scored lower due to runtime implementation quality concerns. Cobra, Boa, and Anaconda scored higher, focusing on the design and pipeline integration.

---

## Improvements Since v4.41.0

- SPEC §3.10 status changed from aspirational to truthful (5-cycle debt resolved)
- 42 new tensor runtime C functions with bounds checking
- 100+ new tensor-specific tests across parser/semantic/LLVM layers
- 6 new golden tests (including the linear regression showcase)
- NumPy-compatible broadcasting with rustc-quality error messages
- Cookbook recipe 15 (tensor operations) added
- carry-forward items A7, A9, #50 found CLOSED during pre-panel audit

---

## Regressions Since v4.41.0

- Aggregate score: 9.36 → 8.99 (-0.37)
- Rattler dropped -1.4 (largest single-reviewer drop) due to bugs in new code
- Mamba dropped -1.0 due to runtime quality concerns
- Three correctness bugs introduced in v4.44.0-v4.45.0

---

## Panel Recommendation

**CONDITIONAL PASS.** The aggregate (8.99) is 0.01 below the 9.0 threshold, driven by two specific bugs (slicing inttoptr, scalar-tensor sub/div). Zero reviewers gave explicit NEEDS WORK.

**Recommendation:** Fix the 2 CRITICAL bugs in a v4.46.1 hotfix or early v4.47.0, then Arc 3 closes. This is not a recovery scenario — the bugs are localized implementation errors, not architectural problems. A full recovery arc would be disproportionate to the issues found.
