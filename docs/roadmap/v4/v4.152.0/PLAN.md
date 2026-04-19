# Mapanare v4.152.0 — E8: re-enable LICM + inlining in self-hosted path

> **The dormant-passes experiment.** In v4.111.0 four MIR passes were
> disabled (`strength_reduce`, `inline_small_functions`, `licm`,
> `escape_analysis`) because v4.109.0's forensic analysis rated them
> zero-ROI and because they crashed `lower__verify_block` on many
> goldens. At that time goldens were 21/64. Today (post-Ge.1 close,
> post-Sh.2 arc) goldens are 54/66 through `mnc-stage1` and the
> verifier is robust. This release re-evaluates those four passes
> under current conditions — re-enable one at a time, measure compile
> time + stage2.ll line count + benchmark delta, keep only those that
> earn their ROI.

**Status:** PLANNED
**Breaking:** No (self-hosted optimizer toggles; no API change)
**Prerequisite:** v4.151.0 shipped (E7 allocator recorded)
**Estimated work:** 2–4 days
**Theme:** E8 — self-hosted MIR optimizer pass triage

---

## Why this release, why now

The four dormant passes are documented at
`mapanare/self/mir_opt.mn:1233-1258`. Each has a comment naming v4.109.0
(the zero-ROI analysis) and v4.111.0 (the disable commit). Each comment
says essentially the same thing: "LLVM's own pass at -O2 does the same
work; disabling the self-hosted pass costs nothing."

That was true at v4.111.0. It may not be true today.

Two things changed across the v4.120.0 → v4.143.0 arc:

1. **Goldens grew from 21/64 → 54/66.** The test surface is 2.5× larger.
   A pass that crashed 13 tests at v4.111.0 might crash zero tests now
   if the underlying MIR invariants that were failing have since been
   repaired (Sh.2, Sh.8, Sh.11, Sh.12, Ge.1 all closed invariant bugs).
2. **The Python MIR optimizer has since been simplified** (v4.123.0
   dead-code sweep removed the legacy Python `optimizer.py`). What
   remains in `mapanare/mir_opt.py` is tighter. For parity, re-enabling
   a self-hosted pass also requires a Python-side re-enable (or a
   documented divergence) so the bootstrap and self-hosted outputs stay
   close.

The E8 experiment is the honest follow-up: if LLVM at -O2 really
subsumes the self-hosted pass, re-enabling has zero effect, we document
that fact, and the passes stay dormant with a refreshed comment. If
the self-hosted pass now *does* earn ROI — either shrinking stage2.ll
line count or improving a benchmark — it comes back on.

Expected outcomes, in order of likelihood:
- `strength_reduce`: likely still zero-ROI. LLVM's `-mem2reg` +
  `-instcombine` at -O2 covers this.
- `inline_small_functions`: plausibly 5–15 % compile-time savings on
  stage2 (fewer MIR → LLVM calls to inline). No runtime delta.
- `licm`: plausibly a stage2.ll line count shrink (hoisting invariants
  out of loops). No runtime delta (LLVM's own LICM runs post-codegen).
- `escape_analysis`: highest risk (v4.111.0 comment says the pass is
  "scaffold, not production"). Likely still dormant unless the scaffold
  has quietly become useful.

## Baseline

```bash
echo "4.152.0" > VERSION
make build-rt
python3 scripts/build_stage1.py

# Capture the canonical measurements
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 \
  | tee docs/roadmap/v4/v4.152.0/goldens-baseline.log
wc -l mapanare/self/main.ll             # self-hosted emitter output
wc -l /tmp/stage2.ll /tmp/stage3.ll     # post-verify_fixed_point
md5sum /tmp/stage2.ll /tmp/stage3.ll

# Compile-time benchmark — how long to compile the self-hosted stack
time python3 scripts/build_stage1.py 2>&1 | tee docs/roadmap/v4/v4.152.0/build-baseline.log

# Full cross-language + async bench for non-regression floor
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.152.0-baseline.json
python3 benchmarks/async/run_async_benchmarks.py --runs 20 \
  --output benchmarks/async/v4.152.0-baseline.json
```

Record in `docs/roadmap/v4/v4.152.0/BASELINE.md`:
- stage2.ll + stage3.ll line counts + md5
- `main.ll` line count
- `build_stage1.py` wall time
- Goldens: 54/66 through `mnc-stage1`
- Cross-language + async geomeans (carried-forward from v4.151.0)
- Reg.1 gate: `check_struct_registry.py` green

## Hypothesis

> *"LLVM's -O2 pipeline subsumes most of what the four dormant
> MIR passes would do. Re-enabling them today will either (a) have
> zero effect (both stage2.ll and benchmarks byte-/perf-identical) or
> (b) shrink stage2.ll line count on a small subset of tests without
> changing runtime perf. Outcome (a) is expected for strength_reduce
> and escape_analysis; outcome (b) is plausible for inline_small_functions
> and licm."*

The experiment either confirms the v4.111.0 rationale (honest refresh
of the comments) or updates it (one or two passes come back on).

## Phased work

### Phase 1 — Baseline snapshot (everything the experiment compares to)

```bash
cp /tmp/stage2.ll docs/roadmap/v4/v4.152.0/stage2-baseline.ll
cp /tmp/stage3.ll docs/roadmap/v4/v4.152.0/stage3-baseline.ll
cp mapanare/self/main.ll docs/roadmap/v4/v4.152.0/main-baseline.ll

# Golden IR snapshot for the 4 test IR diffs that tend to move with optimizer passes
python3 scripts/ir_doctor.py snapshot
# produces tests/golden/*.stage1.ll ; copy the key ones:
cp tests/golden/03_function.stage1.ll docs/roadmap/v4/v4.152.0/03_function-baseline.ll
cp tests/golden/11_closure.stage1.ll docs/roadmap/v4/v4.152.0/11_closure-baseline.ll
cp tests/golden/26_generics.stage1.ll docs/roadmap/v4/v4.152.0/26_generics-baseline.ll
```

### Phase 2 — Pass 4: re-enable `strength_reduce` (~0.5 day)

```mn
// mapanare/self/mir_opt.mn:1238
// BEFORE
let f5: MIRFunction = f4
// AFTER
let f5: MIRFunction = strength_reduce_function(f4)
```

Rebuild and verify:

```bash
bash scripts/rebuild.sh                          # full cycle
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 \
  2>&1 | tee docs/roadmap/v4/v4.152.0/goldens-P4.log
bash scripts/verify_fixed_point.sh --keep 2>&1 | tail -10

# Line-count deltas
wc -l /tmp/stage2.ll
diff docs/roadmap/v4/v4.152.0/stage2-baseline.ll /tmp/stage2.ll | wc -l

# Sanitizer canary (Reg.1 gate catches struct-field drift; pass-interaction
# bugs may slip through; run full valgrind sweep)
VG_OUTDIR=/tmp/vg_v4152_P4 bash scripts/valgrind_all_goldens.sh 2>&1 | tail -5
bash scripts/run_asan_goldens.sh 2>&1 | tail -5

# Benchmark delta
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.152.0-P4.json
```

**Keep criteria:**
- Goldens still 54/66 (no regression)
- Valgrind + ASan still zero
- stage2.ll shrinks or holds (not grows)
- Compile time improves or holds
- Benchmark delta within 5 % rule

If all five hold AND there's a real ROI (stage2.ll shrinks ≥ 1 %, or
compile time drops ≥ 5 %, or a benchmark improves ≥ 5 %), keep enabled.
Otherwise roll back and update the v4.111.0 comment with a "v4.152.0
re-evaluation confirms zero ROI" note.

### Phase 3 — Pass 5: re-enable `inline_small_functions` (~1 day)

Same loop as Phase 2, applied to line 1244. This is the pass most
likely to pay — the self-hosted stage is MIR-heavy, and inlining at
the MIR level lets downstream passes (constant fold, DCE) cascade.

Special attention: the v4.111.0 comment notes the inliner "produces
invalid MIR (blocks with corrupted instructions list) that crashes
lower__verify_block." Post-Sh.8 / Sh.11 / Sh.12 closures, the
verifier's invariants are tighter. If the crash reappears, open an
`In.1` docket and roll back. Do not expand scope to fix the inliner
in this release.

### Phase 4 — Pass 6: re-enable `licm` (~1 day)

Line 1251. Expected effect: stage2.ll line count shrinks on
loop-heavy tests (03_function, 26_generics, 31_generic_multi if they
contain loops). No runtime perf delta (LLVM's LICM runs post-codegen
and does the same work). The value here is compiler speed, not code
speed.

Same keep criteria.

### Phase 5 — Pass 7: re-enable `escape_analysis` (~0.5 day)

Line 1258. The v4.111.0 comment explicitly says the pass is "scaffold,
not production." Expectation is this stays off. Run the loop anyway —
the arc's discipline demands that every dormant pass is re-evaluated,
not just the ones likely to pay.

If `escape_analysis_function` still crashes at `+0x3f3` on golden tests
(as v4.111.0 noted): record the crash offset in the
`PERF_EXPERIMENTS.md` entry, keep disabled, refresh the comment with
a v4.152.0 timestamp.

### Phase 6 — Python-side parity

If any self-hosted pass comes back on, update `mapanare/mir_opt.py`
to match. If the Python side's equivalent pass is already enabled
(likely; the Python dead-code sweep removed its own dormancy), record
"parity restored" in RESULTS.md. If divergence is required (e.g.,
the self-hosted pass is safe but the Python one isn't), document the
divergence in a `docs/roadmap/v4/v4.152.0/PYTHON_SELFHOSTED_DIVERGENCE.md`
so v4.153.0's MEASUREMENTS.md can cite it.

### Phase 7 — Record

Append to `docs/roadmap/v4/PERF_EXPERIMENTS.md`:

```
| E8a | strength_reduce re-enable | no-op / win / dead-end | stage2.ll ΔN | mir_opt.mn:1238 | v4.152.0 |
| E8b | inline_small_functions re-enable | ... | ... | mir_opt.mn:1244 | v4.152.0 |
| E8c | licm re-enable | ... | ... | mir_opt.mn:1251 | v4.152.0 |
| E8d | escape_analysis re-enable | ... | ... | mir_opt.mn:1258 | v4.152.0 |
```

Write `docs/roadmap/v4/v4.152.0/RESULTS.md` with the four pass-by-pass
verdicts + an "honest story" paragraph:

> *Why we disabled these in v4.111.0, what changed between then and
> now, which came back on and why, which stayed off and why.*

This is the paragraph that lands in the v4.154.0 panel's reading
pile. Make it defensible.

Write `docs/roadmap/v4/v4.152.0/SESSION_REPORT.md`.

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `BASELINE.md` written (stage2.ll lines, build time, goldens, benchmarks) | yes |
| 2 | `stage2-baseline.ll` + `stage3-baseline.ll` + `main-baseline.ll` snapshot committed | yes |
| 3 | E8a (strength_reduce) evaluated — keep or roll back, documented | yes |
| 4 | E8b (inline_small_functions) evaluated | yes |
| 5 | E8c (licm) evaluated | yes |
| 6 | E8d (escape_analysis) evaluated | yes |
| 7 | For each kept pass: stage2.ll shrinks OR compile time drops OR benchmark improves — all ≥ ROI threshold | yes |
| 8 | For each rolled-back pass: `mir_opt.mn` comment updated with "v4.152.0 re-evaluation confirms zero ROI" | yes |
| 9 | Python-side `mir_opt.py` parity — either matches or divergence documented | yes |
| 10 | Goldens: 54 / 66 (no regression) | yes |
| 11 | `RESULTS.md` written with "honest story" paragraph | yes |
| 12 | `PERF_EXPERIMENTS.md` — 4 lines added (E8a/E8b/E8c/E8d) | yes |
| 13 | Non-bootstrap pytest: ≥ 5,160 passed / 0 failed | yes |
| 14 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 15 | Valgrind: 0 ERRORS | yes |
| 16 | ASan: 0 ASAN_ERROR | yes |
| 17 | Fixed-point: within `DIFF_THRESHOLD=100` | yes |
| 18 | Reg.1 gate (`check_struct_registry.py`) green | yes |
| 19 | All 8 CI gates green | yes |
| 20 | SESSION_REPORT.md written | yes |
| 21 | Tag `v4.152.0` pushed to origin | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| A pass re-enable reintroduces a Ge.1-class silent divergence (struct-field drift not caught by Reg.1) | medium | high | Run full valgrind + ASan sweep after each re-enable; compare stage2.ll and golden IR snapshots against baseline; if diff is suspicious, bisect with `culebra diff` |
| `inline_small_functions` crashes `verify_block` as it did at v4.111.0 | medium | medium | Roll back; open In.1 docket for v5.x; record crash details in PERF_EXPERIMENTS.md |
| `licm` shrinks stage2.ll but breaks fixed-point (stage2.ll != stage3.ll beyond DIFF_THRESHOLD) | low | high | `verify_fixed_point.sh` runs on every re-enable; if threshold exceeded, roll back; the pass is more likely idempotent than not, but test confirms |
| Re-enabled pass changes stage2.ll in a way that makes MEASUREMENTS.md (v4.153.0) reference churn | low | low | Accepted cost; v4.153.0 is the pre-panel refresh, it's designed to re-capture |
| Python/self-hosted divergence if one side keeps a pass on and the other doesn't | medium | low | Document in a divergence file; v4.153.0 MEASUREMENTS.md cites it; v5.x reunifies |
| 2–4 day budget slips into v4.153.0 territory | medium | low | Accept. The pre-panel refresh can absorb a 1-day slip; if experiment concludes across releases, E8 closes in v4.153.0 itself |

## What this release does NOT do

- Does not add new MIR passes. Only re-evaluates the four dormant ones
  at `mir_opt.mn:1238/1244/1251/1258`.
- Does not touch the LLVM IR emitter. Passes operate on MIR; the
  emitter output changes only as a downstream effect of MIR changes.
- Does not backport any re-enabled pass to the v0.6.0 frozen bootstrap.
  Bootstrap stays frozen.
- Does not chase stage2.ll line count as a goal in itself. Shrinkage
  is a *sign* of ROI, not the target; runtime perf and compile-time
  perf are the actual targets.
- Does not reopen the v4.123.0 dead-code sweep (the Python
  `optimizer.py` deletion was correct; this release is about the
  self-hosted-side MIR passes specifically).

## Carry-forward after v4.152.0

- If 0 passes earn ROI: E8 is a full dead end. `mir_opt.mn` comments
  get a v4.152.0 refresh. The arc gains a credible negative result.
  The v4.154.0 panel reads this as disciplined experimentation.
- If 1–2 passes earn ROI: E8 is a win. The honest story paragraph
  frames it as "revisiting four 'dead' MIR passes and what we learned"
  (this is the blog post queued in the arc marketing payload).
- If an In.1 / Esc.1 / similar docket opens mid-experiment: scope it
  to v5.x. Do not expand v4.152.0 to fix dormant-pass internals.
- Any Python/self-hosted divergence opened becomes v5.x parity work.
  Do not block v4.153.0 pre-panel refresh on it.
