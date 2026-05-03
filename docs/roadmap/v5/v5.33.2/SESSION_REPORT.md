# v5.33.2 — Cd.\* — relax panel-cadence enforcement

**Date:** 2026-05-03.
**Cycle:** Phase 0 → Phase 6 in one session.
**Status:** **READY** (pending lead approval + tag promotion).

---

## Headline

v5.33.2 ships **Cd.\* — relax panel-cadence enforcement to
informational-only**. Tooling-policy hotfix following directly on
v5.33.1's push: the `check_cadence.py` gate fired hard at v5.33.1
HEAD (5 minors past v5.28.0 panel) and the lead's directive was
explicit — "is not like i want to force a review all the time or
after 5 minors no hell no". v5.33.2 demotes the script to
informational-only.

**Zero compiler edits. Zero runtime edits. Zero MIR / IR
changes. Zero `mapanare/self/*.mn` source edits.** Strict 3-stage
fixed point preserved by construction at v5.33.1's 241,898 lines
/ 0-line diff (30-release strict streak from the v5.7.1 baseline).
Goldens **95/95** at HEAD.

The lesson — recorded in user memory as
`feedback_no_forced_cadence_gates` so it survives across sessions:

> **Distinction.** Doc-drift / changelog-honesty / fixed-point
> line-count gates ENFORCE *artifact correctness* and stay hard.
> They catch real drift in shipped artifacts. Cadence
> enforcement tracks a *human scheduling decision*, which is the
> lead's call. The first class enforces; the second informs.

---

## Per-item closure (Cd.1 + Cd.2 + Vb.1 + Vb.2 + Vb.3 + Vb.4)

| ID | What changed |
|----|--------------|
| **Cd.1** | `scripts/check_cadence.py` rewritten. `main()` always returns 0. `OVERDUE` line renamed to `REMINDER` and gains a clarifying "Informational only — lead drives review timing." footer. Docstring rewritten to record the v5.24.0 Hy.3 → v5.33.2 Cd.1 history and articulate the artifact-correctness-vs-human-scheduling distinction so future contributors don't re-introduce the enforcement. |
| **Cd.2** | `tests/test_cadence.py` updated. `test_cadence_within_window_at_head` renamed to `test_cadence_always_exits_zero_at_head` (asserts exit 0; accepts both OK and REMINDER text). `test_cadence_overdue_fixture` and `test_cadence_at_threshold_fires` (renamed to `test_cadence_at_threshold_prints_reminder`) updated to assert exit 0 + REMINDER message. The other 3 tests (just-below-threshold, picks-latest-panel, no-panels-clean) already asserted exit 0 and are unchanged. Module docstring updated to point at the v5.33.2 contract + the user-memory feedback entry. |
| **Vb.1** | `python3 scripts/bump_version.py 5.33.2` ran clean. VERSION 5.33.1 → 5.33.2; README.md + 3 localized README badges; CHANGELOG `[5.33.2]` stub. |
| **Vb.2** | CHANGELOG `[5.33.2]` stub replaced with one-paragraph hotfix entry. `check_changelog_honesty.py` GREEN. |
| **Vb.3** | CLAUDE.md `## Most recent releases` v5.33.2 entry prepended above v5.33.1 (~38 lines, mirrors the v5.33.1 polish-release shape). |
| **Vb.4** | `make build-rt` rebuilt `libmapanare_rt.a` with `-DMAPANARE_VERSION="\"5.33.2\""` for all 8 modules; `python3 scripts/build_stage1.py` rebuilt mnc-stage1; `bash scripts/verify_fixed_point.sh` STRICT preserved at **241,898 lines / 0 diff** (matches v5.33.0 + v5.33.1). 95/95 goldens preserved. **Lesson re-applied:** the v5.31.0 + v5.33.1 SESSION_REPORTs documented that VERSION bumps require BOTH stage1 rebuild AND C-runtime archive rebuild (since `MAPANARE_VERSION` is macro-baked at C-runtime compile time). v5.33.2 ran them in the right order on the first try. |

---

## Phase plan execution

- **Phase 0** (~3 min) — pre-flight: confirmed v5.33.1 HEAD; reproduced both failures locally (`tests/test_cadence.py::test_cadence_within_window_at_head` exit 1; `python3 scripts/check_cadence.py` exit 1). Noted that doc-freshness + ci-gates tests now pass at v5.33.1 (the v5.33.1 fix worked there) — only the cadence axis is failing.
- **Phase 1** (~10 min) — Cd.1: rewrote `scripts/check_cadence.py` with always-exit-0 contract + REMINDER messaging.
- **Phase 2** (~10 min) — Cd.2: rewrote `tests/test_cadence.py` to match.
- **Phase 3** (~5 min) — local pytest validation. Ran `pytest tests/test_cadence.py tests/test_doc_freshness.py tests/test_ci.py -v` → **31/31 PASS**. (Locally caught what v5.33.1's process missed by skipping pytest.)
- **Phase 4** (~5 min) — Vb.1 + Vb.2: bump_version.py 5.33.2 + CHANGELOG entry.
- **Phase 5** (~5 min) — Vb.3: CLAUDE.md release-notes entry; PLAN.md + this SESSION_REPORT under `docs/roadmap/v5/v5.33.2/`.
- **Phase 6** (~5 min) — Vb.4: stage1 + runtime rebuild + STRICT fixed-point + 95/95 goldens; final commits.

**Total wall time:** ~45 min, within the PLAN's 30-min target with a small overshoot for thorough docs.

---

## Process improvement captured

v5.33.1 closed its single-axis (SPEC header) cleanly but skipped
running `pytest` locally before pushing. The CI failure surfaced
3 broken tests, of which 1 (cadence) the v5.33.1 fix could not
have closed and 2 (doc_freshness + ci-gates) it did close. The
gap was: the v5.33.1 PROMPT only required `make ci-gates` +
`make lint` + goldens, none of which catch test failures in
`tests/test_cadence.py` etc.

**v5.33.2 added pytest validation (Phase 3) before any commit.**
Future docs / tooling hotfixes will run targeted pytest on tests
that exercise the gates they're touching, before pushing.

This is captured implicitly in the v5.33.2 PLAN (success
criteria includes "pytest tests/test_cadence.py
tests/test_doc_freshness.py tests/test_ci.py all green") and
explicitly here for the next release author.

---

## Source delta

| File | Lines changed |
|------|---------------|
| `scripts/check_cadence.py` | -27 / +50 (full rewrite — always exit 0; REMINDER messaging; updated docstring) |
| `tests/test_cadence.py` | -16 / +30 (fixture-case rewrites; module docstring rewrite) |
| `CHANGELOG.md` | +18 / -2 (Vb.2 hotfix entry replacing stub) |
| `CLAUDE.md` | +38 / 0 (Vb.3 release-notes entry, before v5.33.1) |
| `VERSION` | +1 / -1 (Vb.1) |
| `README.md` + 3 localized | 4 × (+1 / -1) (Vb.1 badge) |
| `docs/roadmap/v5/v5.33.2/PLAN.md` | new |
| `docs/roadmap/v5/v5.33.2/SESSION_REPORT.md` | new (this file) |

**Zero `mapanare/`, `mapanare/self/`, `runtime/` edits.** Stage1
binary + C-runtime archive both rebuilt, but neither artifact
lands in git.

---

## Carry-forward delta

**Closes:**
- The v5.33.1-push CI failures: "Cadence enforcement (warn-only)"
  job + `tests/test_cadence.py::test_cadence_within_window_at_head`.
  Both depended on `check_cadence.py` exit 1; both now pass.
- The misleading shape of "warn-only" CI labels with `exit 1`
  scripts. The label now matches the behavior.

**Inherits:**
- **Tn.1 — HIGH.** 95-golden link-and-run gate; 6-release overdue.
- **macOS Developer ID notarization — MEDIUM.** Carry from
  v5.33.0 Nu.2.
- **Panel cadence — DEMOTED to LOW.** Was HIGH in v5.33.1
  SESSION_REPORT (escalated for v5.34.0 to address). v5.33.2's
  Cd.\* policy change makes the cadence informational, so the
  HIGH severity is no longer warranted. The cadence-gap signal
  remains visible as a CI-log REMINDER line; the lead can
  schedule a panel at any minor version when work warrants it.
- **Other LOW carries:** Linux aarch64 + macOS x86_64 native
  tarballs from v5.33.0; named-tzdb refresh; etc.

**Aggregate state entering v5.34.0:** **1 HIGH** (Tn.1) /
**2 MEDIUM** (macOS notarization; carry) / **~6 LOW**.

---

## Lessons captured

1. **Don't enforce human scheduling decisions as artifact gates.**
   The v5.24.0 Hy.3 introduction of `check_cadence.py` as an
   exit-1-on-overdue gate conflated "the codebase is in a known
   state" (artifact-correctness, gate-worthy) with "we should
   schedule a panel review" (process decision, lead's call). The
   distinction matters: the former is mechanically verifiable,
   the latter depends on context only humans have. Recorded as
   user memory `feedback_no_forced_cadence_gates`.
2. **Run pytest on tests that exercise the gates you're
   editing.** v5.33.1's SPEC-header fix didn't include pytest in
   its validation, and 1 of 3 CI test failures was exactly the
   kind of test that would have surfaced before the push. v5.33.2
   added Phase 3 explicitly for this. The PROMPT's
   `make ci-gates` + `make lint` are necessary but not
   sufficient when test-suite coverage exists for the gates.
3. **CI labels should match CI behavior.** A job named "warn-only"
   that runs an `exit 1`-when-unhappy script will display as red
   in the UI and confuse contributors who trust the label.
   `continue-on-error: true` at the workflow level is not the
   same as the *job* being non-blocking from a UX perspective —
   the red ❌ still appears. v5.33.2's cleaner shape: the script
   is genuinely warn-only (exit 0 + REMINDER), so the job is
   green and the label is honest.

---

## Closeout checklist

- [x] `scripts/check_cadence.py` always exits 0; REMINDER message intact
- [x] `tests/test_cadence.py` updated; all 6 cases pass at HEAD
- [x] `pytest tests/test_cadence.py tests/test_doc_freshness.py tests/test_ci.py` 31/31 GREEN
- [x] `python3 scripts/check_cadence.py` exit 0 at HEAD
- [x] `make ci-gates` 9/9 GREEN (cadence sub-gate now reports REMINDER as exit 0 → "cadence: GREEN")
- [x] `make lint` clean
- [x] `bump_version.py 5.33.2` ran clean
- [x] CHANGELOG `[5.33.2]` one-paragraph entry written
- [x] `check_changelog_honesty.py` GREEN
- [x] `check_doc_freshness.py` GREEN
- [x] CLAUDE.md release-notes entry added
- [x] `make build-rt` rebuilt `libmapanare_rt.a` with VERSION 5.33.2
- [x] `python3 scripts/build_stage1.py` rebuilt mnc-stage1
- [x] `verify_fixed_point.sh` STRICT — 241,898 lines / 0 diff
- [x] Goldens 95/95
- [x] PLAN.md + SESSION_REPORT.md (this file) complete
- [x] User-memory `feedback_no_forced_cadence_gates` recorded
- [ ] GitNexus index refreshed (`npx gitnexus analyze`) — Phase 6
- [ ] `git push origin dev` — Phase 6 (HTTPS auth in WSL may fail; lead pushes if so)
- [ ] **Tag NOT created until lead approval** — `git tag v5.33.2` waits
