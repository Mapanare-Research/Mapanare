# Mapanare v3.8.1 — Generics, Impl Dispatch, Trait Bounds

> Compile-time specialization of user-defined generic functions and structs.
> Impl method dispatch for user-defined types. Trait bounds validation.
> Each unique `<T>` instantiation generates a concrete, typed copy.
> No runtime polymorphism. No boxing. No vtables.

**Status:** COMPLETE
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No (additive — existing code unaffected)

---

## The Goal

Generics have been parsed since v0.x and are fully specified in SPEC.md
Section 13. v3.8.1 makes them real — `identity<Int>(42)` and
`identity<String>("hello")` each get their own native function with the
correct types. Impl method dispatch routes `obj.method()` to the correct
`Type_method()` mangled function. Trait bounds are validated at call sites.

---

## What Was Delivered

### Phase 1: Generic Functions — Python Bootstrap ✅

- `_generic_fn_defs` stores AST of generic functions
- `_monomorphize_call` infers type args, mangles name, specializes AST
- `_specialize_fn` clones FnDef with type substitution
- Semantic checker recognizes type params as UNKNOWN kind
- Turbofish `fn::<Int>(x)` supported

### Phase 2: Generic Functions — Self-Hosted Compiler ✅

- `LowerState.generic_fns: List<FnDefData>` stores generic fn ASTs
- `find_generic_fn`, `infer_type_args_from_call`, `mangle_generic_name`
- `specialize_fn` clones FnDefData with type substitution
- `try_monomorphize_call` orchestrates the pipeline
- `decode_ret_type` helper avoids Option<String> match (Python emitter bug)

### Phase 3: Generic Structs ✅

- `LowerState.generic_structs: List<StructDefData>` stores generic struct ASTs
- `try_monomorphize_struct` infers field types, registers specialized struct
- `substitute_field_type`, `find_type_param_index` helpers
- Python bootstrap: `_generic_struct_defs`, `_monomorphize_struct`
- `Pair<Int, Bool>` → `Pair__Int_Bool = type { i64, i1 }`

### Phase 4: Trait Bounds Validation ✅

- `_check_trait_bounds_at_call` in semantic.py
- Validates concrete types implement required traits at call sites
- Built-in types (Int, Float, String, Bool) have implicit Display/Eq/Ord/Hash
- Clear error: "Type 'Point' does not implement trait 'Ord' required by T"

### Phase 5: Impl Method Dispatch ✅

- Python lowerer: `_impl_methods` dict lookup in `_lower_method_call`
- Self-hosted lowerer: `lookup_impl_method` resolves `obj.method()` → `Type_method()`
- `fix_self_param_type` injects struct type for bare `self` parameters
- `register_impl` stores impl entries with correct method mappings

### Phase 6: Self-Hosted Parser — Impl Trait for Type ✅

- `parse_impl_def` handles both `impl Type { }` and `impl Trait for Type { }`
- `parse_fn_def_as_data` returns FnDefData directly (avoids DefResult.defn enum bug)
- `skip_brace_block` skips trait definitions (no MIR codegen needed)
- `parse_param` handles bare `self` (no `: Type` annotation)

### Phase 7: v3.8.0 Compiler Hardening ✅

- Loop bounds raised: 200→500, 600→2000, 2000→5000
- Method return types: +14 string, +8 list, +8 map methods
- Substr semantics: fixed comment, 5 native tests added
- toml.mn fixed (35/35 stdlib, up from 34/35)

---

## Golden Tests

| Test | Description |
|------|-------------|
| `26_generics.mn` | Generic functions (Int, Bool, String) + generic struct (Pair) |
| `27_impl.mn` | Impl method dispatch (Counter.get, Counter.add) |
| `28_traits.mn` | Impl dispatch + generics combined (Vec2.magnitude + double<T>) |

---

## Final Scorecard

| Metric | v3.7.0 (start) | v3.8.1 (end) |
|--------|----------------|--------------|
| Golden tests | 25/25 | **28/28** |
| Native assertions | 99 | **104** |
| Stdlib | 34/35 | **35/35** |
| Generics | None | **Functions + structs** |
| Impl dispatch | Broken | **Working (inherent + trait)** |
| Trait bounds | Not checked | **Validated at call sites** |
| Fixed point | stage3==stage4 | **stage3==stage4** |

---

## Known Limitations

1. **Generic type annotations** — `let p: Pair<Int, Bool> = ...` not supported
   (only inferred types work). Blocked by Python emitter enum-field extraction
   bug: adding functions to lower_state.mn that match on enum types triggers
   IR type mismatches in the compiled binary.

2. **Definition enum frozen** — Cannot add new variants (TraitDef) or change
   existing variant field counts (ImplDef 2→3 fields) without breaking the
   enum payload layout in the Python-bootstrapped binary.

3. **Python emitter enum-field bug** — Accessing an enum-typed field from a
   struct (e.g., DefResult.defn where Definition is an enum) produces IR with
   wrong alloca type (ptr instead of {i64, ptr}). Workaround: use accessor
   functions or avoid direct field access.

4. **Dead PHI lines** — 11 dead PHI lines in stage2/stage3 diff. Root cause:
   MIRType.kind field has garbage data in Python-bootstrapped binary from
   enum payload extraction. Cosmetic only, doesn't affect correctness.

---

## Non-Goals (deferred to v3.10.0+)

- Trait objects / dynamic dispatch
- Higher-kinded types
- Const generics
- Generic enums beyond built-in Option/Result
- Associated types
- Nested generics (`List<Pair<Int, String>>`)
- Generic type annotations (`let p: Pair<Int, Bool>`)
