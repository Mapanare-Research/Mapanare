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
    MnList list = __mn_list_new(sizeof(int64_t));
    ASSERT_EQ(__mn_list_get(&list, 0), NULL);
    ASSERT_EQ(__mn_list_get(&list, -1), NULL);
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

    /* OOB returns empty */
    got = __mn_list_str_get(&list, 5);
    ASSERT_EQ(got.len, 0);

    __mn_list_free_strings(&list);
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

    printf("=== Results: %d/%d passed", tests_passed, tests_run);
    if (tests_failed > 0) {
        printf(", %d FAILED", tests_failed);
    }
    printf(" ===\n");

    return tests_failed > 0 ? 1 : 0;
}
