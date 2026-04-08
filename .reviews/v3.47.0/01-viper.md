# Viper -- Rust / Memory Safety Review of Mapanare v3.47.0

**Reviewer:** Viper
**Personality:** Ruthless Rust purist who thinks every non-Rust language is a toy. Even more aggressive for the PRODUCTION RELEASE gate review.
**Previous Version Reviewed:** v3.45.0 (score: 9.3/10, PASS WITH NOTES)
**Verdict:** PASS WITH NOTES
**Confidence:** 9/10
**Score:** 9.5 / 10
**Files Reviewed:**

- `runtime/native/mapanare_gpu.c` (1,951 lines -- **NEW**, full read)
- `runtime/native/mapanare_gpu.h` (737 lines -- **NEW**, full read)
- `runtime/native/mapanare_gpu_builtins.c` (193 lines -- **NEW**, full read)
- `runtime/native/mapanare_internal.h` (63 lines -- **NEW**, full read)
- `runtime/native/mapanare_io.c` (diff from v3.45.0 -- focused read of all changed hunks)
- `runtime/native/mapanare_core.c` (diff from v3.45.0 -- `str_concat`, `str_intern`, `str_from_bool`)
- `runtime/native/mapanare_runtime.c` (partial -- tensor alloc/free/shape_eq)
- `mapanare/emit_llvm_text.py` (diff from v3.45.0 -- GPU builtins, bool ABI fixes)
- `mapanare/self/emit_llvm.mn` (diff from v3.45.0 -- 200 lines of new builtin declarations + handlers)
- `mapanare/self/semantic.mn` (partial)
- `mapanare/types.py` (diff -- 9 new GPU builtin type entries)
- `scripts/build_stage1.py` (diff -- GPU compilation, `-Werror` for all C files)
- `examples/gpu/vector_add.mn`, `examples/gpu/matmul_bench.mn` (full read)
- `docs/SPEC.md` (Section 3.10, Section 23 vicinity)
- `CHANGELOG.md` (v3.46.0--v3.47.0 entries)

---

## Executive Summary

Two releases since my last review. The v3.45.0 review was the first score DECREASE in the project's history, driven by zero resolution of carry-forward items and new attack surface from network-facing C code. I issued PASS WITH NOTES with three must-fix items (crypto `rand()` fallback, self-hosted regex phantom symbols, self-hosted `file_exists` ABI mismatch) and three should-fix items (HTTP response cap, bcrypt handle leak, dlopen thread safety).

v3.46.0 and v3.47.0 fixed ALL SIX of those items. Every single one. Let me repeat that, because I have been doing these reviews since v3.14.0 and this is the first time my entire must-fix list has been cleared in the immediately following version: the `random_bytes` Windows fallback now returns empty instead of `rand()`, the self-hosted emitter now uses the correct compile+exec+free pattern for regex, the `file_exists` call site uses `i64` with an `icmp ne`, the HTTP response buffer has a 64 MB cap, the bcrypt handle is cached in a static, and all three dlopen loaders (`ssl`, `evp`, `pcre2`) use atomic compare-and-swap instead of non-atomic `loaded` flags. Additionally, the `intern_ensure_table()` call was moved inside the lock (4th cycle item, finally fixed), `__mn_str_concat` now has early-return paths that copy instead of borrow (2nd cycle item, fixed), `__mn_str_from_bool` uses `i64` ABI instead of returning static string literals (the i1 ABI bug that Rattler also flagged), and `-Werror` is now applied to ALL C files in `build_stage1.py`, not just `mapanare_core.c`. On top of all that, there are 2,881 lines of brand new GPU runtime code (CUDA + Vulkan + Metal stubs) that, to my grudging admission, are written with proper resource cleanup and thread-safe initialization.

Here is the catch. The new GPU code introduces a handful of new issues -- none as serious as the crypto `rand()` fallback from v3.45.0, but there are real memory safety concerns in the GLSL temp file usage, the `tensor_from_list` data borrowing pattern, and the `__mn_gpu_tensor_matmul` integer overflow potential. The `__mn_net_init` and `mn_init_tag_strings` thread-safety issues remain unfixed (5th cycle for tag strings, and `__mn_net_init` was not touched despite the three sibling loaders being fixed in the same file). And the conservative drop glue for struct-returning functions is now entering its 6th review cycle. But the overall trajectory is unmistakably positive: the v3.47.0 release fixed more review items than any previous version, added a significant GPU subsystem with competent engineering, and cleaned up several entrenched issues. My score goes UP from 9.3 to 9.5.

---

## Progress Since Last Review (v3.45.0 -> v3.47.0)

### Must-Fix Items from v3.45.0

| v3.45.0 Item | Severity | Status in v3.47.0 | Notes |
|---|---|---|---|
| `random_bytes` falls back to `rand()` on Windows | HIGH | **FIXED** | `mapanare_io.c:1237-1238` now returns `__mn_str_empty()` when BCrypt unavailable. `rand()` fallback completely removed. |
| Self-hosted emitter phantom `__mn_regex_match`/`__mn_regex_replace` | MEDIUM | **FIXED** | `emit_llvm.mn:2397-2424` now uses compile+exec+free / compile+replace+free pattern matching Python emitter. Proper handle lifecycle. |
| Self-hosted emitter `file_exists` return type `i1` vs `i64` | MEDIUM | **FIXED** | `emit_llvm.mn:2348-2355` calls as `i64`, then `icmp ne i64 %fe_raw, 0`. Correct ABI. |

**Resolution rate: 3/3 (100%).** First time EVER achieving 100% resolution of my must-fix items.

### Should-Fix Items from v3.45.0

| v3.45.0 Item | Severity | Status in v3.47.0 | Notes |
|---|---|---|---|
| `__mn_http_get` no response size limit | MEDIUM | **FIXED** | `mapanare_io.c:1635` adds `if (cap > 64 * 1024 * 1024) break;` |
| `bcrypt.dll` handle leaked per call | LOW | **FIXED** | `mapanare_io.c:1225-1230` caches `s_bcrypt` and `s_bcrypt_gen` in statics. |
| `ssl_load_library` not thread-safe | LOW | **FIXED** | `mapanare_io.c:300-305` uses `__atomic_compare_exchange_n` with acquire/release. |
| `evp_load` not thread-safe | LOW | **FIXED** | `mapanare_io.c:987-992` same atomic CAS pattern. |
| `pcre2_load` not thread-safe | LOW | **FIXED** | `mapanare_io.c:1313-1318` same atomic CAS pattern. |

**Resolution rate: 5/5 (100%).** Both must-fix and should-fix lists fully cleared.

### Cross-Panel Items Fixed

| Item | Source | Status | Notes |
|---|---|---|---|
| `intern_ensure_table()` outside lock | Mamba, 4th cycle | **FIXED** | `mapanare_core.c:295-297` now calls inside `intern_lock()`. |
| `__mn_str_concat` empty-operand allocation | Mamba, 2nd cycle | **FIXED** | `mapanare_core.c:409-411` early returns with `__mn_str_from_parts()` (copy, not borrow). |
| Self-hosted `str(false)` i1 ABI bug | Rattler | **FIXED** | `emit_llvm.mn:2839-2841` adds `zext i1 to i64` before `__mn_str_from_bool`. Declaration changed from `i1` to `i64`. |
| `-Werror` inconsistent in `build_stage1.py` | Cobra, Anaconda | **FIXED** | `scripts/build_stage1.py:104` now has `-Werror` in base flags applied to all C files. |
| `__mn_str_from_bool` static literal ABI | Rattler (related) | **FIXED** | `mapanare_core.c:660-663` now calls `__mn_str_from_cstr()` instead of returning static `MnString`. Tag bit system works correctly. |
| `obj_path` not in cleanup | Anaconda, 3rd cycle | **FIXED** | `scripts/build_stage1.py:179` includes `obj_path` in the cleanup list. |
| Self-hosted emitter I/O builtin declarations | Rattler | **FIXED** | `emit_llvm.mn:385-421` adds all I/O, crypto, regex, and GPU declarations. |
| `mnstr_to_cstr` duplicated 4x | Mamba | **FIXED** | `mapanare_internal.h:20-29` provides shared `static inline` implementation. |
| `MnHandleTable` duplicated | Mamba | **FIXED** | `mapanare_internal.h:40-61` provides shared implementation. |

### Unfixed Carry-Forward Items

| Item | Cycle | Status | Notes |
|---|---|---|---|
| Conservative drop glue skips struct returns | 6th cycle | **UNCHANGED** | `emit_llvm_text.py:966-968` same early return. |
| `mn_init_tag_strings` not thread-safe | 5th cycle | **UNCHANGED** | `mapanare_core.c:2670-2671` same non-atomic flag. |
| `mn_signal_propagate` recursive, no depth bound | 5th cycle | **UNCHANGED** | `mapanare_core.c:1981` same DFS. |
| `__mn_signal_on_change` drops on overflow | 5th cycle | **UNCHANGED** | Still void return. |
| `__mn_map_new` backward-compat fallback | 5th cycle | **UNCHANGED** | Still heuristic-guess. |
| `MN_PROFILE_FREE` never called | 3rd cycle | **UNCHANGED** | Macro exists, zero callsites. |
| `__mn_read_line` truncates at 4096 | 2nd cycle | **UNCHANGED** | Same stack buffer. |
| `__mn_net_init` not thread-safe | 2nd cycle | **UNCHANGED** | Same non-atomic `s_net_initialized`. See Issue #5. |

**8 items remain, all LOW severity.** The oldest (`mn_init_tag_strings`, `signal_propagate`, `signal_on_change`, `__mn_map_new`) are entering their 5th cycle. None have caused a known production bug. The `__mn_net_init` case is annoying because the three sibling loaders in the same file were fixed -- see Issues.

---

## Strengths

1. **GPU initialization is thread-safe from day one.** `mapanare_gpu.c:1057-1067` uses `pthread_once` on POSIX and `InterlockedCompareExchange` on Windows. This is the correct pattern that I have been requesting for the SSL/EVP/PCRE2 loaders since v3.42.0. The fact that new GPU code ships with the pattern already in place while the old IO loaders were retrofitted in the same release tells me the developer actually learned from the review feedback. Fine, I guess that does not suck.

2. **The GPU resource cleanup ladders are correct.** I traced every allocation path in `mapanare_gpu.c`:
   - `cuda_load_library` (line 483-538): On any symbol resolution failure, closes the handle and returns -1. No leak.
   - `vulkan_load_library` (line 603-683): Same pattern, 30+ symbols loaded, closes handle on any failure.
   - `vulkan_init_context` (line 692-789): Creates instance -> physical device -> logical device -> command pool. On command pool failure, destroys device and instance. On device failure, destroys instance. Correct reverse-order cleanup.
   - `mapanare_vk_pipeline_create` (line 1338-1456): Six objects created in sequence (shader module -> descriptor layout -> pipeline layout -> pipeline -> descriptor pool -> descriptor set allocation). On ANY failure at any stage, all previously-created objects are destroyed. I counted six failure paths and all six release everything allocated up to that point.
   - `cuda_elementwise_op` (line 1590-1668): Allocates 3 GPU buffers, uploads data, loads kernel, launches, downloads result, frees kernel, frees all 3 buffers. Every failure path frees all previously-allocated resources. Correct.
   - `mapanare_gpu_shutdown` (line 1069-1082): Destroys CUDA context, closes CUDA library, destroys Vulkan pipeline components, closes Vulkan library, frees Metal context. Complete.

   In Rust, `Drop` implementations would handle all of this automatically. In C, you write manual cleanup ladders. These cleanup ladders are all correct. This is ~1,950 lines of C with zero resource leaks on error paths. For a dlopen-based GPU runtime, that is solid work.

3. **The `tensor_from_list` / `tensor_borrow_free` pattern in `mapanare_gpu_builtins.c` is a well-defined borrow.** `tensor_from_list` (line 52-64) creates a temporary `mapanare_tensor_t` struct whose `.data` field points directly into the MnList's data buffer. `tensor_borrow_free` (line 67-71) frees only the struct and shape array, NOT the data. This is a manual borrow -- the tensor borrows the list's data, uses it for GPU upload, and then the struct shell is freed without touching the borrowed data. The ownership is clear: the MnList owns the data, the tensor just reads it. In Rust, this would be a `&[f64]` slice. Here it is a pointer with a free-all-but-data function. Correct, if fragile -- see Issue #3.

4. **The atomic CAS pattern on dlopen loaders is correct.** `mapanare_io.c:300-305` (ssl), `987-992` (evp), `1313-1318` (pcre2) all use the same pattern:
   ```c
   if (__atomic_load_n(&s_ssl.loaded, __ATOMIC_ACQUIRE))
       return s_ssl.available ? 0 : -1;
   int expected = 0;
   if (!__atomic_compare_exchange_n(&s_ssl.loaded, &expected, 1, 0,
                                    __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE))
       return s_ssl.available ? 0 : -1;
   ```
   This is the correct double-checked pattern: first acquire-load to fast-path already-initialized case, then CAS to win the initialization race. Losers see the CAS fail and return the `available` result from the winner's initialization. The memory orderings are correct: acquire on the fast-path load ensures visibility of `available` written by the winner; acq_rel on the CAS ensures the initialization writes are visible to all subsequent acquire-loads. In Rust, this would be `Once::call_once`. Here it is manual atomics. The orderings are right.

5. **The `__mn_str_concat` early-return fix is correct and prevents a real double-free.** The commit message says "copy instead of borrow to prevent double-free." The fix at `mapanare_core.c:410-411` returns `__mn_str_from_parts(mn_untag(b.data), b.len)` (which heap-allocates a copy) instead of returning the input string directly (which would give the caller a second reference to memory that might be freed by the original owner). This is the ownership problem I have been warning about since v3.14.0: without a borrow checker, returning a reference to an argument's data creates a shared-ownership situation with no refcounting. The fix (copy on return) is the correct conservative approach. It allocates unnecessarily when the original is not going to be freed, but it is safe. In Rust, the borrow checker would tell you at compile time whether returning a reference is valid. Here, you copy.

6. **The SPEC Section 3.10 Tensor disclaimer is present.** `docs/SPEC.md:591-592` says "Tensor types are specified but not yet implemented in any backend." The GPU builtins that ARE implemented (`gpu_tensor_add`, etc.) operate on `List<Float>`, not `Tensor<Float>[shape]`. The distinction is correct and documented. The SPEC Section 23 area also has the GPU builtins described with their runtime-only status.

---

## Issues Found

### 1. **[MEDIUM]** `vk_compile_glsl` writes to hardcoded `/tmp/mn_gpu_shader.comp` -- race condition and symlink attack

`mapanare_gpu.c:822-823`:
```c
const char *tmp_glsl = "/tmp/mn_gpu_shader.comp";
const char *tmp_spirv = "/tmp/mn_gpu_shader.spv";
```

This is a textbook TOCTOU vulnerability. Two Mapanare processes running on the same machine will race on the same file. Worse, on a multi-user system, an attacker can create a symlink at `/tmp/mn_gpu_shader.comp` pointing to any writable file, and the `fopen(tmp_glsl, "w")` at line 830 will overwrite that file with GLSL source code. The attacker can also replace `/tmp/mn_gpu_shader.spv` between the `glslc` invocation and the `fopen(tmp_spirv, "rb")` at line 934, causing the runtime to load arbitrary SPIR-V bytecode.

On Windows, the fallback names (`mn_gpu_shader.comp`, `mn_gpu_shader.spv`) are in the CURRENT WORKING DIRECTORY, which is even worse -- any Mapanare program using GPU tensor ops will scatter temp files in whatever directory the user runs from.

In Rust, `tempfile::NamedTempFile` creates files with unique names using `O_EXCL` to prevent symlink attacks. Here, `mkstemp()` (POSIX) or `tmpnam_s` + `O_CREAT|O_EXCL` (Windows) would eliminate both the race and the symlink vector.

**Fix:** Use `mkstemp()` to generate unique temp file paths on POSIX, and `GetTempFileName` on Windows.

### 2. **[MEDIUM]** `__mn_gpu_tensor_matmul` does not validate `m*k` and `k*n` against list lengths

`mapanare_gpu_builtins.c:161-185`:
```c
MN_EXPORT MnList __mn_gpu_tensor_matmul(const MnList *a, const MnList *b,
                                         int64_t m, int64_t n, int64_t k) {
    // ...
    ta->shape[0] = m; ta->shape[1] = k;
    ta->size = m * k;
    // ...
    tb->shape[0] = k; tb->shape[1] = n;
    tb->size = k * n;
```

The function accepts user-provided `m`, `n`, `k` dimensions and constructs tensor shapes without checking that `a->len >= m * k` or `b->len >= k * n`. If the user passes dimensions larger than the actual list, the GPU kernel will read past the end of the data buffer. On CUDA, this means reading uninitialized GPU memory (information leak or garbage results). On CPU fallback, this means reading past the end of the MnList's heap buffer -- classic out-of-bounds read.

Additionally, `m * k` and `k * n` can overflow `int64_t` for sufficiently large dimensions. The resulting `ta->size` would be a small or negative number, causing the size check in `cuda_matmul` (line 1674-1675) to pass with a tiny allocation while the kernel reads a huge range.

In Rust, this would be a bounds-checked index or a `checked_mul` with `Result`. Here, adding `if (a->len < m * k || b->len < k * n) return empty_list;` and using `__builtin_mul_overflow` for the multiplications would catch both issues.

**Fix:** Validate `a->len >= m * k` and `b->len >= k * n` before constructing tensors. Use `__builtin_mul_overflow` for the multiplications.

### 3. **[MEDIUM]** `tensor_from_list` borrows list data without lifetime guarantee -- data freed while tensor alive

`mapanare_gpu_builtins.c:52-63`:
```c
static mapanare_tensor_t *tensor_from_list(const MnList *list) {
    // ...
    t->data = list->data;  // borrow!
    // ...
}
```

The tensor borrows the MnList's data pointer. If the MnList is freed or resized between `tensor_from_list()` and the point where the tensor data is consumed (e.g., `mapanare_gpu_buffer_upload`), the tensor's `.data` pointer becomes dangling. Currently this is safe because the element-wise builtins (`__mn_gpu_tensor_add` etc.) create the tensor, pass it to the GPU operation, and free it all in a single function scope. But the pattern is fragile: any future refactoring that moves the tensor creation and GPU operation into different scopes would create a use-after-free.

In Rust, the tensor would hold a `&'a [f64]` reference with a lifetime tied to the list, and the compiler would reject any code where the list is freed before the tensor. Here, there is no such guarantee -- only the discipline that `tensor_from_list` and `tensor_borrow_free` must bracket the same scope as the list lifetime. The comment at line 52 says "borrows list data" which is good documentation, but comments are not enforcement.

This is MEDIUM rather than HIGH because the current usage is all contained within single function bodies and there is no path where the list is freed early. But for a production release, the pattern should be documented with a big "DO NOT move this across scope boundaries" warning, or the borrow should be replaced with a copy.

### 4. **[MEDIUM]** Conservative drop glue for struct-returning functions (6th review cycle)

`emit_llvm_text.py:966-968`:
```python
skip_struct_ret = ret_ty.startswith("{") and ret_ty not in (VOID, I1, I64, DBL)
if skip_struct_ret:
    return
```

Same issue. 6th consecutive review. Every function returning a struct leaks every local resource (strings, closures, boxed values). The GPU examples (`vector_add.mn`, `matmul_bench.mn`) call `gpu_tensor_add`/`gpu_tensor_matmul` which return `List<Float>` (a struct). The caller's `main()` function returns `void`, so its drop glue does fire. But any helper function returning a struct will leak.

I am keeping this at MEDIUM. The leak-over-UAF trade-off remains correct. But this is now the longest-standing open issue in the project.

### 5. **[LOW]** `__mn_net_init` still uses non-atomic `s_net_initialized` -- 3 sibling loaders fixed, this one missed

`mapanare_io.c:73-83`:
```c
static int s_net_initialized = 0;
MN_IO_EXPORT int64_t __mn_net_init(void) {
    if (s_net_initialized) return 0;
    // ...
    s_net_initialized = 1;
    return 0;
}
```

The three dlopen loaders in the same file (`ssl_load_library`, `evp_load`, `pcre2_load`) were all fixed with atomic CAS in this release. The structurally identical `__mn_net_init` in the same file was not. On Windows, `WSAStartup` is ref-counted so the double-init is harmless. On POSIX, `__mn_net_init` is a no-op. So the race is benign. But the inconsistency is jarring -- you fixed three instances of the pattern and missed the fourth one in the same file.

### 6. **[LOW]** `mn_init_tag_strings` not thread-safe (5th review cycle)

`mapanare_core.c:2670-2671`: Same non-atomic flag. Same issue. 5th cycle. I note it for completeness but will not waste more words.

### 7. **[LOW]** `mn_signal_propagate` recursive with no depth bound (5th review cycle)

`mapanare_core.c:1981`: Same recursive DFS. 5th cycle.

### 8. **[LOW]** `MN_PROFILE_FREE` still never called (3rd review cycle)

`mapanare_core.c:64`: Macro defined. Zero callsites. `mn_alloc_live` only goes up, never down. The "peak live" counter in `mn_profile_report()` is really "total allocated." 3rd cycle.

### 9. **[LOW]** `mapanare_gpu_init()` called redundantly on every GPU builtin

`mapanare_gpu_builtins.c:23,29,39,90,108,126,144,163`: Every single GPU builtin function calls `mapanare_gpu_init()`. The init function itself is idempotent (`pthread_once`/`InterlockedCompareExchange`) so this is safe, but each call involves an atomic load and comparison. For the tensor operations (`gpu_tensor_add` etc.), this means the init check is done twice -- once in the builtin wrapper and once internally by `mapanare_gpu_tensor_add` which also calls `mapanare_gpu_init()`. No bug, just wasted cycles.

### 10. **[LOW]** `s_bcrypt` cache in `__mn_random_bytes_str` not thread-safe

`mapanare_io.c:1225-1230`:
```c
static HMODULE s_bcrypt = NULL;
static fn_BCryptGenRandom s_bcrypt_gen = NULL;
if (!s_bcrypt) {
    s_bcrypt = LoadLibraryA("bcrypt.dll");
    if (s_bcrypt) {
        s_bcrypt_gen = (fn_BCryptGenRandom)GetProcAddress(s_bcrypt, "BCryptGenRandom");
    }
}
```

The cached handle uses a non-atomic check-then-set. Two threads calling `random_bytes` simultaneously could both enter the `if (!s_bcrypt)` block and both call `LoadLibraryA`. This is the same class of bug as `__mn_net_init`, and the same class that was just fixed in the three dlopen loaders. The worst case is benign (double `LoadLibrary` returns the same handle, ref count incremented). But the developer just demonstrated they know the atomic CAS pattern and chose not to use it here. Inconsistent.

### 11. **[LOW]** `vk_compile_glsl` does not check `fseek`/`ftell` return values

`mapanare_gpu.c:937-939`:
```c
fseek(f, 0, SEEK_END);
long size = ftell(f);
fseek(f, 0, SEEK_SET);
```

`ftell` returns -1L on error. The subsequent check `if (size <= 0 || (size % 4) != 0)` catches -1L (it is < 0), so there is no bug here. But `fseek` return values are unchecked. On a filesystem error, `fseek(f, 0, SEEK_SET)` could fail, and the subsequent `fread` would read from the wrong position. In practice, if `fseek` fails on a local temp file, the system is in deep trouble anyway. LOW.

### 12. **[LOW]** `cuda_matmul` does not check `mapanare_gpu_buffer_upload` return values

`mapanare_gpu.c:1693-1694`:
```c
mapanare_gpu_buffer_upload(d_a, a->data, a_bytes);
mapanare_gpu_buffer_upload(d_b, b->data, b_bytes);
```

Compare with `cuda_elementwise_op` at lines 1612-1613 which DOES check the return values:
```c
if (mapanare_gpu_buffer_upload(d_a, a->data, nbytes) != 0 ||
    mapanare_gpu_buffer_upload(d_b, b->data, nbytes) != 0) {
```

The matmul path ignores upload failures. If `cuMemcpyHtoD` fails (e.g., PCIe error, device memory corruption), the kernel will operate on uninitialized GPU memory and produce garbage. The element-wise path handles this correctly; the matmul path does not. Copy-paste inconsistency.

---

## Recommendations

### Must-Do Before v4.0.0

1. **Fix `__mn_gpu_tensor_matmul` dimension validation.** Add `if (a->len < m * k || b->len < k * n) return empty;` before constructing tensors. Use `__builtin_mul_overflow` for the multiplications to prevent integer overflow. (Issue #2)

2. **Fix `vk_compile_glsl` temp file race.** Replace hardcoded `/tmp/mn_gpu_shader.*` with `mkstemp()` on POSIX and `GetTempFileName` on Windows. This is both a correctness issue (two processes race) and a security issue (symlink attack on multi-user systems). (Issue #1)

### Should-Do for v4.0.0 Quality

3. **Fix `cuda_matmul` upload return value check.** Add `if (... != 0)` check matching the element-wise path. Copy-paste bug. 1 line. (Issue #12)

4. **Fix `s_bcrypt` thread safety.** Apply the same atomic CAS pattern used for `ssl`/`evp`/`pcre2`. Consistency. (Issue #10)

5. **Fix `__mn_net_init` thread safety.** Same pattern. Consistency. (Issue #5)

### Should-Do for v4.1

6. **Implement targeted drop glue for struct-returning functions.** (Issue #4 -- 6th cycle)
7. **Resolve the 5 remaining multi-cycle LOWs.** `mn_init_tag_strings` (5th cycle), `signal_propagate` (5th), `signal_on_change` (5th), `MN_PROFILE_FREE` (3rd), `__mn_read_line` (2nd).

---

## v4.0.0 Readiness Assessment

**Conditionally ready. Two must-fix items, both in new v3.46.0 GPU code.**

The v3.47.0 release resolved every must-fix and should-fix item from my v3.45.0 review. This is unprecedented in the project's review history. The core runtime (mapanare_core.c, mapanare_io.c, mapanare_runtime.c) is now cleaner than it has ever been: the intern table is properly locked, the string concat prevents double-free, the dlopen loaders are thread-safe, the crypto fallback is secure. The self-hosted emitter has correct ABI for all builtins including the new GPU set. The build system applies `-Werror` uniformly. The shared internal header eliminates code duplication.

The two remaining blockers are both in the new GPU code:

| # | Fix | Effort | Risk if Unfixed |
|---|-----|--------|-----------------|
| 1 | `__mn_gpu_tensor_matmul` validate `m*k <= a->len` and `k*n <= b->len`, overflow-check | 5 lines | Out-of-bounds read on CPU fallback, uninitialized GPU memory read on CUDA |
| 2 | `vk_compile_glsl` use `mkstemp()` / `GetTempFileName` for temp files | 15 lines | Race condition on concurrent GPU programs, symlink attack vector |

Estimated total fix effort: 20 minutes. Both are in isolated functions with clear patterns.

The drop glue issue (6th cycle) is the largest remaining architectural concern. It is the correct safety trade-off (leak > UAF), and the long-running use cases (todo.mn, http_fetch.mn) are bounded by user interaction speed, so memory exhaustion in practice takes hours. But for production, the leak should be documented as a known limitation in the release notes.

---

## Thread Safety Scorecard (v3.47.0)

| Component | Thread-safe? | Notes | Change from v3.45.0 |
|-----------|-------------|-------|---------------------|
| Ring buffer (SPSC) | Yes | Correct atomic head/tail | Same |
| Thread pool | Yes | Mutex-protected work queue | Same |
| Agent registry | Yes | Mutex on all operations | Same |
| Signal batching | Yes | Lock on batch state | Same |
| Signal tracking | Yes | `_Thread_local` context | Same |
| Signal subscribe/unsubscribe/on_change | Yes | `mn_signal_lock()` | Same |
| Intern table | Yes | Mutex on all operations, `intern_ensure_table()` now inside lock | **FIXED** |
| List COW refcount | Yes | Atomic operations | Same |
| Backpressure | Yes | All atomic | Same |
| Shutdown handler | Yes | Set flags only | Same |
| OOB buffer | Yes | `_Thread_local` | Same |
| **SSL library load** | **Yes** | **Atomic CAS** | **FIXED** |
| **EVP library load** | **Yes** | **Atomic CAS** | **FIXED** |
| **PCRE2 library load** | **Yes** | **Atomic CAS** | **FIXED** |
| **GPU init** | **Yes** | **`pthread_once` / `InterlockedCompareExchange`** | **NEW -- correct** |
| Tag string init | No | Non-atomic flag, 5th cycle | Same |
| Net init | No | Non-atomic `s_net_initialized`, 3rd cycle | Same |
| BCrypt cache | No | Non-atomic `s_bcrypt`, NEW | **NEW -- benign** |

**Thread-safe: 16/19. Unsafe: 3 (2 old, 1 new). Previously: 13/18.**

The thread safety posture improved dramatically: 3 loaders fixed, GPU init correct from day one. Net gain: +3 safe, -1 new unsafe (bcrypt cache). Overall: from 72% safe to 84% safe. The three remaining races are all benign (worst case: double-init) but the inconsistency between fixed and unfixed patterns in the same files is sloppy.

---

## Raw Notes

### The `__mn_str_concat` fix is deeper than it looks

The commit message says "copy instead of borrow to prevent double-free." The old code returned the input MnString directly when one operand was empty. The problem: if the caller's drop glue later frees the returned string, and the original owner also frees the same string, you get a double-free. The tag-bit ownership model means `mn_is_heap()` returns true for both the original and the returned copy (same pointer, same bit 0). The new code calls `__mn_str_from_parts()` which allocates a fresh copy, giving the caller sole ownership. This is the correct fix for a language without a borrow checker. It costs one allocation per empty-operand concat, which is fine.

### The GPU code duplicates PTX kernels as C string literals

`mapanare_gpu.c:60-321` contains five PTX kernels (add, sub, mul, div, matmul) totaling ~260 lines of inline string assembly. Plus five GLSL shaders for Vulkan (~100 lines). Plus one minimal SPIR-V blob (11 uint32_t values, line 356-371). This is 360+ lines of GPU assembly embedded as C strings. In Rust, you would use `include_str!("tensor_add.ptx")` to keep the GPU code in separate files. Here, the entire GPU compute backend is in one massive 1,951-line file. For a v1.0, this is acceptable -- the GPU kernels are small and rarely change. But any optimization pass on the PTX (shared memory, tiling, etc.) will make this file unwieldy.

### The `list_from_tensor` function does element-by-element copy

`mapanare_gpu_builtins.c:74-82`:
```c
static MnList list_from_tensor(mapanare_tensor_t *t) {
    MnList list = __mn_list_new((int64_t)sizeof(double));
    if (!t || t->size <= 0) return list;
    for (int64_t i = 0; i < t->size; i++) {
        double val = ((double *)t->data)[i];
        __mn_list_push(&list, &val);
    }
    return list;
}
```

This pushes each element one at a time. Each `__mn_list_push` may trigger a `mn_list_grow` reallocation. For a 1,000,000-element tensor result, that is up to 20 reallocations (doubling from initial capacity). A single `memcpy` after pre-allocating the full size would be O(1) allocations instead of O(log n). For a GPU compute use case where you just did a matrix multiply on an RTX 4090, spending more time copying the result into a list than the GPU spent computing it would be embarrassing. This is not a safety issue, just a performance foot-gun.

### The `mapanare_gpu_init_impl` memset is safe but order-dependent

`mapanare_gpu.c:993`:
```c
memset(&g_gpu_ctx, 0, sizeof(g_gpu_ctx));
```

This zeroes the entire global context before initialization. Safe because `pthread_once` guarantees single execution. But note that `g_gpu_init_result` is a SEPARATE global (line 51), and it is NOT protected by the `pthread_once`. On Windows, `InterlockedCompareExchange` guards the `mapanare_gpu_init_impl` call, but `g_gpu_init_result` is read at line 1066 without synchronization with respect to the `mapanare_gpu_init_impl` write at line 1054. The `pthread_once` path is fine because `pthread_once` provides a full memory barrier. The Windows `InterlockedCompareExchange` path has a subtle issue: the losing thread returns `g_gpu_init_result` before the winning thread has finished writing it. The `InterlockedCompareExchange` provides a barrier for `g_gpu_init_once` but not for `g_gpu_init_result`. In practice, the winning thread sets `g_gpu_init_result` before returning from `mapanare_gpu_init_impl`, and the losing thread's `InterlockedCompareExchange` acts as a full barrier on x86, so this is safe on x86. On ARM Windows (Surface Pro X, etc.), the barrier semantics differ and this could theoretically read stale `g_gpu_init_result`. This is extremely unlikely to cause issues in practice (GPU init is called early, usually from main thread), but it is architecturally wrong on non-x86.

### Score trajectory

**v3.14.0:** 6 CRITICAL, 8 HIGH. Score: 7.0.
**v3.25.0:** 0 CRITICAL, 0 HIGH. Score: 8.4.
**v3.33.0:** 0 CRITICAL, 0 HIGH. Score: 9.0.
**v3.39.0:** 0 CRITICAL, 0 HIGH. Score: 9.4.
**v3.40.0:** 0 CRITICAL, 0 HIGH. Score: 9.5.
**v3.45.0:** 1 HIGH (**NEW**), 4 MEDIUM, 11 LOW. Score: 9.3. (First decrease.)
**v3.47.0:** 0 HIGH, 4 MEDIUM (1 old + 3 **NEW**), 8 LOW (5 old + 3 **NEW**). Score: 9.5. (Recovery.)

The 0.2 increase from 9.3 to 9.5 reflects:
- Resolution of the only HIGH (crypto `rand()` fallback) -- the most impactful single fix since v3.25.0
- Resolution of all 3 v3.45.0 MEDIUMs (regex phantom symbols, file_exists ABI, HTTP response cap)
- Resolution of 5 cross-panel items (intern lock, str_concat, bool ABI, -Werror, obj cleanup, shared header)
- Three new MEDIUMs in GPU code (temp file race, matmul bounds, tensor borrow fragility) -- less severe than the resolved ones
- Net improvement in thread safety (13/18 -> 16/19)
- The continued 6th-cycle presence of the drop glue issue caps improvement

This is the best recovery between consecutive reviews in the project's history. The delta to 10.0 is:
- 0.2 points: fix the 4 MEDIUMs (2 GPU issues + 1 old drop glue + 1 borrow pattern)
- 0.2 points: proper ownership model in emitter (architectural, v4.1+)
- 0.1 points: resolve the 8 multi-cycle LOWs
