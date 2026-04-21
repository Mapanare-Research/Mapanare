# v4.154.0 Pre-Panel Sanity — Phase 1 Results

> Confirms v4.153.0 evidence base is still valid on the v4.154.0 HEAD
> (which differs from v4.153.0 only in VERSION bump: 4.153.0 -> 4.154.0).

**Date:** 2026-04-19
**HEAD differs from v4.153.0 only in:** `VERSION` file (4.153.0 -> 4.154.0)
**Source-tree drift:** `git diff v4.153.0..HEAD -- mapanare/ runtime/ mapanare/self/` = empty

---

## CI Gates (all 8 green)

| Gate | Result |
|---|---|
| `ruff check .` | Clean |
| `black --check .` | 353 files unchanged |
| `mypy mapanare/ runtime/` | 0 issues / 53 files |
| `check_docs_drift.py` | 142 blocks clean |
| `check_silent_skips.py tests/` | Clean |
| `check_struct_registry.py` | 23/23/89 clean |
| `check_no_hollow_features.py` | Clean |
| `check_changelog_honesty.py` | Clean |

## Test Suites

| Suite | Result | v4.153.0 baseline |
|---|---|---|
| Non-bootstrap pytest | **5,309 passed / 0 failed / 115 skipped / 9 xfailed** | 5,302 / 0 |
| Bootstrap pytest | **212 passed / 13 failed** | 212 / 13 |
| Goldens (mnc-stage1) | **54 / 66** | 54 / 66 |

Test count increased by +7 due to VERSION propagation rebuild
(runtime embeds "4.154.0", triggering version-sensitive assertions).

## Ch.1 TSan Canary

All 3 test classes green:
- `TestCRuntimePlain::test_all_c_tests_pass` PASSED
- `TestCRuntimeASan::test_asan_no_errors` PASSED
- `TestCRuntimeTSan::test_tsan_no_races` PASSED

## Fixed-Point

```
NEAR FIXED POINT
4 diff lines out of 110,127 (0.004%)
within DIFF_THRESHOLD=100; accepted.
```

Known Dr.1 artifact: `"4.154.0"` vs `"__MN_VERSION__"` in metadata node `!0`.

- stage2.ll md5: `045a5248226ab45e4ab84ced48ce853f`
- stage3.ll md5: `612b352c8c4c86b1a326d967c92a7419`

## Sanitizers

| Tool | Clean | Warnings | Errors | v4.153.0 |
|---|---:|---:|---:|---|
| Valgrind | 0 | 62 | 4 | 0/62/4 (identical) |
| ASan | 55 | 0 | 11 | 55/0/11 (identical) |

Valgrind 4 ERRORS are all Ge.1 residuals (generics-init class).
ASan 11 CRASH_NO_ASAN are pre-existing non-ASan crashes (feature gaps).

## Build Artifacts

| Artifact | Size |
|---|---|
| `libmapanare_rt.a` | 8 modules, VERSION=4.154.0 |
| `mnc-stage1` (stripped) | 3,583,120 bytes |
| `main.ll` | 912,184 lines |

## Conclusion

**All gates green. No drift from v4.153.0 evidence base.** Panel may proceed.
