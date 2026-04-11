/*
 * signal_stress.c — TSan regression test for v4.28.0 Phase 1.1.
 *
 * Before v4.28.0, ``__mn_signal_set`` ran memcmp / dtor / memcpy on
 * ``signal->value`` OUTSIDE the signal mutex, racing any concurrent
 * ``__mn_signal_set`` on the same signal (v4.26.0 panel: Viper H5, Mamba H1).
 *
 * This test runs 4 writer threads that each perform 5000 set operations on a
 * single shared signal. Under ThreadSanitizer, the pre-fix code reports a
 * data race on the ``signal->value`` memory inside ``__mn_signal_set``; the
 * post-fix code reports clean.
 *
 * Scope note: the fix protects the WRITE side (the panel's specific
 * finding). The reader API ``__mn_signal_get`` still returns a raw pointer
 * to ``signal->value`` for caller dereference; a read-side race between
 * the caller's post-get dereference and a concurrent writer is a larger
 * API change (copy-on-read or get/release bracketing) tracked separately
 * and not in v4.28.0 scope. This test therefore stresses only the writer
 * path the fix covers.
 *
 * Build:
 *   gcc -fsanitize=thread -g -O1 \
 *       tests/runtime/tsan/signal_stress.c runtime/native/mapanare_core.c \
 *       -I runtime/native -o /tmp/tsan_signal \
 *       -lpthread -lm -ldl
 *
 * Run:
 *   /tmp/tsan_signal
 *
 * Exit 0 + zero TSan reports = PASS.
 */

#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* The runtime header exposes the signal API and also pulls in the rest of
 * the types the stress test does not care about. */
#include "mapanare_core.h"

#define STRESS_THREADS 4
#define STRESS_ITERATIONS 5000

static MnSignal *shared_signal = NULL;

static void *writer_thread(void *arg) {
    int64_t tid = (int64_t)(intptr_t)arg;
    for (int i = 0; i < STRESS_ITERATIONS; i++) {
        int64_t value = (tid << 32) | (int64_t)i;
        __mn_signal_set(shared_signal, &value);
    }
    return NULL;
}

int main(void) {
    /* Create a single Int-typed signal. ``__mn_signal_new`` takes an
     * initial pointer to the value and a size. */
    int64_t initial = 0;
    shared_signal = __mn_signal_new(&initial, (int64_t)sizeof(int64_t));
    if (shared_signal == NULL) {
        fprintf(stderr, "signal_stress: __mn_signal_new failed\n");
        return 1;
    }

    pthread_t threads[STRESS_THREADS];
    for (int t = 0; t < STRESS_THREADS; t++) {
        int rc = pthread_create(&threads[t], NULL, writer_thread, (void *)(intptr_t)t);
        if (rc != 0) {
            fprintf(stderr, "signal_stress: pthread_create[%d] failed: %d\n", t, rc);
            return 1;
        }
    }

    for (int t = 0; t < STRESS_THREADS; t++) {
        pthread_join(threads[t], NULL);
    }

    printf("signal_stress: %d writer threads x %d iters complete, no TSan races\n",
           STRESS_THREADS, STRESS_ITERATIONS);
    return 0;
}
