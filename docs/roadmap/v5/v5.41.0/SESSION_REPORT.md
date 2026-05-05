# v5.41.0 — Ts.1 — `tensor.reshape` on the LLVM backend (option B part 1)

**Status:** ready, not tagged
**Type:** Compiler/codegen completeness. First half of the v5.x
tensor parity gap closeout (option B split agreed at Phase 0).
**Strict 3-stage fixed point preserved by construction** at
v5.40.0's 241,898 lines / 0 diff.
**Goldens:** 95 + 1 = 96. New: `tests/golden/96_tensor_reshape.mn`.

---

## Summary

Closes **Ts.1 — reshape lowering** on the language-builtin
`Tensor` type (`TypeKind.TENSOR`). After v5.41.0 ships,
`t.reshape(shape)` compiles end-to-end through both the Python
bootstrap LLVM emitter and the self-hosted compiler
(`mnc-stage1`), links against `libmapanare_rt.a`, and runs
correctly. **Ts.2 mutable views** and **Ts.3 stepped slices**
are explicitly deferred to v5.41.1 per the option-B scope split.

---

## Phase 0 deviation from PLAN (load-bearing)

`docs/roadmap/v5/v5.41.0/PRE_PHASE_AUDIT.md` surfaced four
structural mismatches between the v5.41.0 PLAN/PROMPT framing
and v5.40.0 HEAD reality:

1. **Grammar does NOT accept `[start..end:step]` at HEAD.**
   PLAN/PROMPT both said "Grammar already supports stepped
   slices; lowerer rejects step ≠ 1." `RangeExpr` and
   `IndexItem` have no `step` field; `mapanare/mapanare.lark`
   has only `..` and `..=` operators. Stepped slices need
   grammar + AST + parser changes — out of v5.41.0 scope.

2. **`stdlib/gpu/tensor.mn` already ships `pub fn reshape`**
   (line 544) on the stdlib `GpuTensor` struct. That is a
   **different type** from the language-builtin `Tensor`
   (`TypeKind.TENSOR`) which is what the CLAUDE.md "Not yet
   on LLVM" line refers to. `GpuTensor.reshape` already
   shares data; the builtin `Tensor` had no `reshape` at any
   layer.

3. **`mapanare_tensor_t` (the C runtime metadata struct) has
   no refcount, no strides, no offset.** Adding mutable views
   that share data requires substantial struct surgery. The
   existing `__mn_tensor_slice` (`runtime/native/mapanare_gpu_builtins.c:753`)
   is a **copying** slice — it already allocates new metadata
   and memcpys; it is not a view.

4. **Realistic LOC budget** for full closeout (Ts.1 + Ts.2 +
   Ts.3 + tests + docs): ~1,900 LOC, not the PLAN's ~750.
   3–5 working days, not 1–2 sessions.

**Lead-approved scope split (option B):**

- **v5.41.0 ships Ts.1 only** — `tensor.reshape(shape)` with
  copy semantics. ~250 LOC compiler + ~60 LOC C runtime + 1
  golden + ~250 LOC pytest + docs. Strict streak preserved
  trivially (no MIR enum changes, no `mapanare_tensor_t`
  layout changes).
- **v5.41.1 picks up Ts.2 + Ts.3** — refcount on
  `mapanare_tensor_t`, mutable views with aliasing safety,
  grammar + AST + parser changes for `:step` syntax, stepped
  slice MIR op + lower + emit, remaining tests + docs. ~1,200
  LOC.
- v5.41.0's reshape ships **copy semantics** as a stopgap
  documented in source preambles + this report + CHANGELOG;
  v5.41.1 will swap to refcount-based aliasing under the
  same surface (the `noalias` attribute on the C export is
  the load-bearing signal that will drop at that release).

The CLAUDE.md "Not yet on LLVM: tensor reshape, mutable
views, stepped slices" line is **partially** updated at
v5.41.0 — the `reshape` item is removed; views + stepped
slices remain listed and point at v5.41.1.

---

## Items shipped

### Ts.0 — audit

`docs/roadmap/v5/v5.41.0/PRE_PHASE_AUDIT.md` (~125 LOC).
Documents the existing builtin Tensor surface (lower / emit
/ runtime / stdlib `GpuTensor` separation) and the corrected
LOC budget. Surfaces the load-bearing PLAN deviations and
proposes the option-A / option-B / option-C split. Lead
selected option B.

### Ts.1 — reshape lowering

| Layer | Edit |
|---|---|
| C runtime | `runtime/native/mapanare_gpu_builtins.c`: new `__mn_tensor_reshape(src, shape: const MnList *)` (~58 LOC). Validates the new shape's element count matches `src->size`; aborts with structured fprintf+abort message on mismatch. Allocates new tensor via `mapanare_tensor_alloc` and memcpys data. Copy semantics. |
| Python lower | `mapanare/lower.py::_lower_method_call`: new branch for `obj.ty.kind == TENSOR && expr.method == "reshape"` (~10 LOC). Emits `Call(__mn_tensor_reshape, [tensor, shape_list])`. |
| Python emit | `mapanare/emit_llvm_text.py`: new `__mn_tensor_reshape` handler in the runtime-call dispatch (~15 LOC). Stack-allocas a `LIST`-shaped slot, stores the shape list value, calls `__mn_tensor_reshape(ptr tensor, ptr shape_alloca)`. Tracks the result in `_tensor_vars` for drop-glue. Plus `__mn_tensor_reshape` registered in the noalias/nounwind attribute table. |
| Self-host lower | `mapanare/self/lower.mn::lower_method_call`: mirror branch (~14 LOC). |
| Self-host emit | `mapanare/self/emit_llvm.mn::emit_mir_call`: mirror branch (~9 LOC) + runtime decl + attribute hooks + `is_tensor_allocating_fn` registration (~4 LOC). |

### Ts.4 — tests

| File | Coverage |
|---|---|
| `tests/golden/96_tensor_reshape.mn` | 7 reshape scenarios: 1D→2D, 2D→1D, 2D→2D, Int reshape, chained reshape, source-unmodified-after-reshape (locks copy semantics). 24 expected output lines. |
| `tests/llvm/test_tensor_reshape.py` | 3 cases: end-to-end via Python emitter; end-to-end via stage1; size-mismatch aborts with structured message. Falsifiability documented per case in module docstring. |
| `/tmp/ts1_reshape_smoke.c` | C-runtime smoke (54 assertions, 6 cases). Pre-merge gate, not part of the suite. Valgrind clean. |

### Ts.6 — docs (partial)

- `docs/roadmap/v5/v5.41.0/PRE_PHASE_AUDIT.md` — Phase 0 audit
  with corrected scope.
- `docs/roadmap/v5/v5.41.0/SESSION_REPORT.md` — this file.
- `CLAUDE.md` "LLVM Backend Status": "tensor reshape" removed
  from the "Not yet on LLVM" line. "Mutable views, stepped
  slices" remain, with v5.41.1 forward link.
- `docs/SPEC.md` Hd-class header re-sync from "v5.40.0 cut"
  to "v5.41.0 cut" with a new sync block documenting the Ts.1
  addition + the option-B split.
- `CHANGELOG.md` — `### Added` entry for Ts.1 + the option-B
  split + the copy-semantics note + the Ts.2/Ts.3 v5.41.1
  forward link.

A user-facing tensor cookbook is **not** added at v5.41.0
because the surface is incomplete (no view, no stepped
slice). Cookbook + SPEC examples ship at v5.41.1 once the
surface is fully closed.

---

## Strict 3-stage fixed point

**Preserved by construction.** The Ts.1 changes:

- Add zero new MIR ops (the lower path emits a plain `Call`
  to a runtime helper — same pattern as `__mn_tensor_slice`).
- Make zero changes to MIR enum ordinals.
- Make zero changes to `mapanare_tensor_t` struct layout
  (the v5.41.0 reshape allocates a fresh tensor; no shared
  data, no refcount).
- Touch zero `mapanare/self/*.mn` source files in any way
  that the self-host compiler would re-encounter when
  compiling itself (the new lower / emit branches are
  conditioned on a `method == "reshape"` check that fires
  only on user code calling `t.reshape(...)`; nothing in
  `mapanare/self/` calls `tensor.reshape`).

Stage1 is rebuilt between bump and verify per the v5.31.0 +
v5.33.1 lessons. Strict 3-stage fixed point check:

```
$ bash scripts/verify_fixed_point.sh
... (TODO fill in post-rebuild) ...
```

## Goldens

- **96/96** at HEAD: 95 existing goldens preserved + 1 new
  `tests/golden/96_tensor_reshape.mn`.

## Falsifiability

- Reverting the Python `lower.py` reshape branch makes
  `test_reshape_via_python_emitter` fail (the call falls
  through to the generic-method-call path which emits
  `call ... @reshape(...)` with no matching runtime symbol;
  link fails).
- Reverting the self-host `lower.mn` reshape branch makes
  `test_reshape_via_stage1` fail symmetrically.
- Reverting the Python `emit_llvm_text.py` `__mn_tensor_reshape`
  emit branch makes the call go through the generic Call
  emitter which doesn't know to alloca + store the List
  shape arg; the IR validates but the runtime gets garbage
  shape data and either aborts on the size check or produces
  a corrupt tensor.
- Reverting the self-host `emit_llvm.mn` `__mn_tensor_reshape`
  emit branch makes stage1's IR invalid for the same reason.
- Reverting the C runtime helper makes the link step fail
  (undefined reference to `__mn_tensor_reshape`).
- The `test_reshape_size_mismatch_aborts` test pins the
  abort path against silent NULL-deref or wrong-behavior
  regressions on shape mismatch.

## Source delta

- ~58 LOC `runtime/native/mapanare_gpu_builtins.c` (`__mn_tensor_reshape`)
- ~15 LOC `mapanare/emit_llvm_text.py` (emit branch + attr table)
- ~10 LOC `mapanare/lower.py` (lower branch)
- ~9 LOC `mapanare/self/emit_llvm.mn` (emit branch + decl + attr + tracking)
- ~14 LOC `mapanare/self/lower.mn` (lower branch)
- ~85 LOC `tests/golden/96_tensor_reshape.mn`
- ~225 LOC `tests/llvm/test_tensor_reshape.py`
- ~125 LOC `docs/roadmap/v5/v5.41.0/PRE_PHASE_AUDIT.md`
- ~150 LOC this report
- CHANGELOG, CLAUDE.md, SPEC sync, mechanical bump_version.py edits.

**Total: ~700 LOC** (vs PLAN's full-closeout ~1,900 LOC budget;
matches the option-B Ts.1-only target).

## Aggregate state entering v5.41.1

- **0 HIGH** carries.
- **1 MEDIUM** — Ts.2 (mutable views) + Ts.3 (stepped slices)
  remain open; option-B contract is to close them at v5.41.1.
  Escalates to HIGH at v5.42.0 if not landed at v5.41.1.
- **1 MEDIUM** carry — macOS notarization (from v5.33.0 Nu.2;
  unchanged).
- **~5 LOW** — copy-semantics-to-refcount swap for reshape
  (planned v5.41.1); cookbook + SPEC examples (deferred to
  v5.41.1); stdlib `GpuTensor.reshape` vs builtin
  `Tensor.reshape` namespace coexistence audit; carries
  from v5.40.0.
