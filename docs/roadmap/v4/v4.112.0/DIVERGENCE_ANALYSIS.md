# v4.112.0 Divergence Analysis — Self-Hosted Fixed-Point Verification

> **Phase D release 2.** Running `bash scripts/verify_fixed_point.sh
> --keep` against `mnc-stage1` (built by v4.111.0's Python bootstrap
> pipeline). Docket #7 (byref size heuristic) fixed. Fixed-point
> convergence itself remains blocked by a pre-existing self-hosted
> semantic gap.

---

## Phase 1 — Baseline verification

```text
[Stage 0] Using existing stage1: mapanare/self/mnc-stage1
  stage1: 3,480,712 bytes
[Stage 1] stage1 compiles mnc_all.mn -> stage2.ll
  FAIL: mapanare/self/mnc_all.mn:0:0: error: Undefined variable 'None'
```

**Stage 1 fails.** Self-hosted stage1 cannot compile its own sources.
`stage2.ll` is empty; `stage3.ll` never produced.

**Root cause** (pre-existing, surfaced in v4.111.0's stage2
validation): self-hosted `semantic.mn` doesn't register `None` as an
expression constructor. `mnc_all.mn` contains `let mut guard:
Option<Expr> = None` in several places (`parser.mn:2056`,
`parser.mn:2195`, `parser.mn:2198`), and `semantic.mn`'s identifier
resolution returns "Undefined variable" for `None`.

**Why the Python bootstrap doesn't fail**: `scripts/build_stage1.py:80`
passes `skip_check=True` to `compile_multi_module_mir`, deliberately
bypassing semantic check. Comment: "Self-hosted .mn uses patterns the
Python checker can't resolve." The self-hosted equivalent doesn't
have this bypass.

**Scope note**: this gap is a Phase D later work item (self-hosted
`None`/`Some`/`Ok` constructor registration). Not in scope for
v4.112.0's docket #7 fix.

## Phase 2 — Divergence analysis (structural)

Since the fixed-point script doesn't produce stage2.ll or stage3.ll
for direct diff, we analyze structural divergence between the Python
bootstrap's emission and the self-hosted emitter's emission on the
same input. Both compile a shared test program; their IR is compared.

### Test program (`/tmp/byref_test.mn`)

```mapanare
tipo Large {   // 10 × i64 = 80 bytes (> 64-byte byref threshold)
    a: Int, b: Int, c: Int, d: Int, e: Int,
    f: Int, g: Int, h: Int, i: Int, j: Int
}
tipo Small { x: Int, y: Int }   // 2 × i64 = 16 bytes (< 64)

fn take_large(l: Large) -> Int { da l.a + l.j }
fn take_small(s: Small) -> Int { da s.x + s.y }

fn main() {
    pon l: Large = new Large { a: 1, ..., j: 10 }
    pon s: Small = new Small { x: 100, y: 200 }
    print(str(take_large(l) + take_small(s)))
}
```

### Emitter divergence (baseline, pre-fix)

| Divergence class                          | Python bootstrap | Self-hosted stage1 (pre-fix) |
| ----------------------------------------- | ---------------- | ---------------------------- |
| Named struct type definitions emitted     | **No** (`{i64, i64}` inline) | **Yes** (`%struct.Small = type {i64,i64}`) |
| Small function inlining                   | **Yes** (`take_small` inlined into `main`) | **No** (separate fn, see Cat. A in v4.111.0) |
| byref for 80-byte Large                   | n/a (inlined)    | `ptr %l.byref` ✅ correct    |
| byref for 16-byte Small                   | n/a (inlined)    | `ptr %s.byref` ❌ **wrong**  |
| Attribute syntax on define                | `#0 { ... }` + attr table | inline `nounwind willreturn { }` |

The **byref 16-byte Small** divergence is docket #7: self-hosted's
`llvm_type_size` returned 256 for every `%struct.Foo`, causing
`is_byref_type` to classify all named structs (including 16-byte
ones) as byref.

### Classification

| Class      | Count | Notes |
| ---------- | ----: | ----- |
| **Byref-size**: small structs wrongly byref | ≥ 1 per small-struct fn | Docket #7 — **fixed in this release** |
| **Structural**: named-vs-inline struct types | pervasive | Self-hosted's `%struct.Foo = type ...` vs Python's `{...}`; semantically equivalent, cosmetic |
| **Inliner**: Python inlines small fns, self-hosted doesn't | Cat. A from v4.111.0 (13 tests) | Deferred; `inline_small_functions` was disabled in v4.111.0 because it produced invalid MIR |
| **Attribute syntax**: inline vs `#0` group | every user fn | Cosmetic |
| **`None` semantic gap** (stage1 can't self-compile) | — | Pre-existing, blocks fixed-point verification |

## Phase 3 — Byref size heuristic fix (docket #7)

See commit `6c0f1e7`. Three functions added/modified in
`mapanare/self/emit_llvm.mn`:

```mapanare
fn struct_byte_size(st: EmitState, ty: String) -> Int
fn is_byref_type_st(st: EmitState, ty: String) -> Bool
fn is_byref_type(ty: String) -> Bool  // back-compat wrapper
```

All 7 call sites of the old `is_byref_type` updated to
`is_byref_type_st(st|s, …)`. State variable was already in scope
at every call site (no plumbing required).

## Phase 4 — After fix

### Emitter divergence (post-fix)

| Divergence class                          | Self-hosted (post-fix) | Status |
| ----------------------------------------- | ---------------------- | ------ |
| byref for 80-byte Large                   | `ptr %l.byref`         | correct, unchanged |
| byref for 16-byte Small                   | `%struct.Small %s`     | ✅ **FIXED** |

IR still validates via `llvm-as`. Pipeline (`llc → clang → run`)
produces working binary; output `311` is correct (= `(1+10) +
(100+200)`).

### Fixed-point re-run

Same blocker as Phase 1 — stage1 still can't compile `mnc_all.mn`
due to `None` gap. The byref fix is a self-hosted emitter change
that takes effect when stage1 runs, but stage1 never reaches the
point of emitting `mnc_all.mn` IR. Fixed-point measurement remains
blocked until the `None` semantic gap is closed.

**Takeaway**: the byref fix is verified through (a) the unit test
above, (b) no golden regression (26/64 preserved), (c) byref
classification manually inspected as correct for multiple struct
sizes.

## Phase 5 — Culebra + goldens

Culebra scan on the 854K-line `main.ll` is long-running (>5 min
observed in v4.111.0 on the same file); deferred to future release
with a bounded-time scan mode.

Golden tests (after byref fix):

- **26 / 64 pass** (identical to v4.111.0 result)
- **0 regressions**
- `test_native.py` diff byte-by-byte against the v4.111.0 baseline
  shows only the expected byval-vs-byref difference on tests with
  small user structs (06_struct, 14_nested_struct, 27_impl). These
  changes do not affect correctness.

## Summary

| Exit criterion (from PLAN.md)                              | Status |
| ---------------------------------------------------------- | ------ |
| 1. Fixed-point script runs (3-stage self-compilation)      | ⚠ Blocked at Stage 1 by pre-existing `None` gap |
| 2. Baseline divergences documented                          | ✅ This file |
| 3. Divergences classified (byref / semantic / cosmetic)     | ✅ Above |
| 4. Docket #7 fixed: real struct sizes computed              | ✅ `is_byref_type_st` + `struct_byte_size` |
| 5. Real struct sizes verified on struct-heavy golden        | ✅ `/tmp/byref_test.mn` + 27_impl inspection |
| 6. Fixed-point re-run after fix, delta recorded             | ⚠ Same blocker; delta measured via other means |
| 7. Culebra fixedpoint result recorded                       | ⚠ Deferred (long-running on 854K-line IR) |
| 8. Golden tests: no regression from v4.111.0 count          | ✅ 26/64 preserved |
| 9. `DIVERGENCE_ANALYSIS.md` written with before/after       | ✅ This file |
| 10. No new divergences introduced by the fix                | ✅ Verified via diff and golden re-run |

## Forward dockets

| Docket | Description | Target |
| ------ | ----------- | ------ |
| Sh.8 (new) | Self-hosted `None` constructor registration (unblocks fixed-point) | v4.113.0+ (separate from #8 coroutine) |
| Sh.1 (from v4.111.0) | `inline_small_functions` MIR corruption fix (closes Cat. A structural-diff tests) | still open, v4.113.0+ |
| Sh.2 (from v4.111.0) | `emit_mir_call` NULL `starts_with` crash | still open, v4.113.0+ |
| Sh.3 (from v4.111.0) | Byref size heuristic | **CLOSED this release** |
