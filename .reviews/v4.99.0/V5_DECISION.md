# v5 Gate Decision — v4.99.0

## Score

**Aggregate: 6.59/10**
**NEEDS WORK: 3 reviewers (Rattler, Viper, Anaconda)**

## Decision Rule

- Aggregate >= 9.0 AND 0 NEEDS WORK -> Option A (tag v5.0.0)
- Aggregate < 9.0 -> **Option B (continue v4.100.0+)**
- Aggregate >= 8.5 AND < 9.0 -> Option C (tag + continue)

**Applied: Option B.** Aggregate 6.59 < 9.0, with 3 NEEDS WORK.

## What Option B Means

v4.100.0 opens. The panel's docket (11 items) becomes Arc 15 scope.
The next scheduled panel is v4.104.0 (5-minor cadence). The version
number does not change. The discipline does not change.

## What Must Be Fixed Before v5 Can Be Discussed Again

1. **Tagged-pointer UB** — Replace `mn_tag_heap` bit-tagging with a
   struct field. Rebuild mnc-stage1. Verify golden tests pass.
2. **List indexing bug** — Root-cause and fix `data[j]` garbage in
   accumulation patterns.
3. **Async end-to-end** — Link and run at least one async benchmark
   natively (not just compile to IR).

## The Lead's Assessment

The panel is right. The tagged-pointer issue is a 3-4 hour fix that
blocks everything downstream. It should have been fixed in v4.97.0
when it was discovered. Shipping v4.97.0 and v4.98.0 with a known
binary-corruption bug was a process failure — the anti-rush rules say
"fix the root cause" and we didn't.

The optimization work (Arcs 11-12) was real engineering but the
performance narrative was overstated. The IR annotations didn't move
the O2 numbers. That's an honest finding and the FINAL_REPORT.md
correctly reports it.

The path to v5.0.0 is clear:
1. Fix the tagged-pointer UB (v4.100.0)
2. Fix list indexing (v4.101.0)
3. Async end-to-end verification (v4.102.0)
4. Verify else/sino + closure types (v4.103.0)
5. Panel at v4.104.0 — re-evaluate v5 gate

Estimated: 5 releases, ~2-3 sprints. The work is bounded and known.

## v5.0.0 Tag

**Not created.** Option B does not tag v5.0.0.
