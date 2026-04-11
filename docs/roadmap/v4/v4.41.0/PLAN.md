# Mapanare v4.41.0 — Arc 2 Panel Release (LSP Maturity Close)

> **Second 5-minor cadence panel since v4.31.0.** Arc 2 closes.
> Panel runs against a stable target with 4 releases of LSP work
> to grade.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.40.0
**Delta review:** No
**Full panel:** **YES** — 5-minor cadence
**Estimated work:** 1 sprint for the release + external panel run
**Theme:** Quiet close of Arc 2. Panel grades the LSP work.

---

## What the panel is grading

v4.37.0: Workspace index + go-to-definition + hover types
v4.38.0: Find-references + rename refactoring
v4.39.0: Completion (imports + types + field/method)
v4.40.0: Diagnostic streaming + VS Code extension polish

The arc-2 panel is specifically checking:
- Does cross-module go-to-definition actually work on the Mapanare self-hosted tree?
- Does rename correctly update all references atomically?
- Are completion rankings sensible?
- Do streamed diagnostics arrive within the debounce window?
- Is the VS Code extension publishable quality?

---

## Phase 1 — Pre-panel sweep

- [ ] Open the Mapanare self-hosted tree in VS Code with the v4.40.0 extension.
- [ ] Manually test each LSP capability:
  - Click through 20 cross-module function calls with go-to-def — all resolve
  - Hover over 20 expressions — types all visible and accurate
  - Find-references on a heavily-used stdlib function — all sites listed
  - Rename a small helper function that has ≤10 references — all updated, code still compiles
  - Type completion in a few `fn foo(x: )` positions — offerings sensible
  - Stream diagnostics on a file with deliberately-introduced errors — appear within debounce
- [ ] Any LSP bug found at this stage is closed in v4.41.0 before the panel runs.

## Phase 2 — Documentation polish

- [ ] `docs/reference.md` §Editor Integration — audit the arc-2 LSP content end-to-end.
- [ ] `docs/getting-started.md` — if the tutorial uses VS Code, update screenshots.
- [ ] README.md — LSP-related badges / links up to date.
- [ ] `docs/cookbook.md` §Editor Setup — new subsection if absent.

## Phase 3 — Measurement refresh

- [ ] `culebra summary mapanare/self/main.ll` — the self-hosted main.ll shouldn't change (no compiler work in Arc 2), so function/instruction counts should be near-identical to v4.36.0.
- [ ] LSP-specific metrics:
  - Workspace index build time on the self-hosted tree (target ≤500ms)
  - Hover response time (target ≤50ms)
  - Go-to-def response time (target ≤50ms)
  - Completion response time (target ≤100ms)
  - Rename time on a ≤10-ref symbol (target ≤1s)
- [ ] Write `docs/roadmap/v4/v4.41.0/MEASUREMENTS.md`.

## Phase 4 — LOW sweep

- [ ] Any LOW items from v4.36.0's ledger state that v4.37.0–v4.40.0 did not close (likely just cosmetic ones). Sweep now.
- [ ] `CARRY_FORWARD.md` updated.

## Phase 5 — Pre-panel audit

Same discipline as v4.36.0 Phase 5:
- [ ] Fact-check every v4.37.0-v4.40.0 SESSION_REPORT claim against file:line
- [ ] `PRE_PANEL_AUDIT.md` written at `.reviews/v4.41.0/PRE_PANEL_AUDIT.md`

## Phase 6 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.41.0. Arc being reviewed: Arc 2 (LSP maturity).
- [ ] `mkdir -p .reviews/v4.41.0/` + pre-populate with `culebra_summary.md`, `arc_journal.jsonl`, `MEASUREMENTS.md`, `LEDGER_AUDIT.md`, `PRE_PANEL_AUDIT.md`
- [ ] Spawn 7 reviewers in parallel. Each reads their v4.36.0 file first.
- [ ] Reviewers fact-check the arc 2 SESSION_REPORTs. Special focus:
  - **Boa (Python/DX)** — primary for LSP. Does the editor experience actually work? Would a real Python dev use this?
  - **Coral (Language Design)** — does the completion ranking reflect language semantics sensibly?
  - **Rattler / Anaconda / Cobra** — no compiler changes to scrutinize; they grade the lack of regressions in their domains.
  - **Viper / Mamba** — LSP is in-process Python; memory safety concerns are limited to the index data structures. Still check for leaks and lifetime issues.

## Phase 7 — Closeout

- [ ] Write `.reviews/v4.41.0/README.md` with verdict table + consensus.
- [ ] If panel returns PASS: Arc 2 officially closes. v4.42.0 opens Arc 3 (tensors).
- [ ] If panel returns NEEDS WORK: v4.42.0 is rescoped as a recovery close; Arc 3 slides.
- [ ] Standard release closeout.

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Manual LSP smoke test complete | `MANUAL_SMOKE_TEST.md` checked off |
| 2 | Documentation polish complete | `check_docs_drift.py` clean |
| 3 | LSP performance metrics recorded | `MEASUREMENTS.md` |
| 4 | LEDGER_AUDIT.md written | file exists |
| 5 | PRE_PANEL_AUDIT.md written | file exists |
| 6 | `.reviews/prompt.md` retargeted to v4.41.0 | diff |
| 7 | `.reviews/v4.41.0/` pre-populated | `ls` shows files |
| 8 | 7 reviewer files exist | 01-viper.md through 07-coral.md |
| 9 | `.reviews/v4.41.0/README.md` written | file exists |
| 10 | Panel verdict ≥ 9.0 with zero NEEDS WORK (target) | README.md |
| 11 | SESSION_REPORT written | file exists |

---

## What v4.41.0 does NOT do

- **New features.** Panel releases never ship new features.
- **Compiler changes.** Arc 2 was editor-tooling only; v4.41.0 doesn't touch compilers.
- **VS Code marketplace publish** (unless the lead decides it's time — not a release gate).

---

## Reference

- [`.reviews/REVIEW_CADENCE.md`](../../../../.reviews/REVIEW_CADENCE.md)
- [`v4.36.0/PLAN.md`](../v4.36.0/PLAN.md) — the arc 1 panel release (pattern to follow)
- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 2

---

## After v4.41.0

v4.42.0 opens **Arc 3 (tensor completeness)**. First release: tensor literal syntax + runtime primitive wiring.
