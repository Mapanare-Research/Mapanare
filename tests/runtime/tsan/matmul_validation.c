/*
 * matmul_validation.c — regression test for v4.28.0 Phase 2.1 + 2.2.
 *
 * Exercises ``__mn_gpu_tensor_matmul``'s dimension-validation path on
 * inputs that the v3.47.0 panel said "must be handled before v4.0.0":
 *
 *   - left.cols != right.rows  (dimension mismatch)
 *   - a.len != m * k            (flat-length mismatch)
 *   - m / n / k <= 0            (zero or negative dim)
 *   - dimension overflow        (m * k overflows int64)
 *
 * Before v4.28.0 each of these would either crash (shape malloc without
 * NULL check) or dispatch a bogus request to the GPU kernel. After
 * v4.28.0 each returns the empty list rather than crashing.
 *
 * This test does NOT require a GPU: matmul with ``!ctx->cuda.initialized``
 * returns the empty list via the existing fallback path in
 * ``mapanare_gpu.c``, so the validation check runs and the test is
 * meaningful on CI runners without an Nvidia GPU.
 *
 * Build (no TSan needed — purely behavioural):
 *   gcc -g -O1 -I runtime/native \
 *       tests/runtime/tsan/matmul_validation.c \
 *       runtime/native/mapanare_gpu_builtins.c \
 *       runtime/native/mapanare_gpu.c \
 *       runtime/native/mapanare_core.c \
 *       -o /tmp/matmul_validation -lpthread -lm -ldl
 *
 * Run:
 *   /tmp/matmul_validation
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mapanare_core.h"
#include "mapanare_gpu.h"

/* Extern the function we're testing (header exposes it via MN_EXPORT). */
extern MnList __mn_gpu_tensor_matmul(const MnList *a, const MnList *b,
                                      int64_t m, int64_t n, int64_t k);

static int failures = 0;

#define CHECK(cond, msg) do {                                           \
    if (!(cond)) {                                                      \
        fprintf(stderr, "FAIL: %s (at %s:%d)\n", (msg), __FILE__, __LINE__); \
        failures++;                                                     \
    } else {                                                            \
        fprintf(stderr, "PASS: %s\n", (msg));                           \
    }                                                                   \
} while (0)

static MnList make_list_of_doubles(int64_t len) {
    MnList list = __mn_list_new((int64_t)sizeof(double));
    for (int64_t i = 0; i < len; i++) {
        double v = (double)(i + 1);
        __mn_list_push(&list, &v);
    }
    return list;
}

int main(void) {
    /* 1. ``a.len != m * k`` — a has 6 elements, we claim it is 2x4 (=8). */
    {
        MnList a = make_list_of_doubles(6);
        MnList b = make_list_of_doubles(20);
        MnList out = __mn_gpu_tensor_matmul(&a, &b, 2, 5, 4);
        CHECK(out.len == 0, "a.len != m*k returns empty list");
    }

    /* 2. ``b.len != k * n`` — b has 5 elements, we claim it is 4x3 (=12). */
    {
        MnList a = make_list_of_doubles(8);
        MnList b = make_list_of_doubles(5);
        MnList out = __mn_gpu_tensor_matmul(&a, &b, 2, 3, 4);
        CHECK(out.len == 0, "b.len != k*n returns empty list");
    }

    /* 3. ``m <= 0`` — zero rows. */
    {
        MnList a = make_list_of_doubles(0);
        MnList b = make_list_of_doubles(12);
        MnList out = __mn_gpu_tensor_matmul(&a, &b, 0, 3, 4);
        CHECK(out.len == 0, "m == 0 returns empty list");
    }

    /* 4. ``k <= 0`` — zero inner dim. */
    {
        MnList a = make_list_of_doubles(0);
        MnList b = make_list_of_doubles(0);
        MnList out = __mn_gpu_tensor_matmul(&a, &b, 2, 3, 0);
        CHECK(out.len == 0, "k == 0 returns empty list");
    }

    /* 5. Dimension-overflow: m * k overflows int64. With __int128 mul
     * check, these values must produce empty list rather than UB. */
    {
        MnList a = make_list_of_doubles(0);
        MnList b = make_list_of_doubles(0);
        int64_t huge = (int64_t)1 << 40;  /* 2^40 */
        MnList out = __mn_gpu_tensor_matmul(&a, &b, huge, huge, huge);
        CHECK(out.len == 0, "overflow (m*k > INT64_MAX) returns empty list");
    }

    /* 6. NULL list pointers. Not actually reachable from Mapanare code
     * but the check belongs to the API surface. */
    {
        MnList out = __mn_gpu_tensor_matmul(NULL, NULL, 2, 3, 4);
        CHECK(out.len == 0, "NULL list pointers return empty list");
    }

    /* 7. Valid dimensions, no GPU: should return empty list via the
     * gpu-not-initialised fallback but MUST NOT crash. This exercises
     * the shape-malloc NULL-check path only under memory pressure, so
     * instead we verify the code path reaches the mapanare_gpu_tensor_matmul
     * call without dereferencing a NULL shape. */
    {
        MnList a = make_list_of_doubles(6);  /* 2x3 */
        MnList b = make_list_of_doubles(12); /* 3x4 */
        MnList out = __mn_gpu_tensor_matmul(&a, &b, 2, 4, 3);
        /* Without a GPU this returns empty; with a GPU it returns 2*4=8
         * doubles. Accept either, the point is no crash. */
        CHECK(out.len == 0 || out.len == 8,
              "valid dims reach matmul without NULL-deref");
    }

    if (failures > 0) {
        fprintf(stderr, "\nmatmul_validation: %d failure(s)\n", failures);
        return 1;
    }
    printf("matmul_validation: all checks passed\n");
    return 0;
}
