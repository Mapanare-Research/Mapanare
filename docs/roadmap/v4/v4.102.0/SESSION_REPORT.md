# v4.102.0 Session Report — 2026-04-13

## Verdict

**Shipped. First native async run in the history of the project.**
All three async golden tests (`55_async_basic.mn`, `56_async_await.mn`,
`57_real_await.mn`) compile through the Python bootstrap emitter,
link against the runtime archive, and execute to completion with the
expected output (42, 43, 110). Valgrind clean: zero errors, zero
leaks on 55_async_basic. Dockets #3 (async can't link) and #6
(implicit — runtime symbol export) closed.

## Root cause (two bugs, same symptom)

The Phase 1 audit disproved the simple read of docket #3. The six
`__mn_coro_scheduler_*` symbols were **already** present in
`libmapanare_rt.a` as `T` (defined code). The Makefile's
`RUNTIME_SOURCES` list includes `mapanare_runtime.c` and has since
v4.29.0 when Anaconda's HIGH finding added the drift check. The
scheduler wasn't missing from the archive — it was missing from
anything that actually ran.

Linking `55_async_basic.mn` succeeded on the first try. Running it
segfaulted in `mn_process_task`, calling a NULL function pointer.
Two bugs in series:

**Bug 1 — `mn_coro_is_done` reads the wrong frame offset.** The
inline helper in `mapanare_runtime.c:1517-1519` checked byte
`handle[16]` for values `0xFF` or `0x01`, documenting the check as
"LLVM switched-resume ABI". Modern LLVM (18.x) does not encode the
done marker at that offset — the byte there is user state, not a
status marker. LLVM's actual done signal, after
`llvm.coro.suspend(..., i1 true)` (a final suspend) is lowered by
the coroutine splitter, is a store of NULL into the resume-function
slot at `handle[0]`. This is what `llvm.coro.done(handle)` resolves
to.

With the old check, the scheduler never saw a coroutine as done,
always re-enqueued it, and the next iteration called
`resume_fn(handle)` with `resume_fn == NULL` — the NULL call in the
backtrace.

Fix: `return *(void **)handle == NULL;`. Three lines, no edge cases.

**Bug 2 — `_do_block_on` reloaded the coroutine handle from a slot
the coroutine overwrites.** The emitter modeled `Future` as
`{i8 state, ptr payload}`. At `compute()` entry, `payload` holds the
coroutine handle. At final suspend, `compute.resume` stores the
boxed return value into `payload` — overwriting the handle.

The old `_do_block_on` in `emit_llvm_text.py:4796-4800` loaded
`payload` three times: once to register the handle before
`scheduler_run`, once to dereference the boxed return after
`scheduler_run`, and once more to pass to `llvm.coro.destroy`. The
third load returned the boxed-value pointer (an 8-byte malloc),
and `coro.destroy` lowers to `handle->destroy_fn()` — calling an
integer as a function pointer.

Fix: pass the `hd` SSA value loaded before `scheduler_run` directly
to `coro.destroy`. That value is the handle the coroutine frame
lives at; its `destroy_fn` at offset 8 is still valid after the
resume-fn slot at offset 0 was nulled on final suspend.

## Phase 1 — Audit the build system

- `runtime/native/Makefile` target `build-rt` enumerates
  `RUNTIME_SOURCES` including `mapanare_runtime.c`. Archive
  contained all 6 scheduler symbols as `T`. No build-system gap.
- The docket item description matched a build-system bug but the
  underlying blocker was a runtime correctness bug.

## Phase 2 — Fix the runtime + emitter

- `runtime/native/mapanare_runtime.c:1517-1519` —
  `mn_coro_is_done` rewritten to check `handle[0] == NULL`.
  Explanatory comment documents the LLVM-lowering correspondence.
- `mapanare/emit_llvm_text.py:4795-4810` — `_do_block_on` reuses
  the `hd` SSA value from before `scheduler_run` for the
  destroy-and-free sequence. Explanatory comment documents the
  payload-slot overwrite that made the reload dangerous.
- `make build-rt` reproduces; `nm` confirms all scheduler symbols
  still defined (`T`), no undefined references.

## Phase 3 — Compile + link + run `55_async_basic.mn`

```
$ python3 -m mapanare emit-llvm tests/golden/55_async_basic.mn -o /tmp/55.ll
$ clang /tmp/55.ll -L runtime/native -lmapanare_rt -lpthread -lm -ldl -o /tmp/55
$ /tmp/55
42
$ echo $?
0
```

Expected output: `42`. **First native async run succeeded.**

## Phase 4 — Other async goldens

Same pipeline for `56_async_await.mn` (output `43`) and
`57_real_await.mn` (output `110`). All three pass.

The ramp function for each async fn emits `presplitcoroutine`;
`clang -O0` will run the coroutine splitter at codegen; linking
works with or without `opt` invocation. The `opt
'default<O2>'` pre-pass is not required for correctness — the
optimized version produces the same result.

## Phase 5 — CI step

Added to `.github/workflows/ci.yml` in the `native` job, after the
`test_html_smoke` step and before the Makefile drift check. The
step:

1. Installs `llvm-18` + `clang-18` and symlinks `clang`.
2. Sets up Python 3.12 and installs Mapanare (for `emit-llvm`).
3. For each of the three async goldens: Python bootstrap → clang
   link → run → compare output against `42` / `43` / `110`.
4. Fails loudly on mismatch, with a timeout of 10s per test.

Tested locally: all three pass in ~2 seconds on a recent Ryzen box.

## Phase 6 — Closeout

- `VERSION` bumped to 4.103.0 in the final commit.
- `CHANGELOG.md [4.102.0]` written.
- `SESSION_REPORT.md` (this file).
- `docs/roadmap/v4/README.md` row added.
- `docs/roadmap/ROADMAP.md` "Where We Are" updated.
- `CLAUDE.md` current version entry added.

## Exit criteria (9 items)

| # | Check | Status |
|---|---|---|
| 1 | Scheduler source in `libmapanare_rt.a` | ✅ Confirmed pre-existing (v4.29.0); `mapanare_runtime.c` in `RUNTIME_SOURCES` |
| 2 | `nm` shows `__mn_coro_scheduler_*` as `T` | ✅ All 6 symbols defined |
| 3 | `55_async_basic.mn` compiles + links + runs | ✅ Output `42` |
| 4 | `56_async_await.mn` compiles + links + runs | ✅ Output `43` |
| 5 | `57_real_await.mn` compiles + links + runs | ✅ Output `110` |
| 6 | All three produce correct output | ✅ |
| 7 | CI step added | ✅ `.github/workflows/ci.yml` native job |
| 8 | No undefined scheduler symbols | ✅ `nm -u` clean for coro |
| 9 | 16/62 goldens still pass through mnc-stage1 | ✅ No regressions from v4.101.0 baseline |

All 9 met.

## Deviation from plan

The plan assumed docket #3 was a build-system gap (missing scheduler
object in the archive). Phase 1 disproved that — the archive was
complete. The real blockers were one runtime-correctness bug and
one emitter bug. Both fixes are surgical (3 lines + 5 lines
respectively). The Phase 1 audit was not wasted: confirming the
archive was whole ruled out a class of fixes that would have
cascaded through the build system.

The plan scoped Phase 2 as "Fix the build and rebuild". The actual
Phase 2 was "Fix the runtime's done-detection and rebuild". The
end state — a working archive that runs async programs — is
identical; only the intermediate work changed.

## Docket status

- **Docket #3 (async can't link)** — CLOSED. Linking was not the
  final blocker (it worked on first try after the v4.101.0 move-
  semantics fix made the emitted IR valid); running was.
- **Docket #6 (runtime symbol export)** — CLOSED. All scheduler
  symbols exported as `T`, no undefined references in the archive.

## Follow-up (noted, not this release)

- The `_do_block_on` emitter code still has an implicit assumption
  that the Future's payload slot can be overwritten in-place by the
  coroutine. A cleaner design would separate the handle from the
  return value (e.g., `{i8 state, ptr handle, ptr payload}`). This
  is architectural cleanup, not a correctness issue.
- `mn_process_task` unconditionally calls `mn_coro_resume` even if
  the task was re-enqueued from the wait queue and the awaited
  future is now ready. The current control flow works, but the
  resume call at the top of the function is not the only place
  a coroutine can be resumed — there are subtle race possibilities
  in the multi-threaded scheduler. Mamba's v4.99.0 MEDIUM on
  "coroutine frame coupling fragile" is still valid.
- LLVM's `opt 'default<O2>'` is not strictly required to run the
  coroutine passes — `clang -O0` handles them at codegen. If a
  future LLVM version changes that, the CI step will surface the
  regression.

## After v4.102.0

v4.103.0 closes Phase A with the two remaining HIGH items: else/sino
verification (docket #4) and closure type annotations (docket #5).
After v4.103.0, all 5 critical/high docket items from the v4.99.0
panel are fixed and Phase A closes. v4.104.0 begins Phase B: rebuild
and verify the full pipeline end-to-end before the next panel at
v4.106.0.
