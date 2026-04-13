# Coral — Language Design Lens

**Grade: 9/10** | **Verdict: PASS**

## Assessment

The user-facing experience matches DESIGN.md §3 exactly. `async fn` and `await`
have the expected semantics. The three semantic errors are clear and actionable.
The precedence decision (`await` at unary level) matches Rust and is well-tested.

## Specific findings

1. **PASS**: `async fn foo() -> Int` is sugar for returning `Future<Int>` — the
   type system handles this transparently. Users don't need to write `Future<Int>`
   explicitly (though they can, per DESIGN.md §3.4).
2. **PASS**: "forgot to await" error is excellent — `Cannot use Future<Int> in '+'
   operation — did you forget 'await'?` is actionable and specific.
3. **PASS**: `await` outside async fn produces a clear error at semantic time.
4. **PASS**: `async` and `await` are properly reserved keywords with documented
   breaking change in the v4.68.0 CHANGELOG.
5. **NOTE**: `Future<T>` is recognized as a generic type in the grammar (via
   `BUILTIN_GENERIC_TYPES`), but there's no way to construct a Future manually
   yet. DESIGN.md §3.4 says `Future.ready(x)` should work for explicit
   construction. This is a v4.73.0+ concern — not blocking for Arc 8.
