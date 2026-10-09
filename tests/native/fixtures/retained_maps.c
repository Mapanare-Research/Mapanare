#include "mapanare_core.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int copies, drops;
static void copy_int(void *dst, const void *src) {
    memcpy(dst, src, sizeof(int64_t));
    ++copies;
}
static void drop_int(void *value) { (void)value; ++drops; }

static void raw_strings(int mode) {
    MnMap *map = __mn_map_new(sizeof(MnString), sizeof(MnString), MN_MAP_KEY_STR, MN_MAP_VAL_STR);
    MnString key = __mn_str_from_cstr("key"), val = __mn_str_from_cstr("value");
    __mn_map_set(map, &key, &val); /* legacy ownership transferred to deep cleanup */
    MnMap *alias = __mn_map_retain(map);
    assert(alias == map);
    if (mode == 0) __mn_map_free_deep(map);
    else __mn_map_free(map);
    MnString lookup = {"key", 3}, found;
    memcpy(&found, __mn_map_get(alias, &lookup), sizeof(found));
    assert(__mn_str_byte_at(found, 0) == 'v');
    if (mode == 0) __mn_map_free(alias); /* sticky deep request from first owner */
    else __mn_map_free_deep(alias);
}

static void owned(int mode) {
    copies = drops = 0;
    MnElementOps ops = {copy_int, drop_int};
    MnMap *map = __mn_map_new_owned(8, 8, MN_MAP_KEY_INT, &ops, &ops);
    MnMap *alias = __mn_map_retain(map);
    MnMap *third = __mn_map_retain(alias);
    for (int64_t i = 0; i < 100; ++i) __mn_map_set(map, &i, &i);
    assert(copies == 200 && drops == 0);
    __mn_map_free_deep(map);
    assert(drops == 0 && __mn_map_len(alias) == 100);
    int64_t key = 9, replacement = 999;
    __mn_map_set(alias, &key, &replacement);
    assert(*(int64_t *)__mn_map_get(third, &key) == 999);
    assert(__mn_map_del(third, &key));
    assert(!__mn_map_contains(alias, &key));
    if (mode == 2) { __mn_map_free(alias); __mn_map_free_deep(third); }
    else { __mn_map_free_deep(third); __mn_map_free(alias); }
    assert(copies == drops);
}

static void cursor(int mode) {
    MnMap *map = mode == 4 ? __mn_map_str_str_new_owned()
        : __mn_map_new(sizeof(MnString), sizeof(MnString), MN_MAP_KEY_STR, MN_MAP_VAL_STR);
    MnString key = __mn_str_from_cstr("key"), val = __mn_str_from_cstr("value");
    __mn_map_set(map, &key, &val);
    if (mode == 4) { __mn_str_free_v(key); __mn_str_free_v(val); }
    MnMapIter *first = __mn_map_iter_new(map), *second = __mn_map_iter_new(map);
    __mn_map_free_deep(map);
    void *k, *v;
    assert(__mn_map_iter_next(first, &k, &v));
    __mn_map_iter_free(first);
    assert(__mn_map_iter_next(second, &k, &v));
    MnString found;
    memcpy(&found, v, sizeof(found));
    assert(__mn_str_byte_at(found, 0) == 'v');
    assert(!__mn_map_iter_next(second, &k, &v));
    __mn_map_iter_free(second);
}

int main(int argc, char **argv) {
    assert(argc == 2);
    int mode = atoi(argv[1]);
    assert(__mn_map_retain(NULL) == NULL);
    __mn_map_free(NULL);
    __mn_map_free_deep(NULL);
    __mn_map_iter_free(NULL);
    for (int i = 0; i < 1000; ++i) {
        if (mode < 2) raw_strings(mode);
        else if (mode < 4) owned(mode);
        else cursor(mode);
    }
    puts("ok");
}
