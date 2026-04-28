# v5.5.4 — Sh.4 Option B Phase 1: real LLVM coroutines

> **First real-coroutine release. Ships `presplitcoroutine` +
> full `@llvm.coro.id/begin/save/suspend/end` pipeline on
> async fns. `opt -O1` runs CoroSplit and produces `@foo.resume`
> + `@foo.destroy` split functions. All 5 Sh.4 goldens execute
> correctly through the real LLVM coroutine ABI.**
>
> Bigger than the DESIGN.md §5 forecast: the plan said v5.5.4 =
> emitter wrapping only, v5.5.5 = AwaitSuspend, v5.5.6 = BlockOn.
> Reality: wrapping async fns in coroutines meant they return
> `ptr` (not `i64`), so v5.5.2's Option A copy-based
> BlockOn/AwaitSuspend produced type-mismatched IR. Fixing one
> required fixing all three. Shipped together.

**Status:** SHIPPED
**Breaking:** No (language surface unchanged)
**Goldens:** 59/66 unchanged; all 5 Sh.4 goldens now execute
via real coroutines

---

## What shipped

### Phase 0 — empirical answers to DESIGN.md §8 questions

Before writing code, ran two experiments:

**Q2 — Does `llc -O2` alone run coro passes?** Built a minimal
presplit-coroutine IR and tried `llc -O2` directly. Result:
**crashes** with "LLVM ERROR: Do not know how to promote this
operator's operand!" — coroutine intrinsics aren't lowered.
Must pipe through `opt -O1` first. Post-`opt`, LLVM's
`CoroSplit` pass produces `@foo` (ramp), `@foo.resume`,
`@foo.destroy` split functions. The goldens harness / golden
test scripts must invoke `opt -O1 in.ll | llc -O2` for async
IR.

**Q3 — Is Ve.1 (stage3 segfault) still regressed?** Ran
`scripts/verify_fixed_point.sh`. Stage2.ll builds + llvm-as
clean, but stage3.ll = 0 lines (mnc-stage2 segfaults during
lex of mnc_all.mn). Pre-existing v5.4.4 condition, not
caused by async work. v5.5.4 ships stage2.ll llvm-as clean
as the available bar; true fixed-point blocked on Ve.1 fix.

### Phase 1 — inliner gate (+9 lines)

`mir_opt.mn::should_inline` — new early return when
`fn_is_async(callee)`. Inlining an async fn into a non-
`presplitcoroutine` caller would splice coroutine intrinsics
into a non-coroutine function; LLVM's CoroSplit wouldn't run
and the IR would be malformed. Safe to reject categorically
because async fns are called via `BlockOn` or `AwaitSuspend`
(which handle the future extraction), never invoked as a plain
call whose result is used directly.

### Phase 2 — emit_llvm.mn structural rewrite (+140 lines)

**Detection (`emit_mir_function` + `emit_mir_module`):** Added
`let is_async: Bool = fn_is_async(f)` gate at three points:
- `emit_mir_function` — branches header emission, skips sret
- `emit_mir_function` FnEntry registration — ret_type="ptr"
- `emit_mir_module` forward-declare loop — ret_type="ptr"

Both registration sites need the update because `find_function`
searches backwards and the per-function push overrides the
forward-declare entry.

**Header (`emit_mir_function`):** For async:
- `abi_ret = "ptr"` (regardless of declared T)
- `coro_attr = " presplitcoroutine"` appended to attrs
- `use_sret = false` (async fns never use sret)
- `current_ret_type = "ASYNC_PTR:" + inner_ty` sentinel so
  `emit_mir_return` can branch to the ret-rewrite path while
  still knowing the inner T for box allocation

**Prologue (`emit_mir_function`):** After the `define ... {`
line, emit the `coro.entry:` synthetic block:
```
coro.entry:
  %coro.id   = call token @llvm.coro.id(i32 0, ptr null, ptr null, ptr null)
  %coro.size = call i64 @llvm.coro.size.i64()
  %coro.mem  = call ptr @malloc(i64 %coro.size)
  %coro.hdl  = call ptr @llvm.coro.begin(token %coro.id, ptr %coro.mem)
  %future    = call ptr @malloc(i64 16)
  store i8 0, ptr %future                      ; Pending state
  %future.hdl.slot = gep {i8,ptr}, ptr %future, i32 0, i32 1
  store ptr %coro.hdl, ptr %future.hdl.slot    ; payload = handle
  %coro.init.save = call token @llvm.coro.save(ptr %coro.hdl)
  %coro.init.susp = call i8 @llvm.coro.suspend(token %coro.init.save, i1 false)
  switch i8 %coro.init.susp, label %coro.ret [
    i8 0, label %pre_entry
    i8 1, label %coro.cleanup
  ]
pre_entry:
  br label %<f.blocks[0].label>
```

`pre_entry:` is a trampoline — the MIR's actual entry block
already contains param-stores and allocas from the lowerer, so
no need to duplicate them here. Mirrors
`emit_llvm_text.py:2572–2605`.

**ret-rewrite (`emit_mir_return`):** When
`current_ret_type.starts_with("ASYNC_PTR:")`:
```
  %ret.box.N  = call ptr @malloc(i64 8)
  store <inner_ty> <val>, ptr %ret.box.N
  store i8 1, ptr %future                      ; Ready state
  %ret.val.slot.N = gep {i8,ptr}, ptr %future, i32 0, i32 1
  store ptr %ret.box.N, ptr %ret.val.slot.N
  br label %coro.final
```

Mirrors `emit_llvm_text.py:2613–2628`. Drop-glue still fires
before the rewrite (preserves v5.4.0–v5.4.4 behavior). For
`ret void`: just `store i8 1, ptr %future` + `br %coro.final`.

**Epilogue (`emit_mir_function`):** After all MIR blocks, emit
the three trailing blocks:
```
coro.final:
  %coro.final.save = call token @llvm.coro.save(ptr %coro.hdl)
  %coro.final.susp = call i8 @llvm.coro.suspend(token %coro.final.save, i1 true)
  switch i8 %coro.final.susp, label %coro.ret [
    i8 0, label %coro.ret
    i8 1, label %coro.cleanup
  ]
coro.cleanup:
  %coro.mem.free = call ptr @llvm.coro.free(token %coro.id, ptr %coro.hdl)
  call void @free(ptr %coro.mem.free)
  br label %coro.ret
coro.ret:
  call i1 @llvm.coro.end(ptr %coro.hdl, i1 false, token none)
  ret ptr %future
```

Mirrors `emit_llvm_text.py:2669–2685`.

### Phase 2 bonus — AwaitSuspend + BlockOn real emission (+50 lines)

**Why bundled with Phase 2 (deviation from DESIGN.md §5):** once
async fns return `ptr` (not declared T), v5.5.2's Option A
copy-based BlockOn/AwaitSuspend emission produced type-
mismatched IR (`%dest = add i64 0, %ptr`). Fixing one required
fixing all three.

**BlockOn emission** (synchronous drive, no scheduler yet):
```
; BlockOn(%dest, %future)
%bo.hdl.ptr.N = gep {i8,ptr}, ptr %future, i32 0, i32 1
%bo.hdl.N     = load ptr, ptr %bo.hdl.ptr.N    ; handle BEFORE resume
call void @llvm.coro.resume(ptr %bo.hdl.N)     ; drive to final suspend
%bo.val.ptr.N = gep {i8,ptr}, ptr %future, i32 0, i32 1
%bo.val.box.N = load ptr, ptr %bo.val.ptr.N    ; payload = box
%bo.val.N     = load i64, ptr %bo.val.box.N    ; extract T
%dest         = add i64 0, %bo.val.N
call void @llvm.coro.destroy(ptr %bo.hdl.N)    ; reuse pre-resume handle
call void @free(ptr %bo.val.box.N)
call void @free(ptr %future)
```

**AwaitSuspend emission** (also synchronous — no outer-suspend
yet; v5.5.6 adds scheduler-driven path). Same pattern as
BlockOn but with `%aw.*` prefixes.

**Critical v4.102.0 foot-gun respected:** after
`coro.resume` completes, the future's payload slot is
overwritten from `%coro.hdl` (Pending) to `%box` (Ready). The
handle loaded BEFORE resume is the real handle for
`coro.destroy`. Reloading slot 1 after resume would hand
destroy an 8-byte int and segfault. Documented inline.

### mir_opt.mn — replace_uses_in_instr + clone_instr_for_inline

Already had cases for `await_suspend` / `block_on` from v5.5.1.
Unchanged.

---

## Verification

### End-to-end execution

All 5 Sh.4 goldens compile via mnc-stage1, pass `llvm-as`, pass
`opt -O1` (which triggers CoroSplit/CoroElide/CoroCleanup),
compile via `llc -O2`, link against `libmapanare_rt.a`, and
execute:

| Golden | Expected | Got | Status |
|---|---|---|:---:|
| `55_async_basic` | `42` | `42` | ✅ |
| `56_async_await` | `43` | `43` | ✅ |
| `57_real_await` | `110` | `110` | ✅ |
| `58_async_file_io` | `done` | `done` | ✅ |
| `59_async_fanout` | `220` | `220` | ✅ |

### Post-opt coroutine split verification

Inspecting `/tmp/55_async_basic_v554_opt.ll`:

```
define noundef ptr @compute() local_unnamed_addr #0 { ... }
define noundef i32 @main() local_unnamed_addr #0 { ... }
define internal fastcc void @compute.resume(ptr ... %coro.hdl) #3 { ... }
define internal fastcc void @compute.destroy(ptr ... %coro.hdl) #4 { ... }
```

LLVM's CoroSplit successfully identified our IR as a valid
pre-split coroutine and produced the standard ramp / resume /
destroy triple. Proves the IR shape matches LLVM's expected
convention.

### Self-hosting

`./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn` →
**194,052 lines** / **906 defines** stage2.ll, `llvm-as` clean.
+1.3% line count vs v5.5.2's 192,790 (async fn count in
mnc_all.mn is zero, so the delta is only from the new
branches in emit_mir_return + emit_mir_function).

### Golden harness

`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
→ **59/66 PASS, 7 FAIL**. Unchanged from v5.5.3.

7 FAIL unchanged: Sh.6 × 5 tensor, Sh.7 × 1 closure, B × 1
bootstrap-fail.

### Valgrind

`valgrind --error-exitcode=1 /tmp/55_async_basic_v554.bin`
→ output `42`, exit 0. No leaks, no errors.

### Ve.1 status

Unchanged. Stage3.ll still 0 lines (mnc-stage2 segfaults
during lex). Pre-existing v5.4.4 regression, not caused by
async work. Tracked for future fix.

---

## What did NOT ship (deferred to v5.5.5+)

- **Scheduler-driven block_on.** The runtime scheduler
  (`__mn_coro_scheduler_*`) is declared but never called by
  emitted code. v5.5.4's BlockOn does synchronous
  `llvm.coro.resume` inline — works for trivial async goldens
  but provides no concurrency. v5.5.6 adds the scheduler
  integration.
- **Scheduler-driven await.** Same story — AwaitSuspend
  drives inner coroutines synchronously rather than saving +
  suspending the outer. v5.5.5 adds real suspension.
- **main() scheduler lifecycle.** v5.5.6 adds
  `__mn_coro_scheduler_init(0)` at main entry and
  `__mn_coro_scheduler_destroy()` at main exits.
- **spawn() + join() builtins.** v5.5.8.
- **PARITY_GAPS.md Sh.4 → Historical.** Deferred to v5.5.9
  when the full feature matrix is proved out.

---

## Open questions — status

Updating DESIGN.md §8:

| Q | Question | v5.5.4 answer |
|---|---|---|
| Q1 | Unconditional vs. conditional coro.alloc? | **Unconditional** — matches Python. HALO won't fire anyway (handle escapes to scheduler in v5.5.6+). |
| Q2 | llc alone vs. opt \| llc? | **opt -O1 required.** llc alone crashes on coro intrinsics. |
| Q3 | Does Ve.1 affect async? | **No.** Ve.1 is a pre-existing stage3 issue in drop-glue, orthogonal to async. stage2.ll is llvm-as clean including async. |
| Q4 | Split v5.5.4 further? | **No, and actually bundled MORE** (AwaitSuspend + BlockOn pulled in due to type-mismatch). Phase ordering in DESIGN.md was wrong. v5.5.5's scope is "scheduler-driven" versions of what v5.5.4 ships. |
| Q5 | New real-I/O golden at v5.5.8? | Still pending. |

---

## Risk register status

From DESIGN.md §6:

| ID | Risk | v5.5.4 outcome |
|---|---|---|
| R1 | Drop-glue × coroutine cleanup (HIGH) | Mitigated. Drop-glue fires in `emit_mir_return` BEFORE the ret-rewrite, so locals are freed on the ready-path. Cleanup-path drop-glue (destroy-before-complete) not exercised by goldens; defer to v5.5.7 hardening. |
| R2 | Inliner × monomorphization (MEDIUM) | N/A. The 5 Sh.4 goldens have no generic async fns. Safe for now. |
| R3 | Fixed-point shift (MEDIUM) | Acceptable. stage2.ll +1.3%, llvm-as clean. Ve.1 still blocks stage3 independently. |
| R4 | sret ABI collision (LOW) | Avoided. `use_sret = ... && !is_async`. |
| R5 | Entry-block buffering (MEDIUM) | Handled. Prologue/epilogue written directly to s.lines, bypassing entry_block_body buffer. User body still buffered normally. |
| R6 | Stage1 binary size (LOW) | +100KB (~2%). Negligible. |
| R7 | v4.102.0 handle-reload foot-gun (MEDIUM) | Respected — handle loaded once pre-resume, reused for coro.destroy. Documented inline. |

---

## Commits

- `VERSION`: 5.5.3 → 5.5.4
- `mapanare/self/mir_opt.mn`: +9 lines (inliner gate)
- `mapanare/self/emit_llvm.mn`: +~190 lines
  - emit_mir_function: is_async detection, prologue/epilogue emission, FnEntry reg update
  - emit_mir_return: ASYNC_PTR: prefix branch (ret rewrite)
  - emit_mir_by_kind: real BlockOn + AwaitSuspend
  - emit_mir_module: forward-declare async fn ret="ptr"
- `mapanare/self/mnc_all.mn`: regenerated
- `mapanare/self/main.ll`: regenerated
- `mapanare/self/mnc-stage1`: rebuilt
- `docs/roadmap/v5/v5.5.4/SESSION_REPORT.md`: this file

Runtime (`runtime/native/mapanare_runtime.c`) unchanged.
C runtime scheduler API still unused by emitted output —
v5.5.6 will wire it up.

---

## What's next

Per DESIGN.md §5, with Phase 2's scope expansion:

- **v5.5.5** — **Scheduler-driven AwaitSuspend.** Replace
  synchronous `coro.resume` with `__mn_coro_register_wait` +
  outer-coroutine `coro.save`/`coro.suspend`/switch pattern.
  Enables true concurrency between async fns.
- **v5.5.6** — **Scheduler-driven BlockOn + main lifecycle.**
  Replace synchronous drive with
  `__mn_coro_scheduler_register` + `__mn_coro_scheduler_run`.
  Inject `__mn_coro_scheduler_init(0)` at main entry.
- **v5.5.7** — Sanitizer + fixed-point hardening.
- **v5.5.8** — spawn + join + `60_async_multi_fanout.mn`.
- **v5.5.9** — PARITY_GAPS.md Sh.4 → Historical.
