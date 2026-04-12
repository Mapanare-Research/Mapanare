/**
 * mapanare_gpu_builtins.c — GPU builtin wrappers for the Mapanare language
 *
 * Bridges the language-level MnList/MnString types to the low-level
 * mapanare_gpu.c tensor API. These are the __mn_gpu_* functions called
 * by the LLVM emitter when compiling gpu_available(), gpu_tensor_add(), etc.
 *
 * Tensor builtins take MnList* pointers (not by value) to avoid ABI
 * mismatches between LLVM IR struct passing and SysV calling conventions.
 */

#include "mapanare_gpu.h"
#include "mapanare_core.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -----------------------------------------------------------------------
 * GPU Detection Builtins
 * ----------------------------------------------------------------------- */

/** gpu_available() -> Bool (returned as i64: 0 or 1) */
MN_EXPORT int64_t __mn_gpu_available(void) {
    mapanare_gpu_init();
    return mapanare_gpu_has_cuda() ? 1 : 0;
}

/** gpu_device_name() -> String */
MN_EXPORT MnString __mn_gpu_device_name(void) {
    mapanare_gpu_init();
    const mn_gpu_ctx_t *ctx = mapanare_gpu_get_ctx();
    if (ctx && ctx->cuda.initialized && ctx->cuda.device_name[0]) {
        return __mn_str_from_cstr(ctx->cuda.device_name);
    }
    return __mn_str_from_cstr("No GPU");
}

/** gpu_device_memory() -> Int (bytes) */
MN_EXPORT int64_t __mn_gpu_device_memory(void) {
    mapanare_gpu_init();
    const mn_gpu_ctx_t *ctx = mapanare_gpu_get_ctx();
    if (ctx && ctx->cuda.initialized) {
        return ctx->cuda.device_memory;
    }
    return 0;
}

/* -----------------------------------------------------------------------
 * Helper: MnList<Float> ↔ mapanare_tensor_t conversion
 * ----------------------------------------------------------------------- */

/** Create a temporary 1D tensor that borrows list data. */
static mapanare_tensor_t *tensor_from_list(const MnList *list) {
    if (!list || !list->data || list->len <= 0) return NULL;
    mapanare_tensor_t *t = (mapanare_tensor_t *)malloc(sizeof(mapanare_tensor_t));
    if (!t) return NULL;
    t->data = list->data;
    t->ndim = 1;
    t->shape = (int64_t *)malloc(sizeof(int64_t));
    if (!t->shape) { free(t); return NULL; }
    t->shape[0] = list->len;
    t->size = list->len;
    t->elem_size = (int64_t)sizeof(double);
    return t;
}

/** Free the temporary tensor struct + shape, but NOT the data (borrowed). */
static void tensor_borrow_free(mapanare_tensor_t *t) {
    if (!t) return;
    free(t->shape);
    free(t);
}

/** Convert a result tensor (owns its data) to a new MnList<Float>. */
static MnList list_from_tensor(mapanare_tensor_t *t) {
    MnList list = __mn_list_new((int64_t)sizeof(double));
    if (!t || t->size <= 0) return list;
    for (int64_t i = 0; i < t->size; i++) {
        double val = ((double *)t->data)[i];
        __mn_list_push(&list, &val);
    }
    return list;
}

/* -----------------------------------------------------------------------
 * GPU Tensor Element-wise Builtins (take MnList* to avoid ABI mismatch)
 * ----------------------------------------------------------------------- */

/** gpu_tensor_add(a: List<Float>, b: List<Float>) -> List<Float> */
MN_EXPORT MnList __mn_gpu_tensor_add(const MnList *a, const MnList *b) {
    mapanare_gpu_init();
    mapanare_tensor_t *ta = tensor_from_list(a);
    mapanare_tensor_t *tb = tensor_from_list(b);
    if (!ta || !tb) {
        tensor_borrow_free(ta);
        tensor_borrow_free(tb);
        return __mn_list_new((int64_t)sizeof(double));
    }
    mapanare_tensor_t *result = mapanare_gpu_tensor_add(ta, tb);
    MnList out = list_from_tensor(result);
    mapanare_tensor_free(result);
    tensor_borrow_free(ta);
    tensor_borrow_free(tb);
    return out;
}

/** gpu_tensor_sub(a: List<Float>, b: List<Float>) -> List<Float> */
MN_EXPORT MnList __mn_gpu_tensor_sub(const MnList *a, const MnList *b) {
    mapanare_gpu_init();
    mapanare_tensor_t *ta = tensor_from_list(a);
    mapanare_tensor_t *tb = tensor_from_list(b);
    if (!ta || !tb) {
        tensor_borrow_free(ta);
        tensor_borrow_free(tb);
        return __mn_list_new((int64_t)sizeof(double));
    }
    mapanare_tensor_t *result = mapanare_gpu_tensor_sub(ta, tb);
    MnList out = list_from_tensor(result);
    mapanare_tensor_free(result);
    tensor_borrow_free(ta);
    tensor_borrow_free(tb);
    return out;
}

/** gpu_tensor_mul(a: List<Float>, b: List<Float>) -> List<Float> */
MN_EXPORT MnList __mn_gpu_tensor_mul(const MnList *a, const MnList *b) {
    mapanare_gpu_init();
    mapanare_tensor_t *ta = tensor_from_list(a);
    mapanare_tensor_t *tb = tensor_from_list(b);
    if (!ta || !tb) {
        tensor_borrow_free(ta);
        tensor_borrow_free(tb);
        return __mn_list_new((int64_t)sizeof(double));
    }
    mapanare_tensor_t *result = mapanare_gpu_tensor_mul(ta, tb);
    MnList out = list_from_tensor(result);
    mapanare_tensor_free(result);
    tensor_borrow_free(ta);
    tensor_borrow_free(tb);
    return out;
}

/** gpu_tensor_div(a: List<Float>, b: List<Float>) -> List<Float> */
MN_EXPORT MnList __mn_gpu_tensor_div(const MnList *a, const MnList *b) {
    mapanare_gpu_init();
    mapanare_tensor_t *ta = tensor_from_list(a);
    mapanare_tensor_t *tb = tensor_from_list(b);
    if (!ta || !tb) {
        tensor_borrow_free(ta);
        tensor_borrow_free(tb);
        return __mn_list_new((int64_t)sizeof(double));
    }
    mapanare_tensor_t *result = mapanare_gpu_tensor_div(ta, tb);
    MnList out = list_from_tensor(result);
    mapanare_tensor_free(result);
    tensor_borrow_free(ta);
    tensor_borrow_free(tb);
    return out;
}

/** gpu_tensor_matmul(a: List<Float>, b: List<Float>, m: Int, n: Int, k: Int) -> List<Float>
 *
 * v4.28.0: closes the v3.47.0 hard-blocker carry-forward that was
 * byte-identical to the pre-v4.0.0 state for 27 review cycles (see
 * ``docs/roadmap/v4/v4.28.0/FORENSICS.md``). Three classes of bug:
 *
 * 1. The ``ta->shape`` / ``tb->shape`` mallocs had no NULL check — if
 *    either failed, the immediately following ``ta->shape[0] = m``
 *    dereferenced NULL.
 * 2. ``m * k`` and ``k * n`` were computed without overflow checking.
 *    A caller passing pathological dimensions could produce a negative
 *    ``size`` that the GPU backend would then use for buffer math.
 * 3. The function trusted the caller's ``m, n, k`` values against the
 *    input list lengths. A caller passing mismatched dimensions caused
 *    undefined behaviour inside the GPU tensor compute path.
 *
 * All three are now checked up front. An empty list is returned on
 * every error so the language-level behaviour is "matmul on invalid
 * inputs returns the empty tensor" instead of "crash".
 */
MN_EXPORT MnList __mn_gpu_tensor_matmul(const MnList *a, const MnList *b,
                                         int64_t m, int64_t n, int64_t k) {
    mapanare_gpu_init();

    /* Phase 2.2 — dimension validation up front. */
    if (!a || !a->data || !b || !b->data) {
        return __mn_list_new((int64_t)sizeof(double));
    }
    if (m <= 0 || n <= 0 || k <= 0) {
        return __mn_list_new((int64_t)sizeof(double));
    }
    /* Overflow-safe check: a->len == m*k, b->len == k*n. Use 128-bit mul
     * via ``__int128`` where available, else fall back to a per-step
     * overflow check. */
    int64_t a_expected = 0;
    int64_t b_expected = 0;
#if defined(__SIZEOF_INT128__)
    {
        __int128 ak = (__int128)m * (__int128)k;
        __int128 kn = (__int128)k * (__int128)n;
        if (ak > (__int128)INT64_MAX || kn > (__int128)INT64_MAX) {
            return __mn_list_new((int64_t)sizeof(double));
        }
        a_expected = (int64_t)ak;
        b_expected = (int64_t)kn;
    }
#else
    {
        /* Portable overflow check: if m*k > INT64_MAX, return empty. */
        if (m > INT64_MAX / k) {
            return __mn_list_new((int64_t)sizeof(double));
        }
        if (k > INT64_MAX / n) {
            return __mn_list_new((int64_t)sizeof(double));
        }
        a_expected = m * k;
        b_expected = k * n;
    }
#endif
    if (a->len != a_expected || b->len != b_expected) {
        /* Caller-supplied dimensions don't match the flat list lengths.
         * Rather than dispatching to the GPU kernel with a bogus shape,
         * return the empty tensor. */
        return __mn_list_new((int64_t)sizeof(double));
    }

    /* Phase 2.1 — struct-header NULL checks (unchanged from v3.47.0). */
    mapanare_tensor_t *ta = (mapanare_tensor_t *)malloc(sizeof(mapanare_tensor_t));
    mapanare_tensor_t *tb = (mapanare_tensor_t *)malloc(sizeof(mapanare_tensor_t));
    if (!ta || !tb) {
        free(ta); free(tb);
        return __mn_list_new((int64_t)sizeof(double));
    }

    /* Phase 2.1 — shape-array NULL checks. The panel explicitly called
     * these out: previously the code wrote ``ta->shape[0] = m`` without
     * checking that ``malloc`` succeeded, which is a NULL-deref segfault
     * under memory pressure. */
    ta->shape = (int64_t *)malloc(2 * sizeof(int64_t));
    tb->shape = (int64_t *)malloc(2 * sizeof(int64_t));
    if (!ta->shape || !tb->shape) {
        free(ta->shape); free(tb->shape);
        free(ta); free(tb);
        return __mn_list_new((int64_t)sizeof(double));
    }

    ta->data = a->data;
    ta->ndim = 2;
    ta->shape[0] = m; ta->shape[1] = k;
    ta->size = a_expected;
    ta->elem_size = (int64_t)sizeof(double);

    tb->data = b->data;
    tb->ndim = 2;
    tb->shape[0] = k; tb->shape[1] = n;
    tb->size = b_expected;
    tb->elem_size = (int64_t)sizeof(double);

    mapanare_tensor_t *result = mapanare_gpu_tensor_matmul(ta, tb);
    MnList out = list_from_tensor(result);
    mapanare_tensor_free(result);
    free(ta->shape); free(ta);
    free(tb->shape); free(tb);
    return out;
}

/* -----------------------------------------------------------------------
 * Tensor Literal Runtime (v4.42.0)
 *
 * Language-level wrappers for tensor construction. Called by the LLVM
 * emitter when lowering TensorLiteral AST nodes. CPU-only — no GPU
 * dependency. Falls through to mapanare_tensor_alloc() in
 * mapanare_runtime.c which allocates a plain heap buffer.
 * ----------------------------------------------------------------------- */

/** Allocate a tensor: __mn_tensor_alloc(rank, shape_ptr, elem_size) -> ptr */
MN_EXPORT mapanare_tensor_t *__mn_tensor_alloc(
    int64_t rank, const int64_t *shape, int64_t elem_size) {
    return mapanare_tensor_alloc(rank, shape, elem_size);
}

/** Free a tensor: __mn_tensor_free(tensor_ptr) */
MN_EXPORT void __mn_tensor_free(mapanare_tensor_t *t) {
    mapanare_tensor_free(t);
}

/** Store a float64 element: __mn_tensor_store_f64(tensor, index, value) */
MN_EXPORT void __mn_tensor_store_f64(mapanare_tensor_t *t, int64_t idx, double val) {
    if (!t || !t->data || idx < 0 || idx >= t->size) return;
    ((double *)t->data)[idx] = val;
}

/** Store an int64 element: __mn_tensor_store_i64(tensor, index, value) */
MN_EXPORT void __mn_tensor_store_i64(mapanare_tensor_t *t, int64_t idx, int64_t val) {
    if (!t || !t->data || idx < 0 || idx >= t->size) return;
    ((int64_t *)t->data)[idx] = val;
}

/** Get a float64 element: __mn_tensor_get_f64(tensor, index) -> double */
MN_EXPORT double __mn_tensor_get_f64(const mapanare_tensor_t *t, int64_t idx) {
    if (!t || !t->data || idx < 0 || idx >= t->size) return 0.0;
    return ((const double *)t->data)[idx];
}

/** Get an int64 element: __mn_tensor_get_i64(tensor, index) -> int64_t */
MN_EXPORT int64_t __mn_tensor_get_i64(const mapanare_tensor_t *t, int64_t idx) {
    if (!t || !t->data || idx < 0 || idx >= t->size) return 0;
    return ((const int64_t *)t->data)[idx];
}

/** Get the number of dimensions: __mn_tensor_rank(tensor) -> int64_t */
MN_EXPORT int64_t __mn_tensor_rank(const mapanare_tensor_t *t) {
    return t ? t->ndim : 0;
}

/** Get the total element count: __mn_tensor_size(tensor) -> int64_t */
MN_EXPORT int64_t __mn_tensor_size(const mapanare_tensor_t *t) {
    return t ? t->size : 0;
}

/** Get one dimension of the shape: __mn_tensor_shape_dim(tensor, dim) -> int64_t */
MN_EXPORT int64_t __mn_tensor_shape_dim(const mapanare_tensor_t *t, int64_t dim) {
    if (!t || !t->shape || dim < 0 || dim >= t->ndim) return 0;
    return t->shape[dim];
}

/** Debug print a tensor to stdout. */
MN_EXPORT void __mn_tensor_print_f64(const mapanare_tensor_t *t) {
    if (!t) { printf("Tensor(null)\n"); return; }
    printf("Tensor<Float>[");
    for (int64_t i = 0; i < t->ndim; i++) {
        if (i > 0) printf(", ");
        printf("%lld", (long long)t->shape[i]);
    }
    printf("](");
    int64_t limit = t->size < 20 ? t->size : 20;
    for (int64_t i = 0; i < limit; i++) {
        if (i > 0) printf(", ");
        printf("%.6g", ((const double *)t->data)[i]);
    }
    if (t->size > 20) printf(", ...");
    printf(")\n");
}

/* -----------------------------------------------------------------------
 * Tensor Multi-Dimensional Indexing (v4.43.0)
 *
 * Variadic-via-pointer: pass index array + rank. Computes flat row-major
 * offset with per-dimension bounds checking. Aborts on OOB.
 * ----------------------------------------------------------------------- */

/** Compute row-major flat offset from multi-dim indices. Returns -1 on OOB. */
static int64_t tensor_flat_offset(const mapanare_tensor_t *t,
                                  const int64_t *idx, int64_t rank) {
    if (rank != t->ndim) {
        fprintf(stderr, "mapanare: tensor index rank %lld doesn't match "
                "tensor rank %lld\n", (long long)rank, (long long)t->ndim);
        abort();
    }
    int64_t flat = 0;
    int64_t stride = 1;
    for (int64_t d = rank - 1; d >= 0; d--) {
        int64_t i = idx[d];
        if (i < 0 || i >= t->shape[d]) {
            fprintf(stderr, "mapanare: tensor index out of bounds: "
                    "dimension %lld index %lld not in [0, %lld)\n",
                    (long long)d, (long long)i, (long long)t->shape[d]);
            abort();
        }
        flat += i * stride;
        stride *= t->shape[d];
    }
    return flat;
}

/** Read float64 element: __mn_tensor_get_f64_nd(tensor, rank, i0, i1, ...) */
MN_EXPORT double __mn_tensor_get_f64_nd(mapanare_tensor_t *t, int64_t rank, ...) {
    if (!t || !t->data) { fprintf(stderr, "mapanare: tensor get on null\n"); abort(); }
    if (rank > 16) { fprintf(stderr, "mapanare: tensor rank %lld exceeds max 16\n", (long long)rank); abort(); }
    int64_t idx[16];
    va_list ap;
    va_start(ap, rank);
    for (int64_t d = 0; d < rank; d++) idx[d] = va_arg(ap, int64_t);
    va_end(ap);
    int64_t flat = tensor_flat_offset(t, idx, rank);
    return ((const double *)t->data)[flat];
}

/** Read int64 element: __mn_tensor_get_i64_nd(tensor, rank, i0, i1, ...) */
MN_EXPORT int64_t __mn_tensor_get_i64_nd(mapanare_tensor_t *t, int64_t rank, ...) {
    if (!t || !t->data) { fprintf(stderr, "mapanare: tensor get on null\n"); abort(); }
    if (rank > 16) { fprintf(stderr, "mapanare: tensor rank %lld exceeds max 16\n", (long long)rank); abort(); }
    int64_t idx[16];
    va_list ap;
    va_start(ap, rank);
    for (int64_t d = 0; d < rank; d++) idx[d] = va_arg(ap, int64_t);
    va_end(ap);
    int64_t flat = tensor_flat_offset(t, idx, rank);
    return ((const int64_t *)t->data)[flat];
}

/** Write float64 element: __mn_tensor_set_f64_nd(tensor, rank, i0, i1, ..., val) */
MN_EXPORT void __mn_tensor_set_f64_nd(mapanare_tensor_t *t, int64_t rank, ...) {
    if (!t || !t->data) { fprintf(stderr, "mapanare: tensor set on null\n"); abort(); }
    if (rank > 16) { fprintf(stderr, "mapanare: tensor rank %lld exceeds max 16\n", (long long)rank); abort(); }
    int64_t idx[16];
    va_list ap;
    va_start(ap, rank);
    for (int64_t d = 0; d < rank; d++) idx[d] = va_arg(ap, int64_t);
    double val = va_arg(ap, double);
    va_end(ap);
    int64_t flat = tensor_flat_offset(t, idx, rank);
    ((double *)t->data)[flat] = val;
}

/** Write int64 element: __mn_tensor_set_i64_nd(tensor, rank, i0, i1, ..., val) */
MN_EXPORT void __mn_tensor_set_i64_nd(mapanare_tensor_t *t, int64_t rank, ...) {
    if (!t || !t->data) { fprintf(stderr, "mapanare: tensor set on null\n"); abort(); }
    if (rank > 16) { fprintf(stderr, "mapanare: tensor rank %lld exceeds max 16\n", (long long)rank); abort(); }
    int64_t idx[16];
    va_list ap;
    va_start(ap, rank);
    for (int64_t d = 0; d < rank; d++) idx[d] = va_arg(ap, int64_t);
    int64_t val = va_arg(ap, int64_t);
    va_end(ap);
    int64_t flat = tensor_flat_offset(t, idx, rank);
    ((int64_t *)t->data)[flat] = val;
}
