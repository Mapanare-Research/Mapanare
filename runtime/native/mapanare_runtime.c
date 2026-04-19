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
#include <errno.h>

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
__attribute__((unused))
static inline int32_t atomic_add_i32(mapanare_atomic_i32 *p, int32_t v) {
    return __atomic_fetch_add(p, v, __ATOMIC_ACQ_REL);
}
static inline int32_t atomic_exchange_i32(mapanare_atomic_i32 *p, int32_t v) {
    return __atomic_exchange_n(p, v, __ATOMIC_ACQ_REL);
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
    static LARGE_INTEGER freq = {0};
    LARGE_INTEGER now;
    if (!freq.QuadPart) QueryPerformanceFrequency(&freq);
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
    atomic_store_i32(&agent->needs_join, 0);
    atomic_store_i64(&agent->messages_processed, 0);
    atomic_store_i64(&agent->total_latency_us, 0);

    if (inbox_cap == 0) inbox_cap = MAPANARE_DEFAULT_AGENT_QUEUE;
    if (outbox_cap == 0) outbox_cap = MAPANARE_DEFAULT_AGENT_QUEUE;

    if (mapanare_ring_create(&agent->inbox, inbox_cap) != 0) return -1;
    if (mapanare_ring_create(&agent->outbox, outbox_cap) != 0) {
        mapanare_ring_destroy(&agent->inbox);
        return -1;
    }

    /* v4.28.0: serialize the producer side of the inbox so concurrent
     * ``mapanare_agent_send`` calls do not race on ``head`` / slot writes. */
    mapanare_mutex_init(&agent->inbox_producer_lock);

    mapanare_bp_init(&agent->bp, (int64_t)agent->inbox.capacity);

    mapanare_sem_init(&agent->inbox_ready, 0);
    mapanare_sem_init(&agent->outbox_ready, 0);

    /* v4.78.0 (CARRY_FORWARD #50): default message_dtor to free() so
     * in-flight messages are freed on agent destroy.  Previously
     * message_dtor was NULL after memset, so the drain loop in
     * mapanare_agent_destroy silently leaked every unconsumed payload.
     * Agents needing custom destructors can override after init. */
    agent->message_dtor = free;

    return 0;
}

MAPANARE_EXPORT int mapanare_agent_spawn(mapanare_agent_t *agent) {
    /* Ensure the global thread pool is initialized on first agent spawn */
    mapanare_ensure_pool();

    atomic_store_i32(&agent->running, 1);
    int rc = mapanare_thread_create(&agent->thread, agent_thread_fn, agent);
    if (rc == 0) {
        /* v4.137.0 (Ch.1): mark join as owed after successful thread
         * create. Ordering: set AFTER create so a failed spawn leaves
         * needs_join=0 and destroy() won't try to join an unstarted
         * thread. */
        atomic_store_i32(&agent->needs_join, 1);
        trace_emit(MAPANARE_TRACE_SPAWN, agent, NULL, 0);
    } else {
        atomic_store_i32(&agent->running, 0);
    }
    return rc;
}

MAPANARE_EXPORT int mapanare_agent_send(mapanare_agent_t *agent, void *msg) {
    /* v4.28.0: take the producer lock so concurrent sends serialize on
     * the MPSC side of the ring (the ring itself is still lock-free on
     * the consumer side, which remains single-threaded). */
    mapanare_mutex_lock(&agent->inbox_producer_lock);
    /* v4.150.0 (E6-A): snapshot ring emptiness before push. If the ring
     * was non-empty, the worker is either dispatching or about to loop
     * back to ring_pop — it will find our new item without a wake.
     * Only post the semaphore when the ring was empty, meaning the
     * worker is (or is about to be) parked in sem_wait. Safe because:
     * (1) single-consumer ring — worker always retries ring_pop after
     * dispatch before sem_wait, so it can't miss a pushed item;
     * (2) spurious wakes are harmless — worker re-checks ring_pop. */
    int was_empty = mapanare_ring_is_empty(&agent->inbox);
    int rc = mapanare_ring_push(&agent->inbox, msg);
    mapanare_mutex_unlock(&agent->inbox_producer_lock);
    if (rc == 0) {
        mapanare_bp_increment(&agent->bp);
        if (was_empty) {
            mapanare_sem_post(&agent->inbox_ready);
        }
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
    /* v4.137.0 (Ch.1): only the caller that transitions needs_join
     * from 1 → 0 performs the join. Makes stop() + destroy() safe to
     * call in either order without double-joining. */
    if (atomic_exchange_i32(&agent->needs_join, 0) == 1) {
        mapanare_thread_join(agent->thread);
    }
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
    if (!agent) return;
    /* v4.137.0 (Ch.1): quiesce the worker thread BEFORE freeing any
     * resources it may still be touching. Prior to this, destroy()
     * drained and freed the rings/semaphores while the worker could
     * still be blocked in sem_wait or mid-loop — a UAF that TSan
     * flagged ~100% and ASan flagged intermittently. The atomic
     * exchange on needs_join ensures we join exactly once whether
     * stop() was called earlier or not. */
    atomic_store_i32(&agent->running, 0);
    atomic_store_i32(&agent->paused, 0);
    mapanare_sem_post(&agent->inbox_ready);
    mapanare_sem_post(&agent->outbox_ready);
    if (atomic_exchange_i32(&agent->needs_join, 0) == 1) {
        mapanare_thread_join(agent->thread);
    }
    /* v4.33.0 Phase 4.3 (Viper M5, 2nd cycle): drain inbox/outbox and
     * free remaining messages IF a destructor was provided. If
     * message_dtor is NULL, messages are discarded without freeing
     * (backwards-compatible — caller owns lifetime). */
    void *msg = NULL;
    while (mapanare_ring_pop(&agent->inbox, &msg) == 0) {
        if (agent->message_dtor && msg) agent->message_dtor(msg);
    }
    while (mapanare_ring_pop(&agent->outbox, &msg) == 0) {
        if (agent->message_dtor && msg) agent->message_dtor(msg);
    }
    mapanare_ring_destroy(&agent->inbox);
    mapanare_ring_destroy(&agent->outbox);
    /* v4.28.0: destroy the MPSC producer lock added in agent_init. */
    mapanare_mutex_destroy(&agent->inbox_producer_lock);
    mapanare_sem_destroy(&agent->inbox_ready);
    mapanare_sem_destroy(&agent->outbox_ready);
    /* Note: caller is responsible for freeing the agent struct if heap-allocated.
     * The emitter calls free(agent) after destroy for agents created with
     * mapanare_agent_new(). Stack-allocated agents (via init) must not be freed. */
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
    if (!reg) return;
    /* Clear agent pointers (caller owns agent lifetime). */
    for (uint32_t i = 0; i < reg->count; i++) {
        reg->agents[i] = NULL;
    }
    reg->count = 0;
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
        s_shutdown_signal = (sig_atomic_t)sig;
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

/* =======================================================================
 * Multi-threaded work-stealing coroutine scheduler (v4.93.0)
 *
 * Replaces the v4.92.0 single-threaded scheduler. N worker threads,
 * each with a Chase-Lev work-stealing deque. When a thread has no
 * local work it steals from a random peer. Global overflow queue
 * catches tasks when a local deque is full.
 *
 * API preserves the __mn_coro_scheduler_* symbols for backward compat.
 * N=1 behaves identically to the v4.92.0 single-threaded scheduler.
 * ======================================================================= */

/* Chase-Lev work-stealing deque (bounded, power-of-2 size).
 * Owner pushes/pops from bottom, stealers CAS from top.            */
#define MN_DEQUE_CAP 1024  /* slots per worker, must be power of 2 */

typedef struct {
    void *handle;           /* coroutine handle (ptr from coro.begin)    */
    void *awaited_future;   /* Future* being awaited, or NULL            */
} mn_task_t;

typedef struct {
    mn_task_t        slots[MN_DEQUE_CAP];
    mapanare_atomic_i64 bottom;  /* owner index (push/pop) */
    mapanare_atomic_i64 top;     /* stealer index          */
} mn_ws_deque_t;

static void mn_deque_init(mn_ws_deque_t *d) {
    memset(d->slots, 0, sizeof(d->slots));
    __atomic_store_n(&d->bottom, 0, __ATOMIC_RELAXED);
    __atomic_store_n(&d->top, 0, __ATOMIC_RELAXED);
}

/* Push task (owner only). Returns 0 on success, -1 if full. */
static int mn_deque_push(mn_ws_deque_t *d, mn_task_t task) {
    int64_t b = __atomic_load_n(&d->bottom, __ATOMIC_RELAXED);
    int64_t t = __atomic_load_n(&d->top, __ATOMIC_ACQUIRE);
    if (b - t >= MN_DEQUE_CAP) return -1; /* full */
    d->slots[b & (MN_DEQUE_CAP - 1)] = task;
    __atomic_thread_fence(__ATOMIC_RELEASE);
    __atomic_store_n(&d->bottom, b + 1, __ATOMIC_RELAXED);
    return 0;
}

/* Pop task (owner only). Returns 1 if got a task, 0 if empty. */
static int mn_deque_pop(mn_ws_deque_t *d, mn_task_t *out) {
    int64_t b = __atomic_load_n(&d->bottom, __ATOMIC_RELAXED) - 1;
    __atomic_store_n(&d->bottom, b, __ATOMIC_RELAXED);
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
    int64_t t = __atomic_load_n(&d->top, __ATOMIC_RELAXED);
    if (t <= b) {
        *out = d->slots[b & (MN_DEQUE_CAP - 1)];
        if (t == b) {
            /* Last element — race with stealers. */
            if (!__atomic_compare_exchange_n(&d->top, &t, t + 1,
                    /*weak=*/0, __ATOMIC_SEQ_CST, __ATOMIC_RELAXED)) {
                /* Lost race — deque is empty. */
                __atomic_store_n(&d->bottom, t + 1, __ATOMIC_RELAXED);
                return 0;
            }
            __atomic_store_n(&d->bottom, t + 1, __ATOMIC_RELAXED);
        }
        return 1;
    }
    /* Empty. */
    __atomic_store_n(&d->bottom, t, __ATOMIC_RELAXED);
    return 0;
}

/* Steal task (any thread). Returns 1 if got a task, 0 if empty. */
static int mn_deque_steal(mn_ws_deque_t *d, mn_task_t *out) {
    int64_t t = __atomic_load_n(&d->top, __ATOMIC_ACQUIRE);
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
    int64_t b = __atomic_load_n(&d->bottom, __ATOMIC_ACQUIRE);
    if (t >= b) return 0; /* empty */
    *out = d->slots[t & (MN_DEQUE_CAP - 1)];
    if (!__atomic_compare_exchange_n(&d->top, &t, t + 1,
            /*weak=*/0, __ATOMIC_SEQ_CST, __ATOMIC_RELAXED)) {
        return 0; /* lost race */
    }
    return 1;
}

/* Global overflow queue (mutex-protected, for when local deque is full). */
#define MN_OVERFLOW_CAP 4096

typedef struct {
    mn_task_t slots[MN_OVERFLOW_CAP];
    uint32_t  head;
    uint32_t  count;
    pthread_mutex_t lock;
} mn_overflow_queue_t;

static void mn_overflow_init(mn_overflow_queue_t *q) {
    memset(q->slots, 0, sizeof(q->slots));
    q->head = 0;
    q->count = 0;
    pthread_mutex_init(&q->lock, NULL);
}

static int mn_overflow_push(mn_overflow_queue_t *q, mn_task_t task) {
    pthread_mutex_lock(&q->lock);
    if (q->count >= MN_OVERFLOW_CAP) {
        pthread_mutex_unlock(&q->lock);
        return -1;
    }
    uint32_t idx = (q->head + q->count) % MN_OVERFLOW_CAP;
    q->slots[idx] = task;
    q->count++;
    pthread_mutex_unlock(&q->lock);
    return 0;
}

static int mn_overflow_pop(mn_overflow_queue_t *q, mn_task_t *out) {
    pthread_mutex_lock(&q->lock);
    if (q->count == 0) {
        pthread_mutex_unlock(&q->lock);
        return 0;
    }
    *out = q->slots[q->head];
    q->head = (q->head + 1) % MN_OVERFLOW_CAP;
    q->count--;
    pthread_mutex_unlock(&q->lock);
    return 1;
}

static void mn_overflow_destroy(mn_overflow_queue_t *q) {
    pthread_mutex_destroy(&q->lock);
}

/* Check if a Future is Ready (state byte at offset 0 == 1). */
static inline int mn_future_is_ready(void *future_ptr) {
    if (!future_ptr) return 1; /* NULL future = ready (no await) */
    return __atomic_load_n((uint8_t *)future_ptr, __ATOMIC_ACQUIRE) == 1;
}

/* ── LLVM coroutine frame ABI (switched-resume lowering) ──
 *
 * v4.113.0 (docket #8): replaces the prior pattern of casting the
 * coroutine handle directly to `void **` and indexing by hand. The
 * LLVM switched-resume coroutine ABI places two function pointers at
 * the head of every coroutine frame:
 *
 *   offset 0 = resume_fn  (NULL-nulled by the coroutine splitter on
 *                          final suspend — this is what
 *                          `llvm.coro.done(handle)` lowers to)
 *   offset 8 = destroy_fn (still valid after final suspend; used by
 *                          `llvm.coro.destroy`)
 *
 * Both slots are pointer-sized and follow the host ABI's pointer
 * alignment. Everything after this prefix is opaque user state laid
 * out by the coroutine splitter — we must never peek into it from C.
 *
 * By expressing the prefix as a named struct we get:
 *   - one compile-time-checked place to update if the ABI ever moves
 *   - self-documenting field access (`frame->resume_fn` reads better
 *     than `*(void **)handle`)
 *   - a single definition grep-able by reviewers — no magic offsets,
 *     no hand-rolled casts scattered through the scheduler. */
typedef struct mn_coro_frame_prefix {
    void (*resume_fn)(void *handle);   /* NULL ⇒ coroutine completed */
    void (*destroy_fn)(void *handle);  /* frees the coroutine frame  */
} mn_coro_frame_prefix_t;

/* Check if a coroutine has reached its final suspend. Equivalent to
 * `llvm.coro.done(handle)` in the LLVM switched-resume lowering: the
 * splitter nulls the resume_fn slot when the coroutine returns. */
static inline int mn_coro_is_done(void *handle) {
    const mn_coro_frame_prefix_t *frame = (const mn_coro_frame_prefix_t *)handle;
    return frame->resume_fn == NULL;
}

/* Resume a suspended coroutine by calling its LLVM-emitted resume_fn. */
static inline void mn_coro_resume(void *handle) {
    mn_coro_frame_prefix_t *frame = (mn_coro_frame_prefix_t *)handle;
    frame->resume_fn(handle);
}

/* ── Multi-threaded scheduler ── */

#define MN_MAX_WORKERS 64

typedef struct mn_mt_scheduler {
    mn_ws_deque_t      deques[MN_MAX_WORKERS];   /* per-worker deques         */
    pthread_t          threads[MN_MAX_WORKERS];   /* worker thread handles     */
    uint32_t           num_workers;               /* N (1 = single-threaded)   */
    mn_overflow_queue_t overflow;                  /* global overflow queue     */
    mapanare_atomic_i32 active_tasks;             /* total tasks in system     */
    mapanare_atomic_i32 running;                  /* 1 = active, 0 = shutdown  */
    pthread_mutex_t    wake_lock;                 /* protects condvar          */
    pthread_cond_t     wake_cond;                 /* wake parked workers       */
    pthread_mutex_t    done_lock;                 /* protects done condvar     */
    pthread_cond_t     done_cond;                 /* signal block_on caller    */
} mn_mt_scheduler_t;

static mn_mt_scheduler_t mn_sched;

/* Try to get a task: local pop, then overflow, then steal from peers. */
static int mn_worker_get_task(uint32_t worker_id, mn_task_t *out) {
    /* 1. Pop from own deque. */
    if (mn_deque_pop(&mn_sched.deques[worker_id], out))
        return 1;
    /* 2. Pop from global overflow. */
    if (mn_overflow_pop(&mn_sched.overflow, out))
        return 1;
    /* 3. Steal from random peer. */
    uint32_t n = mn_sched.num_workers;
    if (n <= 1) return 0;
    /* Simple linear scan starting from random offset. */
    uint32_t start = (worker_id + 1) % n;
    for (uint32_t i = 0; i < n - 1; i++) {
        uint32_t victim = (start + i) % n;
        if (mn_deque_steal(&mn_sched.deques[victim], out))
            return 1;
    }
    return 0;
}

/* Process a single task: check readiness, resume, detect completion. */
static void mn_process_task(mn_task_t *task, uint32_t worker_id) {
    /* If awaiting a future that isn't ready, re-enqueue. */
    if (task->awaited_future && !mn_future_is_ready(task->awaited_future)) {
        mn_deque_push(&mn_sched.deques[worker_id], *task);
        return;
    }

    /* Resume the coroutine. */
    mn_coro_resume(task->handle);

    /* If the awaited future is now ready, clear the wait. */
    if (task->awaited_future && mn_future_is_ready(task->awaited_future)) {
        task->awaited_future = NULL;
    }

    /* Check if coroutine completed. */
    if (mn_coro_is_done(task->handle)) {
        __atomic_fetch_sub(&mn_sched.active_tasks, 1, __ATOMIC_ACQ_REL);
        /* Signal block_on waiters. */
        pthread_mutex_lock(&mn_sched.done_lock);
        pthread_cond_broadcast(&mn_sched.done_cond);
        pthread_mutex_unlock(&mn_sched.done_lock);
    } else {
        /* Coroutine suspended again — re-enqueue. */
        if (mn_deque_push(&mn_sched.deques[worker_id], *task) != 0) {
            mn_overflow_push(&mn_sched.overflow, *task);
        }
    }
}

static void *mn_worker_loop(void *arg) {
    uint32_t worker_id = (uint32_t)(uintptr_t)arg;
    uint32_t idle_spins = 0;

    while (__atomic_load_n(&mn_sched.running, __ATOMIC_ACQUIRE)) {
        mn_task_t task;
        if (mn_worker_get_task(worker_id, &task)) {
            mn_process_task(&task, worker_id);
            idle_spins = 0;
        } else {
            /* No work available. */
            if (__atomic_load_n(&mn_sched.active_tasks, __ATOMIC_ACQUIRE) == 0) {
                break; /* All tasks complete. */
            }
            idle_spins++;
            if (idle_spins > 64) {
                /* Park via condvar (no busy-wait). */
                pthread_mutex_lock(&mn_sched.wake_lock);
                /* Double-check under lock. */
                if (__atomic_load_n(&mn_sched.running, __ATOMIC_ACQUIRE) &&
                    __atomic_load_n(&mn_sched.active_tasks, __ATOMIC_ACQUIRE) > 0) {
                    struct timespec ts;
                    clock_gettime(CLOCK_REALTIME, &ts);
                    ts.tv_nsec += 1000000; /* 1ms timeout to re-check */
                    if (ts.tv_nsec >= 1000000000) {
                        ts.tv_sec++;
                        ts.tv_nsec -= 1000000000;
                    }
                    pthread_cond_timedwait(&mn_sched.wake_cond,
                                           &mn_sched.wake_lock, &ts);
                }
                pthread_mutex_unlock(&mn_sched.wake_lock);
                idle_spins = 0;
            }
        }
    }
    return NULL;
}

/* ── Public API (same symbols as v4.92.0) ── */

MN_EXPORT void __mn_coro_scheduler_init(uint32_t num_threads) {
    memset(&mn_sched, 0, sizeof(mn_sched));
    uint32_t n = num_threads;
    if (n == 0) {
        /* v4.150.0 (E6): honour MAPANARE_ASYNC_THREADS env var. On
         * high-core-count machines (32+ cores) the default of spawning
         * one thread per core adds significant startup cost (~2 ms for
         * 31 pthread_create calls) that dominates short-lived async
         * programs. The env var lets users and benchmarks cap the pool
         * without recompilation. */
        const char *env = getenv("MAPANARE_ASYNC_THREADS");
        if (env && env[0]) {
            int v = atoi(env);
            if (v > 0) n = (uint32_t)v;
        }
        if (n == 0) n = (uint32_t)mapanare_cpu_count();
    }
    if (n > MN_MAX_WORKERS) n = MN_MAX_WORKERS;
    mn_sched.num_workers = n;
    __atomic_store_n(&mn_sched.running, 1, __ATOMIC_RELEASE);
    __atomic_store_n(&mn_sched.active_tasks, 0, __ATOMIC_RELEASE);
    pthread_mutex_init(&mn_sched.wake_lock, NULL);
    pthread_cond_init(&mn_sched.wake_cond, NULL);
    pthread_mutex_init(&mn_sched.done_lock, NULL);
    pthread_cond_init(&mn_sched.done_cond, NULL);
    mn_overflow_init(&mn_sched.overflow);
    for (uint32_t i = 0; i < n; i++) {
        mn_deque_init(&mn_sched.deques[i]);
    }
    /* Start worker threads (skip thread 0 — the caller thread acts as worker 0
     * during block_on, which avoids deadlock when block_on is called from main).
     *
     * v4.113.0 (docket #11): pthread_create can fail with EAGAIN when the
     * per-user thread limit is exceeded, or ENOMEM / EPERM in rarer cases.
     * Prior to v4.113.0 the return value was silently dropped — the
     * scheduler would report `num_workers = N` while having only
     * `num_workers - k` live threads, making every task-steal look idle
     * and stalling the whole program. Bail with a specific message that
     * names what failed (thread N of M) and why (strerror on the real
     * errno), so `RLIMIT_NPROC` exhaustion doesn't masquerade as a
     * generic hang. */
    for (uint32_t i = 1; i < n; i++) {
        int rc = pthread_create(&mn_sched.threads[i], NULL, mn_worker_loop,
                                (void *)(uintptr_t)i);
        if (rc != 0) {
            fprintf(stderr,
                    "mapanare: async runtime: failed to spawn worker thread "
                    "%u of %u: %s (errno %d). Likely causes: "
                    "RLIMIT_NPROC exhausted, or ENOMEM at pthread stack "
                    "allocation. Try lowering MAPANARE_ASYNC_THREADS or "
                    "raising `ulimit -u`.\n",
                    i, n, strerror(rc), rc);
            exit(1);
        }
    }
}

MN_EXPORT void __mn_coro_scheduler_register(void *handle) {
    /* v4.113.0 (docket #11): refuse to enqueue a coroutine before
     * __mn_coro_scheduler_init has run. Pre-v4.113.0 the scheduler
     * would silently push into a zero-initialised deque (num_workers=0)
     * and __mn_coro_scheduler_run would spin forever waiting for
     * active_tasks to drain. Emit a specific message naming the
     * missing call so the user knows which init to add. */
    if (mn_sched.num_workers == 0) {
        fprintf(stderr,
                "mapanare: async runtime: cannot spawn task — scheduler "
                "not initialised. The main() emitted by the compiler "
                "should call __mn_coro_scheduler_init() before any "
                "async function runs; if this message appeared, the "
                "emitter (mapanare/emit_llvm_text.py) dropped that "
                "call for the current entry point.\n");
        exit(1);
    }
    mn_task_t task = { .handle = handle, .awaited_future = NULL };
    __atomic_fetch_add(&mn_sched.active_tasks, 1, __ATOMIC_ACQ_REL);
    /* Push to worker 0's deque (caller is main thread = worker 0).
     *
     * v4.113.0 (docket #11): both the per-worker deque and the global
     * overflow queue are bounded; if both are full the task must not
     * be silently dropped (previously we did, and the scheduler would
     * deadlock waiting on a task the scheduler never actually held).
     * Undo the active_tasks bump, name which queue refused the push,
     * and bail. This path is rare but when it triggers silent drop
     * was spectacularly hard to diagnose. */
    if (mn_deque_push(&mn_sched.deques[0], task) != 0) {
        if (mn_overflow_push(&mn_sched.overflow, task) != 0) {
            __atomic_fetch_sub(&mn_sched.active_tasks, 1, __ATOMIC_ACQ_REL);
            fprintf(stderr,
                    "mapanare: async runtime: failed to spawn task — both "
                    "worker-0 deque (cap=%u) and global overflow queue "
                    "(cap=%u) are full. Too many concurrent spawn() calls "
                    "without await points; the scheduler cannot drain. "
                    "Rewrite to spawn in batches or add an await.\n",
                    (unsigned)MN_DEQUE_CAP, (unsigned)MN_OVERFLOW_CAP);
            exit(1);
        }
    }
    /* Wake a parked worker. */
    pthread_mutex_lock(&mn_sched.wake_lock);
    pthread_cond_signal(&mn_sched.wake_cond);
    pthread_mutex_unlock(&mn_sched.wake_lock);
}

MN_EXPORT void __mn_coro_register_wait(void *handle, void *future_ptr) {
    /* The coroutine is about to suspend. We need to associate the future
     * with it so the scheduler knows when to resume. Since the coroutine
     * is mid-execution on the current worker, we create a task entry
     * that will be picked up on the next scheduling round. */
    mn_task_t task = { .handle = handle, .awaited_future = future_ptr };
    /* Push to worker 0's deque. In the multi-threaded model, the actual
     * worker ID should be passed, but for simplicity we use the overflow
     * queue which any worker can drain.
     *
     * v4.113.0 (docket #11): same silent-drop concern as
     * __mn_coro_scheduler_register, but this one is worse — the
     * coroutine is SUSPENDED waiting for a future that will never be
     * resumed. Report the awaited future's address and bail so the
     * user sees a specific "await lost its resumer" failure instead
     * of a hang. */
    if (mn_overflow_push(&mn_sched.overflow, task) != 0) {
        fprintf(stderr,
                "mapanare: async runtime: cannot register await — global "
                "overflow queue (cap=%u) is full. Coroutine at %p is "
                "awaiting Future at %p; without a resumer slot it will "
                "never wake. Rewrite to limit concurrent awaits.\n",
                (unsigned)MN_OVERFLOW_CAP, handle, future_ptr);
        exit(1);
    }
    /* Wake a worker to check the newly-enqueued wait. */
    pthread_mutex_lock(&mn_sched.wake_lock);
    pthread_cond_signal(&mn_sched.wake_cond);
    pthread_mutex_unlock(&mn_sched.wake_lock);
}

MN_EXPORT void __mn_coro_scheduler_run(void) {
    /* The calling thread (main/worker 0) participates as a worker while
     * waiting for all tasks to complete. This avoids deadlock. */
    uint32_t idle_spins = 0;
    while (__atomic_load_n(&mn_sched.active_tasks, __ATOMIC_ACQUIRE) > 0) {
        mn_task_t task;
        if (mn_worker_get_task(0, &task)) {
            mn_process_task(&task, 0);
            idle_spins = 0;
        } else {
            idle_spins++;
            if (idle_spins > 100) {
                /* Wait for a task to complete. */
                pthread_mutex_lock(&mn_sched.done_lock);
                if (__atomic_load_n(&mn_sched.active_tasks, __ATOMIC_ACQUIRE) > 0) {
                    struct timespec ts;
                    clock_gettime(CLOCK_REALTIME, &ts);
                    ts.tv_nsec += 1000000; /* 1ms */
                    if (ts.tv_nsec >= 1000000000) {
                        ts.tv_sec++;
                        ts.tv_nsec -= 1000000000;
                    }
                    pthread_cond_timedwait(&mn_sched.done_cond,
                                           &mn_sched.done_lock, &ts);
                }
                pthread_mutex_unlock(&mn_sched.done_lock);
                idle_spins = 0;
            }
        }
    }
}

MN_EXPORT void __mn_coro_scheduler_destroy(void) {
    __atomic_store_n(&mn_sched.running, 0, __ATOMIC_RELEASE);
    /* Wake all workers so they see the shutdown flag. */
    pthread_mutex_lock(&mn_sched.wake_lock);
    pthread_cond_broadcast(&mn_sched.wake_cond);
    pthread_mutex_unlock(&mn_sched.wake_lock);
    /* Join worker threads (skip 0 — that's the caller). */
    for (uint32_t i = 1; i < mn_sched.num_workers; i++) {
        pthread_join(mn_sched.threads[i], NULL);
    }
    pthread_mutex_destroy(&mn_sched.wake_lock);
    pthread_cond_destroy(&mn_sched.wake_cond);
    pthread_mutex_destroy(&mn_sched.done_lock);
    pthread_cond_destroy(&mn_sched.done_cond);
    mn_overflow_destroy(&mn_sched.overflow);
}

/* v4.93.0: spawn() — enqueue a coroutine for multi-threaded execution. */
MN_EXPORT void __mn_coro_spawn(void *handle) {
    __mn_coro_scheduler_register(handle);
}

/* -----------------------------------------------------------------------
 * Async file I/O (v4.92.0)
 *
 * mapanare_file_read_async(): spawns a thread to read a file, returns
 * a Future<String> immediately. The thread reads the file synchronously
 * and sets the future to Ready when done.
 * ----------------------------------------------------------------------- */

typedef struct {
    void    *future;    /* Future {i8, ptr} — shared with caller  */
    MnString path;      /* File path to read                       */
} mn_async_read_ctx_t;

static void *mn_async_file_read_thread(void *arg) {
    mn_async_read_ctx_t *ctx = (mn_async_read_ctx_t *)arg;

    /* Read the file synchronously. */
    int64_t ok = 0;
    extern MnString __mn_file_read(MnString path, int64_t *ok);
    MnString content = __mn_file_read(ctx->path, &ok);

    /* Allocate result box (i64-sized for uniform extraction). */
    void *box = malloc(sizeof(MnString));
    *(MnString *)box = content;

    /* Store into future: payload = box, then state = Ready.
     * The store order matters: payload first, then state,
     * with a release fence so the scheduler sees both. */
    void **payload_slot = (void **)((uint8_t *)ctx->future + sizeof(uint8_t));
    /* On 64-bit, the {i8, ptr} layout may have padding.
     * Match the LLVM GEP: field 1 is at offset 8 (i8 + 7 padding). */
    payload_slot = (void **)((uint8_t *)ctx->future + 8);
    *payload_slot = box;
    __atomic_store_n((uint8_t *)ctx->future, 1, __ATOMIC_RELEASE);

    free(ctx);
    return NULL;
}

MN_EXPORT void *__mn_file_read_async(MnString path) {
    /* Allocate a Future {i8 state, ptr payload}.
     *
     * v4.113.0 (docket #11): calloc / malloc / pthread_create all
     * check on the happy path; each failure mode gets a specific
     * message naming WHAT we were trying to allocate (Future vs.
     * context) and which errno came back. Previously a failure here
     * produced either a SIGSEGV (from dereferencing NULL future /
     * ctx) or a silent hang (detached thread never started, Future
     * state byte never set to Ready). */
    void *future = calloc(1, 16);  /* 16 bytes = {i8, padding[7], ptr} */
    if (!future) {
        fprintf(stderr,
                "mapanare: async runtime: cannot start file_read_async "
                "— out of memory allocating Future (16 bytes).\n");
        exit(1);
    }

    mn_async_read_ctx_t *ctx = (mn_async_read_ctx_t *)malloc(sizeof(*ctx));
    if (!ctx) {
        free(future);
        fprintf(stderr,
                "mapanare: async runtime: cannot start file_read_async "
                "— out of memory allocating reader context (%zu bytes).\n",
                sizeof(*ctx));
        exit(1);
    }
    ctx->future = future;
    ctx->path = path;

    pthread_t thread;
    int rc = pthread_create(&thread, NULL, mn_async_file_read_thread, ctx);
    if (rc != 0) {
        free(ctx);
        free(future);
        fprintf(stderr,
                "mapanare: async runtime: failed to spawn file-read "
                "thread: %s (errno %d). The Future would never resolve; "
                "aborting rather than hanging the caller.\n",
                strerror(rc), rc);
        exit(1);
    }
    pthread_detach(thread);

    return future;
}

/* -----------------------------------------------------------------------
 * v4.105.0 Phase 4 — crash breadcrumbs (async-signal-safe)
 *
 * The compiler driver sets a thread-local "current source" pointer as it
 * descends through the compile pipeline. On SIGSEGV/SIGABRT/SIGBUS, the
 * signal handler prints this pointer alongside the signal number using
 * only async-signal-safe primitives (write(2), hand-rolled int format,
 * backtrace_symbols_fd which is explicitly AS-safe).
 *
 * Why this exists: v4.105.0 Phase 3's TSan run showed the previous
 * crash_handler (mnc_main.c:23-34 pre-v4.105.0) called fprintf() and
 * backtrace() which triggers malloc via ld.so — UB inside a signal.
 * ----------------------------------------------------------------------- */

#ifndef _WIN32
#include <execinfo.h>

/* Thread-local breadcrumb: last-observed source location.
 * Both fields are set by __mn_set_current_source; the handler reads them. */
static __thread const char *mn_current_file  = NULL;
static __thread int32_t     mn_current_line  = 0;
static __thread const char *mn_current_phase = NULL;  /* e.g., "parse", "lower", "emit" */

/* Set file:line breadcrumb. The compiler driver calls this as it
 * opens a file or enters a function. Must be inlined-free and cheap. */
MN_EXPORT void __mn_set_current_source(const char *filename, int32_t line) {
    mn_current_file = filename;
    mn_current_line = line;
}

MN_EXPORT void __mn_set_current_phase(const char *phase) {
    mn_current_phase = phase;
}

/* AS-safe unsigned decimal print. Writes to fd 2. */
static void mn_as_write_uint(int fd, uint64_t v) {
    char buf[24];
    int i = 23;
    buf[i--] = 0;
    if (v == 0) { buf[i--] = '0'; }
    while (v > 0) { buf[i--] = (char)('0' + (v % 10)); v /= 10; }
    (void)!write(fd, buf + i + 1, 23 - i - 1);
}

/* AS-safe signed decimal print. */
static void mn_as_write_int(int fd, int64_t v) {
    if (v < 0) { (void)!write(fd, "-", 1); v = -v; }
    mn_as_write_uint(fd, (uint64_t)v);
}

static void mn_as_write_cstr(int fd, const char *s) {
    if (!s) return;
    size_t n = 0;
    while (s[n] && n < 4096) n++;
    (void)!write(fd, s, n);
}

static void mn_as_write_sig_name(int fd, int sig) {
    const char *n = NULL;
    switch (sig) {
        case SIGSEGV: n = "SIGSEGV"; break;
        case SIGABRT: n = "SIGABRT"; break;
        case SIGBUS:  n = "SIGBUS";  break;
        case SIGFPE:  n = "SIGFPE";  break;
        case SIGILL:  n = "SIGILL";  break;
        case SIGPIPE: n = "SIGPIPE"; break;
        default: break;
    }
    if (n) mn_as_write_cstr(fd, n);
    else { mn_as_write_cstr(fd, "signal "); mn_as_write_int(fd, sig); }
}

/* The signal handler. Async-signal-safe: no malloc, no stdio, no locks. */
static void mn_crashdiag_handler(int sig) {
    const int fd = 2;  /* stderr */

    (void)!write(fd, "\n[CRASH] ", 9);
    mn_as_write_sig_name(fd, sig);

    if (mn_current_phase) {
        (void)!write(fd, " during ", 8);
        mn_as_write_cstr(fd, mn_current_phase);
    }
    if (mn_current_file) {
        (void)!write(fd, " at ", 4);
        mn_as_write_cstr(fd, mn_current_file);
        if (mn_current_line > 0) {
            (void)!write(fd, ":", 1);
            mn_as_write_int(fd, mn_current_line);
        }
    }
    (void)!write(fd, "\n", 1);

    /* backtrace_symbols_fd is explicitly listed in signal-safety(7) as
     * async-signal-safe. backtrace() itself triggers a lazy ld.so load
     * on first invocation; that *is* unsafe but only the first time.
     * Accept this trade-off: the alternative is no backtrace at all. */
    void *frames[32];
    int n = backtrace(frames, 32);
    backtrace_symbols_fd(frames, n, fd);
    (void)!write(fd, "\n", 1);

    _exit(128 + sig);
}

/* Install the handler on SIGSEGV/SIGABRT/SIGBUS/SIGFPE/SIGILL.
 * Uses sigaction (not signal) for portable semantics.
 * Called once from mnc_main.c before any compiler work. */
MN_EXPORT void __mn_install_crash_handler(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = mn_crashdiag_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESETHAND;  /* let a second crash abort cleanly */
    sigaction(SIGSEGV, &sa, NULL);
    sigaction(SIGABRT, &sa, NULL);
    sigaction(SIGBUS,  &sa, NULL);
    sigaction(SIGFPE,  &sa, NULL);
    sigaction(SIGILL,  &sa, NULL);
}

#else  /* _WIN32 */
MN_EXPORT void __mn_set_current_source(const char *filename, int32_t line) {
    (void)filename; (void)line;
}
MN_EXPORT void __mn_set_current_phase(const char *phase) { (void)phase; }
MN_EXPORT void __mn_install_crash_handler(void) { }
#endif
