# Mapanare v3.13.0 — "Cascabel" (Memory Safety & Runtime Hardening)

> Eliminate every memory leak. Remove the write(2) syscall probe.
> Enable string drop glue. Harden concurrency primitives.
> The release that converts Viper's NEEDS WORK into PASS.

**Status:** PLANNED
**Estimated scope:** Large (2-3 sessions)
**Breaking:** Yes (MnList ABI change: 32 -> 40 bytes)
**Review trigger:** v3.10.0 code review — Viper 6.5/10 (NEEDS WORK), memory leaks systemic

---

## Why This Version Exists

The v3.10.0 code review (7 reviewers, 8.37/10 aggregate) identified memory lifecycle
as the single biggest weakness. Viper (Rust perspective) gave the only NEEDS WORK at
6.5/10. Three reviewers independently flagged `_track_string` as a no-op. The COW list
uses a `write(2)` syscall to `/dev/null` on every push. Range iterators heap-allocate
and never free. The intern table has no thread safety. These issues have persisted
across 2-3 major versions.

v3.13.0 fixes all of them in one focused release.

---

## Phase 1: String Drop Glue [P0]

### 1.1 — Re-enable `_track_string`

**File:** `mapanare/emit_llvm_mir.py:3336-3344`

The method is a no-op (`return` at line 3344). The comment says "adding allocas to
pre_entry after terminator corrupts IR" — but `_aligned_alloca` already handles this
correctly via `ir.IRBuilder(pre_entry)`.

**Fix:** Remove early `return`. Use `_aligned_alloca` to create tracking slots:
```python
def _track_string(self, builder, val):
    slot = _aligned_alloca(builder, LLVM_STRING, f"str.track.{len(self._local_strings)}")
    builder.store(val, slot)
    self._local_strings.append(slot)
```

`_emit_drop_glue` at line 3346 already iterates `_local_strings`, compares against
return value, and calls `__mn_str_free`. No changes needed in drop glue.

**Verification:** `/valgrind-map` on golden tests 05_string, 14_interp_string.
Zero "definitely lost" bytes.

### 1.2 — Targeted arena for string interpolation

**File:** `mapanare/emit_llvm_mir.py` around `_emit_string_interp`

Create arena before interpolation loop, destroy after final concat. All intermediates
are temporaries that can't escape. Safe optimization without full escape analysis.

---

## Phase 2: Runtime Leak Fixes [P0]

### 2.1 — Stack-allocate range iterators

**Files:** `runtime/native/mapanare_core.c:2247`, `mapanare/emit_llvm_mir.py`

`__mn_range()` calls `malloc(16)` for `MnRangeIter {current: i64, end: i64}`. No free
function exists. Every `for i in 0..n` leaks 16 bytes.

**Preferred fix:** Emit `alloca {i64, i64}` + store in the LLVM emitter instead of
calling `__mn_range()`. `__iter_has_next`/`__iter_next` already take `void*`.

**Fallback:** Add `__mn_range_free(void*)` to C runtime, emit call after for-loop exit.

### 2.2 — Remove COW list write(2) syscall probe

**Files:** `runtime/native/mapanare_core.c:722-744`, `runtime/native/mapanare_core.h`

`mn_list_has_magic()` opens `/dev/null` and calls `write()` to probe 16 bytes before
the data pointer. Called on every `mn_list_detach()` → every `push`/`pop`/`set`/`clear`.

**Fix:** Add `int8_t managed` field to `MnList`:
- Set `managed=1` in `mn_list_alloc_buf()`/`__mn_list_new()`
- Replace `mn_list_has_magic()` body: `return list->managed && list->data != NULL`
- Remove the entire `write(2)`/`/dev/null` block
- Update LLVM struct type for MnList in emitter (32 → 40 bytes with alignment)

**Breaking:** This changes MnList ABI. Self-hosted compiler struct definitions must
be updated. Golden reference files must be regenerated.

---

## Phase 3: LLVM Emitter Improvements [P1]

### 3.1 — Add function attributes to runtime declarations

**File:** `mapanare/emit_llvm_mir.py:1252-1260`

`_declare_runtime_fn` sets only `linkage = "external"`. No `nounwind`, `noalias`,
`readonly`, `nocapture`.

**Fix:** Add `_RUNTIME_FN_ATTRS` dict (~30 functions):
- `__mn_str_len` → `["nounwind", "readonly"]`
- `__mn_str_eq`, `__mn_str_cmp` → `["nounwind", "readonly"]`
- `malloc`, `__mn_alloc` → `["nounwind"]` + `noalias` on return
- `free`, `__mn_str_free` → `["nounwind"]`
- All `__mn_list_len`, `__mn_list_get` → `["nounwind", "readonly"]`

Apply in `_declare_runtime_fn` after setting linkage. Expected 5-15% codegen
improvement from LLVM optimization.

### 3.2 — Fix `_approx_type_size` pointer size

**File:** `mapanare/emit_llvm_mir.py:5116-5149`

Hardcoded `8` for `ir.PointerType`. Wrong for wasm32 (4 bytes) and potentially
mobile targets.

**Fix:** Add `_TARGET_PTR_SIZE` constant set from target triple. Use instead of
hardcoded `8` in pointer and fallback cases.

---

## Phase 4: Concurrency Hardening [P1]

### 4.1 — Intern table thread safety

**File:** `runtime/native/mapanare_core.c:194-199`

`s_intern_table` and associated globals are bare statics with no synchronization.
Concurrent agent threads calling `__mn_str_intern` will corrupt entries.

**Fix:** Add mutex (POSIX: `pthread_mutex_t`, Windows: `CRITICAL_SECTION`) around
`__mn_str_intern()`. Same pattern as signal mutex.

### 4.2 — Windows signal mutex TOCTOU

**File:** `runtime/native/mapanare_core.c:1595-1601`

`mn_signal_mutex_initialized` is a plain `int` checked without atomics. Two threads
can race on `InitializeCriticalSection`.

**Fix:** Replace with `InterlockedCompareExchange` pattern (same as GPU init).

---

## New Culebra Templates

Create in Culebra repo (`culebra-templates/`):

1. **`ir/string-track-noop.yaml`** — Detect functions calling `__mn_str_concat`/
   `__mn_str_from_*` without `str.track` allocas. Regression gate for Phase 1.

2. **`c/syscall-in-hot-path.yaml`** — Detect `write()`/`open()` calls inside static
   functions called from `__mn_*` hot paths. Regression gate for Phase 2.2.

---

## Verification Checklist

- [ ] `./dev.ps1 validate` — all existing tests pass
- [ ] `/rebuild` — full rebuild cycle green
- [ ] `/golden` — 32/32 golden tests pass (regenerate `.ref.ll`)
- [ ] `/valgrind-map` on golden 05, 06, 11, 12, 14 — zero "definitely lost"
- [ ] `/culebra-scan` — no new findings, `--reject string-track-noop`
- [ ] CI native with ASAN + TSAN — clean
- [ ] Benchmark list push 100k — no write(2) overhead

## Expected Impact

| Reviewer | v3.10.0 | Expected v3.13.0 | Delta |
|----------|---------|-------------------|-------|
| Viper | 6.5 (NEEDS WORK) | 8.0-8.5 (PASS) | +1.5-2.0 |
| Mamba | 8.1 | 8.5-8.8 | +0.4-0.7 |
| Rattler | 8.5 | 9.0 | +0.5 |
| Aggregate | 8.37 | 8.7-9.0 | +0.3-0.6 |
