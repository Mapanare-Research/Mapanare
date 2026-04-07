# Mapanare v3.23.0 — "Tragavenado" (Dynamic `any` Type)

> Add a first-class `any` type to Mapanare: a tagged value that carries its
> runtime type alongside its data. This is the foundation for Python interop,
> dynamic dispatch, and gradual typing.

**Status:** PLANNED
**Estimated scope:** Medium-Large (2-3 sessions)
**Breaking:** No
**Prerequisite:** v3.22.0

---

## Motivation

Mapanare is statically typed. That's good for performance and correctness, but
it blocks two things:

1. **Python transpilation** — Python code without type hints has no static type.
   We need a box to put untyped values in.
2. **Gradual typing** — Let users start untyped and add types incrementally,
   like TypeScript's `any` or Dart's `dynamic`.
3. **FFI boundaries** — Foreign functions often return opaque values.

`any` is a tagged union at runtime: a type tag + a pointer to the value. The
compiler knows nothing about the contents — all operations go through runtime
dispatch.

---

## Items

### 1. `MnValue` tagged union in C runtime [HIGH]

**File:** `runtime/native/mapanare_core.h`, `runtime/native/mapanare_core.c`

Define the runtime representation:

```c
typedef enum {
    MN_TAG_INT,
    MN_TAG_FLOAT,
    MN_TAG_BOOL,
    MN_TAG_STRING,
    MN_TAG_LIST,
    MN_TAG_MAP,
    MN_TAG_STRUCT,
    MN_TAG_ENUM,
    MN_TAG_FN,
    MN_TAG_OPTION,
    MN_TAG_RESULT,
    MN_TAG_NONE,
} MnTypeTag;

typedef struct {
    MnTypeTag tag;
    union {
        int64_t  i;
        double   f;
        uint8_t  b;
        MnString s;
        MnList   list;
        MnMap    map;
        void*    ptr;   // structs, enums, closures
    } data;
} MnValue;
```

Runtime functions:
- `__mn_any_box_int(int64_t) -> MnValue`
- `__mn_any_box_float(double) -> MnValue`
- `__mn_any_box_bool(uint8_t) -> MnValue`
- `__mn_any_box_string(MnString) -> MnValue`
- `__mn_any_box_ptr(MnTypeTag, void*) -> MnValue`
- `__mn_any_unbox_int(MnValue) -> int64_t` (panics on tag mismatch)
- `__mn_any_unbox_float(MnValue) -> double`
- `__mn_any_unbox_bool(MnValue) -> uint8_t`
- `__mn_any_unbox_string(MnValue) -> MnString`
- `__mn_any_unbox_ptr(MnValue) -> void*`
- `__mn_any_tag(MnValue) -> MnTypeTag`
- `__mn_any_typename(MnValue) -> MnString` (for error messages)

### 2. `any` in the type system [HIGH]

**File:** `mapanare/types.py`

- Add `ANY` to `TypeKind` enum (kind #26)
- `any` is a valid type annotation: `let x: any = 42`
- `any` is assignable from every type (implicit boxing)
- Every type is assignable from `any` (implicit unboxing + runtime check)
- `any` propagates: `any + int -> any`, `any.field -> any`

### 3. `any` in the grammar [LOW]

**File:** `mapanare/mapanare.lark`

`any` becomes a keyword / builtin type name. Parse `any` in type positions:
- `fn foo(x: any) -> any`
- `let x: any = ...`
- `List<any>`, `Map<String, any>`

### 4. Semantic checker support [HIGH]

**File:** `mapanare/semantic.py`

Rules:
- `any` unifies with every type (no type error on assignment)
- Binary ops with `any` operand produce `any` result type
- Method calls on `any` produce `any` (runtime dispatch)
- Field access on `any` produces `any`
- `any` in generics: `List<any>` is valid, element access returns `any`
- Explicit cast: `x as Int` on an `any` value inserts an unbox + tag check

### 5. MIR lowering [HIGH]

**File:** `mapanare/lower.py`

- Assignment `let x: any = 42` lowers to `box_int(42)` call
- Reading `x` where `any` expected: pass through (already boxed)
- Reading `x` where concrete type expected: insert `unbox_T(x)` call
- Binary ops on `any`: dispatch to `__mn_any_binop(op, lhs, rhs)`
- Method calls on `any`: dispatch to `__mn_any_method(name, receiver, args)`

### 6. LLVM IR emission [HIGH]

**File:** `mapanare/emit_llvm_mir.py`

- `any` maps to `%MnValue` struct type (tag i32 + union {i64, double, i8, ptr})
- Box/unbox intrinsics map to C runtime calls
- Implicit conversions at call boundaries: if callee expects `any`, box the arg;
  if callee expects concrete type, unbox the `any` arg

### 7. Runtime dispatch for operators and methods [MEDIUM]

**File:** `runtime/native/mapanare_core.c`

```c
MnValue __mn_any_binop(int32_t op, MnValue lhs, MnValue rhs);
MnValue __mn_any_method(MnString name, MnValue receiver, MnValue* args, int32_t argc);
```

Operator dispatch: check tags, perform the operation, return boxed result.
Tag mismatch → runtime panic with clear error:
`"TypeError: cannot add String and Int"`

Method dispatch: lookup method by name on the runtime type. Start with builtins
only (`len`, `push`, `pop`, `get`, `str`). Struct/trait methods deferred.

### 8. `typeof` builtin [LOW]

**File:** `mapanare/types.py`, `mapanare/lower.py`

```mn
let x: any = 42
if typeof(x) == "Int" {
    let n: Int = x as Int  // safe, we just checked
}
```

`typeof(x)` on a concrete type is a compile-time constant string.
`typeof(x)` on `any` calls `__mn_any_typename(x)` at runtime.

### 9. Type inference with `any` [MEDIUM]

**File:** `mapanare/semantic.py`

The middle-ground rule:
- Function signatures **must** have type annotations (existing requirement)
- Local variables infer from their initializer: `let x = 42` → `Int`, not `any`
- Only explicit `any` annotation or untyped function params produce `any`
- No implicit "everything is any" — the programmer opts in

### 10. Golden test: `any_basics.mn` [LOW]

**File:** `tests/golden/33_any_basics.mn`

```mn
fn identity(x: any) -> any {
    return x
}

fn main() {
    let a: any = 42
    let b: any = "hello"
    let c: any = true

    print(identity(a))    // 42
    print(identity(b))    // hello
    print(typeof(a))      // Int
    print(typeof(b))      // String

    let n: Int = a as Int
    print(n + 1)          // 43
}
```

---

## Verification

- [ ] `MnValue` struct compiles with gcc + clang, no UB under ASan
- [ ] `any` parses in type positions (grammar test)
- [ ] Semantic checker accepts `any` assignments, rejects nothing with `any`
- [ ] `let x: any = 42; print(x)` compiles and prints `42`
- [ ] `let x: any = "hi"; let s: String = x as String` works
- [ ] `let x: any = "hi"; let n: Int = x as Int` panics with TypeError
- [ ] `typeof(x)` returns correct type name at runtime
- [ ] `__mn_any_binop` handles int+int, float+float, string+string
- [ ] `/golden` — all 33 tests pass (existing + new any_basics)
- [ ] No performance regression on typed code (any is opt-in, zero cost if unused)
