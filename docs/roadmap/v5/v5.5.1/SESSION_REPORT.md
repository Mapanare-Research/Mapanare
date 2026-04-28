# v5.5.1 — Sh.4 Phase 2: MIR variants + lowerer

> **Micro-release part 2 of 3.** Adds `BlockOn` + `AwaitSuspend`
> MIR variants, lowerer emission for `block_on(call)` and
> `await expr`, and a `fn_is_async(MIRFunction)` helper that
> reads from the existing `decorators` list. Emitter stubs the
> new kinds so there's no stderr spam; real intrinsic emission
> is v5.5.2's job.

**Status:** SHIPPED
**Breaking:** No
**Goldens:** 59/66 (unchanged — still harness-PASS; execution
correctness pending v5.5.2)

---

## What shipped

### mir.mn (+28 lines)

- `Instruction` enum — new variants:
  - `AwaitSuspend(Value, Value)` — `(dest, future)`
  - `BlockOn(Value, Value)` — `(dest, future)`
- `instr_kind` — `"await_suspend"` + `"block_on"` branches
- `instr_dest` — new variants included
- New accessors:
  - `instr_await_suspend_future(i) -> Value`
  - `instr_block_on_future(i) -> Value`
- New helper `fn_is_async(f: MIRFunction) -> Bool` — scans the
  existing `decorators: List<String>` field for `"async"`. The
  parser already stashes `async fn` as a `"async"` decorator per
  `parser.mn:797–798`, so nothing upstream changes. The emitter
  (v5.5.2) calls this once per function to decide whether to
  wrap the body in a coroutine frame.

**Design decision — helper vs. field.** Adding `is_async: Bool`
to `MIRFunction` would have broken the self-hosted compiler's
struct registry and required a coordinated field bump + new_mir_
function signature change across 2 call sites. The helper is
O(1) in practice (decorator list is ≤2 entries) and doesn't
touch the struct layout. No fixed-point risk.

### lower.mn (+16 lines)

- `lower_expr` — `"await"` case now calls `lower_expr` on the
  inner (to get the future SSA), allocates a fresh dest, and
  emits `Instruction::AwaitSuspend(dest, future)` instead of
  inlining. Previously this branch was a pass-through that
  silently erased the coroutine suspension intent.
- `lower_call_by_name` — new `"block_on"` branch before
  monomorphization. Allocates a fresh dest and emits
  `Instruction::BlockOn(dest, future)` where `future = args[0]`.
  Mirrors `mapanare/lower.py::_lower_call` lines 1836–1845.

### emit_llvm.mn (+13 lines)

- `emit_mir_by_kind` — stub handlers for `"await_suspend"` and
  `"block_on"` that emit a comment line. Prevents the
  `ERROR: unknown MIR instruction kind` stderr spam (at line
  1043) while keeping the IR text stable and inspectable. The
  emitted IR references undefined SSA names for the dest (since
  we never store into them), so `llvm-as` still rejects. That's
  acceptable at v5.5.1 because the goldens harness checks
  function-name parity, not IR validity.

### Verification

- `python3 scripts/build_stage1.py` succeeds.
- `./mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn` → 191,802
  lines, 908 defines, 0 stderr. Self-hosting preserved.
- 5 Sh.4 goldens emit `; v5.5.1 block_on stub` + `; v5.5.1
  await_suspend stub` comments (not naive `@block_on` calls).
  The undeclared `@block_on(...)` call that v5.5.0 emitted is
  gone — the lowerer now short-circuits before the generic Call
  path.
- Goldens harness: 59/66 PASS (unchanged — v5.5.0 already bumped
  the harness number; v5.5.2 will make the IR actually valid).
- 7 FAIL (unchanged): Sh.6 × 5 tensor, Sh.7 × 1 closure, B × 1
  bootstrap-fail.

---

## Exit criteria status

| # | Criterion | v5.5.0 | v5.5.1 | v5.5.2 |
|---|---|:---:|:---:|:---:|
| 1 | 5 Sh.4 goldens compile via mnc-stage1 | ✅ | ✅ | — |
| 2 | Compiled IR passes `llvm-as` | ❌ | ❌ (stub SSA) | ✅ |
| 3 | lli-executed output matches bootstrap | ❌ | ❌ | ✅ |
| 4 | Fixed-point NEAR/STRICT | — | self-host OK | full check |
| 5 | Non-bootstrap pytest 0 failures | N/A | N/A | full run |
| 6 | `make lint` clean | N/A | N/A | full run |
| 7 | No new valgrind/ASan on Sh.4 tests | N/A | N/A | ✅ |
| 8 | PARITY_GAPS.md Sh.4 → Historical | — | — | ✅ |

---

## Risk assessment

**Medium → low.** Changes are additive:

- New enum variants + new accessors can't break existing code.
- Lowerer branches are gated on specific names (`"block_on"`)
  and expression kinds (`"await"`). Non-async code takes the
  original paths byte-identically.
- Emitter stubs are dead code for non-async input.

The only cross-cutting surface is the `Instruction` enum tag
layout. The self-hosted compiler uses string-tagged dispatch via
`instr_kind()` (not match-on-enum), per the `emit_mir_by_kind`
comment at line 957. That means the enum tag order is internal
to each compiler-binary and doesn't have to match across stages
— I can add variants at the end without breaking stage2/stage3
compatibility.

---

## Migration note for v5.5.2

Next release ships the emitter:

1. `emit_llvm.mn::declare_all_runtime` — add the 10 coro
   intrinsic declarations (`@llvm.coro.id/size/begin/save/
   suspend/end/free/resume/destroy/done`).
2. `emit_llvm.mn::emit_fn_header` — for async fns (check via
   `fn_is_async(f)`), emit the `presplitcoroutine` attribute +
   coroutine prologue (`coro.id` / `coro.size` / `malloc` /
   `coro.begin` / future struct / initial suspend).
3. `emit_llvm.mn::emit_mir_return` — for async fns, rewrite
   `ret <ty> <val>` into `store val into future.payload` +
   `br label %coro.final`.
4. Function epilogue — `coro.final` / `coro.cleanup` / `coro.ret`
   blocks always emitted for async fns.
5. Replace stub `"await_suspend"` handler with real
   save/suspend/switch/ready emission (mirror
   `emit_llvm_text.py::_do_await_suspend` lines 5291–5414).
6. Replace stub `"block_on"` handler with scheduler_register +
   scheduler_run + destroy + extract (mirror `_do_block_on`
   lines 5416–5484).
7. `emit_llvm.mn::emit_main` — when `_module_has_async`,
   inject `__mn_coro_scheduler_init` at main entry and
   `__mn_coro_scheduler_destroy` at all main exits.
8. Sanitizer sweep on the 5 Sh.4 goldens.
9. Move Sh.4 to Historical in `PARITY_GAPS.md`.

Expected LOC: ~350 in emit_llvm.mn. High risk — emitter
changes interact with v5.4.0–v5.4.4's drop-glue infrastructure
and every emit_llvm.mn change shifts fixed-point.

---

## Commits

- `VERSION`: 5.5.0 → 5.5.1
- `mapanare/self/mir.mn`: +28 lines
- `mapanare/self/lower.mn`: +16 lines (net; `"await"` branch
  reworked from 2 lines to 8)
- `mapanare/self/emit_llvm.mn`: +13 lines (stubs)
- `mapanare/self/mnc_all.mn`: regenerated via `concat_self.sh`
- `mapanare/self/main.ll`: regenerated
- `mapanare/self/mnc-stage1`: rebuilt
- `docs/roadmap/v5/v5.5.1/SESSION_REPORT.md`: this file
