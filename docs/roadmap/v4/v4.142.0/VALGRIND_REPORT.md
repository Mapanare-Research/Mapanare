# v4.142.0 Valgrind Report — 66 Golden Tests Swept

> Generated 2026-04-16. Ran the self-hosted `mnc-stage1` under
> `valgrind --leak-check=full --track-origins=yes --error-exitcode=99`
> against every `tests/golden/*.mn` file after the Ge.1 fix and rebuild.

## Verdict

| Class | v4.135.0 | **v4.142.0** |
|---|---:|---:|
| CLEAN | 0 | **0** |
| WARNINGS_ONLY | 60 | **66** |
| ERRORS | 5 | **0** |
| Total | 65 | **66** |

**Ge.1 is closed.** The five residual generic-monomorphization
valgrind ERRORS from v4.135.0 are gone, and the new
`66_qualified_type_ref.mn` golden also lands as WARNINGS_ONLY.

The sweep stays at **0 CLEAN** because the compiler still uses the
documented arena-allocation strategy that retains memory to process exit.
Those are warnings, not valgrind errors.

## Methodology

```bash
VG_OUTDIR=docs/roadmap/v4/v4.142.0/valgrind-logs \
    bash scripts/valgrind_all_goldens.sh \
    2>&1 | tee docs/roadmap/v4/v4.142.0/valgrind-run.log
```

Artifacts preserved:

- `docs/roadmap/v4/v4.142.0/valgrind-run.log`
- `docs/roadmap/v4/v4.142.0/valgrind-summary.tsv`
- `docs/roadmap/v4/v4.142.0/valgrind-logs/*.log`

## Binary used

`mapanare/self/mnc-stage1` rebuilt at v4.142.0:

- stripped size: **3,566,736 bytes**
- sha256: `e0fe23b76da31378a32b67c4a255efaea95cb52a168bb1e24527eacb40b8a11a`
- emitted `main.ll`: **909,244 lines**

## Ge.1 closure detail

The five formerly failing tests now complete with **`ERROR SUMMARY: 0`**
and classify as WARNINGS_ONLY:

| Test | v4.135.0 | **v4.142.0** |
|---|---|---|
| `26_generics` | ERRORS | **WARNINGS_ONLY** |
| `29_generic_impl` | ERRORS | **WARNINGS_ONLY** |
| `30_nested_generics` | ERRORS | **WARNINGS_ONLY** |
| `31_generic_multi` | ERRORS | **WARNINGS_ONLY** |
| `32_generic_enum` | ERRORS | **WARNINGS_ONLY** |

Per-test targeted checks all exit clean under valgrind:

```bash
26_generics       -> exit=0
29_generic_impl   -> exit=0
30_nested_generics-> exit=0
31_generic_multi  -> exit=0
32_generic_enum   -> exit=0
```

## What changed

The release did **not** land the prompt's originally sketched
`fresh_tmp`/`MemsetZero` path. That plan was stale against the current
self-hosted tree.

The actual closure came from two fixes in the live self-hosted path:

1. Internal-struct metadata parity fixes in `mapanare/self/emit_llvm.mn`
   and `mapanare/self/lower.mn`, which corrected stale field layouts used
   by the emitter/lowerer boundary.
2. A targeted ownership fix in
   `mapanare/self/lower.mn::try_monomorphize_enum`, where specialized
   enum metadata lists were moved into the returned state and then still
   freed by the local epilogue. Clearing those moved list headers closed
   the remaining `32_generic_enum` use-after-free.

## Carry-forward

- **Valgrind ERRORS: none remain.**
- WARNINGS_ONLY remains the expected arena-allocation profile plus
  feature-gap exits on tests that still return non-zero without
  tripping valgrind errors.
- Ge.1 should now be treated as **CLOSED** in the ledger and in the
  v4.143.0 panel evidence pack.
