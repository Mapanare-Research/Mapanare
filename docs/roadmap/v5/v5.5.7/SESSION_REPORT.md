# v5.5.7 — Sanitizer + fixed-point hardening

> **Stabilization release for the async coroutine pipeline
> (v5.5.4–v5.5.6). Closes the v5.5.5 deferred AwaitSuspend
> inner-coroutine leak via handle-hoisting, ships the v5.5.7
> destroy-path drop-glue helper, runs the full sanitizer
> matrix (valgrind + ASan + LSan + TSan) on all 5 Sh.4
> goldens, and roots-causes Ve.1 to a parser buffer overflow.**

**Status:** SHIPPED
**Breaking:** No
**Goldens:** 59/66 unchanged; all 5 Sh.4 execute correctly
(42, 43, 110, done, 220) and now valgrind/ASan/LSan/TSan-clean.

---

## What shipped

### 7.1 — Destroy-path drop-glue helper

`mapanare/self/emit_llvm.mn::emit_drop_glue_destroy(st)` —
new helper iterates `str_owned` / `list_owned` / `boxed_owned`
unconditionally (no `ret_val` filter — there is no return
value on the cleanup path), still consults `moved_locals` so
ownership transferred pre-suspend doesn't double-free. SSA
prefix `%drop.d.*.N` distinct from the normal-exit
`%drop.s|l|b.N` names.

Wired into the async coroutine epilogue's `coro.cleanup:`
block, immediately before `llvm.coro.free`. **No-op for the
5 Sh.4 goldens** (their async fns hold no heap-allocated
locals — just `Int`) but the correct foundation for future
real-I/O async programs that allocate inside the coroutine
frame and may be cancelled mid-flight.

**LOC:** +73 helper / +6 wire-up.

### 7.2 — AwaitSuspend handle-hoist + cleanup (Rt.05 closure)

The structural leak deferred by v5.5.5's §D1 (and recorded
as TODO in the v5.5.5 SESSION_REPORT) — closed.

**Problem (v5.5.5):** `aw.ready.N` extracted the payload but
emitted no `coro.destroy` + `free(future)` because
`%aw.hdl.N` was loaded only on the `aw.drive.N` edge. SSA
dominance meant the handle wasn't visible from the fast-path
or scheduler-resume entries to `aw.ready.N`. Result: 56-byte
leak per inner await on 56/57/58/59 (4 leaks × 56 B in
58_async_file_io ≈ 112 B; 10 leaks × 56 B in 59_async_fanout
≈ 560 B).

**Fix (v5.5.7):** hoist `%aw.hdl.ptr.N` GEP + `%aw.hdl.N`
load into the entry BB **before** the fast-path readiness
branch. Now `%aw.hdl.N` dominates every entry to
`aw.ready.N` (fast-path direct, drive→check→ready, and
scheduler-resume→ready). `aw.ready.N` gains the cleanup
trio mirroring v5.5.6's BlockOn:

```
call void @llvm.coro.destroy(ptr %aw.hdl.N)
call void @free(ptr %aw.val.box.N)
call void @free(ptr %fut.name)
```

The inner coroutine has already initialised `future.handle`
by the time the outer reaches AwaitSuspend (initial-suspend
path of the inner's `coro.entry` stored `%coro.hdl` into
slot 1), so the entry-block load is well-defined. v4.102.0
foot-gun applies but the load happens *before* any
scheduler activity, so the slot-1 clobber from the inner's
final-suspend (which overwrites the handle with the result
box) is irrelevant — we still hold the original handle in
`%aw.hdl.N`.

**LOC:** +20 / −5 in the `await_suspend` branch of
`emit_mir_by_kind`.

### 7.3 — Full sanitizer matrix (5 Sh.4 goldens)

| Sanitizer | 55 | 56 | 57 | 58 | 59 |
|---|:---:|:---:|:---:|:---:|:---:|
| valgrind (errors / leaks) | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| ASan (errors)             | 0   | 0   | 0   | 0   | 0   |
| LSan (leaks)              | 0   | 0   | 0   | 0   | 0   |
| TSan (races)              | 0   | 0   | 0   | 0   | 0   |

`valgrind --leak-check=full` on 59_async_fanout:
**36 allocs / 36 frees / 0 bytes in use at exit.**

Compiler-side sweeps (mnc-stage1 compiling 66 goldens):
- valgrind: 60 CLEAN / 6 WARNINGS_ONLY / **0 ERRORS** vs
  baseline of 36 ERRORS — every previously-erroring test now
  clean.
- ASan: 60 CLEAN / 6 CRASH_NO_ASAN (the 6 stage1-FAIL
  goldens) / **0 ASAN_ERROR.**
- LSan: 45 CLEAN / 3 LEAK / 6 COMPILE_FAIL / 12 LINK_FAIL /
  **0 regressions** vs `docs/roadmap/v5/v5.4.2/baseline/
  asan-leak-baseline.tsv`.

### 7.4 — Ve.1 root-cause identified, fix deferred

`docs/roadmap/v5/v5.5.7/VE1_INVESTIGATION.md` — full report.
Summary: `parse_fn_body` writes 8 bytes 0-bytes-past a
256-byte heap block. Smallest crashing input is `lower.mn`
(3.6K LOC); `mir.mn` (1.0K LOC) does not crash. 154,355
valgrind errors across 42 contexts when run on `lower.mn`.

256 = 32 × 8 strongly implicates a `List<X>` default-capacity
buffer (32 entries of 8-byte pointers) whose realloc-on-push
path is broken or bypassed. Predates async work; fix
requires parser / runtime list-growth surgery — out of
v5.5.7 stabilization scope. Tracked as `docs/known_issues.md`
Ve.1; recommended micro-release v5.5.7.1.

---

## Verification

### Self-hosting

| Metric | v5.5.6 | v5.5.7 | Delta |
|---|---:|---:|---:|
| stage2.ll lines | 194,799 | 195,348 | +549 (+0.28%) |
| stage2.ll `define` count | 907 | 908 | +1 (`emit_drop_glue_destroy`) |
| stage2.ll `llvm-as` | OK | OK | — |

### Tests

- **Goldens harness:** 59/66 PASS (unchanged).
- **Non-bootstrap pytest:** see commit (run after
  `make build-rt` to bump the VERSION macro).
- **Bootstrap pytest:** 225 passed, 5 xfailed (unchanged).
- **`make lint`:** clean.

---

## Risk register — updated

| Risk | State | Note |
|---|---|---|
| R1 — Sanitizer real bug | NOT OBSERVED on goldens; CLOSED Rt.05 | Handle-hoist eliminated the only structural leak class. Compiler-side runs match baselines. |
| R2 — Destroy-path drop-glue false positive | NOT OBSERVED | `moved_locals` consulted; helper is a no-op for current goldens; conservative by design. |
| R3 — Ve.1 blocked by drop-glue rewrite | NO — different bug | Ve.1 is a parser/list buffer overflow, unrelated to drop-glue infrastructure. |
| R4 — Fixed-point still broken | YES (acceptable per PLAN §R4) | Investigation report shipped; fix deferred to v5.5.7.1. |

---

## What did NOT ship

- **Ve.1 fix.** Investigation only.
- **spawn / join builtins.** v5.5.8.
- **`60_async_multi_fanout` golden.** v5.5.8 (queue-pressure
  workload to exercise lazy-spawn beyond `prime=1`).
- **PARITY_GAPS.md update.** v5.5.9.

---

## Files changed

| File | Change |
|---|---|
| `VERSION` | 5.5.6 → 5.5.7 |
| `mapanare/self/emit_llvm.mn` | +93 / −19 (handle hoist + ready-block cleanup + destroy-path drop-glue helper + wire-up) |
| `mapanare/self/mnc_all.mn` | regenerated |
| `mapanare/self/mnc-stage1` | rebuilt |
| `runtime/native/libmapanare_rt.a` | rebuilt (VERSION macro bump) |
| `docs/roadmap/v5/v5.5.7/SESSION_REPORT.md` | new |
| `docs/roadmap/v5/v5.5.7/VE1_INVESTIGATION.md` | new |
| `docs/known_issues.md` | Rt.05 CLOSED + Ve.1 entry refreshed with root cause |
| `CLAUDE.md` | v5.5.7 entry prepended |

---

## Commit narrative

1. `73162e4` — v5.5.7: VERSION bump
2. (next) — v5.5.7: sanitizer + fixed-point hardening

---

## Handoff to v5.5.7.1 / v5.5.8 / v5.5.9

1. **Ve.1 fix (v5.5.7.1)** — reproduce with ASan-instrumented
   mnc-stage1 on `lower.mn`. Identify the specific 256-byte
   container in `parse_fn_body`. Audit `__mn_list_push` (or
   equivalent) for the realloc contract. Validate by
   re-running `verify_fixed_point.sh --keep`.
2. **spawn + join + multi-fanout golden (v5.5.8)** — add
   `60_async_multi_fanout` with N awaits ≫ `workers*8` to
   exercise the v5.1.4 lazy-spawn gate. This becomes the
   stronger threading proof v5.5.6's PLAN §Phase 4.1 wanted.
3. **PARITY_GAPS.md → Sh.4 Historical (v5.5.9)** — close the
   parity arc.
