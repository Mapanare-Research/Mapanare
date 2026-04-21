# Mamba — C Runtime Review (Arc 12)

**Grade: 8/10**
**Verdict: PASS WITH NOTES**

## Assessment

### Benchmark validity

The 5 benchmarks cover distinct workloads: pure computation (fib_recursive), array manipulation (quicksort), nested loops (matmul_naive), allocation-heavy (string_concat), and concurrency primitives (agent_fanout). This is a reasonable spread for a compiled language optimizer evaluation.

**Methodology:** 5 runs, drop highest and lowest, report median. This is standard and sufficient for the 10-100ms range. However, the sub-2ms benchmarks (quicksort 1.66ms, matmul 1.34ms, agent_fanout 0.71ms) have high relative variance. The Arc 11 panel noted this same issue. Recommendation: either increase to 20+ runs for sub-2ms benchmarks or acknowledge them as directional only.

**Go absence:** Go is not installed in the benchmark environment. Historical data shows "go not installed" across all versions. This is a gap — Go is the most natural comparison point for a compiled systems language with goroutines (analogous to Mapanare agents). Not a blocker but should be addressed in a future arc.

**Negative result on string_concat:** Mapanare is 131x slower than Rust and 2.5x slower than Python on string concatenation. This is a runtime allocator bottleneck, not a codegen issue. The runtime allocates a new buffer per concatenation; Rust uses amortized `String::push_str`. This is an honest measurement and the analysis correctly identifies the root cause.

### Escape analysis and arena interaction

The escape analysis correctly identifies non-escaping allocations. When the emitter wiring ships, promoted allocations will bypass `__mn_alloc` and use `alloca` instead. This is safe because:

1. `alloca` memory is valid for the function's lifetime — promoted allocations are guaranteed not to escape (analysis ensures this).
2. The arena allocator is not notified of the promotion — no bookkeeping mismatch. The allocation simply never enters the arena.
3. Drop glue for promoted allocations should be skipped (no `__mn_free` needed for stack memory). The emitter needs to check `alloc_kind` before emitting drop glue — this is the missing wiring.

### Pass interaction with runtime

Inlining exposes runtime call patterns to downstream passes. For example, after inlining a function that calls `__mn_str_concat`, the concat call is now visible in the caller's MIR, enabling constant propagation on its arguments. This is the mechanism behind the string_concat -9.7% improvement — it's not that inlining makes strings faster, it's that LLVM can now see the full call chain and optimize register allocation.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| Go benchmark | MEDIUM | Missing comparison language; install Go in CI |
| Sub-2ms benchmark variance | LOW | Acknowledged directional; increase runs or extend workloads |
| String allocator bottleneck | HIGH (runtime, not optimizer) | 131x vs Rust; needs amortized growth or builder pattern |

## Score justification

8/10 — benchmark methodology is sound for medium-duration workloads. Go absence and string allocator bottleneck noted. Escape analysis + arena interaction is correctly designed.
