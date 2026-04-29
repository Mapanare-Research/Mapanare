# v5.16.0 — Phase 0 Spec — String Interpolation Case Matrix

**Date:** 2026-04-29
**Goal:** Lock the Python-bootstrap behavior of `"${expr}"` as the
contract that native `mnc-stage1` must mirror byte-for-byte at
runtime (stdout-identity, modulo IR layout differences between the
two emitters).

The "Python algorithm" section below is the contract for the native
port. Every behavior question goes to "what does the Python
bootstrap do?" — not to "what should an interpolation system do?"

---

## Python algorithm

Three layers, all in `mapanare/parser.py` and `mapanare/lower.py`:

### Lexer (Lark, no Python edits)

`STRING_LIT` is a single token covering the whole `"..."` literal,
including any `${...}` substrings. The Lark grammar does no
interpolation-specific lexing — escapes are preserved verbatim into
the token's raw string (so `\$` survives as `\$`, two characters).

### Parser sugar — `_split_interp` (`mapanare/parser.py:206`)

Operates on the post-quote-strip raw value. Iterates byte by byte:

- `\` followed by `$` is a single escaped sequence; the `$` is
  appended to the literal-segment buffer and the scan advances
  past both characters.
- `$` followed by `{` opens an interpolation site. The literal
  buffer flushes as a `("lit", text)` part. Brace-depth counting
  finds the matching `}` (so `${m["k"]}` and `${f({k:1})}` survive).
  The text between `${` and `}` is recorded as `("expr", text)`.
- Any other character is appended to the literal buffer.

If `_split_interp` finds no unescaped `${`, it returns `None`. The
caller falls back to a plain `StringLiteral(value=_unescape(value))`
— note: `_unescape` does **not** strip `\$`, so `"\${var}"` becomes
the literal text `\${var}`, including the backslash.

### Parser sugar — `_parse_interp_expr` (`mapanare/parser.py:256`)

For each `("expr", text)` part, the text is wrapped in
`fn __interp__() { return <text> }` and re-fed through the full
Lark parser. The expression node is extracted from the synthesized
function's body and pushed into the `InterpString.parts` list.

This trick is what lets every expression form work inside `${...}`
— Ident, Binary, MethodCall, Call, Index, MapLiteral, etc. — using
the same precedence rules as the host expression.

### AST node — `InterpString` (`mapanare/ast_nodes.py:116`)

```python
@dataclass
class InterpString(Expr):
    parts: list[Expr]
```

Parts alternate between `StringLiteral` (literal text) and arbitrary
`Expr` (interpolated). Empty `parts` means an empty literal.

### Lowerer — `_lower_interp_string` (`mapanare/lower.py:3984`)

For each part:

- `StringLiteral` parts pass through unchanged.
- Anything else gets a `Cast(target_type=mir_string())` emitted —
  the emitter routes Cast(Int/Float/Bool → String) to the matching
  `__mn_str_from_*` runtime call (with drop tracking on the fresh
  allocation), and Cast(String → String) collapses to an SSA alias.

The full chain of String-typed values is bundled into one
`InterpConcat` MIR instruction.

### Emitter — `InterpConcat` (`mapanare/emit_llvm_text.py`)

A left-fold of `__mn_str_concat` calls. Each intermediate result is
a fresh allocation tracked for drop-glue.

---

## Case matrix

For each case below the **expected stdout** is what
`python3 -m mapanare emit-llvm | clang | run` produces on Linux.
The contract is that native `mnc-stage1 emit-llvm | clang | run`
produces the same stdout. IR is **not** required to be byte-identical
between the two compilers — the two emitters differ structurally
(Python emits a minimal prelude with only the runtime functions
actually used; native declares the full runtime preamble upfront).

| ID | Source | Expected stdout |
|---|---|---|
| 1 | `print("hello")` | `hello` |
| 2 | `let n: String = "world"; print("hi ${n}")` | `hi world` |
| 3 | `let n: Int = 42; print("n=${n}")` | `n=42` |
| 4 | `let f: Float = 3.14; print("f=${f}")` | `f=3.14` |
| 5 | `let b: Bool = true; print("b=${b}")` | `b=true` |
| 6 | `let s: String = "hi"; print("${s.to_upper()}")` | `HI` |
| 7 | `print("sum=${1 + 2}")` | `sum=3` |
| 8 | `let a: Int = 1; let b: Int = 2; print("${a} and ${b}")` | `1 and 2` |
| 9 | `let x: Int = 7; print("[${x}] done")` | `[7] done` |
| 10 | `print("\${not_a_var}")` | `\${not_a_var}` |

Case 10 is a deliberate "Python is the spec" point: the literal
backslash is preserved in the output because Python's `_unescape`
doesn't handle `\$`. Native mirrors that exactly.

---

## Out of scope

- Format specifiers (`${x:.2f}`, `${x:>10}`) — defer to a future
  We.* arc; multiplies the test matrix.
- Raw-string interp (`r"${not_interp}"`) — SPEC doesn't mention
  raw strings.
- Triple-quoted multi-line interpolation — already works in Python;
  native handling lands transparently if the lexer's TRIPLE_STRING
  produces the same `STRING_LIT` shape (audit deferred).
- Pretty error messages on malformed `${...}` — match Python's
  current quality.
- `mnc fmt --to-terse` of `${  x  }` → `${x}` — out of scope for
  v5.16.0 per PLAN Te.4.F (deferred to v5.17.0 Sh.* prep).

---

## Storage of this document

Goldens 72–80 in `tests/golden/string_interp_*.mn` lock the matrix.
The cross-bootstrap test
`tests/bootstrap/test_string_interp_mirror.py` asserts
stdout-identity between the two compilers on each case.
