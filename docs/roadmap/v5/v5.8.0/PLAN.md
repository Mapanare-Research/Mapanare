# v5.8.0 — Re-panel (target 9.7+)

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.7.1 shipped (SPEC + docs polish after 66/66;
culebra clean baseline + arc-journal aggregated)
**Estimated work:** 1 session (measurement + review)

---

## Goal

Re-panel after the full v5.4.0–v5.7.1 feature + polish arc. Same
seven reviewers, same mechanical rule. Target: aggregate >= 9.7.

Unlike the original v5.4.0 plan (which would have panelled after only
the v5.3.x closeout arc), this panel sees the complete picture: all
Sh.* feature gaps closed, 66/66 goldens, Own.1 Phase 2 landed, and a
fresh SPEC + docs polish pass. Every reviewer's ceiling objection
should be resolved.

**New for this panel: culebra-driven evidence**. Every reviewer
gets `docs/roadmap/v5/v5.7.1/culebra/baseline-end.json` plus
`arc-journal.jsonl` (the v5.6.9 → v5.7.1 milestone log) as
structured input. Replaces the per-reviewer "go grep stage2.ll
yourself" pattern from earlier panels and gives Rattler / Cobra /
Anaconda a single source of truth.

## Expected score recovery

| Reviewer | v5.3.0 | Expected v5.8.0 | Delta | Driver |
|----------|--------|-----------------|-------|--------|
| Rattler | 9.3 | 9.7–9.8 | +0.4–0.5 | 66/66 goldens, In.1-stage2 fix, closure + or-pattern fixed |
| Viper | 9.7 | 9.8–9.9 | +0.1–0.2 | Own.1 Phase 2 closes 28-panel carry-forward |
| Anaconda | 8.9 | 9.5–9.7 | +0.6–0.8 | Lint GREEN, stream fixed, 66/66 goldens, async + tensor tests |
| Cobra | 8.8 | 9.5–9.7 | +0.7–0.9 | Fixed-point restored, all Sh.* closed, full self-hosted parity |
| Coral | 9.4 | 9.6–9.8 | +0.2–0.4 | SPEC-pkg, signal demo, tensor + async spec'd + implemented |
| Boa | 9.4 | 9.6–9.7 | +0.2–0.3 | Bo.15/16/17 cleared, 66/66 badge, complete docs refresh |
| Mamba | 9.6 | 9.7–9.8 | +0.1–0.2 | Stream-C fix, async parity, drop-glue stable |
| **Aggregate** | **9.30** | **9.65–9.75** | **+0.35–0.45** | — |

## Why features-first, panel-last

The v5.3.x closeout arc cleared all 5 MEDIUM carry-forwards, but the
reviewers would still flag the Sh.* feature gaps (Sh.2/Sh.4/Sh.6/Sh.7)
and the 54/66 golden ceiling. Panelling at 9.5 then doing 4 more
feature releases then panelling again is two panels for one arc.
Shipping features first (v5.4.0–v5.7.0) and polishing (v5.7.1) before
the single panel maximizes the score delta and eliminates every known
ceiling objection in one pass.

## Closeout arc precedent

The v4.121.0–v4.135.0 closeout arc (15 releases) pushed the aggregate
from 8.21 (v4.120.0, Option B) to 8.80 (v4.136.0, Option C). The
current arc is 7 releases (v5.3.1–v5.7.1) but covers both closeout
AND feature-parity, targeting a larger delta.

## Culebra inputs for the panel

Every reviewer gets the same packet:

| Artifact | Source | What it shows |
|---|---|---|
| `baseline-end.json` | `docs/roadmap/v5/v5.7.1/culebra/` | Final stage2.ll snapshot — counts of all template matches, function metrics |
| `triage.md` | same | Grouped findings by root cause; FP-suppressed |
| `health-{Value,MIRType,EmitState,LowerState,Instruction}.txt` | same | PHI zeroinit / type-pun / null-load checks for the most-touched structs |
| `fixedpoint.md` | same | Stage1→stage2→stage3 cycle stabilization evidence |
| `arc-journal.jsonl` | same | Every milestone / fix / analysis from v5.6.9 → v5.7.1 |
| `baseline-delta-from-v5.6.10.md` | `docs/roadmap/v5/v5.7.1/culebra/` | Quantified IR-shape changes from the closure work |

Per-reviewer focus:

| Reviewer | Primary culebra input |
|---|---|
| Rattler (LLVM) | `triage.md`, `baseline-delta`, `health-*` |
| Cobra (C++/ABI) | `baseline-end.json` (sret/byref counts), `health-Value`, `health-MIRType` |
| Mamba (C runtime) | `arc-journal.jsonl` (drop-glue + tracking discipline) |
| Viper (memory safety) | `health-*`, `triage.md` (UAF / leak templates), LSan baselines |
| Anaconda (toolchain) | `fixedpoint.md`, `baseline-delta`, CI integration |
| Coral (SPEC) | `arc-journal.jsonl` (feature additions match SPEC §s) |
| Boa (docs) | `docs/guides/culebra.md` published in v5.7.1 |
