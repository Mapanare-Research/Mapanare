# v5.x Arc — Closeout + Feature Parity + Re-Panel (target 9.7+)

> Three closeout releases clearing MEDIUM carry-forwards, then four
> feature-parity releases closing all Sh.* gaps and driving goldens to
> 66/66, then a final polish + re-panel. Features first, panel last —
> one panel instead of two.

---

## Roadmap Table

| Release | Theme | Items | Expected Lift | Effort |
|---------|-------|-------|---------------|--------|
| **v5.3.1** | Quick-win closeout | Lint fix, Bo.15/16/17/14r, Stream-C, An.9r | +0.15–0.25 | **30 min** |
| **v5.3.2** | Restore fixed-point | In.1-stage2 (extend `clone_instr_for_inline` to 30+ instruction kinds) | +0.15–0.20 | **1–2 hrs** |
| **v5.3.3** | SPEC + docs polish | SPEC-pkg section, SPEC header bump, signal demo | +0.02–0.05 | **1–2 hrs** |
| **v5.4.0** | **Own.1 Phase 2 — drop-glue** | Move instruction, EmitState slots, 4 drop-glue helpers, Sh.2 (11 goldens) | 54→65/66 | **3–5 sessions** |
| **v5.5.0** | **Sh.4 — self-hosted async** | `block_on`/`await` + coroutine lowering | closes 5 async goldens | **2–3 sessions** |
| **v5.6.0** | **Sh.6 — self-hosted tensor** | `Tensor`/`Float` types + nested-array literal parser | closes 5 tensor goldens | **3–4 sessions** |
| **v5.7.0** | **Sh.7 + or-pattern — 66/66** | Closure-typed params + bootstrap or-pattern fix | 65→**66/66** | **1–2 sessions** |
| **v5.7.1** | SPEC + docs polish (pre-panel) | SPEC refresh, README 66/66, PARITY_GAPS audit, known_issues cleanup | +0.05–0.10 | **1–2 hrs** |
| **v5.8.0** | **RE-PANEL** | Measurement + 7 reviewers | Target: **9.7+** | **1 session** |

---

## Per-Reviewer Recovery Path (full arc → v5.8.0 panel)

| Reviewer | v5.3.0 | What closes (v5.3.1–v5.7.1) | Expected v5.8.0 |
|----------|--------|-------------|-----------------|
| **Rattler** (9.3) | In.1-stage2, goldens ceiling | v5.3.2: cloner fix; v5.4.0–v5.7.0: 66/66 goldens | **9.7–9.8** |
| **Viper** (9.7) | Own.1 Phase 2 (28 panels) | v5.4.0: drop-glue + Move tracking | **9.8–9.9** |
| **Anaconda** (8.9) | Lint RED, stream tests, goldens | v5.3.1: lint + stream; v5.4.0–v5.7.0: full test coverage | **9.5–9.7** |
| **Cobra** (8.8) | Fixed-point, self-hosted parity | v5.3.2: fixed-point; v5.4.0–v5.7.0: all Sh.* closed | **9.5–9.7** |
| **Coral** (9.4) | SPEC-pkg, demo gap, tensor/async | v5.3.3+v5.7.1: SPEC polish; v5.5.0+v5.6.0: async+tensor | **9.6–9.8** |
| **Boa** (9.4) | Bo.15/16/17/14r, 66/66 badge | v5.3.1: docs; v5.7.1: full refresh | **9.6–9.7** |
| **Mamba** (9.6) | Stream-C, async parity | v5.3.1: stream fix; v5.5.0: async parity | **9.7–9.8** |
| **Aggregate** | **9.30** | — | **9.65–9.75** |

---

## MEDIUM Items Closure Schedule

| ID | Release | Reviewer(s) | Description |
|----|---------|-------------|-------------|
| Lint-v5.2.0 | v5.3.1 | Anaconda | `black . && ruff check --fix .` |
| Bo.15 | v5.3.1 | Boa | README fixed-point claim accuracy |
| Bo.16 | v5.3.1 | Boa | known_issues.md: remove "no pkg mgr" |
| Stream-C | v5.3.1 | Mamba | Fix test init + audit Ge.1r fallback |
| In.1-stage2 | v5.3.2 | Rattler, Cobra, Anaconda | Extend `clone_instr_for_inline` to all 30+ instruction kinds |

**5 MEDIUM → 0 MEDIUM in 2 releases.**

---

## LOW Items Status

| ID | Disposition | Release |
|----|-------------|---------|
| Bo.17 | Close | v5.3.1 |
| Bo.14r | Close | v5.3.1 |
| An.9r | Close | v5.3.1 |
| SPEC-pkg | Close | v5.3.3 |
| Demo gap (signals) | Close | v5.3.3 |
| Li.1 | Defer to v5.x | — |
| Own.1 P2 | Close | **v5.4.0** (self-hosted drop-glue) |
| Sh.2 | Close | **v5.4.0** (closes with Own.1 P2) |
| Sh.4 | Close | **v5.5.0** (self-hosted async) |
| Sh.5 | Defer to v5.x feature track | — |
| Sh.6 | Close | **v5.6.0** (self-hosted tensor) |
| Sh.7 | Close | **v5.7.0** (with or-pattern fix — 66/66) |
| Gr.1 | Defer | — |

---

## Feature-parity arc: v5.4.0–v5.7.0 goldens-to-66

The v5.3.x closeout clears MEDIUM carry-forwards. The v5.4.0–v5.7.0
arc targets the **native goldens ceiling** — currently stuck at 54/66
since v5.0.4. Then v5.7.1 polishes and v5.8.0 re-panels with
everything closed.

| Release | Theme | Closes | Goldens |
|---------|-------|--------|---------|
| **v5.4.0** | Own.1 Phase 2 — self-hosted drop-glue | Sh.2 (11 tests) | 54 → 65 |
| **v5.5.0** | Self-hosted async | Sh.4 (5 tests) | (already in 65) |
| **v5.6.0** | Self-hosted tensor | Sh.6 (5 tests) | (already in 65) |
| **v5.7.0** | Closure-typed + or-pattern fix | Sh.7 + B (2 tests) | 65 → **66/66** |
| **v5.7.1** | SPEC + docs polish | (pre-panel refresh) | 66/66 |
| **v5.8.0** | **RE-PANEL** | All items closed | Target: **9.7+** |

Note on accounting: the 12-test gap at v5.3.2 includes overlaps
across Sh.2/Sh.4/Sh.6/Sh.7/B buckets from the v4.126.0 triage. A
fresh triage pass at v5.4.0 Phase 0 re-anchors the trajectory. See
each release's PLAN.md for details.

---

## What NOT to do

- **Do not add features** in v5.3.1–v5.3.3. This is a closeout arc.
- **Do not touch the package registry.** v5.2.0 shipped; improvements
  go to v5.4+ feature track.
- **Do not attempt Li.1 (LICM).** The fixpoint + preheader design is
  a multi-session project, not a quick fix.
- **Do not attempt Own.1 P2.** Move semantics are a v5.x/v6.0 scope.

---

## Success Criteria

The arc succeeds when:
1. All 5 MEDIUM items are closed
2. `black --check . && ruff check .` returns 0
3. `bash scripts/verify_fixed_point.sh --keep` reaches stage2.ll
   that passes `llvm-as` (NEAR or better)
4. `python3 -m pytest tests/native/test_c_hardening.py` → 0 failures
5. README does not make factual claims contradicted by measurements
6. v5.4.0 re-panel aggregate >= 9.5

---

## v5.6.x docket sequence (memory-safety closeout, post-arc)

Issued during the v5.6.x bug-closeout arc (after the v5.4.0–v5.7.0
feature arc was scoped). Tracked here for completeness:

| Release | Docket | Status |
|---|---|---|
| v5.6.5 | Ve.1 (parser overflow) | CLOSED |
| v5.6.6 | Rt.04 (multi-level alias) | RESCOPED → v6.0 |
| v5.6.7 | Ve.2 (lowerer empty-list) | PARTIAL (11/18) |
| v5.6.8 | Ve.3 (stage2 OOM) | INVESTIGATION |
| v5.6.9 | Ve.3 | CLOSED; Ve.4 OPENED |
| v5.6.10 | Ve.2 + struct_byte_size + culebra | PARTIAL; Lk.1 OPENED |
| v5.6.11 | Ve.4 | CLOSED |
| **v5.6.12** | **Lk.1 + Ve.2 residuals** | **CLOSED** |

Every v5.6.x docket is now resolved or appropriately deferred to
v6.0 (Rt.04 only). The v5.6.x closeout arc is genuinely complete
with no v6.0 deferrals from v5.6.x itself — the only v6.0 carry
is Rt.04 from v5.6.6, which has its own scoping rationale
(multi-level alias analysis is a borrow-checker concern).

After v5.6.12 ships, the trajectory rejoins the original arc:
v5.7.0 (Sh.7 + B → 66/66), v5.7.1 (docs polish), v5.8.0
(RE-PANEL).
