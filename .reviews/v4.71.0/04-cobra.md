# Cobra — C++/ABI Lens

**Grade: 8/10** | **Verdict: PASS WITH NOTES**

## Assessment

The coroutine IR shape matches C++20 coroutine expectations. The switched-resume
ABI with `{resume_fn, destroy_fn, index}` frame layout is the same one Clang
uses. The `presplitcoroutine` attribute is the standard marker.

## Specific findings

1. **PASS**: The initial suspend / final suspend pattern is structurally correct.
   C++20 coroutines use the same two-suspend-point structure.
2. **PASS**: The `switch i8` pattern after `coro.suspend` has the correct three
   branches: default (suspend), 0 (resume), 1 (cleanup/destroy).
3. **NOTE**: C++ coroutines use a promise type to communicate values between
   the coroutine and the caller. Mapanare's Future `{i8, ptr}` serves the same
   purpose but doesn't use `llvm.coro.promise`. This is fine — the promise
   intrinsic is optional for switched-resume. But if v5.x wants promise-based
   storage (Rattler's v4.67.0 suggestion), the Future will need to move into the
   frame at a fixed offset.
4. **NOTE**: The 41 tests are all unit tests at the IR string level. No test
   compiles an async fn to an object file and verifies the resulting symbol table.
   This is a testing-depth gap similar to Arc 7.
5. **PASS**: The DESIGN.md rejected options section (§8) correctly identifies
   green threads, CPS, poll-based futures, and fibers as alternatives and explains
   why LLVM coroutines were chosen.
