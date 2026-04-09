# Mapanare v4.22.0 — Dead Block Elimination (Fixed)

> Fix the BFS, enable the optimizer pass, measure IR reduction.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.21.0

---

## The Problem

Dead block elimination was implemented in v4.12.0 but disabled because:
1. The BFS misses while/for header blocks (the lowerer emits jumps that
   the BFS `collect_targets` doesn't follow through all instruction types)
2. PHI nodes reference removed blocks, causing dangling label errors

v4.16.0 attempted to fix this but the BFS still missed block references
from the self-hosted lowerer's patterns.

---

## Phase 1: Diagnose the BFS gap

- [ ] Compile `tests/golden/12_while.mn` with dead block elim enabled
- [ ] Dump the MIR before and after dead block elim
- [ ] Identify which blocks were incorrectly removed
- [ ] Trace why the BFS didn't mark them as reachable
- [ ] Root cause: which instruction type is the BFS not handling?

## Phase 2: Fix the BFS

- [ ] Add missing instruction types to `collect_targets` in mir_opt.mn
- [ ] Verify: all block references from all instruction types are collected
- [ ] Test with all 45 golden tests
- [ ] If any test fails, identify the specific gap and fix

## Phase 3: PHI node cleanup

- [ ] After removing blocks, patch PHI nodes in surviving blocks
- [ ] Remove incoming entries whose source block was eliminated
- [ ] If a PHI has 0 remaining entries, replace with undef or remove
- [ ] Test with all 45 golden tests

## Phase 4: Enable and measure

- [ ] Enable dead block elimination in `optimize_mir`
- [ ] Record IR metrics before and after (blocks, instructions, IR bytes)
- [ ] Rebuild + golden + stage2
- [ ] Update BENCHMARKS.md with optimization column

---

## Exit Criteria

| Check | Required |
|-------|----------|
| Dead block elimination enabled (not commented out) | YES |
| BFS correctly marks all reachable blocks | YES |
| PHI nodes cleaned up after block removal | YES |
| IR size reduction measured | MEASURE |
| 45/45 golden | YES |
| 11/11 stage2 | YES |
