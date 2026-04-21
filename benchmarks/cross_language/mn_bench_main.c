/**
 * mn_bench_main.c — Timing wrapper for Mapanare benchmarks.
 *
 * v4.148.0 (E4): Replaces mn_user_main.c in the benchmark link step to
 * emit __BENCH_METRICS__ with internal wall time (clock_gettime). This
 * matches the Rust/Go/C methodology: timing excludes subprocess spawn
 * and /usr/bin/time overhead.
 *
 * Prior to v4.148.0, Mapanare benchmarks used _run_external (perf_counter
 * around subprocess.run), which included ~1.2 ms of spawn overhead —
 * pinning the reported wall time at ≥ 1.2 ms regardless of actual compute.
 * On sub-millisecond workloads like string_concat, this produced a spurious
 * 30×+ gap vs Rust that was entirely measurement artifact.
 */

#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include <sys/resource.h>

extern void __mn_argv_init(int argc, char **argv);
extern int32_t mn_main(void);

int main(int argc, char *argv[]) {
    __mn_argv_init(argc, argv);

    struct timespec t0, t1;
    struct rusage ru0, ru1;
    getrusage(RUSAGE_SELF, &ru0);
    clock_gettime(CLOCK_MONOTONIC, &t0);

    int32_t rc = mn_main();

    clock_gettime(CLOCK_MONOTONIC, &t1);
    getrusage(RUSAGE_SELF, &ru1);

    double wall = (double)(t1.tv_sec - t0.tv_sec)
                + (double)(t1.tv_nsec - t0.tv_nsec) / 1e9;
    double cpu = (double)(ru1.ru_utime.tv_sec - ru0.ru_utime.tv_sec)
               + (double)(ru1.ru_utime.tv_usec - ru0.ru_utime.tv_usec) / 1e6
               + (double)(ru1.ru_stime.tv_sec - ru0.ru_stime.tv_sec)
               + (double)(ru1.ru_stime.tv_usec - ru0.ru_stime.tv_usec) / 1e6;
    double peak_kb = (double)ru1.ru_maxrss;

    printf("__BENCH_METRICS__\n");
    printf("wall_time_s=%.6f\n", wall);
    printf("cpu_time_s=%.6f\n", cpu);
    printf("peak_memory_kb=%.1f\n", peak_kb);

    return rc;
}
