# v4.147.0 IR Diff — E3 (parameter-level noalias)

## Key Finding

**LLVM `noalias` only applies to pointer-typed parameters.** Mapanare passes
List/Struct/Map/String/Enum as aggregates by value when the LLVM type
is under 64 bytes (`_BYREF_BYTES = 64`). None of the target benchmark
functions have `ptr`-typed user parameters. `noalias` is structurally
inapplicable to the target workloads.

| Type | LLVM repr | Size | Passed as | `noalias` applicable? |
|---|---|---:|---|---|
| `List<Int>` | `{ptr, i64, i64, i64, i64}` | 40 bytes | by value | **No** (aggregate) |
| `String` | `{ptr, i64}` | 16 bytes | by value | **No** (aggregate) |
| `Enum` | `{i64, ptr}` | 16 bytes | by value | **No** (aggregate) |
| `Point` struct | `{i64, i64, i64}` | 24 bytes | by value | **No** (aggregate) |
| `Int` | `i64` | 8 bytes | by value | **No** (scalar) |
| `Bool` | `i1` | 1 byte | by value | **No** (scalar) |
| closure env | `ptr` | 8 bytes | by ref | **Yes** (pointer) |

## partition() — quicksort hot loop

**Mapanare:**
```llvm
define internal noundef i64 @partition(
    {ptr, i64, i64, i64, i64} %arr,   ; <-- aggregate, not pointer
    i64 noundef %lo,
    i64 noundef %hi
) nounwind willreturn {
```

**Rust:**
```llvm
define internal fastcc void @qsort(
    ptr noalias noundef nonnull readonly align 8 captures(none) dereferenceable(24) %arr,
    i64 noundef %lo,
    i64 noundef %hi
) unnamed_addr {
```

Rust passes `&mut Vec<i64>` as a single `ptr` with rich attributes:
`noalias`, `nonnull`, `readonly`, `captures(none)`, `dereferenceable(24)`.
Mapanare passes `List<Int>` as a 40-byte aggregate value. The
representation difference is fundamental: `noalias` is a parameter
attribute for pointer types only.

**Vectorization remark (Mapanare):**
```
loop not vectorized: control flow cannot be substituted for a select
loop not vectorized: value used outside the loop
loop not vectorized: instruction cannot be vectorized
```
The barrier is control flow (conditional swap in partition), not aliasing.

## is_prime() — prime_sieve hot loop

**Mapanare:**
```llvm
define internal noundef i1 @is_prime(i64 noundef %n)
    nofree nosync nounwind willreturn memory(none) {
```

**Rust:**
```llvm
; Inlined into main — no standalone function in optimized IR
```

All-scalar signature. Already marked `memory(none)` by E2 purity pass.
No pointer parameters at all — `noalias` is meaningless here.

**Vectorization remark (Mapanare):**
```
loop not vectorized: could not determine number of loop iterations
```
The barrier is unknown trip count (`d * d <= n`), not aliasing.

## make_point() + main loop — struct_alloc hot loop

**Mapanare:**
```llvm
define internal void @main() nounwind willreturn {
  ; loop body calls make_point(i) which returns {i64, i64, i64}
  ; then sums fields — no pointer params in the loop
```

All-scalar function parameters. The loop body is a function call
(`make_point`) returning a struct by value. No vectorization remarks
emitted — the loop body isn't vectorizable regardless of aliasing
because it contains a function call.

## Across the golden corpus

Scanned all 66 golden programs for user-defined functions with `ptr`
parameters. Only found:
- **Closure environment pointers** (`ptr %__env_ptr`) — these are
  candidates for `noalias` but closures are not present in the
  target benchmarks.
- **sret pointers** — already marked `noalias` since v4.84.0.

No benchmark function has byref (`ptr`) user parameters.

## Conclusion

Parameter-level `noalias` is the wrong lever for these workloads.
The performance gaps are driven by:
1. **By-value aggregate passing** (40-byte List copies vs Rust's 8-byte pointer)
2. **Control flow complexity** (partition swap branches)
3. **Unknown loop trip counts** (prime sieve `d*d <= n`)
4. **Function calls in loop bodies** (struct_alloc `make_point`)

The correct fix for #1 is ABI.1 (v4.149.0 E5), not `noalias`.
