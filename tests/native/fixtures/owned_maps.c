#include "mapanare_core.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void release(MnMap *map, int deep) {
    if (deep) __mn_map_free_deep(map);
    else __mn_map_free(map);
}
static void expect(MnString *value, const char *text) {
    assert(value && value->len == strlen(text));
    for (int64_t i = 0; i < (int64_t)value->len; ++i)
        assert(__mn_str_byte_at(*value, i) == text[i]);
}
static void copy_string(void *dst, const void *src) {
    const MnString *s = src;
    *(MnString *)dst = __mn_str_from_parts(s->data, s->len);
}
static void drop_string(void *value) { __mn_str_free_v(*(MnString *)value); }
static MnMap *int_strings(void) {
    MnElementOps strings = {copy_string, drop_string};
    return __mn_map_new_owned(sizeof(int64_t), sizeof(MnString), MN_MAP_KEY_INT,
                              NULL, &strings); /* stack descriptor expires */
}

static void strings(int mode, int deep) {
    MnMap *map = __mn_map_str_str_new_owned();
    MnString key = {.data = "key", .len = 3};
    for (int i = 0; i < 32; ++i) {
        MnString input_key = __mn_str_from_cstr("key");
        MnString input_val = __mn_str_from_cstr("value");
        __mn_map_set(map, &input_key, &input_val);
        __mn_str_free_v(input_key);
        __mn_str_free_v(input_val);
        assert(__mn_map_len(map) == 1);
        expect(__mn_map_get(map, &key), "value");
        MnMapIter *iter = __mn_map_iter_new(map);
        void *stored_key, *stored_val;
        assert(__mn_map_iter_next(iter, &stored_key, &stored_val) == 1);
        assert(!__mn_map_iter_next(iter, &stored_key, &stored_val));
        __mn_map_iter_free(iter);
        if (mode == 0) {
            /* Both inputs alias storage that replacement may destroy. */
            __mn_map_set(map, stored_key, stored_val);
            expect(__mn_map_get(map, &key), "value");
        } else {
            assert(__mn_map_del(map, stored_key) == 1);
            assert(!__mn_map_del(map, &key));
            assert(!__mn_map_contains(map, &key));
            assert(__mn_map_len(map) == 0);
        }
    }
    release(map, deep);
}

static void growth(int deep) {
    MnMap *map = int_strings();
    int64_t zero = 0;
    MnString input = __mn_str_from_cstr("seed");
    __mn_map_set(map, &zero, &input);
    __mn_str_free_v(input);
    for (int64_t i = 1; i < 300; ++i)
        __mn_map_set(map, &i, __mn_map_get(map, &zero));
    for (int64_t i = 0; i < 300; ++i) expect(__mn_map_get(map, &i), "seed");
    assert(__mn_map_len(map) == 300);
    release(map, deep);
}

static int64_t colliding(int64_t start, uint64_t mask, uint64_t slot) {
    while ((__mn_hash_int(&start) & mask) != slot) ++start;
    return start;
}
static void tombstones(int deep) {
    MnMap *map = __mn_map_new_owned(8, 8, MN_MAP_KEY_INT, NULL, NULL);
    int64_t a = colliding(0, 15, 14), b = colliding(a + 1, 15, 14);
    int64_t c = colliding(b + 1, 15, 14), val = 7;
    __mn_map_set(map, &a, &val);
    __mn_map_set(map, &b, &val);
    __mn_map_set(map, &c, &val); /* wrap around end of table */
    assert(__mn_map_del(map, &a));
    val = 42;
    __mn_map_set(map, &c, &val); /* must find c beyond the tombstone */
    assert(__mn_map_len(map) == 2);
    assert(*(int64_t *)__mn_map_get(map, &c) == 42);
    assert(__mn_map_del(map, &b) && __mn_map_del(map, &c));
    /* Make every bucket a tombstone: missing lookup/delete must terminate. */
    for (uint64_t slot = 0; slot < 16; ++slot) {
        int64_t key = colliding(0, 15, slot);
        __mn_map_set(map, &key, &val);
        assert(__mn_map_del(map, &key));
    }
    assert(!__mn_map_get(map, &a) && !__mn_map_del(map, &a));
    __mn_map_set(map, &a, &val);
    assert(__mn_map_len(map) == 1 && *(int64_t *)__mn_map_get(map, &a) == 42);
    release(map, deep);
}

static void long_chain(int deep) {
    int64_t keys[270], next = 0;
    MnMap *map = __mn_map_new_owned(8, 8, MN_MAP_KEY_INT, NULL, NULL);
    for (int i = 0; i < 270; ++i) {
        keys[i] = colliding(next, 1023, 1020);
        next = keys[i] + 1;
        __mn_map_set(map, &keys[i], &keys[i]);
    }
    assert(__mn_map_len(map) == 270);
    for (int i = 0; i < 270; ++i)
        assert(*(int64_t *)__mn_map_get(map, &keys[i]) == keys[i]);
    for (int i = 0; i < 270; i += 2) assert(__mn_map_del(map, &keys[i]));
    for (int i = 1; i < 270; i += 2)
        assert(*(int64_t *)__mn_map_get(map, &keys[i]) == keys[i]);
    release(map, deep);
}

static void key_list(int deep, int empty) {
    MnMap *map = __mn_map_str_str_new_owned();
    MnString input = __mn_str_from_cstr("key");
    if (!empty) __mn_map_set(map, &input, &input);
    __mn_str_free_v(input);
    MnList keys = __mn_map_keys(map);
    release(map, deep);
    assert(keys.len == !empty && keys.elem_size == sizeof(MnString));
    if (!empty) expect(__mn_list_get(&keys, 0), "key");
    MnList clone = __mn_list_clone(&keys);
    __mn_list_free(&keys);
    MnString added = __mn_str_from_cstr("added");
    __mn_list_push(&clone, &added);
    __mn_str_free_v(added);
    expect(__mn_list_get(&clone, clone.len - 1), "added");
    __mn_list_free(&clone);
}

typedef struct Large {
    _Alignas(max_align_t) int64_t *number;
    char padding[600];
} Large;
static int copies, drops, key_copies, key_drops;
static void copy_large(void *dst, const void *src) {
    assert((uintptr_t)dst % _Alignof(max_align_t) == 0);
    assert((uintptr_t)src % _Alignof(max_align_t) == 0);
    Large copy = *(const Large *)src;
    copy.number = __mn_alloc(sizeof(int64_t));
    *copy.number = *((const Large *)src)->number;
    *(Large *)dst = copy;
    ++copies;
}
static void drop_large(void *value) {
    assert((uintptr_t)value % _Alignof(max_align_t) == 0);
    __mn_free(((Large *)value)->number);
    ++drops;
}
static void copy_key(void *dst, const void *src) {
    *(int64_t *)dst = *(const int64_t *)src;
    ++key_copies;
}
static void drop_key(void *value) { (void)value; ++key_drops; }
static void callbacks(int deep) {
    copies = drops = key_copies = key_drops = 0;
    MnElementOps keys = {copy_key, drop_key}, vals = {copy_large, drop_large};
    MnMap *map = __mn_map_new_owned(8, sizeof(Large), MN_MAP_KEY_INT, &keys, &vals);
    int64_t number = 42;
    Large input = {.number = &number};
    for (int64_t i = 0; i < 40; ++i) __mn_map_set(map, &i, &input);
    assert(copies == 40 && key_copies == 40 && drops == 0 && key_drops == 0);
    int64_t zero = 0;
    __mn_map_set(map, &zero, __mn_map_get(map, &zero));
    assert(copies == 41 && key_copies == 41 && drops == 1 && key_drops == 1);
    MnList list = __mn_map_keys(map);
    assert(key_copies == 81);
    assert(__mn_map_del(map, &zero));
    assert(drops == 2 && key_drops == 2);
    release(map, deep);
    assert(copies == drops && key_drops == 41);
    assert(list.len == 40 && list.elem_size == 8);
    __mn_list_free(&list);
    assert(key_copies == key_drops);
}

typedef struct Row { MnList left, right; } Row;
static void copy_row(void *dst, const void *src) {
    const Row *row = src;
    *(Row *)dst = (Row){__mn_list_clone((MnList *)&row->left),
                        __mn_list_clone((MnList *)&row->right)};
}
static void drop_row(void *value) {
    Row *row = value;
    __mn_list_free(&row->left);
    __mn_list_free(&row->right);
}
static void nested(int reverse) {
    MnElementOps ops = {copy_row, drop_row};
    MnMap *map = __mn_map_new_owned(8, sizeof(Row), MN_MAP_KEY_INT, NULL, &ops);
    Row input = {__mn_list_str_new_owned(), __mn_list_str_new_owned()};
    MnString s = __mn_str_from_cstr("nested");
    __mn_list_push(&input.left, &s);
    __mn_list_push(&input.right, &s);
    __mn_str_free_v(s);
    int64_t zero = 0, one = 1;
    __mn_map_set(map, &zero, &input);
    if (!reverse) drop_row(&input);
    __mn_map_set(map, &one, __mn_map_get(map, &zero));
    __mn_map_set(map, &zero, __mn_map_get(map, &zero));
    assert(__mn_map_del(map, &zero));
    Row *stored = __mn_map_get(map, &one);
    expect(__mn_list_get(&stored->left, 0), "nested");
    expect(__mn_list_get(&stored->right, 0), "nested");
    release(map, reverse);
    if (reverse) {
        expect(__mn_list_get(&input.left, 0), "nested");
        drop_row(&input);
    }
}

static void floats(int deep) {
    MnMap *map = __mn_map_new_owned(sizeof(double), 1, MN_MAP_KEY_FLOAT, NULL, NULL);
    double a = -0.0, b = 0.0;
    char v = 1;
    __mn_map_set(map, &a, &v);
    v = 2;
    __mn_map_set(map, &b, &v);
    assert(__mn_map_len(map) == 1 && *(char *)__mn_map_get(map, &a) == 2);
    MnList keys = __mn_map_keys(map);
    release(map, deep);
    assert(keys.len == 1 && keys.elem_size == sizeof(double));
    assert(*(double *)__mn_list_get(&keys, 0) == 0.0);
    __mn_list_free(&keys);
}

static void grow_key_alias(int deep) {
    MnMap *map = __mn_map_str_str_new_owned();
    MnString val = __mn_str_from_cstr("new-key");
    for (int i = 0; i < 12; ++i) {
        char text[32];
        snprintf(text, sizeof(text), "key-%d", i);
        MnString key = __mn_str_from_cstr(text);
        __mn_map_set(map, &key, &val);
        __mn_str_free_v(key);
    }
    __mn_str_free_v(val);
    MnMapIter *iter = __mn_map_iter_new(map);
    void *stored_key, *stored_val;
    assert(__mn_map_iter_next(iter, &stored_key, &stored_val));
    MnString expected;
    copy_string(&expected, stored_key);
    __mn_map_iter_free(iter);
    /* New key aliases a stored value and new value aliases a stored key.
     * Inserting the thirteenth entry forces both borrows through growth. */
    __mn_map_set(map, stored_val, stored_key);
    MnString new_key = {.data = "new-key", .len = 7};
    MnString *result = __mn_map_get(map, &new_key);
    assert(result && __mn_str_eq(*result, expected));
    assert(__mn_map_len(map) == 13);
    __mn_str_free_v(expected);
    release(map, deep);
}

static void plain_values(int deep) {
    MnElementOps keys = {copy_string, drop_string};
    typedef struct Pair { int64_t first, second; } Pair;
    MnMap *map = __mn_map_new_owned(sizeof(MnString), sizeof(Pair), MN_MAP_KEY_STR,
                                    &keys, NULL);
    MnString key = __mn_str_from_cstr("");
    Pair input = {42, 84};
    __mn_map_set(map, &key, &input);
    __mn_str_free_v(key);
    MnString lookup = {.data = "", .len = 0};
    Pair *found = __mn_map_get(map, &lookup);
    assert(found && found->first == 42 && found->second == 84);
    MnList list = __mn_map_keys(map);
    release(map, deep);
    expect(__mn_list_get(&list, 0), "");
    __mn_list_free(&list);
}

static void model(int deep) {
    MnMap *map = __mn_map_new_owned(8, 8, MN_MAP_KEY_INT, NULL, NULL);
    int live[64] = {0};
    int64_t expected[64] = {0}, count = 0;
    uint64_t rng = 1;
    for (int64_t step = 0; step < 2000; ++step) {
        rng = rng * 6364136223846793005ULL + 1;
        int64_t key = (rng >> 32) % 64;
        if ((rng >> 48) % 3 == 0) {
            assert(__mn_map_del(map, &key) == live[key]);
            count -= live[key];
            live[key] = 0;
        } else {
            __mn_map_set(map, &key, &step);
            count += !live[key];
            live[key] = 1;
            expected[key] = step;
        }
        assert(__mn_map_len(map) == count);
        for (int64_t i = 0; i < 64; ++i) {
            int64_t *got = __mn_map_get(map, &i);
            assert(!!got == live[i]);
            if (got) assert(*got == expected[i]);
        }
    }
    release(map, deep);
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    int mode = atoi(argv[1]), deep = atoi(argv[2]);
    if (mode >= 20) {
        MnElementOps incomplete = {copy_string, NULL};
        if (mode == 20) (void)__mn_map_new_owned(8, 8, 0, NULL, &incomplete);
        if (mode == 21) (void)__mn_map_new_owned(1, 8, 0, NULL, NULL);
        if (mode == 22) (void)__mn_map_new_owned(sizeof(MnString), 8, 1, NULL, NULL);
        if (mode == 23) (void)__mn_map_new_owned(8, 0, 0, NULL, NULL);
        if (mode == 24) (void)__mn_map_new_owned(8, 8, 99, NULL, NULL);
        return 3;
    }
    int iterations = mode == 4 || mode == 9 ? 10 : 1000;
    for (int i = 0; i < iterations; ++i) {
        switch (mode) {
            case 0: case 1: strings(mode, deep); break;
            case 2: growth(deep); break;
            case 3: tombstones(deep); break;
            case 4: long_chain(deep); break;
            case 5: key_list(deep, 0); break;
            case 6: callbacks(deep); break;
            case 7: nested(deep); break;
            case 8: floats(deep); break;
            case 9: model(deep); break;
            case 10: key_list(deep, 1); break;
            case 11: grow_key_alias(deep); break;
            case 12: plain_values(deep); break;
            default: return 2;
        }
    }
    puts("ok");
    return 0;
}
