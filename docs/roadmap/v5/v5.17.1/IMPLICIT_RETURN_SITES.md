# v5.17.1 Sh.D.A — Implicit-Return Sites Survey

**Phase:** 0 (survey)
**Goal:** Identify functions in `mapanare/self/*.mn` where the
trailing `return EXPR` can be dropped to leave bare `EXPR`
(block-form implicit return, SPEC §4.5) or where a single-statement
function can be folded to `fn name(args) -> T = expr` (one-liner
implicit return, v5.15.0 Te.2.D).

**Methodology:** AST-shape walk. For every `fn ... :` block:

1. Strip string literals from body text.
2. Count `\breturn\b` substrings. Must be exactly 1 (no early
   returns inside `if X { return Y }`, no nested returns).
3. The single `return` must be on the LAST non-blank, non-comment
   line of the body, at body indent (4 spaces).
4. Categorize by prelude length: 0 stmts → ONELINER, 1–5 stmts →
   BLOCK_SHORT, >5 stmts → BLOCK_LONG.

## Result

| Category | Count | Cumulative |
|---|---:|---:|
| ONELINER | 109 | 109 |
| BLOCK_SHORT (≤5 prelude stmts) | 88 | 197 |
| BLOCK_LONG (>5 prelude stmts) | 28 | 225 |

### ONELINER — 109 sites (apply all)

Pattern:

```mn
fn llvm_int() -> String:
    return "i64"
```

Rewrites to:

```mn
fn llvm_int() -> String = "i64"
```

Per v5.15.0 Te.2.D the parser lowers `fn name(args) [-> T] = expr`
to `Block([ReturnStmt(expr)])` at parse time — semantically and
MIR-shape identical to the original.

By file:

| File | Count |
|---|---:|
| `emit_llvm_ir.mn` | 35 |
| `parser.mn` | 17 |
| `mir.mn` | 15 |
| `semantic.mn` | 12 |
| `ast.mn` | 8 |
| `emit_llvm.mn` | 8 |
| `lower.mn` | 4 |
| `lexer.mn` | 3 |
| `transpiler.mn` | 3 |
| `mir_opt.mn` | 1 |
| `from_python.mn` | 1 |
| `from_go.mn` | 1 |
| `from_php.mn` | 1 |
| **Total** | **109** |

**Decision: apply all.** One commit per file. The `-> T` annotation
already documents the return type; the `return` keyword adds nothing
the function-init form doesn't say more concisely.

### BLOCK_SHORT — 88 sites (apply most, judgment-heavy)

Pattern:

```mn
fn make_type(name: String) -> TypeInfo:
    let args: List<TypeInfo> = []
    let params: List<TypeInfo> = []
    return new_type_info(name, args, false, params, none, none)
```

Rewrites to:

```mn
fn make_type(name: String) -> TypeInfo:
    let args: List<TypeInfo> = []
    let params: List<TypeInfo> = []
    new_type_info(name, args, false, params, none, none)
```

Per v5.14.0 Te.1 + SPEC §4.5, the bare trailing expression evaluates
as the function's return value when no explicit `return` exists in
the function. Identical AST to original.

By file:

| File | Count |
|---|---:|
| `semantic.mn` | 12 |
| `transpiler.mn` | 11 |
| `emit_llvm.mn` | 10 |
| `parser.mn` | 9 |
| `lower.mn` | 9 |
| `lower_state.mn` | 7 |
| `from_go.mn` | 5 |
| `from_php.mn` | 5 |
| `from_typescript.mn` | 5 |
| `mir.mn` | 4 |
| `mir_opt.mn` | 4 |
| `main.mn` | 3 |
| `from_python.mn` | 3 |
| `ast.mn` | 1 |
| **Total** | **88** |

**Decision: apply per-site judgment.** One commit per file (cluster
mode), gated on stage1 + goldens + fixed-point validation. If the
trailing `return` carries readability weight (e.g., the return
line is hard to recognize as a return without the keyword because
it's a complex method-call chain), keep it.

### BLOCK_LONG — 28 sites (DEFER)

Functions with >5 prelude statements + a single trailing `return`.

By file: `emit_llvm.mn` 11, `lower.mn` 7, `transpiler.mn` 5,
`parser.mn` 2, `lexer.mn` 1, `lower_state.mn` 1, `semantic.mn` 1.

**Decision: SKIP.** Long functions benefit from the explicit
`return` keyword as a punctuation marker — the reader can scan the
function tail and see "this is where it returns." Stripping the
keyword to save one keyword-line in a 30-line function is a
readability loss. Per the PROMPT: "When a function has a name that
doesn't already convey what it builds … the explicit `let r: T = E;
return r` form sometimes documents the return type and value for
the reader."

If a future release decides to revisit these case-by-case, the
candidates are catalogued here.

## Skipped (multi-return)

The strict single-return filter excludes any function that has
additional `return` statements (including those embedded in
brace-form `if X { return Y }` blocks). These cannot use block-form
implicit return without changing semantics — the early returns are
the load-bearing exits, and the trailing `return` is part of the
exit ladder. They stay verbose.

## Risk notes

- **Parser handling of `=`-form fns:** v5.15.0 Te.2.D shipped
  parser support; v5.15.1 Cb.* refreshed bootstrap mirror; v5.17.0
  Sh.* mechanically rewrote the self-host source through these
  parsers. The bootstrap seed at `bootstrap/seed/linux-x86_64/mnc`
  was refreshed from v5.17.0 HEAD. All three pieces (Python parser,
  bootstrap seed, current `mnc-stage1`) handle both forms.

- **Block-form implicit return MIR shape:** The lowerer emits
  `Block([..., ExprStmt(E)])` and `Block([..., ReturnStmt(E)])`
  through the same code path for the function-tail position. Strict
  3-stage fixed point should be preserved by construction.

- **Return-type document loss:** A `fn make_X(...) -> X = ...`
  one-liner still has the `-> X` annotation, so the type is just
  as documented as before. Reader-time loss is purely the visual
  weight of the `return` keyword.

## Apply plan

| Phase | File | Sites | Validation |
|---|---|---:|---|
| Sh.D.B.1 | `emit_llvm_ir.mn` | 35 ONELINER | stage1+goldens+fp |
| Sh.D.B.2 | `mir.mn` | 15 ONELINER + 4 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.3 | `parser.mn` | 17 ONELINER + 9 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.4 | `semantic.mn` | 12 ONELINER + 12 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.5 | `ast.mn` | 8 ONELINER + 1 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.6 | `emit_llvm.mn` | 8 ONELINER + 10 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.7 | `lower.mn` | 4 ONELINER + 9 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.8 | `lexer.mn` | 3 ONELINER | stage1+goldens+fp |
| Sh.D.B.9 | `transpiler.mn` | 3 ONELINER + 11 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.10 | `mir_opt.mn` | 1 ONELINER + 4 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.11 | `lower_state.mn` | 0 ONELINER + 7 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.12 | `from_python.mn` | 1 ONELINER + 3 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.13 | `from_go.mn` | 1 ONELINER + 5 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.14 | `from_php.mn` | 1 ONELINER + 5 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.15 | `from_typescript.mn` | 0 ONELINER + 5 BLOCK_SHORT | stage1+goldens+fp |
| Sh.D.B.16 | `main.mn` | 0 ONELINER + 3 BLOCK_SHORT | stage1+goldens+fp |

Total: 109 ONELINER + 88 BLOCK_SHORT = **197 sites** across **16
commits** (one per module).
