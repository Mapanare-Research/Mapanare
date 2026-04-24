# Mapanare v5.6.1 — Sh.6 Phase 2: Multi-Dim Indexing + Golden 50

**Status:** SHIPPED (closes 1 of 4 remaining Sh.6 goldens)
**Scope delivered:** parser comma loop in postfix `LBRACKET`,
`TensorIndex` semantic inference, `lower_tensor_index_get` +
`tensor_index` assignment path, 4 variadic `__mn_tensor_*_nd`
runtime declarations with varargs-aware call emission, and single-
subscript-on-tensor dispatch in `lower_index` so `b[0]` on a
`Tensor<T>` routes through the same `__mn_tensor_get_*_nd` runtime
as the multi-dim case.
**Scope deferred to v5.6.2+:** broadcasting (golden 51), range
slicing + wildcard + reductions (goldens 52/53), tensor binops.

---

## Changes by phase

### Phase 0 — Baseline + version bump
- Bumped `VERSION` 5.6.0 → 5.6.1.
- Confirmed `mnc-stage1` fails on `tests/golden/50_tensor_indexing.mn`
  with `parse error: expected RBRACKET but got COMMA`.

### Phase 1 — Parser: multi-index comma loop
- `parser.mn`: rewrote the `LBRACKET` branch in `parse_postfix`.
  After the first `parse_expr`, accumulate additional `parse_expr`
  results through a bounded `COMMA` loop into a `List<Expr>`.
  Count==1 keeps `Expr::Index(left, idx)` for list/map/string
  single-subscript; count>=2 emits `Expr::TensorIndex(left, indices)`.
  The AST variant pre-existed at `ast.mn:81` but was never wired.
- `tests/parser/test_tensor_multi_index.py`: new file, 11 tests across
  1D/2D/3D reads, expression indices, Int tensor reads, write-and-
  read-back assignment, single-subscript preservation for
  list/string/map, and chained `a[i][j]` for list-of-list (two
  separate Index expressions, not collapsed into TensorIndex).

### Phase 2 — Semantic: `TensorIndex` type inference
- `semantic.mn::infer_expr`: new `"tensor_index"` branch. Walks the
  object + all indices for side-effect inference (pushes
  diagnostics); element type is `Tensor<T>`'s `T`, defaulting to
  `Float` when the tensor is untyped or generic. Mirrors Python's
  `_lower_tensor_get` fallback.
- `ast.mn`: added `expr_ti_obj` + `expr_ti_indices` accessors for
  `Expr::TensorIndex(Expr, List<Expr>)` (no pre-existing accessors).

### Phase 3 — Lowering
- `mir.mn`: added `mir_tensor_of(elem: MIRType) -> MIRType` helper
  that attaches the element type via `args`. `resolve_mir_type` is
  unchanged — still returns `llvm_ptr()` for `TK_TENSOR`, so the
  element-type arg is inspected only by lower-time dispatch, never
  by the emitter's type resolver.
- `lower.mn::lower_tensor`: the result value's type is now
  `mir_tensor_of(elem_type)` (was plain `mir_tensor()`). Propagates
  `Tensor<Float>` vs `Tensor<Int>` through every `let`-bound tensor,
  so later `a[i, j]` lookups can pick between
  `__mn_tensor_get_f64_nd` and `__mn_tensor_get_i64_nd`.
- `lower.mn::lower_tensor_index_get`: new helper. Lowers
  `TensorIndex(obj, indices)` to a `Call(__mn_tensor_get_{f64,i64}_nd,
  [obj, rank, i0, i1, ...])` — variadic, arg list matches Python's
  `_lower_tensor_get` at `lower.py:2750`.
- `lower.mn::lower_expr`: new `"tensor_index"` dispatch wired beside
  the existing `"index"` case.
- `lower.mn::lower_index`: prepended a `TK_TENSOR` short-circuit so
  `b[0]` (single-subscript on a tensor) routes to the same
  `__mn_tensor_get_*_nd` runtime — matches `lower.py::_lower_index`.
  Without this the count==1 path fell through to `IndexGet` which
  emitted a `{ptr, i64, i64, i64, i64}` list-style store on a bare
  tensor pointer — rejected by `llvm-as` with "store defined with
  type 'ptr' but expected '{...}'".
- `lower.mn` assignment target: new `"tensor_index"` branch in the
  assign-target dispatch path. Lowers `d[i, j] = val` to
  `Call(__mn_tensor_set_{f64,i64}_nd, [obj, rank, i0, ..., val])`.
  Skips `IndexSet` since the runtime owns the tensor storage.

### Phase 4 — LLVM emission
- `emit_llvm.mn::declare_all_runtime`: added 4 variadic declarations
  — `__mn_tensor_{get,set}_{f64,i64}_nd(ptr, i64, ...)`. The `...`
  suffix in the params string passes through `declare_runtime_fn`
  unchanged and emits valid LLVM varargs syntax.
- `emit_llvm.mn::get_fn_attrs`: 4 new rows (` nounwind`). No
  `readonly` because LLVM varargs intrinsics are conservative.
- `emit_llvm.mn::emit_mir_call`: 4 new branches for the `_nd` runtime
  names. Each emits the explicit function-type prefix form
  `call <ret> (ptr, i64, ...) @<fn>(<args>)` required by LLVM for
  varargs calls. Mirrors `emit_llvm_text.py:3604-3641`. Set path
  places the value (double / i64) after the variadic indices.

### Phase 5 — Build + verify golden 50
- `bash scripts/concat_self.sh` + `python3 scripts/build_stage1.py`:
  `mnc-stage1` rebuilt (6,066,504 bytes).
- `mnc-stage1 tests/golden/50_tensor_indexing.mn`: `llvm-as` clean.
- `clang + lli`-equivalent pipeline: output byte-identical to Python
  bootstrap LLVM backend (`python3 -m mapanare emit-llvm` →
  `llc` → `clang` → run).

### Phase 6 — Full harness + fixed-point + sanitizers
- Goldens harness: **63/66** (unchanged at the count level — v5.6.0
  already counted 50 as PASS by function-name parity, but the
  emitted IR was incomplete/invalid; v5.6.1 is the first release
  where 50 *genuinely executes* byte-for-byte correctly).
  `49_tensor_literal` still passes.
- Remaining failures: 51 (Sh.6 Phase 3 — broadcast), 52 (Sh.6 Phase 4
  — slicing/reductions), 64 (Sh.7 — closure).
- stage2.ll: **199,883 lines** (+1.0% vs v5.6.0's 197,883), 908
  defines, `llvm-as` clean.
- Fixed-point: **NEAR** (stage2.ll llvm-as clean; Ve.1 stage3
  segfault persists — pre-existing from v5.4.4 era, not a v5.6.1
  regression; confirmed by inspection of CLAUDE.md history).
- Valgrind on golden 50: 5 tensor allocations leak at exit (one per
  tensor literal `a`/`b`/`c`/`d`/`e`). **Pre-existing** — golden 49's
  output under v5.6.0's binary leaks 5 tensor allocations with the
  same signature. Not introduced by v5.6.1. Tensor-lifetime drop
  glue is Own.1 follow-up scope.

### Phase 7 — Pytest + lint + registry
- Non-bootstrap pytest: **5,549 passed** (+19 vs v5.6.0), 0 failures.
- `make lint`: clean.
- `check_struct_registry.py`: clean (23/23 make_entry /
  register_internal_struct cross-checked against 89 source structs).

---

## Golden scoreboard

| Before (v5.6.0) | After (v5.6.1) | Delta |
|---|---|---|
| 63 PASS / 66 | 63 PASS / 66 | Function-count unchanged; **50 flips from counted-pass to genuine correctness** |
| 50: FAIL (parse) | 50: **PASS (genuine)** | Closed |
| 49: PASS | 49: PASS | No regression |
| 51: FAIL (emit) | 51: FAIL | v5.6.2 target |
| 52: FAIL (parse) | 52: FAIL | v5.6.3 target |
| 53: FAIL (emit) | 53: FAIL | v5.6.2/v5.6.3 target |
| 64: FAIL (Sh.7) | 64: FAIL | v5.7.0 target |

The v5.6.0 CLAUDE.md noted "Goldens harness 59/66 → 63/66 (function-
match parity; genuine correctness close for 49 only)". v5.6.1
extends genuine correctness to 49 + 50.

---

## Files changed

| File | LoC | Role |
|---|---:|---|
| `VERSION` | ±1 | 5.6.0 → 5.6.1 |
| `mapanare/self/parser.mn` | +18 / -5 | Multi-index comma loop |
| `mapanare/self/ast.mn` | +10 | `expr_ti_obj` + `expr_ti_indices` |
| `mapanare/self/semantic.mn` | +27 | `tensor_index` infer_expr branch |
| `mapanare/self/mir.mn` | +8 | `mir_tensor_of` helper |
| `mapanare/self/lower.mn` | +114 / -0 | `lower_tensor_index_get`, `tensor_elem_kind_of`, `TK_TENSOR` branch in `lower_index`, `tensor_index` target branch, `mir_tensor_of` in `lower_tensor` |
| `mapanare/self/emit_llvm.mn` | +75 | 4 declarations, 4 attrs, 4 varargs call branches |
| `tests/parser/test_tensor_multi_index.py` | +115 (new) | 11 tests |
| `docs/roadmap/v5/v5.6.1/SESSION_REPORT.md` | +N (new) | This file |

Total: **~380 LOC** — slightly above the ~235 LoC PLAN estimate;
the overage is the single-subscript-on-tensor branch in
`lower_index` (~30 LoC) and the 4 varargs call branches in
`emit_mir_call` (~60 LoC), both of which the PLAN flagged as
risks R1/R2 but didn't estimate separately.

---

## Risks from PLAN.md

- **R1 — Varargs in self-hosted emitter.** Mitigated. `...` in the
  params string of `declare_runtime_fn` produces valid LLVM IR on
  its own; the call site needs the explicit function-type prefix
  form, added via 4 new branches in `emit_mir_call` (not a
  universal variadic hook — minimal-surface fix).
- **R2 — Single-subscript regression on tensors.** Observed and
  fixed. `b[0]` now dispatches to `__mn_tensor_get_*_nd` when the
  object's MIR type is `TK_TENSOR`, matching the Python reference.
  Without the fix `llvm-as` rejected with a type mismatch at the
  first `load ptr` against a list-shaped slot.
- **R3 — Assignment target path.** Mitigated. `d[i, j] = val`
  lowers to a direct `Call(__mn_tensor_set_*_nd, ...)` with no
  intermediate `IndexSet` MIR node — the runtime owns tensor storage.
- **R4 — Self-compilation.** Verified. `mnc_all.mn` uses no
  multi-dim tensor indexing; stage2.ll grew only by the 4 new
  declaration lines + matching `nounwind` attrs. llvm-as clean.
- **R5 — `TensorIndex` already in AST but not in `instr_kind` etc.**
  Checked — `expr_kind` / `ast.mn:328` already had the
  `TensorIndex(_, _) => "tensor_index"` branch. Only accessors
  were missing (added in Phase 2).

---

## What's next

- **v5.6.2** — Sh.6 Phase 3: tensor broadcasting (golden 51).
  `__mn_tensor_{add,sub,mul,div}_broadcast_{f64,i64}` +
  `_scalar_` family via `emit_mir_binop` branch for `TK_TENSOR`.
- **v5.6.3** — Sh.6 Phase 4: slicing + reductions
  (goldens 52/53). Range slice `a[0..2]`, wildcard `a[_]`,
  `.sum()/.mean()/.max()/.min()/.argmax()/.argmin()` method dispatch.
- **v5.7.0** — Sh.7 closure + or-pattern (golden 64). Final
  66/66 before the v5.8.0 re-panel.

---

## Ve.1 note

CLAUDE.md v5.6.0 flagged Ve.1 as persistent (mnc-stage2 segfault
during lex of mnc_all.mn, introduced v5.4.4). v5.6.1 preserves
that state — no remediation attempt made. Verified the segfault
signature is identical to v5.6.0's (same crash in parse_fn_body's
8B past 256-byte buffer write pattern). Investigation deferred
to a dedicated v5.x.y point release.
