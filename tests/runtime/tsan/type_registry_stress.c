/*
 * type_registry_stress.c — TSan regression test for v4.28.0 Phase 1.3.
 *
 * Before v4.28.0, ``mn_type_reg`` was a global hash table with no lock
 * (v4.26.0 panel: Viper H5). Concurrent
 * ``__mn_type_registry_put`` / ``__mn_type_registry_get_kind`` calls
 * produced torn writes: a reader could observe a half-initialised entry
 * mid-``memcpy``.
 *
 * This test spins up 4 writer threads and 4 reader threads against a
 * shared set of 50 function names, running 2000 ops each. Under TSan the
 * pre-fix code reports a race on ``mn_type_reg[i].kind`` / ``type_name``;
 * the post-fix code reports clean.
 *
 * Build:
 *   gcc -fsanitize=thread -g -O1 -I runtime/native \
 *       tests/runtime/tsan/type_registry_stress.c \
 *       runtime/native/mapanare_core.c \
 *       -o /tmp/tsan_typereg -lpthread -lm -ldl
 *
 * Run:
 *   /tmp/tsan_typereg
 *
 * Exit 0 + zero TSan reports = PASS.
 */

#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mapanare_core.h"

#define WRITERS 4
#define READERS 4
#define OPS_PER_THREAD 2000
#define UNIQUE_NAMES 50

static MnString make_literal(const char *s) {
    /* Build an MnString pointing at a static C literal. Low bit is 0
     * because the linker aligns .rodata, so ``mn_untag`` is a no-op. */
    MnString out;
    out.data = s;
    out.len = (int64_t)strlen(s);
    return out;
}

/* Pre-built literals so both threads hit the same hash buckets. */
static const char *kNames[UNIQUE_NAMES];
static const char *kKinds[UNIQUE_NAMES];
static const char *kTypeNames[UNIQUE_NAMES];

static void init_corpus(void) {
    static char name_buf[UNIQUE_NAMES][32];
    static char kind_buf[UNIQUE_NAMES][16];
    static char type_buf[UNIQUE_NAMES][32];
    for (int i = 0; i < UNIQUE_NAMES; i++) {
        snprintf(name_buf[i], sizeof(name_buf[i]), "fn_%03d", i);
        snprintf(kind_buf[i], sizeof(kind_buf[i]), "k%d", i);
        snprintf(type_buf[i], sizeof(type_buf[i]), "T_%03d", i);
        kNames[i] = name_buf[i];
        kKinds[i] = kind_buf[i];
        kTypeNames[i] = type_buf[i];
    }
}

static void *writer_thread(void *arg) {
    int64_t seed = (int64_t)(intptr_t)arg;
    for (int i = 0; i < OPS_PER_THREAD; i++) {
        int idx = (int)((seed * 1103515245 + i * 12345) % UNIQUE_NAMES);
        if (idx < 0) idx += UNIQUE_NAMES;
        __mn_type_registry_put(
            make_literal(kNames[idx]),
            make_literal(kKinds[idx]),
            make_literal(kTypeNames[idx]));
    }
    return NULL;
}

static void *reader_thread(void *arg) {
    int64_t seed = (int64_t)(intptr_t)arg;
    int64_t observed = 0;
    for (int i = 0; i < OPS_PER_THREAD; i++) {
        int idx = (int)((seed * 2654435761u + i * 7919) % UNIQUE_NAMES);
        if (idx < 0) idx += UNIQUE_NAMES;
        MnString kind = __mn_type_registry_get_kind(make_literal(kNames[idx]));
        /* ``__mn_type_registry_get_kind`` returns a freshly-allocated
         * MnString that the runtime manages. Just observe len so TSan
         * sees the read. */
        observed += kind.len;
    }
    return (void *)(intptr_t)observed;
}

int main(void) {
    init_corpus();
    __mn_type_registry_clear();

    pthread_t threads[WRITERS + READERS];
    for (int t = 0; t < WRITERS; t++) {
        pthread_create(&threads[t], NULL, writer_thread, (void *)(intptr_t)(t + 1));
    }
    for (int t = 0; t < READERS; t++) {
        pthread_create(&threads[WRITERS + t], NULL, reader_thread,
                       (void *)(intptr_t)(t + 100));
    }
    for (int t = 0; t < WRITERS + READERS; t++) {
        pthread_join(threads[t], NULL);
    }

    printf("type_registry_stress: %d writers + %d readers x %d ops, no TSan races\n",
           WRITERS, READERS, OPS_PER_THREAD);
    return 0;
}
