# Mapanare v4.16.0 — Optimizer Complete

> Dead block elimination enabled. Constant and copy propagation. Measurable IR reduction.

**Status:** PARTIAL (const prop done, dead block elim deferred)
**Breaking:** No
**Prerequisite:** v4.15.0

---

## The Problem

The self-hosted optimizer (`mir_opt.mn`) exists but is incomplete:

1. **Dead block elimination is disabled.** The pass was implemented in v4.12.0
   but had to be disabled because `emit_llvm.mn` references unreachable blocks
   by label. When dead blocks are removed, the emitter generates dangling label
   references that crash `llvm-as`.

2. **Constant propagation is shallow.** The current pass only folds binary
   operations on literal constants. It does not propagate constants through
   copies, loads, or function arguments.

3. **Copy propagation does not exist.** Redundant `Copy` instructions are
   emitted for every variable binding, even when the source is directly usable.

4. **No measurement infrastructure.** We cannot track whether optimization
   passes actually reduce IR size or compilation time.

---

## Phase 1: Fix emitter label references

- [ ] Audit `emit_llvm.mn` for all block label references
- [ ] Identify which references point to blocks that dead block elimination removes
- [ ] Fix: emit only labels that exist in the function's block list
- [ ] Fix: PHI nodes must not reference removed predecessor blocks
- [ ] Fix: branch targets must not reference removed blocks
- [ ] Rebuild + golden

## Phase 2: Enable dead block elimination

- [ ] Remove the disable flag / comment in `mir_opt.mn`
- [ ] Run dead block elimination on all MIR functions
- [ ] Rebuild + golden + stage2
- [ ] Measure: count blocks before and after on golden tests
- [ ] If any test breaks, identify the specific block reference and fix

## Phase 3: Constant propagation

- [ ] Extend constant folding to propagate through `Copy` instructions
- [ ] If `Copy(dest, Const(v))`, replace all uses of `dest` with `Const(v)`
- [ ] Iterate to fixpoint (propagation may enable further folding)
- [ ] Handle: Int, Float, Bool, String constants
- [ ] Do NOT propagate through function calls or memory operations
- [ ] Rebuild + golden + stage2

## Phase 4: Copy propagation

- [ ] If `Copy(dest, src)` and `src` is still live, replace uses of `dest` with `src`
- [ ] Respect SSA: only propagate when `src` is not redefined between def and use
- [ ] Remove dead `Copy` instructions after propagation
- [ ] Rebuild + golden + stage2

## Phase 5: Measure IR reduction

- [ ] Record IR metrics for all 40 golden tests BEFORE optimization
- [ ] Record IR metrics AFTER (blocks, instructions, IR bytes)
- [ ] Record mnc-stage1 binary size before and after
- [ ] Record compile time for `mnc_all.mn` before and after
- [ ] Update `tests/golden/BENCHMARKS.md` with optimization column

---

## Exit Criteria

| Check | Required |
|-------|----------|
| Dead block elimination enabled (not commented out) | YES |
| Emitter does not reference removed blocks | YES |
| Constant propagation through Copy | YES |
| Copy propagation pass exists | YES |
| IR size reduction measured on golden tests | MEASURE |
| mnc-stage1 binary size reduction measured | MEASURE |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
