# Mapanare v4.100.0 — Fix Tagged-Pointer UB in MnString

> **Phase A release 1.** The v4.99.0 panel returned 6.59/10 with 3 NEEDS
> WORK. Option B: continue v4.100.0+. The #1 blocker, unanimous across
> all 7 reviewers, is the tagged-pointer undefined behavior in
> `mapanare_core.c`. `mn_tag_heap` sets bit 0 of `char*` pointers; LLVM
> exploits this at -O2, producing garbled strings from mnc-stage1. This
> release removes the bit-tagging and replaces it with an explicit
> `int8_t is_heap` field in the `MnString` struct.

**Status:** PARTIAL — tagged-pointer UB eliminated via bitfield; golden-test verification blocked by pre-existing self-hosted-emitter bug (deferred to v4.101.0).
**Breaking:** No
**Prerequisite:** v4.99.0
**Delta review:** No
**Full panel:** No (v4.106.0)
**Estimated work:** 1 sprint
**Theme:** Eliminate tagged-pointer undefined behavior — the single highest-impact fix from the v4.99.0 docket.

---

## Scope

The `MnString` struct in `runtime/native/mapanare_core.c` uses a tagged-pointer scheme to distinguish heap-allocated strings from arena/static strings. `mn_tag_heap` ORs bit 0 into the `char*` data pointer; `mn_is_heap` checks bit 0; `mn_untag` masks it off. This is undefined behavior: a `char*` with bit 0 set is not a valid pointer, and LLVM's optimizer at -O2 is free to exploit this — and does. The result: mnc-stage1 compiled with -O2 produces garbled string output.

The fix is structural: add an `int8_t is_heap` field to the `MnString` struct and remove the bit-tagging functions entirely. Every site that constructs an `MnString`, checks its heap status, or untags its data pointer must be updated. After the fix, mnc-stage1 must compile cleanly with -O2 and produce correct string output.

This is the single most impactful fix from the v4.99.0 panel docket. Rattler, Viper, and Mamba all identified it as the root cause of binary corruption. Fixing it unblocks golden test verification, fixed-point validation, and async linking.

## Phase 1 — Audit the tagged-pointer API

- [ ] Read `runtime/native/mapanare_core.c` — find `mn_tag_heap`, `mn_is_heap`, `mn_untag` functions
- [ ] Read `runtime/native/mapanare_core.h` — find the `MnString` struct definition
- [ ] Grep for all callers of `mn_tag_heap`, `mn_is_heap`, `mn_untag` across the entire codebase
- [ ] Grep for all construction sites of `MnString` (struct literal initialization, malloc + field assignment)
- [ ] Document every call site in a scratch list — this is the migration surface

## Phase 2 — Replace bit-tagging with `is_heap` field

- [ ] Add `int8_t is_heap` field to the `MnString` struct definition in `mapanare_core.h`
- [ ] Remove `mn_tag_heap` function/macro entirely
- [ ] Remove `mn_is_heap` function/macro — replace with direct field access `s.is_heap` or `s->is_heap`
- [ ] Remove `mn_untag` function/macro — the data pointer is now always valid, no untagging needed
- [ ] Update every `MnString` construction site:
  - Heap allocations: set `is_heap = 1`
  - Arena/static allocations: set `is_heap = 0`
- [ ] Update every tag-check site: replace `mn_is_heap(s)` with `s.is_heap` (or `s->is_heap`)
- [ ] Update every untag site: replace `mn_untag(s.data)` with `s.data`
- [ ] Verify no raw bit manipulation of string data pointers remains

## Phase 3 — Update callers across the codebase

- [ ] Grep for all callers found in Phase 1 — verify each has been updated
- [ ] Check `runtime/native/mapanare_runtime.c` for any string construction or tag checks
- [ ] Check `runtime/native/mapanare_agent.c` (if it touches strings)
- [ ] Check `runtime/native/mapanare_string.c` (if it exists) for string helper functions
- [ ] Check `mapanare/emit_llvm_text.py` — the LLVM emitter may generate code that assumes the old MnString layout. Update struct type definitions in emitted IR if needed
- [ ] Check `mapanare/self/emit_llvm.mn` — the self-hosted emitter may also reference MnString layout
- [ ] Verify no test files reference the old API

## Phase 4 — Rebuild mnc-stage1 with -O2

- [ ] Rebuild: `python scripts/build_stage1.py`
- [ ] Compile with `-O2`: verify clang accepts the IR without warnings
- [ ] Run a string-heavy golden test (e.g., `tests/golden/01_hello.mn` or any test that prints strings)
- [ ] Verify output is NOT garbled — this is the primary success criterion
- [ ] Run `tests/golden/03_struct.mn` (struct with string fields)
- [ ] Run `tests/golden/15_string_methods.mn` (if it exists) or any string-intensive test

## Phase 5 — Run all 61 golden tests

- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Record pass count: target is 61/61 but any improvement over the 0/61 reported by Anaconda is progress
- [ ] For any failures, note whether the failure is string-related (fixed by this release) or a different bug (deferred to v4.101.0+)

## Phase 6 — Valgrind + ASan

- [ ] Valgrind on mnc-stage1 compiling `tests/golden/01_hello.mn`:
  ```bash
  valgrind --leak-check=full ./mapanare/self/mnc-stage1 tests/golden/01_hello.mn
  ```
- [ ] AddressSanitizer: rebuild with `-fsanitize=address` and run the same test
- [ ] Record results — target is zero UB-related errors (some pre-existing leaks may remain)

## Phase 7 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.100.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `int8_t is_heap` field added to `MnString` struct | diff of `mapanare_core.h` |
| 2 | `mn_tag_heap` function/macro removed | grep confirms no hits |
| 3 | `mn_is_heap` and `mn_untag` removed or replaced | grep confirms no hits for old API |
| 4 | All callers updated to use `is_heap` field | grep audit of construction + check sites |
| 5 | mnc-stage1 compiles with `-O2` without warnings | build log |
| 6 | String output from mnc-stage1 is correct (not garbled) | golden test output |
| 7 | Golden pass count recorded (target: 61/61) | test log |
| 8 | Valgrind: zero UB-related errors on string test | valgrind output |
| 9 | ASan: zero UB-related errors on string test | ASan output |

---

## What this release does NOT do

- **Fix list indexing** — that is v4.101.0.
- **Fix async linking** — that is v4.102.0.
- **Touch the emitter logic** — only MnString layout and its callers change. Emitter changes are limited to struct type definitions if the emitted IR references MnString by layout.
- **Optimize string performance** — the string_concat benchmark (2.2x slower than Python) is a separate issue. This release fixes correctness, not performance.
- **Run a panel** — Phase A has no panel. The next panel is v4.106.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| MnString layout change breaks ABI for anything depending on struct size | medium | high | Grep for `sizeof(MnString)` and hardcoded offsets; update all references |
| Emitted LLVM IR references old MnString layout by field index | medium | high | Audit `emit_llvm_text.py` and `emit_llvm.mn` for GEP instructions into MnString; update indices |
| Adding `is_heap` increases MnString size, causing alignment issues | low | medium | `int8_t` adds 1 byte; padding may absorb it. Check `sizeof` before and after. |
| Some callers use the tagged pointer for purposes beyond heap detection | low | medium | Phase 1 audit catches all uses; grep is comprehensive |
| Valgrind shows pre-existing leaks unrelated to this fix | high | low | Document pre-existing leaks separately; focus on UB-related errors only |

---

## After v4.100.0

v4.101.0 fixes the list indexing bug (docket item #2). `data[j]` returns garbage in certain contexts despite working in quicksort. The root cause is likely a GEP or load with wrong type/index in the emitter. After v4.101.0, two of the five critical/high docket items from the v4.99.0 panel will be closed.
