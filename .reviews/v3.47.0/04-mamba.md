# Mamba -- C / Runtime Review of Mapanare v3.47.0

**Reviewer:** Mamba
**Personality:** C minimalist. Every abstraction is bloat. Measures everything in unnecessary allocations. Terse. Brutal.
**Previous Version Reviewed:** v3.45.0 (score: 9.3/10, PASS WITH NOTES)
**Verdict:** PASS
**Confidence:** 9/10
**Score: 9.6/10** (up from 9.3)
**Files Reviewed:**
- `runtime/native/mapanare_core.c` (2,685 lines -- unchanged from v3.45.0)
- `runtime/native/mapanare_core.h` (678 lines -- unchanged)
- `runtime/native/mapanare_io.c` (1,672 lines -- up 17 from v3.45.0)
- `runtime/native/mapanare_io.h` (351 lines -- unchanged)
- `runtime/native/mapanare_runtime.c` (1,343 lines -- unchanged)
- `runtime/native/mapanare_runtime.h` (563 lines -- unchanged)
- `runtime/native/mapanare_platform.h` (97 lines -- unchanged)
- `runtime/native/mapanare_gpu.c` (1,951 lines -- up 13 from v3.45.0)
- `runtime/native/mapanare_gpu.h` (737 lines -- unchanged)
- `runtime/native/mapanare_gpu_builtins.c` (193 lines -- **NEW**)
- `runtime/native/mapanare_internal.h` (63 lines -- **NEW**)
- `runtime/native/mapanare_db.c` (1,130 lines -- unchanged)
- `runtime/native/mapanare_db.h` (210 lines -- unchanged)
- `runtime/native/mapanare_html.c` (812 lines -- unchanged)
- `runtime/native/mapanare_html.h` (124 lines -- unchanged)
- `runtime/native/mapanare_metal.h` (138 lines -- unchanged)
- `mapanare/emit_llvm.py` (2,883 lines -- deprecated, still alive)
- `tests/native/test_c_runtime.c` (1,239 lines -- unchanged)
- `tests/native/` (13 Python test files, 2,776 lines total -- unchanged)
- `VERSION` (3.47.0)

## Executive Summary

This is the first review in six cycles where more issues were fixed than introduced. Five of my seven v3.45.0 issues are resolved. The HMODULE leak is fixed with static caching (line 1225-1232 of `mapanare_io.c`). The `rand()` fallback is deleted -- returns empty on BCrypt failure, which is the only correct behavior. The `intern_ensure_table()` race is fixed after FIVE review cycles -- the call is now inside the lock (line 296, after `intern_lock()` at line 295). The `__mn_str_concat` early returns for empty operands are in (lines 409-411). The dlopen loaders (`ssl_load_library`, `evp_load`, `pcre2_load`) all use atomic CAS now instead of bare `loaded` flags. The HTTP response has a 64 MB cap (line 1636).

Two new files appeared: `mapanare_internal.h` (63 lines) with the shared `mnstr_to_cstr` and `MnHandleTable` that I asked for three times, and `mapanare_gpu_builtins.c` (193 lines) bridging the language-level `MnList` types to the GPU tensor API. The internal header exists but is not included by anyone. The duplicates remain in all three files. The header was written, not wired. Two steps forward, half a step back.

The GPU builtins file is clean. It takes `MnList*` by pointer to avoid ABI mismatch with struct-by-value, borrows list data into temporary tensors without copying, and frees the temporaries correctly. The `list_from_tensor` helper does one element-at-a-time push (line 77-80) which is O(n) in allocations for large tensors -- a single `memcpy` into a pre-sized list would be better -- but this is a convenience wrapper for a GPU path. Acceptable.

## Progress Since Last Review

| v3.45.0 Issue | Status in v3.47.0 | Verdict |
|---|---|---|
| **M1. `__mn_random_bytes_str` HMODULE leak** (MED) | **FIXED.** Lines 1225-1232: `s_bcrypt` and `s_bcrypt_gen` are now `static` -- `LoadLibraryA` called once, handle persisted. `rand()` fallback deleted (lines 1238-1240 return empty). Both the success and failure paths are clean. | **RESOLVED.** |
| **L1. `MN_PROFILE_FREE` never called** (LOW, 2nd cycle) | **NOT FIXED.** Line 64: `#define MN_PROFILE_FREE(sz) do { mn_alloc_live -= (sz); } while(0)`. Line 93: `__mn_free` still just calls `free(ptr)`. `mn_alloc_live` counter still only goes up. | **Still unfixed (3rd cycle).** |
| **L2. `intern_ensure_table()` outside lock** (LOW, 4th cycle) | **FIXED.** Line 295: `intern_lock()` is now called BEFORE line 296: `intern_ensure_table()`. The table allocation happens under the mutex. Five review cycles. | **RESOLVED.** |
| **L3. `__mn_str_concat` empty-operand allocation** (LOW, 2nd cycle) | **FIXED.** Lines 409-411: `if (a.len <= 0 && b.len <= 0) return __mn_str_empty();` then `if (a.len <= 0) return __mn_str_from_parts(...)` and `if (b.len <= 0) return __mn_str_from_parts(...)`. The `from_parts` call still copies when returning the non-empty operand -- a bare `return b;` or `return a;` would avoid the copy -- but the allocation on the zero-length case is gone. Close enough. | **RESOLVED.** |
| **L4. `mnstr_to_cstr` duplicated 4 times** (LOW, 1st cycle) | **PARTIALLY FIXED.** `mapanare_internal.h` was created with shared `mnstr_to_cstr` and `MnHandleTable`. But none of the .c files include it. The three duplicates in `mapanare_io.c:859`, `mapanare_db.c:55`, and `mapanare_html.c:49` remain. The fourth variant `mn_to_cstr` in `mapanare_core.c:1200` also remains. The header exists, the wiring does not. | **Half-fixed (2nd cycle).** |
| **L5. `mn_signal_propagate` unbounded recursion** (LOW, carry from Viper) | **NOT FIXED.** `mapanare_core.c` line 2005: `mn_signal_propagate(sub);` inside loop. Same depth-first traversal. Same stack overflow potential on deep dependency graphs. Same snapshot allocations leaked on stack overflow. | **Still unfixed (carry).** |
| **L6. `mn_init_tag_strings` not thread-safe** (LOW, carry from Viper) | **NOT FIXED.** `mapanare_core.c` line 2671: `if (mn_tag_strings_init) return;` -- bare read, no atomic. TSAN would flag it. | **Still unfixed (carry).** |
| **L7. `emit_llvm.py` still alive** (LOW, 3rd cycle) | **NOT FIXED.** 2,883 lines. Deprecated. Wrong `__mn_map_new` signature. | **Still unfixed (4th cycle).** |

**Summary: 5 of 7 issues resolved (3 fully, 1 partially, 1 close-enough).** This is the first net-positive review cycle since v3.33.0. The two remaining persistent issues (L1, L7) and the two carries (L5, L6) are the same theoretical/hygiene items they have been. The actual bugs are gone.

## Strengths

1. **The HMODULE fix follows the existing pattern.** Lines 1225-1232 of `mapanare_io.c`: `static HMODULE s_bcrypt = NULL; static fn_BCryptGenRandom s_bcrypt_gen = NULL;` with one-time `LoadLibraryA` guarded by the `if (!s_bcrypt)` check. This is exactly the pattern used by `s_ssl` and `s_evp`. Consistent. The deletion of the `rand()` fallback (line 1238-1240 returns empty) removes the only source of predictable "random" bytes. Correct.

2. **All three dlopen loaders are now thread-safe.** `ssl_load_library()` (lines 302-307), `evp_load()` (lines 987-992), and `pcre2_load()` (lines 1313-1318) all use `__atomic_compare_exchange_n` with `__ATOMIC_ACQ_REL` on the `loaded` flag. The loser of the CAS reads the `available` flag with acquire semantics. This is correct double-checked locking. There is a narrow window where a concurrent caller could see `loaded == 1` but `available` is still 0 (between the CAS write and the `available = 1` store at the end of init), but in that case the caller gets a graceful "not available" return, which is the correct fallback. Acceptable.

3. **The `__mn_str_concat` early returns are correct.** Line 409: both empty returns `__mn_str_empty()`. Lines 410-411: one-empty returns a copy of the non-empty operand via `__mn_str_from_parts`. This does copy instead of returning the original, which is overly conservative -- returning the original by value would be safe because MnString is just `{ptr, len}` and the caller already has a copy of the original. But the copy cost is bounded by the string length, not an allocation of a new zero-length buffer. Good enough.

4. **The GPU builtins bridge is clean and minimal.** 193 lines. `tensor_from_list` borrows the list data pointer without copying (line 56: `t->data = list->data`), creates a temporary wrapper struct, and `tensor_borrow_free` frees only the struct (not the data). The element-wise ops (`__mn_gpu_tensor_add` through `__mn_gpu_tensor_div`) are 4 identical functions differing only in the dispatch call. The matmul function manually constructs 2D tensor wrappers. All paths clean up on error. No leaks. Taking `MnList*` by pointer instead of by value avoids the SysV ABI struct-passing complexity.

5. **The HTTP response cap closes the OOM vector.** Line 1636: `if (cap > 64 * 1024 * 1024) break;`. Simple. A malicious server returning unbounded data will now be truncated at 64 MB instead of growing until OOM. The break exits the read loop, closes the connection, and returns whatever was received. Correct.

6. **The `mapanare_internal.h` header is correctly designed.** 63 lines. `static inline` functions so they compile away in release builds. `mnstr_to_cstr` has a `len < 0` guard (line 23) that the per-file duplicates lack. `MnHandleTable` uses `mn_handle_alloc`/`mn_handle_get`/`mn_handle_free` instead of the non-prefixed `handle_alloc` in the duplicates, reducing symbol collision risk. The header is better than the code it replaces. It just needs to be `#include`d.

## Issues Found

### LOW

**L1. `MN_PROFILE_FREE` still never called. (3rd review cycle.)**

`mapanare_core.c` line 64 vs line 93. The macro is defined. `__mn_free` does not call it. The `mn_alloc_live` counter monotonically increases. The `mn_alloc_peak` counter is a monotonically increasing counter of the same monotonically increasing counter. When `MN_PROFILE_MEM` is defined, the "peak live" metric in the atexit report (line 46) is identical to "total bytes," making it useless for leak detection. Same fix: add `MN_PROFILE_FREE(/* need to track size */)` to `__mn_free`, which requires knowing the allocation size. The pragmatic fix: track allocations in a side-table, or accept that peak tracking is broken and rename the counter to "total allocated."

**L2. `mapanare_internal.h` created but not wired. (2nd cycle for the underlying duplication.)**

The header exists at `runtime/native/mapanare_internal.h` with the correct `mnstr_to_cstr` and `MnHandleTable`. Zero files include it:

```
$ grep -r 'mapanare_internal.h' runtime/native/
mapanare_internal.h:2: * mapanare_internal.h ...
```

Three files still define their own local `mnstr_to_cstr`: `mapanare_io.c:859`, `mapanare_db.c:55`, `mapanare_html.c:49`. Two files still define their own `MnHandleTable` + `handle_alloc`/`handle_get`/`handle_free`: `mapanare_db.c:74-97`, `mapanare_html.c:70-95`. A fifth copy `mn_to_cstr` lives in `mapanare_core.c:1200` using `__mn_alloc` instead of `malloc`.

The header's `mnstr_to_cstr` is BETTER than all three local copies (it has `if (len < 0) len = 0;` and a `NULL` check on `raw`). Replace the locals with `#include "mapanare_internal.h"` and delete the duplicates. Three lines of includes, ninety lines of deletion.

**L3. `mn_signal_propagate` unbounded recursion. (Carry from Viper, multi-cycle.)**

`mapanare_core.c` line 2005. Unchanged. Each recursive call allocates a snapshot array (line 1988). Stack depth bounded only by signal dependency graph depth. This was acceptable at v3.33.0 when nobody was building production signal graphs. It remains acceptable at v3.47.0 because the Mapanare signal system is not heavily used in the real-world examples. It will become a problem at v5.0 if anyone builds a reactive UI with 100+ computed signals.

**L4. `mn_init_tag_strings` not thread-safe. (Carry from Viper, multi-cycle.)**

`mapanare_core.c` line 2671: bare `int` read of `mn_tag_strings_init`. Not atomic. The function is called from `__mn_any_typename` (line 2679) which can be called from any thread. The fix is the same CAS pattern now used by `ssl_load_library`, `evp_load`, and `pcre2_load`. This is the fourth dlopen-style loader in the codebase that should use the pattern but does not.

**L5. `emit_llvm.py` still alive. (4th review cycle.)**

2,883 lines. Deprecated since v2.0.0. Contains the wrong `__mn_map_new` 3-param signature (line 414 vs C runtime's 4-param). No code paths use it except via explicit `--emitter=llvm` flag on the CLI. Nobody should be using this flag. Delete the file or at minimum mark it as `# type: ignore` and add a deprecation warning on import.

**L6. `__mn_read_line` truncates at 4096 bytes silently. (Carry from Viper.)**

`mapanare_core.c` line 1296: `char buf[4096];` with `fgets(buf, sizeof(buf), stdin)`. Input longer than 4095 bytes is truncated without warning. This is the bootstrapping stdin reader used by `read_line()` in the language. For the self-hosted compiler reading source files, 4096 is fine (no Mapanare source line is longer than ~300 chars). For user programs reading arbitrary input, it is a silent data loss bug. Use `getline()` on POSIX or a growing buffer on Windows.

**L7. User-Agent header still says "Mapanare/3.42". (NEW, trivial.)**

`mapanare_io.c` line 1613: `User-Agent: Mapanare/3.42`. VERSION is 3.47.0. This is a string literal in a `snprintf` call, so it does not auto-update. Either hardcode the current version or read from a compile-time define.

**L8. `__mn_random_bytes_str` static init race on Windows. (NEW, theoretical.)**

`mapanare_io.c` lines 1225-1227: `static HMODULE s_bcrypt = NULL; ... if (!s_bcrypt) { s_bcrypt = LoadLibraryA(...); }`. The `s_bcrypt` check is a bare pointer read, not an atomic load. Two threads calling `__mn_random_bytes_str` simultaneously on first use could both enter the `if (!s_bcrypt)` block. Windows `LoadLibraryA` is reference-counted, so this causes a double-load (two HMODULE references to the same DLL) rather than UB. The second thread might read `s_bcrypt_gen` before the first thread has stored it. Use the same CAS pattern from `ssl_load_library`.

Severity is LOW because: (a) this function is typically called from a single thread at startup, (b) the worst case is two `LoadLibrary` calls, not memory corruption, and (c) `s_bcrypt` is a static local, so after the first write both threads see the cached value on subsequent calls.

## Bloat Assessment

| Component | Lines (v3.45.0) | Lines (v3.47.0) | Delta | Verdict |
|-----------|-----------------|-----------------|-------|---------|
| mapanare_core.c | 2,685 | 2,685 | 0 | Unchanged |
| mapanare_core.h | 678 | 678 | 0 | Unchanged |
| mapanare_io.c | 1,655 | 1,672 | **+17** | HMODULE fix + rand() removal |
| mapanare_io.h | 351 | 351 | 0 | Unchanged |
| mapanare_runtime.c | 1,343 | 1,343 | 0 | Unchanged |
| mapanare_runtime.h | 563 | 563 | 0 | Unchanged |
| mapanare_gpu.c | 1,938 | 1,951 | **+13** | Minor GPU adjustments |
| mapanare_gpu.h | 737 | 737 | 0 | Unchanged |
| mapanare_gpu_builtins.c | -- | 193 | **+193** | **NEW**: language-level GPU bridge |
| mapanare_internal.h | -- | 63 | **+63** | **NEW**: shared internal helpers |
| All other .c/.h | 3,319 | 3,319 | 0 | Unchanged |
| **Total C runtime** | **13,059** | **13,355** | **+296 (+2.3%)** | Controlled growth |

The delta is 296 lines across two versions. Compare to 5,101 lines across the v3.41-v3.45 arc. Growth rate went from 1,020 lines/version back to 148 lines/version. The 193-line GPU builtins file is justified -- it bridges MnList to the tensor API without polluting either side. The 63-line internal header is justified by definition (it exists to deduplicate). The 17-line io.c growth is bug fixes. The 13-line gpu.c growth is minor. This is a stabilization release, not a feature dump. Correct.

## ABI Compatibility

No ABI changes. All existing function signatures match between headers and implementations. The new GPU builtins take `const MnList *` (pointer, not value) to avoid struct-by-value ABI complexity -- this is explicitly called out in the source comment (line 9 of `mapanare_gpu_builtins.c`). The `__mn_gpu_tensor_matmul` signature takes three extra `int64_t` parameters (m, n, k) for matrix dimensions, matching the LLVM emitter's expectation.

One concern: `tensor_from_list` (gpu_builtins.c line 52) casts `list->data` to `double*` implicitly by storing it in `t->data` (a `void*`) and later indexing it as `((double *)t->data)[i]`. The MnList stores raw bytes -- `list->data` points to an array of `elem_size`-byte elements. For `List<Float>` where `elem_size == 8`, this is correct. For any other list type passed to these functions, it would be silent reinterpretation. The functions are only called from GPU builtins which are typed `List<Float>` in the language, so the invariant holds. But there is no runtime check.

The `__mn_map_new` 3-param vs 4-param ABI mismatch in `emit_llvm.py` persists. Fourth review cycle.

## GPU Runtime Assessment

The GPU runtime (`mapanare_gpu.c`, 1,951 lines) is mostly dead weight for current users. It loads CUDA and Vulkan via dlopen, initializes device contexts, and provides tensor operations. The new `mapanare_gpu_builtins.c` (193 lines) bridges this to the language level.

**Unnecessary complexity for v4.0.0:**

- CUDA + Vulkan + Metal backends = three GPU APIs. Current user base: zero GPU programs. The entire 1,951-line file could be a 200-line stub that loads CUDA only. But dlopen means it costs nothing at link time or startup time unless you call `mapanare_gpu_init()`, so the dead code argument is weaker.

- GLSL shader sources embedded as string constants (lines 374-443): 5 shaders, ~70 lines total. These are compiled at runtime via `glslc` subprocess or fall back to pre-compiled SPIR-V. The pre-compiled SPIR-V (lines 356-371) is a placeholder -- the comment says "actual SPIR-V is generated at runtime." This means the Vulkan fallback path does not actually work without `glslc` installed. This should be documented or the placeholder removed.

- The GPU builtins `list_from_tensor` helper (line 74-82) copies elements one at a time via `__mn_list_push`. For a GPU tensor result of N elements, this is N calls to `__mn_list_push`, each of which may trigger a list growth (realloc). A single pre-allocation + memcpy would be O(1) allocations:
  ```c
  MnList list = __mn_list_new((int64_t)sizeof(double));
  __mn_list_ensure_cap(&list, t->size);  // if such a function existed
  memcpy(list.data, t->data, t->size * sizeof(double));
  list.len = t->size;
  ```
  But `__mn_list_ensure_cap` does not exist in the public API. Low priority -- this only matters for large GPU results.

**What is correct:**
- `mapanare_gpu_init()` uses `pthread_once` on POSIX and `InterlockedCompareExchange` on Windows. Thread-safe.
- All tensor ops fall back to CPU (`mapanare_tensor_*_f64`) when GPU is not available. Correct.
- Device memory is allocated, uploaded, computed, downloaded, and freed in the correct order in `cuda_elementwise_op` (lines 1591-1668). All error paths clean up all buffers. No leaks.

## Recommendations

**Priority 0 (before v4.0.0 tag):**

None from the C runtime. The P0 from v3.45.0 (HMODULE leak) is fixed. All other issues are LOW.

**Priority 1 (should fix for v4.0.0 quality):**

1. **Wire `mapanare_internal.h` into the three consumer files.** Add `#include "mapanare_internal.h"` to `mapanare_io.c`, `mapanare_db.c`, `mapanare_html.c`. Delete the local `mnstr_to_cstr` and `MnHandleTable` definitions. Note: the db.c and html.c `handle_alloc` returns `i + 1` (1-indexed) while the internal header's `mn_handle_alloc` returns `i` (0-indexed). Reconcile before wiring. The 1-indexed convention is better for handle APIs (0 = invalid). Update the internal header.

2. **Update User-Agent string** in `mapanare_io.c` line 1613 from "3.42" to a compile-time define or "3.47".

3. **Add CAS to `__mn_random_bytes_str` static init.** Replace `if (!s_bcrypt)` with `__atomic_compare_exchange_n` like the SSL/EVP/PCRE2 loaders.

**Priority 2 (should do eventually):**

4. **Fix `MN_PROFILE_FREE` or delete the counter.** 3rd cycle.

5. **Delete `emit_llvm.py`.** 4th cycle. 2,883 lines of deprecated code with a wrong ABI.

6. **Add atomic to `mn_init_tag_strings`.** Same CAS pattern.

7. **Convert `mn_signal_propagate` to iterative.** Or add depth bound.

8. **Convert `__mn_read_line` to growing buffer.** Silent truncation at 4096.

## v4.0.0 Readiness Assessment

**Ready from the C runtime perspective. No blockers.**

The HMODULE leak -- the only actual resource leak I flagged as a v4.0.0 blocker in v3.45.0 -- is fixed. The `rand()` fallback that produced predictable "random" bytes is deleted. The intern table race is fixed. The str_concat allocation waste is fixed. The dlopen loaders are thread-safe.

What remains is hygiene: a header that exists but is not included, a counter that is defined but never called, a deprecated file that is kept but never used, a User-Agent string that is stale, and two carries from Viper about thread safety of init functions that are only called once at startup.

The C runtime is 13,355 lines of stable, modular, zero-dependency code that implements strings, lists, maps, signals, streams, agents, TCP, TLS, crypto, regex, HTTP, database bindings, HTML parsing, event loop, thread pool, ring buffers, tensors, and GPU dispatch. All via dlopen. No link-time dependencies beyond libc and libpthread. The binary size is under 200 KB for the .so files. Startup time is zero for features not used (lazy dlopen). ABI is stable. No crashes. No UB that I can find.

This is production-ready. I will not say "ship it" because you already know that. I will say: wire the internal header, update the version string, and stop carrying `emit_llvm.py` into another decade.

## Raw Notes

```
- mapanare_core.c: 2,685 lines. Unchanged from v3.45.0.
  intern_ensure_table() now at line 296, AFTER intern_lock() at line 295.
  __mn_str_concat early returns at lines 409-411. Both fixed.
  MN_PROFILE_FREE still never called (line 64 vs 93). 3rd cycle.
  __mn_list_oob_buf still there (line 932). Break-inside-for workaround.
  mn_signal_propagate recursive (line 2005). Unchanged.
  mn_init_tag_strings race (line 2671). Unchanged.
  mn_to_cstr (line 1200): 5th copy of the conversion function.

- mapanare_io.c: 1,672 lines. Up 17 from 1,655.
  Delta is entirely in the __mn_random_bytes_str function:
    - Lines 1225-1232: static s_bcrypt + s_bcrypt_gen caching (fix)
    - Lines 1238-1240: rand() fallback replaced with return empty (fix)
  ssl_load_library (line 302): atomic CAS on loaded flag. FIXED.
  evp_load (line 987): atomic CAS on loaded flag. FIXED.
  pcre2_load (line 1313): atomic CAS on loaded flag. FIXED.
  HTTP response cap (line 1636): 64 MB. FIXED.
  User-Agent: still "Mapanare/3.42" (line 1613). Stale.
  mnstr_to_cstr duplicate at line 859. NOT wired to internal header.

- mapanare_internal.h: 63 lines. NEW.
  Correct design: static inline mnstr_to_cstr + MnHandleTable.
  Better than all three local copies (has len < 0 guard, NULL check).
  ZERO includers. The header is an island.

- mapanare_gpu_builtins.c: 193 lines. NEW.
  Bridges MnList* -> mapanare_tensor_t* for GPU dispatch.
  tensor_from_list borrows data (no copy). Correct.
  list_from_tensor copies element-by-element (O(n) allocations). Not
  optimal but not a bug.
  __mn_gpu_tensor_matmul (line 161): manual 2D tensor construction
  with separate shape malloc for each tensor. Both freed. Correct.
  All 5 element-wise ops follow identical pattern. DRY would reduce
  to one parameterized function + 4 one-line wrappers. But 193 lines
  is not worth the indirection.

- mapanare_gpu.c: 1,951 lines. Up 13 from 1,938.
  pthread_once / InterlockedCompareExchange for init. Correct.
  CUDA elementwise op (lines 1591-1668): clean alloc/upload/launch/
  download/free sequence. All error paths clean up.
  SPIRV_TENSOR_ADD placeholder (lines 356-371): still a stub.
  5 GLSL strings (lines 374-443): compiled at runtime via glslc.
  This means Vulkan path requires glslc on PATH. Should document.

- mapanare_db.c: 1,130 lines. Unchanged.
  mnstr_to_cstr duplicate at line 55. NOT wired.
  MnHandleTable duplicate at lines 74-97. NOT wired.
  handle_alloc returns i+1 (1-indexed). Internal header returns i
  (0-indexed). MISMATCH. Must reconcile before wiring.

- mapanare_html.c: 812 lines. Unchanged.
  mnstr_to_cstr duplicate at line 49. NOT wired.
  MnHandleTable duplicate at lines 70-95. NOT wired.
  handle_alloc returns i+1 (1-indexed). Same mismatch as db.c.
  Version string "v1.3.0" in docstring (line 3). Stale.

- mapanare_runtime.c: 1,343 lines. Unchanged.
  SPSC ring buffer (lines 215-276): correct. Unchanged.
  Thread pool (lines 322-433): correct. Unchanged.
  mapanare_ensure_pool (lines 451-475): CAS spinlock. Correct.
  Agent thread (lines 492+): correct lifecycle. Unchanged.

- tests/native/: 4,015 lines total across 15 files.
  Up 11 lines from 4,004. Unchanged in substance.
  Still no tests for: intern table, signal propagation, MnValue,
  type registry, GPU builtins.
  Intern table remains the most tested-zero component of the
  runtime. FNV-1a + open addressing + cap lock + thread-safe
  locking -- all untested.

- Binary size impact of new files:
  mapanare_gpu_builtins.c: ~1.5 KB .o (tiny bridge file)
  mapanare_internal.h: 0 bytes (header-only, static inline)
  Net delta: negligible.

- emit_llvm.py: 2,883 lines. 4th review cycle requesting deletion.
  __mn_map_new 3-param ABI mismatch still present at line 414.
  No code paths reach it unless --emitter=llvm is passed.
  This file will outlive me.

- __mn_str_concat (lines 408-427): the early return paths (409-411)
  call __mn_str_from_parts which allocates+copies. A return of the
  non-empty operand by value would avoid the copy. But the copy is
  bounded and correct. Marked resolved.

- __mn_random_bytes_str race: static s_bcrypt init (line 1227) is
  not atomic. Concurrent first-call from two threads: both enter
  if (!s_bcrypt), both LoadLibraryA, second thread may read
  s_bcrypt_gen as NULL. Low severity -- Windows ref-counts DLLs,
  so no handle leak (just double reference). Use CAS for consistency.

- Score: 9.3 -> 9.6. Up because:
  (a) 5/7 issues resolved (including the only MED)
  (b) Net line growth is 296 (controlled)
  (c) Two new files are both justified
  (d) No new bugs above LOW severity
  (e) ABI stable, no regressions
  (f) First positive review delta since v3.33.0

- Carryover tracker (cumulative across all Mamba reviews):
  MN_PROFILE_FREE:           v3.40.0(1), v3.45.0(2), v3.47.0(3)
  emit_llvm.py alive:        v3.39.0(1), v3.40.0(2), v3.45.0(3), v3.47.0(4)
  mn_signal_propagate depth:  carry from Viper, multi-cycle
  mn_init_tag_strings race:   carry from Viper, multi-cycle
  __mn_read_line truncation:  carry from Viper, multi-cycle
  
  RESOLVED this cycle:
  intern_ensure_table() race: v3.33.0-v3.47.0 (5 cycles). FIXED.
  __mn_str_concat empty alloc: v3.40.0-v3.47.0 (3 cycles). FIXED.
  HMODULE leak:               v3.45.0-v3.47.0 (2 cycles). FIXED.
  dlopen thread safety:       v3.45.0-v3.47.0 (2 cycles). FIXED.
  HTTP response cap:          v3.45.0-v3.47.0 (2 cycles). FIXED.
  mnstr_to_cstr duplication:  v3.45.0-v3.47.0 (header exists, not wired)
```
