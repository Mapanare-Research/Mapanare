/* Sanitizer probes for the ownership roadmap. See the work log for commands.
 * deep-clone is a regression gate; the other modes expose unresolved contracts.
 */
#include "mapanare_core.h"
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Row {
    int64_t marker;
    MnList left;
    MnList right;
} Row;

static void destroy_rows(MnList *rows) {
    for (int64_t i = 0; i < rows->len; ++i) {
        Row *row = __mn_list_get(rows, i);
        __mn_list_free(&row->left);
        __mn_list_free(&row->right);
    }
    __mn_list_free(rows);
}

static MnList inner_list(int state) {
    MnList list = __mn_list_new(sizeof(int64_t));
    int64_t value = 17;
    if (state != 0) __mn_list_push(&list, &value);
    if (state == 1) __mn_list_clear(&list);
    if (state == 2) assert(__mn_list_pop(&list, &value) == 0);
    return list;
}

static void deep_clone(int state, int reverse, int mutate_first) {
    MnList source = __mn_list_new(sizeof(Row));
    for (int64_t i = 0; i < 3; ++i) {
        Row row = {i, inner_list(state), inner_list(state)};
        /* Transfer both inner handles into the source row. */
        __mn_list_push(&source, &row);
    }
    const int64_t offsets[] = {offsetof(Row, left), offsetof(Row, right)};
    MnList copy = __mn_list_deep_clone(&source, offsets, 2);
    MnList *first = reverse ? &copy : &source;
    MnList *survivor = reverse ? &source : &copy;
    if (mutate_first) {
        Row *row = __mn_list_get(first, 0);
        int64_t value = 99;
        __mn_list_push(&row->left, &value);
        __mn_list_push(&row->right, &value);
    }
    destroy_rows(first);
    for (int64_t i = 0; i < survivor->len; ++i) {
        Row *row = __mn_list_get(survivor, i);
        assert(row->marker == i);
        assert(row->left.len == (state == 3 ? 1 : 0));
        assert(row->right.len == (state == 3 ? 1 : 0));
        int64_t value = 42;
        __mn_list_push(&row->left, &value);
        __mn_list_push(&row->right, &value);
        assert(*(int64_t *)__mn_list_get(&row->left, row->left.len - 1) == 42);
        assert(*(int64_t *)__mn_list_get(&row->right, row->right.len - 1) == 42);
    }
    destroy_rows(survivor);
}

static void shared_strings(int detach) {
    MnList source = __mn_list_str_new();
    __mn_list_str_push(&source, __mn_str_from_cstr("retained"));
    MnList copy = __mn_list_clone(&source);
    if (detach) __mn_list_str_push(&copy, __mn_str_from_cstr("new"));
    __mn_list_free_strings(&source);
    MnString value = __mn_list_str_get(&copy, 0);
    /* Read the contents, not just the dangling string's length. */
    assert(__mn_str_byte_at(value, 0) == 'r');
    __mn_list_free_strings(&copy);
}

static void nested_retention(void) {
    MnList outer = __mn_list_new(sizeof(MnList));
    MnList inner = inner_list(3);
    __mn_list_push(&outer, &inner);
    /* Current compiler-style shallow outer cleanup cannot release elements. */
    __mn_list_free(&outer);
}

static void map_retention(int remove) {
    MnMap *map = __mn_map_new(sizeof(MnString), sizeof(MnString),
                             MN_MAP_KEY_STR, MN_MAP_VAL_STR);
    for (int64_t i = 0; i < 1000; ++i) {
        MnString key = __mn_str_from_cstr("key");
        MnString value = __mn_str_from_cstr("value");
        __mn_map_set(map, &key, &value);
        if (remove) assert(__mn_map_del(map, &key) == 1);
    }
    __mn_map_free_deep(map);
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    if (strcmp(argv[1], "deep-clone") == 0) {
        if (argc != 5) return 2;
        for (int i = 0; i < 1000; ++i)
            deep_clone(atoi(argv[2]), atoi(argv[3]), atoi(argv[4]));
    } else if (strcmp(argv[1], "shared-strings") == 0) {
        shared_strings(0);
    } else if (strcmp(argv[1], "detached-strings") == 0) {
        shared_strings(1);
    } else if (strcmp(argv[1], "nested-retention") == 0) {
        for (int i = 0; i < 1000; ++i) nested_retention();
    } else if (strcmp(argv[1], "map-overwrite") == 0) {
        map_retention(0);
    } else if (strcmp(argv[1], "map-delete") == 0) {
        map_retention(1);
    } else {
        return 2;
    }
    puts("ok");
    return 0;
}
