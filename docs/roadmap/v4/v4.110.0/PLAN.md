# Mapanare v4.110.0 — Full Benchmark Refresh with All Fixes

> **Phase C release 4 (final).** Phase A (v4.100.0-v4.103.0) fixed
> critical bugs: tagged-pointer UB, list indexing, async linking, enum
> dispatch. Phase B (v4.104.0-v4.106.0) rebuilt, verified, paneled.
> Phase C added Go + C benchmarks (v4.107.0), fixed string_concat
> (v4.108.0), and investigated optimizer ROI (v4.109.0). Now we
> measure everything one final time. Comprehensive comparison with
> all fixes applied. The definitive "where does Mapanare stand" document.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.109.0
**Delta review:** No
**Full panel:** No (numbers are the panel)
**Estimated work:** 1 sprint
**Theme:** Final measurement. All fixes applied. Full cross-language comparison. Honest numbers.

---

## Scope

Three sets of numbers matter:

1. **Current absolute performance** -- where Mapanare stands right now against C, Rust, Go, and Python across 6 workloads. This is the number that goes in the README.

2. **Delta from v4.99.0 pre-panel baseline** -- what did Phase A bug fixes + Phase C string_concat fix actually change? This answers "was the post-panel work worth it?"

3. **Delta from v4.82.0 original optimizer baseline** -- cumulative progress from the start of the optimization era. This answers "how far has Mapanare come?"

The output is `benchmarks/PHASE_C_RESULTS.md` -- the single comprehensive document that replaces `FINAL_REPORT.md` from v4.98.0 as the canonical performance reference. The README is updated with current headline numbers.

---

## Phase 1 -- Re-run ALL benchmarks

- [ ] **Optimizer suite** (6 programs): fib_recursive, quicksort, matmul_naive, string_concat, agent_fanout, plus any new programs from v4.98.0
- [ ] **System suite**: struct_alloc, enum_match, closure_capture, prime_sieve, compile_self
- [ ] **Cross-language** (all 6 workloads): Mapanare (mnc-stage1 + opt -O2), Python 3.12, Go, Rust, C (gcc -O2), C (clang -O2)
- [ ] All benchmarks: 10 runs each, drop highest and lowest, median of middle 8
- [ ] Same hardware, same environment as v4.107.0 (for cross-language consistency)
- [ ] Save raw results to `benchmarks/v4.110.0-final.json`
- [ ] Verify correctness: all programs produce expected checksums

## Phase 2 -- Compute delta from v4.99.0 pre-panel baseline

- [ ] Load `benchmarks/v4.98.0-final.json` (the pre-panel measurement, closest to v4.99.0)
- [ ] For each benchmark measured in both: compute absolute delta (ms) and percentage change
- [ ] Focus on the key changes:
  - **string_concat**: was 95.2ms, should now be < 43ms after v4.108.0 StringBuilder
  - **fib_recursive**: was 19.6ms, may have changed due to Phase A bug fixes
  - **struct_alloc**: was 0.6ms, should be stable or improved (tagged-pointer UB fix)
  - **enum_match**: was 2.3ms, may have improved (enum dispatch fix in Phase A)
- [ ] Produce Table 1: v4.99.0 vs v4.110.0 delta

## Phase 3 -- Compute delta from v4.82.0 original baseline

- [ ] Load `benchmarks/optimizer/v4.82.0-baseline.json`
- [ ] For the 5 optimizer benchmarks (fib, quicksort, matmul, string_concat, agent_fanout): compute cumulative delta from v4.82.0 through v4.110.0
- [ ] This shows the full optimization era progress: Arcs 11-14 + Phase A-C
- [ ] Note: the v4.82.0 baseline did not include struct_alloc, enum_match, etc. Only the 5 optimizer programs are comparable.
- [ ] Produce Table 2: v4.82.0 vs v4.110.0 cumulative delta
- [ ] Compute geometric mean speedup across all 5

## Phase 4 -- Publish PHASE_C_RESULTS.md

- [ ] Write `benchmarks/PHASE_C_RESULTS.md`:
  - **Executive summary**: 3-4 sentences on where Mapanare stands. Include: vs C ratio, vs Rust ratio, vs Go ratio, vs Python ratio. Note the string_concat fix.
  - **Methodology**: hardware, OS, LLVM version, all compiler versions, run count, median method
  - **Table 1: Cross-language comparison (wall-clock ms)** -- 6 columns (C gcc, C clang, Rust, Go, Mapanare, Python), all benchmarks. This is the headline table.
  - **Table 2: Speedup ratios** -- Mapanare vs each language, per benchmark. Geometric means.
  - **Table 3: v4.99.0 -> v4.110.0 delta** -- what Phase A bugs + Phase C string fix changed
  - **Table 4: v4.82.0 -> v4.110.0 cumulative delta** -- full optimization era progress
  - **Table 5: Peak memory comparison** -- 6 columns, all benchmarks
  - **Table 6: Binary size comparison** -- C, Rust, Go, Mapanare (excludes Python)
  - **Table 7: Lines of code** -- all 6 languages (expressiveness comparison)
  - **Analysis by category:**
    - Compute-bound: how close to C/Rust?
    - Allocation-heavy: arena advantage on struct_alloc, string_concat after fix
    - System workloads: enum dispatch, closure capture
  - **String concat before/after**: dedicated subsection showing the 95.2ms -> ???ms improvement
  - **Optimizer ROI summary**: reference v4.109.0 analysis, one paragraph
  - **Known limitations**: WSL overhead, missing async benchmarks, no GPU
  - **Reproducibility**: exact commands
- [ ] Cross-reference against `benchmarks/cross_language/FULL_COMPARISON.md` from v4.107.0 to ensure consistency

## Phase 5 -- Update README.md performance section

- [ ] Read current `README.md` -- find the performance section
- [ ] Update with current headline numbers from Phase C:
  - "Mapanare compiles to native code via LLVM. On representative benchmarks: X-Yx faster than Python, within Xx of Go, within Yx of Rust, within Zx of C."
  - "Arena allocator gives structural advantage on allocation-heavy workloads (struct_alloc beats Rust)."
  - "String handling competitive with Python after auto-StringBuilder optimization."
- [ ] Keep to 3-5 sentences. Link to `benchmarks/PHASE_C_RESULTS.md` for details.
- [ ] Remove or update any stale performance claims from previous versions

## Phase 6 -- LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.110.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | All benchmarks re-run with v4.110.0 compiler (all fixes applied) | `v4.110.0-final.json` exists |
| 2 | v4.99.0 delta computed (Table 3) | table in PHASE_C_RESULTS.md |
| 3 | v4.82.0 delta computed (Table 4) | table in PHASE_C_RESULTS.md |
| 4 | Cross-language table current (C, Rust, Go, Mapanare, Python) | Table 1 in PHASE_C_RESULTS.md |
| 5 | string_concat improvement documented (before/after) | dedicated subsection |
| 6 | `PHASE_C_RESULTS.md` published | file exists, all tables present |
| 7 | `README.md` performance section updated with current numbers | diff of README.md |
| 8 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Change any code** -- zero modifications to compiler, runtime, or benchmark programs. Pure measurement and documentation.
- **Re-run the v4.106.0 panel** -- Phase C has no panel. The numbers are the verdict.
- **Add new benchmarks** -- uses the same programs established in v4.98.0 and v4.107.0. Consistency matters more than coverage at this point.
- **Compare at O0/O1** -- only O2. The optimizer ROI analysis in v4.109.0 covered multi-level comparison.
- **Make projections** -- reports current state, not future predictions. What v5.x might achieve is speculation.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| v4.108.0 StringBuilder didn't land or benchmark doesn't trigger it | low | high | Verify string_concat benchmark fires the optimization before measuring. If not, run with explicit StringBuilder and note the discrepancy. |
| Numbers differ significantly from v4.107.0 (same hardware, different day) | medium | medium | Run v4.107.0 C/Rust/Go baselines again alongside v4.110.0 Mapanare to control for system load. Same session = same conditions. |
| README performance claims are contradicted by specific benchmarks | medium | medium | Use ranges ("1.1-2.1x slower than Rust" not "faster than Rust"). Never cherry-pick the best number without acknowledging the worst. |
| v4.82.0 baseline data missing or incompatible with current benchmark format | low | medium | The JSON files exist in `benchmarks/optimizer/`. Load and verify structure before computing deltas. |
| Phase A bug fixes regressed non-string benchmarks | low | medium | If regressions exist, document them honestly. Bug fixes that sacrifice 5% performance for correctness are acceptable. |

---

## After v4.110.0

Phase C is complete. We now have:
- Honest numbers against C, Rust, Go, and Python across 6 workloads
- String pathology fixed (auto-StringBuilder)
- Optimizer ROI understood (and documented)
- Cross-language comparison published

v4.111.0 begins Phase D: self-hosted compiler maturity. The focus shifts from "how fast" to "how complete" -- closing the remaining gaps between the Python bootstrap and the self-hosted compiler.
