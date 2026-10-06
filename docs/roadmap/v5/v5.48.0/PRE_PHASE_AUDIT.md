# v5.48.0 — Phase 0 Audit (PRE_PHASE_AUDIT.md)

**Status:** complete (Phase 0 gate)
**Generated:** v5.48.0 session-start audit, before any parser/formatter
edit, against `count_user_brace_block_openers` at HEAD = v5.47.5.

This audit measures the brace-block surface that v5.48.0 must
classify, parse, and migrate. It also locks the migration-rule
decisions before Phase 1 implementation begins.

---

## Total brace-block surface

`count_user_brace_block_openers` over every `*.mn` file in the repo
(excluding hidden / build / toolchain dirs) reports:

| Area | Brace-block openers |
|---|---:|
| `mapanare/self/` | **6826** (incl. `mnc_all.mn` snapshot at 3151) |
| `stdlib/**/*.mn` | 6116 |
| `tests/golden/*.mn` | 63 |
| `tests/**` (non-golden) | 595 |
| `examples/**` | 294 |
| Other (fuzz, benchmarks, scripts, docs fences embedded in `.mn`) | 1643 |
| **Total** | **15,537 across 237 files** |

`mnc_all.mn` is the concatenated stage1 build artifact and inherits
whatever shape its constituent modules have, so its 3151 count is
**not** independent — it disappears when the underlying modules
migrate. The Phase-5 migration target is the per-module set.

`mapanare/self/` (excluding `mnc_all.mn`): **3,675** brace-block
openers across 12 modules. These are the load-bearing migration
target — every one of them currently fires the v5.19.0 brace
deprecation warning during stage1 builds.

---

## Shape classification

A line-based heuristic classifier (statement-keyword detection at the
opener; closer presence/absence on the same line; `=>` arm bodies)
buckets each `{` opener into one of seven shapes. Heuristic limits:
`extern { ... }` blocks, `} else if EXPR {` continuations, and
multi-line blocks whose opener line spans wraps look like
"expression_brace" and inflate that bucket. The dominant shapes are
not affected by those edge cases.

### `mapanare/self/` (excluding `mnc_all.mn`, 3,571 classified openers)

| Shape | Count | Migration target |
|---|---:|---|
| `one_line_stmt` | **2653** | `if x: stmt` / `fn name(): stmt` (Phase 1) |
| `one_line_arm_return` | **293** | `Pat => return x` / `da x` (Phase 2) |
| `struct_literal_or_other` | 270 | **Keep verbatim** — `Foo { ... }` literal |
| `multi_line_block` | 186 | already covered by existing `to_terse` |
| `match_arm_open` | 98 | already kept verbatim by `to_terse` |
| `one_line_arm_other` | 64 | mostly multi-stmt one-liners (`{ let _ = x; return y }`) — **expand to multi-line colon** rather than collapse, see decision below |
| `expression_brace` | 7 | leave unchanged — `let r = if cond { ... }` etc. |

The two single-line shapes (`one_line_stmt` + `one_line_arm_return`)
together account for **2,946 of 3,571 openers (82.5%)** in
`mapanare/self/`. These are the openers that are *currently
deprecated* but *cannot be safely migrated* by today's `to_terse`,
because the canonical colon form would expand them onto two extra
lines (opener + body + closer is also two lines after `}` is
dropped, but the body line is at deeper indent and reads worse than
the original brace one-liner).

### `tests/golden/*.mn`

| Shape | Count |
|---|---:|
| `struct_literal_or_other` | 41 |
| `one_line_arm_other` | 42 |
| `one_line_arm_return` | 17 |
| `multi_line_block` | 2 |
| `match_arm_open` | 1 |
| `one_line_stmt` | 1 |

Most golden braces are struct literals (false-positive risk: not
real block openers) and one-line match-arm bodies. Goldens are
ABI / IR snapshot tests; we should *not* touch their `.ref.ll`
expected-output files. `to_terse` migration of a golden `.mn` is
acceptable iff the lowered AST is bit-identical (verified by
re-running `mnc-stage1` against the migrated source and comparing
against the existing `.ref.ll`). Phase 5 leaves goldens for last
and gates them on this verification.

### `stdlib/**/*.mn`

| Shape | Count |
|---|---:|
| `multi_line_block` | 4244 |
| `one_line_stmt` | 1568 |
| `struct_literal_or_other` | 729 |
| `match_arm_open` | 383 |
| `expression_brace` | 357 |
| `one_line_arm_return` | 303 |
| `one_line_arm_other` | 224 |

`stdlib` is a much larger surface (4,244 multi-line + 1,568 one-line
= the 5,812 statement-block openers; the rest are literals or
expression context). Migration is mechanical via
`mnc fmt stdlib/**/*.mn`. This audit does not gate stdlib migration
on Phase 5; the v5.48.0 PROMPT prioritizes `mapanare/self/` and
treats stdlib as a stretch goal.

### `examples/`, other tests, fuzz, etc.

| Area | Total |
|---|---:|
| `examples/**` | 294 (mostly multi-line; small surface) |
| `tests/**` (non-golden) | 595 |
| Other (fuzz, benchmarks, etc.) | 1643 |

These are not on the v5.48.0 migration critical path. Examples are
documentation-shaped and migrating them improves the user-facing
surface; that can ride along with `mnc fmt`.

---

## Migration-rule decisions (locked at Phase 0)

The decisions below are what Phase 1 / 2 / 3 will implement. They
are deliberately narrow — broader grammar moves (if-expression
colon, multi-statement single-line bodies) are explicitly OUT of
scope per `PLAN.md` and stay that way.

### Decision A — single-line statement colon blocks (Phase 1)

Accept exactly these single-line shapes by extending
`_indent_to_braces`:

```mn
fn name(): stmt
if cond: stmt
si cond: da stmt
while cond: stmt
mien cond: stmt
for x in xs: stmt
cada x in xs: stmt
loop: stmt
else: stmt
sino: stmt
do: stmt
```

Implementation rule: a line of the form
`<known_stmt_block_opener_head>: <non-empty body that does NOT end with ":">`
preprocesses to the same brace stream as
`<head> { body }`. The body must be exactly one *statement* — comma-
body openers (`struct`, `enum`, `match`, `tipo`, `modo`, `way`) are
explicitly rejected from one-line shorthand because their bodies
need the multi-line comma-separated grammar.

Reject one-line forms when the head is a comma-body opener:

```mn
struct Point: x: Int    # rejected — keep multi-line
enum Color: Red         # rejected — keep multi-line
match e: Pat => 1       # rejected — match needs body block
```

The rejection diagnostic says "single-line colon blocks are not
supported for `struct` / `enum` / `match` — use a multi-line block".

### Decision B — single-line match-arm statement shorthand (Phase 2)

Accept these match-arm body shapes as a one-statement BlockBody:

```mn
match e:
    IntLit(n) => return n
    FloatLit(f) => da f
    Pat => break
    Pat => sal
    Pat => continue
    Pat => sigue
    Pat => pass
```

Lowering: each of these constructs the same AST as
`Pat => { return n }` — i.e. an arm whose body is a one-statement
`BlockBody`, NOT an expression arm. Existing expression arms
(`Pat => k = 1`, `Pat => some_expr`) keep parsing through the
existing expression-arm path.

Multi-statement one-line arm bodies like
`_ => { let empty: List<Expr> = []; return empty }` have NO
single-line shorthand in v5.48.0. Phase 3 expands them to multi-
line colon shape:

```mn
_ =>
    let empty: List<Expr> = []
    return empty
```

That expansion is conservative (it adds two source lines) but it
preserves the brace-free invariant and keeps the rule narrow.

### Decision C — formatter migration (Phase 3)

Required rewrites:

```mn
if x { return y }      ->  if x: return y
si x { da y }          ->  si x: da y
while x { break }      ->  while x: break
fn main() { print(x) } ->  fn main(): print(x)
Pat => { return x }    ->  Pat => return x
Pat => { da x }        ->  Pat => da x
Pat => { k = 1 }       ->  Pat => k = 1
Pat => { print(x) }    ->  Pat => print(x)
```

Required non-rewrites (verified by negative tests in Phase 3):

```mn
let x = if cond { 1 } else { 2 }    # if-expression
let p = Point { x: 1, y: 2 }        # struct literal
let m: Map<String, Int> = #{}       # empty map literal
extern "C" { fn foo() -> Int }      # FFI block
```

Alias preservation: `da` stays `da`, `return` stays `return`. Same
for `sal`/`break`, `sigue`/`continue`. The formatter never
normalizes one alias to the other.

### Decision D — `mnc fmt --check`

`mnc fmt --check` should fail on any one-line brace source that the
new rules can migrate. The CLI flag `--keep-braces` opts back into
the legacy "format but do not migrate" behavior for users with
external tooling that grep the warning.

### Decision E — bootstrap mirror (Phase 4)

`mapanare/self/parser.mn` already implements colon-block
preprocessing via `parse_match_arm_item` and the indent-to-braces
mirror. Phase 4 extends both halves:

1. The colon-block preprocessor mirror accepts the new single-line
   shape after a known statement-block opener.
2. `parse_match_arm_item` accepts `return` / `da` / `break` / `sal`
   / `continue` / `sigue` / `pass` after `=>` and lowers to the
   same `BlockBody` shape the brace form produces today.

Tests confirm Python and stage1 accept the same syntax and reject
the same out-of-scope syntax.

---

## Edge cases identified at audit and routed forward

1. **`extern "C" {` blocks** — present in `stdlib/sys/*.mn`. These
   already classify as `expression_brace` in the heuristic (no
   stmt keyword); Phase 3 must NOT migrate them. The
   `_looks_like_stmt_block_opener` filter already excludes
   `extern` because it is not a statement keyword in
   `_STMT_BLOCK_KEYWORDS` — but `extern` IS in `_STMT_BLOCK_PREFIXES`
   (after-stripping behavior). The filter behavior is correct
   because after stripping `extern `, the remaining `"C"` does
   not match any stmt keyword. **Already safe.**
2. **`Pat => { let x = ...; return y }`** — multi-statement
   single-line arm bodies. v5.48.0 has no shorthand for these.
   Phase 3 either:
   (a) expands them to multi-line colon arm body, OR
   (b) leaves them in brace form (they continue to warn).
   PLAN says "preserve braces in single-line shape if a one-line
   colon shape cannot be proved safe." We choose (b) — leave them
   in brace form and document the limitation. The warning will
   continue to fire; v6.0 grammar can decide whether
   `Pat => stmt; stmt` is worth supporting.
3. **`fn name() {}`** — empty function body. Existing `to_terse`
   already expands `{}` to `:` + `pass`. Phase 3 keeps that
   behavior.
4. **`match X { ... }` with multi-line arms** — already kept
   verbatim by the formatter via `_find_match_verbatim_lines`.
   That logic remains untouched in v5.48.0; the new arm shorthand
   is for the *single-line* arm bodies only.
5. **Inline comments after the body** — `if x { return y } // note`
   migrates to `if x: return y // note`. Phase 3 preserves
   trailing comments via the existing line-based architecture.
6. **Nested one-liners** — `if x { if y { return z } }`. After
   migration, becomes `if x: if y: return z`. The grammar accepts
   this (one statement is "another single-line if"), but the
   readability suffers. Phase 3 takes the conservative path:
   migrate one level only — if the body of an outer one-liner is
   itself a brace block, leave the outer in brace form. Negative
   test guards this. (Audit found 0 such nests in
   `mapanare/self/`.)

---

## Stop-condition checks

The PROMPT lists five stop conditions for Phase 5 source migration.
Phase 0 confirms none of them are tripped at HEAD:

| Stop condition | Status |
|---|---|
| Single-line colon parsing requires broad grammar changes beyond the preprocessor | NOT TRIPPED — preprocessor extension only |
| `Pattern => return expr` needs invasive lowering | NOT TRIPPED — narrow `BlockBody` construction in transformer |
| Formatter cannot distinguish expression-context braces reliably | NOT TRIPPED — existing `_looks_like_stmt_block_opener` already handles the discriminator |
| Stage1 and Python parser behavior diverge after mirror work | DEFERRED — verified after Phase 4 |
| Strict fixed point breaks for a reason unrelated to formatting | DEFERRED — verified after Phase 5 |

---

## Phase 0 sign-off

Audit complete. No premise from `PLAN.md` is invalidated; no
load-bearing scope change required. Proceed to Phase 1.

The aggregate-state framing for the rest of v5.48.0:

- **First-party self-host migration target:** 2946 single-line
  brace openers (`one_line_stmt` + `one_line_arm_return` in
  `mapanare/self/`, excluding `mnc_all.mn`). These are the openers
  that are *currently deprecated AND currently un-migratable* by
  the formatter, and Phase 1 + Phase 2 + Phase 3 together close
  that gap.
- **Stretch:** stdlib `one_line_stmt` (1568) + `one_line_arm_return`
  (303). Same migration path; not on the critical release gate.
- **Out of scope:** `one_line_arm_other` multi-stmt bodies (288
  across self+stdlib). v6.0 grammar may revisit.
