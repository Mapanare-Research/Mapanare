/**
 * mapanare_internal.h — Shared internal helpers for Mapanare runtime modules.
 *
 * Contains utility functions and types used by multiple runtime .c files
 * (mapanare_io.c, mapanare_db.c, mapanare_html.c) to avoid code duplication.
 */

#ifndef MAPANARE_INTERNAL_H
#define MAPANARE_INTERNAL_H

#include "mapanare_core.h"
#include <stdlib.h>
#include <string.h>

/* -----------------------------------------------------------------------
 * mnstr_to_cstr — Convert MnString to a heap-allocated NUL-terminated C string.
 * Caller must free() the returned pointer.
 * ----------------------------------------------------------------------- */

static inline char *mnstr_to_cstr(MnString s) {
    /* v4.100.0: the data pointer is now always a valid pointer (the
     * tagged-pointer scheme has been replaced by a bit-field
     * ``is_heap`` inside MnString — see mapanare_core.h). ``len`` is
     * a 63-bit unsigned bitfield so it can't be negative; the old
     * ``if (len < 0) len = 0`` guard is dead, but NULL-data is still
     * a possible failure mode. */
    const char *raw = s.data;
    uint64_t len = s.len;
    char *buf = (char *)malloc((size_t)len + 1);
    if (!buf) return NULL;
    if (len > 0 && raw) memcpy(buf, raw, (size_t)len);
    buf[len] = '\0';
    return buf;
}

/* -----------------------------------------------------------------------
 * MnHandleTable — Simple fixed-size pointer table for opaque handles.
 * Used by mapanare_db.c and mapanare_html.c to track open resources.
 * ----------------------------------------------------------------------- */

#ifndef MN_MAX_HANDLES
#define MN_MAX_HANDLES 256
#endif

typedef struct {
    void *ptrs[MN_MAX_HANDLES];
} MnHandleTable;

static inline int64_t mn_handle_alloc(MnHandleTable *t, void *ptr) {
    for (int i = 0; i < MN_MAX_HANDLES; i++) {
        if (!t->ptrs[i]) {
            t->ptrs[i] = ptr;
            return (int64_t)i;
        }
    }
    return -1;
}

static inline void *mn_handle_get(MnHandleTable *t, int64_t id) {
    if (id < 0 || id >= MN_MAX_HANDLES) return NULL;
    return t->ptrs[id];
}

static inline void mn_handle_free(MnHandleTable *t, int64_t id) {
    if (id >= 0 && id < MN_MAX_HANDLES) t->ptrs[id] = NULL;
}

#endif /* MAPANARE_INTERNAL_H */
