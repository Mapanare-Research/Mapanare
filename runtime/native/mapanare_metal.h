/**
 * mapanare_metal.h — Metal compute backend for Mapanare GPU runtime
 *
 * Provides GPU compute on Apple platforms (macOS / iOS) via Metal.
 * Uses the Objective-C runtime C API to call Metal methods — no .m files
 * needed, compiles as plain C with -framework Metal -framework Foundation.
 *
 * Metal has unified memory on Apple Silicon, so host↔device copies are
 * effectively free (shared buffers). This is a significant advantage over
 * CUDA/Vulkan for tensor operations.
 */

#ifndef MAPANARE_METAL_H
#define MAPANARE_METAL_H

#include <stdint.h>
#include <stddef.h>
#include "mapanare_runtime.h"

#ifdef __APPLE__

#ifdef _WIN32
  #define MN_METAL_EXPORT __declspec(dllexport)
#else
  #define MN_METAL_EXPORT __attribute__((visibility("default")))
#endif

/* -----------------------------------------------------------------------
 * Metal context — wraps MTLDevice, MTLCommandQueue, and compiled pipelines
 * ----------------------------------------------------------------------- */

/** Opaque Metal handles (Objective-C objects cast to void*). */
typedef void *MTLDeviceRef;
typedef void *MTLCommandQueueRef;
typedef void *MTLLibraryRef;
typedef void *MTLFunctionRef;
typedef void *MTLComputePipelineStateRef;
typedef void *MTLBufferRef;
typedef void *MTLCommandBufferRef;
typedef void *MTLComputeCommandEncoderRef;

/** Metal compute pipeline — compiled shader + pipeline state. */
typedef struct mn_metal_pipeline {
    MTLFunctionRef              function;
    MTLComputePipelineStateRef  pipeline_state;
    uint32_t                    thread_group_size;  /* max threads per threadgroup */
} mn_metal_pipeline_t;

/** Metal GPU context. */
typedef struct mn_metal_ctx {
    MTLDeviceRef         device;
    MTLCommandQueueRef   command_queue;
    int                  initialized;
    int                  has_unified_memory;  /* Apple Silicon = 1 */
    char                 device_name[256];
    int64_t              memory_bytes;

    /* Pre-compiled tensor operation pipelines */
    mn_metal_pipeline_t  tensor_add;
    mn_metal_pipeline_t  tensor_sub;
    mn_metal_pipeline_t  tensor_mul;
    mn_metal_pipeline_t  tensor_div;
    mn_metal_pipeline_t  tensor_matmul;
} mn_metal_ctx_t;

/* -----------------------------------------------------------------------
 * Metal GPU buffer
 * ----------------------------------------------------------------------- */

typedef struct mn_metal_buffer {
    MTLBufferRef  buffer;
    void         *contents;     /* CPU-accessible pointer (shared memory) */
    size_t        size_bytes;
} mn_metal_buffer_t;

/* -----------------------------------------------------------------------
 * Public API
 * ----------------------------------------------------------------------- */

/** Initialize Metal compute. Returns 0 on success, -1 if Metal unavailable. */
MN_METAL_EXPORT int  mapanare_metal_init(mn_metal_ctx_t *ctx);

/** Shut down Metal and release resources. */
MN_METAL_EXPORT void mapanare_metal_shutdown(mn_metal_ctx_t *ctx);

/** Check if Metal compute is available on this system. */
MN_METAL_EXPORT int  mapanare_metal_available(void);

/** Allocate a Metal buffer (shared memory mode for Apple Silicon).
 *  Returns NULL on failure. */
MN_METAL_EXPORT mn_metal_buffer_t *mapanare_metal_buffer_alloc(mn_metal_ctx_t *ctx, size_t bytes);

/** Free a Metal buffer. */
MN_METAL_EXPORT void mapanare_metal_buffer_free(mn_metal_buffer_t *buf);

/** Compile a Metal shader from source string. Returns pipeline or NULL.
 *  The function_name is the kernel entry point in the MSL source. */
MN_METAL_EXPORT mn_metal_pipeline_t *mapanare_metal_compile(
    mn_metal_ctx_t *ctx, const char *msl_source, const char *function_name);

/** Free a compiled Metal pipeline. */
MN_METAL_EXPORT void mapanare_metal_pipeline_free(mn_metal_pipeline_t *pipeline);

/** Dispatch a compute kernel with the given buffers and grid size.
 *  Returns 0 on success, -1 on error. */
MN_METAL_EXPORT int  mapanare_metal_dispatch(
    mn_metal_ctx_t *ctx,
    mn_metal_pipeline_t *pipeline,
    mn_metal_buffer_t **buffers,
    uint32_t buffer_count,
    uint32_t grid_x, uint32_t grid_y, uint32_t grid_z);

/* -----------------------------------------------------------------------
 * Tensor operations via Metal
 * ----------------------------------------------------------------------- */

/** Element-wise tensor add on Metal GPU. Falls back to CPU if Metal unavailable. */
MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_add(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise tensor sub on Metal GPU. */
MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_sub(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise tensor mul on Metal GPU. */
MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_mul(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise tensor div on Metal GPU. */
MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_div(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Matrix multiply on Metal GPU: (M,K) @ (K,N) -> (M,N). */
MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_matmul(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b);

#endif /* __APPLE__ */
#endif /* MAPANARE_METAL_H */
