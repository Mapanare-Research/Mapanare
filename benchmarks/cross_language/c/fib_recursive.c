/* Benchmark: Recursive Fibonacci(35) -- C equivalent.
 * Compiles clean with gcc -O2 -Wall -Wextra and clang -O2 -Wall -Wextra.
 * Emits __BENCH_METRICS__ block for run_benchmarks.py harness.
 */
#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include <sys/resource.h>
#include <sys/time.h>

static int64_t fib(int64_t n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
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

    int64_t r = fib(35);

    clock_gettime(CLOCK_MONOTONIC, &wall1);
    getrusage(RUSAGE_SELF, &ru1);

    double wall = ts_to_sec(&wall1) - ts_to_sec(&wall0);
    double cpu = (tv_to_sec(&ru1.ru_utime) - tv_to_sec(&ru0.ru_utime))
               + (tv_to_sec(&ru1.ru_stime) - tv_to_sec(&ru0.ru_stime));
    double peak_kb = (double)ru1.ru_maxrss; /* Linux: KB */

    printf("fib(35) = %lld\n", (long long)r);
    printf("__BENCH_METRICS__\n");
    printf("wall_time_s=%.6f\n", wall);
    printf("cpu_time_s=%.6f\n", cpu);
    printf("peak_memory_kb=%.1f\n", peak_kb);
    return 0;
}
