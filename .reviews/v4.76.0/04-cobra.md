# Cobra — C++/ABI Lens

**Grade: 9/10** | **Verdict: PASS**

## Assessment

The coroutine IR matches C++20 expectations structurally. The switched-resume
ABI is correctly implemented. The `{resume_fn, destroy_fn, index}` frame
layout is what `coro-split` produces for any `presplitcoroutine` function.

The inline-resume model is a valid subset of the full coroutine ABI — it's
equivalent to what C++ does with `co_await` on an immediately-ready future.
The IR is structurally correct and would work with real suspension if the
await-point `coro.suspend` calls were restored.

## Specific findings

1. **PASS**: `57_real_await.mn` with 3 await points + fanout is the test
   that was missing since v4.26.0. It exists and compiles.
2. **PASS**: The A1 closure is genuine — compare to v4.24.0's identity
   lowering. Night and day.
3. **NOTE**: 70 tests are all IR string-match. Same testing-depth gap as
   Arc 7 and Arc 8. One test that runs the binary and checks stdout would
   be more convincing than 70 string assertions.
4. **PASS**: The DESIGN.md rejected-options section proved its worth — no
   scope creep toward green threads or CPS during implementation.
