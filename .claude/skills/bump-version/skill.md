# Bump Version

Bump the project version across all files that reference it.

## Instructions

### 1. Parse arguments

The user provides the new version (e.g., `0.5.0`). If not provided,
read the current version from `VERSION` and ask what the new version
should be.

### 2. Run `scripts/bump_version.py`

This script handles the full sweep — `VERSION`, all four README
badges (English / Spanish / Portuguese / Chinese, with their
localized label keys `version-` / `versao-` / `版本-`), and the
`CHANGELOG.md` section + comparison links — in one shot. It refuses
non-forward bumps and is idempotent.

```bash
python3 scripts/bump_version.py <new_version> --dry-run   # preview
python3 scripts/bump_version.py <new_version>             # apply
```

The script is the source of truth. Do NOT do this work by hand —
v5.11.2 burned a CI iteration on missing the `versao-` and `版本-`
badge variants when the previous instructions only said "search every
`docs/README.*.md` file for `version-<old>`". The Python script knows
about all the locale keys.

### 3. Fill in the new CHANGELOG section

The script creates an empty `### Added` / `### Changed` / `### Fixed`
template at the top of the new version block. Replace with the
actual changes. Keep claims grounded in real files — the
`scripts/check_changelog_honesty.py` gate runs in CI and rejects
backticked paths or symbols that don't exist.

### 4. Verify locally before pushing

```bash
python3 scripts/check_changelog_honesty.py    # honesty gate
python3 scripts/check_workflow_shapes.py      # workflow lint
git diff                                       # human review
```

If you touched any `.github/workflows/*.yml`, the workflow-shape lint
will catch the bare-mnc-redirect bug class statically.

### 5. Scan for stragglers (sanity only)

The script handles the canonical surfaces. If you want extra
paranoia, sweep for the old version in any other markdown:

```bash
grep -rEn "v?<old_version>" --include="*.md" \
  | grep -v "/.git/\|/.venv\|/node_modules\|/.tmp-llvm\|/\.reviews/\|/dist/\|/CHANGELOG\.md\|/docs/roadmap/" \
  | head -30
```

Ignore historical references (CHANGELOG entries for prior releases,
SESSION_REPORTs, git comparison URLs for old tags). Flag anything
else.

Do NOT commit. The user will commit when ready.
