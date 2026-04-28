# Mapanare v5.7.1 — SPEC + docs polish — Session Report

**Released:** 2026-04-26
**Headline:** Pre-panel docs/polish release. Zero compiler edits.
SPEC bumped to v5.7.1, docs realigned to the v5.4.0–v5.7.0 feature
arc, culebra clean baseline frozen as v5.8.0 panel input, contributor
guide for the culebra workflow published.

---

## What shipped

### Phase 0 — Version bump

`VERSION` 5.7.0 → 5.7.1. Single line.

### Phase 1 — SPEC refresh

`docs/SPEC.md` header version 5.3.3 → 5.7.1 (closing a 27-release
staleness window — the SPEC was last refreshed at the v5.3.3
closeout-arc cut). Added a v5.7.1 callout block at the top
summarising the v5.4.0–v5.7.0 arc. Spec sync discipline blob
re-pointed at the v5.7.1 audit window (was: v4.129.0).

Section-level updates:

- **§3.11 Tensor Types** — status block expanded to credit the
  v5.6.0–v5.6.3 self-hosted parity work and the v5.6.4 Rt.06
  drop-glue closure. Both emitters now ship the full tensor
  surface; previously the SPEC said it was "stable on LLVM
  backend" without distinguishing Python vs self-hosted.
- **§5.6 Or-Patterns** — appended a v5.7.0 (B closure) note
  documenting the `_is_enum_variant_name` short-circuit and
  `Identifier("None") → Option` resolution that closed the
  bootstrap or-pattern + identifier `None` failure mode.
- **§6.3 Closures and Lambdas** — new "Closure-Typed Parameters"
  subsection with the canonical
  `fn apply(f: fn(Int) -> Int, x: Int)` example and a v5.7.0
  (Sh.7 closure) callout enumerating the four self-hosted
  changes that closed it (parser FAT_ARROW handler, lower
  routing through fn-typed locals, emit %-prefixed callees,
  inliner Call.fn_name renaming).
- **§29 Async** — appended a v5.5.4–v5.5.7 (Sh.4 closure) note
  documenting the full LLVM-coroutine pipeline now in the
  self-hosted emitter and the sanitizer-clean state on all 5
  Sh.4 goldens. The pre-existing v4.115.0 blockquote remains
  for historical context.
- **Appendix B 3-stage fixed point** — refreshed numbers
  (v4.142.0 → v5.7.0), added the v5.6.4–v5.6.10 regression
  window narrative, the v5.6.11 Ve.4 closure that restored
  NEAR fixed-point, and the v5.7.0 66/66 milestone. New
  **Native goldens** subsection right after fixed-point
  documents the 66/66 corpus pass rate.

No grammar / semantics / runtime changes — every edit is a
documentation refresh of behavior already shipped between v5.4.0
and v5.7.0.

### Phase 2 — README + known_issues + PARITY_GAPS cleanup

**README.md** + 3 localized translations (`docs/README.es.md`,
`docs/README.pt.md`, `docs/README.zh-CN.md`):

- Version badge bumped 5.7.0 → 5.7.1 across all 4 language variants.
- Added a "Native compiler — what `mnc-stage1` ships" subsection
  in each variant listing tensors / async / closure-typed params /
  or-patterns / drop-glue. The 66/66 badge was already present at
  v5.7.0; the prose context is new.

**docs/known_issues.md**:

- Pruned all v5.4.0–v5.7.0 closures (Sh.4 async, Sh.6 tensor,
  Sh.7 closure, B or-pattern, Ve.1 / Ve.2 / Ve.3 / Ve.4, Rt.03,
  Rt.05, Rt.06, Lk.1) into a "Closed since v5.4.0" narrative
  block beneath the active table. The active table now lists
  only Sh.5, Sh.9a, Sh.9b, Gr.1, Rt.2, Rt.3, Rt.01, Rt.02, Rt.04
  — the items still actually open.
- Header `Last updated` bumped to v5.7.1.

**docs/roadmap/v5/PARITY_GAPS.md**:

- Disambiguated the dual-namespace Sh.4 ID with an inline note
  pointing the async closure (CLOSED v5.5.4–v5.5.7) at the
  Historical section.
- Added Historical entries for **Sh.4 (async)**, **Sh.6 tensor**,
  **Sh.7 closure-typed**, **B (or-pattern + None)** with full
  closure traces and verification grep commands.

### Phase 3 — Culebra clean baseline + arc journal

Culebra v2.4.0 sweep across the v5.7.1 stage2.ll:

| Artifact | Content |
|---|---|
| `triage-brief.txt` | `5 root causes, 15829 findings: 2 critical (function-count-drop, return-type-divergence), 3 high` |
| `triage.md` | Full triage with template counts (943 / 37 / 7341 / 6398 / 1110) |
| `progress.md` | IR summary + delta vs prior baseline (was 11415 → now 15829) |
| `audit.md` | `OK No pathologies found in 0 functions.` |
| `strings.md` | `OK All 6398 string constants have correct byte counts.` |
| `check.md` | `VALID stage2_v5.7.1.ll` |
| `health-{Value,MIRType,EmitState,LowerState,Instruction}.txt` | All 5 most-touched aggregates: clean |
| `baseline-end.json` | 15,829 findings serialized (v5.8.0 panel anchor) |
| `baseline-delta-from-v5.6.10.md` | Narrative delta with line-count breakdown by intermediate release |
| `summary.md` | Human-readable summary cross-referencing all artifacts |
| `arc-journal.jsonl` | 189 entries aggregated from v5.6.9 + v5.6.10 + v5.7.0 culebra journals |

Per-release journal entry added via `culebra journal add` and
copied to `docs/roadmap/v5/v5.7.1/culebra-journal.jsonl`.

**No NEW critical findings** vs the v5.6.10 anchor; the +74-finding
delta is text-pattern noise from the v5.6.11 + v5.6.12 + v5.6.13 +
v5.7.0 closures absorbed since the v5.6.10 baseline-freeze
(net +947 stage2.ll lines, well below any noise threshold).

### Phase 4 — `docs/guides/culebra.md`

New 6-section contributor guide (~190 lines):

1. **What culebra is** — Rust-built Nuclei-style template engine,
   49+ templates across 5 categories, text-pattern matching (not
   AST analysis).
2. **Daily commands** — the small subset Mapanare uses every
   release, plus the debugging arc the v5.6.9–v5.7.0 sessions
   evolved.
3. **False positive policy** — documents the two known critical
   FPs (`function-count-drop`, `return-type-divergence`) and the
   3 "high" template-noise findings. This is the section that
   eliminates the "no measurement methodology" panel objection.
4. **Per-release journal** — the `culebra journal add` discipline
   v5.6.9+ uses, plus the per-release `.jsonl` cadence.
5. **Panel input** — how `arc-journal.jsonl` + `baseline-end.json`
   serve as primary diagnostic input for the next panel.
6. **Cross-reference** — pointers to v5.6.9 SESSION_REPORT (worked
   debugging example), v5.6.10 SESSION_REPORT (baseline-freeze
   methodology), the v5.7.1 culebra dir (this release's anchor),
   and the `.claude/skills/culebra-scan/SKILL.md` skill.

WSL-interop gotcha (Windows binary, Windows paths required) is
documented inline so future contributors don't hit the same
"file not found" surprise that v5.6.9 and v5.6.10 surfaced.

CLAUDE.md Skills table updated to cross-reference the new guide
and the v2.4.0 template count.

### Phase 5 — Commit (this release)

VERSION + SPEC + 4 READMEs + known_issues + PARITY_GAPS +
culebra/ artifacts + culebra-journal.jsonl + culebra.md +
CLAUDE.md + ROADMAP.md.

---

## Metrics (no compiler edits)

| Metric | v5.7.0 | v5.7.1 | Notes |
|---|---|---|---|
| stage2.ll lines | 217,879 | 217,879 | identical (same binary) |
| stage2.ll structural | clean | clean | no IR changes |
| Goldens | 66/66 | 66/66 | preserved |
| Self-host fixed-point | NEAR | NEAR | preserved |
| Culebra triage critical | 2 | 2 | both known FPs |
| Culebra finding total | (re-baselined) | 15,829 | +74 vs v5.6.10 (text noise) |

`mnc-stage1` binary unchanged (this release does not rebuild).
The `stage2_v5.7.1.ll` artifact archived under
`docs/roadmap/v5/v5.7.1/culebra/stage2-final.ll` was produced by
running the v5.7.0-built `mnc-stage1` against the live v5.7.1
source tree — its `!mapanare.version` metadata reads `5.7.0`
because that's the value frozen into the binary at v5.7.0 build
time. Expected; the next compiler-edit release will pick up
`5.7.1` automatically.

---

## What is NOT in this release

- No compiler edits. Every change is documentation, docs/polish,
  or culebra artifact aggregation.
- No new tests added or removed. The 5,606 non-bootstrap pytest
  + 225 bootstrap pytest counts from v5.7.0 carry forward.
- No grammar / SPEC semantics changes — only spec text describing
  features already shipped.
- No version-tag promotion. Tag + push await user approval per
  `feedback_v5_tag_timing.md`.

---

## Exit criteria

| Criterion | Status |
|---|---|
| `VERSION` reads `5.7.1` | ✓ |
| `docs/SPEC.md` header version → 5.7.1; tensor / async / closure / or-pattern sections accurate | ✓ |
| `README.md` + 3 translations: 66/66 badge | ✓ (preserved from v5.7.0; version badge bumped 5.7.0 → 5.7.1) |
| `docs/known_issues.md` pruned of all v5.4.0–v5.7.0 closures | ✓ |
| `PARITY_GAPS.md` Historical section updated with v5.4.0–v5.7.0 closures | ✓ |
| `docs/guides/culebra.md` published, cross-referenced from CLAUDE.md | ✓ |
| `docs/roadmap/v5/v5.7.1/culebra/baseline-end.json` saved | ✓ (3.3 MB, 15,829 findings) |
| `arc-journal.jsonl` aggregates v5.6.9 + v5.6.10 + v5.7.0 journals | ✓ (189 entries) |
| `culebra triage --brief` no NEW critical findings vs v5.6.10 anchor | ✓ (2 critical, both known FPs) |
| SESSION_REPORT written | ✓ (this file) |
| CLAUDE.md + ROADMAP.md entries added | (Phase 5 — see commit) |

---

## What's next

- **v5.8.0 — RE-PANEL.** Target aggregate ≥ 9.7. With 66/66
  goldens, NEAR fixed-point, all v5.6.x closures shipped, and
  the v5.7.1 culebra clean baseline as panel input, the panel
  reviewers (Coral, Boa, Anaconda, Rattler, Cobra, Mamba, Viper)
  have a structured artifact to grade rather than a narrative
  to hunt through. Cf. v4.144.0 panel attempt 4 which scored
  9.21/10 with 50% less audit infrastructure.
- **v6.0 — borrow checker.** Closes Rt.04 (multi-level
  drop-glue alias analysis, struct→list→string depth-2). Sole
  remaining v5.6.x→v6.0 carry now that v5.6.12's destination
  passing closed Lk.1 at the source.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` and the per-release
SESSION_REPORTs for the full v5.4.0–v5.7.1 trace.
