# Mapanare v5.0.5 — "Gr.2 + Cb.9a: Qualified Type Refs end-to-end"

> **Unblock `stdlib/gpu/tensor.mn` and `kernel.mn`.** Grammar rejects
> `module.Type` in type position. v4.139.0 fixed this in the Python
> parser and self-hosted mirror but the grammar edit was never
> committed. **Cobra v4.154.0 also flagged Cb.9a** — the matching
> `module_path` concept is missing from `mapanare/self/semantic.mn`,
> so even if the grammar accepts `gpu.Tensor`, self-hosted type
> resolution can't follow the dot. This release closes both in one
> pass.

**Status:** SHIPPED
**Breaking:** No
**Prerequisite:** v5.0.4 shipped
**Estimated work:** 1 session (~1 hour)

---

## Why this release exists

v4.139.0's SESSION_REPORT claims Gr.2 closed. Inspection of
`mapanare/mapanare.lark` at HEAD of `dev` shows `named_type` /
`generic_type` still read `NAME` (unqualified only). The fix shipped
in the Python parser (`mapanare/parser.py::_type_from_tree`) but the
grammar was never updated. This works by accident for most cases
because the Lark transformer hand-builds qualified types — except
when the parser's error recovery kicks in on an invalid parse and
presents a misleading "unexpected `.`" diagnostic.

Coral's v4.136.0 panel named this as the last MEDIUM blocker.
v4.143.0 panel noted it as "closed, pending grammar sync."

This release syncs the grammar.

## Scope

**In scope:**
- `mapanare/mapanare.lark` — `named_type` / `generic_type` rules
  accept `NAME (DOT NAME)*`
- `bootstrap/mapanare.lark` — mirrored copy
- `mapanare/self/parser.mn` — already supports this path (v4.139.0);
  verify no drift
- **Cb.9a**: add `module_path: List<String>` field to `TypeExpr` in
  `mapanare/self/semantic.mn` (at the same location as the v4.144.0
  comment at line 520). Teach `resolve_type` to walk the `module_path`
  before looking up the bare name.
- Remove the workaround comments in `stdlib/gpu/tensor.mn:90` and
  `stdlib/gpu/kernel.mn:63`
- Add parser tests for qualified type refs in type position:
  - Variable declaration: `let t: gpu.Tensor<Int> = ...`
  - Function param: `fn apply(k: gpu.Kernel) { ... }`
  - Return type: `fn make() -> gpu.Device { ... }`
  - Generic instantiation: `let m: Map<gpu.Tensor<Int>, String> = ...`

**Out of scope:**
- Arbitrary expression-position qualified types (`gpu.Tensor::new(...)`
  constructor calls — already work via method call chain)
- `use module.Type as LocalAlias` — a separate RFC

## Exit criteria

- `stdlib/gpu/tensor.mn` and `stdlib/gpu/kernel.mn` compile without
  import-alias workarounds
- `pytest tests/parser/test_qualified_types.py` passes with 10+ new
  tests
- `grep -n 'module_path' mapanare/self/semantic.mn` returns a field
  definition (not just Cobra's v4.144.0 comment)
- Gr.2 and Cb.9a both closed on the parity inventory
  (`docs/roadmap/v5/PARITY_GAPS.md` moves both to Historical)

## Risks

**Risk 1 — grammar edit breaks strict fixed-point.**
Any grammar change produces new parse trees for some inputs.
*Mitigation:* `scripts/verify_fixed_point.sh` after the grammar edit.
Because the self-hosted parser already handles qualified types
(v4.139.0), the emitted IR should be identical.

**Risk 2 — LALR(1) conflict on `DOT NAME`.**
The grammar already uses `DOT` in method-call expressions and field
access. Introducing it in type position may create an ambiguity.
*Mitigation:* run `lark --check-grammar` before committing.
