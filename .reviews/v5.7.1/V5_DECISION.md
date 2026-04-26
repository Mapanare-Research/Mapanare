# v5.8.0 RE-PANEL Decision

> **Re-panel of the v5.3.1 → v5.7.1 closeout + feature-parity arc
> (9 releases).** Panel aggregate **9.66 / 10**, 0 NEEDS WORK.
> Mechanical rule -> **Option A — v5.8.0 is a clean production release.**

## Context

The v5.3.1 → v5.7.1 arc spans 9 releases delivered between the v5.2.0
panel (aggregate 9.30, Option A) and this re-panel. The arc closed
all 5 v5.3.0 panel MEDIUM carry-forwards (Lint-v5.2.0, In.1-stage2,
Stream-C, Bo.15, Bo.16); closed every Sh.* feature gap (Sh.4 async,
Sh.6 tensor, Sh.7 closure-typed, plus the orphan B or-pattern fix);
closed Own.1 Phase 2 (28-panel item) at structural root cause; closed
the v5.6.x memory-safety closeout (Ve.1, Ve.2, Ve.3, Ve.4, Lk.1);
restored fixed-point from BROKEN to NEAR; and drove native goldens
54/66 → 66/66 — **the first 100 % native pass in project history**.

v5.8.0 is the panel release: **zero source drift vs v5.7.1**
(`git diff v5.7.0..HEAD -- mapanare/ runtime/ | wc -l` = 0; v5.7.1
landed as a no-source-drift docs/polish release).

## Score

**Aggregate: 9.66 / 10**
**Grade distribution: 7 EXCEEDS / 0 MEETS / 0 NEEDS WORK**

## Decision Rule

| Rule | Condition | Outcome | Applied? |
|---|---|---|---|
| Option A (standard) | Aggregate >= 9.0 AND 0 NEEDS WORK | Clean production release | **YES: 9.0 ≤ 9.66, 0 NEEDS WORK** |
| Option C | 8.5 <= Aggregate < 9.0 AND 0 NEEDS WORK | Closeout arc | No: 9.66 ≥ 9.0 |
| Option B | Aggregate < 8.5 OR any NEEDS WORK | Recovery arc | No: both gates clear |

**Applied: Option A.** v5.8.0 is a clean production release. No
recovery or closeout arc required. The 1 new MEDIUM finding (Bo.18
README internal contradiction on fixed-point status) is documented
as a v5.8.x carry-forward, equivalent in severity to the v5.3.0-era
LOW residuals.

## Per-reviewer scores

| # | Reviewer | Domain | v4.154.0 | v5.2.0 | **v5.8.0** | Δ v5.2.0 | Grade |
|---|---|---|---:|---:|---:|---:|---|
| 1 | Rattler | LLVM IR correctness | 9.6 | 9.3 | **9.8** | **+0.5** | EXCEEDS |
| 2 | Viper | Memory safety | 9.6 | 9.7 | **9.9** | **+0.2** | EXCEEDS |
| 3 | Anaconda | CI / testing | 9.4 | 8.9 | **9.6** | **+0.7** | EXCEEDS |
| 4 | Cobra | Bootstrap / self-hosted | 9.1 | 8.8 | **9.6** | **+0.8** | EXCEEDS |
| 5 | Coral | Language design | 9.3 | 9.4 | **9.6** | **+0.2** | EXCEEDS |
| 6 | Boa | Documentation / DX | 9.3 | 9.4 | **9.4** | **+0.0** | EXCEEDS |
| 7 | Mamba | C runtime / performance | 9.3 | 9.6 | **9.7** | **+0.1** | EXCEEDS |
| | **Aggregate** | — | **9.37** | **9.30** | **9.66** | **+0.36** | — |

## Score trajectory

| Panel | Aggregate | NEEDS WORK | Outcome |
|---|---:|---:|---|
| v4.99.0 | 6.59 | (recovery) | Option B |
| v4.106.0 | 7.87 | 0 | Option B |
| v4.114.0 | 8.21 | 0 | Option B |
| v4.120.0 | 8.21 | 1 (Anaconda) | Option B |
| v4.136.0 | 8.80 | 0 | Option C (v5.0.0-rc1) |
| v4.143.0 | 8.86 | 0 | Option C (rc1 holds) |
| v4.144.0 | 9.21 | 0 | Option A declared (tag deferred) |
| v4.154.0 | 9.37 | 0 | Option A (v5.0.0 tagged) |
| v5.2.0 | 9.30 | 0 | Option A (v5.3.0) |
| **v5.8.0** | **9.66** | **0** | **Option A (v5.8.0)** |

Full trajectory: 6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 → 9.21 →
9.37 → 9.30 → **9.66**.

The +0.36 lift from v5.2.0 to v5.8.0 is the largest single-arc gain
since the v4.114.0 → v4.136.0 closeout (8.21 → 8.80, +0.59 over 22
releases). Per-release lift density: this arc delivered +0.36 / 9
releases = **0.040 lift/release**, vs v4.114→v4.136's +0.59 / 22 =
0.027 lift/release. The arc was efficient.

## What the arc delivered

### v5.3.0 → v5.8.0 hero metrics

| Metric | v5.3.0 | v5.8.0 | Δ |
|---|---:|---:|---|
| Pytest passes | 5,445 | **5,618–5,620** | +175 |
| Pytest fails | 8 | **0** | -8 |
| Flaky audit (5x sequential) | 0 flaky | **0 flaky** | preserved |
| Goldens | **54/66** | **66/66** | **+12** |
| Fixed-point | BROKEN | **NEAR** | restored |
| stage2.ll | 120,956 lines / FAIL | 217,879 lines / **OK** | restored + grown |
| Self-hosted .mn | 41,195 | 48,269 | +7,074 (+17 %) |
| C hardening | 3 fail | **3/3 PASS** | restored |
| Valgrind ERRORS (memory-safety) | 0 | 0 | parity |
| Mn / Rust geomean | 1.17× | **1.003×** | parity |
| Mn / Python geomean | 168× | **328.6×** | ~2× faster |

### MEDIUM carry-forward closures (5 / 5)

| ID | Closed | Verification |
|----|--------|--------------|
| In.1-stage2 | v5.3.2 | `clone_instr_for_inline` extended to 30+ kinds |
| Lint-v5.2.0 | v5.3.1 | `black --check` + `ruff check` GREEN at HEAD |
| Stream-C | v5.3.1 | 74/74 C tests PASS under plain / ASan / TSan |
| Bo.15 (fixed-point claim) | v5.3.1 | README accurate per fixed-point §3 |
| Bo.16 (no-pkg-mgr claim) | v5.3.1 | known_issues.md updated; SPEC §30 added v5.3.3 |

### Sh.* feature-parity closures (4 / 4 + 1 orphan)

| ID | Closed | Goldens impact |
|----|--------|----------------|
| Sh.4 (async self-hosted) | v5.5.4–v5.5.7 | 5 async goldens green |
| Sh.6 (tensor self-hosted) | v5.6.0–v5.6.3 | 5 tensor goldens byte-identical |
| Sh.7 (closure-typed) | v5.7.0 | 1 golden (64) green |
| B (or-pattern + None) | v5.7.0 | 1 golden (51) green |

**66/66 native goldens — first time in project history.**

### Own.1 (the 28-panel item)

| Phase | Closed | What |
|-------|--------|------|
| Phase 1 (Cb.7 zero-after-push) | v5.1.3 | Latent UAF at register_struct/register_enum |
| Phase 2 (infrastructure) | v5.4.0 | Move MIR variant + EmitState slots + drop-glue helpers |
| Phase 2 (functional) | v5.4.1 | Owner-list population at all heap-alloc sites |
| Phase 2 (LSan-gated) | v5.4.2 | scripts/run_asan_leak_goldens.sh + baseline TSV |
| Phase 2 (loop-aware) | v5.4.3 | loop_depth field; Rt.03 closed |
| Phase 2 (Move-aware) | v5.4.4 | Parallel _owned_source arrays |
| Phase 3 (tensor) | v5.6.4 | tensor_owned + emit_track_tensor; Rt.06 closed |

### v5.6.x memory-safety closeout

| Docket | Closed | Class |
|--------|--------|-------|
| Ve.1 (parse_fn_body overflow) | v5.6.5 | GEP-trick + safe sizing |
| Rt.04 (multi-level alias) | v5.6.6 (RESCOPED) | v6.0 borrow-checker scope |
| Ve.2 (lowerer empty-list) | v5.6.7 / .10 / .12 | Destination-passing eliminates floor |
| Ve.3 (drop-glue UAF) | v5.6.9 | List<Enum> RESCOPE; Ve.4 opened |
| Ve.4 (match-arm empty BB) | v5.6.11 | elem_size-stride fix; fixed-point restored |
| Lk.1 (alloca-aliasing) | v5.6.12 | rustc-style PlaceRef destination-passing |
| Layer 1 (struct lets) | v5.6.13 | Optional cleanup; preventive hygiene |

## Key concerns across reviewers

1. **Rt.04 (multi-level alias analysis)** — Viper -0.1; correctly
   RESCOPED to v6.0 borrow checker; 62_list_output baseline-gated at
   13 obj / 346 B. Not a regression, just an open carry.
2. **Bo.18 (README internal contradiction)** — Boa -0.2; lead-in
   paragraph at lines 147-149 says "restoration tracked at v5.3.2"
   while feature subsection at line 135 correctly says "NEAR". Same
   pattern as Bo.15 but smaller blast radius. **NEW MEDIUM.**
3. **Pe.1 (stage2.ll growth scaling)** — Mamba -0.05; stage2.ll grew
   +80 % across the arc (120,956 → 217,879 lines). Bounded by
   per-release < 1-3 % budgets; not a hard ceiling but worth a v6.0
   re-evaluation.
4. **v5.6.x fixed-point churn** — Cobra/Rattler shared concern;
   self-caught and self-restored at v5.6.11; gates could be tighter
   for v6.0 (per-release fixed-point check before tag).

## Carry-forward (for v5.8.x / v6.0)

### MEDIUM (1 new)

- **Bo.18** — README internal contradiction on fixed-point status.
  Single-paragraph copy edit. Targeted v5.8.x docs micro-release or
  rolled into the next compiler release.

### LOW (4 new from this panel)

- **Bo.19** — Test count drift (badge 5800+ / body 5,720+ /
  measurement 5,618-5,620).
- **Bo.20** — README links to v4.153 benchmark report.
- **Bo.14r2** — getting_started.md says "5,445+ tests" (current
  ~5,620).
- **Pe.1** — stage2.ll growth scaling (+80 % v5.3.0 → v5.8.0).

### v6.0 carry (deferred — borrow checker scope)

- **Rt.04** — Multi-level alias analysis (struct→list→string depth 2).
- **Li.1** — LICM with fix-point + preheader insertion.
- **Sh.5 / Sh.9a / Sh.9b / Gr.1** — feature-track items, low priority.
- **Pe.1 follow-up** — IR growth scaling; possibly per-release budget.

### Anaconda informational LOW

- Coverage gate (53-release deferred status quo).
- Windows CI lane (38-release deferred).
- Self-compile pytest smoke gate.
- MIR-level destination-passing tests.
- Inliner-kinds whitelist gate (catch In.1-stage2 regression class).

## Precedent

This decision follows the same structure as v4.154.0/v5.2.0 panels:
Option A applied at aggregate ≥ 9.0 with 0 NEEDS WORK. The v5.8.0
aggregate (9.66) is the **highest in the project's panel history**,
exceeding both v4.154.0 (9.37) and the rejected-but-aspirational
v4.144.0 (9.21).

The +0.36 v5.2.0 → v5.8.0 lift confirms the "features first, panel
last" arc strategy. Every reviewer's v5.2.0 ceiling objection has
been addressed; the only new MEDIUM finding (Bo.18) is documentation
hygiene, not correctness.
