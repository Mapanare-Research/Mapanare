# Pre-Panel Audit — v4.86.0 (Arc 11)

## Arc scope

| Version | Theme | Key deliverable |
|---------|-------|-----------------|
| v4.82.0 | Baseline benchmarks | 5 workloads, run_baseline.py, cross-language programs |
| v4.83.0 | Instruction-level IR | nounwind, inbounds on all GEPs, TBAA tree |
| v4.84.0 | Function-level IR | willreturn, noalias on sret |
| v4.85.0 | Results publication | ARC11_RESULTS.md, fresh measurements, honest negative |

## Test evidence

- Integration tests: 47/59 pass, stable across 3 runs
- Benchmarks: verified within 5% on re-run
- All 5 benchmarks correct checksums at O0/O1/O2

## Arc 11 hypothesis result

**The 2-3x hypothesis did not materialize.** IR annotations produced no statistically significant speedup. The bottleneck is opaque runtime FFI calls. This is a well-measured, honest negative result.

## IR annotation inventory

| Annotation | Semantic justification |
|------------|----------------------|
| `nsw` on add/sub/mul | Mapanare defines overflow as UB |
| `nounwind` on user fns | No exception mechanism |
| `willreturn` on user fns | Infinite recursion/loops are UB |
| `inbounds` on all GEPs | All pointer arithmetic is within allocated objects |
| TBAA tree | int/float/ptr/bool are distinct types |
| `noalias` on sret | Return slot is exclusive to the callee |
