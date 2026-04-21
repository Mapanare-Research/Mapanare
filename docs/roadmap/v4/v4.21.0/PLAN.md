# Mapanare v4.21.0 — Quality Gate + CI/CD

> Fix everything that was rushed. CI catches regressions. Tests prove features work.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.20.0

---

## The Problem

v4.18.0-v4.20.0 shipped syntax/keywords but deferred runtime wiring.
CI/CD was not updated. The fixed-point verification has no CI workflow.
Several test suites have regressions. This version makes everything honest.

---

## Phase 1: Fix pytest regressions

- [ ] Run full `python3 -m pytest tests/ -q --tb=short` — identify ALL failures
- [ ] Categorize: pre-existing vs introduced by v4.14.0-v4.20.0
- [ ] Fix all regressions we introduced (ModuleLetDef side effects, etc.)
- [ ] Target: same pass count as v4.13.0 baseline or higher
- [ ] Run `python3 -m pytest tests/ -q --tb=no` — record total pass count

## Phase 2: CI/CD update

- [ ] Update `.github/workflows/ci.yml` — add const, async, await keywords to test matrix
- [ ] Add `.github/workflows/fixed-point.yml`:
  - Build stage1 from Python
  - Stage1 compiles mnc_all.mn → stage2.ll
  - Validate with llvm-as
  - Build stage2 binary
  - Stage2 compiles mnc_all.mn → stage3.ll
  - Compare stage2.ll vs stage3.ll (report diff count)
- [ ] Add golden test count assertion in CI (must be >= 45)
- [ ] Add stage2 module count assertion (must be 11/11)

## Phase 3: WASM emission validation

- [ ] Run WAT emission for all `examples/wasm/*.mn` — the step CI runs
- [ ] Fix any WAT emission failures
- [ ] Verify: `python3 -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null`

## Phase 4: GCC clean check

- [ ] `gcc -c -fsyntax-only -Wall -Wextra -Werror runtime/native/mapanare_core.c -I runtime/native`
- [ ] Fix any new warnings from runtime changes (mn_list_detach NULL check, etc.)

## Phase 5: Documentation sync

- [ ] Update CLAUDE.md with new commands (mapanare bind, const, async/await)
- [ ] Update test counts in CLAUDE.md
- [ ] Update golden test count in README badges

---

## Exit Criteria

| Check | Required |
|-------|----------|
| pytest regressions fixed (0 new failures) | YES |
| fixed-point.yml CI workflow added | YES |
| WASM emission validated | YES |
| GCC -Wall -Wextra -Werror clean | YES |
| CLAUDE.md updated | YES |
| 45/45 golden | YES |
| 11/11 stage2 | YES |
