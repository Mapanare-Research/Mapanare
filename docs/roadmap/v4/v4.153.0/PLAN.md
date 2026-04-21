# Mapanare v4.153.0 — Pre-perf-panel refresh

> **Measurement-only release.** Zero code changes. Refresh every
> quantitative evidence artifact that v4.154.0's 7 reviewers will
> grade: 6th flaky audit (5 sequential pytest runs × 5 = 30 cumulative
> since v4.141.0), full benchmark re-run with v4.153.0 VERSION
> propagated, full sanitizer re-sweep, MEASUREMENTS.md FINAL (the
> perf-arc version), arc-wide trend graph at
> `benchmarks/TREND_v4.144_v4.153.md`, and a final `PERF_EXPERIMENTS.md`
> review. Mirrors v4.135.0 (pre-v4.136.0 panel) and v4.142.0 (pre-v4.143.0
> panel) — same discipline, perf-arc surface.

**Status:** PLANNED
**Breaking:** No (pre-panel release — no code changes except VERSION)
**Prerequisite:** v4.152.0 shipped (E8 recorded)
**Estimated work:** 1 day (wall-clock dominated by sweeps and bench re-runs)
**Theme:** Every number on the perf-panel desk is fresh and reproducible.

---

## Why v4.153.0 exists

The v4.144.0 → v4.152.0 arc executed 8 experiments across the codegen,
runtime, and MIR-optimizer surfaces. The v4.154.0 panel grades that
arc end-to-end with a perf focus. Between the last experiment and the
panel there is exactly one mechanical step left: refresh every number
the panel reads so nothing cites a stale baseline.

This is the same discipline v4.135.0 applied before the v4.136.0
v5-gate panel and v4.142.0 applied before the v4.143.0 post-rc1 panel.
Both times the pre-panel refresh caught a small number of drifted
artifacts (stale VERSION strings embedded in `libmapanare_rt.a`, golden
counts rounded in README, one or two SESSION_REPORT line-number
references that had shifted). v4.153.0 does the same pass for the perf
arc: audit every experiment's claims, re-run the benchmark corpus on
a clean v4.153.0 build, and emit the canonical MEASUREMENTS.md the
reviewers will cite.

The cumulative flaky evidence at the end of this release is 30
sequential non-bootstrap pytest runs with 0 flaky findings (5 audits
× 5 runs = 25 at v4.141.0, + 5 here = 30). That number is the
Anaconda-score floor for the panel.

## What v4.153.0 produces

- [ ] `docs/roadmap/v4/v4.153.0/FLAKY_AUDIT.md` — 6th 5× sequential pytest audit (cumulative 30 runs since v4.141.0)
- [ ] `docs/roadmap/v4/v4.153.0/VALGRIND_REPORT.md` — fresh sweep on post-v4.152.0 mnc-stage1
- [ ] `docs/roadmap/v4/v4.153.0/ASAN_REPORT.md` — fresh sweep
- [ ] `benchmarks/cross_language/v4.153.0-results.json` + 20 runs per cell
- [ ] `benchmarks/async/v4.153.0-async.json` + 20 runs per cell
- [ ] `benchmarks/FINAL_REPORT_v4.153.md` — supersedes `FINAL_REPORT_v4.144.md` with full-arc numbers
- [ ] `benchmarks/TREND_v4.144_v4.153.md` — arc-wide trend graph data (table + chart-ready CSV)
- [ ] `docs/roadmap/v4/v4.153.0/FIXEDPOINT_STATUS.md` — post-E8 fixed-point (line count, md5, DIFF_THRESHOLD compliance)
- [ ] `docs/roadmap/v4/v4.153.0/DOCKET_LEDGER.md` — every docket opened/closed since v4.144.0
- [ ] `docs/roadmap/v4/v4.153.0/MEASUREMENTS.md` — THE perf-panel evidence document
- [ ] `docs/roadmap/v4/PERF_EXPERIMENTS.md` — end-of-arc review (every E-row verified, dead ends audited for honesty)
- [ ] `.reviews/v4.154.0/PRE_PANEL_AUDIT.md` — fact-check every v4.144.0–v4.152.0 SESSION_REPORT claim

## Phase 1 — Sweeps (mechanical, ~3–4 hours wall time)

```bash
# 1. Bump VERSION + rebuild so artifacts embed 4.153.0
echo "4.153.0" > VERSION
make build-rt
python3 scripts/build_stage1.py
bash scripts/build_asan.sh               # mnc-stage1-asan

# 2. 6th flaky audit (5× sequential)
mkdir -p docs/roadmap/v4/v4.153.0/flaky-runs
for i in 1 2 3 4 5; do
  SECONDS=0
  python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no \
    2>&1 | tee docs/roadmap/v4/v4.153.0/flaky-runs/run$i.log
  echo "elapsed: ${SECONDS}s"
  grep ^FAILED docs/roadmap/v4/v4.153.0/flaky-runs/run$i.log \
    | sort > docs/roadmap/v4/v4.153.0/flaky-runs/run$i.failed.sorted
done
# Pairwise diffs — should all be empty
for i in 1 2 3 4; do
  j=$((i+1))
  echo "=== Run$i vs Run$j ==="
  diff docs/roadmap/v4/v4.153.0/flaky-runs/run$i.failed.sorted \
       docs/roadmap/v4/v4.153.0/flaky-runs/run$j.failed.sorted
done

# 3. Valgrind sweep
VG_OUTDIR=/tmp/v4_153_valgrind bash scripts/valgrind_all_goldens.sh
cp /tmp/v4_153_valgrind/valgrind-summary.tsv docs/roadmap/v4/v4.153.0/

# 4. ASan sweep
bash scripts/run_asan_goldens.sh
cp /tmp/v4_153_asan/asan-summary.tsv docs/roadmap/v4/v4.153.0/ 2>/dev/null || \
  cp /tmp/v4_105_asan/asan-summary.tsv docs/roadmap/v4/v4.153.0/

# 5. Fixed-point (must still hold post-E8)
bash scripts/verify_fixed_point.sh --keep 2>&1 \
  | tee docs/roadmap/v4/v4.153.0/fixedpoint.log
md5sum /tmp/stage2.ll /tmp/stage3.ll

# 6. Native goldens snapshot
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 \
  2>&1 | tee docs/roadmap/v4/v4.153.0/goldens.log

# 7. Full benchmark re-run — 20 runs per cell, clean build
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.153.0-results.json
python3 benchmarks/async/run_async_benchmarks.py --runs 20 \
  --output benchmarks/async/v4.153.0-async.json

# 8. Human-readable report
python3 benchmarks/cross_language/format_report.py \
  benchmarks/cross_language/v4.153.0-results.json \
  > benchmarks/FINAL_REPORT_v4.153.md
```

Expected wall time: pytest 5× ≈ 40 min; valgrind ≈ 15 min; ASan ≈ 10
min; benchmarks 20× across 6 cross-language + 5 async ≈ 45 min;
fixed-point ≈ 5 min. **Total ~2h 15min.**

## Phase 2 — Reports written from sweep data

Each report has a template at `docs/roadmap/v4/v4.135.0/` or
`docs/roadmap/v4/v4.142.0/`. Copy the shape, swap the numbers.

### FLAKY_AUDIT.md

- Cumulative summary: 5 prior audits (v4.117.0, v4.125.0, v4.130.0,
  v4.135.0, v4.141.0) + this one = 6 audits, 30 runs total
- Per-run failure count (should match v4.152.0 baseline — expect 0)
- Pairwise diff output (expect empty across all 4 pairs)
- Conclusion: "30 cumulative sequential runs since v4.141.0, zero
  flaky findings. Anaconda score floor confirmed."

### VALGRIND_REPORT.md

- Class distribution (CLEAN / WARNINGS_ONLY / ERRORS)
- Delta vs v4.142.0 (the last pre-panel audit)
- Expected: ERRORS still 0; WARNINGS_ONLY holds (leaks consistent);
  any new CLEAN count from E-release improvements

### ASAN_REPORT.md

- CLEAN / ASAN_ERROR / CRASH_NO_ASAN breakdown
- Delta vs v4.142.0
- Expected: ASAN_ERROR still 0

### FIXEDPOINT_STATUS.md

- Post-E8 line count + md5
- `DIFF_THRESHOLD=100` compliance
- Known version-metadata placeholder diff (Dr.1 residual) still the
  only expected delta; any new delta = investigate before panel

### DOCKET_LEDGER.md

- One row per docket opened or closed in v4.144.0 → v4.152.0
- Columns: docket ID, opened release, closed release (or OPEN),
  severity, evidence link
- Summary counts at top (total, closed, open by severity)

### MEASUREMENTS.md (THE perf-panel evidence)

Follow `docs/roadmap/v4/v4.142.0/MEASUREMENTS.md` (the v4.143.0
pre-panel) as template. 10 sections, each ending with a one-line
"How to reproduce:" command:

1. **Test count** — 30-run audit summary
2. **Golden count** — 54/66 through mnc-stage1; 65/66 through Python bootstrap
3. **Self-hosted compiler** — .mn line count, module count, mnc-stage1 binary size
4. **Cross-language benchmark summary** — geomeans vs C/Rust/Go/Python; per-workload leaderboard with v4.144.0 → v4.153.0 delta column
5. **Async benchmark summary** — geomean vs Go/asyncio; per-workload delta column
6. **E1–E8 outcomes** — one line per experiment (win / dead end / partial, delta, artifacts link)
7. **Fixed-point status** (from FIXEDPOINT_STATUS.md)
8. **Sanitizer totals** — Valgrind ERRORS, ASan CLEAN/ERROR breakdown
9. **Carry-forward state** — open dockets (severity ranked), closed this arc
10. **Panel score history** — v4.99.0 through v4.143.0 + forecast v4.154.0

Reproducibility appendix at the end: one command per metric.

### TREND_v4.144_v4.153.md (arc-wide chart data)

New file; no prior template. Structure:

```markdown
# Benchmark Trend v4.144.0 → v4.153.0

## Cross-language geomean (ms, median)
| Release | Mapanare | Rust | Go | C gcc | Python |
|---|---:|---:|---:|---:|---:|
| v4.144.0 | 5.84 | 4.86 | ... | 1.20 | 249 |
| v4.145.0 | ... | ... | ... | ... | ... |
| ...
| v4.153.0 | ... | ... | ... | ... | ... |

## Cross-language ratio vs Rust
| Release | Mapanare / Rust |
|---|---:|
| v4.144.0 | 1.20× |
| v4.145.0 | ... |

## Async geomean (ms, median)
...

## Per-workload breakdown (raw JSON link)
- `benchmarks/cross_language/v4.144.0-results.json`
- ...

## Chart-ready CSV
(embed inline — one row per release, one column per bench)
```

This is the canonical trend data the marketing-payload chart (arc-
opening blog post figure 1) draws from. Keep it honest — include
dead-end releases (those where a lever was tried and rolled back).

## Phase 3 — `PERF_EXPERIMENTS.md` end-of-arc review

Walk every row in `docs/roadmap/v4/PERF_EXPERIMENTS.md`:

- E1 (enum_match), E2 (fib), E3 (noalias), E4 (string_concat), E5 (ABI.1)
- E6a/b/c (async levers), E7a/b/c (allocator levers), E8a/b/c/d (dormant passes)

For each row:
- Verify the cited file:line reference still points at the claimed change
- Verify the delta number against the release's RESULTS.md
- Confirm the "win / dead end / partial" label is honest

Record discrepancies at the bottom of `PERF_EXPERIMENTS.md` under a
"v4.153.0 end-of-arc audit" heading. Do not retroactively edit the
table rows; overlay the audit.

## Phase 4 — Pre-panel audit

Walk every SESSION_REPORT from v4.144.0 through v4.152.0. For each
load-bearing claim (file path, function name, line count, benchmark
number, golden count, sanitizer count), verify against current HEAD:

```bash
# For claims naming a file
ls <claimed path>

# For claims naming a symbol
grep -n "<symbol>" <claimed file>

# For claims naming a line count
wc -l <claimed file>

# For claims naming a benchmark number
grep "<metric>" benchmarks/cross_language/v4.*-results.json
```

Write `.reviews/v4.154.0/PRE_PANEL_AUDIT.md`. Mirror
`.reviews/v4.143.0/PRE_PANEL_AUDIT.md` format:

```
## v4.XYZ.0 — [SESSION_REPORT.md path]

### Verified (N claims)
- [claim text] — verified: [evidence]

### Cosmetic drift (N claims)
- [claim text] — drift: [line numbers off by N, etc.]

### Material discrepancy (N claims)
- [claim text] — DISCREPANCY: [what's wrong]
  - Correction: [what panel should know]
```

Target: **0 material discrepancies.** Cosmetic drift is acceptable
and expected. SESSION_REPORTs are NOT retroactively edited — the
audit is an overlay.

## Phase 5 — README + roadmap refresh

Update `README.md`:
- Benchmark claims in the blurb: swap v4.144.0 numbers for v4.153.0
- `Benchmarks` section: replace `FINAL_REPORT_v4.144.md` with `FINAL_REPORT_v4.153.md`
- Test count badge: bump if pytest count has moved

Update `docs/roadmap/ROADMAP.md` with `## Where We Are (v4.153.0 …)`
prepended.

Update `CLAUDE.md` `Current Version & Roadmap` section with v4.153.0
entry at the top of the list.

## Phase 6 — Closeout

- [ ] `SESSION_REPORT.md` with every artifact referenced
- [ ] `CHANGELOG.md [4.153.0]` entry — short, no code changes, lists artifacts
- [ ] VERSION propagated through `libmapanare_rt.a` + `mnc-stage1` (required; v4.141.0 precedent)
- [ ] All artifacts committed under `docs/roadmap/v4/v4.153.0/`
- [ ] Tag `v4.153.0`

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | All sweeps (flaky, valgrind, ASan, bench) run successfully | yes |
| 2 | Pairwise flaky diffs empty across all 4 pairs | 0 flaky |
| 3 | Cumulative 30 sequential pytest runs, 0 flaky | yes |
| 4 | MEASUREMENTS.md includes every metric the panel needs | yes |
| 5 | `PERF_EXPERIMENTS.md` end-of-arc audit completed | yes |
| 6 | Pre-panel audit committed — 0 material discrepancies | yes |
| 7 | FINAL_REPORT_v4.153.md supersedes v4.144.0 report | yes |
| 8 | TREND_v4.144_v4.153.md written with chart-ready data | yes |
| 9 | `libmapanare_rt.a` VERSION string embeds `4.153.0` | yes |
| 10 | `mnc-stage1` VERSION string embeds `4.153.0` | yes |
| 11 | VERSION bumped to 4.153.0 | yes |
| 12 | README + CLAUDE.md + ROADMAP.md updated | yes |
| 13 | Non-bootstrap pytest: baseline hold (≥ 5,160 passed / 0 failed) | yes |
| 14 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 15 | Goldens 54/66 | yes |
| 16 | Valgrind 0 ERRORS, ASan 0 ASAN_ERROR | yes |
| 17 | Fixed-point within `DIFF_THRESHOLD=100` | yes |
| 18 | All 8 CI gates green | yes |
| 19 | Tag `v4.153.0` pushed to origin | yes |

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| 6th flaky audit reveals actual flakiness | very low | high | Five prior audits = 25 runs, zero flaky; if found, document family, escalate to v4.153.1 before panel |
| Benchmark regression vs v4.152.0 (experiment-induced) | low | medium | E-series 5 % rule should have caught this already; if new regression surfaces, bisect and roll back before panel |
| Pre-panel audit finds material discrepancy in an E-release SESSION_REPORT | low | high | Fix the document + the MEASUREMENTS.md; do NOT retroactively edit the SESSION_REPORT (that's historical); flag in audit overlay |
| MEASUREMENTS.md balloons into a rewrite of every E-release SESSION_REPORT | medium | low | Budget 1 day total, not 3; link to SESSION_REPORTs for depth, keep sections concise |
| A fixed-point drift surfaces post-E8 (stage2 != stage3 beyond DIFF_THRESHOLD) | low | high | `verify_fixed_point.sh --keep` is a mandatory step; if diff > threshold, roll back the E8 pass that caused it, re-run sweeps |

---

## What this release does NOT do

- Change any code (no `mapanare/`, `runtime/`, `mapanare/self/` edits)
- Fix any newly-discovered bugs (if Phase 4 finds a material discrepancy,
  document + defer unless it's panel-blocking)
- Panel anything (that's v4.154.0)
- Re-run any of E1–E8 (those are sealed; their RESULTS.md stands as-is)
- Touch WASM, mobile, or GPU benchmarks (the arc corpus is the 6 cross-
  language + 5 async; adding benchmarks mid-arc would corrupt the trend)

---

## After v4.153.0

**v4.154.0 — THE PERF PANEL.** Full 7-reviewer panel on v4.144.0 →
v4.153.0. Perf-focused prompt. Mechanical rule applies:

- Aggregate ≥ 9.5 AND 0 NEEDS WORK → clean `v5.1.0` tag (the perf
  version of the Option-A standard)
- Aggregate ≥ 9.0 AND 0 NEEDS WORK → `v5.1.0` under standard mechanical
  rule (the same gate v5.0.0 fires)
- Aggregate < 9.0 → `v5.1.0-rc` territory or recovery cycle, per the
  v4.154.0 PLAN.md

The v4.153.0 pre-panel evidence pack determines which outcome becomes
reachable. The better the audit, the tighter the panel verdict lands
on the honest number.
