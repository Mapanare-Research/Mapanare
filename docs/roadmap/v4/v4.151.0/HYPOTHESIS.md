# v4.151.0 E7 Hypothesis

## Lever ranking (safest first)

### Lever 1: Capacity doubling audit (no-op)

**Audit result:** Already correct. Line 1077 of `mapanare_core.c`:
```c
int64_t new_cap = list->cap > 0 ? list->cap * 2 : MN_LIST_INITIAL_CAP;
```
Doubling with `MN_LIST_INITIAL_CAP = 8`. No change needed.

### Lever 2: `realloc` for value-type lists

**Patch:** In `mn_list_grow`, when the buffer is managed (COW-headered) and
`elem_size <= 8` (value-type: Int, Float, Bool, Char), use `realloc` on
the COW header base (`data - 16`) instead of fresh-alloc + memcpy + free.

**Safety gate:** `elem_size <= 8` predicate. Post-Sh.2 (v4.131.0), value-type
elements have no pointer aliasing concern. The `mn_list_detach` call before
grow guarantees refcount == 1 (sole owner). Pointer-element lists
(`elem_size > 8`, e.g., `List<String>`, `List<MyStruct>`) keep the original
fresh-alloc path.

**Expected delta:** 5–15% on list-push-heavy workloads. `realloc` lets the
allocator extend in-place when possible, saving the `memcpy(old → new)` on
common-case grows. For 10K pushes with 12 grows, saves up to 16KB of
unnecessary copying.

**ABI impact:** None. Uses existing `elem_size` field as the value-type
predicate — no new fields added to `MnList`.

### Lever 3: Fast-path restructure of `__mn_list_push`

**Patch:** Restructure `__mn_list_push` to check the hot case first:
`data != NULL && len < cap && elem_size > 0` with `__builtin_expect`.
If true, inline the sole-owner check (COW header refcount ≤ 1) and
skip the full validation/corruption-recovery/COW-detach/grow logic.
Fall to slow path only for first push, grow, shared lists, or corruption.

**Expected delta:** 3–8% from eliminating per-push overhead of 7
validation conditions + `mn_list_detach` function call on the hot path.

**Risk:** Low. The slow path preserves all existing safety logic. The
fast path only fires when the list is demonstrably valid (data != NULL,
elem_size > 0, len < cap) and sole-owner (refcount ≤ 1).

## Why the target gap won't close fully

The quicksort benchmark is dominated by **list access** during the sort
phase (~130K `__mn_list_get` + `__mn_list_set` calls), not by list push
(~10K pushes during initialization). These list operations are opaque
function calls that LLVM cannot inline (the function bodies live in
`libmapanare_rt.a`, a separate compilation unit). To close the gap below
2× Rust, the emitter would need to emit inline list operations in the
LLVM IR — that's an emitter-level change for a future experiment (E8+),
not a runtime-only change.

Expected ceiling for runtime-only levers: **5–10% improvement on
quicksort**, bringing the ratio from 3.1× to ~2.9× Rust.
