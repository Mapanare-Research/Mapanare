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

/** gpu_tensor_matmul(a: List<Float>, b: List<Float>, m: Int, n: Int, k: Int) -> List<Float> */
MN_EXPORT MnList __mn_gpu_tensor_matmul(const MnList *a, const MnList *b,
                                         int64_t m, int64_t n, int64_t k) {
    mapanare_gpu_init();
    if (!a || !a->data || !b || !b->data) {
        return __mn_list_new((int64_t)sizeof(double));
    }
    mapanare_tensor_t *ta = (mapanare_tensor_t *)malloc(sizeof(mapanare_tensor_t));
    mapanare_tensor_t *tb = (mapanare_tensor_t *)malloc(sizeof(mapanare_tensor_t));
    if (!ta || !tb) {
        free(ta); free(tb);
        return __mn_list_new((int64_t)sizeof(double));
    }
    ta->data = a->data;
    ta->ndim = 2;
    ta->shape = (int64_t *)malloc(2 * sizeof(int64_t));
    ta->shape[0] = m; ta->shape[1] = k;
    ta->size = m * k;
    ta->elem_size = (int64_t)sizeof(double);

    tb->data = b->data;
    tb->ndim = 2;
    tb->shape = (int64_t *)malloc(2 * sizeof(int64_t));
    tb->shape[0] = k; tb->shape[1] = n;
    tb->size = k * n;
    tb->elem_size = (int64_t)sizeof(double);

    mapanare_tensor_t *result = mapanare_gpu_tensor_matmul(ta, tb);
    MnList out = list_from_tensor(result);
    mapanare_tensor_free(result);
    free(ta->shape); free(ta);
    free(tb->shape); free(tb);
    return out;
}
