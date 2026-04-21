# Rattler — LLVM Lens (PRIMARY)

**Grade: 9/10** | **Verdict: PASS WITH NOTES**

## Assessment

The coroutine foundation is solid. DESIGN.md (v4.67.0) correctly identifies
the switched-resume ABI, correctly describes the pass pipeline, and the
v4.70.0 implementation follows the design faithfully.

The `presplitcoroutine` attribute is correctly placed on the `define` line.
The `coro.id` → `coro.alloc` → `coro.begin` sequence is correct. The initial
and final suspend points use the mandatory `switch i8 %susp` pattern. The
cleanup block calls `coro.free` + `free` in the right order.

## Specific findings

1. **PASS**: `presplitcoroutine` attribute — correctly placed, will trigger
   CoroSplit in the standard `-O1` pipeline.
2. **PASS**: Intrinsic declarations — all 12 present, correct signatures.
3. **NOTE**: The `coro.alloc` check is missing. The emitter always calls
   `malloc` unconditionally. The canonical pattern is `%need = call i1
   @llvm.coro.alloc(token %id); br i1 %need, label %alloc, label %begin`.
   Without this, HALO elision cannot skip the allocation. Low severity —
   every frame is heap-allocated regardless, which is the stated design
   decision for v4.x. But document this as a v5.x optimization target.
4. **NOTE**: The `ret.val.slot` GEP name is not unique across multiple return
   paths. If an async fn has two return statements, the second `ret.val.slot`
   will shadow the first. Use `self._f()` to generate unique names.
5. **PASS**: Future `{i8, ptr}` layout matches DESIGN.md §3.3 exactly.

## Sign-off

Foundation is sound. Arc 9 can proceed with suspension lowering.
