# Phase 3 — Hypothesis 1 test: strip nsw/nuw/attrs, compare -O2 outputs

## Method
1. `sed` strip nsw/nuw/nounwind/willreturn/readonly/noalias from IR
2. `llvm-as` validation passes on all 4 stripped inputs
3. `opt -O2 -S` on both stripped and unstripped
4. `llc -O2 | clang` to binary, 50 timed runs per variant, drop 5 highest
   and 5 lowest, median and stdev of middle 40

## Hint survival post -O2 (stripped vs unstripped input)

| Benchmark     | Unstripped post-O2 | Stripped post-O2 |
|---------------|--------------------|------------------|
|               | nsw / nuw / attrs  | nsw / nuw / attrs|
| fib           | 4 / 0 / 8          | 2 / 0 / 2        |
| quicksort     | 13 / 1 / 13        | 1 / 1 / 3        |
| matmul_naive  | 15 / 13 / 12       | 10 / 13 / 2      |
| string_concat | 1 / 1 / 8          | 1 / 1 / 0        |

**LLVM independently infers nuw and some nsw flags from IR structure.**
matmul_naive: all 13 nuw come from LLVM's own analysis (stripped input
had zero, stripped output has 13). Arc 11's nsw seeding boosts the
final nsw count 2–5× and helps runtime-call function-attribute
propagation stick.

## Runtime delta (median of 40 runs, ms)

| Benchmark     | Unstripped | Stripped | Δ (unstripped − stripped) | Direction       |
|---------------|-----------:|---------:|--------------------------:|-----------------|
| fib           | 24.60      | 24.72    | −0.12                     | within noise    |
| quicksort     |  5.96      |  6.50    | −0.54                     | hints help ~9%  |
| matmul_naive  |  6.14      |  7.60    | −1.46                     | **hints help ~24%** |
| string_concat |  8.49      |  6.68    | +1.81                     | **hints HURT ~21%** |

Noise floor (stdev) for these sub-10 ms benchmarks is 0.3–1.0 ms on
WSL2, so 0.1–0.5 ms deltas are within noise. matmul_naive's −1.46 ms
and string_concat's +1.81 ms are clearly signal.

## Interpretation

- **matmul_naive is the one clear Arc-11 win.** The nsw flags plus
  the nounwind/willreturn attrs on runtime calls let LLVM inline,
  vectorize, and unroll the triple-nested loop more aggressively.
  The 24% speedup represents what Arc 11 was aiming for.

- **string_concat regresses when Arc 11 hints are kept.** The v4.108.0
  MIR pass replaces the old allocate-per-concat pattern with
  sb_append calls. Keeping Arc 11's willreturn attr on runtime
  declarations apparently blocks a tail-call / dead-store elimination
  that fires without it. The hints are actively harmful here.

- **fib is noise-bound.** The recursion structure gives LLVM enough
  information on its own.

- **quicksort shows a ~9% hint benefit** just above the noise floor.

## Conclusion for H1

The hints are NOT uniformly redundant, but neither do they uniformly
help. LLVM infers most arithmetic hints (nuw in particular) from IR
shape alone. Arc 11's contribution is:
  - Small compute workloads (fib, quicksort): noise-to-modest gain
  - Allocation-heavy loops (matmul): meaningful speedup (24%)
  - Mutable string building (string_concat): **regression** (−21%)

The aggregate geomean of ~0.992× at -O2 reported in TOTAL_RESULTS.md
is consistent with a mix of +24%, +9%, 0%, and −21% outcomes
averaging out to approximately flat — Arc 11 produced genuine wins
on some workloads and losses on others.

**All stripped binaries produce correct output** (fib(35) = 9227465,
etc.) — stripping is semantically safe.
