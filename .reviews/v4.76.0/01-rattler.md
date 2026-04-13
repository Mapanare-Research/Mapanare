# Rattler — LLVM Lens (PRIMARY)

**Grade: 9/10** | **Verdict: PASS**

## Assessment

This is the feature I designed at v4.67.0 and graded at v4.71.0. The execution
matches the design. Every intrinsic is used correctly. The inline-resume model
is a pragmatic deviation from DESIGN.md §4.6.2 (which specified real suspension) —
but it's the right call for v4.x single-threaded cooperative async.

The `presplitcoroutine` attribute is correctly placed. `coro.id` → `coro.begin`
→ suspend → body → `coro.end` → cleanup → `coro.free` follows the canonical
switched-resume ABI. The `block_on` resume loop correctly uses `coro.resume` +
`coro.done` + `coro.destroy`.

## Specific findings

1. **PASS**: 12 intrinsic declarations, correct signatures, conditionally emitted.
2. **PASS**: ret.val.slot uniqueness fixed (my v4.71.0 item #2).
3. **PASS**: `57_real_await.mn` has 3 await points with unique labels.
4. **NOTE**: The inline-resume model means `coro.suspend` at await points was
   removed in v4.73.0. The only suspends are initial + final. This is correct
   for the inline model but means LLVM's `coro-split` produces minimal
   resume/destroy functions. If v5.x adds real suspension, the await-point
   `coro.suspend` calls need to come back.
5. **PASS**: A1 closure is genuine. Real intrinsics, not identity lowering.

## Sign-off

The 10-release coroutine arc is the most ambitious feature delivery in
Mapanare's history. It worked. Foundation sound, execution solid.
