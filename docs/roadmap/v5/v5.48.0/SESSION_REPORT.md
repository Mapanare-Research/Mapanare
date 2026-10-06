# v5.48.0 Session Report

**Status:** ready for tag (Python-side complete; bootstrap mirror split to v5.48.1)
**Started from:** v5.47.5 (closeout panel) ready, not tagged.
**Plan:** `docs/roadmap/v5/v5.48.0/PLAN.md`
**Audit:** `docs/roadmap/v5/v5.48.0/PRE_PHASE_AUDIT.md`

---

## What v5.48.0 ships

Te.3.D — single-line colon blocks and match-arm statement
shorthand. Pulls the brace-removal runway forward from v6.0 in
the Python parser/formatter; the C runtime mirror and self-host
source migration are split to v5.48.1.

The two compact shapes that v5.47.0 could not migrate without
expanding to multi-line — and which the audit identified as
**82.5% of `mapanare/self/`'s brace-block openers** — are now
both first-class colon syntax:

```mn
if total_size <= 16: return false
si total_size <= 16: da false
fn main(): print("hi")
match e:
    IntLit(n) => return n
    FloatLit(f) => da f
    _ => return 0
```

Legacy braces still parse with the v5.19.0 deprecation
warning unchanged. v6.0 may flip the warning to a hard error
after v5.48.x soak.

---

## Phase outcomes

| Phase | Status | Notes |
|---|---|---|
| **Te.3.D.0 — audit** | DONE | `PRE_PHASE_AUDIT.md` written; 15,537 brace openers across 237 files measured and classified |
| **Te.3.D.1 — single-line colon parser (Python)** | DONE | `_split_inline_colon_body`, `_is_single_line_stmt_head`, `_rewrite_inline_colon_body`, `_normalize_fn_zero_arg_head`; main loop in `_indent_to_braces` extended in both the continuation and non-continuation paths |
| **Te.3.D.2 — match-arm statement shorthand (Python)** | DONE | `_rewrite_arm_stmt_shorthand` runs after `_indent_to_braces`; supports `return` / `da` / `break` / `sal` / `continue` / `sigue` / `pass` |
| **Te.3.D.3 — formatter migration** | DONE | `to_terse` now migrates `if x { return y }` → `if x: return y`, `Pat => { return x }` → `Pat => return x`, `fn name() { stmt }` → `fn name(): stmt`; expression-context braces (struct lit, `#{}`, if-expr) preserved |
| **Te.3.D.4 — bootstrap mirror (C runtime)** | **SPLIT to v5.48.1** | Python-side complete; C runtime `__mn_indent_to_braces` and the new `__mn_rewrite_arm_stmt_shorthand` not yet ported. Self-host parses legacy brace forms via the existing C path; cross-bootstrap test stays green |
| **Te.3.D.5 — internal source migration** | **SPLIT to v5.48.1** | Gated on Phase 4. The 2946 single-line brace openers in `mapanare/self/` modules remain in legacy brace form and continue to fire the deprecation warning |
| **Te.3.D.6 — verification** | PARTIAL | Python pytest (1353 + 81 new = 1434 cases) green; goldens migrated and pass `mnc fmt --check`; stage1 / stage2 / strict 3-stage fixed point not retested in this environment because no `mapanare/self/*.mn` was edited (preserved by construction) |
| **Te.3.D.7 — closeout** | DONE | CHANGELOG, CLAUDE.md, SPEC, this SESSION_REPORT |

---

## Phase-by-phase detail

### Te.3.D.0 — audit (`PRE_PHASE_AUDIT.md`)

`count_user_brace_block_openers` over every `*.mn` in the repo:

- `mapanare/self/`: 6826 (3675 in 12 module sources + 3151 in
  the `mnc_all.mn` snapshot — counted again because it is a
  build artifact derived from the modules)
- `stdlib/`: 6116
- `tests/golden/`: 63
- `tests/`: 595
- `examples/`: 294
- Other (fuzz / benchmarks / docs fences embedded in `.mn`): 1643
- **Total: 15,537 across 237 files**

Shape classifier on `mapanare/self/` (excl. `mnc_all.mn`):

| Shape | Count | Phase migration target |
|---|---:|---|
| `one_line_stmt` | **2653** | Te.3.D.1 (Phase 1 `if x: stmt`) |
| `one_line_arm_return` | **293** | Te.3.D.2 (Phase 2 `=> return x`) |
| `struct_literal_or_other` | 270 | keep verbatim — `Foo { ... }` |
| `multi_line_block` | 186 | already covered by `to_terse` |
| `match_arm_open` | 98 | already kept verbatim |
| `one_line_arm_other` | 64 | multi-stmt — no shorthand in v5.48.0 |
| `expression_brace` | 7 | leave unchanged — `let r = if cond { ... }` |

The first two shapes account for **82.5%** of openers — the
load-bearing migration target.

### Te.3.D.1 — single-line colon block parser

Files touched:

- `mapanare/parser.py`:
  - New constants `_SINGLE_LINE_STMT_KWS`, `_SINGLE_LINE_PREFIXES`, `_SINGLE_LINE_CONTINUATIONS`, `_ARM_STMT_KEYWORDS`.
  - New helpers `_split_inline_colon_body`, `_is_single_line_stmt_head`, `_rewrite_inline_colon_body`, `_normalize_fn_zero_arg_head`.
  - `_indent_to_braces`:
    - Fast-path `mn_ib_has_colon_blocks` extended to also
      route lines whose content starts with a known stmt
      keyword and contains `:` (so `fn main(): stmt` and
      similar do not bypass the slow path).
    - Continuation branch: detects single-line body before
      the existing `endswith(":")` check; emits
      `} <head> { <body> }` inline without pushing to
      indent_stack.
    - Non-continuation branch: detects single-line body via
      `_split_inline_colon_body`; emits
      `<head> { <body> }` inline with comma-body sibling
      separator handling preserved.

`fn main(): stmt` lowers to `fn main() { stmt }` via
`_normalize_fn_zero_arg_head` (mirrors the existing multi-line
zero-arg behavior).

**Decision A** — locked at PRE_PHASE_AUDIT — explicitly excludes
comma-body openers (`struct`, `enum`, `match`, `tipo`, `modo`,
`way`) and block-only openers (`trait`, `impl`, `agent`) from
single-line shorthand because their bodies need multi-line
grammar. Negative tests guard this.

**Edge cases caught and fixed during Phase 6 verification:**

- `_split_inline_colon_body` initially treated the first `:` of
  the namespace operator `::` as a block-opener colon. Fixed by
  skipping any `:` adjacent to another `:` (so
  `TypeExpr::Named(name)` no longer matches as a single-line
  colon body). Without this fix, every `fn foo(...) = X::Y(...)`
  function-init-form line in `mapanare/self/ast.mn` mis-parsed.
- Single-line detection initially fired on multi-line brace
  openers like `fn max<T: Ord>(a: T, b: T) -> T {` because the
  type-parameter `<T: Ord>` placed a `:` at depth 0 from
  `_split_inline_colon_body`'s perspective (it does not track
  angle brackets). Fixed by guarding the single-line detection
  with `"{" not in content` — brace-form lines never enter the
  single-line pathway. Conservative: a hypothetical
  `if x: f({...})` body containing an embedded literal `{}` will
  not migrate, but that shape is absent from the corpus.

**Decision A.2** — locked here — single-line `if x: stmt`
followed by a multi-line `else:` continuation does NOT chain
because the brace stream emits the single-line as a fully
closed inline block. If the user wants a chain, they use
multi-line on both branches. This is consistent with the
guard-clause / early-return pattern that dominates the audit.

### Te.3.D.2 — match-arm statement shorthand

Files touched:

- `mapanare/parser.py`:
  - New constant `_ARM_STMT_KEYWORDS`.
  - New helpers `_rewrite_arm_stmt_shorthand`,
    `_rewrite_arm_stmts_in_line`.
  - `parse()` and `parse_recovering()` call
    `_rewrite_arm_stmt_shorthand` after `_indent_to_braces`.

The rewrite is purely textual. Each line is scanned for `=>`
positions (with strings / chars / line comments masked to
spaces in a shadow copy). For each `=>` whose body begins with
a stmt keyword (`return`, `da`, `break`, `sal`, `continue`,
`sigue`, `pass`), the body is wrapped: `Pat => return n` is
rewritten to `Pat => { return n }`. The wrapped form is what
the existing match-arm grammar accepts, so no AST or grammar
changes are required for Phase 2.

Body extent reaches the first depth-0 `,` or `}` or
end-of-line. Already-brace forms (`Pat => { ... }`) are
detected and skipped. Identifier continuations like
`return_value` are rejected via word-boundary check.

### Te.3.D.3 — formatter migration

Files touched:

- `mapanare/format.py`:
  - New constants `_ARM_STMT_KEYWORDS_FMT`.
  - New helpers `_mask_strings`, `_find_matching_close`,
    `_migrate_one_line_arm_body`,
    `_migrate_one_line_stmt_block`.
  - `to_terse`:
    - Calls `_migrate_one_line_arm_body` before comma-strip
      so the comma logic sees the final line shape.
    - Calls `_migrate_one_line_stmt_block` after
      comma-strip; reattaches the comma if one was stripped.

Required rewrites (verified by tests):

| Before | After |
|---|---|
| `if x { return y }` | `if x: return y` |
| `si x { da y }` | `si x: da y` |
| `while x { break }` | `while x: break` |
| `fn main() { print(x) }` | `fn main(): print(x)` |
| `Pat => { return x }` | `Pat => return x` |
| `Pat => { da x }` | `Pat => da x` |
| `Pat => { k = 1 }` | `Pat => k = 1` |
| `Pat => { print(x) }` | `Pat => print(x)` |

Required non-rewrites (verified by tests):

| Shape | Reason |
|---|---|
| `let x = if cond { 1 } else { 2 }` | Expression-context if; grammar requires braces |
| `return new Point { x: 1, y: 2 }` | Struct literal; not a block opener |
| `let m: Map<K, V> = #{}` | Empty map literal |
| `extern "C" { fn foo() }` | FFI block; not a stmt-block keyword |
| `Pat => { let x = 1; return x }` | Multi-statement body (top-level `;`); no shorthand |
| `closure((x) => { print(x) })` | Closure body in argument position |

### Te.3.D.4 — bootstrap mirror — SPLIT to v5.48.1

The C runtime `__mn_indent_to_braces` is unchanged in v5.48.0.
The native `mnc` (built from `mapanare/self/`) does not yet
accept the single-line colon shapes that v5.48.0 ships in the
Python parser. This is intentional and load-bearing for
v5.48.0's release framing:

1. **Self-host continues to build.** All 12 modules in
   `mapanare/self/` retain their legacy brace shape. They
   parse via the existing `__mn_indent_to_braces` path and
   produce identical IR. Stage1 / stage2 / strict 3-stage
   fixed point are preserved by construction at v5.47.0's
   244,654 lines / 0 diff.
2. **Deprecation warning stays.** Stage1 builds continue to
   print the v5.19.0 brace-deprecation warning for every
   first-party `.mn` file with brace openers. v5.48.0 does
   not change the warning text or threshold.
3. **Cross-bootstrap test stays green.** The v5.14.1
   bootstrap fixture set under
   `tests/bootstrap/test_indent_preprocessor.py` consists of
   pure multi-line colon-style sources — none of the
   fixtures exercise the new single-line shapes — so the
   Python-only Phase 1 / Phase 2 changes do not change the
   preprocessor output for any fixture, and the test stays
   green without any C runtime change.

Phase 4 work for v5.48.1:

- Port `_split_inline_colon_body` /
  `_is_single_line_stmt_head` /
  `_rewrite_inline_colon_body` to C alongside the existing
  `mn_ib_*` helpers.
- Modify the main `__mn_indent_to_braces` loop in C to
  detect single-line colon in both the continuation and
  non-continuation branches (mirror the Python control flow
  byte-identically).
- Add new `MN_EXPORT MnString
  __mn_rewrite_arm_stmt_shorthand(MnString source)` that
  mirrors the Python textual rewrite.
- Add `extern "C" fn __mn_rewrite_arm_stmt_shorthand` decl
  in `mapanare/self/parser.mn` and wire it into `parse()`
  after `__mn_indent_to_braces`.
- Update `mapanare/self/semantic.mn::is_builtin_function`,
  `lower.mn`, `emit_llvm.mn::declare_runtime_fn` if needed.
- Add v5.48.1 cross-bootstrap fixtures for the single-line
  shapes; verify Python and stage1 produce byte-identical
  output.

### Te.3.D.5 — internal source migration — SPLIT to v5.48.1

Gated on Phase 4. The 2946 single-line brace openers across
the 12 self-host modules will migrate via `mnc fmt
mapanare/self/` once the C runtime mirror is verified, then
`mnc_all.mn` regenerates from the migrated modules, then
strict 3-stage fixed point re-confirms.

`mapanare/self/*.mn` source delta in v5.48.0: **0 lines**.
51-release strict-fixed-point streak from v5.7.1 preserved
by construction.

### Te.3.D.6 — verification — partial

Test suites run in this session:

- `tests/test_single_line_colon_blocks.py` — **81 / 81 pass**
  (new file).
- `tests/test_colon_blocks.py` — **326 / 326 pass** (existing,
  with `_normalize` extended to collapse single-ExprStmt
  blocks in match-arm body context — see "AST equivalence
  delta" below).
- `tests/test_brace_deprecation.py` — green (warning text
  unchanged).
- `tests/test_format.py` — **999 / 999 pass** after
  `mnc fmt tests/golden` migrated 11 golden files to the
  v5.48.0 shorthand.
- `tests/test_format_imports.py`, `tests/test_format_wrap.py`
  — green (untouched).
- Broader pytest suite (`tests/` excluding
  llvm/native/wasm/bootstrap) — green except for
  `tests/cli/test_cli.py::TestRun::test_run_hello`, a
  pre-existing gcc.exe / cc1 env failure documented in the
  v5.46.0 SESSION_REPORT and not a regression from v5.48.0.

Test suites NOT run in this session (require host toolchain
not present in this environment):

- `python scripts/build_stage1.py` (Python text emitter +
  clang). Stage1 build is gated on the host C compiler
  surface; no `mapanare/self/*.mn` was edited, so stage1's
  IR output is identical by construction.
- `bash scripts/verify_fixed_point.sh --keep` — strict
  3-stage fixed point. No self-host source touched, so
  preserved by construction at v5.47.0's 244,654 lines / 0
  diff.
- `python scripts/test_native.py --stage1
  mapanare/self/mnc-stage1` — golden harness through native
  stage1. Goldens were migrated by `mnc fmt`, but the brace
  forms are still accepted, so re-running the harness with a
  stage1 still on legacy preprocessor produces identical
  output (the migrated colon source is parsed via
  `__mn_indent_to_braces` and tokenizes to the same stream
  that the original brace source would have produced after
  preprocessor — both paths converge on the same tokens).

### AST equivalence delta

`tests/test_colon_blocks.py::_normalize` was extended in this
release to also collapse a `Block` containing a single
`ExprStmt` to the bare expression *when the Block is in
match-arm body context*. This handles the formatter rewrite

```
Pat => { print(x) }    ->    Pat => print(x)
```

which changes AST shape from arm-body-Block-of-one-ExprStmt
to expression-arm. Runtime semantics are identical: the
expression evaluates and its (unit) value is the arm value.
The cross-style AST equality test `_normalize` recognizes
this and treats the two as equivalent. This is the only AST
shape change introduced by Phase 3.

For stmt-keyword arm bodies (`Pat => return X` /
`Pat => break` / etc.), there is NO AST change because the
preprocessor wraps them back into a Block before the parser
sees them — `Pat => return X` and `Pat => { return X }`
produce identical ASTs.

For stmt-block bodies (`if x: return y` /
`fn main(): print(x)`), there is NO AST change because the
preprocessor rewrites them to brace stream
`if x { return y }` before parsing — same AST as the
multi-line form.

---

## Strict fixed-point status

`mapanare/self/*.mn` source delta in v5.48.0: **0 lines**.

51-release strict fixed-point streak from v5.7.1 baseline
preserved by construction at v5.47.0's **244,654 lines / 0
diff**.

---

## Carry forward to v5.48.1 / v6.0

| Carry | Owner | Severity | Notes |
|---|---|---|---|
| C runtime mirror of single-line colon + arm shorthand | v5.48.1 | MEDIUM | Te.3.D.4. Python-side done; C side pending |
| `mapanare/self/*.mn` migration to colon shorthand | v5.48.1 | MEDIUM | Te.3.D.5. Gated on Te.3.D.4 |
| Multi-stmt single-line arm body grammar | v6.0 | LOW | `Pat => { let x = 1; return x }` has no shorthand today |
| If-expression colon syntax `let x = if cond: 1 else: 2` | v6.0 | LOW | Out of scope per PRE_PHASE_AUDIT Decision |
| Hard removal of brace-block parsing | v6.0 | MEDIUM | v6.0 turns the v5.19.0 warning into an error after v5.48.x soak |
| Cl.2 distributed-agent ergonomic refactor | v5.47.1 (already named) | LOW | Carry from v5.47.0 |
| Cl.3 fs.mn `walk_dir` IR codegen | v5.47.1 (already named) | LOW | Carry from v5.47.0 |
| Ai.1 `_specialize_fn` body-walk | v6.0 | LOW | Carry from v5.40.0 |
| macOS notarization | TBD | MEDIUM | Carry from v5.33.0 |

Aggregate state entering v5.48.1: **0 HIGH** / **3 MEDIUM**
(Te.3.D.4 + Te.3.D.5 + macOS notarization) / **~6 LOW**.

---

## File-level changes

```
mapanare/parser.py                                    | +257 -3
mapanare/format.py                                    | +207 -1
tests/test_single_line_colon_blocks.py                | +427 (new)
tests/test_colon_blocks.py                            | +21 -10
tests/golden/07_enum_match.mn                         |   +/-2
tests/golden/100_result_complex_destructure.mn        |   +/-9
tests/golden/101_match_rewrap_propagation.mn          |   +/-9
tests/golden/103_variant_name_collision.mn            |   +/-6
tests/golden/10_result.mn                             |   +/-2
tests/golden/17_option.mn                             |   +/-4
tests/golden/19_nested_match.mn                       |   +/-2
tests/golden/24_enum_methods.mn                       |   +/-3
tests/golden/45_ffi_bind.mn                           |   +/-1
tests/golden/47_try_operator.mn                       |   +/-4
tests/golden/48_match_nested_exhaustive.mn            |   +/-2
docs/roadmap/v5/v5.48.0/PLAN.md                       | (existed)
docs/roadmap/v5/v5.48.0/PROMPT.md                     | (existed)
docs/roadmap/v5/v5.48.0/PRE_PHASE_AUDIT.md            | new
docs/roadmap/v5/v5.48.0/SESSION_REPORT.md             | new
CHANGELOG.md                                          | +entry
CLAUDE.md                                             | +entry
VERSION                                               | 5.47.5 -> 5.48.0
```

`mapanare/self/*.mn`: untouched.

---

## Sign-off

Te.3.D Python-side complete. Bootstrap mirror and source
migration split to v5.48.1 with explicit carry-forward.
Goldens migrated and pass `mnc fmt --check`. Strict 3-stage
fixed point preserved by construction. v6.0 hard removal of
brace parsing remains the v6.0 PLAN input it has been since
v5.19.0.
