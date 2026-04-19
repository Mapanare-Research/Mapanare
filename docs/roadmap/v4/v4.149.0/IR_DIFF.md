# v4.149.0 IR Diff — E5 ABI.1

## Return convention comparison: Mapanare v4.148.0 vs Clang vs Rust

### Reference C source

```c
struct S1 { long a; };               // 8 bytes
struct S2 { long a; long b; };       // 16 bytes
struct S3 { long a; long b; long c; }; // 24 bytes

struct S1 make_s1(long n) { struct S1 r = {n}; return r; }
struct S2 make_s2(long n) { struct S2 r = {n, n*2}; return r; }
struct S3 make_s3(long n) { struct S3 r = {n, n*2, n*3}; return r; }
long use_s2(struct S2 s) { return s.a + s.b; }
long use_s3(struct S3 s) { return s.a + s.b + s.c; }
```

### Function return signatures

| Type | Size | Clang SysV (x86_64-linux) | Clang Win64 | Clang AArch64 | Mapanare v4.148.0 |
|------|------|--------------------------|-------------|---------------|-------------------|
| `{i64}` | 8B | `i64 @f(i64)` | `i32 @f(i32)` | `i64 @f(i64)` | by value (no sret) |
| `{i64, i64}` | 16B | `{i64, i64} @f(i64)` | `i64 @f(i32)` | `[2 x i64] @f(i64)` | by value (no sret) |
| `{i64, i64, i64}` | 24B | **`void @f(ptr sret, i64)`** | **`void @f(ptr sret, i32)`** | **`void @f(ptr sret, i64)`** | **by value (no sret)** |

### Function argument passing

| Type | Size | Clang SysV | Clang Win64 | Clang AArch64 | Mapanare v4.148.0 |
|------|------|-----------|-------------|---------------|-------------------|
| `{i64, i64}` | 16B | decomposed: `i64, i64` | `i64` (packed) | `[2 x i64]` | by value |
| `{i64, i64, i64}` | 24B | **`ptr byval`** | **`ptr`** | **`ptr`** | **by value** |

### Mapanare concrete examples (SysV target)

**enum_match.mn — Shape = `{i64, i64, i64}` (24 bytes)**:
```llvm
; Mapanare v4.148.0: returns by value (LLVM backend converts to sret at machine level)
define internal {i64, i64, i64} @make_shape(i64 noundef %i) nounwind willreturn {
  ; ... insertvalue chains ...
  ret {i64, i64, i64} %__retval
}

; Clang SysV equivalent: explicit sret
define void @make_s3(ptr sret(%struct.S3) %0, i64 %1) {
  ; ... store to sret pointer ...
  ret void
}
```

**17_option.mn — Option<Int> = `{i1, i64}` (16 bytes)**:
```llvm
; Mapanare v4.148.0: returns by value (correct — ≤ 16 bytes on SysV)
define internal {i1, i64} @find_positive(i64 noundef %x) nounwind willreturn {
  ret {i1, i64} %val
}

; Clang SysV equivalent: also by value (correct — ≤ 16 bytes)
define {i64, i64} @make_s2(i64 %0) {
  ret {i64, i64} %val
}
```

**10_result.mn — Result<Int,String> = `{i1, {i64, {ptr, i64}}}` (32 bytes)**:
```llvm
; Mapanare v4.148.0: returns by value (should be sret — > 16 bytes on SysV)
define internal {i1, {i64, {ptr, i64}}} @divide(i64 noundef %a, i64 noundef %b) nounwind willreturn {
  ret {i1, {i64, {ptr, i64}}} %val
}
```

## Gap analysis

| Aggregate size | SysV correct convention | Mapanare v4.148.0 | Status |
|---------------|------------------------|-------------------|--------|
| ≤ 16 bytes | Register return | Register return | **Correct** |
| 17–64 bytes | sret | Register return (by value) | **Incorrect — LLVM backend fixes at machine level** |
| > 64 bytes | sret | sret (via `_BYREF_BYTES`) | **Correct** |

The 17–64 byte gap is harmless for same-module calls (LLVM's backend
inserts the correct machine-level convention regardless of IR
representation). The IR-level mismatch may inhibit some LLVM
optimizations that assume the ABI convention is correctly represented
in IR.

## Types affected by E5 fix (change from by-value to sret)

| Type | IR representation | Size | Effect |
|------|------------------|------|--------|
| 3-slot inline enum (Shape) | `{i64, i64, i64}` | 24B | by value → sret |
| Result<Int, String> | `{i1, {i64, {ptr, i64}}}` | 32B | by value → sret |
| Result<Int, Int> | `{i1, {i64, i64}}` | 24B | by value → sret |
| 4-slot inline enum | `{i64, i64, i64, i64}` | 32B | by value → sret |
| Boxed enum `{i64, ptr}` | `{i64, ptr}` | 16B | stays by value |
| Option<Int> `{i1, i64}` | `{i1, i64}` | 16B | stays by value |
| MnString `{ptr, i64}` | `{ptr, i64}` | 16B | stays by value |
