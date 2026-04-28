# v5.10.0 — Win.1b — Bundled LLVM toolchain in Windows release ZIP

**Status:** PLANNING
**Breaking:** No (additive — users without bundled LLVM still
fall through to v5.9.0's DX.3 install-clang-instructions message)
**Prerequisite:** v5.9.0 shipped. Specifically:
- DX.3 (clang-missing detection) — v5.10.0's bundled-clang
  detection layers ON TOP of DX.3's probe; DX.3 becomes the
  fallback when the bundle is absent or disabled.
- DX.6 (`mnc` vs `mapanare.exe` naming canonicalized) — v5.10.0
  extends `install.ps1` and assumes the canonical name is
  settled.
**Estimated effort:**
- Phase 1 (LLVM minimal-subset extraction) — 3-4h
- Phase 2 (CI cache + workflow integration) — 2-3h
- Phase 3 (`mnc` bundled-toolchain detection) — 2-3h
- Phase 4 (install.ps1 ZIP layout + verification) — 1-2h
- Phase 5 (LICENSE + redistribution compliance) — 1h
- Phase 6 (validation matrix + release-size audit) — 1-2h
- **Total:** 10-15 hours across 2-3 focused sessions

---

## Goal

Eliminate the "install LLVM separately" step for Windows users.
Ship `clang.exe`, `lld-link.exe`, and the minimum runtime DLLs
they need INSIDE the Mapanare Windows release ZIP. After this
release:

- A Windows user runs
  `irm https://mapanare.dev/install.ps1 | iex`, types
  `mnc run hello.mn`, and it works. **Zero external dependencies.**
- The published `mapanare-win-x64.zip` grows from ~10 MB to
  ~80-100 MB (depending on Phase 1's minimal-subset extraction
  effectiveness). Within GitHub Actions limits (2 GB asset
  cap; 14 GB Windows runner disk; unlimited public-repo
  bandwidth).
- `mnc` looks for `bin/llvm/clang.exe` next to itself first,
  falls back to PATH-installed clang, falls back to v5.9.0
  DX.3's install-instructions error.
- Users who want a smaller install can set
  `$env:MAPANARE_NO_BUNDLED_LLVM = "1"` before invoking
  `install.ps1` to skip the bundle (download a smaller
  `mapanare-win-x64-minimal.zip` instead).

This is a Windows-only release in scope. macOS and Linux users
already have working clang via system package managers; bundling
there adds bytes without solving real pain. Audit is in §"What
does NOT ship" but the work is deferred.

---

## Why this matters (recap from v5.8.7 Windows install probe)

The user's findings explicitly call out:

> Missing clang dependency is a hard stop: All
> run/compile/build/test commands fail silently with
> "clang failed" if clang isn't installed. Most Windows users
> won't have clang.

And:

> Why Python's approach works:
> - Python's Windows installer adds itself to PATH
> - **Bundles everything needed (no external dependencies)**
> - Creates Start Menu shortcuts
> - Registers file associations (.py)

> Quick wins:
> - **Consider bundling clang.exe or lld-link.exe for Windows**

v5.9.0 closes the "fail silently" gap (DX.3's helpful error
message). v5.10.0 closes the "external dependency" gap by
removing the dependency entirely. After v5.10.0, the v5.9.0
DX.3 message becomes a fallback — users only see it if they
explicitly opted out of the bundle.

---

## Existing infrastructure to build on

`.github/workflows/publish.yml` already vendors a portable
toolchain for **Mapanare's own build** (the `build-cli` and
`build-native` jobs use w64devkit at `:367-385` and `:371-385`).
That's gcc + binutils, not LLVM/clang. v5.10.0 vendors LLVM
clang specifically, for **Mapanare users' builds**.

Key reuse:
- The `actions/cache@v4` pattern for w64devkit caching translates
  directly to LLVM caching.
- The "Stage portable toolchain" step at `:371` is the model for
  the new "Stage LLVM bundle for redistribution" step.
- `packaging/install.ps1` already handles ZIP extraction + PATH
  setup. No changes needed beyond pointing at the new ZIP and
  optionally honoring the `MAPANARE_NO_BUNDLED_LLVM` env var.

What's missing:
1. A Phase 1 audit of which LLVM binaries + DLLs are actually
   required. A naive bundle of all of LLVM is ~800 MB; the
   target is ~80-100 MB.
2. A workflow step that downloads pinned LLVM, strips to the
   minimal subset, and stages it in the release ZIP under
   `bin/llvm/`.
3. `mnc` runtime logic to prefer `bin/llvm/clang.exe` over
   PATH clang. Needs `__mn_executable_dir()` (probably exists;
   verify) so the bundled-clang path can be derived relative
   to the binary's own location.
4. A LICENSE file for the bundled LLVM components — Apache 2.0
   with LLVM Exception is permissive but redistribution
   requires the license text.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Win.1b.A** | HIGH (correctness — release size) | Determine the minimal subset of LLVM that Mapanare actually invokes. Probe via `dumpbin /dependents clang.exe` on the upstream LLVM Windows release; identify required DLLs. Mapanare uses `clang.exe` (compile + link via `clang -o` driver) and may use `lld-link.exe` separately for some paths. Capture the full closure. Target final size: ≤ 100 MB. | 3-4h |
| **Win.1b.B** | HIGH (CI hygiene) | Add `actions/cache@v4` step in publish.yml keyed on the pinned LLVM version. First run downloads from llvm.org; subsequent runs hit the cache. Without this, every release downloads ~800 MB from llvm.org and is at the mercy of llvm.org rate limits / 503s. | 1-2h |
| **Win.1b.C** | MEDIUM (correctness) | New workflow step: extract LLVM, copy minimal subset (per Win.1b.A) into `dist/mapanare-win-x64/bin/llvm/`. Verify the staged binaries actually run by invoking `dist/mapanare-win-x64/bin/llvm/clang.exe --version` in CI. | 1-2h |
| **Win.1b.D** | MEDIUM (correctness) | Mapanare's `mnc` binary must look up the bundled clang relative to its own executable directory. Check if `__mn_executable_dir()` (or equivalent) exists; add it if not. Then update each clang shell-out site in `mapanare/self/main.mn` to prefer `<exe_dir>/llvm/clang.exe` over PATH clang. | 2-3h |
| **Win.1b.E** | LOW (legal) | Apache 2.0 with LLVM Exception requires the LICENSE.TXT to ship with redistributed binaries. Copy `LICENSE.TXT` from the upstream LLVM release into `dist/mapanare-win-x64/bin/llvm/LICENSE.TXT`. Add a `dist/mapanare-win-x64/THIRD-PARTY-LICENSES.md` index referencing it. | 1h |
| **Win.1b.F** | LOW (UX) | install.ps1 honors `$env:MAPANARE_NO_BUNDLED_LLVM = "1"`: when set, downloads `mapanare-win-x64-minimal.zip` (the v5.9.0-shaped ZIP without the LLVM bundle) instead of `mapanare-win-x64.zip`. Both ZIPs published from the same release. install.ps1 also detects whether bundled clang is present and prints a matching getting-started tip ("Using bundled LLVM" vs "Using PATH clang"). | 2h |
| **Win.1b.G** | LOW (validation) | Add a CI smoke job (`windows-bundled-llvm-smoke`) that downloads the published ZIP from a draft release, extracts to a clean dir, and runs `bin/mnc.exe run examples/hello.mn` — without touching system PATH. Catches "the bundle is broken" before users do. | 1-2h |

---

## Phase plan

### Phase 1 — Win.1b.A — minimal-subset extraction

**Run on a Windows host (or VM).** Cannot be done from WSL because
`dumpbin` is a Visual Studio tool.

1. Download pinned LLVM Windows release. Recommended: LLVM 18.1.8
   (latest stable as of 2026-04 with broad clang -target support).
   Pin via:
   ```
   LLVM_VERSION=18.1.8
   url=https://github.com/llvm/llvm-project/releases/download/llvmorg-${LLVM_VERSION}/LLVM-${LLVM_VERSION}-win64.exe
   ```
   The `.exe` is a 7zip self-extracting installer; extract via
   `7z x LLVM-18.1.8-win64.exe -oLLVM-18.1.8`.
2. Identify required binaries. Mapanare's invocations
   (per `mapanare/self/main.mn` audit, post-v5.9.0):
   - `clang.exe` — primary; used in `run_test`, `run_build`,
     `run_program`, `run_compile`
   - `lld-link.exe` — used by `clang -o` driver internally on
     Windows; required on the lookup path
   - Optionally: `llvm-strip.exe` (if v5.9.0's strip portability
     work needs it)
   Cross-check via:
   ```bash
   grep -nE "clang|lld|llvm-" mapanare/self/main.mn
   ```
3. Identify required DLLs. From an extracted LLVM-18.1.8/bin:
   ```cmd
   dumpbin /dependents clang.exe
   dumpbin /dependents lld-link.exe
   ```
   Capture the closure. Recursively, until all transitively-
   referenced DLLs are accounted for. Typical results for LLVM
   18 on Windows:
   - `LLVM-C.dll` (~70-100 MB — the bulk)
   - `clang_rt.builtins-x86_64.lib` (compiler-rt; needed for
     some intrinsics)
   - C runtime DLLs (vcruntime140.dll, msvcp140.dll) — usually
     present on Windows by default; do NOT redistribute unless
     necessary
   - mingw runtime DLLs IF clang was built against mingw
4. Build the minimal subset. Create `tools/llvm-bundle/` with
   a script `extract_minimal.ps1`:
   ```powershell
   # Extracts the minimal LLVM subset for redistribution.
   # Output: $OutDir contains clang.exe, lld-link.exe, required DLLs,
   # LICENSE.TXT.
   param(
       [string]$LlvmDir = ".\LLVM-18.1.8",
       [string]$OutDir = ".\dist\bundle"
   )
   New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
   $required = @(
       "clang.exe",
       "lld-link.exe",
       "LLVM-C.dll"
       # ... add others identified by dumpbin
   )
   foreach ($f in $required) {
       Copy-Item "$LlvmDir\bin\$f" -Destination "$OutDir\$f"
   }
   # compiler-rt (path varies by LLVM version):
   Copy-Item "$LlvmDir\lib\clang\18\lib\windows\clang_rt.builtins-x86_64.lib" `
       -Destination "$OutDir\clang_rt.builtins-x86_64.lib"
   # License:
   Copy-Item "$LlvmDir\LICENSE.TXT" -Destination "$OutDir\LICENSE.TXT"
   # Verify:
   $size = (Get-ChildItem $OutDir -Recurse | Measure-Object Length -Sum).Sum / 1MB
   Write-Host "Bundle size: $([math]::Round($size, 1)) MB"
   if ($size -gt 100) {
       Write-Warning "Bundle exceeds 100 MB target."
   }
   ```
5. Verify the minimal bundle works:
   ```powershell
   # Compile a hello-world C program with ONLY the bundled clang:
   cd $OutDir
   .\clang.exe ..\test\hello.c -o hello.exe
   .\hello.exe
   # Expected: prints "Hello, world!"

   # Confirm no fallthrough to system clang (move bundle to a temp dir
   # outside of PATH, repeat the test):
   $env:PATH = "C:\Windows\System32;C:\Windows"  # strip user PATH
   .\clang.exe ..\test\hello.c -o hello2.exe
   .\hello2.exe
   ```
6. Output of Phase 1: the verified subset list. Commit
   `tools/llvm-bundle/extract_minimal.ps1` and a sibling
   `tools/llvm-bundle/REQUIRED_FILES.md` documenting the closure.

### Phase 2 — Win.1b.B + Win.1b.C — CI integration

1. `.github/workflows/publish.yml` — add a new job step before
   the `build-native` job's "Package and upload" step:

   ```yaml
   - name: Cache LLVM redist bundle
     id: llvm-cache
     if: runner.os == 'Windows'
     uses: actions/cache@v4
     with:
       path: .tmp-llvm
       key: llvm-redist-${{ env.LLVM_VERSION }}
     env:
       LLVM_VERSION: "18.1.8"

   - name: Download + extract LLVM (cache miss)
     if: runner.os == 'Windows' && steps.llvm-cache.outputs.cache-hit != 'true'
     shell: bash
     env:
       LLVM_VERSION: "18.1.8"
     run: |
       mkdir -p .tmp-llvm && cd .tmp-llvm
       url="https://github.com/llvm/llvm-project/releases/download/llvmorg-${LLVM_VERSION}/LLVM-${LLVM_VERSION}-win64.exe"
       curl -fL -o llvm.exe "$url"
       7z x llvm.exe -oLLVM
       rm llvm.exe

   - name: Stage LLVM minimal subset for redistribution
     if: runner.os == 'Windows'
     shell: pwsh
     run: |
       ./tools/llvm-bundle/extract_minimal.ps1 `
         -LlvmDir .tmp-llvm/LLVM `
         -OutDir dist/mapanare-win-x64/bin/llvm

   - name: Verify bundled clang runs
     if: runner.os == 'Windows'
     shell: pwsh
     run: |
       dist/mapanare-win-x64/bin/llvm/clang.exe --version
       # Compile a smoke program with the bundle isolated from PATH:
       $env:PATH = "C:\Windows\System32;C:\Windows"
       echo 'int main(){return 0;}' > smoke.c
       dist/mapanare-win-x64/bin/llvm/clang.exe smoke.c -o smoke.exe
       ./smoke.exe; echo "exit: $LASTEXITCODE"
   ```

2. The existing "Package and upload" step needs to ZIP the
   `dist/mapanare-win-x64/` directory (which now includes
   `bin/mnc.exe` + `bin/llvm/*` + `LICENSE` + `README`).
   Adjust the artifact name from `mnc-win-x64.exe` (line 338)
   to `mapanare-win-x64.zip` to match install.ps1's expected
   asset name (`install.ps1:15`).

3. Publish BOTH ZIPs from the same release:
   - `mapanare-win-x64.zip` (with bundled LLVM, ~80-100 MB)
   - `mapanare-win-x64-minimal.zip` (without LLVM, ~10 MB) —
     for users who want the small version
   The minimal ZIP is cheap to produce: `Compress-Archive` over
   `dist/mapanare-win-x64/` minus the `bin/llvm/` subdirectory.

### Phase 3 — Win.1b.D — `mnc` bundled-toolchain detection

1. Verify `__mn_executable_dir()` (or equivalent) exists in the
   C runtime. Probe:
   ```bash
   grep -n "executable_dir\|exe_dir\|__mn_argv0" runtime/native/mapanare_core.c
   ```
   If absent, add a new export `__mn_executable_dir() -> String`:
   ```c
   const char *__mn_executable_dir(void) {
       static char path[4096];
       static int initialized = 0;
       if (!initialized) {
   #ifdef _WIN32
           GetModuleFileNameA(NULL, path, sizeof(path));
   #elif defined(__APPLE__)
           uint32_t size = sizeof(path);
           _NSGetExecutablePath(path, &size);
   #else
           ssize_t n = readlink("/proc/self/exe", path, sizeof(path) - 1);
           if (n > 0) path[n] = '\0';
   #endif
           // Strip the basename:
           char *slash = strrchr(path, '/');
           char *bslash = strrchr(path, '\\');
           if (bslash > slash) slash = bslash;
           if (slash) *slash = '\0';
           initialized = 1;
       }
       return path;
   }
   ```
   Expose to Mapanare per the v5.8.6 We.1 / v5.9.0 DX.2 export
   pattern.

2. Helper in `mapanare/self/main.mn`:
   ```mn
   fn find_clang() -> String {
       // Prefer bundled LLVM (v5.10.0 Win.1b):
       let exe_dir: String = __mn_executable_dir()
       let bundled: String = exe_dir + "/llvm/clang.exe"
       if __mn_path_exists(bundled) {
           return bundled
       }
       let bundled_unix: String = exe_dir + "/llvm/clang"
       if __mn_path_exists(bundled_unix) {
           return bundled_unix
       }
       // Fall back to PATH clang (v5.9.0 DX.3 detection runs separately):
       return "clang"
   }
   ```

3. Update each clang shell-out site to use `find_clang()`:
   - `main.mn:416` — `run_test`
   - `main.mn:525-526` — `run_build`
   - `main.mn:567, 571` — `run_program`
   - `main.mn:631` — `run_compile`
   - `main.mn:690` — `run_compile` (foreign source)
   ```mn
   let clang_bin: String = find_clang()
   let clang_cmd: String = clang_bin + " -c -O2 ... " + __mn_dev_null_redirect()
   ```

4. v5.9.0's `check_clang_available()` becomes
   `check_clang_available()` checking `find_clang()`'s result —
   if the bundled clang exists, the probe succeeds without
   PATH. If neither bundled nor PATH clang exists, fall through
   to v5.9.0's install-help message.

### Phase 4 — Win.1b.F — install.ps1 ZIP layout + verification

1. Update `packaging/install.ps1`:

   a. Honor `MAPANARE_NO_BUNDLED_LLVM`:
   ```powershell
   $UseBundledLlvm = -not $env:MAPANARE_NO_BUNDLED_LLVM
   $Artifact = if ($UseBundledLlvm) {
       "mapanare-win-x64.zip"
   } else {
       "mapanare-win-x64-minimal.zip"
   }
   ```

   b. After extraction, detect bundle presence + adjust message:
   ```powershell
   $LlvmBundle = Join-Path $InstallDir "llvm\clang.exe"
   if (Test-Path $LlvmBundle) {
       Write-Host "  LLVM toolchain: bundled (no separate install needed)"
   } else {
       Write-Host "  LLVM toolchain: NOT bundled — install via 'winget install LLVM.LLVM' if needed"
   }
   ```

   c. Update download size message to set expectations:
   ```powershell
   if ($UseBundledLlvm) {
       Write-Host "  Download:  ~90 MB (Mapanare + bundled LLVM)"
   } else {
       Write-Host "  Download:  ~10 MB (Mapanare only — clang required separately)"
   }
   ```

2. Update `packaging/install.sh` for parity (no actual bundling
   on Linux/macOS, but the script's getting-started message
   should reflect v5.10.0 reality).

3. Manual verification on a clean Windows VM:
   ```powershell
   # Default install (bundled):
   irm https://github.com/Mapanare-Research/Mapanare/releases/download/v5.10.0/install.ps1 | iex
   mnc run hello.mn   # Works without any LLVM separately installed.

   # Minimal install:
   $env:MAPANARE_NO_BUNDLED_LLVM = "1"
   irm https://github.com/Mapanare-Research/Mapanare/releases/download/v5.10.0/install.ps1 | iex
   mnc run hello.mn   # Prints v5.9.0 DX.3 install-help message.
   ```

### Phase 5 — Win.1b.E — LICENSE + redistribution compliance

1. Confirm LLVM's redistribution license terms. As of LLVM
   18.x: **Apache 2.0 with LLVM Exception** (replaces the
   previous "Illinois/NCSA OSL"). Distribution of compiled
   binaries requires:
   - LICENSE.TXT shipped alongside the binaries
   - No requirement to disclose source, no copyleft
   - The LLVM Exception explicitly permits "linking
     output object files" (i.e. clang's output) without
     copyleft propagation
2. Phase 1's `extract_minimal.ps1` already copies LICENSE.TXT
   into `dist/.../bin/llvm/`. Verify it's the right file
   (LLVM's main LICENSE.TXT, not a sub-component license).
3. Add `dist/mapanare-win-x64/THIRD-PARTY-LICENSES.md`:
   ```markdown
   # Third-Party Licenses

   This Mapanare distribution bundles software from third parties.
   Their licenses are reproduced below.

   ## LLVM Project (clang, lld-link, LLVM-C)

   Located at: `bin/llvm/`
   Version: 18.1.8
   License: Apache 2.0 with LLVM Exception
   See: `bin/llvm/LICENSE.TXT`

   The LLVM project is © the LLVM contributors. Mapanare
   redistributes compiled binaries of clang, lld-link, and
   their required runtime libraries unmodified, as permitted
   by the Apache 2.0 with LLVM Exception license. No source
   modifications are made.
   ```
4. Update `README.md` to mention bundled LLVM in the install
   section: "Windows installs include a bundled LLVM toolchain;
   no separate install needed. See `THIRD-PARTY-LICENSES.md`
   for license details."

### Phase 6 — Win.1b.G + validation matrix + release-size audit

1. New CI smoke job — `.github/workflows/publish.yml`:
   ```yaml
   windows-bundled-llvm-smoke:
     needs: [release, build-native]
     runs-on: windows-latest
     steps:
       - uses: actions/checkout@v4
       - name: Download published ZIP
         shell: pwsh
         run: |
           gh release download v${{ needs.release.outputs.new_version }} `
             -p mapanare-win-x64.zip -O mapanare.zip
         env:
           GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
       - name: Extract + smoke test
         shell: pwsh
         run: |
           Expand-Archive mapanare.zip -DestinationPath out
           # Strip user PATH to ensure ONLY bundled clang is used:
           $env:PATH = "C:\Windows\System32;C:\Windows"
           # Make a hello-world program:
           "fn main() { print(\"Hello, world!\") }" > hello.mn
           ./out/mapanare/bin/mnc.exe run hello.mn
           if ($LASTEXITCODE -ne 0) { throw "Bundled clang test failed" }
   ```
2. Release-size audit:
   ```bash
   ls -la dist/mapanare-win-x64.zip dist/mapanare-win-x64-minimal.zip
   # Targets:
   # mapanare-win-x64.zip:        80-100 MB
   # mapanare-win-x64-minimal.zip: ~10 MB
   ```
   If the bundled ZIP exceeds 150 MB, return to Phase 1 and
   tighten the minimal subset.
3. Standard validation:
   - `make lint` clean
   - Goldens 66/66 preserved (this release should not affect
     compiler IR; gate on byte-identical IR diff vs v5.9.0)
   - Sanitizer matrix unchanged (this release adds runtime
     surface only via `__mn_executable_dir`; small)
4. Bootstrap seed: refresh (Bb.4) IF Phase 3 added new C-runtime
   exports (`__mn_executable_dir`, `__mn_path_exists`). Otherwise
   skip.

---

## Decisions

### Decision 1: which LLVM version to pin?

**Recommendation: LLVM 18.1.8.** Rationale:
- Latest stable in the 18.x series (as of 2026-04).
- Mapanare's existing CI uses `llvm-18` on Linux and
  `brew install llvm@18` on macOS (per `publish.yml:359, 362`),
  so the bundled Windows version matches.
- ABI stable enough that LLVM 19 isn't a forced upgrade for
  another year+ (LLVM ships annually; 19 came in late 2024,
  20 in late 2025).
- Avoid 17.x (older, missing some target improvements) and
  19+ (newer, larger bundle, marginally improved features
  Mapanare doesn't use yet).

Pin in **one place**: an env var at the top of `publish.yml`,
referenced by every download step. Bumping LLVM is then a
single-line edit. Document the bump cadence: "Bump LLVM annually
in the first patch release after the new LLVM stable lands;
test on a side branch before merging."

### Decision 2: bundle `lld-link.exe` separately or rely on `clang -o` driver?

The `clang.exe -o foo.exe foo.c` invocation invokes the linker
internally. On Windows, `clang.exe` calls `lld-link.exe` via the
in-process driver path (or falls back to looking it up next to
itself).

**Recommendation: bundle `lld-link.exe` explicitly.** clang's
in-process linker call expects to find `lld-link.exe` in the
same directory or via PATH. If it's missing, clang errors with
a confusing "ld-link not found" message that doesn't help users.
Bundling it is ~3-5 MB extra; cheap insurance.

### Decision 3: ZIP-or-installer for the bundle?

**Recommendation: stay with ZIP.** install.ps1 already handles
ZIP extraction + PATH setup + version detection. Adding an
NSIS or WiX installer to wrap a ZIP that already works adds
~3 days of Windows-installer plumbing for marginal UX gain.
Defer NSIS/WiX indefinitely; the `irm | iex` install path is
already a "one-liner" experience.

If a real demand signal arrives (multiple users asking for
Start Menu shortcuts, file association, "Add/Remove Programs"
entry), open a v5.11.0 NSIS slot at that point.

### Decision 4: macOS / Linux bundling — defer or include?

**Recommendation: defer to v5.10.x or never.** The user's pain
point is Windows (no system clang by default). On macOS, every
developer has Apple clang via `xcode-select --install` (or full
Xcode); on Linux, `apt install clang` or equivalent is one
command and standard. Bundling there:
- Adds bytes (clang for Linux/macOS is comparable to Windows
  size)
- Doesn't solve real pain
- Risks the bundled clang vs system clang mismatch (Linux
  users get linker errors when the bundled clang's libstdc++
  doesn't match the system one)

Track as a deferred item in `docs/known_issues.md` with the
rationale. Revisit if a demand signal emerges.

### Decision 5: bump VERSION immediately or last?

**Recommendation: last.** Same as v5.8.8 / v5.9.0 — bump after
Phase 6 validation passes.

### Decision 6: `mapanare-win-x64.zip` (default = bundled) vs `mapanare-win-x64-bundled.zip` (explicit)?

The current install.ps1 expects an asset named
`mapanare-win-x64.zip` (`install.ps1:15`). Two options:
- **A:** keep that name; it now means "with bundle." Add
  `mapanare-win-x64-minimal.zip` as the new opt-in.
- **B:** rename to `mapanare-win-x64-bundled.zip`; `mapanare-win-x64.zip`
  becomes the small version; install.ps1 default switches.

**Recommendation: A.** Existing install.ps1 invocations
(documented in install.ps1's header and in README) point at
the existing asset name. Changing it forces every doc + every
user's bookmarked install command to break. The new "default
includes the bundle" semantic is the v5.10.0 announcement.

---

## What ships in v5.10.0

- **Source changes:**
  - `runtime/native/mapanare_core.c` — `__mn_executable_dir()`
    export (and `__mn_path_exists` if not added in v5.9.0)
  - `mapanare/emit_llvm_text.py` — runtime decl block updated
  - `mapanare/self/emit_llvm.mn` — same, parallel
  - `mapanare/self/main.mn` — `find_clang()` helper, every
    clang shell-out updated to use it
  - `tools/llvm-bundle/extract_minimal.ps1` (new)
  - `tools/llvm-bundle/REQUIRED_FILES.md` (new)
  - `.github/workflows/publish.yml` — LLVM cache step,
    download-and-extract step, stage-bundle step,
    verify-bundle step, two-ZIP packaging,
    `windows-bundled-llvm-smoke` job
  - `packaging/install.ps1` — `MAPANARE_NO_BUNDLED_LLVM` env
    var support, bundle-presence detection, updated messages
  - `dist/mapanare-win-x64/THIRD-PARTY-LICENSES.md` (new,
    generated/staged)
- **Docs:**
  - `docs/roadmap/v5/v5.10.0/PLAN.md` (this file)
  - `docs/roadmap/v5/v5.10.0/PROMPT.md` (gitignored)
  - `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md`
  - `CHANGELOG.md` — `[5.10.0]` block
  - `docs/known_issues.md` — Win.1b.* rows added then closed
  - `CLAUDE.md` release-history bullet
  - `README.md` — install section updated to mention bundled
    LLVM on Windows
- **Bootstrap:**
  - **Bb.4 seed refresh** if Phase 3 added new exports.
- **Version:** 5.9.0 → 5.10.0 at end of Phase 6.
- **Release artifacts:**
  - `mapanare-win-x64.zip` (~80-100 MB, with bundled LLVM)
  - `mapanare-win-x64-minimal.zip` (~10 MB, without)
  - existing Linux + macOS artifacts unchanged

## What does NOT ship in v5.10.0

- **macOS bundled toolchain.** Per Decision 4. macOS users
  have Apple clang.
- **Linux bundled toolchain.** Per Decision 4. Linux users
  have package manager.
- **NSIS / WiX Windows installer.** Per Decision 3. install.ps1
  + bundled ZIP covers the pain.
- **Start Menu shortcuts, .mn file association, Add/Remove
  Programs entry.** These are NSIS-specific gains; deferred
  with the installer.
- **Bundling other tools** (e.g. lldb for debugging, llvm-objdump
  for inspection). Out of scope. If users want full LLVM, they
  install it separately.
- **Compiler / parser / semantic / MIR / lower / emitter
  changes.** Zero. v5.10.0 is packaging-only. If any item drifts
  into compiler internals, split to a v5.10.x follow-up.
- **LLVM 19+ bundle.** Per Decision 1. Stay on 18.1.8 until LLVM
  19 has a year of stability + Mapanare needs a 19+ feature.

---

## Risk register

| ID | Risk | Mitigation |
|---|---|---|
| Win.1b.R1 | Phase 1's minimal-subset extraction misses a DLL that clang loads lazily (e.g. only when targeting a specific architecture). User's `mnc run` works for hello-world but breaks on real programs. | Phase 6's smoke test compiles only a trivial program. **Add a more complex smoke** that exercises the runtime: pthreads (Mapanare's agent runtime), libm functions (math), file I/O. If the smoke passes those, lazy-load DLLs are likely covered. Keep the smoke set in `tools/llvm-bundle/smoke_tests/`. |
| Win.1b.R2 | LLVM 18.1.8 download URL changes (llvm.org reorg, GitHub release retraction). | actions/cache means we only download once per cache-key lifetime. If llvm.org URL breaks, the pinned cache key still resolves. Document a "regenerate cache" procedure: bump the cache key, force a fresh download. |
| Win.1b.R3 | Bundled clang version drifts from system clang on user's other tools. User's IDE shows clang 17 errors but bundled clang 18 succeeds (or vice versa). | Document the bundled version in `mnc --version` output: `mapanare 5.10.0 (bundled LLVM 18.1.8)`. Users can identify the mismatch quickly. |
| Win.1b.R4 | Apache 2.0 with LLVM Exception interpretation: do we need to ship modified-source notice if clang's output (the user's compiled .exe) is "modified" via Mapanare's IR processing? | No. The LLVM Exception explicitly permits this. Apache 2.0 only requires source disclosure if WE modify clang itself. We don't — we redistribute upstream binaries unmodified. Phase 5's THIRD-PARTY-LICENSES.md says so explicitly. |
| Win.1b.R5 | Bundle size exceeds 100 MB despite Phase 1's minimal extraction. clang's `LLVM-C.dll` is ~80 MB at LLVM 18; with required DLLs + clang.exe + lld-link.exe, total may run 100-150 MB. | Set the alarm at 150 MB, not 100 MB. 150 MB is well within GitHub's 2 GB asset limit and within typical Windows install sizes (Python 3.12 installer is ~30 MB, but Visual Studio is ~10 GB). 150 MB is fine. If concerned: drop `lld-link.exe` and rely on system linker (verify Phase 1 step 5 with --target=x86_64-w64-mingw32 and gcc as linker). |
| Win.1b.R6 | Phase 3's `find_clang()` looks up bundled clang relative to the binary's exe directory, but `__mn_executable_dir()` returns a different path on Windows (e.g. `C:\Users\Foo\AppData\Local\Mapanare\bin` vs `C:\Users\Foo\AppData\Local\Mapanare`). | Test exhaustively: install via install.ps1 to default location, install to non-default location via `$env:MAPANARE_INSTALL_DIR`, install to a path with spaces, install to a UNC path. The `__mn_executable_dir()` Windows implementation must handle all of these. The test for Phase 3 should run from each. |
| Win.1b.R7 | Cache hit returns a stale LLVM bundle (someone tampered with the cache via a forced-refresh). | actions/cache is per-repo; only repo collaborators with workflow-write can taint it. Low risk for an open project. If caught, bump the cache key (forces fresh download). |
| Win.1b.R8 | install.ps1's `MAPANARE_NO_BUNDLED_LLVM` env var is read post-Bug fix — but the `$Artifact` derivation happens BEFORE `Get-ChildItem` on the install dir, so we can't detect "bundle is already there from a prior install" and skip the smaller-ZIP download. | Acceptable trade-off. install.ps1 is a one-shot installer; users invoking it expect a fresh download. If user wants to skip the LLVM download but already has the bundle, they're an edge case — direct them to `mapanare-up.ps1` (the updater) or to manually delete the install dir first. |
| Win.1b.R9 | Phase 2's two-ZIP packaging step adds significant CI runtime (200+ MB of artifact uploading per release). | upload time on GitHub-hosted runners is typically 5-10 MB/s; 200 MB = ~30s. Negligible in the context of a 5-10 minute publish workflow. |
| Win.1b.R10 | LLVM 18.1.8 is removed from llvm.org's GitHub release after some yearly-cleanup policy. | Mirror the LLVM Windows release in our own GitHub release (`v5.10.0` itself, as a build artifact named `llvm-redist-18.1.8-win64.exe`). Cache step downloads from our mirror first, llvm.org fallback. Deferred work; do only if the upstream actually disappears. |

---

## Closure checklist for v5.10.0

### Phase 1 (minimal subset)

- [ ] LLVM 18.1.8 downloaded + extracted on a Windows host
- [ ] `dumpbin /dependents` closure captured for `clang.exe`,
      `lld-link.exe`
- [ ] `tools/llvm-bundle/extract_minimal.ps1` produces a working
      bundle from a fresh LLVM install
- [ ] Bundle size ≤ 150 MB (target 100; alarm 150)
- [ ] `tools/llvm-bundle/REQUIRED_FILES.md` lists the closure
- [ ] Verification: bundled clang compiles + runs a hello-world
      C program with PATH stripped

### Phase 2 (CI integration)

- [ ] `actions/cache@v4` step keyed on `LLVM_VERSION`
- [ ] Download-and-extract step runs only on cache miss
- [ ] Stage-bundle step copies into
      `dist/mapanare-win-x64/bin/llvm/`
- [ ] Verify-bundle step runs `clang.exe --version` in CI
- [ ] Both ZIPs published from the same release
      (`mapanare-win-x64.zip` + `mapanare-win-x64-minimal.zip`)

### Phase 3 (mnc detection)

- [ ] `__mn_executable_dir()` exported from
      `runtime/native/mapanare_core.c` (added if missing,
      verified if present)
- [ ] `find_clang()` helper added to `mapanare/self/main.mn`
- [ ] Every clang shell-out site uses `find_clang()`
- [ ] v5.9.0's `check_clang_available()` updated to probe
      `find_clang()` result, not bare `clang`
- [ ] Bootstrap seed refreshed (Bb.4) if new exports added

### Phase 4 (install.ps1)

- [ ] `MAPANARE_NO_BUNDLED_LLVM` env var honored
- [ ] Bundle-presence detection in install.ps1's success
      message
- [ ] Download-size message reflects bundle vs minimal
- [ ] `packaging/install.sh` updated for parity

### Phase 5 (license)

- [ ] LLVM `LICENSE.TXT` copied into bundle by
      `extract_minimal.ps1`
- [ ] `dist/mapanare-win-x64/THIRD-PARTY-LICENSES.md` staged
- [ ] `README.md` install section mentions bundled LLVM +
      license

### Phase 6 (validation + smoke)

- [ ] `windows-bundled-llvm-smoke` job runs against published
      ZIP and passes
- [ ] Release-size audit: `mapanare-win-x64.zip` ≤ 150 MB
- [ ] `make lint` clean
- [ ] `make test` non-bootstrap pytest: 0 failures
- [ ] Goldens 66/66 preserved
- [ ] 5+ representative goldens byte-identical IR vs v5.9.0
- [ ] `bash scripts/verify_fixed_point.sh` NEAR or strict
- [ ] `check_struct_registry.py` clean
- [ ] Sanitizer matrix — no new regressions vs v5.9.0
- [ ] Bootstrap seed: clean OR refreshed (Bb.4)
- [ ] Manual Windows VM smoke: fresh install, both ZIPs,
      bundled + minimal paths

### Documentation + release

- [ ] `CHANGELOG.md` `[5.10.0]` block — emphasize bundled
      LLVM as the headline + zero-deps install for Windows
- [ ] `docs/known_issues.md` Win.1b.* rows flipped to CLOSED
- [ ] `CLAUDE.md` release-history bullet
- [ ] `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md`
- [ ] `VERSION` bumped 5.9.0 → 5.10.0
- [ ] `git tag v5.10.0` per user-approval-required rule

---

## What this plan trusts vs. what it gates

**Trusts:**
- LLVM 18.1.8 is Apache 2.0 with LLVM Exception (verified;
  see https://llvm.org/docs/DeveloperPolicy.html#new-llvm-project-license-framework).
- Redistribution of compiled clang.exe binaries unmodified is
  permitted by that license, requiring only LICENSE.TXT inclusion.
- GitHub Actions caches persist for 7+ days at the cache key
  level; weekly publishes hit the cache reliably.
- `dumpbin /dependents` accurately enumerates DLL load
  dependencies for clang.exe (it does, but doesn't catch
  lazy LoadLibrary calls — Phase 6's smoke test handles those).
- `actions/cache@v4` Windows path handling works for the
  `.tmp-llvm` directory (it does; tested in publish.yml's
  existing w64devkit caching).
- 100 MB extra in the Windows release ZIP is acceptable to
  users (it is — Python's installer is comparable; Rust's
  is larger).

**Gates on Phase validation:**
- The minimal subset (Phase 1) actually compiles and runs
  Mapanare-emitted IR, not just trivial C programs. Phase 6
  smoke test gates this with hello.mn (Mapanare program, not
  C program).
- Phase 3's `find_clang()` returns the bundled path on a
  fresh install AND on installs to non-default directories.
  Phase 4's manual smoke test gates this.
- Phase 2's release-size audit holds at ≤ 150 MB. If exceeded,
  return to Phase 1 and tighten.
- Bootstrap seed Bb.4 refreshes cleanly. If it doesn't, the
  release is blocked until the seed issue is resolved (same
  posture as v5.8.5/v5.8.6/v5.9.0 seed refreshes).

---

## Cross-version coordination

- **v5.9.0 dependencies (must ship first):**
  - DX.3 (clang-missing detection) — v5.10.0's `find_clang()`
    layers on top.
  - DX.6 (`mnc` vs `mapanare.exe` canonical name) — v5.10.0
    extends install.ps1 with the canonical name settled.

- **v5.10.0 → v5.11.0+ leftover:**
  - macOS / Linux bundling (deferred per Decision 4)
  - NSIS / WiX installer (deferred per Decision 3)
  - LLVM 19+ bundle (per Decision 1, when the time comes)
  - Bundled lldb / llvm-objdump for advanced users (deferred)

- **Independent of v5.8.8 (Apple AArch64):** zero overlap.
  v5.8.8 touches compiler ABI; v5.10.0 touches packaging.

---

## Footnote: what makes this release "safe"

Three properties make this a low-risk packaging release:

1. **Additive:** existing users (with their own LLVM) see no
   behavior change. The bundled clang is preferred only if
   present; absence falls through to PATH lookup, which falls
   through to v5.9.0's install-help message. Worst case: a
   user with the bundle installed gets the bundled clang
   instead of their PATH clang — both should produce identical
   results for Mapanare's invocations.
2. **Reversible:** if the bundle proves problematic in the
   wild, ship v5.10.1 with the bundle disabled by default
   (swap install.ps1 default to point at `-minimal.zip`).
   Users can fix locally by deleting `bin/llvm/`.
3. **No compiler changes:** v5.10.0 doesn't touch parser,
   semantic, MIR, lower, optimizer, or emitter. Compiler
   correctness is unchanged. Only the dispatch layer's clang
   resolution changes, and that's ~20 LOC behind a single
   helper function.
