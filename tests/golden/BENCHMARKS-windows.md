# Mapanare Benchmarks - Windows

> **v5.21.1 H.12 — Windows benchmark last sync.** The numbers
> below are pinned to v5.8.8 because the Windows benchmark
> runner has not re-emitted since the v5.8.8 → v5.21.0 stretch
> (auto-regenerated only when `scripts/test_native.py` runs on
> a Windows host; the linux runner refreshes
> `BENCHMARKS-linux.md` on every CI run). Per-platform split
> structurally closes the v5.11.0 panel Rattler #1 finding;
> staleness is visible here and in the merged `BENCHMARKS.md`.
> Re-run on a Windows host to refresh.

Generated: 2026-04-28 00:44 UTC (last Windows-host run)
Version: 5.8.8 (`1057e2de`)
Platform: Darwin arm64, Python 3.12.13
Total time: 1.2s

## Bootstrap Compiler (Python)

| Test | Src | IR | KB | Fns | BBs | Stk | ms | Trend | Status |
|------|----:|---:|---:|----:|----:|----:|---:|-------|--------|
| 01_hello | 3 | 32 | 0.9 | 1 | 2 | 9 | 521 | `------~~ v` | PASS |
| 02_arithmetic | 4 | 46 | 1.5 | 1 | 4 | 25 | 3 | `--**--*- v` | PASS |
| 03_function | 8 | 50 | 1.6 | 1 | 6 | 25 | 3 | `....****` | PASS |
| 04_if_else | 8 | 36 | 1.0 | 1 | 4 | 9 | 2 | `***   **` | PASS |
| 05_for_loop | 7 | 96 | 3.1 | 1 | 7 | 75 | 2 | `*** * **` | PASS |
| 06_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 3 | `***** **` | PASS |
| 07_enum_match | 13 | 67 | 2.2 | 1 | 5 | 42 | 5 | `_____ **` | PASS |
| 08_list | 5 | 105 | 4.1 | 1 | 6 | 129 | 3 | ` *      ` | PASS |
| 09_string_methods | 5 | 88 | 3.3 | 1 | 6 | 51 | 1 | `        ` | PASS |
| 10_result | 14 | 147 | 5.3 | 2 | 10 | 155 | 3 | ` ***  **` | PASS |
| 11_closure | 5 | 102 | 3.5 | 1 | 8 | 89 | 1 | `        ` | PASS |
| 12_while | 7 | 77 | 2.4 | 1 | 7 | 58 | 1 | `*      * ^` | PASS |
| 13_fib | 10 | 112 | 3.4 | 2 | 9 | 106 | 1 | `*   * **` | PASS |
| 14_nested_struct | 9 | 61 | 2.1 | 1 | 4 | 49 | 1 | `   *    ` | PASS |
| 15_multifunction | 12 | 78 | 2.6 | 1 | 10 | 50 | 2 | `      **` | PASS |
| 16_string_escape | 8 | 56 | 2.0 | 1 | 2 | 27 | 1 | `  ` | PASS |
| 17_option | 19 | 188 | 6.3 | 2 | 15 | 173 | 3 | ` * ^` | PASS |
| 18_method_chain | 9 | 124 | 4.9 | 1 | 8 | 84 | 2 | `  ` | PASS |
| 19_nested_match | 18 | 164 | 5.6 | 2 | 11 | 170 | 3 | `*  v` | PASS |
| 20_recursion | 11 | 130 | 4.1 | 2 | 11 | 123 | 2 | `  ` | PASS |
| 21_list_ops | 15 | 242 | 9.1 | 2 | 15 | 285 | 2 | `  ` | PASS |
| 22_string_builder | 14 | 167 | 6.0 | 2 | 11 | 134 | 2 | `  ` | PASS |
| 23_multi_return | 15 | 108 | 3.9 | 1 | 8 | 98 | 2 | `  ` | PASS |
| 24_enum_methods | 20 | 109 | 3.9 | 2 | 8 | 82 | 2 | `  ` | PASS |
| 25_fizzbuzz | 18 | 204 | 6.7 | 2 | 20 | 166 | 2 | `*  v` | PASS |
| 26_generics | 29 | 116 | 3.8 | 1 | 12 | 63 | 3 | `*  v` | PASS |
| 27_impl | 21 | 68 | 2.0 | 1 | 6 | 50 | 3 | `  ` | PASS |
| 28_traits | 25 | 73 | 2.3 | 1 | 6 | 58 | 2 | `  ` | PASS |
| 29_generic_impl | 24 | 80 | 2.5 | 1 | 8 | 59 | 3 | `  ` | PASS |
| 30_nested_generics | 20 | 115 | 4.3 | 1 | 2 | 117 | 2 | `  ` | PASS |
| 31_generic_multi | 35 | 120 | 4.0 | 1 | 12 | 93 | 4 | `  ` | PASS |
| 32_generic_enum | 16 | 39 | 1.1 | 1 | 2 | 18 | 1 | `  ` | PASS |
| 33_break_continue | 58 | 440 | 13.8 | 5 | 38 | 454 | 5 | `  ` | PASS |
| 34_file_io | 19 | 238 | 10.3 | 1 | 12 | 193 | 2 | `  ` | PASS |
| 35_stdin | 4 | 92 | 3.6 | 1 | 8 | 65 | 1 | `  ` | PASS |
| 36_crypto | 13 | 147 | 5.9 | 1 | 12 | 108 | 1 | `  ` | PASS |
| 37_regex | 10 | 163 | 6.9 | 1 | 8 | 109 | 2 | `*  v` | PASS |
| 38_http | 5 | 74 | 2.8 | 1 | 6 | 49 | 1 | `  ` | PASS |
| 39_gpu_detect | 8 | 144 | 5.6 | 1 | 13 | 100 | 2 | `  ` | PASS |
| 40_gpu_tensor | 18 | 437 | 19.1 | 1 | 33 | 510 | 3 | `  ` | PASS |
| 41_module_let | 13 | 45 | 1.3 | 1 | 4 | 18 | 1 | `  ` | PASS |
| 42_module_let_string | 19 | 49 | 1.5 | 1 | 4 | 18 | 1 | ` * ^` | PASS |
| 43_module_let_math | 19 | 49 | 1.5 | 1 | 4 | 18 | 1 | ` * ^` | PASS |
| 45_ffi_bind | 15 | 98 | 2.7 | 2 | 9 | 83 | 2 | `  ` | PASS |
| 47_try_operator | 32 | 306 | 11.7 | 4 | 23 | 311 | 4 | `  ` | PASS |
| 48_match_nested_exhaustive | 23 | 345 | 14.0 | 3 | 32 | 325 | 3 | `  ` | PASS |
| 49_match_guards | 16 | 205 | 6.9 | 2 | 16 | 169 | 3 | ` * ^` | PASS |
| 49_tensor_literal | 58 | 735 | 30.4 | 1 | 48 | 826 | 6 | `  ` | PASS |
| 50_match_or_patterns | 25 | 177 | 6.7 | 2 | 11 | 140 | 2 | ` * ^` | PASS |
| 50_tensor_indexing | 46 | 678 | 28.1 | 1 | 34 | 899 | 4 | ` * ^` | PASS |
| 51_match_guards_and_or | 17 | 298 | 10.4 | 2 | 20 | 274 | 3 | `  ` | PASS |
| 51_tensor_broadcast | 57 | 623 | 25.8 | 1 | 48 | 660 | 4 | `  ` | PASS |
| 52_tensor_slicing | 49 | 659 | 27.5 | 1 | 42 | 750 | 4 | `  ` | PASS |
| 53_linear_regression | 43 | 390 | 16.0 | 1 | 25 | 413 | 3 | `  ` | PASS |
| 54_const_basic | 12 | 86 | 3.1 | 1 | 6 | 59 | 1 | `*  v` | PASS |
| 55_async_basic | 12 | 134 | 4.8 | 2 | 11 | 41 | 1 | `  ` | PASS |
| 56_async_await | 17 | 223 | 8.1 | 3 | 22 | 73 | 1 | `  ` | PASS |
| 57_real_await | 28 | 392 | 14.4 | 5 | 44 | 121 | 2 | `  ` | PASS |
| 58_async_file_io | 28 | 309 | 11.1 | 4 | 34 | 90 | 2 | `  ` | PASS |
| 58_const_scope | 21 | 61 | 1.8 | 1 | 10 | 18 | 2 | `  ` | PASS |
| 59_async_fanout | 63 | 1015 | 37.7 | 12 | 121 | 345 | 3 | `  ` | PASS |
| 62_list_output | 35 | 307 | 14.9 | 2 | 20 | 321 | 4 | `  ` | PASS |
| 63_else_sino | 40 | 259 | 8.7 | 3 | 20 | 250 | 3 | `  ` | PASS |
| 64_closure_typed | 25 | 245 | 8.4 | 1 | 22 | 260 | 4 | ` * ^` | PASS |
| 65_list_int_indexing | 31 | 323 | 13.0 | 1 | 26 | 325 | 2 | `  ` | PASS |
| 66_qualified_type_ref | 21 | 46 | 1.3 | 1 | 4 | 33 | 1 | `  ` | PASS |
| **Total** | **1336** | **13053** | **491.8** | **112** | **1039** | **11149** | **680** | | **66/66** |

## Native Compiler (mnc-stage1)

| Test | IR | KB | Fns | ms | Match | Status |
|------|---:|---:|----:|---:|-------|--------|
| 01_hello | 195 | 11.5 | 1 | 8 | YES | PASS |
| 02_arithmetic | 205 | 11.8 | 1 | 8 | YES | PASS |
| 03_function | 227 | 12.5 | 2 | 8 | YES | PASS |
| 04_if_else | 212 | 12.1 | 1 | 7 | YES | PASS |
| 05_for_loop | 228 | 12.7 | 1 | 7 | YES | PASS |
| 06_struct | 208 | 12.0 | 1 | 8 | YES | PASS |
| 07_enum_match | 218 | 12.3 | 1 | 7 | YES | PASS |
| 08_list | 234 | 13.3 | 1 | 6 | YES | PASS |
| 09_string_methods | 218 | 12.6 | 1 | 7 | YES | PASS |
| 10_result | 263 | 14.1 | 2 | 7 | YES | PASS |
| 11_closure | 218 | 12.1 | 1 | 7 | YES | PASS |
| 12_while | 214 | 12.0 | 1 | 6 | YES | PASS |
| 13_fib | 225 | 12.2 | 2 | 7 | YES | PASS |
| 14_nested_struct | 208 | 12.0 | 1 | 8 | YES | PASS |
| 15_multifunction | 238 | 12.8 | 3 | 8 | YES | PASS |
| 16_string_escape | 214 | 12.5 | 1 | 6 | YES | PASS |
| 17_option | 290 | 14.9 | 2 | 8 | YES | PASS |
| 18_method_chain | 240 | 13.6 | 1 | 7 | YES | PASS |
| 19_nested_match | 263 | 13.8 | 2 | 7 | YES | PASS |
| 20_recursion | 231 | 12.6 | 2 | 8 | YES | PASS |
| 21_list_ops | 316 | 16.7 | 2 | 8 | YES | PASS |
| 22_string_builder | 283 | 15.1 | 2 | 7 | YES | PASS |
| 23_multi_return | 257 | 14.1 | 2 | 7 | YES | PASS |
| 24_enum_methods | 251 | 13.7 | 2 | 7 | YES | PASS |
| 25_fizzbuzz | 295 | 14.9 | 2 | 7 | YES | PASS |
| 26_generics | 275 | 14.0 | 5 | 7 | YES | PASS |
| 27_impl | 235 | 12.8 | 3 | 8 | YES | PASS |
| 28_traits | 243 | 13.1 | 3 | 8 | YES | PASS |
| 29_generic_impl | 244 | 13.3 | 3 | 8 | YES | PASS |
| 30_nested_generics | 235 | 13.6 | 1 | 8 | YES | PASS |
| 31_generic_multi | 260 | 14.1 | 4 | 8 | YES | PASS |
| 32_generic_enum | 206 | 11.9 | 1 | 7 | YES | PASS |
| 33_break_continue | 419 | 18.7 | 5 | 8 | YES | PASS |
| 34_file_io | 290 | 16.4 | 1 | 7 | YES | PASS |
| 35_stdin | 220 | 12.7 | 1 | 6 | YES | PASS |
| 36_crypto | 249 | 14.2 | 1 | 6 | YES | PASS |
| 37_regex | 260 | 14.8 | 1 | 8 | YES | PASS |
| 38_http | 211 | 12.3 | 1 | 7 | YES | PASS |
| 39_gpu_detect | 238 | 13.5 | 1 | 7 | YES | PASS |
| 40_gpu_tensor | 425 | 22.2 | 1 | 6 | YES | PASS |
| 41_module_let | 209 | 11.8 | 2 | 6 | YES | PASS |
| 42_module_let_string | 212 | 12.0 | 2 | 6 | YES | PASS |
| 43_module_let_math | 216 | 12.2 | 2 | 6 | YES | PASS |
| 45_ffi_bind | 244 | 12.7 | 3 | 7 | YES | PASS |
| 47_try_operator | 347 | 17.5 | 4 | 9 | YES | PASS |
| 48_match_nested_exhaustive | 440 | 22.0 | 3 | 8 | YES | PASS |
| 49_match_guards | 267 | 14.4 | 2 | 7 | YES | PASS |
| 49_tensor_literal | 472 | 24.0 | 1 | 7 | YES | PASS |
| 50_match_or_patterns | 285 | 15.3 | 2 | 7 | YES | PASS |
| 50_tensor_indexing | 444 | 22.8 | 1 | 7 | YES | PASS |
| 51_match_guards_and_or | 336 | 17.1 | 2 | 7 | YES | PASS |
| 51_tensor_broadcast | 456 | 22.9 | 1 | 8 | YES | PASS |
| 52_tensor_slicing | 451 | 23.1 | 1 | 9 | YES | PASS |
| 53_linear_regression | 378 | 19.4 | 1 | 8 | YES | PASS |
| 54_const_basic | 215 | 12.4 | 1 | 7 | YES | PASS |
| 55_async_basic | 257 | 13.9 | 2 | 6 | YES | PASS |
| 56_async_await | 336 | 16.8 | 3 | 7 | YES | PASS |
| 57_real_await | 492 | 22.6 | 5 | 7 | YES | PASS |
| 58_async_file_io | 419 | 19.8 | 4 | 7 | YES | PASS |
| 58_const_scope | 248 | 13.3 | 2 | 7 | YES | PASS |
| 59_async_fanout | 1045 | 43.6 | 12 | 8 | YES | PASS |
| 62_list_output | 376 | 20.3 | 3 | 8 | YES | PASS |
| 63_else_sino | 304 | 15.2 | 3 | 7 | YES | PASS |
| 64_closure_typed | 317 | 15.4 | 3 | 7 | YES | PASS |
| 65_list_int_indexing | 394 | 20.7 | 1 | 7 | YES | PASS |
| 66_qualified_type_ref | 231 | 12.9 | 2 | 7 | YES | PASS |
| **Total** | | | | **474** | **66/66** | **66/66** |

## Speed Comparison

| Test | Bootstrap (ms) | Stage1 (ms) | Speedup |
|------|---------------:|------------:|--------:|
| 01_hello | 521 | 8 | 63.8x |
| 02_arithmetic | 3 | 8 | 0.4x |
| 03_function | 3 | 8 | 0.4x |
| 04_if_else | 2 | 7 | 0.3x |
| 05_for_loop | 2 | 7 | 0.3x |
| 06_struct | 3 | 8 | 0.3x |
| 07_enum_match | 5 | 7 | 0.8x |
| 08_list | 3 | 6 | 0.5x |
| 09_string_methods | 1 | 7 | 0.2x |
| 10_result | 3 | 7 | 0.4x |
| 11_closure | 1 | 7 | 0.2x |
| 12_while | 1 | 6 | 0.2x |
| 13_fib | 1 | 7 | 0.2x |
| 14_nested_struct | 1 | 8 | 0.2x |
| 15_multifunction | 2 | 8 | 0.3x |
| 16_string_escape | 1 | 6 | 0.2x |
| 17_option | 3 | 8 | 0.4x |
| 18_method_chain | 2 | 7 | 0.2x |
| 19_nested_match | 3 | 7 | 0.5x |
| 20_recursion | 2 | 8 | 0.2x |
| 21_list_ops | 2 | 8 | 0.3x |
| 22_string_builder | 2 | 7 | 0.3x |
| 23_multi_return | 2 | 7 | 0.3x |
| 24_enum_methods | 2 | 7 | 0.3x |
| 25_fizzbuzz | 2 | 7 | 0.3x |
| 26_generics | 3 | 7 | 0.5x |
| 27_impl | 3 | 8 | 0.4x |
| 28_traits | 2 | 8 | 0.3x |
| 29_generic_impl | 3 | 8 | 0.4x |
| 30_nested_generics | 2 | 8 | 0.2x |
| 31_generic_multi | 4 | 8 | 0.5x |
| 32_generic_enum | 1 | 7 | 0.2x |
| 33_break_continue | 5 | 8 | 0.6x |
| 34_file_io | 2 | 7 | 0.3x |
| 35_stdin | 1 | 6 | 0.1x |
| 36_crypto | 1 | 6 | 0.2x |
| 37_regex | 2 | 8 | 0.2x |
| 38_http | 1 | 7 | 0.2x |
| 39_gpu_detect | 2 | 7 | 0.2x |
| 40_gpu_tensor | 3 | 6 | 0.4x |
| 41_module_let | 1 | 6 | 0.2x |
| 42_module_let_string | 1 | 6 | 0.2x |
| 43_module_let_math | 1 | 6 | 0.2x |
| 45_ffi_bind | 2 | 7 | 0.3x |
| 47_try_operator | 4 | 9 | 0.4x |
| 48_match_nested_exhaustive | 3 | 8 | 0.4x |
| 49_match_guards | 3 | 7 | 0.4x |
| 49_tensor_literal | 6 | 7 | 0.9x |
| 50_match_or_patterns | 2 | 7 | 0.3x |
| 50_tensor_indexing | 4 | 7 | 0.6x |
| 51_match_guards_and_or | 3 | 7 | 0.4x |
| 51_tensor_broadcast | 4 | 8 | 0.6x |
| 52_tensor_slicing | 4 | 9 | 0.5x |
| 53_linear_regression | 3 | 8 | 0.4x |
| 54_const_basic | 1 | 7 | 0.2x |
| 55_async_basic | 1 | 6 | 0.2x |
| 56_async_await | 1 | 7 | 0.2x |
| 57_real_await | 2 | 7 | 0.3x |
| 58_async_file_io | 2 | 7 | 0.3x |
| 58_const_scope | 2 | 7 | 0.3x |
| 59_async_fanout | 3 | 8 | 0.4x |
| 62_list_output | 4 | 8 | 0.4x |
| 63_else_sino | 3 | 7 | 0.4x |
| 64_closure_typed | 4 | 7 | 0.6x |
| 65_list_int_indexing | 2 | 7 | 0.4x |
| 66_qualified_type_ref | 1 | 7 | 0.2x |

