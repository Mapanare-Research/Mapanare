# v5.30.0 — Vb.\* — version bump only (packaging release)

**Status:** PLANNING
**Type:** Packaging-only release. **Zero compiler edits. Zero
runtime edits. Zero `mapanare/self/*.mn` source edits. Zero new
features. Zero bug fixes.**
**Breaking:** No.
**Prerequisite:** v5.29.0 shipped (Mb.10 + Pv.7 + Pv.8 — Win64
ABI closeout; STRICT 3-stage fixed point at 241,898 lines / 0
diff; goldens 95/95; Mb.\* arc CLOSED structurally).
**Estimated effort:** 1 short session (~30–45 min).

---

## Why this exists

v5.30.0 is a **version-bump-only release**. Its only purpose is
to advance the published version surface (VERSION file, README
badges across 4 locales, CHANGELOG) and to refresh the open
`dev` → `main` PR description so it reflects the cumulative
scope of every release that has not yet landed on `main`.

There is **no new code** in this release. All recent fix /
feature work shipped at v5.29.0 (Mb.10 self-host emitter routing
plus the Pv.7/Pv.8 commits already on dev pre-v5.29.0). The
v5.29.0 SESSION_REPORT documented STRICT fixed point and arc
closure; v5.30.0 just bumps the surface so the next merge-to-
main carries a clean version number.

This is the smallest possible release shape — the inverse of
v5.28.0 (panel-only, ledger work) and v5.21.1 (docs-only). Both
of those still touched many files; v5.30.0 touches only what
`scripts/bump_version.py` writes plus the GitHub PR body.

### Why not just merge v5.29.0 to main directly?

- `main` is currently at **v5.13.0** (`538584b "Bump version to
  5.13.0 and update changelog"`); the dev branch carries
  v5.13.0 → v5.29.0 worth of work (~16 minor releases) waiting
  to merge.
- The open PR backing the merge was last refreshed when
  v5.28.0 was the dev HEAD. Its description does not yet
  mention v5.29.0's Mb.10 / Pv.7 / Pv.8 closures, and would
  not mention v5.30.0 either if we merged at v5.29.0 HEAD.
- Bumping to v5.30.0 with the PR description refreshed in the
  same step keeps the published version, the merge commit, and
  the PR body in sync.

---

## Goals

1. **Vb.1** Run `python3 scripts/bump_version.py 5.30.0`. This
   handles VERSION + 4 README locales + the CHANGELOG `##
   [5.30.0]` stub.
2. **Vb.2** Fill the CHANGELOG.md `[5.30.0]` section with a
   short "packaging-only / version bump" header. No `### Added`
   / `### Changed` / `### Fixed` content beyond the
   one-paragraph note (this is the ONLY release where empty
   subsections are correct — otherwise `check_changelog_honesty`
   wants real bullets).
3. **Vb.3** Update CLAUDE.md "Most recent releases" — prepend
   a short v5.30.0 entry above v5.29.0 (~15 lines, much
   shorter than substantive releases). Mention zero edits
   posture explicitly.
4. **Pr.1** Refresh the open `dev` → `main` PR description on
   GitHub to cover the v5.13.0 → v5.30.0 cumulative scope.
   Replace any v5.28-specific summary text with v5.29 + v5.30
   entries. (Requires user to either share PR number/body or
   run the gh command — see PROMPT.md Phase 4.)
5. **Vb.4** Strict 3-stage fixed-point validation. Should
   remain **STRICT at 241,898 lines / 0 diff** by construction
   after rebuilding `mnc-stage1` against the v5.30.0-versioned
   runtime (the v5.9.0 DX.2 version-string bake means the
   stage1 binary picks up the new version through the runtime
   re-link; once stage1 is rebuilt, both stages embed
   `"5.30.0"` and the diff is zero).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Vb.1** | LOW (mechanical) | **`bump_version.py 5.30.0`.** VERSION 5.29.0 → 5.30.0; READMEs in en/es/pt/zh-CN; CHANGELOG.md stub. Inspect diff; `bump_version.py` has surfaced one CARRY_FORWARD bug (v5.23.0 RC.3 — goldens-badge regex). Eyeball before commit. | 5 min |
| **Vb.2** | LOW | **CHANGELOG.md `[5.30.0]` writeup.** One-paragraph header explaining "packaging-only release; bumps version surface; no code changes." Empty `### Added` / `### Changed` / `### Fixed` subsections (or just omit them — the section is intentionally minimal). `check_changelog_honesty` should still pass since there are no claims to verify. | 5 min |
| **Vb.3** | LOW | **CLAUDE.md release-notes entry.** Prepend ~15-line v5.30.0 entry above v5.29.0. State "Zero compiler edits. Zero runtime edits. Zero `mapanare/self/*.mn` source edits. Strict 3-stage fixed point preserved by construction at v5.29.0's 241,898 lines / 0 diff (25-release strict streak)." Reference v5.29.0 as the prior release and note Pr.1 PR refresh as the substantive deliverable of v5.30.0. | 10 min |
| **Pr.1** | MEDIUM (process) | **PR description refresh.** Open `dev` → `main` PR was last revised when v5.28.0 was HEAD; needs v5.29.0 + v5.30.0 entries appended (or full rewrite). User-supplied step — Claude does not have GitHub credentials in this environment (no `gh` CLI installed). Two options: (a) user pastes the current PR body and Claude drafts the new one; (b) user runs `gh pr edit <num> --body-file <file>` after Claude generates the file. | 15–20 min |
| **Vb.4** | LOW | **Stage1 rebuild + fixed-point validation.** `python3 scripts/build_stage1.py` then `bash scripts/verify_fixed_point.sh`. Strict 0-line diff at 241,898 lines preserved by construction (no source edits; only the `__mn_version_string()` runtime call's return value changes from `"5.29.0"` → `"5.30.0"`, and once stage1 is re-linked against the v5.30.0 runtime, both stages bake the same string). | 5 min |
| **Vb.5** | LOW | **`make ci-gates` + `make lint`.** Both must be GREEN. Cadence-check fires GREEN (1 minor since v5.28.0 panel; threshold is 5+). Doc-freshness fires GREEN (badges synced by Vb.1). | 5 min |

---

## Phase plan

See PROMPT.md for execution. High-level:

- **Phase 0** — pre-flight: confirm v5.29.0 HEAD is clean
  (goldens 95/95; STRICT 0 diff; ci-gates GREEN). Confirm no
  pending uncommitted source changes.
- **Phase 1** — `bump_version.py 5.30.0`; eyeball diff;
  fill CHANGELOG; commit Vb.1 + Vb.2 together.
- **Phase 2** — CLAUDE.md release-notes entry; commit Vb.3.
- **Phase 3** — Stage1 rebuild + fixed-point validation;
  commit no source changes (rebuild is local-only artifact).
- **Phase 4** — PR description refresh (user-supplied); commit
  any helper file (e.g., `docs/roadmap/v5/v5.30.0/PR_BODY.md`)
  if generated.
- **Phase 5** — closeout: SESSION_REPORT.md (short — mirror
  v5.21.1 polish-release shape, not the v5.29.0 fix-release
  shape).

---

## Out of scope

- **Tn.1** (extend `tests/llvm/test_async_link.py` to all 95
  goldens) — v5.28.0 panel directive escalated to MEDIUM at
  v5.29.0 since v5.29.0 did not pick it up; v5.30.0 also does
  not pick it up because v5.30.0 is packaging-only. **Carries
  forward to v5.31.0 — at that point Tn.1 is overdue and
  should ship.**
- **M.1**, **A.1**, **Ra.New1**, **Pv.8.B** — all carry
  forward to v5.31.0+.
- **Borrow checker** — v6.0.
- **Hard removal of `{}` syntax** — v6.0.
- Any code edit, test addition, or feature work — by
  construction. If a fix is needed, ship it as v5.30.1 or
  v5.31.0 depending on severity.

---

## Risk

1. **`bump_version.py` surprise.** v5.23.0 RC.3 caught a regex
   miss on the goldens badge; v5.29.0 Vb.1 ran clean. Phase 1
   eyeballs the diff before commit (mitigation).
2. **Empty CHANGELOG subsections trip a CI gate.** The honesty
   gate validates that any bullet text resolves to a real
   path/symbol, but does not require non-empty subsections. The
   one-paragraph header is honest because it is verifiable
   ("packaging-only" = empty diff in `mapanare/self/`,
   `runtime/`, `mapanare/`). Mitigation: omit the empty
   subsections entirely if the gate complains.
3. **PR description drift.** The dev → main PR body is
   GitHub-side state, not in the repo. v5.30.0's commit log
   stays consistent regardless, but the PR body needs manual
   refresh. Mitigation: Phase 4 explicitly stages a
   `PR_BODY.md` artifact in `docs/roadmap/v5/v5.30.0/` that
   the lead can `gh pr edit --body-file` from.
4. **Cadence pressure.** v5.30.0 is the second non-substantive
   release in a row (v5.28.0 was panel-only). The cadence-
   check gate is informational, not a fail — it fires hard at
   5+ minor since the last panel (v5.28.0); v5.30.0 is 2
   minor past, so well under threshold.

---

## Success criteria

- ✅ VERSION = 5.30.0; README badges (en/es/pt/zh-CN) bumped.
- ✅ CHANGELOG.md `[5.30.0]` section written; honesty gate
  GREEN.
- ✅ CLAUDE.md release-notes entry added.
- ✅ Strict 3-stage fixed point preserved at 0-line diff
  (post-stage1-rebuild line count documented in
  SESSION_REPORT).
- ✅ Goldens 95/95.
- ✅ `make ci-gates` GREEN; `make lint` clean.
- ✅ PR description on GitHub reflects v5.13.0 → v5.30.0
  cumulative scope.
- ⏳ Tag NOT created until lead approval (per project memory:
  "Never bump to v5 or create v5 tags without explicit user
  approval").

---

## Carry-forward delta

**Closes:**
- nothing structural — v5.30.0 is packaging-only.

**Inherits to v5.31.0:**
- **Tn.1** (now 2-release overdue per v5.28.0 panel directive
  — should ship at v5.31.0).
- M.1, A.1, Ra.New1, Pv.8.B (still LOW, no urgency change).

**Aggregate state entering v5.31.0:** 0 HIGH / 1 MEDIUM (Tn.1
overdue) / ~5 LOW.

**Cadence:** next routine panel still due v5.33.0 (3 minor
after v5.30.0).
