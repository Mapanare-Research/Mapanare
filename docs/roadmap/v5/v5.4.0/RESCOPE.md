# v5.4.0 Rescope — Sh.2 already closed; release is correctness infra

**Date:** 2026-04-23
**Applies to:** `PLAN.md` + `PROMPT.md` in this directory.

## What changed

Phase 0 baseline capture at v5.3.3 → bump to 5.4.0 found that **all 11
Sh.2 tests per `docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md` are already
passing** on every quality axis:

| Metric | Expected (per PLAN.md) | Actual (v5.3.3 baseline) |
|---|---|---|
| Golden harness (IR matches reference) | 0/11 pass | **11/11 PASS** |
| `mnc-stage1` exit code | non-zero | **11/11 exit 0** |
| ASan on `mnc-stage1-asan` compilation | 11 CRASH_NO_ASAN | **11/11 CLEAN** |

The 11 Sh.2 tests are: `13_fib, 19_nested_match, 20_recursion,
22_string_builder, 29_generic_impl, 31_generic_multi, 47_try_operator,
48_match_nested_exhaustive, 49_match_guards, 62_list_output,
63_else_sino`.

Something between v4.126.0 and v5.3.3 silently closed them — most
likely the v5.1.3 Cb.7 zero-after-push workaround at `register_struct`
/ `register_enum`, possibly reinforced by v5.3.2's `clone_instr_for_inline`
fix which restored fixed-point.

## Revised v5.4.0 scope

Release still ships all four phases from PLAN.md, but the **goal
framing changes** from:

> ~~"Drive native goldens 54/66 → 65/66 by closing 11 Sh.2 tests."~~

to:

> **"Land the self-hosted drop-glue + Move tracking infrastructure.
> Close Viper's 28-panel Own.1 carry-forward. Ensure the compiler
> cannot regress to Sh.2-shape bugs. 0 new goldens — Sh.2 already
> closed silently."**

## Revised exit criteria

Based on captured v5.3.3-baseline numbers:

| Metric | Baseline | v5.4.0 target |
|---|---|---|
| Goldens | 54/66 PASS | ≥ 54/66 (no regressions) |
| 11 Sh.2 tests (per v4.126.0 triage) | 11 PASS / exit 0 / ASan-CLEAN | preserve all three |
| Valgrind | 66 WARNINGS_ONLY, 0 ERRORS | 0 new ERRORS |
| ASan | 55 CLEAN, 11 CRASH_NO_ASAN | 55 CLEAN preserved; ≤ 11 CRASH_NO_ASAN |
| Fixed-point | stage2 `llvm-as` OK, stage3 empty (Ve.1) | preserve (not a gate this release) |
| `llvm-as` on stage2 | OK | OK |
| Non-bootstrap pytest | 0 failures | 0 failures |
| `make lint` | clean | clean |
| `PARITY_GAPS.md` | Own.1 Phase 2 open | Own.1 Phase 2 → Historical with Sh.2-already-closed note |
| `SESSION_REPORT.md` | — | documents discovered-already-closed state |

**Note on fixed-point:** v5.3.2 SESSION_REPORT acknowledges stage3.ll is
empty because the stage2 binary's MIR verifier rejects empty
match-arm blocks in `expr_kind` (Ve.1 LOW docket). CLAUDE.md's "NEAR"
description is inaccurate. v5.4.0 does not attempt to fix Ve.1 —
preserving the baseline (stage2 llvm-as OK) is the gate.

**The 11 CRASH_NO_ASAN tests are NOT the Sh.2 tests** — they are the
currently-failing 5 Sh.4 async + 5 Sh.6 tensor + 1 Sh.7 closure_typed.
mnc-stage1 exits non-zero when compiling them because the feature
isn't implemented, not because of a memory bug.

## What the 12 remaining failures actually are

Baseline 54/66 decomposes as:

- 5 Sh.4 async (55–59) — v5.5.0 target
- 5 Sh.6 tensor (49–53) — v5.6.0 target
- 1 Sh.7 closure-typed (64_closure_typed) — v5.7.0 target
- 1 B bootstrap-also-fails (51_match_guards_and_or) — v5.7.0 orthogonal

None are Sh.2. PLAN.md's "65/66 target" was based on a stale triage
from 35+ releases ago.

## Why still ship v5.4.0 (not skip to v5.5.0)

- **Viper's carry-forward.** 28 panels flagging Own.1 Phase 2 as a
  band-aid-only closeout. Landing the real infrastructure closes her
  argument *substantively* rather than on a technicality.
- **Regression defense.** Without drop-glue + Move tracking, any future
  change to `emit_llvm.mn`'s call-emission path could reintroduce Sh.2.
  The infra protects against that.
- **Correctness beyond the current test set.** The 11 Sh.2 tests happen
  to pass today; code patterns not covered by those tests may still be
  vulnerable to the same class of bug.

Rescope approved by user 2026-04-23.
