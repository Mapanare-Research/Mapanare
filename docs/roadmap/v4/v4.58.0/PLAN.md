# Mapanare v4.58.0 — Python Emitter Deletion (A3)

> **Arc 6 release 2.** Closes `CARRY_FORWARD.md` A3. `mapanare/emit_python_mir.py`
> deleted (~1,220 lines). `cmd_run` / `cmd_compile` default paths updated
> to skip the deprecated Python branch. Test infrastructure cleaned up.

**Status:** PLANNED
**Breaking:** **Minor breaking** (the deprecated Python backend is removed; warnings in v4.57.0 gave users one release to migrate)
**Prerequisite:** v4.57.0 (deprecation warnings shipped)
**Delta review:** No
**Full panel:** No (v4.61.0)
**Estimated work:** 1 sprint
**Theme:** 1,220 lines of dead code leave the tree. The bootstrap chain stays LLVM-only.

---

## Scope

1. Delete `mapanare/emit_python_mir.py`
2. Delete any CLI commands / flags that dispatched to it
3. Delete test files tagged `_PYTHON_MIR_XFAIL`
4. Remove the `_PYTHON_MIR_XFAIL` entry from `tests/conftest.py`
5. Verify bootstrap chain doesn't touch it (it shouldn't — already LLVM-only since v4.2.0)

---

## Phase 1 — Delete the file

- [ ] `git rm mapanare/emit_python_mir.py`
- [ ] Grep the tree for any remaining imports: `grep -rn "emit_python_mir\|PythonMIREmitter" mapanare/ tests/`
- [ ] Delete each stale reference. Expected sites:
  - `mapanare/cli.py` — the dispatch to the Python emitter
  - `mapanare/__init__.py` — if it re-exports `PythonMIREmitter`, remove
  - `tests/conftest.py` — `_PYTHON_MIR_XFAIL` list entry
  - `tests/test_emit_python_mir.py` (if exists) — delete the file

## Phase 2 — CLI cleanup

- [ ] `mapanare/cli.py` `cmd_emit_mir_python` (if exists) — delete the function, remove the subparser registration
- [ ] `cmd_run` — if it had a `--backend python` branch, delete it. Default is LLVM; no branch needed.
- [ ] `cmd_compile` — same
- [ ] `cmd_jit` — v4.58.0 does NOT delete `cmd_jit`; that's v4.59.0 (A4 llvmlite JIT removal). v4.58.0 may touch `cmd_jit` if it had a Python fallback path. Remove that fallback if present.
- [ ] Help text for remaining commands — remove any mention of `--backend python`
- [ ] Test: run `mapanare --help` manually, verify no Python-backend mentions

## Phase 3 — Test infrastructure cleanup

- [ ] `tests/conftest.py`:
  - Delete the `_PYTHON_MIR_XFAIL` list
  - Delete any pytest fixture that enabled Python-backend testing
  - Delete any `pytest.mark.python_backend` markers if they existed
- [ ] Delete test files that were exclusively Python-backend:
  - `tests/test_emit_python_mir.py` (if exists)
  - Any `tests/python_mir/` subdirectory
  - Any `tests/end_to_end/test_python_backend.py`
- [ ] Keep tests that test both backends — just delete the Python branches.

## Phase 4 — Documentation cleanup

- [ ] `docs/SPEC.md` — any section describing the Python backend: rewrite to say LLVM is canonical
- [ ] `docs/cookbook.md` — any example using `mapanare emit-mir-python`: delete or rewrite
- [ ] `docs/reference.md` — CLI reference, compilation pipeline diagrams
- [ ] `CLAUDE.md` — the compiler pipeline section mentions Python transpiler as "DEPRECATED" — update to just not mention it
- [ ] `README.md` — no Python-backend mentions
- [ ] `docs/roadmap/ROADMAP.md` and v4/README.md — v4.58.0 row with "Python backend removed"

## Phase 5 — Bootstrap chain audit

- [ ] `scripts/build_from_seed.sh` — verify it doesn't call any deleted symbol
- [ ] `scripts/build_stage1.py` — same
- [ ] Rebuild from seed: `bash scripts/build_from_seed.sh` — must still produce a working `mnc-stage1`
- [ ] This is the load-bearing test: if the bootstrap breaks, v4.58.0 slips until it's fixed

## Phase 6 — Tests

- [ ] `tests/test_python_emitter_deleted.py` — new file:
  - `test_emit_python_mir_file_absent` — grep the tree, expect zero hits for the deleted symbols
  - `test_cli_no_longer_has_python_backend` — run `mapanare --help`, grep for "python", expect no matches
  - `test_import_raises_importerror` — `import mapanare.emit_python_mir` must fail
- [ ] `tests/bootstrap/test_bootstrap_still_works.py` — rebuild mnc-stage1 from scratch, verify output

## Phase 7 — Line count measurement

- [ ] `wc -l mapanare/*.py` — document the before/after line count in SESSION_REPORT
- [ ] Expected: net deletion of ~1,220 lines (the file) + ~100 lines of CLI glue + ~200 lines of test files = **~1,500 lines deleted**

## Phase 8 — LOW sweep

2 items.

## Phase 9 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.58.0
- [ ] `CHANGELOG.md [4.58.0]` — **prominent breaking change note.** "PythonMIREmitter has been removed. Use the LLVM backend. See `docs/migration/v4.57-to-v4.58.md` for details."
- [ ] `.reviews/CARRY_FORWARD.md` — A3 CLOSED
- [ ] SESSION_REPORT

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `mapanare/emit_python_mir.py` deleted | `ls` returns not-found |
| 2 | No remaining imports of `emit_python_mir` or `PythonMIREmitter` | grep clean |
| 3 | CLI has no `--backend python` flag | manual `--help` |
| 4 | `_PYTHON_MIR_XFAIL` removed from conftest | diff |
| 5 | Python-backend-only test files deleted | `ls` empty |
| 6 | Documentation scrubbed of Python backend | `check_docs_drift.py` + grep |
| 7 | `CLAUDE.md` updated | diff |
| 8 | Bootstrap chain still works | `build_from_seed.sh` clean |
| 9 | `test_python_emitter_deleted.py` regression gate | file exists + passes |
| 10 | Stage1 + stage2 still build | rebuild log |
| 11 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 12 | A3 CLOSED in `CARRY_FORWARD.md` | ledger diff |
| 13 | Standard closeout clean | CI |

---

## What v4.58.0 does NOT do

- **Delete llvmlite JIT** — v4.59.0 (A4)
- **Delete the Python-side `emit_c.py`** — that's the C backend, not the Python transpile backend; it stays
- **Break the bootstrap chain** — Phase 5 verifies this explicitly

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Hidden import of `emit_python_mir` somewhere | medium | high | Phase 1 grep + Phase 5 bootstrap test catches it |
| A test relied on Python backend semantics that LLVM backend doesn't match | medium | low | If found, the test is broken — fix it |
| Some user's CI pipeline calls `mapanare emit-mir-python` | low | low | They saw the warning in v4.57.0 and had one release to migrate |

---

## Reference

- [`.reviews/CARRY_FORWARD.md`](../../../../.reviews/CARRY_FORWARD.md) A3
- [`v4.57.0/PLAN.md`](../v4.57.0/PLAN.md)
- [`docs/migration/v4.57-to-v4.58.md`](../../../migration/v4.57-to-v4.58.md) — the user-facing migration doc

---

## After v4.58.0

v4.59.0 is llvmlite JIT deprecation + deletion (A4). Combined into one release because it has a smaller footprint.
