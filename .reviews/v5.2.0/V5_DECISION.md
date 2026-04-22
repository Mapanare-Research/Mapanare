# v5.3.0 Panel Decision

> **v5 arc panel.** Panel aggregate 9.30/10, 0 NEEDS WORK.
> Mechanical rule -> **Option A — v5.3.0 is a clean production release.**

## Context

The v5.0.1-v5.2.0 arc spans 12 releases and 21 commits. It is the
first full v5 panel — the v4.154.0 panel produced the v5.0.0 tag but
predated the v5 arc's docket-closure work.

## Score

**Aggregate: 9.30 / 10**
**Grade distribution: 5 EXCEEDS / 2 MEETS / 0 NEEDS WORK**

## Decision Rule

| Rule | Condition | Outcome | Applied? |
|---|---|---|---|
| Option A (standard) | Aggregate >= 9.0 AND 0 NEEDS WORK | Clean production release | **YES: 9.0 <= 9.30, 0 NEEDS WORK** |
| Option C | 8.5 <= Aggregate < 9.0 AND 0 NEEDS WORK | Closeout arc | No: 9.30 >= 9.0 |
| Option B | Aggregate < 8.5 OR any NEEDS WORK | Recovery arc | No: both gates clear |

**Applied: Option A.** v5.3.0 is a clean production release with no
closeout arc needed. Carry-forward items become v5.4+ planning.

## Per-reviewer scores

| Reviewer | Domain | v4.154.0 | v5.2.0 | Delta | Grade |
|---|---|---:|---:|---:|---|
| Rattler | LLVM IR correctness | 9.6 | **9.3** | -0.3 | EXCEEDS |
| Viper | Memory safety | 9.6 | **9.7** | +0.1 | EXCEEDS |
| Anaconda | CI / testing | 9.4 | **8.9** | -0.5 | MEETS |
| Cobra | Bootstrap / self-hosted | 9.1 | **8.8** | -0.3 | MEETS |
| Coral | Language design | 9.3 | **9.4** | +0.1 | EXCEEDS |
| Boa | Documentation / DX | 9.3 | **9.4** | +0.1 | EXCEEDS |
| Mamba | C runtime / performance | 9.3 | **9.6** | +0.3 | EXCEEDS |
| **Aggregate** | — | **9.37** | **9.30** | **-0.07** | — |

## Score trajectory

| Panel | Aggregate | NEEDS WORK | Outcome |
|---|---:|---:|---|
| v4.99.0 | 6.59 | (recovery) | Option B |
| v4.106.0 | 7.87 | 0 | Option B |
| v4.114.0 | 8.21 | 0 | Option B |
| v4.120.0 | 8.21 | 1 (Anaconda) | Option B |
| v4.136.0 | **8.80** | 0 | Option C (v5.0.0-rc1) |
| v4.143.0 | **8.86** | 0 | Option C (rc1 holds) |
| v4.144.0 | **9.21** | 0 | Option A declared (tag not created) |
| v4.154.0 | **9.37** | 0 | Option A (v5.0.0 tagged) |
| **v5.2.0** | **9.30** | **0** | **Option A (v5.3.0)** |

Full trajectory: 6.59 -> 7.87 -> 8.21 -> 8.21 -> 8.80 -> 8.86 -> 9.21 -> 9.37 -> **9.30**

## What the arc delivered

| Metric | v4.154.0 | v5.2.0 | Delta |
|---|---:|---:|---|
| Carry-forwards closed | — | 19 | Record closure rate |
| Mn/Rust quicksort | 2.99x | **1.14x** | -62% (Perf.1) |
| Mn/Go async (default) | 1.7x | **0.91x** | Faster than Go |
| Valgrind ERRORS | 4 (Ge.1) | **2** (GPU) | -2, different class |
| Test count | 5,309 | **5,445** | +136 |
| Golden tests | 54/66 | 54/66 | Stable |
| Fixed-point | NEAR (4 diff) | **BROKEN** | In.1 regression |

## Why the aggregate dipped (-0.07)

The aggregate dropped from 9.37 to 9.30 despite 19 carry-forward
closures because:

1. **Fixed-point regression** (In.1 inliner broke stage2 self-compilation).
   Cobra -0.3, Rattler -0.3 from this single issue.
2. **v5.2.0 lint gap** (registry code committed without black/ruff).
   Anaconda -0.5, primarily from this process failure.

The gains from Perf.1/Perf.2 (Mamba +0.3), Ge.1r/Own.1 P1 closure
(Viper +0.1), Bo.12 clearance (Boa +0.1), Gr.2 closure (Coral +0.1)
partially offset the regressions but could not overcome them.

## Carry-forward (for v5.4+)

### MEDIUM

- **In.1-stage2** — Inliner SSA rename breaks stage2 self-compilation.
  `clone_instr_for_inline` handles 10 of 30+ instruction kinds; the
  fallthrough pushes un-renamed instructions. Rattler and Cobra both
  identified this.
- **Lint-v5.2.0** — 4 files need black/ruff formatting. Anaconda.
- **Stream-C** — 3 stream C runtime tests fail with wrong element
  values. Mamba root-caused to Ge.1r elem_size fallback interaction.
- **Bo.15** — README claims "strict 3-stage fixed point" but fixed
  point is BROKEN. Boa.
- **Bo.16** — known_issues.md says "No package manager yet" despite
  v5.2.0. Boa.

### LOW

- Li.1 — LICM still regresses live goldens
- Own.1 P2 — Move instruction + drop-glue deferred
- Sh.4/5/6/7/9a — Feature gaps (unchanged)
- Bo.17 — zh-CN/pt README badges at 5.0.6
- Bo.14r — getting_started.md footer stale
- SPEC-pkg — No SPEC section for package management
- An.9 LLVM — E1 opt test LLVM-version-sensitive

## Precedent

This decision follows the same structure as `.reviews/v4.154.0/V5_DECISION.md`
(Option A, v5.0.0 tagged at 9.37). The aggregate is slightly lower
(9.30 vs 9.37) but clears the 9.0 bar with 0 NEEDS WORK.
