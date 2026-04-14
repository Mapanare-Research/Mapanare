# v4.114.0 Panel Summary — Phase D Grade

> 7 reviewers. Holistic grade covering v4.111.0-v4.113.0
> (3 releases: Phase D self-hosted compiler maturity).
> Panel date: 2026-04-14.

## Verdict Table

| Reviewer | Domain | Grade | Verdict |
|----------|--------|------:|---------|
| Rattler | LLVM / codegen | **8.2 / 10** | PASS WITH NOTES |
| Viper | Memory safety | **8.5 / 10** | **PASS** |
| Anaconda | Toolchain / CI | **7.8 / 10** | PASS WITH NOTES |
| Cobra | ABI / fixed-point | **8.0 / 10** | PASS WITH NOTES |
| Coral | Language design | **8.3 / 10** | PASS WITH NOTES |
| Boa | Developer experience | **8.5 / 10** | **PASS** |
| Mamba | C runtime | **8.2 / 10** | PASS WITH NOTES |

**Aggregate: 8.21 / 10**
**PASS count: 2 · PASS WITH NOTES count: 5 · NEEDS WORK count: 0**

## Decision

Per the decision rule in `docs/roadmap/v4/v4.114.0/PROMPT.md`
"Decision 1":

> **Default: same standard as all previous panels.** Aggregate
> >= 8.5 target. Zero NEEDS WORK. The bar does not change because
> the previous panel was harsh — the previous panel was harsh
> because there were real problems. Those problems should now be
> fixed.

Applied: aggregate **8.21 < 8.5** — below the Phase D PASS
threshold even though no single reviewer returned NEEDS WORK.

**Decision: NEEDS WORK. v4.114.1 patch release.**

The gap is 0.29. The panel is **not in crisis**: the v4.106.0 panel
ran 7.87 with 3 reviewers at 7.5 and zero PASS verdicts; v4.114.0
runs 8.21 with 2 PASS verdicts and all reviewers above 7.5. The
direction is positive (v4.106.0 → v4.114.0: +0.34), but the bar
wasn't cleared.

Per `POST_RECOVERY_MASTER_PROMPT.md §12` ("the lead does not
self-certify arcs") the rule applies mechanically; 8.21 is not
rounded to 8.5.

## What the Panel Agreed On

### Unanimous CLOSED — all 11 v4.99.0 docket items

Every reviewer who commented on a docket item confirmed its closure:

- **#1** Tagged-pointer UB (v4.100.0) — `is_heap` bitfield
  (Viper, Mamba, Rattler confirmed)
- **#2** List indexing use-after-free (v4.101.0) — `_move_resource`
  at 6 sites (Rattler, Viper confirmed)
- **#3** Scheduler symbols in `libmapanare_rt.a` (v4.102.0) —
  `nm` output shows all 4 exports (Mamba confirmed)
- **#4** else/sino drop glue (v4.103.0) — `63_else_sino` passes
  (Coral, Rattler confirmed)
- **#5** Closure type annotations (v4.103.0) — `ClosureCall`,
  `ClosureCreate` in `lower.py` (Coral, Rattler confirmed)
- **#6** README perf disclosure (Phase C) — 50× vs Python /
  4.85× vs C gcc geomeans in README
- **#7** Byref size heuristic (v4.112.0) — `struct_byte_size` +
  `is_byref_type_st`; algorithm matches Python `_tsz`
  (Cobra PRIMARY, Rattler confirmed)
- **#8** Coroutine frame decoupling (v4.113.0) —
  `mn_coro_frame_prefix_t`; zero raw offsets in executable code
  (Viper PRIMARY, Mamba confirmed)
- **#9** String concat performance (v4.108.0) — auto-StringBuilder
  55× wall, 109× memory (Coral, Rattler via PHASE_C_RESULTS)
- **#10** SPEC keyword section (v4.113.0) — §2.1.1 Master List
  with 42 entries, both lexers cross-referenced
  (Coral PRIMARY, Boa confirmed)
- **#11** Async error messages (v4.113.0) — 7 messages across 5
  sites in `mapanare_runtime.c`
  (Boa PRIMARY, Viper + Mamba confirmed)

### Universal agreement on regressions

**Zero regressions** from Phase D. All three releases held:
- Golden 26/64 through mnc-stage1 (stable v4.111.0 → v4.114.0)
- Golden 63/64 through Python bootstrap (pre-existing
  `51_match_guards_and_or`)
- Async native outputs 42/43/110 on 55/56/57
- Sanitizer baseline: 0 valgrind errors / 0 ASan errors on the
  async + struct subset

## What the Panel Flagged (findings for v4.114.1)

### HIGH — Release name accuracy (Rattler, Cobra)

**Finding:** v4.112.0 is named "fixed-point verification" but
the 3-stage fixed-point script does not converge — it fails at
Stage 1 with `Undefined variable 'None'` (Sh.8 blocker). The
release delivered the byref fix and a divergence classification
artifact; it did *not* deliver fixed-point convergence.

**Fix:** Update CLAUDE.md and the v4/README.md row for v4.112.0
to say "divergence analysis + byref fix" rather than "fixed-point
verification." Leave the SESSION_REPORT (which is honest) as-is,
but don't let the one-line summary overclaim.

**Owner:** v4.114.1 doc fix.

### HIGH — Commit the byref test case (Cobra)

**Finding:** `/tmp/byref_test.mn` (referenced in v4.112.0
SESSION_REPORT as the acceptance test for the byref fix) was never
committed. The test is regenerable from the SR text but leaves no
in-tree artifact.

**Fix:** Add `tests/golden/byref_test.mn` (or `tests/bootstrap/`)
with the Small/Large struct IR assertion.

**Owner:** v4.114.1.

### MEDIUM — CI gate for self-hosted pipeline (Anaconda)

**Finding:** `scripts/test_native.py --stage1 mnc-stage1` on the
full golden suite is NOT a CI gate. A drop from 26/64 to 25/64
would not fail CI.

**Fix:** Add a `self-hosted-golden` job to `sanitizers.yml` or
`ci.yml` that runs the full suite and fails on count regression.

**Owner:** Phase E (carry-forward from v4.106.0 finding).

### MEDIUM — Fixed-point CI is red (Anaconda)

**Finding:** The fixed-point job is out of required-checks because
Sh.8 keeps Stage 1 red. The gate currently provides no signal.

**Fix:** Either close Sh.8 (Phase E work), or document the gate's
absence so reviewers don't assume coverage.

**Owner:** Phase E.

### LOW — Site 4 cleanup comment (Mamba)

**Finding:** `__mn_coro_register_wait` overflow-full path doesn't
free the coroutine frame before `exit(1)`. Correct in practice
(exit reclaims) but an uncommented subtle invariant.

**Fix:** Add `/* exit(1) below reclaims the frame */` comment.

**Owner:** v4.114.1 (tiny).

### LOW — Reachability tests for async guards (Boa)

**Finding:** 4 of 5 async error sites are untested in CI; they
require env stress (RLIMIT_NPROC, OOM, queue overflow) that's
fragile to reproduce.

**Fix:** Add a debug-only env var (e.g.,
`MAPANARE_ASYNC_FAIL_AT_WORKER=2`) that lets a pytest mock the
failure.

**Owner:** Phase E.

### LOW — Pre-existing user-code coroutine leaks (Viper, Mamba)

**Finding:** Async goldens 56/57 leak in user `__mn_Int_box` sites.
Known since v4.102.0, not introduced by Phase D. Open as
**Coro.1** for a future release.

**Owner:** Phase E.

## v4.114.1 Patch Scope

Quick wins only — the panel's two HIGH findings plus the LOW
comment fix:

1. Doc fix: v4.112.0 name clarification (CLAUDE.md + v4/README.md)
2. Test commit: `tests/bootstrap/byref_test.mn` or equivalent
3. Code comment: site 4 cleanup intent in `mapanare_runtime.c`

Estimated scope: ~50 lines across 4 files. No new features. No
new code beyond the comment. v4.114.1 ships then the panel
re-grades (delta panel, 2-3 reviewers; Rattler + Cobra + Anaconda
are the right set).

If the v4.114.1 delta panel returns >= 8.5 (primary reviewers
moving Rattler 8.2 → 8.5 and Cobra 8.0 → 8.3), Phase D closes.
Otherwise a second patch or a scope review.

## Comparison to v4.106.0 (Phase B panel)

| | v4.106.0 | v4.114.0 | Δ |
|---|---:|---:|---:|
| Rattler | 7.8 | 8.2 | +0.4 |
| Viper | 7.5 | 8.5 | +1.0 |
| Anaconda | 7.8 | 7.8 | 0.0 |
| Cobra | 7.5 | 8.0 | +0.5 |
| Coral | 8.0 | 8.3 | +0.3 |
| Boa | 8.5 | 8.5 | 0.0 |
| Mamba | 8.0 | 8.2 | +0.2 |
| **Aggregate** | **7.87** | **8.21** | **+0.34** |
| PASS count | 1 | 2 | +1 |
| NEEDS WORK count | 0 | 0 | 0 |

Every reviewer who moved, moved up. The work across Phase C + D
is visible in the scores. The gap to PASS is small (0.29 vs
v4.106.0's 0.13 to its own 8.0 bar) but real.

## Phase D retrospective (what worked)

1. **Minimum-surface-area discipline held through 3 releases.**
   Total executable-code delta across Phase D: ~90 lines across 2
   files (runtime + self-hosted emitter). Every release was
   single-file or two-file scope. Single-item-per-release worked.

2. **Byte-for-byte control experiments.** v4.113.0's
   `async-valgrind.md` — checked out HEAD~4, rebuilt, re-ran
   valgrind, compared byte counts. That's the right shape of proof
   for ABI-adjacent changes. Every reviewer who saw the artifact
   scored it positively.

3. **Dockets opened honestly.** Sh.1 through Sh.8 are new
   carry-forwards, named at opening, with root-cause classification.
   The panel found them where expected.

## Phase D retrospective (what to improve)

1. **Release names should match what the release delivers.**
   v4.112.0 was the standout. "Divergence analysis + byref fix"
   would have been accurate; "fixed-point verification" overreached.
   Phase E should name its releases by what they land, not by what
   they aim at.

2. **Test artifacts need to be committed.** `/tmp/byref_test.mn`
   illustrates the problem — the test existed, the output was
   described in prose, but the artifact was ephemeral. The
   reproducibility cost outweighed the "it's just a one-off" savings.

3. **Culebra scan infrastructure gap persists.** Three consecutive
   panels could not scan the full `main.ll`. Phase E: either
   narrow the scan target or fix the scanner.

## Status

Phase D: **DOES NOT CLOSE YET.** v4.114.1 patch scheduled.

Phase E is not unblocked until v4.114.1 lands and the delta panel
grades >= 8.5.

The direction is positive. The docket is genuinely empty. The
remaining gap is process / naming / reproducibility, not
correctness.
