# Mapanare v3.25.0 — "Cuaima" (PHP Transpiler)

> Compile typed PHP to native code via Mapanare. `mapanare compile app.php`
> parses PHP, translates to Mapanare `.mn` source text, and runs the full
> compilation pipeline: semantic check, MIR lowering, LLVM IR, native binary.

**Status:** PLANNED
**Estimated scope:** Large (3-4 sessions)
**Breaking:** No
**Prerequisite:** v3.24.0 (Python transpiler establishes the pattern; `any` type from v3.23.0)

---

## Motivation

PHP powers ~77% of server-side web. Mapanare compiles to native code. Bridging
the two means:

1. **Performance** — Typed PHP compiled to native code, no interpreter overhead
2. **Adoption** — PHP developers can try Mapanare without rewriting anything
3. **Gradual migration** — Start with `.php`, add Mapanare features (agents, signals,
   streams) incrementally, eventually rename to `.mn`
4. **Consistency** — Same transpiler architecture as v3.24.0 Python, proving the
   pattern works for multiple source languages

The strategy: accept PHP 7.4+ with type hints at function/property boundaries.
Infer types for local variables where possible. Fall back to `any` (from
v3.23.0) for genuinely dynamic code.

---

## Items

### 1. PHP parser/tokenizer in Python [HIGH]

**File:** `mapanare/php_parser.py` (new, ~400 lines)
**Reporter:** roadmap
**Fix:** Write a custom regex-based tokenizer + recursive descent parser in Python
that handles the core PHP 7.4+ subset. Produces lightweight AST nodes
(`PhpFunction`, `PhpClass`, `PhpMethod`, `PhpIf`, `PhpFor`, `PhpForeach`,
`PhpWhile`, `PhpSwitch`, `PhpReturn`, `PhpAssign`, `PhpCall`, `PhpExpr`,
`PhpArray`, `PhpString`, `PhpVariable`, `PhpBinaryOp`, `PhpUnaryOp`).
Handles `<?php` tag, typed params, return types, nullable types, class
properties, arrow functions, and `match` expressions. Does NOT handle inline
HTML, heredoc, or advanced namespace resolution.

### 2. PHP → `.mn` translator class [HIGH]

**File:** `mapanare/from_php.py` (new, ~500 lines)
**Reporter:** roadmap
**Fix:** Create `PhpTranslator` class mirroring `PythonTranslator` from
`mapanare/from_python.py`. Walks the PHP AST from `php_parser.py` and emits
valid Mapanare `.mn` source text. Handles: function definitions, class →
struct+impl, control flow (if/elseif/else, for, foreach, while, switch→match),
variable declarations (`$x = 5` → `let mut x = 5`), string concatenation
(`.` → `+`), string interpolation (`"$var"` → concat), `echo`/`print` →
`print()`, `new Class(...)` → constructor call, `$this->` → `self.`,
arrow functions, null coalescing (`??`), type casting, and constants.
Public API: `translate_to_mn(php_source, filename) -> str`.

### 3. CLI integration — `.php` auto-detection [MEDIUM]

**File:** `mapanare/cli.py`
**Reporter:** roadmap
**Fix:** Detect `.php` file extension in `compile`, `emit-llvm`, `transpile`, and
`check` commands. Route through `from_php.translate_to_mn()` to produce `.mn`
source text, then feed into the standard pipeline. Same pattern as `.py`
detection added in v3.24.0.

### 4. Type mapping and inference [MEDIUM]

**File:** `mapanare/from_php.py`
**Reporter:** roadmap
**Fix:** Map PHP types to Mapanare types: `int→Int`, `float→Float`,
`string→String`, `bool→Bool`, `array→List<any>` or `Map<String, any>`,
`?Type→Option<Type>`, `void→Void`, `mixed→any`, union types→`any`,
no hint→`any`. Infer local variable types from initializers (int literal→Int,
string literal→String, array literal→List/Map with element type inference).

### 5. Class → struct + impl translation [MEDIUM]

**File:** `mapanare/from_php.py`
**Reporter:** roadmap
**Fix:** Translate PHP classes: typed properties → struct fields, `__construct`
params → field type inference, methods → `impl` block functions, `$this->`
→ `self.`, static methods → standalone functions, interfaces → traits (basic).
Warn on: abstract classes, inheritance (`extends`), `__call`/`__get`/`__set`.

### 6. PHP array heuristics (list vs map detection) [MEDIUM]

**File:** `mapanare/from_php.py`
**Reporter:** roadmap
**Fix:** Detect whether a PHP array is a list or map: `[1, 2, 3]` (no keys) →
`List`, `["a" => 1]` (has `=>`) → `Map`, `$arr[] = $x` → `List.push()`,
`$arr[$stringKey] = $val` → `Map` set. Default to `List<any>` when ambiguous,
with a comment noting the ambiguity.

### 7. String interpolation translation [LOW]

**File:** `mapanare/from_php.py`
**Reporter:** roadmap
**Fix:** Parse PHP double-quoted strings for `$var` and `{$expr}` interpolation
patterns. Split on interpolation boundaries, emit string concatenation with
`str()` wrapping. Single-quoted strings pass through as literals (no
interpolation). Handle basic cases: `$var`, `$obj->field`, `$arr[$key]`.

### 8. Basic PHP stdlib shim [LOW]

**File:** `mapanare/php_stdlib.py` (new, ~200 lines)
**Reporter:** roadmap
**Fix:** Map ~30 common PHP functions to Mapanare equivalents: `strlen→len`,
`count→len`, `array_push→.push()`, `array_pop→.pop()`, `array_map→.map()`,
`array_filter→.filter()`, `implode→.join()`, `explode→.split()`,
`strtolower→.to_lower()`, `strtoupper→.to_upper()`, `trim→.trim()`,
`str_replace→.replace()`, `substr→.substr()`, `intval→int()`,
`floatval→float()`, `strval→str()`, `isset→!= None`, `empty→len() == 0`,
`sqrt/abs/floor/ceil/round→math.*`, `file_get_contents→fs.read_file`,
`file_put_contents→fs.write_file`. Unmapped calls produce clear error message.

### 9. Unsupported feature diagnostics [MEDIUM]

**File:** `mapanare/from_php.py`
**Reporter:** roadmap
**Fix:** Emit clear, actionable diagnostics for unsupported PHP features:
`include`/`require` (suggest imports), `$_GET`/`$_POST`/superglobals (suggest
params), `global` (suggest explicit state), `&$var` references (suggest
returns), `eval`/`exec` (not possible in compiled), `yield` (suggest streams),
`try/catch` (suggest Result), `goto`, inline HTML, `$$var` variable variables,
magic methods, reflection API. Each diagnostic includes the line number and a
concrete Mapanare alternative.

### 10. Test suite (~30 tests) [MEDIUM]

**File:** `tests/php_compat/` (new directory, 11 test files)
**Reporter:** roadmap
**Fix:** Create test files covering: basic types, functions + arrow functions,
classes → struct+impl, control flow (if/for/foreach/while/switch), array
heuristics (list vs map), string interpolation, type inference, `any` fallback,
stdlib shim mapping, unsupported feature diagnostics, transpile output quality.
Each test provides PHP source as a string, runs the translator, and asserts the
output `.mn` is correct. ~30 test cases across 11 files.

---

## What's NOT in v3.25.0

- **Full PHP stdlib** — only ~30 common functions, not the full 1000+ PHP stdlib
- **Inline HTML** — mixed PHP/HTML files are rejected (pure PHP only)
- **Heredoc/nowdoc** — basic string forms only
- **Namespaces** — basic support; complex `use` resolution deferred
- **PHP traits** — could map to Mapanare traits, but deferred for complexity
- **Generators** — `yield`/`yield from` rejected (suggest streams)
- **References** — `&$var` not supported (suggest return values)
- **Dynamic features** — `eval`, `$$var`, `__call`, `extract`, `compact`
- **Inheritance** — `extends` rejected (suggest traits/composition)
- **Error handling** — `try/catch` emitted as comments (suggest Result pattern)
- **Composer packages** — `use Vendor\Package` doesn't resolve (future: FFI bridge)
- **PDO/MySQLi** — database access not mapped (future: db stdlib)

---

## Verification

- [ ] `mapanare compile tests/php_compat/test_basic_types.php` produces working binary
- [ ] `mapanare transpile tests/php_compat/test_classes.php` outputs valid `.mn`
- [ ] Typed PHP function params get real types, untyped params become `any`
- [ ] `$x = 5` infers `Int`, not `any`
- [ ] Class with typed properties becomes struct with typed fields
- [ ] `[1, 2, 3]` detected as `List<Int>`, `["a" => 1]` detected as `Map<String, Int>`
- [ ] String interpolation `"hello $name"` becomes `"hello " + str(name)`
- [ ] `.` (concat) becomes `+`, `===` becomes `==`, `!==` becomes `!=`
- [ ] `echo $x` and `print($x)` both become `print(x)`
- [ ] `foreach ($items as $item)` becomes `for item in items`
- [ ] `switch/case` translates to `match`
- [ ] Unsupported features produce clear diagnostics with Mapanare alternatives
- [ ] All PHP compat tests pass
- [ ] `/golden` — all existing tests still pass (no regressions)
- [ ] At least one "real" PHP program (50+ lines) compiles and runs correctly
