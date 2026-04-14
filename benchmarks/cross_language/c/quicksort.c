/* Benchmark: Quicksort on 10,000 pseudo-random integers -- C equivalent.
 * LCG: seed=42, a=1103515245, c=12345, mod=2^31. Same as every other language.
 * Checksum = sum of first 10 elements after sort. Expected: 485.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <sys/resource.h>
#include <sys/time.h>

static int64_t lcg_next(int64_t seed) {
    return (seed * 1103515245LL + 12345LL) % 2147483648LL;
}

static int64_t partition_arr(int64_t *arr, int64_t lo, int64_t hi) {
    int64_t pivot = arr[hi];
    int64_t i = lo;
    for (int64_t j = lo; j < hi; j++) {
        if (arr[j] < pivot) {
            int64_t tmp = arr[i];
            arr[i] = arr[j];
            arr[j] = tmp;
            i++;
        }
    }
    int64_t tmp2 = arr[i];
    arr[i] = arr[hi];
    arr[hi] = tmp2;
    return i;
}

static void qsort_rec(int64_t *arr, int64_t lo, int64_t hi) {
    if (lo < hi) {
        int64_t p = partition_arr(arr, lo, hi);
        qsort_rec(arr, lo, p - 1);
        qsort_rec(arr, p + 1, hi);
    }
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

    int64_t *arr = (int64_t *)malloc(10000 * sizeof(int64_t));
    if (!arr) return 1;
    int64_t seed = 42;
    for (int i = 0; i < 10000; i++) {
        seed = lcg_next(seed);
        arr[i] = seed % 100000;
    }
    qsort_rec(arr, 0, 9999);
    int64_t checksum = 0;
    for (int k = 0; k < 10; k++) checksum += arr[k];

    clock_gettime(CLOCK_MONOTONIC, &wall1);
    getrusage(RUSAGE_SELF, &ru1);

    double wall = ts_to_sec(&wall1) - ts_to_sec(&wall0);
    double cpu = (tv_to_sec(&ru1.ru_utime) - tv_to_sec(&ru0.ru_utime))
               + (tv_to_sec(&ru1.ru_stime) - tv_to_sec(&ru0.ru_stime));
    double peak_kb = (double)ru1.ru_maxrss;

    printf("checksum = %lld\n", (long long)checksum);
    printf("__BENCH_METRICS__\n");
    printf("wall_time_s=%.6f\n", wall);
    printf("cpu_time_s=%.6f\n", cpu);
    printf("peak_memory_kb=%.1f\n", peak_kb);
    free(arr);
    return 0;
}
