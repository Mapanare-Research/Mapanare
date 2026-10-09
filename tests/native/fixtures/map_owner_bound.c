/* Link-time observer for generated map ownership calls. No runtime replacement. */
#include "mapanare_core.h"
#include <assert.h>
#include <stdio.h>

static struct { MnMap *map; int refs; } owners[64];
static int live, peak;
MnMap *__real___mn_map_new(int64_t, int64_t, int64_t, int64_t);
MnMap *__real___mn_map_retain(MnMap *);
void __real___mn_map_free_deep(MnMap *);

MnMap *__wrap___mn_map_new(int64_t ks, int64_t vs, int64_t kt, int64_t vt) {
    MnMap *map = __real___mn_map_new(ks, vs, kt, vt);
    for (int i = 0; i < 64; ++i) if (!owners[i].map) {
        owners[i].map = map;
        owners[i].refs = 1;
        if (++live > peak) peak = live;
        return map;
    }
    assert(!"unbounded retained maps");
    return map;
}

MnMap *__wrap___mn_map_retain(MnMap *map) {
    if (map) {
        int found = 0;
        for (int i = 0; i < 64; ++i) if (owners[i].map == map) {
            ++owners[i].refs;
            found = 1;
            break;
        }
        assert(found);
    }
    return __real___mn_map_retain(map);
}

void __wrap___mn_map_free_deep(MnMap *map) {
    if (map) {
        int found = 0;
        for (int i = 0; i < 64; ++i) if (owners[i].map == map) {
            assert(owners[i].refs > 0);
            if (--owners[i].refs == 0) { owners[i].map = NULL; --live; }
            found = 1;
            break;
        }
        assert(found);
    }
    __real___mn_map_free_deep(map);
}

__attribute__((destructor)) static void verify_bound(void) {
    assert(live == 0);
    assert(peak >= 2 && peak <= 8);
    fprintf(stderr, "map peak: %d\n", peak);
}
