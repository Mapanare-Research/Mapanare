# v5.45.0 — Cp.\* — end-of-v5 closeout panel

**Status:** PLANNING
**Type:** Panel-only release. **Zero compiler edits. Zero runtime
edits. Zero `mapanare/self/*.mn` source edits.** No new features.
This is the structural pause before any v6.0 conversation begins.
**Breaking:** No.
**Prerequisite:** v5.44.0 shipped (package-aware imports +
stdlib extraction runway). All v5.31.0 → v5.44.0 releases
shipped: foundation arc (banner, native binaries x3), stdlib
arc (date/time, sqlite, JSON, HTTP, regex, crypto), manifesto
arc (`ask`, tensor closeout, supervision, distributed agents),
plus the package-system runway.
**Estimated effort:** 2–3 sessions. Pre-panel audit, 7-reviewer
panel, decision document, carry-forward to v6.0. Mirrors the shape
of v5.28.0 RE-PANEL.

---

## Why this exists

v5 has been a long, dense series. The user's directive was
explicit: **panels at the end of the series, not in the middle.**
v5.45.0 is that panel — the single closeout review of everything
v5.31.0 through v5.44.0 shipped, which transitively reviews the
entire v5 series since the last panel at v5.28.0 RE-PANEL.

Three decisions need to land here:

1. **Has the v5 thesis delivered?** The terseness arc, the
   stdlib gap-close, the manifesto items. Did they ship at the
   quality the project promised?
2. **Is v6.0 ready to start?** v6.0 is the borrow-checker arc.
   It requires the v5 stdlib to be solid (so users have
   somewhere to land) and the v5 type system to be
   well-understood (so the borrow checker has stable ground to
   build on).
3. **What carries forward to v6.0?** Every release through
   v5.44.0 deferred items to "v6.0 carry." Audit them; the ones
   still relevant become v6.0 PLAN inputs; the ones that don't
   become v5.45.x patches or get explicitly retired.

---

## Goals

1. **Cp.1** — Pre-panel audit: enumerate every shipped item in
   v5.31.0 → v5.44.0; identify silent-RED gates if any (the
   v5.28.0 RE-PANEL caught 3 of these for v5.22.0).
2. **Cp.2** — 7-reviewer panel: Rattler, Viper, Anaconda, Cobra,
   Coral, Boa, Mamba (the standard v5 panel composition; see
   `.reviews/PANEL_AUDIT_TEMPLATE.md`).
3. **Cp.3** — Aggregate decision: Option A (v5 ships clean,
   ready for v6.0) / Option B (v5 ships with caveats; v6.0
   gated on v5.45.x patches) / Option C (recovery arc needed
   before v6.0).
4. **Cp.4** — Carry-forward ledger: v6.0 PLAN inputs from v5
   carries; explicit "retired" list for items no longer
   relevant.
5. **Cp.5** — v5 retrospective: what worked, what didn't, what
   to repeat in v6.0 process.
6. **Cp.6** — CLAUDE.md ledger update: prune the "Most recent
   releases" section; promote v5 closeout summary; archive
   per-release entries to roadmap-only.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Cp.1** | HIGH | **Pre-panel audit (`PRE_PANEL_AUDIT.md`).** Enumerate every numbered item that shipped in v5.31.0 → v5.44.0 (every Bn., Nw., Nu., Dt., Sq., Js., Ht., Re., Cr., Ai., Ts., As., Da., Ps. ID). For each: state at HEAD = SHIPPED / PARTIAL / DEFERRED. Cross-check CI gates: every gate in `make ci-gates` actually GREEN at HEAD (catches silent-RED). | 4h |
| **Cp.2** | HIGH (load-bearing) | **7-reviewer panel.** Use the existing `/code-review` skill. Each reviewer reads PRE_PANEL_AUDIT.md + relevant SESSION_REPORTs and produces `findings.md` with EXCEEDS / MEETS / NEEDS WORK grade per category, plus PASS / PASS WITH NOTES / FAIL recommendation. Standard v5 composition: Rattler (mechanical correctness), Viper (perf), Anaconda (process / test discipline), Cobra (architecture), Coral (UX / docs), Boa (long-tail bug closure), Mamba (security). | 6h (panel runs in parallel) |
| **Cp.3** | HIGH | **Decision document (`V5_DECISION.md`).** Aggregate panel scores; apply the v5-gate mechanical decision rule (mean ≥ 9.5 = Option A green-light; 9.0-9.5 = Option A with notes; <9.0 = Option B or C). Document the chosen path. v5.28.0 RE-PANEL hit 9.72 (Option A); v5.45.0 expectation is similar quality given the structural arc completion, but the panel decides, not the lead. | 2h |
| **Cp.4** | HIGH | **Carry-forward ledger (`V5_TO_V6_CARRY.md`).** Every "carry forward" line from v5.31.0+ PLANs becomes an entry. Categorize: (a) becomes v6.0 PLAN input (real work for v6.0), (b) becomes a v5.45.x patch candidate (small, doesn't need v6.0 scope), (c) retired (no longer relevant). Examples: `Tn.1` (95-golden link gate) — retire if v5.36.0 finally landed it, otherwise v5.45.x. macOS notarization — v5.45.x. Borrow checker — v6.0 PLAN input. Hard removal of `{}` — v6.0 PLAN input. | 3h |
| **Cp.5** | MEDIUM | **v5 retrospective (`V5_RETRO.md`).** What worked: structural fix discipline, panel cadence (when followed), strict fixed-point gate. What didn't: mid-arc panels causing rebumps, SDK-bundle scope creep at v5.12.0 (caught only at v5.31.0), the Tn.1 N-release overrun. What to bring to v6.0: tighter PLAN sizing (v5.43.0 was too big for one release; v6.0 borrow checker should split into Bc.1.0 / Bc.2.0 / Bc.3.0 sub-releases). ~1500 words. | 3h |
| **Cp.6** | MEDIUM | **CLAUDE.md ledger update.** Prune "Most recent releases" — keep only v5.43.0, v5.44.0, v5.45.0 explicit; archive v5.31.0 through v5.42.0 to a "v5 closeout summary" paragraph that references roadmap. Add a v5.45.0 closeout entry with panel score + Option chosen + v6.0 readiness statement. | 1h |
| **Cp.7** | MEDIUM | **`docs/roadmap/v5/CLOSEOUT_ARC.md` final update.** Existing file tracks the v5 closeout arc; v5.45.0 is the actual closeout. Final paragraph: "v5 closed at v5.45.0 with panel decision X. v6.0 PLAN draft begins at v6.0/PLAN.md per V5_TO_V6_CARRY.md inputs." | 30 min |
| **Cp.8** | HIGH (gate) | **Cadence-check + ci-gates GREEN at HEAD.** v5.45.0 is panel-only; the substantive gate is "everything that was supposed to ship in v5 actually shipped and stayed green." `make ci-gates` GREEN; `make lint` clean; goldens 95/95; STRICT 3-stage fixed point preserved. | 30 min |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.44.0 HEAD clean.
- **Phase 1** — Cp.1 PRE_PANEL_AUDIT.md (must precede panel —
  reviewers need the artifact).
- **Phase 2** — Cp.2 panel runs (parallel; ~6h wall but each
  reviewer is independent). Use `/code-review v5_45_closeout` to
  drive.
- **Phase 3** — Cp.3 V5_DECISION.md once findings land. Apply
  the mechanical decision rule.
- **Phase 4** — Cp.4 carry-forward ledger.
- **Phase 5** — Cp.5 retrospective; Cp.6 CLAUDE.md prune;
  Cp.7 CLOSEOUT_ARC update.
- **Phase 6** — Cp.8 ci-gates + bump.

---

## Out of scope

- **Compiler edits.** Panel-only by construction.
- **v6.0 PLAN drafting.** That happens in `docs/roadmap/v6/`
  after v5.45.0 ships and the carry-forward ledger is set;
  v5.45.0 produces the *inputs* to that PLAN, not the PLAN
  itself.
- **New features.** Anything that surfaces during panel as
  "needs work" routes to a v5.45.x patch or to v6.0, not to
  v5.45.0 itself.
- **Hard removal of `{}` syntax.** v6.0; soft deprecation since
  v5.19.0 holds for now.

---

## Risk

1. **Panel finds NEEDS WORK on a load-bearing item.** v5.28.0
   RE-PANEL caught Anaconda's 3 silent-RED CI gates. Panel can
   surprise. Mitigation: Cp.1 audit pre-empts most of this; if
   panel still flags something serious, Option B/C handles it
   (ship v5.45.x patches before v6.0 starts).
2. **Reviewers disagree sharply.** Panel has produced consistent
   results historically (mean ± 0.3 across 7 reviewers); larger
   spreads usually surface real ambiguity. Mitigation: spread
   ≥ 0.5 triggers a follow-up review round before deciding.
3. **The v5.28.0 9.72 ceiling.** v5.45.0 might score lower
   simply because v5.31.0–v5.44.0 covered more ambitious scope
   (manifesto arc) than the v5.23-v5.27 recovery arc. Lower
   score isn't necessarily a problem; it just means
   v5.45.x/v6.0 inherits more carry. Mitigation: judge against
   absolute decision rule, not ceiling-relative.
4. **Cadence drift.** v5.45.0 is the first panel since v5.28.0,
   covering 14 substantive releases. The cadence-check gate
   would have fired at v5.34.0+ if mid-arc panels were the
   policy; user explicitly directed otherwise. Mitigation:
   v5.45.0 PLAN documents the deliberate cadence choice up
   front so the panel doesn't dock for it.

---

## Success criteria

- ✅ PRE_PANEL_AUDIT.md complete, all v5.31-v5.44 items
  classified.
- ✅ 7 reviewer findings.md files in
  `.reviews/v5.45.0/<reviewer>/findings.md`.
- ✅ V5_DECISION.md with explicit Option A/B/C and aggregate
  score.
- ✅ V5_TO_V6_CARRY.md complete with v6.0 PLAN inputs ready.
- ✅ V5_RETRO.md captures lessons.
- ✅ CLAUDE.md pruned + v5 closeout entry added.
- ✅ Goldens 95/95.
- ✅ STRICT 3-stage fixed point preserved.
- ✅ `make ci-gates` GREEN; `make lint` clean.

---

## Carry-forward delta

**Closes:**
- v5 series. The longest-running major version arc in the
  project's history.

**Inherits to v6.0:**
- Whatever Cp.4 carry-forward ledger surfaces. Expected:
  borrow checker (the v6.0 thesis), hard removal of `{}`,
  multi-level alias analysis, view-aliasing safety
  (Ts.2 stopgap), any panel-surfaced "MEDIUM" that's a
  v6.0 scope item.

**Inherits to v5.45.x patches (if any):**
- Per panel findings; small structural items that don't need
  v6.0 scope.

**v5 series state at HEAD:**
- Foundation arc CLOSED (banner + 3 prebuilt binary releases).
- Stdlib gap-close arc CLOSED (date/time, sqlite, JSON, HTTP,
  regex, crypto).
- Manifesto arc CLOSED (`ask`, tensor closeout, supervision,
  distributed agents).
- Package-system runway CLOSED (installed packages compile as
  normal dependencies).
- Terseness arc CLOSED (since v5.27.0).
- Mb.\* arc CLOSED (since v5.29.0).
- Pv.\* arc CLOSED (since v5.32.0 / v5.33.0).
- v6.0 begins.
