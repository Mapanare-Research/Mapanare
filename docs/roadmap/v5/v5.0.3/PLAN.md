# Mapanare v5.0.3 — "macOS x86_64"

> **Ship `mnc-darwin-x64` alongside the ARM64 binary.** The v5.0.0
> release shipped `mnc-darwin-arm64` but no x86_64 asset — Intel Mac
> users (still ~30% of developers at time of writing) fall back to
> the Python bootstrap bundle. This release closes that gap.

**Status:** PLANNED (skeleton)
**Breaking:** No
**Prerequisite:** v5.0.2 shipped
**Estimated work:** 1 session (~1 hour) — GitHub Actions' macOS-13
runners are x86_64, so cross-compile concerns evaporate

---

## Why this release exists

The v5.0.0 release ships:

| Asset | Platform | Present? |
|---|---|---|
| `mnc-linux-x64` | Linux x86_64 | ✅ |
| `mnc-darwin-arm64` | macOS Apple Silicon | ✅ |
| `mnc-win-x64.exe` | Windows x86_64 | ✅ (v5.0.1) |
| `mnc-darwin-x64` | macOS Intel | ❌ |

The `macos-latest` runner on GitHub Actions moved to ARM64 in late
2024. To build x86_64, we need `macos-13` (the last Intel runner)
which GitHub still provides through at least 2026.

## Scope

**In scope:**
- Add `macos-13` entry to `build-native` matrix with
  `artifact: mnc-darwin-x64` and `triple: x86_64-apple-darwin`
- `scripts/build_stage1.py` already detects `sys.platform == 'darwin'`
  and uses the correct datalayout for ARM64. For x86_64 we keep the
  Linux-derived `target datalayout` already emitted by the bootstrap
  (the committed `main.ll` uses the SysV x86_64 layout) — no
  substitution needed.
- Update release body table to list the new binary
- Smoke test (`--version` + trivial compile)

**Out of scope:**
- Universal2 binaries (fat binaries) — separate tooling (`lipo`)
- macOS notarization / codesigning (v5.x ecosystem scope)
- Homebrew formula (separate release)

## Exit criteria

- `mnc-darwin-x64` exists on the v5.0.3 GitHub Release
- macOS Intel user runs `chmod +x mnc-darwin-x64 && ./mnc-darwin-x64
  --version` → prints `mapanare 5.0.3`
- The release table has four rows in the "Native Compiler" column,
  no `—`

## Risks

**Risk 1 — `macos-13` is slower / pricier than `macos-latest`.**
*Mitigation:* the job runs in parallel with Linux and Windows, no
critical-path impact. Budget under 10 minutes total.

**Risk 2 — Apple Silicon users run x86_64 binary via Rosetta.**
Possible but user-driven — they have an ARM64 binary too. Not a
v5.0.3 concern.
