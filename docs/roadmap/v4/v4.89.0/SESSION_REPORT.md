# v4.89.0 Session Report — 2026-04-13

## Verdict

- Escape analysis shipped: heap-to-stack promotion for non-escaping allocations.
- 6 escape criteria implemented, known non-capturing function set (50+ runtime fns).
- Conservative guards: 4KB size cap, no promotion inside loop bodies.
- 12 new unit tests, all passing. Zero regressions (1406 core tests pass).
- Wired into O2 pipeline after strength reduction, before agent inlining.

## What shipped

### Escape analysis (`analyze_escapes`)

Walks the MIR function and identifies which allocation-producing instruction
results escape. An allocation escapes if any of 6 criteria are met:

1. **Returned** from the function (via `Return`)
2. **Stored into a struct field** (via `FieldSet`)
3. **Stored into a list/map** (via `IndexSet`, `ListPush`)
4. **Passed to an unknown/capturing function call** (not in `_NON_CAPTURING_FNS`)
5. **Captured by a closure** (via `ClosureCreate`)
6. **Sent to an agent** (via `AgentSend`, `AgentSpawn`)

Values that flow through `Copy` or `Phi` are tracked transitively via an
alias-set fixed-point computation.

### Heap-to-stack promotion (`escape_analysis_promotion`)

For each allocation-producing instruction whose result does NOT escape:
- Sets `alloc_kind = AllocKind.STACK` (annotation for the LLVM emitter)
- The emitter can use `alloca` instead of `__mn_alloc` and skip drop glue

Conservative guards:
- **4KB size cap**: allocations estimated > 4KB stay on the heap
- **Loop guard**: allocations inside loop bodies are never promoted (prevents unbounded stack growth)
- **Idempotent**: already-promoted instructions are skipped on re-runs

### Known non-capturing functions (`_NON_CAPTURING_FNS`)

50+ runtime functions known to read but never store their arguments:
- I/O: `print`, `__mn_print_*`
- Conversions: `len`, `str`, `__mn_str_from_*`
- String ops: `__mn_str_concat`, `__mn_str_eq`, `__mn_str_contains`, etc.
- Math: `__mn_pow`, `__mn_abs`, `__mn_min`, `__mn_max`
- Assertions: `__mn_assert`, `__mn_assert_msg`

### MIR infrastructure changes

- `AllocKind` enum added to `mir.py` (HEAP, STACK)
- `alloc_kind` field added to 9 allocation-producing instructions:
  `StructInit`, `EnumInit`, `WrapSome`, `WrapNone`, `WrapOk`, `WrapErr`,
  `ListInit`, `MapInit`, `InterpConcat`
- `allocations_promoted` counter added to `MIRPassStats`

## What was NOT shipped

- **Emitter-side codegen for STACK promotions**: The `alloc_kind` annotation
  is set but `emit_llvm_text.py` does not yet read it. The emitter change
  (alloca vs __mn_alloc, drop-glue skip) is a separate phase — safe to ship
  the analysis first since HEAP is the default and behavior is unchanged.
- **LICM**: Still disabled from v4.88.0 (miscompilation).
- **Loop-interior promotion**: Conservative — all loop-body allocations stay on heap.

## Test results

- 73/73 MIR optimizer tests (12 new escape analysis tests)
- 1406/1406 core compiler tests (parser, semantic, LLVM, WASM, MIR)
- 10 pre-existing failures (DWARF debug, emitter hardening, trait LLVM — unrelated)

## Files changed

| File | Change |
|------|--------|
| `mapanare/mir.py` | `AllocKind` enum, `alloc_kind` field on 9 instruction types |
| `mapanare/mir_opt.py` | `analyze_escapes()`, `escape_analysis_promotion()`, `_NON_CAPTURING_FNS`, `_estimate_alloc_size()`, `allocations_promoted` stat, O2 pipeline wiring |
| `tests/mir/test_mir_opt.py` | 12 new `TestEscapeAnalysis` tests |
| `docs/roadmap/v4/README.md` | Arc 12 table entries (v4.87.0–v4.89.0) |
| `docs/roadmap/ROADMAP.md` | Updated "Where We Are" header |
| `CLAUDE.md` | Updated current version |

## Next session should start with

- v4.90.0: Cumulative benchmark delta (v4.82.0 baseline → v4.90.0). Cross-language comparison with Go, Rust, Python.
- OR: Wire `alloc_kind` into `emit_llvm_text.py` (the actual codegen benefit of escape analysis).
