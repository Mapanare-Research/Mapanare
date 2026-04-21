# Mapanare v4.92.0 — Real Suspension at Await Points

> **Arc 13 release 1.** The current async model (shipped in Arc 9,
> v4.67.0-v4.76.0) is cooperative single-threaded with inline-resume:
> when a coroutine hits `await`, the scheduler immediately resumes the
> awaited coroutine in the same call stack. This works for structured
> concurrency but cannot express I/O-bound workloads where the caller
> must yield control to the scheduler and be resumed later. v4.92.0
> upgrades `await` to emit a real `llvm.coro.suspend` that saves the
> coroutine frame to heap and returns control to the scheduler. The
> scheduler resumes the coroutine only when the awaited future becomes
> ready — enabling true non-blocking I/O.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.91.0
**Delta review:** No
**Full panel:** No (v4.96.0)
**Estimated work:** 1 sprint
**Theme:** Await means yield. The coroutine frame survives across suspension points and the scheduler drives resumption.

---

## Scope

Arc 13 is "Runtime + Concurrency Maturity." The async/await shipped in
Arc 9 proved the coroutine infrastructure works end-to-end, but it used
Option A from DESIGN.md section 5.2: cooperative inline scheduling on a
single thread. Resumption was immediate — `await future` would poll
the future in a tight loop and resume the awaited coroutine inline. This
means no real concurrency: coroutine A cannot make progress while
coroutine B is suspended waiting for I/O.

v4.92.0 changes the await semantics so that `await expr` emits a true
`llvm.coro.suspend` call. The coroutine frame is saved to the heap
(this already happens — CoroSplit puts spilled values in the frame
struct). The difference is in the scheduler: instead of polling inline,
`block_on()` becomes a scheduler loop that checks readiness of all
registered futures and resumes whichever coroutines are unblocked.

To prove this works with real I/O, we add `mapanare_file_read_async()`
to the C runtime — a non-blocking file read using epoll (Linux) that
registers a file descriptor and completes asynchronously. An async
golden test reads a file, suspends while waiting, and other work runs
in the meantime.

### What changes in the emitter

In `emit_llvm_text.py`, the `AwaitExpr` emission path currently generates:

1. Call the awaited async function (produces `Future<T>`)
2. Immediately poll in a loop: check `future.state`, if Pending call
   `llvm.coro.resume` on the awaited coroutine, repeat
3. Extract value when Ready

After v4.92.0, step 2 becomes:

1. Call the awaited async function (produces `Future<T>`)
2. Check `future.state` — if Ready, skip to extraction
3. If Pending: store the awaited future handle in the coroutine frame
   (scheduler-visible), call `llvm.coro.save` + `llvm.coro.suspend`,
   switch on result (0=resume, 1=cleanup, default=return to scheduler)
4. When scheduler resumes us: extract value from the now-ready future

This matches the canonical pattern in DESIGN.md section 4.7.2 — the
code was already designed for this; v4.70.0 just took the simpler
inline-resume shortcut.

---

## Phase 1 — Design real suspension model

- [ ] Document the suspension model in `docs/roadmap/v4/v4.92.0/SUSPENSION.md`:
  - Coroutine frame layout review (resume ptr, destroy ptr, suspend index, spills)
  - Scheduler-visible state: how the scheduler knows which future a coroutine is awaiting
  - Readiness notification: the completing coroutine sets `future.state = Ready` and the scheduler sees it on the next tick
  - Backward compatibility: callers using `block_on()` see the same behavior (block_on polls the scheduler loop)
- [ ] Review DESIGN.md sections 4.7.2 and 5.3 for alignment

## Phase 2 — Modify emitter coroutine lowering

- [ ] In `mapanare/emit_llvm_text.py`, change `await` emission from inline-resume to real suspend:
  - Emit `llvm.coro.save` + `llvm.coro.suspend` at each `await` point
  - Emit the 3-way switch: resume -> extract value, cleanup -> drop glue, default -> return to scheduler
  - Store the awaited future pointer in a frame-visible location (alloca that survives suspend)
- [ ] Update `block_on()` emission: instead of a tight poll loop, emit a call to the C runtime scheduler loop `mapanare_coro_scheduler_run()`
- [ ] Ensure `presplitcoroutine` attribute is still emitted on all async functions
- [ ] Unit tests: verify emitted IR matches the canonical pattern from DESIGN.md section 4.7.2

## Phase 3 — Async file I/O in C runtime

- [ ] Add `mapanare_file_read_async()` to `runtime/native/mapanare_runtime.c`:
  - Signature: `void mapanare_file_read_async(const char *path, void *future_ptr)`
  - Opens file, reads contents into a heap-allocated string
  - Sets `future.state = Ready` and `future.payload = string_ptr` when done
  - On Linux: use non-blocking I/O with the existing epoll event loop
  - On other platforms: fallback to synchronous read (still sets future to Ready)
- [ ] Add corresponding declaration to the runtime header
- [ ] C-level unit test: read a known file asynchronously, verify contents

## Phase 4 — I/O-bound golden test

- [ ] Create `tests/golden/58_async_file_io.mn`:
  - `async fn read_file(path: String) -> String` that calls the C runtime async read
  - Main spawns two file reads concurrently, awaits both
  - Verifies contents match expected values
  - Prints a checksum line for golden validation
- [ ] Create `tests/golden/58_async_file_io.expected` output file
- [ ] Verify the test passes through the full pipeline (emit -> llvm-as -> opt -> llc -> link -> run)

## Phase 5 — Memory safety verification

- [ ] Valgrind clean on all async golden tests (55, 56, 58)
- [ ] Verify no dangling coroutine frames: every `coro.begin` has a matching `coro.destroy`
- [ ] Verify no double-free on coroutine frames
- [ ] Test: destroy a coroutine before it completes (cancel path) — drop glue runs, no leaks
- [ ] AddressSanitizer clean on the async test suite

## Phase 6 — Backward compatibility + golden pass

- [ ] Existing async golden tests pass unchanged (55_async_basic.mn, 56_async_await.mn)
- [ ] Full golden suite: 58/58 pass
- [ ] `make test` passes — no regressions in the 4,800+ test suite
- [ ] `make lint` passes

## Phase 7 — LOW sweep + closeout

- [ ] Grep for `TODO(v4.92)` or unfinished items
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `await` emits real `llvm.coro.suspend` (not inline-resume) | IR diff of `emit_llvm_text.py` await emission |
| 2 | `block_on()` drives the scheduler loop (not tight poll) | IR inspection of block_on emission |
| 3 | `mapanare_file_read_async()` exists in C runtime | `grep mapanare_file_read_async runtime/native/mapanare_runtime.c` |
| 4 | `58_async_file_io.mn` golden test exists and passes | `python scripts/test_native.py --filter 58` |
| 5 | I/O test demonstrates real suspension (concurrent reads faster than sequential) | Wall-time measurement in test output |
| 6 | Valgrind clean on all async golden tests | valgrind log |
| 7 | ASan clean on async test suite | ASan build + run |
| 8 | Existing async tests still pass unchanged | golden 58/58 |
| 9 | `make test` passes | CI log |
| 10 | `make lint` passes | CI log |

---

## What this release does NOT do

- **Multi-threaded scheduling** — v4.92.0 is still single-threaded. Real suspension enables the scheduler to interleave coroutines on one thread. Multi-threaded scheduling is v4.93.0.
- **Network I/O** — only file I/O is added. TCP/HTTP async is future work.
- **Structured concurrency** — no nurseries, no cancellation tokens. Those are v5.x.
- **Self-hosted emitter changes** — `emit_llvm.mn` is not updated. The Python emitter is the primary target.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Real suspension changes coroutine frame ABI | medium | high | Frame layout is determined by LLVM CoroSplit, not by us — our change is in what the scheduler does with the handle, not the frame shape. No ABI break. |
| Existing async tests break because inline-resume timing changes | medium | medium | The tests check correctness (output values), not timing. If any test relied on inline-resume ordering, fix the test. |
| epoll-based async file I/O is platform-specific | low | medium | Fallback to synchronous read on non-Linux platforms. CI runs on Ubuntu. |
| Drop glue in cleanup paths may miss values live across new suspend points | medium | high | Valgrind + ASan gate. Test cancel-before-complete scenario explicitly. |
| `opt -O2` may reorder or eliminate suspend points | low | high | `llvm.coro.suspend` is a side-effecting intrinsic — LLVM cannot remove it. Verify with IR inspection. |

---

## After v4.92.0

v4.93.0 adds the multi-threaded work-stealing scheduler (Option B from DESIGN.md). With real suspension in place, coroutines can now be distributed across threads — each thread resumes whichever coroutine becomes ready next.
