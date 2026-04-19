# v4.152.0 Session Report

**Date:** 2026-04-19
**Theme:** E8 — dormant MIR passes re-evaluation
**Result:** Full dead end — 4 passes evaluated, 0 kept, 3 new LOW dockets opened

## What was done

Re-evaluated the four MIR optimizer passes disabled at v4.111.0
(`strength_reduce`, `inline_small_functions`, `licm`,
`escape_analysis`) under v4.152.0 conditions. Each was re-enabled in
isolation, rebuilt, and measured against the baseline.

### E8a: strength_reduce
- Re-enabled `strength_reduce_function(f4)` at mir_opt.mn:1238
- Build: SUCCESS (no crash)
- Goldens: 54/66 (no regression)
- Golden IR: byte-identical to baseline (0 diff lines)
- stage2.ll: +1 line (the call instruction itself), md5 changed only
  from register renumbering
- Verdict: **SAFE, ZERO-ROI.** Pass runs, finds zero mod-by-power-of-2
  patterns in the self-hosted MIR. LLVM instcombine covers this.
  Rolled back.

### E8b: inline_small_functions
- Re-enabled `inline_small_functions(f5, lookup)` at mir_opt.mn:1250
- Build: SUCCESS (no verify_block crash — v4.111.0 crash is GONE)
- Goldens: 54/66 (no regression on individual test programs)
- Fixed-point: **FAIL** — `llvm-as` rejects stage2.ll at line 261:
  `multiple definition of local value named '%t4'` in `parse_program`.
  The inliner prefixes inlined body variables (`_inl0_6_*`) but the
  caller's destination register where the inlined result is assigned
  back reuses the original `%t4` name.
- Root cause: `rename_instructions` (mir_opt.mn:700-766) renames
  variables *inside* the inlined body but not the caller's destination.
- Verdict: **BREAKS SELF-COMPILATION.** Rolled back. Opens In.1 (LOW).

### E8c: licm
- Re-enabled `licm_function(f6)` at mir_opt.mn:1268
- Build: SUCCESS (block_successors crash is GONE)
- Goldens: **51/66 (3 regressions)**: `05_for_loop`, `21_list_ops`,
  `33_break_continue` — all loop-heavy tests.
- Root cause: `hoist_instruction` (mir_opt.mn:1040-1069) moves an
  instruction to the loop header but leaves it in the source block too,
  producing duplicate definitions.
- Verdict: **GOLDEN REGRESSIONS.** Rolled back. Opens Li.1 (LOW).

### E8d: escape_analysis
- Re-enabled `escape_analysis_function(f7)` at mir_opt.mn:1287
- Build: SUCCESS (+0x3f3 crash is GONE — Ge.1 closure fixed it)
- Goldens: 54/66 (no regression)
- stage2.ll: **byte-identical to baseline** (md5
  `39b68cd7333a4c0f69f58bcc9f8e8280`)
- Root cause of zero-ROI: the function is a stub — `return f` at line
  1204 without modifying anything. The Python version
  (`escape_analysis_promotion`) actually modifies `alloc_kind`; the
  self-hosted version lacks this codegen.
- Verdict: **SAFE, ZERO-ROI (STUB).** Rolled back. Opens Ea.1 (LOW).

## Python/self-hosted parity

| Pass | Python | Self-hosted | Status |
|---|---|---|---|
| strength_reduce | ON | OFF | Tolerable divergence |
| inline_small_functions | ON | OFF | Structural divergence (In.1) |
| licm | OFF | OFF | Parity holds |
| escape_analysis | ON | OFF | Structural divergence (Ea.1) |

## Measurements

| Metric | Baseline | Post-E8 |
|---|---|---|
| Goldens | 54/66 | 54/66 (restored) |
| stage2.ll lines | 110,127 | 110,127 |
| stage2.ll md5 | `39b68cd7...` | `39b68cd7...` (identical) |
| Fixed-point | NEAR (4 diff) | NEAR (4 diff) |
| Non-bootstrap pytest | 5,298 / 0 | (unchanged — no source changes survived) |
| Valgrind | 0/62/4 | (unchanged) |
| ASan | 55/0/11 | (unchanged) |
| Build time | 102s | ~109s (comment additions only) |

## Artifacts

- `BASELINE.md` — all pre-experiment measurements
- `HYPOTHESIS.md` — per-pass predictions
- `RESULTS.md` — verdicts + honest story
- `goldens-baseline.log` — 54/66 baseline
- `goldens-E8a.log` — 54/66 (strength_reduce)
- `goldens-E8b.log` — 54/66 (inline_small_functions, but stage2 invalid)
- `goldens-E8c.log` — 51/66 (licm regressions)
- `goldens-E8d.log` — 54/66 (escape_analysis)
- `fixedpoint-baseline.log` — NEAR FIXED POINT
- `build-baseline.log` — 102s
- `stage2-baseline.ll`, `stage3-baseline.ll`, `main-baseline.ll` — IR snapshots
- `03_function-baseline.ll`, `11_closure-baseline.ll`, `26_generics-baseline.ll` — golden IR

## Docket changes

### Opened
- **In.1** (LOW) — self-hosted inliner rename bug (mir_opt.mn:700-766)
- **Li.1** (LOW) — self-hosted LICM hoist_instruction duplicate (mir_opt.mn:1040-1069)
- **Ea.1** (LOW) — self-hosted escape_analysis is a stub (mir_opt.mn:1177-1204)

### Closed
None.

## Verification

- `ruff check .` — clean
- `black --check .` — 353 unchanged
- `mypy mapanare/ runtime/` — 0 issues
- `check_struct_registry.py` — clean (23/23/89)
- Goldens — 54/66
- Fixed-point — NEAR (4 diff lines, version placeholder only)
- Valgrind — 0/62/4
- ASan — 55/0/11
- Non-bootstrap pytest — 5,298 / 0

## Key learnings

1. **The v4.111.0 crashes are largely fixed.** Three of four passes now
   run without crashing (strength_reduce, inline_small_functions on small
   programs, escape_analysis). Only LICM still corrupts output. The Sh.2,
   Ge.1, and Sh.8-12 arcs fixed the underlying MIR invariants that were
   causing the v4.111.0 crashes.

2. **"Doesn't crash" ≠ "earns ROI."** All four passes are subsumed by
   LLVM -O2. The self-hosted MIR optimizer's value is in passes 1-3
   (constant folding, propagation, dead block elimination) which clean up
   MIR before it reaches LLVM. Passes 4-7 duplicate LLVM's work.

3. **The inliner has a real bug.** The rename collision in
   inline_small_functions is a correctness bug, not a verifier quirk. It
   only manifests on large programs (self-compilation) where variable names
   collide after multiple inlining passes. This is fixable (In.1) but not
   in this release.

4. **LICM has a real bug.** The instruction duplication in hoist_instruction
   is a correctness bug that affects 3/54 golden tests. Also fixable (Li.1)
   but not in this release.

5. **Escape analysis needs codegen, not just analysis.** The self-hosted
   version identifies non-escaping allocations correctly but has no codegen
   path to act on the result. The Python version does. This is the most
   actionable docket (Ea.1) if MIR-level stack promotion becomes valuable.
