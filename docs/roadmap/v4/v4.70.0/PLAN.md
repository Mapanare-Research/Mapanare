# Mapanare v4.70.0 — MIR Suspension Points + Coroutine Lowering Pt 1

> **Arc 8 release 4.** First real coroutine lowering. Emits the
> coro-split prelude intrinsics (`llvm.coro.id`, `llvm.coro.alloc`,
> `llvm.coro.begin`) for every `async fn`. Suspension/resume/destroy
> come in v4.72.0.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.69.0
**Delta review:** No (internal lowering — no user-visible syntax change)
**Full panel:** No (v4.71.0)
**Estimated work:** 2 sprints
**Theme:** `async fn` produces real LLVM coroutine IR. It doesn't yet suspend — but the prelude and epilogue are in place.

---

## Scope

At v4.70.0 an `async fn` compiles to IR that includes:

```llvm
define i64 @my_async_fn(i64 %a) presplitcoroutine {
  %id = call token @llvm.coro.id(i32 0, ptr null, ptr null, ptr null)
  %size = call i64 @llvm.coro.size.i64()
  %alloc = call i1 @llvm.coro.alloc(token %id)
  br i1 %alloc, label %dyn_alloc, label %coro_begin

dyn_alloc:
  %mem = call ptr @malloc(i64 %size)
  br label %coro_begin

coro_begin:
  %frame = phi ptr [ %mem, %dyn_alloc ], [ null, %0 ]
  %hdl = call ptr @llvm.coro.begin(token %id, ptr %frame)

  ; ... function body lowers here normally ...
  ; `await` points ARE NOT YET IMPLEMENTED — v4.72.0 adds them

  %result = ... ; the function's normal return value

  %unused = call i1 @llvm.coro.end(ptr %hdl, i1 false, token none)
  ret i64 %result
}
```

`llvm.coro.suspend` is NOT emitted yet. Awaits still produce the "under construction" lowering error from v4.68.0-v4.69.0. The v4.70.0 scope is the **prelude** only — the machinery that wraps the function as a coroutine, without yet adding suspension.

---

## Phase 1 — MIR instruction kinds

### Phase 1.1: New instruction kinds

- [ ] `mapanare/mir.py`:
  ```python
  class InstructionKind(Enum):
      ...
      CORO_ID = "coro_id"
      CORO_ALLOC = "coro_alloc"
      CORO_SIZE = "coro_size"
      CORO_BEGIN = "coro_begin"
      CORO_END = "coro_end"
      CORO_SUSPEND = "coro_suspend"  # v4.72.0
      CORO_SAVE = "coro_save"        # v4.72.0
      CORO_FREE = "coro_free"        # v4.72.0
      CORO_RESUME = "coro_resume"    # v4.72.0
      CORO_DESTROY = "coro_destroy"  # v4.72.0
  ```
- [ ] v4.70.0 uses `CORO_ID`, `CORO_ALLOC`, `CORO_SIZE`, `CORO_BEGIN`, `CORO_END`. The rest are stubbed for v4.72.0.

### Phase 1.2: Coroutine metadata on MIRFunction

- [ ] `MIRFunction.is_async: bool` — already set by the semantic pass (v4.69.0)
- [ ] `MIRFunction.coroutine_frame_type: Optional[MIRType]` — computed by v4.72.0 (the frame struct that holds captured state); stub as None for v4.70.0

---

## Phase 2 — Lowering prelude emission

- [ ] `mapanare/lower.py` `_lower_async_fn_def(node: AsyncFnDef) -> MIRFunction`:
  1. Lower as a regular fn first — build the MIR function body
  2. Insert the prelude at the top:
     - `CORO_ID` — produces a token
     - `CORO_SIZE` — produces the frame size
     - `CORO_ALLOC` — produces an i1 indicating whether malloc is needed
     - Conditional branch: if alloc needed, call `__mn_malloc`; else use stack
     - `CORO_BEGIN` — the coroutine handle
  3. Insert the epilogue at the bottom (before `return`):
     - `CORO_END` — marks completion
  4. Mark the function with the `presplitcoroutine` attribute (emitted in the emitter)

---

## Phase 3 — LLVM emitter coroutine intrinsic support

- [ ] `mapanare/emit_llvm_text.py`:
  - Declare the intrinsics at module top:
    ```llvm
    declare token @llvm.coro.id(i32, ptr, ptr, ptr)
    declare i64 @llvm.coro.size.i64()
    declare i1 @llvm.coro.alloc(token)
    declare ptr @llvm.coro.begin(token, ptr)
    declare i1 @llvm.coro.end(ptr, i1, token)
    ```
  - `_emit_coro_id` / `_emit_coro_alloc` / `_emit_coro_size` / `_emit_coro_begin` / `_emit_coro_end` — each corresponds to one MIR instruction kind
  - The function attribute `presplitcoroutine` is added to `define` lines for async functions

---

## Phase 4 — Pass pipeline placement

- [ ] `mapanare/emit_llvm_text.py` — when any `presplitcoroutine` function is present in the module, the emitted IR needs to be processed by the LLVM `coro-split` pass **before** inlining.
- [ ] The Mapanare pipeline currently invokes `opt` on emitted IR (or relies on `clang` to run the default pipeline). Update the invocation to ensure `coro-split` runs:
  ```
  opt -passes="coro-early,coro-split,coro-cleanup" stage1.ll -o stage1.bc
  ```
- [ ] The `coro-split` pass expects the `presplitcoroutine` attribute and the coro intrinsic skeleton to be correct. If either is missing, `coro-split` doesn't fire or crashes.
- [ ] `scripts/build_stage1.py` — update the link pipeline
- [ ] `Makefile` — update if it invokes `opt` directly

---

## Phase 5 — Runtime malloc integration

- [ ] The coroutine frame is heap-allocated via `malloc`. Mapanare's runtime has `__mn_malloc` — use it instead of raw `malloc` for consistency with the rest of the runtime.
- [ ] `CORO_ALLOC` MIR branch: `if alloc { call __mn_malloc(size) } else { null }`

---

## Phase 6 — Self-hosted mirror

- [ ] `mapanare/self/mir.mn` — add the coro instruction kinds
- [ ] `mapanare/self/lower.mn` — mirror `lower_async_fn_def`
- [ ] `mapanare/self/emit_llvm.mn` — mirror the coro intrinsic emission + `presplitcoroutine` attribute
- [ ] Fixed-point diff still 0 (mnc_all.mn still doesn't use async, so the new paths don't fire on it)

---

## Phase 7 — Verification

### Phase 7.1: IR structure test

- [ ] `tests/llvm/test_coroutine_prelude.py`:
  - `test_async_fn_emits_coro_id` — grep IR for `llvm.coro.id`
  - `test_async_fn_emits_coro_alloc` — grep
  - `test_async_fn_emits_coro_begin` — grep
  - `test_async_fn_has_presplitcoroutine_attr` — grep
  - `test_async_fn_emits_coro_end_before_return` — structural check
  - `test_non_async_fn_does_not_emit_coro_intrinsics` — regression

### Phase 7.2: `llvm-as` clean

- [ ] A compiled `async fn foo() -> Int { return 42 }` produces IR that `llvm-as` accepts without warnings or errors.
- [ ] `test_llvm_as_clean_on_async_fn` — asserts no `llvm-as` output

### Phase 7.3: `coro-split` pass runs

- [ ] After `opt -passes=coro-split`, the presplit function is split into `ramp` / `resume` / `destroy` / `cleanup` functions. Verify:
  - `test_coro_split_produces_four_functions` — parse post-opt IR

### Phase 7.4: Compile and link (don't run yet)

- [ ] `test_async_fn_compiles_to_object_file` — `.ll` → `opt` → `.bc` → `clang` → `.o`, no errors
- [ ] The `.o` file is NOT linked into a runnable binary yet — the scheduler integration is v4.73.0

---

## Phase 8 — Await still errors

- [ ] `await expr` inside an `async fn` still produces the "under construction" error. The suspension handling is v4.72.0.
- [ ] Update the error message: "await suspension arrives in v4.72.0; v4.70.0 emits the coro-prelude"

---

## Phase 9 — LOW sweep

2 items.

## Phase 10 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.70.0
- [ ] `CHANGELOG.md [4.70.0]` — coroutine prelude emission
- [ ] SESSION_REPORT with IR snippets for clarity

---

## Exit criteria (15 items)

| # | Check | Evidence |
|---|---|---|
| 1 | New MIR instruction kinds added | grep |
| 2 | `_lower_async_fn_def` emits prelude | unit test |
| 3 | `_lower_async_fn_def` emits epilogue | unit test |
| 4 | `presplitcoroutine` attribute on async fns | grep IR |
| 5 | `llvm.coro.id` declared + called | grep |
| 6 | `llvm.coro.alloc` + `llvm.coro.size.i64` called | grep |
| 7 | `llvm.coro.begin` called | grep |
| 8 | `llvm.coro.end` called before return | grep |
| 9 | `__mn_malloc` used for dynamic frame allocation | grep |
| 10 | `opt -passes=coro-split` runs without error | `test_coro_split_produces_four_functions` |
| 11 | Compiled async fn produces a linkable `.o` | `test_async_fn_compiles_to_object_file` |
| 12 | `await` still errors (message updated to v4.72.0 target) | manual check |
| 13 | Self-hosted mirror matches Python emitter | byte compare on a test fixture |
| 14 | Fixed-point diff still 0 | verify script |
| 15 | Standard closeout clean | CI |

---

## What v4.70.0 does NOT do

- **Emit `llvm.coro.suspend`** — v4.72.0
- **Emit `llvm.coro.save`** — v4.72.0
- **Emit `llvm.coro.free`** in cleanup — v4.72.0
- **Compile `await expr` past the error** — v4.72.0
- **Run an async program end-to-end** — v4.73.0 (scheduler integration)
- **Support `async` methods on impl blocks** — defer
- **Support generic async fns** — defer; monomorphization should work but test after v4.72.0 lands

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `coro-split` pass doesn't recognize our emission shape | medium | high | Test against Clang's coroutine output; if divergent, adjust emission until it matches |
| Pipeline ordering issue: `coro-split` runs after inlining | medium | high | Explicit `opt -passes=coro-split,...` order; test the `.bc` structure post-opt |
| `presplitcoroutine` attribute conflicts with other attrs | low | medium | LLVM permits it with most attrs; test |
| Frame size computation wrong | low | high | Let LLVM compute it via `llvm.coro.size.i64`; trust the intrinsic |

---

## Reference

- [`v4.67.0/DESIGN.md`](../v4.67.0/DESIGN.md) §4
- LLVM Coroutines §"Coroutine Switch-Resumed ABI" — https://llvm.org/docs/Coroutines.html

---

## After v4.70.0

v4.71.0 is the **arc 8 panel release**. Coroutine foundation is done at the prelude level. Suspension, scheduler, end-to-end come in arc 9.
