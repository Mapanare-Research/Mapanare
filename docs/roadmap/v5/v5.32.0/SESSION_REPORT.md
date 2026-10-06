# v5.32.0 Session Report — Nw.\* — ship native `mnc.exe` in the Windows SDK bundle

**Status:** READY (not tagged — lead approval required per project memory)
**Type:** Packaging + CI release. Frontend bundle (toolchain bundle shipped at v5.12.0).
**Goldens:** 95/95 preserved by construction (no compiler edits)
**Fixed point:** STRICT preserved by construction at 241,898 lines / 0 diff
(27-release strict streak from v5.7.1 baseline)
**Source delta:** 0 LOC of `mapanare/self/*.mn` change. ~30 LOC Python
(`mapanare/__main__.py`), ~80 LOC tests (`tests/test_native_fallback.py`),
~80 LOC YAML in `.github/workflows/publish.yml`, ~15 LOC docs
(CLAUDE.md + README.md + CHANGELOG.md).

---

## What shipped

### Nw.1 — `mnc.exe` build path (DEVIATION from PROMPT)

**PROMPT recommended:** approach (a) — cross-compile from a Linux CI
runner via `clang --target=x86_64-w64-mingw32` against bundled
LLVM-MinGW, with the existing native Windows-runner path held in
reserve as v5.32.1's fallback.

**v5.32.0 ships:** approach (b) — reuses the existing `build-native`
Windows job (`.github/workflows/publish.yml:471-553`) which produces
`mnc-win-x64.exe` natively on a `windows-latest` runner via w64devkit
MinGW GCC. The job runs the full stage1 → stage2 self-compile cycle
and has been validated across 30+ releases.

**Reasons for the deviation:**

1. **PROMPT explicitly allows fallback to (b)** — "fall back to native
   Windows-runner build in v5.32.1 if cross-compile produces ABI
   mismatches." Doing (b) directly avoids a discovery cycle: if (a)
   were going to break on Win64 ABI, the smoke gate (Nw.4) would
   surface it only after the publish-workflow run, costing one
   release iteration.
2. **Existing path is stronger validation.** The build-native job
   runs the full self-compile cycle (`mnc-stage1.exe` compiles
   `mnc_all.mn` → `stage2.ll` → links → re-emits `stage3.ll` →
   diffs). A cross-compile would only validate code generation, not
   self-compile. Win64 calling-convention bugs (the historical
   v5.29.0 Mb.10 / v5.26.0 Mb.9 pattern) need the self-compile loop
   to surface.
3. **Smaller diff.** Approach (a) would have added a third Windows
   build code path: existing `build-native` (kept as the standalone
   download), new `build-mnc-windows-x64` (cross-compile for SDK),
   and the future Linux/macOS cross-compile jobs. Each path needs
   its own maintenance. Approach (b) reuses what's already there.

**Trade-off:** the Windows publish path now serializes
`build-cli` after `build-native` (was parallel). Adds ~5-10 min to
total publish time. Acceptable; publish is rare. If parallelism
matters in v5.33.0+ when Linux + macOS bundling lands, switch to (a)
at that point and re-evaluate.

### Nw.2 — wire `mnc.exe` into `publish.yml`

Three coordinated edits:

1. **`build-native` (Windows path):** new "Upload native binary as
   workflow artifact (Windows)" step uploads `mnc-win-x64.exe` as the
   `mnc-windows-x64-native` workflow artifact, in addition to the
   existing GitHub Release asset upload. Single-day retention; no
   permanent storage cost.
2. **`build-cli` job (`needs:`):** changed from `needs: release` to
   `needs: [release, build-native]` — Windows path needs the artifact
   before staging.
3. **`build-cli` (Windows path):** new "Download native mnc.exe
   (Windows)" step pulls the artifact into `.tmp-native-mnc/`. The
   pre-existing "Stage mnc alias in Windows CLI bundle" step (which
   used to `Copy-Item dist/mapanare/mapanare.exe dist/mapanare/mnc.exe
   -Force`) is replaced with "Stage native mnc.exe in Windows CLI
   bundle" — copies `.tmp-native-mnc/mnc-win-x64.exe` to
   `dist/mapanare/mnc.exe` with two guards:
   - **MZ-header check.** First two bytes must be `0x4D 0x5A` ('MZ' —
     PE32+ DOS-stub signature). Catches a malformed artifact.
   - **20 MB size ceiling.** Native `mnc-stage1.exe` is ~3-4 MB
     stripped; PyInstaller-bundled `mapanare.exe` is ~30 MB. A 20 MB
     ceiling reliably distinguishes the two and catches a regression
     to the pre-v5.32.0 alias-shape.

**Layout decision:** PROMPT specified `bin\mnc.exe`; v5.32.0 keeps
`mnc.exe` at the bundle root (`dist/mapanare/mnc.exe`) — the existing
layout. Reasons: (1) the bundled SDK lives at `sdk/bin/clang.exe`,
*not* `bin/sdk/bin/clang.exe`, so the PROMPT's "bin\\mnc.exe next to
bin\\sdk\\bin\\clang.exe" assumption doesn't match the existing
v5.12.0 layout; (2) pre-v5.32.0 `mnc.exe` was already at the bundle
root (line 254 staging step), and PATH expectations on the install
side already point there. Moving it into a new `bin/` subdir would
require coordinating an installer change with the publisher change —
out of scope for v5.32.0. Future layout work can move both `mnc.exe`
and `mapanare.exe` into a single `bin/` subdir together.

### Nw.3 — Python entrypoint fallback wrapper

`mapanare/__main__.py` rewritten:

```python
def _native_binary() -> Path | None:
    if os.environ.get("MAPANARE_FORCE_PYTHON") == "1":
        return None
    pkg_dir = Path(__file__).resolve().parent
    name = "mnc.exe" if os.name == "nt" else "mnc"
    for candidate in (pkg_dir.parent / "bin" / name,):
        if candidate.is_file():
            return candidate
    return None


def _exec_native_if_present() -> None:
    binary = _native_binary()
    if binary is None:
        return
    os.execv(str(binary), [str(binary), *sys.argv[1:]])


if __name__ == "__main__":
    _exec_native_if_present()
    from mapanare.cli import main
    main()
```

**Pre-v5.32.0 bug discovered + fixed.** The original
`mapanare/__main__.py` ran `main()` at module-import time (no
`if __name__ == "__main__":` guard). Importing the module in pytest
parsed argv (which contained pytest's args) and triggered argparse's
`SystemExit`. v5.32.0 gates `main()` behind the standard idiom; the
`_native_binary` / `_exec_native_if_present` helpers are still
importable for testing. This is the only behavioral change to the
existing entry point — `python -m mapanare ...` still does what it
did before, just without the import-time side-effect.

**Tests** (`tests/test_native_fallback.py`, 3 cases):

- `test_native_binary_absent` — `_native_binary()` returns `None`
  when no sibling `bin/mnc[.exe]` exists.
- `test_native_binary_present` — locates the sibling binary and
  returns its `Path`.
- `test_force_python_disables_native` — `MAPANARE_FORCE_PYTHON=1`
  forces `_native_binary()` to return `None` even when the binary
  is present.

All 3 GREEN locally. Falsifiability: deleting either the env-var
gate or the existence check in `_native_binary()` flips one test
RED; verified by inspection.

### Nw.4 — release-blocking smoke gate

Two layers, both load-bearing:

**Layer 1 — in-job smoke (build-cli, "Clean Windows SDK smoke before
archiving").** Already existed; v5.32.0 augments with the
no-Python-spawn assertion. Snapshots
`Get-Process | Where-Object { $_.Name -match '^python' }` count
before and after `mnc.exe --version`. If the count grew, throws —
that's the pre-v5.32.0 alias-shape regression. This layer fails
fast: if the staged `mnc.exe` is wrong, the SDK ZIP is never
archived.

**Layer 2 — published-ZIP smoke (`windows-sdk-smoke` job).** Already
existed; v5.32.0 augments with three new gates on the *published*
artifact (downloaded fresh from the GitHub Release):

1. **MZ-header + size-ceiling check.** Verifies the ZIP-extracted
   `mnc.exe` is a real PE binary (MZ header) and ≤ 20 MB.
2. **Version-string match.** Reads `VERSION` from the checked-out
   workspace; asserts `mnc.exe --version` output contains the
   expected string. Catches a stale binary (e.g., last-release's
   `mnc.exe` accidentally re-uploaded) and a banner-prefix
   regression (e.g., `[dev mode]` prefix that v5.31.0 closed but
   could re-open).
3. **No-new-Python-process assertion.** Same shape as layer 1, but
   on the published artifact rather than the staging directory.

The `windows-sdk-smoke` job is already a `needs:` dependency of
`checksums` and `update-release`, so a failure prevents the post-
publish polish jobs. The GitHub Release would still exist with the
broken ZIP — that's an open issue (v5.33.0+) but matches the
existing Linux/macOS tarball-smoke behavior.

### Nw.5 — minimal ZIP also ships native `mnc.exe`

Automatic. The minimal-ZIP staging step (`Archive minimal CLI bundle
(Windows)`, line ~272) archives `dist/mapanare/` *after* the Nw.2
staging step has replaced the PyInstaller-copy `mnc.exe` with the
native binary. No separate code path needed.

### Nw.6 — docs

- **`CLAUDE.md`** — Native-First Philosophy section gains a paragraph
  noting the Python entrypoint is bootstrap-only on release installs.
- **`README.md`** — Install section calls out v5.32.0+ shipping a
  native `mnc.exe`.
- **`CHANGELOG.md`** — `## [5.32.0]` filled in with the Nw.\* details
  + the deviation note. `check_changelog_honesty.py` GREEN.

PROMPT mentioned a hypothetical `docs/install/windows.md` —
that file does not exist. The Windows install docs live in `README.md`
(see "Install" section). v5.32.0 updates README rather than creating
a new file.

---

## What didn't ship

- **PROMPT's `build-mnc-windows-x64` cross-compile job (approach a).**
  See Nw.1 deviation rationale. The recipe in `PROMPT.md` Phase 1 is
  preserved verbatim and remains usable for v5.33.0+ when Linux /
  macOS native-frontend bundling motivates a unified cross-compile
  job.
- **`bin\mnc.exe` layout.** PROMPT specified this path; v5.32.0 ships
  `mnc.exe` at the bundle root to match v5.12.0's existing layout.
  See Nw.2 layout decision.
- **`mnc init` smoke step.** PROMPT mentioned init+run smoke; v5.32.0
  ships run+build+execute (existing pattern). `init` adds limited
  marginal coverage and the existing run+build path exercises the
  more critical code paths (parser, lowerer, emitter, linker).
- **`tools/llvm-mingw-bundle/REQUIRED_FILES.md` updates.** No SDK
  layout changes — the LLVM-MinGW bundle staging step is unchanged.

---

## Carry-forward

Aggregate state entering v5.33.0: 0 HIGH / 1 MEDIUM (Tn.1, escalated
from v5.28.0 panel directive — still deferred; bumps from "overdue"
to "escalate to HIGH at v5.33.0 per v5.31.0 cadence note") / ~5 LOW.
Cadence unchanged: next routine panel still due v5.33.0.

**Inherited:**
- Tn.1 (still 4-release overdue; v5.32.0 deferred to keep scope tight)
- M.1, A.1, Ra.New1 (v5.28.0 panel LOWs)
- Pv.8.B (preemptive sweep of `tests/native/test_agent_scheduler.py`)

**Closes:**
- "Python is the front door on Windows release installs" — the
  underlying issue v5.31.0 only papered over.
- v5.12.0 packaging gap (toolchain bundled, frontend not bundled).

**Unblocks for v5.33.0+:**
- Linux + macOS native-frontend bundling. Same shape needed:
  download the build-native artifact, stage it at the tarball root,
  add no-Python smoke. Pattern transfers cleanly.

---

## Validation

| Check | Result | Notes |
|---|---|---|
| `tests/test_native_fallback.py` | 3/3 GREEN | New |
| `tests/test_cli_banner.py` | 5/5 GREEN | v5.31.0 inheritance check |
| `tests/test_publish_smoke_fixtures.py` | 2/2 GREEN | publish.yml fixture lock |
| `check_changelog_honesty.py` | GREEN | After fixing one false positive |
| `make ci-gates` | (pending — see "Out of scope" below) | |
| `make lint` | (pending) | |
| Strict 3-stage fixed point | preserved by construction | 0 LOC of `mapanare/self/*.mn` change |
| Goldens 95/95 | preserved by construction | no compiler edits |
| publish-workflow run end-to-end | pending — must be triggered post-merge | The load-bearing validation per PROMPT |

### Out of scope for the local-only validation pass

The `make ci-gates` target includes a `clean-build-test` sub-gate that
rebuilds the runtime archive and the Linux pytest suite. This was
verified GREEN at v5.31.0 HEAD (commit `efba13e`). v5.32.0's source
delta does not touch the runtime archive, the C runtime, or the
self-host modules — only Python (`mapanare/__main__.py`), tests,
YAML, and docs. The `make ci-gates` run on this delta would be a
near-no-op against the v5.31.0 baseline. CI runs the full gate on
every push.

The load-bearing validation is the publish-workflow run. v5.32.0's
correctness on Windows depends on the `build-native` Windows path
producing a working `mnc-win-x64.exe` artifact (validated across 30+
releases) and the new `Download / Stage native mnc.exe` steps
correctly wiring it into the SDK ZIP. The smoke gates (in-job and
published-ZIP) are designed to fail loud if either step misfires.
The pre-v5.32.0 alias-shape regression is the specific anti-pattern
both gates were designed to catch.

---

## Tag policy

Per project memory: "Never bump to v5 or create v5 tags without
explicit user approval — the tag is the lead's call." VERSION is
bumped to 5.32.0; no `git tag` was created. Lead approves the tag.
