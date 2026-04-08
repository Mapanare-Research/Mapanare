# Mapanare v3.9.0 — TraitDef + Generic Impl Blocks

> TraitDef variant in Definition enum. Generic impl blocks (`impl<T> Box<T> { ... }`).
> Type substitution fix for builtin types (String, Bool, Float).
> Enum-field bug confirmed resolved.

**Status:** COMPLETE
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No (additive — existing code unaffected)

---

## The Goal

v3.8.1 added generic functions, structs, and impl dispatch but couldn't do
`impl<T> Box<T> { fn get(self) -> T }` — methods on generic structs required
separate non-generic impls for each instantiation. v3.9.0 adds generic impl
blocks: write one impl, get monomorphized methods for every instantiation.

Also adds `TraitDef` to the `Definition` enum — previously blocked by the
enum-field bug, which was confirmed resolved by the large-struct handling
improvements in v3.0–v3.8.

---

## What Was Delivered

### Enum-Field Bug Resolution Confirmed

The Python emitter enum-field bug (struct fields of enum type producing wrong
IR type) is **no longer reproducible**. Tested:
- Adding `TraitDef(String, List<FnDefData>)` to Definition: 28/28 golden, fixed point OK
- Adding enum-matching functions to lower_state.mn: works
- Accessing DefResult.def_node (struct → enum field): works

### TraitDef Variant

- `Definition::TraitDef(String, List<FnDefData>)` added to ast.mn
- `def_kind` match arm, `def_trait_name`, `def_trait_methods` accessors
- Parser produces `TraitDef` instead of empty `ImportDef` for trait definitions
- Semantic checker registers trait names in scope
- Lowerer and codegen skip TraitDef (no MIR needed yet)

### Generic Impl Blocks — Python Bootstrap

- Grammar: `impl_def` extended with optional `type_params` before target name
- AST: `ImplDef.type_params: list[str]` field
- Parser: extracts type params from `impl<T>` syntax
- Lowerer: stores generic impl defs, defers method registration
- `_monomorphize_impl`: specializes methods when struct is instantiated
- Injects `self` parameter type for monomorphized struct
- `_substitute_type_expr`: fixed to map TypeKind → type name for builtins

### Generic Impl Blocks — Self-Hosted Compiler

- Parser: `parse_impl_def` skips `<T>` type params and `<T>` type args
- Registration: generic impl methods stored in `generic_fns` with struct prefix
- `monomorphize_impl_methods`: finds, specializes, and lowers impl methods
- `kind_to_type_name`: maps MIR kind strings to Mapanare type names
- `fix_self_param_type`: injects monomorphized struct type for `self`
- Lowerer skips generic impls in `lower_definition` (monomorphized on demand)

### Type Substitution Fix

Both Python and self-hosted compilers had a bug where substituting a type
parameter `T` with a builtin type (String, Bool, Float) would produce "Int"
because builtins have empty `name` fields. Fixed by mapping `TypeKind` to
the correct type name.

---

## Golden Tests

| Test | Description |
|------|-------------|
| `29_generic_impl.mn` | Generic impl blocks (Box<T>.get, Box<T>.set with Int instantiation) |

---

## Final Scorecard

| Metric | v3.8.1 (start) | v3.9.0 (end) |
|--------|----------------|--------------|
| Golden tests | 28/28 | **29/29** |
| Native assertions | 104 | **104** |
| Stdlib | 35/35 | **35/35** |
| Generic impl | Not supported | **Working** |
| TraitDef variant | Blocked | **Added** |
| Enum-field bug | Documented blocker | **Confirmed resolved** |
| Fixed point | stage3==stage4 | **stage3==stage4** |
| Python tests | 2531 | **2531** |

---

## Known Limitations

1. **Generic impl trait syntax** — `impl<T: Display> Box<T>` trait bounds on
   impl blocks not yet validated (methods compile but bounds unchecked)
2. **Multiple generic impls per struct** — Only one generic impl per struct
   name is stored (last one wins)
3. **Generic impls for enums** — Only structs, not enums
4. **Self-hosted trait body parsing** — Trait bodies are still skipped (no
   method signatures extracted)
