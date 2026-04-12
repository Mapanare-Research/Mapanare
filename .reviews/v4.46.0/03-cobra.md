# Cobra -- C++/ABI Review of Mapanare v4.46.0 (Arc 3 Panel)

**Reviewer:** Cobra
**Personality:** The Grumpy C++ Veteran -- condescending, encyclopedic, razor sharp
**Previous Version Reviewed:** v4.41.0 (score: 9.80, PASS -- zero ABI changes, LSP-only arc)
**Verdict:** PASS
**Confidence:** 10/10
**Score:** 9.45/10
**Arc Reviewed:** Arc 3 (Tensor Completeness), v4.42.0 through v4.45.0
**Primary Reviewer:** Yes -- this is the tensor arc, my domain

**Files Reviewed:**
- `runtime/native/mapanare_gpu_builtins.c` (774 lines -- all 42 tensor runtime functions)
- `runtime/native/mapanare_runtime.c` (lines 825-963 -- tensor alloc, free, shape_eq, element-wise ops, matmul)
- `runtime/native/mapanare_runtime.h` (lines 325-430 -- `mapanare_tensor_t` struct, function prototypes)
- `mapanare/emit_llvm_text.py` (lines 330-395 attr table, 660-675 type lowering, 1524-1563 drop glue, 3348-3395 TensorInit)
- `mapanare/types.py` (lines 125, 398-484 -- tensor_shape, broadcast_shape, validate_matmul_shapes)
- `mapanare/semantic.py` (lines 262-264, 435-438, 549-579, 688-751, 806-832 -- tensor type-checking)
- `mapanare/lower.py` (lines 1539-1543, 2209-2230, 2420-2564 -- tensor lowering)
- `mapanare/mir.py` (lines 295-306 -- TensorInit MIR instruction)
- `tests/golden/53_linear_regression.mn` (44 lines -- the showcase demo)
- `tests/semantic/test_tensor_broadcast.py`, `tests/llvm/test_tensor_broadcast.py`
- `tests/semantic/test_tensor_slicing.py`, `tests/llvm/test_tensor_reductions.py`
- `.reviews/CARRY_FORWARD.md`

---

## Executive Summary

Arc 3 adds four releases of tensor infrastructure: tensor literals and 1D indexing (v4.42.0), multi-dimensional indexing (v4.43.0), NumPy-style broadcasting (v4.44.0), and reductions plus slicing (v4.45.0). The central question I was asked: does Mapanare's tensor feel like a real tensor primitive or a thin wrapper around malloc'd arrays?

The honest answer is: it is a real tensor primitive -- at the language surface. The syntax is clean, compile-time shape validation is present and correct, the broadcasting semantics follow NumPy exactly, and the linear regression demo reads like idiomatic NumPy translated to a compiled language. That is genuinely impressive for four releases of work.

Beneath the surface, however, it is, in fact, a thin wrapper around malloc'd arrays. And I say this with the weary affection of someone who has watched every tensor library in history start this way. The `mapanare_tensor_t` struct is five words on the heap (data pointer, ndim, shape pointer, size, elem_size), passed through LLVM IR as an opaque `ptr`, with every operation dispatching through a C runtime call. There is no SIMD intrinsic generation, no expression-template-style fusion, no lazy evaluation, no stride metadata, no view semantics. Every binary operation allocates a new tensor. The matmul is a triple-nested loop with a comment that says "LLVM auto-vectorizer targets SIMD" which is the compiler equivalent of "the compiler will figure it out."

This is fine. This is correct for the stage of the project. But I want the record to reflect exactly what it is, because the language surface promises more than the runtime delivers, and the gap will become visible the moment anyone runs a tensor larger than a few thousand elements.

---

## 1. Tensor ABI: How Is `Tensor<Float>` Represented in LLVM IR?

### The Representation

In `emit_llvm_text.py:668-669`:

```python
if k == TypeKind.TENSOR:
    return PTR  # opaque pointer to mapanare_tensor_t
```

Every `Tensor<T>` at the IR level is `ptr`. Full stop. An opaque pointer to a heap-allocated `mapanare_tensor_t` struct:

```c
typedef struct mapanare_tensor {
    void    *data;       /* pointer to contiguous element buffer         */
    int64_t  ndim;       /* number of dimensions                        */
    int64_t *shape;      /* heap-allocated shape array (ndim elements)   */
    int64_t  size;       /* total number of elements (product of shape)  */
    int64_t  elem_size;  /* size of each element in bytes                */
} mapanare_tensor_t;
```

This is 40 bytes on LP64. Five fields, all heap-allocated independently -- the struct itself, the shape array, and the data buffer are three separate `malloc` calls.

### ABI Assessment

The opaque-pointer approach is the quaint, safe choice. It means tensor-tensor operations pass two pointers through the ABI, which SysV x86-64 handles in `rdi` + `rsi` with zero stack spill. Return values are also pointers -- single register, no sret. The `noalias` attribute on allocating functions (`__mn_tensor_alloc`, all broadcast ops, slice) is correctly applied, letting LLVM assume the returned pointer does not alias any existing memory. The `readonly` attribute on `__mn_tensor_get_f64`/`__mn_tensor_get_i64` is also correct. The `willreturn` annotations were properly stripped from operations that can `abort()` (all reductions except sum, all N-D accessors, slice). This is fastidious work.

**What it costs you:** Every tensor operation -- even `a + 5.0` on a 1D tensor of three floats -- goes through a function call to the C runtime, which mallocs a new tensor, loops over the data, and returns. There is no inlining of the loop body into the caller. There is no opportunity for LLVM to fuse `(X * w + b) - y` into a single pass over the data. Each subexpression allocates, computes, and the result gets freed at function exit by the drop glue.

In C++ with Eigen, `(X * w + b) - y` would be a single expression template that produces a `CwiseBinaryOp<..., CwiseBinaryOp<..., ...>, ...>` type, and the actual loop happens once at assignment time. Mapanare's approach creates three intermediate tensors for this expression. For the 5-element demo, nobody notices. For 10M elements, this is catastrophic.

**Verdict on ABI:** Sound. Conservative. No bugs. The `ptr`-everywhere approach avoids every possible struct-passing ABI landmine. I approve it for the current stage, with the understanding that expression fusion and view semantics are v5.x problems.

---

## 2. Shape Checking: Compile-Time vs. Runtime

This is where Arc 3 actually shines, and I will grudgingly admit it.

### Compile-Time Shape Validation

The `TypeInfo` dataclass carries an optional `tensor_shape: tuple[int, ...] | None` field (`types.py:125`). When all dimensions of a tensor literal are integer literals, the semantic checker resolves the shape at compile time. The `broadcast_shape()` function at `types.py:443-466` implements NumPy's trailing-dimension alignment rule correctly -- I checked it against the NumPy spec. The `broadcast_incompatible_dim()` helper at `types.py:469-483` identifies the failing dimension for rustc-quality diagnostics. The matmul shape validator at `types.py:417-440` handles 1x1, 2x2, 2x1, and 1x2 cases.

The semantic checker at `semantic.py:704-751` uses these to reject shape-incompatible tensor arithmetic at compile time. When shapes are known, you get an error like:

> shapes [3, 4] and [3, 5] are not broadcast-compatible for '+'; dimension 1 differs: 4 vs 5

This is better than what you get from C++ Eigen at compile time (a `STATIC_ASSERTION_FAILURE` with an inscrutable template error), and comparable to what you get from PyTorch at runtime. The fact that Mapanare can catch this statically for literals is a genuine win.

### Runtime Shape Validation

When shapes are dynamic (any non-literal dimension), `tensor_shape` is `None`, and the compile-time checks are skipped. The runtime catches mismatches:

- `compute_broadcast_shape()` in the C runtime returns -1 on incompatible shapes, then the caller aborts.
- `tensor_flat_offset()` checks per-dimension bounds and aborts on OOB.
- `mapanare_tensor_shape_eq()` is O(ndim), called on every non-broadcast binary op.

**The overhead question:** For same-shape operations (add/sub/mul/div without broadcasting), there is one `shape_eq` check per operation. This is O(ndim) where ndim is typically 1-3. Negligible. For broadcast operations, `compute_broadcast_shape()` is O(max_rank). Also negligible. The `broadcast_src_index()` function, however, is called once per output element (inside the inner loop at `gpu_builtins.c:502-504`) and does a full coordinate decomposition + remapping. This is O(ndim) per element, which for large tensors with high rank is not ideal but not catastrophic.

**Verdict on shape checking:** The dual compile-time/runtime approach is correct. Compile-time when possible, runtime when necessary. No unnecessary overhead on the fast path (same-shape ops). The broadcast inner loop could use stride-based indexing instead of per-element coordinate decomposition, but this is a performance issue (see Issue #2), not a correctness issue.

---

## 3. Broadcasting: Comparison to C++ Eigen/xtensor

### The C Runtime Macro Approach

`DEFINE_TENSOR_BROADCAST_OPS(SUFFIX, CTYPE, PROMOTE)` at `gpu_builtins.c:484-520` is a macro that stamps out two functions per type: `tensor_broadcast_op_{SUFFIX}` (tensor+tensor) and `tensor_scalar_op_{SUFFIX}` (tensor+scalar). Instantiated twice: `f64` and `i64`.

The macro approach is... quaint. It is the C equivalent of a template. Two types, four operators, two operand shapes = 16 public functions for broadcast and 8 for scalar ops. This is exactly the kind of combinatorial explosion that C++ templates solve without macros, but in C, macros are the only tool. The macros are well-structured, the function pointers (`f64_add`, `f64_sub`, etc.) are clean, and the generated code is correct. I have seen far worse.

### Versus Eigen

Eigen broadcasts via expression templates: the broadcast object computes indices lazily, and the entire expression tree is fused into a single evaluation loop. Mapanare's approach materializes every intermediate result. `X * w + b` in Eigen: one loop, zero allocations (result is sized once at assignment). In Mapanare: `X * w` allocates a tensor, then `result + b` allocates another tensor, and the first intermediate is freed at scope exit.

### Versus xtensor

xtensor uses lazy broadcasting views (`xt::broadcast(a, shape)`) that compute indices on-the-fly without materializing. Mapanare materializes.

### Is the Macro Approach "Good Enough"?

For the current feature set: yes. The macros generate correct, readable code. The function pointer indirection adds a single indirect call per operation (not per element -- the function pointer is resolved once and then the loop runs). For v4.x, where the tensor surface is being established, this is the right approach. The macro can be replaced by template-like codegen when the performance story matters (v5.x).

**One genuine concern:** The `broadcast_src_index()` helper recomputes a full coordinate decomposition for every output element. In Eigen, broadcasting is handled by stride manipulation -- if a source dimension is 1, the stride for that dimension is 0, and the flat index is computed with a single multiply-add per dimension instead of a division-modulo decomposition. This is the difference between O(1) amortized and O(ndim) per element. For rank-2 tensors this is a 2x overhead in the inner loop; for rank-8 tensors it becomes painful. See Issue #2.

---

## 4. Variadic ABI for N-D Indexing (`gpu_builtins.c:378-429`)

The multi-dimensional get/set functions use `va_list`:

```c
MN_EXPORT double __mn_tensor_get_f64_nd(mapanare_tensor_t *t, int64_t rank, ...) {
    int64_t idx[16];
    va_list ap;
    va_start(ap, rank);
    for (int64_t d = 0; d < rank; d++) idx[d] = va_arg(ap, int64_t);
    va_end(ap);
    ...
}
```

### Is `va_list` the Right Choice vs. Fixed-Rank Overloads?

**No.** And I will tell you why, with the resigned patience of someone who has debugged variadic ABI issues on six different platforms.

On SysV x86-64, variadic functions force all floating-point arguments into the integer register file via `va_arg`, even though the calling convention normally passes them in XMM registers. This is not relevant here (all indices are `int64_t`), but it sets a bad precedent.

The real problem is that `va_list` defeats LLVM's ability to inline and optimize the call. A call to a variadic function cannot be inlined by LLVM unless the callee is in the same compilation unit. Since `__mn_tensor_get_f64_nd` lives in the C runtime (a separate `.o`), LLVM cannot inline it. For a 2D tensor access `t[i, j]`, you pay: one function call, one va_list setup/teardown, a 16-element stack array fill, a bounds-check loop, and a flat-offset computation. In C++ you would write `t.at(i, j)` as a non-variadic inline function and the compiler would reduce it to two multiplies and an add.

**However.** The emitter already passes the indices as separate arguments in the LLVM IR call:

```
call double @__mn_tensor_get_f64_nd(ptr %t, i64 2, i64 %i, i64 %j)
```

This means the calling convention is "variadic in C, but the LLVM IR caller knows the exact signature." A trivial fix would be to generate fixed-arity wrapper functions in the IR (`__mn_tensor_get_f64_2d`, `__mn_tensor_get_f64_3d`) that compute the flat offset inline and call a non-variadic `__mn_tensor_get_f64_flat`. This would let LLVM inline the offset computation and potentially eliminate the function call entirely for small tensors. The variadic functions could remain as a fallback for rank > 4.

The rank cap of 16 in the `int64_t idx[16]` stack array is fine -- no sane tensor has more than 16 dimensions, and if someone tries, the early `abort()` at rank > 16 is the correct behavior.

**Verdict:** The variadic approach works, is correct, and is not a blocking issue. But it leaves performance on the table for the most common case (rank 2-3 tensor access), and the fix is straightforward. See Issue #3.

---

## 5. The 42 Runtime Functions: API Surface Bloat or Necessary?

The 42 tensor-specific `MN_EXPORT` functions in `mapanare_gpu_builtins.c` break down as:

| Category | Count | Functions |
|----------|-------|-----------|
| Lifecycle | 2 | alloc, free |
| Element access (flat) | 4 | store_f64, store_i64, get_f64, get_i64 |
| Metadata query | 3 | rank, size, shape_dim |
| Debug | 1 | print_f64 |
| N-D access (variadic) | 4 | get_f64_nd, get_i64_nd, set_f64_nd, set_i64_nd |
| Broadcast binary (f64) | 4 | add, sub, mul, div |
| Broadcast binary (i64) | 4 | add, sub, mul, div |
| Scalar binary (f64) | 4 | add, sub, mul, div |
| Scalar binary (i64) | 4 | add, sub, mul, div |
| Reductions (f64) | 6 | sum, mean, max, min, argmax, argmin |
| Reductions (i64) | 5 | sum, max, min, argmax, argmin (no mean -- correct, mean of ints is float) |
| Slicing | 1 | slice |

This is not bloat. This is the minimum viable API for a tensor type with two element types and four arithmetic operators. The type duplication (f64 vs i64) accounts for 21 of the 42 functions -- this is the C tax for not having templates. In C++ you would write one `tensor_add<T>` and instantiate it for `double` and `int64_t`. In C, you write two functions or use a macro. Mapanare chose macros for the broadcast ops and explicit functions for everything else. Reasonable.

The one function I would question is `__mn_tensor_print_f64`. It prints to stdout in a hard-coded format. This is a debugging aid, not a production feature. It should be behind a `#ifndef NDEBUG` or at minimum documented as debug-only. In a language that positions itself as compiled and performance-aware, having a printf-to-stdout function baked into the tensor runtime feels... undergraduate. But it is one function out of 42, and I have bigger concerns.

**Missing from the API:** `mean_i64` (returns Float -- currently absent, reasonable omission since the return type changes), axis-based reductions (reduce along one dimension), reshape, transpose, and contiguous/view semantics. All of these are documented as future work (v5.x). The API is complete for what v4.45.0 claims.

---

## 6. The Linear Regression Demo vs. C++ With Eigen

### The Demo

```mapanare
let X = Tensor<Float>[1.0, 2.0, 3.0, 4.0, 5.0]
let y = Tensor<Float>[3.0, 5.0, 7.0, 9.0, 11.0]
let mut w = 0.0
let mut b = 0.0
let lr = 0.01
let n = 5.0

for epoch in 0..10 {
    let pred = X * w + b
    let error = pred - y
    let grad_w = (error * X).sum() * 2.0 / n
    let grad_b = error.sum() * 2.0 / n
    w = w - lr * grad_w
    b = b - lr * grad_b
}
```

This reads beautifully. The tensor-scalar broadcasting (`X * w`, `+ b`) is implicit, the reduction method `.sum()` chains naturally, and the gradient computation is idiomatic. If I showed this to a NumPy programmer they would immediately understand it.

### The Equivalent in C++ With Eigen

```cpp
Eigen::VectorXd X(5); X << 1, 2, 3, 4, 5;
Eigen::VectorXd y(5); y << 3, 5, 7, 9, 11;
double w = 0, b = 0, lr = 0.01, n = 5;

for (int i = 0; i < 10; ++i) {
    auto pred = X * w + Eigen::VectorXd::Constant(5, b);
    auto error = pred - y;
    double grad_w = (error.cwiseProduct(X)).sum() * 2 / n;
    double grad_b = error.sum() * 2 / n;
    w -= lr * grad_w;
    b -= lr * grad_b;
}
```

The Mapanare version is cleaner. `X * w` just works (scalar broadcasting). `error * X` is element-wise by default (Eigen requires `.cwiseProduct()` because `*` is matrix multiply). `+ b` broadcasts without the `Constant(5, b)` boilerplate. The `.sum()` syntax is identical.

**But here is the thing Eigen does that Mapanare does not:** The `auto pred = X * w + ...` line in Eigen creates an expression template, not a materialized vector. The actual computation happens when `pred` is used in `pred - y`, and the entire expression `(X * w + b) - y` is fused into a single SIMD loop. In Mapanare, `X * w` allocates a tensor, `+ b` allocates another, `- y` allocates a third, and all three intermediates are freed at the end of the loop body. That is three `malloc`/`calloc`/`free` cycles per loop iteration for a 5-element vector. For the demo, this is invisible. For training on real data, this is where your wall-clock time goes.

**Verdict on the demo:** Excellent language-surface design. The syntax is arguably better than Eigen for the element-wise case. The performance characteristics are suitable for a demo and a learning exercise, not for production ML. This is correctly positioned -- the roadmap does not claim Mapanare is a production ML framework, and the demo's purpose is to demonstrate the tensor API, not to compete with PyTorch.

---

## 7. Matmul Implementation (`mapanare_runtime.c:934-963`)

```c
for (int64_t i = 0; i < m; i++) {
    for (int64_t p = 0; p < k; p++) {
        double a_ip = ad[i * k + p];
        for (int64_t j = 0; j < n; j++) {
            rd[i * n + j] += a_ip * bd[p * n + j];
        }
    }
}
```

The i-k-j loop order is correct for cache locality. The `a_ip` scalar hoist is correct -- it avoids reloading `a[i][p]` on every j iteration. The inner j-loop accesses `bd` and `rd` contiguously, which is the right pattern for SIMD auto-vectorization.

The comment says "enables SIMD vectorization of the inner j-loop" and it is correct -- with `-O2 -march=native`, both GCC and Clang will auto-vectorize this to AVX2 (4-wide FMA) or AVX-512 (8-wide) on modern x86. The code is clean enough that the auto-vectorizer has no aliasing concerns (the arrays are distinct allocations, and LLVM will prove non-aliasing through the `noalias` attribute on the allocator return).

**What it is not:** This is not a tiled matmul. It does not block for L1/L2 cache. For matrices larger than ~256x256 (where the working set exceeds L1), the naive i-k-j order will suffer from capacity misses on the B matrix. A production implementation would use 32x32 or 64x64 tiles with register blocking. But again, this is a compiled language runtime, not BLAS. The comment does not claim to compete with OpenBLAS or MKL. It claims to enable auto-vectorization, and it does.

**The `calloc` zeroing:** `mapanare_tensor_alloc` uses `calloc` to zero the data buffer (`runtime.c:850`). For matmul, this means the result tensor is zeroed before the `+=` accumulation, which is correct. But for operations like `add` where every element is written unconditionally, the zeroing is wasted work. `malloc` would suffice. This is a minor performance issue -- `calloc` on modern Linux uses `mmap` for large allocations, which is lazily zeroed by the kernel, so the overhead is near-zero for large tensors. For small tensors (the common case currently), the `calloc`-vs-`malloc` difference is noise.

---

## 8. Drop Glue (Tensor Lifetime Management)

The drop glue implementation at `emit_llvm_text.py:1524-1563` is well-structured:

1. Track every tensor allocated in the function via `_tensor_vars` list.
2. At function exit, load each tensor pointer from its alloca.
3. If the pointer is null, skip the free.
4. If the pointer is the return value, skip the free (ownership transfers to caller).
5. Otherwise, call `__mn_tensor_free`.

The null check + return-value check is the correct two-case analysis. The `icmp eq ptr %tp, null` followed by `icmp eq ptr %tp, %retval` merged via `or i1` is a clean pattern.

**One concern:** The `_tensor_vars` list is per-function. If a function calls a sub-function that returns a tensor, and the caller stores it in a local variable, it gets tracked. But if the caller passes a tensor to a sub-function as an argument, and the sub-function frees it (which none currently do -- all tensor functions are pure), there is no ownership protocol beyond "the allocator returns noalias, the caller is responsible." This is fine for now because all tensor ops allocate fresh results and leave inputs unmodified. But it is not a borrow checker, and mutation through `__mn_tensor_set_*_nd` means a tensor that is aliased (assigned to two variables) could be double-freed. The current lowering does not produce aliased tensor pointers, but it is a latent footgun.

---

## Issues Found

### CRITICAL: None

### HIGH: None

### MEDIUM

1. **[MEDIUM] Scalar-tensor subtraction/division operand swap is semantically wrong** -- `mapanare/lower.py:2558-2563`.

   When lowering `5.0 - t` (scalar minus tensor), the lowerer emits `__mn_tensor_sub_scalar_f64(t, 5.0)`. But `tensor_scalar_op_f64` computes `t[i] - 5.0`, not `5.0 - t[i]`. The code comment at line 2559 acknowledges this: "For -/div, this is wrong conceptually but matches NumPy's broadcasting (scalar is promoted to a tensor). We swap and negate if needed." The "negate if needed" part was never implemented. The swap is performed, but no negation or reciprocal is applied.

   For `5.0 - Tensor<Float>[1.0, 2.0, 3.0]`, the user expects `[4.0, 3.0, 2.0]`. The code produces `[-4.0, -3.0, -2.0]`. This is wrong. Similarly, `5.0 / Tensor<Float>[1.0, 2.0, 5.0]` should produce `[5.0, 2.5, 1.0]` but produces `[0.2, 0.4, 1.0]` (the reciprocals).

   The fix is either: (a) emit `__mn_tensor_mul_scalar_f64(t, -1.0)` followed by `__mn_tensor_add_scalar_f64(result, 5.0)` for subtraction, or (b) add `__mn_tensor_rsub_scalar_f64` and `__mn_tensor_rdiv_scalar_f64` runtime functions that compute `scalar - t[i]` and `scalar / t[i]`. Option (b) is cleaner and avoids the extra allocation.

   **Note:** The existing test suite does not cover `scalar - tensor` or `scalar / tensor`. Only `tensor + scalar` and `tensor * scalar` are tested (`test_tensor_broadcast.py:39-45`), which are commutative and thus unaffected. This bug has been shipping since v4.44.0.

### LOW

2. **[LOW] `broadcast_src_index()` recomputes coordinate decomposition per element** -- `mapanare_gpu_builtins.c:460-481`.

   Inside the broadcast inner loop (`gpu_builtins.c:502-504`), `broadcast_src_index()` is called twice per output element (once for each input tensor). Each call performs a division-modulo decomposition across all dimensions. For a rank-3 tensor with 10M output elements, this is 60M divisions. A stride-based approach (precompute broadcast strides, use multiply-add) would reduce this to 20M multiplications, which are significantly cheaper on all modern hardware. This is the standard optimization that Eigen, xtensor, and NumPy all use.

   Not blocking. The current approach is correct and readable. But it is the first thing that should be optimized when tensor performance matters.

3. **[LOW] Slice inner loop recomputes strides on every element** -- `mapanare_gpu_builtins.c:743-771`.

   The `__mn_tensor_slice` function computes `strides[]` and `out_strides[]` inside the per-element loop (lines 748-757). These are loop-invariant and should be hoisted above the `for (int64_t i = 0; i < total; i++)` loop. The compiler may hoist them (they are pure computations with no side effects), but relying on compiler optimization for something this obvious is the kind of programming that makes me sad. Two lines of code moved above the loop.

4. **[LOW] Variadic N-D indexing defeats LLVM inlining** -- `mapanare_gpu_builtins.c:378-429`.

   As discussed in Section 4. The variadic functions are correct but prevent LLVM from inlining the index computation. Fixed-arity wrappers for rank 1-4 (the common cases) would let LLVM reduce tensor access to arithmetic in the caller. Not blocking; the function call overhead is dwarfed by memory access time for large tensors.

5. **[LOW] `__mn_tensor_print_f64` is a debug-only function in the production API** -- `mapanare_gpu_builtins.c:329-344`.

   A `printf`-to-stdout function in the tensor runtime. Truncates at 20 elements with "...". The format is hard-coded. This should be either: (a) behind `#ifndef NDEBUG`, or (b) promoted to a proper formatting function that returns an `MnString` and lets the caller decide where to print. Currently it is a vestige of early development baked into the ABI.

6. **[LOW] `elem_size` byte-copy in slice instead of `memcpy`** -- `mapanare_gpu_builtins.c:770`.

   ```c
   for (int64_t b = 0; b < t->elem_size; b++) dst[b] = src[b];
   ```

   This is a manual byte-copy loop. `memcpy(dst, src, (size_t)t->elem_size)` would let the compiler emit a `rep movsb` or a SIMD copy for elem_size >= 8. For `elem_size = 8` (the only two current types), the compiler might optimize both to the same thing, but the `memcpy` is clearer and more portable.

7. **[LOW] Dead arena code, 13th cycle** -- `mapanare/emit_llvm_text.py:1491-1530`.

   Carrying forward from v4.41.0 Issue #3. Untouched in Arc 3. **13th cycle.** I am approaching the point where I will nominate this code for UNESCO World Heritage protection as a cultural artifact.

8. **[LOW] Stale carry-forward tracking versions for P3 and A10** -- `.reviews/CARRY_FORWARD.md:113, 117`.

   P3 targets v4.37.0, which shipped in Arc 2 without the fix. A10 targets "v4.37.0+ if grammar adds `loop { }`". Both are unchanged from my v4.41.0 review. Should be updated to v4.47.0+. Third consecutive cycle of stale tracking. The carry-forward ledger's utility depends on its tracking versions being current.

---

## Carry-Forward Status

| # | Item | v4.41.0 | v4.46.0 | Note |
|---|------|---------|---------|------|
| P3 | Guard fall-through (MEDIUM) | OPEN (cycle 2) | **OPEN (cycle 3)** | Untouched in Arc 3. `lower.mn:3418-3425` still jumps to next arm. |
| A10 | Bounded-for sentinels (LOW) | OPEN (cycle 10) | **OPEN (cycle 11)** | 552 sites, still no `loop { }` grammar change. |
| 1 | Struct/enum detail strings omit types | NEW at v4.41.0 | UNCHANGED | LSP workspace.py not modified in Arc 3. |
| 2 | Dead arena code (13th cycle) | 12th cycle | **13th cycle** | Geological timescales. |
| 3 | Missing golden ref files 49-51 | 3+ cycles | PRESUMED STALE | Not verified; golden count has grown to 53. |
| 4 | BYREF_BYTES asymmetry | 4th cycle | **5th cycle** | Untouched. |
| NEW | Scalar-tensor sub/div swap bug | -- | **NEW (MEDIUM)** | `lower.py:2558-2563`, wrong result for `scalar - tensor` and `scalar / tensor`. |
| NEW | Broadcast inner loop O(ndim)/element | -- | **NEW (LOW)** | `gpu_builtins.c:502-504`, stride-based indexing would be 3x faster. |
| NEW | Slice stride recomputation in loop | -- | **NEW (LOW)** | `gpu_builtins.c:748-757`, trivially hoistable. |

---

## Recommendations

### Priority 1: Fix scalar-tensor subtraction/division (Issue #1, MEDIUM)

This is a correctness bug. `5.0 - Tensor<Float>[1.0]` produces `-4.0` instead of `4.0`. Add `__mn_tensor_rsub_scalar_f64` and `__mn_tensor_rdiv_scalar_f64` to the runtime, or emit a negate/reciprocal wrapper in the lowerer. Add test cases for `scalar - tensor` and `scalar / tensor` to `test_tensor_broadcast.py`.

### Priority 2: Hoist stride computation out of slice loop (Issue #3, LOW)

Move lines 748-757 above the `for` loop at line 743. Five-minute fix. The strides are loop-invariant.

### Priority 3: Update CARRY_FORWARD.md tracking versions (Issue #8, LOW)

P3 and A10 both target shipped versions. Third consecutive review cycle where I have flagged this. One-line edits.

---

## Arc 3 Assessment

Arc 3 delivered exactly what it promised: a complete tensor surface with literals, N-D indexing, broadcasting, reductions, and slicing, all with compile-time shape validation where possible and runtime validation elsewhere. The language surface is competitive with NumPy and arguably cleaner than Eigen for the element-wise case. The runtime implementation is straightforward C -- no heroics, no premature optimization, just correct code with good NULL checks and overflow guards.

The ABI is sound. The opaque-pointer approach avoids all struct-passing pitfalls. The LLVM IR attribute annotations are precise (`noalias` on allocators, `readonly` on getters, no `willreturn` on aborting operations). The drop glue correctly tracks and frees tensors at function exit, skipping the return value.

I am deducting 0.35 from the previous 9.80 for:
- **-0.15** for the scalar-tensor sub/div operand swap bug (Issue #1, MEDIUM -- the first correctness bug I have found in the compiler since v4.28.0).
- **-0.05** for the broadcast inner loop performance characteristic (Issue #2 -- not a bug, but a known-suboptimal pattern that will need fixing).
- **-0.05** for the slice stride recomputation (Issue #3 -- trivially fixable, slightly embarrassing).
- **-0.05** for the variadic N-D indexing preventing inlining (Issue #4 -- correct but suboptimal).
- **-0.03** for the dead arena code, now entering its teenage years (Issue #7).
- **-0.02** for stale carry-forward tracking (Issue #8).

**Score: 9.45/10, PASS.** The drop from 9.80 is entirely due to the scalar-tensor operand swap bug and the accumulated low-priority items. The tensor infrastructure is real, it works, and the compile-time shape checking is a genuine differentiator. The performance story is "correct but naive" which is exactly right for v4.x. When v5.x arrives with expression fusion and stride-based views, this runtime will need a significant rewrite -- but the ABI surface (opaque pointer, allocate-and-return semantics) will survive that transition cleanly.

This is PASS with maximum confidence. The tensor is real. It just has growing to do.
