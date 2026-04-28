/* Benchmark: Struct allocation -- C equivalent.
 * Allocate 100,000 Point{x,y,z} structs by value, accumulate fields.
 * Expected: checksum = 29999700000 (sum over i in [0..100000) of i+2i+3i).
 *
 * v5.1.2 Bn.4: rewritten to return struct by value (stack return) instead
 * of malloc+free per iteration. This matches the Rust and Mapanare versions
 * which also use stack-based struct return, making the Mn/C geomean an
 * apples-to-apples comparison. Prior version measured malloc throughput,
 * not struct construction — Mamba v4.154.0 flagged the asymmetry.
 */
#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include <sys/resource.h>
#include <sys/time.h>

typedef struct {
    int64_t x, y, z;
} Point;

static Point make_point(int64_t i) {
    Point p = { i, i * 2, i * 3 };
    return p;
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

    int64_t sum = 0;
    for (int64_t i = 0; i < 100000; i++) {
        Point p = make_point(i);
        sum += p.x + p.y + p.z;
    }

    clock_gettime(CLOCK_MONOTONIC, &wall1);
    getrusage(RUSAGE_SELF, &ru1);

    double wall = ts_to_sec(&wall1) - ts_to_sec(&wall0);
    double cpu = (tv_to_sec(&ru1.ru_utime) - tv_to_sec(&ru0.ru_utime))
               + (tv_to_sec(&ru1.ru_stime) - tv_to_sec(&ru0.ru_stime));
    double peak_kb = (double)ru1.ru_maxrss;

    printf("checksum = %lld\n", (long long)sum);
    printf("__BENCH_METRICS__\n");
    printf("wall_time_s=%.6f\n", wall);
    printf("cpu_time_s=%.6f\n", cpu);
    printf("peak_memory_kb=%.1f\n", peak_kb);
    return 0;
}
