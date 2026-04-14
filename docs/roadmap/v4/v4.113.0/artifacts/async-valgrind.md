# v4.113.0 — Async Golden Valgrind (Phase 2 verification)

Phase 1 changed `mn_coro_is_done` / `mn_coro_resume` in
`runtime/native/mapanare_runtime.c` to access the coroutine frame
through a typed `mn_coro_frame_prefix_t` struct instead of raw
`*(void **)handle` casts. This artifact records the post-change
async test runs and proves the fix is memory-neutral.

## Pipeline

```
python3 -m mapanare emit-llvm tests/golden/<test>.mn -o /tmp/<test>.ll
clang /tmp/<test>.ll -L runtime/native -lmapanare_rt -lpthread -lm -ldl -o /tmp/<test>
/tmp/<test>             # check output
valgrind --error-exitcode=99 --errors-for-leak-kinds=none --leak-check=full \
         --show-leak-kinds=all /tmp/<test>
```

Same pipeline the CI `integration` and `tsan-async` jobs run.

## Native output

| Test | Expected | Actual | Pass? |
|---|---|---|---|
| 55_async_basic | 42 | 42 | yes |
| 56_async_await | 43 | 43 | yes |
| 57_real_await | 110 | 110 | yes |

## Valgrind — post-change (v4.113.0)

| Test | `definitely lost` | `indirectly lost` | `possibly lost` | `still reachable` | ERROR SUMMARY |
|---|---|---|---|---|---|
| 55_async_basic | 0 | 0 | 0 | 0 | 0 errors from 0 contexts |
| 56_async_await | 32 B (1 block) | 24 B (2 blocks) | 0 | 0 | 0 errors from 0 contexts |
| 57_real_await | 96 B (3 blocks) | 72 B (6 blocks) | 0 | 0 | 0 errors from 0 contexts |

## Valgrind — pre-change control (v4.112.0 `mn_coro_is_done`)

Checked out `HEAD~1:runtime/native/mapanare_runtime.c`, rebuilt
`libmapanare_rt.a`, re-linked both leaky binaries:

| Test | `definitely lost` | `indirectly lost` |
|---|---|---|
| 56_async_await | 32 B (1 block) | 24 B (2 blocks) |
| 57_real_await | 96 B (3 blocks) | 72 B (6 blocks) |

**Identical.** The leaks trace to user coroutine bodies
(`inner.resume`, `outer.resume`, `fetch_a/b/c`) boxing return values
with `malloc` — call chain ends in
`mn_process_task` → `__mn_coro_scheduler_run`, never through
`mn_coro_is_done` or `mn_coro_resume`. Both pre-date v4.113.0 and are
outside the scope of docket #8.

## CI baseline cross-check

`docs/roadmap/v4/v4.105.0/artifacts/valgrind-summary.tsv` classifies
all three async tests as `WARNINGS_ONLY` (the middle bucket —
memory leaks tolerated, memory-safety errors not). Post-change ERROR
SUMMARY is `0 errors from 0 contexts` on all three, so the CI gate
`scripts/check_valgrind_baseline.py` would pass.

## Conclusion

Docket #8 (coroutine frame decoupling) is fixed without regression.
Async goldens produce correct output (42, 43, 110) and no new memory
errors. Remaining leaks are pre-existing, unrelated to the coroutine
frame ABI surface, and tracked separately.
