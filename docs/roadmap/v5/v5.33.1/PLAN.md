# v5.33.1 — Hd.\* — SPEC header drift hotfix

**Status:** PLANNING
**Type:** Docs-surface-only hotfix. Zero compiler / runtime / dispatch
edits. The single substantive deliverable is one prose edit in
`docs/SPEC.md` (lines 3–4 + a new sync block) plus the standard
Vb.\* mechanical bump.
**Breaking:** No.
**Prerequisite:** v5.33.0 shipped (Nu.\* native `mnc` in Linux + macOS
release tarballs).
**Estimated effort:** 30–60 min, single session.

---

## Why this exists

CI's `check_doc_freshness.py` gate (`make ci-gates`) failed with:

```
check_doc_freshness: 1 drift violation(s):
  - docs/SPEC.md: header references v5.30.* but VERSION is 5.33.0
    (lag of 3 minor versions; max tolerated is 2)
```

The gate landed at v5.24.0 Hy.2 with a 2-minor lag tolerance — wide
enough to absorb a panel + recovery-arc window without firing on
each release. v5.30.0's SPEC sync covered v5.28.0 → v5.30.0; the
v5.31.0 / v5.32.0 / v5.33.0 trio shipped without re-syncing the
header, and the third minor flips the gate hard.

This is the same drift class that capped multiple panels at
9.55–9.66 between v5.7.1 and v5.22.0. Hy.2 closed it
**structurally** so the next recurrence is caught in CI, not at the
panel. v5.33.1 is the gate doing its job.

**Aside — panel cadence is also overdue.** `check_cadence.py` is
warn-only and reports OVERDUE — 5 minor versions since v5.28.0
panel; per `.reviews/REVIEW_CADENCE.md` a panel was due at v5.33.0.
**v5.33.1 does not run the panel** — that's a multi-day full
7-reviewer cycle and would explode the scope. v5.33.1 closes the
hard gate (SPEC header) only; panel cadence remains warn-only and
is escalated in v5.34.0 PLAN as a HIGH carry-forward.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Hd.1** | HIGH (gate) | `docs/SPEC.md:3-4` header bumped: `**Version:** 5.30.0` → `5.33.1`; `synced to the v5.30.0 cut (2026-05-02)` → `synced to the v5.33.1 cut (<today>)`. | 5 min |
| **Hd.2** | HIGH | `docs/SPEC.md` new sync block at the top covering v5.31.0 (Bn.\* banner hotfix), v5.32.0 (Nw.\* native `mnc.exe` Windows SDK ZIP), v5.33.0 (Nu.\* native `mnc` Linux x86_64 + macOS arm64 tarballs), and v5.33.1 (this hotfix). Mirrors the existing "v5.28.0 → v5.30.0" block shape — 10–14 lines, declarative, lists what shipped and asserts "zero language features, zero new MIR ops, zero new IR shapes, zero new runtime functions". | 15 min |
| **Hd.3** | HIGH (gate) | Re-run `python3 scripts/check_doc_freshness.py` locally → exit 0. Re-run `make ci-gates` → all 9 sub-gates GREEN. | 5 min |
| **Vb.1** | MEDIUM | `python3 scripts/bump_version.py 5.33.1` — VERSION + 4 README badges (en/es/pt/zh-CN) + CHANGELOG stub `[5.33.1]`. | 5 min |
| **Vb.2** | MEDIUM | CHANGELOG.md `[5.33.1]` section — one-paragraph header (no `### Added` / `### Changed` / `### Fixed` subsections — there's nothing to add); structurally identical to v5.30.0's packaging-release entry but motivated by Hd.\* not Vb.\*. | 10 min |
| **Vb.3** | LOW | CLAUDE.md `## Most recent releases` v5.33.1 entry (~12–15 lines). Mirror v5.21.1 polish-release shape, not v5.29.0 fix-release shape. | 10 min |
| **Vb.4** | MEDIUM | Rebuild `mnc-stage1` (`python3 scripts/build_stage1.py`) so post-bump VERSION metadata embeds as `!"5.33.1"` in stage2 + stage3; verify_fixed_point.sh STRICT preserved. | 5 min |

**Total source delta:** ~35 lines edited in `docs/SPEC.md`, ~5 lines
in `CHANGELOG.md`, ~15 lines in `CLAUDE.md`, plus the mechanical
files `bump_version.py` touches. **Zero `mapanare/`,
`mapanare/self/`, `runtime/`, `tests/` edits.**

---

## Phase plan

- **Phase 0** — Pre-flight: confirm v5.33.0 HEAD clean; reproduce
  the `check_doc_freshness` failure locally to lock the failure
  shape before the fix.
- **Phase 1** — Hd.1 + Hd.2: edit `docs/SPEC.md` header + add sync
  block.
- **Phase 2** — Hd.3: re-run `check_doc_freshness` → GREEN; full
  `make ci-gates` → 9/9 GREEN.
- **Phase 3** — Vb.1 + Vb.2: bump VERSION 5.33.0 → 5.33.1 + write
  CHANGELOG entry.
- **Phase 4** — Vb.3: CLAUDE.md release-notes entry.
- **Phase 5** — Vb.4: rebuild stage1 + STRICT fixed-point
  verification.
- **Phase 6** — SESSION_REPORT + commit.

---

## Out of scope

- **Compiler edits.** Zero. STRICT 3-stage fixed point preserved by
  construction at v5.33.0's line count / 0 diff.
- **Runtime edits.** Zero.
- **MIR / IR / language surface changes.** Zero.
- **Panel run.** `check_cadence.py` warn-only OVERDUE is real and
  will keep firing; running the full 7-reviewer panel is a
  separate multi-day cycle. Escalated to v5.34.0 as a HIGH
  carry-forward (or its own dedicated v5.X.0 panel-run release).
- **Wider SPEC body refresh.** Hd.2's sync block summarizes what
  changed — it does not rewrite §sections. Wider prose
  verification is v6.0+ per `check_doc_freshness.py` docstring.
- **Tag promotion.** `git tag v5.33.1` waits for explicit lead
  approval per project memory.

---

## Risk

1. **`bump_version.py` regex misses a localized README badge.**
   Same risk as every prior Vb.\* release; the v5.23.0 RC.3 carry
   captured this once. Mitigation: eyeball the diff before
   committing; `check_doc_freshness.py` will catch any miss in CI.
2. **The new sync block introduces a syntactic claim that's
   factually wrong** (e.g., "v5.32.0 added a runtime function" —
   it didn't). Mitigation: cross-check against
   v5.31.0 / v5.32.0 / v5.33.0 SESSION_REPORTs while writing.
   Hd.2 must reflect what those reports say, not what feels
   right at first draft.
3. **Stage1 rebuild reveals a NEAR fixed point** because the
   pre-v5.33.1 stage1 binary still embeds `!"5.33.0"`. This is
   the v5.31.0 SESSION_REPORT's documented lesson — Phase 5
   rebuild is what makes the STRICT claim honest. If the rebuild
   is skipped, fixed-point shows a 4-line VERSION-placeholder
   NEAR diff and CI flags it.
4. **`check_doc_freshness` exposes a second drift not surfaced by
   the original CI failure.** The script reports all violations;
   if Phase 0's local re-run shows additional findings (goldens
   badge, fixed-point line-count consistency), close them in this
   release, not v5.33.2 — they're the same drift class.

---

## Success criteria

- ✅ `python3 scripts/check_doc_freshness.py` exit 0
- ✅ `make ci-gates` → 9/9 GREEN
- ✅ `make lint` clean
- ✅ STRICT 3-stage fixed point preserved (rebuild stage1 first)
- ✅ Goldens 95/95 (no test edits)
- ✅ VERSION = 5.33.1; READMEs (4 locales) badge synced;
  CHANGELOG entry written; CLAUDE.md release-notes entry added;
  SESSION_REPORT.md complete

---

## Carry-forward delta

**Closes:**
- `check_doc_freshness` SPEC-header lag violation. The structural
  gate fires next time the SPEC stays unsynced ≥3 minor versions.

**Does NOT close (deferred to v5.34.0 or later):**
- `check_cadence.py` OVERDUE warning — panel cadence is now 5
  minor versions overdue; full 7-reviewer panel is its own
  release. **Escalated to v5.34.0 as a HIGH carry-forward.**
- Tn.1 — already a HIGH carry-forward per v5.32.0 directive
  (5-release overdue heading into v5.34.0). v5.33.1 does not
  pick this up.
- macOS Developer ID notarization (MEDIUM, from v5.33.0 Nu.2's
  ad-hoc-signing shortcut).
- Other LOW carries: deferred Linux aarch64 / macOS x86_64
  tarballs from v5.33.0; named-tzdb (carry); etc.

**Aggregate state entering v5.34.0:** 1 HIGH (panel cadence —
escalated), 1 HIGH (Tn.1) / 2 MEDIUM (macOS notarization;
carry) / ~6 LOW.
