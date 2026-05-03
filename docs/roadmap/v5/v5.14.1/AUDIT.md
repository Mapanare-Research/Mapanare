# v5.14.1 — Phase 0 audit

**Date captured:** 2026-04-29
**Captured at git HEAD:** `2172b8b` (v5.14.0 release commit)
**Bootstrap binary:** `mapanare/self/mnc-stage1` (built pre-v5.14.0,
6.6 MB ELF, reports `mapanare 5.13.0`)

---

## Goal

Document the v5.14.0-HEAD baseline so v5.14.1's success criterion
is a concrete number, not "should work."

---

## Baseline run

The corpus sweep ran every `tests/golden/*.mn` (n=66) through three
stages:

1. **Native, brace form** — `mnc-stage1 emit-llvm <golden>` on the
   unmodified golden.
2. **Python `--to-terse`** — `mapanare fmt --to-terse --stdout
   <golden>` to produce a colon-style copy.
3. **Native, colon form** — `mnc-stage1 emit-llvm <terse-copy>`.

Stage 3 is the critical column for v5.14.1.

| Stage                            | Result        |
| -------------------------------- | ------------: |
| Native brace OK                  | **66 / 66**   |
| Python `--to-terse` OK           | **66 / 66**   |
| Native colon OK                  | **0 / 66**    |
| Native colon parse-fail          | **66 / 66**   |
| Native colon non-parse fail      | 0 / 66        |

Sample of the parse-fail messages:

```
PARSE-FAIL  01_hello.mn          parse error: expected LBRACE but got COLON
PARSE-FAIL  02_arithmetic.mn     parse error: expected LBRACE but got COLON
PARSE-FAIL  03_function.mn       parse error: expected LBRACE but got COLON
PARSE-FAIL  04_if_else.mn        parse error: expected LBRACE but got COLON
PARSE-FAIL  05_for_loop.mn       parse error: expected LBRACE but got COLON
PARSE-FAIL  06_struct.mn         parse error: expected ASSIGN but got COLON
PARSE-FAIL  07_enum_match.mn     parse error: expected ASSIGN but got COLON
PARSE-FAIL  08_list.mn           parse error: expected LBRACE but got COLON
PARSE-FAIL  09_string_methods.mn parse error: expected LBRACE but got COLON
PARSE-FAIL  10_result.mn         parse error: expected LBRACE but got COLON
```

(Full list: `/tmp/v5141-audit/baseline.txt` — all 66 lines have the
shape `PARSE-FAIL  NN_*.mn  parse error: expected {LBRACE,ASSIGN}
but got COLON`. The two error variants reflect the parse context:
the LBRACE form is the function/if/while/etc. block-opener; the
ASSIGN form is `struct N: ...` / `enum N: ...` colliding with
`let`-style binding parses.)

---

## `pass`-as-identifier audit (in `mapanare/self/`)

Search:

```bash
grep -n "^pass\b\|\"pass\"\|'pass'\| pass\b\|\bpass$" mapanare/self/*.mn
```

Result: **zero collisions**. Every match is either:

- Inside a `//` comment (e.g. "// Default (neither): SysV / AAPCS64 — pass and return aggregates").
- Inside a string literal in the Python transpiler keyword-detection
  helper (`from_python.mn:40`, `from_python.mn:495` — `if s == "pass"` /
  `if t.value == "pass"`).

This means B.1–B.4 (adding `pass` as a real reserved keyword in the
bootstrap lexer/parser) cannot break the self-build. None of the
~14k LOC in `mapanare/self/*.mn` uses `pass` as an identifier.

---

## Acceptance criteria for v5.14.1

The two numbers v5.14.1 must hit:

1. **Native colon OK: 0 → 66** (every parseable golden the Python
   bootstrap accepts in colon form must also parse on `mnc-stage1`).
2. **Native brace OK: 66 → 66** (no regression on the existing
   corpus — `pass` keyword + new preprocessor must be transparent
   to brace-style code).

Plus the two project-wide invariants:

3. **Goldens 66/66 via `scripts/test_native.py`** still pass.
4. **Strict 3-stage fixed point preserved** (the v5.9.0 milestone
   that has held through every release since). This is the hardest
   constraint; the new preprocessor `.mn` code is itself compiled
   through the bootstrap, so any non-determinism (map-iteration
   order, hash collisions, locale-dependent string ops) will
   surface as stage2.ll ≠ stage3.ll.

---

## Reference points (Python preprocessor)

Canonical source: `mapanare/parser.py:1828-1973`. ~145 lines.

Key invariants the bootstrap port must mirror byte-for-byte:

- Fast path: file with no `:`-terminated lines passes through
  unchanged (`_indent_to_braces` returns `source` as-is).
- Indent stack frames are `[level, needs_comma, prev_child_idx]`
  triples. `prev_child_idx` is **mutated** when a sibling is
  emitted (the comma back-patches the previous line in `out`).
- `_COMMA_BODY_OPENERS = ("struct ", "enum ", "match ")`. Bodies
  opened by these get inter-sibling commas.
- `_CONTINUATION_KW = ("else", "sino", "sino si", "else if")`.
  Continuation lines pop the previous block and reopen on the same
  source line.
- `fn name:` (zero-arg, no parens) gets paren insertion:
  `fn name() {` (or `fn name() -> Ret {` if `->` is in the head).
- 4-space indentation only (`level = spaces // 4`).
- Comment-only lines: close blocks for dedent, then pass through.
- Last child of a `match` deliberately does NOT get a trailing
  comma — the LALR grammar accepts `(arm (COMMA arm)* COMMA?)?`
  but rejects the trailing comma in practice (it's the COMMA?
  that's nominal-only).

The Phase 2 port should treat `mapanare/parser.py:1828-1973` as
the oracle. Any deviation surfaces in B.7 cross-bootstrap
validation.
