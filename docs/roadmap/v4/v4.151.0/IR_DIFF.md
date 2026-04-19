# v4.151.0 E7 IR Diff

## §1 Mapanare `__mn_list_push` vs Rust `Vec::push`

### Mapanare — `runtime/native/mapanare_core.c` (v4.151.0, post-E7)

```c
// Hot path (E7-L3): valid sole-owner list with capacity
MN_EXPORT void __mn_list_push(MnList *list, const void *elem_ptr) {
    if (__builtin_expect(list->data != NULL && list->len < list->cap
                         && list->elem_size > 0, 1)) {
        if (list->managed) {
            int64_t *hdr = ((int64_t *)list->data) - 2;
            if (hdr[0] == MN_COW_MAGIC
                && __atomic_load_n(&hdr[1], __ATOMIC_ACQUIRE) > 1)
                goto slow_path;                     // ← shared, rare
        }
        memcpy(dst, elem_ptr, elem_size);           // ← hot: 1 store
        list->len++;
        return;
    }
slow_path:
    // validation + first-push init + COW detach + grow (mn_list_grow)
    // ...
}
```

**Hot path cost:** 3 compares + 1 managed check + 2 header reads + 1
atomic load + 1 memcpy + 1 increment = ~8 operations per push.

### Rust — `alloc/src/vec/mod.rs` (nightly 2025-05)

```rust
#[inline]
pub fn push(&mut self, value: T) {
    if self.len == self.buf.capacity() {
        self.buf.reserve_for_push(self.len);        // ← cold path
    }
    unsafe {
        let end = self.as_mut_ptr().add(self.len);
        ptr::write(end, value);                     // ← hot: 1 store
        self.len += 1;
    }
}
```

**Hot path cost:** 1 compare + 1 ptr::write + 1 increment = 3 operations
per push. No COW, no managed check, no atomic load.

### Lever sites annotated

1. **Lever 2 site (realloc):** Inside `mn_list_grow`, the grow path.
   Pre-E7: `mn_list_alloc_buf + memcpy + free`. Post-E7: `realloc` on
   COW header base when `managed && elem_size <= 8`.

2. **Lever 3 site (fast path):** The `__builtin_expect` branch at the
   top of `__mn_list_push`. Pre-E7: all pushes went through 7 validation
   conditions + `mn_list_detach` function call. Post-E7: hot case
   (data valid, len < cap, sole owner) skips both.

## §2 Remaining gap analysis

The per-push overhead gap (8 ops vs 3 ops) explains the ~3× ratio.
The extra 5 operations are:
1. `elem_size > 0` check — Rust knows the type at compile time
2. `managed` check — Rust has no COW
3. COW header magic read — no analog in Rust
4. Atomic refcount load — no analog in Rust
5. `memcpy(dst, src, elem_size)` vs `ptr::write` — Rust stores directly

Operations 2–4 are the COW tax. The COW system enables O(1) list clone
and safe sharing, which Rust solves differently (ownership + borrow
checker). Removing COW from the hot path requires emitter-level changes
(emit inline stores when the compiler can prove sole ownership).

**Emitter-level optimization (future E8+):** The Python emitter could emit
direct `store` + `getelementptr` instructions for `push` on locally-owned
lists, bypassing the runtime call entirely. This would match Rust's codegen.
