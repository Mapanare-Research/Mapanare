# Mapanare v4.73.0 — Runtime Scheduler Integration

> **Arc 9 release 2.** Extends the C runtime cooperative scheduler
> (currently mobile-only) to desktop. `async fn` goes from "produces
> valid IR" to "actually runs to completion." The load-bearing
> milestone: `async fn foo() -> Int { return 42 }` called from
> `main()` returns 42.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.72.0
**Delta review:** No (runtime work)
**Full panel:** No (v4.76.0)
**Estimated work:** 2 sprints
**Theme:** Scheduler drives the coroutines. The future representation is wired. `await` actually blocks on a real completion.

---

## Scope

### Extending the mobile scheduler

`runtime/native/mapanare_runtime.c` already has a cooperative scheduler gated on `MAPANARE_MOBILE`. It tracks agents and polls inboxes. For v4.73.0:

1. Remove the `MAPANARE_MOBILE` gate (or keep it as a fallback; default-on for desktop)
2. Add coroutine tracking: `mn_scheduler_register_coroutine(handle)`, `mn_scheduler_resume_ready()`, `mn_scheduler_destroy_coroutine(handle)`
3. Add a main scheduler loop that runs after `main()` body completes, driving registered coroutines to completion before the program exits

### The driver pattern

```llvm
; In mn_user_main (wraps user's main):
define i32 @main(i32 %argc, ptr %argv) {
  call void @mn_runtime_init()
  call void @__mn_user_main_impl(i32 %argc, ptr %argv)
  call void @mn_scheduler_run_until_done()  ; NEW: drives any pending coroutines
  call void @mn_runtime_shutdown()
  ret i32 0
}
```

After `__mn_user_main_impl` returns, any `async fn` calls that produced `Future<T>` values still in flight get driven to completion by the scheduler loop. The program exits only when all pending futures have resolved (or been canceled).

---

## Phase 1 — Scheduler data structures

- [ ] `runtime/native/mapanare_runtime.h`:
  ```c
  typedef struct MnCoroutineEntry {
      void *handle;  // the ptr from llvm.coro.begin
      void *frame;   // the heap frame (for llvm.coro.free)
      int state;     // 0 = pending, 1 = ready, 2 = done
      struct MnCoroutineEntry *next;
  } MnCoroutineEntry;

  typedef struct MnScheduler {
      MnCoroutineEntry *head;
      size_t count;
      mapanare_mutex_t lock;
  } MnScheduler;
  ```
- [ ] Single global scheduler instance `static MnScheduler g_scheduler`.

## Phase 2 — Scheduler API

- [ ] `runtime/native/mapanare_runtime.c`:
  - `mn_scheduler_init(void)` — called from `mn_runtime_init`
  - `mn_scheduler_register_coroutine(void *handle, void *frame)` — called by the emitted code after `llvm.coro.begin`
  - `mn_scheduler_resume_ready(void)` — called from the main loop; walks pending entries, resumes those with a ready future
  - `mn_scheduler_destroy_coroutine(void *handle)` — removes from the list, calls `llvm.coro.destroy`
  - `mn_scheduler_run_until_done(void)` — main loop: while `count > 0`, resume ready, sleep briefly if none ready (bounded yield)
  - `mn_scheduler_shutdown(void)` — called from `mn_runtime_shutdown`

## Phase 3 — Future representation runtime support

- [ ] Each `Future<T>` has the layout `{i8 state, T value}` per DESIGN.md §4.
- [ ] Runtime helpers:
  - `__mn_future_set_ready(void *future_ptr, size_t value_size, void *value)` — writes the value slot + sets state to 1
  - `__mn_future_check_ready(void *future_ptr) -> bool` — reads the state slot
  - The emitter calls these from `async fn` bodies when a return happens

## Phase 4 — Emitter integration

- [ ] `mapanare/emit_llvm_text.py` — the `async fn` prelude now calls `__mn_scheduler_register_coroutine` after `llvm.coro.begin`:
  ```llvm
  %hdl = call ptr @llvm.coro.begin(token %id, ptr %frame)
  call void @__mn_scheduler_register_coroutine(ptr %hdl, ptr %frame)
  ```
- [ ] The `mn_user_main` wrapper (whatever Mapanare generates as the entry point) now calls `mn_scheduler_run_until_done` after the user's main returns:
  ```llvm
  ; existing user_main
  call void @__mn_scheduler_run_until_done()
  ```

## Phase 5 — Minimal async test

- [ ] `tests/golden/async_simple.mn`:
  ```mapanare
  async fn compute() -> Int {
      return 42
  }

  fn main() {
      let future: Future<Int> = compute()
      // Main isn't async, so we can't `await` here.
      // Instead, the scheduler drives the future to completion before exit.
      // Need a block_on helper:
      let result: Int = block_on(future)
      print(result)  // expect 42
  }
  ```
- [ ] **Blocker:** `main` isn't async, so `await` doesn't work. v4.73.0 introduces `block_on` as a runtime primitive that a non-async caller can use to wait for a future. It's a blocking call that drives the scheduler loop until the specific future is ready:
  ```c
  int64_t __mn_future_block_on_i64(void *future_ptr) {
      while (!__mn_future_check_ready(future_ptr)) {
          mn_scheduler_resume_ready();
          mn_scheduler_yield();  // bounded sleep
      }
      return *(int64_t*)((char*)future_ptr + sizeof(int8_t));  // read value slot
  }
  ```
- [ ] `block_on(future)` exposed as a Mapanare builtin

## Phase 6 — Async-with-await test

- [ ] `tests/golden/async_with_await.mn`:
  ```mapanare
  async fn inner() -> Int {
      return 42
  }

  async fn outer() -> Int {
      let x: Int = await inner()
      return x + 1
  }

  fn main() {
      let result: Int = block_on(outer())
      print(result)  // expect 43
  }
  ```
- [ ] This exercises:
  - Nested async fn
  - Real suspension at the `await inner()` point
  - Resume via the scheduler
  - Value flow through the `Future<Int>` return

## Phase 7 — Scheduler stress test

- [ ] `tests/runtime/test_scheduler_stress.c`:
  - Spawn 100 coroutines
  - Each suspends N times
  - Drive scheduler until done
  - Verify all 100 complete with the expected results
- [ ] Running time should be sub-second for 100×10 suspensions on a modern CPU

## Phase 8 — Thread safety

- [ ] The scheduler is NOT thread-safe for v4.73.0. Cooperative only. Multi-threaded scheduling is v5.x.
- [ ] The `g_scheduler.lock` exists for future-proofing but is only acquired around individual `register` / `destroy` operations, not across resume.
- [ ] Document this clearly in the runtime code comments.

## Phase 9 — LOW sweep

2 items.

## Phase 10 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.73.0
- [ ] `CHANGELOG.md [4.73.0]` — **the big one**. async/await actually runs. `async fn foo() -> Int { return 42 }` compiles and executes and returns 42.
- [ ] SESSION_REPORT with celebratory note

---

## Exit criteria (15 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `MnScheduler` data structures defined | grep |
| 2 | `mn_scheduler_register_coroutine` works | unit test |
| 3 | `mn_scheduler_resume_ready` drives ready coroutines | unit test |
| 4 | `mn_scheduler_run_until_done` main loop | unit test |
| 5 | Emitter wraps user main with scheduler drive call | grep generated IR |
| 6 | `async fn` registers itself via generated code | grep IR |
| 7 | `__mn_future_set_ready` + `_check_ready` work | unit tests |
| 8 | `block_on(future)` builtin available | compile test |
| 9 | **`tests/golden/async_simple.mn` runs and prints 42** | runtime log |
| 10 | **`tests/golden/async_with_await.mn` runs and prints 43** | runtime log |
| 11 | Scheduler stress test passes (100 coros × 10 suspensions) | `test_scheduler_stress` |
| 12 | No leaks (valgrind clean on async_simple + async_with_await) | valgrind |
| 13 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 14 | Self-hosted mirror runtime hooks | rebuild + test |
| 15 | Standard closeout clean | CI |

---

## What v4.73.0 does NOT do

- **Multi-threaded scheduling** — v5.x
- **I/O-driven scheduling (epoll/kqueue)** — v5.x; v4.73.0 uses a simple polling loop
- **`for await chunk in stream`** — v4.74.0
- **Cancellation / timeouts** — v5.x
- **Backpressure beyond what the stream primitive already has** — no

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| The scheduler polling loop has a busy-wait CPU burn | medium | medium | `mn_scheduler_yield()` inserts a brief `nanosleep`; not perfect but adequate for v4.73.0 |
| `block_on` deadlocks if the future depends on the main thread | medium | high | Document the limitation; users can avoid by structuring code to not create such cycles |
| Coroutine frame not freed on normal completion | medium | high | LLVM's `coro-split` handles this via `llvm.coro.free`; verify with valgrind |
| Scheduler crashes if a coroutine handle is destroyed twice | low | high | Reference counting on the entry; or: only destroy via scheduler API |
| Cleanup path runs drop glue twice | medium | medium | Coroutine state machine prevents; verify with stress test |

---

## Reference

- [`v4.67.0/DESIGN.md`](../v4.67.0/DESIGN.md) §5

---

## After v4.73.0

v4.74.0 adds `Stream<T>.next() -> Future<Option<T>>` and the `for await chunk in stream { ... }` syntax. Delta review for the new syntax.
