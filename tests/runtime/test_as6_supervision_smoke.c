/* v5.42.0 As.6 C smoke test.
 *
 * Spawn a parent + child; child handler returns rc != 0 to trigger
 * FAILED; assert that the parent's on_exit callback fires with the
 * structured exit reason intact.
 *
 * Build:
 *   gcc -O0 -g -pthread /tmp/as6_smoke.c \
 *       runtime/native/libmapanare_rt.a -o /tmp/as6_smoke -lm -lpthread -ldl
 *
 * TSan:
 *   make build-rt CFLAGS="-fsanitize=thread -g"
 *   gcc -O0 -g -fsanitize=thread /tmp/as6_smoke.c ... -o /tmp/as6_smoke_tsan
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdatomic.h>
#include "runtime/native/mapanare_runtime.h"

static atomic_int g_callback_fired      = 0;
static atomic_int g_callback_kind       = -1;
static char       g_callback_reason[MAPANARE_EXIT_REASON_MAX];
static atomic_uintptr_t g_callback_self = 0;

/* Child handler that always returns rc != 0 after stamping a reason. */
static int child_handler(void *agent_data, void *msg, void **out) {
    (void)agent_data; (void)msg; (void)out;
    mapanare_agent_t *self = (mapanare_agent_t *)agent_data;
    mapanare_agent_set_exit_reason(self, MAPANARE_EXIT_CRASHED,
                                    "test failure: deliberate rc!=0");
    return 1;
}

/* Supervisor's on_exit hook. Runs on the dying child's thread. */
static void on_child_exit(struct mapanare_agent *child, void *cb_data) {
    (void)cb_data;
    mapanare_exit_reason_kind_t k;
    char reason[MAPANARE_EXIT_REASON_MAX];
    mapanare_agent_get_exit_reason(child, &k, reason);
    atomic_store(&g_callback_kind, (int)k);
    memcpy(g_callback_reason, reason, MAPANARE_EXIT_REASON_MAX);
    atomic_store(&g_callback_self, (uintptr_t)child);
    atomic_store(&g_callback_fired, 1);
}

int main(void) {
    /* Parent — never receives anything in this smoke; just acts as
     * the supervisor pointer. Real supervisor would have a handler
     * that decodes ChildExited messages from its inbox. */
    mapanare_agent_t *parent = mapanare_agent_new("supervisor", NULL,
                                                   NULL, 16, 16);
    if (!parent) { fprintf(stderr, "parent alloc fail\n"); return 1; }

    mapanare_agent_t *child = mapanare_agent_new("child", child_handler,
                                                   NULL, 16, 16);
    if (!child) { fprintf(stderr, "child alloc fail\n"); return 1; }
    /* child_handler reads agent_data — pass the agent pointer. */
    child->agent_data = child;

    mapanare_agent_set_parent(child, parent);
    mapanare_agent_set_on_exit(child, on_child_exit, parent);

    if (mapanare_agent_spawn(child) != 0) {
        fprintf(stderr, "spawn fail\n"); return 1;
    }

    /* Send any message to wake the handler. */
    mapanare_agent_send(child, (void *)0x1);

    /* Wait up to ~2s for the callback. */
    for (int i = 0; i < 200; i++) {
        if (atomic_load(&g_callback_fired)) break;
        usleep(10000);
    }

    int ok = 1;
    if (!atomic_load(&g_callback_fired)) {
        fprintf(stderr, "FAIL: callback never fired\n"); ok = 0;
    }
    if (atomic_load(&g_callback_kind) != MAPANARE_EXIT_CRASHED) {
        fprintf(stderr, "FAIL: callback kind = %d, expected %d\n",
                atomic_load(&g_callback_kind), MAPANARE_EXIT_CRASHED);
        ok = 0;
    }
    if (strcmp(g_callback_reason, "test failure: deliberate rc!=0") != 0) {
        fprintf(stderr, "FAIL: callback reason = '%s'\n",
                g_callback_reason);
        ok = 0;
    }
    if ((mapanare_agent_t *)atomic_load(&g_callback_self) != child) {
        fprintf(stderr, "FAIL: callback child ptr mismatch\n"); ok = 0;
    }
    if (mapanare_agent_get_state(child) != MAPANARE_AGENT_FAILED) {
        fprintf(stderr, "FAIL: child not in FAILED state\n"); ok = 0;
    }

    mapanare_agent_stop(child);
    mapanare_agent_destroy(child);
    free(child);
    mapanare_agent_destroy(parent);
    free(parent);

    if (ok) {
        printf("PASSED — As.6 callback invoked with structured reason\n");
        return 0;
    }
    return 1;
}
