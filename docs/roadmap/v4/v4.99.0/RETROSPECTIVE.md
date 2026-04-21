# v4.x Retrospective — 99 Releases, the Full Journey

## The Timeline

| Phase | Versions | Releases | Theme |
|-------|----------|----------|-------|
| Production | v4.0.0-v4.26.0 | 27 | Language features, rapid growth |
| Crisis | v4.26.0 panel | 1 | 8.2/10, hollow features discovered |
| Recovery | v4.27.0-v4.31.0 | 5 | 9.343/10, discipline installed |
| Post-recovery plan | v4.32.0-v4.76.0 | 45 | 9 arcs, every feature real and tested |
| Extension | v4.77.0-v4.98.0 | 22 | Optimization, async, benchmarks |
| Final panel | v4.99.0 | 1 | This release |

**Total: 99 releases in the v4.x line.**

## The Numbers

| Metric | v4.26.0 (crisis) | v4.76.0 (plan end) | v4.99.0 (now) |
|--------|-------------------|---------------------|---------------|
| Panel aggregate | 8.2/10 | 9.343/10 | TBD |
| pytest count | ~2,000 | ~4,500 | 5,374 |
| Golden tests | ~25 | ~45 | 61 |
| Self-hosted .mn lines | ~8,000 | ~12,000 | 38,824 |
| C runtime lines | ~5,000 | ~10,000 | 14,243 |
| MIR optimizer passes | 3 | 3 | 7 (self-hosted) |
| fib(35) native | ~173ms | ~20ms | 19.6ms |

## What Arcs 10-14 Delivered

**Arc 10 (v4.77.0-v4.81.0): Integration tests + debt zero.** Established
the integration test pipeline. Carry-forward ledger driven to zero open
Mapanare-owned items.

**Arc 11 (v4.82.0-v4.86.0): Baseline + IR quality.** Created the first
cross-language benchmark suite. Added nsw/nuw, TBAA, function attributes
to the Python bootstrap emitter.

**Arc 12 (v4.87.0-v4.91.0): MIR optimizer passes.** Inlining (single-block
callees), LICM infrastructure, strength reduction, escape analysis.
Fixed convergence bug in the fixpoint loop.

**Arc 13 (v4.92.0-v4.96.0): Real async.** Coroutine suspension via
`coro.suspend`, multi-threaded scheduler with Chase-Lev work-stealing
deques, StringBuilder for O(1) string append. Panel: 8.57/10 PASS.

**Arc 14 (v4.97.0-v4.99.0): Self-hosted propagation + benchmarks.**
All 4 MIR optimization passes ported to mir_opt.mn. IR quality flags
ported to emit_llvm.mn. Final benchmark: 10 programs, 3 languages.

## What Worked

1. **The cadence.** PLAN.md → PROMPT.md → SESSION_REPORT.md for every
   release. No release ships without a plan. No plan ships without a
   session report. The system caught drift immediately.

2. **The panel system.** Seven reviewers every 5 releases. External
   perspective forced honesty. The v4.26.0 crisis was discovered by
   the panel, not by the developer.

3. **Carry-forward ledger.** Every finding tracked with a version tag.
   Nothing falls through the cracks. Items are CLOSED with evidence
   pointers or explicitly deferred with rationale.

4. **Culebra.** Template-driven IR diagnostics caught issues the test
   suite missed. Baseline tracking showed progress across releases.

5. **Benchmark discipline.** v4.82.0 established a baseline. v4.98.0
   measured the same programs with the same methodology. Honest numbers.

## What Didn't Work

1. **Tagged pointer UB.** `mn_tag_heap` in `mapanare_core.c` sets bit 0
   of `char*` pointers. This is undefined behavior in C. LLVM exploits
   it at -O2, producing a binary that emits garbled strings. This was
   discovered in v4.97.0 and is STILL OPEN. It blocks the self-hosted
   binary, golden test verification, and fixed-point validation.

2. **List indexing inconsistency.** `data[j]` returns garbage in some
   code patterns but works correctly in others (quicksort). The root
   cause is unknown. This blocks list-heavy benchmarks.

3. **Async linking gap.** The coroutine scheduler was implemented in the
   C runtime but the scheduler init/run/destroy functions were not
   exported to `libmapanare_rt.a`. Five async benchmarks compile but
   cannot be linked or run.

4. **Optimization ROI.** Arcs 11-12 added nsw/nuw, TBAA, inlining,
   LICM, escape analysis. The benchmark delta from v4.82.0 to v4.98.0
   is **zero** — LLVM -O2 was already capturing these gains. The work
   was not wasted (the IR is now well-formed for LTO/PGO), but the
   performance impact was overstated.

5. **String performance.** Despite 17 releases of optimization work,
   string concatenation is still 2.2x slower than Python. The
   StringBuilder optimization exists but is not automatically applied
   in all cases.

## What v5.0.0 Would Mean

v5.0.0 would signify: "the compiler is correct, the runtime is stable,
the language is complete, and external adoption is viable."

**The honest assessment:** The compiler produces correct and fast native
code for compute workloads. But the self-hosted binary doesn't work
(tagged pointer UB), list indexing is unreliable, async can't link,
and string handling is slower than Python. These are not v5.0.0-quality
issues. They are v4.100.0+ issues.

The cadence works. The numbers are honest. The work continues.
