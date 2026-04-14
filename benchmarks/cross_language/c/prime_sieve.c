/* Benchmark: Prime counter via trial division up to 100,000 -- C equivalent.
 * Same algorithm as Mapanare list_ops.mn: is_prime checks n < 2, n < 4, n % 2,
 * then odd d starting at 3 up to sqrt(n).
 * Expected: primes = 9592.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include <sys/resource.h>
#include <sys/time.h>

static bool is_prime(int64_t n) {
    if (n < 2) return false;
    if (n < 4) return true;
    if (n % 2 == 0) return false;
    int64_t d = 3;
    while (d * d <= n) {
        if (n % d == 0) return false;
        d += 2;
    }
    return true;
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

    int64_t count = 0;
    for (int64_t i = 0; i < 100000; i++) {
        if (is_prime(i)) count++;
    }

    clock_gettime(CLOCK_MONOTONIC, &wall1);
    getrusage(RUSAGE_SELF, &ru1);

    double wall = ts_to_sec(&wall1) - ts_to_sec(&wall0);
    double cpu = (tv_to_sec(&ru1.ru_utime) - tv_to_sec(&ru0.ru_utime))
               + (tv_to_sec(&ru1.ru_stime) - tv_to_sec(&ru0.ru_stime));
    double peak_kb = (double)ru1.ru_maxrss;

    printf("primes = %lld\n", (long long)count);
    printf("__BENCH_METRICS__\n");
    printf("wall_time_s=%.6f\n", wall);
    printf("cpu_time_s=%.6f\n", cpu);
    printf("peak_memory_kb=%.1f\n", peak_kb);
    return 0;
}
