/**
 * mapanare_metal.m — Metal compute backend implementation
 *
 * Uses Objective-C directly (compiled as .m) to call Metal APIs.
 * This is the cleanest approach — Metal is an Objective-C framework
 * and trying to use objc_msgSend from C is fragile and hard to maintain.
 *
 * Compile: clang -c -std=c11 -O2 -fobjc-arc mapanare_metal.m \
 *          -framework Metal -framework Foundation
 */

#ifdef __APPLE__

#import <Metal/Metal.h>
#import <Foundation/Foundation.h>
#include "mapanare_metal.h"
#include <string.h>
#include <stdio.h>

/* -----------------------------------------------------------------------
 * Built-in Metal Shading Language (MSL) kernels for tensor operations
 *
 * These operate on arrays of float (float32) with one element per thread.
 * Using float instead of double because Metal has limited float64 support.
 * For double precision, we use float32 internally and convert at boundaries.
 * ----------------------------------------------------------------------- */

static const char MSL_TENSOR_ADD[] =
    "#include <metal_stdlib>\n"
    "using namespace metal;\n"
    "kernel void tensor_add(\n"
    "    device const float *a [[buffer(0)]],\n"
    "    device const float *b [[buffer(1)]],\n"
    "    device float *out     [[buffer(2)]],\n"
    "    uint id [[thread_position_in_grid]]) {\n"
    "    out[id] = a[id] + b[id];\n"
    "}\n";

static const char MSL_TENSOR_SUB[] =
    "#include <metal_stdlib>\n"
    "using namespace metal;\n"
    "kernel void tensor_sub(\n"
    "    device const float *a [[buffer(0)]],\n"
    "    device const float *b [[buffer(1)]],\n"
    "    device float *out     [[buffer(2)]],\n"
    "    uint id [[thread_position_in_grid]]) {\n"
    "    out[id] = a[id] - b[id];\n"
    "}\n";

static const char MSL_TENSOR_MUL[] =
    "#include <metal_stdlib>\n"
    "using namespace metal;\n"
    "kernel void tensor_mul(\n"
    "    device const float *a [[buffer(0)]],\n"
    "    device const float *b [[buffer(1)]],\n"
    "    device float *out     [[buffer(2)]],\n"
    "    uint id [[thread_position_in_grid]]) {\n"
    "    out[id] = a[id] * b[id];\n"
    "}\n";

static const char MSL_TENSOR_DIV[] =
    "#include <metal_stdlib>\n"
    "using namespace metal;\n"
    "kernel void tensor_div(\n"
    "    device const float *a [[buffer(0)]],\n"
    "    device const float *b [[buffer(1)]],\n"
    "    device float *out     [[buffer(2)]],\n"
    "    uint id [[thread_position_in_grid]]) {\n"
    "    out[id] = (b[id] != 0.0f) ? a[id] / b[id] : 0.0f;\n"
    "}\n";

static const char MSL_TENSOR_MATMUL[] =
    "#include <metal_stdlib>\n"
    "using namespace metal;\n"
    "struct MatmulParams {\n"
    "    uint M;\n"
    "    uint K;\n"
    "    uint N;\n"
    "};\n"
    "kernel void tensor_matmul(\n"
    "    device const float *a      [[buffer(0)]],\n"
    "    device const float *b      [[buffer(1)]],\n"
    "    device float *out          [[buffer(2)]],\n"
    "    constant MatmulParams &p   [[buffer(3)]],\n"
    "    uint2 id [[thread_position_in_grid]]) {\n"
    "    uint row = id.y;\n"
    "    uint col = id.x;\n"
    "    if (row >= p.M || col >= p.N) return;\n"
    "    float sum = 0.0f;\n"
    "    for (uint k = 0; k < p.K; k++) {\n"
    "        sum += a[row * p.K + k] * b[k * p.N + col];\n"
    "    }\n"
    "    out[row * p.N + col] = sum;\n"
    "}\n";

/* -----------------------------------------------------------------------
 * Helper: compile MSL source to pipeline
 * ----------------------------------------------------------------------- */

static int metal_compile_pipeline(
    id<MTLDevice> device,
    const char *msl_source,
    const char *function_name,
    mn_metal_pipeline_t *out_pipeline)
{
    @autoreleasepool {
        NSError *error = nil;
        NSString *source = [NSString stringWithUTF8String:msl_source];

        id<MTLLibrary> library = [device newLibraryWithSource:source options:nil error:&error];
        if (!library) {
            fprintf(stderr, "Metal: failed to compile '%s': %s\n",
                    function_name, error.localizedDescription.UTF8String);
            return -1;
        }

        NSString *fnName = [NSString stringWithUTF8String:function_name];
        id<MTLFunction> function = [library newFunctionWithName:fnName];
        if (!function) {
            fprintf(stderr, "Metal: function '%s' not found in compiled library\n", function_name);
            return -1;
        }

        id<MTLComputePipelineState> pso = [device newComputePipelineStateWithFunction:function error:&error];
        if (!pso) {
            fprintf(stderr, "Metal: failed to create pipeline for '%s': %s\n",
                    function_name, error.localizedDescription.UTF8String);
            return -1;
        }

        out_pipeline->function = (__bridge_retained void *)function;
        out_pipeline->pipeline_state = (__bridge_retained void *)pso;
        out_pipeline->thread_group_size = (uint32_t)[pso maxTotalThreadsPerThreadgroup];
    }
    return 0;
}

/* -----------------------------------------------------------------------
 * Public API — Initialization
 * ----------------------------------------------------------------------- */

MN_METAL_EXPORT int mapanare_metal_available(void) {
    @autoreleasepool {
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        return device != nil ? 1 : 0;
    }
}

MN_METAL_EXPORT int mapanare_metal_init(mn_metal_ctx_t *ctx) {
    if (!ctx) return -1;
    if (ctx->initialized) return 0;
    memset(ctx, 0, sizeof(*ctx));

    @autoreleasepool {
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        if (!device) return -1;

        ctx->device = (__bridge_retained void *)device;
        ctx->command_queue = (__bridge_retained void *)[device newCommandQueue];
        ctx->has_unified_memory = [device hasUnifiedMemory] ? 1 : 0;
        ctx->memory_bytes = (int64_t)[device recommendedMaxWorkingSetSize];

        const char *name = [device.name UTF8String];
        if (name) {
            strncpy(ctx->device_name, name, sizeof(ctx->device_name) - 1);
            ctx->device_name[sizeof(ctx->device_name) - 1] = '\0';
        }

        /* Pre-compile tensor pipelines */
        metal_compile_pipeline(device, MSL_TENSOR_ADD, "tensor_add", &ctx->tensor_add);
        metal_compile_pipeline(device, MSL_TENSOR_SUB, "tensor_sub", &ctx->tensor_sub);
        metal_compile_pipeline(device, MSL_TENSOR_MUL, "tensor_mul", &ctx->tensor_mul);
        metal_compile_pipeline(device, MSL_TENSOR_DIV, "tensor_div", &ctx->tensor_div);
        metal_compile_pipeline(device, MSL_TENSOR_MATMUL, "tensor_matmul", &ctx->tensor_matmul);

        ctx->initialized = 1;
    }
    return 0;
}

MN_METAL_EXPORT void mapanare_metal_shutdown(mn_metal_ctx_t *ctx) {
    if (!ctx || !ctx->initialized) return;

    /* Release pipeline objects */
    mn_metal_pipeline_t *pipelines[] = {
        &ctx->tensor_add, &ctx->tensor_sub, &ctx->tensor_mul,
        &ctx->tensor_div, &ctx->tensor_matmul
    };
    for (int i = 0; i < 5; i++) {
        if (pipelines[i]->pipeline_state)
            CFRelease(pipelines[i]->pipeline_state);
        if (pipelines[i]->function)
            CFRelease(pipelines[i]->function);
    }

    if (ctx->command_queue) CFRelease(ctx->command_queue);
    if (ctx->device) CFRelease(ctx->device);

    memset(ctx, 0, sizeof(*ctx));
}

/* -----------------------------------------------------------------------
 * Buffer management — uses shared memory on Apple Silicon
 * ----------------------------------------------------------------------- */

MN_METAL_EXPORT mn_metal_buffer_t *mapanare_metal_buffer_alloc(mn_metal_ctx_t *ctx, size_t bytes) {
    if (!ctx || !ctx->initialized || bytes == 0) return NULL;

    @autoreleasepool {
        id<MTLDevice> device = (__bridge id<MTLDevice>)ctx->device;

        /* MTLResourceStorageModeShared = CPU + GPU accessible (zero-copy on Apple Silicon) */
        id<MTLBuffer> mtl_buf = [device newBufferWithLength:bytes options:MTLResourceStorageModeShared];
        if (!mtl_buf) return NULL;

        mn_metal_buffer_t *buf = (mn_metal_buffer_t *)calloc(1, sizeof(mn_metal_buffer_t));
        if (!buf) return NULL;

        buf->buffer = (__bridge_retained void *)mtl_buf;
        buf->contents = [mtl_buf contents];
        buf->size_bytes = bytes;
        return buf;
    }
}

MN_METAL_EXPORT void mapanare_metal_buffer_free(mn_metal_buffer_t *buf) {
    if (!buf) return;
    if (buf->buffer) CFRelease(buf->buffer);
    free(buf);
}

/* -----------------------------------------------------------------------
 * Compute dispatch
 * ----------------------------------------------------------------------- */

MN_METAL_EXPORT int mapanare_metal_dispatch(
    mn_metal_ctx_t *ctx,
    mn_metal_pipeline_t *pipeline,
    mn_metal_buffer_t **buffers,
    uint32_t buffer_count,
    uint32_t grid_x, uint32_t grid_y, uint32_t grid_z)
{
    if (!ctx || !ctx->initialized || !pipeline || !pipeline->pipeline_state) return -1;

    @autoreleasepool {
        id<MTLCommandQueue> queue = (__bridge id<MTLCommandQueue>)ctx->command_queue;
        id<MTLComputePipelineState> pso = (__bridge id<MTLComputePipelineState>)pipeline->pipeline_state;

        id<MTLCommandBuffer> cmdBuf = [queue commandBuffer];
        if (!cmdBuf) return -1;

        id<MTLComputeCommandEncoder> encoder = [cmdBuf computeCommandEncoder];
        if (!encoder) return -1;

        [encoder setComputePipelineState:pso];

        for (uint32_t i = 0; i < buffer_count; i++) {
            if (buffers[i] && buffers[i]->buffer) {
                [encoder setBuffer:(__bridge id<MTLBuffer>)buffers[i]->buffer offset:0 atIndex:i];
            }
        }

        MTLSize gridSize = MTLSizeMake(grid_x, grid_y, grid_z);

        /* Calculate threadgroup size based on pipeline's max */
        uint32_t tg = pipeline->thread_group_size;
        if (tg > grid_x) tg = grid_x;
        MTLSize threadgroupSize = MTLSizeMake(tg, 1, 1);

        [encoder dispatchThreads:gridSize threadsPerThreadgroup:threadgroupSize];
        [encoder endEncoding];

        [cmdBuf commit];
        [cmdBuf waitUntilCompleted];

        if ([cmdBuf error]) {
            fprintf(stderr, "Metal: dispatch error: %s\n",
                    [[cmdBuf error] localizedDescription].UTF8String);
            return -1;
        }
    }
    return 0;
}

/* -----------------------------------------------------------------------
 * Compile user-provided MSL source
 * ----------------------------------------------------------------------- */

MN_METAL_EXPORT mn_metal_pipeline_t *mapanare_metal_compile(
    mn_metal_ctx_t *ctx, const char *msl_source, const char *function_name)
{
    if (!ctx || !ctx->initialized || !msl_source || !function_name) return NULL;

    mn_metal_pipeline_t *pipeline = (mn_metal_pipeline_t *)calloc(1, sizeof(mn_metal_pipeline_t));
    if (!pipeline) return NULL;

    id<MTLDevice> device = (__bridge id<MTLDevice>)ctx->device;
    if (metal_compile_pipeline(device, msl_source, function_name, pipeline) != 0) {
        free(pipeline);
        return NULL;
    }
    return pipeline;
}

MN_METAL_EXPORT void mapanare_metal_pipeline_free(mn_metal_pipeline_t *pipeline) {
    if (!pipeline) return;
    if (pipeline->pipeline_state) CFRelease(pipeline->pipeline_state);
    if (pipeline->function) CFRelease(pipeline->function);
    free(pipeline);
}

/* -----------------------------------------------------------------------
 * Tensor operations — element-wise
 *
 * These convert f64 tensors to f32 for Metal (Metal has limited f64 support),
 * dispatch the compute kernel, then convert back to f64.
 * ----------------------------------------------------------------------- */

static mapanare_tensor_t *metal_elementwise_op(
    mn_metal_ctx_t *ctx,
    const mapanare_tensor_t *a,
    const mapanare_tensor_t *b,
    mn_metal_pipeline_t *pipeline)
{
    if (!ctx->initialized || !pipeline->pipeline_state) return NULL;
    if (!mapanare_tensor_shape_eq(a, b)) return NULL;

    int64_t n = a->size;
    size_t f32_bytes = (size_t)n * sizeof(float);

    /* Allocate Metal buffers */
    mn_metal_buffer_t *buf_a   = mapanare_metal_buffer_alloc(ctx, f32_bytes);
    mn_metal_buffer_t *buf_b   = mapanare_metal_buffer_alloc(ctx, f32_bytes);
    mn_metal_buffer_t *buf_out = mapanare_metal_buffer_alloc(ctx, f32_bytes);
    if (!buf_a || !buf_b || !buf_out) {
        mapanare_metal_buffer_free(buf_a);
        mapanare_metal_buffer_free(buf_b);
        mapanare_metal_buffer_free(buf_out);
        return NULL;
    }

    /* Convert f64 -> f32 and upload (shared memory = direct write) */
    const double *da = (const double *)a->data;
    const double *db = (const double *)b->data;
    float *fa = (float *)buf_a->contents;
    float *fb = (float *)buf_b->contents;
    for (int64_t i = 0; i < n; i++) {
        fa[i] = (float)da[i];
        fb[i] = (float)db[i];
    }

    /* Dispatch */
    mn_metal_buffer_t *bufs[] = { buf_a, buf_b, buf_out };
    int rc = mapanare_metal_dispatch(ctx, pipeline, bufs, 3, (uint32_t)n, 1, 1);

    mapanare_tensor_t *result = NULL;
    if (rc == 0) {
        result = mapanare_tensor_alloc(a->ndim, a->shape, sizeof(double));
        if (result) {
            float *fout = (float *)buf_out->contents;
            double *dout = (double *)result->data;
            for (int64_t i = 0; i < n; i++) {
                dout[i] = (double)fout[i];
            }
        }
    }

    mapanare_metal_buffer_free(buf_a);
    mapanare_metal_buffer_free(buf_b);
    mapanare_metal_buffer_free(buf_out);
    return result;
}

MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_add(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    return metal_elementwise_op(ctx, a, b, &ctx->tensor_add);
}

MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_sub(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    return metal_elementwise_op(ctx, a, b, &ctx->tensor_sub);
}

MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_mul(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    return metal_elementwise_op(ctx, a, b, &ctx->tensor_mul);
}

MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_div(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    return metal_elementwise_op(ctx, a, b, &ctx->tensor_div);
}

/* -----------------------------------------------------------------------
 * Matrix multiply via Metal
 * ----------------------------------------------------------------------- */

MN_METAL_EXPORT mapanare_tensor_t *mapanare_metal_tensor_matmul(
    mn_metal_ctx_t *ctx, const mapanare_tensor_t *a, const mapanare_tensor_t *b)
{
    if (!ctx->initialized || !ctx->tensor_matmul.pipeline_state) return NULL;
    if (a->ndim != 2 || b->ndim != 2) return NULL;
    if (a->shape[1] != b->shape[0]) return NULL;  /* K dimension must match */

    int64_t M = a->shape[0];
    int64_t K = a->shape[1];
    int64_t N = b->shape[1];

    size_t a_f32_bytes   = (size_t)(M * K) * sizeof(float);
    size_t b_f32_bytes   = (size_t)(K * N) * sizeof(float);
    size_t out_f32_bytes = (size_t)(M * N) * sizeof(float);

    mn_metal_buffer_t *buf_a      = mapanare_metal_buffer_alloc(ctx, a_f32_bytes);
    mn_metal_buffer_t *buf_b      = mapanare_metal_buffer_alloc(ctx, b_f32_bytes);
    mn_metal_buffer_t *buf_out    = mapanare_metal_buffer_alloc(ctx, out_f32_bytes);
    mn_metal_buffer_t *buf_params = mapanare_metal_buffer_alloc(ctx, 3 * sizeof(uint32_t));

    if (!buf_a || !buf_b || !buf_out || !buf_params) {
        mapanare_metal_buffer_free(buf_a);
        mapanare_metal_buffer_free(buf_b);
        mapanare_metal_buffer_free(buf_out);
        mapanare_metal_buffer_free(buf_params);
        return NULL;
    }

    /* Convert f64 -> f32 */
    const double *da = (const double *)a->data;
    const double *db = (const double *)b->data;
    float *fa = (float *)buf_a->contents;
    float *fb = (float *)buf_b->contents;
    for (int64_t i = 0; i < M * K; i++) fa[i] = (float)da[i];
    for (int64_t i = 0; i < K * N; i++) fb[i] = (float)db[i];

    /* Set params */
    uint32_t *params = (uint32_t *)buf_params->contents;
    params[0] = (uint32_t)M;
    params[1] = (uint32_t)K;
    params[2] = (uint32_t)N;

    /* Dispatch with 2D grid */
    @autoreleasepool {
        id<MTLCommandQueue> queue = (__bridge id<MTLCommandQueue>)ctx->command_queue;
        id<MTLComputePipelineState> pso =
            (__bridge id<MTLComputePipelineState>)ctx->tensor_matmul.pipeline_state;

        id<MTLCommandBuffer> cmdBuf = [queue commandBuffer];
        id<MTLComputeCommandEncoder> encoder = [cmdBuf computeCommandEncoder];

        [encoder setComputePipelineState:pso];
        [encoder setBuffer:(__bridge id<MTLBuffer>)buf_a->buffer offset:0 atIndex:0];
        [encoder setBuffer:(__bridge id<MTLBuffer>)buf_b->buffer offset:0 atIndex:1];
        [encoder setBuffer:(__bridge id<MTLBuffer>)buf_out->buffer offset:0 atIndex:2];
        [encoder setBuffer:(__bridge id<MTLBuffer>)buf_params->buffer offset:0 atIndex:3];

        /* 2D dispatch: columns x rows */
        MTLSize gridSize = MTLSizeMake((NSUInteger)N, (NSUInteger)M, 1);
        NSUInteger w = pso.threadExecutionWidth;
        NSUInteger h = pso.maxTotalThreadsPerThreadgroup / w;
        if (h > (NSUInteger)M) h = (NSUInteger)M;
        if (w > (NSUInteger)N) w = (NSUInteger)N;
        MTLSize threadgroupSize = MTLSizeMake(w, h, 1);

        [encoder dispatchThreads:gridSize threadsPerThreadgroup:threadgroupSize];
        [encoder endEncoding];
        [cmdBuf commit];
        [cmdBuf waitUntilCompleted];

        if ([cmdBuf error]) {
            mapanare_metal_buffer_free(buf_a);
            mapanare_metal_buffer_free(buf_b);
            mapanare_metal_buffer_free(buf_out);
            mapanare_metal_buffer_free(buf_params);
            return NULL;
        }
    }

    /* Convert f32 -> f64 result */
    int64_t out_shape[2] = { M, N };
    mapanare_tensor_t *result = mapanare_tensor_alloc(2, out_shape, sizeof(double));
    if (result) {
        float *fout = (float *)buf_out->contents;
        double *dout = (double *)result->data;
        for (int64_t i = 0; i < M * N; i++) dout[i] = (double)fout[i];
    }

    mapanare_metal_buffer_free(buf_a);
    mapanare_metal_buffer_free(buf_b);
    mapanare_metal_buffer_free(buf_out);
    mapanare_metal_buffer_free(buf_params);
    return result;
}

#endif /* __APPLE__ */
