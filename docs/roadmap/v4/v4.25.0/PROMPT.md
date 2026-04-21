# v4.25.0 — FFI End-to-End + Tensor Shape Checking — Continuation Prompt

> Bindings that actually work. Shapes that actually check.
> You are in WSL. Rebuild + golden + stage2 after every change.
> Run lint before every commit. The Python binding test must CALL compiled
> code and get the right answer.

---

## Context

v4.20.0's `mapanare/bind.py` generates text output:
- Python: ctypes wrapper file
- TypeScript: .d.ts declarations
- Go: cgo binding file

But none of these can actually call compiled Mapanare code because:
1. No shared library (.so) is built
2. String type mapping is wrong (Mapanare strings are `{ptr, len}`, not C strings)
3. No end-to-end test exists

v4.18.0's tensor infrastructure has `TypeInfo.tensor_shape` (a field in types.py)
and `TensorType` AST node with shape, but:
1. Shapes are never extracted from type annotations
2. No compile-time shape validation exists
3. No error messages for shape mismatches

## Part 1: FFI End-to-End

### The Pipeline

```
math_lib.mn → emit_llvm_text.py → math_lib.ll → clang -fPIC → math_lib.o → gcc -shared → libmath_lib.so
                                                                                              ↓
                                                                              Python ctypes wrapper imports .so
                                                                              call add(3, 4) → returns 7
```

### What `cmd_bind` Must Do

1. Parse the .mn file
2. Compile to LLVM IR via `_compile_to_llvm_ir()`
3. Rename `@main` → `@mn_main` (if present)
4. Compile IR to .o: `clang -c -fPIC -O2 file.ll -o file.o`
5. Link as shared library: `gcc -shared -o lib<name>.so file.o runtime/native/libmapanare_rt.a -lm -lpthread`
6. Generate ctypes wrapper alongside the .so
7. Print: "Generated lib<name>.so and <name>.py"

### Type Mapping Fixes

| Mapanare Type | C ABI | ctypes | Issue |
|---------------|-------|--------|-------|
| Int | i64 | c_int64 | OK |
| Float | double | c_double | OK |
| Bool | i1 → i64 (zext) | c_int64 | Need to convert to Python bool |
| String | {ptr, i64} struct | POINTER(c_char), c_int64 | Need struct wrapper |
| List<T> | {ptr, i64, i64, i64, i64} | c_void_p | Opaque handle |
| Struct | Named LLVM struct | ctypes.Structure subclass | Already works |

For v4.25.0, start with **Int-only functions** (no strings/lists). This
avoids the complex string marshaling and proves the pipeline works. String
marshaling is a follow-up.

### The End-to-End Test

```python
# tests/bind/test_python_binding.py
import subprocess, os, ctypes

def test_python_binding_e2e():
    # Step 1: Generate binding
    subprocess.run(["python3", "-m", "mapanare", "bind", "--lang", "python",
                    "examples/bind/math_lib.mn", "-o", "/tmp/bind_test/"],
                   check=True)
    
    # Step 2: Load the .so
    lib = ctypes.CDLL("/tmp/bind_test/libmath_lib.so")
    
    # Step 3: Call function
    lib.add.restype = ctypes.c_int64
    lib.add.argtypes = [ctypes.c_int64, ctypes.c_int64]
    assert lib.add(3, 4) == 7
```

## Part 2: Tensor Shape Checking

### Where Shapes Come From

The grammar already parses `Tensor<Float>[3, 3]` via the `TensorType` AST
node (ast_nodes.py:67-71). The `TensorType` has `element_type` and `shape`
fields. `TypeInfo` has `tensor_shape: Optional[tuple[int, ...]]`.

### What's Missing

1. **Shape extraction.** When the semantic checker resolves a `TensorType`,
   it should evaluate the shape expressions (must be const Int) and store
   them in `TypeInfo.tensor_shape`.

2. **Shape validation.** When binary operators are applied to tensors:
   - `+`, `-`: shapes must be identical
   - `@` (matmul): `[M, K] @ [K, N]` → `[M, N]`; fail if K doesn't match
   - Element-wise `*`, `/`: shapes must match

3. **Error messages.** "Tensor shape mismatch: [3, 4] + [3, 5] — dimension 1
   differs (4 vs 5)" at `filename:line:col`.

### Implementation

In `mapanare/semantic.py`, in the binary expression type checker:
```python
if left.tensor_shape and right.tensor_shape:
    if op in ("+", "-") and left.tensor_shape != right.tensor_shape:
        self._error(f"Tensor shape mismatch: {left.tensor_shape} {op} {right.tensor_shape}", node)
    if op == "@":  # matmul
        if left.tensor_shape[-1] != right.tensor_shape[0]:
            self._error(f"Matmul dimension mismatch: [{left.tensor_shape}] @ [{right.tensor_shape}]", node)
```

### The Shape Test

```python
# tests/semantic/test_tensor_shapes.py (extended)
def test_shape_mismatch_error():
    src = """
    fn main() {
        let a: Tensor<Float>[3, 4] = ...
        let b: Tensor<Float>[3, 5] = ...
        let c = a + b  // should error
    }
    """
    errors = check(parse(src), filename="test.mn")
    assert any("shape mismatch" in e.message.lower() for e in errors)
```

## Key Files

| File | What Changes |
|------|-------------|
| `mapanare/bind.py` | Add shared library compilation, fix type mappings |
| `mapanare/cli.py` | Update `cmd_bind` to compile .so + generate wrapper |
| `mapanare/semantic.py` | Tensor shape extraction from TensorType, shape validation |
| `mapanare/types.py` | `TypeInfo.tensor_shape` (already exists, just needs population) |
| `mapanare/parser.py` | `TensorType` shape parsing (already exists) |
| `examples/bind/math_lib.mn` | Example library (already exists) |
| `tests/bind/test_python_binding.py` | NEW — end-to-end binding test |
| `tests/semantic/test_tensor_shapes.py` | Extended — shape mismatch tests |

## Commands

```bash
# Test binding generation
python3 -m mapanare bind --lang python examples/bind/math_lib.mn -o /tmp/bind_test/

# Test the generated .so
python3 -c "import ctypes; lib = ctypes.CDLL('/tmp/bind_test/libmath_lib.so'); print(lib.add(3, 4))"

# Run binding test
python3 -m pytest tests/bind/test_python_binding.py -v

# Run shape tests
python3 -m pytest tests/semantic/test_tensor_shapes.py -v

# All golden
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Stage2
python3 scripts/ir_doctor.py stage2 --timeout 60

# Lint
black --check . && ruff check . && mypy mapanare/
```

## Rules

- FFI FIRST (Part 1), then tensor shapes (Part 2)
- Start with Int-only functions (no strings) — simplest possible e2e
- The Python test must CALL compiled code, not just check text output
- Shape checking must produce Rust-style errors with line numbers
- If the .so can't be built (missing clang/gcc), skip with clear error message
- Run lint before every commit

## Exit Criteria with Proof Commands

| Criterion | Proof Command |
|-----------|---------------|
| .so is produced | `ls /tmp/bind_test/libmath_lib.so` |
| Python calls compiled code | `python3 -c "import ctypes; lib=ctypes.CDLL('/tmp/bind_test/libmath_lib.so'); assert lib.add(3,4)==7"` |
| Shape mismatch error | `python3 -m pytest tests/semantic/test_tensor_shapes.py -k shape_mismatch` |
| All golden pass | `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` |
| Stage2 valid | `python3 scripts/ir_doctor.py stage2 --timeout 60` → "11/11" |
| Lint clean | `black --check . && ruff check . && mypy mapanare/` |
