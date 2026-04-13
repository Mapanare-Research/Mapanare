# Integration Test Results

Generated: 2026-04-13 05:53 UTC
Source: `integration-results.xml`

## Summary

| Metric | Count |
|--------|-------|
| Total tests | 58 |
| **Passed (end-to-end)** | **46** |
| Failed | 0 |
| Expected failures (xfail) | 5 |
| Skipped (external resources) | 7 |
| Errors | 0 |

**Pass rate: 46/58 (79%)**

## Per-Test Results

| Test | emit | llvm-as | opt | llc | link | run | stdout | Status |
|------|------|---------|-----|-----|------|-----|--------|--------|
| 01_hello | OK | OK | OK | OK | OK | OK | OK | OK |
| 02_arithmetic | OK | OK | OK | OK | OK | OK | OK | OK |
| 03_function | OK | OK | OK | OK | OK | OK | OK | OK |
| 04_if_else | OK | OK | OK | OK | OK | OK | OK | OK |
| 05_for_loop | OK | OK | OK | OK | OK | OK | OK | OK |
| 06_struct | OK | OK | OK | OK | OK | OK | OK | OK |
| 07_enum_match | OK | OK | OK | OK | OK | OK | OK | OK |
| 08_list | OK | OK | OK | OK | OK | OK | OK | OK |
| 09_string_methods | OK | OK | OK | OK | OK | OK | OK | OK |
| 10_result | OK | OK | OK | OK | OK | OK | OK | OK |
| 11_closure | OK | OK | OK | OK | OK | OK | OK | OK |
| 12_while | OK | OK | OK | OK | OK | OK | OK | OK |
| 13_fib | OK | OK | OK | OK | OK | OK | OK | OK |
| 14_nested_struct | OK | OK | OK | OK | OK | OK | OK | OK |
| 15_multifunction | OK | OK | OK | OK | OK | OK | OK | OK |
| 16_string_escape | OK | OK | OK | OK | OK | OK | OK | OK |
| 17_option | OK | OK | OK | OK | OK | OK | OK | OK |
| 18_method_chain | OK | OK | OK | OK | OK | OK | OK | OK |
| 19_nested_match | OK | OK | OK | OK | OK | OK | OK | OK |
| 20_recursion | OK | OK | OK | OK | OK | OK | OK | OK |
| 21_list_ops | OK | OK | OK | OK | OK | OK | OK | OK |
| 22_string_builder | OK | OK | OK | OK | OK | OK | OK | OK |
| 23_multi_return | OK | OK | OK | OK | OK | OK | OK | OK |
| 24_enum_methods | OK | OK | OK | OK | OK | OK | OK | OK |
| 25_fizzbuzz | OK | OK | OK | OK | OK | OK | OK | OK |
| 26_generics | OK | OK | OK | OK | OK | OK | OK | OK |
| 27_impl | OK | OK | OK | OK | OK | OK | OK | OK |
| 28_traits | OK | OK | OK | OK | OK | OK | OK | OK |
| 29_generic_impl | OK | OK | OK | OK | OK | OK | OK | OK |
| 30_nested_generics | OK | OK | OK | OK | OK | OK | OK | OK |
| 31_generic_multi | OK | OK | OK | OK | OK | OK | OK | OK |
| 32_generic_enum | OK | OK | OK | OK | OK | OK | OK | OK |
| 33_break_continue | OK | OK | OK | OK | OK | OK | OK | OK |
| 34_file_io | -- | -- | -- | -- | -- | -- | -- | SKIP |
| 35_stdin | -- | -- | -- | -- | -- | -- | -- | SKIP |
| 36_crypto | -- | -- | -- | -- | -- | -- | -- | SKIP |
| 37_regex | -- | -- | -- | -- | -- | -- | -- | SKIP |
| 38_http | -- | -- | -- | -- | -- | -- | -- | SKIP |
| 39_gpu_detect | -- | -- | -- | -- | -- | -- | -- | SKIP |
| 40_gpu_tensor | -- | -- | -- | -- | -- | -- | -- | SKIP |
| 41_module_let | OK | OK | OK | OK | OK | OK | OK | OK |
| 42_module_let_string | OK | OK | OK | OK | OK | OK | OK | OK |
| 43_module_let_math | OK | OK | OK | OK | OK | OK | OK | OK |
| 45_ffi_bind | OK | OK | OK | OK | OK | OK | OK | OK |
| 47_try_operator | XFAIL | -- | -- | -- | -- | -- | -- | XFAIL |
| 48_match_nested_exhaustive | OK | OK | OK | OK | OK | OK | OK | OK |
| 49_match_guards | OK | OK | OK | OK | OK | OK | OK | OK |
| 49_tensor_literal | OK | OK | OK | OK | OK | OK | OK | OK |
| 50_match_or_patterns | OK | OK | OK | OK | OK | OK | OK | OK |
| 50_tensor_indexing | OK | OK | OK | OK | OK | OK | OK | OK |
| 51_match_guards_and_or | XFAIL | -- | -- | -- | -- | -- | -- | XFAIL |
| 51_tensor_broadcast | OK | OK | OK | OK | OK | OK | OK | OK |
| 52_tensor_slicing | OK | OK | OK | OK | OK | OK | OK | OK |
| 53_linear_regression | OK | OK | OK | OK | OK | OK | OK | OK |
| 54_const_basic | OK | OK | OK | OK | OK | OK | OK | OK |
| 55_async_basic | XFAIL | -- | -- | -- | -- | -- | -- | XFAIL |
| 56_async_await | XFAIL | -- | -- | -- | -- | -- | -- | XFAIL |
| 57_real_await | XFAIL | -- | -- | -- | -- | -- | -- | XFAIL |

## Failure Details

### 47_try_operator (XFAIL)

**Detail:** try operator emits IR with type mismatch (llvm-as rejects)

### 51_match_guards_and_or (XFAIL)

**Detail:** combined guard+or match patterns not yet in emit-llvm

### 55_async_basic (XFAIL)

**Detail:** async/await not yet implemented in emit-llvm

### 56_async_await (XFAIL)

**Detail:** async/await not yet implemented in emit-llvm

### 57_real_await (XFAIL)

**Detail:** async/await not yet implemented in emit-llvm

---

Pipeline: `emit-llvm → llvm-as → opt -O2 → llc -filetype=obj → clang link → execute`

Backend: Python bootstrap (`python -m mapanare emit-llvm`)
