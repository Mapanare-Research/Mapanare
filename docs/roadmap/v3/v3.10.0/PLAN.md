# Mapanare v3.10.0 — Error Messages + Semantic Maturity

> Self-hosted compiler produces useful error messages with line numbers.
> Generic enums. Trait method signatures. Builtin coverage complete.
> The compiler is usable by someone other than its authors.

**Status:** COMPLETE
**Estimated scope:** Medium (2-3 sessions)
**Breaking:** No

---

## Why This Version Exists

The self-hosted compiler works but is hostile to users:
- Error messages say "Undefined variable 'x'" with line 0, column 0
- No source context shown
- Missing builtins silently produce garbage IR
- Generic enums (beyond Option/Result) don't work
- Trait bodies are parsed but discarded — trait requirements unchecked

v3.10.0 makes the compiler usable for external developers.

---

## Phase 1: Error Messages with Line Numbers [DONE]

### 1.1 — Thread source location through AST -> semantic [DONE]

Added `current_span: Span` field to `SemState`. All 24 `add_error` call
sites now use `add_error_here()` which extracts line/column from the
current function/block span. Added `set_span()` helper and wired it into
`check_fn_body`, `check_agent_body`, and `check_block`.

Fixed the commented-out error accumulation (`st.errors.push(err)`) by
creating a new error list and returning updated state.

### 1.2 — Format errors with source context [DONE]

Error format: `file.mn:5:12: error: Undefined variable 'x'`
(function-level precision — exact expression positions require Expr spans).

### 1.3 — Complete builtin function coverage [DONE]

Added all C runtime builtins to `is_builtin_function()` and
`register_builtins()`: `__mn_argc`, `__mn_argv`, `__mn_file_read_or_empty`,
`__mn_exit`, `__mn_str_eprint`, `__mn_str_eprintln`, `__mn_system`,
`__mn_file_write`.

Un-xfailed `test_all_builtin_functions_covered` — now passes.

---

## Phase 2: Generic Enums [DONE]

### 2.1 — User-defined generic enums [DONE]

Added on-demand monomorphization for generic enums, mirroring the
existing generic struct infrastructure:

- `generic_enums: List<EnumDefData>` field in LowerState
- `find_generic_enum`, `is_generic_enum_variant`, `try_monomorphize_enum`
- `infer_enum_type_args` from variant constructor arguments
- Type substitution per-variant via `substitute_field_type`
- Name mangling: `Box<Int>` -> `Box__Int`

Fixed `register_enum_if_enum` (pass 1) to also defer generic enums.

### 2.2 — Golden test for generic enums [DONE]

`32_generic_enum.mn`: `enum Box<T> { Full(T), Empty }` with
`Full(42)` monomorphizing to `Box__Int`.

---

## Phase 3: Trait Method Validation [DONE]

### 3.1 — Parse and store trait method signatures [DONE]

Extended `ImplDef` to carry optional trait name:
`ImplDef(String, Option<String>, List<FnDefData>)`.

Parser preserves trait name from `impl Trait for Type` syntax.

Trait methods registered as `"TraitName.method_name"` symbols in scope.

### 3.2 — Validate impl blocks against trait requirements [DONE]

`validate_trait_methods()` checks that all required methods from the
trait definition are provided in the impl block. Error messages for:
- Missing methods
- Undefined traits
- Non-trait types in `impl Trait for Type`

---

## Exit Criteria

- [x] Error messages include line numbers (>80% of error sites)
- [x] `is_builtin_function` covers all Python-side builtins
- [x] Generic enum monomorphization works (golden test 32)
- [x] Trait method signatures parsed and stored
- [x] `impl Trait for Type` validated against trait requirements
- [x] Builtin coverage xfail test un-xfailed and passing
- [x] 32+ golden tests
