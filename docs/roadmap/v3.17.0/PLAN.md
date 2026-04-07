# Mapanare v3.17.0 — "Tigra" (Text Emitter: Drop Glue + Function Attributes)

> Port string/closure drop glue from emit_llvm_mir.py to emit_llvm_text.py.
> After this version, the default compilation pipeline no longer leaks strings.
> This is the single largest piece of work in the v3.15-v4.0 roadmap.

**Status:** DONE
**Estimated scope:** Large (2-3 sessions)
**Breaking:** No
**Prerequisite:** v3.16.0 (ABI fix, container cleanup functions in runtime)

---

## Items

### 1. Text emitter zero drop glue [CRITICAL — largest item]

**File:** `mapanare/emit_llvm_text.py` (~500 lines new code)
**Reference:** `mapanare/emit_llvm_mir.py:3399-3502`
**Reporters:** Rattler (C1), Viper (C1)

The default emitter has zero string/closure cleanup. Port the pattern:

1. Add `_local_strings: list[str]` and `_local_closures: list[str]` members
2. Add `_track_string(val_name)` — emit alloca in pre_entry, store val, append to list
3. Instrument ~11 string allocation sites (str_from_int, str_from_float, concat, etc.)
4. Add `_emit_drop_glue(ret_val)` — before every `ret`:
   - Load each tracked string from alloca
   - Extract data pointer, compare to return value's data pointer
   - Conditional branch: if different, call `__mn_str_free`
   - Repeat for closures with null check
5. Call `_emit_drop_glue` from every return path

### 2. Text emitter missing function attributes [HIGH]

**File:** `mapanare/emit_llvm_text.py`
**Reporter:** Rattler (H2)

Zero `nounwind`/`readonly` on runtime declarations.

**Fix:** Copy `_RUNTIME_FN_ATTRS` dict from `emit_llvm_mir.py:1273-1311`. Append
attributes to `declare` statements: `declare nounwind readonly i64 @__mn_str_len(...)`.

### 3. `_llvm_type_size` no alignment padding [HIGH]

**File:** `mapanare/emit_llvm_mir.py:966-976`
**Reporter:** Rattler (M8)

`_llvm_type_size` sums element sizes without padding. `{i1, i64}` returns 9 (should be 16).
Used for closure environment sizing — causes buffer overruns on mixed-type captures.

**Fix:** Delegate to `_approx_type_size` which handles alignment correctly.

### 4. Boxed struct fields leak [MEDIUM]

**File:** Both emitters
**Reporter:** Viper (M9)

Enum values with heap-allocated payloads (via boxing for recursive types) leak
the payload pointer on scope exit. Drop glue needs to track boxed fields.

**Fix:** When emitting enum init, if payload is boxed (heap-allocated), track the
pointer and free it in drop glue alongside strings and closures.

---

## Verification

- [ ] Compile string-heavy program via `mapanare run` (text emitter), Valgrind — zero leaks
- [ ] Grep text emitter output for `__mn_str_free` calls — non-zero
- [ ] Grep text emitter output for `nounwind` — present on declarations
- [ ] Compare text vs llvmlite emitter: matching memory behavior
- [ ] `/golden` — 32/32 with both emitters
- [ ] Closure with mixed-type captures: Valgrind clean
