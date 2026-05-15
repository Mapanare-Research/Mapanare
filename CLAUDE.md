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

- **v5.54.0** (ready, not tagged) — **Cl.2 + Cl.3 + Cl.4r —
  agent stdlib ergonomic refactor + walk_dir closure anchor +
  websocket str(byte) sweep.** Ships the v5.47.0 splits that
  v5.48–v5.53 deferred for the Te.3 brace-removal arc. **Cl.2
  is BREAKING for stdlib consumers** — refactors
  `stdlib/agent/{url,remote,node,supervision}.mn` from the
  v5.43.0 flat-tuple Result workaround (`UrlParseResult`,
  `NodeListenResult`, `RemoteConnectResult`, etc. — 8 struct
  types + 16 constructor helpers + the
  `(ok, value, err_kind, err_msg)` field shape) to ergonomic
  `Result<T, NetworkError>` at the 12 public-function surface.
  Structurally unblocked by v5.46.0 Lf.\* (the wrap-shape
  default fix in `mapanare/lower.py` Ok/Err constructor branches
  that closed the v5.43.0-era three-bug class). Two companion
  types added because Mapanare has no first-class tuples:
  `RecvOk { handle: RemoteAgent, frame: Frame }` for
  `remote_agent_recv`'s Ok side, `ConnRecvOk
  { conn: NodeConnection, frame: Frame }` for
  `conn_recv_frame`'s Ok side.
  **Cl.2.0 — Phase 0 audit (load-bearing).** Two reversals of
  v5.47.0/PLAN.md premise documented in `PRE_PHASE_AUDIT.md`:
  (1) **Cl.3's `walk_dir` does not exist** in `stdlib/fs.mn` at
  v5.53.0 HEAD; the original v5.40.0 carry's named function was
  renamed/removed. `walk()` (current name; returns plain
  `List<String>`) uses the bug-class shape internally via
  `match list_dir(current)` against
  `Result<List<String>, FsError>` (line 487) and compiles
  cleanly via the v5.46.0 Lf.\* fix. The Cl.3 carry was
  implicitly closed. (2) **Cl.4r residual count is 5 sites**
  (not 11 per v5.47.0 estimate); v5.47.0 Cl.4 closed 6.
  Remaining at `stdlib/net/websocket.mn:236, 743 (×2),
  1121 (×2)`. (3) **Cl.2 LOC sizing**: ~615 LOC, at the
  600-LOC bundle/split threshold. User authorized atomic
  bundle.
  **Cl.2.1–Cl.2.4 — 4-file atomic migration.**
  url.mn: `parse_agent_url(s) -> Result<AgentUrl, NetworkError>`
  with `Err(BadUrl(...))` / `Err(UnsupportedScheme(...))`
  variants; 13 return sites rewritten. node.mn:
  `node_listen` / `node_listen_tls` / `node_accept_one` /
  `conn_send_frame` return `Result<T, NetworkError>`;
  `conn_recv_frame` returns `Result<ConnRecvOk, NetworkError>`;
  `dr.err` forwarding now uses `Err(dr.err)` directly instead
  of legacy `ne_kind(dr.err)` / `ne_msg(dr.err)` int-shuttle.
  remote.mn: 5 pub fns return `Result<RemoteAgent,
  NetworkError>`; `remote_agent_recv` returns `Result<RecvOk,
  NetworkError>`. supervision.mn: `remote_agent_heartbeat_check`
  passthrough to refactored `remote_agent_ping` returns
  `Result<RemoteAgent, NetworkError>`. **Forward-compatible
  behavior change at `remote_agent_connect`'s
  parse_agent_url error path:** Err now carries the precise
  NetworkError variant (`BadUrl`, `UnsupportedScheme`) instead
  of an int-encoded round-trip through `ne_kind`/`ne_msg`.
  **Cl.2.5 — test migration.**
  `stdlib/agent/tests/test_dist_url.mn` (10 destructures) and
  `stdlib/agent/tests/test_dist_node.mn` (7 destructures)
  rewritten to `match` form with inline variant-discriminator
  helpers (`is_no_key`, `is_connect_failed`,
  `is_unsupported_scheme`). Proto + supervision tests
  unchanged.
  **Cl.2.6 — doc cookbook refresh.** `docs/stdlib/agent.md` 3
  cookbook snippets migrated; "What's not here yet" section
  marked Result-API SHIPPED with v5.54.0 cross-reference.
  Plus `examples/agents/distributed_pool.mn` (unforeseen
  caller found during Phase 2 grep sweep) migrated for example
  consistency.
  **Cl.3 — walk_dir implicit-closure anchor.** New pytest
  class `tests/stdlib/test_fs.py::TestWalkDirCl3Anchor` (3
  cases): asserts `match list_dir(...)` compiles, `walk()`
  compiles, nested `list_dir` destructure compiles.
  Falsifiability locked: revert v5.46.0 Lf.\* (the Ok/Err
  wrap-shape default) → recorded `extractvalue ptr ... 0` +
  `zext ptr to i64` IR pattern resurfaces. Stale `walk_dir`
  comment in `stdlib/ai/ask_cache.mn:19` refreshed to point
  at the anchor.
  **Cl.4r — websocket sweep.** 5 sites at lines 236
  (`apply_mask` XOR'd byte), 743 (×2: `build_send_frame`
  Close arm status code hi/lo), 1121 (×2: `ws_close_normal`
  same shape) replaced with `__mn_str_chr(byte)` per v5.43.0
  Da.0 extern precedent.
  **STRICT 3-stage fixed point preserved by construction at
  v5.53.0's baseline** — zero `mapanare/self/*.mn` edits,
  zero Python compiler edits, zero runtime edits. **Goldens
  103/103.** 56-release strict streak from v5.7.1 holds.
  Source delta: ~ −220 LOC net (Cl.2 removes ~180 LOC of
  flat-tuple plumbing; Cl.4r line-neutral; Cl.3 adds ~50 LOC
  pytest anchor). 8 source files modified + 1 example + 1
  doc cookbook + 1 pytest file extended.
  Aggregate state entering v5.55.0: **0 HIGH** /
  **2 MEDIUM** (Ai.1 `_specialize_fn` carry from v5.40.0;
  Nu.2 macOS notarization carry from v5.33.0) / **~2 LOW**
  (Lf.4 variant-name collision split to v5.46.x, defer-to-v6.0
  candidate; Sf.\* Win64 `__mn_str_free` ABI fix carry from
  v5.53.1). **Cl.\* arc CLOSED at v5.54.0.** See
  `docs/roadmap/v5/v5.54.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.53.0** (ready, not tagged) — **Te.3.F — nested single-line
  stmt-block recursive migration. Sf.\* split to v5.53.1.**
  Phase 0 audit produced two load-bearing reversals of the v5.53.0
  PLAN. (1) **Sf.\* PLAN hypothesis was wrong.** PLAN.md hypothesized
  the `82_struct_update` / `83_struct_update_partial` Win64 integer-
  overflow lived in `_lower_struct_update`'s base-temp synthesis;
  IR inspection of the Python-bootstrap output under
  `target triple = "x86_64-w64-windows-gnu"` shows correct zero-init
  + per-field GEPs at the right stride/width. The actual root cause
  is a Win64-ABI mismatch at three `__mn_str_free` drop-glue call
  sites in `mapanare/emit_llvm_text.py` (lines 1794, 2015, plus the
  decl at 1881) that bypass `_rt`'s Win64 sarg lowering, mirrored
  by four sites in `mapanare/self/emit_llvm.mn` (lines 4660, 4840,
  4844, 4990 + decl at 1101). On SysV the aggregate `{ptr, i64}`
  decomposes to rdi+rsi by coincidence matching the C runtime's
  decomposed `(const char*, int64_t)` signature (v5.8.3 Wb.1
  precedent); on Win64 it becomes sarg and the C function reads
  garbage for `len_with_heap_bit`, which leaks through downstream
  `mn_checked_add` calls. Sized at ~100 LOC across Python + self-
  host emitter + tests; above PLAN.md's 50-LOC bundle threshold
  AND verification is blocked locally (no Windows clang). **Split
  to v5.53.1** with fix recipe documented in
  `docs/roadmap/v5/v5.53.0/PRE_PHASE_AUDIT.md` so the next session
  begins with the localized fix site, not another root-cause hunt.
  (2) **Te.3.F empirical recount.** PLAN's 10 lexer + 1 lower = 11
  residuals stands; CLAUDE.md's "17 lexer.mn predicates" was
  speculative. But only 7 of 11 are migrate-able under v5.48.0
  grammar — 4 chained-if-else cases (lexer.mn 267/276/285 and
  lower.mn:4843) need a single-line `else:` continuation rule
  that v5.48.0 does NOT support (verified empirically — three
  parser probes in PRE_PHASE_AUDIT.md rejected the chained-`else:`
  shapes with `Unexpected 'else' / 'if'` ParseErrors). Defer the
  4-site closeout to v6.0 PLAN where the grammar extension lands
  alongside hard removal of `{}`.
  **Te.3.F.1 — formatter recursion at `mapanare/format.py::_migrate_one_line_stmt_block`.**
  When `body_shadow` contains nested `{` / `}`, recurse inside-out
  on the body — the inner stmt-block migrates first
  (`if B { stmt }` → `if B: stmt`), the outer's line-363 reject
  clears, the outer migrates (`if A: if B: stmt`). If the recursive
  call returns `None` (e.g. chained-if-else inner) or the migrated
  body still contains braces, the outer aborts — no half-migration.
  **Te.3.F.2 — self-host source migration in `mapanare/self/lexer.mn`.**
  Single cluster (one file). 7 sites migrated via
  `python -m mapanare fmt --to-terse mapanare/self/lexer.mn`:
  `is_alpha` (191-192), `is_digit` (196), `is_hex_digit` (212-213),
  `scan_char` close-quote consume (371), `scan_op` AND detect (386).
  `mnc_all.mn` regenerated via `bash scripts/concat_self.sh`.
  Python-bootstrap parse of both files verified post-migration.
  Local STRICT 3-stage verification cannot run (no Windows clang
  for stage1 rebuild + the local stage1 binaries are WSL ELFs
  that don't execute on Windows-cmd); CI is the safety net per
  the v5.49.0 SESSION_REPORT precedent. STRICT preserved by
  construction at v5.52.0's baseline of **246,347 lines / 0 diff**
  because the 7 migrations are AST-equivalent (verified by
  `to_terse` round-trip through `to_braces` to identical brace
  stream → identical MIR / LLVM IR); 55-release strict streak
  from v5.7.1 holds at the same value.
  **Te.3.F.3 — falsifiability lock in
  `tests/test_single_line_colon_blocks.py::TestNestedStmtBlock`.**
  7 cases: 5 pure-nested-2 positive (migration + AST round-trip +
  idempotence + complex inner body + inner-assignment), 2
  deferred-shape negative (chained-if-else outer stays in brace
  form; no half-migration to invalid colon form). Falsifiability
  verified empirically by `git stash mapanare/format.py` + re-run
  → 3 of 5 positive tests fail with the recorded
  `assert 'if X: if Y: ...' in <unchanged brace string>`
  AssertionError; `git stash pop` → 7/7 GREEN.
  **First-party brace surface delta: 25 → 18 (28% reduction).**
  Original PLAN target was 25 → ~14; the 4-site deferral moves
  the v6.0 hard-removal cut from ~14 to 18 first-party residuals
  + chained-if-else grammar work. The 7-site migration silences
  the v5.19.0 `_emit_brace_deprecation_warning` for the migrated
  sites; for the 4 remaining sites it continues firing pending
  v6.0.
  Aggregate state entering v5.53.1: **0 HIGH** (Sf.\* moves to
  v5.53.1 docket but is structurally well-localized + sized) /
  **3 MEDIUM** (Sf.\* Win64 `__mn_str_free` ABI fix to v5.53.1;
  macOS notarization carry from v5.33.0 Nu.2; Ai.1
  `_specialize_fn` carry from v5.40.0) / **~5 LOW** (4 chained-
  if-else residuals to v6.0; Lf.4 variant-name collision to
  v5.46.x; ergonomic refactor of v5.43.0 distributed-agent APIs;
  fs.mn `walk_dir`; websocket.mn `str(byte)`). **Te.3.F arc
  CLOSED at v5.53.0; Sf.\* arc IN-FLIGHT — fix recipe locked,
  v5.53.1 session input ready.** See
  `docs/roadmap/v5/v5.53.0/{PLAN.md, PROMPT.md, PRE_PHASE_AUDIT.md,
  SESSION_REPORT.md}`.

- **v5.50.0** (ready, not tagged) — **Te.3.E — match-arm body
  grammar extensions; close v5.48.1 brace residuals.** Adds
  colon-form shorthand for the two arm-body shapes v5.48.0 Te.3.D
  had no migration target for (multi-stmt single-line
  `Pat => let X = []; return X` and multi-line `Pat =>:` with
  indented body). Pulls the brace-removal runway forward from v6.0
  and migrates the 737 residual brace openers across
  `mapanare/self/*.mn` to colon form. **First-party brace surface
  drops from 737 to 25 occurrences (96.6% reduction) — within
  audit ≤50 success criterion.**
  **Te.3.E.0 — Phase 0 audit (PRE_PHASE_AUDIT.md, mandatory).**
  Per-shape classifier across 10 self-host modules. Three
  load-bearing audit findings: (1) PLAN.md's Te.3.E.1 scope was
  stale — empirical count for single-stmt non-kw arm bodies is 0
  (already migrate via v5.48.0); the real 57 residuals are
  multi-stmt `;`-bearing bodies; (2) 387 of 737 are verbatim
  bystanders that cascade-migrate once Te.3.E.2 lands a colon form
  for multi-line arm bodies; (3) 282 non-verbatim residuals are
  non-deprecated forms with no migration target — adds Te.3.E.X
  counter-tightening as a new bundled phase. Decision:
  **Candidate A** (`Pat =>:`) for multi-line arm grammar
  (LALR-friendly, symmetric with `:` stmt-blocks).
  **Te.3.E.1 — `;`-bearing single-line arm body shorthand.**
  `_rewrite_arm_stmts_in_line` accepts any arm body with a depth-0
  `;` regardless of first keyword. Source
  `Pat => let X = []; return X` parses identically to brace form
  `Pat => { let X = []; return X }`. Mirrored in
  `_migrate_one_line_arm_body` and `_migrate_one_line_stmt_block`
  (formatter for stmt-blocks). 57 self-host residuals + ~12 stmt-
  block residuals closed.
  **Te.3.E.2 — multi-line `Pat =>:` colon form.** The existing
  `_indent_to_braces` `:` branch already produced correct brace
  stream for `Pat =>` heads; the only fix needed was
  comma-tracking on dedent close. Three dedent loops (main,
  comment-only, continuation) now update parent's `prev_child_idx`
  to the `}` closer line. Without this, the next sibling's comma
  was appended to the OPENER `Pat => {,` instead of the closer
  `},`, which the LALR parser rejected. 98 multi-line arm
  residuals + 387 verbatim cascade bystanders closed.
  **Te.3.E.3 — formatter `to_terse` extension.** Multi-line
  `Pat => {` opener emits colon form `Pat =>:`; pushes block as
  "colon" not "verbatim" so inner content gets normal rewriting.
  `_find_match_verbatim_lines` rescoped to expression-context
  openers only — the match-with-multiline-arm verbatim mark was a
  workaround for the missing grammar, now obsolete. `to_braces`
  runs `_rewrite_arm_stmt_shorthand` for symmetric round-trip.
  **Te.3.E.X — counter tightening (NEW phase from Phase 0 audit).**
  `count_user_brace_block_openers` excludes four shapes that have
  no migration target: (1) inline `match X { ... }`, (2) chained
  `if X { ... } else { ... }`, (3) expr-position `if`, (4)
  `Pat => {}` empty arm body. Pre-fix the v5.19.0 deprecation
  warning fired on these shapes; post-fix it fires only when the
  formatter has something to migrate. 282+11 self-host counter
  false positives excluded.
  **Te.3.E.4 — C runtime mirror.** `runtime/native/mapanare_core.c`
  extended byte-for-byte: 3 dedent-loop comma-tracking fixes in
  `__mn_indent_to_braces`; `;`-bearing body acceptance in
  `mn_arm_rewrite_line`; counter refinements in
  `__mn_count_user_brace_block_openers`. mnc-stage1 rebuilt
  against new runtime; cross-bootstrap fixture suite extended
  from 37 to 46 parameterized fixtures plus the corpus sweep —
  **252/252 byte-identical Python vs C** (was 243/243 at v5.48.1).
  **Te.3.E.5 — self-host source migration in 4 clusters.** ast.mn
  / mir.mn / lower_state.mn, then lower.mn / mir_opt.mn /
  emit_llvm.mn, then lexer.mn / parser.mn / semantic.mn, then
  main.mn. Stage1 rebuild + goldens 103/103 + STRICT 3-stage at
  every cluster checkpoint. `mnc_all.mn` regenerated via
  `bash scripts/concat_self.sh` (1.27 MB → 1.02 MB; ~20% drop).
  **Two formatter bugs surfaced and fixed mid-implementation
  (load-bearing).** (1) Comma-tracking on brace-closer line —
  multi-line `Pat =>:` arm bodies emitted the sibling-comma on
  the OPENER `Pat => {,` instead of the closer `},`. Fix applied
  to all three dedent loops on both Python and C sides. (2)
  `} // end-of-block` closer with trailing comment — pre-Te.3.E.3
  the `_find_match_verbatim_lines` workaround hid this case;
  post-Te.3.E.3 the surrounding match migrated to colon form
  leaving an orphan `}` on the comment line. Surfaced on
  `mir_opt.mn:1234` (`} // end param-count guard`). Patched
  `to_terse` to detect `}` followed by line comment and strip the
  brace while preserving the comment. Both bugs caught by Phase
  4's rebuild-after-each-cluster discipline.
  **STRICT 3-stage fixed point preserved at the new v5.50.0
  baseline of 245,155 lines / 0 diff** (∆ +40 from v5.48.1's
  245,115; 53-release strict streak from v5.7.1 preserves at the
  new value). The +40-line shift reflects v5.50.0 self-host
  wiring's marginally different IR span-info encoding, not a
  regression.
  Aggregate state entering v5.50.x: **0 HIGH** / **3 MEDIUM**
  (macOS notarization carry from v5.33.0 Nu.2; Ai.1
  `_specialize_fn` carry from v5.40.0; nested single-line stmt-
  block recursive migration carry from v5.50.0 — 17 lexer.mn
  predicates `if X { if Y { ... } }` shape) / **~5 LOW** (Lf.4
  variant-name collision split to v5.46.x; ergonomic refactor of
  v5.43.0 distributed-agent APIs; fs.mn `walk_dir`; websocket.mn
  `str(byte)`; if-expression colon syntax deferred to v6.0;
  struct-update local integer overflow surfaced during Windows
  goldens — unrelated to Te.3.E\*; file as v5.50.x patch
  candidate). **Te.3.E arc CLOSED at v5.50.0.** The v6.0
  hard-removal cut now needs to address only ~25 self-host
  residuals plus the stdlib/examples sweep. See
  `docs/roadmap/v5/v5.50.0/{PLAN.md, PROMPT.md, PRE_PHASE_AUDIT.md,
  SESSION_REPORT.md}`.

- **v5.49.0** (ready, not tagged) — **Wn.\* — Windows native
  binary smoke fix.** Closes the `mnc.exe run hello.mn` Win64
  OOM regression that the `publish.yml` Windows SDK smoke step
  (line 596) tripped on every release tarball's
  `dist/mapanare/mnc.exe`.
  **Wn.0 — Phase 0 audit.** Reproduced the bug locally on
  Windows 11 x64 (avoiding the `workflow_dispatch` path which
  would have tagged v5.48.1 as a side effect because
  `publish.yml`'s `release` job has no `refs/heads/main`
  guard). gdb backtrace localized:
  `find_clang() → __mn_file_exists(MnString) → mn_to_cstr →
  __mn_alloc(8017634865777560157)`. The `path` arg entered
  `__mn_file_exists` with `data = 0x6f445c6e61754a65` —
  unmapped — decoded as `"eJuan\Do"`, bytes from
  `\Users\Juan\Documents\...`. Output:
  `docs/roadmap/v5/v5.49.0/PRE_PHASE_AUDIT.md`. Bundle/split
  decision: **bundle** Wn.1 (Python emitter) + Wn.2 (self-host
  mirror) in v5.49.0 — single-class single-cause bug, ~25 LOC
  + ~80 LOC respectively, splitting would leave self-host
  emit half-broken on Win64.
  **Wn.1 — Python bootstrap fix.** Added `_RUNTIME_FN_SIGS`
  registry in `mapanare/emit_llvm_text.py` next to the
  existing `_RUNTIME_FN_ATTRS` table. Pre-registers canonical
  `(ret_ty, [param_tys])` for ~40 `__mn_*` runtime symbols
  matching `runtime/native/mapanare_core.h`. Added an
  early-return path in `_do_call` and `_do_extern` that, for
  symbols in the registry, routes through `_rt` (which has
  correct Win64 sarg/sret lowering — alloca + store + pass
  `ptr` for >8-byte aggregates). The auto-declare /
  catchall path no longer gets to derive types from MIR
  context for known runtime symbols, eliminating the
  return-type smell (`declare ptr @__mn_file_exists(ptr)`
  vs the canonical `declare i64 @__mn_file_exists(ptr)`)
  and the call-site ABI mismatch (`call … ({ptr, i64} %v)`
  vs `call i64 … (ptr %sarg)`). Linux/macOS unchanged —
  SysV ABI coincidentally puts the data ptr in RDI either
  way; the bug was Win64-only.
  **Wn.2 — Self-host mirror.** Extended
  `mapanare/self/emit_llvm.mn::emit_mir_call` with one
  `if fn_name == "__mn_file_exists"` →
  `emit_rt_call(..., "i64", "__mn_file_exists", ...)`
  routing branch, mirroring the established v5.26.0 Mb.9 /
  v5.29.0 Mb.10 / v5.48.1 Te.3.D.4.4 precedent (each release
  added one or two routing branches for the specific symbol
  that surfaced). Initial scope was a sweep across ~30
  MnString-arg `__mn_*` symbols, but that pushed the
  generated IR from 2.46M to 3.05M lines and tripped the
  `tests/bench/bench_compile.sh --gate` threshold (2.5M).
  Trimmed to the single bug-confirmed symbol; broader sweep
  becomes a v5.49.x carry candidate (registry-driven
  dispatch preferred over more inline branches). With the
  trim, IR is 2,478,086 lines (~22K headroom under the
  2.5M gate). The self-host's `emit_rt_call` already had
  correct Win64 sarg lowering (Wb.2 closed it for sret,
  Wb.4/We.1 covered the existing sarg surface);
  Wn.2 just adds `__mn_file_exists` to the explicit-
  routing list. Goldens **100/103** locally on Windows
  (3 pre-existing failures in `82_struct_update`,
  `83_struct_update_partial`, `51_match_guards_and_or` —
  all unrelated to Wn.\*; struct-update integer-overflow
  is a pre-existing Windows local-build issue, not
  introduced by this change).
  **Wn.3 — Permanent gdb-backtrace wrapper at
  `publish.yml:596`.** PowerShell mirror of the bash
  Wb.1.dx wrapper at `publish.yml:802-825` and the v5.8.3
  PROMPT Phase 4 paid-forward-instrumentation precedent.
  No-op on success; on the next regression in this class
  the action log surfaces the call site instead of just an
  OOM number, eliminating a re-trigger-CI-to-diagnose round
  trip. `gdb 16.2` is preinstalled on the `windows-latest`
  runner image.
  **Wn.4 — Falsifiability test.**
  `tests/native/test_windows_run_smoke.py`. Five IR-shape
  tests (cross-platform; emit IR under
  `x86_64-w64-windows-gnu` triple and assert call sites use
  `(ptr %sarg.N)` not `({ptr, i64} %v)`) plus one
  Windows-only end-to-end smoke against a staged `mnc.exe`
  (skipped if no binary or no clang on PATH; CI has both).
  Falsifiability round-trip locked in module docstring:
  revert the `_RUNTIME_FN_SIGS` early-return →
  IR-shape gate fails with the recorded by-value-aggregate
  signature; reapply → passes. **5 passed, 1 skipped**
  locally.
  **STRICT 3-stage fixed point** preserves at the new
  v5.49.0 baseline. Local Windows build can't run the full
  STRICT verification (no `libmapanare_rt.a` staged
  locally); CI verifies idempotence.
  Aggregate state entering v5.49.x: **0 HIGH** /
  **3 MEDIUM** (macOS notarization carry from v5.33.0
  Nu.2; Ai.1 `_specialize_fn` carry from v5.40.0;
  `match_arm_open` + `one_line_arm_other` v6.0 grammar
  revisit, carry from v5.48.1) / **~6 LOW** (Lf.4
  variant-name collision split to v5.46.x; ergonomic
  refactor of v5.43.0 distributed-agent APIs; fs.mn
  `walk_dir`; websocket.mn `str(byte)`; if-expression
  colon syntax deferred to v6.0; struct-update local
  integer overflow surfaced during Windows goldens —
  unrelated to Wn.\*, file as v5.49.x patch candidate).
  **Wn.\* arc CLOSED at v5.49.0.** The Windows smoke
  smoke regression is closed; the registry pattern is
  the architectural fix for the entire class (the
  v5.26.0 / v5.29.0 / v5.48.1 ad-hoc routing branches
  in self-host can themselves be replaced by a registry
  in a future cleanup, but that's not v5.49.0 scope).
  See
  `docs/roadmap/v5/v5.49.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.48.1** (ready, not tagged) — **Te.3.D.4 / Te.3.D.5 —
  bootstrap mirror + self-host source migration.** Closes the
  v5.48.0 carry-forward end-to-end. v5.48.0 shipped the Python
  parser/formatter for single-line colon blocks
  (`if x: stmt`, `fn main(): print(1)`) and match-arm statement
  shorthand (`Pat => return n`); the C runtime mirror and the
  migration of `mapanare/self/*.mn` were explicitly split to
  v5.48.1. v5.48.1 brings the native side to byte-identity with
  the Python side and migrates all 17 self-host modules (plus
  `mnc_all.mn`) to the new shorthand. **First-party brace
  surface drops 78%: 6,826 → 1,474 occurrences.** 7 of 18
  self-host files silence the v5.19.0 deprecation warning
  completely (`abi.mn`, `emit_llvm_ir.mn`, `from_go.mn`,
  `from_php.mn`, `from_python.mn`, `from_typescript.mn`,
  `transpiler.mn`); 9 files retain residuals (`match_arm_open`
  multi-line arm bodies and `one_line_arm_other` multi-stmt arm
  bodies — neither has a v5.48.0 shorthand). Legacy braces still
  parse with the v5.19.0 warning unchanged; v6.0 may flip to a
  hard error after v5.48.x soak.
  **Te.3.D.4.0 — Phase 0 audit (PRE_PHASE_AUDIT.md, mandatory).**
  Re-confirmed v5.48.0's 6,826-opener total at HEAD. Per-module
  shape breakdown across 18 files. Empirical migration projection
  via `mapanare.format.to_terse`: 3,675 → 737 across the 17
  modules (80% drop), 8 modules silence completely. 4-cluster
  migration plan locked. 27 cross-bootstrap fixture shapes
  enumerated (positive + negative).
  **Te.3.D.4.1 — C runtime helpers** ported from Python:
  `mn_ib_split_inline_colon`, `mn_ib_is_single_line_stmt_head`,
  `mn_ib_rewrite_inline_colon_body`,
  `mn_ib_normalize_fn_zero_arg_head`, `mn_ib_contains_byte_unquoted`.
  Pure additions to `runtime/native/mapanare_core.c`; mirror
  Python helpers byte-for-byte; cross-bootstrap test is the
  oracle.
  **Te.3.D.4.2 — `mn_ib_has_colon_blocks` extended** with
  prefix-hint check on 14 prefixes (`if /si /while /mien /for /
  cada /fn /pub /async /extern /else /sino /} else /} sino`)
  AND contains `:`. Mirrors Python `_SINGLE_LINE_PREFIX_HINT`.
  **Te.3.D.4.3 — `__mn_indent_to_braces` main loop extended**
  with single-line detection in both branches. Continuation:
  `} else: stmt` -> `} else { stmt }` inline, no indent_stack
  push. Non-continuation: `if x: stmt` -> `if x { stmt }`
  inline. The `'{' not in content` guard uses
  `mn_ib_contains_byte_unquoted` so lines like `if ch == "{":
  stmt` (the `{` is in a string literal in lexer.mn) still
  single-line-migrate.
  **Te.3.D.4.4 — `__mn_rewrite_arm_stmt_shorthand` C export.**
  New `MN_EXPORT MnString` mirrors Python: per-line shadow
  buffer, scan for `=>`, identify keyword
  (`return`/`da`/`break`/`sal`/`continue`/`sigue`/`pass`),
  word-boundary-after check, walk body to first depth-0 `,`/
  `}`/`//`/EOL, emit `{ <body rstripped> }`.
  **Te.3.D.4.5 — self-host wire-up.** `parser.mn::parse` calls
  `__mn_rewrite_arm_stmt_shorthand` after `__mn_indent_to_braces`.
  `main.mn::run_preprocess` mirrors so the cross-bootstrap test
  compares the full pipeline. Registration symmetric with
  `__mn_indent_to_braces` in `semantic.mn`, `lower.mn`, and
  `emit_llvm.mn`. Python bootstrap parity: `types.py`,
  `lower.py`, and `emit_llvm_text.py` (drop-glue tracking +
  Win64 routing matching v5.23.1 Mb.1).
  **Te.3.D.4.6 — cross-bootstrap test extended.** 27 new
  fixtures cover every accepted single-line stmt-block head
  (English + Spanish), every continuation, every arm-shorthand
  keyword, and the negative shapes (struct/enum inline,
  struct literal, namespace `::`, generic `<T: Ord>`,
  `if ch == "{":`). **243/243 passing byte-identically** Python
  vs C.
  **Te.3.D.5.1 — module-by-module migration.** All 17 modules
  in `mapanare/self/*.mn` migrated via `mnc fmt` in 4 clusters
  (10 + 3 + 3 + 1) with rebuild + goldens validation after
  each. Goldens **103/103** at every checkpoint.
  **Te.3.D.5.2 — `mnc_all.mn` regenerated** via
  `bash scripts/concat_self.sh`.
  **Te.3.D.5.3 — STRICT 3-stage fixed-point at the new
  baseline.** Old: 244,654 lines (v5.47.0 → v5.48.0 baseline).
  **New: 245,115 lines** (52-release strict streak from v5.7.1
  preserved at the new value; +461 lines reflect the v5.48.1
  self-host wiring). v5.48.x onward preserves from here.
  **Two v5.48.0 bugs surfaced and fixed mid-implementation
  (load-bearing).** (1) `_migrate_one_line_stmt_block`
  migrated `fn make() -> Point = Point { x }` (implicit-return
  expression with struct literal) to
  `fn make() -> Point: Point: x` — collapsing two distinct
  semantic levels. Fixed via `_has_standalone_eq` guard
  mirroring `count_user_brace_block_openers` Rule (b)'s `=`
  filter. (2) `_indent_to_braces`'s `'{' not in content` guard
  treated `{` inside string literals as a real `{`, preserving
  `if ch == "{": stmt` as colon form which the LALR parser
  then rejected. Fixed via `_mask_strings_chars` (Python) +
  `mn_ib_contains_byte_unquoted` (C) applying the guard against
  the masked shadow. Both bugs were caught by Phase 5's
  rebuild-after-each-cluster discipline.
  Aggregate state entering v5.48.2: **0 HIGH** / **3 MEDIUM**
  (macOS notarization carry from v5.33.0 Nu.2; Ai.1
  `_specialize_fn` carry from v5.40.0; **NEW** —
  `match_arm_open` + `one_line_arm_other` keep brace form and
  warn, v6.0 grammar revisit recommended) / **~7 LOW** (Lf.4
  variant-name collision split to v5.46.x; ergonomic refactor
  of v5.43.0 distributed-agent APIs; fs.mn `walk_dir`;
  websocket.mn `str(byte)`; if-expression colon syntax deferred
  to v6.0).
  **Te.3.D arc CLOSED at v5.48.1.**
  v5.48.x soak begins; v6.0 hard removal of brace parsing
  remains the v6.0 PLAN input it has been since v5.19.0;
  v5.48.1 makes the self-host first-party brace surface 78%
  smaller, so the v6.0 cut only needs to address the ~1,474
  residual + stdlib/examples migration. See
  `docs/roadmap/v5/v5.48.1/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.48.0** (ready, not tagged) — **Te.3.D — single-line
  colon blocks and match-arm statement shorthand (Python-side; C
  runtime + self-host migration shipped at v5.48.1).**
  Pulls the brace-removal runway forward from v6.0 because the
  language is still beta and there is no external compatibility
  burden worth preserving. The objective is not to keep `{}` as
  a special one-line exception. The objective is to make the
  compact brace forms migrate to a compact colon/direct-arm
  form: `if x { return y }` -> `if x: return y`,
  `Pat => { return x }` -> `Pat => return x`,
  `fn main() { print(x) }` -> `fn main(): print(x)`. Legacy
  brace source still parses in v5.48.0 with the v5.19.0
  deprecation warning unchanged; v6.0 may flip the warning to a
  hard error after v5.48.x soak. **Phase 0 audit
  (PRE_PHASE_AUDIT.md, mandatory)** measured 15,537 brace
  openers across 237 files and classified them: dominant
  pattern in `mapanare/self/` is `one_line_stmt` (2653) — guard
  clauses like `if total_size <= 16 { return false }` —
  followed by `one_line_arm_return` (293) — match-arm bodies
  like `IntLit(_) => { return "int_lit" }`. Together these are
  **82.5% of self-host brace openers** and are the shapes the
  formatter could not previously migrate without expanding to
  multi-line. v5.48.0 makes them migratable.
  **Te.3.D.1 — single-line statement-block colon syntax.**
  `_indent_to_braces` (Python) accepts `<head>: <body>` as a
  single-line block when `<head>` is a statement-block opener
  (`fn`, `if`, `si`, `while`, `mien`, `for`, `cada`; with
  optional `pub`/`async`/`extern` modifier prefixes; plus
  continuations `else`, `sino`, `else if`, `sino si`). The
  preprocessor rewrites `if x: stmt` to brace stream
  `if x { stmt }` inline (no indent_stack push). Comma-body
  openers (`struct`, `enum`, `match`, `tipo`, `modo`, `way`)
  and block-only openers (`trait`, `impl`, `agent`) are
  excluded because their bodies need multi-line grammar.
  **Te.3.D.2 — match-arm statement shorthand.**
  `_rewrite_arm_stmt_shorthand` runs after `_indent_to_braces`
  and rewrites `Pat => <stmt_kw> ...` arm bodies to brace form
  `Pat => { <stmt_kw> ... }` for keywords `return`, `da`,
  `break`, `sal`, `continue`, `sigue`, `pass`. AST-equivalent
  to writing the brace form directly because the rewrite
  happens before parsing.
  **Te.3.D.3 — formatter migration (`to_terse`).** Two new
  rewrite rules: `_migrate_one_line_stmt_block` rewrites
  `<head> { <body> }` to `<head>: <body>` for stmt-block heads;
  `_migrate_one_line_arm_body` rewrites `Pat => { <body> }` to
  `Pat => <body>` for any single-stmt body. Trailing commas on
  match-arm siblings are preserved across the rewrite.
  Expression-context braces (struct literals `Foo { ... }`,
  empty maps `#{}`, if-expression braces, FFI `extern "C" { ... }`
  blocks) are correctly NOT migrated.
  **Tests:** 81 new pytest cases in
  `tests/test_single_line_colon_blocks.py` covering colon-body
  splitter unit tests, positive parses for every supported head
  (English + Spanish), negative parses for excluded heads,
  arm-shorthand for every supported keyword, formatter
  migration with AST-preservation checks, idempotence, and
  expression-context passthroughs. All 1353 existing pytest
  cases still green; 11 golden corpus files automatically
  migrated by `mnc fmt tests/golden` to the new compact arm
  forms (IR equivalence preserved — `to_terse` does not change
  AST shape for stmt-keyword arm bodies; for expression-arm
  rewrites the AST shape changes from block-of-ExprStmt to
  expression-arm but runtime semantics are identical and the
  cross-style equivalence test in
  `tests/test_colon_blocks.py::_normalize` is extended to
  collapse these shapes for AST comparison).
  **Te.3.D.4 — bootstrap mirror (C runtime + self-host parser)
  shipped at v5.48.1.** v5.48.0 left the C runtime's
  `__mn_indent_to_braces` accepting only the v5.14.1 colon-block
  shapes; v5.48.1 brings it to byte-identity with the v5.48.0
  Python preprocessor and adds the new
  `__mn_rewrite_arm_stmt_shorthand` C export. v5.48.0 stage1
  continues to accept legacy brace forms unchanged.
  **Te.3.D.5 — internal source migration (`mapanare/self/*.mn`)
  shipped at v5.48.1.** Gated on Te.3.D.4 landing first
  (otherwise stage1 cannot reparse the migrated sources). At
  v5.48.0 the 6,826 brace openers across `mapanare/self/` remain
  in legacy form and continue to fire the v5.19.0 deprecation
  warning; v5.48.1 migrates them.
  **STRICT 3-stage fixed point preserved by construction at
  v5.47.0's 244,654 lines / 0 diff** (51-release strict streak
  from v5.7.1 baseline; **zero `mapanare/self/*.mn` source
  edits** in v5.48.0). Goldens **103/103** (no count change;
  11 files auto-migrated to v5.48.0 shorthand).
  Aggregate state entering v5.48.1: **0 HIGH** / **3 MEDIUM**
  (Te.3.D.4 bootstrap mirror split to v5.48.1; Te.3.D.5
  self-host source migration split to v5.48.1; macOS
  notarization carry from v5.33.0 Nu.2) / **~6 LOW** (Cl.2 +
  Cl.3 carry from v5.47.0; multi-stmt single-line arm grammar
  deferred to v6.0; if-expression colon syntax deferred to
  v6.0; Ai.1 `_specialize_fn` carry from v5.40.0).
  **Tensor closeout arc CLOSED at v5.45.0. Manifesto arc
  CLOSED at v5.43.0. Package-system runway CLOSED at v5.44.0.
  Lowerer-bug closeout CLOSED at v5.46.0. Pre-panel hygiene
  CLOSED at v5.47.0. v5 closeout panel CLOSED at v5.47.5.**
  v5.48.0 begins post-panel terseness work pulling brace-form
  removal forward into v5.48.x with v6.0 hard removal still
  the gate. See
  `docs/roadmap/v5/v5.48.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.47.5** (ready, not tagged) — **Cp.\* — end-of-v5 closeout
  panel.** Panel-only release. **Zero compiler edits. Zero
  runtime edits. Zero `mapanare/self/*.mn` source edits.**
  Strict 3-stage fixed point preserved by construction at
  v5.47.0's **244,654 lines / 0 diff** (50-release strict
  streak from v5.7.1 baseline). Goldens **103/103**. Decides
  three things at the structural pause before v6.0: (1) has v5
  delivered? (2) is v6.0 ready to start? (3) what carries
  forward?
  **Aggregate panel score: 9.76 / 10. Decision: Option A.**
  7-reviewer panel (Rattler 9.85 PASS / Viper 9.85 PASS /
  Anaconda 9.75 PASS / Cobra 9.75 PASS / Coral 9.65 PASS WITH
  NOTES / Boa 9.65 PASS WITH NOTES / Mamba 9.85 PASS) reviewed
  v5.31.0 → v5.47.0 (17 substantive releases plus v5.39.1–v5.39.7
  sub-releases). Spread 0.20 (well below 0.5 follow-up trigger).
  **0 HIGH / 6 dedup MEDIUM / 31 LOW** — all MEDIUMs are either
  v6.0 PLAN inputs (PRE_PHASE_AUDIT promotion, tensor surface
  unification, distributed supervision orchestration, registry
  package signing, STRICT carve-out, perf baseline) or v5.47.x
  patch candidates (CARRY_FORWARD.md drift, localized README
  staleness). Second consecutive Option A under the v5-gate
  framework; second consecutive panel above the v5.7.1 / v5.8.0
  9.66 ceiling (+0.04 vs v5.28.0 RE-PANEL's 9.72 across +9
  releases of scope).
  **v6.0 green-lit** conditional on 9 v6.0 PLAN inputs being
  explicit (borrow checker / multi-level alias analysis; hard
  removal of `{}`; STRICT 3-stage fixed-point gate carve-out;
  tensor surface unification; distributed-supervision
  orchestration; registry-side package signing; `_specialize_fn`
  body-walk fix; PRE_PHASE_AUDIT.md mandatory at every v6.x
  release; convergent-recommendation pattern explicit).
  **v5.47.x patches recommended pre-v6.0:** v5.47.1 (already
  named: Cl.2 agent stdlib ergonomic refactor + Cl.3 fs.mn
  walk_dir IR codegen); v5.47.2 (proposed: 5 docs/process
  polish items — CARRY_FORWARD.md refresh, KNOWN_FAILURES.md
  ledger, localized README refresh, docs/stdlib/INDEX.md,
  manifesto.md As.\*+Da.\* section).
  **Cadence-gap acknowledgment.** v5.47.5 closes 19 minor
  versions late on purpose. Per project memory + v5.28.0
  directive: panels run at the end of an arc, not in the
  middle. v5.45.0's original panel slot was deferred so
  v5.45.0 (tensor closeout) + v5.46.0 (lowerer-bug closeout)
  + v5.47.0 (pre-panel hygiene) could close three long-
  standing debts before the panel audited ecosystem readiness
  for v6.0. `check_cadence.py` is informational REMINDER per
  v5.33.2 Cd.\* exactly to support this shape; reviewers did
  not dock for the gap.
  **v5 series state:** Foundation arc CLOSED. Stdlib gap-close
  arc CLOSED. Manifesto arc CLOSED. Tensor closeout arc CLOSED.
  Package-system runway CLOSED. v5.43.0 lowerer-bug closeout
  CLOSED at v5.46.0. Pre-panel hygiene cleanup CLOSED at
  v5.47.0. Mb.\* arc CLOSED (since v5.29.0). Pv.\* arc CLOSED
  (since v5.32.0/v5.33.0). Js.4 arc CLOSED (v5.39.7).
  Terseness arc CLOSED (since v5.27.0).
  Source delta: 8 panel deliverable files
  (`PRE_PANEL_AUDIT.md` + 7 `<reviewer>/findings.md` +
  `V5_DECISION.md` + `V5_TO_V6_CARRY.md` + `V5_RETRO.md` +
  `README.md`); v5 closeout summary paragraph replacing
  v5.31.0–v5.45.0 explicit ledger entries (Cp.6 prune); final
  paragraph appended to `docs/roadmap/v5/CLOSEOUT_ARC.md`
  (Cp.7); CHANGELOG `### Added` entry for Cp.1..Cp.8 panel
  deliverables; SPEC.md header re-sync to v5.47.5 cut with
  closeout-panel sync block; this CLAUDE.md release-notes
  entry; mechanical bump_version.py edits. **v6.0 PLAN
  drafting begins** at `docs/roadmap/v6/PLAN.md` per
  V5_TO_V6_CARRY.md inputs. See
  `.reviews/v5.47.5/{PRE_PANEL_AUDIT.md, V5_DECISION.md,
  V5_TO_V6_CARRY.md, V5_RETRO.md, README.md, <reviewer>/findings.md}`
  and `docs/roadmap/v5/v5.47.5/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.47.0** (ready, not tagged) — **Cl.\* — pre-panel hygiene
  cleanup; v5.47.5 closeout panel runway begins.** Drains every
  closeable LOW-tier carry before the v5.47.5 closeout panel sees
  the docket. Mirrors the v5.28.0 hygiene-before-panel precedent
  (the +0.31 panel recovery there came from H.\* hygiene closures
  landing ahead of panel cut). **Cl.1 (Lf.4) — variant-name
  collision** closed across both Python bootstrap
  (`mapanare/semantic.py` `_variant_alternatives` multimap +
  `_check_let` annotation-as-`_expected_type` context;
  `_check_call` and Identifier-resolution disambiguation when the
  name has multiple alternatives) AND self-host stage1
  (`mapanare/self/semantic.mn` `expected_type` field on `SemState`
  + `scope_has_variant_for_enum` post-inference helper walking
  `Scope.symbols` which appends rather than replaces;
  `mapanare/self/lower.mn` `expected_enum_name` field on
  `LowerState` + `enum_has_variant` lookup; `lower_let` sets the
  hint when type_ann is TK_ENUM; `lower_call_by_name` enum-variant
  branch prefers the hint over `enum_name_for_variant`'s
  first-match result when the hinted enum has the variant). Phase
  0 audit verified self-host stage1 had the bug too (different
  from v5.46.0 where self-host already had Eu.2 fix); Cl.5 mirror
  is non-trivial (~80 LOC across 4 files). **Cl.4 —
  `stdlib/net/websocket.mn` `str(byte)` decimal-stringification
  cleanup** — 11 sites in `read_frame` / `build_send_frame` /
  chunked-send replaced with `__mn_str_chr` (v5.43.0 Da.0 C
  runtime export). **Two Phase-0-driven scope splits
  (load-bearing for honest release framing):** (1) **Cl.2 —
  agent stdlib ergonomic refactor SPLIT to v5.47.1** — the
  v5.43.0 distributed-agent flat-tuple shape across
  `stdlib/agent/{url,remote,node,supervision}.mn` is structurally
  unblocked by Cl.1 but the refactor is ~400 LOC across
  public-API surfaces + ~50 internal callers + test updates;
  warrants dedicated focus; (2) **Cl.3 — fs.mn walk_dir IR
  codegen SPLIT to v5.47.1** — Phase 0 verified the v5.40.0 carry
  is still open (clang rejects `extractvalue ptr ... 0` then
  `zext ptr to i64`); receiver-side wrong-shape Result aggregate
  bug, different fix-site from v5.46.0's constructor-side
  wrap-shape default. **STRICT 3-stage fixed point preserved at
  244,654 lines / 0 diff** (50-release strict streak from v5.7.1;
  +889 lines vs v5.46.0). Goldens **103/103** (102 + new
  `103_variant_name_collision.mn`). Falsifiability locked per
  layer in `tests/llvm/test_lowerer_fixes.py` (8/8 GREEN;
  +3 new Lf.4 cases). Source delta: ~80 LOC compiler + ~30 LOC
  stdlib + ~85 LOC golden + ~80 LOC test extension + closeout
  artifacts. Aggregate state entering v5.47.5: **0 HIGH** /
  **2 MEDIUM** (Cl.2 + Cl.3 splits to v5.47.1; macOS
  notarization carry from v5.33.0 Nu.2) / ~6 LOW. **Tensor
  closeout arc CLOSED at v5.45.0. Manifesto arc CLOSED at
  v5.43.0. Package-system runway CLOSED at v5.44.0. v5.43.0
  lowerer-bug closeout CLOSED at v5.46.0. Pre-panel hygiene
  cleanup CLOSED at v5.47.0** (with two scope splits to v5.47.1).
  v5.47.5 panel reviews a clean docket. See
  `docs/roadmap/v5/v5.47.0/{PLAN.md, PROMPT.md, PRE_PHASE_AUDIT.md,
  SESSION_REPORT.md}`.

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

- **v5.31.0 → v5.45.0 — closeout summary** (pruned at v5.47.5
  Cp.6; full release notes preserved in
  `docs/roadmap/v5/<release>/SESSION_REPORT.md` per release).
  Six structural sub-arcs shipped across these 15 releases:
  **Foundation arc** (v5.31.0 Bn.\* banner hotfix; v5.32.0 Nw.\*
  Windows native `mnc.exe`; v5.33.0 Nu.\* Linux x86_64 + macOS
  arm64 native `mnc`; v5.33.1 Hd.\* SPEC header re-sync;
  v5.33.2 Cd.\* cadence gate demoted to informational); **Stdlib
  gap-close arc** (v5.34.0 Dt.\* date/time — first-class types
  + 6 new C exports; v5.35.0 Sq.\* first-class sqlite3 driver +
  Tn.1 closure via Sq.0; v5.36.0 Js.\* JSON RFC 8259 strictness
  + typed serde + 2 emitter-bug fixes; v5.37.0 Ht.\* HTTP App /
  router / middleware / streaming encoders; v5.38.0 Re.\* regex
  Regex-first API + Captures + named groups; v5.39.0 Cr.\*
  crypto baseline — hashing additions + streaming digest +
  HMAC-SHA512 + Cr.0 emitter shortcut bypass fix); **Js.4
  staged closure** (v5.39.1 → v5.39.7 — typed-serde round-trip
  closure across all TypeKind branches in 7 sub-releases);
  **Manifesto arc** (v5.40.0 Ai.\* `ask` runtime adapter;
  v5.41.0 Ts.1 tensor.reshape on LLVM; v5.42.0 As.\* agent
  supervision trees + 4 new C runtime exports; v5.43.0 Da.\*
  distributed agents v0 — TCP/TLS wire format v1, HMAC-SHA256
  signed, 100MB DoS guard, 1000-iteration network fuzz);
  **Tensor closeout** (v5.45.0 Ts.2 + Ts.3 — mutable views,
  stepped slices, `mapanare_tensor_t` 40→64 byte append-only
  extension); **Package-system runway** (v5.44.0 Ps.\*
  package-aware imports + lockfile/install/publish wired into
  resolver; v5.44.1 Ps.11+Ps.12 scripts parity + gitignore
  template).
  Every release in the arc shipped with PRE_PHASE_AUDIT.md
  catching PROMPT/PLAN-vs-HEAD-state mismatches before
  implementation began (10+ load-bearing surfaces across the
  arc). STRICT 3-stage fixed-point preserved at every release
  (50-release strict streak from the v5.7.1 baseline at
  v5.47.0 HEAD: 244,654 lines / 0 diff). Goldens trajectory
  95 → 96 (v5.41.0) → 99 (v5.45.0) → 102 (v5.46.0) → 103
  (v5.47.0). Six new stdlib cookbooks shipped under
  `docs/stdlib/` (time, sql, json, http, regex, crypto, ai,
  agent — 8 total). For per-release details see
  `docs/roadmap/v5/v5.31.0/SESSION_REPORT.md` through
  `docs/roadmap/v5/v5.45.0/SESSION_REPORT.md` and CHANGELOG
  entries `## [5.31.0]` through `## [5.45.0]`.

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

This project is indexed by GitNexus as **Mapanare** (32815 symbols, 68439 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
