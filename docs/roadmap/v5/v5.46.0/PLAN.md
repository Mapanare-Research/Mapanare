# v5.46.0 — Lf.\* — v5.43.0 lowerer-bug closeout; ergonomic Result<T, E> API unblocked

**Status:** PLANNING
**Type:** Compiler / codegen correctness. Closes the three (or four,
pending Phase 0 scoping) v5.x lowerer bugs surfaced and worked
around at v5.43.0. After v5.46.0 the v5.43.0 distributed-agent
APIs that ship today as flat `(ok: Bool, value, err_kind: Int,
err_msg: String)` tuples can be refactored back to ergonomic
`Result<T, NetworkError>` shape — that ergonomic refactor is
v5.46.x scope, not v5.46.0.
**Breaking:** No, in the surface sense. **Yes, behavioral** —
code that exercised the buggy paths got either wrong values or
silent no-fire matches; v5.46.0 makes those paths produce the
correct values. CHANGELOG `### Fixed` for each.
**Prerequisite:** v5.45.0 shipped (tensor closeout arc). Lowerer
fixes were committed for "v5.43.x" at the v5.43.0 SESSION_REPORT
ship — escalates to HIGH at this slot if not landed.
**Estimated effort:** 2–3 sessions. Each bug is structurally
small (the v5.36.0 Js.0.B precedent was one ~10-LOC fix in
`_do_wrap_ok` + `_do_wrap_err`); the load-bearing risk is
STRICT 3-stage fixed point preservation across `mapanare/self/`
mirror.

---

## Why this exists

v5.43.0 Phase 3 wanted to ship the distributed-agent surface
with `Result<NodeHandle, NetworkError>` and friends. Three v5.x
lowerer bugs (and a fourth variant-name-collision finding from
v5.39.7) blocked that ergonomic shape; v5.43.0 documented all
three with falsifiability repros at `/tmp/diag_*.mn` and
shipped the user-side APIs in a flat-tuple form
(`(ok: Bool, value, err_kind: Int, err_msg: String)`) instead.

The structural argument for closing now, before the v5.47.0
panel:

1. **The v5.43.0 SESSION_REPORT explicitly escalates these
   to HIGH if not closed by v5.43.x.** We're at v5.46.0; the
   commitment slot has slipped.
2. **The flat-tuple workaround is documented as ugly.** v5.43.0
   PROMPT itself called the shape "less elegant than
   `Result<T, E>`." The v5.47.0 panel will read v5.43.0's
   distributed-agent surface and dock for ergonomic
   compromise unless Lf.\* lands and v5.46.x ergonomic
   refactor is on the docket.
3. **The Js.0.B class is a pattern, not an isolated bug.**
   v5.36.0 fixed one shape; v5.43.0 surfaced three more. Other
   v5.x callers may be silently corrupting Result tags
   wherever the Ok side is non-trivial. Closing the family
   before v6.0 borrow checker means the borrow checker has
   stable Result-shape invariants.
4. **STRICT 3-stage fixed point is at risk every release that
   touches `mapanare/lower.py`.** v5.45.0 already broke the
   "zero `mapanare/self/*.mn` source touches" streak for
   tensor work; doing another self-host mirror release
   immediately after v5.45.0 amortizes the audit cost.

---

## The bugs

(Ground truth: v5.43.0 SESSION_REPORT lines 161–202 +
`/tmp/diag_*.mn` repros captured at v5.43.0 ship.)

### Lf.1 — Result<COMPLEX_OK, COMPLEX_ERR> destructure tag corruption

**Symptom:** `Result<NodeHandle, NetworkError>` returned from
a function with `Err(NetworkError::Unauthorized)` destructures
to `Err` with tag=0 (`BadUrl`) at the call site, regardless of
which variant was actually constructed.

**Repro:** `/tmp/diag_node_listen.mn` (captured at v5.43.0).
Single Int → NodeHandle return-type swap flips kind 3
(correct) → kind 1 (broken).

**Root cause hypothesis** (from v5.43.0 SESSION_REPORT):
"v5.36.0 Js.0.B class — Result wrap-shape mismatch."
v5.36.0's Js.0.B fix in `mapanare/emit_llvm_text.py:5214 / :5223`
addressed `_do_wrap_ok` / `_do_wrap_err` hardcoding the
unfilled side as `ptr`. The v5.43.0 surface goes one level
deeper: when both Ok and Err sides are non-trivial structs,
*destructure* (not just wrap) corrupts the Err tag because the
Err variant struct's layout depends on the Ok struct's size at
the wrapper level.

**Likely fix site:** `mapanare/lower.py` Result destructure
path; mirror in `mapanare/self/lower.mn`. The v5.36.0 Js.0.B
fix is the structural precedent — same author line.

### Lf.2 — Variant rewrap corruption through match propagation

**Symptom:** `match Err(e) { da Err(e) }` propagation
(forwarding the same Err) corrupts the variant tag — same
underlying root cause as Lf.1 plus an additional rewrap step.
**Visible even when `Result<Int, NetworkError>`** (i.e., the
Ok side is trivial) if the rewrap happens.

**Repro:** synthesized from v5.43.0 SESSION_REPORT description;
exact repro file to be reconstructed in Phase 0.

**Root cause hypothesis:** The rewrap path emits
`extractvalue` from the inner Err aggregate then
`insertvalue` into a new outer Result aggregate. If the
inner-aggregate-shape and outer-aggregate-shape differ even
trivially (e.g., padding alignment), the tag bits land at the
wrong offset on the rewrap.

**Likely fix site:** Same lower.py Result-handling region as
Lf.1; the rewrap path is a sibling of the destructure path.

### Lf.3 — Nested 15+-arm match silent no-fire

**Symptom:** Nested match on a destructured `e` from outer
`Err(e)` silently fails to fire any inner arm when the inner
match has 15 or more arms. 3-arm and 10-arm matches in the
same syntactic position work; 15+-arm matches silently
fall through (no panic, no diagnostic — control flow just
exits the match).

**Repro:** v5.43.0 captured this with `NetworkError`'s 15
variants (`BadUrl`, `Timeout`, `RefusedConn`, ..., 12 more).
3-arm and 10-arm subsets of the same match worked.

**Root cause hypothesis:** The lowerer emits a `switch i64`
with N case arms. Above some threshold (likely 15 ≤ N < 16
boundary — possibly `i4`-vs-`i8` width selection in case
indexing, or a hardcoded array-size constant), the switch
dispatch fails to recognize valid case values.

**Likely fix site:** `mapanare/lower.py::lower_match`. May
also be `mapanare/emit_llvm_text.py` switch generation. Phase
0 must localize before edit.

### Lf.4 — Variant-name collision in match patterns

**Symptom:** When two enums in scope share a variant name
(e.g., `NetworkError::TransportLost` and
`RemoteExitReason::TransportLost`), match arms resolve
"TransportLost" to whichever variant the lowerer's name-only
disambiguator picks first — *regardless* of the subject's
type.

**v5.43.0 workaround:** Renamed `RemoteExitReason::TransportLost`
to `RemoteExitReason::RemoteUnreachable`. The v5.39.7
SESSION_REPORT also notes a sister case under different
naming.

**Root cause hypothesis:** Match-pattern resolution lookup is
by variant name across all in-scope enums, not by (subject
type, variant name). Single-line fix candidate; major impact
because the workaround forces awkward variant renames in
user code.

**Likely fix site:** `mapanare/semantic.py` (pattern
resolution) and/or `mapanare/lower.py` match-arm lowering. The
semantic checker should flag the ambiguity at typecheck time
before it reaches the lowerer.

**PHASE 0 SCOPE DECISION POINT:** Lf.4 may either bundle into
v5.46.0 (lower the workaround pressure on user code) or split
to v5.46.x (it's a sister bug-class, not strictly the v5.43.0
SESSION_REPORT's three named bugs). Recommendation: bundle if
Phase 0 audit shows the fix is tractable in ~30 LOC; split if
it requires deeper semantic-checker surgery.

---

## Goals

1. **Lf.0** — Phase 0 audit reconstructs/verifies all four
   `/tmp/diag_*.mn` repros at v5.45.0 HEAD; localizes each
   bug to specific lower.py / emit_llvm_text.py / semantic.py
   call sites; extends or revises the root-cause hypotheses
   above with ground-truth IR diff.
2. **Lf.1** — Result<COMPLEX_OK, COMPLEX_ERR> destructure
   produces correct Err tag; lock with regression test.
3. **Lf.2** — Variant rewrap through match propagation
   preserves variant tag; lock with regression test.
4. **Lf.3** — Nested 15+-arm match fires the correct inner
   arm; lock with regression test that includes 15-, 16-, and
   20-arm cases (and a regression for the working 3- and
   10-arm cases).
5. **Lf.4** *(scope-pending Phase 0)* — Match-pattern resolution
   uses (subject type, variant name) keying; bundles into
   v5.46.0 if ≤ 30 LOC, splits to v5.46.x otherwise.
6. **Lf.5** — Self-host mirror lands cleanly; STRICT 3-stage
   fixed point preserved.
7. **Lf.6** — Broader sweep: `grep -rn "Result<" mapanare/ stdlib/ examples/ tests/`
   for non-trivial-Ok Result usage that may have been silently
   corrupting; verify each works post-fix.
8. **Lf.7** — CHANGELOG `### Fixed` entries; CLAUDE.md release
   notes; SPEC sync; carry-forward update.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Lf.0** | HIGH | **Phase 0 audit + repro reconstruction.** Reconstruct `/tmp/diag_node_listen.mn` and synthesize repros for Lf.2, Lf.3, Lf.4. Run each through Python emitter; capture IR diff vs expected. Localize fix site per bug. Decide Lf.4 bundle/split. Output: `docs/roadmap/v5/v5.46.0/PRE_PHASE_AUDIT.md` with the 4 IR-level diagnoses. | 4h |
| **Lf.1** | HIGH | **Result<COMPLEX_OK, COMPLEX_ERR> destructure fix.** Edit `mapanare/lower.py` (and/or `mapanare/emit_llvm_text.py` per Phase 0 localization). Mirror in `mapanare/self/lower.mn`. Lock: regression test that compiles `Result<NodeHandle, NetworkError>` repro and asserts Err variant tag preserves. ~30–80 LOC fix + ~120 LOC test. | 4h |
| **Lf.2** | HIGH | **Variant rewrap fix.** Likely same fix region as Lf.1; may be a single fix that closes both. Phase 0 determines. Test: `match Err(e) { da Err(e) }` propagation preserves tag through 2- and 3-hop rewrap chains. ~30 LOC fix + ~80 LOC test. | 3h |
| **Lf.3** | HIGH | **Nested 15+-arm match dispatch fix.** Localize the threshold (lower.py switch generation vs emit_llvm_text switch gen). Test: parametrized over arm-count {3, 10, 15, 16, 20, 50}. ~50 LOC fix + ~100 LOC test. | 4h |
| **Lf.4** | MEDIUM (Phase 0 may promote) | **Variant-name collision in match.** Match-pattern resolution keys by (subject type, variant name). May surface as semantic-checker change, lower.py change, or both. Test: two enums with overlapping variant names; match on each compiles and dispatches correctly. Bundle if Phase 0 says ≤ 30 LOC; split otherwise. | 3–6h |
| **Lf.5** | HIGH (gate) | **Self-host mirror.** Lf.1 + Lf.2 + Lf.3 (+ Lf.4 if bundled) require `mapanare/self/lower.mn` and possibly `mapanare/self/emit_llvm.mn` mirror. Phase 0 confirms whether self-host stage1 itself exercises any of these patterns; if it does (e.g., in semantic.mn match arms), STRICT preservation requires careful mirror-edit ordering. Stage1 rebuild after each mirror edit. | 4h |
| **Lf.6** | MEDIUM | **Broader Result<T, E> sweep.** `grep -rn "Result<" mapanare/ stdlib/ examples/ tests/` and audit every non-trivial-Ok Result construction for Lf.1 silent-corruption symptoms. Document findings in SESSION_REPORT — most callers will be fine (work around the bug by accident); any caller that actually relies on the bug's wrong-value output is surfaced. | 2h |
| **Lf.7** | HIGH (gate) | **Test corpus.** Three new goldens (one per bug; +1 if Lf.4 bundled): `100_result_complex_destructure.mn`, `101_match_rewrap_propagation.mn`, `102_nested_15arm_match.mn`. Pytest harness `tests/llvm/test_lowerer_fixes.py` with falsifiability documented per case (revert + restore round-trip). Goldens 99/99 → 102/102 (or 99/99 + 1 for Lf.4 = 103/103). | 5h |
| **Lf.8** | MEDIUM | **Closeout artifacts.** CHANGELOG `### Fixed` per bug (potentially-behavior-changing — if user code happened to depend on the bug's wrong output, it now produces correct output; document explicitly per check_changelog_honesty); CLAUDE.md release-notes entry; SPEC sync to v5.46.0 cut; carry-forward delta updated to remove the three (or four) lowerer-bug carries from MEDIUM. | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.45.0 HEAD clean. Reconstruct or
  re-author each `/tmp/diag_*.mn` repro; capture IR for each;
  localize fix site per bug; decide Lf.4 bundle/split;
  audit `mapanare/self/` for affected patterns. Write
  `PRE_PHASE_AUDIT.md`.
- **Phase 1** — Lf.1 + Lf.2 (Result wrap-shape family). The
  v5.43.0 SESSION_REPORT hypothesized these share a root
  cause; Phase 0 confirms or splits. If shared, single fix
  closes both; if split, Lf.1 first, Lf.2 second.
- **Phase 2** — Lf.3 (nested 15+-arm match). Independent fix
  site; can land in parallel with Phase 1 or sequential.
- **Phase 3** — Lf.4 if bundled. (If split, deferred to
  v5.46.x.)
- **Phase 4** — Lf.5 self-host mirror. Stage1 rebuild after
  each mirror edit per the v5.45.0 Phase 5 ordering pattern.
- **Phase 5** — Lf.7 test corpus; falsifiability locked per
  bug (revert-and-restore round-trip documented in pytest
  module docstring).
- **Phase 6** — Lf.6 broader sweep audit.
- **Phase 7** — Lf.8 closeout artifacts; bump + verify;
  fixed-point STRICT check (mandatory rebuild stage1 between
  bump and verify per v5.31.0 lesson).

---

## Out of scope

- **Ergonomic refactor of v5.43.0 distributed-agent APIs**
  from flat-tuple to `Result<T, NetworkError>`. v5.46.x.
  Scoped separately because (a) it's a stdlib edit, not a
  compiler edit; (b) it changes public function signatures
  in `stdlib/agent/` which is a separate kind of change from
  fixing the codegen bugs that blocked the ergonomic shape.
- **Async heartbeat / auto-route MSG_CHILD_EXITED** from
  v5.43.0 Da.\* carry. Different bug class (fn-typed
  callbacks; agent-runtime threading); v5.43.x scope.
- **Generic `RemoteAgent<T>` with auto-`to_json`** from
  v5.43.0 carry. Blocked on Ai.1 `_specialize_fn` body-walk
  fix from v5.40.0; that's a separate bug-class. Tracked as
  v5.47.x or v6.0 PLAN input.
- **fs.mn `walk_dir` IR codegen** (from v5.40.0 carry). Latent
  bug in stdlib/fs.mn; small but separate. v5.46.x.
- **websocket.mn `str(byte)` decimal-stringification** (from
  v5.43.0). Latent bug in stdlib; v5.46.x.
- **Closeout panel.** v5.47.0.
- **v6.0 borrow checker.** Post-panel.

---

## Risk

1. **STRICT preservation.** v5.45.0 already broke the
   "zero `mapanare/self/*.mn` source touches" streak for
   tensor closeout. v5.46.0 likely needs another mirror —
   `mapanare/self/lower.mn` Result/match handling. If the
   self-host stage1 itself exercises any of the buggy
   patterns, the mirror-edit ordering matters. Mitigation:
   Phase 0 audits `mapanare/self/*.mn` for `Result<` usage
   with non-trivial-Ok and for matches with 15+ arms; if
   none, mirror edits are mechanical. If yes, careful
   ordering required.
2. **Phase 0 localization may surface the bugs are NOT in
   `mapanare/lower.py`.** The v5.43.0 hypothesis was the
   v5.36.0 Js.0.B precedent class — but Phase 0 may reveal
   the bug is in `mapanare/emit_llvm_text.py` IR generation
   instead. Mitigation: don't pre-commit to fix site;
   localize first via IR diff.
3. **Lf.4 bundle/split decision.** If Phase 0 surfaces Lf.4
   needs deeper semantic-checker surgery (>30 LOC), bundling
   it into v5.46.0 expands scope unsafely. Mitigation:
   explicit Phase 0 decision point with ≤30 LOC threshold;
   default to split.
4. **Bug behavior change.** Code that exercised the buggy
   paths got wrong values. v5.46.0 makes those paths produce
   correct values. If any user code (or stdlib code,
   especially v5.43.0 `stdlib/agent/`) actually relied on the
   wrong output, it silently breaks. Mitigation: Lf.6
   sweeps; CHANGELOG `### Fixed` flags potentially-behavior-
   changing per check_changelog_honesty; v5.43.0 stdlib code
   reviewed for accidental dependence.
5. **15-arm threshold may be a red herring.** Phase 0 may
   reveal the actual threshold is something else (16, 17,
   etc.) or that it's enum-size dependent (`NetworkError`
   has 15 variants; the bug may scale with variant count,
   not arm count). Mitigation: Phase 0 captures the
   threshold empirically before fix.
6. **Goldens 99/99 disturbance.** v5.45.0 ships goldens
   99/99 (96 + Ts.4's 3 new). Adding 3 more (or 4 with
   Lf.4) → 102/102 or 103/103. Should land cleanly; flag
   in checklist.
7. **Phase 0 PRE_PHASE_AUDIT premise errors.** v5.41.0,
   v5.43.0, and v5.44.0 all caught structural premise
   errors at Phase 0. Expect 1–2 here; v5.46.0 PLAN
   hypotheses are based on v5.43.0 SESSION_REPORT
   *descriptions*, not first-hand IR diagnosis. Mitigation:
   timebox Phase 0 to ~4h with explicit deviation-surfacing
   protocol.

---

## Success criteria

- ✅ All four `/tmp/diag_*.mn` repros (or reconstructed
  equivalents) compile and run with correct results.
- ✅ Lf.1: `Result<COMPLEX_OK, COMPLEX_ERR>` destructure
  preserves Err variant tag.
- ✅ Lf.2: `match Err(e) { da Err(e) }` rewrap preserves
  variant tag through 2- and 3-hop chains.
- ✅ Lf.3: Nested match with 15, 16, 20, 50 arms all
  fire correctly; 3 and 10 still work (regression).
- ✅ Lf.4 closed at v5.46.0 if bundled, OR explicitly
  scoped to v5.46.x with rationale.
- ✅ Self-host mirror lands; STRICT 3-stage fixed point
  preserved.
- ✅ Goldens at 102/102 or 103/103 (depending on Lf.4
  bundle).
- ✅ Lf.6 broader sweep documents any other Result<T, E>
  callers affected by the bugs.
- ✅ CHANGELOG `### Fixed` per bug.
- ✅ CLAUDE.md release-notes entry.
- ✅ SPEC.md header sync.
- ✅ `make ci-gates` GREEN; `make lint` clean.

---

## Carry-forward delta

**Closes:**
- The three v5.43.0 lowerer bugs (Lf.1, Lf.2, Lf.3) tracked
  as MEDIUM since v5.43.0 ship.
- Lf.4 variant-name collision (sister to v5.39.7) — closes
  if bundled, otherwise carried as v5.46.x.
- The v5.43.0 commitment: "v5.43.x picks up
  `Result<T, NetworkError>` ergonomics once the lowerer
  fixes land." v5.46.0 does the lowerer fixes; v5.46.x
  picks up the ergonomic refactor.

**Inherits to v5.46.x:**
- Ergonomic refactor of v5.43.0 distributed-agent APIs from
  flat tuple to `Result<T, NetworkError>` (now unblocked).
- fs.mn `walk_dir` IR codegen issue (v5.40.0 carry).
- websocket.mn `str(byte)` decimal-stringification (v5.43.0
  carry).
- Lf.4 if Phase 0 says split.

**Inherits to v5.47.0 closeout panel:**
- Aggregate state of all v5 carries; panel decides v6.0
  readiness.

**Inherits to v6.0 or later:**
- Borrow checker (the v6.0 thesis).
- Hard removal of `{}` (carry from v5.19.0).
- Multi-level alias analysis.
- Generic `RemoteAgent<T>` (blocked on Ai.1 `_specialize_fn`
  body-walk fix).

**Aggregate state entering v5.47.0:**
- Tensor closeout arc CLOSED (v5.45.0).
- Manifesto arc CLOSED (v5.43.0).
- Package-system runway CLOSED (v5.44.0).
- v5.43.0 lowerer-bug closeout CLOSED at v5.46.0.
- macOS notarization MEDIUM carry (from v5.33.0 Nu.2).
- Strict 3-stage fixed point preserved at v5.46.0's
  expected ~242k+ lines.
- v5.47.0 panel green-lights v6.0 (or doesn't).
