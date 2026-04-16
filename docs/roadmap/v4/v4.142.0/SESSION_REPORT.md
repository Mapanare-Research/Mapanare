# v4.142.0 Session Report — Ge.1 closed + pre-panel refresh

**Date:** 2026-04-16
**Theme:** Close the last valgrind docket, refresh the evidence pack for the v4.143.0 panel

## Changes

### Ge.1 — generics-init valgrind class (LOW -> CLOSED)

The prompt's suggested `fresh_tmp` / `MemsetZero` path was stale against
the current self-hosted tree:

- `mapanare/self/lower_state.mn::fresh_tmp` no longer owns the failing
  allocation path
- GitNexus CLI could not resolve current self-hosted `.mn` symbols by
  short name (`fresh_tmp`, `try_monomorphize_struct`,
  `try_monomorphize_enum`)
- Python-mirror context on `_fresh_tmp` / `_make_value` showed broad
  lowering fanout, so a wide allocator-behavior change would have been a
  higher-risk edit than the prompt implied

The actual closure came from the live residual path uncovered by the
targeted valgrind run on `32_generic_enum`:

1. **Internal-struct metadata parity fixes**
   `mapanare/self/emit_llvm.mn` and `mapanare/self/lower.mn` were still
   carrying stale layouts for `MIRModule`, `LowerState`,
   `MatchBuildResult`, `ModuleConst`, and several emitter-side support
   records. Those mismatches were corrected so the self-hosted emitter
   and lowerer agree on the data they move through internal structs.
2. **Moved-ownership fix in `try_monomorphize_enum`**
   `mapanare/self/lower.mn::try_monomorphize_enum` specialized enum
   metadata into `new_variants` / `new_variant_names`, moved those lists
   into the returned state, and then still let the local epilogue free
   them. Clearing the moved list headers closed the residual
   `compute_enum_inline_slots` invalid-read path.

Result: all five Ge.1 goldens moved from valgrind ERRORS to
WARNINGS_ONLY, and the full sweep is now `0 ERRORS`.

### Evidence refresh

v4.142.0 ships the full pre-panel evidence bundle:

- `VALGRIND_REPORT.md`
- `ASAN_REPORT.md`
- `MEASUREMENTS.md`
- `FIXEDPOINT_STATUS.md`
- `V5_READINESS.md`
- `.reviews/v4.143.0/PRE_PANEL_AUDIT.md`
- `benchmarks/FINAL_REPORT_v4.143.md`

Two prompt-era tooling mismatches were handled honestly:

- `scripts/summarize_sanitizer_logs.py` does not exist in this tree, so
  the release uses the TSVs emitted directly by the shipped valgrind/ASan
  harnesses.
- The benchmark runners need `--output` to emit real JSON; shell
  redirection only captures the human-readable console report. The final
  v4.142.0 benchmark artifacts were regenerated with `--output`.

### VERSION propagation sync before final verify

The first full non-bootstrap pytest run surfaced one deterministic
release-sync failure:

- `tests/runtime/test_user_agent.py::TestUserAgentMatchesVersion::test_user_agent_contains_current_version`

`VERSION` was already `4.142.0`, but `libmapanare_rt.a` still embedded
the previous runtime string. Rebuilding the runtime archive fixed it:

```bash
make build-rt
python3 -m pytest tests/runtime/test_user_agent.py -q -s --tb=no
```

The targeted test re-ran as **3 passed**, and the full non-bootstrap
suite then completed cleanly.

## Verification

| Check | Result |
|---|---|
| Targeted Ge.1 valgrind tests | `26/29/30/31/32_generic*` all `exit=0` |
| Full valgrind sweep | **0 CLEAN / 66 WARNINGS_ONLY / 0 ERRORS** |
| Full ASan sweep | **55 CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN** |
| Non-bootstrap pytest | **5160 passed / 0 failed / 115 skipped / 9 xfailed / 2 warnings** |
| Bootstrap pytest | **212 passed / 13 failed** |
| Native goldens through `mnc-stage1` | **54/66 passed** |
| Fixed point | **NEAR FIXED POINT** |
| Fixed-point delta | 4 diff lines out of 109,872 |
| `stage2.ll` md5 | `6d4963cdbe060ac1cee85eb58f2fa932` |
| `stage3.ll` md5 | `dddf64c3a77ed9236c82de517bc055d1` |
| `make lint` | clean |
| Cross-language benchmark geomean | **5.841 ms** |
| Async benchmark geomean | **5.817 ms** |

## Dockets closed

| Docket | Severity | Description |
|---|---|---|
| Ge.1 | LOW | Generics-init valgrind class (`26/29/30/31/32_generic*.mn`) |

## Net ledger state

**63 dockets opened since v4.99.0 -> 48 closed / 15 open.**

Open after v4.142.0: **0 CRITICAL · 0 HIGH · 8 MEDIUM · 7 LOW**.

## Residual notes

- Fixed-point is still near-fixed-point, not byte-identical; the only
  remaining diff is the known version-placeholder metadata boundary.
- The async harness currently emits Python comparison cells but not a
  live Go table in the v4.142.0 artifact set, so the benchmark report
  cites the measured Python comparison and leaves that tooling limitation
  explicit.
- `generate_report.py` still writes a one-line stub plus
  `docs/benchmarks/index.html`; `benchmarks/FINAL_REPORT_v4.143.md`
  was therefore written manually from the live benchmark artifacts so the
  panel has a readable summary.
