# v4.104.0 Phase 4 — Async golden tests native execution

**Date:** 2026-04-13
**Tests:** `55_async_basic.mn`, `56_async_await.mn`, `57_real_await.mn`

## Pipeline

Each test went through:
```
python3 -m mapanare emit-llvm tests/golden/<t>.mn -o <t>.ll
llvm-as <t>.ll -o <t>.bc
opt -O2 <t>.bc -o <t>.opt.bc
llc <t>.opt.bc -o <t>.s
clang -no-pie <t>.s runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o <t>.bin
./<t>.bin
```

## Results

| Test | Expected | Got | Link OK | Run OK | Valgrind |
|---|---|---|---|---|---|
| 55_async_basic | 42 | **42** | ✅ | ✅ exit 0 | ✅ clean |
| 56_async_await | 43 | **43** | ✅ | ✅ exit 0 | ✅ clean |
| 57_real_await | 110 | **110** | ✅ | ✅ exit 0 | ✅ clean |

All three tests produce the correct output and valgrind reports no
errors (`--error-exitcode=99` → exit 0 for all three).

## Scheduler exports confirmed

`nm /tmp/v4_104_integration/55_async_basic.bin` confirms the v4.102.0
scheduler exports are present in the final binary:

```
__mn_coro_register_wait
__mn_coro_scheduler_destroy
__mn_coro_scheduler_init
__mn_coro_scheduler_register
__mn_coro_scheduler_run
__mn_coro_spawn
```

v4.102.0's fix — making `libmapanare_rt.a` export the scheduler API so
that `block_on` / `await` can link — survives the clean rebuild.

## Binary size

~81 KB per async test binary (stripped ELF).

## Exit criterion (Exit #4)

- [x] Async golden tests (55, 56, 57) compile through the native pipeline.
- [x] Link against `libmapanare_rt.a` (scheduler exports present).
- [x] Run with correct output (42, 43, 110).
- [x] Valgrind clean — no leaks/errors during coroutine execution.
