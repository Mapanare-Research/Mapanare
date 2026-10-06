# Anaconda — v5.47.5 Closeout Panel Findings

**Reviewer axis:** Process + test discipline + silent-RED detection
**Arc reviewed:** v5.31.0 → v5.47.0 (17 releases)
**Audit reference:** `.reviews/v5.47.5/PRE_PANEL_AUDIT.md`
**Prior-panel score:** 9.60 (v5.28.0 RE-PANEL — +1.20 recovery
from v5.22.0's 8.40 floor)

---

## Summary

The v5.28.0 RE-PANEL graded my axis 9.60 after a +1.20
recovery — driven by v5.23.0 RC.\* + v5.24.0 Hy.\* + v5.25.0
Pv.\* closing 3 silently-RED CI gates that v5.22.0 had
docked at -1.30. v5.47.5 panel cut audit (Cp.1, section 3)
is **silent-RED clean at HEAD** — every CI gate GREEN, no
hidden failures masked by stale config or deprecated
test paths.

The pattern that drove the v5.28.0 recovery is now
load-bearing process discipline: every release in the
v5.31-v5.47.0 arc shipped a PRE_PHASE_AUDIT.md that
surfaced PROMPT/PLAN-vs-HEAD-state mismatches *before*
implementation began. **Ten releases across the arc
documented Phase 0 deviations.** The most striking are:

- v5.41.0 (4 mismatches): grammar HEAD state, GpuTensor
  vs Tensor namespace, mapanare_tensor_t refcount/strides,
  realistic LOC budget
- v5.42.0 (5 deviations): naming drift, no system-message
  enum, no `mn_agent_exit*` API, restart_policy field
  semantics, golden count
- v5.45.0 (5 deviations): grammar HEAD, GpuTensor.reshape
  namespace, struct grow audit, +24 vs +16 bytes, IndexItem
  inclusive flag
- v5.44.0 (PROMPT premise error): "design a package
  system" treated as green-field; Phase 0 found 1037 LOC
  of complete pkg.py infrastructure already shipped
- v5.40.0 Ai.1+Ai.2 deferral: `_specialize_fn` body-walk
  fix gating reserved-keyword work

This is not "PROMPT/PLAN was bad"; it's PROMPT/PLAN
naturally drifts from HEAD as multi-week PROMPTs sit
ahead of fast-moving HEAD. **The PRE_PHASE_AUDIT pattern
is the structural fix for that drift.** Recommend
explicit promotion in v6.0 PLAN as mandatory at every
release.

---

## Per-category grades

### CI gate discipline

**Grade: EXCEEDS**

9/9 sub-gates GREEN at HEAD. `make ci-gates` clean across
the arc (verified via release-by-release SESSION_REPORT
audit). The v5.33.2 Cd.\* demotion of `check_cadence.py`
to informational REMINDER is a deliberate process choice
(captured in `feedback_no_forced_cadence_gates` user-memory
+ codified in PLAN: "panels at the end of an arc, not in
the middle"). This is the right shape — the gate
preserves visibility without blocking on a human-judgment
call.

### PRE_PHASE_AUDIT pattern adoption

**Grade: EXCEEDS**

Every substantive release v5.31.0 → v5.47.0 shipped a
PRE_PHASE_AUDIT (or equivalent Phase 0 audit section in
the SESSION_REPORT). The pattern caught:
- 4 mismatches at v5.41.0
- 5 deviations at v5.42.0 + v5.45.0 each
- PROMPT premise error at v5.44.0 (saved the release —
  green-field rewrite would have produced bad
  duplication of stdlib/pkg.py)
- Ai.1+Ai.2 structural blocker at v5.40.0 (saved the
  release — naming collision + nested-generic
  intrinsic substitution would have shipped subtly
  broken)
- Lf.5 no-op gate at v5.46.0 (preserved STRICT
  trivially)

**This pattern should be mandatory in v6.0.**

### Test discipline (link-and-run vs compile-only)

**Grade: EXCEEDS**

v5.36.0 Js.4.B was latent for 4 releases (v5.36 → v5.39)
because the original `tests/stdlib/test_struct_json.py`
was compile-only (validated IR text generation, never
linked). v5.39.2 added the link-and-run regression suite
(`tests/stdlib/test_struct_json_runtime.py`). **Lesson
codified across the arc:** every typed-serde / Result-
returning / runtime-shape-bearing surface gets a
link-and-run gate at first ship, not after the latent
SEGV surfaces.

The v5.46.0 Lf.\* + v5.47.0 Cl.1 pattern (8/8 GREEN test
suite locking each fix to a per-layer falsifiability
signature) is the canonical shape going forward.

### Honest CHANGELOG discipline

**Grade: EXCEEDS**

`check_changelog_honesty.py` GREEN across the arc.
Examples of correct `### Changed` (potentially breaking-
ish) discipline:
- v5.36.0 Js.1: RFC 8259 strict mode is not opt-out;
  documented in `### Changed`
- v5.39.6: Map<K,V> non-String K compile-time error
  documented as Changed
- v5.43.0 Cl.1 / Lf.4: variant-name collision behavior
  shift documented
- v5.43.0 RemoteExitReason::TransportLost rename
  documented

### Convergent-recommendation pattern

**Grade: EXCEEDS**

v5.28.0 caught Tn.1 via Cb.New1 + Ra.Inf1 independent
surface; closure paid at v5.35.0 Sq.0. The pattern
worked structurally (caught a real gap; gap was load-
bearing; closure was substantive). **Recommend explicit
elevation in V5_DECISION.md "Followups"** as v6.0
process input.

---

## Findings

### An.0 — silent-RED clean at HEAD (LOW, positive)

The v5.28.0 panel-cut process (full ci-gates audit
before reviewer dispatch) caught 3 silent-RED gates in
the v5.22.0 era. v5.47.5 panel-cut audit (Cp.1 section 3)
is silent-RED clean. **The pattern works; the discipline
held.**

### An.1 — PRE_PHASE_AUDIT promotion (MEDIUM, fresh, v6.0 input)

PRE_PHASE_AUDIT pattern caught 10+ load-bearing
PROMPT/PLAN-vs-HEAD mismatches across the arc. **Strong
recommendation:** v6.0 PLAN documents PRE_PHASE_AUDIT.md
as mandatory at every release. Without it, multi-week
PROMPT drafts will silently drift from HEAD; with it,
the drift is caught at Phase 0 cost (~1h) rather than
mid-implementation cost (~rebump).

### An.2 — link-and-run gate as default (LOW, positive)

v5.39.2 codified the lesson; v5.46.0 + v5.47.0 applied
it cleanly. **No fresh action needed**; pattern is
already practiced.

### An.3 — `tests/KNOWN_FAILURES.md` ledger (LOW, fresh)

Three pre-existing baseline failures (`test_run_hello`,
`test_reshape_size_mismatch_aborts`,
`test_link_and_run[98_*/99_*]`) are documented across
v5.45.0 / v5.46.0 / v5.47.0 SESSION_REPORTs. Re-inventoried
each cycle. **Recommend a single source-of-truth
`tests/KNOWN_FAILURES.md`** so cycle-N panel doesn't
re-derive what cycle-N-1 documented. Same Boa Bo.10-class
preventative as last-updated metadata gates.

### An.4 — convergent-recommendation pattern (LOW, fresh, v6.0 input)

v5.28.0's Cb.New1 + Ra.Inf1 → v5.35.0 Sq.0 paid 4
releases later. The pattern is reproducible. **Recommend
explicit V5_DECISION.md "Followups" elevation** as a v6.0
process input — when 2+ reviewers independently surface
the same finding shape, treat as load-bearing.

### An.New1 — v5.39.x staged closure as model (LOW, positive)

v5.39.0 → v5.39.7 closed Js.4.B/C/D/E/F across 8 sub-
releases, each with one TypeKind branch + documented
invariant decision (externally-tagged for ENUM,
string-key only for MAP, etc.). Bundling discipline
traded release count for falsifiability rigor — every
fix has a revert-and-restore test pair. **This shape
should be the default for multi-bug closeout arcs in
v6.0** (e.g., the borrow checker may surface as
similarly stair-step).

### An.New2 — bundle-vs-split decision discipline (LOW, positive)

Three load-bearing examples in the arc:
- v5.46.0 Lf.4 split to v5.47.0 (Phase 0 LOC measurement
  put it ≥50 LOC; exceeded ≤30 LOC bundle threshold)
- v5.41.0 Ts.2+Ts.3 split to v5.45.0 (option B scope
  audit; lead-approved)
- v5.47.0 Cl.2+Cl.3 split to v5.47.1 (Phase 0 verified
  structurally non-trivial)

Each split was Phase-0-driven, not retroactive. **The
discipline is healthy.**

---

## Carry-forward suggestions

For Cp.4 V5_TO_V6_CARRY.md:

- **(a) v6.0 PLAN input:** PRE_PHASE_AUDIT.md mandatory
  at every release (An.1)
- **(a) v6.0 PLAN input:** Convergent-recommendation
  pattern explicit in V5_DECISION followups (An.4)
- **(b) v5.47.x patch candidate:** `tests/KNOWN_FAILURES.md`
  ledger (An.3)
- **(retain process input for v6.0):** v5.39.x staged-
  closure shape as template for multi-bug closeout arcs
  (An.New1)

---

## Score

**9.75 / 10**

Up 0.15 from v5.28.0's 9.60 — driven by the consistent
PRE_PHASE_AUDIT adoption across all 17 releases (the
pattern that closed v5.22.0's silent-RED docks now lives
at v5.47.5 panel cut as the structural fix). The 0.25
remaining gap is process-polish (KNOWN_FAILURES ledger;
explicit pattern documentation).

## Recommendation

**PASS**

v5 ships clean from the process axis. v6.0 green-lit
conditional on PRE_PHASE_AUDIT.md being explicit-mandatory
in v6.0 PLAN.
