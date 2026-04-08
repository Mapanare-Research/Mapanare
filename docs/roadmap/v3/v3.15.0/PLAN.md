# Mapanare v3.15.0 — "Coral" (C Runtime: UB, Crashes, Data Corruption)

> Fix every bug that causes undefined behavior, memory corruption, or crashes
> in the C runtime. The foundation everything else builds on.

**Status:** DONE
**Estimated scope:** Small (1 session)
**Breaking:** No
**Prerequisite:** v3.14.0

---

## Why This Version Exists

The v3.14.0 code review (7 reviewers) found critical memory safety bugs in the
C runtime that cause undefined behavior on real workloads: a null-pointer-minus-16
in list concat, a deadlocking Windows console handler, non-atomic COW refcounts
on ARM64, and an ABI mismatch introduced in v3.13.0. These must be fixed before
any emitter or compiler work because the runtime is the foundation.

---

## Items

### 1. `__mn_list_concat` null-pointer-minus-16 UB [CRITICAL]

**File:** `runtime/native/mapanare_core.c:1006-1026`
**Reporter:** Mamba

`__mn_list_new(es)` returns `data=NULL, cap=0`. Line 1013 computes
`((char *)result.data) - MN_LIST_HEADER_SIZE` = `NULL - 16` = garbage.
This is passed to `realloc()`, which is UB.

**Fix:** When `result.data == NULL`, call `mn_list_alloc_buf(total, es)` directly
instead of trying to realloc a nonexistent header.

### 2. Windows console handler deadlock [CRITICAL]

**File:** `runtime/native/mapanare_runtime.c:1092-1101`
**Reporters:** Viper, Mamba

`mapanare_console_handler` calls `mapanare_registry_stop_all()` which takes a
mutex. If main thread holds the lock when Ctrl+C fires, the handler thread deadlocks.
The POSIX handler (line 1103-1112) correctly only sets a flag.

**Fix:** Remove `mapanare_registry_stop_all()` call. Just set `s_shutdown_requested = 1`.
Actual drain happens in `mapanare_shutdown_requested()` from normal execution context.

### 3. COW list refcount non-atomic [CRITICAL]

**File:** `runtime/native/mapanare_core.c:779,904,958`
**Reporter:** Viper

`(*rc)++` and `(*rc)--` on plain `int64_t` at 3 sites. Data race on ARM64 when
agents share lists.

**Fix:**
- Line 779: `(*rc)--` -> `__atomic_fetch_sub(rc, 1, __ATOMIC_ACQ_REL)`
- Line 904: `(*rc)--` -> `__atomic_fetch_sub(rc, 1, __ATOMIC_ACQ_REL)`
- Line 958: `(*rc)++` -> `__atomic_fetch_add(rc, 1, __ATOMIC_RELAXED)`

### 4. MnList ABI mismatch (3 files) [HIGH]

**Files:** `mapanare/emit_llvm_text.py:77`, `mapanare/emit_llvm.py:89`, `mapanare/self/mnc_main.c:46-51`
**Reporters:** Anaconda, Rattler

v3.13.0 added `int64_t managed` as 5th field to MnList in the C runtime but
three emitter-side definitions still have 4 fields/32 bytes.

**Fix:**
- `emit_llvm_text.py:77`: `LIST = "{ptr, i64, i64, i64}"` -> `"{ptr, i64, i64, i64, i64}"`
- `emit_llvm.py:89`: Add 5th `LLVM_INT` to `LLVM_LIST`
- `mnc_main.c:46-51`: Add `int64_t managed;` to MnList typedef

### 5. VkPhysicalDeviceProperties padding undersized [MEDIUM]

**File:** `runtime/native/mapanare_gpu.h:146`
**Reporter:** Mamba

Total 804 bytes vs real ~824 bytes. Stack smash on Vulkan systems.

**Fix:** `_padding[512]` -> `_padding[544]`

### 6. `__mn_str_from_bool` heap-allocates per call [MEDIUM]

**File:** `runtime/native/mapanare_core.c:611-613`
**Reporter:** Mamba

Calls `__mn_str_from_cstr("true"/"false")` which malloc+memcpy every call.

**Fix:** Two static constants:
```c
static const MnString MN_STR_TRUE  = { "true",  4 };
static const MnString MN_STR_FALSE = { "false", 5 };
```

### 7. `__mn_list_oob_buf` shared mutable global [HIGH]

**File:** `runtime/native/mapanare_core.c:850`
**Reporters:** Viper, Mamba

Static 4KB buffer returned for OOB access, shared across threads. Data race.

**Fix:** `static _Thread_local char __mn_list_oob_buf[4096] = {0};`

---

## Verification

- [x] Native C tests with ASan pass (53/53)
- [x] Native C tests with TSan pass (53/53)
- [ ] `bash scripts/rebuild.sh full` — golden + selftest + memory
- [x] Add `test_list_concat` native test
- [x] 4486 pytest pass (6 pre-existing failures unrelated to v3.15.0)
