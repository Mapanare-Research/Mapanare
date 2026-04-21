# Mapanare v4.130.0 — Pre-Panel Prep + Third Flaky Audit

> **Buffer release 5 of the v4.131.0 closeout arc.** Pre-panel evidence
> assembly. Final verification before the v5 gate attempt 3. Third
> 5× flaky audit, valgrind + ASan sweeps on all 65 goldens, claim-
> level pre-panel audit of v4.120.0–v4.129.0 SESSION_REPORTs,
> MEASUREMENTS.md finalised for the v4.131.0 panel. **Evidence only —
> no new code.**

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.129.0
**Delta review:** No
**Full panel:** No (panel happens at v4.131.0)
**Estimated work:** 1 sprint (~4–6 h wall for sanitizer sweeps + pytest)
**Theme:** 130 releases deep, last chance to catch anything before the panel reads evidence.

> **Note on directory drift.** The original `PLAN.md` in this
> directory (preserved at `PLAN-original.md` for history) described
> v4.130.0 as THE PANEL. The `PROMPT.md` (authoritative per
> CLAUDE.md + v4.129.0 SR's "Next session should start with v4.130.0
> — pre-panel prep") overrode that scope, moving the panel to
> v4.131.0. This file is the PLAN matching the actual release scope.
> Documented as Dr.2 in `PRE_PANEL_AUDIT.md`.

---

## Why v4.130.0 exists

The v4.131.0 panel reads the evidence and renders judgment. This
release produces the evidence. Every claim from v4.120.0–v4.129.0
gets fact-checked. Every golden test gets sanitizer coverage. The
test suite gets a 5× flaky audit. MEASUREMENTS.md assembles every
metric the panel needs.

The v4.120.0 panel (8.21/10) had one NEEDS WORK from Anaconda on
test hygiene. The closeout arc (v4.121.0–v4.130.0) addresses that
directly. This release proves the test suite is reliable, the
memory safety story is documented, and every prior claim holds up
to scrutiny.

---

## Scope

### Phase 1 — Third 5× flaky audit

Run `python3 -m pytest tests/ --ignore=tests/bootstrap -q --no-header`
five times sequentially. Capture the full per-test FAILED list per
run (not just `tail -2` as v4.125.0 did). Diff sorted FAILED lists
pairwise across all 4 adjacent pairs. **Target: 0 flaky findings.**

Artefacts: `docs/roadmap/v4/v4.130.0/FLAKY_AUDIT.md`,
`docs/roadmap/v4/v4.130.0/flaky-runs/run{1..5}.log`,
`docs/roadmap/v4/v4.130.0/flaky-runs/run{1..5}.failed.sorted`,
`docs/roadmap/v4/v4.130.0/flaky-runs/summary.log`.

### Phase 2 — Valgrind sweep

Run `scripts/valgrind_all_goldens.sh` against all 65 goldens,
compiling each through `mnc-stage1` under valgrind. Classify
CLEAN / WARNINGS_ONLY / ERRORS. Compare against v4.105.0 baseline.

Artefacts: `docs/roadmap/v4/v4.130.0/VALGRIND_REPORT.md`,
`docs/roadmap/v4/v4.130.0/valgrind-summary.tsv` (copy of
`/tmp/v4_130_valgrind/valgrind-summary.tsv`).

### Phase 3 — ASan sweep

Rebuild `mnc-stage1-asan` via `scripts/build_asan.sh` (C runtime +
compiled IR + main wrapper with `-fsanitize=address -O1`). Run
`scripts/run_asan_goldens.sh` across all 65 goldens. Classify
CLEAN / ASAN_ERROR / CRASH_NO_ASAN.

Artefacts: `docs/roadmap/v4/v4.130.0/ASAN_REPORT.md`,
`docs/roadmap/v4/v4.130.0/asan-summary.tsv`.

### Phase 4 — Pre-panel audit

Fact-check every load-bearing claim in v4.120.0–v4.129.0
SESSION_REPORTs (10 files, ~2,000 lines). Use `ls`, Grep, Read,
`wc -l`, `git log --follow` to verify. Per PROMPT Decision 3:
discrepancies documented here; **SESSION_REPORTs NOT retroactively
edited.**

Artefacts: `docs/roadmap/v4/v4.130.0/PRE_PANEL_AUDIT.md`.

### Phase 5 — MEASUREMENTS.md

Assemble the single canonical pre-panel snapshot at
`docs/roadmap/v4/v4.131.0/MEASUREMENTS.md`. 10 sections: test
count, self-hosted compiler, benchmark summary, fixed-point, sanitizers,
flaky audit, dead-code, carry-forward, panel score history,
reproducibility.

### Phase 6 — Closeout

Standard closeout: CHANGELOG entry, SESSION_REPORT, PLAN.md Status →
DONE, v4/README.md + ROADMAP.md updates, CLAUDE.md current-version,
VERSION bump (to 4.131.0), final commits.

---

## Decisions (PROMPT defaults)

1. **Valgrind scope: all 64 goldens.** (Actually 65 — one golden
   added v4.122.0.) Completeness > speed for a pre-panel release.
2. **ASan build: rebuild C runtime + full mnc-stage1-asan.** The
   existing `mnc-stage1-asan` binary dated to Apr 14 00:39 (pre-v4.127.0
   self-hosted changes) and was stale for this release's scope.
3. **Discrepancies: document in audit, do NOT retroactively edit
   SESSION_REPORTs.** Historical records stay honest.

---

## Exit criteria (9 items)

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | 5× flaky audit run, 0 flaky findings | PASS | `FLAKY_AUDIT.md`: 5 runs, byte-identical sorted FAILED across all 4 adjacent pairs |
| 2 | Valgrind report complete (all 65 goldens) | PASS | `VALGRIND_REPORT.md`: 0 CLEAN / 34 WARNINGS_ONLY / 31 ERRORS |
| 3 | ASan report complete (all 65 goldens) | PASS | `ASAN_REPORT.md`: 31 CLEAN / 23 ASAN_ERROR / 11 CRASH_NO_ASAN |
| 4 | Pre-panel audit complete (v4.120.0–v4.129.0) | PASS | `PRE_PANEL_AUDIT.md`: 0 material, 5 cosmetic, 2 latent |
| 5 | MEASUREMENTS.md draft committed to v4.131.0/ | PASS | `docs/roadmap/v4/v4.131.0/MEASUREMENTS.md` (10 sections, finalised) |
| 6 | No compiler/runtime/self-hosted `.mn` code changes | PASS | `libmapanare_rt.a` byte-identical; `mnc-stage1` byte-identical |
| 7 | CHANGELOG.md [4.130.0] entry | PASS | this commit |
| 8 | VERSION bumped to 4.131.0 | PASS | final commit |
| 9 | Directory PLAN.md rewrite (Dr.2 fix) | PASS | this file |

9/9 PASS.

---

## What this release does NOT do

- **Change compiler, runtime, or self-hosted `.mn` code.** Pure
  evidence assembly. Only PLAN.md is rewritten (Dr.2 directory drift
  fix). The `.sh` / `.py` scripts shipped at v4.105.0 are re-run as-
  is; no tooling changes.
- **Fix any open docket.** Sh.2 remains open with 39 sanitizer
  findings pointed at it. An.1 remains open with 39 deterministic
  test failures. Dr.1 (self-hosted version-string freeze) is opened
  by this release's audit and remains open. All listed as v4.131.0+
  or v5.x carry-forward.
- **Run the panel.** v4.131.0 is the panel. v4.130.0 is the last
  buffer release before it.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Flaky audit surfaces a new flaky failure | low | medium | If so: fix or catalogue; v4.131.0 panel sees honest findings. Three audits (v4.117.0 / v4.125.0 / v4.130.0) all landed at 0 flaky |
| Valgrind sweep reveals a regression since v4.105.0 | low | medium | Compare top-frames vs baseline; regression → defer fix to v4.131.0+ or annotate as acceptable delta |
| ASan rebuild fails | low | medium | Existing `scripts/build_asan.sh` works from v4.105.0+; no changes needed for this release |
| Pre-panel audit finds a material discrepancy | medium | medium | Per PROMPT Decision 3: document in audit, don't retroactively edit. If panel rejects the evidence on that basis, v4.131.0+ addresses |

---

## After v4.130.0

**v4.131.0 — THE PANEL.** 7 reviewers grade v4.121.0–v4.130.0
holistically. The mechanical rule applies:

- **Option A (tag v5.0.0):** aggregate ≥ 9.0 AND 0 NEEDS WORK
- **Option B (continue v4.132.0+):** aggregate < 9.0 OR any NEEDS WORK
- **Option C (tag v5.0.0-rc1):** aggregate ≥ 8.5 AND < 9.0 AND 0 NEEDS WORK

The numbers are the numbers. The process is the process. 130
releases deep, we keep shipping regardless of the panel outcome.
