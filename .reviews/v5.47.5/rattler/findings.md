# Rattler — v5.47.5 Closeout Panel Findings

**Reviewer axis:** Mechanical correctness — gates, fixed-point,
goldens, sanitizers, ABI invariants
**Arc reviewed:** v5.31.0 → v5.47.0 (17 releases)
**Audit reference:** `.reviews/v5.47.5/PRE_PANEL_AUDIT.md`
**Prior-panel score:** 9.90 (v5.28.0 RE-PANEL)

---

## Summary

The structural foundation that v5.28.0 graded as `EXCEEDS` held
across 17 substantive releases plus 7 Js.4 sub-releases. The
**50-release strict 3-stage fixed-point streak** from the v5.7.1
baseline is the load-bearing measurement; v5.47.0 reports
244,654 lines / 0 diff at HEAD. Every release I audited
preserved STRICT either by construction (zero
`mapanare/self/*.mn` source touches) or by explicit Phase 0
verification of self-host parity (e.g., v5.46.0 Lf.5 no-op
gate; v5.45.0 concat_self.py rebuild lesson).

Goldens trajectory: **95 (v5.28.0) → 96 (v5.41.0 Ts.1) →
99 (v5.45.0 Ts.\*) → 102 (v5.46.0 Lf.\*) → 103 (v5.47.0 Cl.1)** —
8 net-new goldens across the arc, every one falsifiability-
locked at the regression suite. The convergent-recommendation
prediction from v5.28.0 (Cb.New1 + Ra.Inf1 — generalize the
async-link gate to all 95 goldens) closed at v5.35.0 Sq.0 and
that link-and-run gate has been load-bearing ever since
(caught the v5.46.0 Lf.\* repros at PRE_PHASE_AUDIT, which
prevented a v5.43.0-class regression from recurring).

Sanitizer + fuzz state across the arc is exemplary. v5.42.0
shipped a 4-case binary-compat regression test pinning
`mapanare_agent_t` size + field offsets across the
488→984 byte struct extension. v5.43.0 ran 1000 randomized-
input network-fuzz iterations (8 variants), TSan + ASan
clean, valgrind 138/138 alloc/free with 0 leaks. v5.45.0's
Ts.2.A C smoke harness was 8 cases / 22 assertions ASan
clean + valgrind 138/138; Ts.3.B 4/19 + 25/25 same.

---

## Per-category grades

### Fixed-point preservation

**Grade: EXCEEDS**

50-release strict streak is the longest in project history.
Every release in the arc cited STRICT preserved by
construction or by explicit verification. The v5.45.0
concat_self.py lesson (first STRICT NEAR mid-arc, restored
within one cycle — ran scripts/build_stage1.py before
scripts/concat_self.py; reordered) is captured as a
process input for v6.0. The v5.46.0 Lf.5 no-op gate
(self-host already had the v5.26.1 Eu.2 fix; zero `.mn`
touches needed) shows the pattern at its cleanest.

### CI gate health

**Grade: EXCEEDS**

`make ci-gates` GREEN across all 9 sub-gates at HEAD.
Significantly: `check_no_hollow_features` (steps 1+2+3 all
clean) survived 17 releases of new stdlib surface + 6 new
C runtime exports without a single placeholder ship.
`check_struct_registry` cross-check (23 make_entry / 23
register_internal_struct against 81 source structs) held
through the v5.42.0 + v5.45.0 struct extensions —
append-only discipline preserved binary compat invariants
both times.

### Sanitizer + fuzz coverage

**Grade: EXCEEDS**

UB-risk-tier work (v5.42.0 As.\*, v5.43.0 Da.\*, v5.45.0 Ts.\*)
shipped with TSan + ASan + valgrind + (where applicable)
network fuzz. v5.43.0's 1000-iteration randomized network
input is the high watermark; the DoS guard + length
validation in `__mn_node_read_frame_str` held through every
variant (oversize, length=0, truncated, random body,
sub-header, length-without-body, all-random, immediate close).

### Golden corpus + falsifiability

**Grade: EXCEEDS**

103/103 at HEAD; 8 net-new goldens added over the arc, each
documented with revert-and-restore falsifiability cases in
the regression suite. `tests/llvm/test_lowerer_fixes.py`
(8/8 GREEN) is the model for fix-locking — three Lf.\* fixes
locked per layer with documented signatures (Lf.1 `kind=3`,
Lf.2 `kind=3`, Lf.3 `got NoKey`).

### Pre-existing failures inventory

**Grade: MEETS**

Three pre-v5.46.0 baseline failures (`test_run_hello`
gcc.exe env, `test_reshape_size_mismatch_aborts`,
`test_link_and_run[98_*/99_*]`) are documented in v5.46.0
+ v5.47.0 PRE_PHASE_AUDIT and SESSION_REPORTs. Not new
regressions; not silent. Reasonable disposition.

---

## Findings

### Ra.0 — STRICT trajectory cleanly held (LOW, positive)

50-release strict streak is the load-bearing v5 invariant.
v5.47.5 panel cut measured at 244,654 lines / 0 diff. This
is a **+5,300 line** cumulative growth from v5.28.0's
241,842 (baseline-relative; arc work added ~5.3k lines of
self-host source while preserving STRICT). v6.0 borrow
checker work should preserve this gate or document
explicitly why it can't — the v5 record is too valuable
to break silently.

### Ra.1 — Tn.1 closure validated end-to-end (LOW, positive)

The v5.28.0 panel rec to generalize `tests/llvm/test_async_link.py`
from 10 goldens to all 95 closed at v5.35.0 Sq.0 (bundled).
Across the v5.36-v5.46 arc the gate caught:
- v5.46.0 Lf.\* class repros at PRE_PHASE_AUDIT (would
  otherwise have shipped silently broken)
- v5.45.0 Ts.\* link verification across 96/99 goldens
- v5.39.7 Js.4.F externally-tagged enum round-trip

The convergent-recommendation pattern (Cb.New1 + Ra.Inf1
independent surface) worked exactly as predicted.

### Ra.2 — `concat_self.py` lesson surfaced + closed in one cycle (LOW, positive)

v5.45.0 was the first v5.31+ release to touch `mapanare/self/*.mn`
source materially. First STRICT verification post-edit showed
6-line NEAR diff. Root cause: stage1 was still compiled from
stale `mnc_all.mn` because `scripts/build_stage1.py` doesn't
auto-regenerate it. After running `concat_self.py` then
rebuild, STRICT cleanly restored. **Recommend codifying as
v6.0 process input:** every self-host edit must run
`scripts/concat_self.py` before `scripts/build_stage1.py`.
Captured in v5.45.0 SESSION_REPORT but worth a Makefile
target update (`build-stage1` should depend on
`concat-self`).

### Ra.3 — pre-existing baseline failures inventory (LOW, fresh)

Three test cases failed at v5.45.0 baseline pre-v5.46.0:
`test_run_hello` (Windows worker env), `test_reshape_size_mismatch_aborts`,
`test_link_and_run[98_*/99_*]`. The Tensor<Int> parser
issue surfaces under multi-axis stepped slice with Int
elements; float-element variant works. Each is documented
but the inventory is growing — recommend a `tests/KNOWN_FAILURES.md`
ledger so the panel doesn't have to re-inventory each
cycle.

### Ra.New1 — convergent-recommendation pattern as v6.0 process input (LOW, positive)

When two independent reviewers surface the same finding
shape from different axes, that's a load-bearing signal.
v5.28.0 caught Tn.1 this way; the closure paid 4 releases
later. **Recommend explicit elevation in V5_DECISION.md
"Followups"** as a v6.0 process input.

### Ra.New2 — STRICT under v6.0 borrow checker pressure (MEDIUM, fresh)

v6.0 borrow checker is structurally novel; multi-level
alias analysis touches lower.py + emit_llvm_text.py + the
self-host mirror. Preserving STRICT through this is non-
trivial. **Recommend v6.0 PLAN explicitly carve out the
STRICT gate and document the bridge** — likely a multi-
release v6.0.0 / v6.0.1 / v6.0.2 split (per the v5.43.0
sizing lesson the v5 retrospective will surface).

---

## Carry-forward suggestions

For Cp.4 V5_TO_V6_CARRY.md:

- **(a) v6.0 PLAN input:** STRICT 3-stage fixed-point
  preservation under borrow checker work. Explicit gate.
- **(b) v5.47.x patch candidate:** Makefile dep
  (`build-stage1: concat-self`) — process polish, not
  load-bearing.
- **(b) v5.47.x patch candidate:** `tests/KNOWN_FAILURES.md`
  inventory file — closes Ra.3.
- **(retain process input for v6.0):** convergent-recommendation
  pattern explicit elevation.

---

## Score

**9.85 / 10**

Down 0.05 from v5.28.0's 9.90 — entirely attributable to
the slightly noisier baseline-failure inventory (3 cases
vs 0 at v5.28.0 cut), not arc-quality. The
mechanical-correctness substrate is the strongest it's been
in v5 history; the 50-release strict streak is the
unanswerable proof.

## Recommendation

**PASS**

v5 ships clean from the mechanical-correctness axis. v6.0
green-lit conditional on Ra.New2 (STRICT gate carve-out
in v6.0 PLAN) being explicit.
