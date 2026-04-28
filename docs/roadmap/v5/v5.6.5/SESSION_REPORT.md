# v5.6.5 — Ve.1 primary fix + GEP-trick sizing refactor

**Status:** SHIPPED
**Breaking:** No
**Date:** 2026-04-24

## Headline

**FnDefData heap-buffer-overflow CLOSED.** Systemic refactor of the
self-hosted emitter's struct/enum-payload sizing: 435 hardcoded
`malloc(i64 <literal>)` sites → 2. The remaining 505 allocation sites
now use LLVM's GEP-trick (`ptrtoint ptr getelementptr (<ty>, ptr null,
i32 1) to i64`), deferring size computation to LLVM's DataLayout at
link time — the same approach documented in LLVM LangRef and used by
Clang for opaque-size emission. This matches Python's
`_do_enum_init` at `emit_llvm_text.py:4770-4809` for parity.

**ASan confirmation:** 0 heap-buffer-overflow errors compiling both
`lower.mn` and the full `mnc_all.mn` (was 154,355 errors / 42 contexts
at v5.6.4 per `docs/roadmap/v5/v5.5.7/VE1_INVESTIGATION.md`).

**Not fully closed:** stage3.ll remains empty — the fix uncovered a
separate pre-existing bug in the lowerer's empty-list element-type
propagation (the 384-byte list-elem-size floor had been masking it
since v4.x). That bug is scoped to **v5.6.7 (new)** as Ve.2.

## What shipped

### The primary fix — FnDefData overflow

Valgrind on v5.5.7 pinned the crash to `parse_fn_body` writing 8 B
past a 256-byte `malloc`'d block (`docs/roadmap/v5/v5.5.7/VE1_INVESTIGATION.md`).
v5.6.5 ASan-symbolic investigation identified the root cause:

```mapanare
fn llvm_type_size(ty: String) -> Int {
    ...
    if ty.starts_with("%struct.") { return 256 }   // ← hardcoded fallback
    ...
}
```

`FnDefData` is 264 bytes (`Span 32 + String 16 + i1+7pad 8 + List 40 ×
3 + Option {i1, ptr} 16 + Block {Span+List} 72 + List 40`). The `256`
fallback under-allocated by 8 bytes; every `Definition::FnDef(fd)`
boxing corrupted the adjacent heap block.

### The systemic refactor — LLVM-computed sizing everywhere

Rather than patch `FnDefData` alone, v5.6.5 rewrites the
emission pipeline to match what production LLVM-backed compilers do:

**emit_enum_init** (`emit_llvm.mn:2829-2870`): builds an inline
payload struct type `{ <f0_ty>, <f1_ty>, … }` from payload values,
then emits:

```llvm
%sz  = ptrtoint ptr getelementptr (<payload_ty>, ptr null, i32 1) to i64
%ep  = call ptr @malloc(i64 %sz)
%ef0 = getelementptr inbounds <payload_ty>, ptr %ep, i32 0, i32 0
store <f0_ty> <v0>, ptr %ef0
%ef1 = getelementptr inbounds <payload_ty>, ptr %ep, i32 0, i32 1
store <f1_ty> <v1>, ptr %ef1
…
```

LLVM's `DataLayout::getTypeAllocSize` folds `%sz` to a link-time
constant, and typed GEPs use `StructLayout` for exact field offsets
with alignment padding. No hand-computed sizes; no "safe upper bound"
fallbacks.

**emit_enum_payload** (`emit_llvm.mn:3183-3202`): mirror-image fix for
extraction — builds the same inline payload type from the variant's
registered `payload_types`, emits a typed GEP for field address:

```llvm
%pf = getelementptr inbounds <payload_ty>, ptr %pr, i32 0, i32 <field_idx>
%v  = load <dest_ty>, ptr %pf
```

Guaranteed consistent with the storage site since both reference the
same payload type string.

**Two new helpers:**
- `build_payload_type_from_values(st, payload: List<Value>) -> String`
  — for emit_enum_init
- `build_payload_type_from_variant(st, enum_name, variant_name) -> String`
  — for emit_enum_payload (looks up via `st.enum_infos`)

### Supporting fixes

**`lookup_struct_field_types` bug** (`emit_llvm.mn:32-58`):
`register_internal_struct` pushes entries with only field NAMES (empty
`field_types`) as a fallback for `find_field_index`'s index-0-bug
protection. A forward first-match search returned these empty entries
for structs like Value, MIRType, EmitState, LowerState, shadowing the
real MIR-registered entries later in the list. Fixed to skip entries
with empty `field_types` so the real entry wins.

**`llvm_sizeof_st(st, ty) -> Int`** (`emit_llvm.mn:2291-2321`): new
state-aware size calculator, used by the non-GEP paths
(`compute_payload_alloc_size`, `compute_field_offset`,
`sum_field_sizes`, `compute_variant_field_offset`). Recursively
resolves `%struct.*` through the registry, pads fields to 8-byte
alignment (safe for all Mapanare struct layouts — every aggregate
contains at least one ptr/i64 field). Preserved as a fallback for
call sites that haven't been converted to typed GEPs yet; the
enum-init/extract path is now pure GEP-trick.

**`emit_list_init`** (`emit_llvm.mn:2404-2444`): hybrid approach.
Known element types (`%struct.*`, `%enum.*`, `{...}` aggregates) use
the GEP-trick for exact ABI size. Unknown/i64/primitive types keep
the legacy 384-byte floor as a safety net — necessary because the
lowerer produces `elem_ty.kind=TK_UNKNOWN` for empty-literal lists
(`let xs: List<String> = []`), which `resolve_mir_type` maps to
`"i64"`. Using the GEP-trick unconditionally would allocate 8-byte
slots for 16-byte String elements and corrupt memory on push. The
floor will be removed in v5.6.7 after the lowerer fix.

## Metrics

| Gate | v5.6.4 | v5.6.5 | Δ |
|---|---:|---:|---:|
| stage2.ll lines | 205,446 | 207,039 | +0.78% |
| stage2.ll `llvm-as` | OK | OK | — |
| hardcoded `malloc(i64 N)` in stage2.ll | 435 | 2 | **−99.5%** |
| dynamic `malloc(i64 %)` in stage2.ll | 72 | 505 | **+7×** |
| `__mn_list_new(i64 384)` hardcoded | 0 (was `elem_sz` var) | 387 | (fallback safety) |
| `__mn_list_new(i64 %)` dynamic | 0 | 49 | known-type GEP-trick |
| ASan on `lower.mn`: heap-buffer-overflow | 154,355 errors | **0** | ✓ CLOSED |
| ASan on `mnc_all.mn`: heap-buffer-overflow | — | **0** | ✓ CLEAN |
| goldens harness | 64/66 | 64/66 | — |
| `make lint` | clean | clean | — |
| `check_struct_registry.py` | 23/23/91 | 23/23/91 | — |
| non-bootstrap pytest | 5565 passed | 5565 passed | — |
| stage3.ll non-empty | ❌ (parse_fn_body crash) | ❌ (Ve.2 — lowerer) | deferred |

## What NOT closed — Ve.2 (new, scoped for v5.6.7)

Removing the 384-byte List floor exposed a pre-existing bug: empty
list literals `[]` lower to MIR with `elem_ty.kind=TK_UNKNOWN`, even
when the declaration has a type annotation (`let xs: List<String> =
[]`). `resolve_mir_type` maps `TK_UNKNOWN → "i64"` so emit_list_init
sees a scalar element type and either allocates 8-byte slots
(incorrect) or falls back to 384 (wasteful).

v5.6.4 and earlier always fell back to 384 because the floor was
unconditional — wasteful (~24× memory overhead for 16-byte Strings)
but correct. v5.6.5 preserves this fallback under the known/unknown
guard.

**The real fix (v5.6.7)** is in `lower.mn`: when lowering a `let`
with a type annotation, propagate the annotation's element type down
through `ListInit` so `elem_ty.kind` matches the declared type. Once
landed, the 384 floor can be deleted and `emit_list_init` reduces to
an unconditional GEP-trick emission.

Without this fix, `mnc-stage2` runtime construction of its own AST/MIR
data structures (which allocate lots of empty typed lists during
parsing/lowering) still happens via the 384 floor — memory-correct but
wasteful. The runtime OOM seen on non-trivial programs is a
*separate* crash path via `__mn_str_concat` reading a corrupted size
— hypothesized to stem from the same lowerer-type-propagation root
but scoped to the v5.6.7 investigation.

## Research

Investigation drew on production compilers to confirm the approach:

- **LLVM LangRef** (`docs/LangRef.rst`, "Getelementptr") — documents
  the `ptrtoint (getelementptr null, 1)` idiom. LLVM folds to a
  link-time constant via `DataLayout::getTypeAllocSize`.
- **rustc** (`compiler/rustc_codegen_llvm/src/builder.rs`) — uses
  typed GEPs (`struct_gep`) exclusively, never byte-offset GEPs
  except for opaque memory (void\* FFI). rustc computes sizes itself
  via `rustc_target::abi::Size` + `LayoutCalculator` because it needs
  them for const-eval, but emitted IR always uses named types + typed
  GEPs.
- **Clang** (`lib/AST/ASTContext.cpp::getTypeInfoImpl`) — same
  pattern.
- **Go** (`src/cmd/compile/internal/types/size.go::CalcSize`) —
  self-computed layout, but emits typed GEPs in IR.

The **GEP-trick is the idiomatic choice** for a small self-hosting
compiler with no layout engine of its own — defer to LLVM. Mapanare
already used it at 72 sites (mostly `emit_wrap_some` and related
Option/Result wrappers); v5.6.5 extends it to the 435 remaining
payload-boxing sites.

## Known issues

- **Ve.1** (`docs/known_issues.md`) — primary overflow CLOSED; row
  updated to reference this report for the systemic fix. Symptom
  "stage3.ll empty" persists due to Ve.2.
- **Ve.2 (NEW)** — added to `docs/known_issues.md`. Scope:
  lowerer-side empty-list elem_ty propagation. Blocks fixed-point
  verification. Tractable (~1 session), bounded (one MIR-type
  inference path).

## Risks — mitigated or deferred

- **R1 — Fix introduces new memory behavior.** Full ASan sweep on
  both `lower.mn` and `mnc_all.mn` confirms 0 heap-buffer-overflow;
  goldens 64/66 preserved; `make lint` clean.
- **R2 — stage2.ll diverges from v5.6.4.** +0.78% line count (within
  ±1% budget per PLAN §R3). `llvm-as` clean. Diff is dominated by
  GEP-trick IR text replacing hardcoded literal sizes.
- **R3 — Lookup fix breaks existing callers.** The other two callers
  of `lookup_struct_field_types` (emit_llvm.mn:1820, 2005) used empty
  field_types as "no info → fallback to MIR kind" — my skip-empty
  change upgrades them to "get the real types". Goldens preserved
  confirms no regression.
- **R4 — Ve.1 reproduces elsewhere** (PLAN §R4, explicitly permitted
  deferral). Materialized as Ve.2 — new docket, scoped v5.6.7. Not
  this release's fault; masked for 11 versions behind the 384-byte
  floor.

## What's next

- **v5.6.6** (scheduled, scope unchanged) — Rt.04 `%struct.*`
  return-value guard-lift with size gate (62_list_output leak
  closure).
- **v5.6.7** (NEW, was not in roadmap) — **Ve.2 — lowerer empty-list
  elem_ty propagation.** Fix `ListInit` lowering in lower.mn to carry
  `let` declaration type annotations through to MIR. Once landed,
  remove the 384-byte emit_list_init floor and confirm
  `verify_fixed_point.sh` produces non-empty stage3.ll.
- **v5.7.0** (unchanged) — Sh.7 + or-pattern → 66/66.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` for the updated sequence.
