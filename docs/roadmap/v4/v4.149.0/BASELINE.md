# v4.149.0 Baseline — E5 ABI.1

## Cross-language benchmarks (20-run median, internal timing)

| Benchmark | C (gcc) | C (clang) | Rust | Go | Mapanare | Python |
|-----------|---------|-----------|------|----|----------|--------|
| fib_recursive | 11.393 | 18.736 | 19.080 | 32.446 | 15.568 | 793.456 |
| quicksort | 0.345 | 0.338 | 0.373 | 0.386 | 1.142 | 81.471 |
| struct_alloc | 0.581 | 0.017 | 0.021 | 0.020 | 0.028 | 212.161 |
| enum_match | 0.132 | 0.146 | 0.287 | 0.199 | 0.170 | 81.430 |
| prime_sieve | 1.961 | 1.768 | 1.798 | 2.015 | 2.033 | 386.756 |
| string_concat | 0.073 | 0.052 | 0.052 | 52.529 | 0.077 | 9.466 |

All times in milliseconds.

## ABI.1-relevant ratios

| Benchmark | Mapanare / Rust | Return type | Size |
|-----------|----------------|-------------|------|
| enum_match | 0.59× (faster) | `{i64, i64, i64}` | 24B |
| struct_alloc | 1.33× | `{i64}` | 8B |
| quicksort | 3.06× | `i64` (scalar) | N/A |

## sret count baseline

**0 sret** across all 66 golden tests on SysV (x86_64-pc-linux-gnu).

Current `_BYREF_BYTES = 64`: all aggregates ≤ 64 bytes return by value
in LLVM IR. No user function in the golden corpus returns an aggregate
> 64 bytes. The self-hosted compiler's large state structs (LowerState
240B, EmitState 240B) do use sret/byref, but these are not in the
golden test corpus.

## Quality baselines

- pytest: 5258 passed / 0 failed / 115 skipped / 9 xfailed
- goldens: 54/66 (mnc-stage1)
- lint: clean (ruff + black + mypy)
- mnc-stage1: 3,566,736 bytes stripped
