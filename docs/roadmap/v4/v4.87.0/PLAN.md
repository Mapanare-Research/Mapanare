# Mapanare v4.87.0 — MIR Inlining Pass

> **Arc 12 release 1.** Opens the second optimizer arc: MIR-level
> optimizations. Arc 11 (v4.82.0-v4.86.0) improved LLVM IR quality
> with nsw/nuw, TBAA, and function attributes, yielding 2-3x speedup.
> Arc 12 adds transformations that LLVM cannot do because they require
> Mapanare-level knowledge: inlining decisions based on MIR cost
> models, loop-invariant code motion with Mapanare purity semantics,
> and escape analysis for heap-to-stack promotion.
>
> v4.87.0 ships the first new MIR pass since v4.30.0: function
> inlining. Small, non-recursive functions are cloned into their call
> sites, enabling downstream constant folding and DCE to eliminate
> overhead that survives through the LLVM pipeline.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.86.0
**Delta review:** No
**Full panel:** No (v4.91.0)
**Estimated work:** 1 sprint
**Theme:** MIR function inlining with cost-model heuristic. First new optimization pass in `mir_opt.py` since v4.30.0.

---

## Scope

The current MIR optimizer (`mapanare/mir_opt.py`) runs nine passes in a fixpoint loop: constant folding, constant propagation, copy propagation, branch simplification, unreachable block elimination, dead code elimination, agent inlining, stream fusion, and dead function elimination (module-level). None of these are interprocedural in the classical sense -- agent inlining is domain-specific (single-spawn agents become direct calls), not a general inlining pass.

v4.87.0 adds a general-purpose `inline_small_functions()` pass. For every `MIRCall` instruction in a function body, the pass evaluates an inlining heuristic:

1. **Callee body size < 20 MIR instructions** (configurable threshold).
2. **Callee is not recursive** (no call to itself, directly or via mutual recursion within the same SCC).
3. **Callee is not marked `@noinline`** (checked via function metadata).
4. **Cost model:** `call_count * body_size < budget` (default budget: 200). A function called once with 19 instructions is always inlined. A function called 15 times with 14 instructions (210) is not.

When a call site passes the heuristic:
- Clone the callee's basic blocks and instructions.
- Rename all temporaries with a fresh prefix to avoid SSA name collisions.
- Replace parameter values with the argument values from the call site.
- Replace the callee's `Return` instruction with an assignment to the call's destination value.
- Wire the cloned blocks into the caller's control flow (call block jumps to the cloned entry; the cloned exit jumps to the block after the original call).
- Remove the original `MIRCall` instruction.

The pass runs at O2 in the fixpoint loop, after constant folding/propagation and before DCE, so that inlined code is immediately cleaned up. The pass is idempotent: once all eligible call sites are inlined, a second run is a no-op (no new call sites match because the callee functions still exist but their call sites are gone).

## Phase 1 — Inlining heuristic design

- [ ] Add `InlineHeuristic` dataclass to `mapanare/mir_opt.py`:
  - `max_body_size: int = 20` (MIR instruction count)
  - `budget: int = 200` (call_count * body_size cap)
  - `allow_recursive: bool = False`
- [ ] Add `is_recursive(fn: MIRFunction, module: MIRModule) -> bool` helper: walk the callee's instructions, check if any `MIRCall` targets the same function name or any function in the same SCC (simple: direct recursion only for v4.87.0; mutual recursion detection deferred to v4.88.0+)
- [ ] Add `count_calls(fn_name: str, module: MIRModule) -> int` helper: count how many `MIRCall` instructions across all functions target `fn_name`
- [ ] Add `should_inline(callee: MIRFunction, call_count: int, heuristic: InlineHeuristic) -> bool` predicate
- [ ] Add `@noinline` metadata check: `MIRFunction.metadata` dict, key `"noinline"` (set during lowering from `@noinline` decorator)

## Phase 2 — Inline transformation

- [ ] Implement `clone_function_body(callee: MIRFunction, prefix: str) -> list[BasicBlock]`: deep-copy all blocks, rename every `Value.name` with `prefix + original_name`
- [ ] Implement `substitute_params(blocks: list[BasicBlock], params: list[Value], args: list[Value]) -> None`: replace parameter values with argument values throughout the cloned body
- [ ] Implement `replace_return(blocks: list[BasicBlock], dest: Value, continuation_block: str) -> None`: replace `Return(val)` with `Copy(dest=dest, src=val)` + `Jump(continuation_block)`
- [ ] Implement `wire_inline_site(caller: MIRFunction, call_block_idx: int, call_inst_idx: int, cloned_blocks: list[BasicBlock], continuation_block: str) -> None`: splice the cloned blocks into the caller
- [ ] Implement `inline_small_functions(fn: MIRFunction, module: MIRModule, stats: MIRPassStats, heuristic: InlineHeuristic) -> bool`: the top-level pass. Iterates over call sites, evaluates heuristic, performs transformation. Returns `True` if any inlining occurred.

## Phase 3 — Wire into O2 pipeline

- [ ] Add `functions_inlined: int = 0` to `MIRPassStats`
- [ ] In `optimize_function()`, add `inline_small_functions` call at O2 level, positioned after constant propagation and before DCE:
  ```python
  if level >= MIROptLevel.O2:
      changed |= copy_propagation(fn, stats)
      changed |= inline_small_functions(fn, module, stats, heuristic)  # NEW
      changed |= branch_simplification(fn, stats)
      changed |= unreachable_block_elimination(fn, stats)
      changed |= dead_code_elimination(fn, stats)
      changed |= agent_inlining(fn, stats)
  ```
- [ ] Pass the `MIRModule` reference through `optimize_function()` (currently it only receives the function; the inlining pass needs module-level visibility to look up callees). Signature becomes `optimize_function(fn, module, level, stats)`.
- [ ] Update `optimize_module()` to pass `module` to `optimize_function()`

## Phase 4 — Testing

- [ ] Unit tests in `tests/mir/test_inline.py`:
  - `test_inline_small_function`: callee with 5 instructions, 1 call site -- inlined
  - `test_no_inline_large_function`: callee with 25 instructions -- not inlined
  - `test_no_inline_recursive`: recursive callee -- not inlined (fib)
  - `test_no_inline_decorator`: callee marked `@noinline` -- not inlined
  - `test_budget_exceeded`: callee called 20 times with 15 instructions (300 > 200) -- not inlined
  - `test_budget_within`: callee called 5 times with 10 instructions (50 < 200) -- inlined at all 5 sites
  - `test_inline_preserves_ssa`: after inlining, all Value names are unique within the caller
  - `test_inline_return_wiring`: Return in callee becomes Copy + Jump to continuation
  - `test_inline_multiple_blocks`: callee with 3 blocks inlines correctly
  - `test_inline_void_return`: callee returning void -- Return becomes Jump (no Copy)
- [ ] Golden tests: run all 57 golden tests with `-O2`. All must pass.
- [ ] Verify fib(35) does NOT inline the recursive `fib` call (expected: heuristic rejects recursive functions)
- [ ] Verify sort benchmark helper functions DO inline (expected: small comparison/swap functions)

## Phase 5 — Benchmark

- [ ] Run the 5-program benchmark suite (fib, concurrency, stream_pipeline, matrix_mul, agent_pipeline) at `-O2` with inlining enabled
- [ ] Record results to `benchmarks/optimizer/v4.87.0-delta.json`:
  - Per-program: time_ms, speedup_vs_v4.86.0, instructions_inlined, code_size_bytes
  - Aggregate: geometric mean speedup
- [ ] Verify code size does not exceed 2x of pre-inlining for any single function
- [ ] Run `MIRPassStats` and record `functions_inlined` count per benchmark

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.87.0]` entry -- "MIR inlining pass: cost-model-driven function inlining at O2, first interprocedural MIR optimization"
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `inline_small_functions()` pass exists in `mir_opt.py` | `grep "def inline_small_functions" mapanare/mir_opt.py` |
| 2 | Inlining heuristic documented (max_body_size, budget, recursive check) | docstring or comment block |
| 3 | O2 pipeline includes inlining pass | `optimize_function` source |
| 4 | 10+ unit tests in `tests/mir/test_inline.py` | `pytest tests/mir/test_inline.py -v` |
| 5 | All 57 golden tests pass at O2 | `pytest tests/golden/ -v` |
| 6 | fib(35) does not inline recursive call | test assertion |
| 7 | Benchmark delta recorded | `benchmarks/optimizer/v4.87.0-delta.json` exists |
| 8 | No code size explosion > 2x for any function | benchmark data |
| 9 | `make lint` + `make test` pass | CI log |

---

## What this release does NOT do

- **Mutual recursion detection** -- v4.87.0 detects direct recursion only. Mutual recursion via SCC analysis is a future enhancement.
- **Profile-guided inlining** -- the cost model is static. PGO-driven inlining is a v5.x topic.
- **Cross-module inlining** -- inlining only operates within a single `MIRModule`. LTO-style cross-module inlining requires the linker (v5.x).
- **Self-hosted mir_opt.mn** -- the inlining pass is Python only. Porting to the self-hosted compiler is tracked but not part of this release.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Inlining causes code size explosion | medium | high | Budget cap (200), per-function size check in benchmarks, test for 2x limit |
| SSA name collision after inlining | medium | high | Fresh prefix per inline site; unit test `test_inline_preserves_ssa` |
| Fixpoint loop non-convergence after adding inlining | low | high | Inlining is idempotent (inlined sites are gone); explicit test for convergence |
| Performance regression from increased function size (cache pressure) | low | medium | Benchmark will reveal; budget cap limits exposure |
| Inlining a function with side effects changes program semantics | low | critical | Inlining is semantics-preserving by construction (clone, not rewrite); side effects execute in the same order |

---

## After v4.87.0

v4.88.0 adds loop detection (natural loops via dominator tree), loop-invariant code motion, and strength reduction -- the classic loop optimization pair.
