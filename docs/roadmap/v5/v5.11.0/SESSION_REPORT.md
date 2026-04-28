# v5.11.0 — Pk.* — Packaging hygiene + post-bundle cleanup

**Released:** 2026-04-28
**Branch:** `dev`
**Scope:** packaging-only. Zero compiler internals.

---

## What shipped

### Pk.1 — Versioned release-artifact filenames

Every artifact produced by `.github/workflows/publish.yml` now
carries the version in its filename:

| Old (legacy alias kept) | New (canonical) |
|---|---|
| `mapanare-linux-x64.tar.gz` | `mapanare-5.11.0-linux-x64.tar.gz` |
| `mapanare-mac-arm64.tar.gz` | `mapanare-5.11.0-mac-arm64.tar.gz` |
| `mapanare-win-x64.zip` | `mapanare-5.11.0-win-x64.zip` |
| `mapanare-win-x64-minimal.zip` | `mapanare-5.11.0-win-x64-minimal.zip` |
| `mnc-linux-x64` | `mnc-5.11.0-linux-x64` |
| `mnc-darwin-arm64` | `mnc-5.11.0-darwin-arm64` |
| `mnc-win-x64.exe` | `mnc-5.11.0-win-x64.exe` |

Per PLAN Decision 3 the version segment carries no leading `v`
(matches `cat VERSION` output). Per PLAN Decision 2 the separator
is dashed (`-5.11.0-`) not dotted (matches Linux release-tarball
convention; survives shell glob expansion better).

**Implementation.** Each archive/upload step in `build-cli` and
`build-native` computes the versioned name by injecting `-${V}-`
after the prefix (`mapanare-` or `mnc-`) and uploads BOTH names
to the GitHub release with `--clobber`. The legacy unversioned
name is a copy of the versioned file, so any download URL keeps
resolving (per PLAN Decision 1 — 2-release soak window; drop the
legacy alias in v5.13.0).

The `windows-bundled-llvm-smoke` job downloads the **versioned**
ZIP (`mapanare-${V}-win-x64.zip`) so a missing-versioned-asset
upload failure trips the smoke gate before `checksums` and
`update-release` run. If we'd kept the smoke job on the legacy
name the alias upload would have papered over a real bug in the
versioned-upload path.

`packaging/install.ps1` and `packaging/install.sh` compute the
versioned name from the resolved version (with the leading `v`
stripped) and probe it via HEAD before download, falling back to
the legacy unversioned name on 404. This handles two scenarios:

1. **Installing v5.11.0+** — versioned name resolves on first
   probe; legacy fallback unused.
2. **Installing v5.10.0 from a v5.11.0 install script** —
   versioned name 404s (v5.10.0 didn't produce a versioned
   artifact); legacy fallback succeeds. Critical: the install
   script lives at `https://mapanare.dev/install.ps1` so old
   blog-post one-liners always pull the latest install logic, not
   the install logic that shipped alongside the version they're
   asking for.

The release-notes table in the GitHub Release body also points at
the versioned URLs (so the canonical user-facing surface advertises
the new naming).

### Pk.2 — Drop the v5.9.1 implicit-run deprecation note

Single-line deletion at `mapanare/self/main.mn:1127`. Pre-this-
release, `mnc <file.mn>` printed a one-line stderr hint:

```
note: 'mnc <file.mn>' now runs the program; use 'mnc emit-llvm' for IR output
```

The v5.9.1 PLAN scheduled removal at v5.11.0; v5.10.0 carried the
note as the second release of the soak window. It now prints
nothing — the implicit-run dispatch is no longer "deprecated" (no
new behavior is replacing it; it IS the canonical behavior).

`tests/test_cli_default.py::test_default_prints_deprecation_note`
inverted to `test_default_silent_after_v5_11_0`, asserting the
stderr does NOT contain "now runs the program" or "implicit
'run'". The other 5 tests in that file unchanged.

`mapanare/self/mnc_all.mn` regenerated via `bash
scripts/concat_self.sh` after the main.mn edit (the verify_fixed_
point script reads the concat file, not the individual modules).

### Pk.3 — PyInstaller→native bundle swap (evaluate-only; deferred)

Compared `python -m mapanare --help` (25 subcommands) against
`./mapanare/self/mnc-stage1 --help` (7 visible subcommands +
default-dispatch). Native `mnc` is missing 18 subcommands. The
high-priority gaps (`lsp`, `fmt`, `init`, `check`, `lint`) make a
swap impossible today without a visible developer-experience
regression — `mnc init myproject` is the literal first line in
install.ps1's getting-started hint, `lsp` is what every editor
plugin shells out to, and the WASM CI lane uses
`python -m mapanare emit-wasm`.

**Decision: defer.** Open the **Mc.\* (mnc parity)** docket for
v5.12.x with priority order Mc.1 `mnc lsp`, Mc.2 `mnc fmt`,
Mc.3 `mnc init`, Mc.4 `mnc check`, Mc.5 `mnc emit-wasm`.
Re-evaluate the swap once Mc.1–Mc.5 close. Lower-priority
gaps (`bind`, `doc`, registry commands, `deploy`, `migrate`)
can stay in a Python sidecar without blocking.

Also: the savings from the swap are smaller than they appear. The
v5.10.0 95 MB ZIP is dominated by clang.exe + LLVM-C.dll (~85 MB),
not by the PyInstaller bundle (~10 MB). A native swap saves ~7 MB
at most. Users who want a small footprint already have
`MAPANARE_NO_BUNDLED_LLVM=1` → `mapanare-${V}-win-x64-minimal.zip`
at ~10 MB. The cost-benefit math doesn't justify a regression.

Full audit: `docs/roadmap/v5/v5.11.0/MNC_PARITY_GAPS.md`.

### Pk.4 — macOS / Linux LLVM bundling (closeout-doc)

**Decision: stay deferred.** Pre-decided in the v5.10.0 session
conversation; v5.11.0's task was just the closeout. Three reasons
hold:

1. **macOS** — every `xcode-select --install` user has clang at
   `/usr/bin/clang`; every Homebrew user has
   `/opt/homebrew/bin/clang`. Bundling our own clang would either
   conflict with the user's existing toolchain (causing
   "wrong clang version" reports when their IDE diverges) or
   require version-pinning the bundled copy, which is a maintenance
   tax for zero user gain.
2. **Linux** — bundled clang's libstdc++/libc dependencies create
   a portability nightmare. A binary built against glibc 2.35 won't
   run on a glibc 2.31 distro. Static LLVM with bundled libstdc++
   inflates the tarball to ~300 MB (vs Windows' 95 MB target).
3. **No demand signal** has emerged from v5.10.0. Re-open if it
   does — the bundle infrastructure built for v5.10.0 (extract_
   minimal.ps1, the actions/cache step, the windows-bundled-llvm-
   smoke job) ports to other platforms with mostly local edits.

Tracked in `docs/known_issues.md` Packaging table as Pk.4
"closed by anticipation" — open issue with a clear
re-evaluation trigger, not a permanent dead branch.

---

## What did NOT ship

- **PyInstaller→native bundle swap.** Pk.3 is evaluate-only. The
  decision goes to v5.12.0+ as the Mc.\* docket; v5.11.0 ships the
  `mnc-${V}-` versioned native binaries that a swap would later
  promote, but the bundle layout itself is unchanged.
- **macOS / Linux LLVM bundling.** Pk.4 is closeout-doc only.
- **Compiler / parser / semantic / MIR / lower / emitter changes.**
  Zero. v5.11.0 is packaging hygiene + a one-line deprecation
  removal in the dispatch layer.
- **LLVM 19 bundle.** v5.10.0 PLAN Decision 1 set an annual cadence
  after the new LLVM stable lands. v5.11.0 stays on 18.1.8.
- **Bb.4 seed refresh.** Zero new C-runtime exports — first release
  in 5+ to skip Bb.\*. The v5.10.0 seed at
  `bootstrap/seed/linux-x86_64/mnc` resolves all referenced symbols
  through the v5.11.0 build.

---

## Validation

```text
python3 scripts/build_stage1.py            -> Success (mnc-stage1, 6.6 MB stripped)
python3 scripts/test_native.py             -> All 66 tests passed in 13.1s
bash scripts/verify_fixed_point.sh         -> STRICT (0 diff, the v5.9.0 milestone preserved)
bash scripts/build_from_seed.sh            -> Success (existing v5.10.0 seed, no Bb.4 refresh)
python3 scripts/check_changelog_honesty.py -> clean
make lint                                  -> clean
python3 yaml.safe_load publish.yml         -> OK
bash -n install.sh                         -> OK
```

`tests/self_hosted/`: 287 passed, 2 xfailed (the v5.10.0-documented
IR bugs).

---

## Risk register (post-release)

| ID | Risk | Status |
|---|---|---|
| Pk.R1 | Existing install scripts in user docs / blog posts hardcoded `mapanare-win-x64.zip` (legacy unversioned). | **Mitigated.** 2-release legacy alias window per PLAN Decision 1. install.ps1 + install.sh probe versioned first, fall back to legacy. Drop the alias in v5.13.0. |
| Pk.R2 | Version-string interpolation differs between PowerShell tag (`v5.11.0`) and VERSION file (`5.11.0`). install.ps1 must strip leading `v` consistently. | **Mitigated.** Both install.ps1 and install.sh strip `^v` before constructing the versioned filename. Tested in Phase 5 syntax check. |
| Pk.R3 | Pk.3 evaluation reveals `mnc` is missing critical surface; pressure to delay v5.11.0 release while fixing those gaps. | **N/A.** Pk.3 is evaluate-only. The decision (defer the swap) is doc-only. |
| Pk.R4 (new) | The smoke-job switch to versioned-only download could fail if a previous-step environment-variable mishandling drops the version segment. | **Mitigated.** Smoke job uses literal `${{ needs.release.outputs.new_version }}` (the same value that drove the upload step). Failure modes are paired: if upload fails, smoke fails too — no asymmetric blind spot. |

---

## Cross-references

- v5.11.0 PLAN — `docs/roadmap/v5/v5.11.0/PLAN.md`
- v5.11.0 Pk.3 audit — `docs/roadmap/v5/v5.11.0/MNC_PARITY_GAPS.md`
- v5.10.0 SESSION — `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md`
  (bundle layout, the Pk.4 deferral conversation)
- v5.9.1 SESSION — `docs/roadmap/v5/v5.9.1/SESSION_REPORT.md`
  (the soak-window cadence Pk.2 honors)
- v5.9.0 SESSION — `docs/roadmap/v5/v5.9.0/SESSION_REPORT.md`
  (DX.\* docket — the closure arc Pk.\* paid forward)

---

## Estimated vs actual effort

| Phase | Estimated | Actual |
|---|---|---|
| Phase 1 (Pk.1) | 2-3h | within range |
| Phase 2 (Pk.2) | 0.5h | within range |
| Phase 3 (Pk.3) | 1-2h | within range |
| Phase 4 (Pk.4) | 0.5h | within range |
| Phase 5 (validate + release) | 1-2h | within range |
| **Total** | **5-9h** | within range, single session |
