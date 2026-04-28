# LLVM Bundle — Required Files

Mapanare's Windows release bundles a minimal LLVM redistributable
into `<install>/bin/llvm/` so users get a working `mnc run` without
installing clang separately. Pinned to LLVM 18.1.8.

`tools/llvm-bundle/extract_minimal.ps1` builds the bundle from a
fresh extracted LLVM tree. CI invokes it from
`.github/workflows/publish.yml`'s `build-cli` job (Win.1b.B/C).

## Files

| File | Source path | Approx size | Purpose |
|---|---|---:|---|
| `clang.exe` | `LLVM/bin/clang.exe` | 5 MB | IR compiler + linker driver |
| `lld-link.exe` | `LLVM/bin/lld-link.exe` | 4 MB | Linker invoked by `clang -o` on Windows |
| `LLVM-C.dll` | `LLVM/bin/LLVM-C.dll` | 80–90 MB | Core LLVM library; dominates bundle size |
| `clang_rt.builtins-x86_64.lib` | `LLVM/lib/clang/18/lib/windows/` | 1 MB | Compiler intrinsics (some Mapanare ops need these) |
| `LICENSE.TXT` | `LLVM/LICENSE.TXT` | 4 KB | Apache 2.0 + LLVM Exception — required by license |

**Total:** ~95 MB.

## Closure determination

Run on a Windows host:

```powershell
$LlvmVersion = "18.1.8"
$dumpbin = Get-ChildItem `
    "C:\Program Files\Microsoft Visual Studio\2022\*\VC\Tools\MSVC\*\bin\Hostx64\x64\dumpbin.exe" |
    Select-Object -First 1

& $dumpbin /dependents LLVM\bin\clang.exe
& $dumpbin /dependents LLVM\bin\lld-link.exe
```

Closure verified by the smoke test in `extract_minimal.ps1`, which
runs the bundled `clang.exe` against a hello-world C source with
PATH stripped to system DLLs only. Lazy-load DLLs missed by
`dumpbin` surface there.

## C runtime DLLs (`vcruntime140.dll`, `msvcp140.dll`)

The official `LLVM-18.1.8-win64.exe` from llvm.org is built with
MSVC, so its binaries depend on `vcruntime140.dll` and
`msvcp140.dll`. We do **NOT** bundle these — Microsoft's "Visual
C++ Redistributable" is preinstalled on Windows 10+ and bundling
risks DLL-hell with the user's other Microsoft software.

If a future Windows version (or the user's tooling state) lacks
the redistributable, the smoke test in `extract_minimal.ps1` will
fail in CI. At that point: bundle them via the `RequiredBin` array
in the script. They add ~3 MB total.

## Bumping the LLVM version

1. Bump the version literal in `.github/workflows/publish.yml`'s
   `LLVM_VERSION` env var
2. Re-run the dumpbin closure check above on the new version
3. Update this file's Size column if any file's size shifts more
   than 5 MB
4. Verify CI's `windows-bundled-llvm-smoke` job passes against the
   new bundle
5. Cadence: bump annually, in the first patch release after the new
   LLVM stable lands. Skip non-stable releases.

Pinning matters: a silent llvm.org URL change (mirror reorg, asset
removal) breaks our CI. The `actions/cache@v4` step cushions this
by retaining a valid cache against the pinned key.
