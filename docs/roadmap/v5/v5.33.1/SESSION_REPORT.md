# v5.33.1 — Hd.\* — SPEC header drift hotfix

**Date:** 2026-05-03.
**Cycle:** Phase 0 → Phase 6 in one session.
**Status:** **READY** (pending lead approval + tag promotion).

---

## Headline

v5.33.1 ships **Hd.\* — SPEC header drift hotfix**. Single-axis
docs-surface release closing the `check_doc_freshness.py`
SPEC-header lag violation that fired hard at v5.33.0 HEAD —
`docs/SPEC.md` referenced "synced to the v5.30.0 cut" while
`VERSION` was `5.33.0`, a 3-minor lag against the gate's
2-minor tolerance. Same posture as v5.21.1 (pre-panel docs
hygiene) and v5.30.0 (Vb.\*-only): doc-surface release with
zero source-side touch.

**Zero compiler edits. Zero runtime edits. Zero MIR / IR
changes. Zero `mapanare/self/*.mn` source edits. Zero test
edits.** Strict 3-stage fixed point preserved by construction
at v5.33.0's 241,898 lines / 0-line diff (29-release strict
streak from the v5.7.1 baseline). Goldens **95/95** at HEAD.

The structural gate that caught this — `check_doc_freshness.py`
`check_spec_header()`, landed at v5.24.0 Hy.2 — fired exactly as
designed. SPEC stayed unsynced for 3 minor releases (v5.31.0 +
v5.32.0 + v5.33.0), the gate flipped hard at v5.33.0 HEAD, and
v5.33.1 is the gate doing its job.

---

## Per-item closure (Hd.1 + Hd.2 + Hd.3 + Vb.1 + Vb.2 + Vb.3 + Vb.4)

| ID | What changed |
|----|--------------|
| **Hd.1** | `docs/SPEC.md:3-4` header bumped: `**Version:** 5.30.0` → `5.33.1`; `synced to the v5.30.0 cut (2026-05-02)` → `synced to the v5.33.1 cut (2026-05-03)`. Two-line edit. |
| **Hd.2** | `docs/SPEC.md` new sync block prepended above the existing v5.28.0 → v5.30.0 block. 13 lines, declarative, mirrors the existing block shape. Covers v5.31.0 (Bn.\* banner hotfix; "[dev mode]" lie killed on release installs), v5.32.0 (Nw.\* native `mnc.exe` shipped in Windows SDK ZIP; Python becomes bootstrap-only on Windows release installs), v5.33.0 (Nu.\* native `mnc` shipped in Linux x86_64 + macOS arm64 release tarballs; Linux aarch64 + macOS x86_64 deferred to v5.34.0+), and v5.33.1 (Hd.\* — this re-sync). Asserts the trio added "zero language features, zero new MIR ops, zero new IR shapes, zero new runtime functions" — packaging / hotfix releases only. The v5.21.0 sync block remains authoritative for language semantics. Every claim cross-checked against the corresponding SESSION_REPORT before writing. |
| **Hd.3** | `python3 scripts/check_doc_freshness.py` flipped from RED (1 violation) to GREEN ("clean", exit 0). `make ci-gates` 9/9 GREEN (silent_skips, changelog_honesty, workflow_shapes, docs_drift, hollow_features, struct_registry, doc_freshness, cadence (warn-only OVERDUE — see below), clean-build-test). `make lint` clean. |
| **Vb.1** | `python3 scripts/bump_version.py 5.33.1` ran clean. Updated VERSION (5.33.0 → 5.33.1), README.md + docs/README.es.md + docs/README.pt.md + docs/README.zh-CN.md (4 locale badges), CHANGELOG.md (`[5.33.1]` stub inserted). Goldens count auto-detected as 95 from `tests/golden/*.mn`. |
| **Vb.2** | CHANGELOG.md `[5.33.1]` stub replaced with one-paragraph hotfix entry. No `### Added` / `### Changed` / `### Fixed` subsections — there is nothing to add (single-axis docs hotfix). `check_changelog_honesty.py` GREEN. Mirrors v5.30.0's packaging-release entry shape but motivated by Hd.\* not Vb.\*. |
| **Vb.3** | CLAUDE.md `## Most recent releases` v5.33.1 entry prepended above v5.33.0 (~38 lines — slightly longer than the 12-15 PROMPT estimate to fully document the cadence-gap escalation; mirrors v5.30.0's polish-release shape, not v5.29.0's fix-release shape). Documents zero-edit footprint, STRICT fixed-point preservation, 29-release streak, structural gate behaviour, source delta, panel cadence escalation. |
| **Vb.4** | `python3 scripts/build_stage1.py` rebuilt mnc-stage1 against the freshly-bumped VERSION. **Phase-5 deviation note**: first `verify_fixed_point.sh` run after the stage1 rebuild surfaced a NEAR fixed point (4 diff lines, 0.002%) — stage2.ll embedded `!"5.33.1"` while stage3.ll embedded `!"5.33.0"`. Root cause: `verify_fixed_point.sh` links the stage2 binary against `runtime/native/libmapanare_rt.a`, an archive built before the VERSION bump (Mtime: 2026-05-03 02:22). The runtime archive's `MAPANARE_VERSION` macro is baked at C-runtime compile time (per `mapanare_core.c:3372-3378`), so `__mn_version_string()` returned 5.33.0 for stage2's emit pass. Resolution: ran `make build-rt` to rebuild the archive with `-DMAPANARE_VERSION="\"5.33.1\""` for all 8 modules. Re-ran `verify_fixed_point.sh` → STRICT preserved at **241,898 lines / 0 diff** (matches v5.33.0). 95/95 goldens preserved. |

---

## Phase plan execution

- **Phase 0** (~3 min) — pre-flight: VERSION 5.33.0 confirmed; recent commits clean; `?? docs/roadmap/v5/v5.33.1/` only untracked entry. `python3 scripts/check_doc_freshness.py` reproduced the failure exactly: "docs/SPEC.md: header references v5.30.\* but VERSION is 5.33.0 (lag of 3 minor versions; max tolerated is 2)". Single violation — no other drift to bundle. Baseline `python3 scripts/test_native.py` 95/95 GREEN.
- **Phase 1** (~10 min) — Hd.1 + Hd.2: edited `docs/SPEC.md` header + prepended sync block. Cross-checked claims against `docs/roadmap/v5/v5.31.0/SESSION_REPORT.md`, `docs/roadmap/v5/v5.32.0/SESSION_REPORT.md`, `docs/roadmap/v5/v5.33.0/SESSION_REPORT.md` for accuracy (specifically: v5.33.0 deferred Linux aarch64 + macOS x86_64 — block reflects deferral, does not promise four arches).
- **Phase 2** (~5 min) — Hd.3: `check_doc_freshness.py` GREEN; `make ci-gates` 9/9 GREEN; `make lint` clean.
- **Phase 3** (~5 min) — Vb.1 + Vb.2: bump_version + CHANGELOG one-paragraph entry. Single commit `8ec58bf` covering Phase 1 + Phase 3.
- **Phase 4** (~5 min) — Vb.3: CLAUDE.md release-notes entry. Commit `e5abba4`.
- **Phase 5** (~10 min) — Vb.4: stage1 rebuild → first verify NEAR (VERSION-only diff) → diagnosed runtime-archive staleness → `make build-rt` → re-verify STRICT. Documented as a deviation point above (v5.31.0 lesson: rebuild stage1 between bump and verify; v5.33.1 lesson extends to: rebuild the C runtime archive too if your local build is older than the bump, since `MAPANARE_VERSION` is macro-baked).
- **Phase 6** (~10 min) — SESSION_REPORT (this file), final commit, GitNexus refresh, push to dev.

**Total wall time:** ~50 min, within PLAN's 30-60 min estimate.

---

## Decision-1 lock — re-panel deferral

`check_cadence.py` reports `OVERDUE — 5 minor versions since
last panel (v5.28.0)` (warn-only, non-blocking). Per
`.reviews/REVIEW_CADENCE.md` a full 7-reviewer panel was due at
v5.33.0 (4-minor cadence). v5.33.1 deliberately does not run
the panel.

**Reasons:**

1. The full 7-reviewer panel is a multi-day cycle. v5.33.1 is a
   single-axis docs hotfix; bundling a panel here would inflate
   a 50-min release into a multi-day cycle and miss the point
   of a hotfix.
2. The PLAN.md explicitly scopes panel run as out-of-scope and
   defers it to v5.34.0 as a HIGH carry-forward.
3. Honest framing: closing one hard CI gate (the SPEC drift) is
   strictly better than half-closing two. The panel gap remains
   warn-only and visible in every subsequent CI run.

**Escalation:** the cadence gap is now 5 minor versions and
**HIGH** entering v5.34.0. v5.34.0's PLAN must either (a)
bundle a panel run as its primary scope, or (b) ship a
dedicated v5.X.0 panel-run release. Continuing to defer past
v5.34.0 would make the gap structurally indefensible.

---

## Source delta

| File | Lines changed |
|------|---------------|
| `docs/SPEC.md` | +14 / -2 (Hd.1 header bump + Hd.2 new sync block) |
| `CHANGELOG.md` | +12 / -2 (Vb.2 hotfix entry replacing stub) |
| `CLAUDE.md` | +43 / 0 (Vb.3 release-notes entry, before v5.33.0) |
| `VERSION` | +1 / -1 (Vb.1) |
| `README.md` | +1 / -1 (Vb.1, version badge) |
| `docs/README.es.md` | +1 / -1 (Vb.1) |
| `docs/README.pt.md` | +1 / -1 (Vb.1) |
| `docs/README.zh-CN.md` | +1 / -1 (Vb.1) |
| `docs/roadmap/v5/v5.33.1/PLAN.md` | tracked (existed pre-session) |
| `docs/roadmap/v5/v5.33.1/SESSION_REPORT.md` | new (this file) |

**Zero `mapanare/`, `mapanare/self/`, `runtime/`, `tests/`
edits.** Stage1 binary rebuilt + C-runtime archive rebuilt, but
neither artifact lands in git (both are gitignored or local).

---

## Carry-forward delta

**Closes:**
- `check_doc_freshness` SPEC-header lag violation. The gate is
  GREEN at v5.33.1 HEAD; the next recurrence (3-minor lag) is
  caught structurally in CI rather than at the panel.

**Inherits / does not close (deferred to v5.34.0 or later):**
- **Panel cadence — HIGH.** `check_cadence.py` warn-only
  OVERDUE; 5 minors since v5.28.0 panel. Escalated; v5.34.0
  PLAN must address.
- **Tn.1 — HIGH.** 95-golden link-and-run gate; per v5.32.0
  directive, escalates to HIGH at v5.33.0 if not landed; now
  6-release overdue heading into v5.34.0.
- **macOS Developer ID notarization — MEDIUM.** Carry from
  v5.33.0 Nu.2's ad-hoc `codesign -s -` shortcut.
- **Linux aarch64 + macOS x86_64 native tarballs — LOW.**
  Deferred from v5.33.0; `build_stage1.py` `--target` /
  `--output` flags need to land first.
- **Other LOW carries:** named-tzdb refresh, etc.

**Aggregate state entering v5.34.0:** **2 HIGH** (panel cadence
escalated; Tn.1 carrying forward) / **2 MEDIUM** (macOS
notarization; pre-existing carry) / **~6 LOW**.

---

## Lessons captured

1. **Rebuild the C runtime archive after a VERSION bump.**
   v5.31.0 SESSION_REPORT documented: "rebuild stage1 between
   `bump_version.py` and `verify_fixed_point.sh`". v5.33.1
   extends this: if `runtime/native/libmapanare_rt.a` predates
   the bump, `verify_fixed_point.sh` shows a 4-line VERSION-
   placeholder NEAR diff because `MAPANARE_VERSION` is
   macro-baked at C-runtime compile time. Run `make build-rt`
   alongside `python3 scripts/build_stage1.py` post-bump.
   Future `bump_version.py` could chain this — recommended
   v5.34.0+ Vb.\* polish (LOW).
2. **Single-axis hotfix discipline holds.** The PLAN explicitly
   forbade compiler / runtime / `mapanare/self/*.mn` / test
   edits. The Phase 5 deviation surfaced a real gap (runtime
   archive needs rebuilding) but the resolution stayed on the
   docs-only axis: `make build-rt` is a build-system invocation,
   not a source edit. Discipline preserved.
3. **Cross-checking against SESSION_REPORTs is load-bearing
   for sync-block accuracy.** Drafting Hd.2 from memory would
   have promised four native-`mnc` arches (the v5.33.0 PROMPT
   scope) instead of two (the actual v5.33.0 deliverable).
   Cross-check before writing, not after.

---

## Closeout checklist

- [x] `docs/SPEC.md` header bumped + sync block prepended
- [x] `python3 scripts/check_doc_freshness.py` GREEN
- [x] `make ci-gates` 9/9 GREEN
- [x] `make lint` clean
- [x] `bump_version.py 5.33.1` ran clean (VERSION + 4 README badges)
- [x] CHANGELOG `[5.33.1]` one-paragraph entry written
- [x] `check_changelog_honesty.py` GREEN
- [x] CLAUDE.md release-notes entry added
- [x] `python3 scripts/build_stage1.py` rebuilt
- [x] `make build-rt` rebuilt runtime archive with new VERSION
- [x] `verify_fixed_point.sh` STRICT — 241,898 lines / 0 diff
- [x] Goldens 95/95
- [x] SESSION_REPORT.md (this file) complete
- [x] Cadence-gap escalation noted for v5.34.0 to inherit as HIGH
- [ ] GitNexus index refreshed (`npx gitnexus analyze --embeddings`) — Phase 6
- [ ] `git push origin dev` — Phase 6
- [ ] **Tag NOT created until lead approval** — `git tag v5.33.1` waits
