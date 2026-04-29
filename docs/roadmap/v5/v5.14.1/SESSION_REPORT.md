# v5.14.1 — Session Report

**Status:** READY (commits f8bc1d6 + d5849ff + this closeout; VERSION
bump not yet applied — user holds the tag/release decision per
standing instruction).
**Theme:** B.\* — bootstrap colon-block mirror (patch).
**Strict 3-stage fixed point:** **preserved** (228,630 lines, 0 diff).
**Goldens:** 66/66 brace + 66/66 colon (was 0/66 colon at v5.14.0).
**Cross-bootstrap test:** 142 / 142 (`tests/bootstrap/test_indent_preprocessor.py`).
**Effort:** ~one focused session; the `.mn` port path was the
high-cost detour.

---

## What shipped

### B.1–B.4: `pass` keyword in self-host (commit f8bc1d6)

Five lockstep edits across `mapanare/self/{lexer,ast,parser,lower}.mn`,
modeled byte-for-byte on `break`/`continue`:

- `lexer.mn` — `pass` → `KW_PASS` in `is_keyword` and `keyword_token_type`.
- `ast.mn` — new nullary `Pass` variant on `enum Stmt`; matching arm
  in `stmt_kind` returning `"pass"`.
- `parser.mn` — one branch in `parse_stmt` (`KW_PASS` → `Stmt::Pass`).
- `lower.mn` — one branch in `lower_stmt` (`sk == "pass"` returns
  state unchanged, emits zero MIR).
- `semantic.mn` — no change needed; `mapanare/self/semantic.mn` does
  not dispatch on `stmt_kind`, mirroring the Python bootstrap where
  `PassStmt` is also a no-op at the type-check pass.

Phase 0 audit confirmed zero `pass`-as-identifier collisions in
`mapanare/self/*.mn` (the v5.14.0 stdlib renames pre-handled the
three real collisions; the self-host had none). So the keyword
promotion couldn't break the self-build, and didn't.

### B.5–B.6: `__mn_indent_to_braces` in C runtime (commit d5849ff)

Mirrors `mapanare/parser.py::_indent_to_braces` in pure C
(`runtime/native/mapanare_core.c`, ~280 LOC). Routed through C rather
than `.mn` after surfacing two bootstrap-lower pathologies during a
`.mn`-side port attempt — see the [.mn port detour](#mn-port-detour)
section below.

The C function uses a heap-grown line buffer and parallel arrays for
the indent stack; algorithm is line-by-line with the Python reference,
including the comma back-patch for struct/enum/match siblings, the
continuation-keyword recognition (`else`, `sino`, `else if`,
`sino si`), the `fn name:` zero-arg paren insertion, and the fast
path for brace-only sources.

Wiring:

- `mapanare/types.py` — register `__mn_indent_to_braces: STRING_TYPE`
  in `BUILTIN_FUNCTIONS`.
- `mapanare/lower.py` — register `mir_string()` in `_BUILTIN_RET`.
- `mapanare/emit_llvm_text.py` — explicit `_rt(..., STR, [STR],
  [(a, STR)])` branch. **Without this, the bootstrap declared the
  return type as `ptr` (8 bytes) and the high 8 bytes of the
  returned `MnString` (the length) were silently dropped.** First
  reproducer of this failure mode where goldens went 66/66 → 0/66
  with no other diff: stage1 emitted IR with no main function
  because `preprocessed: String` was being read as a 8-byte pointer
  load that missed the length half of the `{ptr, i64}` struct.
- `mapanare/self/{semantic,lower,emit_llvm}.mn` — matching builtin
  registration on the self-host side, modeled after
  `__mn_version_string`. New `register_builtins` entry adds the
  symbol to scope so calls type-check.
- `mapanare/self/parser.mn::parse` — one-line wire-in before
  `tokenize()`. Both top-level `compile()` and the import resolver
  in `main.mn` route through this entry, so the preprocessor applies
  uniformly to every parsed source. Brace-only sources hit the fast
  path (single sweep + memcmp on trailing bytes per line); cost is
  negligible on the 95% of corpus that's still brace-style.

### B.7: cross-bootstrap validation test

New `tests/bootstrap/test_indent_preprocessor.py`:

- 10 hand-rolled fixtures covering each algorithm arm (block opener,
  dedent close, comma back-patch, continuation rewrite, fast path,
  mixed brace+colon, `pass` body, comment-only line, trailing blank,
  empty enum/struct/match).
- 66 corpus parametrized cases on brace form (fast path on both
  sides; result must equal source).
- 66 corpus parametrized cases on colon form (slow path on both
  sides; produced via `mapanare fmt --to-terse`).

A new hidden `mnc-stage1 preprocess <file>` subcommand prints the
result of `__mn_indent_to_braces` to stdout. Used by the test to
exercise the C path; not surfaced in `--help`.

The test strips exactly one trailing `\n` from the C output (the
self-host `print` adds one; Python's `_indent_to_braces` does not).
Anything more nuanced would mask real divergence.

### B.8: native `mnc fmt --to-terse` / `--to-braces`

Already worked at v5.13.0 — the `mnc fmt` dispatch shells out to
`mapanare fmt` and forwards every argv verbatim, so the new v5.14.0
flags came along for free. Updated the usage string to include
`[--to-terse] [--to-braces]` for discoverability; no algorithm
change.

---

## .mn port detour

A first attempt ported `_indent_to_braces` to `mapanare/self/
preprocess.mn` and hit two bootstrap-lower bugs that kept the strict
3-stage fixed point from holding. Both are documented here so they
can be tracked separately and don't ambush future Mc.\* / Sh.\* work
that wants to extend the `.mn` self-host.

### Bug 1 — `List<String>` from `String.split()` reads as garbage

Reproducer: inside a function, `let parts: List<String> =
s.split("\n"); parts[0]` returns a value the lowerer treats as a
raw pointer rather than a `String`. The 16-byte `{data, len}` struct
isn't reconstituted; downstream operations see a NULL-ish or
truncated string.

The same syntax works correctly:

- in user-level code (compiled by the same lowerer through the same
  emit pipeline), and
- when the list is passed as a function parameter and indexed there.

Workaround the `.mn` port was using before being abandoned was a
`pp_rebake_strings(xs)` helper that copied through a parameter. The
underlying lowerer pathology is unfixed.

### Bug 2 — PHI verifier failure in deeply-nested control flow

Reproducer: a function with many nested `if`/`else` chains and
short-circuit (`&&`/`||`) operators emits IR with

```
%if_result183 = phi i64 [ %t168, %if_then30 ], [ undef, %if_else31 ]
```

where the second-arm label (`%if_else31`) is not actually a
predecessor of the merge block. `llvm-as` rejects the output with
*"PHI node entries do not match predecessors"*; stage2.ll fails
verification → strict 3-stage fixed point regresses.

Restructuring patterns tried that did **not** fix it: single-return-
per-arm, decomposing `&&` into nested `if`, factoring nested arms
into helpers. The bug is in the bootstrap's CFG construction, not in
the source-level patterns it sees.

Routing `__mn_indent_to_braces` through C sidesteps both bugs by
construction: plain C is compiled by gcc/clang directly into
`libmapanare_rt.a`, and the `.mn` side that calls it is a single
`extern "C" fn` declaration plus one call site — well below the
complexity threshold either bug requires.

---

## Validation

Numbers captured at HEAD (post-Phase 5 closeout):

| Check                                       | Result        |
| ------------------------------------------- | ------------: |
| Native brace goldens (`scripts/test_native.py`) | **66 / 66** |
| Native colon goldens (`fmt --to-terse \| mnc-stage1`) | **66 / 66** (was 0/66 baseline) |
| Cross-bootstrap test (`tests/bootstrap/test_indent_preprocessor.py`) | **142 / 142** |
| Colon-block round-trip test (`tests/test_colon_blocks.py`) | **208 / 208** |
| Strict 3-stage fixed point                  | **228,630 lines, 0 diff** |
| `make lint`                                 | clean         |

The colon-corpus number is the v5.14.1 success criterion from the
Phase 0 `AUDIT.md`: **0/66 → 66/66**.

Strict fixed point is the project's most-valuable invariant; it
held continuously through both phases. Phase 1 and Phase 2 each
landed only after the verify script reported zero diff.

---

## What this unblocks

- **v5.16.0 (Te.4)** — self-host string-interpolation parity work
  can now land knowing the bootstrap parser already accepts the
  syntax v5.17.0 will introduce.
- **v5.17.0 (Sh.\*)** — `mnc fmt --to-terse mapanare/self/` will
  produce a colon-style codebase that compiles through *both* the
  Python bootstrap and `mnc-stage1`, preserving the strict 3-stage
  fixed point.
- **v5.18.0 (Mc.\*)** — `mnc lsp` / `mnc check` / VSCode extension
  can rely on the bootstrap recognizing the same surface syntax the
  Python compiler does.

---

## What remains deferred

- The two bootstrap-lower pathologies surfaced in the `.mn` port
  detour (`List<String>` indexing, PHI predecessor mismatch). These
  are tracked as bootstrap-quality work; a fix in either should land
  before v5.17.0's mechanical rewrite stresses the lower more.
- Single-line `if x: y` form — still v5.21.0 Te.6.
- Block expressions in colon form — still deferred (no clean grammar
  shape; brace-only by design at v5.14.x).

---

## Files touched

| File | LOC delta | Purpose |
|---|---:|---|
| `runtime/native/mapanare_core.c` | +280 | `__mn_indent_to_braces` C implementation |
| `mapanare/self/lexer.mn` | +5 | `pass` → `KW_PASS` |
| `mapanare/self/ast.mn` | +2 | `Stmt::Pass` variant + `stmt_kind` arm |
| `mapanare/self/parser.mn` | +12 | `KW_PASS` parse arm + builtin call site |
| `mapanare/self/lower.mn` | +8 | `Pass` no-op + `__mn_indent_to_braces` call lower |
| `mapanare/self/semantic.mn` | +6 | builtin registration |
| `mapanare/self/emit_llvm.mn` | +2 | runtime fn declaration |
| `mapanare/self/main.mn` | +25 | `preprocess` subcommand + fmt usage update |
| `mapanare/types.py` | +2 | `BUILTIN_FUNCTIONS` entry |
| `mapanare/lower.py` | +2 | `_BUILTIN_RET` entry |
| `mapanare/emit_llvm_text.py` | +12 | `_rt` emit branch |
| `tests/bootstrap/test_indent_preprocessor.py` | +175 (new) | cross-bootstrap test |
| `docs/roadmap/v5/v5.14.1/{AUDIT,SESSION_REPORT,PLAN,PROMPT}.md` | (docs) | release artifacts |
