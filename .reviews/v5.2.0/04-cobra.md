# Panel v5.2.0 — Cobra (Bootstrap / Self-Hosted)

**Score:** 8.8 / 10
**Grade:** MEETS
**Delta vs v4.154.0:** -0.3

## Summary

Five of my seven carry-forward items closed. The sret classifier port
(Cb.15) is clean and complete. The `bare_type_name` helper (Cb.9a) is
correct and well-scoped. The Own.1 Phase 1 workaround mirrors the
existing Cb.7 pattern. The escape analysis port (Ea.1) is honest about
its limitations. The PARITY_GAPS.md tracking document I demanded at
v4.154.0 exists and is well-structured. The Perf.1 dual-emitter
discipline -- patching both Python and self-hosted simultaneously for
inline list ops -- is the kind of engineering I want to see in every
release.

And then In.1 broke the fixed point.

The v4.134.0 strict fixed point -- La Culebra Se Muerde La Cola -- was
the single greatest achievement in this project's self-hosted compiler
history. It held through the v4.134.0-v4.154.0 perf arc as NEAR (4-line
Dr.1 version diff). At v5.1.2, re-enabling `inline_small_functions`
produced stage2.ll that fails `llvm-as` with `use of undefined value
'%_inl0_6_t4'`. The inliner rename fix works on the 54 golden tests but
breaks when the compiler compiles itself -- a more complex inlining
pattern that the rename logic does not handle. The fixed-point status
went from NEAR to BROKEN.

I cannot grade this as anything other than a regression in my core
domain. Closing In.1 was the right goal. The `replace_uses_in_instr`
helper is comprehensive (30+ instruction variants, well-structured
match). The 4 dedicated rename tests pass. But the self-hosted
compiler's self-compilation was not used as a gate before declaring In.1
closed and enabling the pass in the pipeline. That is the single
process failure of this arc.

## What improved since v4.154.0

- **Cb.15 CLOSED (v5.0.4) -- sret classifier ported.** Verified:
  `grep -c 'sret\|classify_return\|use_sret' mapanare/self/emit_llvm.mn`
  returns 35 (was 0 at v4.154.0). New `abi.mn` (75 LOC) implements
  SysV/Win64/AArch64 classifiers. `use_sret_return` in `emit_llvm.mn`
  replaces `is_byref_type_st` for return types at all 4 sites (call
  registered, call unregistered, return statement, function header).
  Argument passing still uses the old 64B threshold -- correct, since
  ABI.1 only addressed return conventions. The stage2.ll sret count
  went from 2,263 to 4,112 (+1,849). The code is clean, the comments
  are accurate, and the SESSION_REPORT's honesty about the struct_alloc
  hypothesis being wrong ("ABI correctness and parity, not a performance
  optimization") is appreciated. This is the best docket closure in the
  arc for my domain.

- **Cb.9a CLOSED (v5.0.5) -- qualified type refs.** Verified:
  `grep -c 'bare_type_name' mapanare/self/semantic.mn` returns 4. The
  helper extracts the last dot-separated component (e.g.
  `"device.DeviceKind"` -> `"DeviceKind"`) and is used in
  `resolve_type_expr` for both named and generic type branches. Full
  dotted name preserved in TypeInfo for the emitter. The approach is
  pragmatic -- it does not require a `module_path` field on TypeExpr,
  just a string operation at the classification boundary. The
  `concat_self.py` fix (adding `abi.mn` to MODULE_ORDER) was a latent
  bug from v5.0.4 that would have broken any Python-driven concat.
  Good catch.

- **Own.1 Phase 1 CLOSED (v5.1.3).** Verified at `lower.mn:330-336`
  and `lower.mn:364-369`. The zero-after-push pattern mirrors the
  existing Cb.7 pattern at monomorphize sites. The comment blocks cite
  the source pattern and explain the ownership transfer. This is a
  workaround, not a fix -- the design decision to defer Move
  instructions and drop-glue to v5.1.4+ (and full borrow checking to
  v6.0) is documented in PARITY_GAPS.md. I accept this staging.

- **Ea.1 CLOSED (v5.1.2).** The stub at `mir_opt.mn:1370-1398` is
  replaced with real `check_escape` analysis. The pass computes the
  non-escaping set correctly but cannot annotate instructions (the
  self-hosted `Instruction` enum lacks `alloc_kind`). The comment block
  at line 1482-1489 documents this limitation precisely: "the
  self-hosted path is parity-equivalent in analysis but defers codegen
  annotation." Returns `f` unchanged -- safe, zero-risk. The 7 tests
  in `test_escape_analysis.py` cover the analysis logic.

- **PARITY_GAPS.md exists and is maintained.** The document I requested
  at v4.154.0 to address the 27% ledger undercount is here. The close
  policy (section "Close policy") requires: (1) `.mn` implementation
  exists and is invoked, (2) a test asserts parity, (3) item moves to
  Historical with closure release cited. The "Why this doc exists"
  section explicitly references my v4.154.0 finding. This is the
  correct response to my complaint.

- **Perf.1 dual-emitter discipline (v5.1.0).** Both
  `emit_llvm_text.py` (+46/-9) and `emit_llvm.mn` (+60/-12) were
  patched in the same release. The fast-path gate (`_tsz(ety) == 8`)
  is structurally identical in both emitters. No new parity gap opened.
  This is the pattern I want: when you touch the Python emitter, you
  touch the self-hosted emitter in the same release.

- **E8 comment blocks updated.** The four disabled-pass comment blocks
  at mir_opt.mn:1448-1490 now carry v5.1.2 evidence for In.1, Li.1,
  and Ea.1. The In.1 block (lines 1461-1467) documents the rename fix
  and the closure. The Li.1 block (lines 1468-1477) honestly states
  the regression root cause. The Ea.1 block (lines 1479-1490) explains
  the analysis-vs-annotation gap. The documentation quality standard
  I praised at v4.154.0 continues.

## What held

- **54/66 goldens.** Byte-identical pass set across all 12 releases
  in this arc. The 12 failures are the same feature-gap bucket.

- **Binary and module growth within expectations.** mnc-stage1:
  3,648,672 bytes (+1.8% from v4.154.0's 3,583,120). Self-hosted
  source: 41,195 LOC (+876 from 40,319). main.ll: 922,330 lines
  (+1.1%). The growth is from abi.mn (75 LOC), semantic.mn
  bare_type_name, emit_llvm.mn inline list ops, and mir_opt.mn inline
  rename helpers. All accounted for, none surprising.

- **Sanitizers improved.** Valgrind: 62 WARNINGS_ONLY / 2 ERRORS
  (was 62/4 at v4.154.0). The 2 remaining ERRORS are GPU feature-gap
  tests (dlopen, not memory safety). Ge.1r closed -- the 4 generics
  valgrind ERRORS from v4.154.0 are gone.

## What concerns me

- **In.1 closure broke the fixed point.** This is the central issue.
  At v4.154.0, fixed-point status was NEAR (4 diff, version metadata
  only, stage2.ll == stage3.ll structurally at 110,127 lines). At
  v5.1.2, `inline_small_functions` was re-enabled. stage2.ll grew to
  120,956 lines (+10,829 from inlining). `llvm-as stage2.ll` now
  fails with:

  ```
  error: use of undefined value '%_inl0_6_t4'
    store %struct.Span %_inl0_6_t4, ptr %_inl0_6_retval.cpy
  ```

  The `replace_uses_in_instr` helper (30+ variants) handles uses but
  does not handle all definition-use chains in multi-block inlining.
  When the self-hosted compiler compiles itself, the inliner encounters
  patterns where the fresh `%_inl0_6_t4` name is produced in a cloned
  callee block but consumed in a different merge path that the rename
  logic does not reach.

  The 4 tests in `test_inline_rename.py` pass because they use
  synthetic MIR with simpler patterns. The golden tests (54/66) pass
  because the golden programs are small enough that the inliner's
  rename covers all use sites. Self-compilation of 41,195 LOC exposes
  the gap.

  **This is a regression from NEAR to BROKEN.** The v4.134.0 strict
  fixed point was earned over 40+ releases. It was the proof that the
  self-hosted compiler is semantically complete. Losing it in exchange
  for an inliner that cannot handle the compiler's own code is not a
  good trade.

  The correct path was: enable the inliner, run self-compilation as
  the gate, and if self-compilation fails, keep the inliner disabled.
  The v4.152.0 E8 process got this right -- four passes re-evaluated,
  four clean rollbacks when they regressed. v5.1.2 did not apply the
  same discipline. The inliner was enabled, 4 unit tests passed, and
  In.1 was declared closed without running the fixed-point verification
  that would have caught the regression.

  **Proposed: In.1-stage2** (MEDIUM). Self-hosted inliner produces
  invalid SSA when the compiler compiles itself. Fixed point regressed
  from NEAR to BROKEN. Either fix the rename logic for multi-block
  patterns or disable the inliner and revert In.1 to OPEN.

- **PARITY_GAPS.md does not track In.1-stage2.** The MEASUREMENTS.md
  correctly lists `In.1-stage2` as OPEN in its "Remaining Open Items"
  table (line 230). But PARITY_GAPS.md shows In.1 as CLOSED in the
  Historical section (line 203) with no mention of the stage2
  regression. The `~~strikethrough~~` on line 63 marks In.1 as fully
  resolved.

  This is the exact failure mode PARITY_GAPS.md was created to
  prevent. Its own close policy says: "An item does not close just
  because a SESSION_REPORT says it is done." Yet In.1 moved to
  Historical based on the v5.1.2 SESSION_REPORT's closure declaration,
  without the self-compilation gate that would have caught the
  regression.

  The undercount is smaller this time (1 item, not 3), but the pattern
  is identical to what I flagged at v4.154.0: a closure is declared
  before the comprehensive gate is run.

- **Li.1 remains OPEN.** Honestly documented: unit tests pass, live
  goldens regress (54 -> 51). LICM disabled in both pipelines. The
  comment at mir_opt.mn:1468-1477 correctly identifies the root cause
  (single-pass hoist, no fixpoint loop, no preheader insertion). I have
  no complaint here -- this is the correct handling of a pass that is
  not ready. Li.1 is the anti-In.1: an optimizer pass that was honestly
  kept disabled because it fails the live gate.

- **8 test failures in non-bootstrap pytest.** MEASUREMENTS.md
  documents 8 deterministic failures: 2 VERSION drift, 2 lint, 3
  stream runtime, 1 LLVM version. The VERSION drift (binary embeds
  5.1.4, VERSION file reads 5.2.0) means the binary was not rebuilt
  after the v5.2.0 version bump. The lint failures (4 files need
  black/ruff in registry code) mean v5.2.0 was committed without a
  lint pass. The stream runtime failures (3/74 C tests) are
  pre-existing. The LLVM 18 optimization change is environmental. None
  of these are in my domain, but the VERSION drift means the mnc-stage1
  binary on disk is stale -- it is a v5.1.4 binary, not v5.2.0.

## Score reasoning

Prior: 9.1 EXCEEDS.

Deltas:

- **+0.3** -- Cb.15 closure. The sret classifier port is the cleanest
  docket closure in this arc. 75 LOC of pure classification logic in
  abi.mn, 4 call sites updated in emit_llvm.mn, stage2.ll sret count
  nearly doubled. The code is correct, the comments are accurate, and
  the SESSION_REPORT's honesty about the hypothesis being wrong is a
  model of scientific reporting. This was my highest-severity
  carry-forward (MEDIUM at v4.154.0 effective weight) and it is done
  right.

- **+0.15** -- Cb.9a closure. Pragmatic solution to qualified type
  refs. The bare_type_name helper avoids the complexity of a
  module_path field on TypeExpr. 4 references, used at both
  classification points. The concat_self.py fix was a bonus.

- **+0.1** -- Own.1 Phase 1. Correct application of the Cb.7
  zero-after-push pattern at the two sites Viper flagged. The phased
  approach (workaround now, Move instruction later, borrow checker in
  v6.0) is honestly staged and documented.

- **+0.1** -- Ea.1 closure. Analysis ported, limitation documented,
  pass enabled safely (returns f unchanged). The 7 tests cover the
  analysis logic. The comment block explains the codegen annotation
  gap.

- **+0.1** -- PARITY_GAPS.md. The tracking document I demanded exists
  and has a close policy. The 27% undercount complaint is addressed at
  the process level. This is credit for responding to reviewer
  feedback.

- **+0.1** -- Perf.1 dual-emitter discipline. Both emitters patched
  simultaneously for inline list ops. No new parity gap opened. This
  is the correct engineering practice and it should be the norm, not
  the exception.

- **+0.05** -- Ge.1r closure. Valgrind ERRORS: 4 -> 2, and the
  remaining 2 are a different class (GPU dlopen, not memory safety).

- **-0.6** -- Fixed-point regression from NEAR to BROKEN. This is the
  largest single deduction I have ever applied. The v4.134.0 strict
  fixed point was the crown jewel of the self-hosted compiler. NEAR
  (4 diff) was an acceptable steady state. BROKEN (llvm-as failure)
  is not. The regression was avoidable: running `verify_fixed_point.sh`
  before declaring In.1 closed would have caught it. The E8 process
  (v4.152.0) handled the same class of decision correctly -- four
  passes re-evaluated, four rollbacks when they regressed. v5.1.2 did
  not apply the same rigor. The inliner was enabled based on 4 unit
  tests and 54 golden tests without the self-compilation gate.

- **-0.1** -- PARITY_GAPS.md does not track In.1-stage2. In.1 is
  marked CLOSED in the Historical section while the stage2 regression
  is open. The document was created specifically to prevent this
  pattern.

- **-0.1** -- mnc-stage1 binary stale. The binary on disk embeds
  v5.1.4 but the VERSION file says v5.2.0. A stale binary means any
  reviewer running `./mnc-stage1 --version` gets a misleading answer.

Arithmetic:

- Base: 9.1
- Positives: +0.3 + 0.15 + 0.1 + 0.1 + 0.1 + 0.1 + 0.05 = +0.90
- Negatives: -0.6 - 0.1 - 0.1 = -0.80
- Raw: 9.1 + 0.90 - 0.80 = **9.2**

But I cannot give 9.2 EXCEEDS when the fixed point is BROKEN. The
fixed point is the single most important metric in my domain. A
compiler that cannot compile itself to valid IR is not in an EXCEEDS
state, regardless of how many docket closures it achieved. I am
applying a ceiling: no score above 9.0 while the fixed point is
BROKEN (not NEAR, not STRICT -- BROKEN, meaning llvm-as rejects
stage2.ll).

Ceiling-adjusted: **8.8**.

The 0.4 penalty from the ceiling (9.2 -> 8.8) is entirely attributable
to the fixed-point regression. Fix the inliner or disable it, restore
NEAR or STRICT, and the score returns to 9.2+ at the next panel.

## Carry-forward (for v5.3.0+)

| ID | Severity | Scope |
|---|---|---|
| **In.1-stage2** | **MEDIUM** | Inliner SSA rename produces invalid IR when the compiler compiles itself. Fixed point BROKEN. Either fix multi-block rename or disable the pass. |
| Li.1 | LOW | LICM: unit tests pass, live goldens regress. Needs fixpoint + preheader insertion. |
| Own.1 P2 | LOW | Move instruction + drop-glue in self-hosted emitter (v5.2+ deferred) |
| Sh.4-7/9a | LOW | Feature-gap bucket (tensor, async, closures, mutable views, slices) |

That is 4 items (or 9 if you expand Sh.4-7/9a). Delta from v4.154.0:
-5 closed (Cb.15, Cb.9a, In.1, Ea.1, PARITY_GAPS tracking), +1 new
(In.1-stage2 MEDIUM), -1 resolved by overlap (Own.1 P1 closed, P2
remains). Net: -4 items. The carry-forward shrank, but the one new
item (In.1-stage2) is the highest severity I have opened since Cb.5
at v4.140.0.

## The fixed-point lecture

I said at v4.134.0: "La Culebra Se Muerde La Cola." The snake eats
its own tail. That phrase meant something -- it meant the compiler
had reached the point where it could reproduce itself, byte for byte,
through three stages of self-compilation. The 4-line NEAR drift from
Dr.1 was cosmetic. The structure was sound.

In.1 broke the snake's jaw. The compiler now produces IR that LLVM
cannot assemble. This is not a cosmetic regression. This is not a
4-line version-metadata diff. This is `llvm-as` saying "I cannot read
what your compiler wrote about itself."

The fix is likely small -- the `replace_uses_in_instr` helper handles
30+ instruction variants but the rename logic operates on a single
block's post-call instructions plus remaining blocks. The failure
pattern (`%_inl0_6_t4` undefined in a `store` to `%_inl0_6_retval.cpy`)
suggests the callee's cloned block defines the value in a conditional
path that the merge block unconditionally reads. This is the multi-block
phi-like problem that the single-block inliner (lines 1003-1020: "Clone
callee's single block instructions") does not handle -- the inliner only
clones `callee.blocks[0]`, so multi-block callees whose return value is
defined in a non-entry block will produce undefined references in the
merge block.

The path to restoration is clear: either fix the inliner to handle
multi-block callees (real work, real risk), or disable the pass and
restore NEAR (one line change, zero risk). I would accept either.
What I will not accept is the current state: an enabled optimizer
pass that breaks self-compilation, documented as CLOSED.

---

## Reproducibility

```bash
# Module sizes (verified 2026-04-22)
wc -l mapanare/self/*.mn
# 41,195 total

# Cb.15 verification
grep -c 'sret\|classify_return\|use_sret' mapanare/self/emit_llvm.mn
# 35 (was 0 at v4.154.0)

# Cb.9a verification
grep -c 'bare_type_name' mapanare/self/semantic.mn
# 4

# In.1 rename helpers
grep -c '_inl.*_dst\|replace_uses_in_instr' mapanare/self/mir_opt.mn
# 5

# Own.1 Phase 1
grep -n 'Own.1' mapanare/self/lower.mn
# 330, 364

# abi.mn classifier functions
grep -c 'abi_classify\|abi_sysv\|abi_win64\|abi_aapcs64' mapanare/self/abi.mn
# 8

# Inliner enabled in pipeline
grep -n 'inline_small_functions' mapanare/self/mir_opt.mn
# 937 (definition), 1449 (comment), 1467 (ENABLED in pipeline)

# LICM disabled in pipeline
grep -n 'let f7' mapanare/self/mir_opt.mn
# f7 = f6 (identity, pass disabled)

# Escape analysis enabled
grep -n 'escape_analysis_function' mapanare/self/mir_opt.mn
# 1370 (definition), 1490 (ENABLED in pipeline)

# Binary size
ls -la mapanare/self/mnc-stage1
# 3,648,672 bytes

# main.ll line count
wc -l mapanare/self/main.ll
# 922,330 lines

# PARITY_GAPS.md In.1 tracking gap
grep -n 'In.1' docs/roadmap/v5/PARITY_GAPS.md
# Lines 63, 203: both show CLOSED / Historical. No In.1-stage2 entry.
# Compare: MEASUREMENTS.md line 230: In.1-stage2 NEW OPEN.
```
