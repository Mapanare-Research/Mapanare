# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project Overview

Mapanare is an AI-native compiled language with first-class agents,
signals, streams, and tensors. Compiles to LLVM IR (primary) and C
(fallback via gcc). WebAssembly backend for browser/server targets.
Self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in
`mapanare/self/`. The compiler compiles itself —
`bash scripts/build_from_seed.sh` builds from source with no Python.

**Current version:** see `VERSION` file.

## Current Version & Roadmap

Most recent releases (last 6). Full history at
`docs/roadmap/ROADMAP.md`:

- **v5.20.0** (ready, not tagged) — **Te.5 — struct ergonomics
  (Python side).** Post-Sh.* terseness capstone. Four additive
  surface forms, all desugared to existing constructs — zero new
  MIR ops, zero new runtime functions, zero new IR shapes.
  **Te.5.B** — field shorthand: `Point { x, y }` ≡ `Point { x: x,
  y: y }`. Phase 0 surprise: `mapanare/parser.py:1022`
  `field_init` already had a value-omitted fall-through to
  `Identifier(name=name)`; only the grammar rule was mandatory-
  colon. AST and IR byte-identical to long form. **Te.5.C** —
  struct update: `Point { x: 5, ..base }` lowers to `let
  __mn_base_N = base; new Point { x: 5, y: __mn_base_N.y, ... }`.
  Single base only (D2); trailing position only (D1). New
  `_struct_update_counter` separate from `_tmp_counter` keeps the
  synthesized base tmp from perturbing the global `%tN` sequence
  — IR byte-identical to manual long form. **Te.5.D** — let
  destructuring: `let Point { x, y } = p` binds `x` and `y` in
  the surrounding scope. Nested patterns `let Outer { inner: Inner
  { a }, b } = o` (D3 in `let` only), rest patterns `let Point {
  x, .. } = p` (D9), and per-field mutability `let Point { mut x,
  y } = p` (D4) all work. When RHS is a bare Identifier, the
  lowerer skips the synthesized base tmp — IR byte-identical to
  `let x = p.x; let y = p.y`. **Te.5.E** — three refutable-binding
  forms desugared at lower time to existing match/while/let.
  `if let <pat> = <scrut> { ... } [else { ... }]` → 2-arm match.
  `while let <pat> = <scrut> { body }` (D8) → `while true { match
  scrut { pat => body, _ => break } }`. `let <pat> = <scrut> else
  { ... }` (D5/D6) → strategy 2 synthesized return: for
  single-binding `let Some(x) = opt else { ... }` builds `let x =
  match opt { Some(x) => x, _ => { else_block } }`. New module-
  level `_block_diverges` / `_stmt_diverges` /
  `_expr_or_block_diverges` recursively walk the AST tail
  recognizing ReturnStmt/BreakStmt/ContinueStmt/panic/abort/exit
  calls and nested if/match where every leaf branch diverges. The
  function's implicit return does NOT satisfy the divergence
  requirement (D6). v5.20.0 `let else` patterns restricted to
  constructor patterns with 0 or 1 args (single identifier or
  wildcard) and wildcard patterns; multi-binding patterns deferred
  to v5.21.0+. **11 new goldens** at `tests/golden/81-91_*.mn`,
  all compile through `mapanare emit-llvm` and IR-validate via
  `clang -c`. Python bootstrap: 91/91 PASS. Native stage1: 80/80
  existing PASS, **11/11 new FAIL** because `mnc-stage1` was built
  from v5.18.0 source — bootstrap mirror is on the v5.20.1 docket
  (Te.5.F, mirror v5.14.0→v5.14.1 / v5.15.0→v5.15.1 pattern).
  Phase 5 (bootstrap mirror) deferred — 4–6h on its own per
  design doc, splits cleanly. **No `mapanare/self/*.mn` source
  edits in v5.20.0** so existing strict-fixed-point status is
  unchanged from v5.18.0 (232,281 lines / 0-line diff). Source
  delta: +20 lines lark, +44 ast_nodes, +72 parser, +60 semantic,
  +281 lower = **+477 lines Python total**. 557 parser+semantic
  tests pass. 10 design decisions locked in
  `docs/roadmap/v5/v5.20.0/STRUCT_ERGO_DESIGN.md`. See
  `docs/roadmap/v5/v5.20.0/SESSION_REPORT.md`.
- **v5.19.1** (ready, not tagged) — **Dk.* — Docker images +
  `mnc init --docker`.** Packaging-only release. Two new official
  images on GHCR: `mapanare-builder:5.19.1` (~640 MB —
  debian:bookworm-slim + clang-18 + lld-18 from apt.llvm.org +
  the `mnc` binary + `libmapanare_rt.a`) and
  `mapanare-runtime:5.19.1` (~115 MB — debian:bookworm-slim +
  `libmapanare_rt.so`). New `mnc init --docker` flag overlays a
  multi-stage `Dockerfile` + `.dockerignore` on top of the default
  scaffold; `init_project()` learned an `overlays: list[str]`
  parameter; new template at `mapanare/templates/init/docker/`.
  Multi-stage hello-world final image lands at ~115 MB. New
  `.github/workflows/publish-docker.yml` builds + pushes both
  images on every release tag with GHA-cache; new `docker-smoke`
  job in `ci.yml` rebuilds both images on every CI run and
  exercises the multi-stage hello-world end-to-end. New
  `docs/guides/docker.md` covers usage, multi-stage pattern, opt-
  out, troubleshooting. README gains a "Quick start with Docker"
  section + GHCR badges. `tests/test_init.py` 10/10 → 15/15 (5
  new cases for `--docker`). **Three documented design
  amendments** in `docs/roadmap/v5/v5.19.1/DESIGN_AMENDMENT.md`:
  (A1) builder image-size ceiling raised 300 MB → 700 MB —
  libLLVM-18 + libclang-cpp + transitive deps are non-removable
  while `mnc build` shells out to `clang`; (A2) `gcc` symlinked to
  `clang` in the image because `link_with_runtime` invokes literal
  `gcc`; (A3) in-image `mnc` wrapper script symlinks
  `runtime/native/libmapanare_rt.a` into CWD before exec to
  satisfy mnc's relative-path resolution. A2 + A3 have a clean
  v5.20.0+ follow-up ("builder-image diet": switch
  `link_with_runtime` to drive `lld` directly — saves ~99 MB and
  retires both shims). **Zero compiler / runtime / stdlib / .mn
  edits.** Goldens unaffected (80/80). Strict 3-stage fixed point
  preserved by construction. **Closes the Dk.* arc** that was
  originally bundled with v5.19.0 (Te.3 + Dk.*) and split out at
  scope-split commit 6adfee7 so the deprecation work could ship
  clean. See `docs/roadmap/v5/v5.19.1/SESSION_REPORT.md`,
  `DESIGN_AMENDMENT.md`, and the v5.19.0 `DOCKER_DESIGN.md`.
- **v5.18.0** (ready, not tagged) — **Mc.* — LSP + init + check
  (tooling pack).** Editor-quality waypoint. Ships the
  Mc.1 / Mc.3 / Mc.4 trio from the parity arc plus a greenfield
  VSCode extension. **Phase 0 surprise:** the original PLAN
  assumed greenfield — audit found the bulk already shipped.
  `mapanare/lsp/` is a 3,020-line pygls package that already
  implements PLAN's MVP capability set plus extras (find-refs,
  rename, workspace-wide cross-module index); `cmd_check` /
  `cmd_init` / `cmd_lsp` are wired in `cli.py`; every AST node
  carries `span: Span(line, column, end_line, end_column)`;
  the symbol table builds binding-site positions. Reframed as
  **verify-and-fill**: locked design in
  `docs/roadmap/v5/v5.18.0/MC_TOOLING_DESIGN.md`. **Mc.4** —
  added `--all` recursive walk (skips `.git`, `dist/`, `build/`,
  `node_modules`, etc.) plus `tests/test_check.py` (10/10).
  **Mc.3** — refactored from inline-string scaffolding (brace
  syntax, missing files) to template-directory layout at
  `mapanare/templates/init/<template>/` with `{{NAME}}`
  substitution and project-name validation
  (`^[A-Za-z_][A-Za-z0-9_-]*$`); default template uses canonical
  terse syntax and ships `main.mn`, `mapanare.toml`, `.gitignore`,
  `README.md`. `tests/test_init.py` 10/10. **Mc.1** — verified
  the existing pygls LSP via the existing 116-test suite plus a
  new `tests/lsp/test_initialize_roundtrip.py` JSON-RPC stdio
  smoke (117/117). **Mc.1.G** — sibling repo
  `Mapanare-Research/mapanare-vscode` bumped from v0.4.0 → v0.5.0
  to track `mapanare-lsp v0.5.0`; added `mapanare.init` and
  `mapanare.checkAll` commands wiring the v5.18.0 `mapa init` /
  `mapa check --all` surfaces; README refreshed. **Native dispatch** —
  `mapanare/self/main.mn` learned `check`/`init`/`lsp` cases
  shelling out to Python (mirror of the v5.13.0 `fmt` pattern).
  **Strict 3-stage fixed point preserved**: stage2.ll ==
  stage3.ll at **232,281 lines / 0-line diff**, +558 lines vs.
  v5.17.2's 231,723 (the IR cost of the three new dispatch
  arms). **No seed refresh required** (no new C-runtime
  exports). New docs: `docs/guides/lsp.md`,
  `docs/guides/init.md`, `MC_TOOLING_DESIGN.md`,
  `SESSION_REPORT.md`. Marketplace
  publish, `--template` flag, code actions / semantic tokens /
  inlay hints, and native LSP port all explicitly deferred.
  See `docs/roadmap/v5/v5.18.0/SESSION_REPORT.md`.
- **v5.17.2** (shipped) — **Sh.H — defensive-loop
  cleanup.** Closes the 11 defensive-iteration sites catalogued
  in v5.17.1's COMPREHENSION_SITES.md as out-of-scope-for-syntax-
  only. Two patterns. **Pattern A** (10 sites) — pure
  index-collection
  `for _ in 0..LARGE: if i < n: r.push(xs[i]); i = i + 1`
  rewritten to `for i in 0..len(xs): r.push(xs[i])`: 9 sites in
  `lower.mn` (`bind_method_self_param`, tensor method-call /
  __mn_tensor_get / __mn_tensor_slice / tensor-set arg packing,
  closure capture explicit-params packing, for-comprehension
  body-stmts copy, `verify_module` nested loops) plus 1 in
  `emit_llvm.mn` (function-body emission outer loop).
  **Pattern B** (1 site) — state-advance `while true:` in disguise
  in `parser.mn::parse_call_args`; the artificial `0..100` bound
  was a placeholder for a real `while true` that the lowerer
  accepts cleanly with the early-return exits. Source shrink
  **-38 lines** across 3 modules (`parser.mn` 0, `lower.mn` -34,
  `emit_llvm.mn` -4); cumulative v5.13.0 → v5.17.2 shrink
  **-3,988 lines (-13.9%)** off the v5.13.0 baseline. IR shrink
  **-234 lines** (231957 → 231723), consistent with the lowerer
  emitting one less PHI per rewritten counter loop. **Strict
  3-stage fixed point preserved**: stage2.ll == stage3.ll at
  231,723 lines / 0-line diff at every per-module commit.
  **Goldens 80/80** throughout. NO seed refresh required (all
  rewrites are syntax-equivalent within the v5.14.0+ supported
  colon-block / range-for surface; zero new C-runtime exports).
  All 11 catalogued sites applied successfully — none SKIP'd.
  See `docs/roadmap/v5/v5.17.2/SESSION_REPORT.md`.
- **v5.17.1** (shipped) — **Sh.C + Sh.D + Sh.G — terse
  polish.** Per-site judgment follow-up to v5.17.0's mechanical
  brace → colon rewrite. **Sh.C.B** — list comprehensions in
  `transpiler.mn` (3 sites: `pop_scope` accumulators and a
  match-arm `rest` builder); CLEAR-WIN survey across all 17
  modules found only 5 candidate single-push for-loops, of which
  3 were comp-shaped (the other 2 used a prepend-pattern
  comprehension can't express cleanly). Defensive `for _ in 0..N`
  patterns with artificial upper bounds (12+ sites in `lower.mn` /
  `parser.mn` / `emit_llvm.mn`) deliberately SKIP'd as
  out-of-scope-for-syntax-only. **Sh.D.B** — implicit-return
  upgrades across all 16 modules (`abi.mn` had 0 sites; everything
  else got at least one). 159 ONELINER conversions
  (`fn name() -> T: return E` → `fn name() -> T = E`,
  v5.15.0 Te.2.D parser form) plus 121 BLOCK_SHORT conversions
  (drop trailing `return` keyword to leave bare expression as
  block-form implicit return, SPEC §4.5). Strict single-return
  filter: only functions with exactly ONE `return` substring in
  the body and that return on the LAST non-blank line at body
  indent — protects against multi-return functions where dropping
  the keyword changes semantics. 28 BLOCK_LONG candidates (>5
  prelude statements) deliberately SKIP'd: in long functions the
  explicit `return` keyword is a punctuation marker readers scan
  for, and stripping it for one keyword saves a line at a
  readability cost. **Sh.G** — SPEC.md flagship examples,
  README.md first-impression example, and CLAUDE.md release-notes
  preamble refreshed to terse + idiomatic style. Total source
  shrink **-169 lines (-0.7%)** across 17 commits (24,917 →
  24,748). Modest LOC delta: BLOCK_SHORT conversions don't drop
  lines (`return E` and bare `E` both occupy one line), but they
  do count as readability wins. Cumulative v5.13.0 → v5.17.1
  shrink: **-3,950 lines (-13.8%)** off the v5.13.0 baseline.
  **Strict 3-stage fixed point preserved**: stage2.ll == stage3.ll
  at 231,957 lines / 0-line diff at every per-module commit.
  **Goldens 80/80** throughout. NO seed refresh required (no new
  C-runtime exports). NO bootstrap parser changes (v5.15.0
  Te.2.D shipped function-init form; v5.14.0 Te.1 shipped
  block-form implicit return; both forms have been bootstrap-
  ready since their respective releases). Validated by 63/63
  transpiler tests + 137/137 SPEC tests + the standard
  `verify_fixed_point.sh` + `build_from_seed.sh` flow. See
  `docs/roadmap/v5/v5.17.1/SESSION_REPORT.md`,
  `COMPREHENSION_SITES.md`, and `IMPLICIT_RETURN_SITES.md`.
- **v5.17.0** (shipped) — **Sh.* — self-host rewrite to
  terse syntax.** Headline release of the v5.13–v5.21 terseness
  arc: the 14k-line self-hosted compiler in `mapanare/self/` now
  ships in colon-block form. **Sh.B** — all 17 hand-edited modules
  processed via `mapanare fmt --to-terse` in dependency order, one
  commit per module, with stage1 build + goldens 80/80 validated
  between every commit. Total source shrink **-3,781 lines (13.2%)**
  across the 17 modules (28,698 → 24,917). Per-module deltas
  range from 5.3% (`abi.mn`) to 20.2% (`ast.mn`); largest absolute
  drops are `emit_llvm.mn` (-646), `lower.mn` (-603), and
  `parser.mn` (-359). The regenerated `mnc_all.mn` shrinks from
  23,282 to 20,377 lines (-2,905, 12.5%). **No semantic change** —
  this is `to_terse` followed by parser-synthesis-back-to-the-same-
  AST, so the IR shape is conserved by construction. **Sh.E** —
  bootstrap seed refresh: the v5.10.0-vintage Linux seed at
  `bootstrap/seed/linux-x86_64/mnc` segfaulted at stage 1 against
  the new colon-block source (predates v5.14.0's
  `_indent_to_braces` preprocessor); refreshed from the v5.17.0
  HEAD `mnc-stage1`. **Sh.F** — **strict 3-stage fixed point
  preserved**: stage2.ll == stage3.ll at 231,957 lines / 0-line
  diff (the v5.9.0 milestone, held since v5.9.0). **Goldens 80/80**
  at every per-module commit and at HEAD. `scripts/build_from_seed.sh`
  succeeds with the refreshed seed. Phase 0 (Sh.A.1.A/B/C, shipped
  ab057e0 prior to this release) preemptively fixed three v5.14.0-era
  latent rewriter bugs (`to_terse` corruption of multi-line match
  arms, `to_terse` corruption of expression-context blocks,
  `_indent_to_braces` multi-level dedent); the per-module rewrite
  ran to completion without surfacing further issues. **Deferred to
  v5.17.1**: Sh.C (comprehension upgrades), Sh.D (implicit-return
  upgrades), Sh.G (SPEC / README / CLAUDE example refresh) — all
  per-site judgment work that would have blocked the strict-fixed-
  point payoff release. See
  `docs/roadmap/v5/v5.17.0/SESSION_REPORT.md` and
  `docs/roadmap/v5/v5.17.0/PHASE_0_SURVEY.md`.
- **v5.16.0** (shipped) — **Te.4 — self-host
  string-interpolation parity.** Closes the last Python-vs-native
  string-handling gap. Native `mnc-stage1` now lexes / parses /
  lowers `"${expr}"` interpolation the same way the Python
  bootstrap does — same AST shape (`InterpString`), same MIR
  shape (`InterpConcat`), same `__mn_str_concat` chain. Pre-v5.16,
  `mnc-stage1` errored on `"hi ${name}"` with
  "Undefined variable 'name}'" because the half-finished
  `split_interp_parts` in `parser.mn` had a wrong substr API
  (end-index instead of count), early-returned after one site,
  treated expression text as bare `Expr::Ident`, and the lexer's
  `\$` escape stripped the backslash so escaped interp was
  indistinguishable from real interp. **Te.4.A** — Phase 0 spec
  documents Python's `_split_interp` / `_parse_interp_expr` /
  `_lower_interp_string` / `_do_cast` algorithm as the contract,
  with a 10-entry case matrix. **Te.4.B** — single-line lexer
  change preserves `\$` literal. **Te.4.C** — new
  `Expr::InterpString(List<Expr>)` AST variant; `split_interp_parts`
  rewritten to position-tracking scan (replaces a char-by-char
  buffer that hit a bootstrap concat bug, garbage trailing literal
  bytes); each `${...}` site re-tokenizes and re-feeds through
  `parse_expr`. **Te.4.D** — new `lower_interp_string` mirrors
  Python's: each non-StringLit part gets `Cast(target=mir_string)`,
  chain bundles into `InterpConcat`. Extended `emit_cast` to
  handle X→String for Int/Float/Bool/String — emits
  `__mn_str_from_*` (with drop tracking) for primitives, alias
  `emit_copy` for String. Pre-existing `emit_interp_concat` had a
  latent dest-name bug (final concat wrote to `dn.cN` not `dn`);
  fixed. **Te.4.E** — eight new goldens
  `tests/golden/72…80_string_interp_*.mn`; **goldens 71/71 →
  80/80** through `mnc-stage1`. New cross-bootstrap test
  `tests/bootstrap/test_string_interp_mirror.py` (10 cases) asserts
  byte-identical stdout via Python and native compilation.
  **Te.4.F** (mnc fmt whitespace canonicalization) deferred —
  conservative formatter rules out expression-internal rewriting.
  **Strict 3-stage fixed point preserved** (231,957 lines / 0
  diff after mnc_all.mn regeneration; ~3.3k new lines from the
  added lexer / parser / lowerer / emitter paths). NO seed
  refresh required (no new C-runtime exports). See
  `docs/roadmap/v5/v5.16.0/SESSION_REPORT.md`,
  `docs/roadmap/v5/v5.16.0/INTERP_SPEC.md`, and
  `docs/roadmap/v5/v5.16.0/AUDIT.md`.
- **v5.15.1** (shipped) — **Cb.\* — bootstrap
  comprehension mirror (patch).** Closes the v5.15.0 deferred
  item. `mnc-stage1` now parses and lowers list comprehensions
  (`[expr for x in iter (if cond)*]`) and map comprehensions
  (`#{ k: v for ... }`), with multi-`for` cartesian-product
  clauses, exactly matching v5.15.0's Python behavior.
  **Cb.1** — new `Comprehension` variant on `Expr` and new
  `CompClause` struct in `mapanare/self/ast.mn`. **Cb.2/Cb.3**
  — single-token lookahead in `parse_list_lit` /
  `parse_map_lit`: `KW_FOR` after the first element / `key:
  value` pair dispatches to `parse_list_comp_tail` /
  `parse_map_comp_tail`. **Cb.4** — `lower_comprehension`
  mirrors `mapanare/lower.py::_lower_comprehension`
  line-for-line: synthesizes a fresh `__mn_comp_N` accumulator,
  then nested for/if structure with `__r.push(elem)` (lists)
  or `__r[k] = v` (maps). For non-range iterables, the helper
  `wrap_comp_for` emits the index-based pattern. **Cb.5** —
  type-hint plumbing via new `comp_type_hint:
  Option<TypeExpr>` field on `LowerState`; `lower_let` sets it
  before recursing into a comprehension RHS so the synthesizer
  threads the user's `List<T>` / `Map<K, V>` annotation onto
  the internal accumulator. For map comp,
  `patch_last_mapinit_types` post-patches the `MapInit`
  instruction's `key_type` / `val_type` (mirror of Python
  v5.15.0 Te.2.C empty-`MapLit` patch). One pre-existing
  emitter gap surfaced and fixed in scope: `emit_builtin_len`
  now dispatches `len(map)` to `__mn_map_len` via
  `extractvalue` of field 0 of the `{ptr, i64}` map value
  (was falling through to the list path). **Goldens 68/68 →
  71/71** (new `69_list_comp.mn`, `70_list_comp_filter.mn`,
  `71_map_comp.mn`). New cross-bootstrap test
  `tests/bootstrap/test_comprehension_mirror.py` (10 cases)
  re-runs every case from `tests/test_comprehensions.py`
  through `mnc-stage1` and asserts stdout-identity with
  Python. **Strict 3-stage fixed point preserved** (228,630
  lines / 0 diff) — bootstrap parser/lowerer changes are
  purely additive. NO seed refresh required. `make lint`
  clean. v5.15.1 unblocks v5.16.0 (Te.4 — self-host
  string-interp parity) using `mnc-stage1` as the validation
  reference. See `docs/roadmap/v5/v5.15.1/SESSION_REPORT.md`
  and `docs/roadmap/v5/v5.15.1/AUDIT.md`.
- **v5.15.0** (shipped) — **Te.2 — comprehensions,
  implicit-return one-liner, terse lambdas.** Second release in the
  v5.13–v5.21 terseness arc. Three additive surface forms.
  **Te.2.D** — `fn name(args) [-> RetType] = expr` lowers to
  `Block([ReturnStmt(expr)])` at parse time; downstream
  semantic/lowerer/emitter unchanged. Block-form implicit return
  (last-expr-as-result, SPEC §4.5) was already shipped at v5.14.0
  and not in scope. **Te.2.F** — terse lambda `|x| body`,
  `|x, y| body`, `|| body`; lowers to the existing `LambdaExpr`
  AST node, same closure-env machinery as `(x) => body`. BAR is
  unambiguous in expression position. **Te.2.B / Te.2.C** — list
  + map comprehensions `[expr for x in iter (if c)*]` and
  `#{ k: v for ... }`; new `Comprehension` + `CompClause` AST
  nodes, lowered by AST synthesis in
  `lower.py::_lower_comprehension` to fresh accumulator + nested
  for/if + push/insert; result MIR identical to hand-written loop
  modulo SSA naming. For non-range iterables the synthesizer emits
  an index-based loop (`for __i in 0..len(xs) { let x = xs[__i];
  ... }`) routing around the pre-existing `for x in some_list`
  lowering gap (the runtime `__iter_*` shims only know ranges).
  New empty-`MapLiteral` type-annotation patch in `_lower_let`
  mirrors the v4.122.0 empty-`ListLiteral` patch — without it,
  comprehension-produced maps printed `<?>` for indexed values.
  **Bootstrap mirror** — implicit-return one-liner and terse
  lambda land at v5.15.0 (~35 LOC in `mapanare/self/parser.mn`);
  comprehension mirror **deferred to v5.15.1** (mirrors v5.14.0 →
  v5.14.1 colon-block split). Goldens **66/66 → 68/68** (new
  `67_implicit_return_one_liner.mn` and `68_terse_lambda.mn` both
  compile through `mnc-stage1`). **Strict 3-stage fixed point
  preserved** (228,630 lines, 0 diff) — bootstrap parser change is
  purely additive. New tests: `test_implicit_return.py` (5 cases),
  `test_lambdas.py` (6), `test_comprehensions.py` (11,
  Python-only). `make lint` clean. See
  `docs/roadmap/v5/v5.15.0/SESSION_REPORT.md` and
  `docs/roadmap/v5/v5.15.0/TERSENESS_DESIGN.md`.
- **v5.14.1** (shipped) — **B.\* — bootstrap colon-block
  mirror (patch).** Closes the v5.14.0 deferred item. `mnc-stage1`
  now lexes/parses/lowers the **`pass`** keyword (B.1–B.4 — five
  lockstep edits across `mapanare/self/{lexer,ast,parser,lower,
  semantic}.mn` modeled byte-for-byte on `break`/`continue`) and
  accepts colon-block syntax for every parseable golden via the
  new **`__mn_indent_to_braces`** preprocessor (B.5–B.6). The
  preprocessor lives in C (`runtime/native/mapanare_core.c`,
  ~280 LOC), mirrors `mapanare/parser.py::_indent_to_braces`
  line-by-line, and is wired into `parser.mn::parse` as a builtin
  extern call before `tokenize()`. **Routed through C rather than
  `.mn`** after a `.mn`-side port attempt surfaced two bootstrap-
  lower pathologies that broke fixed point: (1) `String.split()`
  results return mangled values when indexed locally (works via
  function param); (2) deeply-nested if/else with short-circuit
  ops emits PHIs whose entries don't match block predecessors
  (llvm-as rejects). Both are tracked separately as bootstrap-
  quality work; the C-route here sidesteps both by construction.
  New cross-bootstrap test (B.7) `tests/bootstrap/test_indent_
  preprocessor.py` (142 cases) asserts byte-identical output
  between Python and C on every parseable golden plus 10 hand-
  rolled fixtures via a hidden `mnc-stage1 preprocess` subcommand.
  B.8 (native `mnc fmt --to-terse` / `--to-braces`) was zero-LOC
  — already worked at v5.13.0 since the dispatch forwards every
  argv verbatim. **Native colon goldens 0/66 → 66/66** (the Phase
  0 acceptance criterion); brace 66/66 unchanged. **Strict 3-stage
  fixed point preserved** (228,630 lines, 0 diff). `make lint`
  clean. v5.14.1 unblocks v5.16.0's self-host string-interp parity
  validation buffer and v5.17.0's mechanical `mnc fmt --to-terse
  mapanare/self/` rewrite. See
  `docs/roadmap/v5/v5.14.1/SESSION_REPORT.md` and
  `docs/roadmap/v5/v5.14.1/AUDIT.md`.
- **v5.14.0** (shipped) — **Te.1 — colon-block syntax
  (additive).** Second release in the v5.13–v5.21 terseness arc.
  Indent-based block syntax now works alongside `{}` for every
  block-introducing construct: `fn`, `if`/`else`/`else if`, `while`,
  `for`, `let`, `trait`, `agent`, `impl`, `struct`, `enum`, `match`.
  Both syntaxes produce identical AST and identical IR. Phase 0
  audit found the v3.0.0-era `_indent_to_braces` preprocessor at
  `mapanare/parser.py:1812` already covered ~70% of the surface;
  v5.14.0 hardens it (struct/enum/match comma-insertion between
  siblings; last child of `match` deliberately not comma-suffixed
  to satisfy LALR), and wires `parse_recovering` through the
  preprocessor — closes a latent bug where `mapanare check` rejected
  colon syntax. New **`pass` keyword** (real reserved word; lowers
  to no-op) required for empty colon-block bodies — `{}` would be
  ambiguous with object/map literals. Three stdlib `pass`-as-identifier
  collisions renamed: `stdlib/db/migrate.mn` (`pass` → `pass_idx`),
  `stdlib/net/http/auth.mn` (`pass` → `password`),
  `stdlib/test/runner.mn` (`pass` → `passed`); seven `tests/native/*.mn`
  test files updated in lockstep. New tooling: **`mapanare fmt
  --to-terse`** (comment-preserving brace → colon rewriter,
  idempotent, strips trailing commas in struct/enum/match bodies,
  expands `... {}` to `: pass`) and **`mapanare fmt --to-braces`**
  (inverse, thin wrapper over `_indent_to_braces` + `format_source`).
  New `tests/test_colon_blocks.py` (208 cross-style validation tests:
  every parseable golden round-trips; rewriter unit rules covered).
  **Bootstrap mirror deferred** — `mnc-stage1` continues to require
  brace-style source; bootstrap colon support only load-bearing at
  v5.17.0 Sh.\*, dedicated PLAN will land before then. **Strict
  3-stage fixed point preserved by construction** (no
  `mapanare/self/*.mn` source edits in v5.14.0). Goldens 66/66
  (brace, unchanged corpus); `mypy mapanare/ runtime/` clean.
  v5.14.0 is the additive precondition for v5.15.0+ rewrite passes
  to compose on top of `format_source`. See
  `docs/roadmap/v5/v5.14.0/SESSION_REPORT.md` and
  `docs/roadmap/v5/v5.14.0/COLON_BLOCK_DESIGN.md`.
- **v5.13.0** (shipped) — **Mc.2 — `mnc fmt` (the formatter).**
  First release in the v5.13–v5.21 terseness arc. New
  `mapanare/format.py` module: idempotent, AST-preserving,
  whitespace-only canonicalizer (~70 LOC). Six rules in order —
  CRLF/CR → LF, strip trailing whitespace, leading tabs → 4 spaces,
  cap 2+ consecutive blank lines at 1, strip leading/trailing
  blanks, single trailing newline. Wired into both `mapanare fmt`
  (Python CLI) and `mnc fmt` (native, shells out to Python). CLI
  surface: `<path>...` writes in place (default preserved from
  v5.12.x), `--check` exits 1 on drift, `--stdout` prints to
  stdout, directory paths recurse. **Conservative by design** — no
  re-indent, no brace-style change, no expression rewriting, no
  import sorting; those decisions deferred to v5.14.0+ rewrite
  passes. Phase 0 audit (`STYLE_AUDIT.md`) found 114/114 corpus
  files use 4-space indent, 0 trailing whitespace, 0 missing
  trailing newlines, 2 CRLF outliers — the unanimity is what made
  the conservative ruleset defensible. One-time self-format on
  `mapanare/self/{ast,lexer}.mn` (CRLF → LF) and the regenerated
  `mnc_all.mn` (10 stripped blank lines at module boundaries).
  v5.13.0 also rolls in the v5.12.0 plan (Mc.6 / Wk.* — Windows
  SDK split; see CHANGELOG). New `tests/test_format.py` (704
  corpus assertions + 13 unit rules + 7 CLI integration tests).
  **Goldens 66/66 preserved.** Strict 3-stage fixed-point
  unaffected by the formatter (the 1-line `!"5.13.0"` vs
  `!"5.11.0"` drift is pre-existing from the version-bump commit
  538584b). `make lint` clean. The formatter is the load-bearing
  foundation for v5.17.0's mechanical `mnc fmt --to-terse`
  rewrite of the 14k-line self-hosted compiler. See
  `docs/roadmap/v5/v5.13.0/SESSION_REPORT.md` and
  `docs/guides/formatter.md`.
- **v5.11.0** (shipped) — **Pk.* — packaging hygiene + post-bundle
  cleanup.** Three deferred-from-v5.10.0 cleanups, zero compiler
  internals. **Pk.1**: release-artifact filenames now include the
  version (`mapanare-5.11.0-win-x64.zip`, `mnc-5.11.0-linux-x64`,
  etc.), driven by the VERSION file. install.ps1 / install.sh probe
  the versioned name first, fall back to legacy unversioned for
  pre-v5.11 releases and for the 2-release alias soak window (drop
  legacy in v5.13.0). `windows-bundled-llvm-smoke` job downloads
  the versioned ZIP so a missing-versioned-asset upload trips the
  smoke gate. **Pk.2**: drops the v5.9.1 `mnc <file.mn>`
  (implicit-run) deprecation stderr line; the v5.9.1 PLAN scheduled
  removal at v5.11.0 and v5.10.0 carried it as the soak-window
  concession. `tests/test_cli_default.py::test_default_prints_
  deprecation_note` inverted to `test_default_silent_after_v5_11_0`.
  **Pk.3** (evaluate-only): native `mnc` covers 7 of `mapanare`'s
  25 subcommands. PyInstaller→native bundle swap **deferred** to
  v5.12.x+ behind Mc.\* (mnc parity) — Mc.1 `mnc lsp`, Mc.2
  `mnc fmt`, Mc.3 `mnc init`, Mc.4 `mnc check`, Mc.5 `mnc emit-wasm`.
  See `docs/roadmap/v5/v5.11.0/MNC_PARITY_GAPS.md`. **Pk.4**
  (closeout-doc): macOS/Linux LLVM bundling stays deferred —
  system clang remains canonical, static Linux LLVM with libstdc++
  is ~300 MB, no demand signal. NO seed refresh required (zero
  new C-runtime exports — first release in 5+ to skip Bb.\*).
  **Strict 3-stage fixed-point preserved** (226,603 lines / 0 diff,
  the v5.9.0 milestone held since v5.9.0). Goldens 66/66;
  `make lint` clean. See `docs/roadmap/v5/v5.11.0/SESSION_REPORT.md`.
- **v5.10.0** (shipped) — **Win.1b — bundled LLVM toolchain in
  Windows release ZIP.** Closes the "missing clang" pain on Windows
  surfaced by the v5.8.7 install probe. v5.9.0 DX.3 made the failure
  mode helpful (install hint instead of bare "clang failed");
  v5.10.0 removes the dependency entirely. Default
  `mapanare-win-x64.zip` grows from ~10 MB to ~95 MB by bundling
  LLVM 18.1.8's minimal redistributable subset (clang.exe +
  lld-link.exe + LLVM-C.dll + compiler-rt + LICENSE.TXT) into
  `mapanare/llvm/`. **Win.1b.A**: `tools/llvm-bundle/
  extract_minimal.ps1` + `REQUIRED_FILES.md`; PATH-stripped smoke
  test. **Win.1b.B/C**: `actions/cache@v4` LLVM step + bundle staging
  in `build-cli` job. **Win.1b.D**: new `__mn_executable_dir()`
  C-runtime export + `find_clang()` helper in `mapanare/self/main.mn`
  + 6 clang shell-out sites updated. **Win.1b.E**:
  `docs/THIRD-PARTY-LICENSES.md` (Apache 2.0 + LLVM Exception).
  **Win.1b.F**: `install.ps1` honors `MAPANARE_NO_BUNDLED_LLVM=1`
  for opt-out users → `mapanare-win-x64-minimal.zip` (~10 MB).
  **Win.1b.G**: `windows-bundled-llvm-smoke` CI job validates the
  published ZIP end-to-end with PATH stripped. Linux/macOS
  artifacts unchanged (PLAN Decision 4 — those platforms have
  system clang; closeout in v5.11.0 Pk.4). Compiler internals
  untouched; packaging-only release.
  See `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md`.
- **v5.9.2** (shipped) — **hygiene — pre-existing test regex +
  stale README line.** Two pre-existing fixes carried over from
  v5.9.1 that didn't fit the DX.5 dispatch scope. Test + docs only;
  zero compiler/runtime edits. **Tg.1**: tighten the quoted-declare
  regex in `tests/bootstrap/test_stage1_compile.py` — anchor at
  start-of-line and refuse newline inside the captured group.
  Closes the latent `Unresolved cross-module refs:
  [', align 8\n@.str.NNNN = ...']` failure shape (reproduced on
  v5.9.0 HEAD with index 3025; v5.9.1 HEAD with 3042). Helper
  extraction de-dups the two call sites; new `TestRegexHelper`
  with 3 cases guards the failure shape. **Dn.1**: README
  fixed-point status line — stale `NEAR (4-line VERSION-metadata
  diff over a 217k-line stage2.ll)` was the v5.6.x state; v5.9.0
  restored STRICT at the source (DX.2), v5.9.1 preserved it.
  README now reads STRICT with v5.9.0 credit. NO seed refresh.
  **Strict 3-stage fixed-point preserved** (the v5.9.0
  milestone). Goldens 66/66; `test_stage1_compile.py` 20/20 pass
  (was 19/20 at v5.9.1 HEAD); `make lint` clean. See
  `docs/roadmap/v5/v5.9.2/SESSION_REPORT.md`.
- **v5.9.1** (shipped) — **DX.5 — `mnc <file.mn>` defaults to run
  (BREAKING).** Empties the v5.8.7 Windows install probe DX.* docket
  list (DX.1–DX.7 all closed). Single behavior change; dispatch-layer
  only. Pre-v5.9.1 `mnc hello.mn` dumped LLVM IR to stdout (useful
  for compiler devs, hostile first impression for newcomers); v5.9.1+
  compiles + runs the program. New `mnc emit-llvm <file.mn>
  [-o output]` subcommand keeps the IR-emission path verbatim,
  parallel to the Python CLI's `mapanare emit-llvm`. Non-`.mn` files
  error with a migration hint pointing at `mnc emit-llvm` (raw IR)
  or `mnc compile` (transpilation). One-line stderr deprecation note
  on the implicit-run path; removed in v5.11.0 (v5.10.0 keeps it as
  a soak window for downstream CI scripts). NO seed refresh required
  (no new builtin call sites). **Strict 3-stage fixed-point
  preserved** (the v5.9.0 milestone). Goldens 66/66; new
  `tests/test_cli_default.py` 6/6 pass; `make lint` clean. See
  `docs/roadmap/v5/v5.9.1/SESSION_REPORT.md`.
- **v5.9.0** (shipped) — **DX.* — native CLI hygiene.** Closes the
  six user-visible CLI gaps surfaced by the v5.8.7 Windows install
  probe: `mnc --help` works (DX.1); `mnc version` no longer leaks
  `__MN_VERSION__` (DX.2 — structural fix: new `__mn_version_string()`
  C-runtime export replaces the v4.28.0 placeholder + build_stage1.py
  substitution dance, same shape as v5.8.6 We.1); missing-clang prints
  platform-specific install instructions and surfaces clang stderr
  (DX.3); `mnc cache stats` / `cache clean` work on Windows via new
  native `__mn_dir_count_files` / `__mn_dir_total_size` /
  `__mn_dir_remove_recursive` exports + `__mn_dev_null_redirect()`
  shim that sweeps every `2>/dev/null` literal (DX.4); install.ps1 +
  install.sh ship `mnc` alongside `mapanare` and getting-started
  uses `mnc` consistently (DX.6 + DX.7). DX.5 (default-command
  change) deferred to v5.9.1. Bb.3 seed refresh shipped. **Strict
  3-stage fixed-point restored** (225,831 lines / 0 diff) — first
  since v4.139.0 — as a side effect of the IR-metadata node now
  calling `__mn_version_string()` at runtime. Goldens 66/66; 36 new
  pytest tests; `make lint` clean. See
  `docs/roadmap/v5/v5.9.0/SESSION_REPORT.md`.
- **v5.8.6** (shipped) — **We.1 closure — i686-w64-mingw32 ABI
  support.** 3-way ABI dispatch in the emitter (SysV/AAPCS64,
  Win64 sret/sarg, i686 cdecl sret/byval); fixes silent miscompile
  of `{ptr,i64}` returns on i686 via LLVM's eax:edx packing.
  Refines host detection (`__mn_host_is_windows()` /
  `__mn_host_arch_bits()`); deprecates `__mn_host_is_win64()`.
  Bb.2 seed refresh (6.57 MB) — old seed predates the new exports.
  stage2.ll 222,095 lines, strict fixed point in no-Python pipeline.
  Goldens 66/66; pytest 2,372 passed. See
  `docs/roadmap/v5/v5.8.6/SESSION_REPORT.md`.
> Older release notes elided. See `docs/roadmap/ROADMAP.md` for the
> full ledger and `docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` for any
> specific release.

### Planned / in-progress

- **v5.12.0** — **Mc.6 / Wk.* — Windows SDK split.** Default
  Windows installs move to `mapanare-${V}-win-x64-sdk.zip`, which
  bundles one curated LLVM-MinGW/UCRT x86_64 SDK under `sdk/` so
  clean-machine `mnc run` / `mnc build` keep working. The opt-in
  `mapanare-${V}-win-x64-minimal.zip` is app-only and requires a
  user/system compiler. `MAPANARE_NO_BUNDLED_TOOLCHAIN=1` and legacy
  `MAPANARE_NO_BUNDLED_LLVM=1` select minimal. `toolchain/` must not
  appear in v5.12.0 Windows release ZIPs. See
  `docs/roadmap/v5/v5.12.0/WINDOWS_TOOLCHAIN_AUDIT.md`.

**Terseness arc — v5.13–v5.20** (drafted 2026-04-28; 12+
PLAN/PROMPT files staged across `docs/roadmap/v5/`). Theme:
move Mapanare's surface syntax to be terser than Python so the
"minimal code, same result" thesis is actually visible in
real code. Every release in this arc includes
`mnc fmt --to-terse` migration tooling; no hard breaks until
v6.0. Audit-driven: a v5.13.0-prep audit verified that several
SPEC features (`?` operator, block-form implicit return,
range syntax `0..10`) were already implemented but undocumented
as shipping, while string interpolation and the `@test` runtime
had latent bugs requiring dedicated releases.

- **v5.13.0** — **Mc.2 — `mnc fmt`.** Idempotent, AST-preserving
  formatter. The linchpin: every later terseness release adds
  one rewrite pass to `--to-terse`, so this has to be solid
  first. See `docs/roadmap/v5/v5.13.0/PLAN.md`.
- **v5.13.1** — **`@test` runtime fix (patch).** Audit found
  `mapanare test` and `mnc-stage1 test` both fail on the
  simplest possible `@test` fixture (linker error in Python,
  `__mn_assert_fail` undefined in native). Bug fix only; ships
  independently of v5.14.0. See
  `docs/roadmap/v5/v5.13.1/PLAN.md`.
- ~~**v5.14.0**~~ — shipped (see release notes above).
- ~~**v5.14.1**~~ — shipped (see release notes above). Bootstrap
  colon-block mirror — closes the v5.14.0 deferred item ahead of
  v5.16.0/v5.17.0.
- ~~**v5.15.0**~~ — shipped (see release notes above).
- ~~**v5.15.1**~~ — shipped (see release notes above). Bootstrap
  comprehension mirror — closes the v5.15.0 deferred item ahead of
  v5.16.0/v5.17.0.
- ~~**v5.16.0**~~ — shipped (see release notes above). Self-host
  string-interp parity — closes the v5.13.0-prep audit divergence
  ahead of v5.17.0.
- ~~**v5.17.0**~~ — shipped (see release notes above). Mechanical
  `mnc fmt --to-terse` on `mapanare/self/*.mn`. **-3,781 lines
  (13.2%)** across the 17 hand-edited modules; strict 3-stage
  fixed point preserved at 0-line diff.
- ~~**v5.17.1**~~ — shipped (see release notes above). Per-site
  comprehension upgrades, implicit-return upgrades, SPEC.md /
  README.md / CLAUDE.md example refresh. **-169 lines** on top
  of v5.17.0; cumulative v5.13.0 → v5.17.1 shrink **-13.8%**.
- ~~**v5.17.2**~~ — shipped (see release notes above). All 11
  defensive-iteration sites rewritten to range-for / `while true`;
  strict 3-stage fixed point preserved at 0-line diff.
- ~~**v5.18.0**~~ — shipped (see release notes above). LSP +
  init + check tooling pack; verify-and-fill on the existing
  pygls implementation, terse-syntax init template, VSCode
  extension at `editors/vscode/`, native dispatch shell-out.
  Strict 3-stage fixed point preserved at 232,281 lines / 0-line
  diff. AST span retrofit was a no-op — every node already
  carried `span` info.
- **v5.19.0** — **Te.3 + Dk.* — closeout.** Soft-deprecate
  `{}` (still parses, emits warning); hard removal scheduled
  for v6.0. Ship `mapanare/builder` + `mapanare/runtime`
  Docker images. See `docs/roadmap/v5/v5.19.0/PLAN.md`.
- ~~**v5.20.0**~~ — shipped (see release notes above). Te.5
  Python side — field shorthand, struct update (`..base`),
  let destructuring, if-let / while-let / let-else. Bootstrap
  mirror split out to v5.20.1 per the v5.14.0→v5.14.1 /
  v5.15.0→v5.15.1 precedent.
- **v5.20.1** — **Te.5.F — bootstrap mirror.** Mirror all four
  Te.5 features in `mapanare/self/{ast,parser,lower,semantic}.mn`.
  Per-feature commit ordering smallest-first (Te.5.B ~10 LOC,
  Te.5.C ~120, Te.5.D ~250, Te.5.E ~400). Strict 3-stage fixed
  point validation between every commit. Closes the v5.20.0
  deferred item; the 11 new goldens (81-91) currently fail
  through `mnc-stage1` because the bootstrap was built from
  v5.18.0 source. See `docs/roadmap/v5/v5.20.0/SESSION_REPORT.md`
  ("Deferred to v5.20.1") and `STRUCT_ERGO_DESIGN.md` ("Bootstrap
  mirror plan").
- **v5.21.0** — **Te.6 — small ergonomic wins.** Chained
  comparisons (`0 < x < 10`) ships first; the cluster is a sink
  for additional small ergonomic wins that surface during the
  arc execution. Deliberately small — small is a feature, not a
  reason to defer. See `docs/roadmap/v5/v5.21.0/PLAN.md`.

- **v5.8.0** — **RE-PANEL** (target 9.7+). Features first, panel last.
- **v6.0** — Borrow checker / multi-level alias analysis. Hard
  removal of `{}` (Te.3 from v5.19.0 was soft deprecation only).
  Closes Rt.04 (multi-level drop-glue alias analysis, rescoped
  v5.6.6 — struct→list→string depth-2). The only remaining
  v5.6.x v6.0 carry now that v5.6.12 closed Lk.1 at the
  source via destination passing.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` and
`docs/roadmap/v5/PARITY_GAPS.md`.

## Pre-Push Validation (MANDATORY)

Run the full validation suite before any commit/push. Mirrors CI.
Writes results to `error.log`.

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT
.\dev.ps1 validate -Watch  # Validate then watch
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only
.\dev.ps1 fmt              # Auto-format
.\dev.ps1 e2e              # End-to-end tests
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for `examples/wasm/*.mn`
— catches WASM CI failures locally. `pytest` alone is NOT sufficient.

Quick partial checks:

```bash
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
black --check . && ruff check . && mypy mapanare/ runtime/
pytest tests/semantic/test_types.py -v
pytest tests/parser/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v  (add -n auto for parallel)
make lint             # ruff + black + mypy
make fmt              # black + ruff --fix
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches + egg-info
```

### Core workflows

```bash
# Golden test harness (WSL for stage1)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Full rebuild cycle (WSL)
bash scripts/rebuild.sh              # concat + build + goldens

# Self-hosted fixed-point (WSL)
python scripts/build_stage1.py
bash scripts/verify_fixed_point.sh --keep
```

### Debug tooling

Full command reference: **`docs/guides/tools_reference.md`**.

- `python scripts/ir_doctor.py <cmd>` — per-function IR diagnostics,
  baselines, valgrind mapping, stage2 pipeline
- `python scripts/mir_trace.py <file.mn> <fn>` — trace type inference
  in the Python lowerer
- `culebra <cmd>` — 49+ templates for IR + C diagnostics (Rust binary,
  WSL)

## Testing the Native Compiler

Golden corpus at `tests/golden/*.mn` (66 programs). Reference IR at
`tests/golden/*.ref.ll`.

Workflow:
1. Edit `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
2. `python scripts/build_stage1.py`
3. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. Harness compares mnc-stage1 output against Python bootstrap —
   shows which functions are missing or different.

Every run updates `tests/golden/BENCHMARKS.md`. Commit to track
regressions.

**Current baseline (v5.7.1):** **66/66 — preserved.** Sh.7
(closure-typed parameters) and B (or-pattern + identifier `None`
resolution) both closed in v5.7.0; v5.7.1 is a docs/polish release
with no compiler edits. The closure arc is closed; every test in
the corpus that defines "self-hosting" now passes through
`mnc-stage1`.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I), **MyPy** strict
- Target Python 3.11+ (bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source
  → Lark LALR parser → AST (dataclasses)
  → Semantic checker
  → MIR lowering
  → MIR optimizer (O0–O3)
  → Emitter:
      ├→ emit_llvm_text.py  → LLVM IR (text)
      ├→ emit_c.py          → C source
      └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:

| File | Role |
|---|---|
| `cli.py` | Entry point — command dispatch |
| `parser.py` | Lark transformer: parse tree → AST |
| `ast_nodes.py` | AST node definitions |
| `semantic.py` | Two-pass type checker + scope resolver |
| `mir.py` / `mir_builder.py` | MIR data + builder |
| `lower.py` | AST → MIR lowering |
| `mir_opt.py` | MIR optimizer passes |
| `emit_llvm_text.py` | LLVM IR generation |
| `emit_c.py` | C source generation |
| `emit_wasm.py` | WebAssembly (WAT) generation |
| `wasm_linker.py` | wasm-ld multi-module linking |
| `types.py` | **Single source of truth** for type system |
| `mapanare.lark` | LALR grammar, 13-level precedence |
| `tracing.py` | OpenTelemetry-compatible tracing |
| `diagnostics.py` | Rust-style structured error output |

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`,
`result.py`, `deploy.py`. **Legacy — being replaced by native .mn
stdlib.**

**Native C runtime** (`runtime/native/`): arena memory (no GC),
lock-free SPSC ring buffers, thread pool with work-stealing, coop
scheduler (mobile), agent lifecycle, TCP sockets, TLS (OpenSSL via
dlopen), file I/O, event loop (epoll/select), string interning,
memory profiling. Used by the LLVM backend.

## LLVM Backend Status

**Working:** functions, structs, enums, pattern matching, control
flow, type inference, generics, Result/Option, print, builtins, lists,
maps (Robin Hood), agents, signals (full reactivity), streams,
closures (env struct capture), traits, module imports, pipes,
multi-agent pipe definitions, string methods, GPU kernel dispatch.

**Not yet on LLVM:** tensor reshape, mutable views, stepped slices
(v5.x). Tensor surface stable since v4.45.0.

New LLVM features target `emit_llvm_text.py` (sole LLVM emitter).

## Type System (`mapanare/types.py`)

Single source of truth:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP,
  OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int,
  float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare → Python name mapping for emitters
- `PYTHON_TYPE_MAP`: Type → Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, ~14,000 lines of Mapanare. Mirrors the Python bootstrap:

| Module | ~LOC | Role |
|---|---:|---|
| `ast.mn` | 781 | AST node definitions |
| `lexer.mn` | 575 | Tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser |
| `semantic.mn` | 1,729 | Type checker + scope resolver |
| `mir.mn` | 791 | MIR data structures |
| `lower_state.mn` | 587 | Lowerer state |
| `lower.mn` | 3,602 | AST → MIR lowering |
| `emit_llvm_ir.mn` | 258 | LLVM type constants + IR builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter |
| `main.mn` | 537 | Compiler driver |

**Patterns:** constructor functions (`let r: T = first_field; return
r`), state-threading, no struct literal syntax in grammar yet.

**Fixed-point:** NEAR (stage2.ll == stage3.ll except VERSION
placeholder). Strict hit at v4.134.0; currently NEAR per v5.3.2.

## Key Conventions

- Grammar: `mapanare/mapanare.lark` (bootstrap copy at `bootstrap/`)
- Emitters detect used features (agents/signals/streams) and import
  only as needed
- Builtins dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted sources: `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Manifesto: `docs/manifesto.md` |
  RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs:
  `docs/roadmap/v0/` → `docs/roadmap/v5/`
- Version: `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

- **Stdlib in .mn:** new stdlib modules are `.mn`, compiled via LLVM.
  No more Python `.py` stdlib files.
- **C runtime as foundation:** OS primitives (sockets, TLS, file I/O)
  in C. Everything above (HTTP, JSON, routing) in Mapanare.
- **Test on LLVM:** every test runs on the LLVM backend.

## GPU / WASM / Mobile (v2.0.0)

- **GPU** — CUDA + Vulkan via dlopen; `@gpu`/`@cuda`/`@vulkan`
  annotations; PTX/SPIR-V codegen; `stdlib/gpu/`.
- **WASM** — `mapanare/emit_wasm.py` → WAT, `wasm_linker.py` for
  wasm-ld. Targets: `wasm32-unknown-unknown`, `wasm32-wasi`.
- **Mobile** — `aarch64-apple-ios`, `aarch64-linux-android`,
  `x86_64-linux-android`. Coop scheduler + smaller defaults (4 KB
  arenas, 256-slot rings, 4 K string intern cap).

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame package
  (pandas+numpy replacement), in .mn
- `net/crawl`, `security/scan`, `security/fuzz` — agents-based
- AI/LLM drivers: `stdlib/ai/` (LLM, embeddings, RAG)

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — black → ruff → mypy → pytest. Matrix: Python 3.11/3.12
- **native** — C runtime: gcc, ASan, TSan
- **wasm** — WAT emit → wat2wasm → wasmtime WASI examples
- **android** — NDK cross-compile: ARM64 + x86_64 `.o` + ELF verify

5,400+ tests across the full pipeline.

## Skills (slash commands)

| Skill | Description |
|---|---|
| `/golden` | 15/15 golden suite through mnc-stage1 + llvm-as |
| `/stage2` | Compile self-hosted modules + validate stage2 IR |
| `/rebuild` | concat + build mnc-stage1 + run goldens |
| `/ir-audit` | LLVM IR pathology audit with baselines |
| `/valgrind-map` | Valgrind + auto-map offsets to struct fields |
| `/bump-version` | Bump VERSION, README, CHANGELOG, localized docs |
| `/code-review` | 7-reviewer panel review |
| `/create-pr` | PR title + description from commits |
| `/simplify` | Review + fix changed code |
| `/autoresearch` | Autonomous experiment loop |
| `/culebra-scan` | Culebra v2.4.0 — 49+ templates (ABI / IR / Binary / Bootstrap / C). Workflow guide: `docs/guides/culebra.md` |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (29965 symbols, 64427 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Mapanare/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Mapanare/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Mapanare/clusters` | All functional areas |
| `gitnexus://repo/Mapanare/processes` | All execution flows |
| `gitnexus://repo/Mapanare/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
