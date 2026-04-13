# Arc 12 Panel — v4.91.0

**Arc:** 12 (Optimizer Phase 2 — MIR-Level Passes)
**Releases graded:** v4.87.0 - v4.90.0
**Panel date:** 2026-04-13
**Aggregate: 8.57/10**
**Verdict: PASS (4 PASS, 3 PASS WITH NOTES, 0 NEEDS WORK)**

Arc 12 added three MIR-level optimization passes (function inlining,
strength reduction, escape analysis), built loop analysis infrastructure,
and measured the cumulative impact of two arcs of optimizer work. All
passes are semantically correct. The benchmark results are honest: O2
geometric mean is flat (0.992x) because LLVM's own optimizer already
handles most of what MIR passes do. The real value is in O0/O1
improvement (9% geomean) and the cross-language story (4/5 within 2x
of Rust).

---

## Verdict Table

| # | Reviewer | Lens | Grade | Verdict |
|---|----------|------|-------|---------|
| 1 | Rattler | LLVM (PRIMARY) | 8/10 | PASS WITH NOTES |
| 2 | Cobra | C++/ABI | 9/10 | PASS |
| 3 | Mamba | C runtime | 8/10 | PASS WITH NOTES |
| 4 | Viper | Memory safety | 9/10 | PASS |
| 5 | Anaconda | Toolchain | 9/10 | PASS |
| 6 | Boa | Python/DX | 8/10 | PASS WITH NOTES |
| 7 | Coral | Language design | 9/10 | PASS |

**Aggregate: 8.57/10** (60/70)

---

## Consensus findings

### What Arc 12 delivered

1. **MIR function inlining (v4.87.0).** Cost-model-driven, single-block
   callees, conservative budget. Single largest runtime improvement on
   string_concat (-7.20ms). SSA correctness verified — no ABI changes,
   no semantic changes.

2. **Loop infrastructure (v4.88.0).** Dominators, natural loops, MIRLoop
   dataclass. Strength reduction (mod→AND) active. LICM built but
   correctly disabled after miscompilation. Infrastructure ships, broken
   transform doesn't.

3. **Escape analysis (v4.89.0).** 6 escape criteria, 50+ known
   non-capturing functions, alias-set computation via fixed-point over
   Copy/Phi. Sound analysis. 4KB cap, loop guard, idempotent. 12 new
   tests. **Emitter wiring not yet shipped** — annotation only.

4. **Cumulative benchmark (v4.90.0).** 5 benchmarks, 3 opt levels,
   cross-language (Rust, Python). O2 geomean 0.992x. O0 geomean 1.09x.
   4/5 benchmarks within 2x of Rust. Honest measurement, honest narrative.

### Unanimous checkpoints

- 7/7 agree: all three passes are semantically correct
- 7/7 agree: no miscompilation risk from the shipped passes
- 7/7 agree: LICM gating was the right decision
- 7/7 agree: benchmark methodology is sound for medium-duration workloads
- 7/7 agree: the honest O2 flat result is correctly reported

### Docket (items for future arcs)

| Item | Source | Priority | Notes |
|------|--------|----------|-------|
| Escape analysis emitter wiring | Rattler, Mamba | **HIGH** | AllocKind.STACK set but not consumed — ship codegen benefit |
| ExternCall escape path | Viper | MEDIUM | Arguments to extern "C" calls should be marked escaping |
| String allocator bottleneck | Mamba | HIGH (runtime) | 131x vs Rust; needs amortized growth or builder |
| `@noinline` annotation | Boa | MEDIUM | User control over inlining |
| `@pure` annotation | Boa | MEDIUM | Enables LICM |
| Go benchmark | Mamba | MEDIUM | Missing comparison language |
| Optimization guide | Coral | MEDIUM | User documentation for O0-O3 |
| Per-function pass stats | Boa | LOW | Optimizer debugging aid |
| Sub-2ms benchmark variance | Mamba, Anaconda | LOW | Increase runs or extend workloads |

---

## Arc 12 retrospective

### What worked

1. **Pass-by-pass development.** Each version shipped one pass with its
   own tests and session report. This made the arc easy to review — each
   delta is small and self-contained.

2. **Measurement discipline.** The v4.82.0 baseline was established before
   any changes. Each version measured its incremental delta. v4.90.0
   provided the cumulative view. The honest flat O2 result prevented
   false claims.

3. **Conservative defaults.** The inliner is budget-limited. Escape
   analysis has size and loop guards. LICM was disabled rather than
   shipped broken. These decisions prioritize correctness over
   performance, which is the right call for an optimizer arc.

### What could improve

1. **Escape analysis is incomplete.** The analysis is sound but the
   emitter doesn't consume it. This is the difference between "we can
   identify promotable allocations" and "allocations are actually
   promoted." The next arc should close this gap.

2. **LICM remains disabled.** The loop infrastructure shipped but the
   transform didn't. Loop-carried value tracking needs to be resolved.

3. **Cross-language gap.** Go benchmarks are missing. For a language with
   agents (analogous to goroutines), Go is the most relevant comparison.

### Arc 12 closes

With aggregate 8.57/10 and 0 NEEDS WORK, **Arc 12 closes.** The docket
items are future work for subsequent arcs.
