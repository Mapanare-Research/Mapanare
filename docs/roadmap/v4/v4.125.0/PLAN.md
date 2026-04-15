# Mapanare v4.125.0 — Benchmark Refresh + Second Flaky Audit + Docs

> **Post-panel closeout release 5.** Final prep before the v4.130.0
> panel. All correctness fixes are in (v4.121.0: DWARF + trait,
> v4.122.0: Qs.1 list indexing). Dead code is removed (v4.123.0:
> optimizer.py + TBAA). Performance is improved (v4.124.0: unboxed
> enums). This release measures everything, confirms stability with a
> 5-run flaky audit, publishes updated benchmarks, and updates all
> documentation. No code changes. Pure measurement and documentation.

**Status:** DONE (shipped 2026-04-14)
**Breaking:** No
**Prerequisite:** v4.124.0
**Delta review:** No
**Full panel:** No (v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Measure. Document. Confirm. Prepare the evidence base for the v4.130.0 panel.

---

## Scope

This is a measurement release. The code is frozen after v4.124.0. The goal is to produce the definitive evidence base for the v4.130.0 panel:

1. **Full cross-language benchmark** — 6 programs x 5 languages (C, Rust, Go, Mapanare, Python). Record deltas from the v4.118.0 benchmark (Phase F). The enum_match improvement from v4.124.0 is the key delta.

2. **5-run flaky audit** — run `make test` 5 times consecutively. Every run must produce 0 failures. This is the ultimate stability proof.

3. **Benchmark report** — update `benchmarks/FINAL_REPORT_v4.130.md` (or equivalent) with current numbers. Include the v4.118.0 baseline for comparison.

4. **README performance section** — update with current benchmark numbers.

5. **V5_READINESS update** — mark Qs.1 as resolved (v4.122.0), enum boxing as improved (v4.124.0), dead code as removed (v4.123.0).

No compiler, runtime, or test changes. Every diff is in `benchmarks/`, `docs/`, or `README.md`.

## Phase 1 — Full cross-language benchmark

- [ ] Run all 6 benchmark programs across 5 languages:
  - `fibonacci` — recursive, CPU-bound
  - `string_concat` — string builder, memory allocation
  - `enum_match` — pattern matching, payload extraction
  - `list_ops` — list creation, indexing, iteration
  - `struct_access` — struct field reads and writes
  - `quicksort` — sorting, comparison, swap (if available)
- [ ] Record wall-clock time (median of 5 runs) for each
- [ ] Compute ratios vs C (gcc -O2) baseline
- [ ] Compare with v4.118.0 numbers — compute deltas
- [ ] Highlight the enum_match improvement from v4.124.0

## Phase 2 — 5-run flaky audit

- [ ] Run `make test` 5 times consecutively:
  ```bash
  for i in 1 2 3 4 5; do
      echo "=== Run $i ===" >> /tmp/flaky_audit_v4125.log
      make test 2>&1 | tail -5 >> /tmp/flaky_audit_v4125.log
  done
  ```
- [ ] Verify: 0 failures across all 5 runs
- [ ] If any failure appears, classify:
  - **Deterministic**: real bug — should have been caught in v4.121.0
  - **Flaky**: environment-dependent — document with root cause
- [ ] Record total test count per run (should be stable across all 5)

## Phase 3 — Benchmark report

- [ ] Write `benchmarks/FINAL_REPORT_v4.130.md` with:
  - Summary table: program x language x time x ratio
  - Delta table: v4.118.0 vs v4.125.0 for each benchmark
  - Analysis: where Mapanare improved, where it stayed the same
  - Spectrum position: C -> Rust -> Go -> Mapanare -> Python (updated)
  - enum_match callout: before (v4.118.0) and after (v4.125.0) optimization
- [ ] Reference `benchmarks/FINAL_REPORT_v4.120.md` for baseline numbers

## Phase 4 — Update README performance section

- [ ] Find the performance section in `README.md`
- [ ] Update with current benchmark numbers
- [ ] Update the spectrum position (e.g., "within 2x of Go" or whatever the current position is)
- [ ] Mention the enum_match improvement if it's notable

## Phase 5 — Update V5_READINESS

- [ ] Read `docs/roadmap/v4/v4.120.0/V5_READINESS.md`
- [ ] Update or create `docs/roadmap/v4/v4.125.0/V5_READINESS.md` with current status:
  - **Qs.1 (List<Int> indexing):** RESOLVED in v4.122.0
  - **Rt.1 (enum boxing):** IMPROVED in v4.124.0 — within Nx of Rust (record actual number)
  - **Dead code (optimizer.py):** REMOVED in v4.123.0
  - **TBAA declaration:** REMOVED in v4.123.0
  - **Test hygiene (22 failures):** ALL RESOLVED across v4.120.0 + v4.121.0
  - **Bounded-generic trait:** RESOLVED in v4.121.0
  - **DWARF warning:** IMPLEMENTED in v4.121.0
- [ ] For any items still open from the v4.120.0 panel, update their status

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.125.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Full benchmark run completed (6 programs x 5 languages) | benchmark output |
| 2 | Deltas from v4.118.0 computed and documented | FINAL_REPORT_v4.130.md |
| 3 | 5x flaky audit: 0 failures across all 5 runs | audit log |
| 4 | Benchmark report published | `benchmarks/FINAL_REPORT_v4.130.md` |
| 5 | README performance section updated | README.md diff |
| 6 | V5_READINESS updated with all resolved items | V5_READINESS.md |
| 7 | `make test` green | test log |
| 8 | `make lint` clean | lint log |

---

## What this release does NOT do

- **Change any code** — no compiler, runtime, or test changes. Every diff is documentation or benchmarks.
- **Fix new bugs** — if the flaky audit reveals a failure, it goes into the v4.126.0 backlog. v4.125.0 measures and documents; it does not fix.
- **Add features** — this is purely measurement + documentation.
- **Run a panel** — the next panel is v4.130.0. This release produces the evidence; v4.130.0 grades it.
- **Guarantee the panel score** — v4.125.0 documents reality. The v4.130.0 panel decides whether it's enough.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| 5-run flaky audit reveals a new failure | low | medium | Classify and document; fix in v4.126.0 if deterministic, ignore if truly flaky (environment) |
| enum_match improvement from v4.124.0 is less than expected | medium | medium | Document the actual numbers honestly; the panel grades reality, not targets |
| Benchmark environment differs from v4.118.0, invalidating comparisons | low | medium | Use the same hardware and toolchain versions; document any differences |
| V5_READINESS has items from v4.120.0 panel that are still open | medium | low | Document them honestly with their current status; don't claim completion that hasn't happened |
| README update makes claims that aren't backed by benchmarks | low | high | Every number in README must reference FINAL_REPORT_v4.130.md |

---

## After v4.125.0

v4.126.0 through v4.129.0 are buffer releases for any remaining items identified during v4.125.0 measurement or by the v4.120.0 panel carry-forward ledger. If v4.125.0 finds no issues, these releases can be used for polish, documentation, or additional carry-forward closure.

**v4.130.0** is the v5 gate attempt 3 (panel). Seven reviewers. The mechanical rule: aggregate >= 9.0 AND 0 NEEDS WORK = Option A (tag v5.0.0). The evidence base from v4.121.0 through v4.125.0 — correctness fixes, dead-code removal, performance optimization, stability proof, updated benchmarks — is the argument for clearing the gate.
