# Mapanare v3.9.0 — Generics Monomorphization

> Compile-time specialization of user-defined generic functions and structs.
> Each unique `<T>` instantiation generates a concrete, typed copy.
> No runtime polymorphism. No boxing. No vtables.

**Status:** IN PROGRESS
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No (additive — existing code unaffected)

---

## The Goal

Generics have been parsed since v0.x and are fully specified in SPEC.md
Section 13. But they're inert — `fn identity<T>(x: T) -> T` parses and
type-checks but the compiler never generates specialized code for
`identity(42)` vs `identity("hello")`. The type parameter `T` is erased
to `unknown` during lowering, producing i64 everywhere.

v3.9.0 makes generics real. After this version, `identity<Int>(42)` and
`identity<String>("hello")` each get their own native function with the
correct types — zero-cost abstraction through monomorphization.

---

## Inherited State (from v3.8.0)

| Component | Status |
|-----------|--------|
| **Parsing** | Complete: `<T>`, `<T: Trait>`, turbofish `fn::<T>(x)` |
| **AST** | Complete: TypeParam, GenericType, type_args on CallExpr |
| **Semantic** | Built-in generics only (List, Map, Option, Result) |
| **MIR lowering** | Only impl methods monomorphized by name-mangling |
| **Self-hosted** | Parses type_params, ignores them during lowering |
| **Spec** | Section 13 fully describes monomorphization semantics |
| **Tests** | Parser + spec tests pass; no end-to-end generic function tests |

---

## Architecture

### Where Monomorphization Lives

```
Source → Parser → AST → Semantic → MIR Lowering → MIR → Emitter → LLVM IR
                                    ^^^^^^^^^^^^^^^
                                    Monomorphize here
```

During MIR lowering, when the lowerer encounters a CALL to a generic
function, it:

1. **Resolves type arguments** — infer `T` from argument types, or use
   explicit turbofish `fn::<Int>(x)`
2. **Generates a mangled name** — `identity__Int`, `pair__Int_String`
3. **Checks the specialization cache** — if already monomorphized, reuse
4. **Clones and specializes the AST** — replace `T` with `Int` in params,
   return type, and body
5. **Lowers the specialized copy** — emits it as a regular (non-generic)
   function

### Mangling Scheme

```
fn identity<T>(x: T) -> T
  identity__Int       when T = Int
  identity__String    when T = String
  identity__Bool      when T = Bool

fn pair<A, B>(a: A, b: B)
  pair__Int_String    when A = Int, B = String

struct Pair<A, B> { first: A, second: B }
  Pair__Int_String    when A = Int, B = String
```

Separator: `__` between base name and type args. `_` between multiple
type args. Nested generics: `List_Int` for `List<Int>`.

### Type Inference

At a call site `identity(42)`:
1. Look up `identity` in scope — find it has type_params `[T]`
2. Match parameter types against argument types: `T` ↔ `Int`
3. Build substitution map: `{T: Int}`
4. Apply to return type: `T` → `Int`

For turbofish `identity::<String>("hello")`:
1. Type args are explicit: `{T: String}`
2. Verify argument types match (String == String)

---

## Phases

### Phase 1: Python Bootstrap — Generic Functions

**Files:** `mapanare/lower.py`, `mapanare/semantic.py`

1. In `lower.py._lower_call()`, detect calls to generic functions
   (functions with non-empty `type_params`)
2. Infer type arguments from call-site argument types
3. Generate mangled name
4. If not already specialized, clone the FnDef AST, substitute types,
   and lower the specialized copy
5. Emit call to the mangled name

**Test:** `fn identity<T>(x: T) -> T { return x }` +
`let a = identity(42)` → compiles to `identity__Int(42)` returning Int

### Phase 2: Self-Hosted Compiler — Generic Functions

**Files:** `mapanare/self/lower.mn`, `mapanare/self/lower_state.mn`

Mirror the Python implementation in the self-hosted lowerer:
1. Add a specialization cache to LowerState (map from mangled name to bool)
2. In lower_call, detect generic functions, infer types, mangle name
3. Clone function definition, substitute type params, lower the clone
4. Emit call to mangled name

### Phase 3: Generic Structs

**Files:** `mapanare/lower.py`, `mapanare/self/lower.mn`

1. When a generic struct is instantiated with concrete types, generate
   a specialized struct definition (mangled name, concrete field types)
2. Register the specialized struct for emission
3. All field accesses, constructors, and method calls use the mangled name

### Phase 4: Trait Bounds (validation only)

Check that type arguments satisfy declared trait bounds:
- `fn max<T: Ord>(a: T, b: T) -> T` — verify T has Ord impl
- Error if no impl exists

### Phase 5: Golden Tests + Native Tests

Add golden tests for:
- Generic identity function
- Generic pair struct
- Turbofish syntax
- Multiple type parameters
- Nested generics (`List<Pair<Int, String>>`)
- Recursive generic calls

---

## Success Criteria

- [ ] `fn identity<T>(x: T) -> T` works with Int, String, Bool
- [ ] `fn pair<A, B>(a: A, b: B) -> A` works with multiple type args
- [ ] Turbofish `identity::<Int>(42)` works
- [ ] Generic functions compile through both Python and self-hosted paths
- [ ] Golden tests added and passing
- [ ] 25/25 existing golden tests still pass
- [ ] Fixed point maintained (stage3 == stage4)
- [ ] No performance regression on existing programs

---

## Non-Goals

- Trait objects / dynamic dispatch (future)
- Higher-kinded types (future)
- Const generics (future)
- Generic enums beyond built-in Option/Result (Phase 3+)
- Associated types (future)
