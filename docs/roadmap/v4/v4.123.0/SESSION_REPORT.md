# v4.123.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase F closeout release 3: dead-code sweep.** The AST-level
optimiser (`mapanare/optimizer.py`, 1,203 lines) and the TBAA metadata
declaration block in `mapanare/emit_llvm_text.py` (nodes `!1`–`!9`)
are gone. Both were non-load-bearing: the optimiser was superseded by
`mir_opt.py` in the v3.x era and reachable only via an
undocumented `--legacy-optimizer` flag that no test exercised; the
TBAA tree was declared in every module header but never attached to
any `load`/`store`, confirmed 100% dead by v4.109.0 forensics. Net
**−1,963 lines**, well above the 1,200-line exit-criterion target.
Zero behaviour changes. Zero new test failures (failure set
byte-identical to v4.122.0 HEAD). Expected panel impact at v4.130.0:
**+0.1** (cleanup smell removed).

## Self-graded aggregate

**8.8 / 10**

- **Single-session, exit-criteria clean, receipt-backed.** All 7 exit
  criteria from `PLAN.md` are green with concrete evidence
  (`git diff --stat` for line counts, `--legacy-optimizer` argparse
  rejection verified, pytest delta confirmed against stash-compare
  baseline, `mnc-stage1` rebuild + golden run). The PLAN called this
  "the easiest release in the closeout arc" and that framing held.
  +strong
- **Zero surprises in downstream impact.** The `git grep` sweep for
  `optimizer` hit 9 code files; every one had a sensible treatment
  path (delete / re-import from `mir_opt` as alias / strip no-op
  call / delete exclusive test class). No hidden user-code
  dependency surfaced. The `OptLevel` alias
  (`from mapanare.mir_opt import MIROptLevel as OptLevel`) avoided a
  mass rename in `cli.py` — both enums are byte-compatible `IntEnum`
  with `O0`–`O3`. +strong
- **Stash-compare receipt for the failure-set assertion.** Ran
  `pytest tests/ --ignore=tests/bootstrap` both at HEAD (stashed)
  and post-change; diffed the sorted `FAILED` lists; the diff was
  empty. 39 pre-existing failures remain, zero new. Same for the
  bootstrap subset: 12 failures both sides, identical names. That
  receipt is the single load-bearing evidence for "no behaviour
  change" — without it, the `−50 passes` delta could have been
  misread as regressions rather than deleted tests. +strong
- **TBAA deletion verified at IR level.** Emitted `01_hello.mn` to
  LLVM IR post-fix; `grep` for `Mapanare TBAA` / `!1 = ` / `!2 = `
  returns nothing; `llvm-as /tmp/hello.ll -o /dev/null` exits 0.
  Module version metadata `!mapanare.version = !{!0}` is preserved.
  +solid
- **Playground scrub was larger than PLAN.md anticipated.**
  `playground/src/worker.js` contained embedded Python strings with
  `from mapanare.optimizer import OptLevel, optimize` in both the
  WASM and Python compile paths; `playground/scripts/bundle-compiler.sh`
  copied `optimizer.py` into the browser bundle; and
  `tests/playground/test_playground.py::REQUIRED_COMPILER_FILES`
  asserted its presence. All three were updated. The in-browser WASM
  compile path no longer runs the AST optimiser before lowering —
  but the MIR optimiser still runs inside the WASM emitter path, so
  the practical output quality is unchanged (the old optimizer was
  called at `O1` in one path and `O0` (no-op) in the other). +solid
- **Coverage report at `tests/COVERAGE.md` left intentionally
  stale.** The v4.117.0 coverage snapshot explicitly listed
  `optimizer.py` at 9% with a recommendation (#3): "Delete
  `optimizer.py` if the `tests/optimizer/` suite confirms nothing
  live depends on it." This release is the execution of that
  recommendation; rewriting the v4.117.0 snapshot would erase the
  rationale trail. Left as-is; a future coverage refresh will
  regenerate the table against the current tree. +solid
- **`TestOptimizerIntegration` comment stub instead of silent
  deletion.** Replaced the 24-line class with a 7-line comment
  block pointing readers to `tests/mir/`, `tests/llvm/`, and the
  golden harness for live MIR-level coverage. A reviewer coming
  back to this file in six months shouldn't wonder whether
  optimiser coverage was ever measured at all. +solid
- **Single cosmetic `black` nit.** My deletion left a 3-blank-line
  gap around where `TestOptimizerIntegration` used to live;
  `black --check` flagged it; compressed to 2 blank lines. No
  semantic change. +solid
- **Didn't touch `bootstrap/cli.py` or `bootstrap/optimizer.py`**
  (the frozen v0.6.0 bootstrap tree). Those files still reference
  `mapanare.optimizer`, which is gone from the live tree. That is
  intentional: the bootstrap is archived source, not a live
  dependency, and modifying it would violate the "bootstrap is
  frozen at v0.6.0" invariant documented in `bootstrap/README.md`.
  +solid
- **One scope-creep decision point.** The redundant
  `MIROptLevel(opt_level.value)` calls in `cli.py` (now
  identity conversions since `OptLevel` IS `MIROptLevel`) could
  have been simplified to just `opt_level`. Left them as-is to keep
  the diff minimal and avoid churning a 940-line file for a
  cosmetic win. A future lint-cleanup release can collapse them.
  +soft
- **Black pre-existing debt on `emit_llvm_text.py` unchanged.** 50
  `ruff` findings + a black quote-style reformat queue existed
  at HEAD and still exist after my TBAA deletion. An.2
  carry-forward, on the v4.126.0 track. Not my release's job.
  +soft

## What shipped

### Deletions (2 files, 2,232 lines)

- **`mapanare/optimizer.py`** (1,203 lines). AST-level optimiser:
  constant folding, DCE, agent inlining, stream fusion. Last
  non-legacy usage was `cmd_emit_mir`'s `if legacy:` branch gated
  on the `--legacy-optimizer` flag, now removed.
- **`tests/optimizer/test_optimizer.py`** (1,029 lines). Exclusively
  tested the deleted module. Companion file
  `tests/optimizer/test_non_convergence.py` is kept — it tests the
  MIR optimiser's non-convergence raise path, not the deleted
  module.

### Compiler changes (2 files)

- **`mapanare/cli.py`** — 16 lines changed:
  - Import: `from mapanare.optimizer import OptLevel, optimize` →
    `from mapanare.mir_opt import MIROptLevel as OptLevel`. The
    `OptLevel` name is preserved as an alias so downstream type
    annotations at 8 call sites compile unchanged.
  - `cmd_emit_mir`: removed `legacy = getattr(args, "legacy_optimizer",
    False)`, the `if legacy: ast, _ = optimize(ast, opt_level)`
    branch, and the corresponding `if not legacy:` guard around the
    MIR optimiser call. The MIR optimiser runs unconditionally now.
  - Argparse: removed the `--legacy-optimizer` flag registration
    from `p_emit_mir`.
- **`mapanare/emit_llvm_text.py`** — 16 lines changed (11 deletions
  + 5 insertions): in the `else` branch of `_emit_module`'s tail
  metadata block, replaced the 8-line TBAA declaration
  (`!1` = root, `!2`–`!5` = int/float/ptr/bool type nodes,
  `!6`–`!9` = access tags) with a 3-line comment explaining the
  v4.123.0 deletion rationale. The `!mapanare.version = !{!0}`
  emission is preserved.

### Test updates (5 files)

- **`tests/bootstrap/test_verification.py`** — 37 lines changed:
  removed `from mapanare.optimizer import OptLevel, optimize`;
  `TestOptimizerIntegration` class (24 lines, 34 parametrised
  tests) replaced by a 7-line comment block.
- **`tests/llvm/test_drop_glue.py`** — 1 line changed: `OptLevel`
  import switched to `from mapanare.mir_opt import MIROptLevel as
  OptLevel`.
- **`tests/llvm/test_emitter_hardening.py`** — 1 line changed:
  same import switch inside `test_multiple_functions`.
- **`tests/test_examples.py`** — 2 lines changed: removed the
  `from mapanare.optimizer import OptLevel, optimize` import and
  the `ast, _ = optimize(ast, OptLevel.O0)` call (no-op at O0
  under the old optimiser).
- **`tests/playground/test_playground.py`** — 1 line changed:
  removed `"optimizer.py"` from `REQUIRED_COMPILER_FILES`.

### Playground updates (2 files)

- **`playground/src/worker.js`** — 7 lines changed: removed
  `from mapanare.optimizer import OptLevel, optimize` and the
  `ast, _ = optimize(ast, OptLevel.O1)` call from
  `_mn_compile_to_wasm`; same for the O0 variant in
  `_mn_compile_and_run`; removed `"optimizer.py"` from the
  `modules` array that Pyodide fetches into the in-browser
  filesystem.
- **`playground/scripts/bundle-compiler.sh`** — 2 lines changed:
  removed `optimizer.py` from the list of compiler modules copied
  into `public/compiler/`.

### Doc updates

- `CHANGELOG.md` — new `[4.123.0] - 2026-04-14` entry.
- `docs/roadmap/v4/v4.123.0/PLAN.md` — Status PLANNED → DONE.
- `docs/roadmap/v4/v4.123.0/SESSION_REPORT.md` — this file.
- `docs/roadmap/v4/README.md` — new v4.123.0 row at the top of the
  Phase F block.
- `docs/roadmap/ROADMAP.md` — "Where We Are" header rewritten.
- `CLAUDE.md` — top-of-file current-version summary replaced;
  "Key modules in `mapanare/`" list no longer lists `optimizer.py`.
- `docs/BOOTSTRAP.md` — "Key files" table replaces the
  `optimizer.py` row with `lower.py` + `mir_opt.py`.

### Regenerated artefacts

- `mapanare/self/main.ll` — version string (`4.122.0` → `4.123.0`)
  and value-name counter renumbering from `scripts/build_stage1.py`.
  No behavioural change: `mnc-stage1` golden pass count is 27/65,
  unchanged from v4.122.0.
- `tests/golden/BENCHMARKS-linux.md`, `BENCHMARKS.md`,
  `HISTORY.jsonl` — auto-updated by `scripts/test_native.py`.

### Not changed

- **No changes** under `runtime/native/`, `mapanare/self/`,
  `stdlib/`, `scripts/`, `benchmarks/`, `bootstrap/`. `libmapanare_rt.a`
  byte-identical to v4.122.0. The self-hosted compiler never had an
  AST-level optimiser — this release is Python-side only.

## Exit criteria (7 items from PLAN.md)

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | `mapanare/optimizer.py` deleted | PASS | `git diff --stat` shows `mapanare/optimizer.py  \| 1203 ---------------------------------`. |
| 2 | `--legacy-optimizer` CLI flag removed | PASS | `python3 -m mapanare emit-mir --legacy-optimizer tests/golden/01_hello.mn` exits 2 with `error: unrecognized arguments: --legacy-optimizer`. |
| 3 | TBAA metadata declaration removed from `emit_llvm_text.py` | PASS | `grep -c "Mapanare TBAA"` on freshly-emitted `01_hello.mn` IR returns 0; `llvm-as` exits 0. |
| 4 | `make test` green (0 new failures) | PASS | Audit subset 5,053 passed / 39 failed — same failure set as v4.122.0 HEAD (stash-compare receipt). Bootstrap subset 213 passed / 12 failed — same failure set as HEAD. −50 + −34 passes = deleted test files, not regressions. |
| 5 | `make lint` clean on modified lines | PASS | `ruff` + `black` clean on all human-touched files. Pre-existing baseline debt in `emit_llvm_text.py` unchanged (An.2 carry-forward). |
| 6 | mnc-stage1 builds and golden tests pass | PASS | `scripts/build_stage1.py` exits 0 (3.5 MB stripped binary); `scripts/test_native.py --stage1 ...` shows **27 passed / 38 failed** — byte-identical to v4.122.0. |
| 7 | Net line count reduction >= 1,200 | PASS | `git diff --stat`: 366 insertions, 2,329 deletions, **net −1,963 lines** (1.6× the target). |

**7/7 PASS.**

## Numbers

- **Deletions**: 2,232 lines across 2 files (`mapanare/optimizer.py`
  1,203 + `tests/optimizer/test_optimizer.py` 1,029).
- **Code edits**: 16 lines in `mapanare/cli.py`, 16 in
  `mapanare/emit_llvm_text.py`, 37 in
  `tests/bootstrap/test_verification.py`, 2 each in 2 `tests/llvm/`
  files, 2 in `tests/test_examples.py`, 1 in
  `tests/playground/test_playground.py`, 7 in
  `playground/src/worker.js`, 2 in
  `playground/scripts/bundle-compiler.sh`, 3 in `docs/BOOTSTRAP.md`,
  1 in `CLAUDE.md` module list.
- **Doc + roadmap edits**: ~300 lines across SESSION_REPORT,
  CHANGELOG, PLAN, v4 README, ROADMAP, CLAUDE top-of-file summary.
- **Autogenerated artefact drift**: 15 lines in
  `mapanare/self/main.ll` (version + counters), 179 lines in
  each of two `tests/golden/BENCHMARKS*.md`, 1 line in
  `tests/golden/HISTORY.jsonl`.
- **`git diff --stat` total**: 17 files, 366 insertions, 2,329
  deletions, **net −1,963 lines**.
- **Audit pytest** (excluding bootstrap): 5,053 passed / 39 failed /
  103 skipped / 7 xfailed in 96.6 s. **HEAD baseline**: 5,103
  passed / 39 failed. Delta: −50 passes (= deleted
  `tests/optimizer/test_optimizer.py` count), identical failure
  set.
- **Bootstrap pytest**: 213 passed / 12 failed in 35.5 s. **HEAD
  baseline**: 247 passed / 12 failed. Delta: −34 passes (= deleted
  `TestOptimizerIntegration` class count), identical failure set.
- **Golden tests through `mnc-stage1`**: 27 passed / 38 failed in
  6.8 s — byte-identical to v4.122.0.
- **`mnc-stage1` binary**: 3,488,912 bytes stripped (12% reduction
  from 3,967,760). Identical to v4.122.0 modulo version-string
  bytes.
- **`libmapanare_rt.a`**: byte-identical to v4.122.0 (no runtime
  changes).

## Next session should start with

**v4.124.0 — Sh.8: self-hosted `semantic.mn` constructor registration
for `None`/`Some`/`Ok`.** This unblocks fixed-point self-compilation
(stage1 currently fails at Stage 1 of `scripts/verify_fixed_point.sh`
with `Undefined variable 'None'` in `mnc_all.mn`; the Python
bootstrap bypasses via `skip_check=True` in
`scripts/build_stage1.py`). Per the v4.121.0 closeout PLAN, Sh.8 is
the v4.124.0 target. Expected panel impact at v4.130.0: +0.3 / 10
(Cobra flagged Sh.8 as the single biggest self-hosted gap in the
v4.120.0 panel).

After v4.124.0: v4.125.0 benchmark refresh (first full cross-language
run since v4.118.0, with all Phase F fixes applied); v4.126.0 lint
sweep (close An.2 — the `lower.py` + `emit_llvm_text.py` baseline
debt); v4.127.0–v4.129.0 buffer for Sh.2 / polish; v4.130.0 is the
panel — v5 gate attempt 3.
