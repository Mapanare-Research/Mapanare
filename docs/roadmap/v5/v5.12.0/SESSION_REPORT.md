# v5.12.0 - Mc.6 / Wk.* - Windows SDK split

**Date:** 2026-04-28
**Scope:** Windows packaging/toolchain discovery only. No compiler
internals, parser, semantic, MIR, lowerer, or emitter changes.

---

## Summary

Closed the v5.11.2 double-toolchain packaging regression without
returning to clean-Windows "missing compiler" behavior:

- The default Windows artifact is now the SDK ZIP:
  `mapanare-${V}-win-x64-sdk.zip`.
- The compatibility full ZIPs `mapanare-${V}-win-x64.zip` and
  `mapanare-win-x64.zip` are aliases to the SDK ZIP.
- The minimal ZIP is archived before any SDK is staged and must not
  contain `toolchain/`, `sdk/`, or `llvm/`.
- No v5.12.0 Windows release ZIP may contain `toolchain/`.

## Before / after asset model

Before, from the live v5.11.2 release:

| Artifact | Size |
|---|---:|
| `mapanare-5.11.2-win-x64-minimal.zip` | 162.0 MB |
| `mapanare-5.11.2-win-x64.zip` | 255.2 MB |
| `mapanare-5.11.2-linux-x64.tar.gz` | 11.9 MB |
| `mapanare-5.11.2-mac-arm64.tar.gz` | 11.6 MB |

After, v5.12.0 CI produces:

| Artifact | Meaning | Gate |
|---|---|---:|
| `mapanare-${V}-win-x64-minimal.zip` | App-only CLI, no compiler SDK | fail above 40 MB, target below 25 MB |
| `mapanare-${V}-win-x64-sdk.zip` | CLI plus one LLVM-MinGW/UCRT SDK | fail above 180 MB, warn above 150 MB |
| `mapanare-${V}-win-x64.zip` | Compatibility alias to SDK ZIP | same as SDK |

No local release ZIP was built in this session, so final post-compress
Windows asset sizes remain a CI/release output. The SDK extractor
locally staged the curated SDK subset at 316.4 MB uncompressed.

## SDK decision

Pinned SDK source:

- Project: Martin Storsjo LLVM-MinGW
- Release: `20260421`
- Asset: `llvm-mingw-20260421-ucrt-x86_64.zip`
- LLVM version: `22.1.4`
- Target: UCRT x86_64
- License: LLVM Apache 2.0 with LLVM Exception plus MinGW-w64 and
  winpthreads upstream runtime/import-library licenses

Why Python's 40 MB Windows installer is not the SDK target:

- Python ships a runtime/interpreter. Running Python scripts does not
  require C headers, startup objects, import libraries, CRT libraries,
  or a linker.
- Mapanare's `run` and `build` commands produce native binaries.
  Clean Windows therefore needs either a bundled compiler SDK or an
  on-demand SDK installer. v5.12.0 keeps the bundled default.

## Implementation

Toolchain discovery:

- `mapanare/toolchain.py` now probes bundled SDK paths before PATH:
  `sdk/bin`, `llvm/bin`, then legacy `toolchain/bin`.
- Bundled SDK probes prefer clang and do not require `gcc.exe`.
- Legacy `toolchain/bin/gcc.exe` remains supported as a fallback.
- `bin_dir` is set for bundled compilers so clang can find adjacent
  wrappers, linker, and DLLs.
- Bundled runtime archive discovery covers
  `sdk/lib/mapanare/libmapanare_rt.a`.

Packaging:

- `packaging/mapanare.spec` no longer auto-captures `repo/toolchain/`.
- `.github/workflows/publish.yml` archives minimal before SDK staging.
- The Windows SDK is staged under `dist/mapanare/sdk/`.
- `libmapanare_rt.a` is built with the same SDK that ships in the ZIP.
- `mnc.exe` is copied into the PyInstaller bundle before archiving.
- `windows-sdk-smoke` downloads `mapanare-${V}-win-x64-sdk.zip`, strips
  PATH/LIB/INCLUDE/CC/CXX, and runs `--version`, `run`, `build`,
  built-exe execution, and `test`.

Installer/docs:

- `install.ps1` and `mapanare-up.ps1` default to the SDK artifact.
- `MAPANARE_NO_BUNDLED_TOOLCHAIN=1` selects minimal.
- `MAPANARE_NO_BUNDLED_LLVM=1` remains a compatibility alias.
- README wording now says "Windows SDK" and removes the stale "~95 MB"
  copy.
- `docs/THIRD-PARTY-LICENSES.md` now documents LLVM-MinGW/UCRT instead
  of w64devkit plus official LLVM.

## Clean-Windows smoke

Local:

- `tools/llvm-mingw-bundle/extract_sdk.ps1` passed after staging:
  it compiled and ran a C smoke program with the SDK `bin/` plus
  `C:\Windows\System32;C:\Windows` on PATH and with `LIB`/`INCLUDE`
  removed.

CI:

- Published ZIP clean-Windows smoke is configured in
  `.github/workflows/publish.yml` as `windows-sdk-smoke`.
- It could not be executed locally because no v5.12.0 release artifact
  was created in this session.

## GitNexus impact summary

Pre-flight:

- `npx gitnexus status`: index stale at first.
- `npx gitnexus analyze`: refreshed successfully with 28,951 nodes,
  62,785 edges, 640 clusters, and 300 flows.

Impact checks before symbol edits:

| Symbol | Risk | Direct callers | Affected processes |
|---|---|---:|---|
| `detect_toolchain` | LOW | 3 | `cmd_build`, `cmd_run` |
| `_bundle_root` | LOW | 1 | `cmd_build`, `cmd_run` |
| `invocation_env` | LOW | 3 | `cmd_build`, `cmd_run` |
| `_search_dir_for_compiler` | LOW | 1 | `cmd_build`, `cmd_run` |
| `_clang_sibling` | LOW | 1 | `cmd_build`, `cmd_run` |
| `Toolchain` | MEDIUM | 3 | `cmd_build`, `cmd_run` |

No HIGH or CRITICAL impact result was returned.

PowerShell `Cmd-Install` in `packaging/mapanare-up.ps1` is not indexed
by GitNexus, so no graph impact result was available for that script
function.

## Validation

Local validation run:

```text
python -m pytest tests/test_toolchain.py -q
  -> 5 passed

python -m pytest tests/test_runner/test_test_runner.py tests/cli/test_cli.py -q
  -> 56 passed, 7 skipped

python -m ruff check mapanare/toolchain.py tests/test_toolchain.py
  -> All checks passed

python -c "import yaml; yaml.safe_load(open('.github/workflows/publish.yml')); print('publish.yml OK')"
  -> publish.yml OK

PowerShell parser:
  packaging/install.ps1 OK
  packaging/mapanare-up.ps1 OK
  tools/llvm-mingw-bundle/extract_sdk.ps1 OK

tools/llvm-mingw-bundle/extract_sdk.ps1 against pinned LLVM-MinGW ZIP
  -> LLVM-MinGW SDK smoke: OK
  -> uncompressed SDK subset size: 316.4 MB

git diff --check
  -> no whitespace errors
```

The self-hosted compiler validation suite was not run because this
session did not edit self-hosted compiler files.

## Change detection

GitNexus MCP tools were not available in this session (`list_mcp_resources`
returned no resources). The local GitNexus CLI also does not expose a
`detect-changes` command. Fallback change detection was used:

- `git diff --stat`
- `git diff --name-only`
- `npx gitnexus status`

Fallback output summary:

```text
git diff --stat
  .github/workflows/publish.yml         | 346 +++++++++++++++++-----------------
  AGENTS.md                             |   2 +-
  CHANGELOG.md                          |  32 +++-
  CLAUDE.md                             |  11 +-
  README.md                             |  10 +-
  docs/THIRD-PARTY-LICENSES.md          |  78 ++++----
  mapanare/toolchain.py                 | 106 ++++++++---
  packaging/install.ps1                 |  95 ++++++----
  packaging/mapanare-up.ps1             |  53 +++++-
  packaging/mapanare.spec               |  11 +-
  tools/llvm-bundle/REQUIRED_FILES.md   |   7 +-
  tools/llvm-bundle/extract_minimal.ps1 |   3 +
  12 files changed, 448 insertions(+), 306 deletions(-)

git status --short
  M .github/workflows/publish.yml
  M AGENTS.md
  M CHANGELOG.md
  M CLAUDE.md
  M README.md
  M docs/THIRD-PARTY-LICENSES.md
  M mapanare/toolchain.py
  M packaging/install.ps1
  M packaging/mapanare-up.ps1
  M packaging/mapanare.spec
  M tools/llvm-bundle/REQUIRED_FILES.md
  M tools/llvm-bundle/extract_minimal.ps1
  ?? docs/roadmap/v5/v5.12.0/SESSION_REPORT.md
  ?? docs/roadmap/v5/v5.12.0/WINDOWS_TOOLCHAIN_AUDIT.md
  ?? tests/test_toolchain.py
  ?? tools/llvm-mingw-bundle/

npx gitnexus status
  Indexed commit: adc6e13
  Current commit: adc6e13
  Status: up-to-date
```

The changed scope matches Wk.* packaging/toolchain/docs. `AGENTS.md`
changed only because `npx gitnexus analyze` refreshed the GitNexus
symbol/edge counts from 28,912/62,763 to 28,951/62,785.
