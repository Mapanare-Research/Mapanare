# v4.25.0 Session Report — 2026-04-09

## Completed

- [x] FFI: `cmd_bind` now compiles .mn → .ll → .o → .so alongside wrapper generation
- [x] FFI: Functions exported with external visibility (removed `define internal`)
- [x] FFI: `@main` renamed to `@mn_main` via regex (handles all signatures)
- [x] FFI: Graceful fallback when runtime archive not -fPIC compatible
- [x] FFI E2E proof: `python3 -c "add(3, 4) == 7"` works via ctypes → compiled .so
- [x] Tensor shape mismatch test added: `test_shape_mismatch_add`
- [x] Tensor matmul shape validation test added: `test_matmul_shape_valid`

## Measurements

- Golden tests: 46/46
- Stage2 modules: 11/11 valid
- Tensor shape tests: 4/4 passed
- FFI E2E: add(3, 4) = 7 via Python ctypes → compiled .so

## FFI Pipeline

```
math_lib.mn → _compile_to_llvm_ir() → math_lib.ll
    → clang -c -fPIC -O2 → math_lib.o
    → gcc -shared → libmath_lib.so
    → Python ctypes wrapper: math_lib.py
```

Key fixes:
- `define internal` → `define` for all functions (FFI requires visibility)
- `@main` → `@mn_main` via regex to avoid C main conflict
- Runtime archive linking: try with runtime first, fall back to without
  (runtime not -fPIC on this platform, but pure Int functions work without it)

## Tensor Shape Checking (already existed)

The semantic checker already had shape validation from v4.18.0:
- Element-wise ops: shapes must match → error if different
- Matmul: inner dimensions must match → error if incompatible
- Shape propagation through type inference

Added 2 tests to verify and document this behavior.

## Verification Results

```
Golden: 46/46
Stage2: 11/11 modules valid
Lint: black clean, ruff clean, mypy clean
FFI: python3 -c "lib.add(3, 4) == 7" → PASS
Tensor: 4/4 shape tests passed
```
