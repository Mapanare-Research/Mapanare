#include "mapanare_core.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

static void check(int64_t start, int64_t end, int inclusive, int count) {
    void *iter = inclusive ? __mn_range_inclusive(start, end) : __mn_range(start, end);
    for (int i = 0; i < count; ++i) {
        assert(__iter_has_next(iter));
        assert(__iter_has_next(iter)); /* peeking must not advance */
        assert((int64_t)(intptr_t)__iter_next(iter) == start + i);
    }
    assert(!__iter_has_next(iter));
    assert(!__iter_has_next(iter));
    __mn_range_free(iter);
}

int main(void) {
    check(-2, 3, 0, 5);
    check(-2, 3, 1, 6);
    check(2, 2, 0, 0);
    check(2, 2, 1, 1);
    check(3, 2, 0, 0);
    check(3, 2, 1, 0);
    check(INT64_MIN, INT64_MIN + 1, 0, 1);
    check(INT64_MIN, INT64_MIN + 1, 1, 2);
    check(INT64_MAX - 1, INT64_MAX, 0, 1);
    check(INT64_MAX - 1, INT64_MAX, 1, 2);
    check(INT64_MAX, INT64_MAX, 0, 0);
    check(INT64_MAX, INT64_MAX, 1, 1);
    puts("ok");
    return 0;
}
