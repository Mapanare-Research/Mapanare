# Coral — Language Design Lens

**Grade: 10/10** | **Verdict: PASS**

## Assessment

The user-facing async surface is clean and well-designed:
- `async fn foo() -> Int` — declares a coroutine
- `await expr` — suspends until ready
- `for await x in stream` — async iteration
- `block_on(future)` — drives from sync context
- `Future<T>` — first-class type with compile-time enforcement

Three compile-time errors catch common mistakes:
- `await` outside `async fn` — "can only be used inside an 'async fn'"
- `await` on non-Future — "requires a Future<T>, got Int"
- Future in arithmetic — "did you forget 'await'?"

The design-first approach (v4.67.0 DESIGN.md before any code) prevented
the v4.19.0 hollow-feature pattern. Every release followed the design or
documented deviations.

## Specific findings

1. **PASS**: Syntax matches DESIGN.md §3 exactly.
2. **PASS**: `await` precedence (unary level, Rust-style) is correct and tested.
3. **PASS**: `for await` reads naturally and matches JS/Python async patterns.
4. **PASS**: "Forgot to await" error is the best diagnostic in the compiler.
5. **PASS**: The 10-release arc pacing was exemplary — each release was
   independently verifiable and coherent.

This is the best feature delivery in the project's history.
