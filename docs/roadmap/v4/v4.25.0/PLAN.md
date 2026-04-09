# Mapanare v4.25.0 — FFI End-to-End + Tensor Shape Checking

> Generated bindings actually call compiled libraries. Tensor shapes checked at compile time.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.24.0

---

## The Problem

v4.20.0's `mapanare bind` generates binding text but:
- Generated Python ctypes can't actually call a compiled .so (no shared lib build)
- Generated TypeScript .d.ts has no WASM loader
- Generated Go cgo has incorrect type conversions (string, float)
- No end-to-end test (compile .mn → .so → call from Python → verify result)

v4.18.0's tensor shape infrastructure exists but:
- No compile-time shape mismatch errors
- No shape propagation through expressions
- No shape-aware tensor operations

---

## Phase 1: Shared library compilation

- [ ] `mapanare bind --lang python source.mn` should:
  1. Compile source.mn to LLVM IR
  2. Compile IR to .o with `-fPIC`
  3. Link as shared library: `gcc -shared -o lib<name>.so <name>.o runtime.a`
  4. Generate ctypes wrapper alongside the .so
- [ ] Test: `python3 -c "from math_lib import add; print(add(3, 4))"`

## Phase 2: Fix type conversions in bindings

- [ ] Python: String ↔ ctypes (Mapanare strings are {ptr, len}, not C strings)
- [ ] Go: string ↔ C.char* conversion, float64 ↔ C.double
- [ ] TypeScript: WASM memory management for strings

## Phase 3: Tensor shape checking

- [ ] Parse `Tensor<Float, [3, 3]>` shape from type annotations
- [ ] Store shape in TypeInfo.tensor_shape during semantic analysis
- [ ] Add shape validation rules:
  - Add/Sub: shapes must match
  - MatMul `@`: [M,K] @ [K,N] → [M,N]
  - Mismatch → compile-time error with line numbers
- [ ] Add tests: `tests/semantic/test_tensor_shapes.py` (expanded)

## Phase 4: End-to-end binding test

- [ ] `tests/bind/test_python_binding.py`:
  - Compile math_lib.mn → libmath_lib.so
  - Import generated wrapper
  - Call add(3, 4) → assert 7
  - Call multiply(2.0, 3.0) → assert 6.0

---

## Exit Criteria

| Check | Required |
|-------|----------|
| `mapanare bind --lang python` produces callable .so + wrapper | YES |
| Python binding end-to-end test passes | YES |
| Tensor shape mismatch is compile-time error | YES |
| Shape propagation for add/sub/matmul | YES |
| 47/47+ golden | YES |
| 11/11 stage2 | YES |
