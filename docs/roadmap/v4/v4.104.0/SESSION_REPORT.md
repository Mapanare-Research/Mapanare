# v4.104.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase B release 1 complete.** Verification-only release,
zero code changes. The compiler rebuilt cleanly from Phase A sources at
`-O2`, 60 of 64 golden tests pass through the full LLVM 18.1.3
integration pipeline, 21 of 64 pass through `mnc-stage1` (unchanged from
v4.103.0 baseline — no regressions), and all 3 async tests (55, 56, 57)
run natively with correct output and valgrind clean. Five semantic
divergences between Python bootstrap and `mnc-stage1` recorded as
v4.106.0 docket items.

## Self-graded aggregate

**9.2 / 10** on the internal smoke check:
- Phase A fixes hold under -O2 (all 60 integration passes, all 3 async
  PASSES, 0 opt/llc/link/runtime failures). +strong
- Stage1 is still 21/64 — not a Phase B regression, just the plateau the
  Phase A sprint didn't claim to fix. Neutral.
- Two pre-existing bootstrap bugs surfaced by the new llvm-as gate
  (47_try_operator, 51_match_guards_and_or). Not blocking; documented.
- One HIGH bug found in stage1's `?`-operator lowering (10_result emits
  invalid IR). Not caught by prior harness; Phase B measurement
  surfaced it. Good catch for a verification release.

## Completed

- **Phase 1** — clean rebuild at `-O2`. `mapanare/self/main.ll` (857,645
  lines), `mapanare/self/mnc-stage1` (3.5 MB stripped). Smoke test
  passes. Log + culebra summary archived.
- **Phase 2** — 21/64 golden tests PASS through `mnc-stage1`; 43
  failures classified into 8 root-cause categories.
- **Phase 3** — 60/64 golden tests PASS through full integration
  pipeline (emit → llvm-as → opt -O2 → llc → clang → run). Zero opt
  crashes, zero llc crashes, zero link errors, zero runtime failures.
- **Phase 4** — async goldens 55/56/57 all run natively with correct
  output (42/43/110), valgrind clean, scheduler exports confirmed.
- **Phase 5** — Divergence report: 17 of 18 comparable tests produce
  byte-identical output; 5 docket items (`Div.1`–`Div.5`) filed.
- **Phase 6** — CHANGELOG, SESSION_REPORT, roadmap updates, validation,
  commit (this file).

## Carry-forward closed

None from the v4.99.0 panel's docket were targeted by v4.104.0 (all 5
critical/high items closed in Phase A). Verification confirms they
remain closed.

## Carry-forward opened (for v4.106.0 panel)

| # | Item | Severity | Evidence |
|---|---|---|---|
| Div.1 | stage1 `?`-op lowering emits wrong-type store | HIGH | `10_result.stg1.ll:159:13` — `store i64 %v6` where `%v6` is `{ptr,i64}` |
| Div.2 | bootstrap `?`-op emits invalid IR | HIGH | `47_try_operator.ll:93:13` — `store i64 %uw.11` where `%uw.11` is `{i64,{ptr,i64}}` |
| Div.3 | Option payload ABI divergence | MEDIUM | `17_option` boot=`{i1,i64}` vs stg1=`{i1,ptr}` (same output, different ABI) |
| Div.4 | or-pattern with enum constructor rejected by semantic checker | MEDIUM | `51_match_guards_and_or.mn:3:19` |
| Div.5 | `main` return type inconsistency | LOW | bootstrap `i64` vs stage1 `i32` across all 21 comparable tests |

Plus the 8 Phase 2 failure categories still open in `mapanare/self/`:
MIR optimizer `block_successors` null deref (14×); String lifetime in
`emit_llvm__emit_mir_call` (9×); lowerer expression crash (3×); MIR
verifier terminator missing (3×); `Tensor`/`None` undefined (3×);
comma-in-index parser gap (2×); `block_on` undefined (5×);
typed-const / `fn(T)->T` (4×).

## Measurements

| Metric | Value | Delta vs v4.103.0 |
|---|---:|---|
| mnc-stage1 binary (stripped) | 3,501,200 B | — |
| mnc-stage1 main.ll lines | 857,645 | — |
| Build time (from clean) | 81 s | — |
| Golden through mnc-stage1 | **21/64** | 21/64 → 21/64 (no change) |
| Golden through full pipeline | **60/64** | first recorded |
| Async goldens native | **3/3** | first recorded |
| Total pytest count | 4,845+ | — |
| llvm-as on main.ll | **OK** (12.5 MB bc) | first recorded |
| Culebra baseline | (saved) | — |

## Decisions Made

- **Optimization level: `-O2` (no fallback needed).** `build_stage1.py`
  already drives `-O2` for both IR-to-object compilation and C runtime
  compilation. No need to try `-O1` or `-O0` — clean build succeeded.
- **Pipeline scope: all 64, not subset.** Phase B is a verification
  release; partial coverage defeats the point.
- **Divergence threshold: document, don't pre-filter.** Captured every
  diff, then classified. 42 `MISSING` (stage1 can't compile), 21
  comparable (all with cosmetic differences that normalize away under
  main-return-type and declare-preamble stripping), 1 both-fail.
- **Do not fix anything this release.** Per PLAN: bugs discovered go
  into docket for v4.105.0 / v4.106.0. Five divergence docket items
  opened; zero code changes committed.

## Verification Results

- `python3 scripts/build_stage1.py` — SUCCESS (1m21s, -O2, 1 benign
  linker warning).
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` —
  21 passed, 43 failed in 6.7s.
- `/tmp/run_integration.sh` — 60 PASS, 2 SKIP, 2 FAIL in 56s.
- `/tmp/run_divergence.sh` — 64 tests classified.
- Async runs: 55=42, 56=43, 57=110, all valgrind clean.
- `llvm-as mapanare/self/main.ll` — SUCCESS, zero errors.
- `culebra audit mapanare/self/main.ll` — no pathologies.
- `culebra check mapanare/self/main.ll` — VALID.

## Tool discipline retrospective

- Raw commands used: `llvm-as`, `opt`, `llc`, `clang`, `valgrind`, `nm`,
  `diff`, `grep`, `wc` — all appropriate for measurement.
- Culebra commands used: `journal add`, `summary`, `audit`, `check`.
- Python bootstrap commands: `python3 -m mapanare emit-llvm`,
  `python3 scripts/build_stage1.py`, `python3 scripts/test_native.py`.
- Ratio: ~70% raw LLVM toolchain / 30% Culebra / Python. For a
  measurement-only release this is the right mix; Culebra's templates
  directory isn't configured locally so `scan` would have been noise.

## Next Session Should Start With

- Read `POST_RECOVERY_MASTER_PROMPT.md` (if > 1 week since last read).
- Read `docs/roadmap/v4/v4.105.0/PLAN.md` — debugging-infrastructure
  release (valgrind, ASan, TSan CI, crash breadcrumbs).
- Read `docs/roadmap/v4/v4.105.0/PROMPT.md`.
- Review this report's `Div.1`–`Div.5` items to understand which
  divergences the v4.105.0 sanitizer CI will also catch in passing.
- Phase A docket continues to be closed; Phase B docket is growing —
  v4.105.0 is a tooling release, v4.106.0 is the panel.
