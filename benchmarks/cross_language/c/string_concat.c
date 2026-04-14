/* Benchmark: String concatenation -- C equivalent.
 * Idiomatic C: realloc + memcpy, growing buffer by exact amount per iteration
 * (no amortized doubling). This mirrors the Mapanare allocate-per-concat pattern.
 * Expected: len = 50000 (10,000 * len("hello")).
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/resource.h>
#include <sys/time.h>

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

    const char *chunk = "hello";
    const size_t chunk_len = 5;
    char *buf = NULL;
    size_t len = 0;

    for (int i = 0; i < 10000; i++) {
        char *new_buf = (char *)realloc(buf, len + chunk_len + 1);
        if (!new_buf) {
            free(buf);
            return 1;
        }
        buf = new_buf;
        memcpy(buf + len, chunk, chunk_len);
        len += chunk_len;
        buf[len] = '\0';
    }

    clock_gettime(CLOCK_MONOTONIC, &wall1);
    getrusage(RUSAGE_SELF, &ru1);

    double wall = ts_to_sec(&wall1) - ts_to_sec(&wall0);
    double cpu = (tv_to_sec(&ru1.ru_utime) - tv_to_sec(&ru0.ru_utime))
               + (tv_to_sec(&ru1.ru_stime) - tv_to_sec(&ru0.ru_stime));
    double peak_kb = (double)ru1.ru_maxrss;

    printf("len = %zu\n", len);
    printf("__BENCH_METRICS__\n");
    printf("wall_time_s=%.6f\n", wall);
    printf("cpu_time_s=%.6f\n", cpu);
    printf("peak_memory_kb=%.1f\n", peak_kb);
    free(buf);
    return 0;
}
