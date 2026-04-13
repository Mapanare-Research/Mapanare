# Mapanare v4.59.0 — llvmlite JIT Deprecation + Deletion (A4)

> **Arc 6 release 3.** Closes `CARRY_FORWARD.md` A4. `mapanare/jit.py`
> and the llvmlite dependency removed. Combined deprecation + deletion
> in one release because the footprint is smaller than the Python
> emitter.

**Status:** DONE (2026-04-12)
**Session log:** All 9 phases executed. All 12 exit criteria green.
**Decisions taken:** Decision 1: delete cmd_jit entirely (Option A). Decision 2: fully remove llvmlite (no optional dep). Decision 3: standalone migration doc.
**Breaking:** **Minor breaking** (`mapanare jit` removed; replacement is `mapanare run`)
**Prerequisite:** v4.58.0
**Delta review:** No
**Full panel:** No (v4.61.0)
**Estimated work:** 1 sprint
**Theme:** Drop the llvmlite Python dependency. `mnc run` is the canonical JIT-equivalent.

---

## Why combined deprecation + deletion

The v4.57.0 → v4.58.0 pattern was "deprecate, then delete" because the Python backend had test infrastructure, conftest entries, migration implications, and possibly users. The llvmlite JIT is simpler:
- It's a single Python file (`mapanare/jit.py`).
- It was never a primary compile path — the text-based `emit_llvm_text.py` has been canonical since v4.2.0.
- `mapanare jit` is explicitly documented as experimental.
- No known user depends on it.

A combined release is fine. If the lead is worried, split into v4.59.0 (deprecate) and v4.60.0 (delete) — same scope either way.

---

## Scope

1. Delete `mapanare/jit.py`
2. Delete or rewrite `mapanare cli.py cmd_jit` — either remove entirely, or alias to `mnc run` (AOT compile + execvp)
3. Remove `llvmlite` from `requirements*.txt`, `setup.py`, `pyproject.toml`
4. Delete `tests/jit/` or migrate remaining tests
5. Update CLAUDE.md architecture notes to say llvmlite is out

---

## Phase 1 — Delete `mapanare/jit.py`

- [ ] `git rm mapanare/jit.py`
- [ ] Grep the tree: `grep -rn "llvmlite\|jit_" mapanare/ tests/` — find every stale reference
- [ ] Delete each

## Phase 2 — CLI `cmd_jit` decision

**Option A: delete `cmd_jit` entirely.**
- Users who wanted a JIT now use `mapanare run` which compiles-and-execs.
- Simplest; matches the "single canonical way" philosophy.
- Breaks `mapanare jit foo.mn` as a command.

**Option B: alias `cmd_jit` to `cmd_run`.**
- `mapanare jit foo.mn` still works; it just invokes the AOT compiler.
- Less breaking.
- Slight lie: it's not JIT, it's AOT.

**Decision: Option B for v4.59.0.** Alias with a deprecation warning on stderr: "mapanare jit is now an alias for mapanare run; will be removed in v4.60.0." Then delete in v4.60.0 Phase 5 (or defer further if user feedback).

Actually wait — simpler: **Option A.** The deprecation cycle was already the v4.57.0→v4.58.0 pattern for the Python emitter. For the JIT, since nobody's asking for it, one-release strike is fine. Users see a "command not found" + the CHANGELOG entry explains the migration.

**Final decision: Option A.** Delete `cmd_jit`. Document in CHANGELOG + migration doc.

- [ ] `mapanare/cli.py` — delete `cmd_jit` function, delete the subparser registration
- [ ] Help text no longer mentions `jit`

## Phase 3 — Dependency cleanup

- [ ] `requirements.txt` / `requirements-dev.txt` — remove `llvmlite` line
- [ ] `setup.py` / `pyproject.toml` — remove `llvmlite` from `install_requires`
- [ ] `Pipfile` / `poetry.lock` — if present, regenerate without llvmlite
- [ ] Fresh `pip install -e ".[dev]"` — confirm no llvmlite pulled in
- [ ] `pip show llvmlite` — confirm not installed in the clean env

## Phase 4 — Test cleanup

- [ ] Delete `tests/jit/` directory if present
- [ ] Grep for `import llvmlite` in tests — delete any remaining tests
- [ ] `tests/conftest.py` — any llvmlite-specific fixtures or markers removed
- [ ] `scripts/check_silent_skips.py` — re-run, should be clean

## Phase 5 — Documentation cleanup

- [ ] `docs/SPEC.md` — any mention of JIT compilation: rewrite to point at `mapanare run`
- [ ] `docs/cookbook.md` — same
- [ ] `docs/reference.md` — CLI reference, remove `jit` subcommand
- [ ] `CLAUDE.md` — architecture section mentions llvmlite; delete
- [ ] `README.md` — any llvmlite reference removed
- [ ] `docs/migration/v4.58-to-v4.59.md` — new migration doc explaining the JIT removal

## Phase 6 — Tests

- [ ] `tests/test_llvmlite_removed.py`:
  - `test_mapanare_jit_module_absent` — `import mapanare.jit` raises `ImportError`
  - `test_mapanare_cli_no_jit_subcommand` — `mapanare jit` returns non-zero
  - `test_llvmlite_not_in_requirements` — grep requirements files
- [ ] `tests/bootstrap/test_bootstrap_without_llvmlite.py` — fresh install without llvmlite, run the test suite, verify nothing depends on it

## Phase 7 — Line count measurement

- [ ] Record the before/after line counts and the Python dep count
- [ ] Expected: ~300 lines of code deleted + one Python dependency removed

## Phase 8 — LOW sweep

2 items.

## Phase 9 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.59.0
- [ ] `CHANGELOG.md [4.59.0]` — prominent breaking change note for `mapanare jit`
- [ ] `.reviews/CARRY_FORWARD.md` — A4 CLOSED
- [ ] SESSION_REPORT

---

## Exit criteria (12 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `mapanare/jit.py` deleted | `ls` returns not-found |
| 2 | No remaining `import llvmlite` anywhere | grep clean |
| 3 | `cmd_jit` deleted | `mapanare jit` returns "command not found" |
| 4 | `llvmlite` removed from requirements | diff |
| 5 | Fresh install doesn't pull llvmlite | `pip show` empty |
| 6 | `tests/jit/` deleted | `ls` empty |
| 7 | Documentation scrubbed of JIT references | `check_docs_drift.py` + grep |
| 8 | Migration doc written | `docs/migration/v4.58-to-v4.59.md` |
| 9 | `test_llvmlite_removed.py` regression gate | passes |
| 10 | Bootstrap chain still works | `build_from_seed.sh` clean |
| 11 | A4 CLOSED | ledger diff |
| 12 | Standard closeout clean | CI |

---

## What v4.59.0 does NOT do

- **Replace `mapanare jit` with a true JIT** (using LLVM ORC or similar). Would be a v5.x HMR feature.
- **Remove llvmlite imports in other tools** that aren't part of `mapanare/` proper — those are user code, not our concern.

---

## Reference

- [`.reviews/CARRY_FORWARD.md`](../../../../.reviews/CARRY_FORWARD.md) A4

---

## After v4.59.0

v4.60.0 is the final dead-code sweep before the arc 6 panel. All TODOs, FIXMEs, stale skips, and ancient tracking comments get audited.
