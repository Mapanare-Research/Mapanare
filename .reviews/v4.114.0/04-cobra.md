# Cobra v4.114.0 Review — C++ / ABI / fixed-point

## Score: 8.0 / 10
## Verdict: PASS WITH NOTES

## Context

v4.106.0 I gave **7.5 / 10 PASS WITH NOTES** — byref size heuristic
was the top finding. The self-hosted `emit_llvm.mn` returned a
stubbed 256 for every `%struct.Foo`, causing all named struct types
to be forced byref regardless of actual size. That's ABI divergence
from the Python bootstrap's `_tsz` algorithm. I asked for a real
size computation.

v4.112.0 landed the fix. I am the primary reviewer for #7.

## Primary lens — Docket #7: byref size heuristic fix

### The fix

`mapanare/self/emit_llvm.mn`:

```
1460:  fn is_byref_type_st(st: EmitState, ty: String) -> Bool {
1463:      let sz_real: Int = struct_byte_size(st, ty)
1495:  fn struct_byte_size(st: EmitState, ty: String) -> Int {
```

`struct_byte_size` resolves `%struct.Foo` through `st.structs`,
retrieves the inline `{...}` form, and calls `llvm_aggregate_size`
which sums field sizes recursively (pointers 8, ints padded to 8 on
x86_64, nested aggregates recursed).

### Does it match the Python bootstrap?

I diffed `_tsz` at `emit_llvm_text.py:141` against
`llvm_aggregate_size` in `self/emit_llvm.mn`. Same recursion, same
rules, same fallback (256 for unresolved named types, consistent
with the Python version's fallback). Algorithm equivalence
confirmed.

### Was the fix verified end-to-end?

v4.112.0 SESSION_REPORT describes a test on `/tmp/byref_test.mn`:

```mn
struct Small { x: Int, y: Int }    // 16 bytes
struct Large { a-j: Int x 10 }     // 80 bytes

fn f(s: Small, l: Large) -> Int { ... }
```

With the fix, `Small` lowers to `%struct.Small %s` (by value) and
`Large` lowers to `ptr %l.byref`. Output is correct. IR validates.

**The test file was not committed.** It's reproducible from the SR
text but leaves no artifact in-tree. That's a reproducibility
finding. 0.2 score cost.

### Fixed-point convergence

**Not reached.** `verify_fixed_point.sh` fails at Stage 1 with
`Undefined variable 'None'`. Stage 2 and Stage 3 artifacts are never
produced. Sh.8 blocks.

So: **the byref fix was verified in isolation, not at the fixed-
point level.** v4.112.0 SESSION_REPORT admits this. v4.114.0
MEASUREMENTS.md admits this. Every honest document admits this.

But the release v4.112.0 was *named* "fixed-point verification" —
and the verification did not converge. The work that actually
landed is the byref fix plus a divergence classification artifact
(`DIVERGENCE_ANALYSIS.md`). That's valuable work. The name is just
aspirational.

I take 0.3 off for the aspirational name. Not because the work is
bad — it's solid — but because "fixed-point verification" as a
release name sets a bar the release didn't clear.

### ABI correctness at the self-hosted output level

I pulled mnc-stage1 output for `06_struct` (16-byte struct) and
`16_list_of_structs` (larger nested struct). For `06_struct`:
- Python-bootstrap output: `%struct.Point %p` (by value)
- Self-hosted output: `%struct.Point %p` (by value)

Match. For `16_list_of_structs`, both pipelines use byref for the
80+ byte container. Match.

ABI alignment between the two pipelines is **real** for the 26
passing goldens. For the 38 failing, the failures are upstream of
the byref decision (symbol crashes, missing features).

**Sub-score for #7: 8.5 / 10.** Algorithm is right, matches
Python, verified on an isolated test, but (a) test not committed,
(b) full fixed-point convergence unreachable due to Sh.8.

## Secondary — Coroutine frame (docket #8)

ABI perspective: `mn_coro_frame_prefix_t` is a two-pointer struct
with natural alignment. On x86_64 that's 16 bytes, matching the
LLVM switched-resume ABI prefix. No padding surprises. The struct
has no C++ constructor / destructor concerns because it's used
as a cast target, not an independently-allocated type.

Verified by link-test: the v4.113.0 runtime links against existing
async golden binaries (55/56/57) without relinking them. No ABI
break in the runtime archive.

## Secondary — Stage2 validation

`ir_doctor.py stage2`: 0/11 modules valid. Same root cause
(Sh.8). The byref fix cannot be exercised at the stage2 level until
Sh.8 is closed.

This is a circular dependency that hurts Phase D: stage2 validation
is the natural acceptance test for the byref fix, but it's unreachable.
Phase E needs to close Sh.8 so the fix can be acceptance-tested at
the stage level.

## What I'd flag

1. **v4.112.0 release name is aspirational.** Document plainly: the
   release delivered the byref fix and the divergence
   classification; fixed-point convergence was not achieved.
2. **Commit the `/tmp/byref_test.mn` test case.** Put it under
   `tests/golden/` or `tests/bootstrap/` so the acceptance path is
   reproducible without rebuilding from SESSION_REPORT text.
3. **Sh.8 is the unlock.** Once self-hosted `semantic.mn` registers
   `None`/`Some`/`Ok`, fixed-point verification can actually run
   and the byref fix can be acceptance-tested at stage level.

## Verdict

**PASS WITH NOTES @ 8.0.**

The byref fix is correct and matches the Python bootstrap. The
release name overreaches. The fixed-point gap is real but the
docket path (Sh.8) is clear.

Phase D closes if the aggregate holds.
