# tools/llvm-bundle/extract_minimal.ps1
#
# v5.10.0 Win.1b — extract the minimal LLVM redistributable subset
# Mapanare's Windows release ships at <install>/bin/llvm/. Pinned to
# LLVM 18.1.8.
#
# Inputs:
#   -LlvmDir   path to an extracted LLVM-18.1.8-win64 tree (must
#              contain bin/clang.exe + LICENSE.TXT)
#   -OutDir    destination — copies the minimal subset here
#
# Output: $OutDir contains clang.exe + lld-link.exe + LLVM-C.dll +
# clang_rt.builtins-x86_64.lib + LICENSE.TXT.
#
# Smoke-tests the bundle by compiling a hello-world C program with
# PATH stripped to system DLLs only — catches lazy-load DLL closure
# gaps that dumpbin alone misses.

param(
    [string]$LlvmDir = ".\LLVM",
    [string]$OutDir  = ".\dist\bundle"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $LlvmDir)) {
    throw "LlvmDir not found: $LlvmDir"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# ---------------------------------------------------------------------
# Required binaries — closure determined by:
#   dumpbin /dependents bin\clang.exe
#   dumpbin /dependents bin\lld-link.exe
# Re-run on each LLVM bump and update tools/llvm-bundle/REQUIRED_FILES.md.
# ---------------------------------------------------------------------
$RequiredBin = @(
    "clang.exe",      # ~5 MB — primary IR compiler + linker driver
    "lld-link.exe",   # ~4 MB — linker invoked by clang -o on Windows
    "LLVM-C.dll"      # ~80-90 MB — core LLVM library; dominates bundle size
)

foreach ($f in $RequiredBin) {
    $src = Join-Path $LlvmDir "bin\$f"
    if (-not (Test-Path $src)) {
        throw "Missing required file: $src"
    }
    Copy-Item $src -Destination (Join-Path $OutDir $f)
}

# compiler-rt builtins — path varies by LLVM version layout. LLVM 18
# ships them at lib/clang/18/lib/windows/. Glob covers minor version
# bumps without rewriting this script.
$CompilerRt = Get-ChildItem -Path (Join-Path $LlvmDir "lib\clang") `
                            -Filter "clang_rt.builtins-x86_64.lib" `
                            -Recurse -ErrorAction SilentlyContinue
if ($CompilerRt) {
    Copy-Item $CompilerRt[0].FullName `
              -Destination (Join-Path $OutDir "clang_rt.builtins-x86_64.lib")
} else {
    Write-Warning "compiler-rt builtins not found — some intrinsics may fail to link"
}

# License — Apache 2.0 with LLVM Exception requires LICENSE.TXT
# alongside redistributed binaries. Missing this is a license violation.
$LicenseSrc = Join-Path $LlvmDir "LICENSE.TXT"
if (-not (Test-Path $LicenseSrc)) {
    throw "LICENSE.TXT missing in $LlvmDir — required for Apache 2.0 + LLVM Exception compliance"
}
Copy-Item $LicenseSrc -Destination (Join-Path $OutDir "LICENSE.TXT")

# ---------------------------------------------------------------------
# Size audit
# ---------------------------------------------------------------------
$size_bytes = (Get-ChildItem $OutDir -Recurse | Measure-Object Length -Sum).Sum
$size_mb = [math]::Round($size_bytes / 1MB, 1)
Write-Host "Bundle size: $size_mb MB"
Write-Host "Files:"
Get-ChildItem $OutDir | ForEach-Object {
    $kb = [math]::Round($_.Length / 1KB, 0)
    Write-Host ("  {0,-40} {1,8} KB" -f $_.Name, $kb)
}

if ($size_mb -gt 150) {
    Write-Warning "Bundle exceeds 150 MB alarm threshold (target 100 MB)"
} elseif ($size_mb -gt 100) {
    Write-Warning "Bundle exceeds 100 MB target (alarm 150 MB)"
}

# ---------------------------------------------------------------------
# Smoke test — compile + run a hello-world with PATH stripped so any
# missing DLL surfaces here instead of in user installs.
# ---------------------------------------------------------------------
$smokeC   = Join-Path $env:TEMP "mapanare_bundle_smoke.c"
$smokeExe = Join-Path $env:TEMP "mapanare_bundle_smoke.exe"
Set-Content -Path $smokeC -Value "#include <stdio.h>`nint main(void){printf(`"ok\n`");return 0;}"

$prevPath = $env:PATH
$env:PATH = "C:\Windows\System32;C:\Windows"
try {
    & (Join-Path $OutDir "clang.exe") $smokeC -o $smokeExe
    if ($LASTEXITCODE -ne 0) { throw "clang invocation failed (exit $LASTEXITCODE)" }
    $smokeOut = & $smokeExe
    if ($smokeOut -ne "ok") { throw "smoke binary output mismatch: '$smokeOut'" }
    Write-Host "Smoke test: OK"
} finally {
    $env:PATH = $prevPath
    Remove-Item $smokeC, $smokeExe -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Bundle ready: $OutDir"
