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

Most recent releases. Full history at
`docs/roadmap/ROADMAP.md` and
`docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` per release:

- **v5.46.0** (ready, not tagged) — **Lf.\* — v5.43.0 lowerer-bug
  closeout; ergonomic `Result<T, E>` API unblocked.** Closes the
  three v5.x lowerer bugs (Lf.1 + Lf.2 + Lf.3) that v5.43.0
  SESSION_REPORT documented and worked around with the flat
  `(ok: Bool, value, err_kind: Int, err_msg: String)` tuple.
  After v5.46.0, the v5.43.0 distributed-agent APIs *can* be
  refactored back to ergonomic `Result<T, NetworkError>` shape
  — that ergonomic refactor is v5.46.x scope, not v5.46.0.
  v5.46.0 ships the codegen fixes that unblock the refactor.
  **Phase 0 audit (load-bearing finding):** all three bugs
  share **one** root cause and that root cause exists **only
  in the Python bootstrap lowerer** (`mapanare/lower.py`). The
  self-host mirror (`mapanare/self/lower.mn`) **already had
  the fix** — v5.26.1 Eu.2 introduced
  `current_fn.return_type` consultation on the self-host side
  at lines 2259-2306; the same fix was never backported to
  the Python bootstrap. Self-host `mapanare/self/mnc-stage1`
  produced correct output for all three repros at v5.45.0
  HEAD (Lf.1 `kind=3` ✓, Lf.2 `kind=3` ✓, Lf.3 `got NoKey` ✓);
  Python bootstrap printed wrong values, failed at IR
  validation, or silently no-fired the inner match. v5.46.0
  backports the self-host's logic into the Python `Ok`/`Err`
  constructor lowering branches at
  `mapanare/lower.py:2398-2453` — **single ~30-LOC edit
  closes all three bugs**.
  **Strict 3-stage fixed point preserved by construction at
  v5.45.0's 243,749 lines / 0 diff** (49-release strict
  streak from the v5.7.1 baseline; **zero
  `mapanare/self/*.mn` source touches** because the self-host
  already had the fix). Goldens **102/102** (99 existing + 3
  new: `100_result_complex_destructure`,
  `101_match_rewrap_propagation`, `102_nested_15arm_match`).
  Plus `tests/llvm/test_lowerer_fixes.py` (5 cases — Lf.1 +
  Lf.2 + Lf.3 + 2 trivial-Ok regression cases) with
  falsifiability protocol documented in module docstring.
  **PROMPT/PLAN deviations surfaced at Phase 0** (load-bearing,
  documented in `PRE_PHASE_AUDIT.md`): (1) Lf.5 self-host
  mirror is a **no-op gate** — PLAN budgeted ~4h, actual
  work is zero `.mn` edits; STRICT preserved trivially.
  (2) **Lf.1 + Lf.2 + Lf.3 share one root cause** — PLAN
  hypothesized Lf.1 + Lf.2 may share with Lf.3 independent;
  IR diagnosis confirms one common cause (the Python
  Ok/Err constructor wrap-shape default). One fix, three
  regressions. (3) **Lf.4 splits to v5.46.x** — Phase 0 LOC
  measurement put the variant-name disambiguation fix at
  ≥50 LOC (multimap-of-variants infrastructure across
  `mapanare/semantic.py` + `mapanare/lower.py`); exceeds
  PLAN's ≤30 LOC bundle threshold. (4) Pre-existing test
  bookkeeping: `tests/llvm/test_llvm_link_all.py::test_golden_corpus_count`
  asserted 95 (pre-v5.34.0 number); v5.46.0 bumps to 102
  and extends the glob from `[0-9][0-9]_*.mn` to also match
  3-digit prefixes. (5) Pre-existing failures —
  `test_run_hello` (gcc.exe env issue),
  `test_reshape_size_mismatch_aborts`,
  `test_link_and_run[98_*/99_*]` — all fail at v5.45.0
  baseline pre-v5.46.0 changes; not regressions from this
  release.
  **Lf.0 — Phase 0 audit.** Reconstructed all 4 v5.43.0
  `/tmp/diag_*.mn` repros at v5.45.0 HEAD; captured IR-level
  diff per bug; localized fix sites; verified self-host
  produces correct output for all three; decided Lf.4
  bundle/split. Audited `mapanare/self/*.mn` for affected
  patterns (no `Err`/`Ok` returns in self-host, no
  Result<NonTrivialOk, NonTrivialErr> usage, max match arms
  in self-host = 12 in `lower.mn` chained_cmp + 184/241 in
  `mnc_all.mn` chained_cmp tables but none nested under
  Err destructure with mismatched Result wrap shape). Output:
  `docs/roadmap/v5/v5.46.0/PRE_PHASE_AUDIT.md`.
  **Lf.1 + Lf.2 + Lf.3 — single fix at `mapanare/lower.py`.**
  In the `Ok` and `Err` constructor lowering branches, when
  the enclosing function returns `Result<T, E>`, default the
  unfilled side of the wrapper to `T` (for Err's Ok-default)
  / `E` (for Ok's Err-default) instead of the legacy `Int` /
  `String` defaults. Mirrors the v5.26.1 Eu.2 fix that the
  self-host already had. Pre-fix the small 32-byte `Result<Int,
  E>` wrapper was stored into the function's larger `__sret__`
  slot; bytes past 32 stayed zero; consumer reads NetworkError
  at the big-layout offset (e.g. 72 for `Result<NodeHandle,
  NetworkError>`) and got tag=0 = BadUrl regardless of which
  variant was actually constructed (Lf.1); rewrap chains
  inherited the wrong shape and IR validation failed (Lf.2);
  nested 15-arm match fired none of the arms because the
  corrupt tag matched no case (Lf.3 — the 15-arm threshold
  reported at v5.43.0 was a red herring). Falsifiability
  locked per fix in `tests/llvm/test_lowerer_fixes.py`
  module docstring + per-test docstring; revert the fix and
  the corresponding pytest case fails with the recorded
  signature.
  **Lf.5 — self-host mirror.** No-op gate. Self-host already
  has the v5.26.1 Eu.2 fix; STRICT 3-stage fixed point
  preserved by construction.
  **Lf.6 — broader sweep.** Audited 237 non-trivial-Ok
  Result-returning functions across `stdlib/`, `examples/`,
  `tests/`. The v5.43.0 `stdlib/agent/` distributed-agent
  surface uses the flat-tuple workaround (per the v5.43.0
  SESSION_REPORT) — the only Result-returning function that
  could have been silently corrupting is
  `stdlib/agent/remote_proto.mn::validate_key`
  (`Result<String, NetworkError>`), but its sole caller is
  internal and exercised through pytest; verified post-fix.
  Existing `tests/stdlib/` regression suite (1043 cases) all
  GREEN — most stdlib Result-returning callers don't trigger
  the bug because their Ok/Err sizes match the inferred
  defaults (e.g., `Result<String, JsonError>` has 16-byte
  ok/err so the small-shape default coincidentally matched).
  No production caller relied on the wrong output.
  **Source delta:** ~30 LOC `mapanare/lower.py` (Ok + Err
  branches) + ~50 LOC `tests/golden/100_*.mn` + ~70 LOC
  `tests/golden/101_*.mn` + ~80 LOC `tests/golden/102_*.mn`
  + ~190 LOC `tests/llvm/test_lowerer_fixes.py` + ~5 LOC
  `tests/llvm/test_llvm_link_all.py` (count + glob) + ~370
  LOC PRE_PHASE_AUDIT.md + SESSION_REPORT.md + ~120 LOC
  CHANGELOG `### Fixed` (3 entries with potentially-
  behavior-changing annotations) + ~25 LOC SPEC sync + this
  CLAUDE.md release-notes entry + mechanical
  bump_version.py edits.
  Aggregate state entering v5.47.0 (closeout panel):
  **0 HIGH** (Lf.\* arc CLOSED) / **2 MEDIUM** (macOS
  notarization carry from v5.33.0 Nu.2; Ai.1
  `_specialize_fn` body-walk fix gating Ai.1+Ai.2 keyword
  sugar, carry from v5.40.0) / ~7 LOW (Lf.4 variant-name
  collision split to v5.46.x; ergonomic refactor of
  v5.43.0 distributed-agent APIs from flat tuple to
  `Result<T, NetworkError>` v5.46.x; fs.mn `walk_dir` IR
  codegen carry from v5.40.0; websocket.mn `str(byte)`
  decimal-stringification carry from v5.43.0; carries
  from v5.45.0). **Tensor closeout arc CLOSED at v5.45.0.
  Manifesto arc CLOSED at v5.43.0. Package-system runway
  CLOSED at v5.44.0. v5.43.0 lowerer-bug closeout CLOSED at
  v5.46.0.** v5.47.0 closeout panel green-lights v6.0 (or
  doesn't). See
  `docs/roadmap/v5/v5.46.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.45.0** (ready, not tagged) — **Ts.\* — tensor closeout arc
  CLOSED.** Closes the v5.41.0 option-B contract carried 4
  releases past slot. Mutable views (`t.view(shape)`), stepped
  slices (`t[start..end:step]`), and an aliasing-flavor reshape
  ship together. After v5.45.0 the "Not yet on LLVM" line in
  CLAUDE.md no longer mentions tensor mutable views or stepped
  slices — the line is removed entirely.
  **`mapanare_tensor_t` grows from 40 → 64 bytes** (append-only
  extension: `int64_t refcount`, `uint8_t is_view`, 7 padding
  bytes, `mapanare_tensor_t *parent`). Pre-v5.45.0 fields preserved
  at original offsets 0/8/16/24/32. Strict 3-stage fixed point
  preserved at **243,749 lines / 0 diff** (48-release strict
  streak from the v5.7.1 baseline; +1,411 lines vs v5.44.1's
  242,338 from new self-host code). Goldens **99/99** (96 existing
  + 3 new: `97_tensor_view_aliasing`, `98_tensor_stepped_slice`,
  `99_tensor_reshape_aliased`).
  **PROMPT/PLAN deviations surfaced at Phase 0** (load-bearing,
  documented in `PRE_PHASE_AUDIT.md`): (1) golden 96 does NOT
  flip on the semantic swap — it never writes to either tensor
  between reshape and read, so output is identical under either
  regime; aliasing-visible test ships as net-new golden 99 using
  multi-index writes via `t[i, j] = val`. (2) Bootstrap grammar
  update is optional, not lockstep — `bootstrap/parser.py` is
  frozen at v0.6.0 and not in v5.45.0's build flow; updated for
  consistency. (3) Three direct-malloc tensor sites in
  `mapanare_gpu_builtins.c` (`tensor_from_list` + matmul ta/tb
  pair) need explicit `memset` zero-init to avoid UB on uninit
  reads of new struct fields. (4) Struct grows by +24 bytes, not
  PLAN's stated +16 (8-byte alignment padding for `parent` ptr
  was overlooked). (5) `IndexItem` loses `RangeExpr.inclusive`
  through translation — pre-existing latent inconsistency since
  v4.45.0; not v5.45.0 introduction.
  **Ts.2.A — refcount on `mapanare_tensor_t`.** Append-only
  struct extension with `int64_t refcount` + `uint8_t is_view` +
  pad + `parent` pointer. `mapanare_tensor_alloc` initializes
  refcount=1; `mapanare_tensor_free` is now refcount-aware:
  decrements; on zero, frees data + shape + metadata for owners
  or just metadata for views (then recurses on parent).
  Single-hop semantics: views always point at the root parent,
  never intermediate views — drop-glue stays O(1) per view. C
  smoke harness `/tmp/ts2a_smoke.c` (8 cases / 22 assertions)
  PASS; ASan 0 leaks 0 errors; valgrind 138 allocs / 138 frees /
  0 leaks / 0 errors.
  **Ts.2.B — `t.view(shape)` + reshape semantic swap.** New
  runtime export `__mn_tensor_view(parent, shape: const MnList *)`
  allocates view metadata sharing parent's data buffer. Element
  count must match parent's; aborts on mismatch with structured
  message. Reshape semantic swap: `__mn_tensor_reshape` body
  delegates to `__mn_tensor_view` — surface API unchanged, but
  semantics changed (writes to reshape result visible in source).
  The `noalias` LLVM attribute drops — would be a lie under
  aliasing. Phase 0 audit confirmed zero production callers
  relied on copy semantics. **Migration:** if your code requires
  v5.41.0 copy semantics, v5.45.0 ships no `.copy()` method
  (deferred to v5.47.0+); cookbook documents the manual
  fresh-tensor-construction workaround.
  **Ts.3.A — grammar/AST/parser for `:step`.** Two new
  productions in `mapanare/mapanare.lark` and
  `bootstrap/mapanare.lark` (range_step_op + range_incl_step_op)
  using the existing COLON token (no new lexer token needed —
  PROMPT proposed RANGE_STEP_SEP; existing COLON works cleanly
  because LALR(1) lookahead disambiguates against type-annotation
  positions). New `step: Expr | None` field on `RangeExpr` and
  `IndexItem`; parser propagates step through `index_expr`'s
  RangeExpr → IndexItem translation. Backward-compatible
  defaults; 256/256 parser regression tests GREEN.
  **Ts.3.B — stepped slice runtime + lower + emit.** New runtime
  export `__mn_tensor_step_slice(t, starts[], ends[], steps[],
  rank)` returns a fresh contiguous tensor (copy semantics, NOT
  a view). Multi-axis: non-stepped axes pass step=1 transparently.
  Literal step ≤ 0 rejected at lower time (catches both
  `IntLiteral(0)` and `UnaryExpr(-, IntLiteral(N))`); non-literal
  step backstopped at runtime with structured error message.
  C smoke `/tmp/ts3b_smoke.c` (4 cases / 19 assertions) PASS;
  ASan 0 leaks 0 errors; valgrind 25 allocs / 25 frees / 0 leaks
  / 0 errors.
  **Ts.4 — test corpus.** 3 new goldens (97/98/99); pytest
  extensions `tests/llvm/test_tensor_views.py` (4 cases),
  `tests/llvm/test_tensor_stepped_slice.py` (8 cases),
  `tests/llvm/test_tensor_views_sanitized.py` (14 ASan + valgrind
  cases — UB-risk tier). All GREEN.
  **Ts.5 — `docs/stdlib/tensor.md` cookbook** (~325 LOC). Quick
  reference, type/API table, lifetime model, six recipes,
  aliasing-safety note explicitly documenting that v5.45.0 ships
  the runtime substrate for view aliasing but NOT static
  borrow-checking (v6.0 deliverable).
  **Ts.7 — self-host mirror.** First v5.45.0 release to touch
  `mapanare/self/*.mn` source. Mirror across `ast.mn`,
  `parser.mn`, `lower.mn`, `emit_llvm.mn`, `semantic.mn` with
  stage1 rebuild + goldens GREEN after each milestone. STRICT
  preserved structurally. **Lesson captured:**
  `scripts/build_stage1.py` does NOT auto-regenerate
  `mnc_all.mn`. First fixed-point check showed NEAR (6 diff
  lines) because stage1 was still compiled from a stale
  `mnc_all.mn`; after running `scripts/concat_self.py` + rebuild,
  STRICT cleanly reached. Future self-host edits must run
  `scripts/concat_self.py` before `scripts/build_stage1.py` —
  same lesson as v5.31.0's stage1-rebuild discipline applied to
  a different layer.
  **Ts.8 — binary-compat regression test.**
  `tests/runtime/test_tensor_struct_compat.py` (5 cases) pins
  `sizeof(mapanare_tensor_t) = 64`, pre-v5.45.0 field offsets at
  0/8/16/24/32, new field offsets at 40/48/56, alloc-init-to-1
  invariant, free-no-op-on-still-aliased. Same pattern as
  v5.42.0 As.6 binary-compat regression for `mapanare_agent_t`.
  **Pre-existing v5.44.1 parser bug surfaced (out-of-scope).**
  `Tensor<Int>` slice + tensor builtin call (e.g.,
  `tensor_size(int_slice_result)`) triggers a parse error.
  Verified the same code fails on the v5.44.1 baseline before
  any v5.45.0 changes. Golden 98 worked around by skipping the
  Int section. Tracked as v5.46.0+ LOW carry. Float-element
  tensors are unaffected.
  **Source delta:** ~80 LOC C in `mapanare_gpu_builtins.c` (Ts.2.A
  + Ts.2.B + Ts.3.B exports) + ~30 LOC C in `mapanare_runtime.c`
  (refcount-aware alloc/free) + ~10 LOC `mapanare_runtime.h`
  (struct extension) + ~70 LOC `mapanare/lower.py` (view branch
  + step routing) + ~75 LOC `mapanare/emit_llvm_text.py` (view +
  step_slice handlers + reshape noalias drop) + ~10 LOC grammar
  (mapanare.lark + bootstrap copy) + ~5 LOC `mapanare/ast_nodes.py`
  + ~30 LOC `mapanare/parser.py` + ~10 LOC `mapanare/semantic.py`
  + ~140 LOC self-host mirror across 5 `.mn` files + ~325 LOC
  cookbook + 3 net-new goldens (~220 LOC) + 3 net-new pytest
  modules (~660 LOC) + binary-compat regression (~195 LOC) +
  CHANGELOG + SPEC sync + this CLAUDE.md release-notes entry +
  mechanical bump_version.py edits + SESSION_REPORT +
  PRE_PHASE_AUDIT.
  Aggregate state entering v5.46.0: **0 HIGH** (tensor closeout
  arc CLOSED) / **2 MEDIUM** (three v5.43.0 lowerer bugs carry —
  v5.46.0's whole release; macOS notarization carry from v5.33.0
  Nu.2) / ~7 LOW (added `.copy()` ergonomic for v5.47.0+; the
  v5.44.1 `Tensor<Int>` parser bug; strided / non-contiguous
  tensors carry to v6.0+; reverse-step carry to v6.0+; GPU
  tensor surface unification carry to v6.0+). **Tensor closeout
  arc CLOSED.** Manifesto arc CLOSED at v5.43.0. Package-system
  runway CLOSED at v5.44.0. v5.46.0 picks up the three lowerer
  bug closeouts; v5.47.0 closeout panel green-lights v6.0. See
  `docs/roadmap/v5/v5.45.0/{PLAN.md, PROMPT.md, PRE_PHASE_AUDIT.md,
  SESSION_REPORT.md}`.

- **v5.44.1** (ready, not tagged) — **Ps.11 + Ps.12 —
  scripts parity + gitignore template; tactical hotfix
  completing the v5.44.0 Ps.\* arc end-to-end.** Two real
  edits, one nit, four tests, one commit. v5.44.0 closed
  package-aware import resolution inside `mapanare/`;
  v5.44.1 closes the parity gap beyond that boundary. **Zero
  compiler edits, zero runtime edits, zero new C-runtime
  exports, zero `mapanare/self/*.mn` source touches, zero
  language surface changes.** Strict 3-stage fixed point
  preserved by construction at v5.44.0's **242,338 lines /
  0 diff** (47-release strict streak from the v5.7.1
  baseline). Goldens **96/96**.
  **PROMPT/PLAN deviation (load-bearing) — surface shape.**
  PROMPT premise was that `scripts/build_stage1.py`,
  `scripts/ir_doctor.py`, `scripts/measure_divergence.py`,
  and `benchmarks/bench_stdlib.py` contained bare
  `ModuleResolver()` constructions matching the v5.44.0
  `tests/packages/test_cli_parity.py` regex. Phase 0 audit
  surfaced that none of these four files construct resolvers
  directly — they invoke `compile_multi_module_mir` /
  `_compile_to_llvm_ir` **without passing a resolver
  argument**, falling through to the helper's in-function
  bare-resolver fallback at `mapanare/multi_module.py:646`.
  Same parity gap, different surface shape. The existing
  bare-`ModuleResolver()` regex doesn't fire for these files
  even with `files_to_audit` extended to include them, so
  Ps.11.B grew a complementary
  `test_scripts_pass_resolver_to_compile_helper` parametrized
  gate that locks the actual invariant: every
  `compile_multi_module_mir` / `_compile_to_llvm_ir` call
  from these files must pass an explicit `resolver=` kwarg.
  Falsifiability verified — reverting the `resolver=resolver`
  kwarg in `scripts/build_stage1.py` fails the new gate with
  the recorded shape.
  **Ps.11.A — scripts/benchmarks resolver parity.** Each of
  the four files now constructs a resolver via
  `build_resolver_for_source(source_path)` with a tolerant
  `PackageDiscoveryError` fallback (mirrors v5.44.0 Ps.3
  LSP/test-runner pattern; tolerant rather than `sys.exit`
  because dev tooling must keep working on broken
  lockfiles). After v5.44.1 the stage1 bootstrap, ir-doctor
  diff, divergence sweep, and stdlib benchmarks all see the
  same package roots `mnc build` does. Incidentally fixed:
  `benchmarks/bench_stdlib.py:55` had a pre-existing invalid
  `use_mir=True` kwarg that would have raised `TypeError` on
  any actual benchmark run — same edit drops it along with
  adding the `resolver=` kwarg.
  **Ps.11.B — gate extension.**
  `tests/packages/test_cli_parity.py` `files_to_audit` +4
  entries (mechanical extension of v5.44.0 audit scope; passes
  trivially) plus the new
  `test_scripts_pass_resolver_to_compile_helper` parametrized
  gate (load-bearing structural change; walks each file via
  paren-depth tracking, strips comment-only lines and inline
  `# tail` comments to ignore docstring/commentary mentions
  of the helper names, asserts every call has `resolver=` in
  its argument list).
  **Ps.12.A — init template gitignore.**
  `mapanare/templates/init/default/.gitignore` now excludes
  `mn_modules/` (load-bearing v5.44.1 add — freshly
  initialized projects no longer commit installed packages),
  `__pycache__/`, `*.pyc`, `*.diag.json`, `*.a`, `*.so`,
  `*.dylib`, `*.dll`. `mapanare.toml` and `mapanare.lock`
  remain committed per Cargo / npm / pip convention; `*.mn`
  remains committed (excluding it would mask every Mapanare
  source file).
  **Ps.12.B — gitignore lock test.** Net-new
  `tests/packages/test_init_template_gitignore.py` (4 cases):
  required-patterns presence, forbidden-patterns absence
  (catches future edits adding `mapanare.toml` /
  `mapanare.lock` / `*.mn` to the gitignore), load-bearing
  `mn_modules/` exclusion, end-to-end via
  `stdlib.pkg.init_project(tmp_path)` verifying produced
  `.gitignore` matches the canonical template (placeholder
  substituted, forbidden patterns absent).
  **Ps.13 — import hoist.** Hoisted `from typing import Any`
  from inside `_surface_install_diagnostics`'s `if
  diag_json:` body to module-top imports in `mapanare/cli.py`
  (1-LOC cleanup nit deferred from v5.44.0).
  **Source delta:** ~50 LOC across 4 scripts/benchmarks
  files (Ps.11.A) + ~80 LOC `tests/packages/test_cli_parity.py`
  (Ps.11.B new gate + comment-stripping logic) + ~12 LOC
  `mapanare/templates/init/default/.gitignore` (Ps.12.A) +
  ~115 LOC net-new `tests/packages/test_init_template_gitignore.py`
  (Ps.12.B) + 2 LOC `mapanare/cli.py` (Ps.13) +
  PRE_PHASE_AUDIT.md + SESSION_REPORT.md + CHANGELOG +
  SPEC sync + this CLAUDE.md release-notes entry +
  mechanical bump_version.py edits. Tests at HEAD:
  `tests/packages/` + `tests/modules/` 98 GREEN (was 90 at
  v5.44.0; +8 = 4 init-template gitignore cases + 4
  scripts-resolver gate parametrized cases). Aggregate
  state entering v5.45.0 (closeout panel): **0 HIGH** /
  **2 MEDIUM** (carries unchanged from v5.44.0: lowerer
  fixes for `Result<T, complex Err>` + variant rewrap +
  nested 15-arm match; macOS notarization carry from
  v5.33.0 Nu.2) / **~8 LOW** (carries unchanged). v5.45.0
  closeout panel runs as planned (per the v5.46.0 deferral
  commit `f7a6272b`). See
  `docs/roadmap/v5/v5.44.1/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.44.0** (ready, not tagged) — **Ps.\* — package-aware
  imports + stdlib extraction runway; ecosystem-bridge gap
  closed before v5.45.0 panel.** First release in the
  package-system arc. After v5.43.0 closed the manifesto arc,
  v5.44.0 wires the existing `stdlib/pkg.py` machinery (~1037
  LOC of manifest parser, lockfile, registry+git install,
  `mn_modules/` layout, publish tarball — all shipped pre-v5.44.0)
  into the existing `mapanare/modules.py` resolver. Result: a
  project with `mapanare.toml` + `mapanare.lock` + `mn_modules/`
  imports installed packages without manual `--stdlib-path`
  hacks. **Adds zero language features, zero new MIR ops, zero
  new IR shapes, zero new C runtime exports, zero
  `mapanare/self/*.mn` source touches, zero compiler edits, zero
  runtime edits.** Strict 3-stage fixed point preserved by
  construction at v5.43.0's **242,338 lines / 0 diff**
  (46-release strict streak from the v5.7.1 baseline). Goldens
  **96/96**. **PROMPT/PLAN deviation (load-bearing)**: PLAN
  framed Ps.\* as "design a package system." Phase 0 audit
  (`PRE_PHASE_AUDIT.md`) found stdlib/pkg.py is 1037 LOC of
  complete manifest/lockfile/install/publish code. v5.44.0
  *wires existing parts together*; doesn't redesign. The
  PROMPT pre-empted this: "the PLAN treats this as if the
  package system were green-field. The premise is partly
  wrong at HEAD." Audit confirmed the warning. **Ps.1+Ps.2 —
  resolver extension + name mapping**: net-new
  `mapanare/pkg_discovery.py` (~280 LOC) shipping
  `PackageRoot` frozen dataclass + `discover_package_roots()` +
  `find_project_dir()` + `package_name_to_import_name()` +
  `build_resolver_for_source()`. The resolver consumes
  `PackageRoot` records produced by discovery; storage layout
  (`mn_modules/<name>-<version>/` today, future global cache
  later) stays inside discovery. `ModuleResolver.__init__`
  extended with kw-only `package_roots: list[PackageRoot] |
  None = None` (backward-compatible — bare `ModuleResolver()`
  unchanged). Search-order policy locked by tests:
  source-local → explicit (`--stdlib-path` / `--extra-path` /
  `MAPANARE_PATH`) → installed packages → bundled stdlib.
  Hyphen→underscore canonicalization (`mn-foo` →
  `import mn_foo`). Bare package import resolves to entry
  module (`mod.mn` else `main.mn`). Lockfile-authoritative
  when present; alphabetical scan fallback otherwise; multiple
  installed versions in scan mode → `PackageDiscoveryError`;
  missing locked install dir → `PackageDiscoveryError("...run
  mnc install")`. **Reserved `source` literals**:
  `"mn_modules"` (v5.44.0), `"path"`, `"git"`,
  `"global-cache"` (forward-compat for v6.0+; the compiler
  must not scan a global cache opportunistically — locked by
  `tests/packages/test_resolver_does_not_scan_global_cache.py`).
  **Ps.3 — CLI parity refactor**: extracted
  `_build_resolver_from_args(args, source_path)`,
  `_collect_explicit_paths(args)`, and
  `_add_resolver_args(parser)` helpers. Refactored 8 of the 9
  existing `ModuleResolver()` construction sites in
  `mapanare/cli.py` (5 sites), `mapanare/multi_module.py`
  (1 site), `mapanare/test_runner.py` (1 site),
  `mapanare/lsp/analysis.py` (1 site). The 9th site (the
  pre-v5.44.0 `cmd_build` site that used `search_paths=`)
  also routes through the helper. Every compile / check /
  emit / test entry point now exposes identical
  `--stdlib-path`, `--extra-path`, `--verbose`, `--diag-json`
  surface (`cmd_check`, `cmd_run`, `cmd_build`,
  `cmd_emit_llvm`, `cmd_emit_c`, `cmd_emit_mir`,
  `cmd_emit_wasm`, `cmd_build_multi`, `cmd_test`).
  **Ps.4 — install diagnostics**: `_import_log` on
  `ModuleResolver` records every package-resolved import.
  `--verbose` prints `[package] <name>@<version> from
  <source>` per import on stderr (deduped on
  `(package_name, version)`). `--diag-json PATH` writes
  `{schema_version: 1, packages: [...]}` JSON. Both
  surfaces silent when not requested; always called AFTER
  successful compilation. **Ps.5 — pure exemplar**:
  `examples/packages/consumer_collections/` net-new (mapanare.toml
  + mapanare.lock + main.mn + README + pre-staged
  `mn_modules/mn_collections-0.1.0/`). The pre-staging means
  the demo runs out-of-the-box without network access.
  **Ps.6 — legacy markers**:
  `examples/packages/mn_http/LEGACY.md` AND
  `examples/packages/mn_json/LEGACY.md` (PROMPT mentioned
  only `mn_http`; Phase 0 audit found `mn_json` has the
  identical `extern "Python"` legacy shape; treated
  identically). Both explain the migration story.
  **Ps.7 + Ps.8 + Ps.9 — docs**:
  `docs/guides/stdlib-packaging.md` (~290 LOC,
  classification table for bundled-core / pure-package /
  runtime-bound / downstream-only stdlib modules + initial
  inventory + migration prerequisites);
  `docs/guides/external-package-workflow.md` (~230 LOC,
  path/git/registry dep modes + dev loop + diagnosis);
  `docs/guides/stdlib-ci-template.yml` (~140 LOC,
  reference-only YAML for the future external stdlib
  repo's CI).
  **Ps.10 — tests**: net-new `tests/packages/` (65 cases
  across 7 files — search order; lockfile;
  CLI parity; install diagnostics; consumer e2e; tarball
  exclusion; no global-cache scan). All 65 GREEN at HEAD
  in 1.77s.
  **Backward-compat verified**: `tests/modules/test_module_resolution.py`
  25/25 GREEN (legacy `ModuleResolver()` and
  `ModuleResolver(search_paths=...)` unchanged).
  **GitNexus impact** on `ModuleResolver` returned CRITICAL
  (56 impacted symbols, 23 direct callers, 17 execution
  flows). Surfaced to lead; approved on the basis that the
  change is structurally additive (kw-only optional new
  param with safe default). The `test_bare_constructor_unchanged_behavior`
  + `test_search_paths_kw_unchanged_behavior` cases lock
  the backward-compat invariant.
  **Source delta:** ~280 LOC net-new
  `mapanare/pkg_discovery.py` + ~80 LOC modified
  `mapanare/modules.py` (resolver extension) + ~190 LOC
  net-new helpers in `mapanare/cli.py` + ~50 LOC modified
  across `multi_module.py`/`test_runner.py`/
  `lsp/analysis.py` + ~1,100 LOC `tests/packages/` (7
  files) + ~660 LOC `docs/guides/` (3 guides) + ~80 LOC
  `examples/packages/consumer_collections/` (4 files +
  staged copies) + ~50 LOC LEGACY.md (2 files) + ~430 LOC
  PRE_PHASE_AUDIT.md + SESSION_REPORT.md + CHANGELOG +
  SPEC sync + this CLAUDE.md release-notes entry +
  mechanical bump_version.py edits.
  Aggregate state entering v5.45.0 (closeout panel):
  **0 HIGH** (Ps.\* arc closed cleanly) /
  **2 MEDIUM** (carry from v5.43.0: lowerer fixes for
  `Result<T, complex Err>` + variant rewrap + nested
  15-arm match; macOS notarization carry from v5.33.0
  Nu.2) / **~8 LOW** (added: native-ABI dependency
  declaration schema, runtime-export ABI versioning,
  global-cache implementation, registry-side package
  signing — all v6.0+ work; carries from v5.43.0).
  **Manifesto arc CLOSED at v5.43.0. Package-system
  runway CLOSED at v5.44.0. v5.45.0 is the closeout
  panel that audits v5.31.0 → v5.44.0 and green-lights
  v6.0.** See
  `docs/roadmap/v5/v5.44.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.43.0** (ready, not tagged) — **Da.\* — distributed agents
  v0; manifesto arc CLOSED for v5.x.** Third and final
  manifesto-arc release after v5.40.0 `ask` and v5.42.0 As.\*
  supervision. Ships network-transparent `agent.send` over
  TCP/TLS: `RemoteAgent` handles addressed by
  `tcp://host:port/agent-id` (or `tls://...`), versioned
  length-prefixed HMAC-SHA256-signed wire protocol, Node
  listener with per-connection state, supervision interop
  bridging remote `ChildExited` frames into the v5.42.0
  `supervisor_handle_exit` strategy library. After v5.43.0 the
  manifesto's "first-class agents" pitch is no longer
  library-class-with-extra-steps — agents span machines.
  Adds two new stdlib modules (`stdlib/agent/node.mn` ~340 LOC
  shipping `NodeHandle`, `node_listen` / `_listen_tls` /
  `_accept_one` / `_shutdown`, `NodeConnection`,
  `conn_send_frame` / `_recv_frame` / `_close`, `ne_kind` /
  `ne_msg`; `stdlib/agent/remote.mn` ~225 LOC shipping
  `RemoteAgent`, `remote_agent_connect` / `_send` / `_recv` /
  `_disconnect` / `_ping`) plus extensions to two existing
  modules (`stdlib/agent/url.mn` shipping `NetworkError`
  15-variant enum + `AgentUrl` + `parse_agent_url` returning
  flat `UrlParseResult`; `stdlib/agent/supervision.mn` net-new
  ~410 LOC shipping `RemoteExitReason` 3-variant enum +
  `ChildExitedMsg` encode/decode + `classify_remote_exit` +
  synchronous `remote_agent_heartbeat_check` +
  `node_key_from_env` / `node_ping_interval_ms` /
  `node_ping_timeout_ms` env config readers).
  **Adds one new C runtime file** (`runtime/native/mapanare_node.c`
  ~360 LOC) with **5 new public exports**
  (`__mn_node_listen_str`, `__mn_node_accept`,
  `__mn_node_connect_str`, `__mn_node_write_str`,
  `__mn_node_read_frame_str`, `__mn_node_close`,
  `__mn_node_get_fd`, plus 2 MnString TLS server ctx
  wrappers). Plus **server-side TLS additions** to
  `mapanare_io.{c,h}` — 5 new dlopen symbols
  (`TLS_server_method`, `SSL_accept`,
  `SSL_CTX_use_certificate_file`,
  `SSL_CTX_use_PrivateKey_file`,
  `SSL_CTX_check_private_key`) + 3 new public exports
  (`__mn_tls_server_ctx_new`, `__mn_tls_server_ctx_free`,
  `__mn_tls_accept`). **Adds zero new MIR ops, zero compiler
  edits, zero `mapanare/self/*.mn` source touches.** Strict
  3-stage fixed point preserved by construction at v5.42.0's
  **242,338 lines / 0 diff** (45-release strict streak from
  the v5.7.1 baseline). Goldens **96/96** (no new goldens —
  distributed agents tested via 4 link-and-run cases under
  `stdlib/agent/tests/test_dist_*.mn`).
  **Wire format (v1, locked at PRE_PHASE_AUDIT):**
  `[u32 length BE][u8 v=1][u8 mt][u64 seq BE][16 b hmac][JSON]`.
  HMAC-SHA256(key, version || msg_type || sequence_be ||
  payload) truncated to 16 bytes (RFC 4868 secure for keys ≥
  32 raw bytes). Replay rejection via per-connection
  last_seen watermark. Six msg_types locked append-only
  (Send / Reply / Ping / Pong / ChildExited / ProtoError;
  7-15 reserved for v1.x; 16+ require v2 frame). DoS guard at
  100 MB. The version byte is the only escape hatch.
  **PROMPT/PLAN deviation (load-bearing) — server-side TLS.**
  Phase 0 audit surfaced that the existing OpenSSL dlopen
  plumbing was client-only (`SSL_connect`, no `SSL_accept`).
  PLAN/PROMPT both presumed server-side TLS was available.
  Lead-approved Option B: expand Da.8 by ~95 LOC C to add the
  5 missing dlopen symbols + 3 new exports + an MnString-form
  wrapper. Rejected Option A (defer `tls://` to v5.43.1)
  because plaintext-only would have undermined the security
  gate the PROMPT itself names.
  **PROMPT/PLAN deviations — three v5.x lowerer bugs surfaced
  + worked around (load-bearing).** All documented in commit
  messages with falsifiability repros at /tmp/diag_\*.mn:
  (1) `Result<COMPLEX_OK, NetworkError>` destructure corrupts
  the Err variant tag when Ok is a non-trivial struct (v5.36.0
  Js.0.B class — Result wrap-shape mismatch). `Result<Int, X>`
  works; `Result<NodeHandle, X>` returns Err with tag=0
  (BadUrl) regardless of constructed value.
  (2) `match Err(e) { da Err(e) }` propagation rewrap also
  corrupts the variant tag — same root cause as (1) plus an
  additional rewrap step.
  (3) Nested 15-arm match on a destructured `e` from outer
  `Err(e)` silently fails to fire any inner arm. 3-arm and
  10-arm matches in the same position work; 15+-arm matches
  silently no-fire.
  **First-cut workaround**: every public function returning a
  struct on success uses a flat
  `(ok: Bool, value, err_kind: Int, err_msg: String)` shape
  instead of `Result<T, NetworkError>`. The 15 NetworkError
  variants are encoded as integer kinds (1..15) at the API
  boundary; the structured enum is preserved internally for
  local matches. v5.43.x picks up `Result<T, NetworkError>`
  ergonomics once the lowerer fixes land. Tracked as v5.43.x
  candidate; out of scope here because (a) Phase 3 needed to
  ship the surface for Phases 4-7 to build on, (b) `lower.py`
  edits put STRICT 3-stage fixed point at risk, (c) any
  compiler edit triggers self-host mirror review.
  **Variant rename** `TransportLost` → `RemoteUnreachable` in
  `RemoteExitReason`. NetworkError already has `TransportLost`
  (Phase 1, url.mn); concat-pattern with both enums in scope
  resolves "TransportLost" to the wrong enum's variant tag —
  the v5.x lowerer disambiguates by name only at match-pattern
  resolution. The semantic supervision distinction
  ("can't reach child" vs "child crashed") is preserved.
  **Async per-connection heartbeat task** and **auto-routing
  of inbound `MSG_CHILD_EXITED` frames** through a parent
  supervisor's inbox both deferred to v5.43.x — both require
  fn-typed callbacks or dedicated agent-runtime threads (paths
  v5.43.0 has not stress-tested at this stage). v5.43.0 ships
  the synchronous heartbeat primitive
  (`remote_agent_heartbeat_check`) + the conversion helpers
  (`encode_child_exited`, `decode_child_exited`,
  `classify_remote_exit`) that make user-side orchestration
  tractable. **Generic `RemoteAgent<T>` with auto-`to_json`**
  deferred behind v5.40.0 Ai.1 prerequisite (the
  `_specialize_fn` body-walk fix); v5.43.0 takes the
  explicit-`to_json::<T>(msg)`-at-call-site fallback the
  v5.40.0 PROMPT authorized.
  **Da.0 runtime fix (latent bug).** `__mn_str_chr` in
  `mapanare_core.c` accepted only 0..127. Per the file-header
  note, Mapanare strings are explicitly byte arrays — the
  0..127 cap was defensive coding that confused
  byte-strings-as-UTF-8. Made any pure-Mapanare binary
  protocol impossible (every header byte ≥ 128 silently became
  empty). Latent because `stdlib/net/websocket.mn` uses
  `str(byte)` decimal stringification instead of
  `__mn_str_chr` and the websocket tests are compile-only.
  Fix extends range to 0..255 + uses `__mn_str_from_parts` to
  preserve byte 0x00. Goldens 96/96 preserved.
  **Test infrastructure.** New
  `tests/stdlib/test_distributed_agents.py` pytest harness
  mirrors the v5.42.0 `test_supervisor.py` concat-pattern.
  4 link-and-run cases at HEAD covering the 10 PROMPT-spec
  Da.7 cases (cases 2 + 3 are covered by the C smoke
  /tmp/da8_smoke.c). **4/4 GREEN.** v5.42.0 supervision
  suite **9/9 GREEN.**
  **Sanitizer + fuzz gates (UB-risk + network-risk tier):**
  TSan run of /tmp/da8_smoke.c — 0 data races. ASan run — 0
  leaks. Network fuzz `/tmp/da_fuzz.c` — 1000 iterations of
  randomized inputs (8 variants: oversize length, length=0,
  truncated, random body, sub-header, length-without-body,
  all-random, immediate close); 1001 accepts, 0 crashes, 0
  hangs. The DoS guard + length validation in
  `__mn_node_read_frame_str` held through every variant.
  Binary-compat regression
  `tests/runtime/test_agent_struct_compat.py` — 4/4 GREEN.
  v5.43.0 adds zero new fields to `mapanare_agent_t`; binary
  compat trivially preserved.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced
  from "v5.42.0 cut" to "v5.43.0 cut" with new sync block
  documenting the wire-format invariants + the 5 new dlopen
  symbols + 3 new public exports + the three v5.x lowerer
  bugs. `check_doc_freshness.py` GREEN.
  `check_changelog_honesty.py` GREEN.
  **Source delta:** ~95 LOC C (mapanare_io server-side TLS) +
  ~360 LOC C (mapanare_node net-new) + ~200 LOC url.mn +
  ~290 LOC remote_proto.mn + ~340 LOC node.mn + ~225 LOC
  remote.mn + ~410 LOC supervision.mn + ~270 LOC `.mn` test
  cases (4 files) + ~250 LOC pytest harness + ~195 LOC
  examples (distributed_pool.mn + heartbeat_demo.mn) + ~210
  LOC `docs/stdlib/agent.md` Distributed-agents extension +
  ~430 LOC PRE_PHASE_AUDIT.md + ~200 LOC SESSION_REPORT.md +
  ~200 LOC CHANGELOG + ~75 LOC SPEC sync + this CLAUDE.md
  release-notes entry + mechanical bump_version.py edits.
  Aggregate state entering v5.44.0 (package-system runway):
  **0 HIGH** (manifesto arc CLOSED) / **3 MEDIUM** (lowerer
  fixes for Result<T, complex Err> + variant rewrap + nested
  15-arm match — three documented bugs blocking ergonomic
  v5.43.x; macOS notarization carry from v5.33.0 Nu.2; Ai.1
  `_specialize_fn` body-walk for generic stdlib functions
  calling generic intrinsics) / ~10 LOW (async heartbeat
  task, auto-route of MSG_CHILD_EXITED, generic
  RemoteAgent<T>, service registry / discovery, replication
  / consensus, mTLS, dynamic key rotation, binary serde fast
  path, IPv6 bracket URL syntax, websocket.mn `str(byte)`
  decimal-stringification latent bug). **Manifesto arc
  CLOSED for v5.x.** v5.44.0 package-system runway begins;
  v5.45.0 panel green-lights v6.0. See
  `docs/roadmap/v5/v5.43.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.42.0** (ready, not tagged) — **As.\* — agent supervision
  trees.** Second manifesto-arc release after v5.40.0 `ask`. Ships
  Erlang/OTP-style supervision: the strategy library
  `stdlib/agent/supervisor.mn` (~370 LOC; `Supervisor`, `ChildSpec`,
  `RestartPolicy` constants Permanent/Temporary/Transient,
  `RestartStrategy` constants OneForOne/RestForOne/OneForAll,
  `RestartDecision`, `WindowCheck`, `SupervisorTransition`) plus
  the C runtime substrate for push-based child-exit notifications
  in `runtime/native/mapanare_runtime.{c,h}`. Erlang/OTP semantics
  exactly for all three strategies. Adds **four new C runtime
  exports** (`mapanare_agent_set_parent`,
  `mapanare_agent_set_on_exit`, `mapanare_agent_set_exit_reason`,
  `mapanare_agent_get_exit_reason`) plus the static C trampoline
  `__mn_supervisor_install_child_hook`. New
  `mapanare_exit_reason_kind_t` enum (NORMAL / SHUTDOWN / KILLED /
  CRASHED). Append-only struct extension on `mapanare_agent_t`
  (4 fields totalling ~496 bytes — 488 → 984 bytes on x86_64
  Linux); zero-init by the existing `memset` in
  `mapanare_agent_init` keeps pre-v5.42.0 callers working
  unchanged. Adds **zero new MIR ops, zero compiler edits, zero
  `mapanare/self/*.mn` source touches**. Strict 3-stage fixed
  point preserved by construction at v5.41.0's **242,338 lines /
  0 diff** (44-release strict streak from the v5.7.1 baseline).
  Goldens **96/96** (no new goldens — supervision tested via 9
  link-and-run cases under `stdlib/agent/tests/`).
  **PROMPT/PLAN deviation (load-bearing).** Phase 0 audit
  (`docs/roadmap/v5/v5.42.0/PRE_PHASE_AUDIT.md`) surfaced five
  premise errors: (1) naming throughout — runtime is
  `mapanare_agent_t` / `mapanare_agent_*`, not `MnAgent` /
  `mn_agent_*` / `MN_MSG_*` as the prompt claimed (cosmetic but
  touches every file path / symbol in the prompt's Phase 1);
  (2) **no system-message-kind enum exists** — inbox messages
  are opaque `void *` discriminated entirely at the user
  agent's handler. PLAN.md Risk #4 ("appending
  `MN_MSG_CHILD_EXITED` shifts later enum values, breaking
  stage1 binaries") cannot materialize as written — there is no
  enum. Re-targeted the binary-compat regression test to lock
  the struct-extension case (the v5.41.0 pattern, applied to a
  different shape); (3) no `mn_agent_exit*` API — agents enter
  FAILED only when the handler returns rc != 0; the structured
  payload propagation (As.4) was implemented as a side-channel
  (handler calls `mapanare_agent_set_exit_reason(self, kind,
  reason)` before returning rc != 0; on_exit reads back via
  `mapanare_agent_get_exit_reason` after the FAILED state-store
  release); (4) the pre-existing `restart_policy` field on
  `mapanare_agent_t` is intra-agent handler-error retry, NOT
  supervisor-driven restart; v5.42.0 As.6 adds the latter on
  top, leaving the former untouched (documented in the
  `docs/stdlib/agent.md` migration/coexistence note);
  (5) goldens at v5.41.0 HEAD are **96/96**, not 98/98 as the
  prompt claimed; v5.42.0 ships 0 new goldens. Lead-approved
  Path B (push-driven via opt-in C callback) over Path A
  (pure-Mapanare poll-based, zero C edits). Path B has lower
  restart latency and preserves the full feature set including
  ExitReason payload routing.
  **Library shape.** v5.42.0 ships the supervisor as a *strategy
  library*, not as an agent itself. The supervisor's job is
  answering "given this child's exit, which children should the
  orchestrator restart, and should we escalate?" — NOT spawning
  / killing agents. This shape sidesteps two known v5.x quirks:
  (a) fn-typed parameters (factories) are unreliable to invoke
  through Mapanare's lowering (v5.37.0 Ht.\* lesson —
  registration-table workaround); (b) cross-typed agents
  (children of mixed `agent X / agent Y` types) cannot be stored
  in a single homogeneous list. Storing just integer agent IDs
  sidesteps it. The orchestrator side does the actual respawn,
  driven by the strategy library's decisions. Tracked as a
  v5.43.0 ergonomic upgrade (MEDIUM): pass a factory closure to
  the supervisor; supervisor spawns + restarts.
  **As.6 substrate.** Three FAILED-transition sites
  (`mapanare_runtime.c:606,612` coop scheduler;
  `mapanare_runtime.c:1411` pthread worker) invoke `on_exit`
  after the state store, before the worker thread exits —
  happens-before edge to the supervisor's read is the FAILED
  state-store release. The static C trampoline
  `supervisor_trampoline` (in `mapanare_runtime.c`, registered
  via `__mn_supervisor_install_child_hook`) builds a heap-
  allocated `__mn_child_exit_msg_t { agent_id: i64, kind: i64,
  reason: char[256] }` and `mapanare_agent_send`s it to the
  parent supervisor's inbox. Layout matches a Mapanare-side
  `ChildExitedMsg` struct so the parent agent's handler can
  decode it.
  **Tests.** New `stdlib/agent/tests/test_*.mn` (9 cases, ~250
  LOC total): three strategy tests (one per RestartStrategy),
  restart-limit exhaustion, backoff progression with cap,
  normal-exit + per-policy matrix, child-id remapping
  (`replace_child_id`), window reset, stale-notification no-op.
  Pytest harness `tests/stdlib/test_supervisor.py` mirrors the
  v5.34.0 / v5.39.x concatenation pattern; **9/9 GREEN at HEAD
  in 3.44s**. Plus `tests/runtime/test_agent_struct_compat.py`
  (4 binary-compat regression cases): locks `sizeof
  (mapanare_agent_t)` between 488 and 1024 bytes (current 984
  on x86_64 Linux), opaque-PTR emitter declarations,
  append-only field placement after the v4.33.0
  `message_dtor` anchor, and the on_exit invocation at every
  FAILED-transition site. **4/4 GREEN.** Plus
  `tests/runtime/test_as6_supervision_smoke.c` — spawn parent +
  child, child handler stamps `EXIT_CRASHED + reason` then
  returns rc != 0, callback fires on the dying child's thread,
  supervisor reads back the structured reason intact.
  **PASSED. TSan compile-clean.** Pre-existing
  `tests/runtime/test_agent_destroy_drain.c` still passes —
  backward compat verified.
  **Examples.** `examples/agents/supervisor_strategy_demo.mn`
  exercises all three strategies on a 3-child tree (output
  verified end-to-end through the LLVM emitter + clang link +
  execution path); `examples/agents/worker_pool_supervised.mn`
  sketches the orchestration pattern with pseudocode for the
  `__mn_supervisor_install_child_hook` integration.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced
  from "v5.41.0 cut" to "v5.42.0 cut" with a new sync block
  summarizing what v5.42.0 ships (specifically calling out the
  four new C runtime exports + the static C trampoline + the
  As.6 struct-extension binary-compat invariant).
  `check_doc_freshness.py` GREEN. `check_changelog_honesty.py`
  GREEN. `make ci-gates` GREEN (9 sub-gates); `make lint`
  clean. Source delta: ~80 LOC C in `mapanare_runtime.{c,h}`
  (As.4 + As.6) + ~370 LOC `stdlib/agent/supervisor.mn`
  (As.1 + As.2 + As.3) + ~250 LOC `.mn` tests (9 files) +
  ~140 LOC pytest harness + ~190 LOC binary-compat regression
  test + ~110 LOC C smoke harness + ~150 LOC examples (2
  files) + ~250 LOC `docs/stdlib/agent.md` (As.8) + ~100 LOC
  CHANGELOG + ~60 LOC SPEC sync + this CLAUDE.md release-notes
  entry + mechanical bump_version.py edits. Aggregate state
  entering v5.43.0: **0 HIGH** / **2 MEDIUM**
  (spawn-restart-via-Mapanare-fn ergonomic — v5.43.0
  commitment for the headline supervision item; macOS
  notarization carry from v5.33.0 Nu.2) / **~7 LOW**
  (`@agent`-handle ↔ `mapanare_agent_t *` bridge; dynamic
  child addition; distributed supervision blocked on remote
  agents work; process registry / via syntax;
  restart-decision logging structured-events; cap doc for the
  256-byte exit-reason buffer; carries from v5.41.0). See
  `docs/roadmap/v5/v5.42.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.41.0** (ready, not tagged) — **Ts.1 — `tensor.reshape`
  on the LLVM backend (option B part 1).** First half of the
  longest-standing v5.x parity gap closeout. The language-builtin
  `Tensor` (`TypeKind.TENSOR`) now has `reshape(shape: List<Int>)
  -> Tensor` end-to-end through both the Python bootstrap LLVM
  emitter and the self-hosted compiler (`mnc-stage1`). Validates
  that the new shape's element count matches `src->size`; aborts
  with a structured fprintf+abort message on mismatch. **Ships
  copy semantics** at v5.41.0 — each call allocates a fresh
  tensor and memcpys; v5.41.1 will swap to refcount-based
  aliasing under the same surface (the `noalias` attribute on
  `__mn_tensor_reshape` will drop at that release). Adds **one
  new C runtime export** (`__mn_tensor_reshape` in
  `runtime/native/mapanare_gpu_builtins.c`). Adds **zero new
  MIR ops** — the lower path emits a plain `Call` to the runtime
  helper (matching the v4.45.0 `__mn_tensor_slice` pattern,
  not the PLAN's "new MIR op" framing). Strict 3-stage fixed
  point preserved by construction at **242,338 lines / 0 diff**
  (43-release strict streak from the v5.7.1 baseline). Goldens
  **96/96** (95 existing + new `tests/golden/96_tensor_reshape.mn`).
  **PROMPT/PLAN deviation (load-bearing) — option B scope split.**
  Phase 0 audit
  (`docs/roadmap/v5/v5.41.0/PRE_PHASE_AUDIT.md`) surfaced four
  mismatches between PLAN framing and v5.40.0 HEAD: (1) **grammar
  does NOT accept `[start..end:step]` at HEAD** (PLAN/PROMPT
  both said it did; `RangeExpr` and `IndexItem` have no `step`
  field; `mapanare/mapanare.lark` has only `..` and `..=`);
  (2) the existing `stdlib/gpu/tensor.mn::reshape` (line 544)
  is on a stdlib `GpuTensor` struct — different type from the
  language-builtin `Tensor` that the CLAUDE.md "Not yet on LLVM"
  line refers to; (3) `mapanare_tensor_t` (the C runtime
  metadata struct) has no refcount/strides/offset and views
  need substantial struct surgery — `__mn_tensor_slice` already
  copies data, not aliases it; (4) realistic budget for full
  closeout (Ts.1 + Ts.2 + Ts.3 + tests + docs) is ~1,900 LOC
  across 3–5 working days, not PLAN's ~750 / "1–2 sessions".
  Lead-approved option B: v5.41.0 = Ts.1 only with copy
  semantics (~700 LOC); v5.41.1 = Ts.2 (mutable views with
  refcount-based aliasing) + Ts.3 (stepped slices, including
  grammar + AST + parser changes for `:step` syntax) +
  remaining tests/docs (~1,200 LOC). CLAUDE.md "Not yet on
  LLVM" line **partially closed** at v5.41.0: `tensor reshape`
  removed; `mutable views, stepped slices` remain with v5.41.1
  forward link. **Falsifiability** — reverting either lowering
  branch (Python `lower.py::_lower_method_call` or self-host
  `mapanare/self/lower.mn::lower_method_call`) makes
  `test_reshape_via_python_emitter` or `test_reshape_via_stage1`
  respectively fail (the call falls through to the
  generic-method-call path which emits an unresolved `reshape`
  symbol; link fails). Reverting either emit branch makes the
  IR validate but the runtime gets garbage shape data and either
  aborts on the size check or produces a corrupt tensor.
  `test_reshape_size_mismatch_aborts` pins the abort path
  against silent NULL-deref or wrong-behavior regressions on
  shape mismatch. Source delta: ~58 LOC C runtime + ~15 LOC
  `emit_llvm_text.py` + ~10 LOC `lower.py` + ~9 LOC
  `mapanare/self/emit_llvm.mn` + ~14 LOC
  `mapanare/self/lower.mn` + ~85 LOC golden + ~225 LOC pytest
  + ~125 LOC `PRE_PHASE_AUDIT.md` + ~150 LOC SESSION_REPORT +
  ~85 LOC CHANGELOG + ~50 LOC SPEC sync + this CLAUDE.md
  release-notes entry + mechanical bump_version.py edits.
  Aggregate state entering v5.41.1: **0 HIGH** / **2 MEDIUM**
  (Ts.2 + Ts.3 — option-B contract is to close at v5.41.1;
  escalates to HIGH at v5.42.0 if not landed; macOS
  notarization carry from v5.33.0 Nu.2) / **~5 LOW**
  (copy-semantics-to-refcount swap planned v5.41.1; cookbook
  + SPEC examples deferred to v5.41.1 once full surface is
  closed; stdlib `GpuTensor.reshape` vs builtin
  `Tensor.reshape` namespace coexistence audit; carries from
  v5.40.0). See `docs/roadmap/v5/v5.41.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.40.0** (ready, not tagged) — **Ai.\* — `ask` runtime
  adapter; manifesto-arc kickoff.** First release in the
  manifesto arc; the AI-native pitch graduates from "library
  API" to "stdlib-level surface." Ships `stdlib/ai/ask.mn`
  (provider-agnostic env-driven LLM dispatch via
  `build_config_from_env()` reading `MAPANARE_AI_PROVIDER` /
  `MAPANARE_AI_MODEL` / `MAPANARE_AI_API_KEY` /
  `MAPANARE_AI_LOCAL_URL` with fallback to `MAPANARE_LLM_*` for
  compatibility; recognised providers: anthropic, openai, groq,
  ollama, local; `ask_text(prompt) -> Result<String, AskError>`
  for free-form chat; `ask_with_schema(prompt, schema) ->
  Result<String, AskError>` for typed-output extraction;
  `AskError` 8-variant enum: `Network(String)`, `RateLimit(Int)`,
  `SchemaMismatch(String)`, `ContentFiltered(String)`,
  `TimedOut`, `ProviderUnavailable(String)`,
  `MalformedResponse(String)`, `DeserializeFailed(String)`;
  `map_extract_error(e: ExtractError) -> AskError` translates the
  underlying retry-on-malformed-JSON engine's failures) and
  `stdlib/ai/ask_cache.mn` (opt-in response cache; SHA-256 over
  `(provider, model, prompt, schema)` keying; cache files at
  `${MAPANARE_AI_CACHE_DIR}/${key}.json`; TTL default 86400s
  override via `MAPANARE_AI_CACHE_TTL_SECONDS`; atomic writes via
  temp + rename) on top of v5.36.0's `__struct_meta::<T>()`
  schema intrinsic and v5.39.x's typed-serde round-trip
  (`to_json::<T>` ↔ `from_json::<T>` closed for every common
  shape). **Zero compiler edits. Zero new C runtime exports.
  Zero `mapanare/self/*.mn` source touches.** Strict 3-stage
  fixed point preserved by construction at v5.39.7's **241,898
  lines / 0 diff** (42-release strict streak from v5.7.1
  baseline). Goldens **95/95**.
  **PROMPT/PLAN deviation (load-bearing) — Ai.1 + Ai.2 + Ai.8
  deferred to v5.41.0.** The reserved `ask` keyword
  (`let plan: Plan = ask("...")` with binding-context type
  inference) and the `ask_typed::<T>(prompt)` intrinsic were
  scoped as the load-bearing manifesto deliverables. Phase 0
  audit at v5.39.7 HEAD surfaced two structural blockers:
  (1) **naming collision** — `stdlib/ai/llm.mn:1114` already
  defines `pub fn ask(config, prompt)`; a reserved keyword
  would shadow this across the entire ecosystem; (2)
  **nested-generic intrinsic substitution does not propagate** —
  `mapanare/lower.py::_specialize_fn` substitutes parameter and
  return types when monomorphizing a generic function, but does
  not walk the body to rewrite nested `CallExpr.type_args`.
  Confirmed empirically: a user-level `fn parse_typed<T>(s: String)
  -> Result<T, JsonError> { da from_json::<T>(s) }` called as
  `parse_typed::<P>("{\"x\": 42}")` with `P { x: Int }` returns
  0 (default-init) instead of 42 because the inner
  `from_json::<T>` was lowered with the literal type-variable
  name "T". Both an intrinsic-form (~80 LOC of Result-chaining
  MIR per call site) and a structural fix in `_specialize_fn`
  threaten the 42-release STRICT streak. The PROMPT explicitly
  authorized fall-back to function-syntax: "If the changes
  threaten STRICT, fall back to a function-syntax shape … and
  revisit the keyword in v5.41.x. The strict streak is more
  valuable than the keyword sugar." v5.40.0 takes the function-
  syntax path; v5.41.0 picks up the keyword on the back of a
  `_specialize_fn` body-walk fix that recursively rewrites
  `CallExpr.type_args` through specialized function bodies (NEW
  MEDIUM tracked).
  **Naming gotcha (load-bearing)** — `LLMError` already defines
  a `Timeout(String)` variant. A unit `Timeout` in `AskError`
  collided silently in match-pattern resolution under
  concatenation; the pattern-matcher resolved to the *other*
  enum's variant. Caught in Phase 1 smoke; renamed to
  `TimedOut`. Documented in CHANGELOG `### Changed` and source
  preamble.
  **Self-contained cache module** — Phase 3 surfaced a pre-
  existing IR codegen issue in `stdlib/fs.mn::walk_dir` (match
  on `Result<List<String>, FsError>` lowers to `extractvalue ptr
  ... 0` then `zext ptr to i64`, which clang rejects).
  Reproduces on `dev` HEAD with no v5.40.0 changes (verified via
  `git stash` + standalone fs-only smoke). **Out of scope** per
  PROMPT (the LLVM emitter / lowerer is the v5.40.0 third rail).
  `stdlib/ai/ask_cache.mn` rewritten to use direct C-runtime
  externs (`__mn_file_write`, `__mn_file_exists`,
  `__mn_file_rename`, `__mn_file_mtime`, `__mn_dir_create`,
  `__mn_file_read_or_empty`, `__mn_now_realtime_ns`,
  `__mn_sha256_str`, `__mn_hex_encode_str`); ~10 extra LOC, no
  fs.mn dependency; the fs.mn issue is tracked as v5.41.0+ LOW.
  **Test infrastructure.** New
  `tests/stdlib/test_ai_ask.py` (concat-pattern mirrors v5.34.0
  Dt.\* / v5.35.0 Sq.\* / v5.39.x Js.4.\*) with 5 deterministic
  `.mn` test cases under `stdlib/ai/tests/`:
  `test_ask_error_variants.mn` (8 AskError variants + 2
  map_extract_error cases), `test_ask_config_env.mn` (default
  path → ollama / llama3.2), `test_ask_config_env_anthropic.mn`
  (env=anthropic + API key → api.anthropic.com:443),
  `test_ask_cache_roundtrip.mn` (store / hit / miss-on-different-
  key), `test_ask_schema_shapes.mn` (7 struct shapes through
  `__struct_meta::<T>()` covering primitives + Option + List +
  Map + nested). **5/5 GREEN at HEAD in 8.92s, 1 SKIPPED**
  (live-gated `test_ai_ask_live` skipped without
  `MAPANARE_AI_API_KEY`).
  **Manifesto demo** — `examples/ai/plan_generator.mn` (~60
  LOC). Takes a goal string, asks the configured provider for a
  structured `Plan { goal: String, steps: List<Step>, eta_days:
  Int }` (where `Step { title: String, detail: String }`),
  decodes via `from_json::<Plan>`, renders the steps with
  title + detail. Run with `MAPANARE_AI_PROVIDER=anthropic
  MAPANARE_AI_API_KEY=sk-ant-...`. Single best demo of
  manifesto-level ergonomic that's tractable today.
  **Hd-class preventative** — `docs/SPEC.md` header re-synced
  from "v5.39.7 cut" to "v5.40.0 cut" with new sync block
  documenting the manifesto-arc kickoff + the Ai.1/Ai.2/Ai.8
  deferral rationale. `check_doc_freshness.py` GREEN;
  `check_changelog_honesty.py` GREEN. `docs/manifesto.md`
  updated with a dedicated "first manifesto item shipped at the
  syntax level" section. `docs/stdlib/ai.md` net-new (~340 LOC
  — quick reference + provider config matrix + typed-output
  pattern + AskError table + cache config + 5 cookbook recipes
  + "what's not here yet" + migration / coexistence note).
  Source delta: ~155 LOC `stdlib/ai/ask.mn` (new) + ~110 LOC
  `stdlib/ai/ask_cache.mn` (new) + ~245 LOC `.mn` test cases (5
  files) + ~175 LOC pytest harness + ~60 LOC manifesto example +
  ~340 LOC `docs/stdlib/ai.md` + ~6 LOC manifesto delta + ~95
  LOC CHANGELOG + ~25 LOC SPEC sync + this CLAUDE.md release-
  notes entry + mechanical bump_version.py edits.
  Aggregate state entering v5.41.0: **0 HIGH** / **2 MEDIUM**
  (`_specialize_fn` body-walk fix gating Ai.1+Ai.2 keyword
  sugar — NEW; macOS notarization carry from v5.33.0 Nu.2) /
  **~6 LOW** (`stdlib/fs.mn::walk_dir` IR codegen issue NEW;
  streaming `ask`, tool calling, multi-turn, plus prior carries
  from v5.39.7). **Manifesto arc begins.** See
  `docs/roadmap/v5/v5.40.0/{PLAN.md, PROMPT.md, PRE_PHASE_AUDIT.md,
  SESSION_REPORT.md}`.

- **v5.39.7** (ready, not tagged) — **Js.4.F.1 + Js.4.F.2 —
  typed-serde ENUM encode + decode; round-trip closure for
  enum-typed fields. Final release in the v5.39.x typed-serde
  arc; Js.4.\* arc CLOSED.** After v5.39.7 the typed-serde
  round-trip `to_json::<T>` ↔ `from_json::<T>` closes for
  **every common LLM JSON response shape** (primitive, struct,
  nested struct, `List<X>`, `Map<String, V>`, and tagged-union
  enums). Adds **zero language features, zero new MIR ops,
  zero new IR shapes, zero new C runtime exports**. **Strict
  3-stage fixed point preserved by construction** at v5.39.6's
  **241,898 lines / 0 diff** (41-release strict streak from
  v5.7.1; zero `mapanare/self/*.mn` source touches — Phase 0
  verified `grep -rn "from_json|decode_to|encode_struct|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **Js.4.F.1 — ENUM encode.**
  `mapanare/lower.py:2689::_encode_field_to_json` had explicit
  handlers for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT`
  (v5.39.3) + `LIST` (v5.39.4) + `MAP` (v5.39.6) but no branch
  for user-defined enum-typed fields. Pre-fix the fallback at
  `Call(fn_name="str", args=[field_val])` emitted the literal
  `<?>` placeholder. `Record(2, Pending(42))` encoded as
  `{"id": 2, "status": <?>}`; post-fix encodes as
  `{"id": 2, "status": {"Pending": 42}}`. Fix adds a new
  `_emit_enum_json_body(enum_val, enum_name) -> Value` helper
  (~120 LOC) that switches on `EnumTag(enum_val)` with one
  block per variant + a default block, merges the per-variant
  strings via a Phi. Per-variant payload shape: **no-payload →
  bare string `"VariantName"`; single-payload →
  `{"VariantName": <encoded>}`; multi-payload →
  `{"VariantName": [<p0>, <p1>, ...]}`** (positional tuple →
  JSON array). Recurses through `_encode_field_to_json` per
  payload type so nested struct / list / map / enum payloads
  fall through uniformly. **Js.4.F.2 — ENUM decode.**
  `mapanare/lower.py:3336::_decode_json_field` had explicit
  handlers for primitives + OPTION + STRUCT (v5.39.4) + LIST
  (v5.39.5) + MAP (v5.39.6) but no branch for user-defined
  enum-typed fields. Pre-fix the raw-jval fallback returned
  the JsonValue enum where the typed enum value was expected
  — silent shape mismatch on the consumer side. Fix adds a
  new `_emit_enum_decode_body(jval, enum_name) -> Value`
  helper (~190 LOC) that switches on the JsonValue tag (Str /
  Object / default), then runs a string-cascade compare
  against each variant name. **Str path:** each no-payload
  variant gets one
  `if jstr == "VariantName" { EnumInit(VariantName) }` arm.
  **Object path:** extract the `Map<String, JsonValue>`
  entries via `EnumPayload(variant="Object")`, pull the single
  variant key via `__mn_map_keys`+`keys[0]`, cascade-compare
  against each payload-bearing variant, decode the payload(s)
  positionally (1-tuple → recurse `_decode_json_field`;
  n-tuple → extract `JsonValue::Array`'s inner
  `List<JsonValue>` and decode each element by its declared
  payload type), then `EnumInit` with the decoded payloads.
  **Linear cascade** — fast enough for typical enums (< 20
  variants); hash-based dispatch is a v5.40+ candidate.
  **Js.4.F.0 — enum/struct disambiguation.**
  `_resolve_type_expr` cannot distinguish enum from struct at
  parse time — both come through as `TypeKind.STRUCT` with
  the user-supplied name. The Js.4.F.1 + Js.4.F.2 branches
  are routed inside the existing STRUCT branches: check
  `self._module.enums` first (with the skip list
  `{Option, Result, JsonValue}` keeping compiler-internal
  enums on their existing paths — OPTION is handled
  separately, Result is the parent context never reached as a
  struct field, JsonValue is the recursive case routed via
  `_ensure_json_types_registered`), fall through to the
  struct path only if the name is genuinely a struct.
  **Externally-tagged JSON shape locked at PLAN.** Three
  shapes were on the table (externally tagged
  `{"V": payload}`, internally tagged `{"tag": "V", ...}`,
  adjacently tagged `{"tag": "V", "payload": ...}`);
  externally tagged was chosen — most common in JSON-RPC,
  OpenAI / Anthropic function-calling schemas, and Rust
  serde's default derive output; round-trips trivially
  through the existing `_emit_list_decode_body` for
  multi-payload variants. Special case: no-payload variants
  encode as the bare string `"VariantName"` (not
  `{"VariantName": null}`) — matches Rust serde's
  `untagged()` for unit variants and is what most LLMs
  produce in function-call responses.
  **Self-host mirror N/A by construction**: Phase 0 grep
  returned 0 matches. The Js.4 typed-serde surface shipped
  Python-bootstrap-only at v5.36.0 and has not been mirrored.
  STRICT preserved trivially.
  **Test infrastructure extension.** Three new `.mn` test
  files appended to `TEST_FILES` in
  `tests/stdlib/test_struct_json_runtime.py`:
  `test_to_json_enum_field.mn` (Js.4.F.1 single-direction
  encode covering all three variant payload shapes),
  `test_from_json_enum_field.mn` (Js.4.F.2 single-direction
  decode covering all three shapes), and
  `test_to_from_enum_roundtrip.mn` (load-bearing round-trip
  ensuring encode and decode wire to the same JSON shape).
  **18/18 GREEN** at HEAD (was 15 at v5.39.6; +3).
  **Match arms use block-form actions** (`=> { ok = ... }`)
  because the parser does not accept `=> return EXPR` after a
  pattern — collect success into a mutable flag and return
  it. Documented in each test file preamble as a v5.40+
  parser-ergonomics candidate. Falsifiability locked per fix
  — reverting either branch fails the corresponding
  single-direction test plus the round-trip; reverting both
  fails all three new tests.
  **Hd-class preventative** — `docs/SPEC.md` header re-synced
  from "v5.39.6 cut" to "v5.39.7 cut" with new sync block
  documenting the externally-tagged invariant decision +
  Js.4.\* arc closeout. `check_doc_freshness.py` GREEN;
  `check_changelog_honesty.py` GREEN. Source delta: ~310 LOC
  `mapanare/lower.py` (Js.4.F.1 helper + branch ~120 LOC;
  Js.4.F.2 helper + branch ~190 LOC) + ~225 LOC `.mn` test
  cases (3 files) + ~22 LOC `test_struct_json_runtime.py`
  TEST_FILES + ~115 LOC CHANGELOG + ~50 LOC SPEC sync + this
  CLAUDE.md release-notes entry + mechanical
  bump_version.py edits. **Arc retrospective:** v5.39.0 →
  v5.39.7 closed every `TypeKind` branch in
  `_encode_field_to_json` / `_decode_json_field` that
  v5.36.0's Phase-0 audit identified as structurally
  incomplete. Round-trip now works end-to-end for: primitives
  (v5.39.2), multi-field structs (v5.39.2), nested structs
  (v5.39.3 + v5.39.4), `List<X>` (v5.39.4 + v5.39.5),
  `Map<String, V>` (v5.39.6), and tagged-union enums
  (v5.39.7). The bundling discipline (one TypeKind per
  release, with documented invariant decisions for the harder
  cases) traded release count for falsifiability rigor —
  every fix has a revert-and-restore test pair locked in the
  regression suite. Aggregate state entering v5.40.0:
  **0 HIGH** (Js.4.F.\* closed; typed-serde round-trip closed
  for every common LLM JSON shape) / **1 MEDIUM** (macOS
  notarization carry from v5.33.0 Nu.2) / ~5 LOW (hash-
  dispatched enum decode, internally/adjacently tagged shapes,
  custom serde rename attributes, parser ergonomic
  `=> return EXPR`, prior carries). **Js.4.\* arc CLOSED.
  v5.40.0 manifesto-arc kickoff (`ask` / `ask_typed::<T>`)
  fully unblocked.** See
  `docs/roadmap/v5/v5.39.7/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.39.6** (ready, not tagged) — **Js.4.E.1 + Js.4.E.2 —
  typed-serde MAP encode + decode; round-trip closure for
  `Map<String, V>`-typed fields.** Sibling release to v5.39.5
  (LIST decode); bundles encode + decode in one release because
  Map's invariant decision is simpler than LIST's was
  (string-key only — JSON object keys are strings per RFC 8259
  §4) and both halves are mechanical mirrors of v5.39.4 +
  v5.39.5 patterns. Adds **zero language features, zero new
  MIR ops, zero new IR shapes, zero new C runtime exports**.
  **Strict 3-stage fixed point preserved by construction** at
  v5.39.5's **241,898 lines / 0 diff** (40-release strict
  streak from v5.7.1; zero `mapanare/self/*.mn` source
  touches — Phase 0 verified
  `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **Js.4.E.1 — MAP encode.**
  `mapanare/lower.py:2689::_encode_field_to_json` had explicit
  handlers for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT`
  (v5.39.3) and `LIST` (v5.39.4) but no branch for
  `TypeKind.MAP`. The fallback at
  `Call(fn_name="str", args=[field_val])` emitted the literal
  `<?>` placeholder. Pre-fix `Bag("box", #{"a": 1, "b": 2})`
  encoded as `{"name": "box", "lookup": <?>}`; post-fix encodes
  as `{"name": "box", "lookup": {"a": 1, "b": 2}}` (key order
  unspecified per RFC 8259). Fix adds a new
  `_emit_map_json_body(map_val, val_type) -> Value` helper
  mirroring v5.39.4's `_emit_list_json_body` shape: iterate via
  `__mn_map_keys` (returns `List<String>`) + per-key IndexGet
  on the map (lowered to `__mn_map_get`), emit
  `"key": value` pairs separated by `, `, recurse through
  `_encode_field_to_json` per value so nested
  `Map<String, Struct>` / `Map<String, List>` /
  `Map<String, Map>` fall through STRUCT / LIST / MAP /
  primitive branches uniformly. Mutable-Phi loop pattern
  matches v5.39.4. **Js.4.E.2 — MAP decode.**
  `mapanare/lower.py:3166::_decode_json_field` had explicit
  handlers for primitives + OPTION + STRUCT (v5.39.4) + LIST
  (v5.39.5) but no branch for `TypeKind.MAP`. Pre-fix
  `from_json::<Bag>("{\"lookup\": {\"a\": 1}}")` SEGV'd
  (consumer treated raw JsonValue::Object enum bytes as a
  `MnMap*`). Fix adds a new
  `_emit_map_decode_body(jval, val_type) -> Value` helper
  mirroring v5.39.5's `_emit_list_decode_body` decode-side
  shape: extract `Map<String, JsonValue>` from the `Object`
  variant via `EnumPayload(variant="Object", payload_idx=0)`,
  initialize an empty `Map<String, V>` accumulator (relies on
  v5.39.2's `_do_map_init` empty-literal type-derivation fix
  for correct bucket sizing), iterate keys, recurse-decode per
  value, accumulate via `IndexSet` (lowered to
  `__mn_map_set`).
  **No SSA-name-reuse trick needed (vs. v5.39.5 ListPush)** —
  Phase 1 audit confirmed `MAP` lowers to `PTR` in the IR
  (`emit_llvm_text._rty`), and `__mn_map_set` mutates the
  bucket array in place without changing the outer `MnMap*`.
  The accumulator value is invariant across loop iterations,
  so the decode helper uses a single counter phi (no acc phi).
  **Invariant decision (locked at PLAN — no Phase 0 audit)**:
  `Map<K, V>` fields with non-String K → compile-time error.
  Diagnostic shape: `to_json/from_json: Map<K, V> requires
  K = String (got <KIND>)`. Rationale: JSON object keys are
  strings per RFC 8259 §4; `Map<Int, X>` and `Map<Float, X>`
  have no canonical JSON projection. Rejected silent lossy
  coercion (`str(key)` → asymmetric round-trip) and runtime
  error (surfaced too late) in favor of compile-time
  rejection. Documented as `### Changed` (potentially
  breaking-ish but no production user has exercised this path
  pre-fix — encode emitted `<?>`, decode SEGV'd).
  **Self-host mirror N/A by construction**: Phase 0 grep
  returned 0 matches. The Js.4 typed-serde surface shipped
  Python-bootstrap-only at v5.36.0 and has not been mirrored.
  STRICT preserved trivially.
  **Test infrastructure extension.** Two new `.mn` test files
  (`test_to_json_map_field.mn`, `test_from_json_map_field.mn`,
  3 sub-cases each wrapped in helper functions per the v5.39.5
  caveat about bare `from_json_merge` block labels) appended
  to `TEST_FILES`. Plus 2 parametrized rejection cases
  (`test_typed_serde_map_nonstring_key_rejected`) asserting
  `RuntimeError` for `Map<Int, V>` and `Map<Float, V>` fields.
  **15/15 GREEN** at HEAD (was 11 at v5.39.5; +4 total).
  Falsifiability locked per fix — disabling either MAP branch
  in `lower.py` makes the corresponding test fail; reapplying
  restores GREEN.
  **Hd-class preventative** — `docs/SPEC.md` header re-synced
  from "v5.39.5 cut" to "v5.39.6 cut" with new sync block
  documenting the MAP invariant decision.
  `check_doc_freshness.py` GREEN; `check_changelog_honesty.py`
  GREEN. Source delta: ~185 LOC `mapanare/lower.py`
  (Js.4.E.1 helper + branch ~95 LOC; Js.4.E.2 helper + branch
  ~90 LOC) + ~160 LOC `.mn` test cases (2 files) + ~44 LOC
  `test_struct_json_runtime.py` (TEST_FILES + rejection
  parametrized cases) + ~120 LOC CHANGELOG + ~35 LOC SPEC sync
  + this CLAUDE.md release-notes entry + mechanical
  bump_version.py edits. Aggregate state entering v5.39.7:
  **0 HIGH** (Js.4.E.\* closed) / **1 MEDIUM** (macOS
  notarization carry from v5.33.0 Nu.2) / ~6 LOW (added ENUM
  encode/decode as v5.39.7 candidate — last typed-serde piece
  before v5.40.0 manifesto-arc kickoff). **Js.4.E.\* arc
  CLOSED.** See
  `docs/roadmap/v5/v5.39.6/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.39.5** (ready, not tagged) — **Js.4.D.3 — typed-serde
  LIST decode (round-trip closure for List-typed fields);
  v5.39.x arc CLOSED.** Symmetric pair to v5.39.4 Js.4.D.1
  (LIST encode). Closes the last v5.39.x-deferred typed-serde
  gap before the v5.40.0 manifesto-arc kickoff. After this
  release, the typed-serde round-trip
  `to_json::<T>` ↔ `from_json::<T>` closes for **every shape
  v5.40.0 Ai.\* (`ask_typed::<T>`) actually returns** from
  typical LLM responses (primitive, struct, nested struct,
  `List<primitive>`, `List<struct>`). Adds **zero language
  features, zero new MIR ops, zero new IR shapes, zero new C
  runtime exports**. **Strict 3-stage fixed point preserved
  by construction** at v5.39.4's **241,898 lines / 0 diff**
  (39-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches — Phase 0 verified
  `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **Js.4.D.3 — LIST decode.**
  `mapanare/lower.py:3166::_decode_json_field` had explicit
  handlers for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT`
  (the latter from v5.39.4) but no branch for
  `TypeKind.LIST`. The fallback `return jval` returned the
  raw `JsonValue::Array` enum where the consumer expected the
  typed `List<X>` value — silent shape mismatch surfaced as
  wrong list contents (or downstream segfault on element
  access). Pre-fix
  `from_json::<Bag>("{\"items\": [1, 2, 3]}")` printed
  garbage `94467072822368` for `len(b.items)`; post-fix
  prints `3`. Fix adds a new
  `_emit_list_decode_body(arr_jval, inner_type) -> Value`
  helper mirroring v5.39.4's `_emit_list_json_body` shape on
  the decode side: extract `List<JsonValue>` from the `Array`
  variant via `EnumPayload(variant="Array", payload_idx=0)`,
  initialize an empty `List<inner>` accumulator, mutable-Phi
  loop over the inner array length, recurse through
  `_decode_json_field` per element, accumulate via in-place
  `ListPush` (mirrors `_lower_method_call`'s `.push()` SSA
  name-reuse pattern at `mapanare/lower.py:3298` — the dest
  reuses `acc_phi_dest`'s name so the emitter's phi alloca
  acts as the single mutable list slot across iterations).
  Element type from `target_type.type_info.args[0]`;
  recursion handles nested `List<List<X>>`, `List<Struct>`,
  etc. uniformly through the existing dispatch.
  **In-place ListPush across the loop boundary** — Phase 1
  audit confirmed Option A (in-place push reusing the phi
  dest's SSA name) works. The phi alloca system at
  `mapanare/emit_llvm_text.py:2461-2473` registers
  `_alloc[acc_phi_dest.name] = (%phi.<name>, ty)`; ListPush
  at `:4761` finds the alloca via `_get_ptr`, calls
  `__mn_list_push` which mutates the buffer in place, then
  reloads. The deferred phi store from the body-exit
  incoming becomes a no-op load-from-self / store-to-self
  because `new_acc.name == acc_phi_dest.name`. Option B
  fallback (`Copy`-then-`ListPush`) was on the table but
  Phase 1 spike produced valid IR for Option A, so Option A
  shipped.
  **Self-host mirror N/A by construction**: Phase 0 grep
  returned 0 matches. The Js.4 typed-serde surface shipped
  Python-bootstrap-only at v5.36.0 and has not been
  mirrored. STRICT preserved trivially.
  **Test infrastructure extension.** New
  `stdlib/encoding/json/tests/test_from_json_list_field.mn`
  (~80 LOC, 3 sub-cases: `List<Int>` with 3 elements, empty
  list, `List<String>` with 2 elements) appended to
  `TEST_FILES` in
  `tests/stdlib/test_struct_json_runtime.py`. Each sub-case
  is wrapped in its own helper function because
  `_lower_from_json`'s `from_json_merge` / `decode_object`
  block labels are bare (not `_fresh_block`-prefixed);
  multiple `from_json::<T>` calls in one function body
  collide pre-MIR-verifier. Documented as a v5.39.6+ LOW
  (cosmetic; surfaced because v5.39.5's test exercised the
  multi-decode shape that prior tests didn't). 11/11 GREEN
  at HEAD (was 10 at v5.39.4 HEAD; +1).
  **Strengthened `test_to_from_nested_roundtrip.mn`** with
  three new assertions
  (`len(decoded.inner.ints) == 3`,
  `decoded.inner.ints[0] == 10`,
  `decoded.inner.ints[2] == 30`). v5.39.4 deliberately
  omitted these because the embedded `List<Int>` field would
  have failed on the decode side; v5.39.5 closes the gap.
  Falsifiability locked per fix — reverting the
  `TypeKind.LIST` branch in `_decode_json_field` makes
  `test_from_json_list_field` SEGV (exit -11) and the
  strengthened nested round-trip fail on the new
  `inner.ints` assertions; reapplying restores both to
  GREEN.
  **Hd-class preventative** — `docs/SPEC.md` header
  re-synced from "v5.39.4 cut" to "v5.39.5 cut" with new
  sync block. `check_doc_freshness.py` GREEN;
  `check_changelog_honesty.py` GREEN. Source delta: ~85 LOC
  `mapanare/lower.py` (helper + branch) + ~80 LOC `.mn`
  test case + ~8 LOC nested-roundtrip strengthening + ~6
  LOC `test_struct_json_runtime.py` TEST_FILES update +
  ~110 LOC CHANGELOG + ~30 LOC SPEC sync + this CLAUDE.md
  release-notes entry + mechanical bump_version.py edits.
  Aggregate state entering v5.40.0: **0 HIGH** (Js.4.D.3
  closed; typed-serde round-trip closed for v5.40.0 Ai.\*
  call shapes) / **1 MEDIUM** (macOS notarization carry
  from v5.33.0 Nu.2) / ~10 LOW (added MAP encode/decode,
  ENUM encode/decode, bare block labels in
  `_lower_from_json` cosmetic). **Js.4.\* arc CLOSED for
  v5.40.0 dependencies.** v5.40.0 manifesto-arc kickoff
  (`ask`/`ask_typed::<T>`) unblocked. See
  `docs/roadmap/v5/v5.39.5/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.39.4** (ready, not tagged) — **Js.4.D.1 + Js.4.D.2 —
  typed-serde round-trip closure for nested-struct + List-typed
  fields.** Two siblings to v5.39.3's STRUCT field encoding
  (Js.4.C), bundled in one release because together they unlock
  the `to_json::<T>` ↔ `from_json::<T>` round-trip for the
  shapes v5.40.0 Ai.\* (`ask_typed::<T>`) actually returns. After
  this release, the typed-serde round-trip handles
  `struct Wrap { name: String, inner: Inner }` end-to-end
  (encode → decode → field-by-field equality holds), and
  List-typed fields encode element-by-element. Adds **zero
  language features, zero new MIR ops, zero new IR shapes,
  zero new C runtime exports**. **Strict 3-stage fixed point
  preserved by construction** at v5.39.3's **241,898 lines / 0
  diff** (38-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches — Phase 0 verified
  `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **Js.4.D.1 — LIST encode.**
  `mapanare/lower.py:2689::_encode_field_to_json` had explicit
  handlers for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT`
  (the latter from v5.39.3) but no branch for `TypeKind.LIST`.
  The fallback `Call(fn_name="str", args=[field_val])` emitted
  the literal `<?>` placeholder via `_mkstr("<?>")`. Pre-fix
  `Bag("box", [1, 2, 3])` encoded as
  `{"name": "box", "items": <?>}`. Fix adds a new
  `_emit_list_json_body(list_val, inner_type) -> Value` helper
  emitting a counter+phi loop that calls `_encode_field_to_json`
  per element, recursing through STRUCT / LIST / primitive
  branches uniformly. Empty `[]`, `["foo", "bar"]`, and
  `[{"id": 1, "name": "a"}, ...]` all encode correctly post-fix.
  Mutable-Phi loop pattern: emit Phi instructions at header with
  empty incoming, fill incoming after body's exit label is known
  (`Phi.incoming` is a mutable list — pattern is safe).
  **Js.4.D.2 — STRUCT decode.**
  `mapanare/lower.py:3019::_decode_json_field` had explicit
  handlers for primitives + OPTION but no branch for
  `TypeKind.STRUCT`. The fallback returned the raw `JsonValue`
  enum where the consumer expected the struct shape — silent
  shape mismatch surfaced as wrong field values after decode
  (no link error, no SEGV — just garbage data). Pre-fix nested
  `from_json::<Wrap>(s)` returned a Wrap with `inner.x=0` /
  `inner.y=""`. Fix mirrors v5.39.3's encode-side helper-extract
  pattern: extracted
  `_emit_decode_struct_inline(json_val, struct_name) -> Value`
  from `_lower_decode_to`'s Object branch (the field-extraction
  + StructInit body, ~30 LOC); the helper is shared between the
  top-level `decode_to::<T>` / `from_json::<T>` Ok-path
  (replacing the inlined body) and the new STRUCT branch in
  `_decode_json_field` (which trusts the JsonValue is an Object
  variant, consistent with the no-tag-check behavior of the
  primitive branches).
  **Field lookup audit (load-bearing):** confirmed at
  `mapanare/lower.py:2912` that `_lower_decode_to` uses
  by-name lookup (`Const(key=fname)` → `IndexGet(entries, key)`)
  — not positional — so the round-trip works for any JSON
  producer regardless of field-declaration order.
  **Bundle scope: STRUCT decode + LIST encode only.** MAP
  encoding has the JSON-string-key invariant question (reject
  vs coerce vs runtime-error); ENUM encoding has the tagged-
  union shape question (`"VariantName"` vs `{"Variant":
  payload}` vs `{"tag": ..., "payload": ...}`); LIST/MAP/ENUM
  decoding mirrors the same questions on the parse side. Each
  deserves its own Phase 0 audit and lead-approved invariant
  decision. v5.39.5+ picks them up.
  **Self-host mirror N/A by construction**: Phase 0 grep
  returned 0 matches. The Js.4 typed-serde surface shipped
  Python-bootstrap-only at v5.36.0 and has not been mirrored.
  STRICT preserved trivially.
  **Test infrastructure extension.** Three new `.mn` test
  files appended to `TEST_FILES` in
  `tests/stdlib/test_struct_json_runtime.py`:
  `test_to_json_list_field.mn` (Js.4.D.1 single-direction encode),
  `test_from_json_nested_struct.mn` (Js.4.D.2 single-direction
  decode), and `test_to_from_nested_roundtrip.mn` (load-bearing
  round-trip with embedded `List<Int>` field exercising both
  fixes). 10/10 GREEN at HEAD (was 7 at v5.39.3 HEAD; +3).
  **Falsifiability locked per fix** — reverting either branch
  fails the corresponding single-direction test; reverting
  both fails the round-trip with the diverging-field signature.
  **Hd-class preventative** — `docs/SPEC.md` header re-synced
  from "v5.39.3 cut" to "v5.39.4 cut" with new sync block.
  `check_doc_freshness.py` GREEN; `check_changelog_honesty.py`
  GREEN. Source delta: ~165 LOC `mapanare/lower.py` (Js.4.D.1
  helper + branch ~115 LOC; Js.4.D.2 helper extraction + branch
  ~50 LOC net) + ~80 LOC `.mn` test cases (3 files) + ~10 LOC
  `test_struct_json_runtime.py` TEST_FILES update + ~85 LOC
  CHANGELOG + ~30 LOC SPEC sync + this CLAUDE.md release-notes
  entry + mechanical bump_version.py edits. Aggregate state
  entering v5.39.5: **0 HIGH** (Js.4.D.1 + Js.4.D.2 closed) /
  **1 MEDIUM** (macOS notarization carry from v5.33.0 Nu.2) /
  ~10 LOW (added MAP encode, ENUM encode, LIST/MAP/ENUM decode
  as v5.39.5+ candidates). See
  `docs/roadmap/v5/v5.39.4/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.39.3** (ready, not tagged) — **Js.4.C — `to_json::<T>`
  nested-struct recursion.** Split-from-v5.39.2 follow-on.
  v5.39.2 closed the runtime SEGV in `from_json::<T>` (Js.4.B.2)
  but explicitly held back the `to_json::<T>` nested-struct fix
  because it lives in a different code path. v5.39.3 closes that
  hole. After this release, the typed-serde encode path
  (`to_json::<T>`) handles nested struct fields end-to-end; the
  manifesto-arc ergonomic v5.40.0 Ai.\* will exercise via
  `ask_typed::<T>`. Adds **zero language features, zero new MIR
  ops, zero new IR shapes, zero new C runtime exports**. **Strict
  3-stage fixed point preserved by construction** at v5.39.2's
  **241,898 lines / 0 diff** (37-release strict streak from v5.7.1;
  zero `mapanare/self/*.mn` source touches — Phase 0 verified
  `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **The bug.** `mapanare/lower.py:2681::_encode_field_to_json`
  had explicit handlers for `STRING` / `INT` / `FLOAT` / `BOOL` /
  `OPTION` (the latter recursing on the inner type) but no branch
  for `TypeKind.STRUCT`. The fallback at line 2762
  (`Call(fn_name="str", args=[field_val])`) emitted the literal
  `<?>` placeholder via `mapanare/emit_llvm_text.py:3465`'s
  `r, _ = self._mkstr("<?>")`. Latent since v5.36.0 Js.4 ship;
  the v5.36.0 `tests/stdlib/test_struct_json.py` was compile-only
  — the placeholder text was syntactically present in IR but
  never link-tested. **Fix.** Refactored `_lower_encode_struct`
  to delegate to a new shared `_emit_struct_json_body(struct_val,
  struct_name) -> Value` helper. Added the missing `TypeKind.STRUCT`
  branch in `_encode_field_to_json` that recurses through the
  same helper, guarded on
  `struct_name in self._module.structs`. The two call sites (the
  top-level `encode_struct::<T>` / `to_json::<T>` intrinsic and
  the new STRUCT-typed-field recursion) now share one load-bearing
  emitter. ~70 LOC change. **Bundle scope: STRUCT only.** Phase 1
  review of the LIST iteration MIR sketch put it at ~30-50 LOC
  (counter alloca + `len()` runtime call + comparison + IndexGet
  + accumulator) — exceeded PLAN's ~20 LOC bundle threshold.
  MAP and ENUM also held: MAP has the JSON-string-key invariant
  question (reject vs coerce vs runtime-error); ENUM has the
  tagged-union shape question (`"VariantName"` vs `{"Variant":
  payload}` vs `{"tag": ..., "payload": ...}`). v5.39.4 will
  pick these up together once the ENUM shape decision aligns
  with `from_json::<T>` round-trip semantics. **Self-host
  mirror N/A**: Phase 0 grep returned 0 matches. The Js.4
  typed-serde surface shipped Python-bootstrap-only at v5.36.0
  and has not been mirrored. STRICT preserved trivially by
  construction. **Test.** New
  `stdlib/encoding/json/tests/test_to_json_nested_struct.mn`
  (~30 LOC) appended to v5.39.2's
  `tests/stdlib/test_struct_json_runtime.py::TEST_FILES`.
  Single-direction encode-and-inspect (`to_json::<Wrap>(w)` then
  `String.contains` checks). Single-direction on purpose: the
  `from_json::<T>` decoder
  (`mapanare/lower.py::_decode_json_field`) only handles
  primitive field types at v5.39.3 HEAD — a round-trip equality
  test would fail on the decode side, not the v5.39.3 fix. Round-
  trip for nested structs is a v5.39.4 candidate. Falsifiability
  locked: reverting the new STRUCT branch reproduces the `<?>`
  placeholder; the new test fails with the recorded
  `FAIL test_to_json_nested_struct: still emits <?> placeholder`
  signature. One Edit-and-pytest cycle. **Hd-class preventative**
  — `docs/SPEC.md` header re-synced from "v5.39.2 cut" to
  "v5.39.3 cut" with new sync block. `check_doc_freshness.py`
  GREEN; `check_changelog_honesty.py` GREEN. Source delta:
  ~70 LOC `mapanare/lower.py` (helper extraction + STRUCT branch)
  + ~30 LOC `.mn` test case + ~2 LOC `test_struct_json_runtime.py`
  TEST_FILES update + ~75 LOC CHANGELOG + ~30 LOC SPEC sync +
  this CLAUDE.md release-notes entry + mechanical bump_version.py
  edits. Aggregate state entering v5.39.4: **0 HIGH** (Js.4.C
  closed for STRUCT) / **1 MEDIUM** (macOS notarization carry
  from v5.33.0 Nu.2) / ~8 LOW (added `to_json::<T>` LIST/MAP/ENUM
  nested encoding + `from_json::<T>` nested-struct decoding as
  v5.39.4 candidates). See
  `docs/roadmap/v5/v5.39.3/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.39.2** (ready, not tagged) — **Js.4.B.2 — `from_json::<T>`
  runtime SEGV closeout + link-and-run regression suite.
  v5.39.1+v5.39.2 arc CLOSED.** Second of two release sessions on
  Js.4.B; together they close the v5.36.0-deferred typed-serde
  defect surfaced at v5.40.0 Phase 0 audit. v5.39.1 closed the
  IR-emission shape (no-import case); v5.39.2 closes the runtime
  SEGV in `__mn_map_get` (with-import case). After v5.39.2 ships,
  v5.40.0 (Ai.\* — `ask` keyword, manifesto-arc kickoff) picks up
  cleanly with the typed-output ergonomic intact. Adds **zero
  language features, zero new MIR ops, zero new IR shapes, zero
  new C runtime exports**. **Strict 3-stage fixed point preserved
  by construction** at v5.39.1's **241,898 lines / 0 diff**
  (36-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches). Goldens **95/95**.
  **The bug.** PROMPT/PLAN's leading hypothesis was that
  `_is_self_ref` doesn't recurse through `LIST` / `MAP` / `OPTION`
  / `RESULT` type args, so `JsonValue::Object(Map<String,
  JsonValue>)` and `Array(List<JsonValue>)` weren't marked boxed
  at registration time. **Phase 1 instrumentation confirmed
  `boxed=set()` for JsonValue but the side-by-side IR audit of
  the construction (`malloc(8); store ptr %map`) vs extraction
  (`extractvalue, 1; gep {ptr}, 0; load ptr`) showed both sides
  agreed on the unboxed `{ptr}` layout.** The audit's hypothesis
  was wrong about the load-bearing root cause. The actual bug
  was one level deeper: **the Map handle itself was created with
  the wrong sizes/key-type.** GDB pinpointed the SEGV not inside
  `__mn_map_get` but two instructions past its return — at
  `load {i64, ptr} from NULL` in main, because
  `__mn_map_get` returned NULL (key not found). Inspecting the
  Map struct showed `key_size=8, val_size=8, key_type=0/INT` for
  what should have been a `Map<String, JsonValue>` (16/16/1).
  **Root cause:** `mapanare/emit_llvm_text.py::_do_map_init`
  empty-literal branch (`if i.pairs: ... else: ksz, vsz, ktag =
  8, 8, 0`) hardcoded `(8, 8, 0)` defaults instead of deriving
  from the declared `MapInit.key_type` / `MapInit.val_type`.
  **Any** `Map<String, X> = #{}` or `Map<Float, X> = #{}` was
  silently miscompiled. `decode_object_inner`'s
  `pon mut entries: Map<String, JsonValue> = #{}` was the
  load-bearing instance. Latent since the multi-typed map
  literal surface landed; never surfaced because the original
  `tests/stdlib/test_struct_json.py` was compile-only. **Fix:**
  derive `ksz` / `ktag` from `i.key_type` and `vsz` from
  `i.val_type` unconditionally. ~25 LOC change. Defensive
  symmetry fix in `_do_enum_init`: Map values consumed as enum
  payloads now also drain from `_map_vars` (was: only
  `_list_vars`) — doesn't fire in the v5.39.2 repro but the
  asymmetry was a latent footgun. **Self-host mirror N/A**:
  Phase 0 verified `mapanare/self/emit_llvm.mn:3106-3169::
  emit_map_init` already derives `key_size`/`val_size` from
  `key_ty`/`val_ty` regardless of pair count (sensible defaults
  16 / 64 for STRUCT/ENUM). The Python bug was a latent drift
  between Python and self-host that the self-host already had
  right. STRICT preserved trivially; v5.39.2 makes zero
  `mapanare/self/*.mn` source touches. **Link-and-run
  regression suite** — new `tests/stdlib/test_struct_json_runtime.py`
  + 6 `.mn` test cases under `stdlib/encoding/json/tests/`
  mirrors v5.34/v5.35/v5.39.0 concat pattern. This is the test
  infrastructure that should have existed since v5.36.0 — the
  compile-only `test_struct_json.py` (preserved unchanged) is
  exactly why Js.4.B stayed latent for 4 releases. All 6
  GREEN; v5.39.1's `test_struct_json_ir_shape.py` (4) +
  `test_struct_json_layout.py` (2) preserved GREEN.
  **Falsifiability round-trip locked as the test suite
  itself** — revert `_do_map_init`, all 6 cases fail with the
  recorded SEGV signature; reapply, all 6 pass. One
  Edit-and-pytest cycle. **`to_json::<T>` nested-struct split
  to v5.39.3** — `to_json::<Wrap>(w)` with struct-typed field
  still emits `<?>`; different code path
  (`_emit_struct_to_json`), out of v5.39.2's scope. **Hd-class
  preventative** — `docs/SPEC.md` header re-synced from
  "v5.39.1 cut" to "v5.39.2 cut". `check_doc_freshness.py`
  GREEN. Source delta: ~25 LOC `mapanare/emit_llvm_text.py`
  (`_do_map_init` + `_do_enum_init` defensive map-vars
  removal) + ~120 LOC pytest harness + ~120 LOC `.mn` test
  cases (6 files) + ~125 LOC CHANGELOG + ~30 LOC SPEC sync +
  this CLAUDE.md release-notes entry + mechanical
  bump_version.py edits. Aggregate state entering v5.39.3:
  **0 HIGH** (Js.4.B fully closed) / **1 MEDIUM** (macOS
  notarization carry from v5.33.0 Nu.2) / ~7 LOW (added
  `to_json::<T>` nested-struct as v5.39.3 candidate). **Js.4.B
  arc CLOSED.** v5.40.0 manifesto-arc kickoff unblocked. See
  `docs/roadmap/v5/v5.39.2/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.39.1** (ready, not tagged) — **Js.4.B.1 — `from_json::<T>`
  IR-emission shape fix (no-import case).** First of two release
  sessions dedicated to closing **Js.4.B** (the v5.36.0-deferred
  typed-serde defect that v5.40.0 Phase 0 audit
  (`docs/roadmap/v5/v5.40.0/PRE_PHASE_AUDIT.md`) re-diagnosed as
  significantly worse than the original SESSION_REPORT
  documented — actually two structurally distinct failure modes,
  not one). v5.39.1 closes the **IR-emission shape mismatch**
  in the no-import case; v5.39.2 will close the **runtime SEGV
  in `__mn_map_get`** in the with-import case. After v5.39.2
  ships, v5.40.0 (Ai.\* — `ask` manifesto-arc kickoff) picks up
  cleanly. Adds **zero language features, zero new MIR ops,
  zero new IR shapes, zero new C runtime exports**. **Strict
  3-stage fixed point preserved by construction** at v5.39.0's
  **241,898 lines / 0 diff** (35-release strict streak from
  v5.7.1; zero `mapanare/self/*.mn` source touches). Goldens
  **95/95**.
  **The bug.** When user code calls `from_json::<T>(s)` without
  `import stdlib::encoding::json`, the lowerer emits
  `EnumPayload(variant="Object", ...)` for the `JsonValue`
  subject. The emitter at `_do_enum_payload`
  (`mapanare/emit_llvm_text.py:5187`) checks `if en in
  self._enums` — false because `JsonValue` was never
  registered. Falls into the Result/Option fallback's `else`
  branch which emits `extractvalue {i64, ptr} %enum, 1` — this
  yields a `ptr` (the boxed payload pointer) but `_put` tags
  the value with `dt = self._rty(i.dest.ty)` which is `i64`
  for an Int field. The next consumer fails IR validation:
  `'%pl.48' defined with type 'ptr' but expected 'i64'`.
  Latent since v5.36.0 Js.4 ship; the v5.36.0
  `tests/stdlib/test_struct_json.py` was compile-only
  (validated IR text generation, never linked) so the
  validation-time failure stayed hidden through v5.36.0 →
  v5.39.0.
  **Strategy A (audit-recommended) chosen.** New
  `_ensure_json_types_registered(self) -> None` helper at
  `mapanare/lower.py:2767` injects the canonical `JsonValue`
  (7 variants: Null, Bool(Bool), Int(Int), Float(Float),
  Str(String), Array(List<JsonValue>),
  Object(Map<String, JsonValue>)) and `JsonError` (3 fields:
  message: String, line: Int, col: Int) layouts into
  `self._module.enums` / `self._module.structs` when not
  already present. Idempotent — guarded with `if "JsonValue"
  not in self._module.enums`. Called at the top of
  `_lower_decode_to` AND `_lower_from_json` (the two
  Js.4-related entry points) so registration runs before any
  `EnumPayload` emission. Layout uses `MIRType(TypeInfo(...))`
  wrapping (matches the stored shape from
  `_register_declarations` at `lower.py:822-848`) and the
  `mir_int()` / `mir_string()` / `mir_bool()` factory helpers
  already imported at line 159-162 — no new imports needed.
  With `JsonValue` registered, the proper boxed-enum
  extraction path (`emit_llvm_text.py:5134-5185`) fires;
  downstream extraction is correct. Runtime SEGV in
  `__mn_map_get` remains — that's v5.39.2's whole release.
  **Strategy B (fix the emitter fallback)** held — narrower
  contract for the fallback path is the right invariant; the
  v5.39.2 runtime SEGV fix needs the Strategy A path anyway
  because `_is_self_ref` recursion only matters once
  `JsonValue` is properly registered.
  **Layout-drift guard** — `tests/stdlib/test_struct_json_layout.py`
  (2 cases) parses `stdlib/encoding/json.mn`, extracts the
  `JsonValue` enum + `JsonError` struct AST shape, asserts
  shape-for-shape match against the lower.py-injected canonical
  layout. If json.mn drifts (variant rename, field reorder,
  type change), the no-import path silently emits IR against
  the wrong shape — the with-import path keeps working,
  masking the divergence. The drift test fails loudly with a
  pointer to the lower.py update needed.
  **IR-shape regression test** —
  `tests/stdlib/test_struct_json_ir_shape.py` (4 cases):
  parametrized over Int / String / Bool single-field structs +
  one mixed Int+String case. Validates with `clang -c` (full
  IR validation, no link). Pre-fix all four fail with the exact
  `'%pl.NN' defined with type 'ptr' but expected ...` error
  shape; post-fix all four pass. The no-import case CANNOT
  link end-to-end (`decode` undefined without the json
  import) and that is correct, not a regression — runtime
  correctness for the with-import path is gated separately in
  v5.39.2's link-and-run suite. The pre-existing
  `tests/stdlib/test_struct_json.py` (20 compile-only cases)
  is preserved unchanged.
  **PROMPT/PLAN deviation (load-bearing) — Phase 2 self-host
  mirror N/A.** PROMPT/PLAN scoped a `mapanare/self/lower.mn`
  mirror as load-bearing for STRICT and budgeted ~1h.
  Phase 0 verification (`grep -rn "from_json\|decode_to"
  mapanare/self/`) returned zero matches: there is no
  `_lower_from_json` / `_lower_decode_to` in the self-host.
  The Js.4 surface (v5.36.0 Shape B — typed serde intrinsics)
  was Python-bootstrap-only and no self-host mirror has ever
  been shipped. STRICT preserved trivially by construction;
  v5.39.1 makes zero `mapanare/self/*.mn` source touches.
  Documented in `docs/roadmap/v5/v5.39.1/SESSION_REPORT.md`
  + CHANGELOG `### Changed`.
  **Falsifiability round-trip locked** — repro confirmed with
  `/tmp/serde_simple.mn` pre-fix; post-fix clean compile;
  reverted (`s/self._ensure_json_types_registered()/pass/g`),
  reproduced exact pre-fix error
  (`'%pl.48' defined with type 'ptr' but expected 'i64'`),
  reapplied, clean compile. v5.39.2 has the anchor when
  STRICT regressions surface from the deeper runtime fix.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced
  from "v5.39.0 cut" to "v5.39.1 cut" with new sync block
  summarizing the Js.4.B.1 fix and the v5.39.1+v5.39.2 arc
  framing. `check_doc_freshness.py` GREEN.
  Source delta: ~50 LOC `mapanare/lower.py` (helper + 2 call
  sites) + ~165 LOC `tests/stdlib/test_struct_json_ir_shape.py`
  + ~115 LOC `tests/stdlib/test_struct_json_layout.py` +
  ~80 LOC CHANGELOG + ~25 LOC SPEC sync + this CLAUDE.md
  release-notes entry + mechanical bump_version.py edits.
  Aggregate state entering v5.39.2: **1 HIGH** (Js.4.B.2 —
  runtime SEGV in `__mn_map_get` when json import is present;
  arc continuation) / **1 MEDIUM** (macOS notarization;
  carry from v5.33.0 Nu.2) / ~6 LOW (carries unchanged from
  v5.39.0). See
  `docs/roadmap/v5/v5.39.1/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`
  and `docs/roadmap/v5/v5.40.0/PRE_PHASE_AUDIT.md` for
  diagnosis artifacts.

- **v5.39.0** (ready, not tagged) — **Cr.\* — crypto stdlib
  hashing/MAC/random extensions; stdlib gap-close arc CLOSED.**
  Sixth and final release in the stdlib gap-close arc
  (Dt.\* @ v5.34.0, Sq.\* @ v5.35.0, Js.\* @ v5.36.0, Ht.\* @
  v5.37.0, Re.\* @ v5.38.0, Cr.\* @ v5.39.0). **Staged scope
  (deviation from PLAN, lead-approved at Phase 0).** v5.39.0
  ships the easy hashing / streaming / random additions on top
  of the pre-existing `stdlib/crypto.mn` (283 LOC; SHA-1/256/512
  + HMAC-SHA256 + Base64 + Hex + JWT HS256 + random_bytes
  already shipped). AEAD (AES-GCM, ChaCha20-Poly1305 +
  NonceCounter helper), Ed25519 + X25519, and password KDFs
  (PBKDF2, HKDF, Argon2id with explicit-Err fallback) explicitly
  deferred to v5.39.1. Reason: each has its own correctness trap
  (GCM nonce reuse, Ed25519 key serialization, Argon2 OpenSSL
  major-version skew); bundling with the easy hashing additions
  raises the chance one ships subtly wrong, and they are
  structurally independent. **Strict 3-stage fixed point
  preserved by construction at v5.38.0's 241,898 lines / 0 diff**
  (35-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches). Goldens **95/95**.
  **Cr.1 hashing additions:** `sha3_256` (FIPS 202; OpenSSL
  1.1.1+), `blake2b` (RFC 7693; 1.1.0+) with `_raw` variants;
  optional symbols, return empty string on older libcrypto.
  **Cr.1 streaming digest:** `DigestCtx { handle, algo }` opaque
  struct + `digest_new(algo) -> Option<DigestCtx>`,
  `digest_update`, `digest_finalize` (hex / `_raw`). Algo IDs:
  1=SHA-256, 2=SHA-512, 3=SHA-3-256, 4=BLAKE2b. Helper functions
  `algo_sha256()` / `algo_sha512()` / `algo_sha3_256()` /
  `algo_blake2b()` (Mapanare does not yet support top-level
  `const` declarations as of v5.39.0 — minor parser ergonomics
  candidate for v5.40+). Caller MUST call `_finalize` exactly
  once; finalize frees the underlying EVP_MD_CTX* regardless of
  success. Handle = `(int64_t)(intptr_t)ctx` direct cast.
  **Cr.2 HMAC additions:** `hmac_sha512` + `_raw` variant.
  `constant_time_eq(a, b) -> Bool` for timing-safe MAC verify;
  prefers OpenSSL `CRYPTO_memcmp`, falls back to a
  volatile-masked aggregation loop. Streaming `HmacCtx` with
  algo 1 (SHA-256) or 2 (SHA-512); HMAC over SHA-3 / BLAKE2 is
  v5.40.x+ via `EVP_MAC` migration.
  **Cr.5 random extensions:** `random_u64()` reads 8 bytes from
  `random_bytes` packed big-endian; `random_range(low, high)`
  uses rejection sampling to avoid modulo bias. Degenerate
  `random_range(5, 5)` returns 5; `random_range(10, 5)` returns
  low. No new C-runtime exports — both derive from
  `__mn_random_bytes_str`.
  **Cr.7 RFC test corpus:** new
  `stdlib/crypto/tests/test_crypto_smoke.mn` (~190 LOC, surface
  smoke + streaming chunked-vs-one-shot equivalence + random
  distribution sanity) and `test_crypto_corpus.mn` (~110 LOC,
  RFC 6234 SHA-256 / SHA-512, FIPS 202 SHA-3-256, RFC 7693
  BLAKE2b-512, RFC 4231 HMAC tests 1, 2, 4, 5). Pytest harness
  `tests/stdlib/test_crypto_runtime.py` (~165 LOC) mirrors the
  v5.34 / v5.35 / v5.38 concatenation pattern: prepend
  `stdlib/crypto.mn`, compile via Python LLVM emitter, link
  against `libmapanare_rt.a`, run, assert "PASSED". **3/3 GREEN.**
  Pre-existing `tests/stdlib/test_crypto.py` (40 compile-only
  cases) preserved unchanged.
  **Cr.8 C runtime extensions** in `runtime/native/mapanare_io.c`
  (NOT a separate `mapanare_crypto.c` — PLAN's `mapanare_tls.c`
  reference is wrong; OpenSSL plumbing already lives in
  `mapanare_io.c`, same wrap-don't-duplicate decision as v5.35.0
  Sq.7 with `mapanare_db.c`). Ten new `__mn_*` exports appended
  at end of existing crypto block: `__mn_sha3_256_str`,
  `__mn_blake2b_str`, `__mn_hmac_sha512_str`,
  `__mn_constant_time_eq`, `__mn_md_ctx_new`,
  `__mn_md_ctx_update`, `__mn_md_ctx_finalize`,
  `__mn_hmac_ctx_new`, `__mn_hmac_ctx_update`,
  `__mn_hmac_ctx_finalize`. ABI-stable: appended, not inserted;
  stage1 binaries built against pre-v5.39.0 runtime keep working.
  Five new EVP function pointers (`EVP_sha3_256`,
  `EVP_blake2b512`, `CRYPTO_memcmp`, plus `HMAC_CTX_*` legacy
  set) wired into `s_evp` struct as **optional** (NULL is
  legitimate; callers gate at runtime). `evp_load()` resolution
  block extended; required-symbols gate unchanged.
  **Cr.9 docs** — new `docs/stdlib/crypto.md` (~290 LOC):
  quick reference, type/API reference, 5 cookbook recipes
  (one-shot hash, chunked stream hash, timing-safe MAC verify,
  BLAKE2b for keyed hashing, jitter via `random_range`),
  "what's not here yet" v5.39.1 plan, compatibility note for
  the Cr.0 emitter fix.
  **Cr.0 emitter shortcut fix (LOAD-BEARING)** —
  `mapanare/emit_llvm_text.py` had unconditional builtin
  shortcuts at lines 3713-3776 for `sha256`, `hmac_sha256`,
  `base64_encode`, `base64_decode`, `hex_encode`, `random_bytes`,
  `regex_match`, `regex_replace`, `http_get`. These shortcuts
  called the underlying `__mn_*_str` C exports directly,
  bypassing the user-defined wrappers in `stdlib/crypto.mn` /
  `stdlib/text/regex.mn` that hex-encode the output / wrap in
  Result types. When MIR inlining failed (high call-site count
  or function-size threshold), the shortcut won and silently
  changed the return shape — `sha256(x)` returned 32 raw bytes
  instead of 64 hex chars; `hmac_sha256(k, m)` returned 32 raw
  bytes instead of hex. Surfaced by the new RFC corpus tests
  with 5 `hmac_sha256` callsites: 4 returned raw, 1 (the only
  call from inside `hmac_sha256`'s own user-defined chain)
  inlined cleanly. The corresponding `hmac_sha512` callsites
  (no shortcut existed) returned hex correctly — the
  asymmetric-failure pattern was the diagnostic. Latent bug
  since v3.42.0 (when the shortcuts were introduced; user-defined
  `stdlib/crypto.mn` wrappers came later). **Fix:** gate each
  shortcut on `fn not in self._sigs`, deferring to the
  user-defined wrapper when one exists. ~10 LOC change. No
  callers depended on the shortcut's raw-bytes return — raw
  access has always been spelled `sha256_raw` / `hmac_sha256_raw`
  in the stdlib. Pre-existing `test_crypto.py` (40) +
  `test_regex.py` (32) all green; broader stdlib sweep 1001 PASS;
  goldens 95/95 preserved; STRICT fixed point preserved.
  **Cr.0 belongs to the same bug-class as v5.36.0 Js.0**
  (`emit_llvm_text.py` `_san` sanitizer over-stripping `%`)
  and v5.36.0 Js.0.B (Result wrap-shape mismatch) — emitter
  bugs surfaced by extending the stdlib in ways that exercise
  more code paths.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced
  from "v5.38.0 cut" to "v5.39.0 cut" with new sync block
  summarizing Cr.\* additions (specifically enumerating the 10
  new C runtime exports and the Cr.0 emitter fix; runtime-additions
  count is the highest since v5.34.0 Dt.\*).
  `check_doc_freshness.py` GREEN. `check_changelog_honesty.py`
  GREEN. Source delta: ~165 LOC C in `mapanare_io.c` (Cr.1 + Cr.2
  + Cr.8) + ~235 LOC `stdlib/crypto.mn` extensions (Cr.1 + Cr.2 +
  Cr.5) + ~300 LOC `.mn` tests (Cr.7) + ~165 LOC pytest harness
  + ~290 LOC `docs/stdlib/crypto.md` (Cr.9) + ~10 LOC
  `mapanare/emit_llvm_text.py` (Cr.0) + ~85 LOC CHANGELOG +
  ~35 LOC SPEC sync + CLAUDE.md release-notes entry +
  mechanical bump_version.py edits.
  Aggregate state entering v5.39.1: **0 HIGH** (the hard items
  Cr.3 + Cr.4 + Cr.6 are explicitly named for v5.39.1, not
  carried forward as HIGH) / **1 MEDIUM** (macOS notarization,
  carry from v5.33.0 Nu.2) / ~6 LOW (EVP_MAC migration, native
  Bytes type, HMAC over SHA-3/BLAKE2, JWT verify routing through
  constant_time_eq, Pike VM regex rewrite candidate, regex_replace
  single-shot follow-up from v5.38.0). **Stdlib gap-close arc
  CLOSED.** Manifesto arc begins v5.40.0 with `ask` (the user's
  v5.40.0 PROMPT will reference Cr.\* surface for HMAC-signed
  API key handling). See
  `docs/roadmap/v5/v5.39.0/{PLAN.md, PROMPT.md, PRE_PHASE_AUDIT.md,
  SESSION_REPORT.md}`.

- **v5.38.0** (ready, not tagged) — **Re.\* — regex stdlib
  closeout.** Fifth release in the stdlib gap-close arc
  (Dt.\* @ v5.34.0, Sq.\* @ v5.35.0, Js.\* @ v5.36.0, Ht.\* @
  v5.37.0, Re.\* @ v5.38.0). **Zero compiler edits. Zero new
  C runtime exports. Zero `mapanare/self/*.mn` source touches.**
  Strict 3-stage fixed point preserved by construction at
  v5.37.0's **241,898 lines / 0 diff** (33-release strict
  streak from v5.7.1). Goldens **95/95**. v5.38.0 audited the
  pre-existing PCRE2-backed `stdlib/text/regex.mn` (271 LOC,
  shipped at v0.9.0), fixed two pre-existing parse / lowering
  bugs that had silently broken the module at HEAD, and
  extended the surface with a `Regex`-first compile-once API
  plus a `Captures` type with named-group lookup.
  **Phase 0 deviation from PLAN (load-bearing).** PLAN
  specified "net-new module at `stdlib/regex/`, ~600 LOC Pike
  VM"; Phase 0 audit established that a complete PCRE2 wrapper
  was already shipped. Audit committed at
  `docs/roadmap/v5/v5.38.0/PRE_PHASE_AUDIT.md`, surfaced to
  lead, **lead approved keeping PCRE2** (Pike VM rewrite is a
  v6.0+ candidate). Same pattern as v5.34.0 / v5.35.0 / v5.37.0
  — Phase-0-driven scope correction toward the right
  deliverable for the release window.
  **Re.1+Re.2 — Regex-first API**:
  `regex_is_match(r, s) -> Bool`,
  `regex_find(r, s) -> Option<Match>`,
  `regex_find_all(r, s) -> List<Match>`,
  `regex_replace(r, s, repl) -> String`,
  `regex_replace_all(r, s, repl) -> String`,
  `regex_free(r) -> Regex`. The pre-existing pattern-string-
  first free-function API (`regex_match`, `find_all`,
  `replace`, `replace_all`, `regex_split`, `is_match`) is
  **preserved unchanged**.
  **Re.3 — Captures + named groups**: new `NamePair` and
  `Captures` types; `regex_captures(r, s) -> Option<Captures>`;
  `regex_captures_iter(r, s) -> List<Captures>`;
  `captures_get(c, idx) -> Option<String>`;
  `captures_get_named(c, name) -> Option<String>`;
  `captures_count(c) -> Int`. Named groups parse
  `(?P<name>...)` and `(?<name>...)` in pattern source via the
  new `parse_named_groups` walker (Path A — no new C runtime
  exports). Walker handles escapes, character classes,
  non-capturing groups, lookarounds, atomic groups, inline
  flags, and comments. **`Captures` stores group state as
  parallel `List<String> + List<Bool>`** rather than
  `List<Option<String>>` to sidestep the v5.x drop-glue carry
  on `List<Option<X>>` appends (`snapshot_all_groups` hung in
  early testing); public `captures_get` surface preserves
  `Option<String>` so callers don't see the workaround.
  **Backref-bearing replacements work natively** — PCRE2's
  default `pcre2_substitute` recognizes `$0..$9`, `${name}`,
  and `$$` without `PCRE2_SUBSTITUTE_EXTENDED`; existing C
  wrapper at `runtime/native/mapanare_io.c` passes the right
  options. Pattern-side backreferences (`\1`) remain
  out-of-scope (NP-complete).
  **Re.4 — runtime test corpus**:
  `stdlib/text/tests/test_regex_smoke.mn` (10 sections,
  ~270 LOC) covers compile happy + error paths,
  `regex_is_match`, `regex_captures` named-group extraction,
  numbered-group access, unknown-name handling,
  `captures_count`, `captures_iter`, `regex_replace_all`
  with `$1`/`$2`, named backref via `${name}`, `$$` literal
  escape. `stdlib/text/tests/test_regex_corpus.mn` (~150 LOC,
  ~40 cases) covers literals + `.`, quantifiers, anchors,
  character classes, alternation, non-capturing groups,
  capture groups (numbered), inline flag `(?i)`, `find_all`
  count assertions, `replace_all` edge cases. Pytest harness
  `tests/stdlib/test_text_regex.py` mirrors v5.34/v5.35
  concatenation pattern (read regex module, prepend to test
  main body, compile via Python LLVM emitter, link against
  `libmapanare_rt.a`, run, assert "PASSED"). Gated on
  `libpcre2-8` dlopen target. **3/3 GREEN.**
  **Re.5 — `docs/stdlib/regex.md`** (~360 LOC): pattern
  syntax reference, type / API reference, 6 cookbook recipes
  (compile-once match-many; extract named fields; swap pairs
  via `$1`/`$2`; replace via named backref; iterate matches
  with groups; case-insensitive via `(?i)`), deviation notes,
  migration note from the pre-v5.38.0 surface.
  **Two pre-existing bugs fixed in v5.38.0** (both
  silently-broken-at-HEAD, would have failed the user's first
  attempt to use regex from a fresh clone): (1) 17 occurrences
  of `pon _: Int = ...` (the parser does not accept `_` as a
  binding name) — renamed to `pon _drop: Int = ...`; (2)
  `parse_named_groups` underlying `String.substr(start, count)`
  semantics — Mapanare's `substr` third arg is a **count**, not
  an exclusive end-index. The pre-existing `regex_split` at
  lines 235/242 has the same shape `text.substr(offset,
  text_len)` — over-reads past string end, mitigated by PCRE2
  capping bounds; latent silent over-read, not a visible crash.
  **Re.6 — new MEDIUM (deferred)**: `pon m: Option<Match> =
  regex_match(...)` allocates `m` as `i1` instead of as the
  `Option<Match>` aggregate (same bug class as v5.36.0 Js.0.B
  / v5.26.1 Eu.\*). Reproduces standalone with no v5.38.0
  additions involved. Out of scope — fix needed in
  `mapanare/lower.py` / `emit_llvm_text.py`, not in the regex
  module. The v5.38.0 Regex-first API does not trigger this
  bug because `Regex` (not `Option<Match>`) is the local type.
  **`regex_replace` (single-shot) returns subject unchanged**
  on multi-match input — underlying C wrapper without
  `PCRE2_SUBSTITUTE_GLOBAL` does not substitute under current
  testing. v5.38.x follow-up; `regex_replace_all` validated.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced
  from "v5.37.0 cut" to "v5.38.0 cut" with new sync block
  summarizing what v5.38.0 ships. `check_doc_freshness.py`
  GREEN. Source delta: ~461 LOC `stdlib/text/regex.mn` (Re.\*
  surface) + ~270 LOC `test_regex_smoke.mn` + ~150 LOC
  `test_regex_corpus.mn` + ~170 LOC pytest harness + ~360 LOC
  `docs/stdlib/regex.md` + CHANGELOG / CLAUDE.md / SPEC sync /
  mechanical bump_version.py edits. Aggregate state entering
  v5.39.0: **0 HIGH** / **3 MEDIUM** (Re.6 new, Ht.5 typed
  handler waits on Js.4.B, macOS notarization carry from
  v5.33.0 Nu.2) / ~9 LOW (Pike VM rewrite candidate added,
  `regex_replace` single-shot follow-up, Rust regex corpus
  port, plus v5.37.0 carries). See
  `docs/roadmap/v5/v5.38.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.37.0** (ready, not tagged) — **Ht.\* — HTTP App / router /
  middleware / streaming encoders.** Fourth release in the stdlib
  gap-close arc (Dt.\* @ v5.34.0, Sq.\* @ v5.35.0, Js.\* @ v5.36.0,
  Ht.\* @ v5.37.0). New `stdlib/net/http/router.mn` ships an opt-in
  `App` container bundling a path-pattern router (`:name`
  parameters + `*name` wildcards alongside literals; method
  dispatch GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS) with a
  **registration-table middleware** list (Logger / Cors /
  BodyLimit / RequestId / Custom). New
  `stdlib/net/http/streaming.mn` ships RFC 7230 §4.1 chunked
  transfer encoding plus a Server-Sent Events encoder. **Zero
  compiler edits. Zero `mapanare/self/*.mn` source touches.**
  Strict 3-stage fixed point preserved by construction at
  v5.36.0's **241,898 lines / 0 diff** (32-release strict streak
  from v5.7.1). Goldens **95/95**. Twenty-nine new pytest
  assertions across 3 `.mn` test files: 12 router + 6 middleware
  + 11 streaming, all GREEN; pytest harness
  `tests/stdlib/test_http_router.py` mirrors the v5.34/v5.35
  concatenation pattern. The legacy `stdlib/net/http/server.mn`
  `Router` (string-named handlers, `${name}` syntax) is
  **preserved unchanged** — existing pytest coverage in
  `tests/stdlib/test_http_server.py` keeps passing; the v5.37.0
  surface is opt-in via the new module. **Five PROMPT deviations,
  all load-bearing, all structurally driven, all surfaced in
  Phase 0.** **(1) Ht.2 — registration table, not closure
  chain.** PROMPT specified `type Middleware = fn(Request, Next)
  -> Response`. Phase-0 spike confirmed both backends fail on
  indirect calls through fn-typed parameters: native
  `mnc-stage1` produces invalid IR (`use of undefined value`);
  Python LLVM emitter links cleanly but **SEGVs at runtime**.
  Same root cause as v5.35.0's deferred
  `transaction<T>(f: fn() -> ...)` shape. v5.37.0 ships the
  registration-table form (Middleware enum variants); custom
  middleware via `Custom(name)` dispatched through a user-
  written `dispatch_custom_middleware_before` switch. Closure-
  chain shape is a v5.38.0+ candidate. **(2) Ht.1 — ordered
  list of compiled patterns, not recursive trie.** Functionally
  equivalent — same API surface, same priority rule (literal >
  parameter > wildcard, locked with explicit overlap tests),
  same big-O on small route counts. Removes a recursion risk
  in the MIR lowerer that the v5.37.0 release scope did not
  budget for. **(3) Ht.3 ships as documentation only.**
  `stdlib/net/websocket.mn` already had a complete RFC 6455
  client + server (`ws_accept_upgrade`, `ws_recv_full` with
  fragmentation, masking, control-frame size cap, UTF-8
  validation, `wss://` over TLS, `ws_echo_loop`). The PROMPT's
  `stdlib/net/http/ws.mn` would have been a redundant wrapper.
  Cookbook in `docs/stdlib/http.md` shows the integration path.
  Autobahn fixture corpus deferred to v5.38.0+ as **Ht.3.B**.
  **(4) Ht.4 — encoders, not bounded-RSS streamer.** Existing
  `__mn_tcp_send_str(fd, data: String)` C-runtime export takes
  a whole string; a real bounded-RSS streaming writer needs
  `__mn_tcp_send_bytes(fd, ptr, len)` plus a chunk-pump driver
  loop. v5.37.0 ships *encoders* (`chunked_encode`,
  `build_chunked_response`, `SseLite` + `sse_lite_encode_stream`)
  that produce wire-format strings; the wire format is identical
  to what the eventual streamer will write. Pump driver is
  **Ht.4.B** for v5.38.0+. **(5) Ht.5 deferred** pending Js.4.B
  drop-glue fix from v5.36.0 carry. `from_json::<T>` builds
  successfully but SEGVs at runtime in field extraction;
  without working `from_json::<T>` the typed-handler-shorthand
  auto-deserialization has no mechanism. v5.36.x will close
  Js.4.B; v5.38.0+ picks Ht.5 back up. **Headers stored as
  `List<String>` alternating-kv** (not `Map<String, String>`)
  in `Request`, `Response`, and middleware return shapes —
  same v5.x map-in-returned-payload drop-glue motivation as
  `MatchedRoute.params_kv`; helpers `hdr_get` / `hdr_set` /
  `hdr_has` provide the standard Map-style operations on top.
  Five v5.x carry-forward bug-classes documented in source-file
  preambles + CHANGELOG `### Changed`: multi-line struct literals
  not parsed (single-line workaround); `for x in some_list` not
  lowered (index-based `while i < len(xs)` workaround); string-
  aliasing on `xs = xs + [cur]; cur = mut` (snapshot via
  `let snap = cur + ""`); `Map<String, String>` drop-glue in
  returned struct/enum (replace with `List<String>` kv); fn-
  value parameter invocation broken (registration-table dispatch
  instead of closure chain). **Hd-class preventative** —
  `docs/SPEC.md` header re-synced from "v5.36.0 cut" to
  "v5.37.0 cut" with new sync block summarizing what v5.37.0
  ships. `check_doc_freshness.py` GREEN. Source delta: ~600
  LOC `stdlib/net/http/router.mn`, ~250 LOC
  `stdlib/net/http/streaming.mn`, ~400 LOC `.mn` tests, ~110
  LOC pytest harness, ~150 LOC walkthrough example, ~360 LOC
  `docs/stdlib/http.md`, plus CHANGELOG / CLAUDE.md / SPEC sync
  / mechanical bump_version.py edits. Aggregate state entering
  v5.38.0: **0 HIGH** / **2 MEDIUM** (Ht.5 typed handler waits
  on Js.4.B; macOS notarization carry from v5.33.0 Nu.2) / ~7
  LOW (Ht.3.B Autobahn corpus, Ht.4.B bounded-RSS streamer,
  closure-chain middleware, native `Bytes` type,
  `Map<String, String>` drop-glue, plus v5.36.0+ carries).
  See `docs/roadmap/v5/v5.37.0/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.36.0** (ready, not tagged) — **Js.\* — JSON completeness
  arc.** Third release in the stdlib gap-close arc (Dt.\* @
  v5.34.0, Sq.\* @ v5.35.0, Js.\* @ v5.36.0); these three are the
  prerequisites named for v5.40.0 `ask`. **Strict 3-stage fixed
  point preserved by construction at v5.35.0's 241,898 lines / 0
  diff** (31-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches). Goldens **95/95**.
  **Js.1 — JSON parser is now RFC 8259 strict.** Inputs that
  previously parsed silently and now error: leading-zero numbers
  (`01`, `-01`, `00.5`); unescaped control chars in strings (bytes
  U+0000..U+001F including embedded `\n`/`\t`/`\r`); documents
  nesting deeper than 256 levels (was a SEGV pre-fix on inputs
  like `[[[...]]]` × 100k). 8 nst/JSONTestSuite fixtures moved
  from broken to conformant; final corpus state **283 CONFORM /
  35 IMPL / 0 DEVIATE / 0 CRASH = 318**. Strict mode is **not
  opt-out** at this release — no `JsonParseOpts { strict: false }`
  flag yet. Documented in `### Changed` (potentially
  breaking-ish) per CHANGELOG honesty rule. **Js.2** —
  `to_json_pretty(value, indent)` configurable indent (was
  hardcoded 2 spaces); `indent <= 0` falls through to compact
  `to_json` byte-for-byte. New aliases `to_json` / `to_json_pretty`
  / `parse` mirror existing `encode` / `encode_pretty` / `decode`.
  **Js.3 (LITE)** — pull-based streaming API
  (`JsonStreamParser`, `JsonStreamStep`, `json_stream_open`,
  `json_stream_next`, `json_stream_error`) on top of the existing
  batch parser. Ships the API contract; true chunked I/O with
  peak-RSS-bounded streaming deferred to a release that adds a
  native `Bytes` type. **Js.4 (Shape B) — typed serde
  intrinsics `to_json::<T>` and `from_json::<T>`** as compile-time
  monomorphized aliases of existing `encode_struct::<T>` /
  `decode_to::<T>`. **`to_json::<T>` works end-to-end** at this
  release (verified `Point{3,4}` → `{"x": 3, "y": 4}`).
  **`from_json::<T>` builds successfully but SEGVs at runtime**
  in field-extraction (a pre-existing v5.x drop-glue bug
  uncovered by the Js.0.B fix). API surface is in place so
  v5.40.0 `ask` work can build against it; runtime fix tracked
  as **Js.4.B for v5.36.1**. **Phase 0 user decision**: Shape B
  (extend existing intrinsics) over Shape A (build runtime
  reflection from scratch — would have been 3-5 release
  sessions). PROMPT/PLAN claimed runtime type metadata existed at
  `runtime/native/mapanare_typeinfo.c` "or inlined in
  mapanare_core.c"; verified empirically that `print(struct)`
  literally just emits `printf("%lld\n", first_field)` with no
  field iteration — runtime metadata does not exist. **Js.5** —
  `tests/stdlib/test_json_corpus_baseline.py` regression gate
  asserting CONFORM ≥ 283 / DEVIATE ≤ 0 / CRASH ≤ 0. Marked
  `pytest.mark.slow`. **Js.7** — `docs/stdlib/json.md` user-
  facing reference. Documents strictness changes, every public
  API, the Js.3-LITE memory characteristic, and Js.4.B
  explicitly so callers know what they can rely on.
  **Js.6 sqlite integration deferred to v5.36.1** — was scoped
  to add `Value::Json(JsonValue)` variant requiring
  `from_json::<JsonValue>` runtime path, blocked by Js.4.B.
  **Two compiler bug-fixes uncovered during the work and shipped
  in-release.** **Js.0** (`mapanare/emit_llvm_text.py:1421`):
  `_san` sanitizer used `nm.lstrip("%")` (only leading) but
  callers interpolated names into compound IDs like
  `f"_map_iter_{value.name}"`; embedded `%` survived
  sanitization → invalid IR (`%_map_iter_%entries37.addr`).
  1-line fix: strip ALL `%`, not just leading. Goldens 95/95
  preserved. **Required for any end-to-end test of the existing
  json.mn module to work** (the bug surfaced as soon as Phase 0
  tried to build the corpus runner). **Js.0.B**
  (`mapanare/emit_llvm_text.py:5214` / `:5223`):
  `_do_wrap_ok` / `_do_wrap_err` hardcoded the unfilled side of
  the Result struct as `ptr`, producing `{i1, {ok_ty, ptr}}` when
  the consumer expected `{i1, {ok_ty, err_ty}}`. Mismatch invisible
  until Phi merge of two arms with full type info hit a size
  conflict. Fix uses dest's `Result.args` when available (kind
  == RESULT and len(args) ≥ 2); falls back to legacy shape
  otherwise. Required for Js.4 `from_json::<T>` to even build.
  **Bb.\*: NOT required** (no C-runtime export changes). **Hd-
  class preventative**: SPEC.md header re-synced from "v5.35.0
  cut" to "v5.36.0 cut" with new sync block summarizing what
  v5.36.0 ships (specifically calling out Js.1 as `### Changed`
  / potentially breaking-ish; Js.4.B as the load-bearing
  deferred fix for v5.40.0 `ask`). `check_doc_freshness.py`
  GREEN. **Vendored RFC 8259 corpus is gitignored** at
  `stdlib/json/tests/fixtures/rfc8259/`; `scripts/run_json_corpus.py`
  clones nst/JSONTestSuite on demand if missing. Aggregate state
  entering v5.37.0: **0 HIGH** / **1 MEDIUM** (Js.4.B
  `decode_to`/`from_json` runtime SEGV; macOS notarization carry
  from v5.33.0 Nu.2) / ~6 LOW (native `Bytes` type, Js.6 sqlite
  paired with Js.4.B, field-type coverage extension paired with
  Js.4.B, `JsonParseOpts` opt-out, multi-line struct literal
  syntax, v5.x match-cleanup SEGV, cyclic-struct detection).
  See `docs/roadmap/v5/v5.36.0/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md, RFC_AUDIT.md}`.

- **v5.35.0** (ready, not tagged) — **Sq.\* — first-class SQLite3
  stdlib driver + Tn.1 closure.** Closes the persistence gap.
  Net-new `stdlib/sql/sqlite.mn` (~720 LOC) wraps the existing
  v5.34.x `mapanare_db.c` sqlite exports plus 8 new ones added at
  Sq.7 (`__mn_sqlite3_libversion`, `_bind_blob`, `_column_blob`,
  `_reset`, `_bind_parameter_index`, `_changes`,
  `_last_insert_rowid`, `_extended_errcode`). **Zero compiler
  edits. Zero `mapanare/self/*.mn` source touches.** Strict 3-stage
  fixed point preserved by construction at v5.34.0's **241,898
  lines / 0 diff** (30-release strict streak from the v5.7.1
  baseline). Goldens **95/95**. Surface: `Database`, `Statement`,
  `Value` (7 variants: Null/Int/Float/Text/Blob/Bool/DateTime),
  `SqlError` (8 variants with retry/recovery semantics —
  `LoadFail`, `VersionTooOld(String)`, `BadSql(String)`,
  `TypeMismatch(String)`, `Constraint(String)`, `Busy`, `Misuse`,
  `Closed`), `SavepointHandle` for nested transactions. Typed
  `column<T>` with mismatch detection; named parameter binding via
  `:name` / `@name` / `$name`; explicit transaction primitives
  (`database_begin / commit / rollback`) plus `SavepointHandle`-
  based nesting; blob support carrying raw bytes through `String`;
  `database_open` does a `>= 3.7.0` libsqlite3 version check via
  the new `sqlite3_libversion` export.
  **Sq.0 (formerly Tn.1) — closure of v5.28.0 RE-PANEL directive
  carried 6 releases.** New `tests/llvm/test_llvm_link_all.py`
  generalizes the v5.26.0 link-and-run pattern from 10 goldens
  (the async cluster + 4 v5.26.1 Eu.\* deferred goldens) to all
  95. 96/96 PASS at HEAD in 8s on 32 workers. Closes the structural
  test gap that hid Eu.1..Eu.4 LINK_FAIL bugs for 3 releases (v5.23.1
  → v5.26.0 Phase 0 audit).
  **Bundled-vs-staged-as-Sq.0 decision.** v5.35.0 PROMPT scoped
  Tn.1 as a hard-gate precondition that should ship as a v5.34.1
  hotfix. After surfacing this at Phase 0, the user directed
  bundle-into-v5.35.0 — preserves deadline integrity (Tn.1 was
  named DEADLINE-at-v5.35.0 in v5.33.0 directive) without spending
  a release slot. Tradeoff: substantive Sq.\* arc + tiny mechanical
  test ship together; honesty cost paid in this release-notes
  entry + SESSION_REPORT explicitly calling out Sq.0's prior
  Tn.1 identity.
  **Sq.6 tests.** 5 `.mn` test files under
  `stdlib/sql/sqlite/tests/` + new pytest harness
  `tests/stdlib/test_sq_sqlite.py` (mirrors the v5.34.0 Dt.\*
  concatenation pattern: read `stdlib/sql/sqlite.mn`, prepend to
  each `.mn` test main body, compile via Python LLVM emitter, link
  against `libmapanare_rt.a`, run, assert `"PASSED"` in stdout).
  7/7 GREEN at HEAD (5 .mn tests + parses-clean + typechecks-clean)
  in 3.98s. Tests cover: Sq.1 lifecycle (open / close idempotent
  / libversion non-empty); Sq.1+2 full CRUD with named-param
  binding; Sq.4 commit + rollback + nested SAVEPOINT (mid-tx
  count → post-commit count → savepoint rollback discards inner
  inserts but outer commit retains); Sq.2+5 manual prepared-stmt
  reuse via `reset+bind+step` over 200 iterations in a single
  transaction; Sq.1+2+3 SqlError variant coverage including
  Constraint extended-rc mapping (UNIQUE = 2067, PRIMARYKEY =
  1555 propagated through the message string).
  **Sq.7 C shim — extends, doesn't duplicate.** Phase 1
  discovery: `runtime/native/mapanare_db.c` already had complete
  sqlite3 dlopen plumbing (877 LOC, 18 function pointers, full
  `SQLITE_SYM(...)` resolution) — the PROMPT's "create net-new
  `mapanare_sqlite.c` (~150 LOC)" was based on incomplete reading
  of the existing runtime. User directed wrap-don't-duplicate;
  Sq.7 added 8 new function pointers + 8 new wrapper functions
  to the existing `s_sqlite` struct + `sqlite3_load()` resolver.
  ~80 LOC of new C, no new source files. Build path unchanged
  (`mapanare_db.c` already in `Makefile` `RUNTIME_SOURCES`). C
  smoke harness at `/tmp/sq7_smoke.c` (6 cases including blob
  round-trip with embedded NUL, named-param resolution,
  duplicate-INSERT extended errcode) PASS against system
  libsqlite3 3.45.1.
  **Sq.8 Windows DLL bundle.** `.github/workflows/publish.yml`
  Windows `build-cli` path now downloads pinned
  `https://www.sqlite.org/2024/sqlite-dll-win-x64-3460100.zip`
  (SQLite 3.46.1), extracts and stages
  `dist/mapanare/bin/sqlite3.dll`. Three guards: MZ-header check
  (catches HTML-error-as-DLL); 500 KB ≤ size ≤ 5 MB (catches
  partial download / wrong file); explicit version-string
  variable in the shell that future bumps must update with the
  URL. Linux + macOS use system libsqlite3 (Ubuntu 20.04+ ships
  3.31+; macOS 13+ ships 3.39+).
  **Sq.9 docs.** `docs/stdlib/sql.md` (~370 lines) — quick
  reference, types, 7 cookbook recipes (open + create + insert +
  read on `:memory:`; on-disk database; transaction-wrapped
  batch insert with the perf-explanation; manual prepared-stmt
  reuse with the Sq.5-deferred note; `match SqlError` for
  retry/recovery; blob handling; Sq.3.B JSON preview with
  forward link to v5.36.0 Js.\*); deviations explicitly listed;
  migration / coexistence note from existing `stdlib/db/sqlite.mn`;
  Sq.8 Windows DLL distribution policy.
  **Five PLAN deviations (all load-bearing, all structurally
  driven).** (1) Single-file module instead of directory layout
  — same lesson as v5.34.0 `stdlib/time.mn`, blocked on cross-
  module mangling/extern-propagation fix. (2) `Value::Blob(String)`
  not `Value::Blob(Bytes)` — Mapanare has no native `Bytes` type;
  v5.36.0 Js.\* arc may introduce one. (3) Explicit transaction
  primitives + `SavepointHandle` instead of `transaction<T>(\|\|
  ...)` closure wrapper — Mapanare stdlib has no precedent for
  generic-closure-arg functions. (4) Sq.5 statement cache deferred
  to v5.36.0 — without first-class state mutation across function
  calls + `Map<K,V>` ergonomics, the auto-cache API is uglier
  than the manual `prepare-once + reset+bind+step` path that
  produces the same 5-10× speedup. (5) Sq.7 wraps existing
  `mapanare_db.c` instead of new `mapanare_sqlite.c` — Phase 1
  scope discovery, surfaced to user, accepted.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced from
  "synced to the v5.34.0 cut" to "synced to the v5.35.0 cut" with
  a new sync block summarizing what v5.35.0 ships (specifically
  enumerating the 8 new C runtime functions in `mapanare_db.c`).
  `check_doc_freshness.py` GREEN.
  Aggregate state entering v5.36.0: **0 HIGH** (Tn.1 closed) /
  **1 MEDIUM** (macOS notarization carry from v5.33.0 Nu.2) /
  ~9 LOW (Sq.5 cache deferred, native `Bytes` type, closure-arg
  transaction wrapper, PostgreSQL/MySQL typed wrappers, schema
  migrations + ORM, async sqlite, cross-module emitter fix,
  carry from v5.34.0). The existing v5.34.x `stdlib/db/sqlite.mn`
  is **untouched**; both drivers coexist (the older one routes
  through `Connection` / unified SQL URLs; the new
  `stdlib/sql/sqlite.mn` is the typed-`column<T>` + named-param
  surface).
  See `docs/roadmap/v5/v5.35.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.34.0** (ready, not tagged) — **Dt.\* — first-class date /
  time stdlib.** First stdlib expansion since v5.21.0. **Zero
  compiler edits. Zero `mapanare/self/*.mn` source touches.**
  Strict 3-stage fixed point preserved by construction at
  v5.33.x's **241,898 lines / 0 diff** (29-release strict streak
  from the v5.7.1 baseline). Goldens **95/95**. Net-new
  `stdlib/time.mn` (~723 LOC) shipping `Date`, `Time`, `DateTime`,
  `Duration`, `Timezone` types with construction-time validation
  (rejects `2026-13-03`, `1900-02-29`, year out of `[1, 9999]`);
  ISO 8601 + RFC 3339 parse/format with strftime specifier subset
  (`%Y %m %d %H %M %S %z %Z %%`); arithmetic with month/day
  rollover and leap-year handling; v0 timezone surface (UTC +
  system-local; `tz_named("America/Lima")` returns explicit
  `Err("named tzdb not yet supported: ...")` — non-negotiable
  defer per PLAN, silent fallback to UTC is the bug-class that
  bites real users). All v5.33.x flat-file surface (`Stopwatch`,
  `now_ns`, `format_duration_ms`, etc.) preserved unchanged at
  the top of the file. Built on a new ~340 LOC portable C shim
  at `runtime/native/mapanare_time.c` (POSIX default + `#ifdef
  _WIN32` for `GetSystemTimePreciseAsFileTime` / `localtime_s` /
  `gmtime_s` / `_mkgmtime`). Six new runtime exports:
  `__mn_now_realtime_ns`, `__mn_utc_pack`, `__mn_local_pack`,
  `__mn_local_offset_minutes`, `__mn_timegm`,
  `__mn_normalize_pack`. Wired into `runtime/native/Makefile`
  `RUNTIME_SOURCES` (`libmapanare_rt.a` now contains 9 modules +
  Metal on Darwin).
  **Phase 0 spike result.** PROMPT scoped Dt.5 with operator
  overloads (`dt + dur`). Spike (`/tmp/op_spike.mn`) confirmed
  `impl Add for Dur` does NOT lower through `mnc-stage1` —
  semantic checker reports `Undefined trait 'Add'` and `Operator
  '+' not supported for types Dur and Dur`. Operator-overload
  infrastructure (`trait Add`, etc.) does not exist in the
  current toolchain. Per PROMPT mitigation, Dt.5 fell back to
  free-function method form: `datetime_add_duration(dt, dur)`,
  `duration_add(a, b)`, `duration_mul(d, n)`, etc. Same surface
  semantics, less ergonomic, no syntax change.
  **PLAN deviation (load-bearing) — single-file vs. directory
  module.** PROMPT specified `stdlib/time/{types,construct,parse,
  format,arith,tz}.mn`. Phase 2 dev surfaced two cross-module
  limitations: (1) native `mnc-stage1` does not propagate
  `extern_fn_def` declarations across module imports — every
  consumer would have to re-declare every extern; (2) the Python
  LLVM emitter mangles defined function names with the module
  prefix (`time__date_new`) but emits unprefixed forward
  declarations at call sites, producing link failures
  (reproduced via `python3 -m mapanare emit-llvm + clang link`;
  same root cause as the `examples/ai/basic_chat.mn` v4.129.0
  known-issue note). Both blocked the multi-file design. Every
  existing stdlib module (`math`, `crypto`, `fs`, `ai/llm`,
  `db/*`) is single-file with self-contained tests for the same
  reason — v5.34.0 follows that proven pattern. Cross-module
  fixes tracked separately and explicitly **outside v5.34.0
  scope** (the PROMPT itself warned "If you find yourself
  opening `mapanare/self/lower.mn` or `emit_llvm.mn`, you have
  gone outside scope"). The directory-module shape remains the
  right structural goal; it has to ride a separate
  cross-module-emitter fix.
  **Dt.7 tests.** 7 `.mn` test files under `stdlib/time/tests/`
  + new pytest harness `tests/stdlib/test_time_dt.py` (mirrors
  the v3.x `test_crypto.py` concatenation pattern: read
  `stdlib/time.mn`, prepend to each `.mn` test main body,
  compile via Python LLVM emitter, link against
  `libmapanare_rt.a`, run, assert `"PASSED"` in stdout). 9/9
  GREEN at HEAD. Tests cover: Dt.1 leap-year boundaries
  (1900/2000/2024/2100/2400 — the bug-class behind every "Feb
  29 1900" mishap); Dt.2 epoch round-trip across 0 (1970) →
  2000000000 (2033); Dt.3 22 parse cases including
  `2026-05-03T14:32:00.123Z` (fractional secs) and
  `+05:30`/`-05:00` offset variants; Dt.4 strftime specifier
  coverage; Dt.5 month/day rollover (Jan 31 + 1d → Feb 1; Dec
  31 23:59:59 + 1s → next year; Feb 29 leap + 365d → Feb 28
  non-leap); Dt.6 `tz_named` explicit-defer assertion; Dt.7
  three property-style tests (parse-then-format round-trip,
  epoch round-trip, arithmetic associativity) on a fixed
  deterministic table of boundary fixtures.
  **Dt.8 C shim.** ~340 LOC. Adapted PROMPT signatures from
  out-pointer form to scalar returns with packed-int64
  representation (`packed = y*10^10 + mo*10^8 + d*10^6 +
  h*10^4 + mi*10^2 + s`) — Mapanare `extern "C" fn` exposes only
  Int / String / List<X> returns, no out-pointer surface. C
  smoke (`/tmp/time_shim_smoke.c`, 20 cases): leap-year
  boundaries, normalization forward/backward, year overflow,
  out-of-range rejection. 20/20 PASS. Valgrind clean.
  **Dt.9 docs.** `docs/stdlib/time.md` — quick reference, type
  definitions with year-range/leap-year/tz-sign conventions
  documented, strftime specifier table, four required cookbook
  recipes (parse-then-format round-trip; "1 week from now"; "is
  this date in the past?"; "format as ISO 8601 in local
  timezone"), migration note from the v5.33.x flat
  `stdlib/time.mn` (every existing surface preserved).
  **Closeout: caught one bug at Phase 6.** ISO parser
  fractional-seconds skip had off-by-one between loop-exit
  sentinel (`p = n`) and post-loop fallback
  (`if p == n { tz_pos = p }`). Symptom:
  `2026-05-03T14:32:00.123Z` failed parse with empty
  diagnostic. Fix: track `found_pos` separately from loop-exit
  sentinel; only fall back to `tz_pos = n` when `found_pos < 0`.
  Pinned in `test_parse_iso.mn` case 17 — round-trip parse →
  format → parse.
  **Hd-class preventative.** SPEC.md header re-synced from
  v5.33.1's "synced to the v5.33.1 cut" to "synced to the
  v5.34.0 cut" with a new 14-line block summarizing what
  v5.34.0 adds (specifically enumerating the 6 new runtime
  functions — the first SPEC-scoped runtime additions since
  v5.21.0). `check_doc_freshness.py` GREEN.
  Aggregate state entering v5.35.0: **1 HIGH** (Tn.1 — DEADLINE
  per v5.33.0 escalation, 6-release overdue carry-forward) /
  **2 MEDIUM** (macOS notarization; carry) / ~7 LOW (added
  named-tzdb, cross-module mangling, operator-overload
  infrastructure, full strftime expansion, sub-second precision
  in broken-down forms). See
  `docs/roadmap/v5/v5.34.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.33.2** (ready, not tagged) — **Cd.\* — relax panel-cadence
  enforcement to informational-only.** Tooling-policy hotfix.
  **Zero compiler edits. Zero runtime edits. Zero
  `mapanare/self/*.mn` source edits.** Strict 3-stage fixed point
  preserved by construction at v5.33.1's 241,898 lines / 0 diff
  (30-release strict streak from the v5.7.1 baseline). Goldens
  **95/95**. Closes the v5.33.1-push CI failures: the
  "Cadence enforcement (warn-only)" job in `.github/workflows/ci.yml`
  reported a red ❌ even though `continue-on-error: true` made it
  non-blocking, and `tests/test_cadence.py::test_cadence_within_window_at_head`
  asserted exit 0 at HEAD which was impossible at 5 minors past
  v5.28.0 panel. **Cd.1**: `scripts/check_cadence.py` rewritten —
  `main()` always returns 0; `OVERDUE` renamed to `REMINDER` +
  clarifying "Informational only — lead drives review timing.";
  docstring updated with the v5.24.0 Hy.3 → v5.33.2 Cd.1 history
  + the artifact-correctness-vs-human-scheduling distinction.
  **Cd.2**: `tests/test_cadence.py` updated — fixture cases that
  previously asserted exit 1 on overdue now assert exit 0 +
  REMINDER message printed. Doc-drift / changelog-honesty /
  fixed-point line-count gates remain hard — those enforce
  *artifact correctness*; this one tracked a *human scheduling
  decision*, which is the lead's call. User-memory entry
  `feedback_no_forced_cadence_gates` recorded so the rule survives
  across sessions: visibility/REMINDER OK, CI-blocking enforcement
  not OK; same rule applies if a future arc proposes the same
  shape under a different name. Source delta: ~50 LOC in
  `scripts/check_cadence.py` (full rewrite), ~30 LOC in
  `tests/test_cadence.py` (fixture-case updates), CHANGELOG
  one-paragraph entry, this CLAUDE.md entry, plus the mechanical
  Vb.\* files. Stage1 + `libmapanare_rt.a` rebuilt post-bump per
  the v5.31.0 + v5.33.1 lessons. Aggregate state entering v5.34.0:
  **1 HIGH** (Tn.1 — 6-release overdue carry; panel cadence
  demoted from HIGH to LOW since the gate is no longer enforcing)
  / **2 MEDIUM** (macOS notarization; carry) / ~6 LOW. See
  `docs/roadmap/v5/v5.33.2/{PLAN.md, SESSION_REPORT.md}`.

- **v5.33.1** (ready, not tagged) — **Hd.\* — SPEC header drift
  hotfix.** Docs-surface-only hotfix. **Zero compiler edits.
  Zero runtime edits. Zero `mapanare/self/*.mn` source edits.**
  Strict 3-stage fixed point preserved by construction at
  v5.33.0's 241,898 lines / 0 diff (29-release strict streak
  from the v5.7.1 baseline). Goldens **95/95**. Closes
  `check_doc_freshness.py` SPEC-header lag violation (3 minors
  stale, max tolerated 2). `docs/SPEC.md` header re-synced from
  `synced to the v5.30.0 cut` to `synced to the v5.33.1 cut`;
  new sync block at the top summarizes v5.31.0 (Bn.\* banner
  hotfix), v5.32.0 (Nw.\* Windows native `mnc.exe` in SDK ZIP),
  v5.33.0 (Nu.\* Linux x86_64 + macOS arm64 native `mnc` in
  release tarballs; Linux aarch64 + macOS x86_64 deferred to
  v5.34.0+), and v5.33.1 (this re-sync) — declarative,
  cross-checked against each release's SESSION_REPORT.
  v5.31–v5.33.1 together added **zero language features, zero
  new MIR ops, zero new IR shapes, zero new runtime functions**
  — packaging / hotfix releases only. The structural gate
  (`check_doc_freshness.py`'s `check_spec_header()`, landed at
  v5.24.0 Hy.2 with a 2-minor lag tolerance) fired exactly as
  designed: SPEC stayed unsynced for 3 minor releases, gate
  flipped hard at v5.33.0 HEAD, hotfix re-syncs and the gate
  closes the next recurrence in CI rather than at the panel.
  Source delta: ~14 LOC in `docs/SPEC.md` (Hd.1 header bump +
  Hd.2 sync block), ~12 LOC in `CHANGELOG.md` (one-paragraph
  hotfix entry, no fake `### Added`/`### Changed`/`### Fixed`
  subsection content), this CLAUDE.md entry, plus the
  mechanical files `bump_version.py` touched (VERSION + 4
  README badges en/es/pt/zh-CN). Stage1 rebuilt post-bump so
  IR-metadata embeds `!"5.33.1"` in stage2 + stage3 (the
  v5.31.0 SESSION_REPORT documented lesson — without the
  rebuild, `verify_fixed_point.sh` would show a 4-line
  VERSION-placeholder NEAR diff). **Panel cadence note:**
  `check_cadence.py` warn-only OVERDUE — 5 minor versions since
  v5.28.0 panel; full 7-reviewer panel deliberately not picked
  up here (multi-day cycle, exceeds hotfix scope). Escalated to
  v5.34.0 as HIGH carry-forward. Aggregate state entering
  v5.34.0: **2 HIGH** (panel cadence escalated; Tn.1 5-release
  overdue carrying forward) / **2 MEDIUM** (macOS notarization;
  carry) / ~6 LOW. See
  `docs/roadmap/v5/v5.33.1/{PLAN.md, SESSION_REPORT.md}`.

- **v5.33.0** (ready, not tagged) — **Nu.1 + Nu.2 + Nu.3 + Nu.4
  + Nu.5 + Nu.6 — ship native `mnc` in the Linux x86_64 and
  macOS arm64 release tarballs.** Mirror of v5.32.0 Nw.\*
  applied to the two existing Unix tarballs. Closes the
  asymmetry where Windows had the fix and Unix didn't —
  release-tarball users on Linux x86_64 and macOS arm64
  no longer hit the Python bootstrap on `mnc --version`,
  `mnc run`, or `mnc build`. **Zero compiler edits. Zero
  runtime edits. Zero `mapanare/self/*.mn` source edits.**
  Strict 3-stage fixed point preserved by construction at
  v5.32.0's **241,898 lines / 0 diff** (28-release strict
  streak from the v5.7.1 baseline). Goldens **95/95**.
  **Nu.1 + Nu.2 deviation from PROMPT.** PROMPT scoped
  four arches: Linux x86_64 + Linux aarch64 + macOS x86_64
  + macOS arm64. v5.33.0 ships only the two arches that
  already build natively in `build-native` (Linux x86_64
  on `ubuntu-latest`, macOS arm64 on `macos-latest`).
  Linux aarch64 and macOS x86_64 are **deferred to v5.34.0**.
  Reasons: (a) `scripts/build_stage1.py` has no `--target`
  / `--output` flags — it always builds for the host;
  cross-compile would need new infrastructure that exceeds
  v5.32.0's "lift the proven path" precedent; (b) Linux
  aarch64 needs a cross-compile + qemu smoke pipeline that
  doesn't exist; (c) macOS x86_64 needs a separate
  `macos-13` runner and a brand-new tarball name in the
  release matrix. Mirrors v5.32.0's own "deviation from
  PROMPT" (build-native reuse vs. PROMPT's cross-compile
  recipe — same logic: prefer the validated path; preserve
  the more ambitious recipe for the next minor when it's
  motivated). **Nu.1 + Nu.2 plumbing**: `build-native`
  Linux + macOS jobs upload `mnc-linux-x64` /
  `mnc-darwin-arm64` as workflow artifacts (mirrors the
  `mnc-windows-x64-native` Nw.2 upload, single-day
  retention, `if-no-files-found: error`). `build-cli`
  Linux + macOS paths download the matching artifact, run
  three guards before staging — ELF / Mach-O magic
  (`7f454c46` for ELF; `cffaedfe` for Mach-O 64-bit
  little-endian) + 20 MB size ceiling (native is ~3-4 MB;
  PyInstaller-copy regression would be ~30 MB) +
  non-zero-bytes check — then copy to
  `dist/mapanare/mnc` (sibling of the existing
  `dist/mapanare/mapanare` PyInstaller binary; bundle-root
  layout matching the v5.32.0 Nw.2 decision rather than
  the PROMPT's `bin/mnc` shape). macOS path also runs
  ad-hoc `codesign -s -` so Gatekeeper doesn't quarantine
  the binary on first run after tar extraction; proper
  Developer ID notarization is a v5.34.0+ LOW.
  **Nu.4** smoke gates: two layers, both load-bearing.
  **Layer 1 in-job** (`build-cli` "Clean Linux/macOS native
  mnc smoke before archiving"): on the staging directory,
  asserts `dist/mapanare/mnc --version` (a) contains the
  expected version string from `VERSION`, (b) does not
  spawn a new Python interpreter (snapshots `pgrep -fl
  python` count before / after — same anti-pattern Windows
  Nw.4 closes). **Layer 2 published** (extends existing
  `linux-tarball-smoke` + `macos-tarball-smoke` jobs which
  already gate on `windows-sdk-smoke`'s shape): downloads
  the published tarball from the GitHub Release, runs the
  same magic / size / version-string / no-Python-spawn
  checks. Per-platform stat flag (`stat -c%s` Linux vs.
  `stat -f%z` macOS). The no-Python assertion is the
  load-bearing one — that's the specific anti-pattern
  v5.33.0 closes for the Unix release tarballs.
  **Nu.5** fallback-wrapper audit: `mapanare/__main__.py`
  refactored to extract `_native_binary_name(os_name=...)`
  (4 LOC). Pre-v5.33.0 the suffix-selection logic
  (`"mnc.exe" if os.name == "nt" else "mnc"`) was inlined
  in `_native_binary` and only host-OS-testable —
  monkeypatching `os.name` globally to test the *other*
  branch crashes pathlib (`NotImplementedError: cannot
  instantiate 'WindowsPath' on your system`). The new
  helper takes `os_name` as a parameter so tests can pin
  the value without touching pathlib. New
  `tests/test_native_fallback.py::test_native_binary_suffix_per_platform`
  parametrizes over (`posix` → `mnc`, `nt` → `mnc.exe`)
  so a Linux CI worker validates the Windows lookup and
  vice versa. 5/5 GREEN. Falsifiability: hardcoding the
  wrong suffix flips one of the two parametrized cases.
  **Nu.6** docs: README.md install section gains a
  paragraph noting v5.33.0+ ships native `mnc` on Linux
  x86_64 + macOS arm64; macOS-quarantine workaround
  (`xattr -d com.apple.quarantine`) documented inline.
  CLAUDE.md "Native-First Philosophy" updated; this
  release-notes entry added. **Localized READMEs
  (es/pt/zh-CN) deliberately not updated** — v5.32.0
  followed the same pattern (English README only); the
  v5.28.0 panel H.4 finding tracks localized README
  updates as a bookkeeping cycle, not per-release work.
  Source delta: ~120 LOC YAML in `.github/workflows/publish.yml`
  (Nu.1+Nu.2 + Nu.3 staging + Nu.4 in-job smoke + extended
  `linux-tarball-smoke` / `macos-tarball-smoke`); ~10 LOC
  Python in `mapanare/__main__.py` (Nu.5 refactor); ~25 LOC
  test in `tests/test_native_fallback.py` (Nu.5 parametrized
  case); ~15 LOC docs (README + CLAUDE). Aggregate state
  entering v5.34.0: 0 HIGH / 2 MEDIUM (Tn.1 — 5-release
  overdue, escalates to HIGH per v5.32.0 directive; macOS
  notarization, new from Nu.2 ad-hoc-signing shortcut) /
  ~6 LOW (deferred Linux aarch64 + macOS x86_64 tarballs
  added). Cadence unchanged: next routine panel still due
  v5.33.0 cadence-gap-acknowledged at v5.34.0 if not
  bundled. See
  `docs/roadmap/v5/v5.33.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.32.0** (ready, not tagged) — **Nw.2 + Nw.3 + Nw.4 + Nw.5
  + Nw.6 — ship native `mnc.exe` in the Windows SDK ZIP.**
  Closes the structural "Python is the front door on Windows
  release installs" problem that v5.31.0 only papered over.
  v5.12.0 shipped the *toolchain* bundle (`sdk\bin\clang.exe` —
  LLVM-MinGW). v5.32.0 ships the *frontend* bundle: `mnc.exe`
  in `mapanare-${V}-win-x64-sdk.zip` and `-minimal.zip` is now
  the native compiler binary, not a PyInstaller copy of
  `mapanare.exe`. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage
  fixed point preserved by construction at v5.31.0's **241,898
  lines / 0 diff** (27-release strict streak from the v5.7.1
  baseline). Goldens **95/95**. After this release a fresh
  Windows SDK install never invokes Python for `mnc --version`,
  `mnc run`, or `mnc build`. **Nw.1 deviation from PROMPT:**
  PROMPT recommended approach (a) cross-compile from Linux CI
  via `clang --target=x86_64-w64-mingw32`. v5.32.0 uses
  approach (b) — reuses the existing `build-native` Windows
  job's `mnc-win-x64.exe` artifact (full stage1 → stage2
  self-compile cycle on a `windows-latest` runner via w64devkit
  MinGW). Reasons: PROMPT explicitly allows fallback to (b)
  "if cross-compile produces ABI mismatches" — doing (b)
  directly avoids a discovery cycle; existing path is validated
  across 30+ releases and runs the full self-compile cycle
  (stronger Win64-ABI validation than cross-compile);
  smaller diff — no third Windows-build code path. Trade-off:
  ~5-10 min of serial CI on the Windows publish path
  (`build-cli` now `needs: [release, build-native]`).
  Cross-compile remains available for v5.33.0+ when Linux /
  macOS native-frontend bundling motivates a unified job.
  **Nw.2** publish.yml wiring: `build-native` Windows path
  uploads `mnc-win-x64.exe` as the `mnc-windows-x64-native`
  workflow artifact (in addition to the existing GitHub
  Release upload). `build-cli` Windows path downloads it and
  stages as `dist/mapanare/mnc.exe` with two guards:
  MZ-header check (PE32+ DOS-stub `0x4D 0x5A`) and 20 MB size
  ceiling (native is ~3-4 MB; PyInstaller copy is ~30 MB —
  20 MB reliably distinguishes). Replaces the pre-v5.32.0
  `Copy-Item dist/mapanare/mapanare.exe dist/mapanare/mnc.exe`
  alias-shape. **Nw.3** native-binary fallback wrapper:
  `mapanare/__main__.py` rewritten with a 25-LOC preamble
  that detects a sibling `bin/mnc[.exe]` and `os.execv`s to
  it. `MAPANARE_FORCE_PYTHON=1` opts out for dev/debug. Also
  fixes a pre-v5.32.0 bug where `cli.main()` ran at module-
  import time (no `if __name__ == "__main__":` guard) — pytest
  collection of the new fallback tests would have hit
  argparse `SystemExit` otherwise. New
  `tests/test_native_fallback.py` (3 cases) locks the
  detection logic and the env-var bypass. **Nw.4** smoke gate:
  augmented existing `Clean Windows SDK smoke before archiving`
  (in build-cli) and `windows-sdk-smoke` (post-publish, on
  the published ZIP) with three new gates — MZ-header +
  size-ceiling check on `mnc.exe`; version-string match
  against `VERSION`; no-new-Python-process assertion across
  the `--version` call (snapshots `Get-Process | Where-Object
  { $_.Name -match '^python' }` count before / after). The
  no-Python assertion is the load-bearing one — that's the
  specific anti-pattern v5.32.0 closes. **Nw.5** minimal ZIP
  also ships native `mnc.exe` automatically — minimal-ZIP
  staging archives `dist/mapanare/` *after* Nw.2 staging has
  swapped the binary, so no separate code path needed.
  **Nw.6** docs: CLAUDE.md Native-First Philosophy section
  gains a paragraph; README.md install section calls out the
  v5.32.0+ native shipping; CHANGELOG.md `## [5.32.0]` filled
  in with full Nw.\* details + the deviation note;
  `check_changelog_honesty.py` GREEN. **Layout decision:**
  PROMPT specified `bin\mnc.exe`; v5.32.0 keeps `mnc.exe`
  at the bundle root because the bundled SDK lives at
  `sdk/bin/clang.exe` (not `bin/sdk/bin/clang.exe`) — PROMPT's
  layout assumption didn't match v5.12.0's existing structure.
  Aggregate state entering v5.33.0: 0 HIGH / 1 MEDIUM (Tn.1,
  4-release overdue; v5.32.0 deferred to keep scope tight;
  escalates to HIGH at v5.33.0 per v5.31.0 cadence note) /
  ~5 LOW. Cadence unchanged: next routine panel still due
  v5.33.0. See
  `docs/roadmap/v5/v5.32.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.31.0** (ready, not tagged) — **Bn.1 + Bn.2 + Bn.3 +
  Bn.4 + Bn.5 — banner hotfix; kill the "[dev mode]" lie.**
  Pure UX hotfix. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage
  fixed point preserved by construction at v5.30.0's
  **241,898 lines / 0 diff** (26-release strict streak from
  the v5.7.1 baseline). Goldens **95/95**. Closes the
  publish-run-#50-shaped report where a fresh Windows SDK
  install ran `mnc --version` and got `[dev mode] Using
  Python bootstrap compiler. For native speed: mnc run
  <file.mn>` printed before the version string — three
  things wrong: "[dev mode]" was a lie on a release install,
  "for native speed: mnc run <file.mn>" was incoherent on a
  metadata command, and the banner fired unconditionally
  before argparse ran. The Python bootstrap was fine — it
  just announced itself wrong. **Bn.1**: new
  `_should_show_dev_banner(argv)` argv-peek in
  `mapanare/cli.py::main` skips the banner when the first
  non-flag token is in `NO_BANNER_COMMANDS = frozenset({
  "--version", "--help", "-h", "init", "list"})`; honest-
  default policy is "when in doubt, don't fire". **Bn.2**:
  new `_is_release_install()` helper (`@lru_cache(1)`):
  primary signal is `MAPANARE_RELEASE=1` env var; fallback
  is the absence of `pyproject.toml` + `.git` directory at
  the repo root (the parent of `mapanare/`). Release
  installs never see the banner. **Bn.3**: dev-clone
  banner reworded to honestly describe the situation:
  `[mapanare dev] running from source clone (.../mapanare/
  cli.py). Set MAPANARE_RELEASE=1 or install via the SDK to
  silence.` Path embedded so a developer with multiple
  checkouts can tell which one they're hitting. Misleading
  "for native speed: mnc run <file.mn>" suggestion removed.
  **Bn.4**: new `tests/test_cli_banner.py` (5 cases) locks
  all four matrix cells {dev clone, release install} ×
  {metadata cmd, compile cmd} plus the new wording.
  Falsifiability: removing either gate in `cli.py`
  reproduces the publish-run-#50 anti-pattern. **Bn.5**:
  `packaging/pyinstaller-entry.py::main()` calls
  `os.environ.setdefault("MAPANARE_RELEASE", "1")` before
  importing `mapanare.cli`. Single edit covers Linux
  tarball, macOS bundle, and Windows SDK ZIP — every
  release platform ships via the PyInstaller bundle so all
  inherit the env var. The Bash shim
  (`packaging/mapanare-shim.sh`) `exec`s the bundled
  binary directly so the env var set inside the entry
  point is the process's own env. `setdefault` (not
  unconditional set) means a user who explicitly unsets
  `MAPANARE_RELEASE` for testing can still trigger the
  path-heuristic fallback. **v5.31.0 ≠ v5.32.0** — the
  native `mnc.exe` shipping work (which makes the Python
  path *unused* on release installs, not just *quiet*)
  is v5.32.0. Source delta: ~115 LOC of behavior change
  across 3 files (`cli.py` +37/-5, new
  `test_cli_banner.py` +75, `pyinstaller-entry.py` +9/-1)
  — well under PLAN's 50–80 LOC target with the test file
  the bulk of the new code. **Lesson captured for future
  bump-only releases**: rebuild stage1 via
  `python3 scripts/build_stage1.py` between
  `bump_version.py` and `verify_fixed_point.sh` — first
  fixed-point run after the bump showed a spurious 4-line
  VERSION-placeholder NEAR diff (`!0 = !{!"5.30.0"}` vs
  `!0 = !{!"5.31.0"}`) because cached stage1 still
  embedded pre-bump VERSION; rebuild restored STRICT.
  Aggregate state entering v5.32.0: 0 HIGH / 1 MEDIUM
  (Tn.1 still 3-release overdue; bumped from "overdue"
  toward "escalate to HIGH at v5.33.0 if not landed";
  deliberately deferred to keep v5.31.0 scope tight) /
  ~5 LOW. Cadence unchanged: next routine panel still
  due v5.33.0. See
  `docs/roadmap/v5/v5.31.0/{PLAN.md, SESSION_REPORT.md}`.

- **v5.30.0** (ready, not tagged) — **Vb.\* — packaging-only
  release: version bump.** **Zero compiler edits. Zero runtime
  edits. Zero `mapanare/self/*.mn` source edits.** Strict
  3-stage fixed point preserved by construction at v5.29.0's
  **241,898 lines / 0 diff** (25-release strict streak from
  the v5.7.1 baseline). Goldens **95/95**. Advances the
  published version surface (VERSION, README badges in
  en/es/pt/zh-CN, CHANGELOG.md) so the next `dev` → `main`
  merge carries a clean v5.30.0 number; the substantive
  deliverable is the refreshed PR description covering
  v5.13.0 → v5.30.0 cumulative scope (currently `main` is
  stuck at v5.13.0). All real fix / feature work shipped at
  v5.29.0 (Mb.10 self-host emitter routing for
  `__mn_indent_to_braces` Win64 ABI; Pv.7 / Pv.8 already on
  `dev` pre-v5.29.0). NO seed refresh required (no C-runtime
  export changes — no `.mn` source touches the C side at
  all). `make ci-gates` GREEN (9 sub-gates); `make lint`
  clean. See `docs/roadmap/v5/v5.30.0/{PLAN.md,
  SESSION_REPORT.md, PR_BODY.md}`.

- **v5.29.0** (ready, not tagged) — **Mb.10 + Pv.7 + Pv.8 —
  Win64 ABI closeout + CI race prevention.** Three findings,
  three fixes, one release. Reopens the **Mb.\*** arc (declared
  closed at v5.26.1) for one residual Win64 ABI gap and closes
  it **structurally** this time. **Strict 3-stage fixed point
  preserved by construction at 241,898 lines / 0 diff** (24-
  release strict streak; restored from v5.28.0's NEAR — the
  prior NEAR was a v5.9.0 DX.2 artifact from a stale stage1
  binary linked against a v5.27.0-vintage runtime, not actual
  divergence). Goldens **95/95**. **Mb.10**: closes
  publish-run-#50 Windows SIGSEGV in `__mn_indent_to_braces`.
  Sister fix to v5.26.0 Mb.9 (which routed the brace-deprecation
  siblings `__mn_count_user_brace_block_openers` and
  `__mn_emit_brace_deprecation_warning` but missed the parent
  function with the same Win64 ABI shape). Pre-fix mechanism:
  `emit_mir_call`'s user-call fallthrough uses the 64-byte
  `is_byref_type_st` threshold for arg classification; `MnString`
  is 16 bytes, so on Win64 the call site emitted the struct by
  value while `declare_runtime_fn` already declared the function
  with `ptr` parameter via `win64_rewrite_decl_params` (8-byte
  threshold). gcc lowered `MnString source` per Win64 ABI as
  pass-by-hidden-pointer with rcx pointing into the struct's
  data buffer instead of into a valid `MnString` — SIGSEGV on
  the first `source.len` read. The Python emitter has had this
  routing since v5.23.1 Mb.1 (`emit_llvm_text.py:3632`); the
  self-host side was missed. The Mb.9 Python comment at
  `mapanare/self/emit_llvm.mn:3778` even names the missing
  routing as the pattern Mb.9 mirrored — but Mb.9's author only
  added the routing for the brace-deprecation pair, not for the
  parent function. Bug stayed latent because Linux/macOS publish
  jobs hide the mismatch via SysV register-passing, and Windows
  publish wasn't reaching the stage2-self-compile step for
  v5.23.1 → v5.27.0 (failing earlier on other things). v5.28.0
  RE-PANEL did not surface Mb.10 (test gap; covered by Tn.1
  panel rec). 3-LOC fix in `mapanare/self/emit_llvm.mn` (12-line
  block including explanatory comment) inserted after the Mb.9
  brace-deprecation routing at line 3786, mirroring the same
  shape — only the return type differs (`llvm_string()` i.e.
  `{ptr, i64}` MnString here, vs `"i64"` for the counter).
  `emit_rt_call` uses `win64_sarg_rewrite_args` (8-byte
  threshold matching `win64_rewrite_decl_params`), producing
  the correct `sret+sarg` shape on Win64 and a no-op on Linux
  SysV. **Mb.10.C** new
  `tests/llvm/test_indent_to_braces_win64_abi.py` (6 cases
  mirrors v5.26.0 Mb.9.C's `test_brace_funcs_windows_abi.py`):
  3 IR-shape gates under Win64 triple via the Python emitter
  (load-bearing); 1 SysV negative gate pinning the by-value
  shape so future emitter refactors don't accidentally rewrite
  it; 3 ctypes contract cases against
  `runtime/native/mapanare_core.c` for runtime-side correctness.
  Falsifiability round-trip verified — reverting the v5.23.1
  Python handler triggers the IR-shape gate failure exactly
  matching the publish-run-#50 anti-pattern (`call ... ({ptr,
  i64} %l.0)`). **Bb.\* seed refresh: NOT required** (no
  C-runtime export changes; the v5.10.0-vintage seed has no
  view of how `mnc-stage1` emits the call). **Pv.7**: closes
  `clean-build-test` race against parallel `pytest -n auto`
  workers. Pre-fix, the `rm -f libmapanare_rt.a && make
  build-rt` sequence in `clean-build-test` left a 1-3 second
  window where the canonical archive was missing; surfaced as
  flake on `tests/bootstrap/test_chained_cmp_mirror.py`
  (gw0 hit the race window). **Already shipped on dev as
  commit `bc3bc7b`** between v5.28.0 and v5.29.0. Fix
  parameterizes `build-rt` with `RT_OUTPUT ?=
  runtime/native/libmapanare_rt.a`, rebuilds into a sandbox
  path on the same filesystem (`runtime/native/.libmapanare_rt
  .cbt-tmp.a`), then atomic `mv -f` into the canonical path.
  Race-window evidence captured in v5.29.0 SESSION_REPORT:
  200-poll watcher at 20 ms cadence over the full 4-second
  rebuild produced **0 MISSING reports**. **Pv.8**: closes
  agent-state timing races in `tests/native/test_c_runtime.c`'s
  `test_agent_pause_resume` (`:712`) and
  `test_agent_failing_handler` (`:738`). `mapanare_agent_pause()`
  is a guarded transition that silently no-ops if the agent
  isn't yet RUNNING; the worker thread sets state=RUNNING only
  after the OS schedules the new thread, and the test's fixed
  `usleep(50000)` was sometimes insufficient under CI load.
  **Already shipped on dev as commit `f119c43`** between
  v5.28.0 and v5.29.0 (the PROMPT/PLAN were drafted assuming
  the fix was uncommitted; verified at Phase 0 that it had
  landed cleanly). Fix adds 4 polling helpers
  (`wait_for_agent_state`, `wait_for_messages_processed`,
  `wait_for_agent_recv`, `wait_for_counter` + `test_sleep_ms`)
  plus 7 fixed-delay sleeps converted to bounded polls
  (`test_agent_lifecycle`, `test_agent_send_recv`,
  `test_agent_pause_resume`, `test_agent_failing_handler`,
  `test_agent_metrics`, `test_shutdown_with_agents`,
  `test_pool_basic` + `test_pool_saturation`). Generous
  timeouts (1000 ms for state, 2000 ms for FAILED /
  messages-processed, 5000 ms for 500-task pool stress) —
  returns on first match; only consumes the full budget if the
  worker is genuinely stuck. Plain + ASan + TSan all green
  (3/3); `gcc -O2 -g -pthread -Wall -Wextra -Werror` clean.
  Pv.8.B (preemptive sweep of 11 same-shape sites in
  `tests/native/test_agent_scheduler.py`) **deferred** to
  v5.30.0+ if a flake materializes; reactive-only fix
  discipline preserved. **Mb.\* arc CLOSED structurally** —
  v5.26.0's "Mb.\* arc CLOSED" claim was strictly correct for
  Mb.7+Mb.9 but missed `__mn_indent_to_braces`; v5.29.0 closes
  the arc for real. Aggregate state entering v5.30.0: 0 HIGH /
  1 MEDIUM (Tn.1 escalated per v5.28.0 panel directive — not
  picked up here, deliberately deferred to keep Mb.10 scope
  tight) / ~5 LOW. Cadence unchanged: next routine panel still
  due v5.33.0. See `docs/roadmap/v5/v5.29.0/{SESSION_REPORT.md,
  PLAN.md, AUDIT.md}`.

- **v5.28.0** (ready, not tagged) — **RE-PANEL — v5.23.0 →
  v5.27.0 recovery + prevention + arc-closeout arc graded.**
  Panel-only release. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage fixed
  point preserved by construction at v5.27.0's 241,842 lines / 0
  diff. 7 reviewers graded the v5.23.0 → v5.27.0 arc (8 releases,
  9 SESSION_REPORTs) using the v5-gate mechanical decision rule.
  **Aggregate: 9.72 / 10. Decision: Option A.** Fourth
  consecutive Option A under the v5-gate framework, **largest
  single-arc recovery in v5 history (+0.31 vs v5.22.0's 9.41
  floor)**, and **first panel above the v5.7.1 / v5.8.0 9.66
  ceiling in the v5 series**. Score trajectory: 9.66 → 9.62 →
  9.41 → **9.72** — 3-consecutive-panel downward trend (-0.04,
  -0.21) broken with +0.31. **Per-reviewer:** Rattler 9.90
  (+0.05), Viper 9.80 (+0.10), **Anaconda 9.60 (+1.20 — load-
  bearing recovery; the v5.22.0 -1.30 dock was driven by 3
  silently-RED CI gates that v5.23.0 RC.\* + v5.24.0 Hy.\* +
  v5.25.0 Pv.\* closed structurally, not symptomatically)**,
  Cobra 9.70 (+0.15), Coral 9.70 (+0.15), **Boa 9.55 (+0.55 —
  largest single-panel Boa improvement in project history;
  Bo.18r 3-consecutive-panel persistence finally structurally
  closed)**, Mamba 9.80 (-0.05). 7 EXCEEDS / 0 MEETS / 0 NEEDS
  WORK; 7 PASS WITH NOTES. **0 NEW HIGH, 0 NEW MEDIUM, ~14 NEW
  LOW** (mostly process polish). **v5.22.0 docket: 25/25 items
  CLOSED at v5.28.0 HEAD** (highest closure rate in v5 history
  across a single recovery arc). Mb.\* / Mc.\* / Eu.\* arcs all
  CLOSED entering this panel; 4 prev-LINK_FAIL goldens
  (47/48/49/51) flipped to PASS via Eu.1..Eu.4. **Phase 2 H.\*
  hygiene closures** (committed `069ff24` ahead of panel cut,
  per Bo.27 / Wd.8 cross-reference convention codified at
  `.reviews/PANEL_AUDIT_TEMPLATE.md`): H.1/H.2/H.3 (Bo.18r-class)
  README.md fixed-point status paragraphs at lines 175 / 183 /
  196-197 bumped to v5.27.0 / 241k / 23 consecutive releases;
  H.4 (Bo.17r-class) 3 localized READMEs (es/pt/zh-CN) native-
  compiler subsection rewritten with v5.23-v5.27 arc summary;
  H.5 (Bo.10-class) `docs/known_issues.md` Last-updated bumped;
  H.6 (An.1-class) `.reviews/CARRY_FORWARD.md` v5.25-v5.27
  closure rows appended (4-release update-protocol drift caught
  + fixed); H.7 cadence-gap acknowledgment in PROMPT.md +
  PRE_PANEL_AUDIT.md preambles. **Cadence-gap closure 1 minor
  late on purpose** — v5.24.0 Hy.3 cadence-enforcement gate
  fired hard at v5.27.0 (5+ minor threshold); v5.28.0 closes
  the gap because bundling formatter polish (Mc.8+Mc.9+Tk.1)
  with a panel cycle was rejected during v5.27.0 PLAN drafting.
  Two reviewers (Anaconda, Coral) independently judged the
  framing honest. **Convergent recommendation (Cobra Cb.New1 +
  Rattler Ra.Inf1 — independent reviewers, same finding shape)**:
  extend `tests/llvm/test_async_link.py` link-and-run pattern
  to all 95 goldens via new `test_llvm_link_all.py` (Tn.\*
  generalization). Closes the structural gap that hid Eu.1..Eu.4
  for 3 releases. **Escalate to MEDIUM at v5.29.0 if not picked
  up in a Pv.\* follow-on.** Other LOW recommendations: M.1
  (Mamba — `.h` vs `.c` header asymmetry recurrence; Pv.7-style
  structural gate); A.1 (Anaconda — new
  `check_carry_forward_freshness.py` gate); Ra.New1 (Rattler —
  Stage2 teardown narrowed to stdout-redirect-specific SIGSEGV;
  investigation tractable, consider closing in v5.29.0 rather
  than v6.0). **Cadence reset:** next routine panel due v5.33.0.
  See `.reviews/v5.28.0/{README.md, V5_DECISION.md, PRE_PANEL_AUDIT.md}`,
  7× `<reviewer>/findings.md`, and
  `docs/roadmap/v5/v5.28.0/SESSION_REPORT.md`.

- **v5.27.0** (ready, not tagged) — **Mc.8 + Mc.9 + Tk.1 —
  formatter polish; Mc.\* parity arc CLOSED.** Three formatter /
  rewriter polish items shipping together because they all live
  in `mapanare/format.py` and ship without compiler edits. Closes
  the v5.13.0 Mc.\* parity gap docket (Mc.8 + Mc.9, 12-release
  carry each) and the v5.24.1 Wd.2 latent rewriter bug (Tk.1,
  3-release carry). **Strict 3-stage fixed point preserved by
  construction at 241,842 lines / 0 diff** (23-release strict
  streak — same line count as v5.26.1 because zero
  `mapanare/self/*.mn` source edits in v5.27.0; the existing
  argv-forwarding loop in `main.mn` carries the new flags through
  the native dispatch unchanged). Goldens **95/95**. **Mc.8**
  (`mapanare fmt --line-length N`): **detect-only** long-line
  reporter. Phase 0 surfaced that Mapanare's grammar is strictly
  single-line for all expressions — newlines are not implicit
  continuations inside `(`/`[`/`{`/`#{` — so an auto-wrap
  rewriter cannot satisfy the v5.13.0 Mc.2 AST-preservation
  invariant. Pure read-only scan; never modifies source; default
  mode reports overlong lines on stderr; under `--check` causes a
  non-zero exit so CI gates can enforce the ceiling; `N=0` (the
  default) disables the check. Auto-wrap rescoped to a future
  release that also adds newline-tolerant grammar inside grouping
  delimiters. **Mc.9** (`mapanare fmt --sort-imports`): sorts
  contiguous top-level `import` blocks alphabetically. Block
  boundaries are any non-import line (blank, comment, or other
  statement), so the user's existing groupings (e.g. stdlib /
  third-party / local separated by blanks) function as the
  de-facto group structure: each group sorts independently.
  Comments inside an import block split the surrounding block
  into sub-blocks — neither side reorders across the comment.
  Idempotent. AST-preserving up to `ImportDecl` declaration
  order; load-bearing corpus check sorts the 8-import block in
  `mapanare/self/main.mn` and asserts `ImportDecl` multiset
  preservation. **Tk.1** (`to_terse` empty `#{}` rewriter bug):
  surgical 6-LOC fix in `mapanare/format.py::to_terse` —
  `endswith("{}")` branch now applies the same
  `_looks_like_stmt_block_opener` filter the `endswith(" {")`
  branch relies on via `_find_match_verbatim_lines`, so
  expression-context empty literals (`let m: Map<String, Int> =
  #{}`, `let p = Point {}`) survive verbatim instead of
  collapsing to grammatically invalid `... = #:` + indented
  `pass`. v5.24.1 Wd.2 sidestepped this latent bug by leaving
  SPEC §17.1 unrewritten; with Tk.1 fixed, `to_terse_markdown
  (SPEC.md)` is now safe to run end-to-end. Falsifiability
  round-trip verified: 3 unit tests (`test_to_terse_preserves_
  empty_map_literal`, `test_to_terse_empty_map_literal_idempotent`,
  `test_to_terse_preserves_empty_struct_literal`) all fail on
  pre-fix `format.py` with the exact pre-fix bug shape; all 3
  pass after the fix. **Source delta:** Python only —
  `mapanare/format.py` ~95 LOC (Tk.1 ~6 + `find_long_lines` ~30
  + `sort_imports` ~50 + `__all__`); `mapanare/cli.py` ~30 LOC
  (argparse + per-file detector wiring); 4 new test files /
  extensions (~525 LOC tests, 47 new test cases); ~90 LOC docs
  in `docs/guides/formatter.md`. **Cadence-gate hard fire**:
  `scripts/check_cadence.py` fires hard at v5.27.0 HEAD (5+
  minor versions since v5.22.0 panel). **Acknowledged and
  informational** — the v5.28.0 RE-PANEL closes the cadence gap
  one minor late on purpose; bundling formatter polish with a
  panel cycle was rejected during PLAN drafting (formatter work
  is the wrong scope to mix with a panel review cycle).
  **Mc.\* parity arc CLOSED** — every Mc.\* item from the
  v5.13.0 parity gap docket is now resolved. See
  `docs/roadmap/v5/v5.27.0/SESSION_REPORT.md` and `PLAN.md`.

- **v5.26.1** (ready, not tagged) — **Eu.1..Eu.4 — close
  v5.26.0-deferred LINK_FAIL bug classes; Eu.\* arc closeout.**
  Four small-but-distinct codegen / lowering fixes that move
  goldens 47, 48, 49, 51 from LINK_FAIL → PASS. Each was a
  pre-existing latent bug surfaced by v5.26.0's Phase 0 audit
  and tracked as `xfail(strict)` in
  `tests/llvm/test_async_link.py`. Per-bug Phase 0 investigations
  honored — bundled in one release for efficiency, not conflated
  (mirrors v5.26.0 Mb.7/Mb.9 split discipline). **Strict 3-stage
  fixed point preserved at 241,842 lines / 0 diff** (22-release
  strict streak; +1,849 lines vs v5.26.0's 239,993 from the new
  lowerer/emitter arms). Goldens **95/95**.
  `tests/llvm/test_async_link.py` 10/10 PASS, 0 XFAIL.
  **Eu.1**: `emit_unwrap` on `Result<T, E>` did one
  `extractvalue ..., 1` returning the inner aggregate `{Ok_ty,
  Err_ty}` rather than the Ok payload at field 0 of that inner
  aggregate. Fixed at both `mapanare/emit_llvm_text.py::_do_unwrap`
  and `mapanare/self/emit_llvm.mn::emit_unwrap` — for `TK_RESULT`
  subjects, do TWO `extractvalue` ops. Closes golden 47 (`?`
  operator on Result). **Eu.2**: standalone `Ok(...)` / `Err(...)`
  literals at call-arg sites (e.g., `classify(Ok(42))` from
  `main`) lowered with empty `dest.ty.args` because the caller
  wasn't a Result-returning fn — `emit_wrap_ok` then derived the
  outer wrapper type from `resolve_mir_type` (fallback `{i1, {ptr,
  ptr}}`) while the inner aggregate used real Ok/Err widths
  (`{i64, ptr}`) — three disagreeing `insertvalue` widths in one
  chain. Fixed at `mapanare/self/lower.mn` Ok/Err lowering to
  default missing args mirroring `mapanare/lower.py:2398`
  (`Result<T, String>` for `Ok(T)` and `Result<Int, T>` for
  `Err(T)`). Closes golden 48. **Eu.3**: `match` on a primitive
  (Int / Bool / String) subject emitted `EnumTag` which lowered
  to `extractvalue i64 %v, 0` — LLVM rejects (i64 is not
  aggregate). Fixed at `mapanare/self/lower.mn::lower_match`:
  primitive subjects bypass the switch entirely and emit a
  sequential test cascade — jump to `arm[0]`; arms with literal
  patterns gain an implicit `subject == LIT` check at entry; the
  existing v4.79.0 P3 guard fall-through is preserved. Also
  `bind_ident_pattern` uniquifies its alloca SSA name with
  `tmp_counter` (mirrors `bind_one_pattern_field`'s pattern) so
  multiple `Some(x) if guard` arms don't collide on `%x.addr`
  under cascade dispatch. Closes golden 49. **Eu.4**: `match`
  with or-pattern + guards (e.g., `Some(0) | None | Some(x) if g
  | ...`) emitted N duplicate `i64 1` switch cases — LLVM rejects
  "duplicate case value in switch". Fixed via two coordinated
  changes in `mapanare/self/lower.mn`: (1) `build_match_arms`
  dedups switch entries by tag value (first arm wins; subsequent
  same-tag arms remain reachable through fall-through), default
  label set once (wildcard wins over earlier ident-non-enum); and
  (2) or-pattern arms with a literal-bearing alt emit a per-alt
  entry switch at the arm body — constructor alts with no payload
  (e.g., `None`) → direct match; constructor alts with literal
  sub-args (e.g., `Some(0)`) → payload-check block; default →
  next arm. New helper `is_builtin_variant_name` recognises
  `None`/`Some`/`Ok`/`Err` as variants when they appear as
  `IdentPat` (the parser does not wrap them in `ConstructorPat`).
  Closes golden 51. **Bb.\* — no seed refresh** (no C-runtime
  call shape changes). **Eu.\* arc CLOSED** — every v5.23.1 →
  v5.26.0 LINK_FAIL bug class is now a regression-locked PASS
  via `tests/llvm/test_async_link.py::test_deferred_link_failures`
  (10/10 PASS at HEAD; the four `pytest.xfail` short-circuits
  were removed). Source delta: ~17 LOC Python + ~14 LOC self-host
  (Eu.1) + ~10 LOC self-host (Eu.2) + ~95 LOC self-host (Eu.3) +
  ~150 LOC self-host (Eu.4) = ~286 LOC total (above the per-fix
  30-LOC ceiling but kept in scope to close the arc structurally;
  alternative was four small releases over 1–2 weeks).
  See `docs/roadmap/v5/v5.26.1/SESSION_REPORT.md` and `AUDIT.md`.

- **v5.26.0** (ready, not tagged) — **Mb.7 + Mb.9 — codegen +
  Win64 ABI fixes; Mb.\* arc closeout.** Two real codegen fixes
  in the same release. Mb.7 closes the 3-release carry (v5.23.1
  → v5.24.0 → v5.25.0) of the i64/i1 tag-emit bug in
  `mapanare/self/emit_llvm.mn::emit_enum_tag`: the function
  zexted Result/Option i1 tags to i64 unconditionally, but the
  try-operator path declared its dest as `mir_bool()` (i1) and
  consumed it in `Branch`, producing invalid `br i1 %i64_val`.
  Surgical 5-LOC fix — honors `dest.ty.kind`: emit i1 directly
  for `TK_BOOL` consumers (try-op), keep zext for `TK_RESULT`/
  `TK_OPTION`/`TK_ENUM` (match → `switch i64`). Mb.9 closes the
  publish-run-#48 Windows OOM in the v5.23.2 Te.3.B.2 functions
  `__mn_count_user_brace_block_openers` and
  `__mn_emit_brace_deprecation_warning`: Python's `_do_call`
  uses a 64-byte byref threshold but `_decl_fn` uses 8 bytes on
  Win64 — the 16-byte `MnString` was passed by-value at the
  call site while the declaration said `ptr`, and gcc's Win64
  pass-by-hidden-pointer semantics for `MnString source` then
  read the data buffer's bytes 8..16 as the length. For
  `mnc_all.mn` (`// Auto-generated:`) those bytes are
  `g e n e r a t e` → `0x65746172656e6567` → `malloc(7e+18)` →
  OOM. Fixed via explicit handlers in Python's `_do_call` AND
  self-host's `emit_mir_call` routing both functions through
  the runtime-call path (mirrors the v5.23.1 Mb.1 pattern for
  `__mn_indent_to_braces`). **No C-runtime edits**; the C side
  was always correct. **No Bb.\* seed refresh** (no call shapes
  change); this corrects the PLAN. **Phase 0 disclosure** — the
  v5.23.1 SESSION_REPORT premise ("9 LINK_FAIL goldens share
  one bug") was wrong: only golden 47 had Mb.7's bug; goldens
  55-59 (the async cluster) never had it (always linked); 47/48/
  49/51 fail for distinct reasons (Eu.1..Eu.4 rescoped to
  v5.26.1). **Strict 3-stage fixed point preserved by
  construction at 239,993 lines / 0 diff** (21-release strict
  streak; +158 lines vs v5.25.0's 239,835 from the new dispatch
  arms). Goldens **95/95**. New `tests/llvm/test_async_link.py`
  (10 tests: 6 PASS + 4 documented xfail) — IR-invariant gate
  for the i64/i1 anti-pattern, link-and-run sanity for the async
  cluster, xfail markers documenting the four v5.26.1-rescoped
  bug classes (XPASS-strict so future fixes auto-flip them).
  New `tests/native/test_brace_funcs_windows_abi.py` (8 PASS)
  — IR-shape gate under forced Win64 triple plus Linux ctypes
  contract proving the C side is correct on SysV. **Mb.\* arc
  CLOSED** — every memory- and ABI-related panel finding
  through v5.22.0 + v5.23.2's Te.3.B.2 follow-on closed. See
  `docs/roadmap/v5/v5.26.0/SESSION_REPORT.md` and `AUDIT.md`.

- **v5.25.0** (ready, not tagged) — **Pv.\* — CI prevention
  infrastructure.** First release in the new **Pv.\*** sub-arc
  (structural pattern parallel to v5.24.0's **Hy.\***). Closes
  the class of failure where a CI-only test path catches a bug
  that could have been caught locally — typically because (a) a
  stale local artifact masks the bug on the developer machine,
  (b) a feature ships without an end-to-end test exercising it
  through the .mn-caller side, or (c) a test asset only runs on a
  non-Windows CI job. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage fixed
  point preserved by construction at **239,835 lines / 0 diff**
  (20-release strict streak; same line count as v5.24.1 because
  no source under `mapanare/self/` changed). Goldens **95/95**.
  **Pv.1**: new `tests/test_runtime_lib_lookup.py` (3 cases)
  locks `mapanare.test_runner._find_runtime_lib()` against
  re-introduction of v3.x-era `libmapanare_core.*` candidate
  names; sweeps stale shadows, asserts canonical name resolution,
  end-to-end links a tiny IR fragment that references
  `__mn_str_eq` against whatever archive the lookup returned.
  Pre-fix (commit `9dcbbb5` shipped on `dev` between v5.24.1 and
  v5.25.0) the lookup silently returned `None` because the
  candidate list still mentioned the v3.x names; a stale local
  `libmapanare_core.so` masked the regression on developer
  machines for 11+ releases. **Pv.2**: new
  `tests/bootstrap/test_preprocess_memcheck.py` (3 parameterized
  cases — brace-only, colon-only, mixed) runs `mnc-stage1
  preprocess` under valgrind. Locks the
  `__mn_indent_to_braces` brace-only fast-path against
  MnString-aliasing regressions; pre-fix the fast path returned
  the input MnString aliased and produced a double-free at
  function-end drop glue. Mirrors v5.23.1 Mb.3's grep-for-symbol
  pattern rather than `--error-exitcode=1` because `mnc-stage1`
  has a pre-existing single-shot leak from `__mn_argv` (~71 bytes,
  known and tracked since v5.23.1) that would otherwise produce a
  100% noise floor. **Pv.3**: extended `make ci-gates` (v5.24.0
  Hy.1) with new `clean-build-test` sub-gate — 9 sub-gates total,
  up from 8. Removes
  `runtime/native/libmapanare_*.{a,so,dylib,dll}` (the explicit
  `rm -f` is what makes the rebuild meaningful — `make clean`
  alone does not touch the archive), runs `make build-rt`, then
  runs `pytest tests/test_at_test_runtime.py
  tests/test_runtime_lib_lookup.py`. Catches the runtime-archive
  rename / relocation class structurally before any PR lands.
  **Pv.4**: new `scripts/validate_wsl.sh` runs the Linux pytest
  path end-to-end (`make build-rt` + `python3
  scripts/build_stage1.py` + `pytest tests/ -x -n auto`) from any
  CWD by resolving the repo root from the script's own location.
  New `dev.ps1 validate-wsl` mode shells out via `wsl -d Ubuntu`
  so a Windows host can produce the Linux pytest signal without
  leaving the dev loop. Optional pre-push hook at
  `scripts/hooks/pre-push.sample` (commented opt-in; not enabled
  by default — forcing the full suite on every push kills the dev
  loop and produces resentment, not safety). **Pv.5**: removed
  the v5.13.1 entry from CLAUDE.md "Planned / in-progress"
  section. The runtime-lib wiring (At.1's only remaining open
  item) shipped on `dev` between v5.24.1 and v5.25.0; the `@test`
  runtime is fully functional end-to-end. **Pv.6**: closes
  publish run #48 Linux + macOS tarball-smoke job failures.
  `.github/workflows/publish.yml` Linux + macOS smoke fixtures
  rewritten from `echo 'fn main(): print("...")' > /tmp/hello.mn`
  (single-line `fn x(): y` was the v5.14.0 SPEC §1009 forward
  promise that v5.21.1 H.4 explicitly rescoped to v6.0 — fixture
  authored against an unshipped feature) to multi-line colon via
  `printf 'fn main():\n    print(...)\n'`. New
  `tests/test_publish_smoke_fixtures.py` (2 cases) extracts every
  inline `.mn` fixture across four shapes (bash echo, bash
  printf, PowerShell here-string, bash heredoc) and parses each
  through `mapanare.parser.parse`; first test guards against a
  regex update silently dropping every fixture. **5 fixtures
  locked at v5.25.0 HEAD**. **Falsifiability**: every Pv.\* test
  documents a revert-and-restore round-trip in its module
  docstring; verified red-then-green for Pv.1 / Pv.2 / Pv.6 in
  the release session. **Out of scope** (held): Mb.7 (i64/i1
  tag-emit, 9 LINK_FAIL goldens) — v5.26.0; `to_terse` empty
  `#{}` rewriter bug — v5.27.0; `mnc fmt` long-line wrap +
  import sort — v5.27.0. See
  `docs/roadmap/v5/v5.25.0/SESSION_REPORT.md` and `PLAN.md`.

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

**Terseness arc — v5.13–v5.21 (shipped).** All terseness arc
releases (v5.13.0 → v5.21.0, plus the Sh.\* self-host rewrite at
v5.17.0 → v5.17.2) have shipped. See per-release SESSION_REPORTs
under `docs/roadmap/v5/v5.13.0/` through `docs/roadmap/v5/v5.21.0/`
for details, or `CHANGELOG.md` for summaries. The terseness thesis
is now visible in real code: cumulative source shrink of −13.8%
across `mapanare/self/` from v5.13.0 baseline.

- **v5.19.0** — **Te.3 + Dk.* — closeout.** Soft-deprecate
  `{}` (still parses, emits warning); hard removal scheduled
  for v6.0. Ship `mapanare/builder` + `mapanare/runtime`
  Docker images. See `docs/roadmap/v5/v5.19.0/PLAN.md`.
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

Tensor surface complete as of v5.45.0 (Ts.\* — closeout arc CLOSED):
reshape (aliasing), view (aliasing), stepped slice (copy). Strided /
non-contiguous tensors reserved for v6.0+ (would force ABI change on
`mapanare_tensor_t` for transpose / permute / reverse step).

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
- **Python entrypoint is bootstrap-only on release installs (v5.32.0+).**
  Windows SDK ZIPs ship a real native `mnc.exe` (built from
  `mapanare/self/` via the stage1 → stage2 self-compile cycle).
  **v5.33.0 extends this to Linux x86_64 and macOS arm64 release
  tarballs** — both ship `dist/mapanare/mnc` (native ELF / Mach-O)
  alongside the existing PyInstaller `mapanare` binary. The native
  `mnc` is invoked directly; no Python interpreter starts on
  `mnc --version`, `mnc run`, or `mnc build`. Linux aarch64 + macOS
  x86_64 tarballs are deferred to v5.34.0+ (no native runner /
  cross-compile infrastructure yet). The Python `mapanare`/`mnc`
  console-script remains for clean clones, pip-installs without
  the SDK, and the `bash scripts/build_from_seed.sh` bootstrap
  path. `mapanare/__main__.py` detects a sibling `bin/mnc[.exe]`
  and `os.execv`s to it; `MAPANARE_FORCE_PYTHON=1` opts out for
  dev/debug.

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

This project is indexed by GitNexus as **Mapanare** (32673 symbols, 68265 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
