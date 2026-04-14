# Mapanare v4.123.0 — Dead-Code Sweep: optimizer.py + TBAA Declaration

> **Post-panel closeout release 3.** Pure cleanup. Two dead-code items
> have been identified across multiple review cycles: `optimizer.py`
> (1,203 lines, 9% test coverage, reachable only via
> `--legacy-optimizer` which zero tests exercise) and the TBAA metadata
> declaration block in `emit_llvm_text.py` (declared but never attached
> to any load/store, confirmed 100% dead by v4.109.0 forensics). This
> release deletes both. The codebase gets smaller.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.122.0
**Delta review:** No
**Full panel:** No (v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Delete dead code. Net negative lines.

---

## Scope

Two targets:

**`mapanare/optimizer.py` — 1,203 lines.** An AST-level optimizer with constant folding, DCE, agent inlining, and stream fusion. It was the original optimization pass from the early v3.x era. The MIR optimizer (`mir_opt.py`) replaced it functionally. The only entry point is the `--legacy-optimizer` CLI flag, which is undocumented and unused by any test. Test coverage is 9% (mostly import-level). Multiple panel reviewers have flagged it as dead weight.

**TBAA metadata declaration in `emit_llvm_text.py`.** Lines ~910-926 declare TBAA (Type-Based Alias Analysis) metadata nodes for the LLVM IR module. However, no load or store instruction in the emitter ever attaches `!tbaa` metadata. v4.109.0 forensics investigated whether wiring TBAA would improve performance at -O2 and concluded it would not — LLVM's built-in alias analysis already handles our patterns. The declaration is pure noise.

Both deletions are safe: no test depends on `--legacy-optimizer`, no emitted IR references the TBAA nodes. This is the easiest release in the closeout arc.

## Phase 1 — Delete optimizer.py

- [ ] Verify no imports of `optimizer` or `optimizer.py` exist outside test files:
  ```bash
  grep -rn "from mapanare.optimizer" mapanare/ --include="*.py"
  grep -rn "import optimizer" mapanare/ --include="*.py"
  ```
- [ ] Remove `mapanare/optimizer.py`
- [ ] Remove the `--legacy-optimizer` CLI flag from `mapanare/cli.py`
- [ ] Remove any imports of `optimizer` from `mapanare/__init__.py` (if present)
- [ ] Remove any test files that exclusively test `optimizer.py` (e.g., `tests/test_optimizer.py` or `tests/optimizer/`)
- [ ] If other test files import `optimizer`, remove those imports
- [ ] Update `CLAUDE.md` if it references `optimizer.py` in the module list

## Phase 2 — Delete TBAA metadata declaration

- [ ] Read `mapanare/emit_llvm_text.py` around lines 910-926 — find the TBAA declaration block
- [ ] Verify no `!tbaa` metadata references exist in the emitter:
  ```bash
  grep -n "tbaa" mapanare/emit_llvm_text.py
  ```
- [ ] Delete the TBAA declaration block
- [ ] Verify no test asserts on the presence of TBAA metadata in emitted IR

## Phase 3 — Run full test suite

- [ ] `make test` — target: 0 failures (no test should depend on either deleted component)
- [ ] `make lint` — clean (removing a module may affect import sorting)
- [ ] Rebuild mnc-stage1: `python scripts/build_stage1.py` — verify the build succeeds without optimizer.py
- [ ] Run golden tests to verify no regression: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`

## Phase 4 — Verify and document

- [ ] Count lines removed: `git diff --stat` should show ~1,200+ lines net negative
- [ ] Verify `--legacy-optimizer` is no longer accepted by the CLI:
  ```bash
  python -m mapanare --legacy-optimizer run tests/golden/01_hello.mn
  # Should error: unrecognized argument
  ```
- [ ] Document the deletion rationale in the SESSION_REPORT

## Phase 5 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.123.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (7 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `mapanare/optimizer.py` deleted | `git diff --stat` |
| 2 | `--legacy-optimizer` CLI flag removed | CLI error on unknown flag |
| 3 | TBAA metadata declaration removed from `emit_llvm_text.py` | diff |
| 4 | `make test` green (0 failures) | test log |
| 5 | `make lint` clean | lint log |
| 6 | mnc-stage1 builds and golden tests pass | build + test log |
| 7 | Net line count reduction >= 1,200 | `git diff --stat` |

---

## What this release does NOT do

- **Add new optimization passes** — the MIR optimizer (`mir_opt.py`) is the active optimizer. No changes to it.
- **Wire TBAA metadata** — v4.109.0 forensics showed it wouldn't help at -O2. The declaration is deleted, not replaced.
- **Fix bugs** — this is pure cleanup. No behavior changes.
- **Touch the self-hosted compiler** — `optimizer.py` is Python-only. The self-hosted compiler never had this module.
- **Run a panel** — the next panel is v4.130.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| A test imports `optimizer` transitively and fails | low | low | Phase 1 grep catches all imports; Phase 3 test run confirms |
| Some undocumented script uses `--legacy-optimizer` | low | low | Grep the entire repo for `legacy-optimizer`; if found, remove the reference |
| Removing TBAA declarations triggers an LLVM verifier warning | very low | medium | TBAA declarations without references are legal LLVM IR; but Phase 3 rebuild confirms |
| A reviewer at v4.130.0 panel asks why optimizer was deleted | low | low | SESSION_REPORT documents the rationale: 9% coverage, zero test usage, superseded by mir_opt.py |

---

## After v4.123.0

v4.124.0 tackles Rt.1: unboxed enum payloads for pointer-fits variants. `enum_match` is 24x slower than C and 2x slower than Rust. The gap is payload boxing — heap allocation on every match arm. The fix: if a variant's payload fits in i64, store it inline. This is the biggest performance opportunity in the closeout arc.
