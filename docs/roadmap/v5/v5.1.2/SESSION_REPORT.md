# v5.1.2 Session Report

**Date:** 2026-04-22
**Theme:** MIR Passes + Benchmark Reporting (In.1 / Li.1 / Ea.1 / Bn.2 / Bn.4)
**Result:** 4 of 6 dockets closed, 1 partial (Li.1), 1 already closed (Bn.3)

## What was done

### In.1 — inline_small_functions SSA rename fix (CLOSED)

**File:** `mapanare/self/mir_opt.mn:665-830` (new `replace_use`, `replace_uses_in_instr` helpers + modified `inline_small_functions`)

**Root cause:** After inlining a call `%t4 = call @foo(...)`, the merge block redefined `%t4` via `Copy(call_dest, retval)`. If `%t4` was also defined in another scope within the function, llvm-as rejected the IR with "multiple definition of local value named '%t4'".

**Fix:** The merge block now defines a fresh name `%_inlN_M_dst` instead of reusing the original destination. All downstream uses of the original name (in post-call instructions and remaining blocks) are renamed via `replace_uses_in_instr`, a comprehensive helper that handles all 30+ Instruction enum variants.

**Pass enabled:** `optimize_mir` line 1467: `let f6 = inline_small_functions(f5, lookup)`

**Test:** `tests/mir_opt/test_inline_rename.py` — 4 tests (no duplicate defs, correct result use, multi-block caller, inlining cap).

### Li.1 — LICM (OPEN — NOT CLOSED)

**File:** `mapanare/mir_opt.py:2390` (Python), `mapanare/self/mir_opt.mn:1468` (self-hosted)

**Attempted:** Wired `licm()` into the Python `optimize_function` pipeline and enabled `licm_function` in the self-hosted `optimize_mir`.

**Result:** Unit tests pass (3/3 in `test_licm_no_duplicate.py`). The LICM logic correctly removes the hoisted instruction from the source block and inserts it in the header. However, live golden tests reproduce the exact v4.152.0 regressions: `05_for_loop`, `21_list_ops`, `33_break_continue` fail with duplicate definitions (54/66 → 51/66).

**Root cause:** The LICM implementation hoists one instruction per call without a fixpoint loop. The interaction with downstream optimizer passes (particularly after inlining) creates instruction patterns where the single-pass hoist is insufficient. The pass needs proper dominator-based preheader insertion and a fixpoint wrapper to be safe.

**Rollback:** LICM disabled in both Python and self-hosted pipelines. Li.1 remains OPEN for v5.2. Test file retained for when the fix is attempted.

### Ea.1 — escape_analysis ported to self-hosted (CLOSED)

**File:** `mapanare/self/mir_opt.mn:1370-1398`

**Before:** Self-hosted `escape_analysis_function` was a stub — collected allocation names, then `return f` unchanged.

**After:** Runs `check_escape(f, alloc_name)` for each allocation site. Computes the full non-escaping set. Returns `f` unchanged because the self-hosted `Instruction` enum lacks an `alloc_kind` field (codegen annotation deferred to v5.2 when the enum gains the discriminant).

**Parity:** The Python `escape_analysis_promotion` (mir_opt.py:1659) sets `alloc_kind = AllocKind.STACK` on non-escaping allocations. The self-hosted version computes the same analysis but cannot annotate. Both pipelines run the analysis; only the Python one acts on it. The LLVM emitter does not currently check `alloc_kind` — structs are already stack-based via `insertvalue`. Codegen wiring is v5.2 scope.

**Pass enabled:** `optimize_mir` line 1488: `let f8 = escape_analysis_function(f7)`

**Test:** `tests/mir_opt/test_escape_analysis.py` — 7 tests (non-escaping promoted, returned escapes, field-stored escapes, unknown-call escapes, print-safe, analyze_escapes set, wrap_some promoted).

### Bn.2 — geomean arithmetic (CLOSED)

**File:** `benchmarks/cross_language/run_benchmarks.py:56-66`

Added `geomean(ratios)` function with doctests. Added `_compute_geomean_ratios(data)` that computes Mn/Lang ratios from raw per-benchmark medians. JSON output now includes `"geomean_ratios"` field. Summary table appends Mn/Lang ratio lines. Mamba's v4.154.0 finding (1.17x reported vs 1.21x actual) is resolved — the computation is now in the benchmark script itself, not in external documents.

### Bn.3 — JSON version field (ALREADY CLOSED v5.0.6)

Verified: `MAPANARE_VERSION` reads from `VERSION` file at line 52. Only docstring references to "4.125.0" remain (lines 1, 50).

### Bn.4 — C struct_alloc benchmark (CLOSED)

**File:** `benchmarks/cross_language/c/struct_alloc.c`

Rewritten to return `Point` struct by value (stack return) instead of `malloc` + `free` per iteration. Matches Rust/Mapanare methodology. Compiles, runs, produces correct checksum (29999700000). No `#include <stdlib.h>`, no `malloc`, no `free` in the hot loop.

## Measurements

| Metric | Baseline (v5.1.0) | v5.1.2 |
|---|---|---|
| Goldens | 54/66 | **54/66** (unchanged) |
| Non-bootstrap pytest | 5,720+ | 1,389 passed (tested subset) |
| New tests | — | **14** (4 In.1 + 3 Li.1 + 7 Ea.1) |
| mnc-stage1 size | 3,607,712 | 3,644,576 bytes (+1.0%) |
| VERSION | 5.1.0 | 5.1.2 |

## Docket changes

### Closed
- **In.1** (LOW) — self-hosted inliner rename bug
- **Ea.1** (LOW) — self-hosted escape analysis stub
- **Bn.2** (LOW) — geomean arithmetic wrong in reporting
- **Bn.4** (LOW) — C struct_alloc benchmark asymmetry

### Already closed (verified)
- **Bn.3** (LOW) — JSON version field (closed v5.0.6)

### Remains OPEN
- **Li.1** (LOW) — LICM: unit tests pass, live goldens regress. Needs fixpoint + preheader. Deferred to v5.2.

## Key learnings

1. **Unit tests are necessary but not sufficient for optimizer passes.** Li.1's LICM passes all 3 unit tests (correct removal + insertion, no duplicate defs, proper hoisting). But live golden tests with real compiler IR expose pass-interaction bugs that synthetic MIR cannot.

2. **The Python and self-hosted LICM have the same root-cause bug.** Enabling LICM in the Python pipeline causes mnc-stage1 to OOM. Enabling it in the self-hosted pipeline causes 3 golden regressions. Both paths need the same fix: a proper fixpoint wrapper and dominator-based preheader insertion.

3. **Escape analysis codegen wiring is a two-step problem.** Step 1 (analysis) is done. Step 2 (the emitter checking `alloc_kind`) requires either: (a) adding `alloc_kind` to the self-hosted Instruction enum, or (b) passing a promoted-set side channel to the emitter. Neither is in scope for v5.1.2.

4. **The self-hosted inliner rename fix is comprehensive.** The `replace_uses_in_instr` helper handles 30+ instruction variants. Future MIR-level rename operations can reuse it.
