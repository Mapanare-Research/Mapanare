# v4.99.0 Panel Summary — Arcs 10-14 Final Review

> 7 reviewers. Holistic grade covering v4.77.0-v4.98.0 (22 releases, 5 arcs).
> Panel date: 2026-04-13.

## Verdict Table

| Reviewer | Domain | Grade | Verdict |
|----------|--------|-------|---------|
| Rattler | LLVM/codegen | 6.5/10 | NEEDS WORK |
| Viper | Memory safety | 5.5/10 | NEEDS WORK |
| Anaconda | Toolchain/CI | 6.5/10 | NEEDS WORK |
| Cobra | ABI/fixed-point | 6.5/10 | PASS WITH SIGNIFICANT NOTES |
| Coral | Language design | 7.5/10 | PASS WITH RESERVATIONS |
| Boa | Developer experience | 7.5/10 | PASS WITH NOTES |
| Mamba | C runtime | 6.1/10 | CONDITIONAL PASS |

**Aggregate: 6.59/10**
**NEEDS WORK count: 3**
**Decision rule: aggregate < 9.0 -> Option B (continue v4.100.0+)**

## Consensus: NOT v5.0.0 READY

The panel unanimously agrees the language design, benchmark methodology,
and CI discipline are strong. The panel also unanimously agrees (6/7
explicitly, Cobra partially dissenting on the UB characterization) that
the tagged-pointer issue in `mapanare_core.c` is the single largest
blocker. It breaks the self-hosted binary, prevents golden test
verification, and makes the fixed-point claim untestable at runtime.

## Top Docket Items (for v4.100.0+)

### CRITICAL (must fix before any v5 discussion)

1. **Fix tagged-pointer UB in `mapanare_core.c`** — Replace `mn_tag_heap`
   bit-tagging with a separate `int8_t is_heap` field in `MnString`.
   Mamba estimates 3-4 hours. This unblocks the self-hosted binary,
   golden tests, fixed-point verification, and async linking.
   (Rattler, Viper, Anaconda, Mamba — all flagged)

2. **Fix list indexing bug** — `data[j]` returns garbage in some code
   contexts. Unknown root cause. Blocks list-heavy programs.
   (Coral, Boa — both flagged)

### HIGH

3. **Rebuild `libmapanare_rt.a`** with scheduler exports — Mamba confirmed
   the functions exist in source and the Makefile rule should include them.
   Verify end-to-end: async benchmark compiles, links, runs.
   (Anaconda flagged; Mamba says resolved in source)

4. **Verify `else`/`sino` works end-to-end** — Grammar has it, SPEC
   documents it, but benchmarks use `si cond {} si !cond {}` double-negation.
   Add an `else`/`sino` golden test. (Coral flagged)

5. **Fix closure type annotations** — `Fn(Int) -> Int` parses per grammar
   but lowering failed in v4.98.0 benchmarks. (Coral flagged)

### MEDIUM

6. **Disclose binary corruption** in README and `build_from_seed.sh` until
   fixed, with clear fallback to Python bootstrap. (Boa flagged)

7. **Fix byref size heuristic divergence** — Self-hosted emitter returns 256
   for all named structs; Python emitter computes actual size. Latent ABI
   inconsistency. (Cobra flagged)

8. **Coroutine frame layout coupling** — `mn_coro_is_done` reads a
   hardcoded offset. Fragile under LTO or LLVM version changes. (Viper flagged)

9. **String concat performance** — 2.2x slower than Python on naive concat.
   Route `+`-chains through StringBuilder automatically. (Mamba flagged)

### LOW

10. **Document bilingual keyword collision space** in SPEC. (Coral noted)
11. **Async-specific error messages** — cryptic suspension/cancellation errors. (Boa noted)

## What the Panel Got Right

- The tagged-pointer issue is real and fixable (3-4 hours per Mamba)
- The optimization ROI was overstated (Rattler: "zero measurable O2 speedup")
- The language design is genuinely coherent (Coral: 7.5/10)
- The benchmark discipline is honest (all reviewers acknowledged)
- The cadence works (all reviewers acknowledged)

## Score Context

| Panel | Aggregate | Outcome |
|-------|-----------|---------|
| v4.26.0 (crisis) | 8.2/10 | Recovery triggered |
| v4.31.0 (recovery close) | 9.343/10 | Recovery complete |
| v4.76.0 (plan end) | 9.0+/10 | Plan complete |
| v4.96.0 (Arc 13 close) | 8.57/10 | PASS |
| **v4.99.0 (v5 gate)** | **6.59/10** | **Option B: continue** |

The 6.59 is the lowest aggregate since v4.26.0. This is not a regression
in quality — it reflects that the panel was given explicit instructions to
grade with v5.0.0 readiness in mind, and the tagged-pointer corruption is
a v5-blocking defect that was discovered in v4.97.0 and not fixed.
