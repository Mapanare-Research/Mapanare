/**
 * test_c_runtime.c — Standalone C test program for Mapanare native runtime.
 *
 * Tests:
 *   1. Ring buffer stress (rapid push/pop, fill/drain cycles)
 *   2. Thread pool saturation (submit more work than threads)
 *   3. Arena allocator stress
 *   4. String operations
 *   5. List operations
 *   6. Backpressure under load
 *   7. Agent lifecycle
 *
 * Compile:
 *   gcc -O2 -pthread test_c_runtime.c ../../runtime/native/mapanare_core.c \
 *       ../../runtime/native/mapanare_runtime.c -o test_c_runtime
 *
 * With AddressSanitizer:
 *   gcc -fsanitize=address -g -pthread test_c_runtime.c \
 *       ../../runtime/native/mapanare_core.c \
 *       ../../runtime/native/mapanare_runtime.c -o test_c_runtime_asan
 *
 * With ThreadSanitizer:
 *   gcc -fsanitize=thread -g -pthread test_c_runtime.c \
 *       ../../runtime/native/mapanare_core.c \
 *       ../../runtime/native/mapanare_runtime.c -o test_c_runtime_tsan
 */

#include "../../runtime/native/mapanare_core.h"
#include "../../runtime/native/mapanare_runtime.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/* -----------------------------------------------------------------------
 * Test infrastructure
 * ----------------------------------------------------------------------- */

static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) static void name(void)
#define RUN_TEST(name) do { \
    tests_run++; \
    printf("  %-50s ", #name); \
    fflush(stdout); \
    name(); \
    tests_passed++; \
    printf("[PASS]\n"); \
} while(0)

#define ASSERT(cond) do { \
    if (!(cond)) { \
        tests_failed++; \
        tests_passed--; \
        printf("[FAIL] %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        return; \
    } \
} while(0)

#define ASSERT_EQ(a, b) ASSERT((a) == (b))
#define ASSERT_NE(a, b) ASSERT((a) != (b))
#define ASSERT_GT(a, b) ASSERT((a) > (b))
#define ASSERT_GE(a, b) ASSERT((a) >= (b))

/* -----------------------------------------------------------------------
 * 1. String tests
 * ----------------------------------------------------------------------- */

TEST(test_str_from_cstr) {
    MnString s = __mn_str_from_cstr("hello");
    ASSERT_EQ(s.len, 5);
    __mn_str_free(s);
}

TEST(test_str_empty) {
    MnString s = __mn_str_empty();
    ASSERT_EQ(s.len, 0);
}

TEST(test_str_concat) {
    MnString a = __mn_str_from_cstr("hello");
    MnString b = __mn_str_from_cstr(" world");
    MnString c = __mn_str_concat(a, b);
    ASSERT_EQ(c.len, 11);
    __mn_str_free(a);
    __mn_str_free(b);
    __mn_str_free(c);
}

TEST(test_str_eq) {
    MnString a = __mn_str_from_cstr("abc");
    MnString b = __mn_str_from_cstr("abc");
    MnString c = __mn_str_from_cstr("def");
    ASSERT_EQ(__mn_str_eq(a, b), 1);
    ASSERT_EQ(__mn_str_eq(a, c), 0);
    __mn_str_free(a);
    __mn_str_free(b);
    __mn_str_free(c);
}

TEST(test_str_cmp) {
    MnString a = __mn_str_from_cstr("abc");
    MnString b = __mn_str_from_cstr("abd");
    ASSERT((__mn_str_cmp(a, b) < 0));
    ASSERT((__mn_str_cmp(b, a) > 0));
    ASSERT_EQ(__mn_str_cmp(a, a), 0);
    __mn_str_free(a);
    __mn_str_free(b);
}

TEST(test_str_substr) {
    MnString s = __mn_str_from_cstr("hello world");
    MnString sub = __mn_str_substr(s, 0, 5);
    MnString expected = __mn_str_from_cstr("hello");
    ASSERT_EQ(__mn_str_eq(sub, expected), 1);
    __mn_str_free(s);
    __mn_str_free(sub);
    __mn_str_free(expected);
}

TEST(test_str_starts_with) {
    MnString s = __mn_str_from_cstr("hello world");
    MnString prefix = __mn_str_from_cstr("hello");
    MnString bad = __mn_str_from_cstr("world");
    ASSERT_EQ(__mn_str_starts_with(s, prefix), 1);
    ASSERT_EQ(__mn_str_starts_with(s, bad), 0);
    __mn_str_free(s);
    __mn_str_free(prefix);
    __mn_str_free(bad);
}

TEST(test_str_ends_with) {
    MnString s = __mn_str_from_cstr("hello world");
    MnString suffix = __mn_str_from_cstr("world");
    ASSERT_EQ(__mn_str_ends_with(s, suffix), 1);
    __mn_str_free(s);
    __mn_str_free(suffix);
}

TEST(test_str_find) {
    MnString s = __mn_str_from_cstr("hello world");
    MnString needle = __mn_str_from_cstr("world");
    ASSERT_EQ(__mn_str_find(s, needle), 6);
    __mn_str_free(s);
    __mn_str_free(needle);
}

TEST(test_str_char_at) {
    MnString s = __mn_str_from_cstr("abc");
    MnString c = __mn_str_char_at(s, 1);
    MnString expected = __mn_str_from_cstr("b");
    ASSERT_EQ(__mn_str_eq(c, expected), 1);
    __mn_str_free(s);
    __mn_str_free(c);
    __mn_str_free(expected);
}

TEST(test_str_byte_at) {
    MnString s = __mn_str_from_cstr("abc");
    ASSERT_EQ(__mn_str_byte_at(s, 0), 'a');
    ASSERT_EQ(__mn_str_byte_at(s, 1), 'b');
    ASSERT_EQ(__mn_str_byte_at(s, 3), -1);  /* out of bounds */
    __mn_str_free(s);
}

TEST(test_str_from_int) {
    MnString s = __mn_str_from_int(42);
    MnString expected = __mn_str_from_cstr("42");
    ASSERT_EQ(__mn_str_eq(s, expected), 1);
    __mn_str_free(s);
    __mn_str_free(expected);
}

TEST(test_str_from_null) {
    MnString s = __mn_str_from_cstr(NULL);
    ASSERT_EQ(s.len, 0);
}

TEST(test_str_concat_empty) {
    MnString a = __mn_str_from_cstr("hello");
    MnString b = __mn_str_empty();
    MnString c = __mn_str_concat(a, b);
    ASSERT_EQ(__mn_str_eq(a, c), 1);
    __mn_str_free(a);
    __mn_str_free(c);
}

TEST(test_str_stress_alloc_free) {
    /* Allocate and free 100K strings */
    for (int i = 0; i < 100000; i++) {
        MnString s = __mn_str_from_cstr("stress test string data");
        __mn_str_free(s);
    }
}

TEST(test_str_stress_concat) {
    /* Concat in a loop with proper free */
    MnString a = __mn_str_from_cstr("hello");
    MnString b = __mn_str_from_cstr(" world");
    for (int i = 0; i < 50000; i++) {
        MnString c = __mn_str_concat(a, b);
        __mn_str_free(c);
    }
    __mn_str_free(a);
    __mn_str_free(b);
}

/* -----------------------------------------------------------------------
 * 2. List tests
 * ----------------------------------------------------------------------- */

TEST(test_list_new) {
    MnList list = __mn_list_new(sizeof(int64_t));
    ASSERT_EQ(list.len, 0);
    __mn_list_free(&list);
}

TEST(test_list_push_pop) {
    MnList list = __mn_list_new(sizeof(int64_t));
    int64_t val = 42;
    __mn_list_push(&list, &val);
    ASSERT_EQ(list.len, 1);

    int64_t *got = (int64_t *)__mn_list_get(&list, 0);
    ASSERT_NE(got, NULL);
    ASSERT_EQ(*got, 42);

    int64_t popped;
    ASSERT_EQ(__mn_list_pop(&list, &popped), 0);
    ASSERT_EQ(popped, 42);
    ASSERT_EQ(list.len, 0);
    __mn_list_free(&list);
}

TEST(test_list_set) {
    MnList list = __mn_list_new(sizeof(int64_t));
    int64_t val = 10;
    __mn_list_push(&list, &val);
    val = 20;
    __mn_list_set(&list, 0, &val);
    int64_t *got = (int64_t *)__mn_list_get(&list, 0);
    ASSERT_EQ(*got, 20);
    __mn_list_free(&list);
}

TEST(test_list_oob) {
    /* v4.133.0 An.1: __mn_list_get / __mn_list_set now abort(3) on OOB
     * reads (runtime/native/mapanare_core.c — deliberate hardening
     * after v4.31.0 removed the static-zero-buffer workaround, since
     * silent zero reads were a worse bug than a clear diagnostic
     * abort). That makes the original expectation (non-NULL return
     * from out-of-bounds __mn_list_get) obsolete — calling it from
     * this test harness would terminate the whole binary. Only the
     * behaviour that is still safe to exercise inline is kept:
     * __mn_list_pop returning -1 on empty. OOB __mn_list_get/_set
     * behaviour is now asserted by the Python-side sanitizer suite
     * (runs each case in its own subprocess). */
    MnList list = __mn_list_new(sizeof(int64_t));
    int64_t dummy;
    ASSERT_EQ(__mn_list_pop(&list, &dummy), -1);
    __mn_list_free(&list);
}

TEST(test_list_grow) {
    MnList list = __mn_list_new(sizeof(int64_t));
    /* Push more than initial capacity (8) to trigger growth */
    for (int64_t i = 0; i < 1000; i++) {
        __mn_list_push(&list, &i);
    }
    ASSERT_EQ(list.len, 1000);
    for (int64_t i = 0; i < 1000; i++) {
        int64_t *got = (int64_t *)__mn_list_get(&list, i);
        ASSERT_EQ(*got, i);
    }
    __mn_list_free(&list);
}

TEST(test_list_clear) {
    MnList list = __mn_list_new(sizeof(int64_t));
    int64_t val = 1;
    __mn_list_push(&list, &val);
    __mn_list_push(&list, &val);
    __mn_list_clear(&list);
    ASSERT_EQ(list.len, 0);
    __mn_list_free(&list);
}

TEST(test_list_str) {
    MnList list = __mn_list_str_new();
    MnString s1 = __mn_str_from_cstr("hello");
    MnString s2 = __mn_str_from_cstr("world");
    __mn_list_str_push(&list, s1);
    __mn_list_str_push(&list, s2);
    ASSERT_EQ(__mn_list_len(&list), 2);

    MnString got = __mn_list_str_get(&list, 0);
    ASSERT_EQ(__mn_str_eq(got, s1), 1);

    got = __mn_list_str_get(&list, 1);
    ASSERT_EQ(__mn_str_eq(got, s2), 1);

    /* v4.133.0 An.1: OOB __mn_list_str_get now aborts(3) to match the
     * hardened MnList API (see test_list_oob above). The old "returns
     * empty string" expectation no longer holds; removing the OOB
     * probe here keeps the in-process C test runnable. */

    __mn_list_free_strings(&list);
}

TEST(test_list_concat) {
    /* Two non-empty lists */
    MnList a = __mn_list_new(sizeof(int64_t));
    MnList b = __mn_list_new(sizeof(int64_t));
    int64_t v1 = 10, v2 = 20, v3 = 30;
    __mn_list_push(&a, &v1);
    __mn_list_push(&a, &v2);
    __mn_list_push(&b, &v3);
    MnList c = __mn_list_concat(&a, &b);
    ASSERT_EQ(c.len, 3);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&c, 0), 10);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&c, 1), 20);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&c, 2), 30);
    __mn_list_free(&c);

    /* Empty + non-empty */
    MnList empty = __mn_list_new(sizeof(int64_t));
    MnList d = __mn_list_concat(&empty, &b);
    ASSERT_EQ(d.len, 1);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&d, 0), 30);
    __mn_list_free(&d);

    /* Non-empty + empty */
    MnList e = __mn_list_concat(&a, &empty);
    ASSERT_EQ(e.len, 2);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&e, 0), 10);
    __mn_list_free(&e);

    __mn_list_free(&a);
    __mn_list_free(&b);
}

TEST(test_list_stress) {
    MnList list = __mn_list_new(sizeof(int64_t));
    for (int64_t i = 0; i < 100000; i++) {
        __mn_list_push(&list, &i);
    }
    ASSERT_EQ(list.len, 100000);
    __mn_list_free(&list);
}

/* -----------------------------------------------------------------------
 * 3. Arena tests
 * ----------------------------------------------------------------------- */

TEST(test_arena_basic) {
    MnArena *arena = mn_arena_create(4096);
    ASSERT_NE(arena, NULL);

    void *p1 = mn_arena_alloc(arena, 64);
    ASSERT_NE(p1, NULL);

    void *p2 = mn_arena_alloc(arena, 128);
    ASSERT_NE(p2, NULL);
    ASSERT_NE(p1, p2);

    mn_arena_destroy(arena);
}

TEST(test_arena_large_alloc) {
    MnArena *arena = mn_arena_create(256);
    /* Allocate larger than block size — should still work */
    void *p = mn_arena_alloc(arena, 1024);
    ASSERT_NE(p, NULL);
    mn_arena_destroy(arena);
}

TEST(test_arena_zero_alloc) {
    MnArena *arena = mn_arena_create(4096);
    void *p = mn_arena_alloc(arena, 0);
    ASSERT_EQ(p, NULL);
    mn_arena_destroy(arena);
}

TEST(test_arena_stress) {
    MnArena *arena = mn_arena_create(8192);
    for (int i = 0; i < 100000; i++) {
        void *p = mn_arena_alloc(arena, 64);
        ASSERT_NE(p, NULL);
        /* Write to allocation to verify it's valid */
        memset(p, 0xAB, 64);
    }
    mn_arena_destroy(arena);
}

TEST(test_agent_arena) {
    MnArena *arena = mn_agent_arena_create();
    ASSERT_NE(arena, NULL);
    void *p = mn_arena_alloc(arena, 256);
    ASSERT_NE(p, NULL);
    mn_agent_arena_destroy(arena);
}

/* -----------------------------------------------------------------------
 * 4. Memory helpers
 * ----------------------------------------------------------------------- */

TEST(test_alloc_free) {
    void *p = __mn_alloc(1024);
    ASSERT_NE(p, NULL);
    /* Verify zero-initialized */
    char *cp = (char *)p;
    for (int i = 0; i < 1024; i++) {
        ASSERT_EQ(cp[i], 0);
    }
    __mn_free(p);
}

TEST(test_realloc) {
    void *p = __mn_alloc(64);
    p = __mn_realloc(p, 256);
    ASSERT_NE(p, NULL);
    __mn_free(p);
}

/* -----------------------------------------------------------------------
 * 5. Ring buffer tests
 * ----------------------------------------------------------------------- */

TEST(test_ring_basic) {
    mapanare_ring_buffer_t rb;
    ASSERT_EQ(mapanare_ring_create(&rb, 16), 0);
    ASSERT_EQ(mapanare_ring_capacity(&rb), 16);
    ASSERT_EQ(mapanare_ring_is_empty(&rb), 1);

    int val = 42;
    ASSERT_EQ(mapanare_ring_push(&rb, (void *)(intptr_t)val), 0);
    ASSERT_EQ(mapanare_ring_size(&rb), 1);

    void *out = NULL;
    ASSERT_EQ(mapanare_ring_pop(&rb, &out), 0);
    ASSERT_EQ((intptr_t)out, 42);
    ASSERT_EQ(mapanare_ring_is_empty(&rb), 1);

    mapanare_ring_destroy(&rb);
}

TEST(test_ring_full) {
    mapanare_ring_buffer_t rb;
    ASSERT_EQ(mapanare_ring_create(&rb, 4), 0);

    for (int i = 0; i < 4; i++) {
        ASSERT_EQ(mapanare_ring_push(&rb, (void *)(intptr_t)(i + 1)), 0);
    }
    ASSERT_EQ(mapanare_ring_is_full(&rb), 1);
    ASSERT_EQ(mapanare_ring_push(&rb, (void *)99), -1);  /* full */

    mapanare_ring_destroy(&rb);
}

TEST(test_ring_wraparound) {
    mapanare_ring_buffer_t rb;
    ASSERT_EQ(mapanare_ring_create(&rb, 4), 0);

    for (int cycle = 0; cycle < 10; cycle++) {
        for (int i = 0; i < 4; i++) {
            ASSERT_EQ(mapanare_ring_push(&rb, (void *)(intptr_t)(cycle * 10 + i)), 0);
        }
        for (int i = 0; i < 4; i++) {
            void *out;
            ASSERT_EQ(mapanare_ring_pop(&rb, &out), 0);
            ASSERT_EQ((intptr_t)out, cycle * 10 + i);
        }
    }
    mapanare_ring_destroy(&rb);
}

TEST(test_ring_stress) {
    /* Rapid push/pop cycling — 1M operations */
    mapanare_ring_buffer_t rb;
    ASSERT_EQ(mapanare_ring_create(&rb, 1024), 0);

    for (int i = 0; i < 1000000; i++) {
        ASSERT_EQ(mapanare_ring_push(&rb, (void *)(intptr_t)(i + 1)), 0);
        void *out;
        ASSERT_EQ(mapanare_ring_pop(&rb, &out), 0);
        ASSERT_EQ((intptr_t)out, i + 1);
    }
    mapanare_ring_destroy(&rb);
}

TEST(test_ring_fill_drain_stress) {
    /* Fill to capacity, drain completely, repeat */
    mapanare_ring_buffer_t rb;
    ASSERT_EQ(mapanare_ring_create(&rb, 256), 0);

    for (int cycle = 0; cycle < 1000; cycle++) {
        for (int i = 0; i < 256; i++) {
            ASSERT_EQ(mapanare_ring_push(&rb, (void *)(intptr_t)(i + 1)), 0);
        }
        ASSERT_EQ(mapanare_ring_is_full(&rb), 1);
        for (int i = 0; i < 256; i++) {
            void *out;
            ASSERT_EQ(mapanare_ring_pop(&rb, &out), 0);
            ASSERT_EQ((intptr_t)out, i + 1);
        }
        ASSERT_EQ(mapanare_ring_is_empty(&rb), 1);
    }
    mapanare_ring_destroy(&rb);
}

/* -----------------------------------------------------------------------
 * 6. Backpressure tests
 * ----------------------------------------------------------------------- */

TEST(test_bp_basic) {
    mapanare_backpressure_t bp;
    mapanare_bp_init(&bp, 10);
    ASSERT_EQ(mapanare_bp_pending(&bp), 0);
    ASSERT_EQ(mapanare_bp_is_overloaded(&bp), 0);

    for (int i = 0; i < 10; i++) {
        mapanare_bp_increment(&bp);
    }
    ASSERT_EQ(mapanare_bp_pending(&bp), 10);
    ASSERT_EQ(mapanare_bp_is_overloaded(&bp), 1);

    mapanare_bp_decrement(&bp);
    ASSERT_EQ(mapanare_bp_is_overloaded(&bp), 0);
}

TEST(test_bp_stress) {
    mapanare_backpressure_t bp;
    mapanare_bp_init(&bp, 1000);

    /* Rapid increment/decrement cycling */
    for (int i = 0; i < 100000; i++) {
        mapanare_bp_increment(&bp);
    }
    ASSERT_EQ(mapanare_bp_pending(&bp), 100000);
    ASSERT_EQ(mapanare_bp_is_overloaded(&bp), 1);

    for (int i = 0; i < 100000; i++) {
        mapanare_bp_decrement(&bp);
    }
    ASSERT_EQ(mapanare_bp_pending(&bp), 0);
    ASSERT_EQ(mapanare_bp_is_overloaded(&bp), 0);
}

/* -----------------------------------------------------------------------
 * 7. Thread pool tests
 * ----------------------------------------------------------------------- */

#ifdef _WIN32
#include <windows.h>
#define ATOMIC_INT volatile LONG
#define ATOMIC_INC(p) InterlockedIncrement(p)
#define ATOMIC_LOAD(p) InterlockedCompareExchange(p, 0, 0)
#else
#include <stdatomic.h>
#include <unistd.h>
#define ATOMIC_INT _Atomic int
#define ATOMIC_INC(p) atomic_fetch_add(p, 1)
#define ATOMIC_LOAD(p) atomic_load(p)
#endif

static ATOMIC_INT g_counter;

static void increment_counter(void *arg) {
    (void)arg;
    ATOMIC_INC(&g_counter);
}

TEST(test_pool_basic) {
    mapanare_thread_pool_t pool;
    ASSERT_EQ(mapanare_pool_create(&pool, 2), 0);
    ASSERT_EQ(mapanare_pool_thread_count(&pool), 2);

#ifdef _WIN32
    InterlockedExchange(&g_counter, 0);
#else
    atomic_store(&g_counter, 0);
#endif

    for (int i = 0; i < 10; i++) {
        ASSERT_EQ(mapanare_pool_submit(&pool, increment_counter, NULL), 0);
    }

    /* Wait for completion */
#ifdef _WIN32
    Sleep(500);
#else
    usleep(500000);
#endif
    ASSERT_EQ(ATOMIC_LOAD(&g_counter), 10);
    mapanare_pool_destroy(&pool);
}

TEST(test_pool_saturation) {
    /* Submit a large number of tasks to stress the pool */
    mapanare_thread_pool_t pool;
    ASSERT_EQ(mapanare_pool_create(&pool, 4), 0);

#ifdef _WIN32
    InterlockedExchange(&g_counter, 0);
#else
    atomic_store(&g_counter, 0);
#endif

    int submitted = 0;
    for (int i = 0; i < 500; i++) {
        if (mapanare_pool_submit(&pool, increment_counter, NULL) == 0) {
            submitted++;
        }
    }

    /* Wait for all tasks to complete */
#ifdef _WIN32
    Sleep(2000);
#else
    usleep(2000000);
#endif
    ASSERT_EQ(ATOMIC_LOAD(&g_counter), submitted);
    mapanare_pool_destroy(&pool);
}

TEST(test_pool_cpu_count) {
    uint32_t count = mapanare_cpu_count();
    ASSERT_GE(count, 1);
}

/* -----------------------------------------------------------------------
 * 8. Agent tests
 * ----------------------------------------------------------------------- */

static int echo_handler(void *agent_data, void *msg, void **out_msg) {
    (void)agent_data;
    *out_msg = msg;
    return 0;
}

static int double_handler(void *agent_data, void *msg, void **out_msg) {
    (void)agent_data;
    intptr_t val = (intptr_t)msg;
    *out_msg = (void *)(val * 2);
    return 0;
}

static int failing_handler(void *agent_data, void *msg, void **out_msg) {
    (void)agent_data;
    (void)msg;
    (void)out_msg;
    return -1;
}

TEST(test_agent_lifecycle) {
    mapanare_agent_t agent;
    ASSERT_EQ(mapanare_agent_init(&agent, "test_lifecycle", echo_handler, NULL, 256, 256), 0);
    ASSERT_EQ(mapanare_agent_get_state(&agent), MAPANARE_AGENT_IDLE);

    ASSERT_EQ(mapanare_agent_spawn(&agent), 0);
#ifdef _WIN32
    Sleep(50);
#else
    usleep(50000);
#endif
    ASSERT_EQ(mapanare_agent_get_state(&agent), MAPANARE_AGENT_RUNNING);

    mapanare_agent_stop(&agent);
    ASSERT_EQ(mapanare_agent_get_state(&agent), MAPANARE_AGENT_STOPPED);
    mapanare_agent_destroy(&agent);
}

TEST(test_agent_send_recv) {
    mapanare_agent_t agent;
    ASSERT_EQ(mapanare_agent_init(&agent, "doubler", double_handler, NULL, 256, 256), 0);
    ASSERT_EQ(mapanare_agent_spawn(&agent), 0);
#ifdef _WIN32
    Sleep(50);
#else
    usleep(50000);
#endif

    mapanare_agent_send(&agent, (void *)21);
#ifdef _WIN32
    Sleep(100);
#else
    usleep(100000);
#endif

    void *out = NULL;
    ASSERT_EQ(mapanare_agent_recv(&agent, &out), 0);
    ASSERT_EQ((intptr_t)out, 42);

    mapanare_agent_stop(&agent);
    mapanare_agent_destroy(&agent);
}

TEST(test_agent_pause_resume) {
    mapanare_agent_t agent;
    ASSERT_EQ(mapanare_agent_init(&agent, "pause_test", echo_handler, NULL, 256, 256), 0);
    ASSERT_EQ(mapanare_agent_spawn(&agent), 0);
#ifdef _WIN32
    Sleep(50);
#else
    usleep(50000);
#endif

    mapanare_agent_pause(&agent);
    ASSERT_EQ(mapanare_agent_get_state(&agent), MAPANARE_AGENT_PAUSED);

    mapanare_agent_resume(&agent);
    ASSERT_EQ(mapanare_agent_get_state(&agent), MAPANARE_AGENT_RUNNING);

    mapanare_agent_stop(&agent);
    mapanare_agent_destroy(&agent);
}

TEST(test_agent_failing_handler) {
    mapanare_agent_t agent;
    ASSERT_EQ(mapanare_agent_init(&agent, "fail_test", failing_handler, NULL, 256, 256), 0);
    ASSERT_EQ(mapanare_agent_spawn(&agent), 0);
#ifdef _WIN32
    Sleep(50);
#else
    usleep(50000);
#endif

    mapanare_agent_send(&agent, (void *)1);
#ifdef _WIN32
    Sleep(200);
#else
    usleep(200000);
#endif

    ASSERT_EQ(mapanare_agent_get_state(&agent), MAPANARE_AGENT_FAILED);
    mapanare_agent_stop(&agent);
    mapanare_agent_destroy(&agent);
}

TEST(test_agent_metrics) {
    mapanare_agent_t agent;
    ASSERT_EQ(mapanare_agent_init(&agent, "metrics", echo_handler, NULL, 256, 256), 0);
    /* v4.137.0 (Ch.1 test hygiene): this test uses pointer-as-token
     * values (1..5) rather than heap allocations. The default dtor
     * (free, set in v4.78.0 CARRY_FORWARD #50) would call free() on
     * those tokens during destroy's outbox drain. NULL it here. */
    agent.message_dtor = NULL;
    ASSERT_EQ(mapanare_agent_messages_processed(&agent), 0);

    ASSERT_EQ(mapanare_agent_spawn(&agent), 0);
#ifdef _WIN32
    Sleep(50);
#else
    usleep(50000);
#endif

    for (int i = 0; i < 5; i++) {
        mapanare_agent_send(&agent, (void *)(intptr_t)(i + 1));
    }
#ifdef _WIN32
    Sleep(300);
#else
    usleep(300000);
#endif

    ASSERT_EQ(mapanare_agent_messages_processed(&agent), 5);
    mapanare_agent_stop(&agent);
    mapanare_agent_destroy(&agent);
}

TEST(test_agent_new_heap) {
    mapanare_agent_t *agent = mapanare_agent_new("heap_agent", echo_handler, NULL, 256, 256);
    ASSERT_NE(agent, NULL);
    ASSERT_EQ(mapanare_agent_get_state(agent), MAPANARE_AGENT_IDLE);
    mapanare_agent_destroy(agent);
    free(agent);
}

/* -----------------------------------------------------------------------
 * 9. Registry tests
 * ----------------------------------------------------------------------- */

TEST(test_registry_basic) {
    mapanare_agent_registry_t reg;
    mapanare_registry_init(&reg);
    ASSERT_EQ(mapanare_registry_count(&reg), 0);

    mapanare_agent_t agent;
    mapanare_agent_init(&agent, "reg_test", echo_handler, NULL, 16, 16);
    ASSERT_EQ(mapanare_registry_add(&reg, &agent), 0);
    ASSERT_EQ(mapanare_registry_count(&reg), 1);

    mapanare_agent_t *found = mapanare_registry_find(&reg, "reg_test");
    ASSERT_NE(found, NULL);

    found = mapanare_registry_find(&reg, "nonexistent");
    ASSERT_EQ(found, NULL);

    ASSERT_EQ(mapanare_registry_remove(&reg, "reg_test"), 0);
    ASSERT_EQ(mapanare_registry_count(&reg), 0);

    mapanare_agent_destroy(&agent);
    mapanare_registry_destroy(&reg);
}

/* -----------------------------------------------------------------------
 * 10. File I/O tests
 * ----------------------------------------------------------------------- */

TEST(test_file_write_read) {
    MnString path = __mn_str_from_cstr("_test_tmp_file.txt");
    MnString content = __mn_str_from_cstr("hello from C tests");

    int64_t rc = __mn_file_write(path, content);
    ASSERT_EQ(rc, 0);

    int64_t ok = 0;
    MnString read_back = __mn_file_read(path, &ok);
    ASSERT_EQ(ok, 1);
    ASSERT_EQ(__mn_str_eq(read_back, content), 1);

    __mn_str_free(path);
    __mn_str_free(content);
    __mn_str_free(read_back);

    /* Clean up temp file */
    remove("_test_tmp_file.txt");
}

TEST(test_file_read_nonexistent) {
    MnString path = __mn_str_from_cstr("_nonexistent_file_12345.txt");
    int64_t ok = 0;
    MnString result = __mn_file_read(path, &ok);
    ASSERT_EQ(ok, 0);
    ASSERT_EQ(result.len, 0);
    __mn_str_free(path);
}

/* -----------------------------------------------------------------------
 * 11. Graceful shutdown tests
 * ----------------------------------------------------------------------- */

TEST(test_shutdown_init) {
    mapanare_agent_registry_t reg;
    mapanare_registry_init(&reg);
    mapanare_shutdown_init(&reg);
    /* Should not be in shutdown state initially */
    ASSERT_EQ(mapanare_shutdown_requested(), 0);
    mapanare_registry_destroy(&reg);
}

TEST(test_shutdown_with_agents) {
    mapanare_agent_registry_t reg;
    mapanare_registry_init(&reg);
    mapanare_shutdown_init(&reg);

    mapanare_agent_t *agent = mapanare_agent_new("shutdown_test", echo_handler, NULL, 16, 16);
    ASSERT_NE(agent, NULL);
    mapanare_registry_add(&reg, agent);
    ASSERT_EQ(mapanare_agent_spawn(agent), 0);
#ifdef _WIN32
    Sleep(50);
#else
    usleep(50000);
#endif
    ASSERT_EQ(mapanare_agent_get_state(agent), MAPANARE_AGENT_RUNNING);

    /* Manually stop (we can't send ourselves a signal safely in tests) */
    mapanare_registry_stop_all(&reg);
    ASSERT_EQ(mapanare_agent_get_state(agent), MAPANARE_AGENT_STOPPED);

    mapanare_agent_destroy(agent);
    free(agent);
    mapanare_registry_destroy(&reg);
}

/* -----------------------------------------------------------------------
 * 12. Map tests
 * ----------------------------------------------------------------------- */

TEST(test_map_new_free) {
    MnMap *m = __mn_map_new(sizeof(int64_t), sizeof(int64_t), MN_MAP_KEY_INT, MN_MAP_VAL_OPAQUE);
    ASSERT_NE(m, NULL);
    ASSERT_EQ(__mn_map_len(m), 0);
    __mn_map_free(m);
}

TEST(test_map_set_get) {
    MnMap *m = __mn_map_new(sizeof(int64_t), sizeof(int64_t), MN_MAP_KEY_INT, MN_MAP_VAL_OPAQUE);
    int64_t k1 = 10, v1 = 100;
    int64_t k2 = 20, v2 = 200;
    int64_t k3 = 30, v3 = 300;
    __mn_map_set(m, &k1, &v1);
    __mn_map_set(m, &k2, &v2);
    __mn_map_set(m, &k3, &v3);
    int64_t *got = (int64_t *)__mn_map_get(m, &k2);
    ASSERT_NE(got, NULL);
    ASSERT_EQ(*got, 200);
    __mn_map_free(m);
}

TEST(test_map_overwrite) {
    MnMap *m = __mn_map_new(sizeof(int64_t), sizeof(int64_t), MN_MAP_KEY_INT, MN_MAP_VAL_OPAQUE);
    int64_t k = 42, v1 = 1, v2 = 2;
    __mn_map_set(m, &k, &v1);
    __mn_map_set(m, &k, &v2);
    ASSERT_EQ(__mn_map_len(m), 1);
    int64_t *got = (int64_t *)__mn_map_get(m, &k);
    ASSERT_NE(got, NULL);
    ASSERT_EQ(*got, 2);
    __mn_map_free(m);
}

TEST(test_map_del) {
    MnMap *m = __mn_map_new(sizeof(int64_t), sizeof(int64_t), MN_MAP_KEY_INT, MN_MAP_VAL_OPAQUE);
    int64_t k = 7, v = 77;
    __mn_map_set(m, &k, &v);
    ASSERT_EQ(__mn_map_contains(m, &k), 1);
    ASSERT_EQ(__mn_map_del(m, &k), 1);
    ASSERT_EQ(__mn_map_contains(m, &k), 0);
    ASSERT_EQ(__mn_map_len(m), 0);
    __mn_map_free(m);
}

TEST(test_map_contains) {
    MnMap *m = __mn_map_new(sizeof(int64_t), sizeof(int64_t), MN_MAP_KEY_INT, MN_MAP_VAL_OPAQUE);
    int64_t k = 5, v = 55, absent = 99;
    __mn_map_set(m, &k, &v);
    ASSERT_EQ(__mn_map_contains(m, &k), 1);
    ASSERT_EQ(__mn_map_contains(m, &absent), 0);
    __mn_map_free(m);
}

TEST(test_map_len) {
    MnMap *m = __mn_map_new(sizeof(int64_t), sizeof(int64_t), MN_MAP_KEY_INT, MN_MAP_VAL_OPAQUE);
    for (int64_t i = 0; i < 10; i++) {
        int64_t v = i * 10;
        __mn_map_set(m, &i, &v);
    }
    ASSERT_EQ(__mn_map_len(m), 10);
    __mn_map_free(m);
}

TEST(test_map_iter) {
    MnMap *m = __mn_map_new(sizeof(int64_t), sizeof(int64_t), MN_MAP_KEY_INT, MN_MAP_VAL_OPAQUE);
    for (int64_t i = 1; i <= 3; i++) {
        int64_t v = i * 100;
        __mn_map_set(m, &i, &v);
    }
    MnMapIter *it = __mn_map_iter_new(m);
    ASSERT_NE(it, NULL);
    int count = 0;
    void *kp, *vp;
    while (__mn_map_iter_next(it, &kp, &vp)) count++;
    ASSERT_EQ(count, 3);
    __mn_map_iter_free(it);
    __mn_map_free(m);
}

TEST(test_map_free_deep) {
    MnMap *m = __mn_map_new(sizeof(MnString), sizeof(MnString), MN_MAP_KEY_STR, MN_MAP_VAL_STR);
    MnString k = __mn_str_from_cstr("key1");
    MnString v = __mn_str_from_cstr("val1");
    __mn_map_set(m, &k, &v);
    /* free_deep should free both the key and value strings */
    __mn_map_free_deep(m);
    /* If ASan is active, any leak or double-free will be detected */
}

/* -----------------------------------------------------------------------
 * 13. Signal tests
 * ----------------------------------------------------------------------- */

TEST(test_signal_new_free) {
    int64_t val = 42;
    MnSignal *s = __mn_signal_new(&val, sizeof(int64_t));
    ASSERT_NE(s, NULL);
    __mn_signal_free(s);
}

TEST(test_signal_set_get) {
    int64_t val = 10;
    MnSignal *s = __mn_signal_new(&val, sizeof(int64_t));
    int64_t *got = (int64_t *)__mn_signal_get(s);
    ASSERT_EQ(*got, 10);
    int64_t val2 = 20;
    __mn_signal_set(s, &val2);
    got = (int64_t *)__mn_signal_get(s);
    ASSERT_EQ(*got, 20);
    __mn_signal_free(s);
}

TEST(test_signal_subscribe_unsubscribe) {
    int64_t va = 1, vb = 0;
    MnSignal *a = __mn_signal_new(&va, sizeof(int64_t));
    MnSignal *b = __mn_signal_new(&vb, sizeof(int64_t));
    __mn_signal_subscribe(a, b);
    int64_t va2 = 2;
    __mn_signal_set(a, &va2);
    /* b should be marked dirty after a changes */
    __mn_signal_unsubscribe(a, b);
    __mn_signal_free(b);
    __mn_signal_free(a);
}

TEST(test_signal_no_change_skip) {
    int64_t val = 42;
    MnSignal *s = __mn_signal_new(&val, sizeof(int64_t));
    /* Setting the same value should not trigger propagation */
    __mn_signal_set(s, &val);
    int64_t *got = (int64_t *)__mn_signal_get(s);
    ASSERT_EQ(*got, 42);
    __mn_signal_free(s);
}

/* -----------------------------------------------------------------------
 * 14. Stream tests
 * ----------------------------------------------------------------------- */

static void stream_double_fn(void *out, const void *in, void *ud) {
    (void)ud;
    *(int64_t *)out = *(const int64_t *)in * 2;
}

static int64_t stream_is_even_fn(const void *elem, void *ud) {
    (void)ud;
    return (*(const int64_t *)elem) % 2 == 0;
}

TEST(test_stream_from_list_collect) {
    MnList list = {0};
    for (int64_t i = 1; i <= 3; i++) __mn_list_push(&list, &i);
    MnStream *s = __mn_stream_from_list(&list, sizeof(int64_t));
    ASSERT_NE(s, NULL);
    MnList result = __mn_stream_collect(s, sizeof(int64_t));
    ASSERT_EQ(result.len, 3);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&result, 0), 1);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&result, 2), 3);
    __mn_list_free(&result);
    __mn_stream_free_chain(s);
    __mn_list_free(&list);
}

TEST(test_stream_map) {
    MnList list = {0};
    for (int64_t i = 1; i <= 3; i++) __mn_list_push(&list, &i);
    MnStream *s = __mn_stream_from_list(&list, sizeof(int64_t));
    MnStream *mapped = __mn_stream_map(s, stream_double_fn, NULL, sizeof(int64_t));
    MnList result = __mn_stream_collect(mapped, sizeof(int64_t));
    ASSERT_EQ(result.len, 3);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&result, 0), 2);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&result, 1), 4);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&result, 2), 6);
    __mn_list_free(&result);
    __mn_stream_free_chain(mapped);
    __mn_list_free(&list);
}

TEST(test_stream_filter) {
    MnList list = {0};
    for (int64_t i = 1; i <= 5; i++) __mn_list_push(&list, &i);
    MnStream *s = __mn_stream_from_list(&list, sizeof(int64_t));
    MnStream *filtered = __mn_stream_filter(s, stream_is_even_fn, NULL);
    MnList result = __mn_stream_collect(filtered, sizeof(int64_t));
    ASSERT_EQ(result.len, 2);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&result, 0), 2);
    ASSERT_EQ(*(int64_t *)__mn_list_get(&result, 1), 4);
    __mn_list_free(&result);
    __mn_stream_free_chain(filtered);
    __mn_list_free(&list);
}

TEST(test_stream_free_chain) {
    MnList list = {0};
    for (int64_t i = 1; i <= 3; i++) __mn_list_push(&list, &i);
    MnStream *s = __mn_stream_from_list(&list, sizeof(int64_t));
    MnStream *mapped = __mn_stream_map(s, stream_double_fn, NULL, sizeof(int64_t));
    MnStream *filtered = __mn_stream_filter(mapped, stream_is_even_fn, NULL);
    /* free_chain should walk the entire upstream pipeline without leaks */
    __mn_stream_free_chain(filtered);
    __mn_list_free(&list);
}

/* -----------------------------------------------------------------------
 * 15. MnValue (any) tests
 * ----------------------------------------------------------------------- */

TEST(test_any_box_int) {
    MnValue v = __mn_any_box_int(42);
    ASSERT_EQ(__mn_any_tag(v), MN_TAG_INT);
}

TEST(test_any_box_float) {
    MnValue v = __mn_any_box_float(3.14);
    ASSERT_EQ(__mn_any_tag(v), MN_TAG_FLOAT);
}

TEST(test_any_box_bool) {
    MnValue v = __mn_any_box_bool(1);
    ASSERT_EQ(__mn_any_tag(v), MN_TAG_BOOL);
}

TEST(test_any_unbox_int) {
    MnValue v = __mn_any_box_int(42);
    ASSERT_EQ(__mn_any_unbox_int(v), 42);
}

TEST(test_any_typename) {
    MnValue v = __mn_any_box_int(1);
    MnString name = __mn_any_typename(v);
    MnString expected = __mn_str_from_cstr("Int");
    ASSERT_EQ(__mn_str_eq(name, expected), 1);
    __mn_str_free(expected);
    /* name is now a static constant — no free needed */
}

/* -----------------------------------------------------------------------
 * Main
 * ----------------------------------------------------------------------- */

int main(void) {
    printf("=== Mapanare C Runtime Tests ===\n\n");

    printf("[String Tests]\n");
    RUN_TEST(test_str_from_cstr);
    RUN_TEST(test_str_empty);
    RUN_TEST(test_str_concat);
    RUN_TEST(test_str_eq);
    RUN_TEST(test_str_cmp);
    RUN_TEST(test_str_substr);
    RUN_TEST(test_str_starts_with);
    RUN_TEST(test_str_ends_with);
    RUN_TEST(test_str_find);
    RUN_TEST(test_str_char_at);
    RUN_TEST(test_str_byte_at);
    RUN_TEST(test_str_from_int);
    RUN_TEST(test_str_from_null);
    RUN_TEST(test_str_concat_empty);
    RUN_TEST(test_str_stress_alloc_free);
    RUN_TEST(test_str_stress_concat);
    printf("\n");

    printf("[List Tests]\n");
    RUN_TEST(test_list_new);
    RUN_TEST(test_list_push_pop);
    RUN_TEST(test_list_set);
    RUN_TEST(test_list_oob);
    RUN_TEST(test_list_grow);
    RUN_TEST(test_list_clear);
    RUN_TEST(test_list_str);
    RUN_TEST(test_list_concat);
    RUN_TEST(test_list_stress);
    printf("\n");

    printf("[Arena Tests]\n");
    RUN_TEST(test_arena_basic);
    RUN_TEST(test_arena_large_alloc);
    RUN_TEST(test_arena_zero_alloc);
    RUN_TEST(test_arena_stress);
    RUN_TEST(test_agent_arena);
    printf("\n");

    printf("[Memory Tests]\n");
    RUN_TEST(test_alloc_free);
    RUN_TEST(test_realloc);
    printf("\n");

    printf("[Ring Buffer Tests]\n");
    RUN_TEST(test_ring_basic);
    RUN_TEST(test_ring_full);
    RUN_TEST(test_ring_wraparound);
    RUN_TEST(test_ring_stress);
    RUN_TEST(test_ring_fill_drain_stress);
    printf("\n");

    printf("[Backpressure Tests]\n");
    RUN_TEST(test_bp_basic);
    RUN_TEST(test_bp_stress);
    printf("\n");

    printf("[Thread Pool Tests]\n");
    RUN_TEST(test_pool_basic);
    RUN_TEST(test_pool_saturation);
    RUN_TEST(test_pool_cpu_count);
    printf("\n");

    printf("[Agent Tests]\n");
    RUN_TEST(test_agent_lifecycle);
    RUN_TEST(test_agent_send_recv);
    RUN_TEST(test_agent_pause_resume);
    RUN_TEST(test_agent_failing_handler);
    RUN_TEST(test_agent_metrics);
    RUN_TEST(test_agent_new_heap);
    printf("\n");

    printf("[Registry Tests]\n");
    RUN_TEST(test_registry_basic);
    printf("\n");

    printf("[File I/O Tests]\n");
    RUN_TEST(test_file_write_read);
    RUN_TEST(test_file_read_nonexistent);
    printf("\n");

    printf("[Graceful Shutdown Tests]\n");
    RUN_TEST(test_shutdown_init);
    RUN_TEST(test_shutdown_with_agents);
    printf("\n");

    printf("[Map Tests]\n");
    RUN_TEST(test_map_new_free);
    RUN_TEST(test_map_set_get);
    RUN_TEST(test_map_overwrite);
    RUN_TEST(test_map_del);
    RUN_TEST(test_map_contains);
    RUN_TEST(test_map_len);
    RUN_TEST(test_map_iter);
    RUN_TEST(test_map_free_deep);
    printf("\n");

    printf("[Signal Tests]\n");
    RUN_TEST(test_signal_new_free);
    RUN_TEST(test_signal_set_get);
    RUN_TEST(test_signal_subscribe_unsubscribe);
    RUN_TEST(test_signal_no_change_skip);
    printf("\n");

    printf("[Stream Tests]\n");
    RUN_TEST(test_stream_from_list_collect);
    RUN_TEST(test_stream_map);
    RUN_TEST(test_stream_filter);
    RUN_TEST(test_stream_free_chain);
    printf("\n");

    printf("[MnValue (any) Tests]\n");
    RUN_TEST(test_any_box_int);
    RUN_TEST(test_any_box_float);
    RUN_TEST(test_any_box_bool);
    RUN_TEST(test_any_unbox_int);
    RUN_TEST(test_any_typename);
    printf("\n");

    printf("=== Results: %d/%d passed", tests_passed, tests_run);
    if (tests_failed > 0) {
        printf(", %d FAILED", tests_failed);
    }
    printf(" ===\n");

    return tests_failed > 0 ? 1 : 0;
}
