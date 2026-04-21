# v4.127.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase F closeout release 7 — self-hosted fixed-point
refinement.** The strict 3-stage stage2-vs-stage3 fixed-point
verification remains blocked by docket **Sh.8** (self-hosted
`semantic.mn` does not register `None` as a constructor; `mnc-stage1`
cannot self-compile `mnc_all.mn`). Sh.8 is pre-existing since v4.112.0
and out of scope for a buffer release per PLAN.md ("Fix semantic
divergences. If the two pipelines genuinely generate different code
for the same input, that is documented and deferred to a future
release"). This release pivots cleanly to the meaningful proxy: the
divergence surface between the Python bootstrap (the reference) and
`mnc-stage1` (the converging implementation) measured on the 39 of 65
goldens both pipelines compile cleanly. That divergence is reduced
from **9,971 to 9,535 unified-diff lines (-4.4%) with zero golden
regressions and zero new dockets opened.**

The framing matches PLAN.md verbatim: "The Python pipeline is the
reference; the self-hosted compiler converges toward it."

## Self-graded aggregate

**8.0 / 10**

- **Honest scope handling**: the Sh.8 blocker is pre-existing and
  documented; the release pivoted to the proxy measurement that
  PLAN.md explicitly enables, did not pretend to have run the
  3-stage script successfully, and did not open Sh.8 itself for
  fixing (out of scope per the v4.121.0 closeout arc PLAN). +strong
- **Real measurable delta**: not a paper exercise. Total diff lines
  reduced 4.4%, M bucket halved (-50%), TBAA tree removed (matching
  v4.123.0's Python equivalent). Every cosmetic fix has a one-line
  audit trail: 9 lines removed, 2 added, 37 whitespace patches. +solid
- **Zero regressions**: golden test count unchanged (39/65, identical
  to v4.126.0); pytest failure set byte-identical (38 failures,
  v4.126.0 An.1 carry-forward unchanged); `mnc-stage1` byte-size
  unchanged at 3,488,912 stripped; `libmapanare_rt.a` byte-identical.
  +solid
- **Categorization is a real instrument**: the bucket classifier
  (`scripts/measure_divergence.py`) is now part of the harness
  surface — future releases get a free comparable baseline. +solid
- **Block-level classifier limitation acknowledged**: L and W buckets
  show 0 not because no label/whitespace divergences exist, but
  because `difflib.SequenceMatcher.get_opcodes()` returns
  block-level diffs and a block that mixes whitespace-only changes
  with semantic ones falls into S. The doc states this honestly.
  -soft (could be fixed by per-line classification, but that's a
  measurement-tool refinement, not a v4.127.0 deliverable)
- **What's missing**: PLAN.md exit criterion 1 ("fixed-point baseline
  diff measured") satisfied via the proxy, not the strict 3-stage
  diff. PLAN.md risk register anticipates this exact pivot. -soft
- **Culebra not run**: same 854K-line `main.ll` that blocked v4.111.0
  / v4.112.0 / v4.126.0 still requires bounded-time scan support. -soft

## What shipped

### Code changes (production)

- `mapanare/self/emit_llvm.mn::emit_mir_module` — module header now
  emits explicit `target datalayout` and `target triple` lines after
  `source_filename` (matching `mapanare/targets.py::TARGET_X86_64_LINUX_GNU`
  defaults). Module footer's TBAA tree (`!1` = `Mapanare TBAA`,
  `!2`–`!5` type nodes, `!6`–`!9` access tags) deleted — 9 lines
  removed. Hardcoded version string bumped from `4.97.0` to `4.127.0`.
  6-line comment block explains the change and references v4.123.0's
  Python equivalent at `emit_llvm_text.py:923-933`.

- `mapanare/self/emit_llvm_ir.mn` — 25 IR-builder helper functions
  (alloca, load, add, sub, mul, sdiv, srem, fadd, fsub, fmul, fdiv,
  frem, fneg, neg, not, icmp, fcmp, and_instr, or_instr, phi,
  call_ir, gep, insertvalue, extractvalue, bitcast) had their format
  string `" =op "` changed to `" = op "` (one space added per
  builder). LLVM accepts both forms — `=` is a token separator — but
  the canonical form has the space and matches the Python emitter.

- `mapanare/self/emit_llvm.mn` — 12 inline call sites in the lowerer
  that built LLVM strings directly (sitofp, fptosi, alloca,
  insertvalue, call, bitcast at lines 1024, 1031, 1067, 1069, 1895,
  1904, 1913, 1917, 1926, 2931, 2948, 3086) had the same `" =op "`
  → `" = op "` fix. The `find_alloca_by_search` helper at
  `emit_llvm.mn:1420` searches for previously-emitted load
  instructions; its search pattern was caught by the same regex
  (`" =load"` → `" = load"`) and continues to match correctly
  against the new builder output.

### Code changes (tooling)

- `scripts/measure_divergence.py` (NEW, 234 lines) — divergence
  measurement harness. For each passing golden, compiles via both
  pipelines, computes line-level diff, classifies each diff hunk
  into L / C / A / S / W / M buckets via heuristics. Emits per-test
  JSON breakdown + summary table. Used to produce both the
  pre-fix baseline and the post-fix delta.

### Documentation

- `docs/roadmap/v4/v4.127.0/FIXEDPOINT_BASELINE.md` (NEW) — Phase 1+2
  measurement, Phase 3 fix list, Phase 4 delta table, top-8 per-test
  contributors. Honest about what was measured (Python-vs-self-hosted
  proxy) and what was not (strict stage2-vs-stage3, blocked by Sh.8).

- `docs/roadmap/v4/v4.127.0/baseline.json` (NEW) — pre-fix per-test
  measurement.

- `docs/roadmap/v4/v4.127.0/post_fix.json` (NEW) — post-fix per-test
  measurement.

- `CHANGELOG.md` — `[4.127.0]` entry summarising the release.

- `CLAUDE.md` — no manual edit (the file shows unrelated working-tree
  modification from another session's GitNexus block re-render).

### Verification

- `mnc-stage1` rebuild: clean (`python3 scripts/build_stage1.py`,
  ~1m20s, 3,967,760 bytes unstripped → 3,488,912 stripped, byte-size
  unchanged from v4.126.0).
- Golden tests (`python3 scripts/test_native.py --stage1
  mapanare/self/mnc-stage1`): **26 failed / 39 passed in 6.5s** —
  identical to v4.126.0; zero regressions in previously-passing tests.
- Post-fix IR validation: `llvm-as` accepts every passing-golden IR.
- pytest excluding bootstrap (`python3 -m pytest tests/
  --ignore=tests/bootstrap -q`): **5,061 passed / 38 failed / 103
  skipped / 7 xfailed in 8m12s**. Failure set sorted-and-diffed
  against v4.126.0 HEAD baseline (verified by stash-pop-stash-pop):
  **byte-identical** — no new pytest failures from this release.
- Lint: `ruff check scripts/measure_divergence.py` clean,
  `black --check` clean (after one auto-format). Self-hosted `.mn`
  files have no Python lint to run; their structural changes are
  whitespace-only and were verified by re-running goldens.
- `libmapanare_rt.a`: not rebuilt (no C runtime changes); byte-identical.

## Sh.8 — not in scope, but documented again

`scripts/verify_fixed_point.sh --keep` fails at Stage 1:

```text
[Stage 1] stage1 compiles mnc_all.mn → stage2.ll
mapanare/self/mnc_all.mn:0:0: error: Undefined variable 'None'
```

Root cause (re-verified): `mapanare/self/lexer.mn:101,161-162` only
recognises lowercase `none` / `nada` as `KW_NONE`. `mnc_all.mn` (and
`parser.mn:2063`) contains `let mut guard: Option<Expr> = None`.
The Python bootstrap accepts this because (a) `compile_multi_module_mir`
in `scripts/build_stage1.py:80` passes `skip_check=True` so the
"Undefined variable" semantic error never fires, and (b)
`mapanare/lower.py::_lower_identifier` (line 1651-1657) recognises
"None" as a bare enum variant of Option. The self-hosted compiler has
neither bypass.

Three plausible fixes:

1. **Lex uppercase `None` as `KW_NONE`** (smallest scope; aligns with
   Rust convention of capitalised constructors).
2. **Register `None`/`Some`/`Ok`/`Err` as built-in symbols in
   `semantic.mn::infer_expr`** (medium scope; matches Python's enum
   variant fallback in `_lower_identifier`).
3. **Add a `--no-check` flag to `mnc-stage1`** (mirrors Python's
   `skip_check=True`).

All three are in scope for a future release dedicated to Sh.8.
v4.121.0 closeout PLAN reserves no slot specifically for this; it
likely lands in the v4.131.0+ post-panel arc.

## Next release

**v4.128.0** — documentation and SPEC sync per the v4.121.0 closeout
PLAN. Boa (DX reviewer) and Coral (language-design reviewer) both
grade documentation currency. Expected scope:

- SPEC.md audit against current implementation
- Cookbook updates for v4.121.0–v4.127.0 changes
- Stale section flagging
- README badge sync

This release's `FIXEDPOINT_BASELINE.md` adds one line of evidence to
the v4.130.0 panel's divergence-surface assessment.
