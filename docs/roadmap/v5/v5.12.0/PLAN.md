# v5.12.0 - Mc.6 / Wk.* - Windows SDK split + true minimal bundle

**Status:** PLANNING
**Breaking:** No for default Windows installs. The default Windows
installer must still produce a working `mnc run` / `mnc build` on a
clean Windows machine.
**Prerequisite:** v5.11.2 shipped with the documented Windows bundle
size regression: `mapanare-5.11.2-win-x64.zip` is 255.2 MB and
`mapanare-5.11.2-win-x64-minimal.zip` is 162.0 MB.

**Estimated effort:**
- Phase 0 (audit + model decision) - 1-2h
- Phase 1 (toolchain.py bundled SDK discovery) - 2-3h
- Phase 2 (replace w64devkit staging with curated LLVM-MinGW SDK) - 3-5h
- Phase 3 (publish/install script artifact split) - 2-3h
- Phase 4 (clean-Windows smoke + size gates) - 2-3h
- Phase 5 (docs + release bookkeeping) - 1-2h
- **Total:** 11-18 hours, likely two sessions because Windows CI is
  the real validator.

---

## Why this exists

v5.10.0 fixed the right user pain: a fresh Windows install should not
say "missing clang" or "missing C compiler" when the first command is
`mnc run`. The implementation fixed that by staging `w64devkit` before
PyInstaller and then adding LLVM afterward. That solved clean-machine
failures, but it shipped two compiler stacks:

- `dist/mapanare/toolchain/` - w64devkit, about 150 MB compressed in
  the release ZIP
- `dist/mapanare/llvm/` - minimal LLVM 18.1.8, about 93 MB compressed
  in the release ZIP

The result is a 255 MB Windows ZIP and a "minimal" ZIP that is not
minimal. macOS and Linux are not affected: their PyInstaller bundles
are about 12 MB because those platforms continue to use system clang.

Python is smaller because the Windows Python installer ships a
prebuilt interpreter, not a native compiler SDK. Plain `.py` execution
does not need a C compiler. Python users only need external build
tools for native extensions, and most users avoid that path through
prebuilt wheels. Mapanare's core promise is different: `mnc run` and
`mnc build` compile native binaries, so the Windows "works out of the
box" artifact needs a real Windows toolchain or an on-demand toolchain
installer.

Reference size baseline:
- Python 3.15.0a8 Windows x64 installer: 40.4 MB
- Python 3.15.0a8 Windows embeddable package: 12.8 MB
- Mapanare v5.11.2 Windows full ZIP: 255.2 MB
- Mapanare v5.11.2 Windows minimal ZIP: 162.0 MB

Python reference: https://www.python.org/downloads/release/python-3150a8/

---

## Goal

Ship a professional Windows distribution model:

1. **Default Windows install still works offline on a clean machine.**
   No return to the "missing clang/gcc" first-run failure.
2. **Stop double-shipping compilers.** The default working artifact
   uses one curated SDK, not `w64devkit` plus official LLVM.
3. **Make the minimal artifact actually minimal.** No bundled compiler
   SDK, no `toolchain/`, no `llvm/`.
4. **Use explicit artifact names.** The SDK artifact should be named
   like an SDK so the size is honest and expected.
5. **Keep existing installer behavior compatible.** Existing users who
   run `install.ps1` with no flags still get the clean-machine working
   install.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Wk.1** | HIGH | Write `WINDOWS_TOOLCHAIN_AUDIT.md`: byte table for current v5.11.2 assets, why Python is not the same packaging problem, and evaluated toolchain options. | 1h |
| **Wk.2** | HIGH | Teach `mapanare/toolchain.py` to detect bundled LLVM-MinGW at `<install>/llvm/bin/clang.exe` or `<install>/sdk/bin/clang.exe` before PATH/system probes. Preserve `toolchain/` support only as a legacy fallback. | 2-3h |
| **Wk.3** | HIGH | Replace `w64devkit` staging in `build-cli` with a curated LLVM-MinGW/UCRT SDK subset that contains clang/lld plus the Windows target headers, startup objects, import libs, and CRT libs needed for generated C/LLVM output. | 3-5h |
| **Wk.4** | HIGH | Produce a true minimal Windows ZIP before any SDK is staged. Target `< 25 MB`; alarm at `> 40 MB`. | 1h |
| **Wk.5** | HIGH | Produce a default SDK Windows ZIP that works on a clean machine. Target `< 150 MB`; hard alarm at `> 180 MB`. | 1-2h |
| **Wk.6** | MEDIUM | Add a published-ZIP smoke job that strips `PATH`, `LIB`, and `INCLUDE`, extracts the SDK ZIP, and runs `mnc run`, `mnc build`, and `mnc test`. | 1-2h |
| **Wk.7** | MEDIUM | Update `packaging/install.ps1`, `packaging/mapanare-up.ps1`, release table copy, and README wording so "minimal" vs "SDK" is honest. Keep `MAPANARE_NO_BUNDLED_LLVM=1` as a compatibility alias. | 1-2h |
| **Wk.8** | MEDIUM | Add focused tests for bundled SDK detection and no-toolchain minimal selection. | 1-2h |

---

## Release model

Canonical artifacts for v5.12.0:

| Artifact | Meaning | Size target |
|---|---|---:|
| `mapanare-5.12.0-win-x64-sdk.zip` | Default clean-machine Windows install. Includes Mapanare plus one curated LLVM-MinGW SDK. | `< 150 MB` |
| `mapanare-5.12.0-win-x64-minimal.zip` | App-only CLI. Requires user-provided compiler toolchain for `run` / `build`. | `< 25 MB` |
| `mapanare-5.12.0-win-x64.zip` | Compatibility alias to SDK ZIP for one release. Existing default install behavior keeps working. | same as SDK |

Installer defaults:

- `install.ps1` with no env vars downloads the SDK ZIP.
- `MAPANARE_NO_BUNDLED_LLVM=1` downloads the minimal ZIP. Keep this
  name for compatibility.
- Add `MAPANARE_NO_BUNDLED_TOOLCHAIN=1` as the clearer new spelling.
- `mapanare-up` mirrors the same selection logic.

This is intentionally not "make Windows as small as Python." The
correct comparison is:

- Python runtime-only installer: small, because no compiler SDK
- Mapanare minimal ZIP: small, because no compiler SDK
- Mapanare SDK ZIP: larger, because it guarantees native compilation
  on a clean Windows machine

---

## Phase plan

### Phase 0 - Audit + model decision

Create:

```text
docs/roadmap/v5/v5.12.0/WINDOWS_TOOLCHAIN_AUDIT.md
```

Required contents:

- Current v5.11.2 release asset sizes from GitHub.
- Current local byte contributors:
  - `toolchain/` uncompressed size
  - `dist/mapanare/llvm/` or `tools/llvm-bundle` staged subset size
  - PyInstaller bundle size on Windows, Linux, macOS
- Python comparison: why Python's 40 MB installer is not a compiler
  SDK.
- Toolchain option table:
  - keep w64devkit: rejected, too broad
  - official LLVM minimal only: rejected unless proven to link on a
    clean machine without MSVC/Windows SDK
  - LLVM-MinGW/UCRT curated subset: preferred
  - on-demand toolchain installer only: deferred because default
    install must keep working offline

Exit criteria:

- The plan names the chosen SDK source and pinned version.
- The audit has a size target and hard alarm.
- No implementation starts until the audit explains exactly which
  files are required.

### Phase 1 - `toolchain.py` bundled SDK discovery

Likely edits:

- `mapanare/toolchain.py`
- tests under `tests/` for detection behavior

Expected behavior:

1. Running from PyInstaller one-dir:
   - prefer `<exe_dir>/sdk/bin/clang.exe` or `<exe_dir>/llvm/bin/clang.exe`
   - set `bin_dir` to that `bin`
   - set `rt_archive` to the bundled `libmapanare_rt.a`
2. Running from source:
   - keep existing `repo/toolchain/` behavior for local tests only
3. System PATH:
   - remains fallback
4. Windows known install roots:
   - remains last fallback

Important: if the bundled SDK is clang-only, `Toolchain.compiler`
must still be clang so `_run_c_source()` and C-backend paths work.
Do not require `gcc.exe` to exist.

### Phase 2 - SDK staging in `publish.yml`

Replace the Windows `build-cli` w64devkit staging path with the
chosen SDK.

Requirements:

- Do not create `repo/toolchain/` before PyInstaller runs.
- Archive the minimal ZIP before SDK staging.
- Stage SDK into `dist/mapanare/sdk/` or `dist/mapanare/llvm/`, not
  `dist/mapanare/toolchain/`.
- Prebuild `libmapanare_rt.a` with the same SDK that ships in the
  ZIP.
- Ensure the Python CLI alias `mnc.exe` exists in the archived ZIP,
  not only after `install.ps1` copies files.

Preferred layout:

```text
mapanare/
  mapanare.exe
  mnc.exe
  runtime/
  stdlib/
  mapanare/
  sdk/
    bin/
      clang.exe
      lld.exe or ld.lld.exe
    x86_64-w64-mingw32/
      include/
      lib/
    lib/
      clang/
      mapanare/libmapanare_rt.a
  THIRD-PARTY-LICENSES.md
```

If `sdk/` is too invasive for v5.12.0, `llvm/` is acceptable, but
the docs must call out that it is a full Windows SDK subset, not just
official LLVM binaries.

### Phase 3 - Artifact split + installer updates

Update:

- `.github/workflows/publish.yml`
- `packaging/install.ps1`
- `packaging/mapanare-up.ps1`
- release body download table
- `README.md` Windows install section

Rules:

- SDK ZIP is default.
- Minimal ZIP is opt-in.
- Existing `MAPANARE_NO_BUNDLED_LLVM=1` continues to work.
- Add `MAPANARE_NO_BUNDLED_TOOLCHAIN=1`.
- Download banner must show honest expected size:
  - SDK: "Mapanare + Windows SDK"
  - minimal: "Mapanare only, requires clang/gcc separately"
- Remove stale "~95 MB" copy. That number was aspirational and is
  no longer the contract.

### Phase 4 - Clean-Windows smoke + size gates

Add or update the published artifact smoke job:

```powershell
$env:PATH = "C:\Windows\System32;C:\Windows"
Remove-Item Env:LIB -ErrorAction SilentlyContinue
Remove-Item Env:INCLUDE -ErrorAction SilentlyContinue
Remove-Item Env:CC -ErrorAction SilentlyContinue
Remove-Item Env:CXX -ErrorAction SilentlyContinue
```

Then:

```powershell
.\out\mapanare\mnc.exe --version
.\out\mapanare\mnc.exe run hello.mn
.\out\mapanare\mnc.exe build hello.mn -o hello.exe
.\hello.exe
.\out\mapanare\mnc.exe test smoke_tests.mn
```

Size checks:

- minimal ZIP `> 40 MB` fails
- SDK ZIP `> 180 MB` fails
- SDK ZIP `> 150 MB` warns with a TODO and requires explicit
  justification in `WINDOWS_TOOLCHAIN_AUDIT.md`

Also assert:

```powershell
if (Test-Path out\mapanare\toolchain) {
    throw "toolchain/ must not be shipped after Wk.*"
}
```

### Phase 5 - Docs + release bookkeeping

Update:

- `CHANGELOG.md`
- `CLAUDE.md`
- `README.md`
- `docs/roadmap/v5/v5.12.0/SESSION_REPORT.md`
- `docs/roadmap/v5/v5.12.0/WINDOWS_TOOLCHAIN_AUDIT.md`
- `docs/THIRD-PARTY-LICENSES.md`

Session report must include:

- before/after asset sizes
- exact SDK source and version
- exact size-gate thresholds
- clean-Windows smoke result
- note that Python can be 40 MB because it does not ship a compiler
  SDK

---

## What ships

- `mapanare/toolchain.py` bundled SDK detection
- tests for bundled SDK detection
- `.github/workflows/publish.yml` Windows artifact split
- `packaging/install.ps1` SDK/minimal selection cleanup
- `packaging/mapanare-up.ps1` matching selection cleanup
- `README.md` and release body wording updates
- `docs/THIRD-PARTY-LICENSES.md` update for the chosen SDK
- `docs/roadmap/v5/v5.12.0/PROMPT.md`
- `docs/roadmap/v5/v5.12.0/PLAN.md`
- `docs/roadmap/v5/v5.12.0/WINDOWS_TOOLCHAIN_AUDIT.md`
- `docs/roadmap/v5/v5.12.0/SESSION_REPORT.md`

## What does not ship

- No macOS/Linux SDK bundling.
- No native-only PyInstaller replacement. `mnc` parity gaps remain a
  separate Mc.* track.
- No attempt to make the SDK ZIP match Python's runtime installer
  size. The honest target is "under 150 MB while still compiling on a
  clean Windows machine."
- No new language/compiler features.

---

## Decisions

### Decision 1: default Windows artifact

**Recommendation:** keep the default installer on the working SDK
artifact. The user-visible problem that started v5.10.0 was clean
Windows installs failing at first compile. Do not reintroduce that.

### Decision 2: canonical SDK name

**Recommendation:** introduce `mapanare-${V}-win-x64-sdk.zip` as the
canonical full artifact, keep `mapanare-${V}-win-x64.zip` as a
compatibility alias to SDK for one release.

### Decision 3: SDK location

**Recommendation:** prefer `sdk/` over `llvm/` if the bundled payload
contains MinGW headers/libs and CRT objects. `llvm/` was accurate for
v5.10.0's official LLVM subset; after v5.12.0 the bundle is a Windows
compilation SDK.

### Decision 4: minimal artifact promise

**Recommendation:** minimal means no bundled compiler SDK. It can type
check, format, emit source/IR, run LSP, etc., but native compile/run
requires a system toolchain or `mapanare-up install-toolchain`.

---

## Risk register

| ID | Risk | Mitigation |
|---|---|---|
| Wk.R1 | Removing w64devkit breaks clean Windows compile/link. | Clean-Windows smoke strips PATH/LIB/INCLUDE and runs `mnc run`, `mnc build`, and `mnc test` from the published ZIP. |
| Wk.R2 | Official LLVM alone lacks Windows SDK pieces and only works on developer machines. | Prefer LLVM-MinGW/UCRT curated subset unless the audit proves official LLVM links with no MSVC/SDK present. |
| Wk.R3 | Minimal ZIP accidentally includes SDK files because PyInstaller sees a staged directory. | Archive minimal before staging SDK; CI asserts no `toolchain/`, `sdk/`, or `llvm/` in minimal. |
| Wk.R4 | SDK ZIP remains too large because the whole toolchain is copied. | Build a required-file manifest and fail above 180 MB. |
| Wk.R5 | Existing users/scripts expect `mapanare-win-x64.zip`. | Keep it as a compatibility alias to SDK for v5.12.0; installer defaults unchanged. |
| Wk.R6 | License attribution is incomplete after switching SDK source. | Update `THIRD-PARTY-LICENSES.md`; copy upstream license files into the SDK directory. |
| Wk.R7 | C backend paths still assume gcc. | `Toolchain.compiler` can be clang; tests must cover clang-only bundled SDK. |

