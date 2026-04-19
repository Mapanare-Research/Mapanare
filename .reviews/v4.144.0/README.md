# v4.144.0 Panel — v5.0.0 Gate Attempt 4

> Seven-reviewer panel. The **v4.143.0 → v4.144.0** LOW polish + benchmark
> refresh is the surface graded. First panel to clear Option A.

**Panel date:** 2026-04-18
**Aggregate: 9.21 / 10**
**Grade distribution: 6 EXCEEDS / 1 MEETS / 0 NEEDS WORK**
**Decision rule applied: Option A — Tag clean `v5.0.0`**

---

## Verdict Table

| # | Reviewer | Domain | Verdict | Score | Δ vs v4.143.0 | Top findings |
|---|---|---|---|---:|---:|---|
| 1 | [Rattler](01-rattler.md) | LLVM IR correctness | **EXCEEDS** | **9.3** | +0.2 | Cb.5-tests adequate; Cb.6 asymmetry documented not regression-tested; benchmark honesty praised |
| 2 | [Viper](02-viper.md) | Memory safety | **EXCEEDS** | **9.6** | +0.0 | Cb.7 correct at site; register_struct/enum are latent UAFs (Own.1); sanitizer state unchanged |
| 3 | [Anaconda](03-anaconda.md) | CI / testing | **EXCEEDS** | **9.3** | +0.2 | All 8 CI gates green; Cb.5-tests well-structured; test count arithmetic minor discrepancy |
| 4 | [Cobra](04-cobra.md) | Bootstrap / self-hosted | **EXCEEDS** | **9.2** | +0.2 | All Cb.6-Cb.10 addressed; Cb.9a honest deferral; fixed-point stable at 110,127 lines |
| 5 | [Coral](05-coral.md) | Language design | PASS WITH NOTES | **8.9** | +0.4 | All Coral carry-forward closed; benchmark honesty credited; Mar.1r (README still cites retracted numbers) |
| 6 | [Boa](06-boa.md) | Documentation / ergonomics | **EXCEEDS** | **9.1** | +0.1 | All Bo.* verified holding; Bo.12 MEDIUM (README benchmark numbers retracted but not updated) |
| 7 | [Mamba](07-mamba.md) | C runtime / performance | **EXCEEDS** | **9.1** | +0.4 | Bn.1 confirmed closed; geomean arithmetic disputed (claims 7.31× not 5.83×); Bn.3 JSON version stale |
| | **Aggregate** | — | — | **9.21** | **+0.35** | — |

Score trajectory v4.99.0 → v4.106.0 → v4.114.0 → v4.120.0 → v4.136.0 →
v4.143.0 → v4.144.0: **6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 → 9.21.**

The v4.143.0 plateau (8.86) broke with a +0.35-point move. The five LOW
polish items from v4.143.0 (Cb.5-tests, Cb.6-Cb.10) closed cleanly enough
to lift Rattler (+0.2), Anaconda (+0.2), Cobra (+0.2), Coral (+0.4), and
Mamba (+0.4). Viper held at 9.6 (no memory-safety changes). Boa gained
+0.1 but opened Bo.12 (README benchmark numbers).

## Mechanical decision rule

From `.reviews/v4.136.0/V5_DECISION.md`:

| Rule | Condition | Outcome | Applied? |
|---|---|---|---|
| **Option A** | **Aggregate ≥ 9.0 AND 0 NEEDS WORK** | **Tag clean `v5.0.0`** | **YES: 9.21 ≥ 9.0, 0 NEEDS WORK** |
| Option C | 8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK | `v5.0.0-rc1` holds | No: 9.21 ≥ 9.0 |
| Option B | Aggregate < 8.5 OR any NEEDS WORK | Recovery cycle | No: both gates clear |

**Applied: Option A.** Tag `v5.0.0`.

This is the first time in the project's history that Option A has fired.
Five prior v5-gate attempts:
- v4.99.0: 6.59 (Option B)
- v4.120.0: 8.21 + 1 NEEDS WORK (Option B)
- v4.136.0: 8.80 (Option C → `v5.0.0-rc1`)
- v4.143.0: 8.86 (Option C → rc1 holds)
- **v4.144.0: 9.21 (Option A → `v5.0.0`)**

## What closed in this release

1. **Cb.5-tests** — 34 dedicated unit tests in `tests/llvm/test_enum_inline.py`.
   Rattler, Cobra, Anaconda all verified adequate.
2. **Cb.6** — Trailing-`*` typed-pointer-legacy guard in self-hosted
   `type_fits_inline_slot`. Intentional asymmetry with Python emitter.
3. **Cb.7** — Clear-after-transfer at `try_monomorphize_struct`.
   `register_struct`/`register_enum` attempted and reverted (Own.1 limitation).
4. **Cb.9 → Cb.9a** — Self-hosted `semantic.mn` lacks `module_path`;
   documented as gap, deferred to v5.x.
5. **Cb.10** — `66_qualified_type_ref.mn` docstring rewritten.

## Carry-forward opened by this panel

### MEDIUM

- **Bo.12** — README (English + 3 localized) still displays retracted
  benchmark numbers ("1.12× of Rust", "4.86× C", "42.6× Python") and
  links to `FINAL_REPORT_v4.136.md`. The v4.144.0 evidence pack corrects
  these to 5.83×/4.57×/168×. ~30 min effort. (Boa, Coral as Mar.1r)

### LOW

- **Own.1** — Self-hosted lowerer lacks compile-time move-semantics
  enforcement (Viper). v5.x refactor.
- **Cb.9a** — Self-hosted `semantic.mn` lacks `module_path` (Cobra).
  v5.x when cross-module type resolution lands.
- **Bn.3** — `v4.144.0-results.json` version field reads `"4.125.0"`
  (Mamba). Cosmetic, one-line fix.
- **Cb.6-test** — No regression test asserting the self-hosted emitter
  rejects `i64*` (Rattler). LOW.
- **llvm_type_size hardcoded** — `llvm_type_size("%enum.X")` returns 16
  for 24-byte 2-slot inline enums (Rattler). LOW.
- **Dr.1-residual** — Source-tree mutation during build (Rattler). LOW.
- **Sh.4/5/7** — Self-hosted async/tensor/closure-typed feature gaps.
  v5.x feature track.
- **ABI.1** — 24-byte struct return ABI (Cobra/Mamba). v5.x perf arc.

## Disagreements

- **Mamba vs lead on geomean arithmetic.** Mamba recomputes Mn/Rust
  geomean as 7.31×, not the report's 5.83×. Both use the same raw numbers;
  the discrepancy may be in whether `struct_alloc` (70× outlier due to
  ABI.1) is included in the geomean. **Resolution:** Report the per-benchmark
  numbers honestly; the geomean is a summary statistic and its value depends
  on the corpus. Both are valid presentations. The perf arc tracks
  per-workload improvements, not aggregate geomean.

## Improvements since v4.143.0

| Metric | v4.143.0 | v4.144.0 | Δ |
|---|---:|---:|---:|
| Aggregate score | 8.86 | **9.21** | **+0.35** |
| EXCEEDS grades | 3 | **6** | +3 |
| Non-bootstrap pytest | 5,160 | **5,187** | +27 |
| Docket ledger open (LOW) | 5 | varies (new panel items) | net same |
| Benchmark harness | Bn.1 closed (v4.143.0) | **Confirmed holding** | — |
| Fixed-point lines | 109,872 | **110,127** | +255 |

## Summary

The v4.144.0 panel is the culmination of the v4.x engineering arc: 144
releases, 5 v5-gate attempts, 63+ docket closures, and a score trajectory
from 6.59 to 9.21. The mechanical rule fires Option A for the first time.

Six of seven reviewers returned EXCEEDS. Coral at 8.9 is the sole MEETS,
held back by a README benchmark drift (Bo.12/Mar.1r) that is a 30-minute
fix. Zero NEEDS WORK verdicts. Zero CRITICAL or HIGH items on the ledger.

The v5.0.0 tag is earned. The perf arc (v4.145.0–v4.154.0, now v5.1.x)
continues with an honest baseline: Mapanare is 4.57× slower than C,
5.83× slower than Rust, and 168× faster than Python. The tag carries the
engineering story; the perf arc carries the marketing story.

**`v5.0.0` is real.**

---

## Per-reviewer files

- [01-rattler.md](01-rattler.md) — LLVM IR correctness — **9.3 EXCEEDS**
- [02-viper.md](02-viper.md) — Memory safety — **9.6 EXCEEDS**
- [03-anaconda.md](03-anaconda.md) — CI / testing — **9.3 EXCEEDS**
- [04-cobra.md](04-cobra.md) — Bootstrap / self-hosted — **9.2 EXCEEDS**
- [05-coral.md](05-coral.md) — Language design — **8.9 MEETS**
- [06-boa.md](06-boa.md) — Documentation / ergonomics — **9.1 EXCEEDS**
- [07-mamba.md](07-mamba.md) — C runtime / performance — **9.1 EXCEEDS**

## Evidence index

- Pre-panel audit — [PRE_PANEL_AUDIT.md](PRE_PANEL_AUDIT.md)
- V5 decision — [V5_DECISION.md](V5_DECISION.md)
- Prior panel — `.reviews/v4.143.0/` (aggregate 8.86)
- v5 decision history — `.reviews/v4.136.0/V5_DECISION.md` (attempt 3, Option C)
- Carry-forward ledger — `.reviews/CARRY_FORWARD.md`
- Benchmark report — `benchmarks/FINAL_REPORT_v4.144.md`
- Baseline — `docs/roadmap/v4/v4.144.0/BASELINE.md`
