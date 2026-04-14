/**
 * mapanare_core.c — Core runtime implementation for Mapanare self-hosting.
 *
 * Provides string, list, file I/O, and memory operations that native-compiled
 * Mapanare programs link against.
 */

#include "mapanare_core.h"
#include "mapanare_platform.h"

#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#ifndef _WIN32
#include <sys/wait.h>
#endif

/* -----------------------------------------------------------------------
 * Memory helpers
 * ----------------------------------------------------------------------- */

/* --- Memory profiling counters (compile with -DMN_PROFILE_MEM to enable) --- */
#ifdef MN_PROFILE_MEM
static _Atomic int64_t mn_alloc_count = 0;
static _Atomic int64_t mn_alloc_bytes = 0;
static _Atomic int64_t mn_alloc_peak  = 0;   /* high-water mark of live bytes */
static _Atomic int64_t mn_alloc_live  = 0;   /* current live bytes (alloc - free) */
static _Atomic int64_t mn_concat_count = 0;
static _Atomic int64_t mn_concat_bytes = 0;
static _Atomic int64_t mn_clone_count = 0;
static _Atomic int64_t mn_grow_count  = 0;
static _Atomic int64_t mn_listbuf_count = 0;
static _Atomic int64_t mn_listbuf_bytes = 0;

static void mn_profile_report(void) {
    fprintf(stderr, "\n=== MN MEMORY PROFILE ===\n");
    fprintf(stderr, "alloc:    %lld calls, %lld MB total\n",
            (long long)atomic_load(&mn_alloc_count), (long long)(atomic_load(&mn_alloc_bytes) / (1024*1024)));
    fprintf(stderr, "peak:     %lld MB live\n",
            (long long)(atomic_load(&mn_alloc_peak) / (1024*1024)));
    fprintf(stderr, "listbuf:  %lld calls, %lld MB total\n",
            (long long)atomic_load(&mn_listbuf_count), (long long)(atomic_load(&mn_listbuf_bytes) / (1024*1024)));
    fprintf(stderr, "grow:     %lld calls\n", (long long)atomic_load(&mn_grow_count));
    fprintf(stderr, "clone:    %lld calls\n", (long long)atomic_load(&mn_clone_count));
    fprintf(stderr, "detach:   (see cow_detaches counter)\n");
    fprintf(stderr, "concat:   %lld calls, %lld MB total\n",
            (long long)atomic_load(&mn_concat_count), (long long)(atomic_load(&mn_concat_bytes) / (1024*1024)));
    fprintf(stderr, "=========================\n");
}
static int mn_profile_init_done = 0;
static void mn_profile_init(void) {
    if (!mn_profile_init_done) {
        mn_profile_init_done = 1;
        atexit(mn_profile_report);
    }
}
#define MN_PROFILE_ALLOC(sz) do { \
    mn_profile_init(); \
    atomic_fetch_add_explicit(&mn_alloc_count, 1, memory_order_relaxed); \
    atomic_fetch_add_explicit(&mn_alloc_bytes, (int64_t)(sz), memory_order_relaxed); \
    int64_t _live = atomic_fetch_add_explicit(&mn_alloc_live, (int64_t)(sz), memory_order_relaxed) + (int64_t)(sz); \
    int64_t _peak = atomic_load_explicit(&mn_alloc_peak, memory_order_relaxed); \
    while (_live > _peak && !atomic_compare_exchange_weak_explicit(&mn_alloc_peak, &_peak, _live, memory_order_relaxed, memory_order_relaxed)) {} \
} while(0)
#define MN_PROFILE_FREE(sz) do { \
    atomic_fetch_sub_explicit(&mn_alloc_live, (int64_t)(sz), memory_order_relaxed); \
} while(0)
#else
#define MN_PROFILE_ALLOC(sz) ((void)0)
#define MN_PROFILE_FREE(sz)  ((void)0)
#endif

MN_EXPORT void *__mn_alloc(int64_t size) {
    if (size < 0) return NULL;
    MN_PROFILE_ALLOC(size);
    void *ptr = calloc(1, (size_t)size);
    if (!ptr && size > 0) {
        fprintf(stderr, "mapanare: out of memory (requested %lld bytes)\n",
                (long long)size);
        exit(1);
    }
    return ptr;
}

MN_EXPORT void *__mn_realloc(void *ptr, int64_t new_size) {
    if (new_size < 0) return NULL;
    void *p = realloc(ptr, (size_t)new_size);
    if (!p && new_size > 0) {
        fprintf(stderr, "mapanare: realloc failed (%lld bytes)\n",
                (long long)new_size);
        exit(1);
    }
    return p;
}

MN_EXPORT void __mn_free(void *ptr) {
    /* v4.34.0: wire MN_PROFILE_FREE so mn_alloc_live tracks currently-live
     * bytes instead of growing monotonically.  We don't know the exact size
     * of the allocation here (libc doesn't expose it portably), so we pass 0.
     * To get accurate live tracking, callers should use __mn_free_sized. */
    (void)ptr;  /* suppress unused-when-profiling-disabled warning */
    free(ptr);
}

MN_EXPORT void __mn_free_sized(void *ptr, int64_t size) {
    MN_PROFILE_FREE(size);
    (void)size;  /* suppress warning when profiling disabled */
    free(ptr);
}

/* -----------------------------------------------------------------------
 * Checked arithmetic — abort on integer overflow instead of wrapping.
 * ----------------------------------------------------------------------- */

int64_t mn_checked_mul(int64_t a, int64_t b) {
    if (a > 0 && b > 0 && a > INT64_MAX / b) {
        fprintf(stderr, "mapanare: integer overflow in %lld * %lld\n",
                (long long)a, (long long)b);
        exit(1);
    }
    if (a > 0 && b < 0 && b < INT64_MIN / a) {
        fprintf(stderr, "mapanare: integer overflow in %lld * %lld\n",
                (long long)a, (long long)b);
        exit(1);
    }
    if (a < 0 && b > 0 && a < INT64_MIN / b) {
        fprintf(stderr, "mapanare: integer overflow in %lld * %lld\n",
                (long long)a, (long long)b);
        exit(1);
    }
    if (a < 0 && b < 0 && a < INT64_MAX / b) {
        fprintf(stderr, "mapanare: integer overflow in %lld * %lld\n",
                (long long)a, (long long)b);
        exit(1);
    }
    return a * b;
}

int64_t mn_checked_add(int64_t a, int64_t b) {
    if (b > 0 && a > INT64_MAX - b) {
        fprintf(stderr, "mapanare: integer overflow in %lld + %lld\n",
                (long long)a, (long long)b);
        exit(1);
    }
    if (b < 0 && a < INT64_MIN - b) {
        fprintf(stderr, "mapanare: integer overflow in %lld + %lld\n",
                (long long)a, (long long)b);
        exit(1);
    }
    return a + b;
}

/* -----------------------------------------------------------------------
 * v4.100.0: the tagged-pointer scheme has been removed. The heap flag
 * now lives in the ``is_heap`` bitfield on MnString (see mapanare_core.h).
 *
 * ``mn_untag`` used to mask bit 0 off the data pointer; it now trivially
 * returns the pointer unchanged, but is kept as a macro so the mechanical
 * diff across this file is small. The construction helpers (``mn_tag_heap``
 * and ``mn_is_heap``) are gone — callers set ``s.is_heap = 1`` / check
 * ``s.is_heap`` directly.
 * ----------------------------------------------------------------------- */

#define mn_untag(ptr) (ptr)

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
    if (block_size <= 0) block_size = MAPANARE_DEFAULT_ARENA_BLOCK;
    MnArena *arena = (MnArena *)malloc(sizeof(MnArena));
    if (!arena) {
        fprintf(stderr, "mapanare: arena create failed\n");
        exit(1);
    }
    arena->default_block_size = block_size;
    arena->head = mn_arena_block_new(block_size);
    arena->lock = 0;
    return arena;
}

/* v4.34.0: spinlock for thread-safe arena allocation */
static inline void arena_lock(MnArena *arena) {
    while (__sync_lock_test_and_set(&arena->lock, 1)) {
        /* spin — arenas are fast, contention is rare */
    }
}
static inline void arena_unlock(MnArena *arena) {
    __sync_lock_release(&arena->lock);
}

MN_EXPORT void *mn_arena_alloc(MnArena *arena, int64_t size) {
    if (size <= 0) return NULL;
    /* Align to 8 bytes */
    size = (size + 7) & ~(int64_t)7;

    arena_lock(arena);
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
    arena_unlock(arena);
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
 * String Interning — hash-set-based deduplication pool
 *
 * Uses open addressing with linear probing.  Key = MnString content,
 * stored as a heap-allocated copy.  When the table reaches its cap,
 * new strings are returned without inserting (no eviction).
 * ----------------------------------------------------------------------- */

typedef struct {
    MnString str;      /* interned string (heap-allocated data) */
    uint64_t hash;     /* cached hash of str                    */
    int      occupied; /* 1 = slot in use                       */
} MnInternEntry;

static MnInternEntry *s_intern_table  = NULL;
static size_t         s_intern_cap    = 0;    /* max entries (set from platform default) */
static size_t         s_intern_count  = 0;    /* current entry count                     */
static size_t         s_intern_bytes  = 0;    /* total bytes of interned string values   */
static size_t         s_intern_tbl_sz = 0;    /* hash table slot count (>= cap * 2)      */
static int            s_intern_sealed = 0;    /* 1 after first use — cap is locked        */

/* Thread safety for the intern table */
#ifdef _WIN32
/*
 * v4.28.0: swapped the ``InterlockedCompareExchange`` double-check pattern
 * for ``InitOnceExecuteOnce`` (same fix as ``mn_signal_mutex`` above).
 * The CAS pattern was flagged by Cobra #5 in the v4.26.0 panel — the
 * Windows memory model does not guarantee the ``InitializeCriticalSection``
 * write is visible to a thread that observed the flag transition.
 */
static CRITICAL_SECTION s_intern_cs;
static INIT_ONCE s_intern_cs_once = INIT_ONCE_STATIC_INIT;
static BOOL CALLBACK s_intern_cs_init_cb(PINIT_ONCE once, PVOID param, PVOID *ctx) {
    (void)once; (void)param; (void)ctx;
    InitializeCriticalSection(&s_intern_cs);
    return TRUE;
}
static void intern_lock(void) {
    InitOnceExecuteOnce(&s_intern_cs_once, s_intern_cs_init_cb, NULL, NULL);
    EnterCriticalSection(&s_intern_cs);
}
static void intern_unlock(void) { LeaveCriticalSection(&s_intern_cs); }
#else
#include <pthread.h>
static pthread_mutex_t s_intern_mutex = PTHREAD_MUTEX_INITIALIZER;
static void intern_lock(void)   { pthread_mutex_lock(&s_intern_mutex); }
static void intern_unlock(void) { pthread_mutex_unlock(&s_intern_mutex); }
#endif

static uint64_t intern_hash(const char *data, int64_t len) {
    /* FNV-1a 64-bit */
    uint64_t h = 14695981039346656037ULL;
    for (int64_t i = 0; i < len; i++) {
        h ^= (uint64_t)(unsigned char)data[i];
        h *= 1099511628211ULL;
    }
    return h;
}

static void intern_ensure_table(void) {
    if (s_intern_table) return;
    if (s_intern_cap == 0) s_intern_cap = MAPANARE_DEFAULT_INTERN_CAP;
    /* Table size = 2x cap for ~50% load factor, rounded to power of 2 */
    size_t tbl = s_intern_cap * 2;
    /* next power of two */
    size_t v = tbl;
    v--; v |= v >> 1; v |= v >> 2; v |= v >> 4;
    v |= v >> 8; v |= v >> 16; v |= v >> 32; v++;
    s_intern_tbl_sz = v;
    s_intern_table = (MnInternEntry *)calloc(v, sizeof(MnInternEntry));
    s_intern_sealed = 1;
}

MN_EXPORT void __mn_intern_set_cap(size_t cap) {
    if (s_intern_sealed) return;  /* too late */
    if (cap > 0) s_intern_cap = cap;
}

MN_EXPORT MnString __mn_str_intern(MnString s) {
    if (s.len <= 0 || !s.data) return s;

    intern_lock();
    intern_ensure_table();
    if (!s_intern_table) { intern_unlock(); return s; }

    const char *raw = s.data;
    uint64_t h = intern_hash(raw, s.len);
    size_t mask = s_intern_tbl_sz - 1;
    size_t idx = (size_t)(h & mask);

    /* Probe for existing entry */
    for (size_t i = 0; i < s_intern_tbl_sz; i++) {
        size_t pos = (idx + i) & mask;
        MnInternEntry *e = &s_intern_table[pos];
        if (!e->occupied) break;
        if (e->hash == h && e->str.len == s.len) {
            const char *eraw = e->str.data;
            if (memcmp(eraw, raw, (size_t)s.len) == 0) {
                intern_unlock();
                return e->str;  /* deduplicated */
            }
        }
    }

    /* Not found — insert if under cap */
    if (s_intern_count >= s_intern_cap) {
        intern_unlock();
        /* Cap reached — return a plain heap copy, no dedup */
        return __mn_str_from_parts(raw, s.len);
    }

    /* Insert new entry */
    for (size_t i = 0; i < s_intern_tbl_sz; i++) {
        size_t pos = (idx + i) & mask;
        MnInternEntry *e = &s_intern_table[pos];
        if (!e->occupied) {
            MnString copy = __mn_str_from_parts(raw, s.len);
            e->str = copy;
            e->hash = h;
            e->occupied = 1;
            s_intern_count++;
            s_intern_bytes += (size_t)s.len;
            intern_unlock();
            return copy;
        }
    }

    intern_unlock();
    /* Table completely full (should not happen with 2x sizing) */
    return __mn_str_from_parts(raw, s.len);
}

MN_EXPORT void __mn_intern_stats(size_t *count, size_t *bytes) {
    if (count) *count = s_intern_count;
    if (bytes) *bytes = s_intern_bytes;
}

MN_EXPORT void __mn_intern_destroy(void) {
    if (!s_intern_table) return;
    for (size_t i = 0; i < s_intern_tbl_sz; i++) {
        if (s_intern_table[i].occupied) {
            __mn_str_free(s_intern_table[i].str);
        }
    }
    free(s_intern_table);
    s_intern_table  = NULL;
    s_intern_count  = 0;
    s_intern_bytes  = 0;
    s_intern_tbl_sz = 0;
    s_intern_sealed = 0;
}

/* -----------------------------------------------------------------------
 * MnString
 * ----------------------------------------------------------------------- */

MN_EXPORT MnString __mn_str_from_cstr(const char *cstr) {
    MnString s;
    if (!cstr) {
        s.data = "";
        s.len = 0;
        s.is_heap = 0;
        return s;
    }
    int64_t len = (int64_t)strlen(cstr);
    char *buf = (char *)__mn_alloc(len + 1);
    memcpy(buf, cstr, (size_t)len);
    buf[len] = '\0';
    s.data = buf;
    s.len = (uint64_t)len;
    s.is_heap = 1;
    return s;
}

MN_EXPORT MnString __mn_str_from_parts(const char *data, int64_t len) {
    MnString s;
    if (!data || len <= 0) {
        s.data = "";
        s.len = 0;
        s.is_heap = 0;
        return s;
    }
    char *buf = (char *)__mn_alloc(len + 1);
    memcpy(buf, data, (size_t)len);
    buf[len] = '\0';
    s.data = buf;
    s.len = (uint64_t)len;
    s.is_heap = 1;
    return s;
}

MN_EXPORT MnString __mn_str_empty(void) {
    MnString s;
    s.data = "";
    s.len = 0;
    s.is_heap = 0;
    return s;
}

MN_EXPORT MnString __mn_str_concat(MnString a, MnString b) {
    if (a.len <= 0 && b.len <= 0) return __mn_str_empty();
    if (a.len <= 0) return __mn_str_from_parts(b.data, (int64_t)b.len);
    if (b.len <= 0) return __mn_str_from_parts(a.data, (int64_t)a.len);
    const char *a_data = a.data;
    const char *b_data = b.data;
    int64_t total = mn_checked_add((int64_t)a.len, (int64_t)b.len);
#ifdef MN_PROFILE_MEM
    atomic_fetch_add_explicit(&mn_concat_count, 1, memory_order_relaxed);
    atomic_fetch_add_explicit(&mn_concat_bytes, (int64_t)(total + 1), memory_order_relaxed);
#endif
    char *buf = (char *)__mn_alloc(total + 1);
    if (a.len > 0) memcpy(buf, a_data, (size_t)a.len);
    if (b.len > 0) memcpy(buf + a.len, b_data, (size_t)b.len);
    buf[total] = '\0';
    MnString s;
    s.data = buf;
    s.len = (uint64_t)total;
    s.is_heap = 1;
    return s;
}

/* =======================================================================
 * StringBuilder (v4.95.0) — amortized O(1) string append
 *
 * Replaces the O(n^2) pattern of repeated __mn_str_concat in loops.
 * Exponential growth (2x) with initial capacity 64 bytes.
 * ======================================================================= */

/* MnStringBuilder is defined in mapanare_core.h */

MN_EXPORT MnStringBuilder __mn_sb_create(int64_t initial_cap) {
    MnStringBuilder sb;
    sb.cap = initial_cap > 0 ? initial_cap : 64;
    sb.buf = (char *)__mn_alloc(sb.cap);
    sb.buf[0] = '\0';
    sb.len = 0;
    return sb;
}

static void mn_sb_grow(MnStringBuilder *sb, int64_t needed) {
    int64_t new_cap = sb->cap;
    while (new_cap < needed) {
        new_cap = new_cap * 2;
        if (new_cap < 0) new_cap = needed; /* overflow guard */
    }
    char *new_buf = (char *)__mn_alloc(new_cap);
    if (sb->len > 0) memcpy(new_buf, sb->buf, (size_t)sb->len);
    new_buf[sb->len] = '\0';
    __mn_free(sb->buf);
    sb->buf = new_buf;
    sb->cap = new_cap;
}

MN_EXPORT void __mn_sb_append(MnStringBuilder *sb, MnString s) {
    if (s.len <= 0) return;
    const char *data = mn_untag(s.data);
    int64_t needed = sb->len + s.len + 1;
    if (needed > sb->cap) {
        mn_sb_grow(sb, needed);
    }
    memcpy(sb->buf + sb->len, data, (size_t)s.len);
    sb->len += s.len;
    sb->buf[sb->len] = '\0';
}

MN_EXPORT void __mn_sb_append_char(MnStringBuilder *sb, char c) {
    int64_t needed = sb->len + 2;
    if (needed > sb->cap) {
        mn_sb_grow(sb, needed);
    }
    sb->buf[sb->len] = c;
    sb->len++;
    sb->buf[sb->len] = '\0';
}

MN_EXPORT MnString __mn_sb_to_string(MnStringBuilder *sb) {
    /* Transfer ownership: the buffer becomes the string's data.
     * The StringBuilder is consumed (zeroed out). */
    MnString s;
    if (sb->len == 0) {
        __mn_free(sb->buf);
        s = __mn_str_empty();
    } else {
        /* Realloc to exact size if significantly oversized. */
        if (sb->cap > sb->len * 2 + 1) {
            char *tight = (char *)__mn_alloc(sb->len + 1);
            memcpy(tight, sb->buf, (size_t)sb->len + 1);
            __mn_free(sb->buf);
            sb->buf = tight;
        }
        s.data = sb->buf;
        s.len = (uint64_t)sb->len;
        s.is_heap = 1;
    }
    sb->buf = NULL;
    sb->len = 0;
    sb->cap = 0;
    return s;
}

MN_EXPORT void __mn_sb_destroy(MnStringBuilder *sb) {
    if (sb->buf) __mn_free(sb->buf);
    sb->buf = NULL;
    sb->len = 0;
    sb->cap = 0;
}

/* v4.108.0: pointer-based API.
 * `__mn_sb_new` allocates both the struct and the initial buffer on the
 * heap so that subsequent calls work with a single scalar pointer
 * (simpler ABI for the MIR emitter). `__mn_sb_finish` consumes the
 * builder — transfers ownership of the buffer to the returned
 * `MnString` and frees the struct. */
MN_EXPORT MnStringBuilder *__mn_sb_new(int64_t initial_cap) {
    MnStringBuilder *sb = (MnStringBuilder *)malloc(sizeof(MnStringBuilder));
    if (!sb) return NULL;
    sb->cap = initial_cap > 0 ? initial_cap : 64;
    sb->buf = (char *)__mn_alloc(sb->cap);
    sb->buf[0] = '\0';
    sb->len = 0;
    return sb;
}

MN_EXPORT MnString __mn_sb_finish(MnStringBuilder *sb) {
    MnString s = __mn_sb_to_string(sb);  /* zeros out sb, transfers buf */
    free(sb);                            /* free the struct itself */
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
    if (a.data == NULL || b.data == NULL) {
        if (a.data == NULL && b.data == NULL) return a.len == b.len ? 1 : 0;
        return 0;
    }
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

MN_EXPORT MnString __mn_str_substr(MnString s, int64_t start, int64_t count) {
    if (start < 0) start = 0;
    if (start >= s.len) return __mn_str_empty();
    int64_t end = start + count;
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
        return s;
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
    if (start == 0) return s;
    return __mn_str_from_parts(data + start, s.len - start);
}

MN_EXPORT MnString __mn_str_trim_end(MnString s) {
    const char *data = mn_untag(s.data);
    int64_t end = s.len;
    while (end > 0 && (data[end - 1] == ' ' || data[end - 1] == '\t' ||
           data[end - 1] == '\n' || data[end - 1] == '\r')) {
        end--;
    }
    if (end == s.len) return s;
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
    r.data = buf;
    r.len = s.len;
    r.is_heap = 1;
    return r;
}

MN_EXPORT MnString __mn_str_to_lower(MnString s) {
    if (s.len == 0) return __mn_str_empty();
    const char *data = s.data;
    char *buf = (char *)__mn_alloc(s.len + 1);
    for (int64_t i = 0; i < s.len; i++) {
        char c = data[i];
        buf[i] = (c >= 'A' && c <= 'Z') ? (char)(c + 32) : c;
    }
    buf[s.len] = '\0';
    MnString r;
    r.data = buf;
    r.len = s.len;
    r.is_heap = 1;
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

    int64_t new_len = mn_checked_add(s.len, mn_checked_mul(count, new_s.len - old_s.len));
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
    r.data = buf;
    r.len = (uint64_t)new_len;
    r.is_heap = 1;
    return r;
}

/* str(true) / str(false) — return non-heap constants (never freed). */
static const char s_true[]  = "true";
static const char s_false[] = "false";

MN_EXPORT MnString __mn_str_from_bool(int64_t value) {
    MnString s;
    if (value) { s.data = s_true;  s.len = 4; }
    else       { s.data = s_false; s.len = 5; }
    s.is_heap = 0;  /* static storage — drop glue must not free */
    return s;
}

/* str(N) for -128..127 — pre-initialized cache (zero allocation). */
#define SMALL_INT_MIN (-128)
#define SMALL_INT_MAX  127
#define SMALL_INT_RANGE (SMALL_INT_MAX - SMALL_INT_MIN + 1)

static char   s_int_bufs[SMALL_INT_RANGE][8]; /* max "-128\0" = 5 chars */
static MnString s_int_cache[SMALL_INT_RANGE];

/*
 * v4.28.0: same pattern as ``mn_init_tag_strings`` — the ``int init`` flag
 * was racy. Switched to the canonical once-init primitive for each platform.
 */
#ifdef _WIN32
static INIT_ONCE s_int_cache_once = INIT_ONCE_STATIC_INIT;
static BOOL CALLBACK init_small_int_cache_cb(PINIT_ONCE once, PVOID param, PVOID *ctx) {
    (void)once; (void)param; (void)ctx;
    for (int i = 0; i < SMALL_INT_RANGE; i++) {
        int val = SMALL_INT_MIN + i;
        int n = snprintf(s_int_bufs[i], sizeof(s_int_bufs[i]), "%d", val);
        s_int_cache[i].data    = s_int_bufs[i]; /* static storage */
        s_int_cache[i].len     = (uint64_t)n;
        s_int_cache[i].is_heap = 0;
    }
    return TRUE;
}
static void init_small_int_cache(void) {
    InitOnceExecuteOnce(&s_int_cache_once, init_small_int_cache_cb, NULL, NULL);
}
#else
static pthread_once_t s_int_cache_once = PTHREAD_ONCE_INIT;
static void init_small_int_cache_impl(void) {
    for (int i = 0; i < SMALL_INT_RANGE; i++) {
        int val = SMALL_INT_MIN + i;
        int n = snprintf(s_int_bufs[i], sizeof(s_int_bufs[i]), "%d", val);
        s_int_cache[i].data    = s_int_bufs[i]; /* static storage */
        s_int_cache[i].len     = (uint64_t)n;
        s_int_cache[i].is_heap = 0;
    }
}
static void init_small_int_cache(void) {
    pthread_once(&s_int_cache_once, init_small_int_cache_impl);
}
#endif

MN_EXPORT MnString __mn_str_from_int(int64_t value) {
    if (value >= SMALL_INT_MIN && value <= SMALL_INT_MAX) {
        init_small_int_cache();
        return s_int_cache[(int)(value - SMALL_INT_MIN)];
    }
    char buf[32];
    int n = snprintf(buf, sizeof(buf), "%lld", (long long)value);
    return __mn_str_from_parts(buf, (int64_t)n);
}

MN_EXPORT MnString __mn_str_from_float(double value) {
    char buf[64];
    int n = snprintf(buf, sizeof(buf), "%g", value);
    return __mn_str_from_parts(buf, (int64_t)n);
}

MN_EXPORT int64_t __mn_str_to_int(MnString s) {
    const char *data = mn_untag(s.data);
    if (!data || s.len <= 0) return 0;
    /* Handle 0x, 0b, 0o prefixes */
    if (s.len > 2 && data[0] == '0') {
        if (data[1] == 'x' || data[1] == 'X') return strtoll(data, NULL, 16);
        if (data[1] == 'b' || data[1] == 'B') return strtoll(data + 2, NULL, 2);
        if (data[1] == 'o' || data[1] == 'O') return strtoll(data + 2, NULL, 8);
    }
    return strtoll(data, NULL, 10);
}

MN_EXPORT double __mn_str_to_float(MnString s) {
    const char *data = mn_untag(s.data);
    if (!data || s.len <= 0) return 0.0;
    return strtod(data, NULL);
}

MN_EXPORT void __mn_str_free(MnString s) {
    if (s.data && s.is_heap) {
        __mn_free((void *)s.data);
    }
}

MN_EXPORT void __mn_str_print(MnString s) {
    if (s.len > 0) {
        fwrite(s.data, 1, (size_t)s.len, stdout);
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

MN_EXPORT void __mn_str_eprint(MnString s) {
    if (s.len > 0) {
        fwrite(mn_untag(s.data), 1, (size_t)s.len, stderr);
    }
}

MN_EXPORT int64_t __mn_str_ord(MnString s) {
    if (s.len <= 0) return -1;
    return (int64_t)(unsigned char)mn_untag(s.data)[0];
}

MN_EXPORT MnString __mn_str_chr(int64_t code) {
    if (code < 0 || code > 127) {
        return __mn_str_empty();
    }
    char buf[2] = { (char)code, '\0' };
    return __mn_str_from_cstr(buf);
}

MN_EXPORT MnString __mn_str_join(MnString sep, MnList *parts) {
    if (parts->len == 0) return __mn_str_empty();

    /* Calculate total length. */
    const char *sep_data = mn_untag(sep.data);
    int64_t total = 0;
    for (int64_t i = 0; i < parts->len; i++) {
        MnString *s = (MnString *)(parts->data + i * parts->elem_size);
        total += s->len;
    }
    total += sep.len * (parts->len - 1);

    char *buf = (char *)__mn_alloc(total + 1);
    int64_t pos = 0;
    for (int64_t i = 0; i < parts->len; i++) {
        if (i > 0 && sep.len > 0) {
            memcpy(buf + pos, sep_data, (size_t)sep.len);
            pos += sep.len;
        }
        MnString *s = (MnString *)(parts->data + i * parts->elem_size);
        if (s->len > 0) {
            memcpy(buf + pos, mn_untag(s->data), (size_t)s->len);
            pos += s->len;
        }
    }
    buf[total] = '\0';

    MnString r;
    r.data = buf;
    r.len = (uint64_t)total;
    r.is_heap = 1;
    return r;
}

/* -----------------------------------------------------------------------
 * MnList — Copy-On-Write (COW) Implementation
 *
 * Layout: the refcount is stored in a header BEFORE the data pointer.
 *   Allocation: [8 bytes refcount][element data...]
 *   list.data points to element data (after the header).
 *   Refcount is at ((int64_t *)list.data)[-1].
 *
 * This keeps MnList at 32 bytes {data, len, cap, elem_size} — no layout change.
 * Clone is O(1): copy header, increment refcount.
 * Mutation (push/set/pop) detaches if refcount > 1: allocate new buffer, copy.
 * ----------------------------------------------------------------------- */

#define MN_LIST_INITIAL_CAP 8
#define MN_LIST_HEADER_SIZE 16  /* [magic: i64][refcount: i64] */
#define MN_COW_MAGIC ((int64_t)0x434F574C495354LL)  /* "COWLIST" in ASCII */

/* Access the refcount for a list's data buffer */
static int64_t *mn_list_rc(MnList *list) {
    if (!list->data || !list->managed) return NULL;
    int64_t *header = ((int64_t *)list->data) - 2;
    if (header[0] != MN_COW_MAGIC) return NULL;  /* corrupted — don't touch */
    return &header[1];
}

/* Check if the buffer has a valid COW magic header.
 * Uses the `managed` field instead of probing memory with write(2). */
static int mn_list_has_magic(MnList *list) {
    return list->managed && list->data != NULL;
}

/* Allocate a new COW buffer: [magic][refcount=1][cap * elem_size] */
static char *mn_list_alloc_buf(int64_t cap, int64_t elem_size) {
    int64_t data_bytes = mn_checked_mul(cap, elem_size);
#ifdef MN_PROFILE_MEM
    atomic_fetch_add_explicit(&mn_listbuf_count, 1, memory_order_relaxed);
    atomic_fetch_add_explicit(&mn_listbuf_bytes, (int64_t)(MN_LIST_HEADER_SIZE + data_bytes), memory_order_relaxed);
#endif
    char *raw = (char *)__mn_alloc(mn_checked_add(MN_LIST_HEADER_SIZE, data_bytes));
    int64_t *header = (int64_t *)raw;
    header[0] = MN_COW_MAGIC;  /* magic */
    header[1] = 1;             /* refcount = 1 */
    return raw + MN_LIST_HEADER_SIZE;  /* data pointer past the header */
}

static int mn_list_is_managed(MnList *list);
static _Atomic int64_t cow_shares = 0;
static _Atomic int64_t cow_fallbacks = 0;
static _Atomic int64_t cow_detaches = 0;

/* Detach: if refcount > 1, allocate a private copy of the data.
 * Also handles lists that were zero-initialized (data == NULL). */
static void mn_list_detach(MnList *list) {
    if (!list->data) {
        /* Zero-initialized list — allocate a fresh buffer */
        int64_t cap = list->cap > 0 ? list->cap : MN_LIST_INITIAL_CAP;
        list->data = mn_list_alloc_buf(cap, list->elem_size > 0 ? list->elem_size : 8);
        list->cap = cap;
        list->managed = 1;
        return;
    }
    if (!mn_list_is_managed(list)) return;  /* unmanaged buffer — nothing to detach */
    int64_t *rc = mn_list_rc(list);
    if (!rc) return;  /* corrupted magic — treat as sole owner */
    if (__atomic_load_n(rc, __ATOMIC_ACQUIRE) <= 1) return;  /* sole owner, no detach needed */
    atomic_fetch_add_explicit(&cow_detaches, 1, memory_order_relaxed);
    /* Shared — make a private copy */
    __atomic_fetch_sub(rc, 1, __ATOMIC_ACQ_REL);  /* decrement original's refcount */
    int64_t cap = list->cap > 0 ? list->cap : MN_LIST_INITIAL_CAP;
    char *new_data = mn_list_alloc_buf(cap, list->elem_size);
    if (list->len > 0) {
        memcpy(new_data, list->data, (size_t)(list->len * list->elem_size));
    }
    list->data = new_data;
    list->cap = cap;
}

MN_EXPORT MnList __mn_list_new(int64_t elem_size) {
    MnList list;
    list.elem_size = elem_size;
    list.len = 0;
    list.cap = 0;
    list.data = NULL;  /* Lazy allocation: first push allocates */
    list.managed = 0;  /* No COW header until first allocation */
    return list;
}

static void mn_list_grow(MnList *list) {
#ifdef MN_PROFILE_MEM
    atomic_fetch_add_explicit(&mn_grow_count, 1, memory_order_relaxed);
#endif
    int64_t new_cap = list->cap > 0 ? list->cap * 2 : MN_LIST_INITIAL_CAP;
    /* Allocate a fresh buffer instead of realloc.  Struct copies may share
     * the same data pointer (bitwise copy without refcount).  realloc would
     * free the old pointer, invalidating the alias.  New + memcpy is safe:
     * if sole owner we free old; if shared the alias keeps valid data. */
    char *old_data = list->data;
    int old_managed = list->managed;
    char *new_data = mn_list_alloc_buf(new_cap, list->elem_size);
    if (old_data && list->len > 0) {
        memcpy(new_data, old_data, (size_t)(list->len * list->elem_size));
    }
    list->data = new_data;
    list->managed = 1;
    list->cap = new_cap;
    /* Free the old buffer if we're the sole owner.  If shared (refcount > 1),
     * decrement but don't free — the other copy still references it. */
    if (old_data && old_managed) {
        int64_t *rc = ((int64_t *)old_data) - 2;
        if (rc[0] == MN_COW_MAGIC) {
            int64_t prev = __atomic_fetch_sub(&rc[1], 1, __ATOMIC_ACQ_REL);
            if (prev <= 1) {
                __mn_free(((char *)old_data) - MN_LIST_HEADER_SIZE);
            }
        }
    }
}

MN_EXPORT void __mn_list_push(MnList *list, const void *elem_ptr) {
    /* Validate list fields before any operation. Garbage from uninitialized
     * struct fields (lambda/recursive lowering) must not cause huge allocs. */
    if (!list->data || list->cap <= 0 || list->elem_size <= 0
        || list->elem_size > 65536 || list->cap > 100000000
        || list->len < 0 || list->len > list->cap) {
#ifndef NDEBUG
        if (list->data) {
            /* Non-NULL data with corrupted fields — compiler bug, not first push */
            fprintf(stderr, "FATAL: __mn_list_push received corrupted list "
                    "(data=%p len=%lld cap=%lld esz=%lld)\n",
                    (void *)list->data, (long long)list->len,
                    (long long)list->cap, (long long)list->elem_size);
            abort();
        }
#endif
        /* First push to empty list — initialize buffer */
        if (list->data) {
            fprintf(stderr, "WARNING: __mn_list_push: reinitializing corrupted list (data=%p len=%lld cap=%lld elem=%lld)\n",
                    (void *)list->data, (long long)list->len, (long long)list->cap, (long long)list->elem_size);
        }
        if (list->elem_size <= 0 || list->elem_size > 65536) list->elem_size = 8;
        list->data = mn_list_alloc_buf(MN_LIST_INITIAL_CAP, list->elem_size);
        list->cap = MN_LIST_INITIAL_CAP;
        list->len = 0;
        list->managed = 1;
    } else {
        mn_list_detach(list);  /* COW: ensure sole ownership */
    }
    if (list->len >= list->cap) {
        mn_list_grow(list);
    }
    memcpy(list->data + list->len * list->elem_size,
           elem_ptr, (size_t)list->elem_size);
    list->len++;
}


/* v4.31.0: the old ``__mn_list_oob_buf`` 4KB thread-local
 * zero-buffer workaround was removed. It papered over a Python
 * lowerer bug where ``break`` inside ``if`` inside ``for`` was
 * silently dropped, letting loops walk past ``list->len`` and
 * read stale memory. That bug was fixed in v4.14.0
 * (``tests/llvm/test_break_nested.py::test_break_in_if_in_for``
 * is the regression gate), but the workaround and its comment
 * survived two cleanup passes — Mamba flagged it in the v4.26.0
 * panel.
 *
 * v4.32.0: when v4.31.0 removed the workaround, __mn_list_get
 * began returning NULL on OOB — but the Python emitter at
 * ``emit_llvm_text.py:3101-3108`` unconditionally dereferences
 * the returned pointer. Viper V2 (arc-end panel) flagged this
 * as a segfault window: any program path that used to silently
 * read zeros now segfaults at a non-deterministic location.
 * The fix is to abort loudly AT THE RUNTIME CALL SITE — a
 * predictable crash with a diagnostic message, instead of a
 * pointer-deref segfault in emitted code. Silent zero reads
 * were a bug; NULL-deref segfaults were a worse bug; abort()
 * with a clear message is the right answer. */
MN_EXPORT void *__mn_list_get(MnList *list, int64_t i) {
    if (i < 0 || i >= list->len) {
        fprintf(stderr,
                "mapanare: list index %ld out of bounds (len=%ld)\n",
                (long)i, (long)list->len);
        abort();
    }
    void *result = list->data + i * list->elem_size;
    return result;
}

MN_EXPORT void __mn_list_set(MnList *list, int64_t i, const void *elem_ptr) {
    if (i < 0 || i >= list->len) {
        fprintf(stderr,
                "mapanare: list index %ld out of bounds (len=%ld)\n",
                (long)i, (long)list->len);
        abort();
    }
    mn_list_detach(list);  /* COW: ensure sole ownership */
    memcpy(list->data + i * list->elem_size,
           elem_ptr, (size_t)list->elem_size);
}

MN_EXPORT void __mn_debug_i64(int64_t val) {
    fprintf(stderr, "[DEBUG] i64=%ld\n", (long)val);
}

MN_EXPORT void __mn_debug_str(MnString s) {
    if (s.data && s.len > 0) {
        fprintf(stderr, "[DEBUG] str='%.*s' len=%ld\n", (int)s.len, mn_untag(s.data), (long)s.len);
    } else {
        fprintf(stderr, "[DEBUG] str=<empty> len=%ld data=%p\n", (long)s.len, (void*)s.data);
    }
}

MN_EXPORT void __mn_debug_list(MnList list) {
    fprintf(stderr, "[DEBUG] list data=%p len=%ld cap=%ld esz=%ld\n",
            (void*)list.data, (long)list.len, (long)list.cap, (long)list.elem_size);
}

MN_EXPORT int64_t __mn_list_len(MnList *list) {
    return list->len;
}

MN_EXPORT int64_t __mn_list_pop(MnList *list, void *out_ptr) {
    if (list->len <= 0) return -1;
    mn_list_detach(list);  /* COW */
    list->len--;
    memcpy(out_ptr, list->data + list->len * list->elem_size,
           (size_t)list->elem_size);
    return 0;
}

MN_EXPORT void __mn_list_clear(MnList *list) {
    mn_list_detach(list);  /* COW */
    list->len = 0;
}

MN_EXPORT void __mn_list_free(MnList *list) {
    if (list->data && list->managed) {
        int64_t *rc = mn_list_rc(list);
        if (rc) {
            int64_t prev = __atomic_fetch_sub(rc, 1, __ATOMIC_ACQ_REL);
            if (prev <= 1) {
                __mn_free(((char *)list->data) - MN_LIST_HEADER_SIZE);
            }
        }
        list->data = NULL;
    }
    list->len = 0;
    list->cap = 0;
    list->managed = 0;
}

/* Check if a list looks like it was properly allocated with a COW header */
static int mn_list_is_managed(MnList *list) {
    if (!list->data) return 0;
    /* The magic number check is the ONLY way to know if data[-16..-8] is valid.
     * Without it, reading data[-8] on a non-COW buffer is undefined behavior. */
    return mn_list_has_magic(list);
}

MN_EXPORT void __mn_cow_stats(void) {
    fprintf(stderr, "[COW] shares=%ld fallbacks=%ld detaches=%ld\n",
            (long)cow_shares, (long)cow_fallbacks, (long)cow_detaches);
}

MN_EXPORT MnList __mn_list_clone(MnList *src) {
#ifdef MN_PROFILE_MEM
    atomic_fetch_add_explicit(&mn_clone_count, 1, memory_order_relaxed);
#endif
    /* If the buffer is a managed COW buffer, share it (O(1)).
     * Otherwise, just copy the header (no allocation). */
    MnList dst;
    dst.elem_size = src->elem_size;
    dst.len = src->len;

    /* Validate ALL fields before touching data. Uninitialised struct fields
     * from lambda/recursive state passing can have garbage in every field. */
    if (!src->data || src->elem_size <= 0 || src->elem_size > 65536
        || src->cap <= 0 || src->cap > 100000000
        || src->len < 0 || src->len > src->cap) {
        /* Garbage or empty — just copy the raw header */
        dst.cap = src->cap;
        dst.data = src->data;
        dst.managed = src->managed;
        atomic_fetch_add_explicit(&cow_fallbacks, 1, memory_order_relaxed);
        return dst;
    }
    if (mn_list_has_magic(src)) {
        int64_t *rc = mn_list_rc(src);
        int64_t rc_val = rc ? __atomic_load_n(rc, __ATOMIC_ACQUIRE) : 0;
        if (rc && rc_val > 0 && rc_val < 10000000) {
            dst.cap = src->cap;
            dst.data = src->data;
            dst.managed = 1;
            __atomic_fetch_add(rc, 1, __ATOMIC_RELAXED);
            atomic_fetch_add_explicit(&cow_shares, 1, memory_order_relaxed);
            return dst;
        }
    }

    /* Not managed by COW — do a full memcpy clone for safety.
     * Extra size check: cap*elem_size must be reasonable (< 256MB). */
    {
        int64_t total = src->cap * src->elem_size;
        if (total <= 0 || total > 256 * 1024 * 1024) {
            /* Unreasonable size — just copy header */
            dst.cap = src->cap;
            dst.data = src->data;
            dst.managed = src->managed;
            atomic_fetch_add_explicit(&cow_fallbacks, 1, memory_order_relaxed);
            return dst;
        }
        dst.cap = src->cap;
        dst.data = mn_list_alloc_buf(dst.cap, src->elem_size);
        dst.managed = 1;
        if (src->len > 0) {
            memcpy(dst.data, src->data, (size_t)(src->len * src->elem_size));
        }
    }
    atomic_fetch_add_explicit(&cow_fallbacks, 1, memory_order_relaxed);
    return dst;
}

MN_EXPORT MnList __mn_list_deep_clone(MnList *src, const int64_t *list_offsets, int64_t num_offsets) {
    MnList dst = __mn_list_clone(src);
    if (num_offsets <= 0 || list_offsets == NULL || dst.len <= 0) return dst;
    /* Detach first — we're about to modify element data (nested list headers) */
    mn_list_detach(&dst);
    /* After detaching, recursively clone any nested MnList fields
     * at the given byte offsets within each element. */
    for (int64_t i = 0; i < dst.len; i++) {
        char *elem = dst.data + i * dst.elem_size;
        for (int64_t j = 0; j < num_offsets; j++) {
            MnList *nested = (MnList *)(elem + list_offsets[j]);
            if (nested->data && nested->len > 0) {
                *nested = __mn_list_clone(nested);
            }
        }
    }
    return dst;
}

MN_EXPORT MnList __mn_list_concat(MnList *a, MnList *b) {
    int64_t es = a->elem_size;
    MnList result = __mn_list_new(es);
    int64_t total = mn_checked_add(a->len, b->len);
    if (total > result.cap) {
        if (result.data == NULL) {
            /* Fresh allocation — __mn_list_new returns data=NULL */
            result.data = mn_list_alloc_buf(total, es);
            result.managed = 1;
        }
        result.cap = total;
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
    s.data = buf;
    s.len = (uint64_t)read;
    s.is_heap = 1;
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

/* Helper: MnString → null-terminated C string (caller must __mn_free) */
static char *mn_to_cstr(MnString s) {
    char *c = (char *)__mn_alloc(s.len + 1);
    memcpy(c, mn_untag(s.data), (size_t)s.len);
    c[s.len] = '\0';
    return c;
}

MN_EXPORT int64_t __mn_file_exists(MnString path) {
    char *cpath = mn_to_cstr(path);
    int exists = access(cpath, F_OK) == 0;
    __mn_free(cpath);
    return exists ? 1 : 0;
}

MN_EXPORT int64_t __mn_file_remove(MnString path) {
    char *cpath = mn_to_cstr(path);
    int rc = remove(cpath);
    __mn_free(cpath);
    return rc == 0 ? 0 : -1;
}

MN_EXPORT int64_t __mn_file_size(MnString path) {
    char *cpath = mn_to_cstr(path);
    struct stat st;
    int rc = stat(cpath, &st);
    __mn_free(cpath);
    return rc == 0 ? (int64_t)st.st_size : -1;
}

MN_EXPORT int64_t __mn_file_mtime(MnString path) {
    char *cpath = mn_to_cstr(path);
    struct stat st;
    int rc = stat(cpath, &st);
    __mn_free(cpath);
    return rc == 0 ? (int64_t)st.st_mtime : -1;
}

MN_EXPORT MnString __mn_realpath(MnString path) {
    char *cpath = mn_to_cstr(path);
    char resolved[4096];
    char *rp = realpath(cpath, resolved);
    __mn_free(cpath);
    if (!rp) return __mn_str_empty();
    return __mn_str_from_cstr(rp);
}

MN_EXPORT int64_t __mn_dir_create(MnString path, int64_t recursive) {
    char *cpath = mn_to_cstr(path);
    int rc = mkdir(cpath, 0755);
    __mn_free(cpath);
    (void)recursive; /* TODO: recursive mkdir */
    return rc == 0 ? 0 : -1;
}

MN_EXPORT int64_t __mn_dir_remove(MnString path) {
    char *cpath = mn_to_cstr(path);
    int rc = rmdir(cpath);
    __mn_free(cpath);
    return rc == 0 ? 0 : -1;
}

MN_EXPORT int64_t __mn_file_rename(MnString old_path, MnString new_path) {
    char *cold = mn_to_cstr(old_path);
    char *cnew = mn_to_cstr(new_path);
    int rc = rename(cold, cnew);
    __mn_free(cold);
    __mn_free(cnew);
    return rc == 0 ? 0 : -1;
}

MN_EXPORT int64_t __mn_file_copy(MnString src, MnString dst) {
    char *csrc = mn_to_cstr(src);
    char *cdst = mn_to_cstr(dst);
    FILE *fin = fopen(csrc, "rb");
    __mn_free(csrc);
    if (!fin) { __mn_free(cdst); return -1; }
    FILE *fout = fopen(cdst, "wb");
    __mn_free(cdst);
    if (!fout) { fclose(fin); return -1; }
    char buf[8192];
    size_t n;
    int err = 0;
    while ((n = fread(buf, 1, sizeof(buf), fin)) > 0) {
        size_t w = fwrite(buf, 1, n, fout);
        if (w < n) { err = 1; break; }
    }
    fclose(fin);
    fclose(fout);
    return err ? -1 : 0;
}

MN_EXPORT MnString __mn_tmpfile_path(void) {
    return __mn_str_from_cstr("/tmp/mn_tmp_XXXXXX");
}

MN_EXPORT MnString __mn_read_line(void) {
    /* v4.34.0: use getline(3) on POSIX for arbitrarily long lines instead
     * of the old 4KB fgets buffer that silently truncated long input. */
#if defined(_POSIX_C_SOURCE) || defined(__linux__) || defined(__APPLE__)
    char *line = NULL;
    size_t cap = 0;
    ssize_t n = getline(&line, &cap, stdin);
    if (n < 0) { free(line); return __mn_str_empty(); }
    /* Strip trailing newline/carriage-return */
    while (n > 0 && (line[n - 1] == '\n' || line[n - 1] == '\r')) n--;
    line[n] = '\0';
    MnString result = __mn_str_from_cstr(line);
    free(line);
    return result;
#else
    /* Windows fallback: loop fgets until we read a full line */
    size_t cap = 4096, len = 0;
    char *buf = (char *)malloc(cap);
    if (!buf) return __mn_str_empty();
    while (fgets(buf + len, (int)(cap - len), stdin)) {
        len += strlen(buf + len);
        if (len > 0 && buf[len - 1] == '\n') break;
        cap *= 2;
        char *tmp = (char *)realloc(buf, cap);
        if (!tmp) break;
        buf = tmp;
    }
    if (len == 0) { free(buf); return __mn_str_empty(); }
    if (len > 0 && buf[len - 1] == '\n') buf[--len] = '\0';
    if (len > 0 && buf[len - 1] == '\r') buf[--len] = '\0';
    MnString result = __mn_str_from_cstr(buf);
    free(buf);
    return result;
#endif
}

MN_EXPORT int64_t __mn_file_append(MnString path, MnString content) {
    char *cpath = mn_to_cstr(path);
    FILE *f = fopen(cpath, "ab");
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

MN_EXPORT MnList __mn_dir_list_strings(MnString path) {
    MnList list = __mn_list_new((int64_t)sizeof(MnString));
    char *cpath = mn_to_cstr(path);
    DIR *d = opendir(cpath);
    __mn_free(cpath);
    if (!d) return list;
    struct dirent *ent;
    while ((ent = readdir(d)) != NULL) {
        if (ent->d_name[0] == '.' &&
            (ent->d_name[1] == '\0' ||
             (ent->d_name[1] == '.' && ent->d_name[2] == '\0')))
            continue;
        MnString name = __mn_str_from_cstr(ent->d_name);
        __mn_list_push(&list, &name);
    }
    closedir(d);
    return list;
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
    int64_t  val_type;    /* MN_MAP_VAL_OPAQUE / STR */
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

MN_EXPORT MnMap *__mn_map_new(int64_t key_size, int64_t val_size, int64_t key_type, int64_t val_type) {
    MnMap *map = (MnMap *)__mn_alloc(sizeof(MnMap));
    map->key_size = key_size;
    map->val_size = val_size;
    map->key_type = key_type;
    /* Backward compat: old callers pass only 3 args (val_type is garbage).
       Accept 0 (OPAQUE) and 1 (STR) explicitly; anything else falls back to
       the size heuristic so pre-v3.34 compiled code still works. */
    if (val_type == MN_MAP_VAL_OPAQUE || val_type == MN_MAP_VAL_STR) {
        map->val_type = val_type;
    } else {
        map->val_type = (val_size == (int64_t)sizeof(MnString))
            ? MN_MAP_VAL_STR : MN_MAP_VAL_OPAQUE;
    }
    map->bucket_size = 2 + key_size + val_size;  /* status + psl + key + val */
    map->len = 0;
    map->cap = MN_MAP_INITIAL_CAP;
    map->buckets = (char *)__mn_alloc(mn_checked_mul(map->cap, map->bucket_size));
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

    /* Stack buffer for Robin Hood swaps (avoids malloc per insert).
     * Falls back to heap for very large keys+values (> 512 bytes). */
    char stack_buf[512];
    int64_t entry_size = map->key_size + map->val_size;
    char *temp = (entry_size <= (int64_t)sizeof(stack_buf))
        ? stack_buf
        : (char *)__mn_alloc(entry_size);
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
            if (temp != stack_buf) __mn_free(temp);
            return;
        }

        /* Check if key already exists → update value */
        if (status == MN_BUCKET_OCCUPIED && eq(mn_bucket_key(bucket), temp)) {
            memcpy(mn_bucket_val(bucket, map->key_size),
                   temp + map->key_size, (size_t)map->val_size);
            if (temp != stack_buf) __mn_free(temp);
            return;
        }

        /* Robin Hood: if our PSL > existing PSL, swap and continue */
        if (status == MN_BUCKET_OCCUPIED && psl > mn_bucket_psl(bucket)) {
            /* Swap current entry with bucket contents */
            uint8_t old_psl = mn_bucket_psl(bucket);
            char *old_key = mn_bucket_key(bucket);
            char *old_val = mn_bucket_val(bucket, map->key_size);

            /* Save old bucket data into temp via in-place swap.
             * We reuse the same temp buffer — no extra allocation needed. */
            char swap_buf[512];
            char *swap = (entry_size <= (int64_t)sizeof(swap_buf))
                ? swap_buf
                : (char *)__mn_alloc(entry_size);
            memcpy(swap, old_key, (size_t)map->key_size);
            memcpy(swap + map->key_size, old_val, (size_t)map->val_size);

            /* Write new data into bucket */
            bucket[1] = (char)psl;
            memcpy(old_key, temp, (size_t)map->key_size);
            memcpy(old_val, temp + map->key_size, (size_t)map->val_size);

            /* Continue inserting displaced entry */
            memcpy(temp, swap, (size_t)entry_size);
            psl = old_psl;
            if (swap != swap_buf) __mn_free(swap);
        }

        psl++;
        if (psl == 255) {
            /* PSL overflow — map is pathologically full. Force a grow to
             * redistribute entries and keep PSL values bounded. */
            if (temp != stack_buf) __mn_free(temp);
            mn_map_grow(map);
            /* Retry the insert from scratch after rehash */
            __mn_map_set(map, key, val);
            return;
        }
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
    map->buckets = (char *)__mn_alloc(mn_checked_mul(map->cap, map->bucket_size));
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

MN_EXPORT MnList __mn_map_keys(MnMap *map) {
    MnList lst = __mn_list_new(sizeof(MnString));
    if (!map) return lst;
    MnMapIter *iter = __mn_map_iter_new(map);
    void *key_out, *val_out;
    while (__mn_map_iter_next(iter, &key_out, &val_out)) {
        /* key_out points to the stored key; for string maps, that's an MnString */
        __mn_list_push(&lst, key_out);
    }
    __mn_map_iter_free(iter);
    return lst;
}

MN_EXPORT void __mn_map_free(MnMap *map) {
    if (map) {
        if (map->buckets) __mn_free(map->buckets);
        __mn_free(map);
    }
}

MN_EXPORT void __mn_map_free_deep(MnMap *map) {
    if (!map) return;
    if (map->buckets) {
        for (int64_t i = 0; i < map->cap; i++) {
            char *bucket = mn_bucket_at(map, i);
            if ((uint8_t)bucket[0] != MN_BUCKET_OCCUPIED) continue;
            /* Free string keys */
            if (map->key_type == MN_MAP_KEY_STR) {
                MnString *key = (MnString *)(bucket + 2);
                __mn_str_free(*key);
            }
            /* Free string values using explicit val_type tag */
            if (map->val_type == MN_MAP_VAL_STR) {
                MnString *val = (MnString *)(bucket + 2 + map->key_size);
                __mn_str_free(*val);
            }
        }
        __mn_free(map->buckets);
    }
    __mn_free(map);
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

    /* Optional destructor for value cleanup (NULL = no-op) */
    void      (*dtor)(void *value);

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

/* --- Batching state (global, mutex-protected for thread safety) --- */

static int64_t    mn_signal_batch_depth = 0;
static MnSignal  *mn_signal_batch_pending[MN_SIGNAL_MAX_PENDING];
static int64_t    mn_signal_batch_pending_len = 0;

/* --- Mutex protection for global signal state --- */

#ifdef _WIN32
#include <windows.h>
/*
 * v4.28.0: replaced the prior ``InterlockedCompareExchange`` /
 * ``volatile LONG`` double-checked-locking pattern (flagged by Cobra #5 in
 * the v4.26.0 panel — the Windows memory model does not guarantee that the
 * ``InitializeCriticalSection`` write is visible to a thread that observed
 * the flag transition) with ``InitOnceExecuteOnce``, which is the
 * canonical Windows one-shot initializer and provides the right release /
 * acquire barriers on flag + payload. Do not reintroduce the CAS pattern
 * here: the panel explicitly called it out.
 */
static CRITICAL_SECTION mn_signal_mutex;
static INIT_ONCE mn_signal_mutex_once = INIT_ONCE_STATIC_INIT;
static BOOL CALLBACK mn_signal_mutex_init_cb(PINIT_ONCE once, PVOID param, PVOID *ctx) {
    (void)once; (void)param; (void)ctx;
    InitializeCriticalSection(&mn_signal_mutex);
    return TRUE;
}
static inline void mn_signal_ensure_mutex(void) {
    InitOnceExecuteOnce(&mn_signal_mutex_once, mn_signal_mutex_init_cb, NULL, NULL);
}
static inline void mn_signal_lock(void)   { mn_signal_ensure_mutex(); EnterCriticalSection(&mn_signal_mutex); }
static inline void mn_signal_unlock(void) { LeaveCriticalSection(&mn_signal_mutex); }
#else
#include <pthread.h>
/* v4.32.0 Phase 2.5 (Viper M2): the signal mutex must be RECURSIVE because
 * mn_signal_recompute now acquires the lock, and compute_fn may call
 * __mn_signal_get → __mn_signal_subscribe → mn_signal_lock again (a
 * standard reactive-graph pattern: reading a dependency while evaluating
 * a computed signal). Windows CRITICAL_SECTION is always recursive; on
 * POSIX we must explicitly set PTHREAD_MUTEX_RECURSIVE.
 *
 * Lock ordering: topological / depth-first. mn_signal_propagate holds
 * the lock for a snapshot, releases it, then recomputes each subscriber
 * (which re-acquires). Because recompute may call __mn_signal_get on
 * dependency signals that are already evaluated (not dirty), the
 * recursive mutex handles the nesting without deadlock. */
static pthread_mutex_t mn_signal_mutex;
static pthread_once_t mn_signal_mutex_once_flag = PTHREAD_ONCE_INIT;
static void mn_signal_mutex_init(void) {
    pthread_mutexattr_t attr;
    pthread_mutexattr_init(&attr);
    pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
    pthread_mutex_init(&mn_signal_mutex, &attr);
    pthread_mutexattr_destroy(&attr);
}
static inline void mn_signal_lock(void)   {
    pthread_once(&mn_signal_mutex_once_flag, mn_signal_mutex_init);
    pthread_mutex_lock(&mn_signal_mutex);
}
static inline void mn_signal_unlock(void) { pthread_mutex_unlock(&mn_signal_mutex); }
#endif

/* --- Dependency tracking context (for auto-tracking) --- */

static _Thread_local MnSignal *mn_signal_tracking_context = NULL;

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

    sig->dtor = NULL;
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

    /*
     * v4.28.0: the memcmp / dtor / memcpy trio used to run OUTSIDE the lock,
     * racing any concurrent ``__mn_signal_set`` on the same signal (v4.26.0
     * panel: Viper H5, Mamba H1). Now the entire value-mutation critical
     * section runs under ``mn_signal_mutex``: readers that hold the lock
     * observe either the full old value or the full new value, never a
     * torn intermediate. Propagation is still called outside the lock so
     * that callbacks that call back into ``__mn_signal_set`` (a common
     * reactive pattern) do not deadlock.
     */
    mn_signal_lock();

    /* Check if value actually changed (memcmp) */
    int changed = 1;
    if (signal->val_size > 0
        && memcmp(signal->value, value, (size_t)signal->val_size) == 0) {
        changed = 0;
    }

    if (!changed) {
        mn_signal_unlock();
        return;  /* No change, skip propagation */
    }

    /* Call destructor on old value before overwriting — still under lock
     * because the destructor reads ``signal->value`` and a concurrent set
     * could otherwise free the same pointer twice. */
    if (signal->dtor) signal->dtor(signal->value);
    memcpy(signal->value, value, (size_t)signal->val_size);

    if (mn_signal_batch_depth > 0) {
        /* Defer propagation: add to pending list */
        if (mn_signal_batch_pending_len >= MN_SIGNAL_MAX_PENDING) {
            /* Overflow: flush the batch immediately, then restart */
            int64_t count = mn_signal_batch_pending_len;
            mn_signal_batch_pending_len = 0;
            mn_signal_unlock();
            for (int64_t i = 0; i < count; i++) {
                mn_signal_propagate(mn_signal_batch_pending[i]);
            }
            mn_signal_lock();
        }
        /* Avoid duplicates */
        int64_t found = 0;
        for (int64_t i = 0; i < mn_signal_batch_pending_len; i++) {
            if (mn_signal_batch_pending[i] == signal) { found = 1; break; }
        }
        if (!found) {
            mn_signal_batch_pending[mn_signal_batch_pending_len++] = signal;
        }
        mn_signal_unlock();
    } else {
        mn_signal_unlock();
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

/* v4.32.0 Phase 2.5 (Viper M2): mn_signal_recompute now runs under
 * the signal mutex. This closes the race where a reader on another
 * thread sees a half-written ``signal->value`` during a concurrent
 * propagation-triggered recompute. The lock is recursive so
 * compute_fn can safely call __mn_signal_get (which acquires the
 * same mutex via mn_signal_lock). */
static void mn_signal_recompute(MnSignal *signal) {
    if (signal->compute_fn == NULL) return;

    mn_signal_lock();

    /* Push tracking context */
    MnSignal *prev_context = mn_signal_tracking_context;
    mn_signal_tracking_context = signal;

    signal->compute_fn(signal->value, signal->compute_user_data);
    signal->dirty = 0;

    /* Pop tracking context */
    mn_signal_tracking_context = prev_context;

    mn_signal_unlock();
}

/* --- Subscribe / Unsubscribe --- */

MN_EXPORT void __mn_signal_subscribe(MnSignal *signal, MnSignal *subscriber) {
    mn_signal_lock();
    /* Check for duplicates */
    for (int64_t i = 0; i < signal->sub_len; i++) {
        if (signal->subscribers[i] == subscriber) { mn_signal_unlock(); return; }
    }
    /* Grow if needed */
    if (signal->sub_len >= signal->sub_cap) {
        int64_t new_cap = signal->sub_cap * 2;
        signal->subscribers = (MnSignal **)__mn_realloc(
            signal->subscribers, new_cap * (int64_t)sizeof(MnSignal *));
        signal->sub_cap = new_cap;
    }
    signal->subscribers[signal->sub_len++] = subscriber;
    mn_signal_unlock();
}

MN_EXPORT void __mn_signal_unsubscribe(MnSignal *signal, MnSignal *subscriber) {
    mn_signal_lock();
    for (int64_t i = 0; i < signal->sub_len; i++) {
        if (signal->subscribers[i] == subscriber) {
            /* Shift remaining elements */
            for (int64_t j = i; j < signal->sub_len - 1; j++) {
                signal->subscribers[j] = signal->subscribers[j + 1];
            }
            signal->sub_len--;
            /* Null out the vacated slot to prevent dangling references */
            signal->subscribers[signal->sub_len] = NULL;
            mn_signal_unlock();
            return;
        }
    }
    mn_signal_unlock();
}

/* --- Callbacks --- */

MN_EXPORT void __mn_signal_on_change(MnSignal *signal, MnSignalCallback cb, void *user_data) {
    mn_signal_lock();
    if (signal->cb_len >= signal->cb_cap) { mn_signal_unlock(); return; }
    signal->callbacks[signal->cb_len].fn = cb;
    signal->callbacks[signal->cb_len].user_data = user_data;
    signal->cb_len++;
    mn_signal_unlock();
}

/* --- Propagation (topological, depth-first) --- */

/* v4.33.0 Phase 4.1 (Viper, 8th cycle): depth limit for the recursive
 * propagation DFS. A pathological computed-signal chain overflows the
 * stack without a bound. 1024 is generous — real-world reactive graphs
 * are typically < 20 deep. */
#define MN_SIGNAL_PROPAGATE_MAX_DEPTH 1024
static _Thread_local int64_t mn_signal_propagate_depth = 0;

static void mn_signal_propagate(MnSignal *signal) {
    if (mn_signal_propagate_depth >= MN_SIGNAL_PROPAGATE_MAX_DEPTH) {
        fprintf(stderr,
                "mapanare: signal propagation depth %ld exceeds max %d "
                "— likely a cycle in the computed-signal graph\n",
                (long)mn_signal_propagate_depth,
                MN_SIGNAL_PROPAGATE_MAX_DEPTH);
        abort();
    }
    mn_signal_propagate_depth++;

    /* Snapshot subscriber list under the lock so realloc in subscribe
     * cannot invalidate our iteration pointer. */
    mn_signal_lock();
    int64_t n = signal->sub_len;
    MnSignal **snap = NULL;
    if (n > 0) {
        snap = (MnSignal **)__mn_alloc(n * (int64_t)sizeof(MnSignal *));
        memcpy(snap, signal->subscribers, (size_t)(n * (int64_t)sizeof(MnSignal *)));
    }
    mn_signal_unlock();

    /* 1. Mark all subscribers dirty */
    for (int64_t i = 0; i < n; i++) {
        snap[i]->dirty = 1;
    }

    /* 2. Re-evaluate computed subscribers and propagate recursively.
     *    This is a depth-first topological traversal: each computed signal
     *    is recomputed before its own subscribers are notified. */
    for (int64_t i = 0; i < n; i++) {
        MnSignal *sub = snap[i];
        if (sub->compute_fn != NULL && sub->dirty) {
            mn_signal_recompute(sub);
            mn_signal_propagate(sub);
        }
    }

    if (snap) __mn_free(snap);

    /* 3. Fire callbacks on this signal */
    for (int64_t i = 0; i < signal->cb_len; i++) {
        signal->callbacks[i].fn(signal->value, signal->callbacks[i].user_data);
    }

    mn_signal_propagate_depth--;
}

/* --- Batching --- */

MN_EXPORT void __mn_signal_batch_begin(void) {
    mn_signal_lock();
    mn_signal_batch_depth++;
    mn_signal_unlock();
}

MN_EXPORT void __mn_signal_batch_end(void) {
    mn_signal_lock();
    if (mn_signal_batch_depth <= 0) {
        mn_signal_unlock();
        return;
    }
    mn_signal_batch_depth--;
    if (mn_signal_batch_depth == 0) {
        /* Snapshot and clear pending list under the lock */
        int64_t count = mn_signal_batch_pending_len;
        MnSignal *local_pending[MN_SIGNAL_MAX_PENDING];
        for (int64_t i = 0; i < count; i++) {
            local_pending[i] = mn_signal_batch_pending[i];
        }
        mn_signal_batch_pending_len = 0;
        mn_signal_unlock();
        /* Propagate outside the lock to avoid deadlock */
        for (int64_t i = 0; i < count; i++) {
            mn_signal_propagate(local_pending[i]);
        }
    } else {
        mn_signal_unlock();
    }
}

/* --- Free --- */

MN_EXPORT void __mn_signal_free(MnSignal *signal) {
    if (!signal) return;

    /* Acquire lock, detach arrays, release lock. Then free outside lock
     * to avoid holding the mutex during deallocation. */
    MnSignal **deps = NULL;
    int64_t dep_len = 0;
    MnSignal **subs = NULL;
    MnSignal **cbs = NULL;

    mn_signal_lock();
    /* Unsubscribe from dependencies while holding the lock. */
    deps = signal->dependencies;
    dep_len = signal->dep_len;
    for (int64_t i = 0; i < dep_len; i++) {
        __mn_signal_unsubscribe(deps[i], signal);
    }
    signal->dependencies = NULL;
    signal->dep_len = 0;

    subs = signal->subscribers;
    signal->subscribers = NULL;
    signal->sub_len = 0;

    cbs = (MnSignal **)signal->callbacks;
    signal->callbacks = NULL;
    signal->cb_len = 0;
    mn_signal_unlock();

    /* Free arrays outside the lock. */
    if (deps) __mn_free(deps);
    if (subs) __mn_free(subs);
    if (cbs) __mn_free(cbs);

    if (signal->value) {
        if (signal->dtor) signal->dtor(signal->value);
        __mn_free(signal->value);
    }
    signal->value = NULL;
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
    /* Free closure environment if present (v4.3.0). */
    if (stream->user_data) {
        __mn_free(stream->user_data);
    }
    __mn_free(stream);
}

MN_EXPORT void __mn_stream_free_chain(MnStream *stream) {
    while (stream) {
        MnStream *source = stream->source;
        __mn_stream_free(stream);
        stream = source;
    }
}

/* -----------------------------------------------------------------------
 * Process + CLI arguments
 * ----------------------------------------------------------------------- */

/* Saved by __mn_argv_init() (called from mnc_main.c or a Mapanare main). */
static int    g_argc = 0;
static char **g_argv = NULL;

MN_EXPORT void __mn_argv_init(int argc, char **argv) {
    g_argc = argc;
    g_argv = argv;
}

MN_EXPORT int64_t __mn_argc(void) {
    return (int64_t)g_argc;
}

MN_EXPORT MnString __mn_argv(int64_t index) {
    if (index < 0 || index >= g_argc || !g_argv) {
        return __mn_str_empty();
    }
    return __mn_str_from_cstr(g_argv[index]);
}

/** Read a file, returning its content. Returns empty string on error
 *  (Mapanare callers distinguish by checking ``len(result) > 0``).
 *  v4.100.0: the previous len=-1 sentinel no longer fits because ``len``
 *  is a 63-bit unsigned bitfield; empty/failure collapse into the same
 *  zero-length string, matching how every caller already checked it. */
MN_EXPORT MnString __mn_file_read_or_empty(MnString path) {
    int64_t ok = 0;
    MnString result = __mn_file_read(path, &ok);
    if (!ok) {
        return __mn_str_empty();
    }
    return result;
}

MN_EXPORT void __mn_exit(int64_t code) {
    exit((int)code);
}

MN_EXPORT int64_t __mn_system(MnString command) {
    char *cmd = mn_to_cstr(command);
#if (defined(__APPLE__) && defined(TARGET_OS_IPHONE) && TARGET_OS_IPHONE) || \
    (defined(__APPLE__) && defined(__ENVIRONMENT_IPHONE_OS_VERSION_MIN_REQUIRED__))
    /* system() is unavailable on iOS */
    __mn_free(cmd);
    return -1;
#elif defined(_WIN32)
    int ret = system(cmd);
    __mn_free(cmd);
    return (int64_t)ret;
#else
    int ret = system(cmd);
    __mn_free(cmd);
    if (ret == -1) return -1;
    if (WIFEXITED(ret)) return (int64_t)WEXITSTATUS(ret);
    return -1;
#endif
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

MN_EXPORT void *__mn_range(int64_t start, int64_t end) {
    MnRangeIter *iter = (MnRangeIter *)malloc(sizeof(MnRangeIter));
    if (!iter) {
        fprintf(stderr, "mapanare: out of memory in __mn_range\n");
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

MN_EXPORT void __mn_range_free(void *iter_ptr) {
    free(iter_ptr);
}

/* -----------------------------------------------------------------------
 * Function Type Registry — global, static, outside LowerState
 *
 * Simple open-addressing hash table. Fixed capacity of 4096 entries.
 * Used by the self-hosted compiler to track fn name → return type
 * without polluting LowerState (which gets deep-cloned on every copy).
 * ----------------------------------------------------------------------- */

#define MN_TYPEREG_CAP 4096

typedef struct {
    char     fn_name[256];
    char     kind[64];
    char     type_name[256];
    int      occupied;
} MnTypeRegEntry;

static MnTypeRegEntry mn_type_reg[MN_TYPEREG_CAP];

/*
 * v4.28.0: the type registry used to be an unlocked global hash table
 * (v4.26.0 panel: Viper H5). Under concurrent ``__mn_type_registry_put``
 * calls, two threads could scribble on the same entry mid-probe. Reads
 * were racing with writes too. This rwlock lets many readers proceed in
 * parallel while serialising writers — the common case in the self-hosted
 * compiler is many lookups vs. rare inserts during module lowering, so a
 * reader-writer lock is the right primitive.
 *
 * Windows has no ``pthread_rwlock_t``; SRWLOCK is the native equivalent.
 */
#ifdef _WIN32
static SRWLOCK mn_typereg_lock = SRWLOCK_INIT;
static inline void mn_typereg_read_lock(void)    { AcquireSRWLockShared(&mn_typereg_lock); }
static inline void mn_typereg_read_unlock(void)  { ReleaseSRWLockShared(&mn_typereg_lock); }
static inline void mn_typereg_write_lock(void)   { AcquireSRWLockExclusive(&mn_typereg_lock); }
static inline void mn_typereg_write_unlock(void) { ReleaseSRWLockExclusive(&mn_typereg_lock); }
#else
static pthread_rwlock_t mn_typereg_lock = PTHREAD_RWLOCK_INITIALIZER;
static inline void mn_typereg_read_lock(void)    { pthread_rwlock_rdlock(&mn_typereg_lock); }
static inline void mn_typereg_read_unlock(void)  { pthread_rwlock_unlock(&mn_typereg_lock); }
static inline void mn_typereg_write_lock(void)   { pthread_rwlock_wrlock(&mn_typereg_lock); }
static inline void mn_typereg_write_unlock(void) { pthread_rwlock_unlock(&mn_typereg_lock); }
#endif

static uint32_t mn_typereg_hash(const char *s, int64_t len) {
    uint32_t h = 5381;
    for (int64_t i = 0; i < len; i++)
        h = ((h << 5) + h) + (uint8_t)s[i];
    return h;
}

MN_EXPORT void __mn_type_registry_put(MnString fn_name, MnString kind, MnString type_name) {
    if (fn_name.len <= 0 || fn_name.data == NULL) return;
    const char *fdata = mn_untag(fn_name.data);
    int64_t flen = fn_name.len > 255 ? 255 : fn_name.len;
    uint32_t idx = mn_typereg_hash(fdata, fn_name.len) % MN_TYPEREG_CAP;

    mn_typereg_write_lock();
    for (int probe = 0; probe < MN_TYPEREG_CAP; probe++) {
        uint32_t i = (idx + probe) % MN_TYPEREG_CAP;
        if (!mn_type_reg[i].occupied ||
            (mn_type_reg[i].fn_name[flen] == '\0' &&
             memcmp(mn_type_reg[i].fn_name, fdata, (size_t)flen) == 0)) {
            memcpy(mn_type_reg[i].fn_name, fdata, (size_t)flen);
            mn_type_reg[i].fn_name[flen] = '\0';

            const char *kdata = mn_untag(kind.data);
            int64_t klen = kind.len > 63 ? 63 : kind.len;
            if (kdata && klen > 0) {
                memcpy(mn_type_reg[i].kind, kdata, (size_t)klen);
            }
            mn_type_reg[i].kind[klen] = '\0';

            const char *tdata = mn_untag(type_name.data);
            int64_t tlen = type_name.len > 255 ? 255 : type_name.len;
            if (tdata && tlen > 0) {
                memcpy(mn_type_reg[i].type_name, tdata, (size_t)tlen);
            }
            mn_type_reg[i].type_name[tlen] = '\0';

            mn_type_reg[i].occupied = 1;
            mn_typereg_write_unlock();
            return;
        }
    }
    mn_typereg_write_unlock();
}

/* Caller must hold the read lock. Populates *out_kind / *out_type_name
 * with a snapshot-on-success so readers can release the lock before
 * allocating a Mapanare string from the buffers. */
static int mn_typereg_snapshot(MnString fn_name,
                                char *out_kind, size_t kind_cap,
                                char *out_type_name, size_t type_cap) {
    if (fn_name.len <= 0 || fn_name.data == NULL) return 0;
    const char *fdata = mn_untag(fn_name.data);
    uint32_t idx = mn_typereg_hash(fdata, fn_name.len) % MN_TYPEREG_CAP;

    for (int probe = 0; probe < MN_TYPEREG_CAP; probe++) {
        uint32_t i = (idx + probe) % MN_TYPEREG_CAP;
        if (!mn_type_reg[i].occupied) return 0;
        int64_t flen = fn_name.len > 255 ? 255 : fn_name.len;
        if (mn_type_reg[i].fn_name[flen] == '\0' &&
            memcmp(mn_type_reg[i].fn_name, fdata, (size_t)flen) == 0) {
            if (out_kind && kind_cap > 0) {
                strncpy(out_kind, mn_type_reg[i].kind, kind_cap - 1);
                out_kind[kind_cap - 1] = '\0';
            }
            if (out_type_name && type_cap > 0) {
                strncpy(out_type_name, mn_type_reg[i].type_name, type_cap - 1);
                out_type_name[type_cap - 1] = '\0';
            }
            return 1;
        }
    }
    return 0;
}

MN_EXPORT MnString __mn_type_registry_get_kind(MnString fn_name) {
    char kind_buf[64] = {0};
    mn_typereg_read_lock();
    int found = mn_typereg_snapshot(fn_name, kind_buf, sizeof(kind_buf), NULL, 0);
    mn_typereg_read_unlock();
    if (found) return __mn_str_from_cstr(kind_buf);
    return __mn_str_empty();
}

MN_EXPORT MnString __mn_type_registry_get_name(MnString fn_name) {
    char name_buf[256] = {0};
    mn_typereg_read_lock();
    int found = mn_typereg_snapshot(fn_name, NULL, 0, name_buf, sizeof(name_buf));
    mn_typereg_read_unlock();
    if (found) return __mn_str_from_cstr(name_buf);
    return __mn_str_empty();
}

MN_EXPORT void __mn_type_registry_clear(void) {
    mn_typereg_write_lock();
    memset(mn_type_reg, 0, sizeof(mn_type_reg));
    mn_typereg_write_unlock();
}

/* -----------------------------------------------------------------------
 * Clock / sleep — used by stdlib/time.mn
 * ----------------------------------------------------------------------- */

#ifndef _WIN32
#include <time.h>
#endif

MN_EXPORT int64_t __mn_clock_monotonic_ns(void) {
#ifndef _WIN32
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000LL + (int64_t)ts.tv_nsec;
#else
    static LARGE_INTEGER freq = {0};
    LARGE_INTEGER now;
    if (!freq.QuadPart) QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&now);
    return (int64_t)((double)now.QuadPart / (double)freq.QuadPart * 1e9);
#endif
}

MN_EXPORT void __mn_sleep_ms(int64_t ms) {
#ifndef _WIN32
    struct timespec req;
    req.tv_sec  = ms / 1000;
    req.tv_nsec = (ms % 1000) * 1000000L;
    nanosleep(&req, NULL);
#else
    Sleep((DWORD)ms);
#endif
}

/* -----------------------------------------------------------------------
 * Dynamic `any` type — boxing / unboxing / tag inspection
 * ----------------------------------------------------------------------- */

MN_EXPORT MnValue __mn_any_box_int(int64_t v) {
    MnValue val;
    val.tag = MN_TAG_INT;
    val._pad = 0;
    val.data.i = v;
    return val;
}

MN_EXPORT MnValue __mn_any_box_float(double v) {
    MnValue val;
    val.tag = MN_TAG_FLOAT;
    val._pad = 0;
    val.data.f = v;
    return val;
}

MN_EXPORT MnValue __mn_any_box_bool(uint8_t v) {
    MnValue val;
    val.tag = MN_TAG_BOOL;
    val._pad = 0;
    val.data.b = v;
    return val;
}

MN_EXPORT int64_t __mn_any_unbox_int(MnValue v) {
    if (v.tag != MN_TAG_INT) {
        fprintf(stderr, "TypeError: expected Int, got tag %d\n", v.tag);
        abort();
    }
    return v.data.i;
}

MN_EXPORT double __mn_any_unbox_float(MnValue v) {
    if (v.tag != MN_TAG_FLOAT) {
        fprintf(stderr, "TypeError: expected Float, got tag %d\n", v.tag);
        abort();
    }
    return v.data.f;
}

MN_EXPORT int32_t __mn_any_tag(MnValue v) {
    return v.tag;
}

static const char *mn_tag_names[] = {
    "Int", "Float", "Bool", "String",
    "List", "Map", "Struct", "Enum",
    "Fn", "Option", "Result", "None",
};
#define MN_TAG_COUNT (int)(sizeof(mn_tag_names) / sizeof(mn_tag_names[0]))
static MnString mn_tag_strings[12];
static MnString mn_tag_unknown;

/*
 * v4.28.0: ``mn_init_tag_strings`` used to be a hand-rolled "if (init)
 * return; ...; init = 1" guard — the classic racy double-check without a
 * memory barrier or mutex. Two concurrent callers could both run the
 * init loop and scribble on ``mn_tag_strings[]`` at the same time. The
 * v4.26.0 panel (Mamba) flagged this as the **7th** cycle carry-forward:
 * the fix has been on the wishlist for seven review cycles without
 * landing. It lands now, on the canonical primitive for each platform:
 * ``pthread_once`` on POSIX, ``InitOnceExecuteOnce`` on Windows.
 */
#ifdef _WIN32
static INIT_ONCE mn_tag_strings_once = INIT_ONCE_STATIC_INIT;
static BOOL CALLBACK mn_init_tag_strings_cb(PINIT_ONCE once, PVOID param, PVOID *ctx) {
    (void)once; (void)param; (void)ctx;
    for (int i = 0; i < MN_TAG_COUNT; i++)
        mn_tag_strings[i] = __mn_str_from_cstr(mn_tag_names[i]);
    mn_tag_unknown = __mn_str_from_cstr("Unknown");
    return TRUE;
}
static void mn_init_tag_strings(void) {
    InitOnceExecuteOnce(&mn_tag_strings_once, mn_init_tag_strings_cb, NULL, NULL);
}
#else
static pthread_once_t mn_tag_strings_once = PTHREAD_ONCE_INIT;
static void mn_init_tag_strings_impl(void) {
    for (int i = 0; i < MN_TAG_COUNT; i++)
        mn_tag_strings[i] = __mn_str_from_cstr(mn_tag_names[i]);
    mn_tag_unknown = __mn_str_from_cstr("Unknown");
}
static void mn_init_tag_strings(void) {
    pthread_once(&mn_tag_strings_once, mn_init_tag_strings_impl);
}
#endif

MN_EXPORT MnString __mn_any_typename(MnValue v) {
    mn_init_tag_strings();
    int idx = v.tag;
    if (idx >= 0 && idx < MN_TAG_COUNT) {
        return mn_tag_strings[idx];
    }
    return mn_tag_unknown;
}
