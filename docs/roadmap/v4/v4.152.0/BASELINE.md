# v4.152.0 E8 Baseline

Captured before any pass re-enable. All measurements taken on WSL2
(Linux 5.15, AMD64, Python 3.12, clang 14, gcc 12).

## Stage IR

| Artifact | Lines | md5 |
|---|---|---|
| `main.ll` (bootstrap → self-hosted) | 912,184 | — |
| `stage2.ll` (mnc-stage1 compiles self) | 110,127 | `39b68cd7333a4c0f69f58bcc9f8e8280` |
| `stage3.ll` (mnc-stage2 compiles self) | 110,127 | `612b352c8c4c86b1a326d967c92a7419` |

Fixed-point: **NEAR FIXED POINT** — 4 diff lines (version placeholder only),
within `DIFF_THRESHOLD=100`.

## Build time

`python3 scripts/build_stage1.py`:
- **real 1m42s** (102s wall)
- user 1m37s, sys 1s

## Golden tests

**54/66** through `mnc-stage1` (12 failures are known: async, tensor,
match_guards, closure_typed — all pre-existing).

## Pytest

- Non-bootstrap: **5,298 passed / 0 failed** / 115 skipped / 9 xfailed
- Bootstrap: (carried forward from v4.151.0) 212 / 13

## Sanitizers

| Suite | CLEAN | WARNINGS_ONLY | ERRORS | ASAN_ERROR | CRASH_NO_ASAN |
|---|---|---|---|---|---|
| Valgrind | 0 | 62 | 4 | — | — |
| ASan | 55 | — | — | 0 | 11 |

4 valgrind ERRORS are pre-existing Ge.1 generics residuals.
11 CRASH_NO_ASAN are pre-existing (async/tensor/closure tests that fail
to compile, not ASan findings).

## CI gates

| Gate | Status |
|---|---|
| `ruff check .` | clean |
| `black --check .` | 353 unchanged |
| `mypy mapanare/ runtime/` | 0 issues (53 files) |
| `check_struct_registry.py` | clean (23/23/89) |

## Cross-language benchmarks (median, 20 runs)

| Benchmark | C gcc | Rust | Go | Mapanare | Ratio vs Rust |
|---|---|---|---|---|---|
| fib_recursive | 11.13 ms | 18.47 ms | 33.24 ms | 15.26 ms | 0.83× |
| quicksort | 0.345 ms | 0.379 ms | 0.400 ms | 1.121 ms | 2.96× |
| struct_alloc | 0.588 ms | 0.019 ms | 0.020 ms | 0.029 ms | 1.53× |
| enum_match | 0.172 ms | 0.301 ms | 0.200 ms | 0.171 ms | 0.57× |
| prime_sieve | 2.030 ms | 1.778 ms | 2.016 ms | 2.047 ms | 1.15× |
| string_concat | 0.072 ms | 0.038 ms | 42.59 ms | 0.076 ms | 2.00× |

## Async benchmarks (median, 20 runs)

| Benchmark | Mapanare |
|---|---|
| sequential_chain | 2.3 ms |
| fanout | 2.9 ms |
| io_bound | 2.4 ms |
| mixed_cpu_io | 2.4 ms |
| backpressure | 2.3 ms |

## ROI thresholds (per PLAN.md)

A re-enabled pass earns its keep if **any** of:
- stage2.ll line count shrinks ≥ 1% (≥ 1,101 lines)
- Build time drops ≥ 5% (≥ 5.1s)
- Any benchmark improves ≥ 5%

Safety hard-stops (any = immediate roll-back):
- Goldens regress below 54/66
- Valgrind ERRORS increase above 4
- ASan ASAN_ERROR increases above 0
- Fixed-point exceeds DIFF_THRESHOLD=100
