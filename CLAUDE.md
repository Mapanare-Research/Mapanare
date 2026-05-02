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

- **v5.24.1** (ready, not tagged) — **Wd.\* — wider docs cleanup
  (arc closeout).** **Final** release in the v5.23–v5.24 recovery
  arc. Closes the 3-consecutive-panel manifesto drift (Coral M2,
  v5.7.1 / v5.11.0 / v5.22.0), the SPEC corpus 72%-brace-style
  state against §4.0's colon-canonical declaration (Coral M3),
  five Coral L1–L5 polish items, and codifies the Bo.27 audit
  cross-reference column convention for the v5.27.0 audit. **Zero
  compiler edits. Zero runtime edits. Zero `mapanare/self/*.mn`
  source edits.** Strict 3-stage fixed point preserved by
  construction at **239,835 lines / 0 diff** (19-release strict
  streak; same line count as v5.24.0 because no `.mn` source
  changed). Goldens **95/95**. **Wd.1**: `docs/manifesto.md:31`
  rewritten to "Indented blocks (with a brace-form legacy through
  v6.0)" per Coral M2's verbatim suggested fix — the manifesto's
  first-impression syntax description now matches the Te.3
  soft-deprecation posture (v5.19.0). **Wd.2**: `docs/SPEC.md`
  migrated from 26 brace-style block-openers to 0 (the 2 remaining
  brace openers live inside the §4.0 "Brace style" demo block,
  intentionally preserved with a `<!-- preserve-brace -->` marker).
  New `to_terse_markdown` function in `mapanare/format.py` (~95
  LOC) walks markdown source line-by-line, runs `to_terse` on each
  `` ```mn `` fence body, and honors the `<!-- preserve-brace -->`
  HTML comment as opt-out. `mapanare/cli.py::cmd_fmt` learned a
  `.md` / `.markdown` dispatch path requiring explicit
  `--to-terse` (no auto-migration default on markdown). New
  `tests/test_format.py::TestMarkdownRewriter` (8 cases). The
  migration also surfaced a latent `to_terse` bug rewriting empty
  `#{}` map literals as `#:` plus indented `pass`; held for
  v5.25.0+ as a scope-creep guard with manual revert at SPEC §17.1.
  **Wd.3**: SPEC §27.3 gained a "Worked example (v5.19.0 → v6.0)"
  paragraph pointing at Te.3 as the canonical worked example of
  the deprecation cycle in v5; cross-links to §4.0 for migration
  commands. **Wd.4**: SPEC §4.0 broken-promise wording tightened
  to acknowledge the v5.14.0 forward promise more explicitly and
  link the v6.0 rescope to the parser ambiguity that hard removal
  eliminates. **Wd.5**: SPEC §4.0 Te.3 status block gained two
  example invocations of `mnc fmt` (auto-migrate +
  `--keep-braces`). **Wd.6**: SPEC §7.4 (Trait Bounds on Generics)
  gained a 10-line worked example — `Comparable` trait + `impl
  Comparable for Score` + generic `min<T: Comparable>(a: T, b: T)
  -> T`. Phase 0 surfaced that `impl <Trait> for Int` doesn't
  compile (primitives aren't impl targets); shipped shape uses a
  user-defined `Score` struct mirroring §7.2 convention. Runnable
  file at `examples/struct_ergo/generic_trait.mn`. **Wd.7**:
  examples directory micro-organization. `chained_cmp.mn` →
  `examples/terseness/chained_cmp.mn`; `examples/struct_ergo/`
  seeded by Wd.6's example. Async demos stay top-level
  (`docs/cookbook/async.md` + `docs/guides/async.md` cite by
  path). New `examples/INDEX.md`. `mapanare/format.py` docstring
  reference updated; historical CHANGELOG / SESSION_REPORT
  references preserved. **Wd.8**: new
  `.reviews/PANEL_AUDIT_TEMPLATE.md` codifying the audit
  cross-reference convention per Boa Bo.27 — every `H.*`
  hygiene-release finding must bind to a prior-panel finding ID
  (or "(none — fresh)"); every prior-panel HIGH/MEDIUM either
  appears in the `H.*` table or in a "deferred to <future
  release>" section. Closes the v5.22.0 Bo.18r failure mode
  (3-panel persistence: hygiene closures patched the audit's
  cited line, walked past the panel-flagged paragraph). Convention
  applies starting v5.27.0. `.reviews/REVIEW_CADENCE.md` updated.
  **Arc closure**: v5.23–v5.24 recovery arc closes at v5.24.1
  HEAD with **0 HIGH / 0 MEDIUM / ~5 LOW** open in the docket.
  Five releases shipped across the arc (RC.\* + Mb.\* + Te.3.B
  + Hy.\* + Wd.\*). v5.27.0 panel inherits zero structural debt;
  targeted at **9.55–9.65** aggregate (recovery from v5.22.0's
  9.41 floor). See `docs/roadmap/v5/v5.24.1/SESSION_REPORT.md`
  and `PLAN.md`.

- **v5.24.0** (ready, not tagged) — **Hy.\* — structural hygiene
  gates.** Fourth release in the v5.23–v5.24 recovery arc. The
  "this should never have slipped" infrastructure release: closes
  the H.\* / Bo.\* drift class **structurally** (vs the closure-
  by-hygiene-release pattern that capped the v5.7.1 / v5.11.0 /
  v5.22.0 panel aggregates at 9.55–9.66). **Zero compiler edits.
  Zero runtime edits. Zero `mapanare/self/*.mn` source edits.**
  Strict 3-stage fixed point preserved by construction at **239,835
  lines / 0 diff** (18-release strict streak; same line count as
  v5.23.2). Goldens **95/95**. **Hy.1**: new `make ci-gates` target
  running 8 sub-gates (`silent_skips`, `changelog_honesty`,
  `workflow_shapes`, `docs_drift`, `hollow_features`,
  `struct_registry`, plus the new `doc_freshness` and `cadence`)
  — pre-release checklist shrinks to "expect zero violations."
  Eliminates the wired-but-unchecked failure mode that produced
  Reg.1 / hollow-feature gate / docs-drift gate silent failures
  across v5.17.0 → v5.22.0 (Anaconda's load-bearing −1.30 hit).
  **Hy.2**: new `scripts/check_doc_freshness.py` (~190 LOC) with
  5 MVP checks — version-badge sync (en/es/pt/zh-CN), goldens-
  badge sync, multiple distinct exact-line-count claims in
  README.md, body-goldens consistency, SPEC.md header version
  (tolerates ≤2 minor lag). Wired into ci.yml parallel to the
  struct-registry gate. Wider scope (every prose claim about every
  metric) is explicitly v6.0+. New `tests/test_doc_freshness.py`
  (7 cases). **Hy.3**: new `scripts/check_cadence.py` (~90 LOC)
  per `.reviews/REVIEW_CADENCE.md` — fires OVERDUE at lag ≥5
  minor versions since last panel. Wired into ci.yml as a
  `cadence-check` job with `continue-on-error: true` (warn-only
  at PR time; hard signal at pre-release via `make ci-gates`). At
  v5.24.0 we are 2 minors past v5.22.0; gate exits 0. Fires hard
  at v5.27.0. New `tests/test_cadence.py` (6 cases). **Hy.4**
  (Cobra 3rd-cycle): `scripts/build_from_seed.sh:159` magic
  `>= 45` replaced with self-evident formula
  `EXPECTED_PASS=$((TOTAL_GOLDENS - EXPECTED_SEED_FAILS))` where
  `EXPECTED_SEED_FAILS=20` (named: `Te.5/Te.6/comprehensions/
  complex closures predate the v5.10.0-vintage seed`). **Hy.5**
  (Pk.1.A, 11-release carry from v5.10.0): two new jobs
  `linux-tarball-smoke` and `macos-tarball-smoke` in
  `.github/workflows/publish.yml`, parallel to the existing
  `windows-sdk-smoke`. Each downloads the published versioned
  tarball, extracts, runs `mapanare --version` + `mapanare
  emit-llvm hello.mn -o hello.ll`, asserts non-empty output.
  `checksums` job `needs:` extended. **Hy.6** (Pe.1 reframe):
  `.reviews/CARRY_FORWARD.md` Pe.1 row updated per Mamba's v5.22.0
  #2 — "curve flattening" framing retired; growth is proportional
  to bootstrap-side AST additions across the Te.\* arc, not a v6.0
  budget concern (30+ releases at +0.5%/release before doubling).
  **Carry-forward delta**: Hy.1 / Hy.2 / Hy.3 (3 MEDIUM) + Hy.4 /
  Hy.5 / Hy.6 (3 LOW) closed. v5.23–v5.24 arc has now closed every
  panel-flagged HIGH and 4 of 8 panel MEDIUMs in four releases
  (RC.\* + Mb.\* + Te.3.B + Hy.\*). **Out of scope** (held): Wd.\*
  (manifesto M2 + SPEC corpus M3 + Coral L1–L5 + TR1) — v5.24.1.
  See `docs/roadmap/v5/v5.24.0/SESSION_REPORT.md` and `PLAN.md`.

- **v5.23.2** (ready, not tagged) — **Te.3.B — bootstrap brace-
  deprecation mirror.** Third release in the v5.23–v5.24 recovery
  arc. Closes the **Te.3 asymmetric closure** flagged independently
  by 3 v5.22.0 panel reviewers (Coral M1 + Anaconda §3 + Rattler
  #1): the Python detector missed single-line `{...}` shapes (line-
  based, only counted lines whose trailing non-comment char was
  `{`); native `mnc-stage1` had zero brace-deprecation logic at
  all. v5.23.2 fixes both at the same algorithm layer with a single
  source of truth (C-runtime export). **Strict 3-stage fixed point
  preserved at 239,835 lines / 0 diff** (17-release strict streak;
  +350 lines vs v5.23.1's 239,485, expected from the new C-extern
  call sites). Goldens **95/95**. **Te.3.B.1**: Python detector
  rewritten as a per-line character-walker over masked code
  (strings / chars / `//` comments → spaces) with three rules —
  (a) `{` is last non-WS on line, (b) block keyword precedes `{`
  with no standalone `=` between latest keyword and `{` (excludes
  implicit-return shapes like
  `fn make() -> Point = Point { x }`; comparison/compound ops `==`
  / `!=` / `<=` / `>=` / `=>` / `+=` etc. don't qualify), (c) `=>`
  immediately precedes `{` (match-arm / closure body). Catches
  single-line `fn main() { print("hi") }` (the gap); does NOT
  false-positive on canonical struct literals like
  `Point { x: 1, y: 2 }` in colon-style code (sweep across goldens
  06/81/82/84/85 confirms count=0). Synthetic-filename filter
  (`<...>`) suppresses the warning for the `_parse_interp_expr`
  recursive `parse(filename="<interp>")` call that synthesizes a
  brace-style wrapper for every interpolated expression — without
  this filter the warning would fire on every `"${expr}"` in any
  user file. **Te.3.B.2**: same algorithm ported to C runtime as
  `__mn_count_user_brace_block_openers` +
  `__mn_emit_brace_deprecation_warning`. Same C-routing rationale
  as v5.14.1 B.5 `__mn_indent_to_braces` — single source of truth,
  byte-identity by construction, sidesteps any bootstrap-lower
  string-walking pathologies (PLAN initially proposed `.mn` port;
  C is strictly better here). `mapanare/self/parser.mn::parse`
  calls both before `__mn_indent_to_braces`;
  `MAPANARE_NO_BRACE_WARNING=1` opt-out honored via `getenv()` in
  C. Bootstrap wiring across `semantic.mn` /
  `lower.mn` / `emit_llvm.mn` / `parser.mn` (~30 LOC). **Te.3.B.3**:
  new `tests/bootstrap/test_brace_deprecation_mirror.py` (11 cases
  — 10 parameterized covering single-line, multi-line, escaped
  brace, brace in string, brace in comment, `#{` map literal,
  `${...}` interpolation, mixed colon + brace, no braces, multiple
  + 1 opt-out) is the byte-identity contract. 11/11 PASS.
  **Te.3.B.4**: `.reviews/v5.22.0/PRE_PANEL_AUDIT.md` "Pre-flight
  commands" updated with v5.23.2-update note + native parallel
  commands documenting the gap closure for the v5.27.0 panel.
  **Te.3.B.5**: Bb.\* seed refresh required —
  `bootstrap/seed/linux-x86_64/mnc` + `.sha256` refreshed from
  v5.23.2 HEAD `mapanare/self/mnc-stage1` because the v5.10.0-
  vintage seed's `is_builtin_function` rejects the new exports.
  Same shape as v5.17.0 Sh.E precedent. Post-refresh
  `bash scripts/build_from_seed.sh` succeeds. **Carry-forward
  delta**: Te.3 hollow / asymmetric closure CLOSED at v5.23.2 (1
  MEDIUM × 3 reviewer cycles). Coral L3 (`mnc fmt --keep-braces`
  polish for single-line shapes) and self-host source migration to
  colon-only (mnc_all.mn still emits 3,116-occurrence warning per
  parse, all legitimate `=> { ... }` match-arm bodies in `ast.mn` /
  `lower.mn`) remain held for v5.24.x. See
  `docs/roadmap/v5/v5.23.2/SESSION_REPORT.md` and `PLAN.md`.

- **v5.23.1** (ready, not tagged) — **Mb.\* — memory hygiene.**
  Second release in the v5.23–v5.24 recovery arc. Closes Viper
  **V.9** (the v5.14.1 `__mn_indent_to_braces` MnString lifecycle
  leak; 30 bytes per colon-syntax compile in stage1; bounded to
  single-shot in `mnc-stage1` but unbounded in long-lived embedded
  contexts), **3 NEW Te.5 ASan leaks** on
  `tests/golden/{88_if_let, 90_while_let, 91_let_else}.mn` (1 leak
  / 8 bytes each, surfaced post-v5.22.0 panel via the
  LeakSanitizer CI workflow), and **V.6 / V.7 / V.8** — Viper LOW,
  3rd cycle each (DX.4 walker carries). Plus prevention
  infrastructure: two new CI gates so future lifecycle /
  cache-walker bugs surface at PR time. **Strict 3-stage fixed
  point preserved at 239,485 lines / 0 diff** (16-release strict
  streak; +260 lines vs v5.23.0's 239,225, expected from the new
  `box_track` allocas at every `Some(x)` site introduced by Mb.2).
  Goldens **95/95**. **Mb.1**: V.9 root cause was NOT the missing
  tracked-output annotation Viper diagnosed — adding the dedicated
  handler in `emit_llvm_text.py::_do_call` and calling
  `_track_string` was insufficient; Python's `_do_call` applies a
  blanket-move at every user-fn arg site
  (`emit_llvm_text.py:4156-4178`), zeroing the
  `_str_slots[name]` tracking slot at `tokenize(preprocessed,
  filename)`. Self-host `emit_llvm.mn` doesn't have this
  blanket-move (relies on explicit Move from lowerer); stage2/3
  are leak-clean by construction. Surgical fix in Python:
  `_last_tracked_str_slot = None` before `_put` so the slot lives
  in `_local_strings` (drop-glue) but not in `_str_slots`
  (blanket-move zero). Defensive: `__mn_indent_to_braces` added
  to `is_string_returning_builtin` in self-host emitter.
  **Mb.2**: Te.5 leak root cause was NOT the let-else / while-let
  / if-let desugaring as the plan suspected — it's
  `mapanare/self/emit_llvm.mn::emit_wrap_some` (line 3599)
  heap-allocating the Some payload via `malloc(sizeof(val))` for
  the `{i1, ptr}` Option representation but never calling
  `emit_track_boxed`. Single-line fix:
  `s = emit_track_boxed(s, ea)` after the malloc. Closes 3 NEW
  Te.5 leaks AND improves baseline 17_option from 2/16 → 1/8.
  Baseline TSV refreshed at
  `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`.
  **Mb.3**: new `sanitizer-mnc-stage1` job in
  `.github/workflows/sanitizers.yml` — runs valgrind on goldens
  86/88/90/91; greps for `__mn_indent_to_braces` in any leak
  chain. Cannot use `--error-exitcode=1` directly (mnc-stage1
  has known pre-existing single-shot leaks). **Mb.4 (V.6, 3rd
  cycle)**: `MN_DIR_WALK_MAX_DEPTH` (4096) cap parameter on
  `mn_dir_walk_size_` / `mn_dir_walk_count_` /
  `mn_dir_remove_recursive_`. Pragmatic alternative to the plan's
  full iterative work-queue rewrite — bounds C stack with minimal
  LOC churn. **Mb.5 (V.7, 3rd cycle)**: Win32 walker branches now
  skip `FILE_ATTRIBUTE_REPARSE_POINT` entries (junctions /
  symlinks / mount points); POSIX side switched `stat()` →
  `lstat()` in count/size paths for symmetric symlink-skip.
  Verified locally: a fixture with a symlink pointing back into
  the tree no longer double-counts files. **Mb.6 (V.8, 3rd
  cycle)**: new `sanitizer-cache-walkers` job — populates
  `.mnc_cache` fixture (3 levels + non-loop symlink) and runs
  `mnc version` / `mnc cache stats` / `mnc cache clean` under
  valgrind. Closes the v5.10.0+ delta sanitizer-coverage gap.
  **Mb.7 deferred to v5.24.0**: investigation found the 9
  LINK_FAIL goldens (47, 48, 49, 51, 55-59) trip an i64/i1
  tag-emit bug in self-host emit_llvm.mn — unrelated to PIC reloc,
  unrelated to memory hygiene. **Carry-forward delta**:
  V.9 + V.6 + V.7 + V.8 + 3 NEW Te.5 leaks closed; 17_option
  improved 2/16 → 1/8. See
  `docs/roadmap/v5/v5.23.1/SESSION_REPORT.md` and `PLAN.md`.

- **v5.23.0** (ready, not tagged) — **RC.\* — CI recovery + HIGH
  closures.** First release in the v5.23–v5.24 recovery arc.
  Closes the **8 silently-failing CI workflows** at v5.22.0 HEAD
  (4 panel-flagged, 4 NEW), the v5.22.0 panel's **4 HIGH** docket
  items, **4 MEDIUM**, and **6 LOW** — 15 items in one mechanical
  session. **Strict 3-stage fixed point preserved at 239,225
  lines / 0-line diff** (15-release strict streak; line count
  grew from v5.22.0's documented 238,086 because `mnc_all.mn` was
  stale at v5.22.0 — re-concatenation surfaced the v5.21.0 Te.6
  chain-compare references that weren't being tested). Goldens
  **95/95**. **HIGH**: **RC.1 Reg.1** —
  `scripts/check_struct_registry.py` regex extended to accept
  colon-form (`[\{:]`) plus indent-tracking body parser; surfaced
  5 real latent drifts all in `LowerState`
  (`comp_type_hint`/v5.15.1, `struct_update_counter`/v5.20.1,
  `chain_compare_counter`/v5.21.0). v5.17.0 Sh.\*'s colon-syntax
  migration silently disabled the gate for 5 releases. Drift was
  cosmetic for runtime correctness (`find_struct_entry` searches
  end-first; `register_mir_struct`'s real registration shadows
  the stale internal one), but the gate's contract is sync.
  Both registry sites in `mapanare/self/emit_llvm.mn` updated to
  20 fields — only `mapanare/self/*.mn` edit in v5.23.0
  (data-only, 3 strings × 2 list literals; zero compiler logic).
  **RC.2 Bo.18r** (3rd consecutive panel) — `README.md:188-192`
  rewritten with rounded `239k` / 14-release / 5,800+ framing
  (self-immunization; v5.9.2 Dn.1 pattern). Closes Bo.19 + Bo.20.
  **RC.3 Bo.25** — goldens badge `66/66` → `95/95` across all 4
  README locales; `scripts/bump_version.py` extended with
  `_GOLDENS_BADGE_RE` + `_count_goldens()` + per-locale sweep
  (parallel to version-badge sweep); new
  `tests/test_bump_version.py` 5/5. **MEDIUM**: **RC.4** added
  `CompClause` + `FieldPattern` to
  `_AST_INFRASTRUCTURE` in `check_no_hollow_features.py`. **RC.5**
  fixed `docs/SPEC.md:1456` (`fn id(y) = y` → `fn id<T>(y: T) -> T = y`).
  **RC.6** force-added `.reviews/v5.22.0/prompt.md` (10/11 panel
  artifacts already tracked from v5.22.0 setup). **RC.7 Docker
  Smoke** — root cause was `runtime/native/build_native.py`
  produces only `.so` not `libmapanare_rt.a`; added "Build runtime
  archive" step (`make build-rt`) to both `ci.yml` and
  `publish-docker.yml`. **RC.8 macOS/iOS** — root cause was
  `cli.py` looks for `libmapanare_rt.a` by exact name but macOS
  workflow built ad-hoc `libmapanare.a`; added `make build-rt`
  step (already has Darwin handling for `mapanare_metal.m`).
  **RC.9 stage2 ir_doctor** — v5.21.0 Te.6 added the first
  cross-module reference (`lower.mn` → `parser.mn::new_match_arm`);
  per-module compile path now detects "Undefined function"
  failures and retries against `mnc_all.mn`, marking modules as
  `OK (via mnc_all)`. **11/11** stage2 modules valid post-fix.
  **LOW**: **RC.10** added `__mn_indent_to_braces` decl to
  `mapanare_core.h`. **RC.11** wrote v5.19.0 SESSION_REPORT.md
  retroactively (Te.3.A/B/C/D/E + scope-split rationale).
  **RC.12** Sh.\* baseline labeling corrected to dual-baseline
  framing. **RC.13** test_indent_preprocessor count refresh
  142 → 201. **RC.14** Bo.22 README `mapanare *` → `mnc *`
  (5 substitutions + alias note). **RC.15** Bo.26 added 4 guide
  links from README. **Carry-forward delta**: 4 HIGH/8 MEDIUM/~12
  LOW → **0 HIGH/4 MEDIUM/~7 LOW**. **Out of scope** (held):
  V.9, Te.5 leaks (v5.23.1); Te.3 hollow-surface (v5.23.2);
  `make ci-gates` + `check_doc_freshness.py` + cadence gate +
  Pk.1.A (v5.24.0); Manifesto M2 + SPEC corpus M3 + Coral L1-L5
  (v5.24.1). See
  `docs/roadmap/v5/v5.23.0/SESSION_REPORT.md`, `PLAN.md`, and
  `docs/roadmap/v5/RECOVERY_ARC_v5.23-v5.24.md`.

- **v5.22.0** (ready, not tagged) — **RE-PANEL — terseness-arc
  closeout.** Panel-only release; the release identity is the
  panel itself. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` edits.** Strict 3-stage fixed
  point preserved by construction at 238,086 lines / 0-line
  diff (v5.9.0 milestone, held through 13 consecutive
  releases — longest streak in project history; 2.6× the
  v5.11.0 streak). Goldens **95/95**. Same posture as v5.8.0
  (which graded v5.3.1 → v5.7.1 at 9.66 — project ceiling).
  **Aggregate: 9.41 / 10. Decision: Option A** (point-release
  health gate clears; no recovery cycle opened) — third
  consecutive Option A under the v5-gate mechanical rule
  (v5.7.1: 9.66; v5.11.0: 9.62; v5.22.0: 9.41). Δ vs v5.11.0:
  **−0.21** — largest single-arc regression since v5.0.0,
  driven entirely by process-discipline debt that the H.\*
  hygiene pattern did not catch. All 7 reviewers PASS or
  PASS WITH NOTES; **0 NEEDS WORK**. **Per-reviewer**:
  Rattler 9.85 (±0.0), Viper 9.7 (−0.20), Anaconda 8.4
  (**−1.30**, load-bearing regression), Cobra 9.55 (−0.15),
  Coral 9.55 (+0.05), Boa 9.0 (+0.10), Mamba 9.85 (+0.05).
  **5 v5.11.0 docket items closed**: Bo.21 version badges
  HIGH (v5.21.1 H.1), Bo.17r localized READMEs MEDIUM ~80%
  (v5.21.1 H.3), Coral SPEC re-sync MEDIUM (v5.21.1 H.2/H.5),
  Mc.\* docket MEDIUM (v5.18.0), Cobra per-PR fixed-point
  gate (mea culpa — was always wired at v4.29.0). **11 still
  open** (Pk.1.A 11-release carry; `>=45` magic 3rd ask;
  V.6/V.7/V.8 3rd cycle; **Bo.18r 3rd consecutive panel —
  escalated to HIGH**; Bo.22 2nd panel; etc.). **2 NEW HIGH**:
  **Reg.1** (Anaconda + Cobra) `check_struct_registry.py`
  regex hard-codes brace headers; inert since v5.17.0 Sh.\*;
  23 violations at HEAD — 5 releases of silent registry
  blindness during the largest feature-velocity arc in v5
  history. **Bo.25** (Boa) goldens badge `66/66` across all
  4 READMEs while body says `95/95`. **8 NEW MEDIUM**: V.9
  (`__mn_indent_to_braces` MnString lifecycle leak,
  unbounded if embedded), Te.3 hollow / asymmetric closure
  (Coral M1 + Anaconda §3 + Rattler #1, three independent
  reviewers — single-line `{...}` shape silently bypasses
  warning AND native `mnc-stage1` has zero brace-deprecation
  logic), `check_no_hollow_features.py` calibration miss
  (`CompClause` + `FieldPattern`), Manifesto coherence (3rd
  panel of "Curly braces for blocks" drift), SPEC example
  corpus 72% brace-style against §4.0 colon-canonical,
  cadence skip (5-minor + 5-language-feature triggers both
  fired and not honored), Sh.\* shrink baseline labeling
  drift (actual −8.18% net v5.13.0 → v5.21.1, not −13.9%
  cited), `check_docs_drift.py` SPEC.md:1456 violation,
  `make ci-gates` Makefile target structural fix,
  `check_doc_freshness.py` CI gate structural fix. **Aggregate
  state entering v5.22.x**: 4 HIGH / 8 MEDIUM / ~12 LOW / 1
  v6.0-rescoped. **Cadence reset**: next routine panel at
  v5.27.0; cadence enforcement gate targeted for v5.23.0.
  See `.reviews/v5.22.0/README.md`,
  `.reviews/v5.22.0/V5_DECISION.md`, and
  `docs/roadmap/v5/v5.22.0/SESSION_REPORT.md`.

- **v5.21.1** (ready, not tagged) — **Mc.7 — pre-panel docs
  hygiene.** Doc-surface-only release closing the 12 H.\*
  findings flagged in `.reviews/v5.22.0/PRE_PANEL_AUDIT.md`.
  Same posture as v5.7.1 → v5.8.0 (project-record 9.66 panel).
  **Zero compiler edits. Zero runtime edits. Zero MIR / IR
  changes. Zero `mapanare/self/*.mn` edits.** Strict 3-stage
  fixed point preserved by construction at 238,086 lines /
  0-line diff (v5.9.0 milestone, held through 13 consecutive
  releases — longest streak in project history). Goldens
  **95/95**. **Decision-1 Path B locked**: the v5.14.0
  forward promise of single-line `if x: y` at v5.21.0 is
  rescoped explicitly to v6.0 (to coincide with `{}` hard
  removal); v5.21.1 PROMPT explicitly forbade the grammar +
  bootstrap edits Path A would require, and rescoping is the
  honest closure for a documentation contract violation.
  **H.1**: README.md goldens 80/80→95/95 + fixed-point
  231,957→238,086 with carry trail. **H.2**: SPEC.md header
  bumped from v5.7.1 cut to v5.21.0 cut + new "What changed
  since v5.7.1 sync" block summarizing the 14-release arc.
  **H.3**: SPEC §4.0 rewritten for v5.19.0 Te.3 — colon-style
  is now canonical, brace-style soft-deprecated with parse-
  time warning, `MAPANARE_NO_BRACE_WARNING=1` opt-out and
  `mnc fmt --keep-braces` documented. **H.4**: SPEC:1009
  broken `if x: y` promise rescoped to v6.0 with explicit
  rationale. **H.5** verify-only: SPEC already has Te.5
  (field shorthand §3.7, struct update §3.7, let destructuring
  §3.7, if-let / while-let / let-else §4.3.1) and Te.6
  (chained comparisons §2.2) sections — no additions needed.
  **H.6**: localized READMEs (es/pt/zh-CN) prose body synced
  (badges already updated at v5.21.0 by `bump_version.py`);
  fixed-point STRICT 238,086 + terseness arc summary in target
  language. Closes Boa Bo.17r structurally. **H.7**: new
  `examples/chained_cmp.mn` — 28-line example exercising 3-/
  4-element chains + once-evaluation demo. **H.8**:
  `mapanare/format.py` module docstring documents that v5.21.0
  chained comparisons are preserved by line-based whitespace
  canonicalization without an expression-level pass; new 4
  unit tests guard idempotence on chain shapes. **H.9**: new
  `tests/bootstrap/test_chained_cmp_mirror.py` (mirror of
  `test_te5_mirror.py`) — 4 golden cases + 6 inline cases,
  Python ↔ `mnc-stage1` byte-identical stdout assertion;
  **10/10 PASS**. **H.10**: `.reviews/CARRY_FORWARD.md` v5.13.0
  → v5.21.1 arc append (19 rows, each with resolving release
  + evidence pointer). **H.11**: `docs/known_issues.md`
  Last-updated bumped to v5.21.1 with v5.13.0 → v5.21.1
  closures narrative (12 entries). **H.12**:
  `BENCHMARKS-windows.md` gained a "last sync v5.8.8"
  admonition making staleness visible; per-platform split was
  already structural — closes Rattler #1 from v5.11.0 panel.
  Pre-panel posture: v5.22.0 panel inherits **0 CRITICAL / 0
  HIGH / 0 MEDIUM / 1 LOW (deferred to v6.0)**. See
  `docs/roadmap/v5/v5.21.1/SESSION_REPORT.md` and `PLAN.md`.

- **v5.21.0** (ready, not tagged) — **Te.6 — chained
  comparisons.** Python-style `0 < x < 10` parses as a single
  chained expression and means `0 < x && x < 10`, with `x`
  evaluated exactly once. All six comparison operators
  (`<`, `<=`, `>`, `>=`, `==`, `!=`) sit at a single merged
  precedence level and freely chain in any combination. Mixed-
  direction chains are legal (`a < b > c`). The "small wins"
  capstone of the v5.13–v5.20 terseness arc — small on
  purpose; the cluster doesn't pad scope. **Phase 0 (D1–D6)**:
  six locked design decisions in
  `docs/roadmap/v5/v5.21.0/CHAINED_CMP_DESIGN.md` — operator
  set, direction mixing, once-evaluation, triviality
  predicate, precedence level, byte-identity for single
  comparisons. **Grammar.** `cmp_expr` rewritten as a chain
  collector: `pipe_expr cmp_tail+ -> cmp_chain`. The
  transformer dispatches on tail count — 0 inlines (pure
  pass-through), 1 emits the legacy `BinaryExpr` (D6 — IR
  byte-identical for single comparisons), 2+ emits a new
  `ChainedCompare(operands, ops)` AST node. The pre-v5.21.0
  `eq_expr` precedence layer is folded into `cmp_expr` (D1)
  — `==`/`!=` move from precedence 3 to 4, matching
  ordering ops. Audit confirmed no existing code mixes
  `==` and `<` at the same level without explicit parens or
  `&&`/`||`. **Lower.** `_lower_chained_compare` desugars at
  lower time: for each interior non-trivial operand,
  synthesize a `LetBinding("__mn_chain_N", value=op)` so the
  operand evaluates exactly once; replace with
  `Identifier("__mn_chain_N")`; build pairwise `BinaryExpr`
  nodes (copying `pair_trait_dispatches[i]` from the
  semantic checker so Eq/Ord trait routing survives); fold
  with `&&`. New `_chain_compare_counter` field on the
  lowerer, separate from `tmp_counter` (same discipline as
  v5.20.1 Te.5.F.C's `struct_update_counter`). **Bootstrap
  mirror** lands in lockstep — `mnc-stage1` parses, type-
  checks, and lowers chains identically. New
  `Expr::ChainedCmp(List<Expr>, List<String>)` variant in
  `mapanare/self/ast.mn`; new `is_cmp_op` helper +
  chain-collection branch in `parser.mn::parse_expr`;
  `op_precedence` updated for the precedence merge; new
  `infer_expr` arm in `semantic.mn`; new `lower_chained_cmp`
  + `is_trivial_chain_operand` in `lower.mn` matching
  Python's predicate verbatim; new `chain_compare_counter`
  field on `LowerState`. **Goldens 91/91 → 95/95** —
  `92_chained_cmp_simple.mn`, `93_chained_cmp_4.mn`,
  `94_chained_cmp_mixed.mn`, `95_chained_cmp_side_effect.mn`
  (the last is the load-bearing once-evaluation test).
  **Strict 3-stage fixed point preserved by construction**:
  single-comparison shapes take the legacy AST + lowering
  path with zero IR diff; bootstrap source delta is
  additive only (no rewrites); `Expr::ChainedCmp` is not yet
  used in any self-host source. **No new MIR ops** —
  everything desugars to existing `BinOp(LT/GT/LE/GE/EQ/NE)`,
  `BinOp(AND)`, and trait `Call` instructions. **No new IR
  shapes**, no runtime functions added. SPEC.md §2.2 gains a
  "Chained Comparisons (v5.21.0)" subsection with migration
  note. See `docs/roadmap/v5/v5.21.0/SESSION_REPORT.md`.

- **v5.20.1** (ready, not tagged) — **Te.5.F — bootstrap mirror
  (patch).** Closes the v5.20.0 SESSION_REPORT's "Deferred to
  v5.20.1" item. `mnc-stage1` now parses and lowers all four
  Te.5 surface forms (field shorthand, struct update `..base`,
  let destructuring, if-let / while-let / let-else) exactly
  matching v5.20.0's Python behavior. **Te.5.F.B** — single-char
  parser relaxation in `parse_struct_fields_to_list` (synthesize
  `Ident(fname)` when COLON absent). **Te.5.F.C** — new
  `Expr::ConstructUpdate` AST + `lower_struct_update` mirroring
  Python: synthesizes a `Construct` in struct-declaration order,
  overrides slotted by name, holes filled with
  `__mn_base_N.<field>`. New `struct_update_counter` on
  `LowerState`. **Te.5.F.D** — new `Stmt::LetDestructure` plus
  `StructPattern` / `FieldPattern` structs; single-token
  `KW_LET KW_MUT? NAME LBRACE` lookahead in `parse_let_stmt`;
  bare-Ident-RHS optimization preserves IR byte-identity with
  manual `let x = p.x; let y = p.y`. **Te.5.F.E** — new
  `Expr::IfLet`, `Stmt::WhileLet`, `Stmt::LetElse`. `parse_if_expr`
  / `parse_while_stmt` / `parse_let_stmt` learn `KW_LET` /
  `NAME LPAREN` / `UNDERSCORE` lookaheads. Lowerers desugar to
  existing match/while/let machinery (zero new MIR ops). Bootstrap
  divergence helpers `block_diverges`, `stmt_diverges`,
  `match_arm_body_diverges` ported from Python. Two pre-existing
  `lower_match` latent bugs surfaced and fixed in scope: (1) skip
  `alloca <fn_ret>` dummy when fn_ret is void (would emit invalid
  `alloca void`); (2) stop demoting TK_UNKNOWN arm values to
  undef (forced phi-skip → alloca-fn_ret → alloca-void in
  `fn main()` for let-else). **91/91 native goldens** PASS
  through `mnc-stage1`; cross-bootstrap test
  `tests/bootstrap/test_te5_mirror.py` (12/12 PASS) asserts
  byte-identical stdout for every Te.5 golden. **Strict 3-stage
  fixed point preserved at 238,086 lines / 0-line diff** (+5,805
  IR lines vs v5.18.0's 232,281, expected from the new bootstrap
  `.mn` code). `bash scripts/build_from_seed.sh` succeeds.
  Source delta: +89 ast.mn, +190 parser.mn, +138 semantic.mn,
  +320 lower.mn, +5 lower_state.mn = **+742 lines** total
  (1.55× the v5.20.0 Python delta). One pre-existing v5.20.0
  mypy error in `mapanare/lower.py::_expr_or_block_diverges`
  fixed in scope. **Bootstrap deviation from Python**: let-else
  non-divergent else block proceeds at lower time (Python raises
  RuntimeError); deliberate — bootstrap can't easily emit a
  structured diagnostic from inside `lower.mn`. Pre-existing
  bootstrap miscompile of out-of-order field initializers in
  non-`..base` literals left untouched (out of scope; Te.5.F.C
  uses a separate by-name path). See
  `docs/roadmap/v5/v5.20.1/SESSION_REPORT.md`,
  `docs/roadmap/v5/v5.20.1/AUDIT.md`.
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
  `emit_llvm.mn` -4); cumulative shrink **-3,988 lines (-13.9%)**
  off the pre-Sh.B-immediate baseline (post-Te.4); **-2,285 lines
  (-8.18%)** net v5.13.0 → v5.21.1. IR shrink
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
- ~~**v5.20.1**~~ — shipped (see release notes above). Te.5.F
  bootstrap mirror. 91/91 native goldens; strict 3-stage fixed
  point preserved at 238,086 lines / 0-line diff. See
  `docs/roadmap/v5/v5.20.0/SESSION_REPORT.md`
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

This project is indexed by GitNexus as **Mapanare** (30508 symbols, 65199 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
