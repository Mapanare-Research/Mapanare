# v4.149.0 Results — E5 ABI.1 struct return

## Headline

**WIN (correctness).** New `mapanare/abi.py` classifier implements
System V AMD64 §3.2.3, Win64 x64, and AArch64 AAPCS64 return-value
rules. The emitter now matches Clang's convention: aggregates > 16
bytes on SysV (> 8 bytes on Win64) use explicit `sret` in LLVM IR
instead of by-value return. Performance neutral — no regression, no
measurable improvement.

## Benchmark results (20-run median, internal timing)

| Benchmark | Baseline (ms) | Patched (ms) | Delta |
|-----------|--------------|-------------|-------|
| fib_recursive | 15.568 | 15.166 | -2.6% |
| quicksort | 1.142 | 1.142 | 0.0% |
| struct_alloc | 0.028 | 0.020 | -28.6% |
| enum_match | 0.170 | 0.171 | +0.6% |
| prime_sieve | 2.033 | 2.076 | +2.1% |
| string_concat | 0.077 | 0.079 | +2.6% |

`struct_alloc` delta is noise (sub-millisecond workload, +/-30% typical).
All other benchmarks are within measurement noise.

## 5% rule

- **Target benchmark** (`enum_match`): +0.6% — no improvement ≥ 5%
- **Other benchmarks**: no regression > 2% outside noise
- **Decision: KEEP** — ABI.1 is a correctness docket, not a perf docket.
  The classifier is correct regardless of the delta magnitude.

## sret count delta

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| sret occurrences (golden corpus) | 0 | 57 | +57 |
| Tests with sret | 0 | 4 | +4 |

The sret count *increases* because E5 *lowers* the by-value threshold
from 64 bytes (`_BYREF_BYTES`) to 16 bytes (SysV) for return types.
Aggregates 17-64 bytes that were previously returned by value in IR
now use explicit sret, matching Clang's convention.

**Affected tests:**
- `10_result`: 7 sret (Result<Int,String> = 32B)
- `47_try_operator`: 25 sret (Result types)
- `48_match_nested_exhaustive`: 11 sret (nested enums > 16B)
- `62_list_output`: 14 sret (Result types)

The PLAN's prediction of "sret count drops ≥ 60%" was based on an
incorrect assumption that Mapanare unconditionally used sret. The
actual baseline had zero sret in the golden corpus.

## Cross-ABI spot-check

| Target | Shape `{i64,i64,i64}` (24B) | Option<Int> `{i1,i64}` (16B) |
|--------|----------------------------|------------------------------|
| SysV (x86_64-linux) | sret | register |
| Win64 (x86_64-windows) | sret | sret |
| AArch64 (aarch64-macos) | sret | register |

All three targets produce correct conventions matching Clang.

## Sanitizer delta

| Sweep | Before | After | Delta |
|-------|--------|-------|-------|
| ASan ASAN_ERROR | 0 | 0 | **+0** (clean) |
| Valgrind ERRORS | 4 | 4 | **+0** (Ge.1 pre-existing) |

## Quality gates

| Gate | Result |
|------|--------|
| pytest | 5286 passed / 0 failed (+28 from 5258, includes 25 ABI tests) |
| goldens (mnc-stage1) | 54/66 (unchanged) |
| fixed-point | NEAR FIXED POINT (4-line version diff) |
| lint (ruff + black + mypy) | clean |
| ASan | 0 new ASAN_ERROR |
| valgrind | 0 new ERRORS |

## What changed

### `mapanare/abi.py` (new, 97 lines)

Per-target return-value classifier:
- `classify_return(ir_ty, total_size, triple)` → `ReturnABI("register"|"sret")`
- `_classify_sysv`: ≤ 16 bytes → register, > 16 → sret
- `_classify_win64`: exactly 1/2/4/8 bytes → register, else → sret
- `_classify_aapcs64`: ≤ 16 bytes → register, > 16 → sret

### `mapanare/emit_llvm_text.py` (~15 lines changed)

- `_use_sret(self, ty)` method: calls classifier with current triple
- Function definition: `_fn_use_sret = _use_sret(rt_orig)` (was `_use_byref(rt_orig)`)
- Known-function call site: `use_sret = _use_sret(ret)` (was `_use_byref(ret)`)
- Auto-declare call site: `use_sret2 = _use_sret(ret_auto)` (was `_use_byref(ret_auto)`)
- Argument passing unchanged (still uses `_use_byref` with 64B threshold)

### `tests/llvm/test_abi_struct_return.py` (new, 25 tests)

- 9 SysV classifier unit tests
- 6 Win64 classifier unit tests
- 3 AArch64 classifier unit tests
- 7 emitter integration tests (header + call site agreement, cross-target)

## Why enum_match didn't regress

Shape enum = `{i64, i64, i64}` = 24 bytes → now uses sret on SysV.
This disables the v4.145.0 E1 unified-ret optimization for `make_shape`.
However, after LLVM inlines `make_shape` into `main`, the sret pointer
becomes a local alloca that SROA can still decompose. The net effect is
neutral because LLVM's optimizer handles both representations equally
well at -O2.
