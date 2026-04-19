# v4.151.0 E7 Baseline

## Target workload: quicksort (10K list pushes + sort)

The cross-language `quicksort` benchmark is the only corpus workload that
exercises `__mn_list_push` (10,000 pushes to build the array, then quicksort
on the result). `list_ops.mn` is actually a prime sieve (no lists),
`struct_alloc.mn` allocates structs inline (no lists).

### v4.150.0 baseline (30-run tight median)

| Language | Wall (ms) | Peak RSS (KB) |
|----------|--------:|--------:|
| C (gcc -O2) | 0.356 | 1,928 |
| C (clang -O2) | 0.352 | 1,920 |
| Rust -O | 0.379 | 2,412 |
| Go | 0.400 | 2,532 |
| **Mapanare O2** | **1.187** | **2,444** |
| Python 3.12 | 83.564 | 13,868 |

**Mapanare / Rust ratio: 3.13×**

### Full corpus baseline (Mapanare O2, 15-run median)

| Benchmark | Wall (ms) |
|-----------|--------:|
| fib_recursive | 15.4 |
| quicksort | 1.19 |
| struct_alloc | 0.021 |
| enum_match | 0.17 |
| prime_sieve | 2.09 |
| string_concat | 0.079 |

### Allocation trace (quicksort, 10K pushes)

- Initial capacity: `MN_LIST_INITIAL_CAP = 8`
- Growth pattern: **doubling** (`cap * 2` at line 1077)
- Grows: 8 → 16 → 32 → 64 → 128 → 256 → 512 → 1,024 → 2,048 → 4,096 → 8,192 → 16,384
- Total grows: **12** for 10,000 pushes
- Total bytes copied (pre-E7): 8+16+32+64+128+256+512+1,024+2,048+4,096+8,192 = **16,376 bytes**
- Pre-E7 grow path: `mn_list_alloc_buf` (fresh malloc + COW header) → `memcpy` → `__mn_free` old buffer
- Each grow: 1 malloc + 1 memcpy + 1 free

### Sort phase dominance

The quicksort partition does ~N·log₂N ≈ 130,000 comparisons/swaps.
Each swap calls `__mn_list_get` (2×) + `__mn_list_set` (2×). These are
opaque function calls in the linked binary — LLVM cannot inline them.
The sort phase dominates the benchmark time; the push phase is ~15% of total.
