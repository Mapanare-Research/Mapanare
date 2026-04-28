# Panel v5.2.0 — Rattler (LLVM IR Correctness)

**Score:** 9.3 / 10
**Grade:** EXCEEDS
**Delta vs v4.154.0:** -0.3

## Summary

The v5.0.1-v5.2.0 arc closed 19 carry-forwards in 12 releases -- the
highest closure rate per release in the project's history. From my
axis, the headline results are clear: Rt.4 (enum type size), Cb.6-test
(typed-pointer regression gate), and Dr.1-mutation (build-script
source-tree mutation) are all properly closed and verified. The Cb.15
sret classifier port to self-hosted (`abi.mn`, 75 LOC) is clean and
correct. The Perf.1 inline list access pattern is textbook-correct
LLVM IR with proper unsigned bounds checking. The closure rate on my
carry-forward items from v4.154.0 is 5/7 (Rt.4, Cb.6-test, Dr.1, In.1,
Ea.1), with two remaining deferred (Li.1, Sh.4/5/6/7).

However, this arc also introduced the most significant quality
regression since the v4.134.0 strict fixed-point: the In.1 inliner
re-enable at v5.1.2 broke stage2 self-compilation. The fixed-point
went from NEAR (4-line version metadata diff) to BROKEN
(`llvm-as: error: use of undefined value '%_inl0_6_t4'`). I have
identified the root cause -- `clone_instr_for_inline` at
`mapanare/self/mir_opt.mn:835-934` handles only 10 of 30+ instruction
kinds, with the fallthrough at line 932-933 pushing the ORIGINAL
un-renamed instruction for any unhandled kind. This means FieldGet,
StructInit, IndexGet, EnumTag, and other instruction types have their
definitions preserved as `%t4` while downstream uses get renamed to
`%_inl0_6_t4`, causing a use-def mismatch. The 4 unit tests in
`test_inline_rename.py` use only BinOp/Const/Call/Return callees,
which are all handled kinds -- the tests are correct but insufficient.
This is a -0.3 delta from baseline because the fixed-point was the
single hardest-won artifact in the v4 arc, and it was broken by a
change that had inadequate test coverage of the instruction-kind space.

The Perf.1 list inlining and the Cb.15 sret port are both excellent
engineering that would normally push the score up. But the fixed-point
regression outweighs them.

## What improved since v4.154.0

### Rt.4 CLOSED (v5.0.6) -- enum type size safe upper bound

At `mapanare/self/emit_llvm.mn:1691-1712`, `llvm_type_size` now
returns 24 for any `%enum.*` type, with a correct three-layout comment:

```
// v5.0.6 Rt.4: enum layouts depend on inline slot count:
//   boxed        {i64, ptr}        = 16 bytes
//   1-slot inline {i64, i64}       = 16 bytes
//   2-slot inline {i64, i64, i64}  = 24 bytes  (Rt.1 v4.124.0)
// llvm_type_size cannot see EmitState, so return the safe upper
// bound (24) for any %enum.*.
```

**Verified:** `grep -n 'always {i64, ptr}' mapanare/self/emit_llvm.mn`
returns 0 matches. The stale comment is gone. The 24-byte upper bound
is correct: over-allocating by up to 8B for 16B enums wastes memory
but never under-allocates. +0.05.

Additionally, the `use_sret_return` wrapper at line 1646-1663 now
routes through `enum_byte_size(st, ty)` at line 1655-1656, which
resolves the actual inline-slot count from the EmitState enum registry.
This means sret classification uses the REAL size, not the upper-bound
fallback. The fallback only fires for `llvm_type_size` callers that
lack EmitState access. Clean layering.

### Cb.6-test CLOSED (v5.0.6) -- structural regression gate

`tests/llvm/test_enum_inline_parity.py` (83 lines, 2 tests) is exactly
the test I asked for at v4.144.0. `test_self_hosted_rejects_typed_pointer_slot`
structurally scans the `type_fits_inline_slot` function body for the
`ends_with("*")` rejection clause. `test_self_hosted_and_python_emitters_agree_on_opaque_ptr`
confirms the Python emitter accepts both `ptr` and `i64*` while the
self-hosted accepts only `ptr`.

The structural-scan approach is the right call: no public `.mn` surface
produces `i64*` (the lowerer emits only opaque pointers), so an
end-to-end test would be brittle. +0.0 (debt closure, expected).

### Dr.1-mutation CLOSED (v5.0.6) -- tempdir substitution

`scripts/build_stage1.py:80`: `with tempfile.TemporaryDirectory(prefix="mn_build_") as td:`
wraps the version-placeholder substitution + compile. The source tree
under `mapanare/self/` is now read-only during build. The fragile
`try/finally` restore pattern from v4.139.0 is gone. +0.0 (debt
closure, expected).

### Cb.15 CLOSED (v5.0.4) -- sret classifier ported to self-hosted

`mapanare/self/abi.mn` (75 LOC) is a clean port of `mapanare/abi.py`.
I verified each classifier against the calling convention documents:

- **SysV** (`abi_sysv_use_sret`, line 26): `total_size <= 16` returns
  false. Correct for Mapanare's INTEGER-only aggregate fields.
- **Win64** (`abi_win64_use_sret`, line 35): explicit 1/2/4/8 byte
  check. Correct per the Win64 x64 ABI.
- **AArch64** (`abi_aapcs64_use_sret`, line 47): `total_size <= 16`
  returns false. Correct for the non-HFA case.

The unified classifier at line 65 dispatches via `target.contains`
string matching. The self-hosted emitter hardcodes
`"x86_64-unknown-linux-gnu"` at `emit_llvm.mn:1663`, which always hits
the SysV path. This is correct for the self-hosted compiler's current
target. The Python emitter reads the actual target triple, so the
self-hosted path is a subset but not wrong.

The sret count jump from 2,263 to 4,112 in stage2.ll confirms the
classifier is active and producing real ABI corrections. The
`use_sret_return` wrapper at `emit_llvm.mn:1646-1663` correctly routes
through `struct_byte_size` / `enum_byte_size` before calling the ABI
classifier, maintaining the function-definition/call-site invariant
(both paths call the same pure function on the same inputs). +0.10.

### Perf.1 CLOSED (v5.1.0) -- inline list ops

The inline list access pattern at `emit_llvm_text.py:4520-4547`
(Python) and `emit_llvm.mn:1910-1938` (self-hosted) is correct LLVM IR:

1. **Gate:** `_tsz(ety) == 8` (Python) / `dest_ty == "i64" || dest_ty == "double" || dest_ty == "ptr"` (self-hosted). Both correctly restrict to 8-byte element types where the GEP stride matches the actual element layout.

2. **Bounds check:** `icmp uge i64 %idx, %len` -- unsigned comparison catches both out-of-range (idx >= len) and negative indices (negative i64 is very large unsigned). The trap block calls `abort()` + `unreachable`. This is the standard LLVM pattern.

3. **Data access:** `getelementptr inbounds {ptr, i64, i64, i64, i64}, ptr %la, i32 0, i32 0` extracts the data pointer (field 0 of the list struct), then `getelementptr inbounds i64, ptr %data, i64 %idx` indexes into the backing buffer. The `inbounds` flag is correct because the bounds check guarantees `idx < len`, and the list's data pointer always points to a valid allocation of at least `len * 8` bytes.

4. **Self-hosted mirror:** The self-hosted version at `emit_llvm.mn:1913-1938` produces structurally identical IR. Counter-based naming (`%lg.lenp.N`, `%lg.dp.N`) prevents SSA collisions across multiple list accesses in the same function.

The quicksort improvement (2.99x -> 1.14x Rust) is consistent with
the mechanism: quicksort's ~130K `__mn_list_get/set` calls per run
were opaque function calls that LLVM could not see through. Inlining
them as GEP+load lets LLVM's alias analysis and loop optimizations
work on the actual memory access pattern. +0.10.

### In.1 CLOSED (v5.1.2) -- but with stage2 regression

The `replace_uses_in_instr` helper at `mir_opt.mn:677-830` is
comprehensive: it handles all 30+ Instruction enum variants and
correctly renames both source operands and destination values. The
post-call rename at lines 1028-1046 creates a fresh `%_inlN_M_dst`
destination and renames all downstream uses in post-call instructions
and remaining blocks. The 4 tests in `test_inline_rename.py` are
correct.

**The fix works for golden tests (54/66 unchanged).** The problem is
in `clone_instr_for_inline`, not in `replace_uses_in_instr`. See
"What concerns me" below. +0.0 (net neutral -- fix is correct but
introduced a regression elsewhere).

### Ea.1 CLOSED (v5.1.2) -- escape analysis ported

`mir_opt.mn:1370-1398` replaces the stub with a real `check_escape`
analysis. The analysis is correctly gated: it computes the
non-escaping set but cannot annotate instructions because the
self-hosted `Instruction` enum lacks an `alloc_kind` field. This is
the right architecture -- analysis and annotation are separable
concerns, and the annotation requires an enum extension that is a
larger change. The Python emitter's `escape_analysis_promotion` is the
reference implementation. +0.0 (correctness-neutral -- analysis runs
but does not affect codegen).

## What held

### Sanitizer state: improved

Valgrind moved from 4 ERRORS (Ge.1 generics residuals) to 2 ERRORS
(GPU dlopen timeouts). The Ge.1r closure at v5.1.1 eliminated the
real memory-safety findings. The remaining 2 are infrastructure
artifacts (dlopen for CUDA/Vulkan on a system without GPU hardware),
not memory bugs. This is a net improvement.

### Golden tests: 54/66, unchanged for 32+ releases

The golden baseline has not moved since v4.144.0. The 12 failures are
all feature-gap tests (async, tensor, GPU, closure-typed) that require
compiler infrastructure not yet in the self-hosted path. No golden
regressions from any change in this arc.

### Test count: 5,309 -> 5,445 (+136)

Primarily from the v5.2.0 registry suite (51 tests) and the various
gates added in v5.0.6 (Cb.6-test, An.9, An.10) and v5.1.0-v5.1.2
(10 list inline + 4 In.1 + 3 Li.1 + 7 Ea.1 = 24 optimizer tests).

### Perf.2 lazy coro threads (v5.1.4) -- not my axis but noted

The async geomean improvement from 2.3ms to 1.19ms at default settings
(0.91x Go) is a meaningful user-visible result. The TSan 0-race and
valgrind 0-leak evidence is clean. This does not affect my score but
is worth noting for arc context.

## What concerns me

### 1. In.1-stage2: inliner broke the fixed-point (NEW, MEDIUM)

**The most significant quality regression in this arc.**

The fixed-point went from NEAR (4-line diff, version metadata only)
at v4.154.0 to BROKEN at v5.1.2. The error:

```
error: use of undefined value '%_inl0_6_t4'
  store %struct.Span %_inl0_6_t4, ptr %_inl0_6_retval.cpy
```

**Root cause I identified:** `clone_instr_for_inline` at
`mir_opt.mn:835-934` has explicit rename handlers for only 10
instruction kinds: `return`, `const`, `copy`, `binop`, `call`,
`alloca`, `load`, `store`, `unaryop`, `cast`. The fallthrough at
line 932-933 (`result.push(inst)`) pushes the ORIGINAL instruction
without renaming for any other kind.

`replace_uses_in_instr` (the use-side renamer added for In.1) handles
30+ kinds. `clone_instr_for_inline` (the def+use renamer for the
callee's body) handles only 10. The asymmetry is the bug.

When a callee function contains a `FieldGet`, `StructInit`, `IndexGet`,
`WrapSome`, `EnumTag`, or any of the 20+ unhandled kinds:
- The instruction's DEFINITION retains the original name (e.g., `%t4`)
- Downstream instructions that USE `%t4` get renamed to `%_inl0_6_t4`
  by `rename_value`
- Result: `%_inl0_6_t4` is used but never defined -- invalid SSA

The 4 tests in `test_inline_rename.py` use callees containing only
`BinOp` + `Const` + `Call` + `Return`, which are all in the handled
set. The tests are necessary but not sufficient. The bug only
manifests when the self-hosted compiler compiles itself, because the
compiler's own small helper functions contain `FieldGet`, `StructInit`,
etc.

**The fix is straightforward:** extend `clone_instr_for_inline` to
cover the same instruction kinds that `replace_uses_in_instr` already
handles. Alternatively, disable `inline_small_functions` until the
cloner is complete. The current state -- pass enabled, stage2 broken
-- is the worst option.

**Docket: In.1-stage2** (MEDIUM -- the fixed-point was the v4 arc's
crown achievement)

### 2. E1 test regression: LLVM version-dependent (LOW)

`test_post_opt_single_switch_in_hot_loop` at
`tests/llvm/test_unified_return_shape.py:102-131` asserts exactly 1
`switch` in the optimized `@main` function. LLVM 18 produces 0
switches (it folds the switch entirely into computed GEPs or
conditional moves). The test was written against LLVM 17 behavior.

This is not a correctness bug -- the optimized code is valid and
likely better (0 switches means LLVM found an even more efficient
lowering than the expected single-switch pattern). But the test is
now a false failure.

**Recommendation:** Change the assertion from `== 1` to `<= 1`
(zero or one switch is acceptable post-optimization), or detect the
LLVM version and adjust the expected count. 15-minute fix.

**Docket: An.9-llvm18** (LOW)

### 3. Li.1: LICM still broken, as expected (LOW, unchanged)

Unit tests pass (3/3), live golden tests regress (54/66 -> 51/66).
The root cause is unchanged from v4.152.0: single-pass hoist without
fixpoint loop or dominator-based preheader insertion. Pass remains
disabled in both pipelines. This is correctly deferred.

**Docket: Li.1** (LOW, 2 cycles, unchanged)

### 4. Sh.4/5/6/7: feature gaps, unchanged (LOW, deferred)

Self-hosted emitter still lacks ownership-tracking in its Copy
instruction handler. This is the single largest correctness gap
between the two emitters for anyone extending the self-hosted path.
Correctly deferred to v5.x feature track.

**Docket: Sh.4/5/6/7** (LOW, deferred, unchanged)

### 5. Stream C runtime test failures (NEW, LOW)

3 of 74 C runtime tests fail: `stream_from_list_collect`,
`stream_map`, `stream_filter`. The MEASUREMENTS.md classifies these
as "`__mn_list_get` returns wrong element values." Given the Perf.1
inline list changes, it is worth verifying whether the C runtime's
`__mn_list_get` was inadvertently broken or whether the test
expectations shifted. Not blocking, but worth a look.

**Docket: Stream-C** (LOW -- 71/74 pass, not a safety issue)

### 6. Lint debt in v5.2.0 registry code (LOW)

4 files need `black`, 9 `ruff` errors. Two pytest failures
(`test_black_check_passes`, `test_ruff_check_passes`). This is
housekeeping, not correctness.

**Docket: Lint-v5.2.0** (LOW)

## Score rationale

Starting from v4.154.0 baseline of 9.6:

- **Rt.4 closure**: +0.05. The enum type size is now correct with a
  clean three-layout comment. Two cycles open, now properly closed.

- **Cb.15 sret port**: +0.10. Clean, correct, per-target-verified
  ABI classifier in the self-hosted emitter. The sret count jump
  (2,263 -> 4,112) confirms it is active.

- **Perf.1 inline list ops**: +0.10. Textbook-correct LLVM IR with
  proper unsigned bounds checking, trap-on-OOB, and inline GEP+load.
  Both emitters produce structurally identical IR. The quicksort
  improvement (2.99x -> 1.14x Rust) traces directly to this mechanism.

- **Cb.6-test + Dr.1-mutation closures**: +0.0. Expected debt closure,
  correctly done but does not raise the ceiling.

- **Ea.1 closure**: +0.0. Analysis-only, correctness-neutral.

- **In.1-stage2 fixed-point regression**: -0.45. This is the most
  heavily penalized item. The fixed-point was achieved at v4.134.0
  after months of work ("La Culebra Se Muerde La Cola"). It was
  maintained as NEAR through v4.154.0 (30+ releases). It is now
  BROKEN because `clone_instr_for_inline` handles only 10 of 30+
  instruction kinds, and the pass was enabled despite this coverage
  gap. The 4 unit tests were necessary but not sufficient -- they
  only exercise handled instruction kinds. The root cause is a
  20-kind coverage gap between the cloner and the renamer, which is
  a class of bug that should have been caught by systematically
  testing callees with FieldGet, StructInit, etc. The fix is
  straightforward (extend the cloner), but the regression should not
  have shipped.

- **E1 test LLVM-version regression**: -0.05. Minor, but a false
  failure in CI is noise that masks real issues.

- **Stream-C test failures**: -0.05. 3 new failures in the C runtime
  test suite. Low severity but new.

Net: 9.6 + 0.05 + 0.10 + 0.10 + 0.0 + 0.0 + 0.0 - 0.45 - 0.05 - 0.05 = **9.3**.

The grade remains **EXCEEDS** because the positive work in this arc
(Rt.4, Cb.15, Perf.1, closure rate) is genuinely excellent. But the
In.1-stage2 regression drops me 0.3 points from baseline. The
fixed-point is the project's most important self-consistency artifact,
and breaking it by enabling a pass with inadequate instruction-kind
coverage in the cloner is a process failure, not just a code bug. The
unit tests tested the happy path; the self-compilation path was the
real validation surface and it was not checked before the pass was
enabled.

I am at 9.3, down from 9.6. The path back to 9.6+ is:
1. Either fix `clone_instr_for_inline` to handle all 30+ kinds, or
   disable `inline_small_functions` until the cloner is complete.
2. Restore fixed-point to at least NEAR.
3. Fix the E1 test for LLVM 18 compatibility.

## Carry-forward

| Docket | Severity | Status | Scope |
|---|---|---|---|
| In.1-stage2 | MEDIUM | **NEW** | `clone_instr_for_inline` handles 10/30+ instruction kinds; stage2 self-compilation broken. Fix: extend cloner to match `replace_uses_in_instr` coverage, or disable pass. |
| An.9-llvm18 | LOW | **NEW** | `test_post_opt_single_switch_in_hot_loop` expects 1 switch; LLVM 18 produces 0. Fix: `<= 1` assertion or version-gate. |
| Li.1 | LOW | OPEN (3 cycles) | LICM needs fixpoint + preheader. Pass disabled. |
| Sh.4/5/6/7 | LOW | DEFERRED | Self-hosted ownership-tracking -- v5.x feature track. |
| Stream-C | LOW | **NEW** | 3/74 C runtime stream tests fail (wrong element values). |
| Lint-v5.2.0 | LOW | **NEW** | 4 files need black/ruff in registry code. |

## Reproducibility

All claims in this review can be verified:

```bash
# Rt.4 closure: stale comment gone
grep -n 'always {i64, ptr}' mapanare/self/emit_llvm.mn
# Expected: 0 matches

# Rt.4: safe upper bound 24 for %enum.*
grep -n 'starts_with("%enum.") { return 24' mapanare/self/emit_llvm.mn
# Expected: 1 match

# Dr.1-mutation: tempdir pattern
grep -n 'TemporaryDirectory' scripts/build_stage1.py
# Expected: 1 match

# Cb.6-test: regression gate
# pytest tests/llvm/test_enum_inline_parity.py -v --tb=no
# Expected: 2 passed

# Perf.1: inline GEP in Python emitter
grep -c 'getelementptr inbounds i64' mapanare/emit_llvm_text.py
# Expected: 2 (one in IndexGet, one in IndexSet)

# Perf.1: inline GEP in self-hosted emitter
grep -c 'getelementptr inbounds i64' mapanare/self/emit_llvm.mn
# Expected: 2

# Cb.15: sret classifier active in self-hosted
grep -c 'use_sret_return' mapanare/self/emit_llvm.mn
# Expected: 5 (wrapper + 4 call sites)

# In.1-stage2: clone_instr_for_inline instruction coverage gap
# Count handled kinds in clone_instr_for_inline:
grep -c 'if ik ==' mapanare/self/mir_opt.mn
# Count should be 10 in the clone function (line 835-934) vs 30+ overall

# In.1-stage2: replace_uses_in_instr handles more kinds
grep -c 'if ik ==' mapanare/self/mir_opt.mn  # (total across file)

# E1 test: verify the assertion expects exactly 1
grep 'switch_count ==' tests/llvm/test_unified_return_shape.py
# Shows: assert switch_count == 1

# Inliner is enabled (not disabled)
grep 'inline_small_functions' mapanare/self/mir_opt.mn | grep -v '//'
# Shows: let f6: MIRFunction = inline_small_functions(f5, lookup)
```
