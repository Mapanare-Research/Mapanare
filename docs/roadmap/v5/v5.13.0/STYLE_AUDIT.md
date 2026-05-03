# v5.13.0 — STYLE_AUDIT.md

Phase 0 deliverable for Mc.2 (`mnc fmt`). Documents the de-facto
style of `.mn` source across the corpus and the resulting design
decisions for `mapanare/format.py`.

The principle is **codify, do not impose** — the formatter encodes
the dominant existing style. Where the corpus is unanimous, the rule
is the unanimous choice. Where it is heterogeneous, the formatter
leaves it alone (deferred to a later release).

---

## 1. Corpus surveyed

114 `.mn` files across:

| Root | Files | Role |
|---|---:|---|
| `tests/golden/` | ~66 | Golden corpus — minimal canonical programs |
| `mapanare/self/` | ~14 | Self-hosted compiler — 14k lines, the v5.17.0 rewrite target |
| `examples/` | ~34 | Curated demos and stdlib showcases |

Every file in each root was scanned by an automated audit script
(see Phase 0 commit history for the throwaway).

---

## 2. Findings

### 2.1 Indentation — UNANIMOUS

| Rule | Files |
|---|---:|
| 4 spaces, no tabs, no mixed | **114 / 114** |
| 2-space indent | 0 / 114 |
| Tab indent | 0 / 114 |
| Mixed | 0 / 114 |

**Decision:** the canonical indent unit is **4 spaces**. v5.13.0
does NOT re-indent (because the corpus is already canonical), but
future releases may enforce this when a non-conforming file is
introduced.

### 2.2 Line endings — NEAR-UNANIMOUS, with two outliers

| Style | Files |
|---|---:|
| LF | 112 / 114 |
| CRLF | 2 / 114 (`mapanare/self/ast.mn`, `mapanare/self/lexer.mn`) |
| Mixed | 0 / 114 |

**Decision:** canonical line ending is **LF**. The two CRLF files
are normalized as part of v5.13.0's one-time self-format commit
(Phase 4). Verify the strict 3-stage fixed point holds after.

### 2.3 Trailing whitespace — UNANIMOUS

0 / 114 files contain trailing whitespace on any line.

**Decision:** strip trailing whitespace from every line.

### 2.4 Final newline — UNANIMOUS

0 / 114 files are missing a final newline.

**Decision:** ensure exactly one trailing newline. Files ending in
`\n\n\n` have the extra blanks collapsed; files ending in `<text>`
with no terminator gain one.

### 2.5 Consecutive blank lines — UNANIMOUS

0 / 114 files contain 4+ consecutive newlines (`\n\n\n\n` = 2+
visual blank lines between non-empty lines).

**Decision:** cap consecutive blank lines at **1** (i.e., at most
one empty line between non-empty lines).

### 2.6 Comment styles

| Style | Files using it |
|---|---:|
| Line `// …` | 84 / 114 |
| Doc `/// …` | 3 / 114 |
| Block `/* … */` | 3 / 114 |

The dominant convention is `//` line comments. Block and doc
comments are present but rare. **The formatter must preserve all
three forms verbatim** — comment content is opaque to v5.13.0.
Block-comment-aware reformatting is deferred to v5.20.0+.

### 2.7 Brace placement

Same-line brace is universal:

```mn
fn main() {       // canonical
    ...
}
```

No file in the corpus uses next-line braces for `fn`, `struct`,
`enum`, `tipo`, `if`, `for`, `while`, `match`, or `agent` blocks.

**Decision:** v5.13.0 does not touch brace placement. The corpus is
already canonical. v5.14.0+ will encode the rule when colon-block
syntax (`:`) is introduced as an alternative.

### 2.8 Trailing commas

Heterogeneous in tipo/struct field lists and arg lists:

```mn
struct Foo {
    a: Int,
    b: Int           // no trailing comma
}

new Foo { a: 1, b: 2, }  // trailing comma — also legal per grammar
```

**Decision:** v5.13.0 leaves trailing commas alone. This is a
real style choice and the corpus has not converged.

### 2.9 String literals

The grammar declares `STRING_LIT: /\"([^\"\\]|\\.)*\"/` — strings
**cannot span multiple lines**. The grammar also declares
`TRIPLE_STRING.4: /\"\"\"[\s\S]*?\"\"\"/`, but **0 / 114 corpus
files contain `"""`**.

**Implication:** line-level operations (strip trailing whitespace,
collapse blanks) are safe on the entire corpus. Each line either
contains complete strings or none — there is no
within-string content past a line break to preserve.

For future-proofing, `format.py` should still avoid mutating bytes
inside any string literal, single- or triple-quoted.

---

## 3. Architecture decision: token-stream vs AST-visit

**Decision: token-stream / line-based.**

Rationale:

1. **Comments must be preserved.** Mapanare's AST currently strips
   `//` line comments and `/* */` block comments — they are not
   attached to any node. An AST-visit formatter would lose them on
   every round-trip, which is unacceptable.
2. **The corpus is already canonical.** All v5.13.0 needs to do is
   strip trailing whitespace, normalize line endings, cap blank
   runs, and ensure a final newline. None of these require AST
   awareness.
3. **AST-preservation is trivially provable.** A line-based pass
   that only touches whitespace at line boundaries cannot change
   any token the parser sees, so `parse(format(x)) == parse(x)`
   holds by construction.
4. **It sets up v5.14.0 cleanly.** Te.1 (colon-block syntax) is
   additive, and the `--to-terse` migration in v5.14.0 does need
   AST awareness — but that pass can layer on top of the
   line-based core, calling `format_source(source)` last to
   normalize whitespace after the structural rewrite.
5. **It is small.** ~50 lines of Python vs. the ~1000+ lines an
   AST-visitor with comment attachment would require.

The trade-off is that v5.13.0 cannot reformat structural elements
(brace placement, indentation, expression layout). That is
acceptable: the PLAN's "conservative formatting wins" guidance and
the unanimous corpus style mean there is nothing structural to
reformat today.

---

## 4. Rules the v5.13.0 formatter applies

In order:

1. Normalize line endings: `\r\n` → `\n`, then bare `\r` → `\n`.
2. Strip trailing whitespace from every line (spaces and tabs).
3. Collapse 2+ consecutive blank lines to 1 blank line.
4. Strip leading blank lines from the file.
5. Strip trailing blank lines.
6. Ensure the file ends with exactly one `\n` (unless the file is
   empty, in which case the result is `""`).

That is the entire rule set. Idempotency, AST-preservation, and
"do not impose" are all satisfied by construction.

---

## 5. Rules deferred (for v5.14.0+ and later)

Documented here so future releases know where to layer:

- Indent re-flowing — wait until a non-conforming file appears.
- Brace style — wait for v5.14.0 colon-block introduction.
- Trailing-comma policy — corpus has not converged.
- Long-line wrapping — v5.20.0+.
- Import sorting — v5.20.0+.
- Comment-aware reformatting (e.g., wrapping `///` doc comments) —
  v5.20.0+.
- Configurable line width via `.mapanare-fmt` — v5.20.0+.
- `--to-terse` migration mode — **v5.14.0 (Te.1)**.

---

## 6. Validation criteria (carried into the implementation)

The formatter is correct iff for every file `f` in the corpus:

- `format(f) == format(format(f))` (idempotent)
- `parse(f) == parse(format(f))` (AST-preserving)
- `format(f)` ends with exactly `"\n"` (or is `""`)
- `format(f)` contains no `\r`
- `format(f)` contains no trailing whitespace on any line
- `format(f)` contains no run of 3+ consecutive `\n`
