# Mapanare v3.18.0 — "Macagua" (Container Memory Management + Arenas)

> Extend drop glue to lists, maps, signals, streams in both emitters.
> Enable per-function arenas for the first time (requested since v3.10.0).

**Status:** PLANNED
**Estimated scope:** Medium (2 sessions)
**Breaking:** No
**Prerequisite:** v3.17.0 (string drop glue pattern established in text emitter)

---

## Items

### 1. Container drop glue (lists/maps/signals/streams) [CRITICAL]

**Files:** `mapanare/emit_llvm_mir.py`, `mapanare/emit_llvm_text.py`
**Reporter:** Viper (C1)

Only strings and closures get drop glue. 4 of 7 heap types never freed by compiler.

**Fix:** Following the `_track_string` pattern:
- Add `_track_list`, `_track_map`, `_track_signal`, `_track_stream`
- Call `__mn_list_free` / `__mn_map_free_deep` / `__mn_signal_free` / `__mn_stream_free_chain` in drop glue
- Apply to BOTH emitters (llvmlite + text)

### 2. `__mn_list_push` silent reinit -> assertion [SMALL]

**File:** `runtime/native/mapanare_core.c:825-835`
**Reporter:** Viper (M11)

Now that list concat UB and COW races are fixed (v3.15.0), the defensive
reinit of garbage lists is no longer justified. Convert to assertion.

**Fix:** `abort()` with diagnostic in debug builds. Keep defensive behavior in release.

### 3. Enable per-function arenas [LARGE]

**File:** `mapanare/emit_llvm_mir.py:1926` and `mapanare/emit_llvm_text.py`
**Reporter:** Mamba (M1, 4th version requested)

Arena infrastructure exists (`_rt_arena_create`, `_rt_arena_destroy`,
`_arena_alloc_or_malloc`) but `_arena_ptr` is always `None`.

**Fix:** Conservative escape analysis:
1. For each function, identify all heap allocations (string temps, enum payloads)
2. If NO allocation escapes (not returned, not stored to globals, not passed out), enable arena
3. Start with: string temporaries in functions that return non-string types
4. Wire `_arena_ptr` to `_rt_arena_create` at function entry, `_rt_arena_destroy` at exit
5. Replace individual `__mn_str_free` calls with single arena destroy when arena is active

---

## Verification

- [ ] Compile list/map/signal/stream program, Valgrind — zero container leaks
- [ ] Arena-enabled functions show `arena_create`/`arena_destroy` in IR
- [ ] Benchmark: arena vs malloc on string-heavy function (expect measurable improvement)
- [ ] `/golden` — all pass
- [ ] `/culebra-scan` — no new findings
