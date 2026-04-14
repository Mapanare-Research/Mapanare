# Mapanare v4.102.0 — Async Linking + End-to-End Native Run

> **Phase A release 3.** The tagged-pointer UB and list indexing bugs are
> fixed (v4.100.0, v4.101.0). The next blockers are docket items #3
> (HIGH) and #6 (implicit): `__mn_coro_scheduler_*` functions are not
> exported to `libmapanare_rt.a`, so no async program has ever linked or
> run natively. This release fixes the build system, links async golden
> tests, and runs them end-to-end.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.101.0
**Delta review:** No
**Full panel:** No (v4.106.0)
**Estimated work:** 1 sprint
**Theme:** Export coroutine scheduler to the runtime archive and run async programs natively for the first time.

---

## Scope

The coroutine scheduler functions (`__mn_coro_scheduler_init`, `__mn_coro_scheduler_run`, `__mn_coro_scheduler_enqueue`, etc.) exist in the C runtime source but are not compiled into or exported from `libmapanare_rt.a`. Any Mapanare program using `async`/`await` compiles to LLVM IR that references these symbols, but linking fails with undefined references.

Anaconda's v4.99.0 review noted: "async can't link." Mamba confirmed: "scheduler export already in source." The fix is a build system change: ensure the scheduler object file is archived into `libmapanare_rt.a`, then verify with `nm`.

Once linking works, we run the three async golden tests (`55_async_basic.mn`, `56_async_await.mn`, `57_real_await.mn`) end-to-end: compile through mnc-stage1, link with `libmapanare_rt.a` and clang, execute the binary, verify output. No async program has ever completed this pipeline natively — this is a first.

## Phase 1 — Audit the build system

- [ ] Read `runtime/native/Makefile` (or equivalent build script) — find how `libmapanare_rt.a` is assembled
- [ ] Identify which `.c` files are compiled into `.o` files and archived
- [ ] Find the scheduler source file (likely `mapanare_coro.c`, `mapanare_scheduler.c`, or scheduler code in `mapanare_runtime.c`)
- [ ] Verify the scheduler functions exist in the source: grep for `__mn_coro_scheduler_init`, `__mn_coro_scheduler_run`, `__mn_coro_scheduler_enqueue`
- [ ] Check current `nm libmapanare_rt.a | grep scheduler` — confirm the symbols are missing

## Phase 2 — Fix the build and rebuild libmapanare_rt.a

- [ ] Add the scheduler source file to the Makefile's object list (or fix whatever exclusion is causing the omission)
- [ ] Rebuild `libmapanare_rt.a`:
  ```bash
  cd runtime/native && make clean && make
  ```
- [ ] Verify with `nm`:
  ```bash
  nm libmapanare_rt.a | grep __mn_coro_scheduler
  ```
  All scheduler symbols must appear as `T` (text/code, defined)
- [ ] Check for undefined symbols in the archive:
  ```bash
  nm -u libmapanare_rt.a
  ```
  No scheduler-related undefined references should remain

## Phase 3 — Compile + link + run `55_async_basic.mn`

- [ ] Compile through mnc-stage1:
  ```bash
  ./mapanare/self/mnc-stage1 tests/golden/55_async_basic.mn -o /tmp/55_async.ll
  ```
- [ ] Link with clang:
  ```bash
  clang /tmp/55_async.ll -L runtime/native -lmapanare_rt -lpthread -o /tmp/55_async
  ```
- [ ] Run the binary:
  ```bash
  /tmp/55_async
  ```
- [ ] Compare output against expected (from Python bootstrap or reference output)
- [ ] If linking fails: check `nm -u /tmp/55_async.o` for remaining undefined symbols, fix each

## Phase 4 — Compile + link + run `56_async_await.mn` and `57_real_await.mn`

- [ ] Repeat Phase 3 for `56_async_await.mn`
- [ ] Repeat Phase 3 for `57_real_await.mn`
- [ ] All three must produce correct output
- [ ] If any has additional undefined symbols beyond the scheduler, document them and fix if possible

## Phase 5 — CI step for async native run

- [ ] Add a step to `.github/workflows/native.yml` (or equivalent CI config):
  - Compile at least one async golden test through mnc-stage1
  - Link with `libmapanare_rt.a`
  - Run the binary and verify output
- [ ] Verify the CI step passes locally before committing:
  ```bash
  # Simulate the CI step
  ./mapanare/self/mnc-stage1 tests/golden/55_async_basic.mn -o /tmp/ci_async.ll
  clang /tmp/ci_async.ll -L runtime/native -lmapanare_rt -lpthread -o /tmp/ci_async
  /tmp/ci_async
  ```

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.102.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Scheduler source compiled into `libmapanare_rt.a` | Makefile diff |
| 2 | `nm libmapanare_rt.a` shows `__mn_coro_scheduler_*` as defined (`T`) | nm output |
| 3 | `55_async_basic.mn` compiles + links + runs natively | binary output |
| 4 | `56_async_await.mn` compiles + links + runs natively | binary output |
| 5 | `57_real_await.mn` compiles + links + runs natively | binary output |
| 6 | All three async tests produce correct output | output comparison |
| 7 | CI step added for async native run | workflow file diff |
| 8 | No undefined scheduler symbols in `nm -u libmapanare_rt.a` | nm output |
| 9 | Existing golden tests (62/62 from v4.101.0) still pass | test log |

---

## What this release does NOT do

- **Fix else/sino or closure types** — that is v4.103.0.
- **Add new async features** — this release makes existing async features work natively. No new syntax, no new runtime primitives.
- **Fix coroutine frame layout coupling** — Mamba noted this as MEDIUM. The frame layout is fragile but functional. Architectural refactoring is deferred.
- **Stress-test the scheduler** — thread pool stress testing under extreme load is a future concern. This release verifies basic correctness.
- **Run a panel** — Phase A has no panel. The next panel is v4.106.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Scheduler functions have unresolved dependencies (e.g., thread pool, arena) | medium | medium | `nm -u` after archive build; link any missing dependencies |
| Async golden tests compile to IR that references symbols beyond scheduler | medium | medium | Phase 3 link step will surface these; fix each undefined symbol |
| Scheduler works on Linux but not on CI runner (different libc, missing pthreads) | low | medium | CI matrix already includes Ubuntu; pthreads is standard |
| Running async binary hangs (deadlock in scheduler) | medium | high | Add timeout to CI step (`timeout 10 /tmp/ci_async`); debug with gdb if hangs |
| Phase 5 CI step is too slow (compiling + linking + running adds to CI time) | low | low | One golden test takes <5 seconds; acceptable overhead |

---

## After v4.102.0

v4.103.0 closes Phase A with two remaining HIGH items: else/sino verification (docket item #4) and closure type annotations (docket item #5). After v4.103.0, all 5 critical/high docket items from the v4.99.0 panel are fixed. v4.104.0 begins Phase B: rebuild and verify the full pipeline end-to-end before the next panel at v4.106.0.
