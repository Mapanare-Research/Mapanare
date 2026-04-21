/*
 * test_agent_destroy_drain.c — v4.78.0 CARRY_FORWARD #50
 *
 * Verify that mapanare_agent_destroy drains in-flight messages and
 * frees their payloads.  Before v4.78.0, message_dtor was NULL by
 * default so the drain loop popped messages without freeing them.
 *
 * Build:
 *   gcc -O2 -g -Wall -I runtime/native \
 *     tests/runtime/test_agent_destroy_drain.c \
 *     runtime/native/libmapanare_rt.a \
 *     -o /tmp/test_agent_destroy_drain -lm -lpthread -ldl
 *   /tmp/test_agent_destroy_drain
 */

#include "mapanare_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

static int dtor_call_count = 0;

static void counting_dtor(void *msg) {
    dtor_call_count++;
    free(msg);
}

/* Dummy handler — never called because we never spawn the agent. */
static int dummy_handler(void *data, void *msg, void **out) {
    (void)data; (void)msg; (void)out;
    return 0;
}

static void test_default_dtor_is_free(void) {
    mapanare_agent_t agent;
    int rc = mapanare_agent_init(&agent, "test", dummy_handler, NULL, 8, 8);
    assert(rc == 0);

    /* v4.78.0: message_dtor should default to free */
    assert(agent.message_dtor != NULL);

    /* Post 3 messages with malloc'd payloads */
    for (int i = 0; i < 3; i++) {
        int *payload = (int *)malloc(sizeof(int));
        assert(payload != NULL);
        *payload = i + 1;
        rc = mapanare_ring_push(&agent.inbox, payload);
        assert(rc == 0);
    }

    /* Destroy without consuming — drain loop should free all 3 */
    mapanare_agent_destroy(&agent);
    printf("test_default_dtor_is_free: PASS\n");
}

static void test_custom_dtor_called(void) {
    mapanare_agent_t agent;
    int rc = mapanare_agent_init(&agent, "test2", dummy_handler, NULL, 8, 8);
    assert(rc == 0);

    /* Override with counting destructor */
    agent.message_dtor = counting_dtor;
    dtor_call_count = 0;

    /* Post 5 messages */
    for (int i = 0; i < 5; i++) {
        int *payload = (int *)malloc(sizeof(int));
        assert(payload != NULL);
        *payload = i;
        rc = mapanare_ring_push(&agent.inbox, payload);
        assert(rc == 0);
    }

    /* Destroy should call counting_dtor 5 times */
    mapanare_agent_destroy(&agent);
    assert(dtor_call_count == 5);
    printf("test_custom_dtor_called: PASS (dtor_call_count=%d)\n", dtor_call_count);
}

int main(void) {
    test_default_dtor_is_free();
    test_custom_dtor_called();
    printf("All agent destroy drain tests passed.\n");
    return 0;
}
