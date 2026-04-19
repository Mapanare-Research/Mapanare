# E4 IR + Runtime Diff — `string_concat`

## Mapanare inner loop (MIR → LLVM IR)

The MIR `string_concat_optimization` pass (v4.108.0) correctly detects
the `s = s + "hello"` loop pattern and rewrites it to StringBuilder:

```
entry:
  %sb = call ptr @__mn_sb_new(i64 64)
  call void @__mn_sb_append(ptr %sb, {ptr, i64} %result)
  br label %while_header0

while_body1:                            ; <-- hot loop
  call void @__mn_sb_append(ptr %sb, {ptr, i64} {"hello", 5})
  %i = add nsw i64 %i, 1
  br label %while_header0

while_exit2:
  %result = call {ptr, i64} @__mn_sb_finish(ptr %sb)
```

After LLVM `opt -O2`, the loop body is a single call to
`__mn_sb_append` plus an integer increment. The IR structure is correct.

## Rust inner loop

```rust
let mut result = String::new();
for _ in 0..10000 {
    result.push_str("hello");
}
```

Rust's `String::push_str` compiles down to `Vec<u8>::extend_from_slice`,
which checks `self.len + 5 <= self.capacity`, and if so, does a 5-byte
memcpy + length increment inline. Growth uses `realloc` via the global
allocator.

## Runtime path analysis — the bottleneck

The performance gap is NOT in the IR structure (both are 1 call per
iteration). The gap is in the **runtime implementation** of
`mn_sb_grow` in `mapanare_core.c:487`:

```c
static void mn_sb_grow(MnStringBuilder *sb, int64_t needed) {
    int64_t new_cap = sb->cap;
    while (new_cap < needed) new_cap *= 2;
    char *new_buf = (char *)__mn_alloc(new_cap);   // <-- calloc!
    if (sb->len > 0) memcpy(new_buf, sb->buf, sb->len);
    __mn_free(sb->buf);
    sb->buf = new_buf;
    sb->cap = new_cap;
}
```

**Problem 1: `__mn_alloc` is `calloc`.** It zero-initializes the entire
new buffer. For the last growth event (32768 → 65536 bytes), this zeros
64 KB just to immediately overwrite ~25 KB of it with memcpy. Rust's
allocator does not zero on growth.

**Problem 2: `calloc` + `memcpy` + `free` instead of `realloc`.** The
C library's `realloc` can often extend the allocation in-place without
copying. When it can't, it does exactly one `malloc` + `memcpy` + `free`
— but crucially, `malloc` does NOT zero-initialize. The current code
always copies and always zeros.

**Problem 3: `__mn_sb_to_string` shrink-to-fit.** When the builder
finishes, it `calloc`s a tight buffer if capacity > 2× length, copies
again, and frees the oversized buffer. This is another unnecessary
alloc+copy+free cycle using calloc.

## Growth events for this benchmark

Appending "hello" (5 bytes) × 10,000 = 50,000 bytes total.
Starting capacity: 64.

| Growth # | Old cap | New cap | Bytes copied | Bytes zeroed (calloc) |
|----------|---------|---------|-------------|-----------------------|
| 1 | 64 | 128 | 64 | 128 |
| 2 | 128 | 256 | 128 | 256 |
| 3 | 256 | 512 | 256 | 512 |
| 4 | 512 | 1024 | 512 | 1024 |
| 5 | 1024 | 2048 | 1024 | 2048 |
| 6 | 2048 | 4096 | 2048 | 4096 |
| 7 | 4096 | 8192 | 4096 | 8192 |
| 8 | 8192 | 16384 | 8192 | 16384 |
| 9 | 16384 | 32768 | 16384 | 32768 |
| 10 | 32768 | 65536 | 32768 | 65536 |
| **Total** | | | **65,534** | **130,942** |
| + shrink-to-fit | | 50001 | 50000 | 50001 |
| **Grand total** | | | **115,534** | **180,943** |

The runtime copies ~116 KB and zeros ~181 KB for a 50 KB result. With
`realloc`, many of these copies become in-place extensions, and zero
of the zeroing happens.

## Conclusion

The IR is structurally correct. The bottleneck is `mn_sb_grow` using
`calloc` + `memcpy` + `free` instead of `realloc`. Fix the growth
function to use `realloc`, remove the shrink-to-fit calloc in
`__mn_sb_to_string`, and use `malloc` instead of `calloc` for initial
buffer allocation.
