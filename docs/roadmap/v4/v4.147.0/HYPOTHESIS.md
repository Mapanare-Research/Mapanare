# E3 Hypothesis

## Original Claim (from PLAN.md)

> MIR-level escape analysis proves `List<T>` parameters non-aliasing in
> >= 3 functions across quicksort/prime_sieve/struct_alloc. Emitting
> `noalias` on these parameters unblocks LLVM loop-vectorize on >= 2
> hot loops, yielding 15-40% wall on target benches.

## Revised Claim (after IR diff)

**The original claim is structurally impossible.** LLVM `noalias` is a
parameter attribute that applies only to pointer-typed (`ptr`)
parameters. Mapanare passes `List<T>`, `String`, `Map<K,V>`, and small
structs as LLVM aggregates by value (e.g., `{ptr, i64, i64, i64, i64}`
for List) because they are under the 64-byte byref threshold. None of
the target benchmark functions have `ptr`-typed user parameters.

Even if `noalias` could be applied, the vectorization barriers in the
target benchmarks are control flow and trip count, not aliasing:
- quicksort: "control flow cannot be substituted for a select"
- prime_sieve: "could not determine number of loop iterations"
- struct_alloc: no vectorizable loop body (function call barrier)

## What COULD benefit from parameter-level noalias

1. **Closure environment pointers** (`ptr %__env_ptr`) — closures pass
   environment structs as bare `ptr`. A sound escape analysis could
   mark these `noalias` when the closure doesn't share its environment
   with another closure. Not present in target benchmarks.

2. **Future byref parameters** — if `_BYREF_BYTES` is lowered (e.g., to
   24 bytes to match Rust's pointer-passing threshold), then List/String
   parameters would become `ptr`-typed and `noalias` would apply. This
   is an ABI change outside E3 scope.

3. **Alias scope metadata** (`!alias.scope` / `!noalias` on load/store
   instructions) — a different mechanism than parameter attributes.
   Could tell LLVM that loads through the List data pointer don't alias
   stores through other pointers. More complex than E3 scopes.

## Escape-analysis precision rules (implemented despite dead-end outcome)

The pass is implemented for completeness and future use. Its precision
rules are:

### Safe to mark `noalias`
- Parameter is pointer-typed in LLVM (`ptr`) — i.e., byref params or
  closure env pointers
- Function body does NOT:
  - Store the parameter pointer into another aggregate (FieldSet/IndexSet/ListPush)
  - Return the parameter pointer
  - Capture the parameter in a closure (ClosureCreate)
  - Pass the parameter to an unknown/potentially-capturing function call
- Function is not recursive with self-calls passing the same parameter
- All call sites pass distinct SSA values for the parameter

### Unsafe (do NOT mark)
- Parameter is not pointer-typed (aggregate, scalar) — `noalias` invalid
- Parameter is `Signal` / `Stream` / `Agent` type — runtime may
  internally share pointers
- Function stores parameter into shared data structure
- Any call site passes the same SSA name for two `noalias`-candidate
  parameters

## Expected outcome

**DEAD END.** Zero parameters marked across target benchmarks (no `ptr`
user params exist). The pass is kept for closure env pointers and future
byref params, but contributes zero performance improvement to the
current benchmark corpus.
