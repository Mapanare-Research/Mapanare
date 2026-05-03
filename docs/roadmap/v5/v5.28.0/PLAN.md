# v5.28.0 — RE-PANEL — recovery + prevention + Mb.* + Mc.* closeout

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.27.0 shipped (Mc.\* parity arc closed; Tk.\*
opened and closed in same release).
**Estimated effort:** 1 session for setup + panel runtime
(~3–4 hours including 7 reviewer agents).
**Arc context:** **Panel-only release.** The release identity is
the panel itself. Same posture as v5.22.0 RE-PANEL (which graded
v5.13.0 → v5.21.1 at 9.41/10) and v5.8.0 (which graded
v5.3.1 → v5.7.1 at 9.66/10).

---

## Why this exists

Six releases of work since v5.22.0 panel need an aggregate
review:

| Release | Codename | What it shipped |
|---|---|---|
| v5.23.0 | RC.\* | CI recovery + 4 HIGH closures |
| v5.23.1 | Mb.\* (V.9 + Te.5 leaks) | Memory hygiene |
| v5.23.2 | Te.3.B | Bootstrap brace-deprecation mirror |
| v5.24.0 | Hy.\* | Structural hygiene gates |
| v5.24.1 | Wd.\* | Wider docs cleanup (recovery arc closeout) |
| v5.25.0 | Pv.\* | CI prevention + retroactive bugfix close |
| v5.26.0 | Mb.7 | i64/i1 tag-emit codegen fix (Mb.\* closeout) |
| v5.27.0 | Mc.8/9 + Tk.1 | Formatter polish (Mc.\* closeout) |

**Cadence:** 6 minor versions since v5.22.0 panel. The v5.24.0
Hy.3 cadence-enforcement gate fired hard at v5.27.0 (5+ minor
threshold). v5.28.0 closes the cadence gap **1 minor late** —
acknowledged in the PLAN; the v5.27.0 formatter polish was the
wrong scope to bundle with a panel cycle, so the deliberate
slip is the correct trade-off.

**Zero compiler edits. Zero runtime edits. Zero
`mapanare/self/*.mn` source edits.** Strict 3-stage fixed
point preserved by construction at v5.27.0's line count.

---

## Goals

1. **Pn.1** Stage `.reviews/v5.28.0/` panel infrastructure:
   `PROMPT.md`, `PRE_PANEL_AUDIT.md`, `README.md` (panel
   index), per-reviewer subdirectories.
2. **Pn.2** Run pre-panel hygiene (H.\* findings) — every
   pre-flight finding must close at v5.28.0 HEAD before the
   panel runs. No "the panel will catch it" deferrals.
3. **Pn.3** 7-reviewer panel: Rattler / Viper / Anaconda /
   Cobra / Coral / Boa / Mamba (per v5.22.0 pattern).
4. **Pn.4** Aggregate decision: **Option A** (point-release
   health gate clears; no recovery cycle) vs **Option B**
   (recovery cycle opened, e.g. v5.29–v5.30).
5. **Pn.5** Aggregate target: **9.55–9.65** per v5.24.1
   SESSION_REPORT projection. Recovery from v5.22.0's
   9.41 floor.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Pn.1** | MEDIUM (process) | **Panel infrastructure stage.** Create `.reviews/v5.28.0/{README.md, PROMPT.md, PRE_PANEL_AUDIT.md}` plus 7 per-reviewer subdirectories. Each per-reviewer dir contains: `prompt.md` (reviewer-specific brief), `findings.md` (output template). PROMPT.md follows v5.22.0 shape — version range under review, decision criteria, scoring rubric. | 1h |
| **Pn.2** | HIGH (gate) | **Pre-panel H.\* hygiene.** Audit `.reviews/v5.28.0/PRE_PANEL_AUDIT.md` enumerates every H.\* finding (README freshness, SPEC header lag, localized README sync, SPEC corpus 100% colon-canonical, etc.). Each finding must close at v5.28.0 HEAD before panel runs. Same posture as v5.21.1 Mc.7 → v5.22.0 panel. | 1–2h |
| **Pn.3** | HIGH (panel) | **7-reviewer panel run.** Each reviewer agent (Rattler, Viper, Anaconda, Cobra, Coral, Boa, Mamba) gets the v5.23.0 → v5.27.0 release range, the prior-panel docket (v5.22.0), and the codebase HEAD. Each produces: aggregate score, per-arc findings, NEW HIGH/MEDIUM/LOW, "still open" carries from v5.22.0. | ~30 min wall-time / agent × 7 = ~3.5h compute |
| **Pn.4** | HIGH (decision) | **V5_DECISION.md.** Aggregate the 7 reviewer outputs. Option A criteria: 0 NEEDS WORK reviewers, ≥9.5 aggregate, no NEW HIGH that wasn't in the v5.22.0 docket. Option B otherwise. Document the decision + rationale in `.reviews/v5.28.0/V5_DECISION.md`. | 1h |
| **Pn.5** | LOW | **Carry-forward update.** `.reviews/CARRY_FORWARD.md` v5.23.0 → v5.28.0 arc append: every closed finding with resolving-release pointer; every still-open finding with re-anchor row. Mirror v5.21.1 H.10 shape. | 30 min |

---

## Phase plan

### Phase 0 — pre-flight verification (~1 day, may span sessions)

Pre-panel audit (Pn.2) is the load-bearing phase. Run before
any reviewer agent invokes. Format mirrors `.reviews/v5.22.0/
PRE_PANEL_AUDIT.md`:

```bash
# Must all pass at v5.28.0 HEAD before panel:
make ci-gates                # all sub-gates green
bash scripts/verify_fixed_point.sh   # strict 3-stage
pytest tests/ -q                     # full suite green
ls tests/golden/*.mn | wc -l         # 95 expected
python scripts/check_doc_freshness.py # version sync
python scripts/check_cadence.py       # cadence gate (will fire — expected)
```

The cadence gate firing is the *signal that v5.28.0 is the
correct release for the panel*, not a failure to close.

### Phase 1 — panel infrastructure (Pn.1)

Mechanical staging. Templates from `.reviews/v5.22.0/` minus
the v5.22.0-specific findings.

### Phase 2 — panel run (Pn.3)

Per reviewer:
1. Spawn the agent with the reviewer-specific prompt.
2. Agent reads CLAUDE.md, the 6 SESSION_REPORTs from v5.23.0 →
   v5.27.0, the v5.22.0 docket, the codebase HEAD.
3. Agent produces `findings.md` in their subdirectory.
4. (User reviews; agent does not commit.)

### Phase 3 — aggregation (Pn.4)

Read all 7 `findings.md` files. Compute aggregate. Write
`V5_DECISION.md` documenting Option A / B with rationale.

### Phase 4 — carry-forward (Pn.5)

Update `.reviews/CARRY_FORWARD.md`. If Option A: docket reset
to NEW finding set. If Option B: open recovery arc with
explicit version sequence.

---

## Out of scope

- **Feature work** — the release IS the panel.
- **Compiler edits, runtime edits, source edits** — zero,
  by construction. Same as v5.22.0 RE-PANEL.
- **Pre-emptive closure of v5.28.0-PANEL-anticipated findings**
  — anything that *might* surface in the panel must be left
  alone; closing-before-asking is the v5.7.1 → v5.8.0
  anti-pattern.

---

## Success criteria

- ✅ All 7 reviewer agents complete.
- ✅ Aggregate ≥ 9.55.
- ✅ 0 NEEDS WORK.
- ✅ No NEW HIGH that wasn't already on the v5.22.0 docket.
  (NEW MEDIUMs are expected and OK — that's the panel doing
  its job.)
- ✅ Cadence gate at HEAD shows GREEN immediately post-panel
  (gate honors the existence of `.reviews/v5.28.0/`).
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.
- ✅ `V5_DECISION.md` documents Option A or B with explicit
  reviewer-by-reviewer rationale.

---

## Risk

**The v5.22.0 panel scored 9.41/10 — Option A but with
−1.30 single-reviewer regression** (Anaconda). The recovery
arc (v5.23–v5.24) closed every Anaconda HIGH and MEDIUM, plus
the load-bearing Reg.1 / hollow-feature gate / docs-drift gate
silent-fail class. v5.25.0 added Pv.\* prevention. v5.26.0
closed Mb.\*. v5.27.0 closed Mc.\*. **There is no
known-open structural debt entering v5.28.0.** Risk is
limited to:

1. **NEW HIGH from a reviewer angle not anticipated.** Most
   likely surface: WSL-specific tooling drift if Pv.4 missed
   an edge case; WASM/Android sub-arcs if reviewers pull from
   v5.23–v5.27 not just v5.27.
2. **Cadence-gate slip framing.** v5.28.0 closes the cadence
   gap 1 minor late. A reviewer may flag this as process
   discipline. Mitigation: explicit acknowledgment in the
   PROMPT.md and PRE_PANEL_AUDIT.md.
3. **Mb.7's stage2/3 fixed-point risk** (per v5.26.0 PLAN
   risk #2) — if the codegen fix moved the line count
   baseline, a reviewer may flag the streak break. Mitigation:
   document the new baseline; a deliberate, one-time
   line-count delta is not a streak break in spirit.

---

## Carry-forward delta

Closes (panel grading):
- v5.23–v5.27 arc graded.
- Cadence gap closed (1 minor late, acknowledged).
- All Mb.\* / Mc.\* / Hy.\* / Pv.\* arcs closed entering
  next post-panel release.

Opens (depending on panel outcome):
- Option A: NEW finding set per reviewer batch. Next routine
  panel at v5.33.0 (5 minors out).
- Option B: Recovery arc explicit version sequence
  (e.g. v5.29.0 RC.\* parallel to v5.23.0).

Inherits to next panel:
- v6.0-rescoped: Rt.04 (multi-level alias), Te.3 hard removal
  of `{}`, stage2-binary teardown crash, single-line
  `if x: y` (rescoped from v5.14.0 promise).
