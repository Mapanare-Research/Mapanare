# Mapanare v5.1.2 — "MIR Passes + Benchmark Reporting (In.1 / Li.1 / Ea.1 / Bn.2 / Bn.3 / Bn.4)"

> **Fix the bugs v4.152.0 E8 uncovered and turn the passes on. Bundle
> Mamba's three-cycle benchmark-reporting carry-forwards.**
>
> v4.152.0 re-evaluated four MIR optimizer passes disabled at
> v4.111.0: `strength_reduce` (zero-ROI, kept off), but
> `inline_small_functions`, `licm`, and `escape_analysis` all had
> latent bugs in the rewrite logic that produced invalid IR. This
> release fixes those bugs and turns them on again. Mamba v4.154.0
> re-flagged **Bn.2** (wrong geomean), **Bn.3** (stale JSON version
> field — third cycle), and **Bn.4** (C benchmark asymmetry); these
> are small, unrelated fixes opportunistically bundled.

**Status:** PLANNED (skeleton)
**Breaking:** No (pure optimization; output semantics unchanged)
**Prerequisite:** v5.1.1 shipped
**Estimated work:** 2-4 sessions

---

## Why this release exists

v4.152.0 SESSION_REPORT documents three open dockets:

**In.1** (`inline_small_functions`)
> The v4.111.0 `verify_block` crash is gone (post-Sh.2/Ge.1 arcs),
> but the inliner still produces SSA name collisions. Example:
> `parse_program` after inlining has `%t4` defined twice because
> `rename_instructions` renames the inlined body but does not rename
> the caller's destination register. `llvm-as` rejects stage2.ll.

**Li.1** (`licm`)
> `block_successors` crash gone, but `hoist_instruction` leaves the
> hoisted instruction in the source block, producing duplicate
> definitions. Goldens 54 → 51 (regressions: `05_for_loop`,
> `21_list_ops`, `33_break_continue`).

**Ea.1** (`escape_analysis`)
> +0x3f3 crash gone (Ge.1 fix), pass runs cleanly but the analysis
> function is a stub: `return f` unchanged. No codegen path acts on
> the analysis, so it's dead code.

## Scope

**In scope:**
- **In.1**: extend `rename_instructions` to rename the caller's
  destination register (the `%dst` of the call) consistently with the
  inlined body's renames. Add `tests/mir_opt/test_inline_rename.py`.
- **Li.1**: `hoist_instruction` should remove the instruction from
  the source block after insertion in the preheader. Add test that
  verifies every hoisted instruction appears exactly once.
- **Ea.1**: wire `escape_analysis` output into allocation decisions:
  when a local allocation is proven non-escaping, emit
  `alloca`-on-stack rather than `malloc`-on-heap. Measure perf
  improvement on `struct_alloc` benchmark.
- Re-enable all three in `mapanare/mir_opt.py` and
  `mapanare/self/mir_opt.mn` (Python / self-hosted parity).
- **Bn.2**: recompute geomean from raw JSON in
  `benchmarks/run_benchmarks.py`; update `FINAL_REPORT_v4.153.md`
  (or its v5.x successor) with 7.31× → 1.21× trajectory, not the
  currently-reported 5.83× → 1.17×.
- **Bn.3**: one-line — `run_benchmarks.py` hardcodes
  `"version": "4.125.0"` in its JSON output; replace with a
  `VERSION` file read (same pattern Dr.1 / v4.138.0 Bo.5 used).
- **Bn.4**: rewrite `benchmarks/cross_language/struct_alloc.c` to
  return the struct by value (stack) rather than heap-allocate. This
  makes the Mn/C geomean meaningful (currently distorted by 0.033×
  outlier where C is measuring malloc throughput).

**Out of scope:**
- Re-enabling `strength_reduce` (v4.152.0 E8a showed zero-ROI; LLVM
  instcombine already covers the patterns)
- New MIR passes beyond the dormant three

## Exit criteria

- `pytest tests/mir_opt/` passes with new tests for each docket
- Strict 3-stage fixed-point still holds
- No regression in the cross-language benchmark geomean
- `struct_alloc` benchmark improves by ≥ 5% (Ea.1 stack-alloc win)
- `llvm-as` accepts every stage2.ll in the golden corpus
- Fresh benchmark run's JSON contains `"version": "5.1.2"` (not
  `"4.125.0"`); `FINAL_REPORT` geomean matches independent
  recomputation from raw JSON (Mamba's Bn.2 audit passes)
- `struct_alloc.c` returns a struct by value; Mn/C geomean with it
  excluded vs included differ by < 10% (meaningful apples-to-apples)

## Risks

**Risk 1 — fixing one breaks the others.**
These three passes run in sequence; fixing inliner renaming may
expose new PHI-insertion edge cases in LICM.
*Mitigation:* turn on one pass at a time. Commit after each. The
`fail-fast` CI matrix catches regressions fast.

**Risk 2 — Ea.1 changes memory lifetime.**
Promoting heap allocations to stack changes lifetime. Any code that
stashes a pointer into a heap-allocated struct and uses it after the
allocating function returns becomes UB.
*Mitigation:* the escape analysis must be sound before we wire it
up. If the analysis says "does not escape" but the value actually
does, we get a UAF. Fuzz with ASan.
