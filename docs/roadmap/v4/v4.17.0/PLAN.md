# Mapanare v4.17.0 — Fixed-Point Bootstrap (Python Independence)

> The compiler compiles itself. Python bootstrap becomes optional.

**Status:** DONE (near fixed-point: 0.062% diff)
**Breaking:** No
**Prerequisite:** v4.16.0

---

## The Goal

This is the milestone. After v4.17.0:

- `mnc-stage1` (built by Python bootstrap) compiles `mnc_all.mn` to produce `mnc-stage2`
- `mnc-stage2` compiles `mnc_all.mn` to produce `mnc-stage3`
- `mnc-stage2` output == `mnc-stage3` output (fixed point)
- The Python bootstrap is still available but is no longer REQUIRED

This is the moment the language becomes self-sustaining. Every version after
this can be built from the previous version's binary. The Python code becomes
a reference implementation, not a dependency.

---

## Phase 1: Audit cross-module type resolution

- [ ] Run `python3 scripts/ir_doctor.py stage2` — list all 11 modules
- [ ] For each module that fails or produces different IR, identify the gap
- [ ] Common gaps: struct type definitions not visible across modules, enum
      variant numbering inconsistent, function signatures mismatched
- [ ] Document every cross-module resolution failure

## Phase 2: Fix struct type visibility

- [ ] When compiling a module, the compiler must know ALL struct types from
      ALL modules (not just the current one)
- [ ] Implement: module header / type-declaration pass before lowering
- [ ] Each module emits its struct types first, all modules see all types
- [ ] Rebuild + golden + stage2

## Phase 3: Fix enum variant numbering

- [ ] Enum variants must have consistent numbering across modules
- [ ] If module A defines `enum Foo { A, B, C }` and module B matches on it,
      both must agree that `A=0, B=1, C=2`
- [ ] Implement: shared enum registry or deterministic ordering from source
- [ ] Rebuild + golden + stage2

## Phase 4: Fix function signature matching

- [ ] Cross-module function calls must use the same calling convention
- [ ] Audit: sret vs direct return, pointer vs value passing
- [ ] Fix any mismatches between the caller's expected signature and the
      callee's actual signature
- [ ] Rebuild + golden + stage2

## Phase 5: Stage2 self-compilation

- [ ] Build mnc-stage1: `python3 scripts/build_stage1.py`
- [ ] Compile mnc_all.mn with mnc-stage1 to produce stage2.ll
- [ ] Build mnc-stage2: `clang -O2 stage2.ll runtime/native/*.c -o mnc-stage2`
- [ ] Compile mnc_all.mn with mnc-stage2 to produce stage3.ll
- [ ] Compare: `culebra diff stage2.ll stage3.ll`
- [ ] If not identical, identify divergent functions and fix

## Phase 6: Fixed-point verification script

- [ ] Implement / update `bash scripts/verify_fixed_point.sh`:
  1. Build stage1 from Python
  2. Build stage2 from stage1
  3. Build stage3 from stage2
  4. `diff stage2.ll stage3.ll` — must be empty
- [ ] Add `--keep` flag to preserve intermediate files for debugging
- [ ] Run it end-to-end, get a clean pass

## Phase 7: CI integration

- [ ] Add fixed-point verification to GitHub Actions
- [ ] New workflow: `fixed-point.yml` — runs on push to dev
- [ ] Failure = regression (the compiler can no longer compile itself)
- [ ] Ship the mnc-stage2 binary as a CI artifact

---

## Exit Criteria

| Check | Required |
|-------|----------|
| mnc-stage1 compiles mnc_all.mn successfully | YES |
| mnc-stage2 compiles mnc_all.mn successfully | YES |
| stage2.ll == stage3.ll (fixed point) | YES |
| verify_fixed_point.sh passes | YES |
| Fixed-point CI workflow added | YES |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
| Python bootstrap still works (not broken) | YES |
