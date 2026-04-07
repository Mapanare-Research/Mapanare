# v3.25.0 — "Cuaima" — PHP Transpiler

> Compile typed PHP to native code: `mapanare compile app.php`.
> PHP source → Mapanare `.mn` source text → existing compilation pipeline.
> Same strategy as v3.24.0 (Python transpiler): parse, translate, compile.
> Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.25.0/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.
> Run `/golden` to ensure no regressions. Run PHP compat tests after every translator change.

---

## Context

v3.24.0 added the Python transpiler — parse `.py` files, translate to `.mn`
source text, and compile through the standard pipeline. v3.25.0 applies the
same strategy to PHP: parse `.php` files, translate to `.mn` source, and let
the existing compiler handle the rest.

PHP does not have a Python-level `ast` module, so we write a custom PHP parser
in Python (~400 lines) that handles the core PHP 7.4+ subset. This parser
tokenizes PHP source using regex patterns matching PHP's token structure, then
builds a lightweight AST that the translator walks to emit `.mn` source.

**Current version:** 3.24.0
**Target version:** 3.25.0

---

## What Needs Doing

### 1. PHP Parser/Tokenizer in Python [HIGH — do first, largest item]

**File:** `mapanare/php_parser.py` (new, ~400 lines)

Write a custom PHP tokenizer + recursive descent parser in Python. This is NOT
a full PHP parser — it handles the core subset that maps cleanly to Mapanare.

**Tokenizer** — regex-based, handles:
- Keywords: `function`, `class`, `if`, `elseif`, `else`, `for`, `foreach`,
  `while`, `switch`, `case`, `default`, `return`, `break`, `continue`,
  `echo`, `print`, `new`, `public`, `private`, `protected`, `static`,
  `const`, `null`, `true`, `false`, `match` (PHP 8.0)
- Variables: `$name` (strip the `$` during translation)
- Type hints: `int`, `float`, `string`, `bool`, `array`, `?Type` (nullable)
- Operators: `+`, `-`, `*`, `/`, `%`, `**`, `.` (concat), `==`, `===`,
  `!=`, `!==`, `<`, `>`, `<=`, `>=`, `&&`, `||`, `!`, `??`, `?:`
- String literals: single-quoted, double-quoted (with `$var` interpolation),
  heredoc/nowdoc (basic)
- Numbers: integers, floats
- Arrays: `[1, 2, 3]`, `["key" => "value"]`, `array(...)` syntax
- Arrow functions: `fn($x) => $x + 1` (PHP 7.4)
- Type unions: `int|string` (PHP 8.0, map to `any`)
- Return types: `function foo(): int`
- Nullable types: `?int` → `Option<Int>`

**Parser** — recursive descent, produces lightweight AST nodes:
- `PhpFunction`, `PhpClass`, `PhpMethod`, `PhpIf`, `PhpFor`, `PhpForeach`,
  `PhpWhile`, `PhpSwitch`, `PhpReturn`, `PhpAssign`, `PhpCall`, `PhpExpr`,
  `PhpArray`, `PhpString`, `PhpVariable`, `PhpBinaryOp`, `PhpUnaryOp`

The `<?php` opening tag is consumed and ignored. Inline HTML is not supported
(emit diagnostic). Closing `?>` is optional and ignored.

### 2. PHP → `.mn` Translator [HIGH — second item]

**File:** `mapanare/from_php.py` (new, ~500 lines)

Walk the PHP AST from `php_parser.py` and emit Mapanare source text, following
the exact same pattern as `from_python.py` (`PythonTranslator` class).

Key mappings:

| PHP | Mapanare |
|-----|----------|
| `function foo(int $x): string` | `fn foo(x: Int) -> String` |
| `class User { public string $name; }` | `struct User { name: String }` |
| `class User { public function greet(): string }` | `impl User { fn greet(self) -> String }` |
| `if ($x > 0) { } elseif (...) { } else { }` | `if x > 0 { } else if ... { } else { }` |
| `for ($i = 0; $i < 10; $i++)` | `for i in 0..10` |
| `foreach ($items as $item)` | `for item in items` |
| `foreach ($map as $key => $value)` | `for key, value in map` |
| `while ($cond) { }` | `while cond { }` |
| `switch ($x) { case 1: ... break; }` | `match x { 1 => ... }` |
| `$x = 5` | `let mut x = 5` |
| `$items = [1, 2, 3]` | `let mut items = [1, 2, 3]` |
| `$map = ["a" => 1, "b" => 2]` | `let mut map = {"a": 1, "b": 2}` |
| `"hello $name"` | `"hello " + str(name)` |
| `"hello {$name}"` | `"hello " + str(name)` |
| `$a . $b` (string concat) | `a + b` |
| `echo $x` / `print($x)` | `print(x)` |
| `(int)$x` | `int(x)` |
| `$x === $y` | `x == y` |
| `$x !== $y` | `x != y` |
| `$x ?? $default` | `x` (with Option unwrap, or comment) |
| `new User("Juan")` | `User("Juan")` (constructor call) |
| `fn($x) => $x + 1` | `(x) => x + 1` |
| `null` | `None` |
| `true`/`false` | `true`/`false` |
| `return $x` | `return x` |
| `const PI = 3.14` | `let PI: Float = 3.14` |

**Type mapping:**

| PHP type | Mapanare type |
|----------|---------------|
| `int` | `Int` |
| `float` | `Float` |
| `string` | `String` |
| `bool` | `Bool` |
| `array` (numeric keys) | `List<any>` |
| `array` (string keys) | `Map<String, any>` |
| `?Type` (nullable) | `Option<Type>` |
| `void` | `Void` |
| `mixed` | `any` |
| `int\|string` (union) | `any` |
| (no type hint) | `any` |

### 3. CLI Integration [MEDIUM]

**File:** `mapanare/cli.py`

```bash
mapanare compile app.php           # PHP → .mn → MIR → LLVM → binary
mapanare compile app.php -o app    # Custom output name
mapanare emit-llvm app.php         # PHP → LLVM IR (inspect)
mapanare transpile app.php         # PHP → .mn source (human-readable)
mapanare check app.php             # Type-check only, no compilation
```

Detection: if input file ends with `.php`, route through `from_php.py` first,
producing `.mn` source text, then feed into the standard pipeline.

### 4. Type Mapping and Inference [MEDIUM]

**File:** `mapanare/from_php.py`

PHP 7.4+ has type hints at function boundaries. Strategy:

1. **Function signatures** — use declared types, fall back to `any` if missing
2. **Property types** — PHP 7.4 typed properties: `public int $age` → `age: Int`
3. **Local variables** — infer from initializer:
   - `$x = 5` → `Int`
   - `$name = "hello"` → `String`
   - `$items = [1, 2, 3]` → `List<Int>`
   - `$map = ["a" => 1]` → `Map<String, Int>`
   - `$result = foo()` → return type of `foo`
   - `$x = bar($y)` where `bar` is untyped → `any`
4. **Ambiguous** — emit error:
   `"Cannot infer type for '$x' at line 42. Add a type hint."`

### 5. Class → Struct + Impl [MEDIUM]

**File:** `mapanare/from_php.py`

```php
class Point {
    public float $x;
    public float $y;

    public function __construct(float $x, float $y) {
        $this->x = $x;
        $this->y = $y;
    }

    public function distance(Point $other): float {
        return sqrt(($this->x - $other->x) ** 2 + ($this->y - $other->y) ** 2);
    }
}
```

Becomes:

```mn
struct Point {
    x: Float,
    y: Float,
}

impl Point {
    fn distance(self, other: Point) -> Float {
        return (((self.x - other.x) ** 2) + ((self.y - other.y) ** 2)) ** 0.5
    }
}
```

Rules:
- Typed properties → struct fields
- `__construct` params → used for type inference on untyped fields
- Methods (excluding `__construct`) → `impl` block functions
- `$this->field` → `self.field`
- `$this->method()` → `self.method()`
- `static function` → standalone function
- `abstract class` → not supported (warn, suggest traits)
- `interface` → translate to trait
- Inheritance (`extends`) → not supported in v1 (warn, suggest traits)
- Visibility modifiers (`public`/`private`/`protected`) → ignored (all public in Mapanare)

### 6. PHP Array Heuristics (List vs Map) [MEDIUM]

**File:** `mapanare/from_php.py`

PHP arrays serve as both lists and maps. Detection heuristics:

- `[1, 2, 3]` — all values, no keys → `List<Int>`
- `["a" => 1, "b" => 2]` — has `=>` keys → `Map<String, Int>`
- `array(1, 2, 3)` — `array()` syntax, no keys → `List<Int>`
- `array("a" => 1)` — `array()` with keys → `Map<String, Int>`
- `$arr[] = $x` — append syntax → treat as `List`, emit `.push(x)`
- `$arr[$key] = $val` — index assignment:
  - If `$key` is string → `Map`
  - If `$key` is integer → `List` (index set)

When ambiguous, default to `List<any>` and emit a comment:
`// NOTE: PHP array type ambiguous, defaulting to List`

### 7. String Interpolation Translation [LOW]

**File:** `mapanare/from_php.py`

PHP double-quoted strings support `$var` and `{$expr}` interpolation:

- `"hello $name"` → `"hello " + str(name)`
- `"value is {$obj->field}"` → `"value is " + str(obj.field)`
- `"count: {$arr[0]}"` → `"count: " + str(arr[0])`
- `'no interpolation'` → `"no interpolation"` (single-quote = literal)

The translator splits the string on interpolation boundaries and emits
concatenation with `str()` wrapping for non-string expressions.

### 8. Basic Stdlib Shim [LOW]

**File:** `mapanare/php_stdlib.py` (new, ~200 lines)

Map common PHP functions to Mapanare equivalents:

- `echo $x` / `print($x)` → `print(x)`
- `strlen($s)` → `len(s)`
- `count($arr)` → `len(arr)`
- `array_push($arr, $x)` → `arr.push(x)`
- `array_pop($arr)` → `arr.pop()`
- `array_merge($a, $b)` → `a + b` (list concat)
- `array_map(fn, $arr)` → `arr.map(fn)`
- `array_filter($arr, fn)` → `arr.filter(fn)`
- `in_array($val, $arr)` → `arr.contains(val)`
- `implode($sep, $arr)` → `sep.join(arr)`
- `explode($sep, $s)` → `s.split(sep)`
- `strtolower($s)` → `s.to_lower()`
- `strtoupper($s)` → `s.to_upper()`
- `trim($s)` → `s.trim()`
- `str_replace($search, $replace, $s)` → `s.replace(search, replace)`
- `substr($s, $start, $len)` → `s.substr(start, len)`
- `intval($x)` / `(int)$x` → `int(x)`
- `floatval($x)` / `(float)$x` → `float(x)`
- `strval($x)` / `(string)$x` → `str(x)`
- `isset($x)` → `x != None` (approximate)
- `empty($x)` → `len(x) == 0` (approximate)
- `var_dump($x)` → `print(x)` (approximate)
- `json_encode($x)` → comment, suggest encoding stdlib
- `json_decode($s)` → comment, suggest encoding stdlib
- `file_get_contents($path)` → `fs.read_file(path)`
- `file_put_contents($path, $data)` → `fs.write_file(path, data)`
- `sqrt($x)` / `abs($x)` / `floor($x)` / `ceil($x)` / `round($x)` → `math.*`
- `max($a, $b)` / `min($a, $b)` → inline or math stdlib

Anything not in the shim → error:
`"PHP function 'preg_match' has no Mapanare equivalent yet."`

### 9. Unsupported Feature Diagnostics [MEDIUM]

**File:** `mapanare/from_php.py`

Clear errors for things we cannot translate:

| PHP feature | Diagnostic |
|-------------|-----------|
| `include`/`require`/`require_once` | "Use Mapanare module imports instead: `import module`" |
| `$_GET`/`$_POST`/`$_SERVER`/`$_SESSION` | "Superglobals not supported. Pass data as explicit function parameters." |
| `global $var` | "Global variables not supported. Pass state explicitly." |
| `&$var` (references) | "Pass-by-reference not supported. Use return values instead." |
| `eval()` / `exec()` | "Dynamic code execution not supported in compiled languages." |
| `namespace` | "Basic namespace support only. Complex namespace resolution not supported." |
| `trait` (PHP traits) | "PHP traits → Mapanare traits is planned but not yet implemented." |
| `yield` / `yield from` | "Generators not supported. Use streams instead: `stream { ... }`" |
| `try/catch/finally` | "Use Result types instead: `Result<T, String>` + `match`" |
| `throw new Exception(...)` | "Use `return Err(msg)` instead of throwing exceptions." |
| `goto` | "goto is not supported." |
| Inline HTML | "Mixed PHP/HTML not supported. Use pure PHP files." |
| `extract()`/`compact()` | "Dynamic variable creation not supported in compiled languages." |
| `$$var` (variable variables) | "Variable variables not supported." |
| `__call`/`__get`/`__set` (magic methods) | "Magic methods not supported. Define explicit methods." |
| `ReflectionClass` / reflection API | "Runtime reflection not available in compiled code." |

### 10. Test Suite [MEDIUM]

**Directory:** `tests/php_compat/` (new)

Test programs — each contains PHP source as string literals fed to the translator:

```
tests/php_compat/
    test_basic_types.py       # int, float, string, bool, null
    test_functions.py         # typed functions, default args, arrow functions
    test_classes.py           # class → struct+impl, properties, constructor
    test_control_flow.py      # if/elseif/else, for, foreach, while, switch
    test_arrays.py            # list vs map heuristics, array functions
    test_strings.py           # interpolation, concatenation, single/double quotes
    test_type_inference.py    # untyped locals, inference rules
    test_any_fallback.py      # untyped params → any
    test_stdlib_shim.py       # strlen, count, array_push, echo, etc.
    test_unsupported.py       # verify diagnostics for unsupported features
    test_transpile_output.py  # .php → .mn output quality
```

---

## Verification Checklist

```bash
# 1. Basic PHP file compiles
cat > /tmp/test.php << 'EOF'
<?php
function main(): void {
    echo "hello from php\n";
}
EOF
mapanare compile /tmp/test.php -o /tmp/test && /tmp/test

# 2. Typed PHP with classes
mapanare compile tests/php_compat/test_classes.php -o /tmp/cls && /tmp/cls

# 3. Transpile output is valid .mn
mapanare transpile tests/php_compat/test_basic_types.php > /tmp/out.mn
mapanare check /tmp/out.mn

# 4. Untyped code uses any, not crash
mapanare compile tests/php_compat/test_any_fallback.php

# 5. Unsupported features produce diagnostics
mapanare check tests/php_compat/test_unsupported.php 2>&1 | grep -c "not supported"

# 6. Array heuristics: list vs map correctly detected
mapanare transpile tests/php_compat/test_arrays.php | grep -E "(List|Map)"

# 7. String interpolation translated correctly
mapanare transpile tests/php_compat/test_strings.php | grep "str("

# 8. Golden tests unaffected
/golden

# 9. Full pytest
pytest tests/ -v -n auto
```

---

## Version Bump

1. Run `/bump-version` to 3.25.0
2. CHANGELOG.md:
   - **Added:** PHP transpiler — `mapanare compile app.php` compiles typed PHP to native
   - **Added:** `mapanare transpile app.php` outputs idiomatic `.mn` source
   - **Added:** PHP stdlib shim (echo, strlen, count, array_push, implode, explode, etc.)
   - **Added:** Class → struct+impl, PHP array → List/Map heuristic detection
   - **Added:** 11 PHP compatibility tests
3. Commit: `v3.25.0: "Cuaima" — PHP transpiler, compile .php to native`
