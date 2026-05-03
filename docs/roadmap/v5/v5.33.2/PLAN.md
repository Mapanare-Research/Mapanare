# v5.33.2 — Cd.\* — relax panel-cadence enforcement

**Status:** READY
**Type:** Tooling-policy hotfix. Zero compiler / runtime / IR edits.
**Breaking:** No.
**Prerequisite:** v5.33.1 shipped (Hd.\* SPEC header re-sync).
**Estimated effort:** 30 min.

---

## Why this exists

After v5.33.1 was pushed, CI surfaced two failures that v5.33.1
did not address:

1. The **"Cadence enforcement (warn-only)" job** in
   `.github/workflows/ci.yml` runs `python3 scripts/check_cadence.py`
   directly. The script exits 1 when the lag past the last
   `.reviews/v*` panel directory is ≥5 minor versions. At v5.33.1
   HEAD that lag is exactly 5 (last panel: v5.28.0), so the job
   reports a red ❌ in the GitHub UI even though the job is
   `continue-on-error: true`.
2. **`tests/test_cadence.py::test_cadence_within_window_at_head`**
   asserts the script exits 0 at HEAD. Currently fails.

Both stem from one design choice: **`check_cadence.py` enforces a
human scheduling decision (when to run a 7-reviewer panel) as if
it were an artifact-correctness gate**. Per project memory, the
roadmap is fluid by design and panel/tag timing is the lead's
call. Treating "5 minors since last panel" as a CI-blocking
condition does not match that project shape.

The right fix is to demote the script to **informational-only**:
print a `REMINDER` line in CI logs when the lag is past threshold
(so the cadence stays visible), but always exit 0. Doc-drift /
changelog-honesty / fixed-point line-count gates stay hard —
those enforce *artifact correctness* (good). This one tracks a
*human scheduling decision* (informational-only).

User policy at v5.33.2: forced-cadence review/panel gates are
not wanted. Recorded in user memory as
`feedback_no_forced_cadence_gates`.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Cd.1** | HIGH (CI) | `scripts/check_cadence.py` rewritten — `main()` always returns 0; `OVERDUE` message renamed to `REMINDER` + clarifying "Informational only — lead drives review timing." line; docstring rewritten with the v5.24.0 → v5.33.2 history. | 10 min |
| **Cd.2** | HIGH | `tests/test_cadence.py` updated — `test_cadence_within_window_at_head` renamed to `test_cadence_always_exits_zero_at_head` (asserts exit 0, accepts both OK and REMINDER); `test_cadence_overdue_fixture` and `test_cadence_at_threshold_fires` updated to assert exit 0 + REMINDER (the latter renamed to `test_cadence_at_threshold_prints_reminder`). Other 3 tests unchanged (already asserted exit 0). | 10 min |
| **Vb.1** | MEDIUM | `python3 scripts/bump_version.py 5.33.2` — VERSION + 4 README badges + CHANGELOG stub. | 5 min |
| **Vb.2** | MEDIUM | CHANGELOG `[5.33.2]` one-paragraph hotfix entry. | 5 min |
| **Vb.3** | LOW | CLAUDE.md release-notes entry. | 5 min |
| **Vb.4** | MEDIUM | Stage1 + runtime archive rebuild post-bump (lessons captured at v5.31.0 + v5.33.1: rebuild stage1 AND `make build-rt` to keep VERSION metadata + macro consistent). Verify STRICT fixed point preserved. | 5 min |

**Total source delta:** ~120 LOC across 2 files (script + tests).
Plus mechanical Vb.\* surfaces.

---

## Out of scope

- **Compiler / runtime / IR / `mapanare/self/*.mn` edits.** Zero.
- **Removing the script entirely.** Considered but rejected — the
  REMINDER line still has value as a low-noise visibility signal
  in CI logs. Keeping it informational means the cadence stays
  visible without ever turning into a blocker.
- **Removing the workflow job.** Not needed — with the script
  always exit 0, the job will be GREEN every push. Removing it
  would lose the visibility.
- **Bumping the threshold instead of relaxing the exit code.**
  Considered (e.g. 5 → 20). Rejected because the user's directive
  is "no forced cadence", which the threshold-bump approach only
  delays. Informational-only is the structurally correct fix.
- **Wider review-process documentation refresh.** `.reviews/REVIEW_CADENCE.md`
  may want a one-line note that cadence is now suggested, not
  enforced. Tracked as a follow-on doc-polish for v5.34.0+ (LOW).
- **Tag promotion.** `git tag v5.33.2` waits for explicit lead
  approval per project memory.

---

## Risk

1. **Removing exit-1 hides a real cadence problem.** Mitigation:
   the REMINDER line still prints, and CI logs are visible. If the
   lead wants to schedule a panel after seeing 10+ REMINDER lines,
   nothing prevents it.
2. **A future contributor re-introduces the enforcement** by
   adding back `return 1`. Mitigation: docstring + memory entry +
   CHANGELOG entry document the v5.33.2 decision; the test suite
   actively asserts exit 0 on overdue (so re-introducing exit 1
   would fail tests).

---

## Success criteria

- ✅ `python3 scripts/check_cadence.py` exit 0 at v5.33.2 HEAD
- ✅ `pytest tests/test_cadence.py tests/test_doc_freshness.py tests/test_ci.py` all green
- ✅ `make ci-gates` 9/9 GREEN (cadence sub-gate now reports REMINDER as exit 0)
- ✅ `make lint` clean
- ✅ STRICT 3-stage fixed point preserved at v5.33.1's line count / 0 diff
- ✅ Goldens 95/95 (no test edits beyond `test_cadence.py`)
- ✅ VERSION = 5.33.2; READMEs (4 locales) bumped; CHANGELOG entry
  written; CLAUDE.md release-notes entry added; SESSION_REPORT
  complete
- ✅ `feedback_no_forced_cadence_gates` user-memory entry recorded

---

## Carry-forward delta

**Closes:**
- "Cadence enforcement (warn-only)" CI job's red-❌ shape — the
  script is now genuinely warn-only.
- `tests/test_cadence.py::test_cadence_within_window_at_head` test
  failure — replaced with a test that asserts the actual
  v5.33.2 contract.

**Inherits:**
- **Tn.1 — HIGH.** 95-golden link-and-run gate; 6-release overdue.
- **Panel cadence — now LOW** (was HIGH at v5.33.1 SESSION_REPORT).
  Cd.\* relaxed the gate to informational; the lead can schedule
  a panel at any minor version when the work warrants one. The
  cadence-gap metric is still visible in CI logs as a REMINDER
  line.
- **macOS Developer ID notarization — MEDIUM.** From v5.33.0 Nu.2.
- Other LOW carries (Linux aarch64 + macOS x86_64 tarballs, etc.)
