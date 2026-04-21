# Viper -- Rust Review of Mapanare v4.46.0 (Arc 3 Panel: Tensor Completeness)

**Reviewer:** Viper
**Personality:** The Rust Purist -- ruthless, sarcastic, zero sugar coating
**Previous Version Reviewed:** v4.41.0 (Arc 2 Close)
**Arc Under Review:** v4.42.0 -- v4.45.0 (Tensor Completeness)
**Verdict:** PASS WITH NOTES
**Confidence:** 9/10
**Score:** 9.4/10

**Files Reviewed:**

- `mapanare/emit_llvm_text.py` (lines 244-387: `_RUNTIME_FN_ATTRS` tensor entries; lines 1132-1183: `_emit_drop_glue` dispatch; lines 1524-1563: `_emit_drop_glue_tensors`; lines 1140-1158: early return on struct-ret; lines 2726-2791: tensor reduction/broadcast/slice call emission; lines 3348-3395: `_do_tensor_init`)
- `runtime/native/mapanare_gpu_builtins.c` (lines 277-773: all 42 tensor runtime functions -- alloc, free, store, get, rank, size, shape_dim, print, N-D indexing, broadcasting, reductions, slicing)
- `runtime/native/mapanare_runtime.c` (lines 684-706: `mapanare_agent_destroy` with `message_dtor` drain; lines 829-861: `mapanare_tensor_alloc` / `mapanare_tensor_free`)
- `runtime/native/mapanare_runtime.h` (lines 231-238: `message_dtor` field definition)
- `runtime/native/mapanare_core.c` (lines 103-116: `__mn_free` / `__mn_free_sized`; lines 122-136: `mn_checked_mul`)
- `runtime/native/mapanare_io.c` (lines 1021-1060: `evp_load` CAS pattern)
- `mapanare/lower.py` (lines 2453-2528: `_lower_tensor_get`, `_lower_tensor_set`, `_lower_tensor_slice`; lines 2536-2555: `_lower_tensor_binop`; lines 2755-2782: `_lower_tensor_literal`)
- `.reviews/CARRY_FORWARD.md` (full file -- carry-forward queue status)
- `docs/roadmap/v4/v4.46.0/PRE_PANEL_AUDIT.md` (18/19 claims PASS, 1 FAIL)

---

## Executive Summary

Arc 3 shipped four releases (v4.42.0 -- v4.45.0) that delivered the entire tensor surface: literals, multi-dimensional indexing, broadcasting, reductions, and slicing. This is the first arc since the v4.27.0 -- v4.31.0 recovery era that made substantial changes to both the C runtime and the LLVM emitter simultaneously. 42 new C runtime functions. 37 new entries in `_RUNTIME_FN_ATTRS`. New drop-glue tracking for tensor variables. New MIR lowering methods. New grammar rules. New AST nodes. This is real compiler work, not LSP window dressing.

From a memory-safety and ownership lens, the work is surprisingly competent. The big architectural decision -- copy-based slicing instead of view-with-refcount -- is the correct call for this stage of the language. Views introduce aliasing, and this project does not have a borrow checker. Copy semantics mean every tensor owns its data, `__mn_tensor_free` is always correct, and there is no use-after-free possible through slicing. In Rust terms: they chose `Clone` over `Rc<RefCell<T>>`, which is the right default when you do not have lifetime analysis.

That said, I found three new issues: one MEDIUM (the `__mn_tensor_get_f64` function carries the exact same `readonly`+`willreturn` misannotation pattern that was P1 for `__mn_list_get` -- they learned the lesson and immediately re-introduced it), one MEDIUM (stride recomputation inside the inner loop of `__mn_tensor_slice`), and one LOW (integer sum reduction has no overflow protection despite the runtime providing `mn_checked_mul` for exactly this pattern). The old carry-forward items show mixed progress: P1 is CLOSED (the `__mn_list_get` attrs fix landed in v4.42.0), item #50 is CLOSED (agent destroy now drains with `message_dtor`), but item #49 (the drop-glue struct-ret early return) enters its **12th cycle** -- now the longest-lived carry-forward in project history.

The pre-panel audit's honest admission of `mean_i64` being missing (11 reductions, not 12) is noted and appreciated. Integer mean returning a float is a valid design choice. The claim should have said 11, but the omission is defensible.

---

## Progress Since Last Review (v4.41.0)

### Carry-Forward Resolution

| Item | v4.41.0 Status | v4.46.0 Status | Notes |
|------|----------------|----------------|-------|
| V1 (v4.36.0): `__mn_list_get` `readonly`+`willreturn` attrs | OPEN (3rd cycle) | **CLOSED** | Fixed in v4.42.0: `emit_llvm_text.py:253-255` now only `{"nounwind"}`. Correct. |
| V2 (v4.36.0): `evp_load`/`pcre2_load` CAS-before-init | OPEN (3rd cycle) | **STILL OPEN (5th cycle)** | `mapanare_io.c:1021-1027` unchanged. `s_evp.loaded` set to 1 before function pointers are written. Second thread can read uninitialized fn ptrs. |
| V3 (v4.36.0): `__mn_free` comment discrepancy | OPEN (3rd cycle) | **CLOSED** | Fixed in v4.34.0: `mapanare_core.c:104-107` comment now accurately describes the `__mn_free_sized` companion. |
| V4 (v4.36.0): Agent `message_dtor` not wired by emitter | OPEN (3rd cycle) | **STILL OPEN (5th cycle)** | `grep message_dtor mapanare/emit_llvm_text.py` still returns no matches. Runtime mechanism works; emitter never sets it. |
| V1 (v4.41.0): Debounce timer leak on close | OPEN (1st cycle) | **NOT CHECKED** | LSP code untouched in Arc 3. Carrying forward. |
| V2 (v4.41.0): WorkspaceIndex retains ASTs | OPEN (1st cycle) | **NOT CHECKED** | LSP code untouched in Arc 3. Carrying forward. |
| #49: Drop-glue struct-ret early return | OPEN (10th cycle) | **STILL OPEN (12th cycle)** | `emit_llvm_text.py:1157-1158` unchanged. Comment still says "tracked to v4.33.0". We are at v4.46.0. |
| #50: Agent destroy in-flight message freeing | OPEN (mechanism only) | **CLOSED** | `mapanare_runtime.c:686-696` drains inbox/outbox via `message_dtor`. Runtime-side complete. Emitter wiring (my V4) still missing. |
| P1: `__mn_list_get` attrs | OPEN (2nd cycle) | **CLOSED** | Same as V1 above. |
| P4: SPEC wording | OPEN (2nd cycle) | **CLOSED** | Fixed in v4.42.0 per pre-panel audit. |

**Resolution rate this arc: 4/10.** Better than Arc 2 (0/4). The right items got fixed -- P1 was the only MEDIUM in my carry-forward, and closing it removes the only real miscompilation risk I was tracking.

---

## Strengths

1. **Copy-based slicing is the correct ownership model.** `__mn_tensor_slice` at `mapanare_gpu_builtins.c:721-773` allocates a fresh `mapanare_tensor_t`, copies elements via byte-level `memcpy` (well, a manual byte loop -- more on that later), and returns the new tensor. The caller owns it exclusively. The slice cannot alias the source. This means `__mn_tensor_free` is always safe -- there are no dangling references through slicing, no double-free through shared data buffers, no use-after-free through invalidated views. In Rust terms, this is `fn slice(&self) -> Tensor` returning an owned value, not `fn slice(&self) -> &[T]` returning a borrow. For a language without lifetime analysis, this is the only safe choice. Views are correctly deferred to v5.x when the ownership model is mature enough to support them. Fine, I guess that doesn't suck.

2. **Tensor drop glue is structurally correct.** `_emit_drop_glue_tensors` at `emit_llvm_text.py:1524-1563` follows the exact same pattern as lists, maps, signals, and streams: iterate tracked variables, load the pointer from the alloca, null-check, return-value-check, free. The null check (`icmp eq ptr {tp}, null`) prevents double-free. The return-value check (`icmp eq ptr {tp}, {ret_val}`) prevents freeing a tensor that is being returned to the caller. Both branches correctly land at a `skip` label. The `_tensor_vars` list is populated at all four creation sites: `_do_tensor_init` (line 3394), slice (line 2756), broadcast (line 2779), and scalar-broadcast (line 2789). Every tensor that enters the function's scope is tracked. Every tracked tensor is freed or skipped. This is the right pattern.

3. **N-D indexing bounds checking aborts deterministically.** `tensor_flat_offset` at `mapanare_gpu_builtins.c:354-375` checks rank match (abort), per-dimension bounds (abort), and prints a diagnostic to stderr before aborting. The variadic wrappers at lines 378-429 check null tensor, null data, and rank > 16 before proceeding. The abort-on-OOB approach is correct -- returning a sentinel value (like the flat `__mn_tensor_get_f64` does at line 302) silently hides bugs. The N-D variants got this right. The flat variants did not. Inconsistency noted as an issue below.

4. **Checked multiplication in tensor allocation.** `mapanare_tensor_alloc` at `mapanare_runtime.c:845` uses `mn_checked_mul` for the total-size computation. This prevents integer overflow when computing `shape[0] * shape[1] * ... * shape[N]`, which would otherwise lead to a too-small `calloc` and subsequent buffer overwrite. The `mn_checked_mul` implementation at `mapanare_core.c:122-136` checks all four sign quadrants. This has been correct since v4.28.0 (Viper #13 resolution) and remains correct. Good.

5. **Broadcasting shape validation aborts, does not return garbage.** `compute_broadcast_shape` at `mapanare_gpu_builtins.c:441-456` returns -1 on incompatible shapes. The caller (`tensor_broadcast_op_f64/i64` macro at line 491-493) checks for -1 and aborts with a diagnostic message. No silent garbage, no partial computation, no uninitialized data exposure. The broadcast source-index mapping at `broadcast_src_index` (lines 460-481) correctly handles the dimension-offset calculation for tensors of different ranks. The clamping to 0 for broadcast dimensions (`if (src->shape[d] == 1) c = 0;` at line 476) is the standard NumPy rule.

6. **Runtime function attributes are correctly conservative for tensor operations.** The N-D indexing functions (`__mn_tensor_get_f64_nd`, `__mn_tensor_set_f64_nd`, etc.) at `emit_llvm_text.py:347-350` are annotated with only `{"nounwind"}` -- no `readonly`, no `willreturn`. This is correct because they call `abort()` on OOB. The broadcast and scalar operators at lines 353-368 are `{"nounwind", "noalias"}` -- correct because they return fresh allocations (noalias) and can abort on incompatible shapes (no willreturn). The reduction functions at lines 371-381 are `{"nounwind"}` only -- correct because `mean`/`max`/`min`/`argmax`/`argmin` abort on empty tensors. The lesson from P1 (`__mn_list_get`) was learned for the new functions. Almost all of them. See Issue V1 below.

7. **Agent destroy drain loop is correctly guarded.** `mapanare_agent_destroy` at `mapanare_runtime.c:684-696` drains both inbox and outbox rings, calling `message_dtor` on each message only if the destructor is non-NULL and the message pointer is non-NULL. The `while (mapanare_ring_pop(...) == 0)` loop terminates when the ring is empty. The `message_dtor` field at `mapanare_runtime.h:238` is a function pointer with clear documentation (lines 231-237). The backwards-compatibility contract (NULL dtor means caller owns lifetime) is sensible. Item #50 is CLOSED on the runtime side. The emitter wiring is still missing (my V4), but the mechanism is correct.

8. **The `_RUNTIME_FN_ATTRS` dictionary is well-organized and extensively commented.** Every tensor function group has a version annotation and a rationale comment explaining why specific attributes are present or absent. The v4.42.0 comment at line 253-254 explicitly references the P1 closure. The v4.43.0 comment at line 345-346 explains why `willreturn` is omitted for N-D variants. The v4.44.0 comment at lines 351-352 explains `noalias`. The v4.45.0 comments at lines 369-370 and 382-383 continue the pattern. This level of attribution makes review tractable and prevents future developers from "helpfully" adding `willreturn` back. Begrudgingly: this is well-documented.

---

## Issues Found

### V1. **[MEDIUM]** `__mn_tensor_get_f64` and `__mn_tensor_get_i64` marked `readonly`+`willreturn` but silently return sentinel on OOB

`emit_llvm_text.py:339-340`:

```python
"__mn_tensor_get_f64": {"nounwind", "readonly", "willreturn"},
"__mn_tensor_get_i64": {"nounwind", "readonly", "willreturn"},
```

`mapanare_gpu_builtins.c:301-310`:

```c
MN_EXPORT double __mn_tensor_get_f64(const mapanare_tensor_t *t, int64_t idx) {
    if (!t || !t->data || idx < 0 || idx >= t->size) return 0.0;
    return ((const double *)t->data)[idx];
}

MN_EXPORT int64_t __mn_tensor_get_i64(const mapanare_tensor_t *t, int64_t idx) {
    if (!t || !t->data || idx < 0 || idx >= t->size) return 0;
    return ((const int64_t *)t->data)[idx];
}
```

These functions return sentinel values (0.0 / 0) on OOB. The `readonly` attribute is technically correct -- they do not modify memory. The `willreturn` attribute is also technically correct -- they always return (they do not abort like the N-D variants). But the combination is problematic: a function marked `readonly`+`willreturn` is declared to have no observable side effects except its return value. LLVM is permitted to hoist the call out of loops, CSE identical calls, and even delete calls whose return value is unused.

The practical risk: if the compiler emits `__mn_tensor_get_f64(t, i)` in a loop where `t` is mutated between iterations (e.g., a tensor element is updated, then immediately read back), LLVM at -O2 may hoist the read before the write, returning the old value. The function dereferences through `t->data`, which is a pointer-to-mutable-data. The `readonly` attribute claims the function does not write through any pointer, which is true, but LLVM may also infer that the function's result depends only on its arguments (i.e., it does not read from memory that other functions modify). This is the `readnone` promotion risk.

This is the **exact same pattern** as the old P1 finding for `__mn_list_get`. P1 was closed in v4.42.0 by removing `readonly`+`willreturn` from `__mn_list_get`. The tensor get functions, added in the same release (v4.42.0!), carry the same attrs. The lesson was learned and immediately re-introduced in the same commit scope.

**Fix:** Change both entries to `{"nounwind"}` only, matching the N-D variants. Alternatively, keep `readonly` (it is technically correct) but drop `willreturn` to prevent the CSE/hoist combination. But given the precedent set by P1's resolution, the simplest and safest fix is `{"nounwind"}` only.

I am also noting that `__mn_tensor_shape_dim` (line 343) carries the same `readonly`+`willreturn` attrs and has the same sentinel-return pattern (`mapanare_gpu_builtins.c:323-325` returns 0 on invalid dim). Same fix needed.

### V2. **[MEDIUM]** `__mn_tensor_slice` recomputes strides inside the inner loop -- O(N*R^2) instead of O(N*R)

`mapanare_gpu_builtins.c:743-765`:

```c
for (int64_t i = 0; i < total; i++) {
    int64_t rem = i;
    int64_t src_flat = 0;
    /* Compute src strides */
    int64_t strides[MN_TENSOR_MAX_RANK];
    strides[rank - 1] = 1;
    for (int64_t d = rank - 2; d >= 0; d--)
        strides[d] = strides[d + 1] * t->shape[d + 1];

    /* Map output coords to source coords */
    int64_t out_strides[MN_TENSOR_MAX_RANK];
    out_strides[out_rank - 1] = 1;
    for (int64_t d = out_rank - 2; d >= 0; d--)
        out_strides[d] = out_strides[d + 1] * out_shape[d + 1];

    src_flat = 0;
    rem = i;
    for (int64_t d = 0; d < out_rank; d++) {
        int64_t coord = rem / out_strides[d];
        rem %= out_strides[d];
        src_flat += (coord + starts[d]) * strides[d];
    }
    // ...
}
```

Both `strides[]` and `out_strides[]` are recomputed on every iteration of the outer loop. These are loop-invariant -- they depend only on `t->shape` and `out_shape`, neither of which changes during the loop. For a 1000x1000 tensor slice (1M iterations) with rank 2, this adds 4M unnecessary multiplications.

This is not a correctness bug. It is a performance bug that compounds quadratically with rank. For the current use case (small tensors in demos), it is invisible. For the v5.x target (large tensors, potentially GPU-backed), it will be a bottleneck.

**Fix:** Hoist both stride computations above the `for (int64_t i = 0; ...)` loop. Five-line diff.

Additionally, the element copy at line 770 (`for (int64_t b = 0; b < t->elem_size; b++) dst[b] = src[b]`) should be `memcpy(dst, src, t->elem_size)`. The compiler will probably optimize the byte loop to `memcpy` at -O2, but relying on the optimizer to fix your code is not engineering.

### V3. **[LOW]** `__mn_tensor_sum_i64` has no overflow protection

`mapanare_gpu_builtins.c:671-677`:

```c
MN_EXPORT int64_t __mn_tensor_sum_i64(const mapanare_tensor_t *t) {
    if (!t || !t->data || t->size <= 0) return 0;
    int64_t s = 0;
    const int64_t *d = (const int64_t *)t->data;
    for (int64_t i = 0; i < t->size; i++) s += d[i];
    return s;
}
```

Summing N int64 values can overflow. The runtime provides `mn_checked_mul` and `mn_checked_add` (at `mapanare_core.c:122-141`) for exactly this kind of protection. The tensor allocation uses `mn_checked_mul` for shape products. The tensor sum does not use `mn_checked_add` for element accumulation. A tensor of 10 elements each set to `INT64_MAX / 5` will silently wrap.

This is LOW because: (a) the f64 path (`__mn_tensor_sum_f64`) has the same issue in principle (accumulated floating-point error), but float overflow to `+inf` is defined behavior in IEEE 754, while signed integer overflow is undefined behavior in C; (b) in practice, tensor values are small and tensor sizes are moderate in current usage; (c) the `__mn_tensor_sum_i64` function is `nounwind` but not `willreturn`, so LLVM cannot exploit the UB for miscompilation. But the UB is there.

**Fix:** Use a checked-add accumulation, or add a comment explicitly acknowledging the overflow risk and deferring to v5.x when tensor values may come from untrusted sources.

### V4. **[LOW]** `i64_div` returns 0 on divide-by-zero instead of aborting

`mapanare_gpu_builtins.c:530`:

```c
static int64_t i64_div(int64_t a, int64_t b) { return b ? a / b : 0; }
```

This is the division helper used by `__mn_tensor_div_broadcast_i64` and `__mn_tensor_div_scalar_i64`. When `b` is 0, it silently returns 0. Compare with `f64_div` at line 526 (`return a / b;`), which returns `+inf`/-inf/NaN per IEEE 754.

Silently returning 0 for integer division by zero masks bugs. The user writes `t / 0` and gets a zero tensor instead of a crash or diagnostic. A Rust implementation would panic. A Python implementation would raise `ZeroDivisionError`. A C implementation should at minimum `fprintf + abort`, matching the pattern used everywhere else in this file (broadcasting shape mismatch, OOB indexing, empty tensor reductions, null tensor access).

**Fix:** Replace with `if (!b) { fprintf(stderr, "mapanare: tensor integer divide by zero\n"); abort(); } return a / b;`.

### V5. **[LOW]** Flat `__mn_tensor_store_f64/i64` silently drop writes on OOB

`mapanare_gpu_builtins.c:289-297`:

```c
MN_EXPORT void __mn_tensor_store_f64(mapanare_tensor_t *t, int64_t idx, double val) {
    if (!t || !t->data || idx < 0 || idx >= t->size) return;
    ((double *)t->data)[idx] = val;
}

MN_EXPORT void __mn_tensor_store_i64(mapanare_tensor_t *t, int64_t idx, int64_t val) {
    if (!t || !t->data || idx < 0 || idx >= t->size) return;
    ((int64_t *)t->data)[idx] = val;
}
```

On OOB, the store is silently dropped. No abort, no diagnostic, no return value indicating failure. The N-D set variants (`__mn_tensor_set_f64_nd` at line 404, `__mn_tensor_set_i64_nd` at line 418) abort on OOB. The inconsistency between the flat and N-D error handling is confusing and error-prone.

These flat store functions are only called from `_do_tensor_init` (the tensor literal emitter at `emit_llvm_text.py:3388-3391`), where the index is always a compile-time constant `j` iterating from 0 to `len(elements)-1`. In this context, OOB is impossible unless the allocator returned a smaller buffer than requested (which would be a bug in `mapanare_tensor_alloc`). So the silent return is harmless in practice. But the inconsistency with the N-D variants is a latent trap for any future caller.

**Fix:** Add `fprintf + abort` matching the N-D variants, or add a comment explaining why the flat variants use silent-return semantics.

---

## Item #49: The Eternal Early Return (12th Cycle)

`emit_llvm_text.py:1152-1158`:

```python
# Skip compound returns that contain ptr fields -- escape analysis
# cannot follow them. v4.32.0 Viper V1 (8th cycle) asked for
# this early return to be retired because per-kind helpers now
# consult ret_ptr_fields directly, but Phase 2.2 is a pure
# refactor -- tracked to v4.33.0 as CARRY_FORWARD.md row #49.
if ret_ty.startswith("{") and ret_ty not in (VOID, I1, I64, DBL) and "ptr" in ret_ty:
    return
```

This is still here. The comment says "tracked to v4.33.0". We are at v4.46.0. That is 13 versions past the tracking target.

The early return skips ALL drop glue (strings, closures, boxed enums, lists, maps, signals, streams, AND tensors) for any function that returns a struct containing a pointer field. The per-kind helpers (lines 1165-1183) already consult `ret_ptr_fields` to avoid freeing pointers that escape through the return value. The early return makes those guards unreachable for struct-returning functions.

For tensors specifically: if a function allocates a tensor and also allocates a list, and returns a struct containing the tensor pointer, the early return at line 1157-1158 causes the list to leak. The tensor is also not freed (which is correct -- it is being returned), but the per-kind check at `_emit_drop_glue_tensors:1548-1553` already handles this case correctly via the return-value pointer comparison.

I have been asking for this to be removed since v4.18.0 era. Twelve cycles. The infrastructure to remove it has existed since v4.32.0. The per-kind helpers have been refactored, tested, and proven to handle the escape-analysis correctly for every resource type. The early return is a safety net that prevents the safety net from running.

**Recommendation:** Delete lines 1152-1158. Run the full test suite. If anything breaks, fix the per-kind helper that broke. But I predict nothing breaks, because the per-kind helpers already do the right thing. If I am wrong, the test suite will tell you. This is the definition of dead code that prevents live code from running.

---

## Recommendations

### For v4.47.0 (immediate)

1. **V1 (MEDIUM):** Remove `readonly`+`willreturn` from `__mn_tensor_get_f64`, `__mn_tensor_get_i64`, and `__mn_tensor_shape_dim` in `_RUNTIME_FN_ATTRS`. One-line change per entry. This is the exact same bug that was P1, closed in v4.42.0 for `__mn_list_get`, and reintroduced in the same release for tensor functions. Do not let this reach a 2nd cycle.

2. **V2 (MEDIUM):** Hoist stride computation above the inner loop in `__mn_tensor_slice`. Five-line diff. Also replace the byte-copy loop with `memcpy`.

3. **Item #49 (12th cycle):** Delete the drop-glue struct-ret early return. Run the test suite. Close the oldest carry-forward in project history.

### For v4.48.0 (near-term)

4. **V3 (LOW):** Add overflow commentary or checked-add accumulation to `__mn_tensor_sum_i64`.

5. **V4 (LOW):** Change `i64_div` to abort on divide-by-zero instead of returning 0.

6. **V5 (LOW):** Align flat store OOB handling with N-D set variants (abort or document).

### Carry-forward (all still open from prior reviews)

7. **My V4 from v4.36.0 (LOW, 5th cycle):** Wire `message_dtor` in the LLVM emitter's agent-wrap code. The runtime mechanism exists and works; the emitter never sets the field. All agents currently get `message_dtor = NULL`, meaning in-flight messages are discarded without freeing on destroy.

8. **My V2 from v4.36.0 (LOW, 5th cycle):** Migrate `evp_load` to `pthread_once`. `mapanare_io.c:1021-1027` still has the CAS-before-init pattern where `s_evp.loaded` is set to 1 before function pointers are written. A concurrent reader can see `loaded=1` with uninitialized fn ptrs.

9. **My V1 from v4.41.0 (LOW, 3rd cycle):** Cancel debounce timers in `on_close`.

10. **My V2 from v4.41.0 (LOW, 3rd cycle):** Clear retained ASTs after reference collection.

---

## Post-Production Health Assessment

Arc 3 is the most memory-safety-relevant arc since the v4.27.0 -- v4.31.0 recovery era. It adds real C runtime surface (42 functions), real drop-glue tracking, and real ownership semantics. The fact that it shipped with only two MEDIUM issues and three LOWs is genuinely good -- the tensor runtime is defensive (null checks, bounds checks, overflow protection in allocation), the drop glue correctly tracks all creation sites, and the copy-based slicing eliminates an entire class of aliasing bugs.

The decision to defer views to v5.x is the single most important architectural decision in this arc, and it is the correct one. Views require either a borrow checker (Rust-style), reference counting (Swift-style), or garbage collection (Python-style) to be safe. Mapanare has none of these. Copy semantics are O(n) in the slice size, but they are always safe. When the ownership model matures to support views (the roadmap says v5.x), the transition from copy to view is a backwards-compatible performance optimization -- the semantics do not change, only the implementation.

The V1 finding (tensor get attrs) is disappointing because it is a known-pattern bug. The P1 closure for `__mn_list_get` was resolved in the same release that introduced the tensor functions. Whoever wrote the `__mn_tensor_get_f64` entry in `_RUNTIME_FN_ATTRS` either did not know about P1 or did not connect the dots. The fix is trivial. The lesson is: when you close a bug pattern, grep the entire `_RUNTIME_FN_ATTRS` dict for the same pattern. Do not fix one instance and introduce three more in the same commit.

Item #49 is becoming a joke. Twelve cycles. The comment references v4.33.0. The carry-forward ledger says "v4.32.0 Phase 2.2 (opportunistic) or v4.33.0+". The per-kind helpers that make the early return redundant have been in place since v4.32.0. The early return prevents tensor drop glue from running on struct-returning functions. The test suite presumably passes because no test currently exercises a function that allocates both a tensor and another resource and returns a struct containing one of them. That does not mean the code is correct -- it means the test coverage has not caught it yet. Delete the early return. If I have to mention this at v4.51.0 I am going to be genuinely upset.

---

## Raw Notes

- `mapanare_tensor_t` struct is `{ndim, elem_size, size, *shape, *data}` -- straightforward owned-data layout. No refcount, no view pointer, no aliasing. Clean.
- `calloc` for data buffer (line 850) is correct -- zero-initialized prevents info leaks from uninitialized memory. Good.
- `mn_checked_mul` for shape product (line 845) prevents overflow-based under-allocation. Good.
- The `mapanare_tensor_free` at line 856-861 is null-safe (`if (!t) return`), frees all three allocations (data, shape, struct), and does not double-free. Correct.
- The `MN_TENSOR_MAX_RANK` limit (16) at line 438 prevents stack overflow in the VLA-style `int64_t idx[16]` arrays. This is a reasonable limit.
- The `va_list` variadic pattern for N-D indexing (lines 378-429) is inherently unsafe -- wrong rank means reading garbage from the stack. But the rank is always a compile-time constant emitted by `_lower_tensor_get` / `_lower_tensor_set` at `lower.py:2468-2470`, so the risk is low in practice. A varargs-free API (pass an `i64*` array like `__mn_tensor_slice` does) would be safer, but this ships and works.
- The `f64_div` helper at line 526 (`return a / b;`) will produce `+inf` or NaN for zero divisor. This is IEEE 754 compliant and correct. No issue.
- All 16 broadcast functions at lines 536-569 delegate to the macro-generated `tensor_broadcast_op_f64/i64` at lines 484-520. The macro is clean. `abort()` on alloc failure (line 497) is correct.
- Reduction functions (lines 615-717) consistently abort on empty tensor for all operations except `sum` (which returns 0). This is a defensible design: sum of empty set is identity element (0), but mean/max/min/argmax/argmin of empty set is undefined. Good.
- `__mn_tensor_print_f64` is marked `willreturn` (line 344) which is technically wrong -- it calls `printf` which can block or fail -- but the consequence is negligible. Not flagging.
- The `_do_tensor_init` emitter (lines 3349-3395) stack-allocates the shape array (`alloca [N x i64]`), which is correct for small compile-time-known shapes. For a 16-dimensional tensor, this is 128 bytes on the stack -- well within limits.
- The lower.py tensor methods (`_lower_tensor_get`, `_lower_tensor_set`, `_lower_tensor_slice`, `_lower_tensor_binop`, `_lower_tensor_literal`) are all clean MIR emission with proper type resolution. No memory-safety surface in the lowerer.

---

## Score Justification

```
v3.47.0:  0 CRIT, 0 HIGH.  Viper score: 9.5   (PASS WITH NOTES)
v4.26.0:  0 CRIT, 6 HIGH.  Viper score: 8.0   (NEEDS WORK)
v4.31.0:  0 CRIT, 1 HIGH.  Viper score: 9.1   (PASS WITH NOTES)
v4.36.0:  0 CRIT, 0 HIGH.  Viper score: 9.5   (PASS WITH NOTES)
v4.41.0:  0 CRIT, 0 HIGH.  Viper score: 9.5   (PASS WITH NOTES)
v4.46.0:  0 CRIT, 0 HIGH.  Viper score: 9.4   (PASS WITH NOTES)
```

The score drops from 9.5 to 9.4 because:

- **-0.2 for V1 (MEDIUM):** The `readonly`+`willreturn` misannotation on tensor get functions is the same bug pattern as P1, reintroduced in the same release that closed P1. This is a process failure. The fix is trivial, but the fact that it happened at all after explicitly closing the identical bug is concerning.
- **-0.15 for V2 (MEDIUM):** Stride recomputation inside the inner loop is a correctness-adjacent performance bug that will bite when tensors scale.
- **-0.1 for V3-V5 (3 LOWs):** Integer overflow in sum, silent zero on divide-by-zero, inconsistent OOB handling.
- **-0.1 for carry-forward stagnation:** V2 (evp_load) and V4 (message_dtor wiring) from v4.36.0 are now at their 5th cycle. Item #49 is at its 12th cycle.
- **+0.45 for positive work:** Copy-based slicing ownership model (+0.15), correct tensor drop glue tracking (+0.1), proper N-D bounds checking with abort (+0.05), correct attrs on 30+ new runtime functions (+0.05), 4/10 carry-forward items closed (+0.05), honest pre-panel audit (+0.05).

Net: 10.0 - 0.2 - 0.15 - 0.1 - 0.1 + 0.45 = **9.4** (rounding from 9.9 base to account for accumulated backlog).

To reach 9.7+: fix V1 (one-line change, removes the only -O2 miscompilation risk), delete item #49 (five-line deletion), and hoist the slice strides (five-line refactor). Three fixes, one session each. The same recommendation I gave at v4.41.0 for P1 and #49, which was partially followed (P1 closed, #49 not). Do the other half.

---

**Verdict: PASS WITH NOTES.** Score: **9.4/10.** Confidence: **9/10.** The tensor runtime is well-built with correct ownership semantics. The copy-based slicing decision is architecturally sound. But the `readonly`+`willreturn` reintroduction is a process failure that should not have happened, and item #49 at 12 cycles is an embarrassment. Fix V1 and delete #49 before the next release. Everything else is LOW and can wait.

---

**End of review.**
