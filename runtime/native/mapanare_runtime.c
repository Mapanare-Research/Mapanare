/**
 * mapanare_runtime.c — Native agent runtime implementation (Phase 4.3)
 *
 * Implements:
 *   Task 1: Agent scheduler (called via FFI)
 *   Task 2: Lock-free SPSC ring buffer for message queues
 *   Task 3: Thread pool — one thread per physical core
 *   Task 4: Native backpressure with atomic counters
 */

#include "mapanare_runtime.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <signal.h>

#ifndef _WIN32
#include <unistd.h>
#endif

/* -----------------------------------------------------------------------
 * Platform atomic helpers (using GCC built-ins for portability)
 * ----------------------------------------------------------------------- */

static inline int64_t atomic_load_i64(mapanare_atomic_i64 *p) {
    return __atomic_load_n(p, __ATOMIC_ACQUIRE);
}
static inline void atomic_store_i64(mapanare_atomic_i64 *p, int64_t v) {
    __atomic_store_n(p, v, __ATOMIC_RELEASE);
}
static inline int64_t atomic_add_i64(mapanare_atomic_i64 *p, int64_t v) {
    return __atomic_fetch_add(p, v, __ATOMIC_ACQ_REL);
}
static inline int32_t atomic_load_i32(mapanare_atomic_i32 *p) {
    return __atomic_load_n(p, __ATOMIC_ACQUIRE);
}
static inline void atomic_store_i32(mapanare_atomic_i32 *p, int32_t v) {
    __atomic_store_n(p, v, __ATOMIC_RELEASE);
}
static inline int32_t atomic_add_i32(mapanare_atomic_i32 *p, int32_t v) {
    return __atomic_fetch_add(p, v, __ATOMIC_ACQ_REL);
}

#ifdef _WIN32

static inline void mapanare_mutex_init(mapanare_mutex_t *m) {
    InitializeCriticalSection(m);
}
static inline void mapanare_mutex_lock(mapanare_mutex_t *m) {
    EnterCriticalSection(m);
}
static inline void mapanare_mutex_unlock(mapanare_mutex_t *m) {
    LeaveCriticalSection(m);
}
static inline void mapanare_mutex_destroy(mapanare_mutex_t *m) {
    DeleteCriticalSection(m);
}

static inline void mapanare_sem_init(mapanare_semaphore_t *s, int initial) {
    *s = CreateSemaphoreA(NULL, initial, 0x7FFFFFFF, NULL);
}
static inline void mapanare_sem_wait(mapanare_semaphore_t *s) {
    WaitForSingleObject(*s, INFINITE);
}
static inline void mapanare_sem_post(mapanare_semaphore_t *s) {
    ReleaseSemaphore(*s, 1, NULL);
}
static inline void mapanare_sem_destroy(mapanare_semaphore_t *s) {
    CloseHandle(*s);
}

static inline int64_t mapanare_time_us(void) {
    LARGE_INTEGER freq, now;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&now);
    return (int64_t)((double)now.QuadPart / (double)freq.QuadPart * 1000000.0);
}

static inline void mapanare_sleep_ms(int ms) {
    Sleep((DWORD)ms);
}

typedef DWORD (WINAPI *thread_fn_t)(LPVOID);

static inline int mapanare_thread_create(mapanare_thread_t *t, DWORD (WINAPI *fn)(LPVOID), void *arg) {
    *t = CreateThread(NULL, 0, fn, arg, 0, NULL);
    return (*t == NULL) ? -1 : 0;
}
static inline void mapanare_thread_join(mapanare_thread_t t) {
    WaitForSingleObject(t, INFINITE);
    CloseHandle(t);
}

#else /* POSIX */

static inline void mapanare_mutex_init(mapanare_mutex_t *m) {
    pthread_mutex_init(m, NULL);
}
static inline void mapanare_mutex_lock(mapanare_mutex_t *m) {
    pthread_mutex_lock(m);
}
static inline void mapanare_mutex_unlock(mapanare_mutex_t *m) {
    pthread_mutex_unlock(m);
}
static inline void mapanare_mutex_destroy(mapanare_mutex_t *m) {
    pthread_mutex_destroy(m);
}

#if defined(__APPLE__)
static inline void mapanare_sem_init(mapanare_semaphore_t *s, int initial) {
    *s = dispatch_semaphore_create(initial);
}
static inline void mapanare_sem_wait(mapanare_semaphore_t *s) {
    dispatch_semaphore_wait(*s, DISPATCH_TIME_FOREVER);
}
static inline void mapanare_sem_post(mapanare_semaphore_t *s) {
    dispatch_semaphore_signal(*s);
}
static inline void mapanare_sem_destroy(mapanare_semaphore_t *s) {
    /* dispatch_semaphore is ARC-managed or refcounted; release if non-ARC */
    #if !__has_feature(objc_arc)
    dispatch_release(*s);
    #endif
    *s = NULL;
}
#else
static inline void mapanare_sem_init(mapanare_semaphore_t *s, int initial) {
    sem_init(s, 0, initial);
}
static inline void mapanare_sem_wait(mapanare_semaphore_t *s) {
    sem_wait(s);
}
static inline void mapanare_sem_post(mapanare_semaphore_t *s) {
    sem_post(s);
}
static inline void mapanare_sem_destroy(mapanare_semaphore_t *s) {
    sem_destroy(s);
}
#endif

#include <time.h>
static inline int64_t mapanare_time_us(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000 + ts.tv_nsec / 1000;
}

static inline void mapanare_sleep_ms(int ms) {
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (ms % 1000) * 1000000L;
    nanosleep(&ts, NULL);
}

static inline int mapanare_thread_create(mapanare_thread_t *t, void *(*fn)(void*), void *arg) {
    return pthread_create(t, NULL, fn, arg);
}
static inline void mapanare_thread_join(mapanare_thread_t t) {
    pthread_join(t, NULL);
}

#endif

/* Trace hook — declared early so agent_thread_fn can call trace_emit */
static mapanare_trace_hook_fn s_trace_hook = NULL;

static inline void trace_emit(
    mapanare_trace_event_t event,
    const mapanare_agent_t *agent,
    void *data,
    int64_t duration_us
) {
    mapanare_trace_hook_fn hook = __atomic_load_n(&s_trace_hook, __ATOMIC_ACQUIRE);
    if (hook) {
        hook(event, agent, data, duration_us);
    }
}

/* -----------------------------------------------------------------------
 * Utility: CPU core count
 * ----------------------------------------------------------------------- */

MAPANARE_EXPORT uint32_t mapanare_cpu_count(void) {
#ifdef _WIN32
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    return (uint32_t)si.dwNumberOfProcessors;
#else
    long n = sysconf(_SC_NPROCESSORS_ONLN);
    return (n > 0) ? (uint32_t)n : 1;
#endif
}

/* -----------------------------------------------------------------------
 * Utility: next power of two
 * ----------------------------------------------------------------------- */

static uint32_t next_pow2(uint32_t v) {
    if (v == 0) return 1;
    v--;
    v |= v >> 1;
    v |= v >> 2;
    v |= v >> 4;
    v |= v >> 8;
    v |= v >> 16;
    return v + 1;
}

/* =======================================================================
 * Task 2: Lock-free SPSC ring buffer
 * ======================================================================= */

MAPANARE_EXPORT int mapanare_ring_create(mapanare_ring_buffer_t *rb, uint32_t min_capacity) {
    if (min_capacity == 0) min_capacity = 1;
    uint32_t cap = next_pow2(min_capacity);
    rb->slots = (void**)calloc(cap, sizeof(void*));
    if (!rb->slots) return -1;
    rb->capacity = cap;
    rb->mask = cap - 1;
    atomic_store_i64(&rb->head, 0);
    atomic_store_i64(&rb->tail, 0);
    return 0;
}

MAPANARE_EXPORT void mapanare_ring_destroy(mapanare_ring_buffer_t *rb) {
    if (rb->slots) {
        free(rb->slots);
        rb->slots = NULL;
    }
    rb->capacity = 0;
    rb->mask = 0;
}

MAPANARE_EXPORT int mapanare_ring_push(mapanare_ring_buffer_t *rb, void *msg) {
    int64_t h = atomic_load_i64(&rb->head);
    int64_t t = atomic_load_i64(&rb->tail);
    if ((uint32_t)(h - t) >= rb->capacity) {
        return -1;  /* full */
    }
    rb->slots[h & rb->mask] = msg;
    /* Store barrier: ensure slot write is visible before head advances. */
    atomic_store_i64(&rb->head, h + 1);
    return 0;
}

MAPANARE_EXPORT int mapanare_ring_pop(mapanare_ring_buffer_t *rb, void **out) {
    int64_t t = atomic_load_i64(&rb->tail);
    int64_t h = atomic_load_i64(&rb->head);
    if (t >= h) {
        return -1;  /* empty */
    }
    *out = rb->slots[t & rb->mask];
    /* Store barrier: ensure slot read completes before tail advances. */
    atomic_store_i64(&rb->tail, t + 1);
    return 0;
}

MAPANARE_EXPORT uint32_t mapanare_ring_size(mapanare_ring_buffer_t *rb) {
    int64_t h = atomic_load_i64(&rb->head);
    int64_t t = atomic_load_i64(&rb->tail);
    return (uint32_t)(h - t);
}

MAPANARE_EXPORT uint32_t mapanare_ring_capacity(mapanare_ring_buffer_t *rb) {
    return rb->capacity;
}

MAPANARE_EXPORT int mapanare_ring_is_full(mapanare_ring_buffer_t *rb) {
    return mapanare_ring_size(rb) >= rb->capacity ? 1 : 0;
}

MAPANARE_EXPORT int mapanare_ring_is_empty(mapanare_ring_buffer_t *rb) {
    return mapanare_ring_size(rb) == 0 ? 1 : 0;
}

/* =======================================================================
 * Task 4: Native backpressure with atomic counters
 * ======================================================================= */

MAPANARE_EXPORT void mapanare_bp_init(mapanare_backpressure_t *bp, int64_t capacity) {
    atomic_store_i64(&bp->pending, 0);
    atomic_store_i64(&bp->capacity, capacity);
    atomic_store_i32(&bp->overloaded, 0);
}

MAPANARE_EXPORT void mapanare_bp_increment(mapanare_backpressure_t *bp) {
    int64_t new_val = atomic_add_i64(&bp->pending, 1) + 1;
    int64_t cap = atomic_load_i64(&bp->capacity);
    if (new_val >= cap) {
        atomic_store_i32(&bp->overloaded, 1);
    }
}

MAPANARE_EXPORT void mapanare_bp_decrement(mapanare_backpressure_t *bp) {
    int64_t new_val = atomic_add_i64(&bp->pending, -1) - 1;
    int64_t cap = atomic_load_i64(&bp->capacity);
    if (new_val < cap) {
        atomic_store_i32(&bp->overloaded, 0);
    }
}

MAPANARE_EXPORT int64_t mapanare_bp_pending(mapanare_backpressure_t *bp) {
    return atomic_load_i64(&bp->pending);
}

MAPANARE_EXPORT int mapanare_bp_is_overloaded(mapanare_backpressure_t *bp) {
    return atomic_load_i32(&bp->overloaded) != 0 ? 1 : 0;
}

MAPANARE_EXPORT double mapanare_bp_pressure(mapanare_backpressure_t *bp) {
    int64_t pend = atomic_load_i64(&bp->pending);
    int64_t cap = atomic_load_i64(&bp->capacity);
    if (cap <= 0) return 1.0;
    double ratio = (double)pend / (double)cap;
    if (ratio < 0.0) return 0.0;
    if (ratio > 1.0) return 1.0;
    return ratio;
}

/* =======================================================================
 * Task 3: Thread pool — one thread per physical core
 * ======================================================================= */

#ifdef _WIN32
static DWORD WINAPI pool_worker(LPVOID arg) {
#else
static void *pool_worker(void *arg) {
#endif
    mapanare_thread_pool_t *pool = (mapanare_thread_pool_t *)arg;
    while (atomic_load_i32(&pool->running)) {
        mapanare_sem_wait(&pool->work_ready);
        if (!atomic_load_i32(&pool->running)) break;

        void *item_ptr = NULL;
        mapanare_mutex_lock(&pool->queue_lock);
        int got = mapanare_ring_pop(&pool->work_queue, &item_ptr);
        mapanare_mutex_unlock(&pool->queue_lock);
        if (got == 0 && item_ptr != NULL) {
            mapanare_work_item_t *item = (mapanare_work_item_t *)item_ptr;
            item->fn(item->arg);
            free(item);
        }
    }
#ifdef _WIN32
    return 0;
#else
    return NULL;
#endif
}

MAPANARE_EXPORT int mapanare_pool_create(mapanare_thread_pool_t *pool, uint32_t num_threads) {
    if (num_threads == 0) {
        num_threads = mapanare_cpu_count();
    }
    if (num_threads == 0) num_threads = 1;

    pool->thread_count = num_threads;
    atomic_store_i32(&pool->running, 1);

    if (mapanare_ring_create(&pool->work_queue, MAPANARE_DEFAULT_RING_CAPACITY) != 0) {
        return -1;
    }

    mapanare_mutex_init(&pool->queue_lock);
    mapanare_sem_init(&pool->work_ready, 0);

    pool->threads = (mapanare_thread_t *)calloc(num_threads, sizeof(mapanare_thread_t));
    if (!pool->threads) {
        mapanare_ring_destroy(&pool->work_queue);
        return -1;
    }

    for (uint32_t i = 0; i < num_threads; i++) {
        if (mapanare_thread_create(&pool->threads[i], pool_worker, pool) != 0) {
            /* Partial failure — stop already-started threads */
            atomic_store_i32(&pool->running, 0);
            for (uint32_t j = 0; j < i; j++) {
                mapanare_sem_post(&pool->work_ready);
            }
            for (uint32_t j = 0; j < i; j++) {
                mapanare_thread_join(pool->threads[j]);
            }
            free(pool->threads);
            mapanare_ring_destroy(&pool->work_queue);
            mapanare_mutex_destroy(&pool->queue_lock);
            return -1;
        }
    }
    return 0;
}

MAPANARE_EXPORT void mapanare_pool_destroy(mapanare_thread_pool_t *pool) {
    atomic_store_i32(&pool->running, 0);

    /* Wake all workers so they can exit */
    for (uint32_t i = 0; i < pool->thread_count; i++) {
        mapanare_sem_post(&pool->work_ready);
    }

    for (uint32_t i = 0; i < pool->thread_count; i++) {
        mapanare_thread_join(pool->threads[i]);
    }

    /* Drain remaining work items */
    void *item_ptr = NULL;
    while (mapanare_ring_pop(&pool->work_queue, &item_ptr) == 0) {
        free(item_ptr);
    }

    free(pool->threads);
    mapanare_ring_destroy(&pool->work_queue);
    mapanare_mutex_destroy(&pool->queue_lock);
    mapanare_sem_destroy(&pool->work_ready);
}

MAPANARE_EXPORT int mapanare_pool_submit(mapanare_thread_pool_t *pool, mapanare_work_fn fn, void *arg) {
    mapanare_work_item_t *item = (mapanare_work_item_t *)malloc(sizeof(mapanare_work_item_t));
    if (!item) return -1;
    item->fn = fn;
    item->arg = arg;

    mapanare_mutex_lock(&pool->queue_lock);
    int rc = mapanare_ring_push(&pool->work_queue, item);
    mapanare_mutex_unlock(&pool->queue_lock);
    if (rc != 0) {
        free(item);
        return -1;
    }
    mapanare_sem_post(&pool->work_ready);
    return 0;
}

MAPANARE_EXPORT uint32_t mapanare_pool_thread_count(mapanare_thread_pool_t *pool) {
    return pool->thread_count;
}

/* =======================================================================
 * Global lazy-initialized thread pool
 *
 * The pool is created on first use (when the first agent is spawned)
 * rather than eagerly at startup. This saves resources on mobile targets
 * and programs that never spawn agents.
 * ======================================================================= */

static mapanare_thread_pool_t mn_global_pool;
static mapanare_atomic_i32 mn_pool_initialized = 0;
static mapanare_atomic_i32 mn_pool_initializing = 0;

MAPANARE_EXPORT mapanare_thread_pool_t *mapanare_ensure_pool(void) {
    if (atomic_load_i32(&mn_pool_initialized)) {
        return &mn_global_pool;
    }
    /* Simple spinlock for one-time init */
    int32_t expected = 0;
    if (__atomic_compare_exchange_n(&mn_pool_initializing, &expected, 1,
                                    0, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE)) {
        if (mapanare_pool_create(&mn_global_pool, MAPANARE_DEFAULT_THREADS) != 0) {
            atomic_store_i32(&mn_pool_initializing, 0);
            return NULL;
        }
        atomic_store_i32(&mn_pool_initialized, 1);
    } else {
        /* Another thread is initializing — spin until done */
        while (!atomic_load_i32(&mn_pool_initialized)) {
#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
            __builtin_ia32_pause();
#elif defined(__aarch64__)
            __asm__ volatile("yield");
#endif
        }
    }
    return &mn_global_pool;
}

MAPANARE_EXPORT void mapanare_pool_destroy_global(void) {
    if (atomic_load_i32(&mn_pool_initialized)) {
        mapanare_pool_destroy(&mn_global_pool);
        atomic_store_i32(&mn_pool_initialized, 0);
        atomic_store_i32(&mn_pool_initializing, 0);
    }
}

/* =======================================================================
 * Task 1: Agent scheduler — port to C (called via FFI)
 * ======================================================================= */

static uint64_t s_next_agent_id = 1;

#ifdef _WIN32
static DWORD WINAPI agent_thread_fn(LPVOID arg) {
#else
static void *agent_thread_fn(void *arg) {
#endif
    mapanare_agent_t *agent = (mapanare_agent_t *)arg;

    atomic_store_i32(&agent->state, MAPANARE_AGENT_RUNNING);
    if (agent->on_init) agent->on_init(agent->agent_data);

    int restarts = 0;

    while (atomic_load_i32(&agent->running)) {
        /* Check for pause */
        if (atomic_load_i32(&agent->paused)) {
            mapanare_sleep_ms(1);
            continue;
        }

        /* Try to receive a message from inbox */
        void *msg = NULL;
        if (mapanare_ring_pop(&agent->inbox, &msg) == 0 && msg != NULL) {
            mapanare_bp_decrement(&agent->bp);

            int64_t t0 = mapanare_time_us();
            void *out_msg = NULL;
            int rc = 0;

            if (agent->handler) {
                rc = agent->handler(agent->agent_data, msg, &out_msg);
            }

            int64_t elapsed = mapanare_time_us() - t0;
            atomic_add_i64(&agent->messages_processed, 1);
            atomic_add_i64(&agent->total_latency_us, elapsed);
            trace_emit(MAPANARE_TRACE_HANDLE, agent, msg, elapsed);

            if (rc != 0) {
                trace_emit(MAPANARE_TRACE_ERROR, agent, msg, 0);
                /* Handler error — apply supervision */
                if (agent->restart_policy == MAPANARE_RESTART_RESTART) {
                    restarts++;
                    agent->restart_count = restarts;
                    if (restarts > agent->max_restarts) {
                        atomic_store_i32(&agent->state, MAPANARE_AGENT_FAILED);
                        atomic_store_i32(&agent->running, 0);
                        break;
                    }
                    continue;
                } else {
                    atomic_store_i32(&agent->state, MAPANARE_AGENT_FAILED);
                    atomic_store_i32(&agent->running, 0);
                    break;
                }
            }

            /* Send output if handler produced one */
            if (out_msg != NULL) {
                mapanare_ring_push(&agent->outbox, out_msg);
                mapanare_sem_post(&agent->outbox_ready);
            }
        } else {
            /* No message — wait on semaphore instead of polling */
            mapanare_sem_wait(&agent->inbox_ready);
        }
    }

    if (atomic_load_i32(&agent->state) != MAPANARE_AGENT_FAILED) {
        atomic_store_i32(&agent->state, MAPANARE_AGENT_STOPPED);
    }
    if (agent->on_stop) agent->on_stop(agent->agent_data);

#ifdef _WIN32
    return 0;
#else
    return NULL;
#endif
}

MAPANARE_EXPORT int mapanare_agent_init(mapanare_agent_t *agent, const char *name,
                                 mapanare_handler_fn handler, void *agent_data,
                                 uint32_t inbox_cap, uint32_t outbox_cap) {
    memset(agent, 0, sizeof(*agent));
    agent->id = __atomic_fetch_add(&s_next_agent_id, 1, __ATOMIC_RELAXED);
    if (name) {
        strncpy(agent->name, name, sizeof(agent->name) - 1);
        agent->name[sizeof(agent->name) - 1] = '\0';
    }
    atomic_store_i32(&agent->state, MAPANARE_AGENT_IDLE);
    agent->handler = handler;
    agent->agent_data = agent_data;
    agent->restart_policy = MAPANARE_RESTART_STOP;
    agent->max_restarts = 0;
    agent->restart_count = 0;

    atomic_store_i32(&agent->paused, 0);
    atomic_store_i32(&agent->running, 0);
    atomic_store_i64(&agent->messages_processed, 0);
    atomic_store_i64(&agent->total_latency_us, 0);

    if (inbox_cap == 0) inbox_cap = MAPANARE_DEFAULT_AGENT_QUEUE;
    if (outbox_cap == 0) outbox_cap = MAPANARE_DEFAULT_AGENT_QUEUE;

    if (mapanare_ring_create(&agent->inbox, inbox_cap) != 0) return -1;
    if (mapanare_ring_create(&agent->outbox, outbox_cap) != 0) {
        mapanare_ring_destroy(&agent->inbox);
        return -1;
    }

    mapanare_bp_init(&agent->bp, (int64_t)agent->inbox.capacity);

    mapanare_sem_init(&agent->inbox_ready, 0);
    mapanare_sem_init(&agent->outbox_ready, 0);
    return 0;
}

MAPANARE_EXPORT int mapanare_agent_spawn(mapanare_agent_t *agent) {
    /* Ensure the global thread pool is initialized on first agent spawn */
    mapanare_ensure_pool();

    atomic_store_i32(&agent->running, 1);
    int rc = mapanare_thread_create(&agent->thread, agent_thread_fn, agent);
    if (rc == 0) {
        trace_emit(MAPANARE_TRACE_SPAWN, agent, NULL, 0);
    }
    return rc;
}

MAPANARE_EXPORT int mapanare_agent_send(mapanare_agent_t *agent, void *msg) {
    int rc = mapanare_ring_push(&agent->inbox, msg);
    if (rc == 0) {
        mapanare_bp_increment(&agent->bp);
        mapanare_sem_post(&agent->inbox_ready);
        trace_emit(MAPANARE_TRACE_SEND, agent, msg, 0);
    }
    return rc;
}

MAPANARE_EXPORT int mapanare_agent_recv(mapanare_agent_t *agent, void **out) {
    return mapanare_ring_pop(&agent->outbox, out);
}

MAPANARE_EXPORT void mapanare_agent_pause(mapanare_agent_t *agent) {
    if (atomic_load_i32(&agent->state) == MAPANARE_AGENT_RUNNING) {
        atomic_store_i32(&agent->state, MAPANARE_AGENT_PAUSED);
        atomic_store_i32(&agent->paused, 1);
        trace_emit(MAPANARE_TRACE_PAUSE, agent, NULL, 0);
        if (agent->on_pause) agent->on_pause(agent->agent_data);
    }
}

MAPANARE_EXPORT void mapanare_agent_resume(mapanare_agent_t *agent) {
    if (atomic_load_i32(&agent->state) == MAPANARE_AGENT_PAUSED) {
        atomic_store_i32(&agent->state, MAPANARE_AGENT_RUNNING);
        atomic_store_i32(&agent->paused, 0);
        trace_emit(MAPANARE_TRACE_RESUME, agent, NULL, 0);
        if (agent->on_resume) agent->on_resume(agent->agent_data);
    }
}

MAPANARE_EXPORT void mapanare_agent_stop(mapanare_agent_t *agent) {
    trace_emit(MAPANARE_TRACE_STOP, agent, NULL, 0);
    atomic_store_i32(&agent->running, 0);
    atomic_store_i32(&agent->paused, 0);  /* unblock if paused */
    mapanare_sem_post(&agent->inbox_ready);   /* wake agent thread */
    mapanare_sem_post(&agent->outbox_ready);  /* wake any blocking recv */
    mapanare_thread_join(agent->thread);
}

MAPANARE_EXPORT mapanare_agent_state_t mapanare_agent_get_state(mapanare_agent_t *agent) {
    return (mapanare_agent_state_t)atomic_load_i32(&agent->state);
}

MAPANARE_EXPORT int64_t mapanare_agent_messages_processed(mapanare_agent_t *agent) {
    return atomic_load_i64(&agent->messages_processed);
}

MAPANARE_EXPORT double mapanare_agent_avg_latency_us(mapanare_agent_t *agent) {
    int64_t count = atomic_load_i64(&agent->messages_processed);
    if (count == 0) return 0.0;
    int64_t total = atomic_load_i64(&agent->total_latency_us);
    return (double)total / (double)count;
}

MAPANARE_EXPORT void mapanare_agent_destroy(mapanare_agent_t *agent) {
    /* Drain inbox/outbox — discard remaining messages.
     * Messages are void* and may not be heap-allocated,
     * so we cannot free them here. Callers own message lifetime. */
    void *msg = NULL;
    while (mapanare_ring_pop(&agent->inbox, &msg) == 0) { (void)msg; }
    while (mapanare_ring_pop(&agent->outbox, &msg) == 0) { (void)msg; }
    mapanare_ring_destroy(&agent->inbox);
    mapanare_ring_destroy(&agent->outbox);
    mapanare_sem_destroy(&agent->inbox_ready);
    mapanare_sem_destroy(&agent->outbox_ready);
}

MAPANARE_EXPORT mapanare_agent_t *mapanare_agent_new(const char *name,
                                                      mapanare_handler_fn handler,
                                                      void *agent_data,
                                                      uint32_t inbox_cap,
                                                      uint32_t outbox_cap) {
    mapanare_agent_t *agent = (mapanare_agent_t *)calloc(1, sizeof(mapanare_agent_t));
    if (!agent) return NULL;
    if (mapanare_agent_init(agent, name, handler, agent_data, inbox_cap, outbox_cap) != 0) {
        free(agent);
        return NULL;
    }
    return agent;
}

MAPANARE_EXPORT int mapanare_agent_recv_blocking(mapanare_agent_t *agent, void **out) {
    while (1) {
        /* Try non-blocking first */
        if (mapanare_ring_pop(&agent->outbox, out) == 0) {
            return 0;
        }
        /* If agent is done, drain remaining and fail */
        if (!atomic_load_i32(&agent->running)) {
            if (mapanare_ring_pop(&agent->outbox, out) == 0) {
                return 0;
            }
            return -1;
        }
        /* Wait for signal */
        mapanare_sem_wait(&agent->outbox_ready);
    }
}

MAPANARE_EXPORT void mapanare_agent_set_restart_policy(mapanare_agent_t *agent,
                                                        mapanare_restart_policy_t policy,
                                                        int32_t max_restarts) {
    agent->restart_policy = policy;
    agent->max_restarts = max_restarts;
}

/* =======================================================================
 * Agent registry
 * ======================================================================= */

MAPANARE_EXPORT void mapanare_registry_init(mapanare_agent_registry_t *reg) {
    memset(reg->agents, 0, sizeof(reg->agents));
    reg->count = 0;
    mapanare_mutex_init(&reg->lock);
}

MAPANARE_EXPORT int mapanare_registry_add(mapanare_agent_registry_t *reg, mapanare_agent_t *agent) {
    mapanare_mutex_lock(&reg->lock);
    if (reg->count >= MAPANARE_MAX_AGENTS) {
        mapanare_mutex_unlock(&reg->lock);
        return -1;
    }
    reg->agents[reg->count++] = agent;
    mapanare_mutex_unlock(&reg->lock);
    return 0;
}

MAPANARE_EXPORT mapanare_agent_t *mapanare_registry_find(mapanare_agent_registry_t *reg, const char *name) {
    mapanare_mutex_lock(&reg->lock);
    for (uint32_t i = 0; i < reg->count; i++) {
        if (reg->agents[i] && strcmp(reg->agents[i]->name, name) == 0) {
            mapanare_agent_t *found = reg->agents[i];
            mapanare_mutex_unlock(&reg->lock);
            return found;
        }
    }
    mapanare_mutex_unlock(&reg->lock);
    return NULL;
}

MAPANARE_EXPORT int mapanare_registry_remove(mapanare_agent_registry_t *reg, const char *name) {
    mapanare_mutex_lock(&reg->lock);
    for (uint32_t i = 0; i < reg->count; i++) {
        if (reg->agents[i] && strcmp(reg->agents[i]->name, name) == 0) {
            /* Shift remaining entries */
            for (uint32_t j = i; j < reg->count - 1; j++) {
                reg->agents[j] = reg->agents[j + 1];
            }
            reg->agents[--reg->count] = NULL;
            mapanare_mutex_unlock(&reg->lock);
            return 0;
        }
    }
    mapanare_mutex_unlock(&reg->lock);
    return -1;
}

MAPANARE_EXPORT void mapanare_registry_stop_all(mapanare_agent_registry_t *reg) {
    mapanare_mutex_lock(&reg->lock);
    for (uint32_t i = 0; i < reg->count; i++) {
        if (reg->agents[i]) {
            mapanare_agent_stop(reg->agents[i]);
        }
    }
    mapanare_mutex_unlock(&reg->lock);
}

MAPANARE_EXPORT uint32_t mapanare_registry_count(mapanare_agent_registry_t *reg) {
    mapanare_mutex_lock(&reg->lock);
    uint32_t c = reg->count;
    mapanare_mutex_unlock(&reg->lock);
    return c;
}

MAPANARE_EXPORT void mapanare_registry_destroy(mapanare_agent_registry_t *reg) {
    mapanare_mutex_destroy(&reg->lock);
}

/* =======================================================================
 * Task 5.1: Tensor operations (Phase 5.1)
 * ======================================================================= */

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_alloc(
    int64_t ndim, const int64_t *shape, int64_t elem_size) {

    mapanare_tensor_t *t = (mapanare_tensor_t *)malloc(sizeof(mapanare_tensor_t));
    if (!t) return NULL;

    t->ndim = ndim;
    t->elem_size = elem_size;

    /* Allocate and copy shape */
    t->shape = (int64_t *)malloc((size_t)ndim * sizeof(int64_t));
    if (!t->shape) { free(t); return NULL; }

    int64_t total = 1;
    for (int64_t i = 0; i < ndim; i++) {
        t->shape[i] = shape[i];
        total = mn_checked_mul(total, shape[i]);
    }
    t->size = total;

    /* Allocate zeroed data buffer */
    t->data = calloc((size_t)total, (size_t)elem_size);
    if (!t->data) { free(t->shape); free(t); return NULL; }

    return t;
}

MAPANARE_EXPORT void mapanare_tensor_free(mapanare_tensor_t *t) {
    if (!t) return;
    if (t->data)  free(t->data);
    if (t->shape) free(t->shape);
    free(t);
}

MAPANARE_EXPORT int mapanare_tensor_shape_eq(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    if (a->ndim != b->ndim) return 0;
    for (int64_t i = 0; i < a->ndim; i++) {
        if (a->shape[i] != b->shape[i]) return 0;
    }
    return 1;
}

/** Internal: clone shape from source tensor and allocate result. */
static mapanare_tensor_t *tensor_clone_shape(const mapanare_tensor_t *src) {
    return mapanare_tensor_alloc(src->ndim, src->shape, src->elem_size);
}

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_add_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    if (!mapanare_tensor_shape_eq(a, b)) return NULL;
    mapanare_tensor_t *r = tensor_clone_shape(a);
    if (!r) return NULL;
    const double *ad = (const double *)a->data;
    const double *bd = (const double *)b->data;
    double *rd = (double *)r->data;
    /* Simple loop — LLVM auto-vectorizer targets SIMD (SSE/AVX/NEON) */
    for (int64_t i = 0; i < a->size; i++) {
        rd[i] = ad[i] + bd[i];
    }
    return r;
}

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_sub_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    if (!mapanare_tensor_shape_eq(a, b)) return NULL;
    mapanare_tensor_t *r = tensor_clone_shape(a);
    if (!r) return NULL;
    const double *ad = (const double *)a->data;
    const double *bd = (const double *)b->data;
    double *rd = (double *)r->data;
    for (int64_t i = 0; i < a->size; i++) {
        rd[i] = ad[i] - bd[i];
    }
    return r;
}

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_mul_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    if (!mapanare_tensor_shape_eq(a, b)) return NULL;
    mapanare_tensor_t *r = tensor_clone_shape(a);
    if (!r) return NULL;
    const double *ad = (const double *)a->data;
    const double *bd = (const double *)b->data;
    double *rd = (double *)r->data;
    for (int64_t i = 0; i < a->size; i++) {
        rd[i] = ad[i] * bd[i];
    }
    return r;
}

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_div_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    if (!mapanare_tensor_shape_eq(a, b)) return NULL;
    mapanare_tensor_t *r = tensor_clone_shape(a);
    if (!r) return NULL;
    const double *ad = (const double *)a->data;
    const double *bd = (const double *)b->data;
    double *rd = (double *)r->data;
    for (int64_t i = 0; i < a->size; i++) {
        rd[i] = ad[i] / bd[i];
    }
    return r;
}

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_matmul_f64(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b) {
    /* Only supports 2D: (M,K) @ (K,N) → (M,N) */
    if (a->ndim != 2 || b->ndim != 2) return NULL;
    int64_t m = a->shape[0], k = a->shape[1];
    int64_t k2 = b->shape[0], n = b->shape[1];
    if (k != k2) return NULL;

    int64_t out_shape[2] = { m, n };
    mapanare_tensor_t *r = mapanare_tensor_alloc(2, out_shape, sizeof(double));
    if (!r) return NULL;

    const double *ad = (const double *)a->data;
    const double *bd = (const double *)b->data;
    double *rd = (double *)r->data;

    /* i-k-j loop order for cache-friendly access — enables SIMD vectorization
     * of the inner j-loop.  With -O2/-O3 and -march=native, LLVM/GCC will
     * auto-vectorize this to SSE/AVX (x86) or NEON (ARM). */
    for (int64_t i = 0; i < m; i++) {
        for (int64_t p = 0; p < k; p++) {
            double a_ip = ad[i * k + p];
            for (int64_t j = 0; j < n; j++) {
                rd[i * n + j] += a_ip * bd[p * n + j];
            }
        }
    }

    return r;
}

/* -----------------------------------------------------------------------
 * 6. GPU Backend — Detection & Dispatch (Phase 5.2)
 * ----------------------------------------------------------------------- */

MAPANARE_EXPORT mapanare_gpu_detection_t *mapanare_detect_gpus(void) {
    mapanare_gpu_detection_t *det = (mapanare_gpu_detection_t *)calloc(
        1, sizeof(mapanare_gpu_detection_t));
    if (!det) return NULL;

    /* Maximum 16 devices across all backends */
    det->devices = (mapanare_gpu_device_t *)calloc(16, sizeof(mapanare_gpu_device_t));
    if (!det->devices) { free(det); return NULL; }
    det->device_count = 0;

    /*
     * CUDA detection — try loading nvcuda / libcuda dynamically.
     * We don't link against CUDA at compile time; instead we probe at runtime.
     */
#ifdef _WIN32
    {
        HMODULE cuda = LoadLibraryA("nvcuda.dll");
        if (cuda) {
            det->cuda_available = 1;
            /* Enumerate via nvidia-smi is done in Python wrapper;
             * here we just flag availability. */
            FreeLibrary(cuda);
        }
    }
#elif defined(__APPLE__)
    /* No CUDA on modern macOS */
    det->cuda_available = 0;
#else
    {
        void *cuda = NULL;
        /* Try dlopen if available (linked dynamically) */
        /* For portability, we just check the file system */
        FILE *f = fopen("/usr/lib/x86_64-linux-gnu/libcuda.so.1", "r");
        if (!f) f = fopen("/usr/lib/libcuda.so.1", "r");
        if (!f) f = fopen("/usr/local/cuda/lib64/libcuda.so", "r");
        if (f) {
            det->cuda_available = 1;
            fclose(f);
        }
    }
#endif

    /*
     * Metal detection — only on macOS
     */
#ifdef __APPLE__
    /* Metal is available on all modern macOS (10.11+) / iOS devices */
    det->metal_available = 1;
    if (det->device_count < 16) {
        mapanare_gpu_device_t *d = &det->devices[det->device_count++];
        d->kind = MAPANARE_DEVICE_METAL;
        snprintf(d->name, sizeof(d->name), "Apple GPU");
        d->index = 0;
    }
#else
    det->metal_available = 0;
#endif

    /*
     * Vulkan detection — check for Vulkan loader library
     */
#ifdef _WIN32
    {
        HMODULE vk = LoadLibraryA("vulkan-1.dll");
        if (vk) {
            det->vulkan_available = 1;
            FreeLibrary(vk);
        }
    }
#elif defined(__APPLE__)
    /* MoltenVK may provide Vulkan on macOS */
    {
        FILE *f = fopen("/usr/local/lib/libvulkan.dylib", "r");
        if (!f) f = fopen("/usr/local/lib/libMoltenVK.dylib", "r");
        if (f) {
            det->vulkan_available = 1;
            fclose(f);
        }
    }
#else
    {
        FILE *f = fopen("/usr/lib/x86_64-linux-gnu/libvulkan.so.1", "r");
        if (!f) f = fopen("/usr/lib/libvulkan.so.1", "r");
        if (f) {
            det->vulkan_available = 1;
            fclose(f);
        }
    }
#endif

    return det;
}

MAPANARE_EXPORT void mapanare_gpu_detection_free(mapanare_gpu_detection_t *det) {
    if (!det) return;
    free(det->devices);
    free(det);
}

/*
 * GPU dispatch functions — route tensor ops to the appropriate backend.
 * Currently all GPU paths fall back to CPU implementation since the actual
 * GPU kernel launch requires linking against CUDA/Metal/Vulkan SDKs.
 * The dispatch layer is in place for when native GPU support is compiled in.
 */

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_add_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device) {
    /* TODO: dispatch to CUDA/Metal/Vulkan kernel when compiled with GPU support */
    (void)device;
    return mapanare_tensor_add_f64(a, b);
}

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_sub_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device) {
    (void)device;
    return mapanare_tensor_sub_f64(a, b);
}

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_mul_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device) {
    (void)device;
    return mapanare_tensor_mul_f64(a, b);
}

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_div_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device) {
    (void)device;
    return mapanare_tensor_div_f64(a, b);
}

MAPANARE_EXPORT mapanare_tensor_t *mapanare_tensor_matmul_dispatch(
    const mapanare_tensor_t *a, const mapanare_tensor_t *b,
    mapanare_device_kind_t device) {
    (void)device;
    return mapanare_tensor_matmul_f64(a, b);
}

/* =======================================================================
 * 7. Graceful Shutdown — SIGTERM/SIGINT handling
 * ======================================================================= */

static mapanare_agent_registry_t *s_shutdown_registry = NULL;
static volatile sig_atomic_t s_shutdown_requested = 0;
static volatile sig_atomic_t s_shutdown_signal = 0;

#ifdef _WIN32
static BOOL WINAPI mapanare_console_handler(DWORD sig) {
    if (sig == CTRL_C_EVENT || sig == CTRL_BREAK_EVENT || sig == CTRL_CLOSE_EVENT) {
        s_shutdown_requested = 1;
        if (s_shutdown_registry) {
            mapanare_registry_stop_all(s_shutdown_registry);
        }
        return TRUE;
    }
    return FALSE;
}
#else
static void mapanare_signal_handler(int sig) {
    /*
     * Async-signal-safe: only set flags. Do NOT call mutex-protected
     * functions (mapanare_registry_stop_all) from within a signal handler.
     * The main event loop or mapanare_shutdown_requested() caller is
     * responsible for calling mapanare_shutdown_drain() to stop agents.
     */
    s_shutdown_requested = 1;
    s_shutdown_signal = sig;
}
#endif

MAPANARE_EXPORT void mapanare_shutdown_init(mapanare_agent_registry_t *reg) {
    s_shutdown_registry = reg;
    s_shutdown_requested = 0;
#ifdef _WIN32
    SetConsoleCtrlHandler(mapanare_console_handler, TRUE);
#else
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = mapanare_signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);
#endif
}

MAPANARE_EXPORT int mapanare_shutdown_requested(void) {
    if (s_shutdown_requested && s_shutdown_registry) {
        /* Drain agents safely outside the signal handler context */
        mapanare_registry_stop_all(s_shutdown_registry);
        s_shutdown_registry = NULL;  /* Only drain once */
    }
    return s_shutdown_requested;
}

MAPANARE_EXPORT void mapanare_shutdown_drain(void) {
    if (s_shutdown_requested && s_shutdown_registry) {
        mapanare_registry_stop_all(s_shutdown_registry);
        s_shutdown_registry = NULL;
    }
    /* Tear down the lazy-initialized global pool if it was created */
    mapanare_pool_destroy_global();
#ifndef _WIN32
    if (s_shutdown_signal != 0) {
        /* Re-raise with default handler so the exit code reflects the signal */
        int sig = s_shutdown_signal;
        s_shutdown_signal = 0;
        signal(sig, SIG_DFL);
        raise(sig);
    }
#endif
}

/* =======================================================================
 * 8. Trace hooks — observability for native agent operations
 * ======================================================================= */

MAPANARE_EXPORT void mapanare_trace_set_hook(mapanare_trace_hook_fn hook) {
    __atomic_store_n(&s_trace_hook, hook, __ATOMIC_RELEASE);
}

MAPANARE_EXPORT mapanare_trace_hook_fn mapanare_trace_get_hook(void) {
    return __atomic_load_n(&s_trace_hook, __ATOMIC_ACQUIRE);
}

/* =======================================================================
 * 9. Cooperative Scheduler — single-threaded agent execution for mobile
 *
 * Instead of spawning one OS thread per agent, the cooperative scheduler
 * runs all agents on the calling thread using a round-robin ready queue.
 * Each agent gets up to `max_steps` message-handling iterations per tick
 * before yielding to the next agent.
 * ======================================================================= */

MAPANARE_EXPORT void mapanare_coop_scheduler_init(mapanare_coop_scheduler_t *sched,
                                                   uint32_t capacity) {
    if (capacity == 0) capacity = MAPANARE_DEFAULT_AGENT_QUEUE;
    uint32_t cap = next_pow2(capacity);
    sched->ready_queue = (mapanare_agent_t **)calloc(cap, sizeof(mapanare_agent_t *));
    if (!sched->ready_queue) {
        sched->queue_cap = 0;
        return;
    }
    sched->queue_cap  = cap;
    sched->queue_head = 0;
    sched->queue_tail = 0;
    sched->max_steps  = 1000;
    atomic_store_i32(&sched->running, 0);
}

MAPANARE_EXPORT void mapanare_coop_scheduler_destroy(mapanare_coop_scheduler_t *sched) {
    if (sched->ready_queue) {
        free(sched->ready_queue);
        sched->ready_queue = NULL;
    }
    sched->queue_cap  = 0;
    sched->queue_head = 0;
    sched->queue_tail = 0;
}

static inline uint32_t coop_queue_size(mapanare_coop_scheduler_t *sched) {
    return sched->queue_head - sched->queue_tail;
}

MAPANARE_EXPORT int mapanare_coop_scheduler_enqueue(mapanare_coop_scheduler_t *sched,
                                                     mapanare_agent_t *agent) {
    if (coop_queue_size(sched) >= sched->queue_cap) return -1;
    uint32_t mask = sched->queue_cap - 1;
    sched->ready_queue[sched->queue_head & mask] = agent;
    sched->queue_head++;

    /* Mark agent as running (cooperative mode — no thread spawned) */
    atomic_store_i32(&agent->running, 1);
    atomic_store_i32(&agent->state, MAPANARE_AGENT_RUNNING);
    if (agent->on_init) agent->on_init(agent->agent_data);
    trace_emit(MAPANARE_TRACE_SPAWN, agent, NULL, 0);
    return 0;
}

MAPANARE_EXPORT int mapanare_coop_scheduler_step(mapanare_coop_scheduler_t *sched) {
    if (coop_queue_size(sched) == 0) return 0;

    uint32_t mask = sched->queue_cap - 1;
    mapanare_agent_t *agent = sched->ready_queue[sched->queue_tail & mask];
    sched->queue_tail++;

    /* Skip paused agents — re-enqueue them silently */
    if (atomic_load_i32(&agent->paused)) {
        if (coop_queue_size(sched) < sched->queue_cap) {
            sched->ready_queue[sched->queue_head & mask] = agent;
            sched->queue_head++;
        }
        return 1;
    }

    /* Process up to max_steps messages for this agent */
    uint32_t steps = 0;
    int agent_done = 0;
    while (steps < sched->max_steps && !agent_done) {
        void *msg = NULL;
        if (mapanare_ring_pop(&agent->inbox, &msg) != 0 || msg == NULL) {
            break;  /* No more messages — yield */
        }
        mapanare_bp_decrement(&agent->bp);

        int64_t t0 = mapanare_time_us();
        void *out_msg = NULL;
        int rc = 0;
        if (agent->handler) {
            rc = agent->handler(agent->agent_data, msg, &out_msg);
        }
        int64_t elapsed = mapanare_time_us() - t0;
        atomic_add_i64(&agent->messages_processed, 1);
        atomic_add_i64(&agent->total_latency_us, elapsed);
        trace_emit(MAPANARE_TRACE_HANDLE, agent, msg, elapsed);

        if (rc != 0) {
            trace_emit(MAPANARE_TRACE_ERROR, agent, msg, 0);
            if (agent->restart_policy == MAPANARE_RESTART_RESTART &&
                agent->restart_count < agent->max_restarts) {
                agent->restart_count++;
                continue;
            }
            /* Agent failed — don't re-enqueue */
            atomic_store_i32(&agent->state, MAPANARE_AGENT_FAILED);
            atomic_store_i32(&agent->running, 0);
            if (agent->on_stop) agent->on_stop(agent->agent_data);
            agent_done = 1;
        }

        if (out_msg != NULL) {
            mapanare_ring_push(&agent->outbox, out_msg);
        }
        steps++;
    }

    /* Re-enqueue agent if still running */
    if (!agent_done && atomic_load_i32(&agent->running)) {
        if (coop_queue_size(sched) < sched->queue_cap) {
            sched->ready_queue[sched->queue_head & mask] = agent;
            sched->queue_head++;
        }
    } else if (!agent_done) {
        /* Agent was stopped externally */
        atomic_store_i32(&agent->state, MAPANARE_AGENT_STOPPED);
        if (agent->on_stop) agent->on_stop(agent->agent_data);
    }

    return 1;
}

MAPANARE_EXPORT int mapanare_coop_scheduler_run(mapanare_coop_scheduler_t *sched) {
    atomic_store_i32(&sched->running, 1);
    while (atomic_load_i32(&sched->running) && coop_queue_size(sched) > 0) {
        if (!mapanare_coop_scheduler_step(sched)) {
            /* Queue empty — all agents finished */
            break;
        }
    }
    atomic_store_i32(&sched->running, 0);
    return 0;
}

MAPANARE_EXPORT void mapanare_coop_scheduler_stop(mapanare_coop_scheduler_t *sched) {
    atomic_store_i32(&sched->running, 0);
}

/* =======================================================================
 * 10. Memory profiling helpers
 * ======================================================================= */

MAPANARE_EXPORT void mapanare_arena_stats(const MnArena *arena,
                                           size_t *out_allocated,
                                           size_t *out_used) {
    size_t allocated = 0, used = 0;
    if (arena) {
        const MnArenaBlock *blk = arena->head;
        while (blk) {
            allocated += (size_t)blk->size;
            used      += (size_t)blk->used;
            blk = blk->next;
        }
    }
    if (out_allocated) *out_allocated = allocated;
    if (out_used)      *out_used      = used;
}

MAPANARE_EXPORT void mapanare_memory_stats(mapanare_memory_stats_t *out) {
    if (!out) return;
    memset(out, 0, sizeof(*out));

    /* Intern table stats — delegated to __mn_intern_stats in mapanare_core.c */
    extern void __mn_intern_stats(size_t *count, size_t *bytes);
    __mn_intern_stats(&out->intern_count, &out->intern_bytes);

    /* NOTE: arena_allocated/arena_used and agent_count/ring_allocated require
     * a global arena registry and agent registry respectively. Currently only
     * intern stats are available; add arena/agent aggregation when a global
     * registry is introduced. */
}
