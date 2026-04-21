# Mamba -- C/Runtime Review of Mapanare v4.46.0 (Arc 3 Close)

**Reviewer:** Mamba
**Personality:** The C Minimalist -- terse, brutal, "delete this"
**Previous Version Reviewed:** v4.41.0 (PASS, 9.5/10, confidence 10/10)
**Verdict:** PASS
**Score:** 8.5 / 10
**Confidence:** 9 / 10

**Scope:** Arc 3 (v4.42.0-v4.45.0) -- Tensor Completeness. Four releases
that added tensor literals, N-D indexing, broadcasting, reductions, and
slicing to the C runtime. First runtime changes since v4.36.0.

**Files reviewed:**
- `runtime/native/mapanare_gpu_builtins.c` (773 lines -- **+509** since v4.41.0)
- `runtime/native/mapanare_runtime.c` (1,369 lines -- unchanged)
- `runtime/native/mapanare_runtime.h` (lines 329-369 -- `mapanare_tensor_t` struct, tensor API)
- `runtime/native/mapanare_core.c` (3,009 lines -- unchanged)
- `runtime/native/mapanare_core.h` (line 290 -- `mn_checked_mul`)
- `mapanare/emit_llvm_text.py` (lines 324-383 -- tensor function attrs; lines 1524-1563 -- tensor drop glue; lines 2693-2791 -- tensor dispatch; lines 3349-3395 -- `_do_tensor_init`)

## Executive Summary

509 new lines of C in one file. That is the entire Arc 3 runtime delta.
The rest of the runtime is byte-identical to v4.41.0 (which was
byte-identical to v4.36.0). The new code is concentrated in
`mapanare_gpu_builtins.c`, which went from 264 lines (GPU wrappers
only) to 773 lines (GPU wrappers + tensor literal runtime + N-D
indexing + broadcasting + reductions + slicing). 47 new exported
functions. One macro template (`DEFINE_TENSOR_BROADCAST_OPS`). The
code is structurally sound but has real problems that cost a full
point from the previous 9.5.

**The good:** The `DEFINE_TENSOR_BROADCAST_OPS` macro is the right
approach -- two instantiations (f64, i64) generate 4 internal
dispatch functions that the 16 public broadcast/scalar wrappers
delegate to. The broadcast shape computation is correct. The
reduction functions are tight loops with no allocation. Slicing
validates bounds. The drop-glue emitter correctly skips freeing a
tensor that is being returned.

**The bad:** Every tensor operation uses raw `malloc` -- the arena
allocator that exists 600 lines away in `mapanare_core.c` is
completely ignored. No buffer sharing. No views. Slicing does a full
copy. The N-D variadic ABI is a code smell that will age poorly.
The stride computation inside `__mn_tensor_slice` is recomputed per
element inside the inner loop.

Score drops from 9.5 to 8.5. The 509 lines are competent but they
introduce allocation patterns that the rest of the runtime already
solved better.

## 1. `mapanare_tensor_t` Struct Layout

```c
typedef struct mapanare_tensor {
    void    *data;       // 8 bytes
    int64_t  ndim;       // 8 bytes
    int64_t *shape;      // 8 bytes (heap pointer)
    int64_t  size;       // 8 bytes
    int64_t  elem_size;  // 8 bytes
} mapanare_tensor_t;     // 40 bytes total
```

**Overhead per tensor: 40 bytes struct + 1 heap allocation for shape
(`ndim * 8` bytes) + 1 heap allocation for data (`size * elem_size`
bytes) = 3 `malloc` calls per tensor.**

For a scalar tensor (1 element): 40 + 8 + 8 = 56 bytes of metadata
for 8 bytes of payload. 7x overhead. For a 1000-element vector:
40 + 8 + 8000 = 8048 bytes, overhead drops to <1%. Acceptable for
medium-to-large tensors. Terrible for small temporaries, which is
exactly what broadcast and reduction chains produce.

**Missing from the struct:** No strides array. No refcount. No flags
(owned vs. view). No offset. This means:

- No strided views (slicing must copy)
- No shared buffers (broadcast results are always new allocations)
- No COW semantics
- No sub-tensor aliasing

This is a v1.0 tensor struct. Adequate for the current feature set
but structurally incapable of supporting views, which the roadmap
lists for v5.x. Adding strides + offset + refcount later means
changing the struct layout, which is an ABI break for every compiled
binary.

**Recommendation:** Add `int64_t *strides` and `int32_t flags` now,
even if unused. Zero cost at runtime (NULL strides = contiguous).
Prevents ABI break later.

## 2. Allocation Strategy: malloc, Not Arena

`mapanare_tensor_alloc` at `mapanare_runtime.c:829-854`:

```c
mapanare_tensor_t *t = (mapanare_tensor_t *)malloc(sizeof(mapanare_tensor_t));
t->shape = (int64_t *)malloc((size_t)ndim * sizeof(int64_t));
t->data = calloc((size_t)total, (size_t)elem_size);
```

Three `malloc`/`calloc` calls per tensor. The arena allocator at
`mapanare_core.c:187+` (which bump-allocates from 4KB-64KB blocks
with a spinlock and free-list) is not used. The runtime has
`__mn_alloc` / `__mn_free` which route through the arena system.
Tensor code uses raw `malloc` / `free` everywhere.

`mapanare_tensor_free` at `mapanare_runtime.c:856-861`:

```c
void mapanare_tensor_free(mapanare_tensor_t *t) {
    if (!t) return;
    if (t->data)  free(t->data);
    if (t->shape) free(t->shape);
    free(t);
}
```

Three `free` calls per tensor.

**In a tight loop like `a + b + c + d` (3 broadcast ops), this
creates and destroys 2 intermediate tensors: 6 `malloc` + 6 `free`
= 12 allocator calls for the temporaries alone.** The arena would
reduce this to 2 bump-pointer increments + 0 frees (arena-scoped
lifetime).

**Why this matters:** The arena exists. It was designed for exactly
this pattern (short-lived allocations within a function scope). The
tensor code ignores it. The `__mn_alloc` function at
`mapanare_core.c:97` is 10 characters longer than `malloc`. There
is no technical reason for the bypass.

**Recommendation:** Replace `malloc` with `__mn_alloc` in
`mapanare_tensor_alloc`. Replace `free` with `__mn_free` in
`mapanare_tensor_free`. One-line changes, 6 total. This integrates
tensors into the arena system, the profiler, and the memory stats.

## 3. The 42 Tensor C Functions -- Collapse Analysis

Actual count of exported tensor functions across both files:

| Category | File | Count |
|----------|------|-------|
| Alloc/free/query (alloc, free, shape_eq, rank, size, shape_dim, print) | gpu_builtins + runtime | 10 |
| Flat get/set (get_f64, get_i64, store_f64, store_i64) | gpu_builtins | 4 |
| N-D get/set (get_f64_nd, get_i64_nd, set_f64_nd, set_i64_nd) | gpu_builtins | 4 |
| Element-wise same-shape (add/sub/mul/div_f64) | runtime | 4 |
| Matmul (matmul_f64) | runtime | 1 |
| Dispatch wrappers (add/sub/mul/div/matmul_dispatch) | runtime | 5 |
| Broadcast tensor+tensor (add/sub/mul/div x f64/i64) | gpu_builtins | 8 |
| Broadcast tensor+scalar (add/sub/mul/div x f64/i64) | gpu_builtins | 8 |
| Reductions f64 (sum, mean, max, min, argmax, argmin) | gpu_builtins | 6 |
| Reductions i64 (sum, max, min, argmax, argmin) | gpu_builtins | 5 |
| Slicing | gpu_builtins | 1 |
| GPU wrappers (gpu_tensor_add/sub/mul/div/matmul) | gpu_builtins | 5 |
| GPU helpers (tensor_from_list, list_from_tensor, tensor_borrow_free) | gpu_builtins | 3 (static) |
| **Total exported** | | **61** |

61 exported functions. Not 42. The original same-shape element-wise
ops in `mapanare_runtime.c` (4 functions) are duplicated by the
broadcast versions in `mapanare_gpu_builtins.c` (8 functions) --
the broadcast versions handle same-shape as a special case of
broadcasting (all dims equal). The 5 dispatch wrappers in
`mapanare_runtime.c` are dead code -- they just call through to the
f64 same-shape ops, ignoring the `device` parameter entirely.

**Functions that could be deleted today:**

1. **5 dispatch wrappers** (`mapanare_tensor_add_dispatch` etc.) --
   Dead code. The `device` param is `(void)device`'d on every path.
   No caller in the emitter references these. Delete.

2. **4 same-shape element-wise ops** (`mapanare_tensor_add_f64` etc.
   in `mapanare_runtime.c`) -- Subsumed by broadcast versions. The
   broadcast path handles same-shape correctly (all strides align,
   `broadcast_src_index` returns identity). Performance difference
   is the `broadcast_src_index` call overhead per element, which
   the compiler can inline away at -O2. Keep for now only if
   profiling shows the broadcast path is slower for same-shape.

**Net: 9 functions could be removed.** That is 15% of the tensor API
surface. Delete the dispatch wrappers unconditionally. Benchmark the
same-shape ops against broadcast before deleting those.

### Macro Template: `DEFINE_TENSOR_BROADCAST_OPS`

```c
#define DEFINE_TENSOR_BROADCAST_OPS(SUFFIX, CTYPE, PROMOTE)
    // generates: tensor_broadcast_op_##SUFFIX (internal)
    //            tensor_scalar_op_##SUFFIX    (internal)
```

Two instantiations: `f64` and `i64`. Each generates 2 static
functions. The 16 public broadcast/scalar wrappers are one-liner
delegates. This is the right pattern. The `PROMOTE` parameter is
unused (passed as empty) -- it was likely intended for `i32 -> i64`
promotion. Delete the parameter or use it.

The 8 operator functions (`f64_add`, `f64_sub`, ... `i64_div`) are
passed as function pointers to the macro-generated functions. The
compiler will inline these at -O2. If it doesn't, the function
pointer call per element is a performance bug. Verify with
`-Rpass=inline` or mark the op functions `__attribute__((always_inline))`.

## 4. Variadic ABI for N-D Indexing

```c
MN_EXPORT double __mn_tensor_get_f64_nd(mapanare_tensor_t *t, int64_t rank, ...) {
    int64_t idx[16];
    va_list ap;
    va_start(ap, rank);
    for (int64_t d = 0; d < rank; d++) idx[d] = va_arg(ap, int64_t);
    va_end(ap);
    int64_t flat = tensor_flat_offset(t, idx, rank);
    return ((const double *)t->data)[flat];
}
```

**The variadic ABI costs:**
- 128 bytes of stack for `idx[16]` (always, even for 1D)
- `va_start` + `va_end` overhead (register spill on x86-64 SysV ABI)
- No type safety -- wrong argument count is silent UB
- Cannot be `readonly` or `willreturn` in LLVM attrs (correctly marked
  without these in `emit_llvm_text.py:347-350`)

**The LLVM emitter already passes indices as separate i64 args:**

```
call double (ptr, i64, ...) @__mn_tensor_get_f64_nd(ptr %t, i64 2, i64 %i, i64 %j)
```

**The alternative:** Pass a pointer to a stack-allocated `[N x i64]`
array. The emitter already stack-allocates shape arrays for
`TensorInit` (line 3361). The same pattern would work for indexing:

```
%idx = alloca [2 x i64]
store i64 %i, ptr %idx.0
store i64 %j, ptr %idx.1
call double @__mn_tensor_get_f64_nd(ptr %t, i64 2, ptr %idx)
```

This eliminates the variadic overhead, allows `readonly willreturn`
attrs, and makes the rank/index count mismatch detectable at the
call site.

**Severity: MEDIUM.** The variadic ABI works but it is the wrong
tool for a compiler-generated call where the argument count is
always known at compile time.

## 5. Slicing: Full Copy

`__mn_tensor_slice` at `mapanare_gpu_builtins.c:721-773`:

```c
MN_EXPORT mapanare_tensor_t *__mn_tensor_slice(
    const mapanare_tensor_t *t, const int64_t *starts,
    const int64_t *ends, int64_t rank) {
    // ... allocate result ...
    for (int64_t i = 0; i < total; i++) {
        // recompute strides INSIDE the loop (lines 748-757)
        int64_t strides[MN_TENSOR_MAX_RANK];
        strides[rank - 1] = 1;
        for (int64_t d = rank - 2; d >= 0; d--)
            strides[d] = strides[d + 1] * t->shape[d + 1];

        int64_t out_strides[MN_TENSOR_MAX_RANK];
        out_strides[out_rank - 1] = 1;
        for (int64_t d = out_rank - 2; d >= 0; d--)
            out_strides[d] = out_strides[d + 1] * out_shape[d + 1];

        // decompose, map, copy one element
    }
}
```

**Three problems:**

1. **Stride arrays recomputed every iteration.** `strides[]` and
   `out_strides[]` depend on `t->shape` and `out_shape`, which are
   loop-invariant. Hoist them above the loop. This is `O(rank *
   total)` work that should be `O(rank + total)`. For a 1000x1000
   tensor sliced to 500x500, that is 500,000 extra stride
   multiplications. LICM might save you at -O2 but you should not
   rely on the optimizer to fix an algorithmic mistake.

2. **Full copy, no view.** `t[0..2, _]` on a 1000x1000 tensor
   allocates a new 2x1000 tensor (16KB data + 40B struct + 16B
   shape) and copies 2000 elements byte-by-byte. A strided view
   would be: 40B struct + 16B shape + 16B strides = 72 bytes, zero
   copy. The current struct lacks strides, so views are impossible.
   This is the cost of the v1.0 struct layout.

3. **Byte-by-byte element copy.** Line 770:
   `for (int64_t b = 0; b < t->elem_size; b++) dst[b] = src[b];`
   `elem_size` is always 8 (sizeof(double) or sizeof(int64_t)).
   This should be `memcpy(dst, src, t->elem_size)` or, since we
   know the size, `*(int64_t *)dst = *(const int64_t *)src`. The
   byte loop defeats auto-vectorization. The compiler might optimize
   it, but `memcpy` is a contract.

**Severity: MEDIUM (stride hoist), LOW (view), LOW (memcpy).**

## 6. Reductions: 11 Functions, Missing `mean_i64`

| Reduction | f64 | i64 |
|-----------|-----|-----|
| sum | Y | Y |
| mean | Y | **N** |
| max | Y | Y |
| min | Y | Y |
| argmax | Y | Y |
| argmin | Y | Y |

`mean_i64` is missing. The LLVM emitter at `emit_llvm_text.py:732-735`
does not declare it. This is intentional -- integer mean produces a
float (or requires truncation), so the user would call `mean_f64` on
a float-converted tensor. Acceptable design choice. Document it.

The reduction functions are clean. Tight loops, no allocation, proper
empty-tensor guards with `abort()`. `sum_f64` uses naive summation
(no Kahan/pairwise), which is fine for a language runtime -- precision
is the user's problem.

## 7. Buffer Sharing Between Tensors

**There is none.** Every operation allocates a new tensor with its own
data buffer. No refcount. No COW. No view sharing. Two tensors cannot
alias the same memory.

The `tensor_from_list` helper in the GPU wrappers does borrow a
list's data pointer (`t->data = list->data`), but the tensor header
is still malloc'd and the data is never freed through the tensor
path (`tensor_borrow_free` frees only the header). This is the one
instance of shared memory, and it is a local optimization within the
GPU bridge layer, not a general mechanism.

**Impact:** `a + b` where `a` and `b` are 10000-element tensors
allocates a third 10000-element tensor. `a + b + c` allocates two:
one for `a+b` (freed by drop glue) and one for `(a+b)+c` (returned).
The intermediate is created and destroyed within the same function.
With refcounted views, the intermediate could be allocated once and
reused. Without it, a chain of N operations allocates N-1
temporaries.

## 8. Drop Glue: Tensor Cleanup at Function Exit

`emit_llvm_text.py:1524-1563`:

```python
for var_name in self._tensor_vars:
    # load alloca -> null check -> free (skip if returning this ptr)
```

Every tensor variable tracked via `_tensor_vars` gets a null-check +
conditional free at every function exit point. For a function that
creates 5 tensors (e.g., a linear regression step), this emits 5
load-null-check-branch-free sequences. Each sequence is ~8 IR
instructions, so 40 instructions of drop glue for 5 tensors.

**The implementation is correct.** It skips freeing a tensor that
equals the return value (lines 1548-1553). It handles null tensors
(from failed allocations). The only issue is code bloat -- a function
with many tensor operations will have a large drop-glue epilogue.
This is the same pattern used for strings, closures, lists, maps,
signals, and streams. Consistent. Not wrong. Not elegant either --
a scope-based arena would eliminate all of it.

**One concern:** The drop glue fires for every tracked tensor var,
including those that were already freed by user code (e.g.,
`tensor_free(t)`). The null check prevents double-free only if the
user sets the variable to null after freeing. The emitter does not
null-out freed variables. If the user manually calls free and the
drop glue fires, it is a double-free. Currently there is no
user-facing `tensor_free` in the language syntax, so this is not
reachable. But if/when one is added, the emitter must null the
alloca after the manual free.

## Carry-Forward Queue (Mamba-owned)

| # | Item | Severity | Cycles | Status | Notes |
|---|------|----------|--------|--------|-------|
| M1 | `__mn_signal_get` lockless read | MEDIUM | 5 | OPEN | No change. |
| M2 | `mn_signal_propagate` recursive | MEDIUM | 9 | OPEN | No change. |
| **M3** | **Tensor variadic N-D ABI** | **MEDIUM** | **1** | **NEW** | Should be ptr-to-array, not va_list. |
| **M4** | **Tensor slice stride recomputation in inner loop** | **MEDIUM** | **1** | **NEW** | Hoist strides above the loop. |
| **M5** | **Tensor alloc uses raw malloc, not arena** | **MEDIUM** | **1** | **NEW** | 6 one-line changes to use `__mn_alloc`/`__mn_free`. |
| L1 | `mn_arena_block_new` malloc+memset | LOW | 10 | OPEN | Eternal. |
| L2 | db/html handle tables unguarded | LOW | 5 | OPEN | No change. |
| L3 | `g_argc`/`g_argv` non-atomic | LOW | 5 | OPEN | Benign. |
| **L4** | **Tensor slice byte-by-byte copy** | **LOW** | **1** | **NEW** | Use `memcpy` or direct cast. |
| **L5** | **9 dead/redundant tensor dispatch+same-shape functions** | **LOW** | **1** | **NEW** | Delete dispatch wrappers. Benchmark same-shape. |
| **L6** | **`DEFINE_TENSOR_BROADCAST_OPS` unused PROMOTE param** | **LOW** | **1** | **NEW** | Delete or use. |
| **L7** | **No tensor struct strides/flags fields for future views** | **LOW** | **1** | **NEW** | Add now to prevent ABI break. |
| 49 | Drop-glue skip-struct-ret | LOW | 11 | OPEN | Emitter, not runtime. |
| 50 | Agent destroy drain-under-contention | LOW | 5 | OPEN | No change. |

## Runtime Size Delta

| File | v4.41.0 lines | v4.46.0 lines | Delta |
|------|---------------|---------------|-------|
| `mapanare_core.c` | 3,009 | 3,009 | 0 |
| `mapanare_io.c` | 1,717 | 1,717 | 0 |
| `mapanare_runtime.c` | 1,369 | 1,369 | 0 |
| `mapanare_gpu.c` | 2,029 | 2,029 | 0 |
| `mapanare_gpu_builtins.c` | 264 | 773 | **+509** |
| `mapanare_db.c` | 877 | 877 | 0 |
| `mapanare_html.c` | 799 | 799 | 0 |
| `mapanare_internal.h` | 63 | 63 | 0 |
| **Total** | **10,127** | **10,636** | **+509** |

509 lines. All in one file. The runtime grew 5% in one arc after 10
versions of zero growth. The growth is justified -- tensors are a
first-class type and they need runtime support. But 509 lines of
hand-rolled C for operations that a 40-line macro template could
generate is not minimalist. The broadcast macro proves the pattern
works. Extend it to reductions.

## Strengths

1. **The broadcast macro is correct.** `compute_broadcast_shape` does
   NumPy-compatible trailing-dimension alignment. `broadcast_src_index`
   maps output coordinates to source coordinates with dimension-1
   clamping. Two instantiations cover both element types. This is the
   cleanest section of the new code.

2. **`mn_checked_mul` in `mapanare_tensor_alloc`.** Overflow-safe
   product for the total element count. The rest of the runtime uses
   it. Tensor alloc uses it. Consistent.

3. **Bounds checking on N-D indexing.** `tensor_flat_offset` validates
   every dimension and `abort()`s on OOB with a diagnostic message.
   No silent corruption. The `abort()` is the right call for a
   language runtime where the compiler has already validated shapes
   at the type level.

4. **Drop glue return-value escape.** The emitter checks if a tensor
   pointer equals the return value before freeing. This prevents the
   most common use-after-free pattern (return a newly created tensor,
   drop glue frees it before the caller sees it). Correct.

5. **Null guards everywhere.** Every public function checks `!t`,
   `!t->data`, `t->size <= 0`. Defensive. Correct. Not elegant, but
   correct.

## Verdict

**PASS.** The tensor runtime is structurally sound. No memory
corruption paths. No UB (except the variadic ABI edge case, which
the compiler controls). The new code is 509 lines of competent C.

The score drops from 9.5 to 8.5 because:

- **-0.5** for ignoring the arena allocator. The entire runtime
  routes through `__mn_alloc`. Tensors don't. This is inconsistent
  and leaves performance on the table.
- **-0.5** for the slice stride recomputation, the variadic ABI,
  and the dead dispatch wrappers. These are the kind of issues that
  compound as the tensor surface grows. Fix them now while there
  are 47 functions, not when there are 200.

The 0.5 dock from v4.41.0 (M1, M2) remains unchanged. Total dock:
1.5. All items are tracked. None are blockers. The runtime is at
10,636 lines and growing in the right direction.
