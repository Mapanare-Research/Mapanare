# Mapanare v3.27.0 — "Güio" (Transpiler Framework)

> Build the shared transpiler framework in the self-hosted compiler. Extract
> common translation patterns (type mapping, class→struct, exception→Result,
> type inference, diagnostics) into `transpiler.mn` so each language front-end
> is ~400 lines of language-specific code instead of ~1,800 lines of duplicated
> logic.

**Status:** DONE
**Estimated scope:** Large (2-3 sessions)
**Breaking:** No
**Prerequisite:** v3.26.0 (review fixes, `any` type in spec, stale main.ll rebuilt)

---

## Motivation

The Python transpiler (928 lines) and PHP transpiler (1,811 lines) duplicate
significant logic: type mapping, class→struct+impl translation, exception→Result
conversion, stdlib shim lookup, local type inference, unsupported feature
diagnostics, and `any` boxing decisions. Adding TypeScript and Go would triple
the duplication.

The framework extracts shared patterns into `transpiler.mn`, reducing each
language module to its lexer, parser, and AST-walk — the parts that are
genuinely language-specific. This mirrors how the compiler itself works:
`semantic.mn`, `lower.mn`, and `emit_llvm.mn` are language-agnostic backends
that process the shared Mapanare AST.

The name "Güio" (Venezuelan anaconda) reflects the framework wrapping around
all transpiler modules.

---

## Architecture

```
mapanare/self/
    transpiler.mn          ← shared framework (~500 lines)
    from_python.mn         ← Python-specific lexer/parser + walks (~400 lines)
    from_php.mn            ← PHP-specific lexer/parser + walks (~400 lines)
    from_typescript.mn     ← v3.30.0
    from_go.mn             ← v3.31.0

                  ┌─ lexer.mn + parser.mn ───── .mn source
                  │
  Mapanare AST ◄──┼─ from_python.mn ─────────── .py source
                  │
                  ├─ from_php.mn ──────────────  .php source
                  │
                  ├─ from_typescript.mn ────────  .ts source (v3.30.0)
                  │
                  └─ from_go.mn ───────────────  .go source (v3.31.0)
                  │
                  ▼
            semantic.mn → lower.mn → emit_llvm.mn → binary
```

---

## Items

### 1. `TypeMapping` struct and `translate_type()` [HIGH]

**File:** `mapanare/self/transpiler.mn` (new)
**Reporter:** roadmap
**Fix:** Define the core type mapping infrastructure:

```mn
struct TypeMapping {
    source_name: String,
    target_kind: String,     // "Int", "Float", "String", etc.
    generic_args: List<String>,
}

fn translate_type(source_type: String, mappings: List<TypeMapping>) -> String {
    // Lookup in mapping table
    // Handle nullable: "?Type" → "Option<Type>"
    // Handle generics: "List<int>" → "List<Int>"
    // Fallback: return "any"
}
```

Each language registers its own mappings (e.g., Python: `int→Int`, `str→String`;
PHP: `int→Int`, `string→String`; TS: `number→Float`, `string→String`).

### 2. `translate_class_to_struct()` [HIGH]

**File:** `mapanare/self/transpiler.mn`
**Reporter:** roadmap
**Fix:** Extract the shared class→struct+impl translation:

```mn
struct FieldDef {
    name: String,
    type_name: String,
    default_value: String,  // empty string = no default
}

struct MethodDef {
    name: String,
    params: List<ParamDef>,
    return_type: String,
    body_lines: List<String>,
    is_static: Bool,
}

fn translate_class_to_struct(
    name: String,
    fields: List<FieldDef>,
    methods: List<MethodDef>,
) -> String {
    // Emit: struct Name { field: Type, ... }
    // Emit: impl Name { fn method(self, ...) -> T { ... } }
    // Static methods become standalone functions
}
```

This is the same logic in `PythonTranslator._translate_class` and
`PhpTranslator._translate_class`, extracted and parameterized.

### 3. `translate_exception_to_result()` [HIGH]

**File:** `mapanare/self/transpiler.mn`
**Reporter:** roadmap
**Fix:** Shared try/except → Result pattern:

```mn
struct CatchClause {
    exception_type: String,
    variable: String,
    body_lines: List<String>,
}

fn translate_exception_to_result(
    try_body: List<String>,
    catch_clauses: List<CatchClause>,
    finally_body: List<String>,
) -> String {
    // Emit: match result_expr { Ok(val) => ..., Err(e) => ... }
    // Map exception types to error enum variants where possible
    // Preserve finally body as unconditional suffix
}
```

### 4. `infer_local_type()` [MEDIUM]

**File:** `mapanare/self/transpiler.mn`
**Reporter:** roadmap
**Fix:** Shared type inference from initializer expressions:

```mn
fn infer_local_type(initializer: String) -> String {
    // Integer literal → "Int"
    // Float literal → "Float"
    // String literal → "String"
    // Boolean literal → "Bool"
    // List literal → "List<T>" (infer T from first element)
    // Map literal → "Map<K, V>"
    // Constructor call → struct name
    // Ambiguous → "any"
}
```

### 5. `report_unsupported()` diagnostic [MEDIUM]

**File:** `mapanare/self/transpiler.mn`
**Reporter:** roadmap
**Fix:** Shared diagnostic for unsupported source language features:

```mn
fn report_unsupported(
    feature: String,
    suggestion: String,
    source_line: Int,
    filename: String,
) -> String {
    // Returns: "// WARNING: {feature} not supported (line {source_line}). {suggestion}"
    // Also logs to stderr: "warning: {filename}:{source_line}: {feature} — {suggestion}"
}
```

Used by all transpilers for consistent diagnostics when encountering
decorators, generators, metaclasses, abstract classes, etc.

### 6. Stdlib shim registry [MEDIUM]

**File:** `mapanare/self/transpiler.mn`
**Reporter:** roadmap
**Fix:** A registry pattern for stdlib function mappings:

```mn
struct StdlibShim {
    source_name: String,
    target_expr: String,     // e.g., "len", ".to_lower()", "math.sqrt"
    is_method: Bool,         // true = ".method()", false = "func()"
    arg_reorder: List<Int>,  // empty = same order, [1, 0] = swap first two
}

fn translate_stdlib_call(
    func_name: String,
    args: List<String>,
    shims: List<StdlibShim>,
) -> String {
    // Lookup func_name in shims
    // Apply arg reorder if specified
    // Emit method call or function call
    // Return "/* unknown: func_name(...) */" for unmapped functions
}
```

### 7. `TranspilerState` struct [MEDIUM]

**File:** `mapanare/self/transpiler.mn`
**Reporter:** roadmap
**Fix:** Shared state for all transpilers:

```mn
struct TranspilerState {
    filename: String,
    source_language: String,   // "python", "php", "typescript", "go"
    indent_level: Int,
    declared_vars: List<String>,  // flat list; scope push/pop via markers
    type_mappings: List<TypeMapping>,
    stdlib_shims: List<StdlibShim>,
    warnings: List<String>,
    errors: List<String>,
}

fn new_state(filename: String, lang: String) -> TranspilerState
fn push_scope(state: TranspilerState) -> TranspilerState
fn pop_scope(state: TranspilerState) -> TranspilerState
fn is_declared(state: TranspilerState, name: String) -> Bool
fn declare_var(state: TranspilerState, name: String) -> TranspilerState
fn indent(state: TranspilerState) -> String   // returns current indentation
```

### 8. `any` boxing decision helper [LOW]

**File:** `mapanare/self/transpiler.mn`
**Reporter:** roadmap
**Fix:** Helper to decide when `any` is needed vs when a concrete type can
be inferred:

```mn
fn needs_any_boxing(source_type: String, mappings: List<TypeMapping>) -> Bool {
    // Returns true if source_type cannot be mapped to a concrete Mapanare type
    // Used to emit boxing calls when assigning to any-typed variables
}

fn emit_any_annotation(param_name: String, inferred_type: String) -> String {
    // If inferred_type == "any", emit: "// NOTE: {param_name} typed as any — add type annotation for safety"
}
```

### 9. Integration tests [MEDIUM]

**File:** `tests/transpiler/test_framework.py` (new)
**Reporter:** roadmap
**Fix:** Test the framework functions independently of any specific language:
- `translate_type` with Python, PHP, TS, Go mappings
- `translate_class_to_struct` with various field/method combinations
- `infer_local_type` with all literal types
- `report_unsupported` output format
- `translate_stdlib_call` with arg reorder
- `TranspilerState` scope push/pop

### 10. Wire into self-hosted build [LOW]

**File:** `scripts/build_stage1.py`, `mapanare/self/mnc_all.mn`
**Reporter:** roadmap
**Fix:** Add `transpiler.mn` to the self-hosted module concatenation list.
Ensure it compiles through the Python bootstrap emitter. The module is
imported by `from_python.mn` (v3.28.0) and `from_php.mn` (v3.29.0) but
has no callers yet in this version — it is the foundation.

---

## What's NOT in This Release

- **No self-hosted Python transpiler.** That is v3.28.0.
- **No self-hosted PHP transpiler.** That is v3.29.0.
- **No TypeScript or Go.** Those are v3.30.0 and v3.31.0.
- **No changes to the Python-based transpilers.** `from_python.py` and
  `from_php.py` continue to work unchanged. The `.mn` framework is the
  foundation for the self-hosted replacements.

---

## Verification

- [ ] `transpiler.mn` compiles through the Python bootstrap emitter
- [ ] `transpiler.mn` concatenated into `mnc_all.mn` — golden tests still pass
- [ ] `translate_type("int", python_mappings)` returns `"Int"`
- [ ] `translate_type("?string", php_mappings)` returns `"Option<String>"`
- [ ] `translate_class_to_struct(...)` produces valid struct + impl block text
- [ ] `translate_exception_to_result(...)` produces valid match expression
- [ ] `infer_local_type("42")` returns `"Int"`
- [ ] `infer_local_type('"hello"')` returns `"String"`
- [ ] Framework tests pass: `pytest tests/transpiler/ -v`
