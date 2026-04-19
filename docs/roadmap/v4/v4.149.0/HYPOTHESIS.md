# E5 Hypothesis

**Claim:** Replacing by-value return with explicit sret for aggregates
whose total size exceeds the target ABI's register-return threshold
(16 bytes on SysV, 8 bytes on Win64, 16 bytes on AArch64) produces
IR that matches Clang's convention and may allow LLVM to optimize the
sret pointer path more effectively. The sret count in golden-test IR
will increase from 0 to a positive number (the inverse of the PLAN's
original expectation — the PLAN assumed unconditional sret; the actual
baseline has zero sret).

## Per-ABI classification rules

### System V AMD64 (§3.2.3)

An aggregate is classified by splitting it into 8-byte "eightbytes."
Each eightbyte is classified as INTEGER, SSE, SSEUP, X87, X87UP,
COMPLEX_X87, NO_CLASS, or MEMORY.

**Register return when:** aggregate ≤ 16 bytes AND each eightbyte
classifies as INTEGER or SSE (at most two eightbytes). Mapanare's
aggregate fields are all integer-class (i64, i32, i8, i1, ptr), so
the only threshold that matters is **≤ 16 bytes → register**.

**sret when:** aggregate > 16 bytes OR any eightbyte classifies as
MEMORY.

### Win64 x64 calling convention

**Register return when:** aggregate size is exactly 1, 2, 4, or 8
bytes → returned in rax.

**sret when:** all other sizes (including 16 bytes) → caller passes
hidden first parameter (pointer in rcx).

### AArch64 AAPCS64

**Register return when:** aggregate ≤ 16 bytes → returned in x0/x1
(two 64-bit registers). For HFA/HVA types (homogeneous float/vector
aggregates), up to 4 registers — not relevant for Mapanare since
struct fields are integer/pointer.

**sret when:** aggregate > 16 bytes → caller passes pointer in x8.

## Expected impact

| Metric | Before (v4.148.0) | After (v4.149.0) | Direction |
|--------|-------------------|-------------------|-----------|
| sret count (golden corpus) | 0 | 15–30 (estimate) | **increase** |
| enum_match wall | 0.170 ms | 0.160–0.180 ms | ambiguous |
| struct_alloc wall | 0.028 ms | 0.028 ms | unchanged |
| quicksort wall | 1.142 ms | 1.142 ms | unchanged (scalar return) |

**Why the sret count goes UP, not down:** The PLAN.md assumed Mapanare
unconditionally used sret for all aggregates. In reality, `_BYREF_BYTES
= 64` means all aggregates ≤ 64 bytes already return by value, and
no golden test has a struct > 64 bytes. The E5 fix *lowers* the
by-value threshold from 64 to 16 (SysV), causing aggregates 17–64
bytes to switch from by-value to sret.

**Why enum_match impact is ambiguous:** The E1 unified-ret optimization
(v4.145.0) relies on by-value return + SROA to merge enum dispatch
switches. Switching 24-byte enums to sret disables unified-ret for
those functions. However, after inlining, the sret pointer becomes a
local alloca in the caller, which SROA *can* still decompose. The net
effect depends on LLVM's optimization pipeline.

## Invariant

The classifier must be called at both function definition and call
sites with identical inputs. Any disagreement between the two sites
is a miscompilation — the caller would pass/expect sret while the
callee expects by-value, or vice versa.
