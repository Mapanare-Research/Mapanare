# v5.0.5 Session Report — Gr.2 + Cb.9a: Qualified Type Refs

**Date:** 2026-04-21
**Scope:** Grammar sync + self-hosted semantic type resolution for qualified types
**Breaking:** No

---

## Changes

### 1. Bootstrap grammar sync (Gr.2)

`bootstrap/mapanare.lark:136-137` updated to match main grammar:

```diff
-named_type: NAME
-generic_type: NAME LT type_expr (COMMA type_expr)* GT
+named_type: NAME (DOT NAME)*
+generic_type: NAME (DOT NAME)* LT type_expr (COMMA type_expr)* GT
```

Main grammar already had this since v4.139.0 (lines 170-171). The
bootstrap copy was never synced — this release closes the gap.

LALR(1) check clean on both grammars (no shift-reduce conflicts).

### 2. Self-hosted semantic — `bare_type_name()` (Cb.9a)

`mapanare/self/semantic.mn` gains a new helper:

```mapanare
fn bare_type_name(name: String) -> String
```

Extracts the last dot-separated component from a qualified type name
(e.g., `"device.DeviceKind"` → `"DeviceKind"`). Used in
`resolve_type_expr` for both named and generic type branches:

- **Named types**: `is_primitive_type(bare)` classifies correctly
  even when prefixed (e.g., `std.Int` → `Int` → primitive).
- **Generic types**: `is_builtin_generic(bare)` classifies correctly
  (e.g., `gpu.Tensor<Int>` → `Tensor` → builtin generic).
- Full dotted name preserved in TypeInfo for emitter round-tripping.

The v4.144.0 Cb.9a gap comment replaced with a "CLOSED v5.0.5" note.

### 3. concat_self.py fix

`scripts/concat_self.py` MODULE_ORDER was missing `abi.mn` (added in
v5.0.4). The bash script `concat_self.sh` already had it. Added
`abi.mn` between `emit_llvm_ir.mn` and `mir_opt.mn` to match.

Without this fix, `python3 scripts/concat_self.py` would produce an
`mnc_all.mn` that failed self-compilation with
`Undefined function 'abi_classify_return_sret'`.

### 4. Parser tests

New file `tests/parser/test_qualified_types.py` — 12 tests across
3 classes:

- `TestQualifiedNamedType` (5 tests): let binding, 2-segment path,
  fn param, return type, unqualified baseline
- `TestQualifiedGenericType` (5 tests): let binding, fn param,
  return type, nested in builtin, unqualified baseline
- `TestQualifiedTypeInStructField` (2 tests): named and generic
  qualified types in struct field position

All 12 pass. Total parser tests: 206 passed.

### 5. stdlib/gpu status

`stdlib/gpu/tensor.mn:90` and `kernel.mn:63` already use
`device.DeviceKind` directly — no workaround aliases to remove.
The qualified type grammar and semantic resolution were the missing
pieces, now closed.

Note: `mapanare check stdlib/gpu/tensor.mn` still has pre-existing
errors (doc comments on non-definitions, `@gpu` decorators, cross-
module import resolution). These are unrelated to Gr.2/Cb.9a.

---

## Verification

| Check | Result |
|-------|--------|
| `lark --check-grammar mapanare/mapanare.lark` | LALR(1) OK |
| `lark --check-grammar bootstrap/mapanare.lark` | LALR(1) OK |
| `pytest tests/parser/test_qualified_types.py -v` | 12 passed |
| `pytest tests/parser/ -v` | 206 passed |
| Golden tests through mnc-stage1 | 54/66 (unchanged) |
| `verify_fixed_point.sh --keep` | NEAR (4 diff, Dr.1 version placeholder only) |
| stage2.ll lines | 112,004 |
| mnc-stage1 size | 3,603,616 bytes stripped |

---

## Docket closures

| Docket | Severity | Panel | Status |
|--------|----------|-------|--------|
| **Gr.2** | MEDIUM | Coral v4.136.0 | **CLOSED** — bootstrap grammar synced |
| **Cb.9a** | MEDIUM | Cobra v4.144.0+v4.154.0 | **CLOSED** — `bare_type_name()` + resolve classification |

Both moved to Historical in `docs/roadmap/v5/PARITY_GAPS.md`.

---

## Files changed

| File | Change |
|------|--------|
| `bootstrap/mapanare.lark` | `named_type` / `generic_type` accept `NAME (DOT NAME)*` |
| `mapanare/self/semantic.mn` | `bare_type_name()` helper, `resolve_type_expr` updated |
| `scripts/concat_self.py` | Added `abi.mn` to MODULE_ORDER |
| `tests/parser/test_qualified_types.py` | New: 12 parser tests |
| `VERSION` | 5.0.4 → 5.0.5 |
| `CLAUDE.md` | v5.0.5 entry added |
| `docs/roadmap/ROADMAP.md` | v5.0.5 entry added |
| `docs/roadmap/v5/PARITY_GAPS.md` | Gr.2 + Cb.9a moved to Historical |
| `docs/roadmap/v5/v5.0.5/PLAN.md` | Status → SHIPPED |
| `docs/roadmap/v5/v5.0.5/SESSION_REPORT.md` | This file |
| `mapanare/self/mnc_all.mn` | Regenerated (includes abi.mn + semantic.mn changes) |
| `mapanare/self/main.ll` | Regenerated (build_stage1.py) |
| `mapanare/self/mnc-stage1` | Rebuilt binary |
