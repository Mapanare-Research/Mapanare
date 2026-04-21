# v4.149.0 Session Report — E5 / ABI.1

> **Closes docket: ABI.1 (LOW).** Opened v4.125.0, flagged at v4.136.0
> panel, re-flagged at v4.143.0 panel. Oldest open perf docket on the
> ledger. Now closed.

## Summary

This release implements per-target return-value ABI classification for
the LLVM emitter. A new module `mapanare/abi.py` encodes the register-
return thresholds from three calling conventions:

- **System V AMD64 §3.2.3**: ≤ 16 bytes → registers (rax + rdx)
- **Win64 x64**: exactly 1, 2, 4, or 8 bytes → register (rax)
- **AArch64 AAPCS64**: ≤ 16 bytes → registers (x0 + x1)

The emitter's return-type sret decision (`_fn_use_sret`, call-site
`use_sret`) now delegates to the classifier instead of using the
blanket `_BYREF_BYTES = 64` threshold. Argument passing is unchanged.

## The PLAN's wrong premise — and what we actually found

The PLAN.md for v4.149.0 assumed "Mapanare currently returns every
aggregate via sret, regardless of size." The measured baseline tells
a different story:

**Zero sret across all 66 golden tests.**

The `_BYREF_BYTES = 64` threshold (introduced for the self-hosted
compiler's 240-byte state structs) means all normal user aggregates
(enums, Options, Results, small structs) were already returned by
value in LLVM IR. The threshold was set high enough that no golden
test aggregate exceeded it.

The actual ABI.1 gap was subtler: aggregates between 17 and 64 bytes
(like a 3-slot inline enum `{i64, i64, i64}` = 24 bytes, or
`Result<Int, String>` = 32 bytes) were returned by value in LLVM IR,
but the machine-level SysV convention requires sret for these because
they exceed 16 bytes. LLVM's backend silently inserted the sret
transformation at code generation, but the IR representation didn't
match Clang's convention.

The fix *lowers* the by-value threshold for returns from 64 to 16
(SysV), 8 (Win64), or 16 (AArch64), causing the sret count to
*increase* from 0 to 57 — the inverse of the PLAN's prediction.

## System V AMD64 §3.2.3 — implementation notes

The SysV classification algorithm is designed for the general case of
mixed-type aggregates with SSE, X87, and COMPLEX_X87 fields. For
Mapanare's current type system, every struct/enum field is either an
integer type (i64, i32, i16, i8, i1) or a pointer (ptr), all of which
classify as INTEGER. This means the full eightbyte classification
algorithm simplifies to a single size check: ≤ 16 bytes = two
INTEGER eightbytes = register return.

If Mapanare later adds float struct fields (e.g., `struct Point { x:
Float, y: Float }`), the classifier would need to handle SSE class
fields. But `{double, double}` = 16 bytes, which still passes the
size check — the complication only arises when mixing SSE and INTEGER
in the same eightbyte, which Mapanare's type system currently cannot
express.

## Win64 divergence

Win64 is notably stricter than SysV: only 1, 2, 4, or 8-byte
aggregates can return in rax. This means `{i64, i64}` (16 bytes,
register-eligible on SysV) must use sret on Win64. The existing
`_is_large_struct` check (> 8 bytes) already handled this for runtime
function declarations, but user function definitions and call sites
used the permissive `_use_byref` (> 64 bytes) threshold. After E5,
both paths are consistent.

The Win64 integration test confirms `Option<Int>` = `{i1, i64}` (16
bytes) uses sret on Win64 but register on SysV — the correct
per-target behavior.

## AArch64 AAPCS64 notes

AArch64 mirrors SysV's 16-byte threshold for the simple case.
AAPCS64 additionally defines Homogeneous Floating-Point Aggregates
(HFA) that can return in up to four SIMD registers, but Mapanare
doesn't generate HFA-eligible aggregates (no float-only struct
variants). The classifier handles this correctly by falling through
to the size check.

## Interaction with E1 unified-ret

The v4.145.0 E1 optimization uses a unified return block with an
alloca for inline enum returns. It requires `not _fn_use_sret` to
activate. With E5, 24-byte inline enums (like `Shape` in enum_match)
now use sret, which disables unified-ret for those functions.

The predicted regression didn't materialize: enum_match went from
0.170 ms to 0.171 ms (+0.6%, within noise). The likely reason is
that LLVM's inliner converts the sret call into a local alloca +
stores, which SROA can decompose just as effectively as the by-value
path. The two approaches converge to identical machine code at -O2.

This is a useful data point: the E1 unified-ret optimization is
only load-bearing for aggregates ≤ 16 bytes (where sret is NOT
used), not for the 24-byte Shape enum where it was originally
measured. The E1 measurement used 10M iterations and external timing,
which amplified a difference that disappears at the sub-millisecond
internal-timing scale used since E4.

## Classifier invariant

The single most important invariant is: the classifier must be called
at both function definition and call sites with identical inputs. Any
disagreement between the two is a miscompilation — the caller would
emit `call {i64,i64,i64} @foo(...)` while the callee expects
`void @foo(ptr sret)`, or vice versa.

The implementation ensures this by:
1. Both paths read the return type from `_sigs[fn]` (same string)
2. Both paths call `_use_sret(ty)` → `classify_return(ty, _tsz(ty), self._triple)`
3. `classify_return` is a pure function of its inputs
4. Integration test `test_header_and_call_agree` validates the invariant

## Carry-forward state

**ABI.1: CLOSED** in `.reviews/CARRY_FORWARD.md`.

New LOW docket opened: **Cb.15-abi-self-hosted** — the self-hosted
emitter (`mapanare/self/emit_llvm.mn`) doesn't have the classifier.
This is a parity item for v4.152.0 or v4.153.0 scope.

## Metrics

- **mapanare/abi.py**: 97 lines (new)
- **mapanare/emit_llvm_text.py**: +17 lines (import + _use_sret method + 3 call sites)
- **tests/llvm/test_abi_struct_return.py**: 178 lines (new, 25 tests)
- **Total diff**: ~292 lines added
- **pytest**: 5286 passed / 0 failed (+28 from 5258)
- **goldens**: 54/66 (unchanged)
- **fixed-point**: NEAR FIXED POINT (4-line version diff)
- **sret count**: 0 → 57 in golden corpus
- **mnc-stage1**: 3,583,120 bytes (was 3,566,736 — +0.5%)
- **ASan**: 0 new findings
- **valgrind**: 0 new findings (4 pre-existing Ge.1)

## Files changed

| File | Change |
|------|--------|
| `mapanare/abi.py` | NEW — per-target classifier |
| `mapanare/emit_llvm_text.py` | `_use_sret` method + 3 call site changes |
| `tests/llvm/test_abi_struct_return.py` | NEW — 25 regression tests |
| `docs/roadmap/v4/v4.149.0/BASELINE.md` | Baseline measurements |
| `docs/roadmap/v4/v4.149.0/IR_DIFF.md` | Cross-target IR comparison |
| `docs/roadmap/v4/v4.149.0/HYPOTHESIS.md` | Per-ABI classification rules |
| `docs/roadmap/v4/v4.149.0/RESULTS.md` | Final measurements + gate status |
| `docs/roadmap/v4/PERF_EXPERIMENTS.md` | E5 row added |
| `.reviews/CARRY_FORWARD.md` | ABI.1 marked CLOSED |
| `benchmarks/cross_language/v4.149.0-*.json` | Benchmark data |
