# Mapanare v4.3.0 — Drop Glue Done Right (Memory Correctness)

> Functions returning structs stop leaking. Every allocation has an owner.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.2.0 (single emitter — can't fix drop glue with 3 emitters)

---

## The Core Problem

`emit_llvm_text.py:966` has `skip_struct_ret` which disables ALL drop glue when
a function returns a struct or enum. This means every string, closure, list, map,
signal, and stream allocated inside a struct-returning function is leaked.

This was deliberate — the alternative was use-after-free. If the return value
contains a string that's also in the cleanup list, freeing it destroys the return
value. The real fix is return-value escape analysis: track which values are moved
into the return struct and skip only those.

---

## Phase 1: Return-Value Escape Analysis

### 1A. Track escaping values

- [ ] In `emit_llvm_text.py`, when building the return value (`insertvalue` chain),
      record every SSA register that is inserted into the return struct
- [ ] For nested structs, walk the return value recursively to find all embedded
      pointers (strings nested 2+ levels deep)
- [ ] Build a `_return_escapes: set[str]` per function containing all SSA names
      that escape via return

### 1B. Replace `skip_struct_ret`

- [ ] Remove the `skip_struct_ret` bail-out at line ~966
- [ ] In `_emit_drop_glue`, check each tracked value against `_return_escapes`
- [ ] Skip only values whose SSA name is in the escape set
- [ ] Free everything else normally

### 1C. Test thoroughly

- [ ] Write a golden test: function returns struct containing a string, verify
      no use-after-free (run under valgrind in WSL)
- [ ] Write a golden test: function allocates 3 strings, returns struct containing 1,
      verify the other 2 are freed (check with MN_PROFILE_MEM)
- [ ] Run all 40 golden tests under valgrind: `/valgrind-map`

**Files:** `mapanare/emit_llvm_text.py`

---

## Phase 2: Free String Intermediates

### 2A. Concat/interp temporaries

- [ ] In `_emit_str_concat`, track the result as a temporary
- [ ] After the concat result is stored/used, emit `__mn_str_free` for the
      intermediate (unless it escapes)
- [ ] Same for `InterpConcat` chains — each intermediate should be freed after
      the next concat consumes it

### 2B. Boolean/int/float to string

- [ ] Track `str_from_bool`, `str_from_int`, `str_from_float` results as temporaries
- [ ] Free after use (these allocate via malloc every call)

**Files:** `mapanare/emit_llvm_text.py`

---

## Phase 3: Free Containers and Handles

### 3A. Map iterators

- [ ] After every `for key, value in map:` loop body, emit `__mn_map_iter_free`
- [ ] The iterator is created by `__mn_map_iter_new` at loop entry — track it
- [ ] Verify no double-free if loop exits early via `break`

### 3B. Stream `user_data`

- [ ] In `mapanare_core.c`, update `__mn_stream_free` to call `__mn_free` on
      `stream->user_data` if non-NULL (closure environment)
- [ ] Same for `__mn_stream_free_chain`
- [ ] Test: create stream with closure, destroy it, verify no leak

### 3C. String intern table

- [ ] In `mnc_main.c` (or wherever the program epilogue is emitted), call
      `__mn_intern_destroy()` before `return 0`
- [ ] Self-hosted: add `__mn_intern_destroy` call in `main.mn` epilogue

### 3D. Agent struct

- [ ] In `mapanare_runtime.c`, add `free(agent)` at the end of
      `mapanare_agent_destroy`
- [ ] OR: emit `__mn_free(agent_ptr)` in the emitter after the destroy call
- [ ] Test: spawn agent, let it complete, verify no leak

### 3E. Agent registry

- [ ] Add `mapanare_registry_destroy()` function to `mapanare_runtime.c`
- [ ] Destroys the mutex, frees the registry array
- [ ] Call from program epilogue

**Files:** `mapanare/emit_llvm_text.py`, `runtime/native/mapanare_core.c`,
`runtime/native/mapanare_runtime.c`, `mapanare/self/main.mn`

---

## Phase 4: Verification

- [ ] `.\dev.ps1 validate` — full validation passes
- [ ] `/golden` — 40/40 pass
- [ ] Run ALL golden tests under valgrind in WSL:
      `for f in tests/golden/*.mn; do python scripts/ir_doctor.py valgrind "$f"; done`
- [ ] Zero "definitely lost" bytes in valgrind report for:
  - Function returning struct with strings
  - For-in-map loop
  - Stream with closure
  - Agent spawn + complete
- [ ] `/rebuild` + `/stage2` — self-hosted still works

---

## Exit Criteria

| Check | Required |
|-------|----------|
| `skip_struct_ret` removed from `emit_llvm_text.py` | YES |
| Return-value escape analysis implemented | YES |
| String concat intermediates freed | YES |
| Map iterators freed after for-in loops | YES |
| Stream `user_data` freed on destroy | YES |
| `__mn_intern_destroy` called at program exit | YES |
| Agent struct freed in `mapanare_agent_destroy` | YES |
| `mapanare_registry_destroy` exists and is called | YES |
| All 40 golden tests pass | YES |
| Valgrind: zero "definitely lost" on struct-return test | YES |
| Self-hosted rebuild + fixed point maintained | YES |
