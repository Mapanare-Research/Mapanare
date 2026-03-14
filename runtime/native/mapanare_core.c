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

MN_EXPORT int64_t __mn_str_contains(MnString haystack, MnString needle) {
    return __mn_str_find(haystack, needle) >= 0 ? 1 : 0;
}

MN_EXPORT MnList __mn_str_split(MnString s, MnString delim) {
    MnList result = __mn_list_str_new();
    const char *s_data = mn_untag(s.data);

    if (delim.len == 0) {
        /* Split into individual characters. */
        for (int64_t i = 0; i < s.len; i++) {
            MnString ch = __mn_str_from_parts(s_data + i, 1);
            __mn_list_str_push(&result, ch);
        }
        return result;
    }

    const char *d_data = mn_untag(delim.data);
    int64_t start = 0;
    for (int64_t i = 0; i <= s.len - delim.len; i++) {
        if (memcmp(s_data + i, d_data, (size_t)delim.len) == 0) {
            MnString part = __mn_str_from_parts(s_data + start, i - start);
            __mn_list_str_push(&result, part);
            i += delim.len - 1; /* -1 because the loop increments */
            start = i + 1;
        }
    }
    /* Push the remainder. */
    MnString tail = __mn_str_from_parts(s_data + start, s.len - start);
    __mn_list_str_push(&result, tail);
    return result;
}

MN_EXPORT MnString __mn_str_trim(MnString s) {
    const char *data = mn_untag(s.data);
    int64_t start = 0;
    int64_t end = s.len;
    while (start < end && (data[start] == ' ' || data[start] == '\t' ||
           data[start] == '\n' || data[start] == '\r')) {
        start++;
    }
    while (end > start && (data[end - 1] == ' ' || data[end - 1] == '\t' ||
           data[end - 1] == '\n' || data[end - 1] == '\r')) {
        end--;
    }
    if (start == 0 && end == s.len) {
        return __mn_str_from_parts(data, s.len);
    }
    return __mn_str_from_parts(data + start, end - start);
}

MN_EXPORT MnString __mn_str_trim_start(MnString s) {
    const char *data = mn_untag(s.data);
    int64_t start = 0;
    while (start < s.len && (data[start] == ' ' || data[start] == '\t' ||
           data[start] == '\n' || data[start] == '\r')) {
        start++;
    }
    if (start == 0) return __mn_str_from_parts(data, s.len);
    return __mn_str_from_parts(data + start, s.len - start);
}

MN_EXPORT MnString __mn_str_trim_end(MnString s) {
    const char *data = mn_untag(s.data);
    int64_t end = s.len;
    while (end > 0 && (data[end - 1] == ' ' || data[end - 1] == '\t' ||
           data[end - 1] == '\n' || data[end - 1] == '\r')) {
        end--;
    }
    if (end == s.len) return __mn_str_from_parts(data, s.len);
    return __mn_str_from_parts(data, end);
}

MN_EXPORT MnString __mn_str_to_upper(MnString s) {
    if (s.len == 0) return __mn_str_empty();
    const char *data = mn_untag(s.data);
    char *buf = (char *)__mn_alloc(s.len + 1);
    for (int64_t i = 0; i < s.len; i++) {
        char c = data[i];
        buf[i] = (c >= 'a' && c <= 'z') ? (char)(c - 32) : c;
    }
    buf[s.len] = '\0';
    MnString r;
    r.data = mn_tag_heap(buf);
    r.len = s.len;
    return r;
}

MN_EXPORT MnString __mn_str_to_lower(MnString s) {
    if (s.len == 0) return __mn_str_empty();
    const char *data = mn_untag(s.data);
    char *buf = (char *)__mn_alloc(s.len + 1);
    for (int64_t i = 0; i < s.len; i++) {
        char c = data[i];
        buf[i] = (c >= 'A' && c <= 'Z') ? (char)(c + 32) : c;
    }
    buf[s.len] = '\0';
    MnString r;
    r.data = mn_tag_heap(buf);
    r.len = s.len;
    return r;
}

MN_EXPORT MnString __mn_str_replace(MnString s, MnString old_s, MnString new_s) {
    if (old_s.len == 0 || s.len == 0) {
        return __mn_str_from_parts(mn_untag(s.data), s.len);
    }

    const char *s_data = mn_untag(s.data);
    const char *old_data = mn_untag(old_s.data);
    const char *new_data = mn_untag(new_s.data);

    /* Count occurrences to pre-allocate. */
    int64_t count = 0;
    for (int64_t i = 0; i <= s.len - old_s.len; i++) {
        if (memcmp(s_data + i, old_data, (size_t)old_s.len) == 0) {
            count++;
            i += old_s.len - 1;
        }
    }

    if (count == 0) {
        return __mn_str_from_parts(s_data, s.len);
    }

    int64_t new_len = s.len + count * (new_s.len - old_s.len);
    char *buf = (char *)__mn_alloc(new_len + 1);
    int64_t out = 0;
    int64_t i = 0;
    while (i < s.len) {
        if (i <= s.len - old_s.len &&
            memcmp(s_data + i, old_data, (size_t)old_s.len) == 0) {
            if (new_s.len > 0) {
                memcpy(buf + out, new_data, (size_t)new_s.len);
            }
            out += new_s.len;
            i += old_s.len;
        } else {
            buf[out++] = s_data[i++];
        }
    }
    buf[new_len] = '\0';

    MnString r;
    r.data = mn_tag_heap(buf);
    r.len = new_len;
    return r;
}

MN_EXPORT MnString __mn_str_from_bool(int64_t value) {
    return value ? __mn_str_from_cstr("true") : __mn_str_from_cstr("false");
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

MN_EXPORT MnList __mn_list_concat(MnList *a, MnList *b) {
    int64_t es = a->elem_size;
    MnList result = __mn_list_new(es);
    int64_t total = a->len + b->len;
    if (total > result.cap) {
        result.cap = total;
        result.data = (char *)__mn_realloc(result.data, result.cap * es);
    }
    if (a->len > 0) {
        memcpy(result.data, a->data, (size_t)(a->len * es));
    }
    if (b->len > 0) {
        memcpy(result.data + a->len * es, b->data, (size_t)(b->len * es));
    }
    result.len = total;
    return result;
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
 * MnMap — Robin Hood open-addressing hash table
 * ----------------------------------------------------------------------- */

#define MN_MAP_INITIAL_CAP 16
#define MN_MAP_LOAD_FACTOR_NUM 3
#define MN_MAP_LOAD_FACTOR_DEN 4  /* 0.75 */

/* Bucket status bytes */
#define MN_BUCKET_EMPTY     0
#define MN_BUCKET_OCCUPIED  1
#define MN_BUCKET_TOMBSTONE 2

struct MnMap {
    char    *buckets;     /* Array of (status:1 + psl:1 + key:key_size + val:val_size) */
    int64_t  len;         /* Live entry count */
    int64_t  cap;         /* Number of buckets (power of 2) */
    int64_t  key_size;
    int64_t  val_size;
    int64_t  bucket_size; /* 2 + key_size + val_size (status + psl + key + val) */
    int64_t  key_type;    /* MN_MAP_KEY_INT / STR / FLOAT */
};

struct MnMapIter {
    MnMap  *map;
    int64_t index;
};

/* --- Hash functions (FNV-1a) --- */

MN_EXPORT uint64_t __mn_hash_int(const void *key) {
    int64_t v = *(const int64_t *)key;
    /* Splitmix64-style finalizer */
    uint64_t x = (uint64_t)v;
    x ^= x >> 30;
    x *= 0xbf58476d1ce4e5b9ULL;
    x ^= x >> 27;
    x *= 0x94d049bb133111ebULL;
    x ^= x >> 31;
    return x;
}

MN_EXPORT uint64_t __mn_hash_str(const void *key) {
    const MnString *s = (const MnString *)key;
    const char *data = mn_untag(s->data);
    int64_t len = s->len;
    /* FNV-1a */
    uint64_t h = 14695981039346656037ULL;
    for (int64_t i = 0; i < len; i++) {
        h ^= (uint64_t)(unsigned char)data[i];
        h *= 1099511628211ULL;
    }
    return h;
}

MN_EXPORT uint64_t __mn_hash_float(const void *key) {
    double v = *(const double *)key;
    /* Handle -0.0 == 0.0 */
    if (v == 0.0) v = 0.0;
    uint64_t bits;
    memcpy(&bits, &v, sizeof(bits));
    /* Splitmix64-style finalizer */
    bits ^= bits >> 30;
    bits *= 0xbf58476d1ce4e5b9ULL;
    bits ^= bits >> 27;
    bits *= 0x94d049bb133111ebULL;
    bits ^= bits >> 31;
    return bits;
}

/* --- Internal equality functions --- */

static int64_t mn_eq_int(const void *a, const void *b) {
    return *(const int64_t *)a == *(const int64_t *)b ? 1 : 0;
}

static int64_t mn_eq_str(const void *a, const void *b) {
    return __mn_str_eq(*(const MnString *)a, *(const MnString *)b);
}

static int64_t mn_eq_float(const void *a, const void *b) {
    return *(const double *)a == *(const double *)b ? 1 : 0;
}

/* --- Internal helpers --- */

typedef uint64_t (*mn_hash_fn)(const void *);
typedef int64_t  (*mn_eq_fn)(const void *, const void *);

static mn_hash_fn mn_map_hash_fn(int64_t key_type) {
    switch (key_type) {
        case MN_MAP_KEY_STR:   return __mn_hash_str;
        case MN_MAP_KEY_FLOAT: return __mn_hash_float;
        default:               return __mn_hash_int;
    }
}

static mn_eq_fn mn_map_eq_fn(int64_t key_type) {
    switch (key_type) {
        case MN_MAP_KEY_STR:   return mn_eq_str;
        case MN_MAP_KEY_FLOAT: return mn_eq_float;
        default:               return mn_eq_int;
    }
}

static inline char *mn_bucket_at(MnMap *map, int64_t i) {
    return map->buckets + i * map->bucket_size;
}

static inline uint8_t mn_bucket_status(const char *bucket) {
    return (uint8_t)bucket[0];
}

static inline uint8_t mn_bucket_psl(const char *bucket) {
    return (uint8_t)bucket[1];
}

static inline void *mn_bucket_key(char *bucket) {
    return bucket + 2;
}

static inline void *mn_bucket_val(char *bucket, int64_t key_size) {
    return bucket + 2 + key_size;
}

static void mn_map_grow(MnMap *map);

MN_EXPORT MnMap *__mn_map_new(int64_t key_size, int64_t val_size, int64_t key_type) {
    MnMap *map = (MnMap *)__mn_alloc(sizeof(MnMap));
    map->key_size = key_size;
    map->val_size = val_size;
    map->key_type = key_type;
    map->bucket_size = 2 + key_size + val_size;  /* status + psl + key + val */
    map->len = 0;
    map->cap = MN_MAP_INITIAL_CAP;
    map->buckets = (char *)__mn_alloc(map->cap * map->bucket_size);
    /* calloc zeros → all status bytes are MN_BUCKET_EMPTY (0) */
    return map;
}

MN_EXPORT void __mn_map_set(MnMap *map, const void *key, const void *val) {
    /* Grow if load factor exceeded */
    if (map->len * MN_MAP_LOAD_FACTOR_DEN >= map->cap * MN_MAP_LOAD_FACTOR_NUM) {
        mn_map_grow(map);
    }

    mn_hash_fn hash = mn_map_hash_fn(map->key_type);
    mn_eq_fn   eq   = mn_map_eq_fn(map->key_type);
    uint64_t h = hash(key);
    int64_t mask = map->cap - 1;
    int64_t idx = (int64_t)(h & (uint64_t)mask);
    uint8_t psl = 0;

    /* Copy key/val into temp buffer for potential swaps */
    char *temp = (char *)__mn_alloc(map->key_size + map->val_size);
    memcpy(temp, key, (size_t)map->key_size);
    memcpy(temp + map->key_size, val, (size_t)map->val_size);

    for (;;) {
        char *bucket = mn_bucket_at(map, idx);
        uint8_t status = mn_bucket_status(bucket);

        if (status == MN_BUCKET_EMPTY || status == MN_BUCKET_TOMBSTONE) {
            /* Insert here */
            bucket[0] = MN_BUCKET_OCCUPIED;
            bucket[1] = (char)psl;
            memcpy(mn_bucket_key(bucket), temp, (size_t)map->key_size);
            memcpy(mn_bucket_val(bucket, map->key_size),
                   temp + map->key_size, (size_t)map->val_size);
            map->len++;
            __mn_free(temp);
            return;
        }

        /* Check if key already exists → update value */
        if (status == MN_BUCKET_OCCUPIED && eq(mn_bucket_key(bucket), temp)) {
            memcpy(mn_bucket_val(bucket, map->key_size),
                   temp + map->key_size, (size_t)map->val_size);
            __mn_free(temp);
            return;
        }

        /* Robin Hood: if our PSL > existing PSL, swap and continue */
        if (status == MN_BUCKET_OCCUPIED && psl > mn_bucket_psl(bucket)) {
            /* Swap current entry with bucket contents */
            uint8_t old_psl = mn_bucket_psl(bucket);
            char *old_key = mn_bucket_key(bucket);
            char *old_val = mn_bucket_val(bucket, map->key_size);

            /* Save old bucket data */
            char *swap = (char *)__mn_alloc(map->key_size + map->val_size);
            memcpy(swap, old_key, (size_t)map->key_size);
            memcpy(swap + map->key_size, old_val, (size_t)map->val_size);

            /* Write new data into bucket */
            bucket[1] = (char)psl;
            memcpy(old_key, temp, (size_t)map->key_size);
            memcpy(old_val, temp + map->key_size, (size_t)map->val_size);

            /* Continue inserting displaced entry */
            memcpy(temp, swap, (size_t)(map->key_size + map->val_size));
            psl = old_psl;
            __mn_free(swap);
        }

        psl++;
        idx = (idx + 1) & mask;
    }
}

MN_EXPORT void *__mn_map_get(MnMap *map, const void *key) {
    mn_hash_fn hash = mn_map_hash_fn(map->key_type);
    mn_eq_fn   eq   = mn_map_eq_fn(map->key_type);
    uint64_t h = hash(key);
    int64_t mask = map->cap - 1;
    int64_t idx = (int64_t)(h & (uint64_t)mask);
    uint8_t psl = 0;

    for (;;) {
        char *bucket = mn_bucket_at(map, idx);
        uint8_t status = mn_bucket_status(bucket);

        if (status == MN_BUCKET_EMPTY) return NULL;

        if (status == MN_BUCKET_OCCUPIED) {
            if (psl > mn_bucket_psl(bucket)) return NULL;  /* Robin Hood early exit */
            if (eq(mn_bucket_key(bucket), key)) {
                return mn_bucket_val(bucket, map->key_size);
            }
        }

        psl++;
        idx = (idx + 1) & mask;
    }
}

MN_EXPORT int64_t __mn_map_del(MnMap *map, const void *key) {
    mn_hash_fn hash = mn_map_hash_fn(map->key_type);
    mn_eq_fn   eq   = mn_map_eq_fn(map->key_type);
    uint64_t h = hash(key);
    int64_t mask = map->cap - 1;
    int64_t idx = (int64_t)(h & (uint64_t)mask);
    uint8_t psl = 0;

    for (;;) {
        char *bucket = mn_bucket_at(map, idx);
        uint8_t status = mn_bucket_status(bucket);

        if (status == MN_BUCKET_EMPTY) return 0;

        if (status == MN_BUCKET_OCCUPIED) {
            if (psl > mn_bucket_psl(bucket)) return 0;
            if (eq(mn_bucket_key(bucket), key)) {
                bucket[0] = MN_BUCKET_TOMBSTONE;
                map->len--;
                return 1;
            }
        }

        psl++;
        idx = (idx + 1) & mask;
    }
}

MN_EXPORT int64_t __mn_map_len(MnMap *map) {
    return map->len;
}

MN_EXPORT int64_t __mn_map_contains(MnMap *map, const void *key) {
    return __mn_map_get(map, key) != NULL ? 1 : 0;
}

static void mn_map_grow(MnMap *map) {
    int64_t old_cap = map->cap;
    char *old_buckets = map->buckets;
    int64_t old_bucket_size = map->bucket_size;

    map->cap = old_cap * 2;
    map->buckets = (char *)__mn_alloc(map->cap * map->bucket_size);
    map->len = 0;

    /* Re-insert all occupied entries */
    for (int64_t i = 0; i < old_cap; i++) {
        char *bucket = old_buckets + i * old_bucket_size;
        if (mn_bucket_status(bucket) == MN_BUCKET_OCCUPIED) {
            __mn_map_set(map, mn_bucket_key(bucket),
                         mn_bucket_val(bucket, map->key_size));
        }
    }
    __mn_free(old_buckets);
}

/* --- Iterator --- */

MN_EXPORT MnMapIter *__mn_map_iter_new(MnMap *map) {
    MnMapIter *iter = (MnMapIter *)__mn_alloc(sizeof(MnMapIter));
    iter->map = map;
    iter->index = 0;
    return iter;
}

MN_EXPORT int64_t __mn_map_iter_next(MnMapIter *iter, void **key_out, void **val_out) {
    MnMap *map = iter->map;
    while (iter->index < map->cap) {
        char *bucket = mn_bucket_at(map, iter->index);
        iter->index++;
        if (mn_bucket_status(bucket) == MN_BUCKET_OCCUPIED) {
            *key_out = mn_bucket_key(bucket);
            *val_out = mn_bucket_val(bucket, map->key_size);
            return 1;
        }
    }
    return 0;
}

MN_EXPORT void __mn_map_iter_free(MnMapIter *iter) {
    __mn_free(iter);
}

MN_EXPORT void __mn_map_free(MnMap *map) {
    if (map) {
        if (map->buckets) __mn_free(map->buckets);
        __mn_free(map);
    }
}

/* -----------------------------------------------------------------------
 * MnSignal — reactive signal with dependency graph
 * ----------------------------------------------------------------------- */

#define MN_SIGNAL_INITIAL_SUBS  4
#define MN_SIGNAL_MAX_PENDING  256
#define MN_SIGNAL_MAX_CB        8

/** Internal callback entry. */
typedef struct {
    MnSignalCallback fn;
    void            *user_data;
} MnSignalCbEntry;

struct MnSignal {
    void       *value;         /* Heap-allocated value buffer */
    int64_t     val_size;      /* Size of value in bytes */

    /* Subscriber list (dependent signals notified on change) */
    MnSignal  **subscribers;
    int64_t     sub_len;
    int64_t     sub_cap;

    /* Callback list (user-registered on_change callbacks) */
    MnSignalCbEntry *callbacks;
    int64_t          cb_len;
    int64_t          cb_cap;

    /* Computed signal support */
    MnSignalComputeFn  compute_fn;
    void              *compute_user_data;
    MnSignal         **dependencies;   /* Signals this computed signal reads */
    int64_t            dep_len;
    int64_t            dirty;          /* 1 if needs recomputation */
};

/* --- Batching state (global) --- */

static int64_t    mn_signal_batch_depth = 0;
static MnSignal  *mn_signal_batch_pending[MN_SIGNAL_MAX_PENDING];
static int64_t    mn_signal_batch_pending_len = 0;

/* --- Dependency tracking context (for auto-tracking) --- */

static MnSignal *mn_signal_tracking_context = NULL;

/* --- Forward declarations --- */

static void mn_signal_propagate(MnSignal *signal);
static void mn_signal_recompute(MnSignal *signal);

/* --- Creation --- */

MN_EXPORT MnSignal *__mn_signal_new(const void *initial_value, int64_t val_size) {
    MnSignal *sig = (MnSignal *)__mn_alloc(sizeof(MnSignal));
    sig->val_size = val_size;
    sig->value = __mn_alloc(val_size > 0 ? val_size : 8);
    if (initial_value && val_size > 0) {
        memcpy(sig->value, initial_value, (size_t)val_size);
    }

    sig->subscribers = (MnSignal **)__mn_alloc(
        MN_SIGNAL_INITIAL_SUBS * (int64_t)sizeof(MnSignal *));
    sig->sub_len = 0;
    sig->sub_cap = MN_SIGNAL_INITIAL_SUBS;

    sig->callbacks = (MnSignalCbEntry *)__mn_alloc(
        MN_SIGNAL_MAX_CB * (int64_t)sizeof(MnSignalCbEntry));
    sig->cb_len = 0;
    sig->cb_cap = MN_SIGNAL_MAX_CB;

    sig->compute_fn = NULL;
    sig->compute_user_data = NULL;
    sig->dependencies = NULL;
    sig->dep_len = 0;
    sig->dirty = 0;
    return sig;
}

/* --- Get --- */

MN_EXPORT void *__mn_signal_get(MnSignal *signal) {
    /* Auto-register dependency if inside a computed signal evaluation */
    if (mn_signal_tracking_context != NULL && mn_signal_tracking_context != signal) {
        __mn_signal_subscribe(signal, mn_signal_tracking_context);
    }

    /* Recompute if dirty (lazy evaluation for computed signals) */
    if (signal->compute_fn != NULL && signal->dirty) {
        mn_signal_recompute(signal);
    }

    return signal->value;
}

/* --- Set --- */

MN_EXPORT void __mn_signal_set(MnSignal *signal, const void *value) {
    /* Don't allow setting computed signals */
    if (signal->compute_fn != NULL) return;

    /* Check if value actually changed (memcmp) */
    if (signal->val_size > 0 && memcmp(signal->value, value, (size_t)signal->val_size) == 0) {
        return;  /* No change, skip propagation */
    }

    memcpy(signal->value, value, (size_t)signal->val_size);

    if (mn_signal_batch_depth > 0) {
        /* Defer propagation: add to pending list */
        if (mn_signal_batch_pending_len < MN_SIGNAL_MAX_PENDING) {
            /* Avoid duplicates */
            int64_t found = 0;
            for (int64_t i = 0; i < mn_signal_batch_pending_len; i++) {
                if (mn_signal_batch_pending[i] == signal) { found = 1; break; }
            }
            if (!found) {
                mn_signal_batch_pending[mn_signal_batch_pending_len++] = signal;
            }
        }
    } else {
        mn_signal_propagate(signal);
    }
}

/* --- Computed signals --- */

MN_EXPORT MnSignal *__mn_signal_computed(
    MnSignalComputeFn compute_fn,
    void *user_data,
    MnSignal **deps,
    int64_t n_deps,
    int64_t val_size
) {
    MnSignal *sig = __mn_signal_new(NULL, val_size);
    sig->compute_fn = compute_fn;
    sig->compute_user_data = user_data;
    sig->dirty = 1;

    /* Store dependencies and subscribe to each */
    if (n_deps > 0 && deps != NULL) {
        sig->dependencies = (MnSignal **)__mn_alloc(n_deps * (int64_t)sizeof(MnSignal *));
        sig->dep_len = n_deps;
        for (int64_t i = 0; i < n_deps; i++) {
            sig->dependencies[i] = deps[i];
            __mn_signal_subscribe(deps[i], sig);
        }
    }

    /* Initial evaluation */
    mn_signal_recompute(sig);
    return sig;
}

static void mn_signal_recompute(MnSignal *signal) {
    if (signal->compute_fn == NULL) return;

    /* Push tracking context */
    MnSignal *prev_context = mn_signal_tracking_context;
    mn_signal_tracking_context = signal;

    signal->compute_fn(signal->value, signal->compute_user_data);
    signal->dirty = 0;

    /* Pop tracking context */
    mn_signal_tracking_context = prev_context;
}

/* --- Subscribe / Unsubscribe --- */

MN_EXPORT void __mn_signal_subscribe(MnSignal *signal, MnSignal *subscriber) {
    /* Check for duplicates */
    for (int64_t i = 0; i < signal->sub_len; i++) {
        if (signal->subscribers[i] == subscriber) return;
    }
    /* Grow if needed */
    if (signal->sub_len >= signal->sub_cap) {
        int64_t new_cap = signal->sub_cap * 2;
        signal->subscribers = (MnSignal **)__mn_realloc(
            signal->subscribers, new_cap * (int64_t)sizeof(MnSignal *));
        signal->sub_cap = new_cap;
    }
    signal->subscribers[signal->sub_len++] = subscriber;
}

MN_EXPORT void __mn_signal_unsubscribe(MnSignal *signal, MnSignal *subscriber) {
    for (int64_t i = 0; i < signal->sub_len; i++) {
        if (signal->subscribers[i] == subscriber) {
            /* Shift remaining elements */
            for (int64_t j = i; j < signal->sub_len - 1; j++) {
                signal->subscribers[j] = signal->subscribers[j + 1];
            }
            signal->sub_len--;
            return;
        }
    }
}

/* --- Callbacks --- */

MN_EXPORT void __mn_signal_on_change(MnSignal *signal, MnSignalCallback cb, void *user_data) {
    if (signal->cb_len >= signal->cb_cap) return;  /* Silently ignore overflow */
    signal->callbacks[signal->cb_len].fn = cb;
    signal->callbacks[signal->cb_len].user_data = user_data;
    signal->cb_len++;
}

/* --- Propagation (topological, depth-first) --- */

static void mn_signal_propagate(MnSignal *signal) {
    /* 1. Mark all subscribers dirty */
    for (int64_t i = 0; i < signal->sub_len; i++) {
        signal->subscribers[i]->dirty = 1;
    }

    /* 2. Re-evaluate computed subscribers and propagate recursively.
     *    This is a depth-first topological traversal: each computed signal
     *    is recomputed before its own subscribers are notified. */
    for (int64_t i = 0; i < signal->sub_len; i++) {
        MnSignal *sub = signal->subscribers[i];
        if (sub->compute_fn != NULL && sub->dirty) {
            mn_signal_recompute(sub);
            mn_signal_propagate(sub);
        }
    }

    /* 3. Fire callbacks on this signal */
    for (int64_t i = 0; i < signal->cb_len; i++) {
        signal->callbacks[i].fn(signal->value, signal->callbacks[i].user_data);
    }
}

/* --- Batching --- */

MN_EXPORT void __mn_signal_batch_begin(void) {
    mn_signal_batch_depth++;
}

MN_EXPORT void __mn_signal_batch_end(void) {
    if (mn_signal_batch_depth <= 0) return;
    mn_signal_batch_depth--;
    if (mn_signal_batch_depth == 0) {
        /* Propagate all pending signals */
        int64_t count = mn_signal_batch_pending_len;
        mn_signal_batch_pending_len = 0;
        for (int64_t i = 0; i < count; i++) {
            mn_signal_propagate(mn_signal_batch_pending[i]);
        }
    }
}

/* --- Free --- */

MN_EXPORT void __mn_signal_free(MnSignal *signal) {
    if (!signal) return;
    /* Unsubscribe from dependencies */
    for (int64_t i = 0; i < signal->dep_len; i++) {
        __mn_signal_unsubscribe(signal->dependencies[i], signal);
    }
    if (signal->dependencies) __mn_free(signal->dependencies);
    if (signal->subscribers) __mn_free(signal->subscribers);
    if (signal->callbacks) __mn_free(signal->callbacks);
    if (signal->value) __mn_free(signal->value);
    __mn_free(signal);
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
 * MnStream — lazy, composable stream (iterator-based)
 * ----------------------------------------------------------------------- */

/** Stream node kind tags. */
#define MN_STREAM_FROM_LIST 0
#define MN_STREAM_MAP       1
#define MN_STREAM_FILTER    2
#define MN_STREAM_TAKE      3
#define MN_STREAM_SKIP      4
#define MN_STREAM_BOUNDED   5

struct MnStream {
    int64_t kind;          /* MN_STREAM_* tag */
    int64_t elem_size;     /* byte size of elements this stream yields */
    MnStream *source;      /* upstream stream (NULL for source nodes) */
    void    *state;        /* kind-specific state */
    void    *fn;           /* function pointer (map_fn, filter_fn, etc.) */
    void    *user_data;    /* closure context for fn */
};

/* --- FROM_LIST state --- */
typedef struct {
    MnList *list;
    int64_t index;
} MnStreamListState;

static int64_t _stream_list_next(MnStream *s, void *out) {
    MnStreamListState *st = (MnStreamListState *)s->state;
    if (st->index >= st->list->len) return 0;
    void *elem = st->list->data + st->index * s->elem_size;
    memcpy(out, elem, (size_t)s->elem_size);
    st->index++;
    return 1;
}

MN_EXPORT MnStream *__mn_stream_from_list(MnList *list, int64_t elem_size) {
    MnStream *s = (MnStream *)__mn_alloc(sizeof(MnStream));
    s->kind = MN_STREAM_FROM_LIST;
    s->elem_size = elem_size;
    s->source = NULL;
    MnStreamListState *st = (MnStreamListState *)__mn_alloc(sizeof(MnStreamListState));
    st->list = list;
    st->index = 0;
    s->state = st;
    s->fn = NULL;
    s->user_data = NULL;
    return s;
}

/* --- MAP --- */
typedef struct {
    int64_t in_elem_size;
} MnStreamMapState;

static int64_t _stream_map_next(MnStream *s, void *out) {
    MnStreamMapState *st = (MnStreamMapState *)s->state;
    char buf[256]; /* temp buffer for input element */
    void *in_buf = (st->in_elem_size <= 256) ? buf : __mn_alloc(st->in_elem_size);
    int64_t ok = __mn_stream_next(s->source, in_buf);
    if (ok) {
        MnStreamMapFn map_fn = (MnStreamMapFn)s->fn;
        map_fn(out, in_buf, s->user_data);
    }
    if (st->in_elem_size > 256) __mn_free(in_buf);
    return ok;
}

MN_EXPORT MnStream *__mn_stream_map(MnStream *source, MnStreamMapFn map_fn,
                                     void *user_data, int64_t out_elem_size) {
    MnStream *s = (MnStream *)__mn_alloc(sizeof(MnStream));
    s->kind = MN_STREAM_MAP;
    s->elem_size = out_elem_size;
    s->source = source;
    MnStreamMapState *st = (MnStreamMapState *)__mn_alloc(sizeof(MnStreamMapState));
    st->in_elem_size = source->elem_size;
    s->state = st;
    s->fn = (void *)map_fn;
    s->user_data = user_data;
    return s;
}

/* --- FILTER --- */

static int64_t _stream_filter_next(MnStream *s, void *out) {
    MnStreamFilterFn pred = (MnStreamFilterFn)s->fn;
    while (__mn_stream_next(s->source, out)) {
        if (pred(out, s->user_data)) return 1;
    }
    return 0;
}

MN_EXPORT MnStream *__mn_stream_filter(MnStream *source, MnStreamFilterFn pred_fn,
                                        void *user_data) {
    MnStream *s = (MnStream *)__mn_alloc(sizeof(MnStream));
    s->kind = MN_STREAM_FILTER;
    s->elem_size = source->elem_size;
    s->source = source;
    s->state = NULL;
    s->fn = (void *)pred_fn;
    s->user_data = user_data;
    return s;
}

/* --- TAKE --- */
typedef struct {
    int64_t remaining;
} MnStreamTakeState;

static int64_t _stream_take_next(MnStream *s, void *out) {
    MnStreamTakeState *st = (MnStreamTakeState *)s->state;
    if (st->remaining <= 0) return 0;
    int64_t ok = __mn_stream_next(s->source, out);
    if (ok) st->remaining--;
    return ok;
}

MN_EXPORT MnStream *__mn_stream_take(MnStream *source, int64_t n) {
    MnStream *s = (MnStream *)__mn_alloc(sizeof(MnStream));
    s->kind = MN_STREAM_TAKE;
    s->elem_size = source->elem_size;
    s->source = source;
    MnStreamTakeState *st = (MnStreamTakeState *)__mn_alloc(sizeof(MnStreamTakeState));
    st->remaining = n;
    s->state = st;
    s->fn = NULL;
    s->user_data = NULL;
    return s;
}

/* --- SKIP --- */
typedef struct {
    int64_t to_skip;
    int64_t skipped;
} MnStreamSkipState;

static int64_t _stream_skip_next(MnStream *s, void *out) {
    MnStreamSkipState *st = (MnStreamSkipState *)s->state;
    /* Skip initial elements on first calls */
    while (st->skipped < st->to_skip) {
        char buf[256];
        void *skip_buf = (s->elem_size <= 256) ? buf : __mn_alloc(s->elem_size);
        int64_t ok = __mn_stream_next(s->source, skip_buf);
        if (s->elem_size > 256) __mn_free(skip_buf);
        if (!ok) return 0;
        st->skipped++;
    }
    return __mn_stream_next(s->source, out);
}

MN_EXPORT MnStream *__mn_stream_skip(MnStream *source, int64_t n) {
    MnStream *s = (MnStream *)__mn_alloc(sizeof(MnStream));
    s->kind = MN_STREAM_SKIP;
    s->elem_size = source->elem_size;
    s->source = source;
    MnStreamSkipState *st = (MnStreamSkipState *)__mn_alloc(sizeof(MnStreamSkipState));
    st->to_skip = n;
    st->skipped = 0;
    s->state = st;
    s->fn = NULL;
    s->user_data = NULL;
    return s;
}

/* --- BOUNDED (backpressure via pre-allocated buffer) --- */
typedef struct {
    char   *buffer;     /* circular buffer */
    int64_t capacity;
    int64_t head;       /* next read position */
    int64_t tail;       /* next write position */
    int64_t count;      /* current items in buffer */
    int64_t source_done;
} MnStreamBoundedState;

static int64_t _stream_bounded_next(MnStream *s, void *out) {
    MnStreamBoundedState *st = (MnStreamBoundedState *)s->state;
    /* Refill buffer from source up to capacity */
    while (!st->source_done && st->count < st->capacity) {
        void *slot = st->buffer + (st->tail % st->capacity) * s->elem_size;
        if (__mn_stream_next(s->source, slot)) {
            st->tail++;
            st->count++;
        } else {
            st->source_done = 1;
        }
    }
    if (st->count == 0) return 0;
    void *slot = st->buffer + (st->head % st->capacity) * s->elem_size;
    memcpy(out, slot, (size_t)s->elem_size);
    st->head++;
    st->count--;
    return 1;
}

MN_EXPORT MnStream *__mn_stream_bounded(MnStream *source, int64_t capacity,
                                         int64_t elem_size) {
    MnStream *s = (MnStream *)__mn_alloc(sizeof(MnStream));
    s->kind = MN_STREAM_BOUNDED;
    s->elem_size = elem_size;
    s->source = source;
    MnStreamBoundedState *st = (MnStreamBoundedState *)__mn_alloc(sizeof(MnStreamBoundedState));
    st->buffer = (char *)__mn_alloc(capacity * elem_size);
    st->capacity = capacity;
    st->head = 0;
    st->tail = 0;
    st->count = 0;
    st->source_done = 0;
    s->state = st;
    s->fn = NULL;
    s->user_data = NULL;
    return s;
}

/* --- NEXT (unified dispatch) --- */

MN_EXPORT int64_t __mn_stream_next(MnStream *stream, void *out_ptr) {
    switch (stream->kind) {
        case MN_STREAM_FROM_LIST: return _stream_list_next(stream, out_ptr);
        case MN_STREAM_MAP:       return _stream_map_next(stream, out_ptr);
        case MN_STREAM_FILTER:    return _stream_filter_next(stream, out_ptr);
        case MN_STREAM_TAKE:      return _stream_take_next(stream, out_ptr);
        case MN_STREAM_SKIP:      return _stream_skip_next(stream, out_ptr);
        case MN_STREAM_BOUNDED:   return _stream_bounded_next(stream, out_ptr);
        default: return 0;
    }
}

/* --- COLLECT (terminal) --- */

MN_EXPORT MnList __mn_stream_collect(MnStream *stream, int64_t elem_size) {
    MnList list = __mn_list_new(elem_size);
    char buf[256];
    void *elem_buf = (elem_size <= 256) ? buf : __mn_alloc(elem_size);
    while (__mn_stream_next(stream, elem_buf)) {
        __mn_list_push(&list, elem_buf);
    }
    if (elem_size > 256) __mn_free(elem_buf);
    return list;
}

/* --- FOLD (terminal) --- */

MN_EXPORT void __mn_stream_fold(MnStream *stream, void *init_ptr, int64_t acc_size,
                                 MnStreamFoldFn fold_fn, void *user_data, void *out_ptr) {
    memcpy(out_ptr, init_ptr, (size_t)acc_size);
    int64_t elem_size = stream->elem_size;
    char buf[256];
    void *elem_buf = (elem_size <= 256) ? buf : __mn_alloc(elem_size);
    while (__mn_stream_next(stream, elem_buf)) {
        fold_fn(out_ptr, elem_buf, user_data);
    }
    if (elem_size > 256) __mn_free(elem_buf);
}

/* --- FREE --- */

MN_EXPORT void __mn_stream_free(MnStream *stream) {
    if (!stream) return;
    if (stream->kind == MN_STREAM_BOUNDED) {
        MnStreamBoundedState *st = (MnStreamBoundedState *)stream->state;
        if (st) {
            __mn_free(st->buffer);
            __mn_free(st);
        }
    } else if (stream->state) {
        __mn_free(stream->state);
    }
    __mn_free(stream);
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

/* -----------------------------------------------------------------------
 * Range Iterator
 *
 * Used by `for i in start..end` loops.  The iterator is a heap-allocated
 * struct holding {current, end}.  Values are returned as i8* (inttoptr)
 * so the LLVM IR can ptrtoint them back to i64.
 * ----------------------------------------------------------------------- */

typedef struct {
    int64_t current;
    int64_t end;
} MnRangeIter;

MN_EXPORT void *__range(int64_t start, int64_t end) {
    MnRangeIter *iter = (MnRangeIter *)malloc(sizeof(MnRangeIter));
    if (!iter) {
        fprintf(stderr, "mapanare: out of memory in __range\n");
        exit(1);
    }
    iter->current = start;
    iter->end = end;
    return (void *)iter;
}

MN_EXPORT int8_t __iter_has_next(void *iter_ptr) {
    MnRangeIter *iter = (MnRangeIter *)iter_ptr;
    return iter->current < iter->end ? 1 : 0;
}

MN_EXPORT void *__iter_next(void *iter_ptr) {
    MnRangeIter *iter = (MnRangeIter *)iter_ptr;
    int64_t val = iter->current;
    iter->current++;
    return (void *)(intptr_t)val;
}
