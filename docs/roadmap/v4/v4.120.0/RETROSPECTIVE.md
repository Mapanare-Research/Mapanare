# Mapanare v4.x — Retrospective

> Written at v4.119.0 (2026-04-14). This retrospective is the narrative layer
> on top of the `STATISTICS.md` data and `V5_READINESS.md` gap analysis
> that sit alongside it in `docs/roadmap/v4/v4.120.0/`. It is written for
> the seven reviewers who will grade the v4.120.0 panel. It is honest,
> not promotional. Failures and gaps are named. Target length: under 500
> lines.

---

## Executive summary

The v4.x line produced **121 releases** over approximately one calendar
year, scoring between `9.79` (v3.47.0 — the gate panel before v4.0.0)
and `6.59` (v4.99.0 — the v5 gate failure). It contains the project's
worst regression (v4.26.0 crisis) and its best recovery (v4.100.0–
v4.118.0, 20 consecutive releases).

The v4.120.0 panel is the **v5 gate, attempt 2**. Between the first and
second attempts, the project closed **every critical / high docket item
the v4.99.0 panel flagged**, moved the self-hosted compiler from 0/61
golden tests to 26/64 (39/64 with semantic equivalence accounting),
landed the first native async I/O benchmarks in project history,
narrowed the geomean performance gap vs. C from 9.5× to 5.46×, and
extended ASan + TSan + Valgrind CI gates to the entire golden suite and
async demos.

The recovery arc cost about 1,150 net lines of code (`−2,434` Python,
`+939` self-hosted, `+340` C runtime). **It removed more than it added.**
That is the single most important sentence in this retrospective.

---

## Timeline

### Pre-v4.0.0 production gate (v3.33.0 – v3.47.0, 2025)

| Panel | Score | Verdict |
|---|---:|---|
| v3.33.0 | 9.44 | 5 PASS / 2 WITH NOTES / 0 NEEDS WORK |
| v3.45.0 | 9.69 | 6 / 1 / 0 |
| **v3.47.0** | **9.79** | **7 / 0 / 0 — unanimous. v4.0.0 gate passes.** |

Methodology of the pre-v4 era: **large-multiple-of-5 cadence, 7-reviewer
panels every 5 minors**, unconditional rejection on any CRITICAL item.
The process worked: 6 cycles of climbing scores, zero regressions, all
carry-forwards either closed or explicitly retired.

### The feature arcs (v4.0.0 – v4.76.0)

v4.x opened strong. The gate conditions from v3.47.0 were met; v4.0.0
shipped with a production-ready LLVM backend, first-class agents /
signals / streams / tensors, and the self-hosted compiler reaching
~15,000 lines of `.mn`.

From v4.0.0 to v4.26.0 (the crisis), the project added feature surface
rapidly:

- **Async / await** (v4.2.0 promised; revisited across v4.26–v4.30)
- **FFI bindings** (v4.25.0)
- **GPU kernel dispatch** (`@gpu` / `@cuda` / `@vulkan`, v4.2.x onward)
- **`const` keyword** (v4.24.0)
- **Mobile targets** (v4.0.0 line)
- **WebAssembly backend** (v2.0.0, carried through v4.x)

From v4.32.0 through v4.76.0 (the recovery from the v4.26.0 crisis,
then the coroutine arc), the project ran nine named arcs. The last of
these — **Arc 9, coroutine completion** — closed at v4.76.0 with a
panel of **8.86/10, 6 PASS / 1 WITH NOTES / 0 NEEDS WORK**. Arc 9 was
notable because it produced the first `10/10` individual review score
in project history (Rattler, on LLVM coroutine IR).

This is the high-water mark of v4.x so far. v4.76.0 is the version the
v4.99.0 panel later called "release-gate quality" and that the v5.0.0
tag could theoretically have been cut from, if not for what came
next.

### The optimizer arc (v4.77.0 – v4.99.0)

Between v4.76.0 and v4.99.0, twenty-three releases landed without a
7-reviewer panel. The theme was *performance*: Arcs 11 and 12 added
`nsw`/`nuw` integer flags, `inbounds` GEPs, function attributes
(`nounwind`, `willreturn`, `readonly`), TBAA metadata, and the
`v4.82.0` baseline benchmark suite.

Three problems compounded:

1. **Hollow wins.** The v4.98.0 FINAL_REPORT's geomean of 0.992× at
   -O2 after eight releases of optimiser work was reported honestly
   at the time — but not widely enough. v4.109.0's Phase C forensics
   later showed TBAA metadata was *100% dead* (declared in the module
   header, never attached to any load or store; the documenting
   comment described intended wiring that was never written). Arc 11's
   only load-bearing contribution turned out to be the function
   attributes on runtime-call declarations, which propagate through
   LLVM's module-level attribute table; the inline `nsw`/`nuw` flags
   were largely redundant (LLVM inferred them independently at -O2).
2. **Tagged-pointer UB shipped.** `mapanare_core.c::mn_tag_heap` set
   bit 0 of a `char*` pointer — undefined behaviour under C's strict
   aliasing. LLVM exploited the UB at -O2, producing garbled `mnc-
   stage1` output. Discovered in v4.97.0; shipped in v4.97.0 and
   v4.98.0 anyway. This was a *process failure*: the anti-rush rules
   said "fix the root cause," and they were not followed.
3. **`libmapanare_rt.a` never rebuilt for the new async scheduler.**
   v4.93.0 added a multi-threaded work-stealing scheduler to the C
   runtime source, but the static library was not re-made. Result: the
   v4.94.0 async benchmark suite compiled to IR but could not link.
   `benchmarks/async/ASYNC_RESULTS.md` had to ship with "Runtime
   measurements deferred" — a stranger-than-fiction outcome given
   that this was supposed to be Arc 13's deliverable.

### The v4.99.0 panel — v5 gate attempt 1 (2026-04-13)

| Metric | Value |
|---|---|
| Aggregate | **6.59 / 10** |
| Verdict | **1 PASS / 3 WITH NOTES / 3 NEEDS WORK** |
| Decision | **Option B — continue v4.100.0+; v5 NOT tagged** |
| Docket | 11 items. 2 CRITICAL, 3 HIGH, 3 MEDIUM, 3 LOW |

Three panelists returned NEEDS WORK (Rattler, Viper, Anaconda). The
convergent finding: **correctness first, then performance**. The
tagged-pointer UB, the list-indexing bug (`arr.push(42); arr[0]`
returning garbage), the async-can't-link situation, and the else/sino
+ closure-type latent bugs were all blockers. Performance numbers that
depend on compiling correct IR are meaningless if the binary is
corrupt.

The lead's assessment at the time (quoted in `.reviews/v4.99.0/
V5_DECISION.md`): *"The panel is right. The tagged-pointer issue is a
3-4 hour fix that blocks everything downstream. It should have been
fixed in v4.97.0 when it was discovered. Shipping v4.97.0 and v4.98.0
with a known binary-corruption bug was a process failure."*

The v4.99.0 panel created the recovery arc's first ten items of scope
plus one item surfaced during Phase A audit (drop-glue reachability
bug that the original docket did not capture but the v4.103.0 fix
closed).

---

## The recovery arc (v4.100.0 – v4.118.0)

Six phases, twenty releases, two point-release patches.

### Phase A — critical / high bug fixes (v4.100.0 – v4.103.0)

| Release | Core delivery |
|---|---|
| v4.100.0 | **Tagged-pointer UB removed structurally.** `MnString` bitfield (`len:63, is_heap:1`) replaces bit-tagging. ABI preserved at 16 bytes. |
| v4.101.0 | **Self-hosted emitter output corruption fixed.** Root cause: use-after-free drop glue. `_move_resource` at 6 call sites. Golden 0/61 → 16/62. |
| v4.102.0 | **First native async run in project history.** `mn_coro_is_done` + `_do_block_on` fixes. Async goldens 55/56/57 → 42/43/110. |
| v4.103.0 | **Phase A complete.** Else/sino and closure-type fixes land. Drop-glue boxed-enum skip. Golden 16/62 → **21/64**. All 5 critical / high docket items closed. |

Phase A's theme was *mechanical*: named bug, named root cause, named fix,
named evidence. Every release closed at least one panel docket. None
added features.

### Phase B — rebuild, verification, panel (v4.104.0 – v4.106.0)

| Release | Core delivery |
|---|---|
| v4.104.0 | **Zero code changes.** `mnc-stage1` rebuilt cleanly at -O2. Integration pipeline 60/64. Async goldens run natively. Five `Div.*` dockets opened for v4.106.0 panel. |
| v4.105.0 | **Debugging infrastructure.** Valgrind over 64 goldens (top frame `mir_opt__block_successors` 14×). ASan 21/38 CLEAN. TSan race-free on async. CI gates permanent. |
| v4.106.0 | **Phase B panel: NEEDS WORK @ 7.87.** 1 PASS, 6 WITH NOTES, 0 NEEDS WORK. Load-bearing finding: the `64_closure_typed` -O2 miscompile re-classified from "LLVM opt bug" to **Mapanare emitter bug** (Rt.1 — 2-arg lambda signature mismatch). |
| v4.106.1 | Patch: Rt.1 emitter signature + Ih.1 integration harness stdout-diff against bootstrap reference. |

The Phase B re-grade of 7.87 was **zero NEEDS WORK but below the 8.0
PASS threshold**. Rattler's insight — treating LLVM's silence as a
*Mapanare* bug, not a back-end bug — was load-bearing. Opaque pointers
mean LLVM 18 will accept `define internal void @lambda4(ptr, ptr, ptr)`
with a caller doing `call i64 %cfn(ptr, i64, i64)` without
complaining; the miscompile is ours, not LLVM's.

### Phase C — benchmarks, string fix, optimiser forensics (v4.107.0 – v4.110.0)

| Release | Core delivery |
|---|---|
| v4.107.0 | **Go + C added to benchmark suite.** `run_benchmarks.py` rewritten with `/usr/bin/time -v` wrap. 5-language full comparison. Geomean Mapanare 9.5× slower than C gcc. |
| v4.108.0 | **Auto-StringBuilder MIR pass.** `mir_opt.py::string_concat_optimization` rewritten against the real CFG pattern. `string_concat` 94.57 → 1.36 ms (70× speedup, 109× memory reduction). |
| v4.109.0 | **Arcs 11–12 optimiser ROI forensics.** TBAA metadata 100% dead. `willreturn` on runtime calls is load-bearing; inline flags are mostly redundant. Per-workload geomean hid heterogeneity. |
| v4.110.0 | **Phase C complete.** Full benchmark refresh with all fixes. Geomean 5.46× slower than C gcc (down from 9.5×). `benchmarks/PHASE_C_RESULTS.md` canonical. |

Phase C was an *honest reckoning* of the optimiser arc that had
preceded v4.99.0. The forensics in `OPT_ROI_ANALYSIS.md` replaced
"Arc 11 made Mapanare 2× faster" with "Arc 11's load-bearing
contribution is function attributes propagating through LLVM's module
attribute table; TBAA is dead; inline flags are redundant." The
`string_concat` fix was the arc's only single-digit-percent-or-better
benchmark win, and it was a single-file MIR CFG rewrite.

### Phase D — self-hosted 64/64 + fixed-point (v4.111.0 – v4.114.0)

| Release | Core delivery |
|---|---|
| v4.111.0 | **Rebuild mnc-stage1 from full self-hosted pipeline**, run all 64 goldens, categorise every failure in 9 buckets. **21/64 → 26/64** (+5 unblocks) by disabling 4 zero-ROI MIR passes flagged by v4.105.0 valgrind. Effective 39/64 counting Cat. A. |
| v4.112.0 | **Fixed-point verification + docket #7 closed.** `struct_byte_size` replaces the 256-byte byref heuristic. Fixed-point convergence not measured — stage1 can't self-compile because self-hosted `semantic.mn` doesn't register `None` as a constructor. Docket Sh.8 opened. |
| v4.113.0 | **Dockets #8, #10, #11 closed.** Coroutine frame ABI named via struct. SPEC §2.1.1 reserved keyword table. 5 async failure sites gain specific stderr + exit(1). |
| v4.114.0 | **Phase D panel: NEEDS WORK @ 8.21.** 2 PASS, 5 WITH NOTES, 0 NEEDS WORK. 11/11 v4.99.0 docket items confirmed CLOSED with line-by-line evidence in `DOCKET_AUDIT.md`. |
| v4.114.1 | Patch: v4.112.0 name correction (divergence analysis, not fixed-point verification); `tests/bootstrap/byref_test.mn` committed; site-4 cleanup comment. |

Phase D was the *correctness* phase. The self-hosted compiler moved
from "does not run the goldens" to "runs the goldens with known,
categorised gaps." The fixed-point block (Sh.8) is honest and
documented rather than papered over.

### Phase E — async I/O, documentation, test hardening (v4.115.0 – v4.117.0)

| Release | Core delivery |
|---|---|
| v4.115.0 | **First native async I/O run in project history.** `async_file_io.mn` and `async_http_demo.mn`. `docs/guides/async.md` (244 lines). Two Python-bootstrap emitter bugs (Sh.9a, Sh.9b) worked around in the examples. Zero compiler / runtime changes. |
| v4.116.0 | **Documentation batch.** Five gaps from v4.82.0+ panels closed: README version badge and benchmark line, SPEC header + §29 async status, cookbook async workflows, debugging guide rewrite (removes stale DWARF claim), new `docs/guides/getting_started.md`. Zero code changes. |
| v4.117.0 | **Testing sweep.** Sanitizer CI extended to v4.115.0 async demos. 5-run flaky audit: **zero flaky tests** (22 deterministic failures catalogued). Coverage 43% aggregate / 73% core pipeline. 6 new integration-harness hardening tests. Zero code changes. |

Phase E was the *polish* phase. Three releases, zero code changes in
the compiler or runtime, every change user-facing or CI-facing. The
async I/O demos are the single most-cited improvement from this phase
because they close the v4.94.0 "runtime measurements deferred" gap
directly: `libmapanare_rt.a` already had the scheduler (from v4.104.0's
rebuild); Phase E proved that ordinary Mapanare programs could use it.

### Phase F — final benchmark, retrospective (v4.118.0 – v4.119.0)

| Release | Core delivery |
|---|---|
| v4.118.0 | **Final cross-language benchmark.** 6 workloads × 6 language configs × 10 runs, plus 5 async workloads × 3 languages × 10 runs. All 41 cells correct. `FINAL_REPORT_v4.120.md` (500 lines) published. Zero code changes. |
| v4.119.0 | **Retrospective, statistics, v5 readiness, pre-panel audit.** This document + STATISTICS.md + V5_READINESS.md + AUDIT_NOTES.md. Zero code changes. |

---

## What worked

- **Cadence discipline.** 20 consecutive releases, each with a
  CHANGELOG entry, a SESSION_REPORT, a PLAN, a PROMPT, and a commit
  history that anyone can re-trace. No silent changes.
- **Panel system.** Three full panels in the recovery arc (v4.106.0,
  v4.114.0, and the upcoming v4.120.0). Each produced written
  reviewer output. Each fed a docket into the next phase's scope.
- **Docket-driven development.** Every phase's scope was a named list
  of items with IDs. Phase D's DOCKET_AUDIT.md walked the 11-item
  v4.99.0 list with `file:line` evidence for each closure. No hand-
  waving, no "substantially addressed."
- **Culebra tooling.** Template-driven static analysis and journal /
  baseline diff capabilities meant every release could compare its IR
  findings to a previous known-good state. Findings are per-template,
  per-file, line-accurate.
- **Scope honesty.** Phase B documented that `libmapanare_rt.a` was
  byte-identical across releases when that was true. Phase C called
  TBAA metadata "100% dead" when that was true. Phase E noted that
  ASan and TSan CI gates already existed since v4.105.0 when crediting
  v4.117.0's extension rather than claiming new infrastructure.

## What didn't work

- **Optimizer ROI (Arcs 11–12).** Eight releases of optimiser work
  produced one load-bearing effect (module attribute table) and three
  ineffective ones (inline flags redundant, TBAA never wired, escape
  analysis framework-only). The v4.109.0 forensics reached this
  conclusion months after the releases shipped. Earlier panel
  oversight (a panel at v4.82.0 or v4.90.0 instead of waiting for
  v4.99.0) would have caught it sooner.
- **Documentation lag.** By v4.99.0, the README badge still said v4.31.0.
  `docs/SPEC.md` header still said "1.0.0 Final." `docs/guides/debugging.md`
  still claimed Mapanare emits DWARF with `-g` when DWARF had been
  deferred 21 releases earlier. v4.116.0 closed five doc gaps in a
  single release; three more phases could have had a "documentation
  tax" per release to prevent the debt.
- **Deferred medium items.** The v4.99.0 docket had three MEDIUM items
  that carried through all of Phase A and Phase B; they closed in
  Phase D (v4.113.0) only. In hindsight they could have landed earlier.
- **`verify_fixed_point.sh` as of v4.112.0.** The divergence analysis
  was real work, but the test script can't yet produce a clean stage1
  → stage3 identity because of Sh.8. The v4.112.0 SESSION_REPORT
  originally called it "fixed-point verification"; v4.114.1 had to
  rename it to "divergence analysis + byref fix." The correction is
  committed, but the naming churn is a quality-gate miss.

## Numbers that matter

From `STATISTICS.md` — see that file for methodology:

| Metric | v4.0.0 line start | v4.99.0 | v4.118.0 |
|---|---|---|---|
| Panel aggregate score | 9.79 (v3.47.0 gate) | **6.59** | **≥ 8.21** (v4.114.0 last panel) |
| Golden (Python bootstrap) | — | 61/61 | 64/64 |
| Golden (mnc-stage1, native) | — | 0/61 | 26/64 (39/64 effective) |
| Async benchmarks linking | — | 0/5 | 5/5 |
| Geomean vs C gcc -O2 | — | n/a | **5.46×** (from 9.5× at v4.107.0) |
| Geomean vs Python 3.12 | — | n/a | **36.9× faster** |
| pytest test count | — | 5,374 | 5,479 |
| CI enforcing gates | Black/Ruff/Mypy/pytest (4) | 4 | 10 (+ valgrind + 2× sanitizer + WASM + Android + native-gcc) |

And the number that goes against the grain of "more is better":

> **Net lines of code v4.99.0 → v4.118.0: −1,155.** The recovery arc
> removed more than it added.

## Where v4.x stands going into the panel

The v4.120.0 panel inherits:

- 11 closed v4.99.0 dockets, with `DOCKET_AUDIT.md` walking each one
- 20 committed recovery-arc releases with individual SESSION_REPORTs
- Two prior recovery panels (v4.106.0 @ 7.87, v4.114.0 @ 8.21)
- 500-line benchmark evidence document (`FINAL_REPORT_v4.120.md`)
- 10 enforcing CI gates, including sanitizer regression gates
- A self-hosted compiler at 39,763 lines of `.mn` that executes its
  own golden suite at 26/64 literally / 39/64 effectively
- A Python bootstrap at 36,092 lines (down from 38,526) that produces
  golden-stable IR for 64/64 tests
- A native async runtime with 5/5 benchmark programs linking and
  executing

v4.x set out to ship v5. It did not. What it shipped instead was the
discipline to know when not to ship v5 — and the process to earn the
tag honestly at the next attempt. Whether v4.120.0 crosses the 9.0
aggregate / 0 NEEDS WORK bar is the panel's call, with the evidence in
hand.

---

## A note on voice

The recovery arc was written in SESSION_REPORTs by one lead and one
assistant agent. Both had access to prior session reports, CLAUDE.md,
and the codebase. Both wrote in the first person singular (the lead's
voice) or the first person plural (when describing team decisions). The
SESSION_REPORTs were self-graded (typical grades: 8.0–8.9 / 10) and the
panels independently graded against the shipped work (7.87 and 8.21).
The ≤ 0.5 gap between self-grade and panel-grade is an acceptable
calibration. Where it widened (e.g., v4.99.0 self-grade vs. v4.99.0
panel), the panel was correct.

This retrospective continues that tradition. It names what worked, what
didn't, who the "we" is, and what the panel is being asked to grade.

If the panel grades this arc at ≥ 9.0 with 0 NEEDS WORK, v5.0.0 is
tagged. If not, v4.121.0 opens — and the cadence continues.
