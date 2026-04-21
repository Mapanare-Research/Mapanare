# Culebra Summary — v4.46.0

**Date:** 2026-04-12
**Tool:** Culebra v2.4.0 (not available in WSL test environment)

## Status

Culebra binary not available in this WSL environment. Summary generated from
code inspection and IR validation instead.

## IR Validation

All 5 tensor golden tests compile through Python bootstrap (`emit-llvm`) and
validate with `llvm-as`:

- `49_tensor_literal.mn` → PASS
- `50_tensor_indexing.mn` → PASS
- `51_tensor_broadcast.mn` → PASS
- `52_tensor_slicing.mn` → PASS
- `53_linear_regression.mn` → PASS

## Self-Hosted IR (main.ll)

- **Lines:** 188,968
- **Size:** 17.6 MB
- **Tensor-related changes:** Minimal (runtime function declarations + emitter stubs only — self-hosted emitter delegates tensor init to null ptr)

## Known Suppressions

Per `PROMPT.md` Culebra discipline section:
- `break-inside-nested-control` — 43 findings, all intentional return-in-for patterns
- `missing-typedef` — forward-declared runtime structs in C headers
- `c-memcpy-size-mismatch` at `runtime/native/mapanare_core.c:1470` — double/uint64_t bitcast idiom
