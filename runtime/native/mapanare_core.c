/**
 * mapanare_core.c — Core runtime implementation for Mapanare self-hosting.
 *
 * Provides string, list, file I/O, and memory operations that native-compiled
 * Mapanare programs link against.
 */

#include "mapanare_core.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -----------------------------------------------------------------------
 * Memory helpers
 * ----------------------------------------------------------------------- */

MN_EXPORT void *__mn_alloc(int64_t size) {
    void *ptr = calloc(1, (size_t)size);
    if (!ptr) {
        fprintf(stderr, "mapanare: out of memory (requested %lld bytes)\n",
                (long long)size);
        exit(1);
    }
    return ptr;
}

MN_EXPORT void *__mn_realloc(void *ptr, int64_t new_size) {
    void *p = realloc(ptr, (size_t)new_size);
    if (!p && new_size > 0) {
        fprintf(stderr, "mapanare: realloc failed (%lld bytes)\n",
                (long long)new_size);
        exit(1);
    }
    return p;
}

MN_EXPORT void __mn_free(void *ptr) {
    free(ptr);
}

/* -----------------------------------------------------------------------
 * Tag-bit helpers for heap vs constant string distinction.
 *
 * We use the lowest bit of the data pointer as a tag:
 *   0 = constant (points to .rodata or static global) — do NOT free
 *   1 = heap-allocated via __mn_alloc            — safe to free
 *
 * All calloc/malloc returns are at least 8-byte aligned, so the lowest
 * bit is always 0. We set it to 1 after allocation.
 * ----------------------------------------------------------------------- */

static inline const char *mn_tag_heap(const char *ptr) {
    return (const char *)((uintptr_t)ptr | 1);
}

static inline int mn_is_heap(const char *ptr) {
    return (int)((uintptr_t)ptr & 1);
}

static inline const char *mn_untag(const char *ptr) {
    return (const char *)((uintptr_t)ptr & ~(uintptr_t)1);
}

/* -----------------------------------------------------------------------
 * Arena Allocator
 * ----------------------------------------------------------------------- */

static MnArenaBlock *mn_arena_block_new(int64_t size) {
    MnArenaBlock *blk = (MnArenaBlock *)malloc(
        sizeof(MnArenaBlock) + (size_t)size);
    if (!blk) {
        fprintf(stderr, "mapanare: arena block alloc failed (%lld bytes)\n",
                (long long)size);
        exit(1);
    }
    blk->next = NULL;
    blk->size = size;
    blk->used = 0;
    memset(blk->data, 0, (size_t)size);
    return blk;
}

MN_EXPORT MnArena *mn_arena_create(int64_t block_size) {
    if (block_size <= 0) block_size = 8192;
    MnArena *arena = (MnArena *)malloc(sizeof(MnArena));
    if (!arena) {
        fprintf(stderr, "mapanare: arena create failed\n");
        exit(1);
    }
    arena->default_block_size = block_size;
    arena->head = mn_arena_block_new(block_size);
    return arena;
}

MN_EXPORT void *mn_arena_alloc(MnArena *arena, int64_t size) {
    if (size <= 0) return NULL;
    /* Align to 8 bytes */
    size = (size + 7) & ~(int64_t)7;

    MnArenaBlock *blk = arena->head;
    if (blk->used + size > blk->size) {
        /* Need a new block — at least big enough for this allocation */
        int64_t new_size = arena->default_block_size;
        if (size > new_size) new_size = size;
        MnArenaBlock *new_blk = mn_arena_block_new(new_size);
        new_blk->next = blk;
        arena->head = new_blk;
        blk = new_blk;
    }
    void *ptr = blk->data + blk->used;
    blk->used += size;
    return ptr;
}

MN_EXPORT void mn_arena_destroy(MnArena *arena) {
    if (!arena) return;
    MnArenaBlock *blk = arena->head;
    while (blk) {
        MnArenaBlock *next = blk->next;
        free(blk);
        blk = next;
    }
    free(arena);
}

/* -----------------------------------------------------------------------
 * MnString
 * ----------------------------------------------------------------------- */

MN_EXPORT MnString __mn_str_from_cstr(const char *cstr) {
    MnString s;
    if (!cstr) {
        s.data = "";
        s.len = 0;
        return s;
    }
    int64_t len = (int64_t)strlen(cstr);
    char *buf = (char *)__mn_alloc(len + 1);
    memcpy(buf, cstr, (size_t)len);
    buf[len] = '\0';
    s.data = mn_tag_heap(buf);
    s.len = len;
    return s;
}

MN_EXPORT MnString __mn_str_from_parts(const char *data, int64_t len) {
    MnString s;
    if (!data || len <= 0) {
        s.data = "";
        s.len = 0;
        return s;
    }
    char *buf = (char *)__mn_alloc(len + 1);
    memcpy(buf, data, (size_t)len);
    buf[len] = '\0';
    s.data = mn_tag_heap(buf);
    s.len = len;
    return s;
}

MN_EXPORT MnString __mn_str_empty(void) {
    MnString s;
    s.data = "";
    s.len = 0;
    return s;
}

MN_EXPORT MnString __mn_str_concat(MnString a, MnString b) {
    const char *a_data = mn_untag(a.data);
    const char *b_data = mn_untag(b.data);
    int64_t total = a.len + b.len;
    if (total == 0) {
        return __mn_str_empty();
    }
    char *buf = (char *)__mn_alloc(total + 1);
    if (a.len > 0) memcpy(buf, a_data, (size_t)a.len);
    if (b.len > 0) memcpy(buf + a.len, b_data, (size_t)b.len);
    buf[total] = '\0';
    MnString s;
    s.data = mn_tag_heap(buf);
    s.len = total;
    return s;
}

MN_EXPORT MnString __mn_str_char_at(MnString s, int64_t i) {
    if (i < 0 || i >= s.len) {
        return __mn_str_empty();
    }
    const char *data = mn_untag(s.data);
    return __mn_str_from_parts(data + i, 1);
}

MN_EXPORT int64_t __mn_str_byte_at(MnString s, int64_t i) {
    if (i < 0 || i >= s.len) {
        return -1;
    }
    const char *data = mn_untag(s.data);
    return (int64_t)(unsigned char)data[i];
}

MN_EXPORT int64_t __mn_str_len(MnString s) {
    return s.len;
}

MN_EXPORT int64_t __mn_str_eq(MnString a, MnString b) {
    if (a.len != b.len) return 0;
    if (a.len == 0) return 1;
    return memcmp(mn_untag(a.data), mn_untag(b.data), (size_t)a.len) == 0 ? 1 : 0;
}

MN_EXPORT int64_t __mn_str_cmp(MnString a, MnString b) {
    const char *a_data = mn_untag(a.data);
    const char *b_data = mn_untag(b.data);
    int64_t min_len = a.len < b.len ? a.len : b.len;
    if (min_len > 0) {
        int cmp = memcmp(a_data, b_data, (size_t)min_len);
        if (cmp != 0) return (int64_t)cmp;
    }
    if (a.len < b.len) return -1;
    if (a.len > b.len) return 1;
    return 0;
}

MN_EXPORT MnString __mn_str_substr(MnString s, int64_t start, int64_t end) {
    if (start < 0) start = 0;
    if (end > s.len) end = s.len;
    if (start >= end) return __mn_str_empty();
    const char *data = mn_untag(s.data);
    return __mn_str_from_parts(data + start, end - start);
}

MN_EXPORT int64_t __mn_str_starts_with(MnString s, MnString prefix) {
    if (prefix.len > s.len) return 0;
    if (prefix.len == 0) return 1;
    return memcmp(mn_untag(s.data), mn_untag(prefix.data), (size_t)prefix.len) == 0 ? 1 : 0;
}

MN_EXPORT int64_t __mn_str_ends_with(MnString s, MnString suffix) {
    if (suffix.len > s.len) return 0;
    if (suffix.len == 0) return 1;
    const char *s_data = mn_untag(s.data);
    const char *suf_data = mn_untag(suffix.data);
    return memcmp(s_data + s.len - suffix.len, suf_data,
                  (size_t)suffix.len) == 0 ? 1 : 0;
}

MN_EXPORT int64_t __mn_str_find(MnString haystack, MnString needle) {
    if (needle.len == 0) return 0;
    if (needle.len > haystack.len) return -1;
    const char *h_data = mn_untag(haystack.data);
    const char *n_data = mn_untag(needle.data);
    for (int64_t i = 0; i <= haystack.len - needle.len; i++) {
        if (memcmp(h_data + i, n_data, (size_t)needle.len) == 0) {
            return i;
        }
    }
    return -1;
}

MN_EXPORT MnString __mn_str_from_int(int64_t value) {
    char buf[32];
    int n = snprintf(buf, sizeof(buf), "%lld", (long long)value);
    return __mn_str_from_parts(buf, (int64_t)n);
}

MN_EXPORT MnString __mn_str_from_float(double value) {
    char buf[64];
    int n = snprintf(buf, sizeof(buf), "%g", value);
    return __mn_str_from_parts(buf, (int64_t)n);
}

MN_EXPORT void __mn_str_free(MnString s) {
    if (s.data && mn_is_heap(s.data)) {
        __mn_free((void *)mn_untag(s.data));
    }
}

MN_EXPORT void __mn_str_print(MnString s) {
    if (s.len > 0) {
        fwrite(mn_untag(s.data), 1, (size_t)s.len, stdout);
    }
}

MN_EXPORT void __mn_str_println(MnString s) {
    __mn_str_print(s);
    fputc('\n', stdout);
}

MN_EXPORT void __mn_str_eprintln(MnString s) {
    if (s.len > 0) {
        fwrite(mn_untag(s.data), 1, (size_t)s.len, stderr);
    }
    fputc('\n', stderr);
}

/* -----------------------------------------------------------------------
 * MnList
 * ----------------------------------------------------------------------- */

#define MN_LIST_INITIAL_CAP 8

MN_EXPORT MnList __mn_list_new(int64_t elem_size) {
    MnList list;
    list.elem_size = elem_size;
    list.len = 0;
    list.cap = MN_LIST_INITIAL_CAP;
    list.data = (char *)__mn_alloc(list.cap * elem_size);
    return list;
}

static void mn_list_grow(MnList *list) {
    int64_t new_cap = list->cap * 2;
    list->data = (char *)__mn_realloc(list->data, new_cap * list->elem_size);
    list->cap = new_cap;
}

MN_EXPORT void __mn_list_push(MnList *list, const void *elem_ptr) {
    if (list->len >= list->cap) {
        mn_list_grow(list);
    }
    memcpy(list->data + list->len * list->elem_size,
           elem_ptr, (size_t)list->elem_size);
    list->len++;
}

MN_EXPORT void *__mn_list_get(MnList *list, int64_t i) {
    if (i < 0 || i >= list->len) return NULL;
    return list->data + i * list->elem_size;
}

MN_EXPORT void __mn_list_set(MnList *list, int64_t i, const void *elem_ptr) {
    if (i < 0 || i >= list->len) return;
    memcpy(list->data + i * list->elem_size,
           elem_ptr, (size_t)list->elem_size);
}

MN_EXPORT int64_t __mn_list_len(MnList *list) {
    return list->len;
}

MN_EXPORT int64_t __mn_list_pop(MnList *list, void *out_ptr) {
    if (list->len <= 0) return -1;
    list->len--;
    memcpy(out_ptr, list->data + list->len * list->elem_size,
           (size_t)list->elem_size);
    return 0;
}

MN_EXPORT void __mn_list_clear(MnList *list) {
    list->len = 0;
}

MN_EXPORT void __mn_list_free(MnList *list) {
    if (list->data) {
        __mn_free(list->data);
        list->data = NULL;
    }
    list->len = 0;
    list->cap = 0;
}

/* -----------------------------------------------------------------------
 * Convenience: MnList of MnString
 * ----------------------------------------------------------------------- */

MN_EXPORT void __mn_list_free_strings(MnList *list) {
    if (!list || !list->data) return;
    /* Free each contained MnString before freeing the list buffer. */
    for (int64_t i = 0; i < list->len; i++) {
        MnString *sp = (MnString *)(list->data + i * list->elem_size);
        __mn_str_free(*sp);
    }
    __mn_list_free(list);
}

MN_EXPORT MnList __mn_list_str_new(void) {
    return __mn_list_new(sizeof(MnString));
}

MN_EXPORT void __mn_list_str_push(MnList *list, MnString s) {
    __mn_list_push(list, &s);
}

MN_EXPORT MnString __mn_list_str_get(MnList *list, int64_t i) {
    void *ptr = __mn_list_get(list, i);
    if (!ptr) return __mn_str_empty();
    MnString s;
    memcpy(&s, ptr, sizeof(MnString));
    return s;
}

/* -----------------------------------------------------------------------
 * File I/O
 * ----------------------------------------------------------------------- */

MN_EXPORT MnString __mn_file_read(MnString path, int64_t *ok) {
    *ok = 0;
    /* Null-terminate the path for fopen */
    const char *path_data = mn_untag(path.data);
    char *cpath = (char *)__mn_alloc(path.len + 1);
    memcpy(cpath, path_data, (size_t)path.len);
    cpath[path.len] = '\0';

    FILE *f = fopen(cpath, "rb");
    __mn_free(cpath);
    if (!f) {
        return __mn_str_empty();
    }

    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (size <= 0) {
        fclose(f);
        *ok = 1;
        return __mn_str_empty();
    }

    char *buf = (char *)__mn_alloc(size + 1);
    size_t read = fread(buf, 1, (size_t)size, f);
    fclose(f);
    buf[read] = '\0';

    MnString s;
    s.data = mn_tag_heap(buf);
    s.len = (int64_t)read;
    *ok = 1;
    return s;
}

MN_EXPORT int64_t __mn_file_write(MnString path, MnString content) {
    const char *path_data = mn_untag(path.data);
    char *cpath = (char *)__mn_alloc(path.len + 1);
    memcpy(cpath, path_data, (size_t)path.len);
    cpath[path.len] = '\0';

    FILE *f = fopen(cpath, "wb");
    __mn_free(cpath);
    if (!f) return -1;

    if (content.len > 0) {
        size_t written = fwrite(mn_untag(content.data), 1, (size_t)content.len, f);
        fclose(f);
        return written == (size_t)content.len ? 0 : -1;
    }
    fclose(f);
    return 0;
}

/* -----------------------------------------------------------------------
 * Process
 * ----------------------------------------------------------------------- */

/* -----------------------------------------------------------------------
 * Agent-Scoped Arenas
 * ----------------------------------------------------------------------- */

MN_EXPORT MnArena *mn_agent_arena_create(void) {
    /* Agents get a larger default block (64KB) since they may run longer */
    return mn_arena_create(65536);
}

MN_EXPORT void mn_agent_arena_destroy(MnArena *arena) {
    mn_arena_destroy(arena);
}

/* -----------------------------------------------------------------------
 * Process
 * ----------------------------------------------------------------------- */

MN_EXPORT void __mn_exit(int64_t code) {
    exit((int)code);
}

MN_EXPORT void __mn_panic(MnString message) {
    fprintf(stderr, "mapanare panic: ");
    if (message.len > 0) {
        fwrite(mn_untag(message.data), 1, (size_t)message.len, stderr);
    }
    fputc('\n', stderr);
    exit(1);
}
