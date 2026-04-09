# Mapanare v3.47.0 — "Guacamaya" (GPU Examples + v4.0.0 Gate)

> Real GPU programs in `examples/`. SPEC Section 23 shows code that compiles.
> Every review item addressed. v4.0.0 is tagged after this.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v3.46.0 (GPU foundation)

---

## The Problem

After v3.46.0, GPU builtins work from Mapanare code. But there are no
real examples showing GPU usage, the SPEC still needs its Section 23
rewritten with working code, the self-hosted emitter has ABI mismatches
from the v3.45.0 review, and several multi-cycle carry-forward items
need resolution before v4.0.0 can be tagged.

---

## Checklist

### 1. GPU Examples

Create `examples/gpu/` with programs that compile and run:

- [ ] `vector_add.mn` — Add two large vectors on GPU, print first 10 results:
  ```mn
  fn main() {
      si gpu_available() {
          print("Running on " + gpu_device_name())

          // Build two 10,000-element vectors
          pon a: List<Float> = []
          pon b: List<Float> = []
          cada i en 0..10000 {
              a = push(a, float(i))
              b = push(b, float(i) * 2.0)
          }

          pon c = gpu_tensor_add(a, b)
          // Print first 10 results
          cada i en 0..10 {
              print(str(i) + ": " + str(c[i]))
          }
      } sino {
          print("No GPU available")
      }
  }
  ```
- [ ] `matmul_bench.mn` — Matrix multiply benchmark: CPU vs GPU timing:
  ```mn
  fn main() {
      si gpu_available() {
          pon n: Int = 256
          // Build n*n matrices
          pon a: List<Float> = []
          pon b: List<Float> = []
          cada i en 0..(n * n) {
              a = push(a, 1.0)
              b = push(b, float(i % n))
          }

          pon result = gpu_tensor_matmul(a, b, n, n, n)
          print("Matmul " + str(n) + "x" + str(n) + " done on GPU")
          print("result[0] = " + str(result[0]))
      }
  }
  ```
- [ ] `README.md` in `examples/gpu/` — requirements (NVIDIA GPU, WSL or Linux)
- [ ] Move existing `examples/experimental/gpu/` content:
  - Keep `matmul.mn`, `benchmark.mn`, `neural_net.mn` as `@gpu` decorator
    examples with a `// NOTE: @gpu decorator syntax planned — use gpu_*
    builtins for now` header
  - Or rewrite them to use the new gpu_* builtins

### 2. SPEC Section 23 — Rewrite with Working Code

- [ ] Replace the opening paragraph:
  - OLD: "Mapanare supports GPU-accelerated computation as a first-class feature"
  - NEW: "Mapanare provides GPU-accelerated tensor operations via built-in
    functions. GPU compute uses the CUDA Driver API loaded at runtime via
    `dlopen` — no SDK installation required. Programs degrade gracefully
    to CPU when no GPU is available."
- [ ] Replace the code example with one that actually compiles:
  ```mn
  fn main() {
      si gpu_available() {
          print("GPU: " + gpu_device_name())

          pon a: List<Float> = [1.0, 2.0, 3.0, 4.0]
          pon b: List<Float> = [5.0, 6.0, 7.0, 8.0]
          pon c = gpu_tensor_add(a, b)
          print(str(c))  // [6.0, 8.0, 10.0, 12.0]
      }
  }
  ```
- [ ] Add subsection: "23.1 Built-in GPU Functions" — document all gpu_* builtins
- [ ] Add subsection: "23.2 Supported Backends" — CUDA (via dlopen), Vulkan (planned)
- [ ] Add subsection: "23.3 Future: @gpu Decorator" with status note:
  > **Status:** The `@gpu` decorator syntax is specified but not yet connected
  > to codegen. The decorator, PTX embedding, and kernel dispatch infrastructure
  > exist in `emit_llvm_mir.py` and `mapanare_gpu.c`. Enabling this path
  > requires porting GPU dispatch to the text emitter. Use `gpu_*` builtins
  > for GPU compute in the current release.
- [ ] Update SPEC Section 1 "ML-ready" goal — add "(via GPU builtins)" caveat

### 3. Self-Hosted Emitter — ABI Fixes (Review Items)

Fix all 4 self-hosted emitter bugs from the v3.45.0 review:

- [ ] **`str(false)` i1 ABI**: Add `zext i1 to i64` before `__mn_str_from_bool`
  call at `emit_llvm.mn:2744` (same pattern as printf path at line 2676)
- [ ] **`file_exists` return type**: Change call from `i1` to `i64` + add
  `icmp ne i64 %r, 0` at `emit_llvm.mn:2325`
- [ ] **Regex phantom symbols**: Replace `__mn_regex_match`/`__mn_regex_replace`
  with compile+exec+free / compile+replace+free pattern matching the Python
  emitter at `emit_llvm.mn:2359-2365,399-400`
- [ ] **9 missing I/O builtins**: Add `file_remove`, `file_size`, `file_mtime`,
  `dir_create`, `dir_remove`, `file_rename`, `file_copy`, `realpath`,
  `tmpfile_path` declarations to `declare_all_runtime` in `emit_llvm.mn`

### 4. Self-Hosted Emitter — GPU Builtins

- [ ] Add GPU function declarations to `declare_all_runtime` in `emit_llvm.mn`:
  - `mapanare_gpu_init`, `mapanare_gpu_has_cuda`, `mapanare_gpu_get_ctx`
  - `__mn_gpu_tensor_add`, `__mn_gpu_tensor_sub`, `__mn_gpu_tensor_mul`
  - `__mn_gpu_tensor_div`, `__mn_gpu_tensor_matmul`
  - `mapanare_gpu_shutdown`
- [ ] Add GPU builtin dispatch in self-hosted emitter's `emit_builtin_call`
- [ ] Add GPU builtins to `semantic.mn` builtin registry

### 5. Review Carry-Forward — Should-Fix

Address remaining should-fix items from v3.45.0 review:

- [ ] **Thread-safe dlopen loaders**: Add `pthread_once` or atomic flag to
  `ssl_load_library`, `evp_load`, `pcre2_load` in `mapanare_io.c`
- [ ] **`__mn_http_get` response size limit**: Add 64 MB cap with `break`
- [ ] **`intern_ensure_table()` inside lock**: Move call inside `intern_lock()`
  in `mapanare_core.c:294` (4th review cycle — fix it this time)
- [ ] **`__mn_str_concat` early returns**: Add `if (a.len <= 0) return b;`
  and `if (b.len <= 0) return a;` in `mapanare_core.c:408`
- [ ] **`mnstr_to_cstr` deduplication**: Extract to shared `mapanare_internal.h`
- [ ] **`MnHandleTable` deduplication**: Same — shared internal header

### 6. Version Strings + Rebuild

- [ ] `VERSION` → `3.47.0`
- [ ] `main.mn:31` → `"mapanare 3.47.0"`
- [ ] Rebuild `main.ll` and `mnc-stage1` with updated version
- [ ] Re-bless golden refs: `python scripts/test_native.py --bless`
- [ ] Update `reference.md` version from 0.5.0 to 3.47.0
- [ ] Update `cookbook.md` example version from 3.20.0

### 7. CI Updates

- [ ] Add GPU example parse/emit tests (no GPU execution on CI)
- [ ] Add `examples/gpu/` to `test_examples.py` `_find_mn_files()`
- [ ] Verify all 7 CI jobs pass

### 8. Validation

- [ ] 40/40 golden tests pass (bootstrap + stage1)
- [ ] GPU examples compile and run on WSL with 4090
- [ ] GPU examples compile and run on CI without GPU (graceful skip)
- [ ] `culebra scan main.ll` — zero critical
- [ ] `culebra abi main.ll --header runtime/native/mapanare_core.h` — all match
- [ ] Self-hosted emitter: `regex_match` compiles without linker error
- [ ] Self-hosted emitter: `str(false)` produces "false" not "true"
- [ ] Self-hosted emitter: `file_exists` returns correct boolean
- [ ] dlopen loaders pass TSan
- [ ] All stale version strings updated

---

## Exit Criteria

```bash
# GPU vector add — 10,000 elements on the 4090:
mnc run examples/gpu/vector_add.mn
# Running on NVIDIA GeForce RTX 4090
# 0: 0.0
# 1: 3.0
# 2: 6.0
# ...

# GPU matmul — 256x256 on the 4090:
mnc run examples/gpu/matmul_bench.mn
# Matmul 256x256 done on GPU
# result[0] = 256.0

# Self-hosted regex works:
echo 'fn main() { print(str(regex_match("[0-9]+", "abc123"))) }' > /tmp/regex_test.mn
./mapanare/self/mnc-stage1 /tmp/regex_test.mn
# (compiles without linker error)

# SPEC Section 23 code example compiles:
# (extract example from docs/SPEC.md Section 23, save as gpu_spec.mn)
mnc run gpu_spec.mn
# (runs and produces output)
```

After this version passes:
```bash
# Tag v4.0.0
git tag -a v4.0.0 -m "Mapanare v4.0.0 — Production Release"
```
