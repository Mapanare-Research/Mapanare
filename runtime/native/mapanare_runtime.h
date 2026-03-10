/**
 * mapanare_runtime.h — Native agent runtime for Mapanare (Phase 4.3)
 *
 * Provides:
 *   - Lock-free SPSC ring buffer for message queues
 *   - Thread pool with one thread per physical core
 *   - Atomic backpressure counters
 *   - Agent scheduler with lifecycle management (called via FFI)
 */

#ifndef MAPANARE_RUNTIME_H
#define MAPANARE_RUNTIME_H

#include <stdint.h>
#include <stddef.h>

/* -----------------------------------------------------------------------
 * Platform abstractions
 * ----------------------------------------------------------------------- */

#ifdef _WIN32
  #define MAPANARE_EXPORT __declspec(dllexport)
  #include <windows.h>
  typedef HANDLE            mapanare_thread_t;
  typedef CRITICAL_SECTION  mapanare_mutex_t;
  typedef HANDLE            mapanare_semaphore_t;
  typedef HANDLE            mapanare_event_t;
  typedef volatile LONG     mapanare_atomic_i32;
  typedef volatile LONG64   mapanare_atomic_i64;
#else
  #define MAPANARE_EXPORT __attribute__((visibility("default")))
  #include <pthread.h>
  #include <semaphore.h>
  #include <stdatomic.h>
  typedef pthread_t         mapanare_thread_t;
  typedef pthread_mutex_t   mapanare_mutex_t;
  typedef sem_t             mapanare_semaphore_t;
  typedef struct { pthread_mutex_t m; pthread_cond_t c; int flag; } mapanare_event_t;
  typedef _Atomic int32_t   mapanare_atomic_i32;
  typedef _Atomic int64_t   mapanare_atomic_i64;
#endif

/* -----------------------------------------------------------------------
 * Cache line size for padding
 * ----------------------------------------------------------------------- */

#define MAPANARE_CACHE_LINE 64

/* -----------------------------------------------------------------------
 * 1. Lock-free SPSC ring buffer
 *
 * Single-producer, single-consumer ring buffer using power-of-two sizing
 * and atomic head/tail indices.  Stores opaque void* message pointers.
 * ----------------------------------------------------------------------- */

typedef struct mapanare_ring_buffer {
    void**           slots;      /* heap-allocated slot array         */
    uint32_t         capacity;   /* always a power of two             */
    uint32_t         mask;       /* capacity - 1 for fast modulo      */
    char             _pad0[MAPANARE_CACHE_LINE - sizeof(void*) - 2*sizeof(uint32_t)];
    mapanare_atomic_i64  head;       /* write index (producer)            */
    char             _pad1[MAPANARE_CACHE_LINE - sizeof(mapanare_atomic_i64)];
    mapanare_atomic_i64  tail;       /* read index  (consumer)            */
    char             _pad2[MAPANARE_CACHE_LINE - sizeof(mapanare_atomic_i64)];
} mapanare_ring_buffer_t;

/** Create a ring buffer with at least `min_capacity` slots (rounded up to power of 2). */
MAPANARE_EXPORT int  mapanare_ring_create(mapanare_ring_buffer_t *rb, uint32_t min_capacity);

/** Destroy a ring buffer (frees slot array). */
MAPANARE_EXPORT void mapanare_ring_destroy(mapanare_ring_buffer_t *rb);

/** Try to push a message.  Returns 0 on success, -1 if full. */
MAPANARE_EXPORT int  mapanare_ring_push(mapanare_ring_buffer_t *rb, void *msg);

/** Try to pop a message.  Returns 0 on success (msg stored in *out), -1 if empty. */
MAPANARE_EXPORT int  mapanare_ring_pop(mapanare_ring_buffer_t *rb, void **out);

/** Current number of items in the buffer. */
MAPANARE_EXPORT uint32_t mapanare_ring_size(mapanare_ring_buffer_t *rb);

/** Capacity of the ring buffer. */
MAPANARE_EXPORT uint32_t mapanare_ring_capacity(mapanare_ring_buffer_t *rb);

/** Returns 1 if full, 0 otherwise. */
MAPANARE_EXPORT int  mapanare_ring_is_full(mapanare_ring_buffer_t *rb);

/** Returns 1 if empty, 0 otherwise. */
MAPANARE_EXPORT int  mapanare_ring_is_empty(mapanare_ring_buffer_t *rb);

/* -----------------------------------------------------------------------
 * 2. Thread pool — one worker thread per physical core
 * ----------------------------------------------------------------------- */

/** Signature for work items submitted to the pool. */
typedef void (*mapanare_work_fn)(void *arg);

typedef struct mapanare_work_item {
    mapanare_work_fn  fn;
    void         *arg;
} mapanare_work_item_t;

typedef struct mapanare_thread_pool {
    mapanare_thread_t  *threads;         /* worker thread handles            */
    uint32_t        thread_count;    /* number of workers                */
    mapanare_ring_buffer_t work_queue;   /* ring buffer of work items        */
    mapanare_semaphore_t   work_ready;   /* signalled when work is available */
    mapanare_atomic_i32    running;      /* 1 = pool active, 0 = shutting down */
} mapanare_thread_pool_t;

/** Create a thread pool.  If `num_threads == 0`, auto-detect core count. */
MAPANARE_EXPORT int  mapanare_pool_create(mapanare_thread_pool_t *pool, uint32_t num_threads);

/** Destroy the pool, joining all threads. */
MAPANARE_EXPORT void mapanare_pool_destroy(mapanare_thread_pool_t *pool);

/** Submit a work item.  Returns 0 on success, -1 if the queue is full. */
MAPANARE_EXPORT int  mapanare_pool_submit(mapanare_thread_pool_t *pool, mapanare_work_fn fn, void *arg);

/** Number of worker threads. */
MAPANARE_EXPORT uint32_t mapanare_pool_thread_count(mapanare_thread_pool_t *pool);

/* -----------------------------------------------------------------------
 * 3. Backpressure — atomic counters
 * ----------------------------------------------------------------------- */

typedef struct mapanare_backpressure {
    mapanare_atomic_i64  pending;        /* messages waiting to be processed */
    mapanare_atomic_i64  capacity;       /* max before signalling overload   */
    mapanare_atomic_i32  overloaded;     /* 1 = overloaded, 0 = ok           */
} mapanare_backpressure_t;

/** Initialise a backpressure tracker with the given capacity. */
MAPANARE_EXPORT void mapanare_bp_init(mapanare_backpressure_t *bp, int64_t capacity);

/** Record a new pending message.  Sets overloaded flag if pending >= capacity. */
MAPANARE_EXPORT void mapanare_bp_increment(mapanare_backpressure_t *bp);

/** Record a processed message.  Clears overloaded flag if pending < capacity. */
MAPANARE_EXPORT void mapanare_bp_decrement(mapanare_backpressure_t *bp);

/** Current pending count. */
MAPANARE_EXPORT int64_t mapanare_bp_pending(mapanare_backpressure_t *bp);

/** Returns 1 if overloaded, 0 otherwise. */
MAPANARE_EXPORT int  mapanare_bp_is_overloaded(mapanare_backpressure_t *bp);

/** Current pressure as a fraction 0.0–1.0. */
MAPANARE_EXPORT double mapanare_bp_pressure(mapanare_backpressure_t *bp);

/* -----------------------------------------------------------------------
 * 4. Agent scheduler
 * ----------------------------------------------------------------------- */

/** Agent lifecycle states (mirrors Python AgentState). */
typedef enum {
    MAPANARE_AGENT_IDLE    = 0,
    MAPANARE_AGENT_RUNNING = 1,
    MAPANARE_AGENT_PAUSED  = 2,
    MAPANARE_AGENT_STOPPED = 3,
    MAPANARE_AGENT_FAILED  = 4,
} mapanare_agent_state_t;

/** Restart policy. */
typedef enum {
    MAPANARE_RESTART_STOP    = 0,
    MAPANARE_RESTART_RESTART = 1,
} mapanare_restart_policy_t;

/** Message handler callback.  Return 0 on success, non-zero on error. */
typedef int (*mapanare_handler_fn)(void *agent_data, void *msg, void **out_msg);

/** Lifecycle callbacks. */
typedef void (*mapanare_lifecycle_fn)(void *agent_data);

typedef struct mapanare_agent {
    /* Identity */
    uint64_t             id;
    char                 name[64];

    /* State */
    mapanare_agent_state_t   state;
    mapanare_atomic_i32      paused;           /* 1 = paused */

    /* Message queues */
    mapanare_ring_buffer_t   inbox;            /* incoming messages   */
    mapanare_ring_buffer_t   outbox;           /* outgoing messages   */
    mapanare_backpressure_t  bp;               /* backpressure for inbox */
    mapanare_semaphore_t     inbox_ready;      /* signalled on inbox push  */
    mapanare_semaphore_t     outbox_ready;     /* signalled on outbox push */

    /* Handler */
    mapanare_handler_fn      handler;          /* user message handler   */
    void                *agent_data;       /* opaque user data       */

    /* Lifecycle callbacks */
    mapanare_lifecycle_fn    on_init;
    mapanare_lifecycle_fn    on_stop;
    mapanare_lifecycle_fn    on_pause;
    mapanare_lifecycle_fn    on_resume;

    /* Supervision */
    mapanare_restart_policy_t restart_policy;
    int32_t              max_restarts;
    int32_t              restart_count;

    /* Metrics */
    mapanare_atomic_i64      messages_processed;
    mapanare_atomic_i64      total_latency_us;  /* microseconds */

    /* Internal */
    mapanare_thread_t        thread;
    mapanare_atomic_i32      running;           /* internal run flag */
} mapanare_agent_t;

/** Initialise an agent.  Does NOT start it — call mapanare_agent_spawn(). */
MAPANARE_EXPORT int  mapanare_agent_init(mapanare_agent_t *agent, const char *name,
                                  mapanare_handler_fn handler, void *agent_data,
                                  uint32_t inbox_cap, uint32_t outbox_cap);

/** Spawn (start) the agent on its own thread.  Returns 0 on success. */
MAPANARE_EXPORT int  mapanare_agent_spawn(mapanare_agent_t *agent);

/** Send a message to the agent's inbox.  Returns 0 on success, -1 if full. */
MAPANARE_EXPORT int  mapanare_agent_send(mapanare_agent_t *agent, void *msg);

/** Receive from the agent's outbox.  Returns 0 on success, -1 if empty. */
MAPANARE_EXPORT int  mapanare_agent_recv(mapanare_agent_t *agent, void **out);

/** Pause the agent (it stops processing until resumed). */
MAPANARE_EXPORT void mapanare_agent_pause(mapanare_agent_t *agent);

/** Resume a paused agent. */
MAPANARE_EXPORT void mapanare_agent_resume(mapanare_agent_t *agent);

/** Stop the agent and join its thread. */
MAPANARE_EXPORT void mapanare_agent_stop(mapanare_agent_t *agent);

/** Get current agent state. */
MAPANARE_EXPORT mapanare_agent_state_t mapanare_agent_get_state(mapanare_agent_t *agent);

/** Get messages processed count. */
MAPANARE_EXPORT int64_t mapanare_agent_messages_processed(mapanare_agent_t *agent);

/** Get average latency in microseconds. */
MAPANARE_EXPORT double mapanare_agent_avg_latency_us(mapanare_agent_t *agent);

/** Clean up agent resources (call after stop). */
MAPANARE_EXPORT void mapanare_agent_destroy(mapanare_agent_t *agent);

/** Allocate, init and return a new heap-allocated agent. Returns NULL on failure. */
MAPANARE_EXPORT mapanare_agent_t *mapanare_agent_new(const char *name,
                                                      mapanare_handler_fn handler,
                                                      void *agent_data,
                                                      uint32_t inbox_cap,
                                                      uint32_t outbox_cap);

/** Blocking receive from agent's outbox. Waits until message available or agent stopped.
 *  Returns 0 on success, -1 if agent stopped with no more messages. */
MAPANARE_EXPORT int mapanare_agent_recv_blocking(mapanare_agent_t *agent, void **out);

/** Set the restart policy for an agent. Must be called before spawn. */
MAPANARE_EXPORT void mapanare_agent_set_restart_policy(mapanare_agent_t *agent,
                                                        mapanare_restart_policy_t policy,
                                                        int32_t max_restarts);

/* -----------------------------------------------------------------------
 * Agent registry — track agents by name
 * ----------------------------------------------------------------------- */

#define MAPANARE_MAX_AGENTS 256

typedef struct mapanare_agent_registry {
    mapanare_agent_t *agents[MAPANARE_MAX_AGENTS];
    uint32_t      count;
    mapanare_mutex_t  lock;
} mapanare_agent_registry_t;

/** Initialise the global registry. */
MAPANARE_EXPORT void mapanare_registry_init(mapanare_agent_registry_t *reg);

/** Register an agent.  Returns 0 on success, -1 if full. */
MAPANARE_EXPORT int  mapanare_registry_add(mapanare_agent_registry_t *reg, mapanare_agent_t *agent);

/** Look up an agent by name.  Returns NULL if not found. */
MAPANARE_EXPORT mapanare_agent_t *mapanare_registry_find(mapanare_agent_registry_t *reg, const char *name);

/** Remove an agent by name.  Returns 0 on success. */
MAPANARE_EXPORT int  mapanare_registry_remove(mapanare_agent_registry_t *reg, const char *name);

/** Stop all agents in the registry. */
MAPANARE_EXPORT void mapanare_registry_stop_all(mapanare_agent_registry_t *reg);

/** Number of registered agents. */
MAPANARE_EXPORT uint32_t mapanare_registry_count(mapanare_agent_registry_t *reg);

/** Destroy the registry (does NOT stop agents). */
MAPANARE_EXPORT void mapanare_registry_destroy(mapanare_agent_registry_t *reg);

/* -----------------------------------------------------------------------
 * 5. Tensor operations (Phase 5.1)
 * ----------------------------------------------------------------------- */

/** Tensor struct — contiguous row-major storage. */
typedef struct mapanare_tensor {
    void    *data;       /* pointer to contiguous element buffer         */
    int64_t  ndim;       /* number of dimensions                        */
    int64_t *shape;      /* heap-allocated shape array (ndim elements)   */
    int64_t  size;       /* total number of elements (product of shape)  */
    int64_t  elem_size;  /* size of each element in bytes                */
} mapanare_tensor_t;

/** Allocate a tensor with the given shape and element size. Data is zeroed. */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_alloc(
    int64_t ndim, const int64_t *shape, int64_t elem_size);

/** Free a tensor (data + shape + struct). */
MAPANARE_EXPORT void mapanare_tensor_free(mapanare_tensor_t *t);

/** Check if two tensors have the same shape.  Returns 1 if equal. */
MAPANARE_EXPORT int mapanare_tensor_shape_eq(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise add (float64).  Returns new tensor; caller must free. */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_add_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise subtract (float64). */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_sub_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise multiply (float64). */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_mul_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Element-wise divide (float64). */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_div_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/** Matrix multiply (float64): (M,K) @ (K,N) → (M,N).
 *  Uses cache-friendly i-k-j loop order for SIMD auto-vectorization. */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_matmul_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b);

/* -----------------------------------------------------------------------
 * 6. GPU Backend (Phase 5.2)
 * ----------------------------------------------------------------------- */

/** Device kind enum for GPU dispatch. */
typedef enum {
    MAPANARE_DEVICE_CPU    = 0,
    MAPANARE_DEVICE_CUDA   = 1,
    MAPANARE_DEVICE_METAL  = 2,
    MAPANARE_DEVICE_VULKAN = 3
} mapanare_device_kind_t;

/** GPU device info struct. */
typedef struct mapanare_gpu_device {
    mapanare_device_kind_t kind;
    char                   name[256];
    int                    index;
    int64_t                memory_bytes;
    char                   driver_version[64];
} mapanare_gpu_device_t;

/** GPU detection result. */
typedef struct mapanare_gpu_detection {
    mapanare_gpu_device_t *devices;
    int                    device_count;
    int                    cuda_available;
    int                    metal_available;
    int                    vulkan_available;
} mapanare_gpu_detection_t;

/** Auto-detect all available GPU devices. Caller must free result with
 *  mapanare_gpu_detection_free(). */
MAPANARE_EXPORT mapanare_gpu_detection_t *mapanare_detect_gpus(void);

/** Free a GPU detection result. */
MAPANARE_EXPORT void mapanare_gpu_detection_free(mapanare_gpu_detection_t *det);

/** Dispatch tensor add to the specified device backend. Falls back to CPU. */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_add_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device);

/** Dispatch tensor sub to the specified device backend. */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_sub_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device);

/** Dispatch tensor mul to the specified device backend. */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_mul_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device);

/** Dispatch tensor div to the specified device backend. */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_div_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device);

/** Dispatch matmul to the specified device backend. */
MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_matmul_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device);

/* -----------------------------------------------------------------------
 * Utility
 * ----------------------------------------------------------------------- */

/** Detect number of physical CPU cores. */
MAPANARE_EXPORT uint32_t mapanare_cpu_count(void);

#endif /* MAPANARE_RUNTIME_H */
