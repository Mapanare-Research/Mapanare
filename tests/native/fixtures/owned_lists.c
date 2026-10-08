#include "mapanare_core.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void expect(MnList *list, int64_t i, const char *expected) {
    MnString value = __mn_list_str_get(list, i);
    assert(value.len == strlen(expected));
    for (int64_t n = 0; n < (int64_t)value.len; ++n)
        assert(__mn_str_byte_at(value, n) == expected[n]);
}

static MnList strings(void) {
    MnList list = __mn_list_str_new_owned();
    MnString input = __mn_str_from_cstr("owned");
    __mn_list_str_push(&list, input);
    __mn_list_str_push(&list, input); /* independent copies of the same input */
    __mn_str_free_v(input);
    MnString literal = {.data = "literal", .len = 7, .is_heap = 0};
    __mn_list_str_push(&list, literal);
    return list;
}

static void string_case(int operation, int reverse) {
    MnList a = strings();
    MnList b = __mn_list_clone(&a);
    assert(a.data == b.data); /* shallow handle cloning remains COW */
    if (operation == 1) {
        /* Input aliases the shared buffer we are about to detach. */
        __mn_list_push(&b, __mn_list_get(&b, 0));
        assert(a.data != b.data);
    } else if (operation == 2) {
        /* Grow with an element borrowed from the very buffer being grown. */
        for (int i = 0; i < 40; ++i) __mn_list_push(&b, __mn_list_get(&b, 0));
    } else if (operation == 3) {
        __mn_list_set(&b, 0, __mn_list_get(&b, 0));
        __mn_list_set(&b, 1, __mn_list_get(&b, 2));
        expect(&a, 1, "owned");
        expect(&b, 1, "literal");
    } else if (operation == 4) {
        __mn_list_clear(&b);
        assert(b.len == 0);
        /* The empty buffer must retain its policy through clear/clone. */
        MnList empty = __mn_list_clone(&b);
        MnString input = __mn_str_from_cstr("owned");
        __mn_list_str_push(&b, input);
        __mn_str_free_v(input);
        __mn_list_free(&empty);
    } else if (operation == 5) {
        MnString popped;
        assert(__mn_list_pop(&b, &popped) == 0);
        __mn_list_clear(&b);
        assert(__mn_str_byte_at(popped, 0) == 'l');
        __mn_str_free_v(popped);
        assert(__mn_list_pop(&b, &popped) == -1);
        MnString input = __mn_str_from_cstr("owned");
        __mn_list_str_push(&b, input);
        __mn_str_free_v(input);
    } else if (operation == 6) {
        MnList combined = __mn_list_concat(&b, &b);
        __mn_list_free(&b);
        b = combined;
        expect(&b, 3, "owned");
    } else if (operation == 7) {
        MnList empty = __mn_list_str_new_owned();
        MnList combined = __mn_list_concat(&empty, &b);
        __mn_list_free(&empty);
        __mn_list_free(&b);
        b = combined;
    } else if (operation == 8) {
        __mn_list_free(&b);
        b = __mn_list_deep_clone(&a, NULL, 0);
        assert(a.data != b.data);
    }
    MnList *first = reverse ? &b : &a;
    MnList *last = reverse ? &a : &b;
    __mn_list_free_strings(first);
    expect(last, 0, "owned");
    __mn_list_free(last);
    __mn_list_free(last); /* reset handle is safe to release again */
}

typedef struct Large {
    int64_t *value;
    _Alignas(max_align_t) char padding[300];
} Large;
static int copies, drops;
static void copy_large(void *dest, const void *src) {
    Large result = *(const Large *)src;
    result.value = __mn_alloc(sizeof(int64_t));
    *result.value = *((const Large *)src)->value;
    memcpy(dest, &result, sizeof(result));
    ++copies;
}
static void drop_large(void *value) {
    __mn_free(((Large *)value)->value);
    ++drops;
}
static MnList large_list(void) {
    MnElementOps ops = {copy_large, drop_large}; /* descriptor has stack lifetime */
    return __mn_list_new_owned(sizeof(Large), &ops);
}
static void callbacks(void) {
    copies = drops = 0;
    MnList a = large_list();
    int64_t number = 42;
    Large input = {.value = &number};
    for (int i = 0; i < 20; ++i) __mn_list_push(&a, &input);
    assert(copies == 20 && drops == 0); /* growth transfers, never recopies */
    MnList b = __mn_list_clone(&a);
    assert(copies == 20);
    __mn_list_set(&b, 0, __mn_list_get(&b, 0));
    assert(copies == 41 && drops == 1);
    __mn_list_free(&a);
    Large popped;
    assert(__mn_list_pop(&b, &popped) == 0);
    __mn_list_clear(&b);
    assert(*popped.value == 42);
    drop_large(&popped);
    __mn_list_free(&b);
    assert(copies == drops);
}

typedef struct Row { MnList left, right; } Row;
static void copy_row(void *dest, const void *src) {
    const Row *input = src;
    Row result = {__mn_list_clone((MnList *)&input->left),
                  __mn_list_clone((MnList *)&input->right)};
    memcpy(dest, &result, sizeof(result));
}
static void drop_row(void *value) {
    Row *row = value;
    __mn_list_free(&row->left);
    __mn_list_free(&row->right);
}
static void nested(int reverse) {
    MnElementOps ops = {copy_row, drop_row};
    MnList a = __mn_list_new_owned(sizeof(Row), &ops);
    Row input = {strings(), strings()};
    __mn_list_push(&a, &input);
    drop_row(&input);
    MnList b = __mn_list_clone(&a);
    __mn_list_push(&b, __mn_list_get(&b, 0));
    Row popped;
    assert(__mn_list_pop(&b, &popped) == 0);
    __mn_list_free(reverse ? &b : &a);
    MnList *last = reverse ? &a : &b;
    Row *row = __mn_list_get(last, 0);
    expect(&row->left, 0, "owned");
    expect(&row->right, 1, "owned");
    __mn_list_free(last);
    expect(&popped.left, 0, "owned");
    drop_row(&popped);
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    int mode = atoi(argv[1]), reverse = atoi(argv[2]);
    if (mode == 11) {
        MnList a = strings(), b = __mn_list_str_new();
        (void)__mn_list_concat(&a, &b); /* incompatible policies must abort */
        return 3;
    }
    for (int i = 0; i < 1000; ++i) {
        if (mode <= 8) string_case(mode, reverse);
        else if (mode == 9) callbacks();
        else if (mode == 10) nested(reverse);
        else return 2;
    }
    puts("ok");
    return 0;
}
