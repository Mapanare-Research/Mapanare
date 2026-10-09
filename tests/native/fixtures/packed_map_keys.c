#include "mapanare_core.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    /* Deliberately unaligned public hash inputs, as well as packed buckets. */
    _Alignas(16) char raw[sizeof(MnString) + 1];
    int64_t integer = 17;
    double floating = 17.5;
    MnString text = {"seventeen", 9};
    memcpy(raw + 1, &integer, sizeof(integer));
    assert(__mn_hash_int(raw + 1) == __mn_hash_int(&integer));
    memcpy(raw + 1, &floating, sizeof(floating));
    assert(__mn_hash_float(raw + 1) == __mn_hash_float(&floating));
    memcpy(raw + 1, &text, sizeof(text));
    assert(__mn_hash_str(raw + 1) == __mn_hash_str(&text));

    for (int kind = 0; kind < 3; ++kind) {
        int64_t type = kind == 0 ? MN_MAP_KEY_INT :
                       kind == 1 ? MN_MAP_KEY_FLOAT : MN_MAP_KEY_STR;
        MnMap *map = __mn_map_new(kind == 2 ? sizeof(MnString) : 8,
                                  sizeof(int64_t), type, MN_MAP_VAL_OPAQUE);
        char names[100][20];
        for (int64_t i = 0; i < 100; ++i) {
            double f = i + 0.5;
            snprintf(names[i], sizeof(names[i]), "key-%lld", (long long)i);
            MnString s = {names[i], (int64_t)strlen(names[i])};
            __mn_map_set(map, kind == 0 ? (void *)&i : kind == 1 ? (void *)&f :
                         (void *)&s, &i);
        }
        assert(__mn_map_len(map) == 100);
        for (int64_t i = 0; i < 100; ++i) {
            double f = i + 0.5;
            MnString s = {names[i], (int64_t)strlen(names[i])};
            void *key = kind == 0 ? (void *)&i : kind == 1 ? (void *)&f : (void *)&s;
            int64_t value;
            void *stored = __mn_map_get(map, key);
            assert(stored);
            memcpy(&value, stored, sizeof(value));
            assert(value == i);
            assert(__mn_map_del(map, key) == 1);
            assert(!__mn_map_contains(map, key));
        }
        __mn_map_free(map);
    }
    puts("ok");
}
