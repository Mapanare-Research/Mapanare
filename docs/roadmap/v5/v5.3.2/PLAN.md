# v5.3.2 — In.1-stage2: Restore fixed-point

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.3.1 shipped
**Estimated work:** 1–2 hours

---

## Goal

Restore the fixed-point from BROKEN to at minimum NEAR. This is
the single biggest score driver: Cobra (-0.3) and Rattler (-0.3)
both docked for it, and Anaconda's score rationale also cited it.

## The bug

`clone_instr_for_inline` in `mapanare/self/mir_opt.mn:835-934`
handles only **10 of 30+** Instruction enum variants when cloning
a callee's body into the caller. The fallthrough at line 932-933
pushes the **original** (un-renamed) instruction for unhandled kinds:

- **Handled (10):** Return, Const, Copy, BinOp, Call, Alloca, Load,
  Store, UnaryOp, Cast
- **Unhandled (20+):** FieldGet, StructInit, IndexGet, IndexSet,
  EnumTag, EnumPayload, WrapSome, WrapNone, UnwrapOption, WrapOk,
  WrapErr, UnwrapResult, ListPush, ClosureCreate, Print, ...

The sister function `replace_uses_in_instr` (lines 677-830) covers
all 30+ variants for **use** renaming but does not rename **definitions**.
This asymmetry creates use-def mismatches when the self-hosted compiler
inlines helpers in the lexer module (FieldGet on Span struct).

## Approach options

### Option A: Extend the cloner (preferred)

Add the missing 20+ instruction variants to `clone_instr_for_inline`.
Each variant follows the same pattern: extract operands, create fresh
destination name with `_inlN_M_` prefix, push the new instruction.
The `replace_uses_in_instr` function already shows the template for
each variant.

**Estimated effort:** 60–100 LOC, 1 hour.
**Risk:** Low — each variant is mechanical.
**Verification:** `bash scripts/verify_fixed_point.sh --keep` must
reach stage2.ll that passes `llvm-as`.

### Option B: Disable the inliner

Revert the v5.1.2 `inline_small_functions` enablement by commenting
out the call at `mir_opt.mn:1467`. This immediately restores the
NEAR fixed-point but loses the inliner for self-hosted compilation.

**Estimated effort:** 1 line, 30 seconds.
**Risk:** Zero.
**Trade-off:** The inliner works for 54/66 golden tests. Disabling
it penalizes the self-hosted binary size and regresses Cobra's "pass
enablement" credit from v5.1.2.

### Option C: Gate the inliner on self-compilation detection

Keep the inliner enabled for normal `.mn` files but disable it when
compiling `mnc_all.mn` (the concatenated self-hosted source). This
preserves inliner benefits for users while avoiding the self-compilation
regression.

**Estimated effort:** 5–10 LOC.
**Risk:** Low but feels like a band-aid.

## Recommendation

**Option A.** The v4.152.0 E8 SESSION_REPORT documented the exact
root cause (In.1), and the v5.1.2 In.1 fix addressed one half
(use renaming) but not the other (definition cloning). Extending
the cloner is the complete fix.

## Expected panel impact

- **Cobra**: +0.3 (fixed-point restored, 9.1 territory)
- **Rattler**: +0.1–0.2 (correctness concern addressed)
- **Anaconda**: +0.1 (quality metric restored)
- **Net aggregate lift**: +0.15–0.20

## Exit criteria

- `bash scripts/verify_fixed_point.sh --keep` → stage2 passes `llvm-as`
- stage2.ll == stage3.ll structurally (NEAR or STRICT)
- 54/66 goldens unchanged
- `python3 -m pytest tests/mir_opt/test_inline_rename.py -v` → 4+ passed
- New tests covering FieldGet, StructInit, IndexGet inlining
