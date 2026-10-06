# v5.41.0 — Ts.\* — tensor closeout (LLVM backend)

**Status:** PLANNING
**Type:** Compiler/codegen completeness. Closes the v5.x tensor
parity gap on the LLVM backend.
**Breaking:** No. Tensor surface has been stable since v4.45.0;
v5.41.0 just extends LLVM coverage to features the surface
already promised.
**Prerequisite:** v5.40.0 shipped (`ask` primitive). No direct
dependency, but this release bundles cleanly with manifesto
items because tensors are core to the AI-native pitch.
**Estimated effort:** 1–2 sessions. Compiler/lowering changes;
no stdlib code.

---

## Why this exists

Per CLAUDE.md "LLVM Backend Status":

> **Not yet on LLVM:** tensor reshape, mutable views, stepped
> slices (v5.x). Tensor surface stable since v4.45.0.

Three concrete features that the language grammar accepts and
the type system understands, but that don't compile through the
LLVM backend yet. They've been deferred for many releases. They
are the longest-standing v5.x parity gap.

This release closes them. After v5.41.0, every tensor operation
the language accepts compiles through the LLVM backend.

---

## Goals

1. **Ts.1** — `tensor.reshape(new_shape)`: produce a tensor with
   the same data but a different shape, where total element
   count matches. Compile-time shape check when both shapes are
   known statically; runtime check otherwise.
2. **Ts.2** — Mutable views: `let mut view = tensor.view(...)`
   that aliases tensor data; mutations through the view affect
   the underlying tensor.
3. **Ts.3** — Stepped slices: `tensor[0..10:2]` (every other
   element), `tensor[::2]` (full range, step 2). Multi-dim
   stepped slices for 2D+ tensors.
4. **Ts.4** — Tests including round-trip (reshape then reshape
   back), aliasing assertions for views, end-to-end for stepped
   slices through the LLVM backend.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Ts.1** | HIGH | **Reshape lowering.** `mapanare/lower.py` and `mapanare/self/lower.mn`: lower `tensor.reshape(shape)` to a `TensorReshape` MIR op. Emitter `mapanare/emit_llvm_text.py` produces a runtime call `__mn_tensor_reshape(t, new_shape, new_rank) -> tensor` that allocates new metadata pointing at the same data buffer. Static shape check at compile time when both shapes literal; runtime `__mn_assert_reshape_compatible` otherwise. ~150 LOC compiler + ~50 LOC C runtime. | 4h |
| **Ts.2** | HIGH | **Mutable views.** Type system already permits `mut`; codegen needs to emit views as alias of underlying buffer. New MIR op `TensorView` with shape + stride + offset. Emitter produces a struct {data_ptr, shape_ptr, stride_ptr, offset, rank, dtype} that aliases parent data. Mutation through view = pointer-to-element write. ~250 LOC compiler. | 5h |
| **Ts.3** | MEDIUM | **Stepped slices.** Grammar already supports `[start..end:step]`; lowering currently rejects step ≠ 1. Lift the rejection; lower step-N slices to a `TensorView` with stride * step. Multi-dim stepped slices compose strides per-axis. ~150 LOC compiler. | 3h |
| **Ts.4** | HIGH (gate) | **Tests in `tests/llvm/test_tensor_*.py`.** `test_tensor_reshape.py` (5 cases: 1D→2D, 2D→1D, mismatched shape error, dynamic shape, chained reshape). `test_tensor_view.py` (mutation visibility, drop-glue safety, view-of-view). `test_tensor_step_slice.py` (1D step, 2D step, negative step deferred / explicit error). Plus golden tests added to corpus: `tests/golden/tensor_reshape.mn`, `tensor_view_mutate.mn`, `tensor_step_slice.mn`. | 4h |
| **Ts.5** | LOW | **C runtime helpers** in `runtime/native/mapanare_tensor.c`. `__mn_tensor_reshape`, `__mn_assert_reshape_compatible`, `__mn_tensor_view`, `__mn_tensor_step_slice`. Most of the work is metadata bookkeeping; data is shared. ~100 LOC. | 2h |
| **Ts.6** | LOW | **Doc updates.** `docs/SPEC.md` tensor section gains examples for reshape/view/stepped slices; CLAUDE.md "LLVM Backend Status" updates to remove the parity gap line. | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.40.0 HEAD clean. Confirm goldens
  pass with current tensor surface.
- **Phase 1** — Ts.5 C runtime helpers first (codegen depends on
  the call shape).
- **Phase 2** — Ts.1 reshape lowering + emitter; goldens green
  including new `tensor_reshape.mn`.
- **Phase 3** — Ts.2 mutable views (most subtle item).
- **Phase 4** — Ts.3 stepped slices (composes with views).
- **Phase 5** — Ts.4 round out tests; Ts.6 docs.
- **Phase 6** — Bump + tag.

---

## Out of scope

- **Negative step slices** (`tensor[::-1]` reverse). Useful but
  opens questions about semantics that aren't urgent. Defer.
- **Broadcasting in views.** NumPy-style broadcasting is a
  separate feature; Mapanare's tensor type doesn't have it yet
  and adding it requires the borrow-checker arc (v6.0).
- **GPU codegen for new ops.** Reshape/view/stepped-slice on
  CPU only for v5.41.0; GPU dispatch follows once CPU lowering
  is solid.
- **WebAssembly backend coverage.** WASM emitter doesn't have
  tensor support broadly; v5.41.0 doesn't change that.
- **Strided I/O optimization.** Stepped slices may fragment
  cache lines; pure perf concern. Future release.

---

## Risk

1. **Aliasing safety.** Mutable views point into shared buffers;
   if the parent tensor is freed (drop glue) while a view is
   alive, dangling pointer. Mitigation: refcount or borrow flag
   on tensor metadata; view holds a parent reference. v6.0
   borrow checker will close this structurally; v5.41.0 needs a
   runtime guard (refcount probably; borrow flag wouldn't be
   enforced compile-time without v6.0).
2. **Shape mismatch errors.** Reshape of incompatible shapes
   (3×4 → 5×2 = 10 elements vs 12) needs to fail clearly.
   Mitigation: `__mn_assert_reshape_compatible` aborts with
   structured error; static check rejects at compile time when
   shapes are known.
3. **Stride math bugs.** Multi-dim stepped slices compose
   strides; off-by-one bugs are easy. Mitigation: Ts.4 includes
   a generative test that creates random tensors, applies
   random stepped slices, and compares to a slow reference
   implementation.
4. **MIR ABI compatibility.** Adding `TensorView` MIR op
   requires the self-hosted compiler's MIR enum to know about
   it. Mitigation: stage1 update first; verify stage1 → stage2
   → stage3 fixed point with new op present.

---

## Success criteria

- ✅ `tensor.reshape([rows, cols])` works for 1D ↔ 2D cases.
- ✅ Mutable view writes propagate to underlying tensor.
- ✅ `tensor[0..n:2]` returns every other element.
- ✅ Compile-time shape mismatch error for static cases;
  runtime abort for dynamic.
- ✅ Goldens 95/95 (with 3 new added: reshape, view_mutate,
  step_slice).
- ✅ Strict 3-stage fixed point preserved with new MIR op.
- ✅ CLAUDE.md "Not yet on LLVM" line removed.

---

## Carry-forward delta

**Closes:**
- v5.x tensor parity gap on LLVM backend (longest-standing).

**Inherits to v5.42.0:**
- Negative step slices (LOW).
- Borrow-checker closure of view aliasing safety (v6.0 carry —
  Ts.2's runtime refcount is a stopgap).
- WASM tensor coverage (LOW).
- GPU codegen for new ops (MEDIUM; users with GPU workloads
  may need this faster than CPU users).
