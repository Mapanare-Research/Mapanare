# Hypothesis — v5.1.0 List IR Inlining (Perf.1)

**Date:** 2026-04-21
**Author:** Claude (Opus 4.6) + Juan Denis
**Status:** TESTING

---

## Target workload

**Primary:** `benchmarks/cross_language/quicksort.mn` — 10K-element
list sort with ~130,000 `__mn_list_get`/`__mn_list_set` calls per run.

**Secondary:** `benchmarks/cross_language/prime_sieve.mn` — list-index-
heavy inner loop.

## Baseline (v4.153.0 / v5.0.6)

| Workload | Mapanare (ms) | Rust (ms) | Ratio |
|---|---|---|---|
| `quicksort` | 1.102 | 0.368 | **2.99×** |
| `prime_sieve` | — | — | **1.20×** |
| `fib_recursive` | — | — | 1.11× |
| `enum_match` | — | — | 0.56× |
| `struct_alloc` | — | — | 1.06× |
| `string_concat` | — | — | 2.04× |
| **Geomean** | | | **1.21×** (Bn.2-corrected) |

The 1.21× geomean uses the corrected computation from v5.0.6 Bn.2
(Mamba's v4.154.0 recomputation), not the earlier-reported 1.17×.

## Hypothesis

Inlining `__mn_list_get` and `__mn_list_set` as LLVM IR
(`getelementptr` + `load`/`store`) for `elem_size == 8` value-type
lists will let LLVM see through to the backing buffer, enabling:

1. **SROA** — decompose list-header allocas into scalar SSA values
2. **Loop vectorization** — autovectorize tight index loops now that
   the loop body is visible (no opaque function call barrier)
3. **Load hoisting** — hoist `data` pointer load out of loops when
   the list is not mutated (TBAA metadata enables this)
4. **Dead bounds-check elimination** — LLVM's ScalarEvolution can
   prove `i < len` when the loop is `for i in range(len(arr))`,
   eliminating the inline bounds check entirely

Currently, every `arr[i]` compiles to:
```llvm
%ptr = call ptr @__mn_list_get(ptr %list_alloca, i64 %idx)
%val = load i64, ptr %ptr
```

The `call` is an optimization barrier — LLVM cannot inline across
the C runtime boundary without LTO. After this change:
```llvm
; Inline bounds check (foldable by ScalarEvolution)
%len_ptr = getelementptr inbounds {ptr, i64, i64, i64, i64}, ptr %la, i32 0, i32 1
%len = load i64, ptr %len_ptr
%oob = icmp uge i64 %idx, %len
br i1 %oob, label %trap, label %ok

trap:
  call void @abort()
  unreachable

ok:
  %data_ptr = getelementptr inbounds {ptr, i64, i64, i64, i64}, ptr %la, i32 0, i32 0
  %data = load ptr, ptr %data_ptr
  %elem_ptr = getelementptr inbounds i64, ptr %data, i64 %idx
  %val = load i64, ptr %elem_ptr
```

## Patch sketch

~60 LOC in `mapanare/emit_llvm_text.py` (`_do_idx_get` + `_do_idx_set`):
- Gate on `_tsz(ety) == 8` (covers `List<Int>`, `List<Float>`,
  `List<Ptr>`)
- Emit inline GEP sequence for data access
- Emit inline bounds check with `abort()` trap
- Fall back to `call @__mn_list_get` for all other element sizes
  (String at 16B, structs, nested aggregates)

~60 LOC mirror in `mapanare/self/emit_llvm.mn` for parity.

## Expected outcome

- **quicksort:** 2.99× → ≤ 1.50× Rust
- **prime_sieve:** 1.20× → ≤ 1.05× Rust
- **Geomean:** 1.21× → ≤ 1.05× Rust
- **Non-target workloads:** ≤ 2% regression each (fib_recursive,
  enum_match, struct_alloc, string_concat)

## 5% rule

quicksort must improve by ≥ 5% to ship. If it doesn't, revert the
emitter change entirely, keep `__mn_list_get` as the sole code path,
and mark Perf.1 as "attempted and reverted."

## Non-target watch list

| Workload | Baseline ratio | Max acceptable regression |
|---|---|---|
| `fib_recursive` | 1.11× | ≤ 2% |
| `enum_match` | 0.56× | ≤ 2% |
| `struct_alloc` | 1.06× | ≤ 2% |
| `string_concat` | 2.04× | ≤ 2% |

These workloads do not use list indexing in their hot loops, so
regression would indicate a systemic codegen problem (not expected).

## Risks

**R1 — Memory safety via skipped COW detach.**
The current `IndexSet` path already uses `__mn_list_get` + direct
store (no `mn_list_detach`). The MIR ownership tracking from v4.131.0
ensures sole ownership before mutation. Inlining doesn't change this
invariant — it just makes the same store visible to LLVM.

**R2 — Fixed-point break.**
Emitter changes always risk this. Mitigated by mirroring into
self-hosted simultaneously and running `verify_fixed_point.sh`.

**R3 — LLVM alias confusion.**
Inlining exposes `ptr` loads that were hidden behind the opaque call.
If LLVM's alias analysis incorrectly hoists a data-pointer load
across a `__mn_list_push` that reallocates, the hoisted load would
read a stale pointer. Mitigated by: (a) push invalidates the list
alloca, so LLVM sees the store; (b) the inline load is from a fresh
GEP off the alloca, not a cached value.

**R4 — Bool/Char element type mismatch.**
`List<Bool>` has `elem_size=1` at runtime but the inline path
requires `elem_size==8`. The gate (`_tsz(ety) == 8`) ensures these
fall to the opaque call path. No risk.
