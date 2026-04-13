# Anaconda — Toolchain Review (Arc 12)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

### O2 pipeline composition

The unified fixpoint loop at O2 now contains 10 passes (8 O2-level + 2 O1-level). The iteration cap is 10. Key question: does adding 3 new passes (inlining, strength reduction, escape analysis) cause convergence issues?

**Evidence of convergence:**
- 73/73 MIR optimizer tests pass, including tests that exercise the full O2 pipeline.
- 1406/1406 core compiler tests pass — no non-convergence exceptions observed.
- The `MIROptimizerNonConvergence` exception with its diagnostic message was never triggered during testing.

**Idempotency analysis:**
- **Inlining:** Processes one call site per iteration. After all eligible calls are inlined, no more call sites match. Idempotent on settled MIR. ✓
- **Strength reduction:** Replaces `mod 2^n` with `and (2^n-1)`. After replacement, the original BinOp is gone. Cannot re-trigger. ✓
- **Escape analysis:** Sets `alloc_kind = STACK` on qualifying instructions. On subsequent iterations, the `alloc_kind == STACK` check skips them. Idempotent. ✓

**Pass ordering:** Escape analysis runs after DCE and strength reduction, which is correct — dead allocations are removed before analysis runs, reducing false negatives. Inlining runs after copy propagation, allowing propagated constants to flow into inlined bodies.

### Compile time overhead

Measured on fib_recursive.mn:
- O0: 673ms
- O1: 669ms
- O2: 677ms

**Ratio: 1.006x.** Effectively zero overhead. The Python interpreter startup (~500ms) dominates; MIR passes execute in microseconds on small programs. For the self-hosted compiler (14,000+ lines), the overhead would be slightly higher but still negligible compared to parsing and emission.

### CI integration

The MIR optimizer tests (`tests/mir/test_mir_opt.py`) run in CI as part of the standard pytest suite. The 12 new escape analysis tests are automatically included. The benchmark suite (`run_baseline.py`) is not in CI but has a `reproduce.sh` for manual reproduction. This is acceptable — benchmarks are inherently environment-dependent and should not gate CI.

### reproduce.sh

The benchmark reproduction script checks prerequisites, accepts a `--quick` flag, and produces deterministic output. The script is well-structured. One note: it should emit the LLVM version for reproducibility (minor).

## Score justification

9/10 — pipeline composition is sound, convergence is empirically verified, compile time overhead is negligible. All passes are idempotent. CI coverage is adequate.
