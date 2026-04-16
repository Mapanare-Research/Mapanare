# v4.139.0 Session Report — SPEC + language close

**Date:** 2026-04-15
**Theme:** Coral's carry-forward empty — Gr.2 / Sem.1 / §0 / Co.1 / Dr.1

## Changes

### Gr.2 — Qualified type refs in type position (MEDIUM → CLOSED)

Grammar (`mapanare/mapanare.lark`) `named_type` and `generic_type`
rules now accept `NAME (DOT NAME)*`, enabling `device.DeviceKind` in
type position. Unblocks `stdlib/gpu/tensor.mn:90` and
`stdlib/gpu/kernel.mn:63`.

- **AST:** `NamedType` and `GenericType` gain `module_path: list[str]`
  field for the module segments preceding the type name.
- **Parser:** `named_type` and `generic_type` transformers extract
  qualified name segments from children tokens.
- **Semantic:** `_resolve_type_expr` checks `module_path` first;
  if non-empty, validates module exists in scope and resolves as
  struct-like type. Full cross-module type resolution deferred.
- **Self-hosted mirror:** `parser.mn::parse_type_expr` consumes
  DOT-separated NAME sequences. New `parse_generic_type_at` helper
  accepts a pre-parsed qualified name. `mnc_all.mn` mirrored.
- **Tests:** 3 new parser tests (`test_qualified_named_type`,
  `test_qualified_generic_type`, `test_deep_qualified_type`).
  New golden `66_qualified_type_ref.mn`.

### Sem.1 — Module-level `let mut` rejected (LOW → CLOSED)

Parser `start()` now raises `ParseError("E420: ...")` when a
mutable `LetBinding` appears at module scope. Fix-it message
suggests `const` or wrapping in `fn main()`.

- **SPEC §2.1:** `mut` keyword description updated to document
  block-scoping rule and E420 diagnostic.
- **Benchmarks:** 3 files wrapped in explicit `fn main()`:
  `02_concurrency.mn`, `04_matrix_mul.mn`, `05_agent_pipeline.mn`.
- **Tests:** `test_implicit_main_with_let` → `test_implicit_main_rejects_let_mut`
  (asserts E420). 5 diagnostic span tests wrapped in `fn main()`.

### SPEC §0 stale line (LOW → CLOSED)

Deleted "A legacy Python transpiler backend exists for reference and
bootstrapping only" from SPEC line 6. Replaced with accurate
description of all three backends (LLVM, C, WebAssembly). Version
header bumped to 4.139.0.

### Co.1 — Fixed-point precision (LOW → already CLOSED, content added)

SPEC Appendix B gains "Strict 3-stage fixed point (v4.134.0)"
section describing `stage2.ll == stage3.ll` with md5 provenance
and cross-link to `FIXEDPOINT_STATUS.md`.

### Dr.1 — Version string parameterized (LOW → CLOSED)

`emit_llvm.mn:3523` changed from `!"4.127.0"` to `!"__MN_VERSION__"`.
`scripts/build_stage1.py` now substitutes `__MN_VERSION__` across
ALL self-hosted `.mn` modules before compilation (with try/finally
restore). Removes the manual-bump drift class entirely.

Also fixed stale `const` reference in SPEC §2.1 bilingual keyword
section (was "parser-reserved with no semantics", now "compile-time
constant").

## Metrics

- **Pytest:** 5,127 passed / 0 failed / 118 skipped / 9 xfailed
  (+3 new parser tests, +1 golden pipeline, +2 MIR verifier)
- **Parser tests:** 194 passed (was 191, +3)
- **Semantic tests:** 303 passed (unchanged)
- **Goldens:** 54/66 through pipeline (was 53/65 + 1 new = 54/66)
- **VERSION:** 4.139.0

## Dockets closed

| Docket | Severity | Description |
|--------|----------|-------------|
| Gr.2 | MEDIUM | Qualified type refs in type position |
| Sem.1 | LOW | Module-level `let mut` scoping |
| Dr.1 | LOW | Self-hosted frozen version metadata |

SPEC §0 stale line and Co.1 precision were editorial, not dockets.
