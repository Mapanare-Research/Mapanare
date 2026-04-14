# v4.115.0 Phase 4 — C Runtime Additions Needed

## Decision: none

Per PROMPT.md Decision 3 ("minimal"), the two demo programs
(`examples/async_file_io.mn`, `examples/async_http_demo.mn`)
compile, link, and run against the existing `libmapanare_rt.a`
without adding a single new symbol.

Every function the demos call is already exported from the runtime
archive at the start of v4.115.0:

| Symbol | Source | Role in demos |
|---|---|---|
| `__mn_file_read_or_empty` | `runtime/native/mapanare_core.c:2765` | Read input file |
| `__mn_file_write` | `runtime/native/mapanare_core.c:1411` | Write summary file |
| `__mn_http_get` | `runtime/native/mapanare_io.c:1598` | HTTP GET to example.com |
| `__mn_coro_scheduler_init/register/register_wait/run/destroy` | `runtime/native/mapanare_runtime.c:1670-1824` | async coroutine driver (emitted by `block_on` lowering) |
| `__mn_str_concat` | `runtime/native/mapanare_core.c:447` | String concat inside `write_summary` body |
| `__mn_int_to_str` / `__mn_str_*` helpers | `runtime/native/mapanare_core.c` | `str(Int)` conversion |

Verified:

```
$ nm runtime/native/libmapanare_rt.a | grep -E "__mn_(file_(read_or_empty|write)|http_get|coro_scheduler|str_concat)" | head
0000000000005520 T __mn_coro_scheduler_destroy
0000000000005080 T __mn_coro_scheduler_init
0000000000005230 T __mn_coro_scheduler_register
0000000000005420 T __mn_coro_scheduler_run
00000000000050f0 T __mn_file_read_or_empty
0000000000002e00 T __mn_file_write
0000000000002690 T __mn_http_get
0000000000000180 T __mn_str_concat
```

## Why nothing was added

Decision 1 set the async I/O model to "wrap synchronous" — the C
runtime's synchronous `fopen`/`fread`/`fwrite` and libcurl-backed
`__mn_http_get` are sufficient for a cooperative async demo.
True non-blocking I/O (epoll + O_NONBLOCK + poll-for-readiness
in the scheduler) is a v5.x feature per the plan's
"What this release does NOT do" section.

The existing `__mn_file_read_async` (in
`runtime/native/mapanare_runtime.c:1885`) already offers a
thread-pool-backed background read that yields a `Future`, but no
Mapanare source has ever invoked it — the emitter cannot lower
`await` on a String-returning async fn (Sh.9), and that's the
shape `__mn_file_read_async` needs. Making it callable from user
Mapanare code is a larger change that belongs with the Sh.9 fix.

## Regression check

`libmapanare_rt.a` is unchanged at v4.115.0 (no source
modifications in `runtime/native/*.c`). The async golden tests
(55/56/57) still link and run:

```
$ for t in 55_async_basic 56_async_await 57_real_await; do
    python3 -m mapanare emit-llvm tests/golden/$t.mn -o /tmp/$t.ll
    clang /tmp/$t.ll -L runtime/native -lmapanare_rt -lpthread -lm -ldl -o /tmp/$t
    /tmp/$t
  done
42
43
110
```

Unchanged from v4.114.0.
