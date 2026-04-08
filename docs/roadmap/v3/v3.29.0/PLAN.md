# Mapanare v3.29.0 — "Morrocoy" (Self-Hosted PHP Transpiler)

> Port the PHP transpiler from Python (`from_php.py`) to self-hosted Mapanare
> (`from_php.mn`). `mnc compile app.php` produces native binaries with zero
> Python dependency.

**Status:** DONE
**Estimated scope:** Large (2-3 sessions)
**Breaking:** No
**Prerequisite:** v3.28.0 (self-hosted Python transpiler proves the pattern)

---

## Motivation

The PHP transpiler (`from_php.py`, 1,811 lines) is the largest Python-based
module in the transpiler system. It includes a custom regex tokenizer and
recursive descent parser because Python has no built-in PHP parser. Porting
to `.mn` makes the entire PHP compilation pipeline self-hosted.

The v3.25.0 review flagged the regex tokenizer as a limitation (Coral M4:
"regex tokenizer, not a parser"). The self-hosted version uses a proper
character-by-character tokenizer, eliminating regex backtracking risks and
improving handling of edge cases (nested string interpolation, heredoc).

The name "Morrocoy" (Venezuelan tortoise) reflects the steady, methodical
nature of porting the largest transpiler module.

---

## Items

### 1. PHP tokenizer in `.mn` [HIGH]

**File:** `mapanare/self/from_php.mn` (new)
**Reporter:** roadmap
**Fix:** Character-by-character tokenizer replacing the Python regex approach.
Must handle:
- `<?php` open tag (required), `?>` close tag (optional)
- PHP keywords: `function`, `class`, `if`, `elseif`, `else`, `for`, `foreach`,
  `while`, `do`, `switch`, `case`, `default`, `return`, `echo`, `print`,
  `new`, `public`, `private`, `protected`, `static`, `const`, `var`,
  `extends`, `implements`, `interface`, `abstract`, `final`, `try`, `catch`,
  `finally`, `throw`, `use`, `namespace`, `match`, `fn`, `null`, `true`,
  `false`, `array`, `isset`, `empty`, `unset`
- Variable tokens: `$identifier`
- String literals: `"..."` (with `$var` and `{$expr}` interpolation), `'...'`
- Operators: multi-char ordered longest-first (`===`, `!==`, `<=>`, `=>`,
  `->`, `??`, `::`, `**`, `...`, `++`, `--`, `+=`, `-=`, `*=`, `/=`, `.=`,
  `==`, `!=`, `<=`, `>=`, `&&`, `||`, `<<`, `>>`)
- Comments: `//`, `#`, `/* ... */`
- Type hints: `int`, `float`, `string`, `bool`, `array`, `?Type`, `void`, `mixed`
- Case-insensitive keywords (PHP standard)

### 2. PHP AST data structures [HIGH]

**File:** `mapanare/self/from_php.mn`
**Reporter:** roadmap
**Fix:** PHP-specific AST nodes:

```mn
enum PhpExpr {
    IntLit(Int), FloatLit(Float), StrLit(String), BoolLit(Bool),
    NullLit, Variable(String), BinOp(PhpExpr, String, PhpExpr),
    UnaryOp(String, PhpExpr), PostfixOp(PhpExpr, String),
    Call(String, List<PhpExpr>), MethodCall(PhpExpr, String, List<PhpExpr>),
    PropertyAccess(PhpExpr, String), StaticAccess(String, String),
    ArrayAccess(PhpExpr, PhpExpr), ArrayLit(List<PhpExpr>),
    MapLit(List<PhpExpr>, List<PhpExpr>), New(String, List<PhpExpr>),
    Ternary(PhpExpr, PhpExpr, PhpExpr), NullCoalesce(PhpExpr, PhpExpr),
    ArrowFn(List<PhpParam>, PhpExpr), Concat(PhpExpr, PhpExpr),
    Cast(String, PhpExpr), Instanceof(PhpExpr, String),
    InterpolatedString(List<PhpExpr>),
}

enum PhpStmt {
    FuncDef(String, List<PhpParam>, String, List<PhpStmt>),
    ClassDef(String, String, List<String>, List<PhpStmt>),
    If(PhpExpr, List<PhpStmt>, List<PhpStmt>),
    For(PhpStmt, PhpExpr, PhpStmt, List<PhpStmt>),
    Foreach(PhpExpr, String, String, List<PhpStmt>),
    While(PhpExpr, List<PhpStmt>), Switch(PhpExpr, List<PhpCase>),
    Return(PhpExpr), Echo(List<PhpExpr>),
    Assign(PhpExpr, PhpExpr), ExprStmt(PhpExpr),
    TryCatch(List<PhpStmt>, List<PhpCatch>, List<PhpStmt>),
    Throw(PhpExpr), Property(String, String, String, PhpExpr),
    Break, Continue,
}
```

### 3. PHP recursive descent parser [HIGH]

**File:** `mapanare/self/from_php.mn`
**Reporter:** roadmap
**Fix:** 13-level precedence climbing parser for PHP expressions:
- Level 0: Assignment (`=`, `+=`, `-=`, etc.)
- Level 1: Ternary (`?:`) and null coalesce (`??`)
- Level 2: Logical OR (`||`, `or`)
- Level 3: Logical AND (`&&`, `and`)
- Level 4: Bitwise OR (`|`)
- Level 5: Bitwise XOR (`^`)
- Level 6: Bitwise AND (`&`)
- Level 7: Equality (`==`, `!=`, `===`, `!==`, `<=>`)
- Level 8: Comparison (`<`, `>`, `<=`, `>=`)
- Level 9: Concatenation (`.`)
- Level 10: Addition (`+`, `-`)
- Level 11: Multiplication (`*`, `/`, `%`, `**`)
- Level 12: Unary (`!`, `-`, `++`, `--`, `(type)`)
- Level 13: Postfix (`++`, `--`, `->`, `::`, `[]`, `()`)

Statement parsing: function, class, if/elseif/else, for (C-style pattern
detection → range), foreach (key => value), while, switch→match, try/catch,
echo/print, return, throw, property declarations.

### 4. Walk: functions and type mapping [HIGH]

**File:** `mapanare/self/from_php.mn`
**Reporter:** roadmap
**Fix:** Walk `PhpFuncDef` nodes:
- Register PHP type mappings with transpiler framework:
  `int→Int`, `float→Float`, `string→String`, `bool→Bool`,
  `array→List<any>`, `?Type→Option<Type>`, `void→Void`,
  `mixed→any`, `object→any`, `callable→any`
- `$this` → `self` (fix from v3.26.0 carried into self-hosted)
- Return types through `translate_type()` (fix from v3.26.0)
- `$variable` → strip `$` prefix

### 5. Walk: classes → struct + impl [MEDIUM]

**File:** `mapanare/self/from_php.mn`
**Reporter:** roadmap
**Fix:** Walk `PhpClassDef` using `transpiler.translate_class_to_struct()`:
- Typed properties → struct fields
- `__construct` params → field type inference
- Methods → impl block with `self` parameter
- `$this->field` → `self.field`
- Static methods → standalone functions
- `extends` → warn unsupported, emit comment
- `implements` → trait impl (basic)

### 6. Walk: arrays, control flow, strings [MEDIUM]

**File:** `mapanare/self/from_php.mn`
**Reporter:** roadmap
**Fix:**
- Array heuristics: `[1,2,3]` → `List`, `["a"=>1]` → `Map`
- C-style `for($i=0; $i<n; $i++)` → `for i in 0..n`
- `foreach($arr as $item)` → `for item in arr`
- `foreach($map as $key => $value)` → `for key in map` (with value warning)
- `switch/case` → `match` expression
- String interpolation: `"hello $name"` → `"hello " + str(name)`
- Null coalescing: `$x ?? $default` → `x.unwrap_or(default)`

### 7. PHP stdlib function mapping [MEDIUM]

**File:** `mapanare/self/from_php.mn`
**Reporter:** roadmap
**Fix:** Register ~30 PHP stdlib shims via `transpiler.translate_stdlib_call()`:
- String: `strlen→len`, `strtolower→.to_lower()`, `strtoupper→.to_upper()`,
  `trim→.trim()`, `substr→.substr()`, `str_replace→.replace()`,
  `explode→.split()`, `implode→.join()`, `strpos→.index_of()`
- Array: `count→len`, `array_push→.push()`, `array_pop→.pop()`,
  `array_map→.map()`, `array_filter→.filter()`, `in_array→.contains()`,
  `array_merge→+` (list concat), `sort→.sort()`, `array_reverse→.reverse()`
- Type: `intval→int()`, `floatval→float()`, `strval→str()`,
  `is_array→typeof() == "List"`, `is_string→typeof() == "String"`,
  `isset→!= None`, `empty→len() == 0`
- Math: `sqrt→math.sqrt`, `abs→math.abs`, `floor→math.floor`,
  `ceil→math.ceil`, `round→math.round`

### 8. Unsupported feature diagnostics [MEDIUM]

**File:** `mapanare/self/from_php.mn`
**Reporter:** roadmap
**Fix:** Use `transpiler.report_unsupported()` for:
- Heredoc/nowdoc strings → "Use regular strings"
- Namespaces → "Use module imports"
- Abstract classes → "Use traits"
- Multiple inheritance (implements) → "Use multiple trait impls"
- Generators/yield → "Use streams"
- Anonymous classes → "Use closures or named structs"
- `__call`/`__get`/`__set` → "Magic methods not supported"

### 9. CLI integration in self-hosted driver [LOW]

**File:** `mapanare/self/main.mn`
**Reporter:** roadmap
**Fix:** Add `.php` extension detection alongside `.py` detection from v3.28.0.
Route through `from_php.translate_php()`.

### 10. Compatibility test suite [MEDIUM]

**File:** `tests/self_hosted_transpiler/test_php.py` (new)
**Reporter:** roadmap
**Fix:** Port the 47 PHP compatibility tests to run through both
`from_php.py` (Python) and `from_php.mn` (self-hosted). Verify output matches.
Cover: functions, classes, arrays, control flow, string interpolation,
type hints, foreach, switch, stdlib shims, end-to-end programs.

---

## What's NOT in This Release

- **No TypeScript or Go.** Those are v3.30.0 and v3.31.0.
- **No heredoc/nowdoc support.** Diagnosed with warning.
- **No namespace support.** Diagnosed with warning.
- **No generator/yield support.** Diagnosed with warning.
- **No changes to Python-based `from_php.py`.** It remains as fallback.

---

## Verification

- [ ] `from_php.mn` compiles through the Python bootstrap emitter
- [ ] `mnc compile fizzbuzz.php` produces correct native binary
- [ ] `mnc compile fibonacci.php` produces correct native binary
- [ ] PHP class → struct + impl with `self.field` (not `this.field`)
- [ ] `function get(): int` → `fn get() -> Int`
- [ ] `isset($x)` → `x != None`
- [ ] `foreach ($arr as $item)` → `for item in arr`
- [ ] `$x ?? "default"` → `x.unwrap_or("default")`
- [ ] 47 compatibility tests pass through both transpiler paths
- [ ] `bash scripts/rebuild.sh` — golden tests still pass
