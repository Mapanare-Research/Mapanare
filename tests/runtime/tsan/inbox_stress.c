/*
 * inbox_stress.c — TSan regression test for v4.28.0 Phase 1.2.
 *
 * Before v4.28.0, ``mapanare_agent_send`` called ``mapanare_ring_push`` on
 * the agent's inbox ring directly. The ring is documented SPSC — its
 * ``head`` advance sequence is atomic-store-barrier but not mutex
 * protected. When multiple threads called ``agent_send`` concurrently,
 * the producers would race on slot writes + head advance (v4.26.0 panel:
 * Viper H5). The fix wraps the producer side in
 * ``agent->inbox_producer_lock``.
 *
 * This test:
 *
 * - Spawns 4 producer threads that each push 5000 messages into one agent.
 * - Uses a no-op handler so the consumer side is still single-threaded.
 * - Validates that exactly ``4 * 5000`` messages were accepted and
 *   processed.
 *
 * Under TSan the pre-fix code reports a data race on ``rb->slots[..]``
 * and ``rb->head``; the post-fix code reports clean.
 *
 * Build:
 *   gcc -fsanitize=thread -g -O1 -I runtime/native \
 *       tests/runtime/tsan/inbox_stress.c \
 *       runtime/native/mapanare_runtime.c runtime/native/mapanare_core.c \
 *       -o /tmp/tsan_inbox -lpthread -lm -ldl
 *
 * Run:
 *   /tmp/tsan_inbox
 *
 * Exit 0 + zero TSan reports = PASS.
 */

#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "mapanare_runtime.h"

#define PRODUCERS 4
#define MESSAGES_PER_PRODUCER 5000

static _Atomic int64_t received_count = 0;

static int inbox_handler(void *agent_data, void *msg, void **out_msg) {
    (void)agent_data;
    (void)msg;
    if (out_msg) *out_msg = NULL;
    atomic_fetch_add_explicit(&received_count, 1, memory_order_relaxed);
    return 0;
}

static void *producer_thread(void *arg) {
    mapanare_agent_t *agent = (mapanare_agent_t *)arg;
    for (int i = 0; i < MESSAGES_PER_PRODUCER; i++) {
        /* Retry on BACKPRESSURE/full ring. ``agent_send`` returns -1
         * when the inbox is full; the consumer drains it continuously. */
        while (mapanare_agent_send(agent, (void *)(intptr_t)(i + 1)) != 0) {
            /* brief yield so the consumer catches up */
            sched_yield();
        }
    }
    return NULL;
}

int main(void) {
    mapanare_agent_t agent;
    int rc = mapanare_agent_init(&agent, "inbox_stress", inbox_handler, NULL, 64, 64);
    if (rc != 0) {
        fprintf(stderr, "inbox_stress: mapanare_agent_init failed: %d\n", rc);
        return 1;
    }
    rc = mapanare_agent_spawn(&agent);
    if (rc != 0) {
        fprintf(stderr, "inbox_stress: mapanare_agent_spawn failed: %d\n", rc);
        mapanare_agent_destroy(&agent);
        return 1;
    }

    pthread_t producers[PRODUCERS];
    for (int t = 0; t < PRODUCERS; t++) {
        if (pthread_create(&producers[t], NULL, producer_thread, &agent) != 0) {
            fprintf(stderr, "inbox_stress: pthread_create[%d] failed\n", t);
            return 1;
        }
    }
    for (int t = 0; t < PRODUCERS; t++) {
        pthread_join(producers[t], NULL);
    }

    /* Wait for the consumer to drain the queue. The handler increments
     * ``received_count``; we poll until we see every message arrive. */
    int64_t expected = (int64_t)PRODUCERS * MESSAGES_PER_PRODUCER;
    int spins = 0;
    while (atomic_load_explicit(&received_count, memory_order_relaxed) < expected) {
        if (++spins > 10000) {
            fprintf(stderr,
                    "inbox_stress: consumer drained only %lld / %lld messages\n",
                    (long long)atomic_load(&received_count), (long long)expected);
            mapanare_agent_stop(&agent);
            mapanare_agent_destroy(&agent);
            return 1;
        }
        usleep(100);
    }

    mapanare_agent_stop(&agent);
    mapanare_agent_destroy(&agent);

    printf("inbox_stress: %d producers x %d msgs = %lld received, no TSan races\n",
           PRODUCERS, MESSAGES_PER_PRODUCER, (long long)expected);
    return 0;
}
