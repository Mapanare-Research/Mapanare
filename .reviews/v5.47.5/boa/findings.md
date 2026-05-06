# Boa — v5.47.5 Closeout Panel Findings

**Reviewer axis:** Long-tail bug closure + carry-forward discipline
**Arc reviewed:** v5.31.0 → v5.47.0 (17 releases)
**Audit reference:** `.reviews/v5.47.5/PRE_PANEL_AUDIT.md`
**Prior-panel score:** 9.55 (v5.28.0 RE-PANEL — +0.55 recovery
from v5.22.0's 9.00 floor; largest single-panel Boa improvement
in project history)

---

## Summary

The v5.28.0 RE-PANEL graded my axis 9.55 after the largest
single-panel Boa improvement in project history (Bo.18r
3-consecutive-panel persistence finally structurally closed
through Hy.\* fixed-point gate work).

The v5.31-v5.47.0 arc tested the recovery substantively:

- **Tn.1 multi-release overrun** (escalated through v5.28.0
  → v5.29.0 → v5.32.0 → v5.33.0 directives; deadlined
  v5.35.0; bundled into v5.35.0 Sq.0 closeout)
- **Js.4 typed-serde latency** (v5.36.0 Js.4.B latent for
  4 releases v5.36 → v5.39; closed at v5.39.2 with
  link-and-run regression suite)
- **v5.43.0 lowerer-bug carry** (3 distinct symptoms; one
  ~30 LOC fix at v5.46.0 closed all three after Phase 0
  found one common root cause)
- **Lf.4 split discipline** (v5.46.0 PROMPT/PLAN had Lf.4
  bundled; Phase 0 measurement put it ≥50 LOC exceeding
  ≤30 LOC bundle threshold; cleanly split to v5.47.0 Cl.1)
- **Pre-panel hygiene cleanup** (v5.47.0 Cl.\* mirrored
  v5.28.0's H.\* pattern: drain LOW carries pre-panel-cut
  so docket is clean for reviewers)

**The discipline held.** Carry-forward closure rates per
release are visible in the SHIPPED/PARTIAL/DEFERRED matrix
(Cp.1 section 2). Across the arc, **17 v5.x deferred items
closed in scope** (per Cp.1 section 5(c) retired list).

---

## Per-category grades

### Tn.1 trajectory + closure

**Grade: EXCEEDS**

Tn.1 (95-golden link-and-run gate generalization)
escalated through 4 directives (v5.28.0 panel rec →
v5.29.0 carry → v5.32.0 PLAN → v5.33.0 PLAN with
DEADLINE-at-v5.35.0). Bundled into v5.35.0 Sq.0
ahead-of-deadline. **The escalation pattern worked**
— deadline framing forced the closure rather than
silently slipping. Closure was substantive (96/96 PASS
at HEAD in 8s on 32 workers, mirroring the v5.26.0
pattern at scale).

### Js.4 staged closure

**Grade: EXCEEDS**

Js.4.B latent for 4 releases is a substantive failure
(the original v5.36.0 test was compile-only). Closure
discipline at v5.39.1 → v5.39.7 was exemplary: one
TypeKind branch per release with documented invariant
decisions (externally-tagged for ENUM, string-key for
MAP, multi-payload as JSON array for ENUM). 8 sub-
releases produced 7 substantive fixes + 1 sub-release
(v5.39.0 Cr.0) preconditioning the emitter shortcut
bypass. **The v5.39.0 → v5.39.7 sequence is the model
for multi-bug closeout arcs.**

### v5.43.0 lowerer-bug closeout

**Grade: EXCEEDS**

Three distinct symptoms (Lf.1/Lf.2/Lf.3) had one common
root cause (Python bootstrap `Ok`/`Err` constructor
wrap-shape default missing the `current_fn.return_type`
consultation that v5.26.1 Eu.2 had added on the self-
host side). Phase 0 audit found this; v5.46.0 ~30 LOC
fix closed all three. **Three regressions, one fix —
the Phase 0 audit pattern at its cleanest.**

The Lf.5 no-op gate (self-host already correct) is the
honest framing — STRICT preserved trivially.

### Pre-panel hygiene cleanup (v5.47.0)

**Grade: EXCEEDS**

v5.47.0 Cl.\* mirrors v5.28.0's H.\* hygiene-ahead-of-
panel pattern. Cl.1 (Lf.4) closure across both Python
bootstrap AND self-host stage1 is the right discipline.
Cl.2 + Cl.3 honest splits to v5.47.1 (Phase 0
verified non-trivial).

### Carry-forward ledger discipline

**Grade: MEETS**

`.reviews/CARRY_FORWARD.md` updated through v5.27.0 at
v5.28.0 hygiene pass. Across the v5.31-v5.47.0 arc the
file's update protocol drifted again (last "Items
resolved" append covers v5.27.0 closures; v5.31-v5.47.0
closures NOT logged at HEAD). **This is a recurrence
of v5.28.0 H.6 (An.1-class) — process-discipline drift
on the canonical docket ledger.** Recommend a v5.47.x
patch refresh.

### Pre-existing-baseline-failure inventory

**Grade: MEETS**

3 pre-v5.46.0 baseline failures (`test_run_hello`,
`test_reshape_size_mismatch_aborts`,
`test_link_and_run[98_*/99_*]`) inventoried in v5.46.0 +
v5.47.0 SESSION_REPORTs. Re-inventoried each cycle —
same pattern as Anaconda's An.3.

---

## Findings

### Bo.0 — Tn.1 closure pattern (LOW, positive)

Multi-release escalation with explicit DEADLINE-at-vX.Y
shape forced the closure. Recommend the pattern is
codified for v6.0 (carries that escalate through 3+
releases get a hard deadline applied).

### Bo.1 — `.reviews/CARRY_FORWARD.md` drift (MEDIUM, fresh, recurring)

Same shape as v5.28.0 H.6 (An.1-class). The file's
"Update protocol" section states updates are mandatory
at every release; was not honored across v5.31-v5.47.0
arc. **Recommend v5.47.x patch:** append v5.31-v5.47.0
closure rows (mirror the v5.28.0 hygiene-pass shape).
Could also be folded into the v5.47.5 closeout deliverables
(Cp.4 V5_TO_V6_CARRY.md effectively replaces this file
for v6.0+, but the v5-era ledger should still be brought
current).

### Bo.2 — `tests/KNOWN_FAILURES.md` ledger missing (LOW, fresh)

(See Anaconda An.3 — convergent recommendation)
Three pre-existing baseline failures inventoried per-
release. Single source-of-truth ledger would prevent
re-inventory each panel cycle.

### Bo.3 — Lf.4 split discipline (LOW, positive)

v5.46.0 PROMPT/PLAN had Lf.4 bundled; Phase 0 LOC
measurement (≥50 LOC across `mapanare/semantic.py` +
`mapanare/lower.py`) exceeded ≤30 LOC bundle threshold.
Split to v5.47.0 Cl.1 was the right call. **Discipline
held.**

### Bo.4 — Cl.2 + Cl.3 honest splits to v5.47.1 (LOW, positive)

v5.47.0 PROMPT had pre-panel hygiene cleanup as a single
Cl.\* arc. Phase 0 measurement put Cl.2 (~400 LOC across
4 files + ~50 internal callers + test updates) and Cl.3
(receiver-side wrong-shape Result aggregate, different
fix-site from v5.46.0 constructor-side) both
structurally non-trivial. Split to v5.47.1 was the right
call. **The bundle-vs-split pattern is consistent across
the arc.**

### Bo.New1 — V5_TO_V6_CARRY.md as canonical successor (LOW, fresh)

`.reviews/CARRY_FORWARD.md` was the v5-era canonical
ledger. v5.47.5's V5_TO_V6_CARRY.md (Cp.4) effectively
replaces it for v6.0+. **Recommend v6.0 PLAN explicitly
adopt V5_TO_V6_CARRY.md as the new ledger** with
update-protocol mandatory at every v6.x release. The v5
era ledger should be marked CLOSED at v5.47.5.

### Bo.New2 — convergent-recommendation pattern (LOW, fresh, v6.0 input)

(See Anaconda An.4 + Rattler Ra.New1 — convergent
recommendation across 3 reviewer axes)

The pattern surfaced in v5.28.0 RE-PANEL (Cb.New1 +
Ra.Inf1 → v5.35.0 Sq.0 closure 4 releases later); now
re-surfaces in v5.47.5 across Anaconda + Rattler + Boa.
**Recommend explicit V5_DECISION.md "Followups" elevation**
as v6.0 process input.

---

## Carry-forward suggestions

For Cp.4 V5_TO_V6_CARRY.md:

- **(b) v5.47.x patch candidate:** `.reviews/CARRY_FORWARD.md`
  refresh with v5.31-v5.47.0 closures (Bo.1)
- **(b) v5.47.x patch candidate:** `tests/KNOWN_FAILURES.md`
  ledger (Bo.2)
- **(a) v6.0 PLAN input:** V5_TO_V6_CARRY.md adopted as
  canonical ledger going forward (Bo.New1)
- **(retain process input for v6.0):** convergent-
  recommendation pattern (Bo.New2)
- **(retain process input for v6.0):** multi-release
  escalation → DEADLINE pattern (Bo.0)

---

## Score

**9.65 / 10**

Up 0.10 from v5.28.0's 9.55 — driven by Tn.1 closure +
Js.4 staged-closure discipline + Lf.\* one-fix-three-
regressions + bundle-vs-split discipline holding across
17 releases. The 0.35 gap is the recurring CARRY_FORWARD.md
drift (Bo.1) being honest process-discipline debt, plus
KNOWN_FAILURES (Bo.2) being a small inventory gap.

## Recommendation

**PASS WITH NOTES**

v5 ships clean from the long-tail bug closure axis. The
"with notes" is Bo.1 — the canonical docket-ledger drift
should close at v5.47.x before v6.0 starts so the
v5-era ledger reflects v5-era reality.
