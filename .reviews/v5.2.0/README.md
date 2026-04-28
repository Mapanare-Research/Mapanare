# v5.2.0 Panel — THE v5 ARC PANEL

> Seven-reviewer panel. The **v5.0.1 -> v5.2.0** arc
> (12 releases, 19 carry-forward closures) is the surface graded.
> First full v5 panel since v5.0.0 was tagged.
>
> **Aggregate: 9.30 / 10. Decision: Option A.**

**Panel date:** 2026-04-22
**Aggregate: 9.30 / 10**
**Grade distribution: 5 EXCEEDS / 2 MEETS / 0 NEEDS WORK**
**Decision rule applied: Option A — v5.3.0 is a clean production release**

---

## Verdict Table

| # | Reviewer | Domain | Verdict | Score | Delta vs v4.154.0 | Top findings |
|---|---|---|---|---:|---:|---|
| 1 | [Rattler](01-rattler.md) | LLVM IR correctness | **EXCEEDS** | **9.3** | -0.3 | Perf.1 inline correct; In.1-stage2 regression (10/30 instr kinds) |
| 2 | [Viper](02-viper.md) | Memory safety | **EXCEEDS** | **9.7** | +0.1 | Ge.1r confirmed closed; Own.1 P1 addresses flagged UAFs |
| 3 | [Anaconda](03-anaconda.md) | CI / testing | MEETS | **8.9** | -0.5 | Lint gates RED from v5.2.0 registry; 51 registry tests well-structured |
| 4 | [Cobra](04-cobra.md) | Bootstrap / self-hosted | MEETS | **8.8** | -0.3 | Fixed-point BROKEN (In.1); 5/7 carry-forwards closed |
| 5 | [Coral](05-coral.md) | Language design | **EXCEEDS** | **9.4** | +0.1 | Gr.2 closed after 19 releases; pkg registry well-designed |
| 6 | [Boa](06-boa.md) | Documentation / DX | **EXCEEDS** | **9.4** | +0.1 | Bo.12 fully closed; README redesign; pkg guide; fixed-point claim stale |
| 7 | [Mamba](07-mamba.md) | C runtime / performance | **EXCEEDS** | **9.6** | +0.3 | All 5 carry-forwards closed; Perf.1 -62% quicksort; Perf.2 0.91x Go |
| | **Aggregate** | — | — | **9.30** | **-0.07** | — |

Score trajectory: 6.59 -> 7.87 -> 8.21 -> 8.21 -> 8.80 -> 8.86 -> 9.21 -> 9.37 -> **9.30**

## What the arc delivered

- **19 carry-forward closures** in 12 releases (record closure rate)
- **Perf.1**: Inline list ops — quicksort 2.99x -> 1.14x Rust (-62%)
- **Perf.2**: Lazy coro threads — async 0.91x Go at default settings
- **Ge.1r**: Valgrind generics ERRORS eliminated (4 -> 0)
- **Own.1 Phase 1**: Specific UAFs at register_struct/register_enum closed
- **Cb.15**: sret classifier ported to self-hosted
- **Package Registry MVP**: First user-facing v5 feature
- **Both emitters patched simultaneously** for Perf.1 (no new parity gap)

## Key concerns across reviewers

1. **Fixed-point regression** (Cobra 8.8, Rattler 9.3, Anaconda 8.9):
   In.1 inliner re-enable breaks stage2. `clone_instr_for_inline`
   handles 10/30+ instruction kinds.
2. **v5.2.0 lint gap** (Anaconda 8.9): Registry code committed without
   running `black`/`ruff`. First red CI gates in 37 releases.
3. **Stream C tests** (Mamba): 3/74 fail with wrong values. Root-caused
   to Ge.1r elem_size fallback interaction.

## Evidence

- MEASUREMENTS.md — `docs/roadmap/v5/v5.3.0/MEASUREMENTS.md`
- PARITY_GAPS.md — `docs/roadmap/v5/PARITY_GAPS.md`
- V5_DECISION.md — [V5_DECISION.md](V5_DECISION.md)
- Prior panel — `.reviews/v4.154.0/` (aggregate 9.37, Option A)
