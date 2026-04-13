# Mapanare v4.90.0 — Total Optimizer Benchmark: v4.82.0 to v4.90.0

> **Arc 12 release 4.** Measurement release. No new optimization
> passes. Re-runs the full benchmark suite and computes the cumulative
> delta across both arcs of optimizer work: Arc 11 (LLVM IR quality,
> v4.82.0-v4.85.0) and Arc 12 (MIR-level optimizations,
> v4.87.0-v4.89.0).
>
> This is the release that answers the question: "How much faster is
> Mapanare now?" The answer is a single table showing the journey from
> unoptimized baseline to fully optimized, broken down by LLVM-level
> and MIR-level contributions, with cross-language context (Go, Rust,
> Python).

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.89.0
**Delta review:** No
**Full panel:** No (v4.91.0)
**Estimated work:** 1 sprint
**Theme:** Cumulative optimizer benchmark. Two arcs of work, one table.

---

## Scope

Arc 11 (v4.82.0-v4.86.0) improved LLVM IR quality: nsw/nuw flags, TBAA metadata, function attributes, readonly/nounwind annotations. The v4.85.0 delta showed the LLVM-level contribution.

Arc 12 (v4.87.0-v4.89.0) added MIR-level transformations: function inlining (v4.87.0), LICM + strength reduction (v4.88.0), escape analysis with heap-to-stack promotion (v4.89.0). Each release recorded its own delta.

v4.90.0 produces the final composite picture:

1. **Cumulative delta:** v4.82.0 (pre-optimization baseline) vs. v4.90.0 (all optimizations enabled). This is the headline number.
2. **Breakdown:** LLVM-level contribution (v4.82.0 -> v4.85.0) vs. MIR-level contribution (v4.85.0 -> v4.90.0). Shows whether the two arcs were complementary or redundant.
3. **Per-pass attribution:** individual contribution of each MIR pass (inlining alone, LICM alone, escape analysis alone). Measured by disabling one pass at a time.
4. **Cross-language refresh:** re-run Go, Rust, and Python implementations of the same 5 benchmarks. Compare Mapanare v4.90.0 against the same versions used in v4.82.0 (pin versions for reproducibility).
5. **Publication:** `benchmarks/optimizer/TOTAL_RESULTS.md` with all tables, charts described in text, and methodology notes.

## Phase 1 — Re-run full benchmark suite

- [ ] Run the 5-program suite (fib(35), concurrency(100K), stream_pipeline(1M), matrix_mul(512x512), agent_pipeline(10K)) at each optimization configuration:
  - O0 (no optimization, same as v4.82.0 baseline)
  - O2 with Arc 11 only (LLVM IR quality, no MIR passes beyond what existed pre-v4.87.0)
  - O2 with Arc 11 + inlining only (v4.87.0)
  - O2 with Arc 11 + inlining + LICM + strength reduction (v4.88.0)
  - O2 with Arc 11 + all MIR passes (v4.89.0 = v4.90.0 full)
- [ ] Each configuration runs 5 times; report median with stddev
- [ ] Record wall time (ms), peak RSS (KB), instruction count (via `perf stat` if available)
- [ ] Save raw results to `benchmarks/optimizer/v4.90.0-raw.json`

## Phase 2 — Compute cumulative delta

- [ ] Load v4.82.0 baseline from `benchmarks/optimizer/v4.82.0-baseline.json`
- [ ] Compute per-program speedup: `baseline_time / optimized_time`
- [ ] Compute geometric mean across all 5 programs
- [ ] Break down:
  - LLVM-level contribution: speedup from O0 to Arc-11-only
  - MIR-level contribution: speedup from Arc-11-only to full
  - Total: speedup from O0 to full
- [ ] Per-pass attribution (disable one at a time, measure delta):
  - Inlining contribution
  - LICM contribution
  - Strength reduction contribution
  - Escape analysis contribution
- [ ] Save computed deltas to `benchmarks/optimizer/v4.90.0-delta.json`

## Phase 3 — Cross-language refresh

- [ ] Run Go benchmarks (same source in `benchmarks/cross_language/`): `go build -o /tmp/bench_go && /tmp/bench_go`
- [ ] Run Rust benchmarks: `cargo build --release && ./target/release/bench`
- [ ] Run Python benchmarks: `python benchmarks/cross_language/run_benchmarks.py`
- [ ] Pin versions: Go (same as v4.82.0), Rust (same as v4.82.0), Python (same as v4.82.0)
- [ ] Compare Mapanare v4.90.0 optimized vs. each language:
  - Ratio: `mapanare_time / go_time`, `mapanare_time / rust_time`, `mapanare_time / python_time`
  - Flag any benchmark where Mapanare is within 2x of Go (this is the headline-worthy threshold)
- [ ] Save to `benchmarks/optimizer/v4.90.0-crosslang.json`

## Phase 4 — Publish TOTAL_RESULTS.md

- [ ] Create `benchmarks/optimizer/TOTAL_RESULTS.md` with the following sections:
  - **Executive summary:** one-paragraph headline with geometric mean speedup and any within-2x-of-Go results
  - **Methodology:** hardware, OS, compiler versions, measurement protocol (5 runs, median, stddev)
  - **Table 1: Cumulative optimization delta** — rows: programs, columns: O0, Arc 11 only, +inlining, +LICM, +escape, full; cells: time_ms and speedup
  - **Table 2: Per-pass attribution** — rows: programs, columns: inlining, LICM, strength reduction, escape analysis; cells: marginal speedup when that pass is disabled
  - **Table 3: Cross-language comparison** — rows: programs, columns: Mapanare O0, Mapanare optimized, Go, Rust, Python; cells: time_ms and ratio-to-Go
  - **Table 4: Memory impact** — rows: programs, columns: peak RSS at O0, peak RSS optimized, delta; escape analysis should show RSS reduction
  - **Analysis:** which passes contributed most, which benchmarks benefited most, where Mapanare still lags
  - **Next steps:** what further optimizations could close remaining gaps (loop unrolling, vectorization, PGO)
- [ ] If any benchmark is within 2x of Go, add a note to the project README under "Performance"

## Phase 5 — Benchmark reproducibility

- [ ] Create `benchmarks/optimizer/reproduce.sh`: a script that re-runs the entire measurement from scratch (builds Mapanare at each configuration, runs all benchmarks, generates TOTAL_RESULTS.md)
- [ ] Document hardware requirements and expected runtime
- [ ] Run `reproduce.sh` once to verify it produces consistent results within 5% of the manual run

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.90.0]` entry -- "Total optimizer benchmark: v4.82.0-v4.90.0 cumulative delta across 2 arcs (LLVM IR quality + MIR inlining/LICM/escape analysis)"
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (7 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Full benchmark suite re-run at all 5 configurations | `v4.90.0-raw.json` |
| 2 | Cumulative delta computed with LLVM vs. MIR breakdown | `v4.90.0-delta.json` |
| 3 | Per-pass attribution measured (disable-one-at-a-time) | `v4.90.0-delta.json` |
| 4 | Cross-language comparison refreshed (Go, Rust, Python) | `v4.90.0-crosslang.json` |
| 5 | `TOTAL_RESULTS.md` published with 4 tables | file exists |
| 6 | `reproduce.sh` script works end-to-end | manual verification |
| 7 | `make lint` + `make test` pass | CI log |

---

## What this release does NOT do

- **New optimization passes.** v4.90.0 is measurement only.
- **Runtime changes.** No modifications to the C runtime, allocator, or scheduler.
- **Optimizer tuning.** Heuristic thresholds (inline budget, LICM purity set, escape size cap) are not changed. Tuning based on benchmark data is a future release.
- **Self-hosted compiler optimization.** The self-hosted `mir_opt.mn` is not updated.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Benchmark results are noisy (variance > 10%) | medium | medium | 5 runs per configuration, median, report stddev. If stddev > 10%, increase to 10 runs. |
| Cross-language versions differ from v4.82.0 baseline | low | medium | Pin exact versions in `reproduce.sh`. Document in TOTAL_RESULTS.md. |
| One pass shows negative contribution (regression) | low | high | Investigate: the pass may conflict with a subsequent LLVM optimization. Document if confirmed. |
| Results do not meet the 1.5-2x MIR-level target | medium | medium | Document honestly. The target was an estimate; actual numbers are what they are. |
| Hardware differences between v4.82.0 and v4.90.0 runs | low | medium | Run all configurations on the same hardware in the same session. Baseline re-run, not historical comparison. |

---

## After v4.90.0

v4.91.0 is the Arc 12 panel release. 7 reviewers grade the optimizer work from v4.87.0-v4.90.0. Special focus on correctness (Rattler, Viper), ABI impact of inlining (Cobra), benchmark validity (Mamba), and escape analysis soundness (Viper).
