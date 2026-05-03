# v5.30.0 — Vb.\* — packaging-only release: version bump

**Theme:** advance the published version surface so the next
`dev` → `main` merge carries a clean v5.30.0 number and the PR
description reflects the cumulative scope of every release that
has not yet landed on `main` (`main` is currently at v5.13.0;
this merge carries v5.13.0 → v5.30.0).

**Posture:** zero compiler edits, zero runtime edits, zero
`mapanare/self/*.mn` source edits. Mirrors v5.21.1 (also a
no-code polish release).

## What shipped

| Item | Description | Source delta |
|------|-------------|-------------:|
| Vb.1 | VERSION 5.29.0 → 5.30.0 (via `bump_version.py`) | 1 LOC |
| Vb.2 | README badges bumped (en/es/pt/zh-CN); CHANGELOG.md `[5.30.0]` section written | 5 LOC |
| Vb.3 | CLAUDE.md release-notes entry for v5.30.0 added | ~17 LOC |
| Vb.4 | stage1 rebuilt; `libmapanare_rt.a` rebuilt with VERSION=5.30.0; STRICT 3-stage fixed point verified | — |
| Hy.1 | CLAUDE.md release-notes section condensed: dropped v5.24.1 → v5.8.6 (still in CHANGELOG.md and per-release SESSION_REPORTs); dropped 13 stale "shipped" strikethrough lines from "Planned / in-progress" section; dropped stale v5.8.0 RE-PANEL line | −1143 LOC (1995 → 852) |

## Fixed point

**STRICT 3-stage fixed point** at `stage2.ll == stage3.ll` =
**241,898 lines / 0 diff** (26-release strict streak from the
v5.7.1 baseline; +0 lines vs v5.29.0 because zero
`mapanare/self/*.mn` source edits).

**Phase 4 surprise:** First `verify_fixed_point.sh` run after
the Phase 3 stage1 rebuild showed NEAR with 1-line drift in
the **opposite direction** the PROMPT predicted: stage2.ll
embedded `!"5.30.0"` but stage3.ll embedded `!"5.29.0"`. Root
cause: `runtime/native/libmapanare_rt.a` was last built (21:43)
before the Phase 1 VERSION bump, so `__mn_version_string()`
baked `MAPANARE_VERSION="5.29.0"` into the archive (the
runtime's version is set at C compile time via
`-DMAPANARE_VERSION=` from the Makefile, which reads VERSION).
`scripts/verify_fixed_point.sh` links the stage2 binary against
this archive (line 101: `gcc -o /tmp/mnc-stage2 ... "$RUNTIME_A" ...`),
so stage3 inherited the stale version. Fix: `make build-rt`
before the second `build_stage1.py` + `verify_fixed_point.sh`
cycle. STRICT achieved on the second cycle.

**Lesson for v5.31.0+:** `bump_version.py` should `make build-rt`
as part of its sequence, OR the v5.29.0 PROMPT's Phase 3
instruction should be expanded to include the runtime rebuild
step explicitly. Filed as a LOW for the next maintenance pass.

## Goldens

**95 / 95** through `mnc-stage1` (17.0s plain; 17.3s after
runtime rebuild). No regressions.

## CI gates

`make ci-gates` GREEN across all 9 sub-gates:
silent_skips, changelog_honesty, workflow_shapes, docs_drift,
hollow_features, struct_registry, doc_freshness, cadence,
clean-build-test.

`make lint` clean.

## CLAUDE.md condensation (Hy.1)

CLAUDE.md was approaching 2000 lines (1995) with 77% of the
file (1532 lines) consumed by per-release notes that duplicate
CHANGELOG.md and per-release SESSION_REPORTs. The "Most recent
releases (last 6)" header was overflowing to ~25 entries.

**What was cut (1089 lines):**
- v5.24.1 → v5.8.6 release-notes entries (21 releases)
- 13 strikethrough "shipped" entries from "Planned /
  in-progress" (v5.14.0, v5.14.1, v5.15.0, v5.15.1, v5.16.0,
  v5.17.0, v5.17.1, v5.17.2, v5.18.0, v5.20.0, v5.20.1, etc.)
- Stale v5.8.0 RE-PANEL line (already happened multiple times:
  v5.22.0, v5.28.0)
- v5.13.0 / v5.21.0 "planned" entries (both shipped)

**What was kept:**
- Last 7 release-notes entries (v5.30.0 through v5.25.0) at
  current verbosity — these are the reference set for the
  current PR-to-`main` cycle
- "Planned / in-progress" section with v5.12.0 (Windows SDK
  split, still planned) + v5.19.0 (Te.3 + Dk.* closeout) +
  v6.0 (borrow checker)
- New 6-line summary paragraph for the shipped terseness arc
  pointing at SESSION_REPORTs

**Result:** CLAUDE.md = 852 lines (−57%). Information loss
zero — every cut line is preserved in CHANGELOG.md, per-release
SESSION_REPORTs, or `docs/roadmap/ROADMAP.md`.

## What did NOT ship

- **Pr.1 (PR_BODY.md draft).** Lead has the PR description text
  at `.pr/2026-05-02.md` (135 lines, 27 KB). Phase 4 of the
  PROMPT was canceled mid-execution per lead direction.
- **Tag creation.** Per project memory + PROMPT discipline:
  `git tag v5.30.0` waits for explicit lead approval.

## Carry-forward

Closes nothing structural. Inherits:

- **Tn.1** (link-and-run gate generalization to all 95 goldens
  via `test_llvm_link_all.py`) — now 2-release overdue per the
  v5.28.0 panel directive (Cobra Cb.New1 + Rattler Ra.Inf1
  convergent recommendation). Should be picked up in v5.31.0.
- **M.1** (`.h` vs `.c` header asymmetry recurrence; Pv.7-style
  structural gate) — Mamba v5.28.0.
- **A.1** (`check_carry_forward_freshness.py` gate) — Anaconda
  v5.28.0.
- **Ra.New1** (Stage2 teardown stdout-redirect SIGSEGV
  investigation) — Rattler v5.28.0.
- **Pv.8.B** (preemptive sweep of 11 same-shape sites in
  `tests/native/test_agent_scheduler.py`) — v5.29.0 deferral.
- **bump_version.py runtime rebuild** (new LOW, this release)
  — `bump_version.py` should `make build-rt` automatically so
  the next post-bump `verify_fixed_point.sh` is STRICT on the
  first cycle, not the second.

## Cadence

`scripts/check_cadence.py` GREEN (1 minor since v5.28.0; next
panel due v5.33.0).

## Files

- `PLAN.md` — pre-execution plan
- `PROMPT.md` — execution prompt (gitignored per project
  convention)
- `SESSION_REPORT.md` — this file
