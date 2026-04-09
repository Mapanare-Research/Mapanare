# Mapanare v3.28.0 — "Danta" (Self-Hosted Python Transpiler)

> Port the Python transpiler from Python (`from_python.py`) to self-hosted
> Mapanare (`from_python.mn`). The compiler can now compile Python source to
> native code without any Python tooling in the pipeline.

**Status:** DONE
**Estimated scope:** Large (2-3 sessions)
**Breaking:** No
**Prerequisite:** v3.27.0 (transpiler framework provides shared helpers)

---

## Motivation

The Python transpiler currently lives in `mapanare/from_python.py` (928 lines)
and depends on Python's `ast` module for parsing. This means compiling `.py`
files requires a Python runtime — which defeats the "compile everything to
native" promise.

Porting to `from_python.mn` means `mnc compile app.py` works with zero Python
dependency. The transpiler framework from v3.27.0 handles type mapping,
class→struct, exception→Result, and stdlib shims. This module only needs to
implement the Python-specific lexer, parser, and AST walk.

The name "Danta" (Venezuelan tapir) bridges two worlds — like the transpiler
bridges Python and Mapanare.

---

## Architecture

```
from_python.mn (~800 lines)
    │
    ├─ lex_python(source: String) -> List<Token>
    │   └─ Python keyword table, indent tracking, string literals
    │
    ├─ parse_python(tokens: List<Token>) -> PyModule
    │   └─ Recursive descent: def, class, if/elif/else, for, while, return,
    │      assign, call, lambda, f-string, import, try/except
    │
    └─ walk_python(node: PyNode) -> String
        └─ PyFuncDef → FnDef (via transpiler.translate_type)
           PyClassDef → struct+impl (via transpiler.translate_class_to_struct)
           PyTryExcept → Result (via transpiler.translate_exception_to_result)
           PyFormatString → concat chain
           PyLambda → arrow function
           PyImport → import statement
```

---

## Items

### 1. Python lexer in `.mn` [HIGH]

**File:** `mapanare/self/from_python.mn` (new)
**Reporter:** roadmap
**Fix:** Write a character-by-character tokenizer for Python 3.10+ syntax.
Must handle:
- Indentation tracking (INDENT/DEDENT tokens via indent stack)
- Keywords: `def`, `class`, `if`, `elif`, `else`, `for`, `while`, `return`,
  `import`, `from`, `as`, `try`, `except`, `finally`, `raise`, `with`,
  `lambda`, `and`, `or`, `not`, `in`, `is`, `None`, `True`, `False`,
  `pass`, `break`, `continue`, `yield`, `async`, `await`, `global`,
  `nonlocal`, `del`, `assert`
- String literals: `"..."`, `'...'`, `f"..."`, `"""..."""`, `'''...'''`
- Operators: `+`, `-`, `*`, `/`, `//`, `**`, `%`, `==`, `!=`, `<`, `>`,
  `<=`, `>=`, `=`, `+=`, `-=`, `*=`, `/=`, `->`, `:`, `.`, `,`, `(`, `)`,
  `[`, `]`, `{`, `}`
- Comments: `#` to end of line
- Type annotations: `x: int`, `-> str`, `Optional[T]`, `list[T]`, `dict[K,V]`

### 2. Python AST data structures [HIGH]

**File:** `mapanare/self/from_python.mn`
**Reporter:** roadmap
**Fix:** Define Python-specific AST nodes as enums/structs:

```mn
enum PyExpr {
    IntLit(Int),
    FloatLit(Float),
    StrLit(String),
    BoolLit(Bool),
    NoneLit,
    Name(String),
    BinOp(PyExpr, String, PyExpr),
    UnaryOp(String, PyExpr),
    Call(PyExpr, List<PyExpr>),
    Attribute(PyExpr, String),
    Index(PyExpr, PyExpr),
    ListLit(List<PyExpr>),
    DictLit(List<PyExpr>, List<PyExpr>),
    Lambda(List<String>, PyExpr),
    FString(List<PyExpr>),
    Ternary(PyExpr, PyExpr, PyExpr),
}

enum PyStmt {
    FuncDef(String, List<PyParam>, String, List<PyStmt>),
    ClassDef(String, List<String>, List<PyStmt>),
    If(PyExpr, List<PyStmt>, List<PyStmt>),
    For(String, PyExpr, List<PyStmt>),
    While(PyExpr, List<PyStmt>),
    Return(PyExpr),
    Assign(String, String, PyExpr),
    AugAssign(String, String, PyExpr),
    ExprStmt(PyExpr),
    Import(String, String),
    TryExcept(List<PyStmt>, List<PyCatch>, List<PyStmt>),
    Raise(PyExpr),
    Pass,
    Break,
    Continue,
}
```

### 3. Python parser [HIGH]

**File:** `mapanare/self/from_python.mn`
**Reporter:** roadmap
**Fix:** Recursive descent parser for the Python subset. Handles:
- Function definitions with type annotations and defaults
- Class definitions with `__init__` field extraction
- Control flow: if/elif/else, for, while, break, continue
- Assignments with type annotations
- Return statements
- Import statements
- Try/except/finally blocks
- Lambda expressions
- f-string parsing into concat chains
- Operator precedence (13 levels, matching Python)

### 4. Walk: functions and type mapping [HIGH]

**File:** `mapanare/self/from_python.mn`
**Reporter:** roadmap
**Fix:** Walk `PyFuncDef` nodes:
- Map Python types to Mapanare via `transpiler.translate_type()`:
  `int→Int`, `float→Float`, `str→String`, `bool→Bool`,
  `list[T]→List<T>`, `dict[K,V]→Map<K,V>`, `Optional[T]→Option<T>`,
  `None type→Void`, no annotation→`any`
- Map `async def` → `agent` definition
- Map `await` → `sync` expression
- First assignment to a variable → `let mut`; subsequent → reassignment

### 5. Walk: classes → struct + impl [MEDIUM]

**File:** `mapanare/self/from_python.mn`
**Reporter:** roadmap
**Fix:** Walk `PyClassDef` nodes using `transpiler.translate_class_to_struct()`:
- Extract fields from `__init__` parameter annotations and `self.x = ...`
- Map methods to `impl` block (skip `__init__`, `__str__`, `__repr__`)
- Map `@staticmethod` → standalone function
- Map `@property` → getter method
- Warn on: `__call__`, `__getattr__`, metaclasses, multiple inheritance

### 6. Walk: exceptions → Result [MEDIUM]

**File:** `mapanare/self/from_python.mn`
**Reporter:** roadmap
**Fix:** Walk `PyTryExcept` using `transpiler.translate_exception_to_result()`:
- `raise ValueError("msg")` → `return Err("msg")`
- `try: ... except ValueError as e: ...` → `match result { Ok(val) => ..., Err(e) => ... }`
- Unsupported: `finally` (emit as unconditional suffix with warning)

### 7. Walk: f-strings, lambdas, comprehensions [MEDIUM]

**File:** `mapanare/self/from_python.mn`
**Reporter:** roadmap
**Fix:**
- f-strings: `f"hello {name}"` → `"hello " + str(name)`
- Lambdas: `lambda x: x + 1` → `(x) => x + 1`
- List comprehensions: `[x*2 for x in items]` → `items.map((x) => x * 2)`
- Dict comprehensions: emit with `// WARNING: dict comprehension approximated`
- Decorators: emit as `// WARNING: decorator @name ignored`

### 8. Stdlib method mapping [MEDIUM]

**File:** `mapanare/self/from_python.mn`
**Reporter:** roadmap
**Fix:** Register Python stdlib shims via `transpiler.translate_stdlib_call()`:
- `append→push`, `extend→push` (with loop), `pop→pop`
- `upper→to_upper`, `lower→to_lower`, `strip→trim`
- `startswith→starts_with`, `endswith→ends_with`
- `find→index_of`, `replace→replace`, `split→split`, `join→join`
- `len→len`, `str→str`, `int→int`, `float→float`
- `range(n)→0..n`, `range(a,b)→a..b`
- `print→print`, `isinstance→typeof`

### 9. CLI integration [MEDIUM]

**File:** `mapanare/self/main.mn`
**Reporter:** roadmap
**Fix:** In the self-hosted compiler driver, detect `.py` file extension and
route through `from_python.translate_python()` before the normal pipeline.
Mirror the `_read_source()` auto-detection from `cli.py`.

### 10. Compatibility test suite [MEDIUM]

**File:** `tests/self_hosted_transpiler/test_python.py` (new)
**Reporter:** roadmap
**Fix:** Port the 44 Python compatibility tests to also run through the
self-hosted transpiler. Each test provides Python source, runs it through
both `from_python.py` (Python) and `from_python.mn` (self-hosted via mnc),
and asserts the output matches. Focus on: functions, classes, control flow,
type annotations, f-strings, exceptions, lambdas, and stdlib methods.

---

## What's NOT in This Release

- **No PHP self-hosted transpiler.** That is v3.29.0.
- **No TypeScript or Go.** Those are v3.30.0 and v3.31.0.
- **No Python's `ast` module replacement for edge cases.** The self-hosted
  transpiler handles the common subset (typed functions, classes, control flow).
  Decorators, generators, metaclasses, `*args/**kwargs`, and advanced typing
  (`TypeVar`, `Protocol`, `Literal`) are diagnosed with warnings.
- **No changes to the Python-based `from_python.py`.** It continues to work
  as the fallback for the Python bootstrap compiler.

---

## Verification

- [ ] `from_python.mn` compiles through the Python bootstrap emitter
- [ ] `mnc compile fizzbuzz.py` produces correct native binary
- [ ] `mnc compile fibonacci.py` produces correct native binary
- [ ] Python class with typed methods → struct + impl with correct types
- [ ] `try/except` → Result match pattern
- [ ] f-string → concat chain
- [ ] `lambda x: x + 1` → `(x) => x + 1`
- [ ] Unannotated parameters → `any` type
- [ ] 44 compatibility tests pass through both transpiler paths
- [ ] `bash scripts/rebuild.sh` — golden tests still pass
