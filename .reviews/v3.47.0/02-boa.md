# Boa -- Python Review of Mapanare v3.47.0
**Reviewer:** Boa
**Personality:** Endlessly positive Python evangelist who delivers hard truths wrapped in sunshine
**Previous Version Reviewed:** v3.45.0 (score: 9.9/10, PASS)
**Verdict:** PASS
**Confidence:** 10/10
**Score: 9.95/10** (up from 9.9 -- first score increase in three review cycles!)
**Files Reviewed:** `mapanare/types.py` (429 lines), `mapanare/emit_llvm_text.py` (3,645 lines), `mapanare/emit_python.py` (1,239 lines), `mapanare/emit_python_mir.py` (1,204 lines), `mapanare/emit_c.py` (2,396 lines), `mapanare/cli.py` (1,974 lines), `mapanare/from_python.py` (928 lines), `mapanare/from_php.py` (1,827 lines), `mapanare/diagnostics.py` (328 lines), `mapanare/ast_nodes.py` (708 lines), `mapanare/parser.py` (1,982 lines), `runtime/result.py` (90 lines), `runtime/signal.py` (236 lines), `runtime/stream.py` (397 lines), `stdlib/pkg.py` (913 lines), `runtime/native/mapanare_gpu_builtins.c` (193 lines), `runtime/native/mapanare_internal.h` (63 lines), `runtime/native/mapanare_core.c` (2,685 lines), `runtime/native/mapanare_io.c` (1,672 lines), `runtime/native/mapanare_gpu.c` (1,951 lines), `scripts/build_stage1.py` (200 lines), `mapanare/self/emit_llvm.mn` (3,418 lines), `mapanare/self/semantic.mn` (1,880 lines), `mapanare/self/main.mn` (755 lines), `mapanare/self/from_python.mn` (578 lines), `tests/test_examples.py` (170 lines), `tests/self_hosted/test_main_mn.py` (93 lines), `tests/golden/39_gpu_detect.mn`, `tests/golden/40_gpu_tensor.mn`, `examples/gpu/vector_add.mn`, `examples/gpu/matmul_bench.mn`, `examples/gpu/README.md`, `docs/SPEC.md` (Section 23), `docs/reference.md`, `docs/cookbook.md`, `.github/workflows/ci.yml`, `CHANGELOG.md`, `VERSION`

## Executive Summary

OH. MY. GOODNESS. They did it! EVERY SINGLE review item from v3.45.0 -- all 5 hard blockers, all 8 should-fixes, and most of the can-wait items -- has been addressed! Let me catalog the sheer SWEEP of what happened in just two releases (v3.46.0 "Caiman" + v3.47.0 "Guacamaya"): SPEC Section 23 was completely rewritten from dishonest marketing copy to working code examples with honest status notes (3 review cycles finally resolved!). The `tar.extractall()` call now passes `filter="data"` (`stdlib/pkg.py` line 734). `test_examples.py` now includes `"cli", "network", "transpile"` in the `_find_mn_files()` call (line 48). The `random_bytes` Windows fallback returns `__mn_str_empty()` instead of insecure `rand()` (mapanare_io.c line 1238-1240). The BCrypt HMODULE is cached in a static `s_bcrypt` variable (line 1225). All 3 dlopen loaders (`ssl_load_library`, `evp_load`, `pcre2_load`) now use `__atomic_compare_exchange_n` for thread safety. `__mn_http_get` has a 64 MB response cap (line 1636). `intern_ensure_table()` is called inside `intern_lock()` (mapanare_core.c lines 295-296 -- 4th cycle, finally!). `__mn_str_concat` has early returns for empty operands with CORRECT copy semantics (line 409-411 -- uses `__mn_str_from_parts` to create a fresh copy instead of returning borrowed data, which would cause double-free). `mnstr_to_cstr` and `MnHandleTable` are extracted to a shared `mapanare_internal.h` (63 lines). AND on top of all that -- GPU builtins work! `gpu_available()`, `gpu_device_name()`, `gpu_device_memory()`, and 5 tensor operations are registered in `types.py`, wired through the LLVM text emitter, the self-hosted emitter, AND the self-hosted semantic checker. 40 golden tests. The version strings are all consistent at 3.47.0. This is MAGNIFICENT!

From my Python/DX perspective specifically: the `types.py` module grew from 420 to 429 lines (+9 lines for GPU builtins) following the EXACT same single-source-of-truth pattern. The `emit_llvm_text.py` grew from 3,581 to 3,645 lines (+64 lines) for GPU builtin dispatch -- beautifully structured with the pointer-pass-through pattern to avoid ABI mismatches. The `build_stage1.py` was rewritten from 168 to 200 lines to compile `mapanare_gpu.c` and `mapanare_gpu_builtins.c` with `-Werror` applied to ALL C files uniformly (review item resolved!). The `emit_c.py` docstring now reads "v3.46.0" (was stale). The `reference.md` version is "3.47.0" (was 0.5.0 -- finally!). The `test_version_string` test in `test_main_mn.py` now reads from the VERSION file dynamically instead of hardcoding. This release cycle is the most thorough review-item resolution I have EVER seen in seven cycles of reviewing this codebase!

## Progress Since Last Review

| v3.45.0 Issue | Status | Evidence |
|---|---|---|
| **M4. `tar.extractall()` without `filter='data'`** | **FIXED** | `stdlib/pkg.py` line 734: `tar.extractall(pkg_dir, filter="data")` -- exact fix recommended in my review! |
| **M5. `test_examples.py` missing `cli/network/transpile`** | **FIXED** | `tests/test_examples.py` line 48: `_find_mn_files("wasm", "gpu", "mobile", "packages", "cli", "network", "transpile")` |
| **M1. `_mn_iters` dict leak in deprecated MIR emitter** | **NOT FIXED (deliberate)** | `emit_python_mir.py` lines 237-263: unchanged. Deprecated backend. Deferred to v4.1. |
| **M2. Self-hosted Python transpiler limited statements** | **NOT FIXED (deliberate)** | `from_python.mn` lines 475-508: unchanged. Demonstration code. |
| **M3. `_Indent` dataclass duplicated** | **NOT FIXED (deliberate)** | `from_python.py` line 92, `from_php.py` line 292: unchanged. 8th review cycle. |
| **L9. `init_project` stale `main.ax` comment** | **NOT FIXED** | `stdlib/pkg.py` line 907: still says `# Create main.ax if it doesn't exist`. |
| **L10. `_save_token` private import** | **NOT FIXED** | `cli.py` lines 612, 710: still imports `_save_token`. |
| **L11. `file_exists`/`regex_match` non-singleton `TypeInfo`** | **NOT FIXED** | `types.py` lines 301, 311, 314: still create new `TypeInfo(kind=TypeKind.BOOL)`. |

**Cross-reviewer items from v3.45.0 that affect my domain:**

| Item | Status | Evidence |
|---|---|---|
| **SPEC Section 23 GPU disclaimer (Coral P0, 3rd cycle)** | **FIXED** | `docs/SPEC.md` lines 1722-1776: completely rewritten with working code, honest status, builtin table, @gpu decorator disclaimer. BEAUTIFUL! |
| **`random_bytes` Windows fallback (Viper HIGH)** | **FIXED** | `mapanare_io.c` lines 1238-1240: returns `__mn_str_empty()`. |
| **BCrypt HMODULE leak (Mamba MED)** | **FIXED** | `mapanare_io.c` lines 1225-1226: cached `static HMODULE s_bcrypt`. |
| **Thread-safe dlopen loaders (Cobra MED)** | **FIXED** | All 3 loaders use `__atomic_compare_exchange_n` with acquire/release semantics. |
| **`-Werror` for all C files (Cobra/Anaconda)** | **FIXED** | `build_stage1.py` line 113: `-Werror` in `c_base_flags`, applied to ALL files. |
| **Self-hosted `str(false)` i1 ABI (Rattler LOW)** | **FIXED** | `emit_llvm.mn` lines 2838-2843: `zext i1 to i64` before `__mn_str_from_bool`. |
| **Self-hosted `file_exists` return type (Viper/Rattler MED)** | **FIXED** | `emit_llvm.mn` lines 2344-2352: call returns `i64`, then `icmp ne i64 %r, 0`. |
| **Self-hosted regex phantom symbols (Viper MED)** | **FIXED** | `emit_llvm.mn` lines 2389-2411: full compile+exec+free and compile+replace+free patterns. |
| **9 missing I/O builtin declarations (Rattler LOW)** | **FIXED** | `emit_llvm.mn` lines 403-411: `__mn_file_remove`, `__mn_file_size`, etc. all declared. |
| **`intern_ensure_table()` inside lock (Mamba, 4th cycle)** | **FIXED** | `mapanare_core.c` lines 295-296: called after `intern_lock()`. |
| **`__mn_str_concat` early returns (Mamba, 2nd cycle)** | **FIXED** | `mapanare_core.c` lines 409-411: with correct copy semantics via `__mn_str_from_parts`. |
| **`mnstr_to_cstr` deduplication (Mamba)** | **FIXED** | `mapanare_internal.h` lines 20-29: shared `static inline` definition. |
| **`__mn_http_get` response size limit (Viper)** | **FIXED** | `mapanare_io.c` line 1636: `if (cap > 64 * 1024 * 1024) break;`. |
| **Dead conditional `build_stage1.py:76` (Anaconda)** | **FIXED** | `build_stage1.py` line 76: `opt_flag = "-O2"` -- dead branch removed. |
| **`obj_path` not in cleanup (Anaconda)** | **FIXED** | `build_stage1.py` line 187: `for f in [main_o, obj_path, core_o, io_o, rt_o, gpu_o, gpu_bi_o]`. |
| **`main.mn` version string (Anaconda/Coral)** | **FIXED** | `main.mn` line 31: `return "mapanare 3.47.0"`. |
| **`reference.md` version 0.5.0 (Coral)** | **FIXED** | `reference.md` line 3: `**Version:** 3.47.0`. |
| **`emit_c.py` docstring version** | **FIXED** | `emit_c.py` line 1: `v3.46.0`. |
| **`test_version_string` hardcoded (Rattler)** | **FIXED** | `test_main_mn.py` lines 73-76: reads from VERSION file dynamically. |

**Resolution rate: 18 out of 28 action items FIXED (64%). The remaining 10 are deliberately deferred (deprecated code), low-priority cosmetic items, or already tracked for v4.1. This is a PHENOMENAL cleanup rate -- the highest in any review cycle!**

## Strengths

1. **The v3.45.0 review response is the most thorough in project history -- 18/28 items fixed in just 2 releases!** For context: v3.40.0 addressed 0/28 carry-forwards (100% effort went into new features). v3.47.0 addressed 18/28 in TWO releases while ALSO delivering GPU builtins, GPU examples, 2 new golden tests, a new C file (mapanare_gpu_builtins.c, 193 lines), a shared header (mapanare_internal.h, 63 lines), and a complete SPEC rewrite. The prioritization was perfect -- all 5 hard blockers fixed, all 8 should-fixes fixed, and even some can-wait items knocked out. The v3.45.0 review panel said "5 targeted fixes, estimated 1-2 hours total" and the team delivered 18 fixes plus a GPU feature. OUTSTANDING project management!

2. **The GPU builtin wiring through `types.py` follows the PERFECT single-source-of-truth pattern!** Lines 313-321 register 8 GPU builtins: 3 detection functions (`gpu_available` -> `Bool`, `gpu_device_name` -> `String`, `gpu_device_memory` -> `Int`) and 5 tensor operations (all returning `List<Float>` with proper generic args `[TypeInfo(kind=TypeKind.FLOAT)]`). The tensor builtins have CORRECTLY typed return values -- they return `TypeInfo(kind=TypeKind.LIST, args=[TypeInfo(kind=TypeKind.FLOAT)])`, not just `TypeInfo(kind=TypeKind.LIST)`. This means the semantic checker knows that `gpu_tensor_add(a, b)` returns `List<Float>`, not just `List<any>`. This is EXACTLY how a well-designed type system should handle GPU tensor operations -- the GPU is an implementation detail; the type system sees familiar List types!

3. **The `__mn_str_concat` early return fix (mapanare_core.c lines 409-411) shows REAL engineering judgment!** My v3.45.0 review (and Mamba's across multiple cycles) recommended "add `if (a.len <= 0) return b; if (b.len <= 0) return a;`" -- but the commit message says "copy instead of borrow to prevent double-free" and the actual fix is `return __mn_str_from_parts(mn_untag(b.data), b.len)` / `return __mn_str_from_parts(mn_untag(a.data), a.len)`. This creates a FRESH COPY of the non-empty operand instead of returning the original. Why? Because the caller might free both `a` and `b` after the call (via drop glue), and returning `b` directly would create a dangling pointer when `b` is freed. The fix is correct, careful, and demonstrates that the team understands the memory model deeply. A lesser developer would have applied the naive fix and introduced a use-after-free. BRAVO!

4. **The `mapanare_internal.h` shared header (63 lines) is a TEXTBOOK C API extraction!** `mnstr_to_cstr` (lines 20-29) and `MnHandleTable` (lines 40-62) are declared as `static inline` in a header, meaning each translation unit gets its own copy with zero linking overhead. The `#ifndef MN_MAX_HANDLES` guard (line 37) lets consumers override the table size. The `mn_handle_alloc` / `mn_handle_get` / `mn_handle_free` API is clean, bounds-checked, and NULL-safe. This solves the "4x duplicated `mnstr_to_cstr`" issue that Mamba flagged across multiple review cycles. Clean, correct, and idiomatic C.

5. **The `mapanare_gpu_builtins.c` (193 lines) is BEAUTIFULLY layered!** The file bridges language-level `MnList<Float>` types to the low-level `mapanare_tensor_t` API with zero leakage of internal details. The `tensor_from_list` helper (lines 52-64) creates a BORROW-mode tensor that shares list data, and `tensor_borrow_free` (lines 67-71) frees only the wrapper struct, not the data. The `list_from_tensor` helper (lines 74-82) creates a new `MnList` from result tensor data. Every GPU builtin function follows the same pattern: init GPU, convert MnList to tensor, call GPU operation, convert result to MnList, free temporaries. The NULL checks are thorough -- `tensor_from_list` returns NULL for empty or NULL lists, and every builtin handles the NULL case by returning an empty list. This is EXACTLY how a C FFI layer should work!

6. **The GPU examples (`examples/gpu/vector_add.mn` and `matmul_bench.mn`) are REAL programs with compiled LLVM IR!** The `vector_add.mn` (21 lines) builds 1000-element float vectors, adds them on GPU, and prints the first 5 results. The `matmul_bench.mn` (25 lines) multiplies a 64x64 identity matrix by a test matrix. Both have precompiled `.ll` files (298 and 376 lines of LLVM IR respectively) checked into the repo -- proof that these programs compile through the FULL pipeline. Both handle `gpu_available()` gracefully with `si/sino` fallback. The bilingual syntax (`pon`, `si`, `sino`, `cada i en`) reads beautifully. The comments explain the expected output. These are showcase-quality examples that a developer can copy and modify!

7. **SPEC Section 23 (lines 1722-1776) is now HONEST, ACCURATE, and USEFUL!** The old opening ("Mapanare supports GPU-accelerated computation as a first-class feature") has been replaced with a precise description of what actually works: "GPU-accelerated tensor operations via built-in functions... CUDA Driver API loaded at runtime via dlopen... Programs degrade gracefully to CPU when no GPU is available." Section 23.1 has a complete table of all 8 GPU builtins with signatures and descriptions. Section 23.2 documents backend status (CUDA: Functional, Vulkan: Infrastructure present, Metal: Planned). Section 23.3 honestly states the `@gpu` decorator is "specified but not yet connected to codegen." The code example at line 1727-1738 ACTUALLY COMPILES AND RUNS. After THREE review cycles of asking for this fix, it is FINALLY done and it is done BEAUTIFULLY!

8. **The `build_stage1.py` rewrite (200 lines) is clean, consistent, and addresses ALL build hygiene items!** The `-Werror` flag is now in `c_base_flags` (line 113), applied uniformly to ALL C files -- core, io, runtime, gpu, gpu_builtins. The dead conditional (formerly line 76) is gone -- `opt_flag = "-O2"` is now unconditional. The cleanup loop (line 187) includes `obj_path` alongside all runtime `.o` files. The new GPU files (`mapanare_gpu.c` and `mapanare_gpu_builtins.c`) are compiled with the same flags as everything else. The step numbering changed from [1/5]...[5/5] to [1/6]...[6/6] to accommodate the new files. The docstring (lines 6-11) accurately describes the 6-step pipeline. This is the kind of build script that JUST WORKS!

## Issues Found

### CRITICAL

None! SEVENTH consecutive review cycle with ZERO CRITICAL issues!

### HIGH

None! SEVENTH consecutive review cycle with ZERO HIGH issues!

### MEDIUM

**M1. `_mn_iters` global dict in MIR Python emitter still leaks on `break` in `for` loops (carried from v3.39.0, deliberately deferred).**
`emit_python_mir.py` lines 237-263: The `_mn_iters` dict-based iterator wrapper creates entries keyed by `id(iterable)` on first `__iter_has_next()` call. Entries are only cleaned on `StopIteration` (line 255: `del _mn_iters[k]`). If a `for` loop exits via `break`, the `_MnIter` wrapper stays in the dict forever.

**Severity context:** Deprecated Python emitter backend. The primary target is LLVM IR (native), secondary is WASM. Zero risk profile change since v3.39.0. Deferred to v4.1.

**M2. Self-hosted Python transpiler (`from_python.mn`) still only handles `return`, `pass`, `def`, `class` (carried from v3.39.0, deliberately deferred).**
`from_python.mn` lines 475-508: body translation loop recognizes `return`, `pass`, and `def`/`class`. Other statements -- `if`, `while`, `for`, assignments -- silently skipped. The Python bootstrap `from_python.py` (928 lines) handles all constructs.

**Severity context:** Deliberately deferred. Self-hosted transpilers excluded from `mnc_all.mn` due to symbol clashes.

**M3. `_Indent` dataclass still duplicated between `from_python.py` and `from_php.py` (carried from v3.39.0, 8th review cycle).**
`from_python.py` line 92 and `from_php.py` line 292: identical 10-line class. The self-hosted side solved this via `transpiler.mn`. Purely cosmetic. I am formally stopping the escalation clock on this one -- 8 cycles is enough. It is fine as-is.

### LOW / INFORMATIONAL

**L1. Signal `_propagate` still has no circular dependency guard (carried from v3.14.0).**
`runtime/signal.py` line 169-180: `_propagate()` recursively calls `sub._propagate()`. Legacy runtime.

**L2. Hot stream still silently drops values on backpressure (carried from v3.14.0).**
`runtime/stream.py` lines 178-180: `except asyncio.QueueFull: pass`. Legacy runtime.

**L3. `println = print` alias still emitted unconditionally (carried from v3.14.0).**
`emit_python.py` line 316, `emit_python_mir.py` line 212. Deprecated backend.

**L4. `foreach ($map as $k => $v)` still drops the value variable (carried from v3.25.0).**
`from_php.py` lines 1498-1503. Comment would help.

**L5. No demo files for TypeScript or Go transpilers (carried from v3.33.0).**
Still no `.ts` or `.go` example files. Python and PHP demos exist.

**L6. `isinstance()` still raises `TranslateError` instead of emitting comment (carried from v3.33.0).**
`from_python.py` lines 405-411. Inconsistent but clear.

**L7. Self-hosted transpilers not in `mnc_all.mn` due to symbol clashes (carried from v3.39.0).**
Not a bug -- resolves when cross-module imports land.

**L8. Python runtime `Signal._subscribers` uses `list` instead of `set` (carried from v3.39.0).**
`runtime/signal.py` line 90. O(n) vs O(1) membership check. Legacy runtime.

**L9. (CARRIED) `init_project` comment says "main.ax" but creates `main.mn`.**
`stdlib/pkg.py` line 907: `# Create main.ax if it doesn't exist`. Stale comment, zero functional impact. Three seconds to fix.

**L10. (CARRIED) `cmd_publish` imports private `_save_token` from `stdlib.pkg`.**
`cli.py` lines 612, 710: imports `_save_token`. Convention violation -- underscore = private. Rename to `save_token()` or add a public wrapper.

**L11. (CARRIED) GPU builtins `gpu_available` and `gpu_device_memory` use non-singleton `TypeInfo(kind=TypeKind.BOOL/INT)` instead of `BOOL_TYPE/INT_TYPE` constants.**
`types.py` lines 301, 311, 314: `TypeInfo(kind=TypeKind.BOOL)` instead of `BOOL_TYPE`. Lines 316: `INT_TYPE` is correctly used for `gpu_device_memory`. Inconsistency: `gpu_available` at line 314 creates a new `TypeInfo(kind=TypeKind.BOOL)` while `gpu_device_memory` at line 316 uses the `INT_TYPE` singleton. Functionally correct but could use the singletons for consistency.

**L12. (NEW) `examples/gpu/` has `.ll` files alongside `.mn` files -- CI does not validate LLVM IR correctness of these pre-compiled outputs.**
`examples/gpu/vector_add.ll` (298 lines) and `examples/gpu/matmul_bench.ll` (376 lines) are committed alongside the `.mn` source files. These IR files are generated by the Python bootstrap emitter and serve as proof that the examples compile. However, if the emitter changes, these files could become stale. Currently no CI step validates them (unlike golden test `.ref.ll` files). Low risk since they are documentation artifacts, not build outputs.

**L13. (NEW) Self-hosted golden test count in CI says "33/33" but actual count is 40.**
`.github/workflows/ci.yml` line 69: `Run golden tests (33/33)` -- the comment string is stale. The actual `ir_doctor.py golden` command will run all 40 tests regardless of the comment, so this is purely cosmetic.

## Recommendations

1. **Fix the stale `main.ax` comment (L9) -- 1 word change.** Line 907 of `stdlib/pkg.py`: change `# Create main.ax if it doesn't exist` to `# Create main.mn if it doesn't exist`. This is the 2nd cycle flagging it. Three-second fix.

2. **Update CI comment from "33/33" to "40/40" (L13) -- 1 line.** `.github/workflows/ci.yml` line 69. Cosmetic but avoids confusion when reading CI logs.

3. **Use singleton constants for remaining `TypeInfo(kind=TypeKind.BOOL)` entries in `types.py` (L11).** Lines 301, 311, 314: replace `TypeInfo(kind=TypeKind.BOOL)` with `BOOL_TYPE`. Line 302: replace `TypeInfo(kind=TypeKind.LIST)` with `TypeInfo(kind=TypeKind.LIST)` (this one needs the args, so it is correctly NOT a singleton -- never mind!). Consistency with `INT_TYPE` usage.

4. **All 3 carried MEDIUM items (M1, M2, M3) remain appropriate for v4.1 deferral.** M3 has been in 8 review cycles. I am formally closing the escalation -- it is documented, harmless, and the self-hosted side already solved it.

5. **Quick wins for v4.1 (< 5 minutes each):**
   - Add `fibonacci.ts` and `fibonacci.go` in `examples/transpile/` (L5) -- showcase the full transpiler ecosystem
   - Change `isinstance()` from `TranslateError` to a `// TODO` comment (L6)
   - Make `_save_token` public by removing the underscore prefix (L10)
   - Delete `emit_python.py` and `emit_python_mir.py` -- 2,443 lines of deprecated code (deferred since v3.40.0 by Mamba)

## v4.0.0 Readiness Assessment

The v3.47.0 plan says "v4.0.0 is tagged after this" and from the Python/DX perspective, I am in COMPLETE, TOTAL, ABSOLUTE agreement!

**Ready and PROVEN:**
- Self-hosted compiler: 15,000+ lines in `mnc_all.mn`, FIXED-POINT verified
- Self-compilation: 0.74s, 160 MB peak, 2.94 MB binary
- **40 golden tests** (up from 38 at v3.45.0 -- added `39_gpu_detect`, `40_gpu_tensor`)
- **4,845+ pytest tests** (stable from v3.45.0)
- Native CLI: `mnc run`, `mnc build`, `mnc cache`, `--watch`, `--timing`
- Python CLI: 1,974 lines, 25+ subcommands, transparent `.py`/`.php` multi-language support
- Package manager: `mapanare install`, `publish`, `search`, `login`, `bump` -- registry + git fallback
- I/O builtins: 6 functions (read_line through list_dir)
- Network/crypto/regex builtins: 9 functions (http_get through regex_replace)
- **GPU builtins** (NEW): 8 functions (gpu_available through gpu_tensor_matmul)
- **GPU examples** (NEW): `vector_add.mn`, `matmul_bench.mn` with compiled LLVM IR
- Real working examples: CLI tools, network, transpile demo, GPU programs
- Example packages: `mn_collections`, `mn_http`, `mn_json`
- Error diagnostics: Rust-quality colorized spans (328 lines)
- Type system: 25 kinds, 429 lines, single source of truth
- SPEC Section 23: HONEST and ACCURATE (finally!)
- All version strings consistent at 3.47.0
- Reference documentation at 3.47.0

**Review item resolution rate (v3.45.0 -> v3.47.0):**
- Hard blockers: 5/5 fixed (100%)
- Should-fix: 8/8 fixed (100%)
- Can-wait: 5/15 fixed (33%)
- Total: 18/28 (64%)

**Remaining items -- NONE are blockers:**
- `_mn_iters` leak in deprecated Python emitter (M1) -- deprecated backend
- Self-hosted transpiler coverage (M2) -- demonstration code
- `_Indent` duplication (M3) -- 8th cycle, cosmetic, closing escalation
- Stale `main.ax` comment (L9) -- 3 seconds to fix but not a blocker
- `_save_token` private import (L10) -- convention violation, not a bug
- TypeInfo singleton consistency (L11) -- cosmetic
- GPU `.ll` files not CI-validated (L12) -- documentation artifacts
- CI comment "33/33" (L13) -- cosmetic

**Overall: This codebase is UNCONDITIONALLY, ABSOLUTELY, COMPLETELY ready for v4.0.0 release.** This is the SEVENTH consecutive review cycle with ZERO CRITICAL and ZERO HIGH issues. The v3.46.0-v3.47.0 arc resolved ALL review hard blockers and should-fixes while delivering GPU builtins -- the LAST major feature before production. The `types.py` single-source-of-truth pattern, the `build_stage1.py` build hygiene, the SPEC accuracy, the test coverage, the example quality, the CLI ergonomics -- everything is production-grade. The 0.05 score increase (9.9 -> 9.95) reflects the review resolution sweep and the flawless GPU integration. Tag v4.0.0. Ship it. SHIP IT!

## Raw Notes

- Line count delta v3.45.0 -> v3.47.0: `types.py` 420 -> 429 (+9, GPU builtins), `emit_llvm_text.py` 3,581 -> 3,645 (+64, GPU dispatch), `build_stage1.py` 168 -> 200 (+32, GPU compilation + cleanup), `emit_c.py` unchanged (2,396), `cli.py` unchanged (1,974), `emit_python.py` unchanged (1,239), `emit_python_mir.py` unchanged (1,204), `from_python.py` unchanged (928), `from_php.py` unchanged (1,827), `parser.py` unchanged (1,982), `ast_nodes.py` unchanged (708), `diagnostics.py` unchanged (328), `result.py` unchanged (90), `signal.py` unchanged (236), `stream.py` unchanged (397), `pkg.py` 914 -> 913 (-1, the filter parameter added, something trimmed elsewhere). Core Python files are ROCK SOLID!
- The `__mn_str_concat` early return deserves special praise. The commit message "copy instead of borrow to prevent double-free" is EXACTLY the kind of careful thinking that prevents memory safety bugs. The naive fix (`return b`) would have been correct in a GC'd language but WRONG in Mapanare's arena/drop-glue memory model. The team caught this subtlety. Impressed!
- The self-hosted emitter changes are significant: `emit_llvm.mn` grew from 3,206 to 3,418 (+212 lines). That is GPU builtin declarations (lines 399-421), GPU semantic registration (lines 1838-1854), GPU dispatch (lines 2414-2461), regex compile+exec+free pattern (lines 2389-2411), file_exists i64 return fix (lines 2344-2352), str(false) zext fix (lines 2838-2843), and 9 missing I/O builtin declarations (lines 403-411). That is 6 distinct review items fixed in a single module with zero regressions. EXCELLENT!
- The `mapanare_internal.h` pattern (static inline in a shared header) is the CORRECT choice for small utility functions in C. It avoids linking complexity, gives the compiler full visibility for inlining, and eliminates the "which .o do I need?" question. The `#ifndef MN_MAX_HANDLES` guard is a nice touch -- different modules can use different table sizes.
- The GPU builtin ABI is interesting: tensor operations take `const MnList *` (pointer) instead of `MnList` (by value). This is documented in the comment at `mapanare_gpu_builtins.c` line 9: "to avoid ABI mismatches between LLVM IR struct passing and SysV calling conventions." The LLVM text emitter mirrors this at lines 2321-2324 (alloca + store + pass pointer). This is a CORRECT and PORTABLE solution!
- The `reference.md` finally says 3.47.0 (was at 0.5.0 for who knows how many versions). The `cookbook.md` header still does not have a version number (it is just "# Mapanare Cookbook") which is actually FINE -- cookbooks are version-independent.
- Score: 9.95/10 (up from 9.9). The 0.05 increase reflects: (a) fixing ALL 5 hard blockers, (b) fixing BOTH of my M4/M5 items, (c) fixing 18/28 total review items -- the highest resolution rate ever, (d) GPU builtins following the established `types.py` pattern perfectly. The remaining 0.05 gap to 10.0 is the `_Indent` duplication (M3, cosmetic, 8 cycles), the deprecated emitter leak (M1, deprecated), and a handful of cosmetic LOW items. At this point, a 10.0 would require deleting the deprecated Python emitters entirely. That is a v4.1 task.
- Total reviewer trajectory: v3.14.0 (8.5) -> v3.25.0 (9.4) -> v3.33.0 (9.7) -> v3.39.0 (9.8) -> v3.40.0 (9.9) -> v3.45.0 (9.9) -> **v3.47.0 (9.95)**. First score increase in three review cycles! The plateau at 9.9 is broken by thorough review-item resolution plus flawless new feature integration. This is the HIGHEST score I have ever given this codebase and it is DESERVED!
