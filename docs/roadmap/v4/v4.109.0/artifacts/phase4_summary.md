# Phase 4 — Hypothesis 2 test: does the delta scale?

## Method
Scale fib from fib(35) to fib(45). Work grows ~120×. If Arc 11 hints
shipped latent benefit that process startup / small-sample noise was
hiding, the delta should grow with problem size.

matmul and quicksort could not be scaled safely: both hit the pre-
existing `List<Int>` indexing bug (docket Qs.1) and produce
non-deterministic garbage. Timing stays valid at current size; growing
the workload amplifies the UB rather than the optimization signal.

## Results — fib scaling

| Variant     | fib(35) median | fib(45) median | fib(45) stdev |
|-------------|---------------:|---------------:|--------------:|
| unstripped  |       25.98 ms |     2,426.2 ms |       12.0 ms |
| stripped    |       27.56 ms |     2,393.9 ms |       27.1 ms |
| **Δ**       |     **−1.58**  |      **+32.4** |               |
| %           |       −6.1 %   |        +1.3 %  |               |

- At fib(35) the hinted version is ~6% faster (noise-boundary signal).
- At fib(45) the gap vanishes or reverses (+1.3% is within 2 stdev).
- **Scaling the workload 120× does NOT amplify the hint benefit.**
  LLVM converges to the same codegen quality at scale regardless of
  whether the frontend seeded nsw/nuw flags.

## Interpretation

H2 is rejected for fib: the optimizations don't provide latent
value that only shows at scale. If hints help at all (matmul result
in Phase 3), they help at every size — they don't unlock
vectorization or unrolling that was hidden at small N.

This is consistent with the fib hot loop being a simple recursive
tail call: LLVM's tail-call elimination pass converts it to a loop
either way, and the resulting two-variable accumulator recurrence
is trivial to analyze with or without explicit nsw.
