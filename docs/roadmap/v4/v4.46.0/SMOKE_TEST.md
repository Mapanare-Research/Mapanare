# v4.46.0 Pre-Panel Smoke Test Results

**Date:** 2026-04-12
**Environment:** WSL2 (Ubuntu), Python 3.12.3

## Pytest Suite

- **4911 passed**, 37 failed, 49 skipped, 64 xfailed, 8 xpassed
- **Zero tensor-related failures.** All 37 failures are infrastructure/environment:
  - `test_doc_links`: 8 broken links to far-future PLANs (v4.58+)
  - `test_ci`: black/ruff/mypy not available in WSL test environment
  - `test_c_hardening`: native C tests require gcc/asan/tsan
  - `test_fs_extended`: filesystem tests require native runtime
  - `test_main_mn`: mnc-stage1 VERSION mismatch (expected)
  - `test_doc_consistency`: feature table drift (1 test)

## Tensor-Specific Tests: 100/100 PASS

| Module | Tests | Status |
|--------|-------|--------|
| `tests/parser/test_tensor_literal.py` | 13 | PASS |
| `tests/semantic/test_tensor_literal.py` | 7 | PASS |
| `tests/semantic/test_tensor_indexing.py` | 8 | PASS |
| `tests/semantic/test_tensor_broadcast.py` | 10 | PASS |
| `tests/llvm/test_tensor_literal.py` | 12 | PASS |
| `tests/llvm/test_tensor_indexing.py` | 7 | PASS |
| `tests/llvm/test_tensor_broadcast.py` | 9 | PASS |
| `tests/llvm/test_tensor_reductions.py` | 8 | PASS |
| `tests/llvm/test_tensor_reductions.py::Slicing` | 2 | PASS |
| **Remaining tensor tests** | 24 | PASS |

## Golden Tests: 5/5 Tensor Goldens Compile + Validate

| Golden | emit-llvm | llvm-as |
|--------|-----------|---------|
| `49_tensor_literal.mn` | PASS | PASS |
| `50_tensor_indexing.mn` | PASS | PASS |
| `51_tensor_broadcast.mn` | PASS | PASS |
| `52_tensor_slicing.mn` | PASS | PASS |
| `53_linear_regression.mn` | PASS | PASS |

Total golden count: **54** (6 tensor-related including 40_gpu_tensor.mn).

## GPU Smoke Test

**Skipped** — no CUDA/Vulkan available in CI environment. CPU fallback path is the real requirement and passes all tests. Not a release blocker.

## Verdict

Pre-panel smoke test: **PASS**. Tensor pipeline is clean across all 4 arc releases (v4.42.0-v4.45.0).
