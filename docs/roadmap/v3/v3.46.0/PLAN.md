# Mapanare v3.46.0 — "Caimán" (GPU Foundation)

> Your 4090 does real math from Mapanare code.
> `gpu_available()` returns true. `gpu_tensor_add()` runs on CUDA.
> SPEC Section 23 stops lying.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v3.45.0 (package manager + polish)

---

## The Problem

`mapanare_gpu.c` is 1,938 lines of working CUDA Driver API code with
embedded PTX kernels for tensor add/sub/mul/div/matmul. It loads
`libcuda.so` via dlopen — no SDK dependency. The 4090 is visible in WSL.
None of this is linked into native binaries.

The same pattern as v3.41.0 (mapanare_io.c was written but not linked).
The fix is the same: compile it, link it, wire builtins, add golden tests.

Additionally, the v3.45.0 review identified 5 hard blockers for v4.0.0.
All are trivial fixes. Ship them here.

---

## Checklist

### 1. Build System — Link mapanare_gpu.c

- [ ] `scripts/build_stage1.py`: compile `mapanare_gpu.c` to `mapanare_gpu.o`
  - Use same `c_base_flags` as other runtime files
  - Add `-Werror` (fix for review item: apply `-Werror` to ALL C files)
  - Include `-lpthread -ldl` (already present from mapanare_runtime.c)
- [ ] Add `mapanare_gpu.o` to the linker step
- [ ] Verify with `nm mnc-stage1 | grep mapanare_gpu` — symbols present
- [ ] Update `.github/workflows/ci.yml`:
  - native job: compile `mapanare_gpu.c` with `-Wall -Wextra -Werror`
  - Skip GPU runtime tests on CI (no GPU in GitHub Actions)
  - Add `--skip-gpu` flag to native test runner
- [ ] ASan on mapanare_gpu.c (TSan less relevant — GPU init is single-threaded)

### 2. GPU Detection Builtins

- [ ] Register in `mapanare/types.py` BUILTIN_FUNCTIONS:
  - `gpu_available() -> Bool` — returns true if CUDA initialized
  - `gpu_device_name() -> String` — returns GPU name (e.g., "NVIDIA GeForce RTX 4090")
  - `gpu_device_memory() -> Int` — returns total VRAM in bytes
- [ ] Handle in `mapanare/emit_llvm_text.py`:
  - `gpu_available` → call `mapanare_gpu_init()`, then `mapanare_gpu_has_cuda()`
  - `gpu_device_name` → call `mapanare_gpu_get_ctx()`, extract device name
  - `gpu_device_memory` → call `mapanare_gpu_get_ctx()`, extract total memory
- [ ] Add to `_RUNTIME_FN_ATTRS`:
  - `mapanare_gpu_init`: `nounwind`
  - `mapanare_gpu_has_cuda`: `nounwind readonly`
  - `mapanare_gpu_get_ctx`: `nounwind readonly`
  - `mapanare_gpu_shutdown`: `nounwind`
- [ ] Register in `mapanare/self/semantic.mn` (self-hosted compiler)
- [ ] Register in `mapanare/self/emit_llvm.mn` (self-hosted emitter)

### 3. GPU Tensor Builtins

These builtins operate on List<Float> — the language already has lists.
The C runtime handles device allocation, upload, kernel launch, download.

- [ ] Register in `mapanare/types.py` BUILTIN_FUNCTIONS:
  - `gpu_tensor_add(a: List<Float>, b: List<Float>) -> List<Float>`
  - `gpu_tensor_sub(a: List<Float>, b: List<Float>) -> List<Float>`
  - `gpu_tensor_mul(a: List<Float>, b: List<Float>) -> List<Float>`
  - `gpu_tensor_div(a: List<Float>, b: List<Float>) -> List<Float>`
  - `gpu_tensor_matmul(a: List<Float>, b: List<Float>, m: Int, n: Int, k: Int) -> List<Float>`
- [ ] Add C wrapper functions in `mapanare_gpu.c` (or new `mapanare_gpu_builtins.c`):
  - `__mn_gpu_tensor_add(MnList a, MnList b) -> MnList`
    1. Extract float arrays from MnList
    2. `mapanare_gpu_buffer_alloc` + `upload` for a, b, result
    3. Load PTX_TENSOR_ADD kernel, launch, sync
    4. `download` result into new MnList
    5. Free GPU buffers
  - Same pattern for sub/mul/div
  - `__mn_gpu_tensor_matmul(MnList a, MnList b, i64 m, i64 n, i64 k) -> MnList`
- [ ] Handle in `mapanare/emit_llvm_text.py`:
  - `gpu_tensor_add` → `__mn_gpu_tensor_add`
  - Track returned list for drop glue (same as existing list builtins)
- [ ] Register in `mapanare/self/semantic.mn` + `emit_llvm.mn`
- [ ] CPU fallback: if `mapanare_gpu_has_cuda()` returns 0, do element-wise on CPU
  - The wrapper functions handle this internally

### 4. Golden Tests

- [ ] `tests/golden/39_gpu_detect.mn` — GPU detection + device info:
  ```mn
  fn main() {
      si gpu_available() {
          print("GPU: " + gpu_device_name())
          print("VRAM: " + str(gpu_device_memory()))
      } sino {
          print("No GPU available")
      }
  }
  ```
- [ ] `tests/golden/40_gpu_tensor.mn` — GPU tensor operations:
  ```mn
  fn main() {
      pon a: List<Float> = [1.0, 2.0, 3.0, 4.0]
      pon b: List<Float> = [5.0, 6.0, 7.0, 8.0]

      si gpu_available() {
          pon c = gpu_tensor_add(a, b)
          print(str(c))  // [6.0, 8.0, 10.0, 12.0]
      } sino {
          print("GPU not available, skipping")
      }
  }
  ```
- [ ] Both tests handle no-GPU gracefully (CI has no GPU)
- [ ] Both pass through Python bootstrap AND mnc-stage1

### 5. v3.45.0 Review — Hard Blockers

Fix all 5 hard blockers identified by the review panel:

- [ ] **SPEC Section 23 GPU disclaimer**: Rewrite section opening with honest
  status note now that GPU builtins actually work. Change from disclaimer
  to "basic GPU compute is functional via builtins; `@gpu` decorator syntax
  is planned for a future release."
- [ ] **`random_bytes` fallback**: Return `__mn_str_empty()` when BCrypt
  unavailable on Windows instead of `rand()` (mapanare_io.c:1226-1228)
- [ ] **`__mn_random_bytes_str` HMODULE leak**: Cache bcrypt.dll handle in
  static struct like `s_ssl`/`s_evp` (mapanare_io.c:1217-1225)
- [ ] **`tar.extractall()` filter**: Add `filter='data'` to `stdlib/pkg.py:734`
- [ ] **`test_examples.py` coverage**: Add `"cli", "network", "transpile"` to
  `_find_mn_files()` call at line 48

### 6. v3.45.0 Review — Should-Fix (Build Hygiene)

- [ ] Apply `-Werror` to ALL C files in `build_stage1.py` (not just core.c)
- [ ] Fix dead conditional in `build_stage1.py:76` (`-O2 if ... else -O2`)
- [ ] Include `obj_path` in cleanup loop at `build_stage1.py:162`
- [ ] Update `main.mn:31` version string to "mapanare 3.46.0"
- [ ] Update `emit_c.py:1` docstring version

### 7. Validation

- [ ] 40/40 golden tests pass (bootstrap + stage1)
- [ ] Native binary: `gpu_available()` returns `true` on WSL with 4090
- [ ] Native binary: `gpu_tensor_add` produces correct results on GPU
- [ ] `nm mnc-stage1 | grep mapanare_gpu` — symbols present
- [ ] `nm mnc-stage1 | grep __mn_gpu_tensor` — builtin wrappers present
- [ ] All 5 review hard blockers verified fixed
- [ ] CI passes (GPU tests skipped gracefully)

---

## Exit Criteria

```bash
# This program compiles and runs on WSL with a 4090:
cat > gpu_demo.mn << 'EOF'
fn main() {
    si gpu_available() {
        print("GPU: " + gpu_device_name())

        pon a: List<Float> = [1.0, 2.0, 3.0, 4.0]
        pon b: List<Float> = [5.0, 6.0, 7.0, 8.0]
        pon c = gpu_tensor_add(a, b)
        print("a + b = " + str(c))
    } sino {
        print("No GPU — running on CPU")
    }
}
EOF
mnc run gpu_demo.mn
# GPU: NVIDIA GeForce RTX 4090
# a + b = [6.0, 8.0, 10.0, 12.0]
```

```bash
# Same program on CI (no GPU) — runs without crashing:
mnc run gpu_demo.mn
# No GPU — running on CPU
```
