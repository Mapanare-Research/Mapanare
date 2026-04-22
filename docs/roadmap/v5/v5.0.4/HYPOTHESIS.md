# v5.0.4 HYPOTHESIS — Cb.15 ABI Classifier Port

> Written before any code edit. This prevents post-hoc rationalization.

## Target workload

`benchmarks/system/struct_alloc.mn` compiled via `mnc-stage1`
(self-hosted compiler), not the Python bootstrap.

## Baseline (v5.0.3)

### struct_alloc via mnc-stage1

```
make_point signature: define %struct.Point @make_point(i64 %i) nounwind willreturn {
call to make_point:    %t8 = call %struct.Point @make_point(i64 %i_val7)
sret count in struct_alloc.ll: 0
```

`Point` is `{i64, i64, i64}` = 24 bytes. On SysV AMD64 (the self-
hosted compiler's hardcoded target), 24B > 16B → should use sret.
Currently returned by value because `is_byref_type_st` uses a 64B
threshold.

### stage2.ll (self-compiling compiler)

```
stage2 lines:   110,127
stage2 sret:    2,263 (all from types > 64B)
by-value aggregate returns: 242 functions total
  {ptr, i64}               = 16B × 147 fns → register (correct)
  {ptr, i64, i64, i64, i64} = 40B ×  60 fns → should be sret (GAP)
  {i1, ptr}                 = 16B ×  35 fns → register (correct)
```

60 functions return `List<T>` (40B) by value — these should all be
sret on SysV. This is the self-compilation gap.

## Hypothesis

Porting `abi.py`'s `classify_return` to `mapanare/self/abi.mn` and
wiring it into `emit_llvm.mn` (replacing the 64B `is_byref_type_st`
threshold for return types only) will:

1. Flip 60 functions in stage2.ll from by-value to sret (List returns)
2. Flip `make_point` in struct_alloc.ll from by-value to sret
3. Reproduce the Python emitter's struct_alloc performance win
   (70× Rust → ~1.06× Rust) for self-compiled programs

The mechanism: `sret` eliminates `insertvalue`/`extractvalue` chains
for 17-64B aggregates. For struct_alloc specifically, `Point` (24B)
no longer needs caller-side aggregate construction — LLVM can
optimize the sret pointer to direct stores into the destination.

## Patch sketch

- **New file** `mapanare/self/abi.mn` (~80-100 LOC):
  - `fn type_byte_size_for_abi(st: EmitState, ty: String) -> Int`
  - `fn use_sret_return(st: EmitState, ty: String) -> Bool` — SysV:
    aggregate > 16B → true
  - Win64 + AArch64 classifiers present but not wired (target triple
    is hardcoded to x86_64-unknown-linux-gnu)
- **Edit** `mapanare/self/emit_llvm.mn` — 4 sites:
  - `emit_mir_function:3402` — function header sret decision
  - `emit_call (registered):2952` — call-site sret
  - `emit_call (unregistered):2973` — call-site sret
  - `emit_return:3141` — return store-to-sret
- **Edit** `scripts/concat_self.sh` — add `abi.mn` before `emit_llvm.mn`

## Expected outcome

- struct_alloc via `mnc-stage1`: **≤ 1.5× Rust** (from ~70× baseline)
- stage2.ll sret count: 2,263 → ~2,383 (+60 from List returns, +
  additional from other 17-64B aggregates in compiler structs)
- Fixed-point: byte-identical stage2 == stage3 (both emitters now
  agree on the convention)

## 5% rule

Target ratio must improve by ≥ 5% to ship. Dead end if it doesn't.
Given the baseline is ~70× Rust and expected outcome is ~1× Rust,
the 5% threshold is trivially met if the port is correct.

## Non-target watch list

These workloads should show no regression (> 2%):

- `fib_recursive` — returns `i64` (scalar), unaffected by sret
- `enum_match` — returns `{i64, i64, i64}` (24B), will gain sret
  (may improve or neutral, not degrade)
- `quicksort` — dominated by list ops, not struct returns
- `string_concat` — returns `{ptr, i64}` (16B String), stays register
- `prime_sieve` — returns `i64`, unaffected

## Rollback criteria

- Fixed-point breaks → revert emitter wiring, keep `abi.mn` dormant
- Sanitizer gate fires (new valgrind ERROR or ASan finding) → revert
- struct_alloc improvement < 5% → mark dead end
