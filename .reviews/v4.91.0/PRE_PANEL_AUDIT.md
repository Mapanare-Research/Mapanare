# v4.91.0 Pre-Panel Audit — Arc 12 MIR Optimizer

**Date:** 2026-04-13
**Arc:** 12 (v4.87.0-v4.90.0) — MIR-level optimizer passes
**Prior panel:** v4.86.0 (Arc 11, LLVM IR quality) — 8.71/10 PASS

---

## What this panel grades

Arc 12 added three new MIR optimization passes and measured cumulative impact:

| Version | Pass | Lines added | Tests added |
|---------|------|-------------|-------------|
| v4.87.0 | Function inlining | ~200 | 2 (inline tests in pass combinations) |
| v4.88.0 | Loop detection + strength reduction | ~120 | 0 (infra only, LICM disabled) |
| v4.89.0 | Escape analysis + heap-to-stack promotion | ~305 | 12 (TestEscapeAnalysis) |
| v4.90.0 | Cumulative benchmark (no code) | 0 | 0 |

**Total new code in mir_opt.py:** ~625 lines across 3 passes.
**Total mir_opt.py:** 2,042 lines, 11 pass functions.
**Test coverage:** 73 MIR optimizer tests (12 escape analysis + 61 existing).

## Pre-panel verification

| Check | Result |
|-------|--------|
| MIR optimizer tests | 73/73 PASS |
| Core compiler tests | 1406/1406 PASS (10 pre-existing failures) |
| Compile time O2/O0 | 1.006x (677ms / 673ms) — negligible overhead |
| Fixpoint convergence | 10 iteration cap, no non-convergence observed |
| Pass stats reporting | All 12 counters functional including allocations_promoted |
| LICM | Disabled (miscompilation v4.88.0) — not graded as active pass |

## Benchmark exhibit

See `benchmarks/optimizer/TOTAL_RESULTS.md`:
- O2 geometric mean: 0.992x (flat vs v4.82.0)
- O0 geometric mean: 1.09x (9% improvement from IR quality)
- 4/5 benchmarks within 2x of Rust
- string_concat: -9.7% at O2 (MIR inlining benefit)

## Key questions for the panel

1. **Correctness:** Do the 3 new passes preserve program semantics? Is the escape analysis alias-set computation sound?
2. **LICM:** Is it acceptable to ship disabled infrastructure? Should it be removed or kept gated?
3. **Benchmark methodology:** Are 5 benchmarks x 5 runs x median sufficient? Is the Go absence a gap?
4. **Escape analysis emitter gap:** The analysis sets AllocKind.STACK but the emitter doesn't read it yet. Is this acceptable or does it constitute a hollow feature?
5. **Pass interaction:** Does the fixpoint loop with 10 passes converge reliably? Any evidence of ping-ponging?
