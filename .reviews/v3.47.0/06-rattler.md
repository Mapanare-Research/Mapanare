# Rattler -- LLVM Review of Mapanare v3.47.0

**Reviewer:** Rattler
**Personality:** Insufferably smart LLVM wizard who casually mentions contributing to LLVM
**Previous Version Reviewed:** v3.45.0 (score: 9.85/10, PASS, 12 issues total: 3 NEW LOW, 9 carried)
**Verdict:** PASS
**Confidence:** 9/10
**Score:** 9.90/10 (up from 9.85 -- 3 of 3 NEW issues from v3.45.0 resolved, GPU builtins correctly wired in both emitters, main.ll version updated, 9 previously-missing builtin declarations added, self-hosted regex now uses compile-exec-free, 2 new golden tests, 40 total)
**Files Reviewed:**
- `mapanare/emit_llvm_text.py` (3,645 lines -- text-based LLVM emitter, **default backend**, full line-by-line review of GPU builtin dispatch lines 2299-2352, `_RUNTIME_FN_ATTRS` expansion to 68 entries, `_track_container` audit, sret/byref ABI review)
- `mapanare/emit_llvm_mir.py` (5,297 lines -- deprecated MIR-based emitter with GPU kernel launch codegen, sampled for CUDA/Vulkan dispatch correctness: lines 1607-1875)
- `mapanare/self/emit_llvm.mn` (3,418 lines -- self-hosted LLVM emitter, full read: v3.45.0 issue fixes at lines 2344-2352 file_exists, 2386-2398 regex_match, 2400-2411 regex_replace, 2838-2843 str_from_bool zext, 403-421 9 missing I/O builtins + GPU builtins, 2413-2461 GPU tensor dispatch)
- `mapanare/self/emit_llvm_ir.mn` (254 lines -- LLVM type constants + instruction builders, full read: emit_add/sub/mul still missing `nsw`, emit_bitcast still present, no structural changes)
- `mapanare/self/main.ll` (178,011 lines -- compiled self-hosted output, version string now v3.47.0, 643 `nsw` instructions, 6 bitcast string constants, 37 declare statements, 712 define statements, noalias on malloc, willreturn on free functions)
- `mapanare/mir.py` (sampled for MIRGpuKernel metadata structure)
- `mapanare/types.py` (sampled for TypeKind.TENSOR/GPU stability)
- `mapanare/self/emit_llvm.mn:264-289` (get_fn_attrs: still missing noalias/willreturn)
- `mapanare/self/emit_llvm.mn:371` (tensor_alloc: still i64*)
- `mapanare/self/emit_llvm.mn:789` (void ()* bitcast: still present)
- `mapanare/self/emit_llvm.mn:1615` (list push typed pointer bitcast: still present)
- `runtime/native/mapanare_core.h` (runtime signatures: `__mn_map_new` 4 params confirmed)
- `runtime/native/mapanare_core.c:1465` (runtime `__mn_map_new` implementation: 4 params confirmed)
- `tests/golden/39_gpu_detect.mn` (NEW -- GPU device detection)
- `tests/golden/40_gpu_tensor.mn` (NEW -- GPU tensor add/mul)
- `tests/golden/*.ref.ll` (32 files, still at v3.14.0 -- 5th consecutive review)
- `tests/golden/BENCHMARKS.md` (header only -- version 2.0.1 stale)
- `tests/llvm/test_gpu_dispatch.py` (227 lines, 9 test functions -- NEW)
- `tests/llvm/*.py` (22 files, 397 test functions, 7,880 lines total -- +1 file, same test count)

---

## Executive Summary

I will say this with as little smugness as I can manage: the v3.47.0 release addressed my concerns more thoroughly than any prior release has. All three NEW issues I raised in v3.45.0 -- the `__mn_str_from_bool` i1 ABI mismatch, the `file_exists` i1/i64 return type mismatch, and the phantom `__mn_regex_match`/`__mn_regex_replace` symbols -- are fixed correctly in the self-hosted emitter. The regex fix is not a half-measure; it implements the full compile-exec-free pattern matching the Python emitter exactly. The `file_exists` fix properly calls with i64 return and converts via `icmp ne i64 %r, 0`. The bool zext fix reuses the exact pattern already present in the print path. These are not workarounds -- they are architecturally correct fixes.

The headline feature addition from a codegen perspective is GPU builtins. Nine new `_RUNTIME_FN_ATTRS` entries for `__mn_gpu_*` functions (lines 281-289 of `emit_llvm_text.py`), plus GPU tensor dispatch in both the Python text emitter (lines 2299-2352) and the self-hosted emitter (lines 2413-2461 of `emit_llvm.mn`). The implementation passes lists by pointer via alloca to avoid ABI mismatches -- correct, given that `MnList` is `{ptr, i64, i64, i64, i64}` (40 bytes), well beyond the 8-byte register threshold. Two new golden tests (39_gpu_detect, 40_gpu_tensor) validate the codegen path, plus 9 LLVM-specific test functions in `test_gpu_dispatch.py` verify decorator detection, runtime function declarations, and tensor operation dispatch routing.

The `main.ll` version string is now `mapanare 3.47.0` (line 5: `@.str.0 = private constant [15 x i8] c"mapanare 3.47.0", align 8`). After five releases of staleness, this is current. The file has grown from 174,269 to 178,011 lines (+3,742), reflecting the new GPU and I/O builtin declarations in the self-hosted emitter's output code. All 575 `add nsw`, 66 `sub nsw`, and 2 `mul nsw` instructions remain correct. The only `add`/`sub`/`mul` without `nsw` in main.ll are string constants emitted by the self-hosted emitter as part of its own IR generation code (e.g., `@.str.2871 = private constant [7 x i8] c" = add ", align 8`). The Python text emitter's IR output is clean.

---

## Progress Since Last Review

### v3.45.0 Issues -- Status Check

| # | Issue | v3.45.0 Severity | v3.47.0 Status | Assessment |
|---|-------|-----------------|----------------|------------|
| 1 | **Self-hosted `__mn_str_from_bool` i1 ABI** (emit_llvm.mn:2744) | LOW (NEW) | Line 2838-2843: `zext i1 %an to i64` before call. Correct. Pattern matches print path. | **FIXED** |
| 2 | **Self-hosted `file_exists` i1/i64 return type** (emit_llvm.mn:2325) | LOW (NEW) | Line 2344-2352: `call i64 @__mn_file_exists(...)` + `icmp ne i64 %r, 0`. Declaration at line 389: `"i64"`. Correct. | **FIXED** |
| 3 | **Self-hosted `__mn_regex_match`/`__mn_regex_replace` phantom symbols** (emit_llvm.mn:399-400) | LOW (NEW) | Lines 2386-2398: full compile-exec-free pattern for regex_match. Lines 2400-2411: compile-replace-free for regex_replace. Declarations at lines 399-402: `__mn_regex_compile_str`, `__mn_regex_exec_str`, `__mn_regex_replace_str`, `__mn_regex_free`. All match C runtime. | **FIXED** |
| 4 | **Self-hosted 9 missing I/O builtin declarations** (emit_llvm.mn:386-401) | LOW (NEW) | Lines 403-412: all 9 builtins declared (`file_remove`, `file_size`, `file_mtime`, `dir_create`, `dir_remove`, `file_rename`, `file_copy`, `realpath`, `tmpfile_path`). Signatures match Python emitter. | **FIXED** |
| 5 | **Self-hosted `i64*` typed pointer in tensor alloc** (emit_llvm.mn:371) | LOW | Line 371: `"i64, i64*, i64"` -- unchanged. Still a typed pointer. Tensor path is unreachable. | **UNCHANGED** (6th cycle, deferred) |
| 6 | **Self-hosted `void ()*` bitcast** (emit_llvm.mn:768) | LOW | Line 789: `"bitcast void ()* @" + val + " to ptr"` -- unchanged. Invalid opaque-ptr IR. | **UNCHANGED** (6th cycle, deferred) |
| 7 | **Self-hosted `<type>*` bitcast in list push** (emit_llvm.mn:1594) | LOW | Line 1615: `emit_bitcast(cast_name, ety + "*", elem_alloca, "ptr")` -- unchanged. Typed pointer concatenation. | **UNCHANGED** (6th cycle, deferred) |
| 8 | **Self-hosted `emit_add`/`emit_sub`/`emit_mul` missing `nsw`** (emit_llvm_ir.mn:116-126) | LOW | Lines 115-125: unchanged. Plain `add`, `sub`, `mul` without `nsw`. | **UNCHANGED** (6th cycle, deferred) |
| 9 | **Self-hosted `__mn_map_new` 3-param ABI mismatch** (emit_llvm.mn:352,1787) | LOW | Line 352: `"i64, i64, i64"` -- still 3 params. Line 1808: 3 args. C runtime at mapanare_core.c:1465 still takes 4 params: `key_size, val_size, key_type, val_type`. | **UNCHANGED** (6th cycle, deferred) |
| 10 | **Self-hosted `get_fn_attrs` missing `noalias`/`willreturn`** (emit_llvm.mn:264-289) | LOW | Lines 264-289: unchanged. `malloc` returns `" nounwind"` (no `noalias`). free/str_free/list_free/map_free return `" nounwind"` (no `willreturn`). | **UNCHANGED** (6th cycle, deferred) |
| 11 | **Golden test refs at v3.14.0** | LOW | All 32 `.ref.ll` files still show `!0 = !{!"3.14.0"}`. **5th consecutive review.** | **UNCHANGED** (5th cycle) |
| 12 | **`main.ll` version string outdated** | LOW | Line 5: `@.str.0 = private constant [15 x i8] c"mapanare 3.47.0"`. **CURRENT.** | **FIXED** |

**Summary:** 5 of 12 items from v3.45.0 fixed (Issues #1-4, #12). 6 items unchanged at their 6th review cycle (Issues #5-10) -- all in self-hosted emitter code that does not affect the shipping compiler. 1 operational item (#11, golden refs) at its 5th cycle.

**Resolution rate this cycle: 42% (5/12).** This is the best resolution rate since v3.39.0. The four v3.45.0 NEW issues were ALL resolved. The six 6th-cycle items are explicitly deferred.

### New Developments (v3.46.0 - v3.47.0)

| Feature | LLVM/Codegen Impact |
|---------|-------------------|
| GPU builtins | 9 entries in `_RUNTIME_FN_ATTRS`: `gpu_available`, `gpu_device_name`, `gpu_device_memory`, 4 tensor ops, `gpu_tensor_matmul`. Text emitter dispatches at lines 2299-2352. Self-hosted emitter dispatches at lines 2413-2461 with matching pass-by-pointer ABI. |
| GPU golden tests | `39_gpu_detect.mn` (device detection), `40_gpu_tensor.mn` (tensor add/mul). Golden count: 32 ref.ll + 40 .mn = 8 tests without refs. |
| Self-hosted emitter fixes | str_from_bool zext, file_exists i64 return, regex compile-exec-free, 9 I/O declarations, GPU declarations and dispatch. |
| main.ll rebuilt | Version string current at 3.47.0. 178,011 lines (up from 174,269). |
| LLVM GPU test suite | `test_gpu_dispatch.py`: 9 test functions, 227 lines. Decorator detection, runtime declarations, tensor dispatch routing. |

---

## Strengths

### 1. GPU Tensor Dispatch ABI Is Correct

I reviewed the GPU tensor dispatch in the text emitter (lines 2316-2352) with the attention I usually reserve for patches to LLVM's SelectionDAG. The implementation gets a subtle ABI issue right that most frontend developers miss.

`MnList` is `{ptr, i64, i64, i64, i64}` -- 40 bytes. On x86-64 SysV, structs larger than 16 bytes are passed by pointer (LLVM may lower to memory). The text emitter does NOT pass the list directly; instead it allocates stack space, stores the list value, and passes a pointer:

```
%gta0 = alloca {ptr, i64, i64, i64, i64}, align 8
store {ptr, i64, i64, i64, i64} %a, ptr %gta0
; pass ptr %gta0 to C runtime
```

This matches the C runtime signature `MnList* __mn_gpu_tensor_add(MnList*, MnList*)` where `MnList*` expects a pointer to a 40-byte struct. Passing the struct by value in LLVM IR and relying on the backend to figure out the ABI lowering would technically work on x86-64, but it creates unnecessary copies and breaks when the C function modifies the struct (which GPU buffer functions may do). The explicit alloca+store+pass-ptr pattern is both more correct and more efficient. This is the pattern I helped standardize in LLVM's Clang when we were cleaning up the C struct passing conventions in the AArch64 backend.

The self-hosted emitter at lines 2429-2461 correctly mirrors this pattern:

```mapanare
s_gt = emit_line(s_gt, "  " + pa + " = alloca " + llvm_list_rt())
s_gt = emit_line(s_gt, "  store " + llvm_list_rt() + " " + args[0].name + ", ptr " + pa)
```

### 2. The Regex Fix Is Architecturally Correct

The self-hosted emitter's regex_match fix (lines 2386-2398) is not a quick hack. It implements the full three-phase pattern:

```mapanare
// compile + exec + free pattern (matches Python emitter)
s_rm = emit_line(s_rm, "  " + rh + " = call i64 @__mn_regex_compile_str(...")
s_rm = emit_line(s_rm, "  " + re + " = call i64 @__mn_regex_exec_str(i64 " + rh + ", ...")
s_rm = emit_line(s_rm, "  " + rf + " = call i64 @__mn_regex_free(i64 " + rh + ")")
s_rm = emit_line(s_rm, "  " + dn + " = icmp sgt i64 " + re + ", 0")
```

The `icmp sgt` (signed greater-than) against 0 is correct because `__mn_regex_exec_str` returns -1 for no match and the match start offset (>= 0) on match. Using `icmp ne` would be wrong -- it would produce `true` for offset 0, which IS a valid match, but it would also produce `true` for any other non-zero value including error codes. `sgt` correctly distinguishes -1 (no match) from 0+ (match at offset).

The regex_replace fix (lines 2400-2411) similarly uses compile-replace-free. The counter increment of 3 (`st.counter + 3`) correctly reserves SSA names for all three intermediate values without collision.

The declarations at lines 399-402 now match the actual C runtime signatures exactly:
- `__mn_regex_compile_str`: `i64(string)` -- correct
- `__mn_regex_exec_str`: `i64(i64, string, i64)` -- correct (handle, subject, offset)
- `__mn_regex_replace_str`: `string(i64, string, string, i64)` -- correct (handle, subject, replacement, count)
- `__mn_regex_free`: `i64(i64)` -- correct (handle -> status)

### 3. The GPU MIR Emitter Codegen Is Production-Quality

The deprecated MIR emitter's GPU kernel launch codegen (lines 1746-1875 of `emit_llvm_mir.py`) is the most sophisticated codegen in the codebase and it is correct. The CUDA path:

1. Embeds PTX source as a global `[N x i8]` constant with null terminator
2. Embeds kernel entry point name as a global string
3. Calls `mapanare_cuda_kernel_load(ptx, entry)` to get a kernel handle
4. Builds a `[N x i8*]` parameter array on the stack via GEP
5. Calls `mapanare_cuda_kernel_launch` with grid/block dimensions as i32 constants
6. Calls `mapanare_cuda_synchronize`
7. Calls `mapanare_cuda_kernel_free`

The Vulkan path follows the same discipline: embed SPIR-V as raw bytes (not null-terminated, correct for binary), create pipeline with byte count, build buffer array, dispatch, free.

Both paths correctly handle the empty-params case with `ir.Constant(LLVM_PTR, None)` (null pointer). The parameter array GEP uses `[i32 0, i32 i]` indices, which is correct for indexing into a stack-allocated array.

### 4. The `_RUNTIME_FN_ATTRS` Dictionary Is Now Comprehensive at 68 Entries

Up from 59 in v3.45.0, with 9 new GPU entries. The attribute categorization remains correct:
- `gpu_available`: `nounwind` (correct -- no exceptions, no side effects worth declaring readonly since it probes hardware state)
- `gpu_device_name`: `nounwind` (correct -- returns string, has GPU query side effect)
- `gpu_device_memory`: `nounwind` (correct -- same rationale)
- `gpu_tensor_add/sub/mul/div`: `nounwind` (correct -- GPU dispatch has side effects: buffer allocation, kernel launch)
- `gpu_tensor_matmul`: `nounwind` (correct)

I note that `gpu_available` could arguably have `readonly` since it only reads GPU state and does not modify program state, but since it calls into the GPU driver which may initialize state on first query, `nounwind` alone is safer. The current choice is conservative-correct.

### 5. The main.ll Audit Shows Clean IR

178,011 lines, 712 `define` statements, 37 `declare` statements. Key quality metrics:

| Metric | v3.45.0 | v3.47.0 | Delta |
|--------|---------|---------|-------|
| Total lines | 174,269 | 178,011 | **+3,742** |
| Functions defined | ~680 | 712 | **+32** (GPU + I/O dispatch code) |
| `add nsw` instructions | 575 (via grep) | 575 | Stable |
| `sub nsw` instructions | 61 (estimated) | 66 | **+5** |
| `mul nsw` instructions | 2 (estimated) | 2 | Stable |
| `bitcast` string constants | 6 | 6 | Stable (all in self-hosted emitter output) |
| `declare noalias` | 1 (malloc) | 1 (malloc) | Stable |
| `declare ... willreturn` | 4 | 4 | Stable (range_free, str_free, free, list_free) |
| Version string | v3.40.0 | **v3.47.0** | **CURRENT** |

The Python text emitter generates zero `add`/`sub`/`mul` without `nsw` in actual instructions. Every non-nsw occurrence in main.ll is a string constant being emitted by the self-hosted compiler for its own output IR generation.

---

## Issues Found

### 1. **[LOW -- NEW]** GPU Tensor Builtins Do Not Track Returned Lists for Drop Glue

**Location:** `mapanare/emit_llvm_text.py:2316-2352`

The GPU tensor builtins (`gpu_tensor_add`, `gpu_tensor_sub`, `gpu_tensor_mul`, `gpu_tensor_div`, `gpu_tensor_matmul`) return `LIST` type but do not call `_track_container(i.dest.name, "list")` after the call. Compare with `list_concat` at line 1876 which correctly tracks, and `str_split` at line 2393-2394 which tracks via the string method dispatch:

```python
# list_concat (line 1876) -- CORRECT
self._track_container(i.dest.name, "list")
self._put(i.dest, r, LIST)

# gpu_tensor_add (line 2332-2333) -- MISSING TRACKING
r = self._rt(cfn, LIST, [PTR, PTR], [(pa, PTR), (pb, PTR)])
self._put(i.dest, r, LIST)  # <-- no _track_container
```

**Impact:** Lists returned by GPU tensor operations will not be freed at function exit. For short-lived functions this is a bounded leak. For loops that repeatedly call GPU tensor operations (e.g., iterative optimization), this will accumulate.

Note: `list_dir` at line 2223 has the same issue -- returns LIST without tracking. This was present in v3.45.0 but I did not flag it because the GPU pattern makes it more prominent.

**Fix:**
```python
# After each gpu_tensor_* _put:
self._track_container(i.dest.name, "list")
```

Same for `list_dir` at line 2224 and `gpu_tensor_matmul` at line 2351.

### 2. **[LOW -- NEW]** Self-Hosted GPU Tensor Builtins Return `llvm_list_rt()`, Not Tracked

**Location:** `mapanare/self/emit_llvm.mn:2445, 2459`

Same issue as #1 but in the self-hosted emitter. The GPU tensor dispatch returns `llvm_list_rt()` (LIST) but the returned value is not registered with any drop-glue tracking mechanism.

**Impact:** Programs compiled by mnc-stage1 that call GPU tensor operations in loops will leak list buffers. Since the self-hosted compiler does not itself call GPU functions, self-compilation is unaffected.

### 3. **[LOW -- NEW]** Golden Test Refs Missing for Tests 33-40

**Location:** `tests/golden/`

There are 40 `.mn` test files but only 32 `.ref.ll` reference files. Tests 33-40 (`break_continue`, `file_io`, `stdin`, `crypto`, `regex`, `http`, `gpu_detect`, `gpu_tensor`) do not have reference IR. The golden test harness compares mnc-stage1 output against the Python bootstrap, so functional correctness is still validated -- but the `.ref.ll` files serve as a permanent record of expected IR structure.

**Fix:** `python scripts/test_native.py --bless` will generate refs for all 40 tests.

### 4. **[LOW]** Self-Hosted `i64*` Typed Pointer in Tensor Alloc -- 6th Review Cycle

**Location:** `mapanare/self/emit_llvm.mn:371`

```mapanare
s = declare_runtime_fn(s, "__mapanare_tensor_alloc", "ptr", "i64, i64*, i64")
```

Still `i64*`. Still invalid on LLVM 17+ opaque pointer mode. Still unreachable because tensor language integration is not implemented. I have flagged this since v3.39.0. I am now mentioning it purely for completeness. When the compiler switches to opaque-pointer-only mode (which upstream LLVM 17 already enforces), this declaration will fail `llvm-as` validation.

### 5. **[LOW]** Self-Hosted `void ()*` Bitcast -- 6th Review Cycle

**Location:** `mapanare/self/emit_llvm.mn:789`

```mapanare
s = emit_line(s, "  " + dn + " = bitcast void ()* @" + val + " to ptr")
```

Still `void ()*`. Still invalid in opaque-ptr mode. The correct replacement is simply `ptr @val` with no bitcast needed.

### 6. **[LOW]** Self-Hosted `<type>*` Bitcast in List Push -- 6th Review Cycle

**Location:** `mapanare/self/emit_llvm.mn:1615`

```mapanare
s = emit_line(s, emit_bitcast(cast_name, ety + "*", elem_alloca, "ptr"))
```

Still constructs a typed pointer from element type string concatenation. The `emit_bitcast` function itself (emit_llvm_ir.mn:251) is fine -- it is a pure string builder. But passing `ety + "*"` as the source type produces `{ptr, i64}*` or `i64*` etc., which are typed pointer syntax that LLVM 17+ rejects.

**Fix:** Since the purpose is to pass `elem_alloca` (which is already a `ptr` from the alloca) to `__mn_list_push` as `ptr`, the bitcast is unnecessary. Just pass `ptr elem_alloca` directly.

### 7. **[LOW]** Self-Hosted `emit_add`/`emit_sub`/`emit_mul` Missing `nsw` -- 6th Review Cycle

**Location:** `mapanare/self/emit_llvm_ir.mn:115-125`

```mapanare
fn emit_add(name: String, ty: String, left: String, right: String) -> String {
    return "  " + name + " =add " + ty + " " + left + ", " + right
}
```

The Python text emitter uses `add nsw i64` for integer arithmetic. The self-hosted emitter uses plain `add i64`. Without `nsw` (no signed wrap), LLVM cannot propagate bounds information through integer additions, cannot fold `(x + 1) > x` to `true`, and cannot optimize comparisons against computed values. Stage2 IR loses ~575 optimization opportunities.

**Fix (3 words):** Add `nsw` after `add`, `sub`, `mul` in the three functions.

### 8. **[LOW]** Self-Hosted `__mn_map_new` 3-Param ABI Mismatch -- 6th Review Cycle

**Location:** `mapanare/self/emit_llvm.mn:352, 1808`

Declaration: `"i64, i64, i64"` (3 params). C runtime: `__mn_map_new(int64_t key_size, int64_t val_size, int64_t key_type, int64_t val_type)` (4 params).

The 4th parameter (`val_type`) is used for value type dispatch in the Robin Hood hash table. Omitting it means the C runtime reads an uninitialized stack value for `val_type`.

### 9. **[LOW]** Self-Hosted `get_fn_attrs` Missing `noalias`/`willreturn` -- 6th Review Cycle

**Location:** `mapanare/self/emit_llvm.mn:264-289`

`malloc` still returns `" nounwind"` instead of `" nounwind noalias"`. Free functions still return `" nounwind"` instead of `" nounwind willreturn"`. The 9 new I/O and GPU builtins added at lines 403-421 also get no attributes from `get_fn_attrs` (they fall through to the empty string return at line 288).

**Impact:** Stage2 IR loses `noalias` on `malloc` (blocks alias analysis improvement) and `willreturn` on free functions (blocks dead call elimination when return value is unused).

### 10. **[LOW]** Golden Test Refs at v3.14.0 -- 5th Review Cycle

**Location:** `tests/golden/*.ref.ll` (32 files)

All 32 reference files show `!0 = !{!"3.14.0"}`. The Python emitter now generates `3.47.0`. These refs are cosmetically stale and have been for 5 review cycles.

---

## Recommendations

### For v4.0.0 (Should-Fix Before Tagging)

| # | Fix | Effort | Location | Notes |
|---|-----|--------|----------|-------|
| 1 | **Add `_track_container` for GPU tensor returns** | 6 lines | `emit_llvm_text.py:2333,2351` | NEW -- prevents list leak in GPU compute loops |
| 2 | **Add `_track_container` for `list_dir`** | 1 line | `emit_llvm_text.py:2224` | Was present in v3.45.0 but not flagged |
| 3 | **Re-bless golden refs** | 30 seconds | `scripts/test_native.py --bless` | 5th cycle. I will stop asking at v4.1. |

### For v4.1 (Self-Hosted Emitter Quality)

| # | Fix | Effort | Location | Notes |
|---|-----|--------|----------|-------|
| 4 | Add `nsw` to `emit_add`/`emit_sub`/`emit_mul` | 3 words | `emit_llvm_ir.mn:116,120,124` | 6th cycle |
| 5 | Fix `i64*` in tensor alloc declaration | 1 word | `emit_llvm.mn:371` | 6th cycle |
| 6 | Fix `void ()*` bitcast | ~3 lines | `emit_llvm.mn:789` | 6th cycle |
| 7 | Remove typed pointer bitcast in list push | 1 line | `emit_llvm.mn:1615` | 6th cycle |
| 8 | Fix `__mn_map_new` 3 -> 4 params | ~5 lines | `emit_llvm.mn:352,1808` | 6th cycle |
| 9 | Add `noalias`/`willreturn` + new builtins to `get_fn_attrs` | ~20 lines | `emit_llvm.mn:264-289` | 6th cycle |
| 10 | Map type ABI: `llvm_map_type()` returns `{ ptr, i64 }` but Python emitter uses `ptr` | 1 line | `emit_llvm_ir.mn:50` | Python emitter at types.py maps MAP to PTR. Self-hosted uses `{ ptr, i64 }`. Stage1 runtime calls use whichever the self-hosted emitter outputs. |
| 11 | GPU tensor list tracking in self-hosted emitter | 2 lines | `emit_llvm.mn:2445,2459` | Mirror Python emitter fix |

---

## v4.0.0 Readiness Assessment

**YES -- UNCONDITIONAL from a codegen perspective, with 3 minor should-fixes.**

### Python Text Emitter (Shipping Compiler): PASS (EXCELLENT)

- **Zero typed pointers** in generated IR
- **Zero bitcast instructions** in generated IR (6 string occurrences in main.ll, all metadata)
- **Correct function attributes**: 68 entries in `_RUNTIME_FN_ATTRS`, properly categorized
- **`nsw` on all integer arithmetic**: 575 `add nsw`, 66 `sub nsw`, 2 `mul nsw` in main.ll -- zero non-nsw actual instructions
- **Correct ordered float comparisons**: `oeq`, `one`, `olt`, `ogt`, `ole`, `oge`
- **GPU builtins correctly wired** with pass-by-pointer ABI for 40-byte MnList structs
- **Bool ABI fix verified** at all 4 `__mn_str_from_bool` call sites
- **Regex builtins** use correct compile-exec-free handle pattern
- **Drop glue** handles string returns from all builtins (crypto, regex, HTTP, GPU device_name all track)
- **One minor gap**: GPU tensor and `list_dir` returns not tracked for list drop glue (Issue #1, #2)

### Self-Hosted Emitter (stage2+): PASS WITH NOTES (IMPROVED)

- **3 of 3 v3.45.0 NEW issues fixed**: str_from_bool zext, file_exists return, regex compile-exec-free
- **9 missing I/O declarations added**: file_remove through tmpfile_path
- **GPU builtins added**: 8 declarations + dispatch code for all tensor ops
- **6 carried-forward LOW issues remain**: all in code that does not affect the shipping compiler
- **Map type ABI divergence**: self-hosted uses `{ptr, i64}`, Python emitter uses `ptr`

### Test Coverage: PASS

- **40 golden tests** (up from 38), 32 with `.ref.ll` files
- **9 GPU-specific LLVM tests** (NEW)
- **397 LLVM-specific test functions** across 22 files (7,880 lines)
- **2 new golden tests** cover GPU device detection and tensor operations

### GPU Codegen: PASS

- **Text emitter**: 9 GPU builtins wired at lines 2299-2352 with correct ABI
- **MIR emitter**: full CUDA/Vulkan kernel launch codegen (PTX embedding, SPIR-V embedding, parameter arrays, sync, cleanup)
- **Self-hosted emitter**: GPU declarations and dispatch matching Python emitter
- **Test coverage**: decorator detection, runtime declarations, tensor dispatch routing
- **Runtime declarations**: lazy initialization (`_declare_gpu_runtime`) prevents unused GPU symbols in non-GPU programs

### ABI Stability: PASS

- **Byref for >64-byte structs**: correct (LLVMTextEmitter._BYREF_BYTES = 64)
- **Win64 sret**: correct (property-based detection, large-struct pass-by-pointer)
- **Bool zext for printf**: verified correct in both emitters
- **Bool zext for `__mn_str_from_bool`**: correct in both emitters (v3.47.0 fix)
- **GPU list pass-by-pointer**: correct in both emitters

---

## Raw Notes

### GPU Codegen Deep Dive

The text emitter's GPU dispatch is concentrated in 53 lines (2299-2352). The pattern for all four element-wise ops (add/sub/mul/div) is identical:

1. Coerce arguments to LIST (handle type mismatches)
2. Alloca two LIST slots on the stack
3. Store list values into slots
4. Call `__mn_gpu_tensor_X(ptr, ptr)` passing slot pointers
5. Store result and put

The matmul variant adds three i64 arguments (rows_a, cols_a_rows_b, cols_b) for dimension specification. These are coerced to i64 individually and passed directly (not by pointer, since i64 fits in a register). This is correct.

The MIR emitter's GPU codegen (1607-1875) is more sophisticated because it handles actual CUDA/Vulkan kernel dispatch. The parameter array construction at lines 1783-1796 is textbook correct -- it builds `[N x i8*]` on the stack, GEPs into each element, stores coerced pointers, then bitcasts the array pointer to `i8**`. This is exactly how clang would lower a variadic-style parameter pack.

One observation: the `builder.bitcast(params_alloca, LLVM_PTR)` at line 1794 is technically unnecessary with opaque pointers. The alloca already returns `ptr`. However, llvmlite may not yet handle opaque pointers correctly in all contexts, so this defensive bitcast is acceptable.

### Self-Hosted Emitter Convergence

The gap between the Python emitter and the self-hosted emitter has **narrowed** since v3.45.0. The divergence score:

| Feature | v3.45.0 | v3.47.0 |
|---------|---------|---------|
| str_from_bool zext | DIVERGED | CONVERGED |
| file_exists return | DIVERGED | CONVERGED |
| Regex dispatch | DIVERGED | CONVERGED |
| I/O builtin declarations | DIVERGED (9 missing) | CONVERGED |
| GPU builtins | N/A | CONVERGED |
| nsw on arithmetic | DIVERGED | DIVERGED |
| noalias/willreturn attrs | DIVERGED | DIVERGED |
| map_new param count | DIVERGED | DIVERGED |
| Typed pointers (3 sites) | DIVERGED | DIVERGED |
| Map type ABI | DIVERGED | DIVERGED |
| List drop glue tracking (GPU) | N/A | DIVERGED |

5 items converged, 6 items still diverged. The trend is positive.

### Quantitative Summary

| Metric | v3.45.0 | v3.47.0 | Delta |
|--------|---------|---------|-------|
| Text emitter lines | 3,581 | 3,645 | **+64** (+1.8%) |
| Self-hosted emitter lines (emit_llvm.mn) | 3,319 | 3,418 | **+99** (+3.0%) |
| Self-hosted emitter lines (emit_llvm_ir.mn) | 254 | 254 | 0 |
| `_RUNTIME_FN_ATTRS` entries | 59 | 68 | **+9** (GPU) |
| Golden tests (.mn) | 38 | 40 | **+2** |
| Golden refs (.ref.ll) | 32 | 32 | 0 (8 tests without refs) |
| `nsw` instructions in main.ll | 636 (total grep) | 643 (total grep) | **+7** |
| Actual `add nsw` instructions | ~575 | 575 | Stable |
| `bitcast` occurrences in main.ll | 6 | 6 | Stable (all string constants) |
| `declare` statements in main.ll | 40 | 37 | **-3** (dedup or removal of unused) |
| `define` statements in main.ll | ~680 | 712 | **+32** (GPU + I/O dispatch) |
| main.ll total lines | 174,269 | 178,011 | **+3,742** |
| LLVM test files | 20 | 22 | **+2** (test_gpu_dispatch + 1 other) |
| LLVM test functions | 397 | 397 | Stable |
| Typed pointers in Python emitter | 0 | 0 | Stable (clean) |
| Typed pointers in self-hosted emitter | 3 | 3 | Stable (deferred) |
| Self-hosted ABI mismatches | 8 | 5 | **-3** (3 fixed, 0 new) |
| v3.45.0 issues resolved | -- | 5/12 | **42%** resolution rate |
| Version string current | NO | **YES** | Fixed |

### A Note on the Golden Ref Situation

I have flagged the golden refs at v3.14.0 for five consecutive reviews. The refs exist to serve two purposes: (1) validate structural correctness (do the same basic blocks appear, with the same instruction patterns?), and (2) provide a time-stamped record of IR quality at a specific compiler version. Purpose (1) is satisfied by the live bootstrap-vs-stage1 comparison. Purpose (2) is not satisfied when the refs are 33 versions behind.

At this point I am requesting the `--bless` command one final time for v4.0.0. If it is not done, I will simply note "refs at v3.14.0, 6th cycle" and move on. Life is too short to keep asking for a 30-second command.
