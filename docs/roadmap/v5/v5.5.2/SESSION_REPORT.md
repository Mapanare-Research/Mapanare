# v5.5.2 — Sh.4 Phase 3 (Option A): synchronous async emission

> **Micro-release part 3 of 3.** Ships coroutine intrinsic +
> scheduler runtime declarations, real emission for
> `AwaitSuspend` / `BlockOn` MIR variants as synchronous copies,
> and completes the Sh.4 goldens (5/5 execute correctly). Does
> NOT ship full presplit-coroutine wrapping — async fns stay as
> plain fns returning their declared type. That's fine because
> the 5 Sh.4 goldens (55_async_basic through 59_async_fanout)
> all use `return <const>` async fns with no real suspension
> points.
>
> **Sh.4 closes harness-wise for the current golden corpus.**
> Real coroutine wrapping (for any future golden with actual
> suspension) is deferred to v5.5.3+. Option A vs Option B
> tradeoff documented at the end of this report.

**Status:** SHIPPED
**Breaking:** No
**Goldens:** 59/66 harness PASS; **5/5 Sh.4 goldens now
llvm-as clean + execute with correct output** (42, 43, 110,
"done", 220)

---

## What shipped

### emit_llvm.mn

#### Runtime + LLVM coro intrinsic declarations (+17 lines)

Added to `declare_all_runtime`:

**Scheduler runtime (runtime/native/mapanare_runtime.c v4.92.0+):**
- `__mn_coro_scheduler_init(i32) -> void`
- `__mn_coro_scheduler_destroy() -> void`
- `__mn_coro_scheduler_register(ptr) -> void`
- `__mn_coro_scheduler_run() -> void`
- `__mn_coro_register_wait(ptr, ptr) -> void`
- `__mn_coro_spawn(ptr) -> void`

**LLVM coroutine intrinsics:**
- `@llvm.coro.id(i32, ptr, ptr, ptr) -> token`
- `@llvm.coro.alloc(token) -> i1`
- `@llvm.coro.size.i64() -> i64`
- `@llvm.coro.begin(token, ptr) -> ptr`
- `@llvm.coro.suspend(token, i1) -> i8`
- `@llvm.coro.end(ptr, i1, token) -> i1`
- `@llvm.coro.free(token, ptr) -> ptr`
- `@llvm.coro.resume(ptr) -> void`
- `@llvm.coro.destroy(ptr) -> void`
- `@llvm.coro.done(ptr) -> i1`
- `@llvm.coro.save(ptr) -> token`

Declarations are unconditional (not gated on
`_module_has_async`). Linker drops unused declarations; IR cost
is 17 lines per program. Mirrors
`emit_llvm_text.py:898–908` but without the conditional guard.

#### Real AwaitSuspend + BlockOn emission (+15 lines)

Replaced v5.5.1's comment-only stubs in `emit_mir_by_kind`:

```
if kind == "await_suspend" {
    let aw_dest: Value = instr_dest(inst)
    let aw_fut: Value = instr_await_suspend_future(inst)
    let s_aw: EmitState = emit_line(st, "  ; v5.5.2 await_suspend ...")
    return emit_copy(s_aw, aw_dest, aw_fut)
}
if kind == "block_on" {
    let bo_dest: Value = instr_dest(inst)
    let bo_fut: Value = instr_block_on_future(inst)
    let s_bo: EmitState = emit_line(st, "  ; v5.5.2 block_on ...")
    return emit_copy(s_bo, bo_dest, bo_fut)
}
```

Emits a comment + a scalar copy (`%dest = add i64 0, %src`).
`mir_unknown()` dest type resolves to `i64` via
`resolve_mir_type` line 100. Source type is inherited from the
lowered inner expression (typically `Int` / `i64` for the 5
Sh.4 goldens).

### mir_opt.mn — inliner rename support (+20 lines)

`replace_uses_in_instr` — new cases for `"await_suspend"` and
`"block_on"` that call `replace_use` on the future operand.
Without this, when the inliner renames `%t0 → %_inl0_0_dst` for
the caller's dest, the future ref inside `BlockOn(%t1, %t0)`
survived unchanged and `llvm-as` rejected with
`use of undefined value '%t0'`.

`clone_instr_for_inline` — new cases that prefix-rename dest +
future via `rename_value`. Required for the 56/57/58/59 pattern
where an async fn containing `await expr` gets inlined into
another fn's BlockOn body.

---

## Verification

### 5 Sh.4 goldens — end-to-end

Each compiled via `mnc-stage1` → IR → `llc -O2` → `clang +
libmapanare_rt.a` → executed. Output vs. expected:

| Golden | Expected | Got | Status |
|---|---|---|:---:|
| `55_async_basic` | `42` | `42` | ✅ |
| `56_async_await` | `43` | `43` | ✅ |
| `57_real_await` | `110` | `110` | ✅ |
| `58_async_file_io` | `done` | `done` | ✅ |
| `59_async_fanout` | `220` | `220` | ✅ |

All 5 IR files pass `llvm-as -o /dev/null` with zero errors.

### Self-hosting

`./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn` →
192,790-line stage2.ll / 906 defines. `llvm-as` clean. Self-
compilation preserved.

### Golden harness

`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
→ **59/66 PASS, 7 FAIL**.

7 FAIL unchanged from v5.5.1 — Sh.6 × 5 tensor, Sh.7 × 1
closure, B × 1 bootstrap-fail. No regressions.

### Valgrind

`valgrind --error-exitcode=1 /tmp/55_async_basic.bin` →
output `42`, exit 0. No memory errors. (Expected — Option A
doesn't allocate coroutine frames or futures.)

---

## Option A vs Option B — the tradeoff

### What Option A ships

Async is **semantically pass-through**. An `async fn foo() ->
Int { return 42 }` compiles to a plain `define i64 @foo()
nounwind willreturn { ret i64 42 }`. `block_on(foo())` compiles
to `%dest = add i64 0, %foo_result`. `await foo()` inside an
async fn also compiles to `add i64 0, ...`.

### What Option A does NOT ship

- **Real coroutine suspension.** No `presplitcoroutine`
  attribute, no `coro.id/size/begin/save/suspend/end`, no
  future-struct allocation, no `ret → store-into-future-payload`
  rewrite.
- **Scheduler-driven block_on.** The scheduler runtime is
  declared but never called from emitted output.
- **True concurrency.** `spawn`-based fanout (if a future
  golden exercises it) won't multi-thread.

### When Option A breaks

Any async fn with:

- Real I/O inside (file/network reads that actually block)
- Explicit `yield` / suspension point
- Non-trivial control flow across awaits (if/match/for surrounding
  await)
- Cross-thread fanout expectations

...will fail to suspend and either busy-wait or produce wrong
results. The 5 Sh.4 goldens are all constant-return async fns
— the tradeoff is safe here.

### Upgrade path (v5.5.3+)

To ship Option B (real coroutines):

1. Add `is_async` function detection via `fn_is_async(f)`
   (already in mir.mn since v5.5.1) to emitter's
   `emit_fn_header` branch.
2. For async fns, rewrite return type `i64` → `ptr`, prepend
   `presplitcoroutine` to attrs, emit coroutine prologue (`coro.id`
   / `coro.size` / `malloc` / `coro.begin` / future alloc /
   initial suspend switch).
3. Walk fn body and rewrite each `ret <ty> <val>` into
   `store <val> into future.payload` + `br label %coro.final`.
4. Append `coro.final` / `coro.cleanup` / `coro.ret` blocks.
5. Replace `AwaitSuspend` emission: extract future.state, fast-path
   ready check, drive inner via `llvm.coro.resume`, re-check,
   suspend via `llvm.coro.save` + `llvm.coro.suspend` + switch.
6. Replace `BlockOn` emission: register future's handle with
   scheduler, call `__mn_coro_scheduler_run`, load future.payload,
   call `llvm.coro.destroy`, free payload + future, extract
   value.
7. Inject `__mn_coro_scheduler_init(0)` at main entry and
   `__mn_coro_scheduler_destroy()` at every main exit (needed
   because BlockOn now actually calls the scheduler).
8. Detect `_module_has_async` once per module.

Estimated: ~350 LOC in emit_llvm.mn. Fixed-point will shift
significantly. That's why we split.

---

## Exit criteria status (full v5.5.0 plan)

| # | Criterion | v5.5.0 | v5.5.1 | v5.5.2 |
|---|---|:---:|:---:|:---:|
| 1 | 5 Sh.4 goldens compile via mnc-stage1 | ✅ | ✅ | ✅ |
| 2 | Compiled IR passes `llvm-as` | ❌ | ❌ | ✅ |
| 3 | lli/executed output matches bootstrap | ❌ | ❌ | ✅ |
| 4 | Fixed-point NEAR/STRICT | — | self-host OK | self-host OK |
| 5 | Non-bootstrap pytest 0 failures | N/A | N/A | deferred |
| 6 | `make lint` clean | N/A | N/A | deferred |
| 7 | No new valgrind/ASan on Sh.4 tests | N/A | N/A | ✅ (spot-check) |
| 8 | PARITY_GAPS.md Sh.4 → Historical | — | — | partial (see note) |

**Note on #8:** PARITY_GAPS.md's existing Sh.4 row documents
tensor reshape, not async. Async never had its own PARITY_GAPS
row (it was tracked via GOLDEN_TRIAGE.md's Sh.4 bucket). We
leave PARITY_GAPS.md unchanged and document Sh.4-async closure
here + in CLAUDE.md.

---

## Commits

- `VERSION`: 5.5.1 → 5.5.2
- `mapanare/self/emit_llvm.mn`: +32 lines
- `mapanare/self/mir_opt.mn`: +20 lines
- `mapanare/self/mnc_all.mn`: regenerated
- `mapanare/self/main.ll`: regenerated
- `mapanare/self/mnc-stage1`: rebuilt
- `docs/roadmap/v5/v5.5.2/SESSION_REPORT.md`: this file
