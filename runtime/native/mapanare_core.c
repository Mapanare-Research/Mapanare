/**
 * mapanare_core.c — Core runtime implementation for Mapanare self-hosting.
 *
 * Provides string, list, file I/O, and memory operations that native-compiled
 * Mapanare programs link against.
 */

#include "mapanare_core.h"

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
    s.data = buf;
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
    s.data = buf;
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
    int64_t total = a.len + b.len;
    if (total == 0) {
        return __mn_str_empty();
    }
    char *buf = (char *)__mn_alloc(total + 1);
    if (a.len > 0) memcpy(buf, a.data, (size_t)a.len);
    if (b.len > 0) memcpy(buf + a.len, b.data, (size_t)b.len);
    buf[total] = '\0';
    MnString s;
    s.data = buf;
    s.len = total;
    return s;
}

MN_EXPORT MnString __mn_str_char_at(MnString s, int64_t i) {
    if (i < 0 || i >= s.len) {
        return __mn_str_empty();
    }
    return __mn_str_from_parts(s.data + i, 1);
}

MN_EXPORT int64_t __mn_str_byte_at(MnString s, int64_t i) {
    if (i < 0 || i >= s.len) {
        return -1;
    }
    return (int64_t)(unsigned char)s.data[i];
}

MN_EXPORT int64_t __mn_str_len(MnString s) {
    return s.len;
}

MN_EXPORT int64_t __mn_str_eq(MnString a, MnString b) {
    if (a.len != b.len) return 0;
    if (a.len == 0) return 1;
    return memcmp(a.data, b.data, (size_t)a.len) == 0 ? 1 : 0;
}

MN_EXPORT int64_t __mn_str_cmp(MnString a, MnString b) {
    int64_t min_len = a.len < b.len ? a.len : b.len;
    if (min_len > 0) {
        int cmp = memcmp(a.data, b.data, (size_t)min_len);
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
    return __mn_str_from_parts(s.data + start, end - start);
}

MN_EXPORT int64_t __mn_str_starts_with(MnString s, MnString prefix) {
    if (prefix.len > s.len) return 0;
    if (prefix.len == 0) return 1;
    return memcmp(s.data, prefix.data, (size_t)prefix.len) == 0 ? 1 : 0;
}

MN_EXPORT int64_t __mn_str_ends_with(MnString s, MnString suffix) {
    if (suffix.len > s.len) return 0;
    if (suffix.len == 0) return 1;
    return memcmp(s.data + s.len - suffix.len, suffix.data,
                  (size_t)suffix.len) == 0 ? 1 : 0;
}

MN_EXPORT int64_t __mn_str_find(MnString haystack, MnString needle) {
    if (needle.len == 0) return 0;
    if (needle.len > haystack.len) return -1;
    for (int64_t i = 0; i <= haystack.len - needle.len; i++) {
        if (memcmp(haystack.data + i, needle.data, (size_t)needle.len) == 0) {
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
    /* Don't free empty string constant or string literals in .rodata */
    if (s.data && s.len > 0 && s.data[0] != '\0') {
        /* Heuristic: only free if the pointer looks heap-allocated.
         * In practice, we always heap-allocate in __mn_str_from_parts,
         * and constant strings from LLVM globals should not be freed.
         * We rely on the caller not freeing constants. */
        /* For now, we accept the leak for constant strings. A proper
         * solution would use a tag bit or arena allocator. */
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
        fwrite(s.data, 1, (size_t)s.len, stderr);
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
    char *cpath = (char *)__mn_alloc(path.len + 1);
    memcpy(cpath, path.data, (size_t)path.len);
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
    s.len = (int64_t)read;
    *ok = 1;
    return s;
}

MN_EXPORT int64_t __mn_file_write(MnString path, MnString content) {
    char *cpath = (char *)__mn_alloc(path.len + 1);
    memcpy(cpath, path.data, (size_t)path.len);
    cpath[path.len] = '\0';

    FILE *f = fopen(cpath, "wb");
    __mn_free(cpath);
    if (!f) return -1;

    if (content.len > 0) {
        size_t written = fwrite(content.data, 1, (size_t)content.len, f);
        fclose(f);
        return written == (size_t)content.len ? 0 : -1;
    }
    fclose(f);
    return 0;
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
        fwrite(message.data, 1, (size_t)message.len, stderr);
    }
    fputc('\n', stderr);
    exit(1);
}
