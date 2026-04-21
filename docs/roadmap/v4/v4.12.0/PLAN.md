# Mapanare v4.12.0 — Self-Hosted Optimizer

> The self-hosted compiler produces better code. Fewer instructions, faster binaries.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.11.0

---

## The Problem

The self-hosted compiler does zero optimization — all optimization is
deferred to LLVM's -O2 pass. Adding MIR-level optimization in the
self-hosted pipeline would:
1. Reduce IR size (fewer instructions to emit)
2. Speed up LLVM compilation (less IR to process)
3. Enable optimizations LLVM can't do (Mapanare-specific patterns)

---

## Phase 1: Constant folding

- [ ] New module: `mapanare/self/mir_opt.mn`
- [ ] Fold `BinOp(Const(3), Add, Const(4))` → `Const(7)`
- [ ] Handle: add, sub, mul, div for Int
- [ ] Handle: string concat of two constants
- [ ] Handle: bool AND/OR of two constants
- [ ] Wire into compile() pipeline after lower(), before emit()
- [ ] Rebuild + golden + stage2

## Phase 2: Constant propagation

- [ ] If a `Copy` copies a `Const`, replace all uses of the copy with the constant
- [ ] Iterate to fixpoint
- [ ] Rebuild + golden + stage2

## Phase 3: Dead block elimination

- [ ] Walk from entry block, mark reachable blocks
- [ ] Delete unreachable blocks
- [ ] Rebuild + golden + stage2

## Phase 4: Measure

- [ ] Compare golden test IR size before and after
- [ ] Compare mnc-stage1 binary size before and after
- [ ] Compare compilation time on large .mn files

---

## Exit Criteria

| Check | Required |
|-------|----------|
| mir_opt.mn exists with 3 passes | YES |
| Wired into compile() pipeline | YES |
| Golden IR size reduced (measured) | MEASURE |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
