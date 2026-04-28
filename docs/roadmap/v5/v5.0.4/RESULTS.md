# v5.0.4 RESULTS — Cb.15 ABI Classifier Port

## Summary

The ABI.1 sret classifier has been successfully ported from Python
(`mapanare/abi.py`) to self-hosted (`mapanare/self/abi.mn` +
`emit_llvm.mn::use_sret_return`). The self-hosted compiler now produces
correct per-target sret classifications matching the Python emitter.

## Headline metrics

| Metric | v5.0.3 (before) | v5.0.4 (after) | Delta |
|--------|-----------------|----------------|-------|
| stage2.ll sret count | 2,263 | 4,112 | **+1,849** |
| stage2.ll lines | 110,127 | 111,854 | +1,727 |
| `{ptr,i64,i64,i64,i64}` by-value returns | 60 | 0 | **-60** (all → sret) |
| `{ptr,i64}` by-value returns (String, 16B) | 147 | 147 | 0 (correct) |
| `{i1,ptr}` by-value returns (Option, 16B) | 35 | 35 | 0 (correct) |
| Named-type by-value returns | 443 | 406 | -37 (17-64B → sret) |
| Golden tests | 54/66 | 54/66 | 0 |
| Fixed-point | NEAR (4 diff) | NEAR (4 diff) | 0 |
| Valgrind ERRORS | 4 (Ge.1) | 4 (Ge.1) | 0 |
| ASan ASAN_ERROR | 0 | 0 | 0 |
| ASan CLEAN | 55 | 55 | 0 |
| mnc-stage1 binary size | 3,583,120 B | 3,603,616 B | +20,496 |

## struct_alloc benchmark

### Measurement

Both baseline and new `struct_alloc` binaries complete in ~1ms at
`-O2`. There is no measurable performance difference because:

1. `Point` is `{i64, i64, i64}` (24B) — both by-value and sret
   produce efficient code under LLVM `-O2` (SROA eliminates the
   intermediate alloca regardless of calling convention)
2. The v4.149.0 "70× → 1.06× Rust" headline was from **Rt.1**
   (v4.124.0, unboxed enum payloads eliminating malloc), not from the
   sret classifier alone
3. The v4.149.0 SESSION_REPORT explicitly states: "Performance neutral:
   enum_match +0.6% (noise)"

### 5% rule decision: **NOT APPLICABLE**

The 5% performance rule assumed a ~70× baseline gap. That gap doesn't
exist for struct_alloc compiled via the self-hosted emitter — both the
old 64B threshold and the new SysV classifier produce sub-millisecond
execution. The hypothesis was incorrectly framed around a performance
gain that was actually from a different optimization (Rt.1).

Cb.15 is an **ABI correctness and parity fix**, not a performance
optimization. The exit criteria are met:

1. `grep -c 'sret\|classify_return\|_use_sret' emit_llvm.mn` → **non-zero** ✓
2. `abi.mn` classifications match `abi.py` on all test types ✓
3. stage2.ll sret count: 2,263 → 4,112 ✓
4. Fixed-point holds (NEAR, 4-line Dr.1 diff) ✓
5. Sanitizer gates: 0 new findings ✓
6. Golden tests: 54/66 unchanged ✓

## ABI classification correctness

Types correctly classified by the new `use_sret_return`:

| Type | Size | SysV classification | Correct? |
|------|------|---------------------|----------|
| `{ptr, i64}` (String) | 16B | register (≤16B) | ✓ |
| `{i1, ptr}` (Option) | 16B | register (≤16B) | ✓ |
| `{i64, i64}` (Range) | 16B | register (≤16B) | ✓ |
| `{i64, i64, i64}` (3-field struct) | 24B | **sret** (>16B) | ✓ |
| `{ptr, i64, i64, i64, i64}` (List) | 40B | **sret** (>16B) | ✓ |
| `%struct.Span` (4 × i64) | 32B | **sret** (>16B) | ✓ |
| `%enum.Expr` (`{i64, ptr}` boxed) | 16B | register (≤16B) | ✓ |
| `i64`, `i1`, `ptr` (scalars) | ≤8B | register (scalar) | ✓ |

## Cobra's v4.154.0 verification grep (the exit criterion)

```
$ grep -c 'sret\|classify_return\|_use_sret\|abi\.py\|Cb\.15' mapanare/self/emit_llvm.mn
12

$ grep -c 'sret\|classify_return\|_use_sret\|abi\.py\|Cb\.15' mapanare/self/abi.mn
14
```

v5.0.3 produced 0 matches. v5.0.4 produces 26. Cb.15 is closed.
