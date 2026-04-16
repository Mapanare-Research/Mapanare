# v4.142.0 ASan Report — 66 Golden Tests Swept

> Generated 2026-04-16. Rebuilt `mnc-stage1-asan` and ran the full golden
> suite through the ASan harness after the Ge.1 closure patch.

## Verdict

| Class | v4.135.0 | **v4.142.0** |
|---|---:|---:|
| CLEAN | 54 | **55** |
| ASAN_ERROR | 0 | **0** |
| CRASH_NO_ASAN | 11 | **11** |
| Total | 65 | **66** |

**ASAN_ERROR remains at zero.** The new clean cell is the added
`66_qualified_type_ref.mn` golden, and all five former Ge.1 generic
tests remain ASan-clean.

## Methodology

```bash
bash scripts/build_asan.sh
ASAN_OUTDIR=docs/roadmap/v4/v4.142.0/asan-logs \
    bash scripts/run_asan_goldens.sh \
    2>&1 | tee docs/roadmap/v4/v4.142.0/asan-run.log
```

Artifacts preserved:

- `docs/roadmap/v4/v4.142.0/asan-run.log`
- `docs/roadmap/v4/v4.142.0/asan-summary.tsv`
- `docs/roadmap/v4/v4.142.0/asan-logs/*.err`

## Live result

The harness summary is:

- **Total:** 66
- **CLEAN:** 55
- **ASAN_ERROR:** 0
- **CRASH_NO_ASAN:** 11

## CLEAN set change

The Ge.1 targets are all now clean under ASan:

| Test | Class |
|---|---|
| `26_generics` | CLEAN |
| `29_generic_impl` | CLEAN |
| `30_nested_generics` | CLEAN |
| `31_generic_multi` | CLEAN |
| `32_generic_enum` | CLEAN |
| `66_qualified_type_ref` | CLEAN |

## Residual CRASH_NO_ASAN set

The 11 residual non-ASan crashes are unchanged feature-gap tests:

- `49_tensor_literal`
- `50_tensor_indexing`
- `51_tensor_broadcast`
- `52_tensor_slicing`
- `53_linear_regression`
- `55_async_basic`
- `56_async_await`
- `57_real_await`
- `58_async_file_io`
- `59_async_fanout`
- `64_closure_typed`

These remain the self-hosted async / tensor / closure-typed gap cohort,
not memory-safety findings.

## Carry-forward

- **ASAN_ERROR stays at 0.**
- No new sanitizer docket opens here.
- The only remaining non-clean ASan outcomes are the already-docketed
  feature gaps above.
