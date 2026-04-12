# Culebra Baseline Delta — v4.46.0 vs v4.41.0

**Date:** 2026-04-12

## Status

Culebra binary not available in WSL environment. Delta assessed via code
inspection of changes between v4.41.0 and v4.45.0.

## Arc 3 Changes to IR-Generating Code

| File | Changes | Impact |
|------|---------|--------|
| `emit_llvm_text.py` | +55 runtime fn declarations (tensor), `_do_tensor_init`, `_emit_drop_glue_tensors`, tensor binop/reduction/slice handlers | New IR patterns for tensor ops |
| `lower.py` | `_lower_tensor_get/set/slice/binop` + `TensorInit` handling | New MIR → IR lowering paths |
| `semantic.py` | `_check_tensor_literal` + broadcasting rules + IndexItem handling | No IR impact (semantic only) |
| `types.py` | `broadcast_shape()`, `broadcast_incompatible_dim()`, `tensor_shape` | No IR impact (type system) |
| `ast_nodes.py` | `TensorLiteral`, `IndexItem`, `IndexExpr.indices` migration | No IR impact (AST only) |

## Expected Finding Changes

| Category | Expected |
|----------|----------|
| New runtime declarations | +55 `__mn_tensor_*` function declares (noalias, nounwind, willreturn attrs) |
| New variadic calls | Tensor N-D get/set use `call ... (ptr, i64, ...)` variadic ABI |
| New drop glue | `_emit_drop_glue_tensors` frees tensor vars at function exit |
| Broadcast dispatch | Element-wise ops route to `__mn_tensor_*_broadcast_*` calls |

## Risk Assessment

**LOW.** Arc 3 changes are additive — new runtime function declarations and call sites.
No existing IR patterns were modified. The self-hosted emitter (`emit_llvm.mn`) has
tensor stubs but does not generate tensor IR.
