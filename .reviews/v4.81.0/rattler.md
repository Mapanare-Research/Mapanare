# Rattler — LLVM Review (Arc 10)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

The integration test harness (v4.77.0) is the most consequential infrastructure addition since the self-hosted compiler. For the first time, emitted IR goes through `llvm-as -> opt -O2 -> llc -> clang link -> execute` and the output is checked. 47 of 59 golden tests survive the full pipeline at -O2 — a strong result given that no optimization-specific IR hardening was done in this arc.

The drop-glue escape analysis fix (item 49) is correct. The blanket early return was a v4.18.0-era hack that skipped all cleanup for struct-return functions. The per-kind helpers already had the ret_ptr_fields comparison logic; the early return was redundant. Removing it is safe because `_emit_drop_glue_collect_ret_ptrs` correctly extracts every escaping pointer. Verified by the `TestStructReturnDropGlue` tests.

The 5 xfailed tests (async 55-57, try operator 47, match guards+or 51) are legitimate IR gaps in the emit-llvm backend, not optimizer-induced failures. The harness correctly distinguishes which stage each failure occurs at.

## Specific findings

1. **PASS**: -O2 does not miscompile any of the 47 passing tests. IR quality is sufficient for real optimization.
2. **PASS**: `-relocation-model=pic` correctly handled for PIE linking on Ubuntu.
3. **NOTE**: The pipeline uses sequential stages (no parallel compilation). For 59 tests at ~0.7s each, total time is ~42s. Acceptable but could benefit from pytest-xdist.

## Score justification

9/10 — the integration harness is real infrastructure with real teeth. The 5 xfails are properly tracked, not silenced. One point deducted because the harness does not yet test with mnc-stage1 (only the Python bootstrap).
