# Mapanare v4.15.0 — Module-Level Let + MIRType Enum

> Top-level constants and a real TypeKind enum. The compiler stops comparing strings for types.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.14.0

---

## The Problem

Two foundational gaps remain in the self-hosted compiler:

1. **Module-level `let` not supported.** There is no `LetDef` variant in the
   `Definition` enum in `ast.mn`. Top-level constants (like lookup tables,
   format strings, configuration values) must be passed as function arguments
   or hardcoded inline. This blocks clean MIRType enum migration because the
   enum variants need module-level constant definitions.

2. **MIRType.kind is a String.** Type checking uses `t.kind == "int"` string
   comparisons throughout the compiler. Functions like `TK_INT()`, `TK_FLOAT()`,
   etc. return string constants. This is slow (string comparison on every type
   check), fragile (typos compile but produce wrong behavior), and prevents
   exhaustive match checking on types.

---

## Phase 1: Add LetDef to the AST

- [ ] Add `LetDef` variant to `Definition` enum in `mapanare/self/ast.mn`
- [ ] Fields: `name: String`, `type_name: String`, `value: Expr`
- [ ] Add constructor: `fn make_let_def(name: String, type_name: String, value: Expr) -> Definition`
- [ ] Update Python AST in `mapanare/ast_nodes.py` to match
- [ ] Rebuild + golden

## Phase 2: Parser support for top-level let

- [ ] In `mapanare/self/parser.mn`: recognize `let` at module scope
- [ ] Parse: `let NAME: TYPE = EXPR` at top level
- [ ] Emit `LetDef` node
- [ ] Update Python parser in `mapanare/parser.py` to match
- [ ] Rebuild + golden

## Phase 3: Lowerer support for module constants

- [ ] In `mapanare/self/lower.mn`: handle `LetDef` during module registration
- [ ] Emit as LLVM `@global_name = private constant ...`
- [ ] Support Int, Float, Bool, String constant types
- [ ] In `mapanare/self/emit_llvm.mn`: emit global constant definitions
- [ ] Update Python lowerer `mapanare/lower.py` to match
- [ ] Update Python emitter `mapanare/emit_llvm_text.py` to match
- [ ] Rebuild + golden + stage2
- [ ] Add golden test: `tests/golden/41_module_let.mn`

## Phase 4: Migrate MIRType to enum

- [ ] Define `TypeKind` enum in `mapanare/self/mir.mn`:
  ```
  enum TypeKind:
      TkInt
      TkFloat
      TkBool
      TkString
      TkVoid
      TkStruct
      TkEnum
      TkList
      TkMap
      TkOption
      TkResult
      TkFn
      TkAgent
      TkSignal
      TkStream
      TkTensor
      TkPtr
      TkUnknown
  ```
- [ ] Change `MIRType.kind` field from `String` to `TypeKind`
- [ ] Define module-level constants using the new `let`:
  ```
  let TYPE_INT: TypeKind = TkInt
  let TYPE_FLOAT: TypeKind = TkFloat
  ```
- [ ] Replace ALL `TK_INT()` / `TK_FLOAT()` / etc. function calls with constant references
- [ ] Replace ALL `t.kind == "int"` comparisons with `t.kind == TkInt`
- [ ] Delete the `TK_*()` functions
- [ ] Rebuild + golden + stage2

## Phase 5: Exhaustive type matching

- [ ] Anywhere the compiler switches on `MIRType.kind`, use `match` on TypeKind
- [ ] Verify no fallthrough cases — every TypeKind variant handled or has default
- [ ] Rebuild + golden + stage2

---

## Exit Criteria

| Check | Required |
|-------|----------|
| LetDef variant in Definition enum | YES |
| Parser emits LetDef at module scope | YES |
| Lowerer emits LLVM global constants | YES |
| Golden test for module-level let | YES |
| TypeKind enum defined in mir.mn | YES |
| MIRType.kind uses TypeKind (not String) | YES |
| All TK_*() functions deleted | YES |
| No string-based type comparisons remain | YES |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
