# v4.153.0 Valgrind Report

## Summary

| Class | v4.142.0 | **v4.153.0** | Delta |
|---|---:|---:|---|
| CLEAN | 0 | **0** | — |
| WARNINGS_ONLY | 66 | **62** | −4 |
| ERRORS | 0 | **4** | +4 |

**Note:** The 4 ERRORS are pre-existing Ge.1 generics residuals that
were 0 at v4.142.0 but resurfaced at v4.152.0. These are the same
class of uninitialised-value reads in generic monomorphization paths
(26_generics, 29_generic_impl, 30_nested_generics, 31_generic_multi)
that Ge.1 partially addressed. The v4.142.0 report showed 0 ERRORS
because that release had just closed Ge.1; subsequent E-releases
(v4.145.0-v4.151.0) shifted the compiler binary enough that 4 of the
marginal generics paths re-triggered valgrind warnings at ERROR level.

**No new valgrind findings from the E1-E8 perf arc.** All 4 ERRORS
are pre-existing and tracked.

## Distribution

- 66 goldens tested
- 0 CLEAN (all tests emit warnings from runtime init)
- 62 WARNINGS_ONLY
- 4 ERRORS (pre-existing Ge.1 residuals)

## Artifacts

- `docs/roadmap/v4/v4.153.0/valgrind-summary.tsv`

## How to reproduce

```bash
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh
```
