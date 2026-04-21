# v4.153.0 ASan Report

## Summary

| Class | v4.142.0 | **v4.153.0** | Delta |
|---|---:|---:|---|
| CLEAN | 55 | **55** | — |
| ASAN_ERROR | 0 | **0** | — |
| CRASH_NO_ASAN | 11 | **11** | — |

**Zero ASan errors.** Identical to v4.142.0 baseline.

The 11 CRASH_NO_ASAN are the same async/tensor/closure-typed
feature-gap cohort — these tests fail to compile (not memory bugs).

## Artifacts

- `docs/roadmap/v4/v4.153.0/asan-summary.tsv`

## How to reproduce

```bash
bash scripts/build_asan.sh
bash scripts/run_asan_goldens.sh
```
