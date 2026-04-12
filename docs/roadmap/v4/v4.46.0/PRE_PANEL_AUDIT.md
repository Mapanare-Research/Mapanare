# v4.46.0 Pre-Panel Audit

**Date:** 2026-04-12
**Auditor:** Lead (self-check before panel)

Fact-checks every v4.42.0-v4.45.0 SESSION_REPORT claim against file:line evidence.

## Results: 18/19 claims PASS, 1 FAIL

### v4.42.0 — Tensor Literals + Runtime Wiring (8 claims)

| # | Claim | File:Line | Verdict |
|---|-------|-----------|---------|
| 1 | `tensor_literal` grammar rule | `mapanare.lark:356` | PASS |
| 2 | `TensorLiteral` AST dataclass | `ast_nodes.py:301` | PASS |
| 3 | `_check_tensor_literal` semantic | `semantic.py:1309` | PASS |
| 4 | `_do_tensor_init` LLVM emitter | `emit_llvm_text.py:3349` | PASS |
| 5 | `__mn_tensor_alloc` C runtime | `mapanare_gpu_builtins.c:278` | PASS |
| 6 | `_emit_drop_glue_tensors` | `emit_llvm_text.py:1524` | PASS |
| 7 | P1 closure: `__mn_list_get` attrs fixed | `emit_llvm_text.py:255` — only `nounwind` | PASS |
| 8 | P4 closure: SPEC §5.6 wording corrected | `SPEC.md:964` — "name-set equality" | PASS |

### v4.43.0 — Multi-Dimensional Indexing (4 claims)

| # | Claim | File:Line | Verdict |
|---|-------|-----------|---------|
| 9 | `IndexExpr.indices` is `list` field | `ast_nodes.py:227` | PASS |
| 10 | Variadic `__mn_tensor_get_f64_nd` declared | `emit_llvm_text.py:347` | PASS |
| 11 | `_lower_tensor_get` + `_lower_tensor_set` | `lower.py:2453, 2474` | PASS |
| 12 | C variadic `__mn_tensor_get_f64_nd` | `mapanare_gpu_builtins.c:378` | PASS |

### v4.44.0 — Broadcasting (3 claims)

| # | Claim | File:Line | Verdict |
|---|-------|-----------|---------|
| 13 | `broadcast_shape()` function | `types.py:443` | PASS |
| 14 | 16 broadcast runtime function decls | `emit_llvm_text.py:353-368` | PASS |
| 15 | `_lower_tensor_binop` | `lower.py:2536` | PASS |

### v4.45.0 — Reductions + Slicing (4 claims)

| # | Claim | File:Line | Verdict |
|---|-------|-----------|---------|
| 16 | `IndexItem` AST node with `kind` | `ast_nodes.py:205-215` | PASS |
| 17 | "12 reduction runtime functions" | `mapanare_gpu_builtins.c:615-716` | **FAIL** |
| 18 | `__mn_tensor_slice` C function | `mapanare_gpu_builtins.c:721` | PASS |
| 19 | `_lower_tensor_slice` | `lower.py:2491` | PASS |

## Claim 17 Detail (FAIL)

The v4.45.0 SESSION_REPORT claims "12 runtime C functions (sum/mean/max/min/argmax/argmin x f64/i64)." Actual count is **11**:

- Float64 (6): sum, mean, max, min, argmax, argmin
- Int64 (5): sum, max, min, argmax, argmin
- **Missing: `__mn_tensor_mean_i64`** — integer mean was omitted (arguably correct — mean of integers is a float)

**Severity:** LOW. The omission is arguably intentional (integer mean → float result doesn't fit the `i64` return type), but the claim overstates the count. The panel should note this as an honest accounting error, not a missing feature.

## Carry-Forward Audit Summary

See `LEDGER_AUDIT.md` for full details. Key findings:
- 3 items marked OPEN are actually CLOSED (A7, A9, #50)
- 1 item needs dual-closure update (A8)
- 1 item has stale count (A10: 442 → 589)
- 5 items are accurately tracked as OPEN (#49, P2, P3, P5, P6)
