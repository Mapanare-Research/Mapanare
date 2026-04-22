# v5.1.3 Session Report — Own.1 Phase 1: Drop-Glue Ownership

**Date:** 2026-04-22
**Sessions:** 1 (combined — design space narrower than expected for
the actual code change, wider than expected for the infrastructure)

---

## Session 1 (2026-04-22) — Design + Implementation + Verification

### Critical finding: no drop-glue in self-hosted emitter

The execution prompt assumed `emit_llvm.mn` has an `emit_drop_glue`
function. It does not. The self-hosted emitter has:
- No `emit_drop_glue` function
- No ownership tracking (no `_str_slots`, `_list_vars`, etc.)
- No `_move_resource` equivalent
- Bare `ret` instructions at function return — no cleanup

The Python emitter (`emit_llvm_text.py`) has all of the above (~500
lines of drop-glue infrastructure).

**Consequence:** the execution prompt's "in `emit_drop_glue`, filter
out moved locals" cannot be implemented as written. Per the prompt's
guidance: "If the design space reveals itself wider than expected in
Phase 1, split the release: ship the detection mechanism only."

### Decision: Cb.7 workaround (the detection mechanism IS the fix)

The Cb.7 pattern (zero locals after ownership transfer) already existed
at monomorphization sites (lines 1795-1798, 1997-1998) but was missing
at `register_struct` (line 330) and `register_enum` (line 357). Applied
the same pattern to both sites.

The Python emitter already handles this correctly via `_do_call`'s
blanket move-on-call (line 3882). No Python changes needed.

Full design for the Move instruction + `@takes_ownership` annotation
documented in `DESIGN.md` for v5.1.4+ implementation.

### `@takes_ownership` sites found + annotated

**Tagged sites: 2** (exactly as planned)
- `register_struct` (lower.mn:330-336) — `fields`, `field_names`, `field_types` zeroed after push
- `register_enum` (lower.mn:364-369) — `variants`, `variant_names` zeroed after push

**Pre-existing Cb.7 sites (already had the workaround): 2**
- `try_monomorphize_struct` (lower.mn:1795-1798)
- `try_monomorphize_enum` (lower.mn:1997-1998)

### Stage2.ll IR size delta

| Metric | Before (v5.1.2) | After (v5.1.3) | Delta |
|--------|-----------------|----------------|-------|
| stage2.ll lines | 120,931 | 120,956 | +25 |
| New `__mn_list_new` calls | 0 | 5 | +5 (3 register_struct + 2 register_enum) |
| Removed `__mn_list_free` | N/A | N/A | 0 (no drop-glue to skip) |

The delta is +25 lines, not "slightly smaller" as the execution prompt
predicted. This is because the self-hosted emitter has no drop-glue —
there are no free calls to remove. The new instructions are the empty
list creations from the Cb.7 workaround.

### Valgrind before/after

| Golden | Before (ERRORS) | After (ERRORS) | Leak delta |
|--------|-----------------|-----------------|------------|
| All 66 | 0 | 0 | +44 bytes/golden (1 empty list header) |
| 26_generics (Ge.1r) | 0 | 0 | +44 bytes |
| 29_generic_impl (Ge.1r) | 0 | 0 | +44 bytes |
| 30_nested_generics (Ge.1r) | 0 | 0 | +44 bytes |
| 31_generic_multi (Ge.1r) | 0 | 0 | +44 bytes |

**Valgrind summary: 66 total, 0 CLEAN, 66 WARNINGS_ONLY, 0 ERRORS.**
Identical classification to v5.1.2. The +44 bytes/golden is from the
compiler's `register_struct` creating one additional empty list during
compilation (the zero-after-push replacement list).

### Fixed-point status

The `verify_fixed_point.sh` script aborts at the llvm-as step because
stage2.ll has a pre-existing In.1 SSA name collision (`%_inl0_6_t4`
defined twice). This is from the In.1 inliner pass re-enabled in
v5.1.2 — not caused by Own.1 changes.

**Determinism verified:** two consecutive `mnc-stage1` runs on
`mnc_all.mn` produce byte-identical output.

### Golden tests

**54/66 passed** — unchanged from v5.1.2. The 12 failures are all
pre-existing (async/tensor/closure features not in self-hosted path).

### Pytest

- Bootstrap + self-hosted: **514 passed, 0 failed, 5 xfailed**
- LLVM: **587 passed, 1 failed** (pre-existing `test_post_opt_single_switch_in_hot_loop` — LLVM version-dependent)

---

## What shipped

1. Cb.7 workaround applied to `register_struct` and `register_enum`
   in `mapanare/self/lower.mn` (10 lines of code + comments)
2. `DESIGN.md` documenting the full Move instruction design for v5.1.4+
3. `PARITY_GAPS.md` updated: Own.1 Phase 1 in Historical
4. VERSION bumped to 5.1.3

## What deferred (v5.1.4+)

1. `Move(Value)` instruction variant in MIR (`mir.mn` + `mir.py`)
2. `@takes_ownership` annotation recognition in parser/lowerer
3. `moved_locals: List<String>` field in `EmitState`
4. Drop-glue emission in self-hosted emitter (200-400 lines estimated)
5. Full borrow checker (v6.0)
