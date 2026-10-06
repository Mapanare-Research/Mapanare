# v5.48.0 - Te.3.D - single-line colon blocks and internal brace cleanup

**Status:** PLANNING
**Type:** Language ergonomics + formatter migration release. Pulls the
brace-removal runway forward from v6.0 because the language is still
beta and there is no external compatibility burden worth preserving.
**Breaking:** Soft-breaking internally. Existing brace-style source
continues to parse in v5.48.0 and still emits the stable deprecation
warning, but all first-party source and formatter output move to colon
canonical form. v6.0 may still hard-error on braces after this release.
**Prerequisite:** v5.47.5 closeout panel shipped or explicitly deferred.
If v5.47.5 remains unshipped, v5.48.0 is a targeted v5 patch before the
v6.0 borrow-checker arc.
**Estimated effort:** 1-2 sessions. Parser + formatter + bootstrap
mirror + mechanical self-host migration. Medium risk because this
touches parse preprocessing and self-host source shape, but the intended
semantic delta is zero.

---

## Why this exists

The original terseness arc deprecated brace blocks and made colon blocks
canonical, but it left a real ergonomic regression: common one-liners
like this:

```mn
if total_size <= 16 { return false }
Some(x) => { return x }
fn main() { print("hi") }
```

currently migrate to longer multi-line colon blocks, or are left in
legacy brace form because `mnc fmt` cannot prove a safe one-line
replacement. That defeats the point of the terseness work for guard
clauses, small command bodies, and match-arm returns.

The better answer is not "allow braces forever on one-liners." That
keeps two block syntaxes alive permanently and makes v6.0's promised
hard removal fuzzy. The cleaner answer is:

```mn
if total_size <= 16: return false
si total_size <= 16: da false
Some(x) => return x
Some(x) => da x
fn main(): print("hi")
```

v5.48.0 ships that missing surface now, migrates first-party source, and
keeps the warning for any remaining legacy input.

---

## Goals

1. **Te.3.D.0** - Phase 0 audit: count and classify all remaining
   first-party brace-block warnings, especially one-line `if`, `fn`, and
   `match` arm shapes in `mapanare/self/*.mn`.
2. **Te.3.D.1** - Add single-line colon blocks for statement-level block
   openers where the body is exactly one statement on the same line.
3. **Te.3.D.2** - Add single-line match-arm statement shorthands for the
   stubborn brace forms that are not expression arms today, especially
   `Pattern => return expr`.
4. **Te.3.D.3** - Teach `mnc fmt` / `mapanare fmt` to migrate one-line
   brace blocks to one-line colon or direct match-arm forms instead of
   expanding to multi-line blocks or preserving braces.
5. **Te.3.D.4** - Migrate internal `.mn` sources, especially
   `mapanare/self/*.mn`, to the new canonical shape so stage1 builds stop
   printing thousands of first-party brace warnings.
6. **Te.3.D.5** - Preserve the warning surface for legacy brace input:
   parse still works, `MAPANARE_NO_BRACE_WARNING=1` still suppresses,
   and the warning continues to point at `mnc fmt`.
7. **Te.3.D.6** - Bootstrap mirror + native path: Python parser,
   self-hosted parser, and native warning/migration behavior agree.
8. **Te.3.D.7** - Verification: AST equivalence, golden stability,
   strict fixed point, and formatter idempotence.

---

## Syntax decision

### In scope

Single-line colon statement blocks:

```mn
fn main(): print("hi")
if n <= 1: return n
si n <= 1: da n
while ready(): break
for x in xs: print(x)
else: return fallback()
sino: da fallback()
```

Single-line match-arm statement bodies:

```mn
match e:
    IntLit(n) => return n
    FloatLit(f) => da f
    _ => return 0
```

Direct expression / assignment match arms remain preferred where they
already parse:

```mn
match err:
    BadUrl(s) => k = 1
    Timeout(s) => k = 2
```

### Out of scope

- Single-line colon forms for comma-body declarations such as
  `struct Point: x: Int` or `enum Color: Red`. Keep those multi-line.
- New expression-continuation grammar. Newlines inside `(...)`, `[...]`,
  `{...}`, or `#{...}` remain non-continuing unless already supported.
- If-expression colon syntax such as `let x = if cond: 1 else: 2`.
  Existing if-expression brace grammar stays until a separate design.
- Full hard removal of brace parsing. v5.48.0 makes braces internally
  obsolete and formatter-migratable; v6.0 can convert the warning to an
  error after this soak.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.3.D.0** | HIGH (gate) | **Phase 0 audit.** Run the existing brace detector across `mapanare/self/*.mn`, `tests/golden/*.mn`, `stdlib/**/*.mn`, examples, and docs code fences. Classify counts into: one-line statement block, one-line match arm, multi-line block, expression-context brace, struct/map literal false-positive risk. Output: `docs/roadmap/v5/v5.48.0/PRE_PHASE_AUDIT.md`. | 2h |
| **Te.3.D.1** | HIGH | **Single-line colon block parser.** Extend Python `_indent_to_braces` so `if x: stmt`, `fn main(): stmt`, `while x: stmt`, `for x in xs: stmt`, `else: stmt`, and Spanish forms lower to the same brace stream as their multi-line equivalents. Reject ambiguous comma-body openers on one line with a clear diagnostic. Mirror in `mapanare/self/parser.mn`. | 4h |
| **Te.3.D.2** | HIGH | **Single-line match-arm statement shorthand.** Permit `Pattern => return expr`, `Pattern => da expr`, `Pattern => break` / `sal`, `Pattern => continue` / `sigue`, and `Pattern => pass` by lowering them to a one-statement `BlockBody`. Keep normal expression arms unchanged. This gives `=> { return x }` and `=> { da x }` brace-free compact replacements without forcing every helper into `return match ...`. Mirror in self-host parser/lowering where needed. | 3h |
| **Te.3.D.3** | HIGH | **Formatter migration.** Update `mapanare/format.py::to_terse` and CLI default formatting so one-line block braces migrate to compact colon/direct-arm forms: `if x { return y }` -> `if x: return y`, `si x { da y }` -> `si x: da y`, `fn main() { print("hi") }` -> `fn main(): print("hi")`, `Pat => { return x }` -> `Pat => return x`, `Pat => { da x }` -> `Pat => da x`, `Pat => { k = 1 }` -> `Pat => k = 1`. Preserve expression-context braces (`if` expressions, struct literals, `#{}` maps, closure bodies if still required). Preserve the source spelling of aliases rather than forcing `da` to `return` or vice versa. | 5h |
| **Te.3.D.4** | HIGH | **Internal source migration.** Run the new formatter over `mapanare/self/*.mn` module-by-module. Do not rewrite unrelated style. Commit discipline: after each cluster, rebuild stage1 and keep strict fixed point. `mnc_all.mn` regeneration must reflect the migrated module order. | 4h |
| **Te.3.D.5** | MEDIUM | **Warning surface preservation.** `count_user_brace_block_openers` still detects legacy brace blocks, including one-line shapes. Warning text remains stable except, optionally, replacing "Hard removal in v6.0" with "Hard removal after v5.48.0 soak" only if the release owner decides the old text is now misleading. `MAPANARE_NO_BRACE_WARNING=1` behavior unchanged. | 1h |
| **Te.3.D.6** | HIGH (gate) | **Bootstrap/native mirror.** Python parser, self-host `parser.mn`, concatenated `mnc_all.mn`, and native warning path agree on accepted syntax and warning behavior. Add cross-bootstrap tests for every new accepted shape. | 4h |
| **Te.3.D.7** | HIGH (gate) | **Tests.** New `tests/test_single_line_colon_blocks.py`; extend `tests/test_colon_blocks.py`, `tests/test_brace_deprecation.py`, formatter tests, and bootstrap mirror tests. Include negative tests for `struct Point: x: Int`, one-line comma-body match blocks, and expression-context braces that must not migrate. | 4h |
| **Te.3.D.8** | HIGH (gate) | **Verification.** `pytest tests/test_single_line_colon_blocks.py tests/test_colon_blocks.py tests/test_brace_deprecation.py tests/test_format.py`; goldens; stage2; strict 3-stage fixed point; `mnc fmt --check mapanare/self/` passes without brace warnings from first-party self-host modules. | 3h |
| **Te.3.D.9** | MEDIUM | **Docs and closeout.** SPEC section 4.0 updated: single-line colon blocks are shipped in v5.48.0; brace-style remains legacy parse-only with warning. Formatter guide updated with one-line migration examples. CHANGELOG, CLAUDE.md, SESSION_REPORT. | 2h |

---

## Phase plan

- **Phase 0** - Audit. Produce `PRE_PHASE_AUDIT.md`; decide exact
  migration rules before implementation.
- **Phase 1** - Python parser single-line colon support
  (`_indent_to_braces`) with focused tests.
- **Phase 2** - Match-arm statement shorthand. Keep this narrow:
  `return`, `break`, `continue`, `pass` only unless Phase 0 proves a
  broader statement-arm grammar is required.
- **Phase 3** - Formatter migration rules. Lock idempotence and
  AST-equivalence before touching first-party source.
- **Phase 4** - Bootstrap mirror in `mapanare/self/parser.mn` and any
  native generated path required by the build.
- **Phase 5** - Internal source migration, module-by-module.
- **Phase 6** - Full rebuild, goldens, stage2, strict fixed point.
- **Phase 7** - Docs, changelog, CLAUDE.md, SESSION_REPORT.

---

## Risk

1. **Parser ambiguity.** Single-line `:` is already meaningful in type
   annotations and map/struct syntax. Mitigation: only enable the new
   form after known statement-level block openers; keep comma-body
   declaration one-liners out of scope.
2. **Formatter false positives.** `Foo {}` and `#{}` must never become
   blocks. `if` expressions must keep expression braces until a separate
   expression-colon design exists. Mitigation: re-use the existing
   statement-block-opener filter and add negative tests.
3. **Match-arm lowering drift.** `Pattern => return x` must be a
   `BlockBody`, not an expression arm. Mitigation: lower it by
   constructing the same AST shape as `Pattern => { return x }`.
4. **Self-host churn.** Migrating thousands of one-line braces can hide a
   semantic regression. Mitigation: module-by-module formatting,
   rebuilds, AST equivalence checks, strict fixed point.
5. **Warning text churn.** Downstream CI may grep the warning. Mitigation:
   keep wording stable in v5.48.0 unless there is a strong reason to
   change the v6.0 hard-removal sentence.

---

## Success criteria

- Single-line colon blocks parse in Python and self-host paths.
- `if x { return y }` formats to `if x: return y`.
- `fn main() { print("hi") }` formats to `fn main(): print("hi")`.
- `Pat => { return x }` formats to `Pat => return x`.
- First-party self-host modules no longer emit brace-deprecation warnings
  during stage1 builds.
- Legacy brace input still parses with the existing warning.
- Formatter is idempotent on migrated source.
- AST/IR output for migrated first-party code is equivalent.
- Goldens pass; stage2 validates; strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes now:**
- The practical blocker that made brace removal feel like a terseness
  regression: one-line guard clauses and match-arm returns.
- The self-host warning flood caused by legitimate but legacy one-line
  brace blocks.

**Leaves for v6.0:**
- Turning legacy brace parsing from warning into hard error.
- If-expression colon syntax, if still desired.
- Any broader multi-statement single-line syntax beyond the narrow
  one-statement form shipped here.
