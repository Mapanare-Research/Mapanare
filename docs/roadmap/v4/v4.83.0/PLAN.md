# Mapanare v4.83.0 — nsw/nuw + TBAA + inbounds + mem2reg-Friendly Allocas

> **Arc 11 release 2.** The first real IR quality pass. Adds `nsw`
> flags to signed integer arithmetic, `nuw` where unsigned, TBAA
> metadata to loads/stores, `inbounds` to GEPs, and restructures
> alloca patterns so `mem2reg` can promote them. These are the four
> lowest-hanging fruit that unlock LLVM's mid-level optimizer.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.82.0
**Delta review:** No
**Full panel:** No (v4.86.0)
**Estimated work:** 1.5 sprints
**Theme:** Make the IR LLVM-friendly. Let `opt -O2` do its job.

---

## Scope

The IR emitted by `emit_llvm_text.py` is semantically correct but
pessimistic. LLVM treats missing flags conservatively: without `nsw`,
it assumes integer overflow is defined behavior (it isn't in Mapanare);
without TBAA, it assumes any pointer may alias any other; without
`inbounds`, GEPs are treated as arbitrary pointer arithmetic; without
`mem2reg`-friendly allocas, LLVM can't promote stack variables to SSA
registers.

This release fixes all four. The changes are purely additive --
existing semantics don't change, but LLVM now has enough information
to optimize aggressively.

### nsw/nuw flags

Mapanare integers are signed 64-bit. Overflow is undefined behavior
(same as C). Every `add`, `sub`, `mul` on signed integers gets `nsw`
(no signed wrap). Unsigned operations (if any) get `nuw`. This unlocks
strength reduction (e.g., `x * 2` -> `x << 1`), induction variable
simplification, and SCEV-based loop optimizations.

### TBAA metadata

Type-Based Alias Analysis tells LLVM that a load of an `i64` cannot
alias a load of a `double`, and neither can alias a struct pointer.
We emit a TBAA tree at module scope:

```llvm
!0 = !{!"Mapanare TBAA root"}
!1 = !{!"int",    !0}
!2 = !{!"float",  !0}
!3 = !{!"ptr",    !0}
!4 = !{!"struct", !0}
!5 = !{!"bool",   !0}
```

Every load/store gets a `!tbaa !N` reference matching its type. This
lets LLVM reorder loads/stores that don't alias, enabling better
instruction scheduling and loop-invariant code motion.

### inbounds GEP

Every `getelementptr` that accesses a struct field or array element
within known bounds gets the `inbounds` keyword. This tells LLVM the
pointer stays within the allocated object, enabling more aggressive
alias analysis and bounds-check elimination.

### mem2reg-friendly allocas

The `mem2reg` pass promotes stack allocas to SSA registers -- but only
if the alloca has a single definition point. Current IR patterns
sometimes store to an alloca multiple times before the final use
(e.g., initializing struct fields one by one into a stack slot). We
restructure these to use `insertvalue` chains or move allocas to
function entry blocks where `mem2reg` expects them.

---

## Phase 1 -- nsw/nuw flags

- [ ] `mapanare/emit_llvm_text.py`: identify all `add`, `sub`, `mul` emission sites
- [ ] Add `nsw` to all signed integer operations (`i64` arithmetic)
- [ ] Add `nuw` to any unsigned operations (index calculations, length comparisons)
- [ ] Do NOT add flags to floating-point operations (those use `fadd`/`fsub`/`fmul`, not integer ops)
- [ ] Verify: `grep -c 'add nsw' output.ll` shows flags present on integer adds

## Phase 2 -- TBAA metadata

- [ ] `mapanare/emit_llvm_text.py`: emit TBAA root + type nodes at end of module
- [ ] Design the TBAA tree: `root -> {int, float, ptr, struct, bool, string}`
- [ ] Each `load` instruction gets `!tbaa !N` where N matches the loaded type
- [ ] Each `store` instruction gets `!tbaa !N` where N matches the stored type
- [ ] Struct field loads/stores use a sub-tree: `struct -> field_type`
- [ ] Verify: `grep -c '!tbaa' output.ll` shows metadata present

## Phase 3 -- inbounds GEP

- [ ] `mapanare/emit_llvm_text.py`: find all `getelementptr` emission sites
- [ ] Add `inbounds` to GEPs that access:
  - Struct fields (always in bounds by construction)
  - Array elements where the index is known or checked
  - String character access within validated length
- [ ] Do NOT add `inbounds` to GEPs on raw pointers from C interop (unsafe context)
- [ ] Verify: `grep -c 'getelementptr inbounds' output.ll` vs `grep -c 'getelementptr ' output.ll`

## Phase 4 -- mem2reg-friendly allocas

- [ ] `mapanare/emit_llvm_text.py`: audit alloca patterns that block `mem2reg`
- [ ] Move all `alloca` instructions to the function entry block
- [ ] Eliminate multi-store patterns: where a struct is built field-by-field via stores to an alloca, convert to `insertvalue` chains where possible
- [ ] Ensure every alloca that can be promoted has at most one store before its dominating use
- [ ] Verify: run `opt -mem2reg -S output.ll` and check that allocas are eliminated

## Phase 5 -- Integration tests

- [ ] Run all 58 golden tests through `llvm-as` -> `opt -O2` -> `llc` -> link -> run
- [ ] Verify every golden produces correct output at O2 (no miscompilation from new flags)
- [ ] Run `culebra scan` on the modified IR -- verify no new findings from the flag additions
- [ ] Run the self-hosted compiler build (`scripts/build_stage1.py`) -- mnc-stage1 still works

## Phase 6 -- Benchmark delta

- [ ] Run `benchmarks/optimizer/run_baseline.py` against the new IR
- [ ] Save results to `benchmarks/optimizer/v4.83.0-delta.json`
- [ ] Compute delta vs `v4.82.0-baseline.json`: per-benchmark, per-opt-level
- [ ] Document which changes had the biggest impact (hypothesis: nsw unlocks the most for fib, TBAA for matmul)

## Phase 7 -- LOW sweep + closeout

- [ ] Grep for `TODO(v4.83)` or unfinished items
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `nsw` on all signed integer `add`/`sub`/`mul` | `grep 'add nsw' output.ll` |
| 2 | `nuw` on unsigned operations where applicable | grep |
| 3 | TBAA tree emitted at module level | `grep '!tbaa' output.ll` |
| 4 | Every `load`/`store` has `!tbaa` metadata | count match |
| 5 | `inbounds` on all struct-field and in-bounds array GEPs | grep |
| 6 | Allocas in entry block, mem2reg-friendly | `opt -mem2reg` test |
| 7 | 58/58 golden tests pass through `llvm-as -> opt -O2 -> llc -> run` | test log |
| 8 | mnc-stage1 still builds and passes golden | `scripts/build_stage1.py` + `test_native.py` |
| 9 | Benchmark delta measured and recorded | `v4.83.0-delta.json` |
| 10 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Function attributes** (`noalias`, `nonnull`, `readonly`, etc.) -- that's v4.84.0
- **MIR-level optimization** -- that's Arc 12
- **Self-hosted emitter changes** (`emit_llvm.mn`) -- Python bootstrap first; self-hosted mirrors in a later release
- **New language features** -- this is infrastructure only
- **Profile-guided optimization** -- v5.x

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `nsw` causes miscompilation (some operation actually wraps) | low | critical | Mapanare integers don't wrap; if an edge case exists, the golden tests will catch it |
| TBAA metadata format wrong, `llvm-as` rejects | medium | medium | Test incrementally; `llvm-as` validates metadata on parse |
| `inbounds` on a GEP that actually goes out of bounds | low | critical | Only add to struct fields (always in bounds) and checked array access |
| mem2reg refactor changes behavior | low | high | Golden tests are the safety net; run all 58 before and after |
| Self-hosted compiler broken by IR changes | low | medium | Build mnc-stage1 as Phase 5 gate; don't ship if broken |

---

## After v4.83.0

v4.84.0 adds function attributes: `noalias`, `nonnull`, `readonly`, `readnone`, `willreturn`, `nounwind`. The second half of making LLVM's optimizer effective.
