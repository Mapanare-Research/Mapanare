# v4.144.0 Baseline

## Quality gates (pre-release)

| Gate | Result | Notes |
|---|---|---|
| `ruff check .` | 0 errors | clean |
| `black --check .` | 0 reformats (348 files) | clean |
| `mypy mapanare/ runtime/` | 0 errors (52 files) | clean |
| `check_docs_drift` | clean (142 blocks / 4 files) | |
| `check_silent_skips` | clean | |
| `check_struct_registry` | clean (23/23/89) | |
| Non-bootstrap pytest | **5187 passed** / 0 failed / 115 skipped / 9 xfailed | +27 from v4.143.0 (34 Cb.5-tests added) |
| Bootstrap pytest | 212 passed / 13 failed | byte-identical to v4.143.0 |
| Native goldens (`mnc-stage1`) | **54 / 66** | unchanged from v4.143.0 |
| Valgrind ERRORS | 0 | baseline from v4.143.0 |
| ASan ASAN_ERROR | 0 | baseline from v4.143.0 |
| Fixed-point | NEAR FIXED POINT | 4-line diff (Dr.1 version-metadata), 110,127 lines |
| stage2.ll md5 | `436d34e72936c87c659cafe6fd80f8a2` | |
| stage3.ll md5 | `612b352c8c4c86b1a326d967c92a7419` | |
| mnc-stage1 size | 3,566,736 bytes (stripped) | |

## What changed from v4.143.0

- **Cb.5-tests**: 34 new unit tests in `tests/llvm/test_enum_inline.py`
  (9 eligibility + 12 type predicate + 7 pack/unpack + 3 IR shape + 3 ABI parity)
- **Cb.6**: Trailing-`*` typed-pointer-legacy guard added to self-hosted
  `type_fits_inline_slot` in `emit_llvm.mn`
- **Cb.7**: Clear-after-transfer pattern applied to `try_monomorphize_struct`
  in `lower.mn` (mirrors the v4.142.0 Ge.1 fix in `try_monomorphize_enum`).
  `register_struct` / `register_enum` sites were attempted but reverted —
  the reassignment triggers drop-glue on the transferred buffer during
  the assignment itself (Mapanare lacks move semantics; the reassignment
  `x = []` drops the old value of `x` before the new value is assigned,
  which frees the buffer that was already transferred to the module state).
  The monomorphization sites are safe because the clear runs after the
  enclosing `if !is_*_name` block, by which point the buffer is already
  committed to the returned state and the function continues execution
  (not an immediate return). Filed as note for Own.1 (v5.x move semantics).
- **Cb.9a**: Self-hosted `semantic.mn` documented as lacking `module_path`
  concept; qualified type refs resolve via flattened string. Deferred to v5.x.
- **Cb.10**: `66_qualified_type_ref.mn` docstring rewritten to match actual
  test shape (struct construction, not qualified type refs).

## Benchmark baseline

Benchmark numbers deferred to Phase 7. This section will be populated
after the cross-language + async benchmark runs complete.
