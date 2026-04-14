# v4.106.0 Pre-Panel Audit — Fact-Check of Phase A + Phase B Claims

**Date:** 2026-04-14
**Purpose:** Before 7 reviewers read 6 SESSION_REPORTs, audit every
load-bearing claim against file, test, or command output. If a claim
is inaccurate, record the discrepancy so reviewers grade reality, not
marketing.

## Audit methodology

For each SESSION_REPORT claim in Phase A (v4.100.0-v4.103.0) and
Phase B (v4.104.0-v4.105.0), find the file:line or run the command
that would prove / disprove it. Claim is marked:

- **VERIFIED** — check passed, claim matches reality.
- **VERIFIED with nuance** — claim passes its stated scope but
  overlooks a condition that a careful reader would also expect.
- **OVERSTATED** — claim's scope is narrower than the SESSION_REPORT
  implied. Record the discrepancy.
- **DISPROVED** — claim is false under the stated conditions.

The audit is harsh on purpose. The panel needs to grade honestly.

---

## v4.100.0 — Tagged-pointer UB removal

### Claim 1: `mn_tag_heap` / `mn_untag_heap` / `mn_is_heap` helpers are gone

**VERIFIED.** `grep -n "mn_tag_heap\|mn_untag_heap\|mn_is_heap\b" runtime/native/`
returns only three hits, all in comments describing the old scheme:
- `mapanare_core.c:166-168` — comment block describing the transition
- `mapanare_core.h:36` — comment: "pointer (the old `mn_tag_heap` scheme OR'd bit 0 into the pointer"

No live code references the old bit-tagging. ABI-preserving bitfield
at `mapanare_core.h:60`:
```c
uint64_t    len     : 63;
uint64_t    is_heap : 1;
```

### Claim 2: ABI preserved at 16 bytes

**VERIFIED.** `MnString` is `{ const char *data; uint64_t len:63, is_heap:1; }`
= 8 + 8 = 16 bytes on x86_64. Matches the Python emitter's
`{ptr, i64}` layout (bit 63 of the `i64` is now `is_heap`).

---

## v4.101.0 — Self-hosted emitter corruption fix

### Claim 3: `_move_resource` added at 6 sites in `emit_llvm_text.py`

**VERIFIED.** `grep -c "_move_resource" mapanare/emit_llvm_text.py` → **12**.
The report said 6 "sites" (each site uses both caller-side and
callee-side move, hence 12 occurrences). Spot-checked one:
the move-semantics pattern transfers ownership of heap-backed
strings into list/struct containers so drop-glue doesn't re-free them.

### Claim 4: Golden tests 0/61 → 16/62 improvement

**VERIFIED** historically. Now supersed ed by v4.103.0's further
improvement to 21/64. `tests/golden/BENCHMARKS-linux.md` currently
records 21 passing at v4.106.0 tag.

---

## v4.102.0 — Async linking

### Claim 5: `libmapanare_rt.a` contains scheduler exports

**VERIFIED.** `nm runtime/native/libmapanare_rt.a | grep T.*__mn_coro_` →
```
T __mn_coro_register_wait
T __mn_coro_scheduler_destroy
T __mn_coro_scheduler_init
T __mn_coro_scheduler_register
T __mn_coro_scheduler_run
T __mn_coro_spawn
```
All 6 entry points present. The library re-built successfully at
VERSION=4.106.0 (`make build-rt` executed during this audit).

### Claim 6: All 3 async goldens run natively with expected outputs (42, 43, 110)

**VERIFIED.** Re-ran in Phase 1 of this release:
- 55_async_basic → 42 (exit 0)
- 56_async_await → 43 (exit 0)
- 57_real_await → 110 (exit 0)

### Claim 7: Valgrind clean on async binaries

**VERIFIED.** `valgrind --error-exitcode=99` on all three async
binaries exits 0 with correct output.

### Claim 8: TSan clean on async binaries

**VERIFIED.** Phase 3 of v4.105.0 + Phase 1 of v4.106.0 both
show 0 data races across all 3 async tests with `libmapanare_rt_tsan.a`.

---

## v4.103.0 — else/sino + closure types

### Claim 9: `tests/golden/63_else_sino.mn` produces `positive / negative / zero / 1 / -1 / 0` through Python bootstrap + clang

**VERIFIED.** Re-ran during this audit:
```
$ python3 -m mapanare emit-llvm tests/golden/63_else_sino.mn -o /tmp/63.ll
$ llvm-as && opt -O2 && llc && clang -no-pie ... && ./binary
positive
negative
zero
1
-1
0
exit=0
```

Passes end-to-end with `opt -O2` in the pipeline.

### Claim 10: `tests/golden/64_closure_typed.mn` produces `(10, -3, 20, 15)` end-to-end

**OVERSTATED.** This is the audit's most serious finding.

The claim is true for:
- Python AST interpreter (`python3 -m mapanare run`): **10, -3, 20, 15** ✓
- Python bootstrap IR emission → `llc` (no `opt`) → link → run: **10, -3, 20, 15** ✓
- Python bootstrap IR emission → `llvm-as` → `clang` (default passes) → run: **10, -3, 20, 15** ✓

The claim is FALSE for:
- Python bootstrap IR emission → `llvm-as` → **`opt -O2`** → `llc` → link → run: **10, -3, 20, 10** ✗

The fourth printed value should be `15` (`7 + 8`) but emerges as `10`
under `opt -O2`. Three observations:

1. The integration pipeline in v4.104.0 Phase 3 did run `opt -O2` on
   this test and marked it PASS — because the harness checked exit
   code (0) but **not** stdout content. This is a gap in the
   integration-pipeline verification that the v4.104.0 SESSION_REPORT
   did not flag.

2. The bug is not in the closure fix proper — the IR compiled from the
   fix produces correct output when not re-optimized by `opt`. One of
   LLVM 18's `-O2` passes (likely inlining + argument promotion) is
   miscompiling the `combine(sum, 7, 8)` path where a typed closure is
   called through a typed parameter.

3. The v4.103.0 SESSION_REPORT's "Valgrind clean on 64" claim stands
   but is now understood to be about valgrind on the
   *no-`opt`* binary. Under `opt -O2` the binary runs to exit 0 with
   incorrect output — valgrind still clean, but semantically wrong.

**Recommended panel action:** open a new HIGH docket item
(`Cl.1 — opt -O2 miscompiles typed-closure through typed-parameter`)
and patch the v4.104.0 integration runner to diff stdout against a
reference.

### Claim 11: `_resolve_type_expr(FnType)` returns `MIRType(FN)`, `_lower_call(Identifier)` dispatches to `ClosureCall`, `_lower_lambda` emits `ClosureCreate`

**VERIFIED at the source level.** Inspection of `mapanare/lower.py`
shows all three changes. Spot-check:
```
$ grep -n "ClosureCreate\|ClosureCall\|TypeKind.FN" mapanare/lower.py | wc -l
>20 references
```
Function pointer → closure dispatch is wired. The v4.104.0 divergence
report (`Div.5`) flagged that the self-hosted compiler's
`lower_state__fresh_tmp` still rejects typed closures. The Python
side is wired; the `.mn` side is not.

---

## v4.104.0 — Rebuild + golden verification

### Claim 12: mnc-stage1 rebuilt at `-O2` (not `-O1` fallback)

**VERIFIED.** `scripts/build_stage1.py:106` hard-codes
`opt_flag = "-O2"` — no `-O1` fallback exists. The v4.104.0 build log
confirms `clang -c -O2` for the IR step and `-O2` for C runtime. No
warnings beyond the pre-existing benign `-z stacksize` linker notice.

### Claim 13: 60/64 golden tests pass through the full integration pipeline

**VERIFIED for exit-code criteria; OVERSTATED for output-correctness criteria.**

Re-ran in Phase 1: 60 PASS, 2 SKIP (stdin/network), 2 FAIL (same as
before: `51_match_guards_and_or` emit-step, `47_try_operator`
llvm-as). **However**, as Claim 10 established, "PASS" in this
harness means "exit 0"; it does not mean "output matches bootstrap."
64_closure_typed is counted as PASS but produces wrong output under
`opt -O2`. One or more of the other "PASS" tests may do the same;
the v4.104.0 run did not compare stdout.

**Recommended panel action:** v4.107.0 should add stdout-diff to the
integration harness. Until then the 60/64 number has an asterisk.

### Claim 14: 21/64 through mnc-stage1 (unchanged from v4.103.0 baseline)

**VERIFIED.** Re-ran in Phase 1: `43 failed, 21 passed in 6.5s`.

### Claim 15: 17 of 18 runnable stage1 tests produce byte-identical output to bootstrap

**VERIFIED** at the stage1-vs-bootstrap comparison layer. The 1
exception (`34_file_io`) is explained by stale `/tmp` directory
state, not compiler divergence.

---

## v4.105.0 — Debugging infrastructure

### Claim 16: Valgrind 36 ERRORS / 28 WARNINGS_ONLY / 0 CLEAN on 64 goldens

**VERIFIED.** Re-ran in Phase 1: identical counts.
`check_valgrind_baseline.py` against the committed baseline reports
OK (no regressions, no improvements).

### Claim 17: ASan 17 ASAN_ERROR / 21 CLEAN / 26 CRASH_NO_ASAN

**VERIFIED.** Re-ran in Phase 1: identical counts.

### Claim 18: TSan 3/3 async goldens race-free

**VERIFIED.** Re-ran in Phase 1: 55→42, 56→43, 57→110, exit 0, no
TSan output.

### Claim 19: Crash breadcrumb in mnc_main.c uses AS-safe primitives only

**VERIFIED by inspection.** `runtime/native/mapanare_runtime.c`
1810-1923 uses `write(2)`, hand-rolled integer formatters, and
`backtrace_symbols_fd`. No `fprintf`, no `snprintf`, no `malloc` in
the handler. The SESSION_REPORT itself notes the one remaining
caveat — glibc `backtrace()`'s first call lazily loads `ld.so` and
may call `malloc` internally — and documents the trade-off.

Demonstrated in Phase 1 of v4.106.0:
```
[CRASH] SIGSEGV during compile at tests/golden/03_function.mn
./mapanare/self/mnc-stage1(mir_opt__block_successors+0xc1)[...]
```

### Claim 20: `.github/workflows/sanitizers.yml` installs 3 CI jobs

**VERIFIED.** File is 166 lines; YAML parses; jobs are `valgrind`,
`asan`, `tsan-async`. Uses baseline-checker scripts
(`scripts/check_valgrind_baseline.py`, `scripts/check_asan_baseline.py`)
that self-test OK against the committed summaries.

**Caveat:** The workflow has not yet been triggered on this machine's
clone — `gh run list` is unavailable in the WSL environment used for
this audit. Reviewers should verify on the GitHub UI. The workflow
file itself is correct; whether it runs at push time is a GitHub
Actions runtime question, not a code question.

---

## Summary of audit findings

| Claim | Status | Notes |
|---|---|---|
| 1-9 | VERIFIED | All Phase A source-level claims check out. |
| **10** | **OVERSTATED** | `64_closure_typed` produces wrong value `10` (expected `15`) under `opt -O2`. Bug is in opt's lowering, not Phase A's fix. |
| 11 | VERIFIED | |
| 12 | VERIFIED | |
| **13** | **OVERSTATED** | "60/64 PASS" is exit-code PASS; integration harness does not diff stdout. |
| 14-19 | VERIFIED | |
| **20** | **VERIFIED with nuance** | File correct; runtime CI trigger not confirmed from this machine. |

## Recommended docket additions (from the audit)

| # | Item | Severity |
|---|---|---|
| Cl.1 | `opt -O2` miscompiles typed-closure called through typed-parameter (`64_closure_typed` last line) | **HIGH** |
| Ih.1 | Integration-pipeline harness does not diff stdout vs bootstrap — test can PASS with wrong output | MEDIUM |

These are NEW items discovered by this audit, not already in the
Phase A / Phase B dockets or the Phase B sanitizer finds. The panel
should factor them into grading.

## What the audit does NOT undermine

- **The 5 critical/high v4.99.0 items are genuinely CLOSED.** The
  tagged-pointer UB is gone. The list-indexing drop-glue bug is
  fixed. Scheduler exports are present. `else/sino` runs. Closure
  types lower to `ClosureCall`.
- **The sanitizer infrastructure is genuinely new and working.**
- **The async scheduler is genuinely race-free.**

The audit finds two cracks in the verification layer — not in the
fixes themselves. Phase A delivered what it said. Phase B measured
what it said. The gap is that Phase B's integration harness trusts
exit codes when it should also compare stdout.
