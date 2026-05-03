# v5.14.0 — Colon-block syntax — design doc

**Status:** locked. Phase 0 deliverable. Decisions below bind the
rest of the release.

---

## Pre-implementation audit

Before writing one line, I probed what colon syntax already does on
HEAD. Two big findings reshaped scope:

1. **The Python parser already has `_indent_to_braces`** at
   `mapanare/parser.py:1812`, a v3.0.0-era preprocessor that
   converts colon-blocks to brace-blocks before Lark sees them.
   Most of v5.14.0 is hardening, not invention.
2. **`parse_recovering` skips the preprocessor.** It calls
   `_parser.parse(source)` directly — so `mapanare check` and the
   whole error-recovery path don't see colon syntax. Bug.

### What works on HEAD

| Construct | Status |
|---|---|
| `fn name():` | ✅ |
| `if/else/else if` | ✅ |
| `while`, `for`, `let` | ✅ |
| `trait`, `agent`, `impl` | ✅ |
| `struct Point: \n  x: int \n  y: int` | ❌ — preprocessor doesn't insert `,` between fields |
| `enum Shape: \n  A \n  B` | ❌ — same |
| `match x: \n  1 => ... \n  _ => ...` | ❌ — same |
| `pass` for empty block | ❌ — lexes as identifier, fails semantic |
| Single-line `if x: y` | ❌ — preprocessor doesn't handle |
| Bootstrap (`mnc-stage1`) on any colon source | ❌ — no preprocessor at all |

### Implication for scope

The PLAN's "indent-aware lexer with INDENT/DEDENT tokens" is one of
two valid architectures. The existing preprocessor architecture is
the other, and it's already shipping on `parse()`. Adopting the
preprocessor approach (rather than a Lark `Indenter` postlex):

- Re-uses what works
- Avoids a grammar rewrite
- Lets the bootstrap mirror be a 1:1 string-rewriter port (`str→str`),
  not a tokenizer rewrite — the bootstrap parser is 2,599 lines of
  hand-written recursive descent and the smaller this change, the
  smaller the chance of breaking the strict 3-stage fixed point
- Keeps the single source of truth: AST is identical because the
  parser sees the same brace-form text

The trade-off: the preprocessor is more brittle than a real
indent-aware lexer (string-level transforms can mis-handle edge
cases like colons inside strings). v5.14.0 documents the known
limitations; later releases can promote to a real INDENT/DEDENT
tokenizer if a real-world bug demands it.

---

## Locked decisions

### 1. Terminator strategy

**Indent-based via the existing string preprocessor `_indent_to_braces`.**
No `end` keyword. No Lark `Indenter` postlex. Bootstrap mirrors via
a 1:1 `.mn` port of the same preprocessor.

Rationale: PLAN recommendation matches; existing preprocessor
already validates the architecture; bootstrap port is small.

### 2. Tab/space rule

**Spaces only.** Tab in indent → preprocessor canonicalizes it to 4
spaces (matches `format_source` rule from v5.13.0). No error,
because v5.13.0's formatter already silently fixes the same thing
and cosmetic divergence is not worth a hard error.

### 3. Empty colon-block

**Requires `pass` keyword.** New reserved word. Lowers to a no-op
statement. The user observation — `{}` looks like an object literal,
empty colon-block is ambiguous — is correct, and `pass` removes the
ambiguity at zero parser cost.

`fn empty() {}` continues to work (brace form unchanged). The
colon-form spelling is `fn empty(): \n    pass`.

### 4. Single-line `if x: y`

**Deferred** to a later release (v5.21.0 Te.6 small ergonomic wins).
Keeps the preprocessor simple, reduces ambiguity surface, can be
added without breaking anything later.

Diagnostic: the preprocessor will detect `if cond: stmt` (colon
followed by non-newline content) and emit a parse error pointing to
"single-line colon-blocks not yet supported, put body on next line".

### 5. Mixed brace + colon in one file

**Legal at parse time.** The preprocessor only transforms
colon-suffixed lines; brace blocks pass through unchanged. fmt
normalizes to one style on save (`--to-terse` or `--to-braces`).

### 6. Comments at end-of-block

**Comment-only lines never trigger DEDENT.** Existing preprocessor
already does this correctly (line 1852–1859). A comment at reduced
indent attaches to whatever block the next real line attaches to —
matches Python's mental model.

### 7. `pass` as a new keyword

New `KW_PASS` token. New `pass_stmt` rule. New `PassStmt` AST node.
Semantic: no-op. Lowering: emits zero MIR instructions. Emitter: no
LLVM output. Bootstrap mirrors the same chain.

---

## Out of scope (to be explicit)

- Single-line `if x: y` (decision 4 above)
- Significant whitespace inside expressions
- Indent-sensitive comprehensions (those are v5.15.0 Te.2)
- Deprecating `{}` (that's v5.19.0 Te.3)
- Rewriting `mapanare/self/` to colon style (that's v5.17.0 Sh.\*)

---

## Implementation order

1. **`pass` keyword** end-to-end (lex → parse → AST → semantic →
   lower → emit_llvm → emit_c → bootstrap mirror). Smallest
   self-contained change; gives us `pass` independently of the
   indent work.
2. **Fix `_indent_to_braces`**: insert `,` between
   struct fields, enum variants, match arms when the body came from
   a colon block. Detect single-line `if x: y` and emit the
   diagnostic from decision 4.
3. **Wire `parse_recovering` through `_indent_to_braces`** so
   `mapanare check` and friends see colon syntax.
4. **Bootstrap mirror**: port `_indent_to_braces` to `.mn` in
   `mapanare/self/main.mn`. Same algorithm, run before the bootstrap
   tokenizer.
5. **`mnc fmt --to-terse`**: AST-aware brace → colon rewriter.
   Idempotent. Round-trips with `--to-braces`.
6. **`mnc fmt --to-braces`**: convenience inverse — runs
   `_indent_to_braces` and then `format_source`.
7. **Cross-style validation tests**: every parseable golden file
   round-trips both directions to identical AST.
8. **Docs**: SPEC, README example, SESSION_REPORT.

---

## Risk register (revised after audit)

| Risk | Likelihood | Mitigation |
|---|---|---|
| Bootstrap port drops a token vs Python preprocessor | MEDIUM | Phase 4 adds a parametrized test that runs both preprocessors on every golden and asserts identical output |
| `_indent_to_braces` mis-handles `:` inside string literals | LOW | Existing code already uses `lstrip().startswith("#", "//")` for comments; extend to track in-string state for the new struct/enum/match code paths |
| Strict 3-stage fixed point breaks | LOW | No `mapanare/self/*.mn` source changes in v5.14.0 — bootstrap edits only add a no-op preprocessor before existing tokenizer |
| `pass` collides with any existing identifier in tests/golden | LOW | Grep first; rename if collision found |
| `--to-terse` rewrite produces non-round-trippable AST | MEDIUM | Phase 5 cross-style validation must run on every golden before merge |

---

## Success criteria

- `parse(brace_src) == parse(to_terse(brace_src))` on every golden
- `parse_recovering` accepts colon syntax (closes Bug #1)
- `pass` is a real no-op statement
- Bootstrap `mnc-stage1` accepts colon source for at least the same
  set of constructs the Python parser does
- Goldens 66/66 (brace-form, unchanged corpus)
- Strict 3-stage fixed point preserved
- `make lint` clean
