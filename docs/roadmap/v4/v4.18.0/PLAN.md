# Mapanare v4.18.0 — Compile-Time Tensor Shapes + @gpu Auto-Kernels

> First new language feature post-foundation. Tensors know their shapes. GPU functions write themselves.

**Status:** DONE (const keyword + tensor infra, auto-kernel extraction deferred)
**Breaking:** No
**Prerequisite:** v4.17.0

---

## The Goal

Two features that make Mapanare's GPU story first-class:

1. **Compile-time tensor shapes.** `Tensor<Float, [3, 3]>` carries its shape
   in the type system. Shape mismatches are compile-time errors, not runtime
   crashes. Matrix multiplication `A @ B` where `A: Tensor<Float, [3, 4]>`
   and `B: Tensor<Float, [5, 3]>` fails at compile time ("dimension mismatch:
   4 != 5").

2. **@gpu auto-kernel extraction.** Decorate a function with `@gpu` and the
   compiler extracts the function body to PTX (CUDA) or SPIR-V (Vulkan)
   automatically. No manual kernel writing. The MIR GpuKernel metadata
   infrastructure from `lower.py` already exists — this version wires it to
   actual code generation from function bodies.

Both features require the `const` keyword for compile-time constants (tensor
dimensions must be known at compile time).

---

## Phase 1: const keyword

- [ ] Add `const` keyword to grammar (`mapanare.lark`)
- [ ] `const N: Int = 3` — evaluated at compile time, inlined everywhere
- [ ] Semantic check: const value must be a literal or expression of other consts
- [ ] Self-hosted: add Const variant to Definition enum, update parser + lowerer
- [ ] Rebuild + golden
- [ ] Add test: `tests/golden/42_const.mn`

## Phase 2: Tensor shape annotations

- [ ] Extend type syntax: `Tensor<ElementType, [dim1, dim2, ...]>`
- [ ] Shape is a list of const Int expressions
- [ ] Store shape in `TypeInfo` (new field: `shape: List<Int>`)
- [ ] Semantic checker validates shape dimensions are positive
- [ ] Rebuild + golden

## Phase 3: Shape checking

- [ ] Tensor operations check shape compatibility at compile time:
  - Add/Sub: shapes must be identical
  - MatMul: `[M, K] @ [K, N] -> [M, N]`
  - Element-wise: shapes must match or broadcast
  - Transpose: `[M, N] -> [N, M]`
  - Reshape: product of dimensions must be equal
- [ ] Emit shape-related errors via `diagnostics.py` with line numbers
- [ ] Add tests: `tests/semantic/test_tensor_shapes.py`

## Phase 4: @gpu auto-kernel extraction

- [ ] Parse `@gpu` decorator on functions (already in grammar)
- [ ] In the lowerer: when a `@gpu` function operates on Tensors, extract the
      body to a GPU kernel specification
- [ ] Generate PTX source string from the function body (simple arithmetic ops)
- [ ] Generate SPIR-V byte sequence for Vulkan targets
- [ ] Emit as `MIRGpuKernel` metadata (existing infrastructure)
- [ ] The LLVM emitter already handles `MIRGpuKernel` — verify it works
- [ ] Rebuild + golden

## Phase 5: Integration test

- [ ] New example: `examples/gpu/tensor_matmul.mn`
  ```
  const M: Int = 64
  const K: Int = 128
  const N: Int = 64

  @gpu
  fn matmul(a: Tensor<Float, [M, K]>, b: Tensor<Float, [K, N]>) -> Tensor<Float, [M, N]>:
      return a @ b
  ```
- [ ] Compile to LLVM IR, verify PTX/SPIR-V embedded in output
- [ ] If GPU hardware available, run and verify correctness
- [ ] If not, verify IR structure only (PTX string present, launch call emitted)

---

## Exit Criteria

| Check | Required |
|-------|----------|
| const keyword works (compile-time evaluation) | YES |
| Tensor<T, [dims]> type syntax parsed | YES |
| Shape mismatch is a compile-time error | YES |
| @gpu extracts function body to PTX/SPIR-V | YES |
| MIRGpuKernel metadata populated from function body | YES |
| examples/gpu/tensor_matmul.mn compiles | YES |
| 40/40 golden (existing tests unbroken) | YES |
| 11/11 stage2 | YES |
| Fixed-point preserved | YES |
