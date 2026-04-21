# Mapanare v4.85.0 — Benchmark Refresh: Arc 11 Phase 1 Results

> **Arc 11 release 4.** The payoff measurement. Re-runs the full
> benchmark suite from v4.82.0, computes delta tables showing the
> cumulative impact of v4.83.0 (nsw/TBAA/inbounds/mem2reg) and
> v4.84.0 (function attributes). Refreshes cross-language comparison.
> Publishes `ARC11_RESULTS.md` -- the definitive answer to "did it
> work?"

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.84.0
**Delta review:** No
**Full panel:** No (v4.86.0)
**Estimated work:** 1 sprint
**Theme:** Measure the payoff. Close the loop.

---

## Scope

This is a measurement release. No IR changes. No new compiler features.
The entire release is about running benchmarks, computing deltas, and
publishing results.

The hypothesis from Arc 11's inception: making the emitted IR
"LLVM-friendly" (nsw/nuw, TBAA, inbounds, function attributes) should
yield a 2-3x speedup over the v4.82.0 baseline, closing the gap with
Go from 5.8x to 2-3x.

v4.85.0 answers the question: did it work?

### What we measure

1. **Per-benchmark speedup** -- each of the 5 programs, at O0/O1/O2:
   - fib_recursive (pure integer compute)
   - quicksort (array access + recursion)
   - matmul_naive (loop-heavy FP math)
   - string_concat (allocation-heavy)
   - agent_fanout (concurrency runtime)

2. **Per-release delta** -- isolate what v4.83.0 vs v4.84.0 contributed:
   - v4.82.0 -> v4.83.0 (nsw/TBAA/inbounds/mem2reg)
   - v4.83.0 -> v4.84.0 (function attributes)
   - v4.82.0 -> v4.85.0 (cumulative)

3. **Cross-language gap** -- fresh numbers for Python, Go, Rust on the
   same 5 workloads. How much did the gap close?

4. **Opt-level analysis** -- does the improvement mostly appear at O2?
   Does O1 get most of the benefit? Is O0 unchanged (expected)?

---

## Phase 1 -- Re-run benchmark suite

- [ ] Run `benchmarks/optimizer/run_baseline.py` on the current (v4.84.0+) IR
- [ ] All 5 benchmarks, all 3 opt levels (O0, O1, O2)
- [ ] 5 runs per config, median of middle 3 (same methodology as v4.82.0)
- [ ] Verify all checksums match baseline
- [ ] Save raw results to `benchmarks/optimizer/v4.85.0-final.json`

## Phase 2 -- Compute delta tables

- [ ] Load `v4.82.0-baseline.json`, `v4.83.0-delta.json`, `v4.84.0-delta.json`, `v4.85.0-final.json`
- [ ] Compute per-benchmark, per-opt-level:
  - Delta v4.82.0 -> v4.83.0 (already computed; re-verify)
  - Delta v4.83.0 -> v4.84.0 (already computed; re-verify)
  - **Cumulative delta v4.82.0 -> v4.85.0** (fresh measurement vs original baseline)
- [ ] Express deltas as both absolute (ms) and relative (speedup factor)
- [ ] Identify which optimization had the biggest impact per benchmark

## Phase 3 -- Cross-language refresh

- [ ] Re-run Python, Go, Rust programs from `benchmarks/optimizer/`
- [ ] Same methodology: 5 runs, median of middle 3
- [ ] Fresh numbers (don't reuse v4.82.0 cross-language data -- machine state may differ)
- [ ] Save cross-language results in `v4.85.0-final.json` under `cross_language` key

## Phase 4 -- Publish ARC11_RESULTS.md

- [ ] `benchmarks/optimizer/ARC11_RESULTS.md`:
  - **Table 1: Cumulative speedup** -- v4.82.0 baseline vs v4.85.0 final, all 5 benchmarks at O2
  - **Table 2: Per-release breakdown** -- v4.83.0 contribution vs v4.84.0 contribution
  - **Table 3: Cross-language comparison** -- Mapanare O2 vs Python vs Go vs Rust
  - **Table 4: Gap closure** -- v4.82.0 gap (Go/Mapanare ratio) vs v4.85.0 gap
  - **Table 5: Opt-level analysis** -- O0 vs O1 vs O2 for Mapanare (showing where LLVM's optimizer benefits most)
  - **Narrative**: what worked, what didn't, what's left for Arc 12 (MIR-level optimization)
  - **Methodology**: hardware specs, OS, LLVM version, run count, outlier policy

## Phase 5 -- README performance update

- [ ] If cumulative speedup >= 1.5x: update `README.md` performance section with new numbers
- [ ] If Go gap closed to <= 3x: call it out as a milestone
- [ ] If Python gap widened to >= 10x: update that ratio too
- [ ] If improvement < 1.5x: don't update README; document in SESSION_REPORT why the hypothesis was partially wrong

## Phase 6 -- LOW sweep + closeout

- [ ] Grep for `TODO(v4.85)` or unfinished items
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`
- [ ] SESSION_REPORT includes: "Arc 11 hypothesis test: did 2-3x materialize?"

---

## Exit criteria (7 items)

| # | Check | Evidence |
|---|---|---|
| 1 | All 5 benchmarks re-run with current IR | `v4.85.0-final.json` |
| 2 | Delta tables computed (per-release + cumulative) | tables in JSON + MD |
| 3 | Cross-language comparison refreshed (fresh Python/Go/Rust numbers) | `cross_language` key |
| 4 | `ARC11_RESULTS.md` published with all 5 tables | file exists |
| 5 | Numbers are reproducible (re-run matches within 5% tolerance) | verification run |
| 6 | README updated if >= 1.5x improvement | diff or SESSION_REPORT explanation |
| 7 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Change IR emission** -- zero modifications to `emit_llvm_text.py`
- **MIR-level optimization** -- that's Arc 12
- **New language features** -- measurement only
- **Self-hosted emitter mirror** -- the Python bootstrap numbers are the target
- **Profile-guided optimization** -- v5.x

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Numbers don't show 2-3x improvement | medium | medium | Document honestly; partial improvement is still progress; identify what Arc 12 should target |
| Benchmark variance between v4.82.0 and v4.85.0 sessions | medium | low | Re-run baseline from v4.82.0 programs on same session hardware for apples-to-apples |
| Cross-language programs got faster (Go/Rust updated compilers) | low | low | Document compiler versions; the ratio is what matters, not absolute numbers |
| One benchmark regressed (attributes caused worse code) | low | medium | Investigate in SESSION_REPORT; may indicate an attribute was applied incorrectly |
| README update overpromises | low | medium | Use conservative language; cite specific benchmark, not "up to Nx faster" |

---

## After v4.85.0

v4.86.0 is the **Arc 11 panel release**. 7 reviewers grade the entire optimizer phase 1 arc: benchmark methodology, IR quality improvements, measured results, and the ARC11_RESULTS.md publication.
