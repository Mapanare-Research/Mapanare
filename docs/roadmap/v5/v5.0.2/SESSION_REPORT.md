# v5.0.2 Session Report — "Reactive Patch"

**Date:** 2026-04-21
**Category:** A — pre-emptive fix (Windows `build-native` job has never
run; fix applied before first merge to `main`)

---

## Triage

`gh run list --workflow=publish.yml --limit 5` showed:

| Run | Conclusion | Title |
|-----|-----------|-------|
| 24703542790 | success | Merge pull request #20 (v5.0.0) |
| 24702964301 | failure | Release — Binary Distribution |
| 24701957507 | failure | Release — Binary Distribution |

The failures are all `publish-pypi` (PyPI already had `mapanare-4.160.0`).
**No `build-native (windows-latest, ...)` job appeared in any run** — the
v5.0.1 commit (`d72426c`) that adds the Windows matrix entry is on `dev`
but has not been merged to `main`. The Windows native build has literally
never executed in CI.

---

## Which candidate fired

**Candidate 1 — `.exe` suffix in `scripts/build_stage1.py:236`.**

### Root cause

`build_stage1.py:236` hard-coded `binary = SELF_DIR / "mnc-stage1"`.
On Windows, MinGW GCC given `-o mapanare/self/mnc-stage1` produces
`mapanare/self/mnc-stage1.exe`. Line 283 (`binary.stat().st_size`)
would throw `FileNotFoundError` because the path without `.exe` does
not exist. The `strip` call at line 293 and the `return binary` at
line 303 would also reference the wrong path.

### Fix

`scripts/build_stage1.py:236` — 1 line added, 1 line changed:

```python
# Before:
binary = SELF_DIR / "mnc-stage1"

# After:
binary_name = "mnc-stage1.exe" if sys.platform == "win32" else "mnc-stage1"
binary = SELF_DIR / binary_name
```

All downstream uses (`-o str(binary)`, `binary.stat()`, `strip`,
`return binary`) follow the new name transparently. No other file
changes needed — the `publish.yml` workflow already expects
`mnc-stage1.exe` at the `cp` step:

```yaml
cp mapanare/self/mnc-stage1.exe "${{ matrix.artifact }}"
```

### CI verification

Pending — v5.0.1 + v5.0.2 have not been merged to `main` yet. CI will
run on the next `dev → main` merge. This report will be updated with
the CI run URL once it goes green.

---

## Other candidates — not fired

| # | Candidate | Status |
|---|-----------|--------|
| 2 | `strip` fails on MinGW output | Not observed (deferred to v5.0.3 if needed) |
| 3 | `-Werror` trips on MinGW warning | Not observed |
| 4 | `__chkstk` alias undefined | Not observed |
| 5 | Smoke test version mismatch | Not observed |

---

## Files changed

| File | Change |
|------|--------|
| `scripts/build_stage1.py:236` | `.exe` suffix on Windows |
| `VERSION` | `5.0.1` → `5.0.2` |
| `CLAUDE.md` | v5.0.2 entry added |
| `docs/roadmap/ROADMAP.md` | "Where We Are" entry added |
| `docs/roadmap/v5/v5.0.2/SESSION_REPORT.md` | This file |
