# Bump Version

Bump the project version across all files that reference it.

## Instructions

### 1. Parse arguments

The user provides the new version (e.g., `0.5.0`). If not provided, read the current version from `VERSION` and ask what the new version should be.

### 2. Read current state

```bash
cat VERSION
```

Store the old version for find-and-replace.

### 3. Update all version references

Update these files in order. Each step depends on the previous value being known.

#### a. `VERSION` file
Replace the old version string with the new one.

#### b. `CHANGELOG.md`
- Add a new `## [<new_version>] - <today's date YYYY-MM-DD>` section between `## [Unreleased]` and the previous version entry.
- Leave the section body as a placeholder for the user to fill in, with empty `### Added`, `### Changed`, and `### Fixed` subsections.
- Update the `[Unreleased]` comparison link at the bottom to compare from the new version tag.
- Add a new comparison link for the new version pointing from the old version tag.

#### c. `README.md`
- Find the version badge (`version-X.Y.Z`) and replace with the new version.

#### d. All localized READMEs (`docs/README.*.md`)
- Search every `docs/README.*.md` file for `version-<old_version>`.
- Replace any matches with `version-<new_version>`.
- Skip files that don't have a version badge — don't add one.

### 4. Scan for stragglers

Run a repo-wide search for the old version string to catch anything missed:

```bash
grep -r "<old_version>" --include="*.md" --include="*.py" --include="*.toml" --include="*.cfg" --include="*.json"
```

Ignore matches that are clearly historical (e.g., inside CHANGELOG entries for previous releases, git comparison URLs for old tags). Flag anything else to the user.

### 5. Summary

Print a short summary of what was updated:
- Files modified
- Old version -> New version
- Reminder to review the CHANGELOG section and fill in the actual changes

Do NOT commit. The user will commit when ready.
