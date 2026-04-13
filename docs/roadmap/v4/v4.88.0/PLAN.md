# Mapanare v4.88.0 — Loop Invariant Code Motion + Strength Reduction

> **Arc 12 release 2.** Adds loop-level optimizations to the MIR
> pipeline. v4.87.0 shipped function inlining; v4.88.0 builds on that
> by detecting natural loops, hoisting invariant computations out of
> loop bodies, and replacing expensive operations with cheaper ones
> inside tight loops.
>
> These are the two optimizations that matter most for numeric code:
> matrix multiply, sorting, stream pipelines. LLVM has its own LICM,
> but it operates on LLVM IR where Mapanare-level purity information
> is lost. MIR-level LICM can safely hoist more because it knows which
> Mapanare functions are pure.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.87.0
**Delta review:** No
**Full panel:** No (v4.91.0)
**Estimated work:** 1 sprint
**Theme:** Loop detection, LICM, and strength reduction in the MIR optimizer. The classic loop optimization pair.

---

## Scope

The MIR optimizer currently has no concept of loops. Control flow is a flat list of basic blocks with branches; the fixpoint loop in `optimize_function()` iterates passes until convergence but treats all blocks equally. This means:

1. A computation like `len(arr)` inside a for-loop body is re-evaluated every iteration, even though `arr` does not change inside the loop.
2. A multiplication `i * stride` where `stride` is constant and `i` is the induction variable could be replaced with an addition of `stride` per iteration.

v4.88.0 adds three things:

**Loop detection.** Identify natural loops via back-edge detection. A back-edge is a CFG edge from block B to block H where H dominates B. The loop body is the set of blocks that can reach B without going through H. The loop header is H. The loop preheader is the unique predecessor of H that is not part of the loop body (created if necessary).

**LICM (Loop Invariant Code Motion).** For each natural loop, identify instructions whose operands are all defined outside the loop (or are constants). These are loop-invariant. Hoist them to the loop preheader. Safety: only hoist instructions with no side effects -- pure computations, field reads from immutable objects, constant loads. Never hoist stores, calls to impure functions, agent operations, or signal mutations.

**Strength reduction.** Inside loops, find patterns:
- `%x = mul %iv, %const` where `%iv` is a linear induction variable and `%const` is loop-invariant -> replace with `%x = add %x_prev, %const` (initialize `%x_init = mul %iv_init, %const` in preheader).
- `%x = div %y, %const` where `%const` is a power-of-2 integer -> replace with right shift.
- `%x = mod %y, %const` where `%const` is a power-of-2 integer -> replace with bitwise AND.

## Phase 1 — Loop detection infrastructure

- [ ] Add `MIRLoop` dataclass to `mapanare/mir.py`:
  ```
  @dataclass
  class MIRLoop:
      header: str           # block name
      back_edge_source: str # block name
      body: set[str]        # block names in the loop body
      preheader: str | None # block name (created if needed)
      depth: int = 1        # nesting depth
  ```
- [ ] Implement `compute_dominators(fn: MIRFunction) -> dict[str, set[str]]`: standard iterative dominator algorithm on the CFG. Returns dominator sets per block.
- [ ] Implement `find_back_edges(fn: MIRFunction, dominators: dict) -> list[tuple[str, str]]`: scan all CFG edges, return (source, header) pairs where header dominates source.
- [ ] Implement `find_natural_loops(fn: MIRFunction) -> list[MIRLoop]`: for each back-edge, compute loop body via reverse reachability. Handle nested loops (inner loop has higher depth).
- [ ] Implement `ensure_preheader(fn: MIRFunction, loop: MIRLoop) -> str`: if the loop header has predecessors from outside the loop that are not a single dedicated preheader block, create one by inserting a new block that jumps to the header and redirecting outside predecessors to the new block. Return the preheader block name.

## Phase 2 — LICM pass

- [ ] Implement `is_loop_invariant(inst: Instruction, loop: MIRLoop, fn: MIRFunction) -> bool`:
  - All operands (from `_get_uses`) are either constants or defined outside `loop.body`
  - The instruction has no side effects: not a `Call` to an impure function, not a store, not an agent/signal/stream operation
  - Pure function whitelist: builtins `len`, `str`, `int`, `float`, and any function marked `@pure` in metadata
- [ ] Implement `licm(fn: MIRFunction, module: MIRModule, stats: MIRPassStats) -> bool`:
  - Compute dominators and find natural loops
  - For each loop (innermost first): ensure preheader, scan body for invariant instructions, hoist to preheader
  - Track `invariants_hoisted: int` in stats
  - Return True if any instruction was hoisted
- [ ] Add `invariants_hoisted: int = 0` to `MIRPassStats`

## Phase 3 — Strength reduction pass

- [ ] Implement `find_induction_variables(loop: MIRLoop, fn: MIRFunction) -> list[tuple[str, Value, BinOpKind]]`: identify basic induction variables -- values that are incremented/decremented by a loop-invariant value in every iteration via a `Phi` + `BinOp(ADD/SUB)` pattern.
- [ ] Implement `strength_reduction(fn: MIRFunction, module: MIRModule, stats: MIRPassStats) -> bool`:
  - For each loop, find induction variables
  - For each `MIR BinOp(MUL, %iv, %const)` where `%iv` is an induction variable and `%const` is loop-invariant: replace with addition chain
  - For each `BinOp(DIV, %x, %const)` where `%const` is power-of-2: replace with right shift
  - For each `BinOp(MOD, %x, %const)` where `%const` is power-of-2: replace with AND `(%const - 1)`
  - Track `strengths_reduced: int` in stats
- [ ] Add `strengths_reduced: int = 0` to `MIRPassStats`

## Phase 4 — Wire into O2 pipeline

- [ ] In `optimize_function()`, add LICM and strength reduction at O2 level, after inlining and before DCE:
  ```python
  if level >= MIROptLevel.O2:
      changed |= copy_propagation(fn, stats)
      changed |= inline_small_functions(fn, module, stats, heuristic)
      changed |= licm(fn, module, stats)                    # NEW
      changed |= strength_reduction(fn, module, stats)      # NEW
      changed |= branch_simplification(fn, stats)
      changed |= unreachable_block_elimination(fn, stats)
      changed |= dead_code_elimination(fn, stats)
      changed |= agent_inlining(fn, stats)
  ```
- [ ] Ensure the fixpoint loop still converges (LICM and strength reduction are idempotent: once all invariants are hoisted and all strengths reduced, a second pass is a no-op)

## Phase 5 — Testing

- [ ] Unit tests in `tests/mir/test_loops.py`:
  - `test_find_natural_loop_simple`: single back-edge, correct body computed
  - `test_find_nested_loops`: two nested loops, depth is correct
  - `test_ensure_preheader_created`: loop header with 2 outside predecessors gets a preheader
  - `test_ensure_preheader_exists`: loop with existing preheader is not modified
  - `test_dominator_computation`: verify dominator sets on a known CFG
- [ ] Unit tests in `tests/mir/test_licm.py`:
  - `test_hoist_pure_computation`: `len(arr)` inside loop hoisted to preheader
  - `test_no_hoist_store`: store instruction stays inside loop
  - `test_no_hoist_impure_call`: call to non-pure function stays inside loop
  - `test_hoist_constant_expression`: `3 + 4` inside loop hoisted
  - `test_nested_loop_innermost_first`: invariant of inner loop hoisted to inner preheader, invariant of outer loop hoisted to outer preheader
- [ ] Unit tests in `tests/mir/test_strength_reduction.py`:
  - `test_mul_to_add`: `i * 4` in loop becomes `prev + 4`
  - `test_div_power_of_two`: `x / 8` becomes right shift by 3
  - `test_mod_power_of_two`: `x % 16` becomes AND with 15
  - `test_no_reduce_non_constant`: `i * j` where j varies -- not reduced
- [ ] Golden tests: 57/57 at O2

## Phase 6 — Benchmark

- [ ] Run the 5-program benchmark suite at O2 with LICM + strength reduction enabled
- [ ] Record results to `benchmarks/optimizer/v4.88.0-delta.json`:
  - Per-program: time_ms, speedup_vs_v4.87.0, invariants_hoisted, strengths_reduced
  - Expected: sort(10K) and matrix_mul show the most improvement (loop-heavy)
  - Expected: fib(35) shows minimal change (no loops in the hot path)
- [ ] Cross-check: run the same programs at O2 without LICM/strength-reduction (flag-gated) to isolate the contribution

## Phase 7 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.88.0]` entry -- "Loop optimizations: natural loop detection, LICM (hoist invariants to preheader), strength reduction (mul->add, div->shift, mod->and)"
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `MIRLoop` dataclass exists in `mir.py` | `grep "class MIRLoop" mapanare/mir.py` |
| 2 | `compute_dominators()` returns correct dominator sets | unit test |
| 3 | `find_natural_loops()` identifies loops and nesting | unit test |
| 4 | `licm()` hoists loop-invariant pure computations | unit test (hoist_pure_computation) |
| 5 | `licm()` does NOT hoist side-effecting instructions | unit test (no_hoist_store, no_hoist_impure_call) |
| 6 | `strength_reduction()` fires on mul-by-constant in loop | unit test (mul_to_add) |
| 7 | Both passes wired into O2 pipeline | `optimize_function` source |
| 8 | All 57 golden tests pass at O2 | `pytest tests/golden/ -v` |
| 9 | Benchmark delta recorded | `benchmarks/optimizer/v4.88.0-delta.json` exists |
| 10 | `make lint` + `make test` pass | CI log |

---

## What this release does NOT do

- **Loop unrolling** -- a separate optimization pass, deferred. LICM and strength reduction are the highest-value loop passes; unrolling is a code-size tradeoff better left to LLVM.
- **Polyhedral analysis** -- out of scope entirely. Mapanare is not a scientific computing DSL.
- **Vectorization** -- LLVM's auto-vectorizer handles this after the MIR-level passes run.
- **Mutual recursion detection for inlining** -- still deferred from v4.87.0.
- **Self-hosted mir_opt.mn update** -- Python only for now.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Incorrect LICM hoists side-effecting instruction | low | critical | Conservative purity check: only hoist pure computations + known-pure builtins. Comprehensive unit tests. |
| Preheader insertion breaks existing branch targets | medium | high | `ensure_preheader` rewires all outside predecessors; unit test verifies correctness |
| Dominator computation is O(n^2) on large CFGs | low | medium | Functions with > 500 blocks are rare; fallback: skip LICM for oversized functions |
| Strength reduction introduces precision issues (shift vs div) | low | medium | Only apply to integer types; float div-by-constant is not reduced |
| Fixpoint non-convergence after adding two new passes | low | high | Both passes are idempotent on settled MIR; test convergence on all 57 goldens |

---

## After v4.88.0

v4.89.0 adds escape analysis: heap allocations that do not escape the function are promoted to stack allocations, eliminating malloc/free overhead entirely.
