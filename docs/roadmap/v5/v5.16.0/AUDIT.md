# v5.16.0 — Phase 0 Audit

**Date:** 2026-04-29
**Goal:** Document the v5.15.1-HEAD divergence that v5.16.0 closes
plus prerequisite checks for the lexer / parser / lowerer port.

---

## Baseline state

- VERSION = `5.15.1`.
- Goldens through `mnc-stage1`: **71/71 PASS**.
- Strict 3-stage fixed point: holds (228,630 lines / 0 diff).
- `tests/bootstrap/test_comprehension_mirror.py`: 10/10 PASS.

## Failure shape on `mnc-stage1`

```
$ cat /tmp/case_var.mn
fn main() {
    let n: String = "world"
    print("hi ${n}")
}
$ mapanare/self/mnc-stage1 emit-llvm /tmp/case_var.mn -o /tmp/x.ll
/tmp/case_var.mn:0:0: error: Undefined variable 'n}'
```

Root cause: pre-existing `split_interp_parts` in
`mapanare/self/parser.mn:1919` is half-finished:

1. `s.substr(i + 2, j)` passes the absolute end-index `j` as the
   `count` argument, but the runtime `__mn_str_substr(s, start,
   count)` takes a **count**. With `${n}` at byte offset 3, the
   call extracts characters `[5, 5+6) = "n}"` instead of just `"n"`.
2. After finding the first `${...}` site, the function returns
   immediately — it can never produce more than one expression
   part, so `"${a} ${b}"` is also broken.
3. The expression text is wrapped in `Expr::Ident(expr_text)`
   verbatim, so any non-bare-identifier interpolation
   (`${a + b}`, `${s.to_upper()}`, `${m["k"]}`) errors during
   semantic resolution.
4. The lexer's `\$` escape strips the backslash, so the parser
   can't distinguish escaped `\${` from real interpolation —
   `"\${not_a_var}"` errors with "Undefined variable
   'not_a_var}'" instead of printing the literal text.

Even with all four fixed, the AST shape (`Binary("+", a, b)`) chain
emitted by the original code mismatches the Python lowerer's output,
which uses a dedicated `InterpString` AST node lowered through
`InterpConcat` MIR. The Binary chain also doesn't auto-coerce
non-string operands, breaking `"n=${n}"` for any `n` not already a
String. Wrapping each non-StringLit part in `Expr::Call(Ident("str"),
[expr])` works for primitives but triggers a double-free in the
existing emit_builtin_tostring's String-input path (`emit_copy`
aliases the source buffer, then both the str() result and the
underlying source-tracker call `__mn_str_free` on the same memory
at function exit).

## Resolution chosen

Mirror Python's structure exactly:

- New `Expr::InterpString(List<Expr>)` AST node parallel to
  Python's `InterpString`.
- New `lower_interp_string` in `mapanare/self/lower.mn` mirroring
  `mapanare/lower.py::_lower_interp_string` line-for-line: each
  non-StringLit part gets a `Cast(target=mir_string)`; the chain
  bundles into a single `InterpConcat` MIR instruction.
- Extend `emit_cast` to handle X→String for Int / Float / Bool /
  String — emits `__mn_str_from_*` (with drop tracking) for
  primitives, alias-only `emit_copy` for String. Mirrors Python
  `_do_cast`.
- Existing `emit_interp_concat` handles the multi-part fold
  (left-to-right `__mn_str_concat`); fixed a pre-existing bug
  where the last concat wrote to `dn.cN` instead of the dest
  itself, leaving downstream uses of `dest` undefined.

## Native side rewrite of `split_interp_parts`

The original char-by-char buffer (`lit = lit + ch`) hit a
bootstrap-lower String concat bug: trailing literal segments after
an interp site emitted garbage bytes (a 6-byte `"] done"` literal
came out as `\01\00\00\00\00\00`). Replaced with a position-tracking
scan that captures pending literal segments via `s.substr(seg_start,
i - seg_start)` once at flush time. Same algorithm shape as Python's
`_split_interp` but routed around the bootstrap concat issue.

## Lexer change

`scan_string` now preserves `\$` literally as the two-character
sequence `\` + `$` instead of collapsing it to `$`. Mirrors Python
behavior: `_split_interp` operates on raw STRING_LIT content with
`\$` still in place.

## Validation

- All 10 Phase 0 case-matrix entries produce stdout matching the
  Python bootstrap.
- Goldens 72–80 (eight new `string_interp_*.mn`) plus existing
  71 → 80/80 PASS.
- Cross-bootstrap test
  `tests/bootstrap/test_string_interp_mirror.py` 10/10 PASS.
- Strict 3-stage fixed point preserved: 228,630 lines / 0 diff
  between stage2.ll and stage3.ll (unchanged from v5.15.1).
- `mypy mapanare/ runtime/` clean.

## Prerequisite verifications (passed before Phase 2 started)

- `tokenize` and `parse_expr` are accessible from inside
  `mapanare/self/parser.mn` (both already in scope).
- `Instruction::InterpConcat` and `emit_interp_concat` exist in
  the native compiler but were never emitted from the lowerer
  before v5.16.0 — `mir_opt.mn` already has the rename / track
  cases for it.
- `__mn_str_from_int` / `_float` / `_bool` are declared in the
  emitter's runtime preamble; no new C-runtime exports needed.
