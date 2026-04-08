# Mapanare v3.16.0 — "Lora" (C Runtime: Concurrency Safety + Leak Fixes)

> Make signal/stream/map subsystems thread-safe. Fix runtime-level memory leaks.
> Harden CI. All changes in C runtime + CI config.

**Status:** DONE
**Estimated scope:** Small (1 session)
**Breaking:** No
**Prerequisite:** v3.15.0

---

## Items

### 1. Signal tracking context bare global [HIGH]

**File:** `runtime/native/mapanare_core.c:1624`
**Reporter:** Viper

`static MnSignal *mn_signal_tracking_context` read/written without sync.
Concurrent computed signals clobber each other's tracking.

**Fix:** `static _Thread_local MnSignal *mn_signal_tracking_context = NULL;`

### 2. Signal subscriber list unprotected during propagation [HIGH]

**File:** `runtime/native/mapanare_core.c:1764-1826`
**Reporter:** Viper

`mn_signal_propagate` iterates `signal->subscribers` without lock while
`__mn_signal_subscribe` can realloc the array. Use-after-free.

**Fix:** Wrap both functions with `mn_signal_lock()`/`mn_signal_unlock()`.

### 3. `__mn_map_free` doesn't free string keys/values [HIGH]

**File:** `runtime/native/mapanare_core.c:1550-1555`
**Reporter:** Viper

Frees bucket array and map struct but not string entries.

**Fix:** Add `__mn_map_free_deep(MnMap *map, int free_keys, int free_values)` that
iterates entries and calls `__mn_str_free` on string keys/values before freeing.

### 4. `__mn_stream_free` doesn't free upstream chain [HIGH]

**File:** `runtime/native/mapanare_core.c:2164-2176`
**Reporters:** Viper, Mamba

Frees current node but `stream->source` leaks.

**Fix:** Add `__mn_stream_free_chain(MnStream *stream)` that recursively frees
`stream->source` before freeing the current node.

### 5. String constant `align 2` fragile [MEDIUM]

**File:** Text emitter output
**Reporter:** Rattler

`align 2` is minimum for current tag-bit scheme. No room for expansion.

**Fix:** Change to `align 8` for all string global constants.

### 6. CI `continue-on-error` on stage2 validation [HIGH]

**File:** `.github/workflows/ci.yml:75`
**Reporter:** Coral

Self-compilation failures masked.

**Fix:** Remove `continue-on-error: true` from stage2 validation step.

### 7. `mapanare run` no `-Wall` on gcc [MEDIUM]

**File:** `mapanare/cli.py:1027-1037`
**Reporter:** Anaconda

Most common developer command suppresses all gcc warnings.

**Fix:** Add `-Wall -Wextra` to `gcc_cmd` list.

### 8. `char_at` spec says Char, impl returns String [MEDIUM]

**File:** `docs/SPEC.md:1335`
**Reporter:** Coral

Spec says `(Int) -> Char`, impl returns `String` everywhere.

**Fix:** Update spec to say `(Int) -> String`.

---

## Verification

- [ ] TSan tests pass (signal thread safety)
- [ ] Valgrind on signal+map+stream program — no leaks
- [ ] `mapanare run demos/fizzbuzz.mn` compiles with `-Wall -Wextra`
- [ ] CI all green including stage2 (no `continue-on-error`)
- [ ] Spec `char_at` matches implementation
