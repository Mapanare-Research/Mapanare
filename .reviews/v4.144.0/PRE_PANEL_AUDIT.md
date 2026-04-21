# Pre-Panel Audit — v4.144.0

> Lead's own fact-check. 0 material discrepancies is the target.

## Claims verified

### Cb.5-tests (Rattler / Cobra carry-forward)
- **Claim:** 34 dedicated unit tests added in `tests/llvm/test_enum_inline.py`.
- **Verified:** `pytest tests/llvm/test_enum_inline.py -v` → **34 passed**. Breakdown:
  - 9 eligibility tests (`TestEnumInlineEligibility`): Int×2, Int×1, Float, Bool, 3-field-ineligible, String-ineligible, List-ineligible, self-ref-ineligible, unit-only
  - 12 type predicate tests (`TestTypeFitsInlineSlot`): parametrized across i64/double/i1/i8/i16/i32/ptr/i64*/String/List/struct/void
  - 7 pack/unpack tests (`TestEnumInlinePackUnpack`): i64-passthrough, double-bitcast, i1/i8/i16/i32-zext-trunc, ptr-ptrtoint-inttoptr
  - 3 IR shape tests (`TestEnumInlineIRShape`): inline-type, no-malloc, extractvalue
  - 3 ABI parity tests (`TestEnumInlineABIParity`): Python emitter inline, self-hosted inline, type-width equivalence
- **File exists at:** `tests/llvm/test_enum_inline.py` (263 lines after black formatting)
- **Lint:** `ruff check` clean, `black --check` clean

### Cb.6 (Cobra carry-forward)
- **Claim:** Trailing-`*` typed-pointer-legacy guard added to `type_fits_inline_slot` in self-hosted emitter.
- **Verified:** `mapanare/self/emit_llvm.mn:753-756` — `if resolved.ends_with("*") { return false }` with Cb.6 comment.
- **Note:** The Python emitter at `emit_llvm_text.py:1129` has `if ft.endswith("*"): return True` (the opposite). This is intentional — the Python emitter accepts typed pointers for legacy compatibility; the self-hosted emitter rejects them because modern LLVM uses opaque `ptr`. Cb.6 explicitly addresses this asymmetry.

### Cb.7 (Cobra carry-forward)
- **Claim:** Clear-after-transfer pattern applied to monomorphization call sites.
- **Verified:**
  - `try_monomorphize_struct` at `lower.mn:1807-1810`: `fields = []`, `field_names = []`, `field_types = []` with Cb.7 comment — **NEW in v4.144.0**
  - `try_monomorphize_enum` at `lower.mn:1997-1998`: `new_variants = []`, `new_variant_names = []` — **existing from v4.142.0 Ge.1**
- **Note:** `register_struct` and `register_enum` were attempted but reverted — the reassignment triggers drop-glue on the transferred buffer during the assignment itself. Documented in BASELINE.md. This is a real language-design limitation (Own.1).
- **Regression check:** Fixed-point re-verified after changes: NEAR FIXED POINT, 4-line diff (110,127 lines). Goldens: 54/66 unchanged.

### Cb.9 → Cb.9a (Cobra carry-forward)
- **Claim:** Self-hosted `semantic.mn` lacks `module_path` concept; shipped as docstring (Cb.9a) per the execution prompt's fallback path.
- **Verified:** `mapanare/self/semantic.mn:520-530` — 10-line comment documenting the gap and tracking as Cb.9a for v5.x.
- **Note:** The self-hosted AST's `TypeExpr::Named(String)` carries a flattened dotted string (`"device.DeviceKind"`), not a module_path list. Full port requires an AST change.

### Cb.10 (Cobra carry-forward)
- **Claim:** `66_qualified_type_ref.mn` docstring rewritten to match actual test shape.
- **Verified:** `tests/golden/66_qualified_type_ref.mn:1-5` — now reads "struct construction and field access" with explicit note that it does NOT test qualified type refs.

### Benchmark refresh
- **Claim:** Cross-language benchmarks re-run with post-Bn.1 harness.
- **Verified:** `benchmarks/cross_language/v4.144.0-results.json` exists. 6 workloads × 6 languages. 10 runs per workload.
- **Key numbers (Mapanare median wall):**
  - fib_recursive: 20.657 ms (0.98× Rust — parity)
  - quicksort: 2.385 ms
  - enum_match: 1.619 ms
  - struct_alloc: 1.198 ms
  - prime_sieve: 3.406 ms
  - string_concat: 1.656 ms
- **Geomean vs C gcc: 4.57×, vs Rust: 5.83×**
- **Honest disclosure:** The v4.135.0 "Mapanare 1.12× of Rust" was an artifact of the Bn.1 harness tax. The corrected geomean is 5.83× — documented prominently in `FINAL_REPORT_v4.144.md`.

### Quality gates (post-change verification)
- **ruff check .**: 0 errors
- **black --check .**: 349 files unchanged
- **mypy mapanare/ runtime/**: 0 errors (52 files)
- **check_docs_drift**: clean (142 blocks / 4 files)
- **check_silent_skips**: clean
- **check_struct_registry**: clean (23/23/89)
- **Non-bootstrap pytest**: 5,187 passed / 0 failed (+27 from v4.143.0)
- **Goldens**: 54/66
- **Fixed-point**: NEAR FIXED POINT (4-line diff, 110,127 lines)

## Material discrepancies

**0.** All claims verified against live file:line references.

## Carry-forward state entering panel

| # | Item | Severity | Status |
|---|---|---|---|
| Own.1 | Self-hosted lowerer lacks compile-time move-semantics enforcement | LOW | OPEN (v5.x refactor) |
| Cb.9a | Self-hosted `semantic.mn` lacks `module_path` (documented gap) | LOW | OPEN (v5.x) |

All other v4.143.0 panel items (Cb.5-tests, Cb.6, Cb.7, Cb.10) are CLOSED in this release.
