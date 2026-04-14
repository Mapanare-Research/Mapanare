/* Benchmark: Enum dispatch -- C equivalent.
 * Tagged union with enum discriminant + union payload, switch-based dispatch.
 * 6 variants matching Mapanare's Shape: Circle, Square, Triangle, Point, Line, Rect.
 * Expected: checksum = 52818168.
 */
#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include <sys/resource.h>
#include <sys/time.h>

typedef enum {
    TAG_CIRCLE = 0,
    TAG_SQUARE = 1,
    TAG_TRIANGLE = 2,
    TAG_POINT = 3,
    TAG_LINE = 4,
    TAG_RECT = 5
} ShapeTag;

typedef struct {
    ShapeTag tag;
    union {
        int64_t radius;      /* Circle */
        int64_t side;        /* Square */
        struct { int64_t base, height; } tri;  /* Triangle */
        int64_t length;      /* Line */
        struct { int64_t w, h; } rect;  /* Rect */
    } payload;
} Shape;

static int64_t area(Shape s) {
    switch (s.tag) {
        case TAG_CIRCLE:   return s.payload.radius * s.payload.radius * 3;
        case TAG_SQUARE:   return s.payload.side * s.payload.side;
        case TAG_TRIANGLE: return s.payload.tri.base * s.payload.tri.height / 2;
        case TAG_POINT:    return 0;
        case TAG_LINE:     return s.payload.length;
        case TAG_RECT:     return s.payload.rect.w * s.payload.rect.h;
    }
    return 0; /* unreachable */
}

static Shape make_shape(int64_t i) {
    Shape s;
    int64_t tag = i % 6;
    switch (tag) {
        case 0: s.tag = TAG_CIRCLE;   s.payload.radius = i % 50 + 1; break;
        case 1: s.tag = TAG_SQUARE;   s.payload.side = i % 30 + 1; break;
        case 2: s.tag = TAG_TRIANGLE; s.payload.tri.base = i % 20 + 1; s.payload.tri.height = i % 40 + 1; break;
        case 3: s.tag = TAG_POINT;    break;
        case 4: s.tag = TAG_LINE;     s.payload.length = i % 100 + 1; break;
        default: s.tag = TAG_RECT;    s.payload.rect.w = i % 25 + 1; s.payload.rect.h = i % 35 + 1; break;
    }
    return s;
}

static double tv_to_sec(const struct timeval *tv) {
    return (double)tv->tv_sec + (double)tv->tv_usec / 1e6;
}

static double ts_to_sec(const struct timespec *ts) {
    return (double)ts->tv_sec + (double)ts->tv_nsec / 1e9;
}

int main(void) {
    struct timespec wall0, wall1;
    struct rusage ru0, ru1;

    getrusage(RUSAGE_SELF, &ru0);
    clock_gettime(CLOCK_MONOTONIC, &wall0);

    int64_t total = 0;
    for (int64_t i = 0; i < 100000; i++) {
        total += area(make_shape(i));
    }

    clock_gettime(CLOCK_MONOTONIC, &wall1);
    getrusage(RUSAGE_SELF, &ru1);

    double wall = ts_to_sec(&wall1) - ts_to_sec(&wall0);
    double cpu = (tv_to_sec(&ru1.ru_utime) - tv_to_sec(&ru0.ru_utime))
               + (tv_to_sec(&ru1.ru_stime) - tv_to_sec(&ru0.ru_stime));
    double peak_kb = (double)ru1.ru_maxrss;

    printf("checksum = %lld\n", (long long)total);
    printf("__BENCH_METRICS__\n");
    printf("wall_time_s=%.6f\n", wall);
    printf("cpu_time_s=%.6f\n", cpu);
    printf("peak_memory_kb=%.1f\n", peak_kb);
    return 0;
}
