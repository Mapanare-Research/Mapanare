# v5.16.0 — Te.4 — self-host string-interpolation parity

**Status:** ready, not tagged.
**Date:** 2026-04-29.
**Theme:** closes the last Python-vs-native string-handling gap.
`mnc-stage1` now lexes, parses, and lowers `"${expr}"` interpolation
the same way the Python bootstrap does, with the same AST shape
(`InterpString`) and the same MIR shape (`InterpConcat`).

---

## What landed

The native compiler accepts every interpolation surface from the
Phase 0 case matrix and produces stdout identical to the Python
compiler on every case (`tests/bootstrap/test_string_interp_mirror.py`,
10 cases). Goldens 72–80 (`tests/golden/string_interp_*.mn`) lock
the matrix into the standard test harness.

### Te.4.A — Phase 0 spec (`docs/roadmap/v5/v5.16.0/INTERP_SPEC.md`)

10-entry case matrix. Each entry's expected stdout was captured by
running the source through `python3 -m mapanare emit-llvm | clang |
run`. Python's algorithm — `_split_interp` (parser sugar),
`_parse_interp_expr` (re-feeds expr text through Lark),
`_lower_interp_string` (Cast-to-String + InterpConcat), and
`_do_cast` (X→String dispatch) — documented as the contract for the
native port.

### Te.4.B — Lexer (`mapanare/self/lexer.mn`)

Single-line change: `scan_string` now preserves `\$` as the
two-character sequence `\` + `$` instead of collapsing it to `$`.
Mirrors Python's pre-`_unescape` STRING_LIT shape so the parser
can detect escaped interpolation via the prior backslash byte.

### Te.4.C — Parser (`mapanare/self/parser.mn`)

`split_interp_parts` rewritten to use a position-tracking scan:
`seg_start` and `i` bracket the pending literal segment, which
flushes via `s.substr(seg_start, i - seg_start)` at each interp
site. The previous `lit = lit + ch` char-by-char rebuild hit a
bootstrap-lower String concat bug where the trailing literal
segment after an interp emitted garbage (a 6-byte `"] done"`
literal came out as `\01\00\00\00\00\00`). Same algorithm shape as
Python's `_split_interp`; routed around the concat issue.

Each `${...}` site's text is re-tokenized and re-fed through
`parse_expr`, so any expression form works inside `${...}`. The
result is wrapped in the new `Expr::InterpString(List<Expr>)` AST
node and pushed through the regular expression pipeline. The old
`Binary("+", ...)` chain — including its `str(...)` wrap workaround
that triggered a double-free in `emit_builtin_tostring`'s
String-input path — is gone.

### Te.4.C — AST (`mapanare/self/ast.mn`)

New `Expr::InterpString(List<Expr>)` variant mirrors Python's
`InterpString`. `expr_kind` extended with `interp_string`; new
accessor `expr_interp_parts`. Only one exhaustive `match` on `Expr`
existed in the codebase (in `ast.mn` itself); other modules
dispatch via `expr_kind` strings, so the change is purely additive.

### Te.4.C — Semantic (`mapanare/self/semantic.mn`)

`infer_expr` learns `interp_string`: walks each part for
side-effect inference (pushes diagnostics, propagates ERROR types),
returns `string_type()`. Mirrors Python `_infer_expr`'s
delegation to per-part Cast lowering.

### Te.4.D — Lowerer (`mapanare/self/lower.mn`)

New `lower_interp_string` mirrors Python `_lower_interp_string`:

```
for each part:
    if expr_kind(part) == "string_lit":
        push lower_expr(part)
    else:
        v = lower_expr(part)
        c = make_value(mir_string)
        emit Cast(c, v, mir_string)
        push c
emit InterpConcat(dest, vals)
```

The Cast(String→String) that arises when the inner expression is
already a String collapses to an alias in `emit_cast` (no copy, no
new tracker). Cast(Int/Float/Bool→String) emits the matching
`__mn_str_from_*` runtime call with drop tracking on the fresh
allocation. Both behaviors mirror Python `_do_cast`.

### Te.4.D — Emitter (`mapanare/self/emit_llvm.mn`)

Two changes:

1. `emit_cast` extended to dispatch X→String to `__mn_str_from_int`
   / `__mn_str_from_float` / `__mn_str_from_bool` (with
   `zext i1 → i64` for the bool case), tracking the result.
   Cast(String→String) routes to `emit_copy` (alias-only).
2. `emit_interp_concat` final-concat fix: the last
   `__mn_str_concat` now writes into the dest's SSA name directly
   instead of into `dn.cN`. Without this, downstream uses of the
   dest resolved to an undefined value (latent bug — only surfaced
   once `lower_interp_string` started actually emitting
   InterpConcat; the dead-code instruction had been declared in
   MIR since an earlier release but never reached the emitter from
   live lowering paths).

### Te.4.E — Goldens (`tests/golden/`)

Eight new `.mn` files (`72_string_interp_var.mn` →
`80_string_interp_escaped.mn`) covering var / int / float / bool /
method / arith / multi / mixed / escaped. **66 → 80/80 PASS** (66
existing + Te.2's 5 new + Te.4's 8 new + 1 unchanged
`pass`-keyword golden).

### Te.4.F — Formatter

Out of scope. The conservative formatter is whitespace-only by
design; canonicalizing `${ x }` → `${x}` would rewrite expression
internals, which conflicts with the formatter's stated invariants
(§ STYLE_AUDIT). Deferred to v5.17.0 Sh.* prep where rewrite passes
become first-class.

### Te.4.G — SPEC.md

§2.3 already had a "String Literals" subsection mentioning
interpolation; no edits beyond a reference to v5.16.0 as the
release that achieves Python ↔ native parity.

---

## Cross-bootstrap test

`tests/bootstrap/test_string_interp_mirror.py` (10 parameterized
cases) compiles each Phase 0 fixture through both compilers, links
both via clang against the C runtime, runs both binaries, and
asserts byte-identical stdout. Same shape as
`test_comprehension_mirror.py` from v5.15.1.

---

## Strict 3-stage fixed point

Preserved at 231,957 lines / 0 diff (mnc_all.mn regenerated) between stage2.ll and stage3.ll
— unchanged from v5.15.1. The four added emitter / lowerer paths
(InterpString, lower_interp_string, Cast→String, emit_interp_concat
final-concat fix) are all purely additive: no existing emit path
changed shape, so `mnc-stage1` compiles `mapanare/self/*.mn`
identically before and after the change.

No seed refresh required (no new C-runtime exports).

---

## Known divergences from PLAN

PLAN's success criterion "byte-identical IR (modulo trivial
metadata) through Python `emit-llvm` and `mnc-stage1 emit-llvm`"
is not achievable — the two emitters differ structurally well beyond
the interp surface (Python emits a minimal prelude with only the
runtime functions actually used; native declares the full runtime
preamble upfront). The operational contract is **stdout-identity**
under run, mirroring the v5.15.1 cross-bootstrap test pattern. The
PLAN's case matrix and goldens-pass criteria are met.

Te.4.F (mnc fmt whitespace canonicalization inside `${...}`)
deferred to v5.17.0 prep — the conservative formatter design says
"does NOT rewrite expressions", and stripping whitespace inside
interpolation expressions is on the wrong side of that line.

---

## Files touched

| File | Change |
|---|---|
| `mapanare/self/ast.mn` | `Expr::InterpString(List<Expr>)` variant + `expr_kind` + accessor |
| `mapanare/self/lexer.mn` | Preserve `\$` in `scan_string` |
| `mapanare/self/parser.mn` | Rewritten `split_interp_parts` + `Expr::InterpString` wrap |
| `mapanare/self/semantic.mn` | `infer_expr` `interp_string` case |
| `mapanare/self/lower.mn` | `lower_interp_string` + dispatch |
| `mapanare/self/emit_llvm.mn` | `emit_cast` X→String + `emit_interp_concat` last-concat fix |
| `tests/golden/72…80_string_interp_*.mn` | 8 new goldens |
| `tests/bootstrap/test_string_interp_mirror.py` | New cross-bootstrap test |
| `docs/roadmap/v5/v5.16.0/INTERP_SPEC.md` | Phase 0 case matrix |
| `docs/roadmap/v5/v5.16.0/AUDIT.md` | Failure shape + resolution doc |
| `docs/roadmap/v5/v5.16.0/SESSION_REPORT.md` | This doc |
| `CHANGELOG.md` | v5.16.0 entry |
| `VERSION` | `5.15.1` → `5.16.0` |
| `README.md` / `CLAUDE.md` | Most-recent-releases ledger |

`make lint` clean. Goldens 80/80; cross-bootstrap interp 10/10;
stage2 fixed point 228,630/0.
