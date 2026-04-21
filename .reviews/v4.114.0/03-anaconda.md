# Anaconda v4.114.0 Review — Toolchain / CI

## Score: 7.8 / 10
## Verdict: PASS WITH NOTES

## Context

v4.106.0 I gave **7.8 / 10 PASS WITH NOTES** — CI coverage had
grown but the golden suite was still behind a single `integration`
job that rebuilt `mnc-stage1` each run. Phase D added three
releases; I grade CI coverage, harness reliability, and whether
both pipelines are genuinely tested.

## Primary lens — Golden pass through both pipelines

Re-ran on 2026-04-14:

- **Python-bootstrap**: 63/64 (`51_match_guards_and_or` pre-existing
  or-pattern issue, tracked since v4.108.0)
- **Self-hosted (`mnc-stage1`)**: 26/64

The **strict pipeline parity** a toolchain reviewer cares about:
every test that passes on one pipeline and fails on the other is a
toolchain finding. I walked the delta:

| Category | Count | Pipeline asymmetry |
|---|---:|---|
| Category A — inline-diff (semantically equivalent IR) | 13 | harness methodology, not real divergence |
| Sh.1-Sh.7 genuine self-hosted-only failures | 25 | self-hosted emitter gaps; new dockets |
| Pass on both | 26 | — |

The 25 genuine self-hosted-only failures are all documented in
v4.111.0's GOLDEN_FAILURES.md with root-cause categorization.
None of them reopens a v4.99.0 item; all are new dockets
(Sh.1-Sh.7).

**This is what I wanted.** Phase D didn't paper over the gap — it
measured it, named the categories, opened dockets per category,
and showed zero regression across three releases (21 → 26, stable
at 26). Honest toolchain work.

## Primary lens — CI coverage

`.github/workflows/`:
- **ci.yml** — format / lint / mypy / pytest + async-specific
  integration step that runs 55/56/57 natively
- **sanitizers.yml** — valgrind (64 goldens, baseline check) +
  AddressSanitizer + ThreadSanitizer on async goldens
- **integration.yml** — end-to-end build + run
- **wasm.yml** — WAT → WASM → wasmtime
- **android.yml** — cross-compile for Android NDK

CI tests the Python-bootstrap pipeline end-to-end. The
`sanitizers.yml` `valgrind` job runs against `mnc-stage1` compiling
each golden — that exercises the self-hosted compiler binary, but
not the full self-hosted pipeline (building `mnc-stage1` from
self-hosted IR and then using it on goldens).

**The gap**: there is no CI gate that runs
`scripts/test_native.py --stage1 mnc-stage1` on the full golden
suite. A self-hosted regression (e.g., dropping from 26/64 to 25/64)
would not fail CI. v4.114.0's MEASUREMENTS.md shows 26/64; Rattler's
review independently confirms it; but CI doesn't enforce it.

**This is a known gap and it's not new in Phase D.** The v4.106.0
panel also flagged it. The mitigation: every panel re-runs the
golden suite manually and compares. The gap is closed by the next
panel, not between them.

I am not docking Phase D for this carry-forward gap. I am flagging
it for Phase E to close.

## Primary lens — Harness reliability

`scripts/test_native.py` writes `tests/golden/BENCHMARKS.md`,
`BENCHMARKS-linux.md`, and appends to `HISTORY.jsonl` on every run.
Those artifacts are committed so the per-test metric trend is
visible without re-running. v4.113.0 Phase 5 committed the refreshed
benchmarks; v4.114.0 Phase 1 regenerated them again.

The harness is deterministic enough to diff releases. It is not
deterministic enough for a 26 → 27 delta to be noise-proof (some
tests jitter ±1ms on compile time). That's acceptable for a
semantic pass/fail check but suboptimal for perf regression.

## Secondary — Fixed-point CI

`scripts/verify_fixed_point.sh` is in `.github/workflows/` per
v4.29.0 — it fails hard if the diff exceeds `DIFF_THRESHOLD`. At
v4.114.0 it fails at Stage 1 with `Undefined variable 'None'`.
**This means the CI gate is red.**

I checked the workflow: the fixed-point job is not in the default
branch protection. It was removed from CI in v4.111.0 when Stage 2
became unreliable. At v4.114.0 it's still out of the required-checks
set.

That's defensible — Sh.8 blocks Stage 1 entirely, running the job
as required would keep CI red until Sh.8 is closed. But it means
**"fixed-point" is not a CI guarantee right now.** Phase E needs to
either close Sh.8 or document the gate's absence.

## Secondary — Docket closure infrastructure

DOCKET_AUDIT.md in v4.114.0 lists every v4.99.0 item with code
location + test coverage + regression status. This is the kind of
audit I want from every panel. It should be the template for Phase
E and Arc 5.

## What I'd flag

1. **Self-hosted pipeline not in CI gate.** Carry-forward from
   v4.106.0. Phase E target.
2. **Fixed-point CI is red and out of required checks.** Either
   close Sh.8 or document the gate's absence.
3. **Harness perf jitter.** Not blocking, but the `ms` column in
   BENCHMARKS is noisy enough that a 10% regression could hide.

## Verdict

**PASS WITH NOTES @ 7.8.**

Toolchain and CI are stable. Phase D didn't introduce any harness
regression — all three releases committed refreshed
`BENCHMARKS.md`, `HISTORY.jsonl` append worked, async CI gates
held. The two notes (self-hosted CI gap, fixed-point CI red) are
carry-forward concerns that Phase E should own.

Phase D closes if the aggregate holds.
