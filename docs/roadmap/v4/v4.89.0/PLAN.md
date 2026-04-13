# Mapanare v4.89.0 — Escape Analysis: Heap-to-Stack Promotion

> **Arc 12 release 3.** The final new optimization pass before the
> cumulative benchmark. v4.87.0 added inlining, v4.88.0 added loop
> optimizations, v4.89.0 adds escape analysis -- the last of the
> three MIR-level optimizations planned for Arc 12.
>
> Escape analysis determines whether a heap allocation's lifetime is
> confined to the function that created it. If so, the allocation can
> be promoted to a stack allocation (`alloca` in LLVM), eliminating
> malloc/free overhead entirely. This is the optimization that makes
> temporary strings, intermediate Result/Option wrappers, and
> short-lived agent structs free at runtime.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.88.0
**Delta review:** No
**Full panel:** No (v4.91.0)
**Estimated work:** 1 sprint
**Theme:** Escape analysis for heap-to-stack promotion. Eliminate malloc/free for function-local temporaries.

---

## Scope

Mapanare's runtime uses arena-based allocation (`mapanare_alloc` in the C runtime). Every struct, string, list, and map created at runtime goes through the arena. While arena allocation is fast (bump pointer), it still has overhead: the allocation call, potential arena growth, and the implied free (arena reset or explicit `mapanare_free`).

Many allocations are purely local: a temporary string built for interpolation, a Result wrapper returned from a match arm, an Option unwrapped and immediately consumed. These allocations never escape the function -- no pointer to them is stored globally, returned, or passed to a function that might capture it.

v4.89.0 adds an escape analysis pass to `mapanare/mir_opt.py` that identifies non-escaping heap allocations and promotes them to stack allocations. The LLVM emitter already supports `alloca` for local variables; the MIR transformation changes the allocation kind from heap to stack, and the emitter handles the rest.

### Escape criteria

A heap allocation **escapes** if any of the following are true:

1. **Returned from the function.** The pointer appears in a `Return` instruction (directly or as a field of a returned struct).
2. **Stored to a non-local location.** The pointer is used as the value operand of a `FieldSet` or `IndexSet` where the target object itself escapes.
3. **Passed to an unknown function.** The pointer is an argument to a `Call` where the callee is not known to be non-capturing. Conservative: any call to a function not in the current module or not marked `@pure`/`@noescape` is considered potentially capturing.
4. **Stored to a global or module-level variable.** (Mapanare does not have mutable globals currently, but the analysis should handle this for forward-compatibility.)
5. **Captured by a closure.** The pointer appears in a `ClosureCreate` captures list.
6. **Sent to an agent.** The pointer is the value in an `AgentSend`.

A heap allocation **does not escape** if none of the above are true. The allocation can then be promoted to stack.

### Promotion

For non-escaping allocations:
- Replace the `MIRAlloc(kind=HEAP)` with `MIRAlloc(kind=STACK)`.
- Remove any corresponding `MIRFree` instruction for that allocation (stack allocations are freed automatically at function return).
- The LLVM emitter maps `MIRAlloc(kind=STACK)` to `alloca` instead of a call to `mapanare_alloc`.

## Phase 1 — Escape analysis design

- [ ] Add `AllocKind` enum to `mapanare/mir.py`: `HEAP`, `STACK` (if not already present; check current `MIRAlloc` representation)
- [ ] Add `EscapeInfo` dataclass to `mapanare/mir_opt.py`:
  ```
  @dataclass
  class EscapeInfo:
      alloc_value: Value        # the SSA value produced by the allocation
      escapes: bool = False     # True if the allocation escapes
      escape_reason: str = ""   # for diagnostics
  ```
- [ ] Implement `analyze_escapes(fn: MIRFunction, module: MIRModule) -> dict[str, EscapeInfo]`: for each heap allocation in the function, trace all uses transitively. Apply the six escape criteria above. Return a map from allocation value name to escape info.
- [ ] The analysis must be transitive: if pointer P is copied to Q (`Copy(dest=Q, src=P)`), then Q's uses also determine P's escape status. Build a points-to set per allocation.

## Phase 2 — Stack promotion transformation

- [ ] Implement `promote_heap_to_stack(fn: MIRFunction, module: MIRModule, stats: MIRPassStats) -> bool`:
  - Run `analyze_escapes` to get the escape map
  - For each non-escaping allocation: change kind from HEAP to STACK
  - For each non-escaping allocation: find and remove the corresponding `MIRFree` instruction (if any)
  - Track `heap_to_stack_promoted: int` in stats
  - Return True if any promotion occurred
- [ ] Add `heap_to_stack_promoted: int = 0` to `MIRPassStats`
- [ ] Handle edge cases:
  - Allocation used in a Phi node: if the Phi merges escaping and non-escaping paths, conservatively mark as escaping
  - Allocation in a loop: if the allocation is inside a loop body, stack promotion is still valid (alloca inside a loop is valid in LLVM, though it grows the stack frame per iteration -- gate on loop depth: only promote allocations in loops with known bounded iteration or outside loops)
  - Zero-size allocations: skip (no benefit)

## Phase 3 — Conservative escape for unknown calls

- [ ] Build a "known non-capturing" function set:
  - All builtins: `len`, `print`, `str`, `int`, `float` -- these do not capture pointer arguments
  - All functions in the current module marked `@pure`
  - All functions in the current module where we can prove the parameter does not escape (intra-module interprocedural analysis -- optional, can start with just builtins)
- [ ] Any `Call` passing the allocation pointer to a function NOT in the known set -> marks the allocation as escaping
- [ ] Document the known-set in the pass docstring for future extension

## Phase 4 — Wire into O2 pipeline

- [ ] In `optimize_function()`, add `promote_heap_to_stack` at O2 level, after LICM and before DCE:
  ```python
  if level >= MIROptLevel.O2:
      changed |= copy_propagation(fn, stats)
      changed |= inline_small_functions(fn, module, stats, heuristic)
      changed |= licm(fn, module, stats)
      changed |= strength_reduction(fn, module, stats)
      changed |= promote_heap_to_stack(fn, module, stats)  # NEW
      changed |= branch_simplification(fn, stats)
      changed |= unreachable_block_elimination(fn, stats)
      changed |= dead_code_elimination(fn, stats)
      changed |= agent_inlining(fn, stats)
  ```
- [ ] Note: escape analysis benefits from inlining having run first -- inlined callees expose their local allocations to the caller's escape analysis. This is why the pass runs after inlining in the pipeline.

## Phase 5 — Testing

- [ ] Unit tests in `tests/mir/test_escape.py`:
  - `test_local_alloc_does_not_escape`: allocation used only locally, promoted
  - `test_returned_alloc_escapes`: allocation in a Return -- not promoted
  - `test_stored_to_field_escapes`: allocation stored as field of escaping struct -- not promoted
  - `test_passed_to_unknown_call_escapes`: allocation as arg to external call -- not promoted
  - `test_passed_to_pure_builtin_does_not_escape`: allocation passed to `len()` -- still promoted
  - `test_closure_capture_escapes`: allocation in ClosureCreate captures -- not promoted
  - `test_agent_send_escapes`: allocation in AgentSend -- not promoted
  - `test_copy_transitivity`: P copied to Q, Q escapes -> P escapes
  - `test_phi_merge_conservative`: Phi merges escaping and non-escaping -> escapes
  - `test_free_removed_after_promotion`: corresponding MIRFree is removed
  - `test_loop_allocation_gated`: allocation inside unbounded loop -- not promoted (stack safety)
  - `test_multiple_allocations_mixed`: function with 3 allocations, 1 escapes, 2 promoted
- [ ] Golden tests: 57/57 at O2
- [ ] Correctness check: run all golden tests with AddressSanitizer (`-fsanitize=address`) to catch any use-after-free from incorrect promotion

## Phase 6 — Benchmark

- [ ] Run the 5-program benchmark suite at O2 with escape analysis enabled
- [ ] Record results to `benchmarks/optimizer/v4.89.0-delta.json`:
  - Per-program: time_ms, speedup_vs_v4.88.0, heap_to_stack_promoted, allocations_total
  - Expected: string-heavy benchmarks (stream_pipeline) show the most improvement
  - Expected: agent_pipeline shows moderate improvement (agent setup structs may be local)
- [ ] Memory profile: compare peak RSS before and after escape analysis on each benchmark

## Phase 7 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.89.0]` entry -- "Escape analysis: non-escaping heap allocations promoted to stack, eliminating malloc/free for function-local temporaries"
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `analyze_escapes()` exists and returns correct escape info | unit tests |
| 2 | `promote_heap_to_stack()` promotes non-escaping allocations | unit test (local_alloc_does_not_escape) |
| 3 | Escaping allocations are NOT promoted (returned, stored, captured, sent) | unit tests (6 escape-reason tests) |
| 4 | Corresponding `MIRFree` removed after promotion | unit test (free_removed_after_promotion) |
| 5 | Pass wired into O2 pipeline after inlining | `optimize_function` source |
| 6 | All 57 golden tests pass at O2 | `pytest tests/golden/ -v` |
| 7 | AddressSanitizer clean on all golden tests | ASAN log |
| 8 | Benchmark delta recorded | `benchmarks/optimizer/v4.89.0-delta.json` exists |
| 9 | `make lint` + `make test` pass | CI log |

---

## What this release does NOT do

- **Partial escape analysis** -- an allocation that escapes on one path but not another is conservatively treated as escaping. Partial escape analysis (allocate on stack, re-materialize on heap at escape point) is a JVM-class optimization deferred to v5.x.
- **Escape analysis for closures** -- closures that capture allocations always mark them as escaping. Closure escape analysis (does the closure itself escape?) is a separate, more complex analysis.
- **Stack size limits** -- v4.89.0 does not enforce a maximum stack frame size after promotion. If a function promotes many large allocations, the stack could overflow. A future pass could add a size budget.
- **Self-hosted mir_opt.mn update** -- Python only for now.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Incorrect escape analysis -> UAF | low | critical | Conservative default (unknown call = escaping). ASAN on all goldens. 12 unit tests covering every escape path. |
| Stack overflow from promoting large allocations | low | high | Gate: do not promote allocations > 4KB. Document the limit. |
| Transitive points-to analysis is expensive | medium | low | Functions with > 100 allocations are rare. Add a bail-out threshold. |
| Phi-node merge makes analysis imprecise | medium | medium | Conservative: any Phi merging escaping + non-escaping = escaping. This is correct, just imprecise. |
| Loop allocations promoted, stack grows unboundedly | medium | high | Gate: only promote allocations outside loops or in loops with known bounded iteration count |

---

## After v4.89.0

v4.90.0 is the cumulative benchmark release: re-run the full suite, compute the total delta from v4.82.0 (pre-optimization) through v4.90.0 (all LLVM + MIR optimizations), and refresh the cross-language comparison.
