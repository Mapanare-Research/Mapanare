# v4.46.0 Session Report — Arc 3 Panel Release

**Date:** 2026-04-12
**Type:** Panel release (zero new features)
**Self-Grade:** 8.99/10 (panel aggregate)

---

## What This Release Did

Full 7-reviewer panel grading the tensor completeness arc (v4.42.0-v4.45.0).
Zero new features. Documentation polish, pre-panel audit, and panel execution.

## Panel Verdict

**Aggregate: 8.99/10** — CONDITIONAL PASS (0.01 below the 9.0 threshold)

| Reviewer | Score | Verdict |
|----------|-------|---------|
| Viper (memory safety) | 9.4 | PASS WITH NOTES |
| Boa (Python/DX) | 9.4 | PASS |
| Cobra (C++/ABI) | 9.45 | PASS |
| Mamba (C runtime) | 8.5 | PASS |
| Anaconda (toolchain) | 9.2 | PASS |
| Rattler (LLVM codegen) | 8.0 | PASS WITH RESERVATIONS |
| Coral (language design) | 9.0 | PASS WITH NOTES |

Zero explicit NEEDS WORK verdicts. Score pulled below 9.0 by Rattler (8.0)
and Mamba (8.5) due to implementation bugs found in new tensor code.

## Three Bugs Found

### BUG 1: Slicing inttoptr (CRITICAL — Rattler)
`_lower_tensor_slice` passes individual i64 values where the C runtime expects
`int64_t*` array pointers. LLVM emitter's `_coerce(i64→ptr)` emits `inttoptr`,
converting indices to memory addresses. Segfault at runtime. Passes llvm-as
validation because `inttoptr` is syntactically valid IR.

### BUG 2: Scalar-tensor sub/div operand swap (MEDIUM — Cobra, Anaconda, Rattler, Coral)
`_lower_tensor_binop` at `lower.py:2558-2563` swaps operands for non-commutative
scalar-tensor ops. `5.0 - Tensor<Float>[1.0]` computes `1.0 - 5.0 = -4.0`
instead of `5.0 - 1.0 = 4.0`. Shipping since v4.44.0, zero test coverage.

### BUG 3: Loop-body tensor temporaries leak (MEDIUM — Rattler)
Tensors allocated inside loop bodies are tracked in `_tensor_vars` but only
freed at function return, not per-iteration. The linear regression demo
allocates ~40 tensors over 10 iterations but frees ~6.

## Pre-Panel Work

1. **Smoke test:** 100/100 tensor-specific tests pass, 5/5 tensor goldens
   compile + validate via llvm-as, 4911/4948 pytest pass (37 infra-only failures)
2. **Documentation:** SPEC §3.10 expanded with broadcasting, reductions, slicing
   syntax. Cookbook recipe 15 (tensor ops + linear regression) added.
   `check_docs_drift.py` clean (140 blocks, 0 violations).
3. **Measurements:** Per-golden compilation times (626-672ms), IR sizes (15-30KB),
   42 tensor runtime function inventory.
4. **Pre-panel audit:** 18/19 SESSION_REPORT claims PASS, 1 FAIL (mean_i64
   missing — 11 reductions, not 12). Carry-forward queue: 3 items found stale
   (A7, A9, #50 are CLOSED).

## Carry-Forward Items Closed

| Item | Evidence |
|------|----------|
| SPEC §3.10 (5-cycle Coral debt) | Status line updated, body expanded with broadcasting/reductions/slicing docs |

## New Carry-Forward Items

| Item | Severity | Tracking |
|------|----------|----------|
| Slicing inttoptr bug | CRITICAL | v4.47.0 |
| Scalar-tensor sub/div operand swap | MEDIUM | v4.47.0 |
| Loop-body tensor temp leaks | HIGH | v4.47.0 |
| Tensor get/shape attrs repeat P1 pattern | MEDIUM | v4.47.0 |
| Self-hosted emit_tensor_init stub | MEDIUM | v4.47.0+ |
| examples/ showcase gap (5th cycle) | HIGH | v4.47.0+ |

## Key Decision

**Panel recommendation: CONDITIONAL PASS.** The bugs are localized implementation
errors in `lower.py` and `emit_llvm_text.py`, not architectural problems.
v4.47.0 fixes the 2 CRITICAL/MEDIUM bugs, then Arc 3 closes and Arc 4 opens.
A full recovery arc is disproportionate to the findings.

## Test Counts

- Tensor-specific pytest: 100 (167 found by Anaconda counting broader tensor-related tests)
- Full pytest: 4,911 pass
- Golden tests: 54 (6 tensor-related)
- docs drift blocks: 140, 0 violations

## Files Changed

- `docs/SPEC.md` — §3.10 broadcasting + reductions + slicing docs
- `docs/cookbook.md` — recipe 15 tensor operations
- `docs/reference.md` — tensor ops table expanded
- `docs/roadmap/v4/v4.46.0/SMOKE_TEST.md` — smoke test evidence
- `docs/roadmap/v4/v4.46.0/MEASUREMENTS.md` — compilation metrics
- `docs/roadmap/v4/v4.46.0/LEDGER_AUDIT.md` — carry-forward audit
- `docs/roadmap/v4/v4.46.0/PRE_PANEL_AUDIT.md` — 18/19 claims verified
- `.reviews/v4.46.0/` — 7 reviewer files + README.md + culebra artifacts
- `.reviews/prompt.md` — retargeted to v4.46.0

## Breaking Changes

None. Panel release.
