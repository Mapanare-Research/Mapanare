# Rattler v4.114.0 Review — LLVM / codegen

## Score: 8.2 / 10
## Verdict: PASS WITH NOTES

## Context: v4.106.0 → v4.114.0

At v4.106.0 I gave **7.8 / 10 PASS WITH NOTES** — one PASS in the
whole panel, aggregate 7.87, the release went to v4.106.1 patch.
Phase B had verified what Phase A fixed, but the verification layer
had cracks. Phase C refreshed benchmarks (v4.110.0 reached the 50×
vs Python / 1.06× vs Rust / 4.85× vs C gcc geomeans the README
advertises). Phase D is three releases — self-hosted golden parity,
fixed-point verification, the last three v4.99.0 docket items.

I re-ran everything before grading. I am not grading session reports
in isolation.

## Primary lens — Self-hosted IR correctness

### mnc-stage1 golden rate: **26/64 strict / 39/64 effective**

`scripts/test_native.py --stage1 mnc-stage1` re-run on 2026-04-14:
`26 passed, 38 failed in 6.6s`. Identical to v4.112.0 and v4.113.0.

The 38 failures are categorized in
`docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md` — 10 `__mn_str_starts_with`
crashes at `emit_mir_call+0x23515` (Sh.2), 5 async-missing (Sh.4),
5 tensor-missing (Sh.6), 2 const-missing (Sh.5), plus smaller
buckets. Every failure has a docket. None of them reopens a v4.99.0
item.

13 of the 38 "failures" are Category A — the self-hosted IR is
semantically equivalent to Python-bootstrap output but
`test_native.py` strict-compares function counts and flags them
because the Python bootstrap inlines more aggressively. If the
harness counted those as pass, the effective rate is 39/64. I accept
this claim after spot-checking three (5_for_loop, 11_closure,
24_enum_methods) — the self-hosted IR is legitimately correct.

### IR quality: sampled 5 emitted `.ll` outputs

I pulled `mnc-stage1` output for `01_hello`, `03_function`,
`06_struct`, `10_result`, `11_closure` and ran each through
`llvm-as` + `opt -O2` + `llc`. All five produce valid object code
that links and runs natively with the expected output. No
malformed metadata, no undefined types, no `ret void` in value-
returning functions. This was the v4.101.0 carryforward worry;
it is dead.

## Primary lens — Fixed-point

**Fixed-point script does not converge.** `verify_fixed_point.sh`
fails at Stage 1 with `Undefined variable 'None'` when `mnc-stage1`
tries to compile `mnc_all.mn`. Stage 2 and Stage 3 artifacts are
never produced.

This is Sh.8 (self-hosted `semantic.mn` does not register
`None`/`Some`/`Ok` as constructors). The Python bootstrap bypasses
this via `skip_check=True` in `build_stage1.py`; the self-hosted
binary has no bypass.

**Here is where I have to be careful.** The v4.99.0 docket did not
list "achieve full fixed-point." It listed the byref size heuristic
(#7). The byref fix has been verified in isolation on
`/tmp/byref_test.mn` (16-byte struct by value, 80-byte by reference,
correct output). That verification is legitimate as an isolated
test. But v4.112.0 was named "fixed-point verification" — and the
verification itself did not converge.

My read: **v4.112.0's name is overclaimed.** The session report was
honest about the blocker, but the release name promises something
it does not deliver. Phase D should own that cleanly.

Grading impact: this costs 0.3–0.5 points. Not more, because: (a)
v4.112.0's SESSION_REPORT was explicit; (b) the byref fix is real
and can be verified independently; (c) Sh.8 is the right way to
track the unfinished work.

## Primary lens — Byref size fix quality (docket #7)

`mapanare/self/emit_llvm.mn:1495` — `struct_byte_size(st, ty)`
reads the inline `{...}` form from `st.structs` and calls
`llvm_aggregate_size`. `mapanare/self/emit_llvm.mn:1460` —
`is_byref_type_st(st, ty)` routes named types through
`struct_byte_size` and compares against the 64-byte threshold.

The algorithm matches the Python bootstrap's `_tsz` at
`emit_llvm_text.py:141`. I verified by diffing both: identical
recursion (aggregate of fields, pointers 8, integers padded to
8 on x86_64). This is the right fix for the right reason.

8 call sites updated (v4.114.0 PRE_PANEL_AUDIT counted 8; the
SESSION_REPORT claimed 7 — minor count mismatch, more is better).

**Sub-score for #7: 9.0 / 10.** Execution is clean. The only
reason it's not 10 is that the fix can't be verified at the
fixed-point level because of Sh.8.

## Secondary — Coroutine frame (docket #8)

The refactor renames `*(void **)handle` to
`frame->resume_fn` via a named struct. I compiled both and
diffed the `-emit-llvm -O0` output — the load instruction is
identical. This is code-quality, not a functional fix.

Is code-quality worth closing a MEDIUM docket for? Viper is
grading this as primary; I defer to her. From an LLVM angle the
change is inert.

## Secondary — Async error messages (docket #11)

Not my lane. I note that `__mn_coro_scheduler_init` now bails
cleanly on `pthread_create` failure instead of silently starting
fewer threads — that prevents a class of "mystery hang" reports
which could otherwise look like LLVM codegen bugs when they
aren't. +0.1 for indirect LLVM-adjacent improvement.

## What the panel should call out

1. **v4.112.0 release name is overclaimed.** Acknowledge that
   Phase D did not complete full fixed-point verification;
   name the blocker (Sh.8); commit to measuring fixed-point
   in the release that actually closes Sh.8.

2. **Culebra scan over main.ll is still blocked.** Three
   panels in a row now. Open Instr.1 or equivalent — narrow
   the scan target or make culebra incremental.

3. **Self-hosted IR quality is solid on the 26 passing
   goldens.** Spot-check four more in the next arc as a smoke
   test; if they hold, the codegen concern is fully closed.

## Verdict

**PASS WITH NOTES @ 8.2.**

The Phase D work is real. The byref fix is clean and correct.
The self-hosted compiler genuinely produces valid IR for 26
goldens. Zero v4.99.0 items remain open.

The notes are:
- Fixed-point did not fully converge; Sh.8 is a real blocker and
  the v4.112.0 name should not imply it closed.
- Phase D floor is 26/64 self-hosted; Sh.1-Sh.7 remain for Phase E.
- Culebra scan instrumentation gap carries forward.

Phase D closes if the aggregate holds.
