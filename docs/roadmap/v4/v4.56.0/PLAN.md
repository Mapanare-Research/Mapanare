# Mapanare v4.56.0 — Arc 5 Panel Release (Compiler Debt Drain Close)

> **Fifth 5-minor cadence panel.** Arc 5 closes. Panel grades the
> compiler debt drain from v4.52.0–v4.55.0 — four long-standing
> `CARRY_FORWARD.md` A-items resolved.

**Status:** DONE (2026-04-12)
**Session log:** Same session as v4.52.0-v4.55.0. Pre-panel audit verified all 4 closures. 7 reviewers spawned in parallel.
**Decisions taken:** 6 broken fixtures verified. const Path A checklist in PRE_PANEL_AUDIT.md.
**Breaking:** No
**Prerequisite:** v4.55.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** Debt drain arc closes. `const` finally real.

---

## Arc scope the panel grades

- v4.52.0: Self-hosted semantic wiring (A7 closed)
- v4.53.0: UNRESOLVED/ERROR split (A8 closed)
- v4.54.0: `emit_c.mn` decision (A9 closed, Path B)
- v4.55.0: `const` Path A — real `ConstDef` AST node

Panel-specific questions:
- Does the self-hosted semantic pass now catch broken programs? Show 3 broken fixtures that used to silently lower to garbage IR and now produce rustc-quality errors.
- Does UNRESOLVED/ERROR suppress cascading correctly? The v4.31.0 panel's hypothesis was that the self-hosted side had no error suppression. Verify.
- Is the v4.54.0 Path B decision defensible? Does anyone miss `emit_c.mn`?
- Is `const` finally real? Can `const N: Int = 3; let a: Tensor<Float>[N, N] = ...` compile correctly?
- **Most importantly:** are the v4.33.0 `?` operator and v4.34.0 match features now also *checked* by the self-hosted semantic (not just the Python one)?

---

## Phase 1 — Pre-panel sweep

- [ ] Build `mnc-stage1` with the full v4.52.0-v4.55.0 stack.
- [ ] Run a "broken fixtures" suite:
  - File with type mismatch → expect exit 1 + rustc-quality error
  - File with undefined symbol → expect exit 1 + single error (no cascade)
  - File with non-exhaustive match → expect exit 1 + witness pattern
  - File with `?` in non-Result function → expect exit 1
  - File with assignment to `const` → expect exit 1
  - File with `const` initializer that's not constant → expect exit 1
- [ ] All 6 should produce loud, honest errors. If any silently lowers, that's a Phase 1 bug and gets fixed before the panel.

## Phase 2 — Documentation polish

- [ ] `docs/SPEC.md` — `const` section, UNRESOLVED/ERROR pass info, self-hosted compile path description
- [ ] `docs/cookbook.md` — `const`-for-tensor-shape example
- [ ] `docs/reference.md` — semantic pass is now on the self-hosted path; reflect this in architecture diagrams

## Phase 3 — Measurement refresh

- [ ] `culebra summary mapanare/self/main.ll` — with the wired semantic pass, main.ll may include more symbol-table data but the lowering is unchanged. Verify.
- [ ] Self-hosted semantic pass time on `mnc_all.mn` — target < 2s (15k lines)
- [ ] Compile-time constant folding depth handled correctly — stress test with 10-deep constant chain
- [ ] `MEASUREMENTS.md` written

## Phase 4 — LOW sweep + pre-panel audit

- [ ] Any LOW items from v4.51.0 ledger
- [ ] Fact-check v4.52.0-v4.55.0 SESSION_REPORT claims
- [ ] `PRE_PANEL_AUDIT.md`

## Phase 5 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.56.0. Arc: Arc 5 (compiler debt drain).
- [ ] `mkdir -p .reviews/v4.56.0/` + pre-populate
- [ ] Spawn 7 reviewers. Special focus:
  - **Anaconda (toolchain)** — primary. The semantic pass wiring is her domain; she flagged A7 in v4.26.0 as CRITICAL.
  - **Coral (language design)** — the `const` closure is hers. v4.26.0 CRITICAL is finally, really, done.
  - **Rattler (LLVM)** — the lowering didn't change, but tensor shape substitution via const is new; verify IR quality.
  - **Viper (memory safety)** — UNRESOLVED/ERROR suppression is a type-system soundness check; grade it.

## Phase 6 — Closeout

- [ ] `.reviews/v4.56.0/README.md` written
- [ ] If PASS: arc 5 closes. v4.57.0 opens arc 6 (deprecation + deletion).
- [ ] If NEEDS WORK: recovery protocol; arc 6 slides.
- [ ] Standard release closeout.

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Broken fixtures suite all produce rustc-quality errors | Phase 1 log |
| 2 | Documentation polish complete | `check_docs_drift.py` |
| 3 | Metrics recorded | `MEASUREMENTS.md` |
| 4 | `LEDGER_AUDIT.md` | file exists |
| 5 | `PRE_PANEL_AUDIT.md` | file exists |
| 6 | `.reviews/prompt.md` retargeted | diff |
| 7 | `.reviews/v4.56.0/` pre-populated | `ls` |
| 8 | 7 reviewer files exist | listed |
| 9 | `.reviews/v4.56.0/README.md` written | file exists |
| 10 | Panel verdict ≥ 9.0 with zero NEEDS WORK (target) | README.md |
| 11 | SESSION_REPORT written | file exists |

---

## What v4.56.0 does NOT do

- **New features.** Panel release.
- **Additional A-items.** A1 (await) is arcs 8+9; A2 (DWARF) is arc 7; A3/A4 (Python emitter, llvmlite) are arc 6; A5/A6 are not in scope of this plan.

---

## Reference

- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 5

---

## After v4.56.0

v4.57.0 opens **Arc 6 (deprecation and deletion)** — Python emitter and llvmlite JIT get warnings first, then delete.
