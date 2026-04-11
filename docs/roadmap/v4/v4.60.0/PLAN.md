# Mapanare v4.60.0 — Dead Code Audit + Test Honesty Final Pass

> **Arc 6 release 4.** Final sweep before the arc 6 panel. Vulture
> audit, TODO/FIXME cleanup, ancient test-skip tracking audit,
> CARRY_FORWARD.md reconciliation. No new features, no deletions
> beyond dead code.

**Status:** PLANNED
**Breaking:** No (only dead code goes)
**Prerequisite:** v4.59.0
**Delta review:** No
**Full panel:** No (v4.61.0)
**Estimated work:** 1 sprint
**Theme:** Housekeeping. The tree is as clean as it's going to get before the panel.

---

## Scope

### Vulture audit

Run `vulture` (Python dead-code detector) at min confidence 80 across `mapanare/`, `runtime/`, `scripts/`. For every hit:
- If truly dead: delete
- If false positive (e.g., `__exit__` args): annotate with a `# vulture: ignore` comment
- If potentially dead but uncertain: add a TODO comment with a tracking version, keep for now

### TODO/FIXME audit

Grep for `TODO` / `FIXME` / `XXX` / `HACK` comments. For each:
- If older than v4.30.0 and no longer relevant: delete the comment
- If still relevant: make sure it names a tracking version. Add if missing.

### Skip-tracking audit

The `scripts/check_silent_skips.py` gate enforces that every `pytest.mark.skip` / `xfail` has a tracking version. v4.60.0 goes further:
- Every tracking version must be **later than the current version** (`4.60.0`)
- Any tracking that's "past due" — e.g., tracked to `v4.30.0` and still open — is a red flag. Either fix the underlying issue or re-track with a new future version.

### CARRY_FORWARD.md reconciliation

Walk every row in `.reviews/CARRY_FORWARD.md`:
- For CLOSED rows: verify the evidence still resolves
- For OPEN rows: re-verify the tracking version is future, not past
- Any row missing from the Python-emitter vs self-hosted-emitter split columns: add them
- Any duplicate rows: merge

---

## Phase 1 — Vulture audit

- [ ] `python -m vulture mapanare/ runtime/ scripts/ --min-confidence 80 > vulture.log`
- [ ] Walk through `vulture.log` line by line
- [ ] For each hit, classify and act:
  - Dead → delete
  - False positive → annotate
  - Uncertain → TODO with tracking version
- [ ] Commit the deletions + annotations in a single commit for reviewability
- [ ] Record line count before/after in SESSION_REPORT

## Phase 2 — TODO/FIXME audit

- [ ] `grep -rn -E "TODO|FIXME|XXX|HACK" mapanare/ runtime/ scripts/ stdlib/ > todos.log`
- [ ] Walk through
- [ ] For each:
  - Still relevant + future-dated: keep
  - Still relevant + past-dated: re-date
  - No longer relevant: delete
  - Relevant but uncertain: upgrade to a real CARRY_FORWARD.md row
- [ ] Commit changes

## Phase 3 — Skip-tracking audit

- [ ] `python scripts/check_silent_skips.py tests/ --verbose` (add a `--verbose` flag to list every tracking version found)
- [ ] For each tracking version < `v4.60.0`: investigate
  - The bug was fixed and the test was never unmarked: unmark the test
  - The bug is still open: re-track with a future version (`v5.x` if no specific release)
  - The test is obsolete: delete

## Phase 4 — CARRY_FORWARD.md reconciliation

- [ ] Read `.reviews/CARRY_FORWARD.md` row by row
- [ ] For CLOSED rows:
  - Does the evidence pointer (file:line) still resolve?
  - Does the test named still exist?
  - If not: either fix the pointer or note the evidence is stale
- [ ] For OPEN rows:
  - Is the tracking version still future?
  - Re-track if past
- [ ] Missing column split: any 6-emitter-item row that doesn't have Python vs self-hosted split columns, add them (Rattler's v4.31.0 ask)
- [ ] Merge duplicate rows
- [ ] Write a summary to `LEDGER_AUDIT.md` for the panel

## Phase 5 — Comment hygiene

- [ ] `black --check . && ruff check .` — any stale comment that ruff has a rule for (unused imports, commented-out code) — clean up
- [ ] Docstrings: any docstring older than v4.30.0 that mentions deleted features — update or delete
- [ ] `git grep "emit_python_mir\|PythonMIREmitter\|llvmlite" -- "*.py" "*.mn"` — should all be gone from v4.58.0 and v4.59.0; any remaining reference is a bug

## Phase 6 — Stale files

- [ ] `find . -name "*.orig" -o -name "*.bak" -o -name "*.rej"` — delete
- [ ] `find . -name "__pycache__" -prune -o -size 0 -print` — audit zero-byte files; delete if orphaned
- [ ] `git ls-files | xargs -I{} sh -c 'file "{}" 2>/dev/null | grep -qE "ELF|PE32|Mach-O|shared object" && echo "{}"'` — any binary files still tracked? `git rm` them (should have been done in v4.32.0 Phase 2.1, but re-verify)

## Phase 7 — Measurement

- [ ] Record before/after line counts for `mapanare/`, `runtime/`, `tests/`, `docs/`
- [ ] Record the `CARRY_FORWARD.md` row count (OPEN / CLOSED / total)
- [ ] Record the TODO/FIXME count
- [ ] Record the skip count (should be stable — only tracking version changes)

## Phase 8 — LOW sweep (if any remain)

1-2 items.

## Phase 9 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.60.0
- [ ] `CHANGELOG.md [4.60.0]` — housekeeping release
- [ ] `SESSION_REPORT.md` with the reconciliation numbers

---

## Exit criteria (12 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Vulture audit run; dead code deleted or annotated | `vulture.log` archived; commit with deletions |
| 2 | TODO/FIXME audit run; stale comments removed | `todos.log` archived; commit |
| 3 | Skip-tracking audit run; no past-due tracking | `check_silent_skips.py --verbose` output |
| 4 | `CARRY_FORWARD.md` row-by-row audit done | `LEDGER_AUDIT.md` |
| 5 | Every CLOSED row's evidence pointer still resolves | manual cross-check |
| 6 | Python vs self-hosted column split complete | ledger schema |
| 7 | Stale files (.orig, .bak, .rej) deleted | `find` returns empty |
| 8 | No tracked binary files remaining | grep+file check |
| 9 | Docstrings / comments referencing deleted features cleaned | grep clean |
| 10 | Line count delta recorded | `SESSION_REPORT` |
| 11 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 12 | Standard closeout clean | CI |

---

## What v4.60.0 does NOT do

- **New features**
- **Deep refactors** — housekeeping only
- **Performance optimization**
- **Anything the panel could be surprised by** — this is a maximally quiet release before v4.61.0

---

## Reference

- `vulture` — https://github.com/jendrikseipp/vulture
- [`v4.31.0/README.md`](../../../../.reviews/v4.31.0/README.md) — the arc-end panel that started the ledger discipline

---

## After v4.60.0

v4.61.0 is the arc 6 panel release. Arc 6 closes with: Python emitter gone, llvmlite gone, dead code swept, tracking reconciled.
