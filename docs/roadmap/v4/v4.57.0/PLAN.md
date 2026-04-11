# Mapanare v4.57.0 — Python Emitter Deprecation (Warnings Only)

> **Arc 6 release 1.** Warning-only release. Adds loud deprecation
> warnings to every public entry of `mapanare/emit_python_mir.py`.
> No deletion yet — that's v4.58.0. One release of advance warning
> so users of the Python backend (if any exist) have time to
> migrate.

**Status:** PLANNED
**Breaking:** No (still works; just warns)
**Prerequisite:** v4.56.0 (arc 5 panel PASS)
**Delta review:** No
**Full panel:** No (v4.61.0)
**Estimated work:** 1 sprint (mostly documentation + migration guide)
**Theme:** Give the user a heads-up. The Python backend is going away.

---

## Why warn before delete

The recovery arc's anti-rush rule: "don't break things without advance notice, even things you're sure nobody uses." Users who have set up a CI pipeline that calls `mapanare emit-mir-python` get a stderr warning in v4.57.0, see it in their CI logs, have one release to react, and then see the actual removal in v4.58.0.

It also gives the lead one release to confirm they actually want to delete it. If the v4.57.0 warning is shipped and users complain, the deletion in v4.58.0 can be reconsidered.

---

## Scope

- Add `warnings.warn(..., DeprecationWarning)` at every public entry point of `mapanare/emit_python_mir.py`
- Add stderr warnings to CLI commands that dispatch through the Python emitter (`cmd_emit_mir_python`, `cmd_jit` if it uses Python, `cmd_run` if it defaults to Python)
- Write `docs/migration/v4.57-to-v4.58.md` explaining what's going away, why, and how to migrate to LLVM backend
- Update `tests/conftest.py` — any `_PYTHON_MIR_XFAIL` tracking version reset to `v4.58.0` (currently v5.0.0; A3 was scheduled for v5.0.0 but we're doing it in v4.58.0)

---

## Phase 1 — Warnings on Python emitter entry points

- [ ] `mapanare/emit_python_mir.py` — find every function / class / method that's called from outside the module. Add at the top of each:

  ```python
  import warnings

  class PythonMIREmitter:
      def __init__(self, ...):
          warnings.warn(
              "PythonMIREmitter is deprecated and will be removed in v4.58.0. "
              "Use the LLVM backend via `mnc run` or `mnc build`. "
              "See docs/migration/v4.57-to-v4.58.md for the migration path.",
              DeprecationWarning,
              stacklevel=2,
          )
          # ... existing body

      def emit(self, ...):
          warnings.warn(...)
          # ... existing body
  ```

- [ ] `mapanare/jit.py` — if `llvmlite` JIT is its own beast, add warnings there too (A4 is v4.59.0 but v4.57.0 can pre-warn)

## Phase 2 — CLI warnings

- [ ] `mapanare/cli.py` — find CLI commands that dispatch to Python backend:
  - `cmd_emit_mir_python` — warn and still run
  - `cmd_run --backend python` — if this flag exists, warn
  - Any default dispatch that hits Python
- [ ] Warnings go to stderr (not stdout — stdout is usually captured for IR output)
- [ ] Include the v4.58.0 target so users know when to fix

## Phase 3 — Migration guide

- [ ] `docs/migration/v4.57-to-v4.58.md` — new file:
  - What's going away: `PythonMIREmitter`, `mapanare/emit_python_mir.py`, any test infrastructure built around it
  - Why: the LLVM backend has been canonical since v4.2.0; the Python backend was retained for bootstrap convenience and hasn't been touched except for occasional bit-rot fixes
  - How to migrate:
    - If you're running `mapanare run foo.mn --backend python`: drop `--backend python`, the default is LLVM
    - If you're running `mapanare emit-mir-python foo.mn`: use `mapanare emit-llvm foo.mn` instead
    - If you have CI that depends on Python-style MIR output: rewrite to consume LLVM IR
  - Timeline: v4.57.0 warnings, v4.58.0 deletion, v4.59.0 llvmlite JIT deletion (separate)
  - FAQ: "What if I rely on Python-specific features?" → "Report it before v4.58.0 ships and we can discuss"

## Phase 4 — Test honesty

- [ ] `tests/conftest.py` — the `_PYTHON_MIR_XFAIL` entries are tracked to v5.0.0. Retarget to **v4.58.0** (the actual deletion release).
- [ ] Run `scripts/check_silent_skips.py` — should still be clean (the retarget is a tracking-version bump, not a new skip).

## Phase 5 — Tests

- [ ] `tests/test_deprecation_warnings.py`:
  - `test_python_emitter_instantiation_warns` — pytest can capture warnings
  - `test_emit_mir_python_cli_warns` — capture stderr of the CLI
  - `test_migration_guide_exists` — file exists at the right path
  - `test_python_emitter_still_works` — regression: warnings are not errors, the emitter still emits valid output

## Phase 6 — LOW sweep

2 items.

## Phase 7 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.57.0
- [ ] `CHANGELOG.md [4.57.0]` — includes the deprecation notice prominently
- [ ] SESSION_REPORT

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `PythonMIREmitter.__init__` emits DeprecationWarning | `test_python_emitter_instantiation_warns` |
| 2 | All public entries warn | grep `warnings.warn` count matches public method count |
| 3 | CLI commands print stderr warnings | `test_emit_mir_python_cli_warns` |
| 4 | `docs/migration/v4.57-to-v4.58.md` written | file exists |
| 5 | `_PYTHON_MIR_XFAIL` tracking retargeted to v4.58.0 | conftest.py diff |
| 6 | `check_silent_skips.py` still clean | CI gate |
| 7 | Python emitter still works (regression test) | `test_python_emitter_still_works` |
| 8 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 9 | CHANGELOG.md prominently mentions deprecation | diff review |
| 10 | Standard closeout clean | CI |

---

## What v4.57.0 does NOT do

- **Delete anything.** That's v4.58.0.
- **Convert warnings to errors.** DeprecationWarning is silent by default in Python; users who have `-W error` see them as errors, which is correct.
- **Block compilation** if the user ignores the warning.

---

## Reference

- Python `warnings` module — https://docs.python.org/3/library/warnings.html#warnings.DeprecationWarning

---

## After v4.57.0

v4.58.0 is the deletion: `mapanare/emit_python_mir.py` and all related infrastructure gone. A3 closed.
