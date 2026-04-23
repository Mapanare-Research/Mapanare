# v5.3.x Closeout Arc — Push panel aggregate from 9.30 to 9.5+

> Three focused releases clearing every MEDIUM carry-forward from the
> v5.3.0 panel. Same pattern as v4.121.0-v4.135.0 (15 releases, 8.21
> to 8.80) but much shorter because the items are smaller.

---

## Roadmap Table

| Release | Theme | Items | Expected Lift | Effort |
|---------|-------|-------|---------------|--------|
| **v5.3.1** | Quick-win closeout | Lint fix, Bo.15/16/17/14r, Stream-C, An.9r | +0.15–0.25 | **30 min** |
| **v5.3.2** | Restore fixed-point | In.1-stage2 (extend `clone_instr_for_inline` to 30+ instruction kinds) | +0.15–0.20 | **1–2 hrs** |
| **v5.3.3** | SPEC + docs polish | SPEC-pkg section, SPEC header bump, signal demo | +0.02–0.05 | **1–2 hrs** |
| **v5.4.0** | **RE-PANEL** | Measurement + 7 reviewers | Target: **9.5+** | **1 session** |

---

## Per-Reviewer Recovery Path

| Reviewer | v5.3.0 | What closes | Expected v5.4.0 |
|----------|--------|-------------|-----------------|
| **Rattler** (9.3) | In.1-stage2 regression | v5.3.2: extend cloner, restore fixed-point | **9.5–9.6** |
| **Viper** (9.7) | Stable | (Own.1 P2 is v5.x, not closing here) | **9.7** |
| **Anaconda** (8.9) | Lint RED, stream tests, An.9r | v5.3.1: lint + stream + opt test fix | **9.3–9.5** |
| **Cobra** (8.8) | Fixed-point BROKEN | v5.3.2: restore NEAR or STRICT | **9.1–9.3** |
| **Coral** (9.4) | SPEC-pkg, demo gap | v5.3.3: SPEC section + signal example | **9.5–9.6** |
| **Boa** (9.4) | Bo.15/16/17/14r docs | v5.3.1: accurate docs | **9.5–9.6** |
| **Mamba** (9.6) | Stream-C tests | v5.3.1: fix test init | **9.6–9.7** |
| **Aggregate** | **9.30** | — | **9.45–9.55** |

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
| Own.1 P2 | Close | **v5.5.0** (self-hosted drop-glue) |
| Sh.2 | Close | **v5.5.0** (closes with Own.1 P2) |
| Sh.4 | Close | **v5.6.0** (self-hosted async) |
| Sh.5 | Defer to v5.x feature track | — |
| Sh.6 | Close | **v5.7.0** (self-hosted tensor) |
| Sh.7 | Close | **v5.8.0** (with or-pattern fix — 66/66) |
| Gr.1 | Defer | — |

---

## Post-arc: v5.5–v5.8 goldens-to-66 sequel

The v5.3.x closeout + v5.4.0 re-panel arc targets the panel score
ceiling. A second arc (v5.5.0–v5.8.0) targets the **native goldens
ceiling** — currently stuck at 54/66 since v5.0.4.

| Release | Theme | Closes | Goldens |
|---------|-------|--------|---------|
| **v5.5.0** | Own.1 Phase 2 — self-hosted drop-glue | Sh.2 (11 tests) | 54 → 65 |
| **v5.6.0** | Self-hosted async | Sh.4 (5 tests) | (already in 65) |
| **v5.7.0** | Self-hosted tensor | Sh.6 (5 tests) | (already in 65) |
| **v5.8.0** | Closure-typed + or-pattern fix | Sh.7 + B (2 tests) | 65 → **66/66** |

Note on accounting: the 12-test gap at v5.3.2 includes overlaps
across Sh.2/Sh.4/Sh.6/Sh.7/B buckets from the v4.126.0 triage. A
fresh triage pass at v5.5.0 Phase 0 re-anchors the trajectory. See
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
