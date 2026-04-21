# v4.90.0 Session Report — 2026-04-13

## Verdict

Measurement release. No new compiler code. Cumulative benchmark results
for Arc 11 + Arc 12 optimizer work (v4.82.0 through v4.89.0).

## Headline numbers

- **Geometric mean speedup at O2: 0.992x** (effectively flat vs v4.82.0 baseline)
- **String concatenation: -9.7% at O2** (the one benchmark with meaningful improvement)
- **O0 geometric mean: 1.09x** (9% faster — raw IR quality improved)
- **4 of 5 benchmarks within 2x of Rust** at O2
- **fib_recursive and agent_fanout within 1.1x of Rust** (near-parity)
- **40x faster than Python** on fib_recursive

## What was measured

5 benchmarks x 3 opt levels x 5 runs each, plus cross-language
comparison (Rust, Python; Go unavailable):

| Benchmark | v4.82.0 O2 | v4.90.0 O2 | vs Rust | vs Python |
|-----------|-----------|-----------|---------|-----------|
| fib_recursive | 19.55ms | 19.35ms (-1.0%) | 1.1x | 0.025x |
| quicksort | 1.63ms | 1.66ms (+1.8%) | 1.8x | 0.041x |
| matmul_naive | 1.28ms | 1.34ms (+4.7%) | 1.7x | 0.021x |
| string_concat | 96.08ms | 86.77ms (-9.7%) | 131.5x | 2.46x |
| agent_fanout | 0.65ms | 0.71ms (+9.2%) | 1.1x | 0.024x |

## Honest assessment

The O2 results are mostly flat because LLVM's own optimizer already
handled what our MIR passes do. Our passes primarily help at O0/O1
(where LLVM optimization is reduced) and for string-heavy code (where
MIR inlining exposes patterns LLVM alone can't see).

The string_concat outlier (131x vs Rust) is a runtime allocator issue,
not a codegen quality issue. Fixing this requires either amortized
string growth or wiring escape analysis into the emitter for stack
promotion — both are outside the optimizer pass scope.

Sub-2ms benchmarks (quicksort, matmul, agent_fanout) are in the noise
floor. Their apparent regressions (0.03-0.06ms) are within run-to-run
variance.

## Files produced

| File | Description |
|------|-------------|
| `benchmarks/optimizer/v4.90.0-current.json` | Fresh benchmark data |
| `benchmarks/optimizer/TOTAL_RESULTS.md` | 4-table analysis with narrative |
| `benchmarks/optimizer/reproduce.sh` | Reproduction script |

## Next session

v4.91.0: Arc 12 panel. 7 reviewers grade the optimizer arc. TOTAL_RESULTS.md
is the primary exhibit.
