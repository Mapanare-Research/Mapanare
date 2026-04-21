# Anaconda — Toolchain Review (Arc 13)

**Grade: 8/10**
**Verdict: PASS WITH NOTES**

## Assessment

### CI coverage

The existing CI pipeline (format, lint, type check, pytest) covers the Python-side changes (emitter, types, lower, mir_opt). The C runtime changes compile but are not tested in CI beyond compilation — no C-level unit tests for StringBuilder or the scheduler. **This is a gap.** The native CI job tests the agent runtime with AddressSanitizer and ThreadSanitizer, but the coroutine scheduler functions are not exercised there because the benchmarks don't link.

### Benchmark infrastructure (v4.94.0)

The async benchmark suite is well-designed: 5 workloads covering distinct patterns, 3 languages for comparison, JSON output for analysis. The harness (`run_async.py`) follows the established `run_baseline.py` pattern.

**Concern:** Only Python baselines were measured. The Mapanare binaries can't link because `libmapanare_rt.a` hasn't been rebuilt. The Go binaries can't run because Go isn't installed. This means the benchmark suite is infrastructure without measurements. The harness is ready, but **v4.94.0's value is potential, not realized.**

### Compile-time impact

No significant compile-time change expected — StringBuilder is a C runtime addition, not an emitter change. The `string_concat_optimization` MIR pass adds one more pass to the O2 fixpoint loop, but it's O(n) in instructions and idempotent. Negligible overhead.

### Cross-platform readiness

The scheduler uses POSIX pthreads, condvars, and `clock_gettime(CLOCK_REALTIME)`. This works on Linux and macOS but not on Windows (no native pthreads). The existing thread pool has the same limitation with Windows `CRITICAL_SECTION`/`HANDLE` abstractions. The scheduler should use the same abstractions. **Currently Linux/macOS only.**

### Test coverage numbers

- 1412/1412 core tests pass
- 73/73 MIR optimizer tests pass
- 5/5 async golden tests emit valid IR
- C runtime compiles on Linux

## Items

| Item | Priority | Notes |
|------|----------|-------|
| C-level unit tests for StringBuilder | HIGH | No test coverage for the core runtime addition |
| Rebuild libmapanare_rt.a for benchmark linking | MEDIUM | Infrastructure ready but no numbers |
| Windows scheduler using platform abstractions | LOW | Currently POSIX-only |
| Go installation for benchmark comparison | LOW | Programs written, toolchain missing |

## Score justification

8/10 — the infrastructure is solid and the Python-side CI coverage is complete. Deduction for missing C-level tests and unrealized benchmark measurements. The benchmark harness is well-designed but delivered potential, not numbers.
