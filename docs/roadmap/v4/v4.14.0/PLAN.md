# Mapanare v4.14.0 — Break Fix + 11/11 Stage2

> Fix 3 CRITICAL break-inside-nested-control findings. Fix main.mn stage2 crash. Zero Culebra CRITICAL.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.13.0

---

## The Problem

Culebra v2.3.1 found 3 CRITICAL `break-inside-nested-control` findings in the
Python lowerer: `break` statements inside nested `if` / `for` constructs are
silently dropped during MIR lowering. The affected loops run to their maximum
iteration count instead of exiting early. The self-hosted compiler has 3 call
sites where this pattern appears in `.mn` code, compiled through the Python
bootstrap. Separately, main.mn crashes in stage2 because drop glue frees
strings through compound pointer returns that escape analysis cannot follow.

Until both are fixed, stage2 is 10/11 and Culebra reports CRITICAL findings.

---

## Phase 1: Identify affected .mn sites

- [ ] Run `culebra scan mapanare/self/main.ll --id break-inside-nested-control`
- [ ] Cross-reference findings with `.mn` source lines
- [ ] Document the 3 sites: which module, which function, which loop
- [ ] For each site, verify the bug: does the loop run to max iterations?

## Phase 2: Rewrite affected functions (flag pattern)

- [ ] For each of the 3 sites, rewrite the loop to use a `done` flag:
  ```
  let done: Bool = false
  for i in range(0, n):
      if done:
          # skip
      else:
          if condition:
              let done: Bool = true
          else:
              # loop body
  ```
- [ ] Rebuild after each rewrite: `bash scripts/rebuild.sh`
- [ ] Verify: `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
- [ ] 40/40 golden after all rewrites

## Phase 3: Fix main.mn stage2 crash

- [ ] Run `python3 scripts/ir_doctor.py stage2` — identify the crash point
- [ ] Run `culebra valgrind-map ./mapanare/self/mnc-stage1 mapanare/self/main.mn`
- [ ] Root cause: drop glue frees strings returned through compound pointers
- [ ] Fix approach: extend escape analysis in `emit_llvm_text.py` to track
      heap pointers through struct returns in modular compilation
- [ ] Alternative: mark main.mn's entry-point returns as no-drop
- [ ] Rebuild + stage2: `python3 scripts/ir_doctor.py stage2`
- [ ] Target: 11/11 stage2 modules valid

## Phase 4: Culebra verification

- [ ] `culebra scan mapanare/self/main.ll --severity critical` — 0 findings
- [ ] `culebra scan mapanare/self/main.ll --id break-inside-nested-control` — 0 findings
- [ ] `culebra triage mapanare/self/main.ll --brief` — no CRITICAL
- [ ] Full golden + stage2

## Phase 5: Fix Python lowerer (root cause)

- [ ] Fix `break` handling in `mapanare/lower.py` for nested if/for
- [ ] The break MIR instruction must propagate through nested control flow
- [ ] Add regression test: `tests/semantic/test_break_nested.py`
- [ ] Run full pytest: `make test`

---

## Exit Criteria

| Check | Required |
|-------|----------|
| 3 break-inside-nested-control sites rewritten | YES |
| Python lowerer break bug fixed | YES |
| main.mn stage2 crash fixed | YES |
| Culebra: 0 CRITICAL findings | YES |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
| Regression test for nested break | YES |
