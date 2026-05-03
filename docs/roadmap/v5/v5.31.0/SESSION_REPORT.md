# v5.31.0 Session Report — Bn.\* — banner hotfix

**Date:** 2026-05-03
**Type:** UX hotfix (no compiler / runtime / `mapanare/self/*.mn`
edits).
**Prerequisite:** v5.30.0 shipped (packaging-only bump).
**Effort:** ~1.5 hours actual (within PLAN's 1–2h estimate).

---

## TL;DR

Killed the "[dev mode]" lie that fired unconditionally on every CLI
invocation regardless of subcommand or install context. v5.30.0
publish-run-#50-shaped user report (a fresh Windows SDK install ran
`mnc --version` and got the dev-mode banner before the version
string) is now structurally impossible.

- **Bn.1 + Bn.3** — argv-peek skip on metadata commands
  (`--version`, `--help`, `-h`, `init`, `list`); banner reworded to
  honestly describe the dev-clone path; misleading "for native
  speed: mnc run <file.mn>" suggestion removed.
- **Bn.2** — `_is_release_install()` helper with `MAPANARE_RELEASE=1`
  env var (primary) + path heuristic (fallback: dev clones have
  `pyproject.toml` + `.git` at the repo root; release installs do
  not).
- **Bn.4** — 5 cases in new `tests/test_cli_banner.py` lock all
  four matrix cells plus the new wording.
- **Bn.5** — `packaging/pyinstaller-entry.py` sets
  `MAPANARE_RELEASE=1` before importing `mapanare.cli`. Single
  edit covers Linux tarball, macOS bundle, and Windows SDK ZIP
  — all PyInstaller bundles inherit the env var.

**Source delta:** ~70 LOC across 3 files, well under PLAN's
50–80 LOC target. Goldens **95/95**. **STRICT 3-stage fixed point
preserved by construction at 241,898 lines / 0 diff** (26-release
strict streak from the v5.7.1 baseline).

---

## Aggregate state entering v5.32.0

- **0 HIGH**.
- **1 MEDIUM** — Tn.1 (95-golden link-and-run gate; 3-release
  overdue per v5.28.0 panel rec; bumped from "overdue" toward
  "escalate to HIGH at v5.33.0 if not landed"; deliberately
  deferred to keep v5.31.0 scope tight).
- **~5 LOW** — Pv.8.B preemptive sweep, M.1 / A.1 / Ra.New1
  panel recs, Bn.5-on-`.bat`/`.ps1`-shim follow-up if a
  non-PyInstaller release path is ever added.

**Cadence unchanged:** next routine panel still due v5.33.0.

---

## What changed

### Bn.1 — skip-banner-on-metadata-commands

`mapanare/cli.py::main` used to call `print(...)` unconditionally
before argparse ran. New `_should_show_dev_banner(argv)` helper
peeks at `sys.argv[1:]`:

- If `_is_release_install()` returns True → no banner (Bn.2).
- Walk argv looking for the first non-flag token. If it's in
  `NO_BANNER_COMMANDS = frozenset({"--version", "--help", "-h",
  "init", "list"})` → no banner.
- If the first non-flag token is a compile/run subcommand
  (anything not in `NO_BANNER_COMMANDS`) → banner fires.
- Argv has no non-flag tokens (likely `--help` with no args
  or empty `mnc` invocation) → no banner; argparse will print
  help anyway.

Honest-default policy: when in doubt, *don't* fire the banner.
The user can always run `MAPANARE_RELEASE=1` to silence in any
edge case the heuristic misses.

### Bn.2 — release-install detection

```python
@lru_cache(maxsize=1)
def _is_release_install() -> bool:
    if os.environ.get("MAPANARE_RELEASE") == "1":
        return True
    pkg_dir = Path(__file__).resolve().parent
    repo_root_candidate = pkg_dir.parent
    return not (
        (repo_root_candidate / "pyproject.toml").exists()
        and (repo_root_candidate / ".git").is_dir()
    )
```

`lru_cache(1)` because this is called on every CLI invocation
and the answer never changes mid-process. Cached *within* a
process, not across them; no persistent state.

### Bn.3 — reword the dev-clone banner

Before:

```text
[dev mode] Using Python bootstrap compiler. For native speed: mnc run <file.mn>
```

Three things wrong with the old text: "[dev mode]" is a lie on
release installs; "For native speed: mnc run <file.mn>" is
incoherent on metadata commands; the suggestion is meaningless
to a user who just typed `mnc --version`.

After (new, fires only on dev-clone + compile-or-run command):

```text
[mapanare dev] running from source clone (.../mapanare/cli.py). Set MAPANARE_RELEASE=1 or install via the SDK to silence.
```

Honest description of the actual situation. Tells the user how
to silence it. Path embedded so a developer with multiple
checkouts can tell which one they're hitting.

### Bn.4 — `tests/test_cli_banner.py`

5 cases via `subprocess.run(... [sys.executable, "-m", "mapanare",
*argv] ...)`:

1. `--version` on release install (`MAPANARE_RELEASE=1`) → no
   banner; version printed.
2. `--version` on dev clone (env var unset) → no banner (Bn.1
   wins over Bn.2).
3. `--help` on release install → no banner.
4. `check h.mn` on release install → no banner.
5. `check h.mn` on dev clone → banner fires with "running from
   source clone" wording.

Case 4 uses `check` instead of `run` (PLAN-suggested) because
`check` exercises the full CLI dispatch but doesn't require a
working compiler/linker chain in the test environment. Banner
firing is dispatched by `_should_show_dev_banner` *before*
argparse runs, so any subcommand suffices.

**Falsifiability** (verified at end of Phase 3): direct API
assertion via `from mapanare.cli import _should_show_dev_banner`
confirms (a) `--version` skips banner with no env var, (b)
`check foo.mn` fires banner with no env var, (c) `check foo.mn`
skips banner with `MAPANARE_RELEASE=1` (after `lru_cache.clear()`).
All three assertions pass with the v5.31.0 fix; flipping the
return value of `_is_release_install` in-process flips assertion
(c).

### Bn.5 — installer launcher

The Windows SDK ZIP and Linux/macOS release tarballs all ship
PyInstaller-bundled binaries built from
`packaging/pyinstaller-entry.py` per
`packaging/mapanare.spec`. Setting `MAPANARE_RELEASE=1` at the
top of `pyinstaller-entry.py::main()` (before importing
`mapanare.cli`) covers every release platform in one edit.

```python
def main():
    os.environ.setdefault("MAPANARE_RELEASE", "1")
    from mapanare.cli import main as cli_main
    cli_main()
```

Used `setdefault` so a user who explicitly unsets
`MAPANARE_RELEASE` (e.g. for testing) can still trigger the
path-heuristic fallback if they want to. The path heuristic
(also in Bn.2) handles the case where someone unpacks the SDK
ZIP and runs the bundled `mapanare` binary in a way that bypasses
the entry point — there's no `pyproject.toml` next to a bundled
binary either, so the heuristic still fires.

**Bash shim** (`packaging/mapanare-shim.sh`) — `exec`s the bundled
binary directly; the env var set inside the entry point is the
process's own env, which it inherits from the shim regardless.
No shim edits required.

---

## Verification

### CI gates (9 sub-gates)

```text
=== All gates GREEN ===
```

Sub-gates passed: silent_skips, changelog_honesty, workflow_shapes,
docs_drift, hollow_features, struct_registry, doc_freshness,
cadence (3 minor versions since v5.28.0; next panel at v5.33.0),
clean-build-test (6 passed in 4.60s).

### Lint

```text
ruff check . && black --check . && mypy mapanare/ runtime/
All checks passed!
408 files would be left unchanged.
Success: no issues found in 56 source files
```

### Goldens

```text
All 95 tests passed in 19.3s
```

### Fixed point (after `python3 scripts/build_stage1.py` rebuild)

```text
[Verify] Fixed point: diff stage2.ll stage3.ll
  ✓ FIXED POINT REACHED
  stage2.ll == stage3.ll (241898 lines, 0 diff)

=== La Culebra Se Muerde La Cola ===
```

Note: first `verify_fixed_point.sh` run after the v5.30.0 → v5.31.0
bump showed a 4-line diff in the VERSION metadata
(`!0 = !{!"5.30.0"}` vs `!0 = !{!"5.31.0"}`) because the cached
`mnc-stage1` binary was built before the bump. Rebuilding stage1
via `python3 scripts/build_stage1.py` (~30s) resolved this and
restored STRICT. Worth flagging for future bump-only releases:
**always rebuild stage1 after `bump_version.py` and before
`verify_fixed_point.sh`** to avoid a spurious "NEAR" report.

### Banner tests

```text
tests/test_cli_banner.py::test_version_release_install_no_banner PASSED
tests/test_cli_banner.py::test_version_dev_clone_no_banner_on_metadata PASSED
tests/test_cli_banner.py::test_help_release_install_no_banner PASSED
tests/test_cli_banner.py::test_run_release_install_no_banner PASSED
tests/test_cli_banner.py::test_run_dev_clone_does_show_banner PASSED
============================== 5 passed in 5.65s ===============================
```

### Manual smoke

```text
$ python3 -m mapanare --version
mapanare 5.31.0
(no banner on stderr)

$ python3 -m mapanare check /tmp/h.mn
[mapanare dev] running from source clone (/mnt/c/.../mapanare/cli.py). Set MAPANARE_RELEASE=1 or install via the SDK to silence.
check: /tmp/h.mn OK

$ MAPANARE_RELEASE=1 python3 -m mapanare check /tmp/h.mn
check: /tmp/h.mn OK
(no banner on stderr)
```

---

## Source delta

| File | LOC delta | Role |
|---|---:|---|
| `mapanare/cli.py` | +37 / −5 (net +32) | New helpers + main() rewire |
| `tests/test_cli_banner.py` | +75 (new file) | Bn.4 matrix lock |
| `packaging/pyinstaller-entry.py` | +9 / −1 (net +8) | Bn.5 env var set |
| `CHANGELOG.md` | +50 (5.31.0 entry) | Release notes |
| `CLAUDE.md` | +90 (release-notes entry) | Roadmap state |
| `VERSION`, 4× README badges | bump | Vb.1 |
| `docs/roadmap/v5/v5.31.0/SESSION_REPORT.md` | +250 (this file) | Session doc |

**Total source delta:** ~115 LOC of behavior change (cli.py +
new test file + pyinstaller-entry); +140 LOC of docs/release
notes.

---

## Out of scope

- **Native `mnc.exe` shipping.** v5.32.0. The banner fix is
  decoupled — even after v5.32.0 ships, dev-clone users still
  see the Python path, so the new wording is durable.
- **Tn.1** (95-golden link-and-run gate; 3-release overdue per
  v5.28.0 panel rec) — carried forward to v5.32.0+.
- **M.1, A.1, Ra.New1, Pv.8.B** — carried forward.
- **Removing the Python bootstrap entirely.** Never; bootstrap
  from source needs Python at least once.

---

## Lessons (for future bump-only / hotfix releases)

1. **Rebuild stage1 between `bump_version.py` and
   `verify_fixed_point.sh`.** The cached binary embeds the
   pre-bump VERSION string in IR metadata; stage2 (built from
   current source) embeds the post-bump VERSION; the `diff`
   shows a 4-line VERSION-placeholder delta even though the
   actual code is byte-identical. PLAN should call this out
   explicitly for any release that runs `bump_version.py`.

2. **`_should_show_dev_banner` argv-peek is intentionally
   primitive.** Don't reach for argparse pre-parse or any
   clever introspection — keep the rule simple and the
   `NO_BANNER_COMMANDS` set explicit, and document the rule
   in `cli.py` near the constant for the next person who adds
   a metadata subcommand.

3. **Test the four matrix cells, not just the user-reported
   one.** v5.30.0 publish-run-#50 was specifically "release
   install + metadata cmd"; the test file locks all four cells
   so a future regression that only affects "dev clone +
   compile cmd" doesn't slip past.

---

## Tag policy

**Not tagged.** Per project memory: `git tag` waits for explicit
user approval. Lead's call.
