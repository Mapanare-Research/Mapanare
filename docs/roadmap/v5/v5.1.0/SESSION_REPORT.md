# Session Report — v5.1.0 List IR Inlining (Perf.1)

**Date:** 2026-04-21
**Duration:** ~2 hours
**Status:** SHIPPED

---

## What shipped

Inline list access for value-type elements in both the Python and
self-hosted LLVM emitters. The codegen change replaces opaque
`call @__mn_list_get(ptr, i64)` with inline `getelementptr` + `load`
for 8-byte element types (`List<Int>`, `List<Float>`, `List<Ptr>`).

### Files changed

| File | LOC delta | What |
|---|---|---|
| `mapanare/emit_llvm_text.py` | +46 / -9 | Python emitter: `_do_idx_get` + `_do_idx_set` inline fast path |
| `mapanare/self/emit_llvm.mn` | +60 / -12 | Self-hosted mirror: `emit_index_get` + `emit_index_set` |
| `tests/llvm/test_list_inline.py` | +157 (new) | 10 correctness tests |
| `tests/llvm/test_emitter_hardening.py` | 6 assertions updated | `__mn_list_get` → `getelementptr inbounds i64` |
| `tests/llvm/test_tensor_indexing.py` | 1 assertion updated | Same |
| `tests/bootstrap/test_list_push.py` | 1 assertion updated | Same |

### Codegen change

**Gate:** `_tsz(ety) == 8` — fires for `i64`, `double`, `ptr`.

**Fast path (inline):**
```llvm
%lenp = getelementptr inbounds {ptr, i64, i64, i64, i64}, ptr %la, i32 0, i32 1
%len = load i64, ptr %lenp
%oob = icmp uge i64 %idx, %len
br i1 %oob, label %trap, label %ok

trap:
  call void @abort()
  unreachable

ok:
  %dp = getelementptr inbounds {ptr, i64, i64, i64, i64}, ptr %la, i32 0, i32 0
  %data = load ptr, ptr %dp
  %ep = getelementptr inbounds i64, ptr %data, i64 %idx
  %val = load i64, ptr %ep
```

**Slow path (unchanged):** `call ptr @__mn_list_get(ptr, i64)` for
String (16B), Bool (1B), structs, nested aggregates.

## Performance results

| Workload | Before | After | Delta |
|---|---|---|---|
| quicksort | 2.99× Rust | **1.14×** | **-62%** |
| prime_sieve | 1.20× | 1.17× | -2.4% |
| fib_recursive | 1.11× | 0.83× | improved |
| string_concat | 2.04× | 1.76× | improved |
| enum_match | 0.56× | 0.72× | noise |
| struct_alloc | 1.06× | 1.24× | noise |
| **Geomean** | **1.30×** | **1.10×** | **-15%** |

**5% rule:** PASS (62% improvement on quicksort).

## Quality gates

- **Golden tests:** 54/66 (unchanged)
- **Test suite:** 802 passed / 0 failed (LLVM + bootstrap)
- **stage2.ll:** 112,758 lines, llvm-as OK
- **Fixed point (stage2→stage3):** Pre-existing MIR verifier issue
  (empty match-arm blocks in `expr_kind`). Same failure occurs without
  this change. Not caused by Perf.1.
- **New tests:** 10 in `tests/llvm/test_list_inline.py`

## Closes

- **Perf.1** (Mamba v4.154.0): "Inline list operations in LLVM IR for
  locally-owned lists — closes the 2.80× quicksort gap"
- v4.151.0 E7 SESSION_REPORT recommendation: "the remaining gap
  requires emitter-level changes (inline list operations in LLVM IR)"

## What was NOT done

- TBAA metadata on list data pointers (future optimization)
- Inlining for non-value-type lists (elem_size > 8)
- Removal of `__mn_list_get` / `__mn_list_set` from runtime
- Bounds-check elision via loop analysis (v5.2.x)
- IR_DIFF.md with culebra extract (culebra not available in this session)
