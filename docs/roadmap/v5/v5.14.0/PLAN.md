# v5.14.0 — Te.1 — colon-block syntax (additive)

**Status:** PLANNING
**Breaking:** No. `{}` blocks continue to parse and behave
identically. This release **adds** a second valid syntax.
**Prerequisite:** v5.13.0 shipped (`mnc fmt` working, idempotent on
full corpus).
**Estimated effort:** 14–24h, two or three sessions. The hardest
work is the indent-aware tokenizer, not the grammar itself.

---

## Why this exists

Mapanare's "minimal code, same result" thesis is undermined by
mandatory `{}` braces on every block. Python's indent-based syntax
is one of the reasons it reads as half the size of equivalent C or
Rust. To compete on terseness we need indent-based blocks — but as
an **additive** change, not a hostile breaking one. Both syntaxes
must round-trip through the parser to identical AST.

This release is the first half of the terse-syntax pivot. v5.15.0
adds expression-level density (comprehensions, implicit return).
v5.17.0 mechanically rewrites `mapanare/self/*.mn` to the new
syntax using `mnc fmt --to-terse`. v5.19.0 deprecates `{}`.

The migration tool that v5.17.0 depends on lives here, in this
release: `mnc fmt --to-terse <file>` rewrites brace blocks to
colon blocks. Without it, the self-host rewrite is a hand-edited
disaster.

---

## Goal

1. The parser accepts both `fn foo() { ... }` and Python-style
   `fn foo(): <newline + indent block>`.
2. Both syntaxes lower to identical AST nodes — no semantic
   difference whatsoever.
3. `mnc fmt --to-terse` mechanically rewrites brace blocks to
   colon blocks (idempotent, AST-preserving).
4. `mnc fmt --to-braces` does the inverse (so the migration is
   reversible if Te.* is rolled back).
5. The bootstrap parser at `mapanare/self/parser.mn` is updated in
   lockstep — self-hosted compiler still parses everything.
6. Strict 3-stage fixed point still holds.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.1.A** | HIGH | Phase 0 design doc: `COLON_BLOCK_DESIGN.md`. Choose terminator strategy: indent-based (Python-style INDENT/DEDENT tokens) vs explicit `end` keyword. Decision binds the rest of the release. | 1–2h |
| **Te.1.B** | HIGH | Lexer: emit synthetic INDENT / DEDENT tokens when a line starts with greater indentation following a `:` at end-of-line. Handle blank lines, line continuations, and string literals correctly. | 4–6h |
| **Te.1.C** | HIGH | Grammar in `mapanare/mapanare.lark`: every block-introducing rule (function body, if/else, while, for, match, struct, enum, trait, agent) accepts `{ ... }` OR `: INDENT ... DEDENT`. | 2–3h |
| **Te.1.D** | HIGH | Bootstrap parser mirror: same tokenization + grammar updates in `mapanare/self/lexer.mn` and `mapanare/self/parser.mn`. | 4–6h |
| **Te.1.E** | HIGH | `mnc fmt --to-terse <file>`: rewrites brace blocks to colon blocks. Reuses Phase 1 formatter from v5.13.0. | 2–3h |
| **Te.1.F** | MEDIUM | `mnc fmt --to-braces <file>`: inverse rewriter. Lower priority but cheap to add once `--to-terse` works. | 1h |
| **Te.1.G** | HIGH | Tests: every golden file is duplicated (or temp-rewritten via fmt) into a `:`-style version, both must produce identical IR. | 2–3h |
| **Te.1.H** | MEDIUM | Docs: `docs/SPEC.md` block-syntax section updated; README example switched to colon style with brace-style note. | 1h |

---

## Phase plan

**Phase 0 — Design doc.** Pick terminator strategy. Document edge
cases: nested blocks, single-line `if x: y`, mixed brace + colon
within a single file (allow or forbid?), empty blocks (`pass` or
`{}` or just `: end`?), comments at end-of-block.

Recommendation (subject to Phase 0 rigor): **indent-based with
INDENT/DEDENT tokens, no `end` keyword.** Rationale: matches
Python's UX exactly, what users want; explicit terminators feel
verbose against the terseness thesis.

**Phase 1 — Lexer changes.** This is the hard part. Indent tracking
in an LALR-driven parser requires the lexer to emit synthetic
tokens. Reference: Python's `tokenize` module. Edge cases:
- Blank lines and pure-comment lines: ignore for indent
- Line continuations (`\` at EOL or unclosed brackets): no DEDENT
- String literals spanning lines: tokenize as single STRING
- Mixing tabs and spaces: error or canonicalize?

**Phase 2 — Grammar.** Extend `mapanare.lark` so every block-rule
accepts both forms. The grammar duplication is verbose but
mechanical. Test with a representative file in both styles —
parse trees must be identical.

**Phase 3 — Bootstrap mirror.** `mapanare/self/lexer.mn` and
`mapanare/self/parser.mn` get the same updates. This is
~6h of work because the bootstrap parser is hand-written recursive
descent, not Lark.

**Phase 4 — fmt integration.** Extend `mapanare/format.py`:
- `format_source(src, target_style="braces" | "colons")` parameter
- `mnc fmt --to-terse` and `mnc fmt --to-braces` flags

**Phase 5 — Cross-style validation.** For every file in
`tests/golden/`:
- Original (brace style) → IR_braces
- Run `mnc fmt --to-terse` → colon-style version → IR_colons
- Assert `IR_braces == IR_colons` (modulo trivial whitespace)

**Phase 6 — Bootstrap dogfood.** `mnc fmt --to-terse
mapanare/self/lexer.mn`, parse it, compare AST to original. Do not
commit the rewritten self/ here — that's v5.17.0. Just prove the
tooling works end-to-end on the largest real codebase.

**Phase 7 — Docs + closeout.** SPEC, README, SESSION_REPORT.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Indent tokenization breaks LALR(1) parser | MEDIUM | Phase 0 prototypes the lexer change in isolation before touching grammar. If LALR can't accept it, fall back to PEG-ish or hand-written shim layer. |
| Self-hosted parser rewrite drops a token | HIGH | Phase 3 has its own test pass: parse every file in `tests/golden/` and `mapanare/self/` through the new bootstrap parser, diff AST against Python parser. |
| Single-line `if x: y` ambiguity with multi-line `if x:\n  y` | LOW | Specify in Phase 0: single-line form requires the body on the same line; multi-line form requires newline + INDENT. Match Python. |
| Mixed brace + colon in one file confuses fmt | LOW | fmt is the canonicalizer — `--to-terse` converts everything, `--to-braces` converts everything. Mixed input is legal but always normalized on save. |
| Strict 3-stage fixed point breaks | MEDIUM | self-hosted parser changes are AST-equivalent only, so emitted IR must be byte-identical. Validate after Phase 3. |
| Tabs-vs-spaces religious war | LOW | Spaces only. Tabs in indent are an error. Codify in Phase 0. |

---

## Out of scope (deferred)

- Deprecating `{}` → **v5.19.0 (Te.3)**
- Rewriting `mapanare/self/` to colon style → **v5.17.0 (Sh.*)**
- Comprehensions, implicit return, terse lambdas → **v5.15.0 (Te.2)**
- `if x: y` single-line nesting (`if x: if y: z`) — too cute, defer
- Significant whitespace inside expressions — not happening

---

## Success criteria

- Both `fn main() { print("hi") }` and `fn main(): \n  print("hi")`
  parse and produce identical AST and identical IR
- `mnc fmt --to-terse` round-trips: `to_braces(to_terse(x)) == x`
  modulo whitespace
- Goldens 66/66 pass with brace-style source
- Goldens 66/66 pass with `--to-terse`-rewritten source
- Self-hosted compiler still builds and self-compiles
- Strict 3-stage fixed point preserved
- `make lint` clean
