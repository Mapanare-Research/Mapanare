# v5.31.0 — Bn.\* — banner hotfix; kill the "[dev mode]" lie

**Status:** PLANNING
**Type:** UX hotfix. Small, mechanical, ~50 LOC.
**Breaking:** No. Behavior change is purely in stderr output and
exit-path semantics for metadata-only commands.
**Prerequisite:** v5.30.0 shipped (packaging-only / version bump).
**Estimated effort:** 1 short session (~1–2h).

---

## Why this exists

A user installed Mapanare on Windows via the bundled SDK installer
and ran `mnc --version`. The output was:

```text
PS C:\Users\juanh> mnc --version
[dev mode] Using Python bootstrap compiler. For native speed: mnc run <file.mn>
mapanare 5.30.0
```

Three things are wrong with this:

1. **"[dev mode]" is a lie on a release install.** This was a
   shrink-wrapped SDK ZIP, not a dev clone. The user did nothing
   wrong. The banner makes the install look broken.
2. **"For native speed: mnc run <file.mn>" is incoherent.** The
   user just asked for the version string. They are not running a
   `.mn` file. The suggestion does not apply to `--version`,
   `--help`, `init`, or any metadata-only command.
3. **The banner fires unconditionally.** Look at
   `mapanare/cli.py:2329-2334`:
   ```python
   def main() -> None:
       print(
           "[dev mode] Using Python bootstrap compiler. "
           "For native speed: mnc run <file.mn>",
           file=sys.stderr,
       )
       parser = build_parser()
       args = parser.parse_args()
   ```
   It runs before argparse even sees the command. There is zero
   context-awareness.

This is purely a UX bug, not a compiler bug. The Python bootstrap
itself is fine — it just announces itself wrong.

> **Note:** v5.32.0 (next release) is the *real* fix — ship a native
> `mnc.exe` so Python is no longer the front door at all on release
> installs. v5.31.0 is the immediate hotfix that doesn't require any
> CI/publish-pipeline work; it can ship same-day.

---

## Goals

1. **Bn.1** — Suppress the banner entirely on metadata-only
   commands: `--version`, `--help`, `-h`, `init`, `list` (any
   command that doesn't compile or execute Mapanare code).
2. **Bn.2** — Detect "release install" vs "dev clone" by environment
   signal; suppress the banner unconditionally on release installs.
3. **Bn.3** — Reword the banner that *does* fire on dev-clone +
   compile/run commands so it doesn't tell the user to do something
   they're already doing or that doesn't apply.
4. **Bn.4** — Lock the new behavior with tests covering all four
   matrix cells: {dev clone, release install} × {metadata cmd,
   compile cmd}.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Bn.1** | MEDIUM (UX) | **Skip banner on metadata commands.** In `mapanare/cli.py::main`, parse argv first to detect `--version` / `--help` / `-h` / `init` / `list` and skip the banner for those. The simplest shape: peek at `sys.argv[1:]` *before* `parser.parse_args()`; if the first non-flag token is in a NO_BANNER set, don't print. Keep it boring — no clever introspection. | 15 min |
| **Bn.2** | MEDIUM (UX) | **Detect release install.** Check for an env var `MAPANARE_RELEASE=1` set by the installer/launcher script, OR check the install-path heuristic: if `__file__` resolves under a release-install path (no adjacent `pyproject.toml` + `.git` directory at the repo root), it's a release install — suppress the banner. Use env var as the primary signal, path heuristic as fallback. The Windows SDK installer at `bin/sdk/bin/clang.exe` already wraps the Python entry; have the wrapper set `MAPANARE_RELEASE=1` before exec. | 30 min |
| **Bn.3** | LOW | **Reword the dev-clone banner.** Replace the current line with something honest: `"[mapanare dev] running from source clone (mapanare/cli.py). Add `MAPANARE_RELEASE=1` or install via the SDK to silence."` Drop the "for native speed: mnc run <file.mn>" suggestion — that's misleading on its own and doubly so on metadata commands. The banner's only job is to remind a *developer* they're hitting their checkout, not the installed copy. | 10 min |
| **Bn.4** | LOW | **Tests in `tests/test_cli_banner.py`** (new). Four cases: (a) `--version` on release install → no banner on stderr; (b) `--version` on dev clone → no banner on stderr (Bn.1 wins over Bn.2); (c) `run hello.mn` on release install → no banner; (d) `run hello.mn` on dev clone → banner fires with new wording. Use `subprocess.run` to invoke the CLI; stub `MAPANARE_RELEASE` via env. | 30 min |
| **Bn.5** | LOW | **Update Windows SDK installer launcher.** Whatever script wraps `python -m mapanare` on the SDK install (PowerShell shim or `.bat`) sets `MAPANARE_RELEASE=1` in the environment before exec. Find via grep for `mnc.exe` / `mapanare.exe` in `installer/` or `scripts/win/`. If no wrapper exists, this is a no-op for now and the path-heuristic fallback in Bn.2 handles it. | 15 min |

**Total source delta:** ~50–80 LOC across 2-3 files (`cli.py`,
new `test_cli_banner.py`, optional installer launcher tweak).

---

## Phase plan

- **Phase 0** — Pre-flight: confirm v5.30.0 HEAD is clean (goldens
  95/95; STRICT 0 diff; ci-gates GREEN).
- **Phase 1** — Bn.1 + Bn.3 in `cli.py::main`. Inline.
- **Phase 2** — Bn.2 release-install detection. Adds a small helper
  `_is_release_install()`.
- **Phase 3** — Bn.4 tests. Lock all four matrix cells.
- **Phase 4** — Bn.5 installer launcher. Optional; ship without
  if launcher is non-trivial to locate.
- **Phase 5** — Bump version + CHANGELOG + release notes.

---

## Out of scope

- **Native `mnc.exe` shipping.** That's v5.32.0. The banner fix is
  decoupled — even after v5.32.0 ships, dev-clone users still see
  the Python path, so the rewording is durable.
- **Removing the Python bootstrap entirely.** Never; bootstrap from
  source needs Python at least once.
- **Tn.1** (95-golden link-and-run gate; 2-release overdue per
  v5.28.0 panel) — carry forward to v5.32.0+.
- **M.1, A.1, Ra.New1, Pv.8.B** — carry forward.

---

## Risk

1. **Argv parsing before argparse.** Bn.1 peeks at `sys.argv[1:]`
   before argparse runs. Risk: a flag like `--no-banner` or a
   not-yet-added subcommand misclassifies. Mitigation: keep the
   NO_BANNER set tight (literal string match for `--version`,
   `--help`, `-h`, `init`, `list`); fall through to "show banner"
   on anything else (safe default — the banner is annoying but not
   wrong on dev clones).
2. **Path heuristic false-positives.** Bn.2 fallback path check
   could miss edge installs (e.g., user pip-installs from git
   directly). Mitigation: env var is the primary signal; path
   check is a backup. The env var is set by the SDK installer
   exactly to avoid this.
3. **Installer launcher unreachable.** Bn.5 may require touching
   InnoSetup / NSIS / PyInstaller spec files. If the launcher
   isn't trivially modifiable, ship Bn.1+Bn.2+Bn.3+Bn.4 only;
   path heuristic carries the load until Bn.5 lands in v5.31.1.

---

## Success criteria

- ✅ `mnc --version` on a fresh Windows SDK install prints **only**
  the version string. No banner.
- ✅ `mnc --help` on a fresh install prints help. No banner.
- ✅ `mnc run hello.mn` on a fresh install runs the program. No banner
  (release install).
- ✅ `python -m mapanare --version` on a dev clone — no banner
  (Bn.1 metadata-command skip).
- ✅ `python -m mapanare run hello.mn` on a dev clone — new banner
  fires with the reworded text.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.
- ✅ `make ci-gates` GREEN; `make lint` clean.

---

## Carry-forward delta

**Closes:**
- Banner-misfires-on-release-installs UX bug.

**Inherits to v5.32.0:**
- Tn.1 (still overdue; should ship at v5.32.0 if scope permits, or
  escalated to HIGH if it slips again).
- The *real* "Python is the front door on release installs"
  problem — banner fix is cosmetic; v5.32.0 fixes the underlying
  shape by shipping a native binary.

**Aggregate state entering v5.32.0:** 0 HIGH / 1 MEDIUM (Tn.1 still
overdue; bumped from "overdue" toward "escalate to HIGH at v5.33.0
if not landed") / ~5 LOW.
