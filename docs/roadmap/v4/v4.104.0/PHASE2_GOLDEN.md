# v4.104.0 Phase 2 — Golden tests through mnc-stage1

**Date:** 2026-04-13
**Harness:** `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
**Wall time:** 6.7 s

## Headline

**21 / 64 passing** — unchanged from the v4.103.0 baseline. Phase A fixes hold
(no regressions), and the 43 failures are all pre-existing self-hosted-
compiler bugs, not Phase A regressions.

The `21/64` count matches what v4.103.0's SESSION_REPORT predicted for the
corpus under mnc-stage1: Phase A unblocked the Python bootstrap path, but
the self-hosted compiler (`mapanare/self/*.mn`) has its own set of bugs
that were never claimed fixed by any Phase A release.

## Passing tests (21)

01_hello, 02_arithmetic, 04_if_else, 06_struct, 07_enum_match, 08_list,
09_string_methods, 10_result, 12_while, 14_nested_struct, 16_string_escape,
17_option, 18_method_chain, 30_nested_generics, 32_generic_enum,
34_file_io, 35_stdin, 36_crypto, 37_regex, 38_http, 39_gpu_detect.

## Failing tests by root cause (43)

Every failure was captured (`/tmp/stage1_errs/<test>.err`) and classified by
the symbol at the top of the crash trace or the first error message.

### Category A — Crash in `mir_opt__block_successors` (14 tests)

The self-hosted MIR optimizer's block-successor analysis dereferences a
null or bogus pointer. Deterministic SIGSEGV at `mir_opt__block_successors+0xc1`.

- 03_function, 11_closure, 15_multifunction, 23_multi_return, 26_generics
- 27_impl, 28_traits, 29_generic_impl, 31_generic_multi
- 41_module_let, 42_module_let_string, 43_module_let_math, 45_ffi_bind
- 62_list_output

### Category B — Crash in `__mn_str_starts_with` via `emit_llvm__emit_mir_call` (9 tests)

The self-hosted compiler's LLVM emitter's String lifetime bug — the analog
of the Python-emitter use-after-free that v4.101.0 fixed. Heap strings
pushed into dispatch tables are freed before the comparator runs.

- 13_fib, 19_nested_match, 20_recursion, 24_enum_methods
- 47_try_operator, 48_match_nested_exhaustive, 49_match_guards
- 50_match_or_patterns, 63_else_sino

This is the known v4.103.0 follow-up: "self-hosted String lifetime across
multiple function calls crashes `__mn_str_starts_with` in
`emit_llvm__emit_mir_call`."

### Category C — Crash in `lower__lower_expr` (3 tests)

Self-hosted lowerer crashes while lowering an expression; distinct from A
and B by the top frame.

- 21_list_ops, 33_break_continue, 40_gpu_tensor

### Category D — MIR verifier: block missing terminator (3 tests)

The self-hosted lowerer produces a `for_header0` block with no terminator
instruction. The verifier catches it before emission.

- 05_for_loop, 22_string_builder, 25_fizzbuzz

### Category E — Semantic: `'Tensor'` undefined (3 tests)

Self-hosted semantic checker does not know about the `Tensor` builtin.

- 49_tensor_literal, 51_tensor_broadcast, 53_linear_regression

### Category F — Parser: comma in index `[a, b]` (2 tests)

Grammar in the self-hosted parser rejects tuple indexing `t[i, j]`.

- 50_tensor_indexing, 52_tensor_slicing

### Category G — Semantic: `block_on` undefined (5 tests)

Self-hosted semantic checker does not recognize the `block_on` async
builtin. Phase A's v4.102.0 async fix applied to the Python bootstrap + C
runtime, not to `mapanare/self/semantic.mn`.

- 55_async_basic, 56_async_await, 57_real_await, 58_async_file_io,
  59_async_fanout

### Category H — Semantic: miscellaneous undefined (4 tests)

- 51_match_guards_and_or — `'None'` undefined (no `Option` import resolution)
- 54_const_basic — top-level `N` const not wired into scope
- 58_const_scope — top-level `MAX` const not wired into scope
- 64_closure_typed — typed `fn(T) -> T` parameter not resolved; identical
  story to v4.103.0 Python fix not yet ported to `mapanare/self/lower.mn`

## Evidence trail

- Full harness log: `docs/roadmap/v4/v4.104.0/artifacts/stage1-goldens.log`
- Per-test stderr: `/tmp/stage1_errs/<test>.err` (captured during session)
- Classification table: `/tmp/fail_classification.txt`
- Updated benchmarks: `tests/golden/BENCHMARKS.md`, `tests/golden/BENCHMARKS-linux.md`

## Interpretation

Of the 43 failures, **29 are compiler crashes** (Categories A/B/C/D: 14+9+3+3)
and **14 are front-end semantic gaps** (E/F/G/H: 3+2+5+4). The crashes cluster
tightly into three root causes: `mir_opt__block_successors`, String
lifetime in `emit_llvm__emit_mir_call`, and expression lowering. The
semantic gaps are all single missing features in `mapanare/self/`.

**None of these are new.** Every category maps to either a v4.103.0
"Known follow-up" or a feature that was never shipped in the self-hosted
compiler's front-end. The 21/64 count is honest: it is the number of
golden tests whose source patterns the self-hosted compiler already
supports.

## Exit criterion (Exit #2)

- [x] All 64 golden tests run through mnc-stage1, every result recorded.
- [x] Target of 64/64: **not** met (21/64). This is documented, not fixed
  — per the PLAN, bug fixes belong to v4.105.0+ and the v4.106.0 panel.
- [x] `tests/golden/BENCHMARKS.md` refreshed (harness auto-updates).
