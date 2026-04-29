# v5.14.0 — Session Report

**Status:** READY (this PR; VERSION bump not yet applied — user
holds the tag/release decision per standing instruction).
**Theme:** Te.1 — colon-block syntax (additive).
**Strict 3-stage fixed point:** preserved by construction (no
`mapanare/self/*.mn` source changes).
**Goldens:** 66/66 (Python parser; bootstrap unchanged).
**Cross-style validation:** 208/208 (every golden round-trips).
**Effort:** ~one focused session; significantly under the 14–24h
PLAN estimate because the v3.0.0-era `_indent_to_braces`
preprocessor already covered most of the surface.

---

## What shipped

### Surface syntax

Indent-based colon-block syntax now works alongside `{}` blocks for
every block-introducing construct in the language. Both syntaxes
produce identical AST and identical IR.

```mn
// Brace style (continues to work; canonical for v5.14.0)
fn factorial(n: int) -> int {
    if n <= 1 {
        return 1
    } else {
        return n * factorial(n - 1)
    }
}

// Colon style (new in v5.14.0; opt-in)
fn factorial(n: int) -> int:
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)
```

Mixed brace + colon in one file is legal at parse time; `mnc fmt
--to-terse` / `--to-braces` normalize to one style on save.

### `pass` keyword

New reserved word. Required to mark empty colon-block bodies (you
can't write `fn empty(): {}` — `{}` is read as object/map literal).
Lowers to a no-op (zero MIR, zero LLVM output). Also legal as a
standalone statement in brace blocks.

```mn
fn empty():
    pass
```

### Tooling

- `mapanare fmt --to-terse <path>` — comment-preserving brace →
  colon rewriter
- `mapanare fmt --to-braces <path>` — inverse rewriter (thin wrapper
  over `_indent_to_braces` + `format_source`)
- Both compose with `--check`, `--stdout`, directory recursion

### New / changed code

| File | Change |
|---|---|
| `mapanare/mapanare.lark` | New `KW_PASS` keyword; `pass_stmt` rule added to `?stmt` alternatives |
| `mapanare/ast_nodes.py` | New `PassStmt` dataclass |
| `mapanare/parser.py` | `pass_stmt` transformer; `_indent_to_braces` rewritten to track parent-block context (struct/enum/match get `,` separators); `parse_recovering` now invokes the preprocessor |
| `mapanare/semantic.py` | `PassStmt` recognized as no-op |
| `mapanare/lower.py` | `PassStmt` returns immediately, emits zero MIR |
| `mapanare/format.py` | New `to_terse()` and `to_braces()` functions |
| `mapanare/cli.py` | `--to-terse` / `--to-braces` flags wired into `cmd_fmt` |
| `stdlib/db/migrate.mn` | `pass` → `pass_idx` (identifier collision) |
| `stdlib/net/http/auth.mn` | `pass` → `password` (identifier collision, two sites) |
| `stdlib/test/runner.mn` | `pass` parameter → `passed` |
| `tests/native/test_{fs,log,json,text,time,string_utils,math}.mn` | `pass` local var → `passed` (lockstep with runner.mn) |
| `tests/test_colon_blocks.py` | 208 new tests (rewriter unit rules + golden cross-style) |
| `docs/roadmap/v5/v5.14.0/COLON_BLOCK_DESIGN.md` | Phase 0 deliverable |
| `docs/roadmap/v5/v5.14.0/SESSION_REPORT.md` | this file |
| `CHANGELOG.md` | v5.14.0 entry |
| `CLAUDE.md` | release-notes entry under Current Version & Roadmap |

---

## How the design decisions landed

### Indent-based via the existing preprocessor (not Lark Indenter)

The PLAN recommended a Lark `Indenter` postlex. Phase 0's
pre-implementation audit found that the v3.0.0-era
`_indent_to_braces` preprocessor at `mapanare/parser.py:1812`
already worked for `fn`, `if`/`else`, `while`, `for`, `let`, `trait`,
`agent`, `impl` — about 70% of the surface. It was just missing
struct/enum/match (no comma insertion) and was not invoked from
`parse_recovering` (so `mapanare check` silently rejected colon
syntax).

Choosing to harden the existing preprocessor instead of swapping
to Indenter:

- Re-uses what already shipped and ships green.
- Avoids a grammar rewrite — every block-rule in the LALR grammar
  stays as `... block`, where `block: LBRACE ... RBRACE`.
- The brace path in the parser is byte-identical to v5.13.0; the
  colon path is a string-level rewrite that runs ahead of Lark.
  The parser sees the same tokens whether the user wrote braces or
  colons, so AST equivalence is enforced *by construction*.

Trade-off: text-level transforms can be confused by unusual
layouts. The rewriters are conservative (never invent syntax,
pass through patterns they don't recognize). When a real-world
edge case demands a stricter foundation, a future release can
promote to a real INDENT/DEDENT lexer.

### `pass` as a real keyword (not contextual)

Considered making `pass` contextual (only a keyword inside an empty
colon-block, an identifier elsewhere). Rejected: contextual
keywords confuse the tokenizer and the LALR parser; cost is
3 stdlib renames and ~10 test-file lockstep edits, all mechanical.

### Bootstrap mirror deferred

PLAN.md Phase 3 calls for porting the preprocessor to
`mapanare/self/main.mn`. That work is real but *only load-bearing
at v5.17.0* (Sh.\* — mechanical rewrite of `mapanare/self/`).
Touching `mapanare/self/` is the only way v5.14.0 can break the
strict 3-stage fixed point — the v5.9.0 milestone the project has
held since.

Decision: ship v5.14.0 with bootstrap untouched. Users who want
to feed colon-style source to `mnc-stage1` run `mapanare fmt
--to-braces` first. A dedicated bootstrap-mirror release will
land the port before v5.17.0. Communicated to the user; approved.

### Match grammar quirk

`match_arms: (match_arm (COMMA _nl* match_arm)* COMMA?)?` looks
like it accepts a trailing comma, but the LALR(1) lookahead can't
disambiguate the trailing `COMMA?` against a following `RBRACE`
that's separated by newlines, so trailing commas on `match` arms
fail to parse in practice. struct/enum *do* accept trailing
commas (`(struct_field COMMA _nl*)* struct_field?`).

The preprocessor was rewritten to insert commas *between* siblings
(not at end of each), so `match` works without rewriting the
grammar. Side benefit: the brace-form output is cleaner (no
spurious trailing commas).

---

## Verification

| Check | Result |
|---|---|
| `pytest tests/test_colon_blocks.py` | **208 / 208** |
| `pytest tests/parser/ tests/cli/ tests/test_format.py tests/semantic/ tests/spec/ tests/stdlib/` | 1,439 + N pass (full broad scope green) |
| `pytest tests/stdlib/test_sql_migrate.py` | 23 / 23 (was 8 failing pre-fix from `pass` collision) |
| `mypy mapanare/ runtime/` | clean |
| `mapanare check` on colon source | works (was failing before — `parse_recovering` was bypassing the preprocessor) |
| `mapanare fmt --to-terse` on every golden | every file rewrites to colon-form that re-parses to AST-equivalent program |
| `mapanare fmt --to-braces` on every `--to-terse`-rewritten golden | round-trip recovers original AST (modulo spans + PassStmt no-op) |
| Goldens 66/66 (brace form, unchanged corpus) | preserved |
| Strict 3-stage fixed point | preserved by construction (no `mapanare/self/*.mn` edits) |

---

## Test-only infrastructure

`tests/test_colon_blocks.py` is the single point of truth for
cross-style equivalence. Its `_normalize` helper recursively strips
`Span` fields (line/column shift when source layout changes) and
collapses a body of `[PassStmt]` to `[]` (the `fn empty() {}` →
`fn empty(): pass` rewrite is semantically equivalent — both lower
to the same MIR).

Three parametrized tests run against every parseable golden:

1. `to_terse` is idempotent
2. `to_terse(brace_src)` AST-equals the original (normalized)
3. `to_braces(to_terse(src))` AST-equals the original (normalized)

All 208 cases pass.

---

## Known limitations / deferred

Tracked here so future releases know where to layer.

- **Bootstrap requires brace-style source.** v5.16.0 or a dedicated
  v5.14.x patch will land the bootstrap preprocessor port.
- **Single-line `if x: y` form** rejected. Pushed to v5.21.0 Te.6
  (small ergonomic wins). Diagnostic is the standard Lark error.
- **Block expressions in colon form.** `let x = { stmt; stmt }`
  has no clean colon equivalent in v5.14.0; brace form continues
  to be the only way to write a block expression. v5.15.0 (Te.2 —
  expression density) is the natural place to revisit.
- **`to_terse` is text-based, not AST-walking.** Patterns it
  doesn't recognize pass through unchanged. The corpus is canonical
  enough that this is invisible in practice; if a real-world layout
  trips the rewriter, the symptom is "no rewrite happened" not
  "wrong rewrite happened."
- **`mnc fmt --to-terse` / `--to-braces` not yet wired into the
  native `mnc` CLI.** The Python `mapanare fmt` flags work; native
  `mnc fmt` shells out to Python (per v5.13.0 design) but doesn't
  forward the new flags. Trivial follow-up.
- **VERSION file not bumped.** User holds the tag/release decision.

---

## What it means for v5.15.0+

- **v5.15.0 (Te.2)** — comprehensions, terse lambdas, one-liner
  implicit return. Lays AST rewrites on top of `format_source`.
  `--to-terse` will gain new rewrite passes for these features.
- **v5.16.0 (Te.4)** — self-host string-interp parity. Natural
  place to also fold in the bootstrap colon-syntax port if not
  shipped earlier as a v5.14.x patch.
- **v5.17.0 (Sh.\*)** — mechanical `mapanare fmt --to-terse` over
  `mapanare/self/*.mn`. **Highest-risk release in the arc.** Now
  has a working `--to-terse` to lean on; failing modes show up
  here as "rewriter doesn't recognize this layout, leaves it
  alone" rather than "rewriter produced wrong output." That's the
  right failure shape for an automated migration.
- **v5.19.0 (Te.3)** — soft-deprecate `{}` (warning only). v5.14.0's
  preservation of brace-form makes this trivial — just emit a
  diagnostic when the parser encounters `LBRACE` in a block-opener
  position.

---

## Closeout checklist

- [x] `COLON_BLOCK_DESIGN.md` written before implementation.
- [x] `pass` keyword end-to-end (lex → parse → AST → semantic →
      lower).
- [x] `_indent_to_braces` handles struct/enum/match.
- [x] `parse_recovering` wired through the preprocessor.
- [x] `mapanare fmt --to-terse` / `--to-braces` shipped.
- [x] `tests/test_colon_blocks.py` exists and is green (208 / 208).
- [x] Stdlib `pass` collisions renamed; lockstep test updates done.
- [x] Goldens 66/66 (brace, unchanged).
- [x] Strict 3-stage fixed point preserved by construction.
- [x] `mypy mapanare/ runtime/` clean.
- [x] CHANGELOG entry.
- [x] CLAUDE.md release-notes entry.
- [ ] VERSION bump (user-driven via `/bump-version`).
- [ ] Bootstrap mirror (deferred — see "Known limitations").
- [ ] `mnc fmt` (native) `--to-terse` / `--to-braces` flag forwarding
      (trivial follow-up).
