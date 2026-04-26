# v5.8.0 Panel — THE v5.3.1 → v5.7.1 ARC RE-PANEL

> Seven-reviewer panel. The **v5.3.1 → v5.7.1** arc
> (9 releases, all 5 v5.3.0 panel MEDIUMs closed, 4 Sh.* feature
> gaps closed, Own.1 Phase 2 closed, fixed-point restored, goldens
> 54/66 → 66/66) is the surface graded.
>
> **Aggregate: 9.66 / 10. Decision: Option A.**

**Panel date:** 2026-04-26
**Aggregate: 9.66 / 10**
**Grade distribution: 7 EXCEEDS / 0 MEETS / 0 NEEDS WORK**
**Decision rule applied: Option A — v5.8.0 is a clean production release**

---

## Verdict Table

| # | Reviewer | Domain | Verdict | Score | Δ vs v5.2.0 | Top findings |
|---|---|---|---|---:|---:|---|
| 1 | [Rattler](01-rattler.md) | LLVM IR correctness | **EXCEEDS** | **9.8** | +0.5 | In.1-stage2 closed (39 instr-kind handlers); fixed-point restored; Sh.4/6/7+B closed at root cause |
| 2 | [Viper](02-viper.md) | Memory safety | **EXCEEDS** | **9.9** | +0.2 | Own.1 P2 closed (28-panel item); Ve.1/2/3/4+Lk.1 all root-cause closures; Rt.04 correctly v6.0 |
| 3 | [Anaconda](03-anaconda.md) | CI / testing | **EXCEEDS** | **9.6** | +0.7 | Lint trio GREEN; 8 fails → 0; 5x flaky audit clean; 66/66 goldens; 66 new feature tests |
| 4 | [Cobra](04-cobra.md) | Bootstrap / self-hosted | **EXCEEDS** | **9.6** | +0.8 | Fixed-point NEAR restored; all 4 Sh.* + B closed; PARITY_GAPS.md ledger discipline holds |
| 5 | [Coral](05-coral.md) | Language design | **EXCEEDS** | **9.6** | +0.2 | SPEC §30 Pkg added; 27-release SPEC staleness window closed; demo gap closed |
| 6 | [Boa](06-boa.md) | Documentation / DX | **EXCEEDS** | **9.4** | +0.0 | All 4 v5.2.0 carry-forwards closed; new culebra contributor guide; **Bo.18 MEDIUM (README contradiction)** |
| 7 | [Mamba](07-mamba.md) | C runtime / performance | **EXCEEDS** | **9.7** | +0.1 | Stream-C closed; Mn/Rust 1.003× geomean; async coro pipeline TSan-clean |
| | **Aggregate** | — | — | **9.66** | **+0.36** | — |

Score trajectory: 6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 → 9.21 →
9.37 → 9.30 → **9.66** (highest in project panel history).

## What the arc delivered

- **5/5 MEDIUM carry-forwards from v5.3.0 panel closed**
  (Lint, Stream-C, In.1-stage2, Bo.15, Bo.16) at v5.3.1–v5.3.3.
- **All 4 Sh.* feature gaps closed**: Sh.4 async (v5.5.4–v5.5.7),
  Sh.6 tensor (v5.6.0–v5.6.3), Sh.7 closure-typed (v5.7.0), B
  or-pattern + identifier `None` (v5.7.0).
- **Goldens 54/66 → 66/66** — first 100 % native pass in project
  history.
- **Own.1 Phase 2 closed** (28-panel carry-forward) across
  v5.4.0–v5.4.4 + v5.6.4 (tensor drop-glue Rt.06).
- **v5.6.x memory-safety closeout**: Ve.1/Ve.2/Ve.3/Ve.4/Lk.1 all
  closed at structural root cause; Rt.04 correctly RESCOPED to v6.0.
- **Fixed-point: BROKEN → NEAR** restored (217,879-line stage2.ll
  byte-identical to stage3.ll modulo VERSION metadata).
- **Pytest 8 fails → 0 fails**, 5,445 → 5,618-5,620 passes.
- **Lint trio GREEN** at HEAD (black, ruff, mypy strict).
- **Mn/Rust geomean 1.17× → 1.003×** (essentially parity).
- **Mn/Python geomean 168× → 328.6×** (~2× faster than v5.3.0).
- **C hardening 3 fail → 3/3 PASS** (plain, ASan, TSan).

## Key concerns across reviewers

1. **Bo.18 (NEW MEDIUM)**: README lines 147-149 lead-in paragraph
   says fixed-point "restoration tracked at v5.3.2" while the
   "Native compiler" subsection at line 135 says "NEAR" — internal
   contradiction inside the same README. Same shape as the original
   Bo.15. Single-paragraph copy edit. Boa flagged.
2. **Rt.04 (MEDIUM, RESCOPED v6.0)**: Multi-level alias analysis —
   62_list_output baseline-gated at 13 obj / 346 B. Structural fix
   needs the borrow checker. Viper carry.
3. **Pe.1 (LOW)**: stage2.ll grew +80 % v5.3.0 → v5.8.0. Bounded by
   per-release budgets, but worth a v6.0 budget check. Mamba carry.
4. **v5.6.x fixed-point churn**: BROKEN → NEAR → broken-transiently
   → restored at v5.6.11. Self-caught, self-restored. Cobra/Rattler
   suggest tighter per-release fixed-point gate for v6.0.

## Evidence

- MEASUREMENTS.md — `docs/roadmap/v5/v5.8.0/MEASUREMENTS.md`
- PARITY_GAPS.md — `docs/roadmap/v5/PARITY_GAPS.md`
- PARITY_AUDIT.md — `docs/roadmap/v5/v5.8.0/PARITY_AUDIT.md`
- V5_DECISION.md — [V5_DECISION.md](V5_DECISION.md)
- Prior panel — `.reviews/v5.2.0/` (aggregate 9.30, Option A)
- Culebra baseline — `docs/roadmap/v5/v5.7.1/culebra/`
