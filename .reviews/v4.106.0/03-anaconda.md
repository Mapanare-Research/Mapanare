# Anaconda v4.106.0 Review — Toolchain / CI

## Score: 7.8/10
## Verdict: PASS WITH NOTES

## Context: v4.99.0 → v4.106.0

At v4.99.0 I gave 6.5/10 NEEDS WORK on three counts: integration pipeline
untested end-to-end, `libmapanare_rt.a` missing scheduler exports, and CI
gates insufficient for regression prevention. Two of three are now
structurally closed. The third — CI regression prevention — has been
materially strengthened by v4.105.0's three sanitizer jobs but is still
leaky in the one place this panel spotlighted: the integration harness
signals PASS on exit code alone.

## v4.99.0 item #3 (libmapanare_rt.a scheduler exports)

**CLOSED.** Pre-panel audit Claim 5: `nm` shows `__mn_coro_spawn`,
`__mn_coro_register_wait`, `__mn_coro_scheduler_{init,destroy,register,run}`
— all 6 entry points present. 3/3 async goldens run natively with
correct output (42, 43, 110), valgrind-clean, TSan-clean. Not my worry
anymore.

## Integration pipeline (v4.104.0)

`INTEGRATION_RESULTS.md` reports **60/64 PASS** through the full
`emit-llvm → llvm-as → opt -O2 → llc → clang -no-pie → run` pipeline in
56 s wall time, with 2 SKIP (stdin/network) and 2 genuine FAILs
(`51_match_guards_and_or` at emit; `47_try_operator` at llvm-as). The
fact that `opt -O2` rejected zero IRs across 62 tests is a real,
release-gate-quality signal.

**But the 60 number is exit-code PASS**, and I reproduced the gap on my
own machine:

```
$ /tmp/a_bin   # 64_closure_typed through full pipeline
10
-3
20
10      # ← should be 15
exit=0  # ← harness marks PASS
```

The harness's PASS criterion is `exit==0`. `64_closure_typed` exits 0
while emitting the wrong fourth value under `opt -O2`. The integration
harness has no bootstrap-stdout diff. This is exactly `Ih.1` in the
pre-panel audit and I want to call it by its first name: a false-green
CI signal is worse than no signal — it invites silent wrong-output
regressions into `main`.

## CI gates (v4.105.0 sanitizers.yml)

Three jobs — `valgrind`, `asan`, `tsan-async` — confirmed by YAML parse.
All three use baseline-comparison regression logic (not absolute-zero
gates, which would be unshippable given 36 Vg ERRORS / 17 ASan ERRORS
exist today). The self-test of `check_valgrind_baseline.py` against its
own committed TSV returned `36 ERRORS (committed) | 36 ERRORS (fresh) —
OK exit=0`. Same-shape self-test for the ASan checker per the v4.105.0
session report.

The gate design is right: new CLEAN→ERROR transitions fail; existing
ERRORs are grandfathered with docket references; TSan uses
`halt_on_error=1` since 0-race on async is the invariant we ship. The
per-artifact upload (14-day retention) means reviewers can post-mortem
failures without re-running locally. This is a professional CI posture.

Total gate count: **11** (8 pre-existing + 3 new). Tooling footprint at
26 scripts under `scripts/` (`*.sh`/`*.py`) is substantial and organized.

## Test infrastructure completeness

What I'd also want, in priority order:

1. **Stdout-diff in the integration harness** — the `Ih.1` fix. Golden
   reference stdout per test, diffed against bootstrap output. Trivial
   to add; closes the `64_closure_typed` false-green class entirely.
2. **LTO build in CI** — v4.99.0 item #8 flagged "coroutine frame layout
   fragile under LTO." Measurements show no LTO build exists. Phase C.
3. **UBSan pass** — the Phase A work removed tagged-pointer UB; I want a
   `ubsan` job to guarantee we don't reintroduce it (or discover new UB).
4. **Nightly long-soak** — sanitizers.yml fires per push. A nightly
   matrix that runs integration + sanitizers on a larger example corpus
   (stdlib + playground) would catch regressions the 64-test goldens
   miss.

## Findings

- Integration harness's PASS semantics are exit-code only; one confirmed
  false-green (`64_closure_typed`). Others may exist and we wouldn't
  know — nobody has diffed stdout on the other 59 "PASS" entries.
- `sanitizers.yml:50` caveat: runtime CI trigger not confirmed from WSL
  in pre-panel audit (Claim 20). YAML is valid; the first production
  push after v4.106.0 tag will surface any GitHub-side misconfiguration.
- `tsan-async` rebuilds `libmapanare_rt_tsan.a` inline (lines 134-145)
  rather than via a build script. Duplicated build knowledge. Minor —
  factor into `scripts/build_tsan_rt.sh` next release.

## Docket items you would open

- **`Ih.1` MEDIUM already exists** — I endorse it and recommend elevating
  to HIGH for Phase C. A false-green integration harness is a CI
  correctness bug, not a nice-to-have.
- **New `Ih.2` LOW** — factor `tsan-async` RT build out of the workflow
  YAML into a script (mirrors `build_asan.sh` pattern).
- **New `CI.1` LOW** — add post-merge sanity run on `main` that actually
  exercises the upload-artifacts path, to catch workflow drift before
  it's load-bearing.

## Grade justification

Up from 6.5 to 7.8 because the tooling uplift is real: scheduler
exports present, integration pipeline measured end-to-end, three
sanitizer gates live with baseline-aware regression checkers, 26-script
tooling surface, crash breadcrumbs async-signal-safe. Capped below 8.5
because the harness gap is structural and known — `Ih.1` means the
top-line "60/64 PASS" number overstates what the CI can actually enforce.
Closing Ih.1 in Phase C would take this to 9.0+.

## One-line summary

Real CI uplift — three sanitizer jobs with baseline checkers are the
genuine article — but the integration pipeline's exit-code-only PASS
lets wrong-output regressions slip through; fix `Ih.1` in Phase C.
