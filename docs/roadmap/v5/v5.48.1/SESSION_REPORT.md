# v5.48.1 Session Report

**Status:** ready for tag
**Started from:** v5.48.0 (Python-side complete; bootstrap mirror +
self-host source migration explicitly split).
**Plan:** `docs/roadmap/v5/v5.48.1/PLAN.md`
**Audit:** `docs/roadmap/v5/v5.48.1/PRE_PHASE_AUDIT.md`

---

## What v5.48.1 ships

Te.3.D.4 (bootstrap mirror) + Te.3.D.5 (self-host source migration).
Closes the v5.48.0 carry-forward: brings the C runtime preprocessor +
arm-shorthand rewriter to parity with the v5.48.0 Python parser, and
migrates `mapanare/self/*.mn` to the new shorthand so the v5.19.0
brace-deprecation warning silences on the modules that have only
single-line stmt-block openers.

Single-line shapes accepted on both Python and C sides:

```mn
if x > 0: return 1
si x > 0: da 1
fn main(): print(1)
fn pi() -> Float: return 3.14
pub fn ping(): print(1)
async fn run(): print(1)
while ready(): step()
mien ready(): step()
for x in xs: print(x)
cada x in xs: print(x)
else: stmt
sino: stmt
else if x: stmt
sino si x: stmt

match e:
    IntLit(n) => return n
    FloatLit(f) => da f
    Pat => break
    Pat => sal
    Pat => continue
    Pat => sigue
    Pat => pass
```

Negative shapes correctly NOT migrated:

```mn
struct Point: x: Int                     # rejected (comma-body)
let p = Point { x: 1, y: 2 }             # struct literal preserved
let r = if cond { 1 } else { 2 }         # if-expression preserved
extern "C" { fn foo() -> Int }           # FFI block preserved
fn max<T: Ord>(a: T, b: T) -> T { ... }  # generic with `<T: Ord>` colon
let x = X::Y::Z                          # `::` namespace preserved
fn make() -> Point = Point { x }         # implicit-return preserved
if ch == "{": return X                   # `{` in string literal still migrates
```

---

## Phase outcomes

| Phase | Status | Notes |
|---|---|---|
| **Te.3.D.4.0 — Phase 0 audit** | DONE | `PRE_PHASE_AUDIT.md` re-confirms v5.48.0 totals (6,826 brace openers across 18 self-host files); per-module shape breakdown; cross-bootstrap fixture surface enumerated; 4-cluster migration plan locked. |
| **Te.3.D.4.1 — C helpers** | DONE | `mn_ib_split_inline_colon`, `mn_ib_is_single_line_stmt_head`, `mn_ib_rewrite_inline_colon_body`, `mn_ib_normalize_fn_zero_arg_head`, `mn_ib_contains_byte`, `mn_ib_contains_byte_unquoted` added to `runtime/native/mapanare_core.c`. |
| **Te.3.D.4.2 — fast-path extension** | DONE | `mn_ib_has_colon_blocks` extended with prefix-hint check on `if /si /while /mien /for /cada /fn /pub /async /extern /else /sino /} else /} sino` AND contains `:`. |
| **Te.3.D.4.3 — main loop extension** | DONE | Single-line detection in both branches of `__mn_indent_to_braces`. Continuation branch emits `} <head> { <body> }`; non-continuation emits `<head> { <body> }`. `'{' not in content` guard via `mn_ib_contains_byte_unquoted`. |
| **Te.3.D.4.4 — `__mn_rewrite_arm_stmt_shorthand`** | DONE | `MN_EXPORT MnString` C function mirrors Python line-for-line. |
| **Te.3.D.4.5 — self-host wire-up** | DONE | `parser.mn::parse` calls `__mn_rewrite_arm_stmt_shorthand` after `__mn_indent_to_braces`. Registration in `semantic.mn` / `lower.mn` / `emit_llvm.mn` mirrors `__mn_indent_to_braces` symmetrically. Python bootstrap registers in `types.py`, `lower.py`, and `emit_llvm_text.py` (with drop-glue tracking and Win64 routing matching v5.23.1 Mb.1). |
| **Te.3.D.4.6 — cross-bootstrap test** | DONE | 27 new fixtures; **243/243** byte-identical Python vs C. |
| **Te.3.D.5.0 — pre-migration audit** | DONE (in PRE_PHASE_AUDIT.md) | 4-cluster migration plan with empirical projection (3,675 → 737 residual). |
| **Te.3.D.5.1 — module-by-module migration** | DONE | All 17 modules migrated. Cluster A (10 modules) → cluster B (3 modules) → cluster C (3 modules) → cluster D (1 module). Goldens 103/103 after each cluster. |
| **Te.3.D.5.2 — `mnc_all.mn` regeneration** | DONE | `bash scripts/concat_self.sh` produces 1,025,408-byte concat. |
| **Te.3.D.5.3 — STRICT 3-stage fixed-point** | DONE | **245,115 lines / 0 diff** at v5.48.1. |
| **Te.3.D.6 — verification** | DONE | Goldens 103/103. Cross-bootstrap 243/243. Language test suites (1434 + 161 skipped) green. STRICT fixed-point reached. |
| **Te.3.D.7 — closeout** | DONE | This SESSION_REPORT, CHANGELOG, CLAUDE.md release notes, version bump. |

---

## Phase-by-phase detail

### Te.3.D.4.0 — Phase 0 audit (`PRE_PHASE_AUDIT.md`)

`count_user_brace_block_openers` over `mapanare/self/*.mn` at
v5.48.1 HEAD: 6,826 across 18 files (3,675 in 17 modules + 3,151 in
`mnc_all.mn` snapshot). Matches v5.48.0 audit byte-for-byte.

Empirical migration projection via `mapanare.format.to_terse`:
3,675 → 737 (80% drop). 8 modules silence completely; 9 modules
have residuals (match-arm bodies that v5.48.0 cannot shorthand).

Cross-bootstrap fixture surface enumerated: positive shapes (every
accepted head, English + Spanish, single-line continuation, all 7
arm keywords), negative shapes (struct/enum inline, struct literal,
empty map, if-expression, FFI block, generic with `<T: Ord>` colon,
namespace `::` operator). Total 27 new fixtures.

### Te.3.D.4.1 — C helpers

Pure additions to `runtime/native/mapanare_core.c`:

- `mn_ib_split_inline_colon`: depth-tracked walk to find a top-level
  `:` splitting `(content, n)` into `(head_off, head_len, body_off,
  body_len)`. Skips colons inside `()`/`[]`/`{}`, string/char
  literals; bails on `//`; symmetrically skips `::` namespace
  operator.
- `mn_ib_is_single_line_stmt_head`: strip leading `} ` continuation
  closer; loop-strip `pub `/`async `/`extern ` modifiers; return
  true if the remaining slice matches one of `{fn, if, si, while,
  mien, for, cada}` (with `<space>`/`(`/`<` continuation) or one of
  `{else, sino}` (with `<space>` continuation). Mirrors Python
  `_is_single_line_stmt_head` byte-for-byte.
- `mn_ib_rewrite_inline_colon_body`: bounded recursion. If `body`
  itself parses as `<head>: <body2>` with a stmt-block head, emits
  `<head> { <rewrite(body2)> }`; else appends body verbatim.
- `mn_ib_normalize_fn_zero_arg_head`: rewrites `fn name` →
  `fn name()`, `fn name -> Ret` → `fn name() -> Ret`. Mirrors
  Python `_normalize_fn_zero_arg_head`.

### Te.3.D.4.2 — fast-path extension

`mn_ib_has_colon_blocks` previously triggered only on lines ending
with `:`. Extended with prefix-hint check: walk each line; if
stripped content begins with one of the 14 prefix hints AND
contains `:`, return 1. Mirrors Python `_SINGLE_LINE_PREFIX_HINT`
verbatim.

### Te.3.D.4.3 — main-loop extension

Two insertion points in `__mn_indent_to_braces`:

1. **Continuation branch** (after `mn_ib_is_continuation`): if line
   does not end with `:`, attempt single-line split. If the head is
   a stmt-block opener, emit `<indent>} <head> { <body> }` inline,
   no indent_stack push.
2. **Non-continuation branch** (before `if line_ends_colon`): same
   pattern. The `'{' not in content` guard uses
   `mn_ib_contains_byte_unquoted` (string-literal-aware) so lines
   like `if ch == "{": return X` (the `{` is in a string literal in
   `lexer.mn`) still single-line-migrate.

### Te.3.D.4.4 — `__mn_rewrite_arm_stmt_shorthand`

New `MN_EXPORT MnString __mn_rewrite_arm_stmt_shorthand(MnString
source)` mirrors `mapanare/parser.py::_rewrite_arm_stmt_shorthand`.
Per line: build shadow buffer (string/char/`//` masked to spaces),
walk for `=>` positions, identify keyword at body_start in shadow,
verify membership in the 7-keyword set, check word-boundary-after,
walk body to first depth-0 `,` / `}` / `//` / EOL, emit
`{ <body rstripped> }`. Replacements applied left-to-right
(streaming into a fresh output buffer). Fast path returns a fresh
copy when source has no `=>`.

### Te.3.D.4.5 — self-host wire-up

`mapanare/self/parser.mn::parse`:

```mn
let preprocessed: String = __mn_indent_to_braces(source)
let preprocessed2: String = __mn_rewrite_arm_stmt_shorthand(preprocessed)
let tokens: List<Token> = tokenize(preprocessed2, filename)
```

`mapanare/self/main.mn::run_preprocess` mirrors the same pair so the
cross-bootstrap test compares the full pipeline.

Symmetric registration with `__mn_indent_to_braces`:

- `semantic.mn::is_builtin_function` (line 152): `if name ==
  "__mn_rewrite_arm_stmt_shorthand" { return true }`
- `semantic.mn::register_builtins` (line 2109): symbol entry
- `lower.mn::lower_call_by_name` (line 2188 sibling): typed call
  emission
- `emit_llvm.mn::declare_runtime_fn` (line 1170 sibling):
  `declare {ptr, i64} @__mn_rewrite_arm_stmt_shorthand({ptr, i64})`
- `emit_llvm.mn::emit_call_by_name` (line 3812 sibling): Win64
  ABI route via `emit_rt_call`
- `emit_llvm.mn::is_returns_string_runtime` (line 4590 sibling):
  belt-and-suspenders for V.9 lifecycle leak.

Python bootstrap symmetric with v5.14.1 / v5.23.1 patterns:
`mapanare/types.py::BUILTIN_RETURN_TYPES`,
`mapanare/lower.py::_BUILTIN_RET`, and
`mapanare/emit_llvm_text.py` handler (drop-glue tracking + Win64
routing).

### Te.3.D.4.6 — cross-bootstrap test

27 new fixtures in `tests/bootstrap/test_indent_preprocessor.py`.
Test now compares against the full pipeline
(`_rewrite_arm_stmt_shorthand(_indent_to_braces(src))`) on the
Python side; C side runs `mnc-stage1 preprocess` which now also
runs both. **243 / 243 fixtures pass byte-identically.**

### Te.3.D.5.1 — module-by-module migration

Cluster A (10 modules — abi, emit_llvm_ir, lexer, lower_state, main,
from_go, from_php, from_python, from_typescript, transpiler):
939 → 47 residuals. Rebuild + goldens after: **103/103**.

Cluster B (3 modules — mir, mir_opt, ast):
1,094 → 335 residuals. Rebuild + goldens: **103/103**.

Cluster C (3 modules — semantic, lower, parser):
1,075 → 290 residuals. Rebuild + goldens: **103/103**.

Cluster D (1 module — emit_llvm):
569 → 65 residuals. Rebuild + goldens: **103/103**.

`mnc_all.mn` regenerated via `bash scripts/concat_self.sh`:
1,025,408 bytes / 737 residuals (mirrors per-module residuals).

### Te.3.D.5.3 — STRICT 3-stage fixed-point

```
[Stage 0] stage1: 7,593,144 bytes
[Stage 1] stage2.ll: 245,115 lines  llvm-as: OK
[Stage 2] stage3.ll: 245,115 lines  llvm-as: OK
[Verify] FIXED POINT REACHED — 0 diff

=== La Culebra Se Muerde La Cola ===
```

New baseline: **245,115 lines** (v5.47.0 was 244,654; +461 reflects
the v5.48.1 self-host wiring of the new builtin). 52-release strict
streak from v5.7.1 baseline preserved.

---

## Bugs surfaced + fixed mid-implementation

Two v5.48.0 bugs surfaced when running cluster A migration; both
required fixes before Phase 5 could continue.

### `_migrate_one_line_stmt_block` — implicit-return regression

`mnc fmt mapanare/self/lexer.mn` rewrote
`fn new_token(...) -> Token = new Token { ... }`
to
`fn new_token(...) -> Token: new Token: ...`
— corrupting 88 sites. The v5.48.0 formatter's
`_looks_like_stmt_block_opener` accepted heads that began with
`fn`/`if`/etc. but didn't filter implicit-return shapes
(`fn name() -> T = expr { ... }`). v5.48.1 adds `_has_standalone_eq`
mirroring `count_user_brace_block_openers` Rule (b)'s `=` filter:
if the head contains a `=` not part of `==`/`!=`/`<=`/`>=`/`=>`/
`+=`/`-=`/`*=`/`/=`/`%=`, refuse migration.

### `_indent_to_braces` — `{` in string literal preservation bug

`if ch == "{": return new_token(...)` (real shape from
`mapanare/self/lexer.mn`) was preserved as colon form by the
preprocessor because the `'{' not in content` guard treated the `{`
inside the string literal as a real `{`. The LALR parser then
rejected with `Unexpected ':' — expected '{'`. v5.48.1 introduces
`_mask_strings_chars` (Python) and `mn_ib_contains_byte_unquoted`
(C) and applies the guard against the masked shadow. New
cross-bootstrap fixture `v5481_brace_in_string_literal` locks the
regression.

Both bugs were caught by Phase 5's rebuild-after-each-cluster
discipline — Cluster A migration produced files that failed to
parse in stage1, surfacing the formatter bug; later, the same file
failed with the unquoted-`{` message after the formatter fix,
surfacing the preprocessor bug. Without the cluster discipline,
both would have shipped silently and the v6.0 hard-removal milestone
would inherit them.

---

## PROMPT/PLAN deviations surfaced at Phase 0

(Load-bearing, documented in `PRE_PHASE_AUDIT.md`.)

1. **Residual brace count after migration is ~737, not ~70.** PLAN
   estimated the post-migration residual at ~70 (the
   `one_line_arm_other` 64-case bucket). Empirical projection (and
   confirmed actual) shows 737. Diff comes from `match_arm_open`
   multi-line arm bodies and per-module `one_line_arm_other` /
   `multi_line_block` shapes — the formatter keeps these verbatim.
   PLAN's "drops from ~6826 to ~70" wording corrected to
   "drops from 6,826 to 1,474 (78% reduction)".
2. **17 modules in `mapanare/self/`, not 12.** v5.48.0 audit grouped
   the 5 transpiler-port files (`from_*.mn`, `transpiler.mn`)
   outside the "core 12". v5.48.1 migrates all 17. Total file count
   in `mapanare/self/` is 18 (17 + `mnc_all.mn`).

Two v5.48.0 BUGS surfaced and fixed during Phase 5 (see "Bugs
surfaced" above) — neither was anticipated by PLAN; both are
load-bearing for the v5.48.x soak preceding v6.0 hard removal.

---

## Aggregate state entering v5.48.2

**0 HIGH** / **3 MEDIUM** / **~7 LOW**.

- **0 HIGH:** Te.3.D arc closed end-to-end — bootstrap mirror +
  self-host migration both shipped; STRICT preserved at the new
  baseline.
- **3 MEDIUM:**
  - macOS notarization carry from v5.33.0 Nu.2 (unchanged).
  - Ai.1 `_specialize_fn` body-walk fix gating Ai.1+Ai.2 keyword
    sugar (carry from v5.40.0, unchanged).
  - **NEW:** `match_arm_open` multi-line arm bodies (98 per-module
    + per `mnc_all.mn`) and `one_line_arm_other` multi-stmt arm
    bodies (114 per-module + per `mnc_all.mn`) keep brace form and
    will keep firing the v5.19.0 deprecation warning. v6.0 grammar
    revisit recommended (multi-stmt single-line arm body shorthand
    is the obvious fix; alternatively the user-facing messaging
    can soften — these aren't user-actionable today).
- **~7 LOW:** Lf.4 variant-name collision split to v5.46.x (carry);
  ergonomic refactor of v5.43.0 distributed-agent APIs (carry);
  fs.mn `walk_dir` IR codegen carry from v5.40.0; websocket.mn
  `str(byte)` decimal-stringification carry from v5.43.0; **NEW:**
  the v5.48.0 formatter / preprocessor bugs documented above are
  fixed in-place at v5.48.1 — no carry.

---

## Tensor closeout arc CLOSED at v5.45.0. Manifesto arc CLOSED at v5.43.0. Package-system runway CLOSED at v5.44.0. Lowerer-bug closeout CLOSED at v5.46.0. Pre-panel hygiene CLOSED at v5.47.0. v5 closeout panel CLOSED at v5.47.5. **Te.3.D arc CLOSED at v5.48.1.**

v5.48.x soak begins. v6.0 hard removal of brace parsing remains
the v6.0 PLAN input it has been since v5.19.0; v5.48.1 makes the
self-host first-party brace surface 78% smaller, so the v6.0 cut
will only need to address the ~1,474 residual (and stdlib /
examples, which are not on the gating path).

See `docs/roadmap/v5/v5.48.1/{PLAN.md, PROMPT.md,
PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.
