# v5.12.0 Windows Toolchain Audit

**Scope:** Mc.6 / Wk.* Windows SDK split.
**Date:** 2026-04-28.
**Decision:** v5.12.0 will ship one curated LLVM-MinGW UCRT x86_64
SDK in the default Windows ZIP and no compiler SDK in the minimal ZIP.

---

## Evidence

### Published release asset sizes

Command:

```powershell
$raw = Invoke-WebRequest `
  -Uri 'https://api.github.com/repos/Mapanare-Research/Mapanare/releases?per_page=10' `
  -UseBasicParsing
$releases = $raw.Content | ConvertFrom-Json
foreach ($release in $releases) {
  Write-Host "TAG $($release.tag_name)"
  foreach ($asset in $release.assets) {
    Write-Host ("  {0} {1} MB" -f $asset.name, [math]::Round($asset.size/1MB,1))
  }
}
```

Relevant output:

```text
TAG v5.11.2
  mapanare-5.11.2-linux-x64.tar.gz 11.9 MB
  mapanare-5.11.2-mac-arm64.tar.gz 11.6 MB
  mapanare-5.11.2-win-x64-minimal.zip 162 MB
  mapanare-5.11.2-win-x64.zip 255.2 MB
  mapanare-win-x64-minimal.zip 162 MB
  mapanare-win-x64.zip 255.2 MB
```

The current Windows "minimal" ZIP is the same size as the pre-v5.10
Windows full ZIP because PyInstaller sees `repo/toolchain/` before the
minimal archive is made. The later LLVM stage then makes the default
ZIP larger again.

### Local size contributors

Command:

```powershell
Get-ChildItem -Path toolchain -Recurse -File -ErrorAction SilentlyContinue |
  Measure-Object Length -Sum
```

Output:

```text
Count : 8120
Sum   : 584057890
```

The staged local `toolchain/` tree is 584,057,890 bytes, about
557.0 MiB uncompressed. That is the source of the 162 MB compressed
Windows "minimal" ZIP.

Command:

```powershell
Get-ChildItem -Path dist\mapanare -Recurse -File -ErrorAction SilentlyContinue |
  Group-Object { Split-Path $_.FullName -Parent } |
  Sort-Object { ($_.Group | Measure-Object Length -Sum).Sum } -Descending |
  Select-Object -First 30
```

Output:

```text
No local dist\mapanare directory was staged in this checkout.
```

### Python comparison

Python 3.15.0a8 is a useful sanity check only for the runtime-only
case. The official Python release page lists:

- Windows installer (64-bit): 40.4 MB
- Windows embeddable package (64-bit): 12.8 MB

Reference: https://www.python.org/downloads/release/python-3150a8/

Python can hit those sizes because it ships an interpreter and standard
library, not a Windows C compiler SDK. Running Python scripts does not
need headers, startup objects, import libraries, a linker, or a CRT
sysroot. Mapanare's `run` and `build` commands produce native binaries,
so a clean Windows install needs either a bundled SDK or a first-run SDK
installer. v5.12.0 keeps the bundled SDK path for the default artifact.

---

## Current failure mode

v5.11.2 double-ships compiler stacks:

1. `dist/mapanare/toolchain/` from w64devkit, staged before
   PyInstaller, so it is captured inside both the default ZIP and the
   "minimal" ZIP.
2. `dist/mapanare/llvm/` from official LLVM 18.1.8, staged after the
   minimal ZIP, so only the default ZIP gets it.

The current result is:

- `mapanare-5.11.2-win-x64-minimal.zip`: 162 MB, not minimal.
- `mapanare-5.11.2-win-x64.zip`: 255.2 MB, w64devkit plus LLVM.

The fix is not to remove the compiler from the default install. The fix
is to stop staging `toolchain/` before PyInstaller and to make the
default ZIP include exactly one Windows SDK.

---

## Toolchain options

| Option | Decision | Reason |
|---|---|---|
| Keep w64devkit | Rejected | It works on clean Windows but is too broad for the default ZIP and, when staged before PyInstaller, makes the minimal ZIP 162 MB. |
| Official LLVM minimal only | Rejected | The current official LLVM subset has `clang.exe`, `lld-link.exe`, `LLVM-C.dll`, and compiler-rt builtins, but it does not include MinGW or MSVC Windows headers, startup objects, import libraries, or UCRT libraries. It can appear to work on developer or CI machines that already expose SDK pieces through `LIB`/`INCLUDE`; that is not a clean-machine guarantee. |
| LLVM-MinGW UCRT curated subset | Accepted | It ships clang/lld plus a MinGW-w64/UCRT sysroot: Windows headers, CRT startup objects, import libs, and runtime libraries. This matches Mapanare's clean Windows requirement without shipping both w64devkit and official LLVM. |
| On-demand SDK installer only | Deferred | It could keep the default download small, but it would change the v5.10.0 promise that default Windows installs compile offline on first run. |

---

## Chosen SDK

**Source:** Martin Storsjo LLVM-MinGW.

**Pinned release:** `20260421`, named `llvm-mingw 20260421 with LLVM
22.1.4`.

**Pinned asset:** `llvm-mingw-20260421-ucrt-x86_64.zip`.

**Upstream compressed size:** 178.5 MB for the full multi-target/tool
archive.

**Local extractor check:** `tools/llvm-mingw-bundle/extract_sdk.ps1`
staged the curated subset at 316.4 MB uncompressed and passed its
clang smoke with only the staged SDK `bin/` plus Windows system
directories on `PATH`; `LIB` and `INCLUDE` were removed.

**License:** LLVM components are Apache License 2.0 with LLVM
Exception. MinGW-w64 runtime/import libraries and winpthreads carry
their upstream permissive/runtime licenses. v5.12.0 must update
`docs/THIRD-PARTY-LICENSES.md` and stage upstream license files inside
the Windows SDK ZIP.

The release was selected because it is the current upstream LLVM-MinGW
UCRT x86_64 release as of 2026-04-28 and contains LLVM 22.1.4 plus the
matching MinGW-w64/UCRT sysroot. Pinning the date-stamped asset keeps CI
reproducible.

---

## Required SDK subset

The v5.12.0 SDK ZIP must contain enough to compile and link generated C
and LLVM IR on a clean Windows machine. It must not include non-Windows
targets, LLDB, clangd, Python, BusyBox, or general developer tools.

Required layout under `dist/mapanare/sdk/`:

```text
sdk/
  LICENSE.TXT
  bin/
    clang.exe
    clang-22.exe
    x86_64-w64-mingw32-clang.exe
    ld.lld.exe
    ld.exe              # staged copy of ld.lld.exe for clang's GNU driver lookup
    llvm-ar.exe
    llvm-ranlib.exe
    llvm-strip.exe
    ar.exe
    libLLVM-22.dll
    libclang-cpp.dll
    libwinpthread-1.dll
    libunwind.dll
    libc++.dll
  include/
    ... MinGW-w64/UCRT Windows headers ...
  lib/
    clang/22/include/
    clang/22/lib/windows/libclang_rt.builtins-x86_64.a
    mapanare/libmapanare_rt.a
  x86_64-w64-mingw32/
    bin/
      libwinpthread-1.dll
      libunwind.dll
      libc++.dll
    lib/
      crt2.o
      dllcrt2.o
      libmingw32.a
      libmingwex.a
      libucrt.a
      libkernel32.a
      libadvapi32.a
      libuser32.a
      libws2_32.a
      libshell32.a
      libgcc.a          # staged copy of compiler-rt builtins
      libgcc_eh.a       # staged copy of libunwind.a
      ... x86_64 import libraries required by clang's MinGW driver ...
    share/mingw32/
      COPYING*
```

Implementation note: keep the full `include/`,
`lib/clang/22/include/`, `lib/clang/22/lib/windows/` builtins file, and
`x86_64-w64-mingw32/lib/` for v5.12.0. More aggressive import-library
trimming can happen only after the clean-Windows smoke proves all
Mapanare runtime paths link without hidden host SDK state.

---

## Size gates

Hard gates for v5.12.0:

- Minimal Windows ZIP: fail above 40 MB. Target below 25 MB.
- SDK Windows ZIP: fail above 180 MB. Target below 150 MB.
- Warn above 150 MB for the SDK ZIP and document why the target was
  missed.

CI must also fail if:

- The minimal ZIP contains `toolchain/`, `sdk/`, or `llvm/`.
- Any v5.12.0 Windows release ZIP contains `toolchain/`.
- The SDK smoke passes only with inherited `PATH`, `LIB`, `INCLUDE`,
  `CC`, or `CXX`.

---

## Phase 0 conclusion

Proceed to Phase 1 with LLVM-MinGW UCRT x86_64 pinned to release
`20260421`. The implementation target is:

- `mapanare-${V}-win-x64-minimal.zip`: app-only, no SDK, under 40 MB.
- `mapanare-${V}-win-x64-sdk.zip`: app plus curated LLVM-MinGW SDK,
  under 180 MB hard gate, under 150 MB target.
- `mapanare-${V}-win-x64.zip`: compatibility alias to the SDK ZIP.
