# v4.106.0 Panel Summary — Phase B Grade

> 7 reviewers. Holistic grade covering v4.100.0–v4.105.0 (6 releases: Phase A bug sprint + Phase B verification).
> Panel date: 2026-04-14.

## Verdict Table

| Reviewer | Domain | Grade | Verdict |
|----------|--------|------:|---------|
| Rattler | LLVM / codegen | **7.8 / 10** | PASS WITH NOTES |
| Viper | Memory safety | **7.5 / 10** | PASS WITH NOTES |
| Anaconda | Toolchain / CI | **7.8 / 10** | PASS WITH NOTES |
| Cobra | ABI / fixed-point | **7.5 / 10** | PASS WITH NOTES |
| Coral | Language design | **8.0 / 10** | PASS WITH NOTES |
| Boa | Developer experience | **8.5 / 10** | **PASS** |
| Mamba | C runtime | **8.0 / 10** | PASS WITH NOTES |

**Aggregate: 7.87 / 10**
**PASS count: 1 · PASS WITH NOTES count: 6 · NEEDS WORK count: 0**

## Decision

Per the decision rule in `docs/roadmap/v4/v4.106.0/PLAN.md` §Phase 6:

> **If PASS (aggregate ≥ 8.0, 0 NEEDS WORK):** Phase B complete. Proceed to Phase C.
> **If NEEDS WORK:** Issues go into v4.106.1 patch release.

Applied: aggregate **7.87 < 8.0** — below the Phase B PASS threshold
even though no single reviewer returned NEEDS WORK.

**Decision: NEEDS WORK. v4.106.1 patch release.**

The gap is 0.13. The panel is clearly not in crisis (compare v4.99.0's
6.59 aggregate that triggered Phase A). Three reviewers sat at 7.5, two
at 7.8, two at ≥ 8.0 — the pattern is "substantial improvement,
verification layer has cracks." Per
`POST_RECOVERY_MASTER_PROMPT.md §12` (**"the lead does not
self-certify arcs"**) the rule applies mechanically; the 7.87 is not
rounded up.

## What the Panel Agreed On

### Unanimous CLOSED (6 of 7 reviewers explicitly confirmed; 1 by silence)

All 5 critical / high v4.99.0 docket items are CLOSED with verifiable
evidence:

- **#1 Tagged-pointer UB** — `is_heap` bitfield at `mapanare_core.h:60`,
  all helpers deleted, ABI preserved at 16 bytes (Mamba, Viper,
  Rattler, Cobra verified).
- **#2 List indexing drop-glue** — `_move_resource` at 6 Python-emitter
  sites plus v4.103.0 boxed-payload extension (Coral, Rattler confirmed
  via `62_list_output.mn`).
- **#3 `libmapanare_rt.a` scheduler exports** — all 6 exports present;
  `nm` proves it; 3/3 async goldens run natively (Anaconda, Mamba).
- **#4 `else` / `sino` end-to-end** — reproduced through full pipeline
  including `opt -O2`; golden 63 produces expected output in all
  reviewers' local runs.
- **#5 Closure type annotations** — lowering changes in `lower.py` are
  present; bootstrap interpreter and `-O0` / `-O1` paths produce
  correct output (Coral, Rattler).

### Unanimous positive new finding

**v4.102.0's async scheduler is TSan-clean.** 3/3 async goldens run
under TSan-instrumented `libmapanare_rt_tsan.a` with zero data races
and correct output (42, 43, 110). Viper's v4.99.0 concern about
concurrent scheduler soundness is directly addressed. Every reviewer
that touched async flagged this as the strongest positive signal in
the release.

### Unanimous negative finding

**The `64_closure_typed.mn` miscompile under `opt -O2` is real.**

The PRE_PANEL_AUDIT initially classified this as an LLVM opt bug.
**Rattler's review overturned that classification**: reading the
emitted IR shows the 2-arg `sum` lambda emits `define internal void
@lambda4(ptr %__env_ptr, ptr %a, ptr %b)` — `void` return and `ptr`
parameters — while the caller does `call i64 %cfn.53(ptr, i64, i64)`.
LLVM's opaque-pointer verifier accepts the malformed IR; `-O0`
accidentally works due to register ABI; `-O2` inlines and propagates
the previous `double(10)` result into the output.

This promotes Cl.1 from "LLVM optimizer miscompile" to **Rt.1 HIGH:
Mapanare emitter bug, multi-arg lambda signature mismatch**. It is
the load-bearing reason this panel returns below 8.0.

## What the Panel Disagreed On

- **Docket item #8 (coroutine frame coupling)**: Viper holds it
  PARTIAL — the immediate offset bug is fixed but broader LTO
  fragility is untested. Other reviewers accepted it as CLOSED.
- **ABI divergence Div.3 (Option `{i1,i64}` vs `{i1,ptr}`)**: Cobra
  grades it HIGH (fixed-point blocker). Other reviewers grade it
  MEDIUM (latent but not immediately harmful). Does not change the
  verdict outcome either way.

## Consolidated Action Items for v4.106.1

Ranked by the panel's collective prioritisation:

| # | Item | Severity | Opened by | Blocking for |
|---|---|---|---|---|
| Rt.1 | Fix multi-arg lambda emitter (void return + ptr params → correct i64 signatures) | **HIGH** | Rattler | 64_closure_typed under `-O2` |
| Rt.2 / Ih.1 | Patch integration harness to diff stdout vs bootstrap reference | **HIGH** | Rattler + Anaconda | Silent wrong-output regressions |
| Rt.3 | Audit emitter-generated IR for similar signature mismatches (Div.1, Div.2, Div.3 cluster) | MEDIUM | Rattler | ABI parity |
| As.1 / Vg.2 / Vg.3 | Fix `__mn_list_free` shared-buffer heap-UAF in `mapanare_core.c` (Mamba's generation-counter sketch, ~3-4h, ~40 LOC) | MEDIUM | Mamba | 12 golden tests |
| Cb.1 | Unify Option payload ABI across bootstrap / stage1 (`{i1,i64}` everywhere) | MEDIUM | Cobra | fixed-point self-compile |
| Vp.1 | Add LTO build job to CI (exercises item #8 fragility concern) | MEDIUM | Viper | — |
| Bo.1 | Rewrite `stage1` async error ("Undefined function 'block_on'" → "mnc-stage1 does not yet support async / block_on; compile via Python bootstrap") | LOW | Boa | DX polish |

### v4.106.1 scope (narrow)

Per the Phase 6 rule "Scope is narrowly defined by the panel's
findings. Fix only what the panel flagged." v4.106.1 targets the two
**HIGH** items:

1. **Rt.1** — fix multi-arg lambda emitter. Add a targeted regression
   test that runs `64_closure_typed` through `opt -O2`.
2. **Rt.2 / Ih.1** — integration-pipeline stdout-diff. Any test that
   currently PASSES exit-code must also match bootstrap's stdout.
   Expect 1-3 additional failures to surface when the gate activates;
   those are real bugs, document and fold in.

Everything else (`As.1`, `Cb.1`, `Vp.1`, `Bo.1`, Div.* residue) is
Phase C scope. The panel is explicit that they are not v4.106.1
gates — only the HIGH items are.

## Re-panel after v4.106.1

Only the 3 affected domains re-grade:
- **Rattler** — on Rt.1 specifically. Does the emitter now produce
  valid IR for the `sum = (a, b) => a + b` pattern?
- **Anaconda** — on Rt.2 / Ih.1. Does the integration pipeline now
  reject tests whose stdout differs from bootstrap?
- **Coral** — on whether `64_closure_typed` passes end-to-end
  through the `-O2` pipeline with correct output.

Viper, Cobra, Boa, Mamba carry forward their current grades unless
the patch touches their domain. If the 3 re-grades come back PASS
(each ≥ 8.0), the arc closes and Phase C opens at v4.107.0.

## Score Context

| Panel | Aggregate | Outcome |
|-------|----------:|---------|
| v4.26.0 (crisis) | 8.2 / 10 | Recovery triggered |
| v4.31.0 (recovery close) | 9.343 / 10 | Recovery complete |
| v4.76.0 (plan end) | 9.0+ / 10 | Plan complete |
| v4.96.0 (Arc 13 close) | 8.57 / 10 | PASS |
| v4.99.0 (v5 gate) | 6.59 / 10 | Option B — continue (Phase A) |
| **v4.106.0 (Phase B grade)** | **7.87 / 10** | **NEEDS WORK → v4.106.1 patch** |

The +1.28 delta from v4.99.0 is the largest improvement since the v4.31.0 recovery arc close. Phase A + Phase B delivered real, verifiable fixes. The 0.13 shortfall from PASS is a verification-layer gap, not a recovery crisis.

## Reviewer Files

- `01-rattler.md` — LLVM / codegen
- `02-viper.md` — memory safety
- `03-anaconda.md` — toolchain / CI
- `04-cobra.md` — ABI / fixed-point
- `05-coral.md` — language design
- `06-boa.md` — developer experience
- `07-mamba.md` — C runtime

Plus `PRE_PANEL_AUDIT.md` (pre-panel fact-check) and this summary.
