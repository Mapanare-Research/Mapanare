# Mapanare v4.135.0 — Pre-panel refresh

> **Measurement-only release.** Zero code changes. Refresh every
> quantitative evidence artifact that v4.136.0's 7 reviewers will
> grade: 5× flaky audit, valgrind sweep, ASan sweep, cross-language
> benchmarks, async benchmarks, fixed-point status, docket ledger,
> MEASUREMENTS.md. The v4.131.0 + v4.132.0 + v4.133.0 + v4.134.0
> closures compound here — this release is where the panel sees the
> aggregate delta.

**Status:** PLANNED
**Prerequisite:** v4.134.0
**Estimated work:** 1 sprint (mostly wall-clock for the sweeps)
**Theme:** Every number on the panel desk is fresh.

---

## Why v4.135.0 exists

The v4.120.0 panel aggregate was 8.21 with 1 NEEDS WORK. The v4.131.0
PLAN frames v4.136.0 as "v5 gate attempt 3" — mechanical rule: aggregate
≥ 9.0 AND 0 NEEDS WORK → Option A. Gap to close from v4.120.0: 0.79
points across 7 reviewers.

Closures since v4.120.0:
- v4.121.0 — 22 audit-subset pytest failures
- v4.122.0 — Qs.1 (List<Int> indexing)
- v4.123.0 — Dead code sweep (-1,963 lines)
- v4.124.0 — Rt.1 (unboxed enum payloads)
- v4.125.0 — Benchmark refresh, 5× flaky audit (0 flaky)
- v4.126.0 — Golden test push (27 → 39/65)
- v4.127.0 — Self-hosted cosmetic convergence (-4.4% divergence)
- v4.128.0 — Sh.8 + divergence M bucket fully closed
- v4.129.0 — SPEC + docs sync
- v4.130.0 — Pre-panel prep (flaky audit #3, valgrind, ASan, pre-panel audit)
- v4.131.0 — Sh.2 List fix (39 → 53/65, valgrind 31 → 14, ASan 23 → 9)
- v4.132.0 — Sh.2 String fix (targets: 53 → ≥58, 14 → ≤6, 9 → 0)
- v4.133.0 — An.1 reduction (38 → ≤15 pytest failures)
- v4.134.0 — Sh.11 investigation + fix (fixed-point blocker)

That's 14 closeout-arc releases. The panel needs every measurement to
reflect all 14. v4.130.0's MEASUREMENTS.md draft is stale relative to
v4.131.0+ numbers.

## What v4.135.0 produces

- [ ] `docs/roadmap/v4/v4.135.0/FLAKY_AUDIT.md` — 4th 5× sequential pytest audit
- [ ] `docs/roadmap/v4/v4.135.0/VALGRIND_REPORT.md` — fresh sweep on post-v4.134.0 mnc-stage1
- [ ] `docs/roadmap/v4/v4.135.0/ASAN_REPORT.md` — fresh sweep
- [ ] `benchmarks/cross_language/v4.135.0-results.json` + 10-run data per cell
- [ ] `benchmarks/async/v4.135.0-async.json` + async benchmark refresh
- [ ] `benchmarks/FINAL_REPORT_v4.136.md` — supersedes v4.130.0 report with v4.134.0 numbers
- [ ] `docs/roadmap/v4/v4.135.0/FIXEDPOINT_STATUS.md` — status post-Sh.11 work
- [ ] `docs/roadmap/v4/v4.135.0/DOCKET_LEDGER.md` — every open/closed docket with evidence
- [ ] `docs/roadmap/v4/v4.135.0/V5_READINESS.md` — feature matrix refresh (from v4.119.0 baseline)
- [ ] `docs/roadmap/v4/v4.135.0/MEASUREMENTS.md` — THE panel evidence document (supersedes v4.131.0 draft)
- [ ] `.reviews/v4.136.0/PRE_PANEL_AUDIT.md` — fact-check every claim in closeout-arc SESSION_REPORTs

## Phase 1 — Sweeps (mechanical, ~2-3 hours wall time)

```bash
# Rebuild to make sure artifacts are current
python3 scripts/concat_self.py
python3 scripts/build_stage1.py          # mnc-stage1
bash scripts/build_asan.sh                 # mnc-stage1-asan

# Flaky audit: 5× sequential pytest runs
mkdir -p docs/roadmap/v4/v4.135.0/flaky-runs
for i in 1 2 3 4 5; do
  python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no \
    2>&1 | tee docs/roadmap/v4/v4.135.0/flaky-runs/run$i.log
  grep ^FAILED docs/roadmap/v4/v4.135.0/flaky-runs/run$i.log \
    | sort > docs/roadmap/v4/v4.135.0/flaky-runs/run$i.failed.sorted
done
# Pairwise diff — should be empty (deterministic)
for i in 1 2 3 4; do
  j=$((i+1))
  diff docs/roadmap/v4/v4.135.0/flaky-runs/run$i.failed.sorted \
       docs/roadmap/v4/v4.135.0/flaky-runs/run$j.failed.sorted
done

# Valgrind sweep
VG_OUTDIR=/tmp/v4_135_valgrind bash scripts/valgrind_all_goldens.sh
cp /tmp/v4_135_valgrind/valgrind-summary.tsv docs/roadmap/v4/v4.135.0/

# ASan sweep
bash scripts/run_asan_goldens.sh
cp /tmp/v4_105_asan/asan-summary.tsv docs/roadmap/v4/v4.135.0/

# Benchmarks
python3 benchmarks/cross_language/run_benchmarks.py --runs 10 --output v4.135.0-results.json
python3 benchmarks/async/run_async_benchmarks.py --runs 10 --output v4.135.0-async.json
```

## Phase 2 — Reports written from sweep data

- [ ] `FLAKY_AUDIT.md` — pairwise diffs, deterministic vs flaky split, family classification (same format as v4.130.0 FLAKY_AUDIT.md)
- [ ] `VALGRIND_REPORT.md` — class distribution (CLEAN/WARNINGS_ONLY/ERRORS), top frames, delta vs v4.130.0
- [ ] `ASAN_REPORT.md` — class distribution (CLEAN/ASAN_ERROR/CRASH_NO_ASAN), finding kind breakdown, delta vs v4.130.0
- [ ] `FIXEDPOINT_STATUS.md` — post-v4.134.0 status; either (a) strict fixed-point achieved, (b) stage2 runs with diff N, or (c) documented Sh.11 reproducer + v5.x plan
- [ ] `DOCKET_LEDGER.md` — full table: every docket opened/closed from v4.99.0 panel onward, with release + evidence link
- [ ] `V5_READINESS.md` — refreshed feature matrix (from v4.119.0 baseline, updated with v4.120.0-v4.134.0 closures)

## Phase 3 — MEASUREMENTS.md (the canonical panel document)

Using the data from Phases 1-2, produce `MEASUREMENTS.md` with:

- Test count (pytest passed / failed / skipped / xfailed — 5 runs, median, variance)
- Golden count (through mnc-stage1; through Python bootstrap)
- Self-hosted LOC, module count, binary size
- Cross-language benchmark geomeans (Mapanare vs C/Rust/Go/Python; per-workload leaderboard)
- Async benchmark geomeans
- Fixed-point status (strict + proxy)
- Sanitizer totals
- Dead-code metrics (cumulative since v4.99.0)
- Carry-forward state (open dockets, closed since v4.120.0)
- Panel score history (v4.26.0 through v4.120.0, v4.136.0 TBD)
- Reproducibility table — one command per metric

Structure: follow v4.131.0/MEASUREMENTS.md (the draft) as template. Each
section ends with "How to reproduce:" command.

## Phase 4 — Pre-panel audit

Fact-check every load-bearing claim in:
- v4.121.0 SESSION_REPORT
- v4.122.0 SESSION_REPORT
- v4.123.0 SESSION_REPORT
- v4.124.0 SESSION_REPORT
- v4.125.0 SESSION_REPORT
- v4.126.0 SESSION_REPORT
- v4.127.0 SESSION_REPORT
- v4.128.0 SESSION_REPORT
- v4.129.0 SESSION_REPORT
- v4.130.0 SESSION_REPORT
- v4.131.0 SESSION_REPORT
- v4.132.0 SESSION_REPORT
- v4.133.0 SESSION_REPORT
- v4.134.0 SESSION_REPORT

Per v4.130.0 methodology: for each claim (file path, function name,
line count, benchmark number, golden pass count), verify against HEAD.
Record in `.reviews/v4.136.0/PRE_PANEL_AUDIT.md` as:
- Material discrepancies (must be corrected before panel)
- Cosmetic drifts (line number off by 1, file grew, etc.)
- Latent doc inconsistencies

Per v4.130.0 discipline: SESSION_REPORTs are NOT retroactively edited.
The audit is an overlay. Documented drifts inform the panel but don't
invalidate the evidence.

## Phase 5 — Closeout

- [ ] `SESSION_REPORT.md`
- [ ] `CHANGELOG.md [4.135.0]` entry
- [ ] Roadmap status updates
- [ ] Bump to 4.136.0

---

## Exit criteria

| # | Check | Target |
|---|---|---|
| 1 | All sweeps (flaky, valgrind, ASan, bench) run successfully | yes |
| 2 | Pairwise flaky diffs empty across all 4 pairs | 0 flaky |
| 3 | MEASUREMENTS.md includes every metric panel needs | yes |
| 4 | Pre-panel audit completed, drifts catalogued | yes, 0 material discrepancies |
| 5 | V5_READINESS.md updated with every closure since v4.119.0 | yes |
| 6 | FINAL_REPORT_v4.136.md publishes benchmark numbers | yes |
| 7 | `libmapanare_rt.a` byte-identical to v4.134.0 | yes (no code changes) |
| 8 | VERSION bumped to 4.136.0 | yes |

---

## What this release does NOT do

- Change any code (no `mapanare/`, `runtime/`, `mapanare/self/` edits)
- Fix any newly-discovered bugs (if Phase 4 finds a material discrepancy
  in a claim, document + defer unless it's panel-blocking)
- Panel anything (that's v4.136.0)

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Flaky audit reveals actual flakiness | very low | high | Three prior audits found zero; if found, document family + defer to v4.136.1 |
| Benchmark regression vs v4.125.0 | low | medium | Sh.2 arc should be neutral to benchmarks (compilation-side fix); if regression, investigate |
| Pre-panel audit finds material discrepancy | low | high | Fix the document, NOT the SESSION_REPORT (that's historical); note in audit |
| MEASUREMENTS.md turns into a rewrite of every prior SESSION_REPORT | medium | low | Budget: 1 sprint total, not 3; keep sections concise, link to SESSION_REPORTs for depth |

---

## After v4.135.0

- v4.136.0 — THE PANEL. Full 7-reviewer panel on v4.121.0-v4.135.0.
  Mechanical rule applies. Aggregate + grade decision:
  - ≥ 9.0 AND 0 NEEDS WORK → Option A (tag v5.0.0)
  - ≥ 8.5 AND < 9.0 AND 0 NEEDS WORK → Option C (tag v5.0.0-rc1)
  - Otherwise → Option B (continue v4.137.0+)

If Option A: the v4.x line closes at 136 releases.
If Option C: one more release (v4.137.0 or v5.0.0) closes remaining items.
If Option B: the recovery continues. Same cadence.
