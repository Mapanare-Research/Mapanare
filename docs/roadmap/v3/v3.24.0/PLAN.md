# Mapanare v3.24.0 — "Macagua" (Python Transpiler)

> Compile typed Python to native code via Mapanare. `mapanare compile main.py`
> parses Python, translates to Mapanare AST, and runs the full compilation
> pipeline: semantic check, MIR lowering, LLVM IR, native binary.

**Status:** DONE
**Estimated scope:** Large (3-4 sessions)
**Breaking:** No
**Prerequisite:** v3.23.0 (`any` type required for untyped expressions)

---

## Motivation

Python is the most popular programming language. Mapanare has a full native
compilation pipeline. Bridging the two means:

1. **Performance** — Typed Python compiled to native code, no interpreter overhead
2. **Adoption** — Python developers can try Mapanare without rewriting anything
3. **Gradual migration** — Start with `.py`, add Mapanare features (agents, signals,
   streams) incrementally, eventually rename to `.mn`

The strategy: accept Python with type annotations at function boundaries. Infer
types for local variables where possible. Fall back to `any` (from v3.23.0) for
genuinely dynamic code.

---

## Items

### 1. Python AST → Mapanare AST translator [HIGH]

**File:** `mapanare/from_python.py` (new, ~800-1000 lines)

Use Python's `ast` module to parse `.py` files, then walk the AST and emit
Mapanare `ast_nodes` dataclasses.

**Direct mappings:**
| Python | Mapanare |
|--------|----------|
| `def f(x: int) -> int:` | `fn f(x: Int) -> Int` |
| `class Foo:` | `struct Foo` + `impl Foo` |
| `if/elif/else` | `if/else if/else` |
| `for x in items:` | `for x in items` |
| `while cond:` | `while cond` |
| `return x` | `return x` |
| `x: int = 5` | `let x: Int = 5` |
| `x = 5` | `let x = 5` (infer Int) |
| `[1, 2, 3]` | `[1, 2, 3]` (List<Int>) |
| `{"a": 1}` | `{"a": 1}` (Map<String, Int>) |
| `None` | `None` (Option) |
| `True`/`False` | `true`/`false` |
| `f"hello {name}"` | `"hello " + str(name)` |
| `try/except` | Result<T, E> + match |
| `async def` | `agent` |
| `await` | `sync` |
| `lambda x: x+1` | `(x) => x + 1` |
| `@decorator` | (ignore or warn) |

**Type mapping:**
| Python type | Mapanare type |
|-------------|---------------|
| `int` | `Int` |
| `float` | `Float` |
| `str` | `String` |
| `bool` | `Bool` |
| `list[T]` | `List<T>` |
| `dict[K, V]` | `Map<K, V>` |
| `Optional[T]` | `Option<T>` |
| `tuple[T, ...]` | `List<T>` (or struct) |
| `None` | `None` |
| (no annotation) | `any` (v3.23.0) |

### 2. CLI integration [MEDIUM]

**File:** `mapanare/cli.py`

```bash
mapanare compile main.py           # Python → AST → MIR → LLVM → binary
mapanare compile main.py -o app    # Custom output name
mapanare emit-llvm main.py         # Python → LLVM IR (inspect)
mapanare transpile main.py         # Python → .mn source (human-readable)
mapanare check main.py             # Type-check only, no compilation
```

Detection: if input file ends with `.py`, route through `from_python.py` before
entering the standard pipeline.

### 3. Type inference for untyped locals [MEDIUM]

**File:** `mapanare/from_python.py`

The middle-ground strategy:

1. **Function signatures** — require type annotations (or fall back to `any`)
2. **Local variables** — infer from initializer:
   - `x = 5` → `Int`
   - `name = "hello"` → `String`
   - `items = [1, 2, 3]` → `List<Int>`
   - `result = foo()` → return type of `foo`
   - `x = bar(y)` where `bar` is untyped → `any`
3. **Ambiguous** — emit error with suggestion:
   `"Cannot infer type for 'x' at line 42. Add a type hint: x: int = ..."`

### 4. Class → struct + impl translation [MEDIUM]

**File:** `mapanare/from_python.py`

```python
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance(self, other: 'Point') -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
```

Becomes:

```mn
struct Point {
    x: Float,
    y: Float,
}

impl Point {
    fn distance(self, other: Point) -> Float {
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    }
}
```

Rules:
- `__init__` params (excluding `self`) become struct fields
- Methods become `impl` block functions
- `self.field` → struct field access
- `@staticmethod` → standalone function
- `@classmethod` → not supported (warn)
- Inheritance → not supported in v1 (warn, suggest traits)

### 5. Exception → Result translation [MEDIUM]

**File:** `mapanare/from_python.py`

```python
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("division by zero")
    return a / b

try:
    result = divide(10, 0)
except ValueError as e:
    print(f"Error: {e}")
```

Becomes:

```mn
fn divide(a: Float, b: Float) -> Result<Float, String> {
    if b == 0.0 {
        return Err("division by zero")
    }
    return Ok(a / b)
}

fn main() {
    match divide(10.0, 0.0) {
        Ok(result) => print(result),
        Err(e) => print("Error: " + e),
    }
}
```

This is the biggest semantic shift. The translator must:
- Detect functions that `raise` → return type becomes `Result<T, String>`
- Wrap normal returns in `Ok(...)`
- Convert `raise` to `return Err(...)`
- Convert `try/except` to `match` on the Result

### 6. Python stdlib shim [LOW]

**File:** `mapanare/py_stdlib.py` (new, ~200 lines)

Map common Python stdlib calls to Mapanare equivalents:
- `print()` → `print()`
- `len()` → `len()`
- `str()` → `str()`
- `int()` → `int()`
- `float()` → `float()`
- `range()` → generate `for i in 0..n`
- `enumerate()` → generate index counter + for loop
- `input()` → not supported (warn)
- `open()` → `fs.read_file()` / `fs.write_file()`
- `json.loads/dumps` → `encoding.json` stdlib
- `os.path.*` → `fs.*`
- `math.*` → inline operations or future math stdlib

Anything not in the shim → error with message:
`"Python stdlib 'os.listdir' has no Mapanare equivalent yet. Use mapanare/fs stdlib directly."`

### 7. `.py` → `.mn` transpiler output [LOW]

**File:** `mapanare/from_python.py`

`mapanare transpile main.py` outputs clean `.mn` source — for users who want
to migrate permanently. The output should be idiomatic Mapanare, not a
mechanical translation:
- Use `match` instead of `if isinstance()`
- Use `for x in items` instead of `for i in range(len(items))`
- Use `|>` pipe where natural
- Add comments at translation boundaries: `// was: try/except`

### 8. Unsupported feature diagnostics [MEDIUM]

**File:** `mapanare/from_python.py`

Clear errors for things we can't translate:

| Python feature | Diagnostic |
|----------------|-----------|
| `*args, **kwargs` | "Variadic arguments not supported. Use explicit parameters." |
| Metaclasses | "Metaclasses have no equivalent in Mapanare." |
| `eval()` / `exec()` | "Dynamic code execution not supported in compiled languages." |
| Multiple inheritance | "Use traits instead: `impl TraitA for MyStruct`" |
| Generators (`yield`) | "Use streams instead: `stream { ... }`" |
| Global mutable state | "Global variables not supported. Pass state explicitly." |
| `del` statement | "Memory is managed automatically." |
| Monkey patching | "Cannot modify types at runtime." |

### 9. Test suite [MEDIUM]

**File:** `tests/python_compat/` (new directory)

Test programs — each is a valid Python file that also serves as the test input:

```
tests/python_compat/
    test_basic_types.py       # int, float, str, bool, None
    test_functions.py         # typed functions, default args, lambdas
    test_classes.py           # class → struct+impl
    test_control_flow.py      # if/for/while/match
    test_collections.py       # list, dict, set → List, Map
    test_exceptions.py        # try/except → Result
    test_type_inference.py    # untyped locals, inference rules
    test_any_fallback.py      # untyped params → any
    test_stdlib_shim.py       # range, enumerate, print, len
    test_unsupported.py       # verify diagnostics for unsupported features
    test_transpile_output.py  # .py → .mn output quality
```

### 10. Documentation [LOW]

**File:** `docs/for-python-devs.md` (update existing)

Expand the Python migration guide:
- "Compile your Python" — `mapanare compile main.py`
- Supported subset table
- Type mapping reference
- Common patterns: class→struct, exception→Result, async→agent
- "Gradual migration" — start with `.py`, add `.mn` features, rename when ready

---

## What's NOT in v3.24.0

- **Full Python stdlib** — only basic shims, not comprehensive coverage
- **Dynamic features** — `eval`, `exec`, monkey patching, metaclasses
- **Inheritance** — classes with base classes are rejected (suggest traits)
- **Comprehensions** — list/dict comprehensions (future: desugar to map/filter)
- **Decorators** — ignored with warning (except `@staticmethod`)
- **Type stubs** — no `.pyi` support yet
- **Third-party packages** — `import numpy` doesn't work (future: FFI bridge)

---

## Verification

- [ ] `mapanare compile tests/python_compat/test_basic_types.py` produces working binary
- [ ] `mapanare transpile tests/python_compat/test_classes.py` outputs valid `.mn`
- [ ] Untyped function params become `any`, typed params get real types
- [ ] `let x = 5` in Python infers `Int`, not `any`
- [ ] `try/except` translates to `Result` + `match`
- [ ] Class with `__init__` becomes struct + impl
- [ ] `range(10)` becomes `0..10`
- [ ] Unsupported features produce clear diagnostics
- [ ] All Python compat tests pass
- [ ] `/golden` — all existing tests still pass (no regressions)
- [ ] At least one "real" Python program (50+ lines) compiles and runs correctly
