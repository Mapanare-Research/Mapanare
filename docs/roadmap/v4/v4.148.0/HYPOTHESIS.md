# E4 Hypothesis

**Claim:** `mn_sb_grow` uses `calloc` + `memcpy` + `free` where
`realloc` suffices. The unnecessary zero-initialization and missed
in-place growth account for most of the 33× gap vs Rust. Switching to
`realloc` and removing the shrink-to-fit copy in `__mn_sb_to_string`
will close ≥ 60% of the gap.

## Current path

```
__mn_sb_new(64)          → calloc(64)
__mn_sb_append × 10000:
  mn_sb_grow:            → calloc(new_cap) + memcpy(old) + free(old)
                           ~10 growth events, 181 KB zeroed, 116 KB copied
__mn_sb_finish:
  __mn_sb_to_string:     → calloc(exact) + memcpy + free(oversized)
                           another 50 KB zeroed + 50 KB copied
```

## Proposed path

```
__mn_sb_new(64)          → malloc(64)
__mn_sb_append × 10000:
  mn_sb_grow:            → realloc(new_cap)
                           ~10 growth events, 0 KB zeroed
                           many may extend in-place (0 copy)
__mn_sb_finish:
  __mn_sb_to_string:     → realloc(exact)
                           may shrink in-place (0 copy)
```

## What changes

1. `__mn_sb_new`: use `malloc` instead of `__mn_alloc` (calloc) for
   the initial buffer.
2. `mn_sb_grow`: replace `calloc` + `memcpy` + `free` with `realloc`.
3. `__mn_sb_to_string` shrink-to-fit: replace `calloc` + `memcpy` +
   `free` with `realloc`.
4. `__mn_sb_create` (by-value API): same changes for consistency.

## What does NOT change

- `MnString` struct layout: still `{ptr, i64}` (no capacity field).
- `__mn_str_concat`: unchanged (the MIR pass already rewrites loops
  to StringBuilder; standalone concats outside loops stay as-is).
- Interning, hashing, `_lenheap` bit-63 packing: untouched.
- User-visible String API: unchanged.

## Expected delta

- Wall time: ≥ 60% reduction (from ~1.5 ms toward ~0.3–0.5 ms)
- Target: ≤ 10× of Rust (from 33×); stretch ≤ 5×
- Allocation count: ~12 → ~12 (same count, but realloc vs calloc+free)
- Bytes zeroed: ~181 KB → 0 KB
- Bytes copied: ~116 KB → much less (realloc extends in-place)
