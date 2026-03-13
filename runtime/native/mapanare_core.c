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
