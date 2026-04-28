# tools/llvm-mingw-bundle/extract_sdk.ps1
#
# v5.12.0 Wk.* - stage the curated LLVM-MinGW UCRT x86_64 SDK subset
# that lets Windows release ZIPs compile and link on clean machines.

param(
    [string]$LlvmMingwDir = ".\llvm-mingw-20260421-ucrt-x86_64",
    [string]$OutDir = ".\dist\mapanare\sdk"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $LlvmMingwDir)) {
    throw "LlvmMingwDir not found: $LlvmMingwDir"
}

if (Test-Path $OutDir) {
    Remove-Item -Recurse -Force $OutDir
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Copy-RequiredFile {
    param([string]$RelativePath)

    $src = Join-Path $LlvmMingwDir $RelativePath
    if (-not (Test-Path $src)) {
        throw "Missing required file: $src"
    }
    $dest = Join-Path $OutDir $RelativePath
    New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
    Copy-Item $src -Destination $dest -Force
}

function Copy-RequiredTree {
    param([string]$RelativePath)

    $src = Join-Path $LlvmMingwDir $RelativePath
    if (-not (Test-Path $src)) {
        throw "Missing required directory: $src"
    }
    $dest = Join-Path $OutDir $RelativePath
    New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
    Copy-Item $src -Destination $dest -Recurse -Force
}

$RequiredBin = @(
    "bin\clang.exe",
    "bin\clang-22.exe",
    "bin\x86_64-w64-mingw32-clang.exe",
    "bin\ld.lld.exe",
    "bin\llvm-ar.exe",
    "bin\llvm-ranlib.exe",
    "bin\llvm-strip.exe",
    "bin\ar.exe",
    "bin\libLLVM-22.dll",
    "bin\libclang-cpp.dll",
    "bin\libwinpthread-1.dll",
    "bin\libunwind.dll",
    "bin\libc++.dll",
    "LICENSE.TXT"
)

foreach ($f in $RequiredBin) {
    Copy-RequiredFile $f
}

Copy-RequiredTree "include"
Copy-RequiredTree "x86_64-w64-mingw32\lib"
Copy-RequiredTree "x86_64-w64-mingw32\bin"
Copy-RequiredTree "x86_64-w64-mingw32\share\mingw32"

$clangRoot = Join-Path $LlvmMingwDir "lib\clang"
$clangVersion = Get-ChildItem -Path $clangRoot -Directory |
    Sort-Object Name -Descending |
    Select-Object -First 1
if (-not $clangVersion) {
    throw "No lib\clang version directory found in $clangRoot"
}

$clangRel = "lib\clang\$($clangVersion.Name)"
Copy-RequiredTree "$clangRel\include"
Copy-RequiredFile "$clangRel\lib\windows\libclang_rt.builtins-x86_64.a"

# LLVM-MinGW's Windows clang driver invokes "ld" and looks for GNU-style
# libgcc names by default. The upstream ZIP provides ld.lld.exe,
# compiler-rt builtins, and libunwind instead, so stage compatibility
# aliases inside the SDK rather than relying on host PATH or extra CLI flags.
Copy-Item (Join-Path $OutDir "bin\ld.lld.exe") -Destination (Join-Path $OutDir "bin\ld.exe") -Force
Copy-Item (Join-Path $OutDir "$clangRel\lib\windows\libclang_rt.builtins-x86_64.a") `
    -Destination (Join-Path $OutDir "x86_64-w64-mingw32\lib\libgcc.a") -Force
Copy-Item (Join-Path $OutDir "x86_64-w64-mingw32\lib\libunwind.a") `
    -Destination (Join-Path $OutDir "x86_64-w64-mingw32\lib\libgcc_eh.a") -Force

$sizeBytes = (Get-ChildItem $OutDir -Recurse -File | Measure-Object Length -Sum).Sum
$sizeMb = [math]::Round($sizeBytes / 1MB, 1)
Write-Host "LLVM-MinGW SDK staged: $OutDir"
Write-Host "Uncompressed SDK subset size: $sizeMb MB"
Write-Host "Top-level contributors:"
Get-ChildItem $OutDir -Directory |
    ForEach-Object {
        $mb = [math]::Round(((Get-ChildItem $_.FullName -Recurse -File | Measure-Object Length -Sum).Sum) / 1MB, 1)
        Write-Host ("  {0,-24} {1,8} MB" -f $_.Name, $mb)
    }

$smokeC = Join-Path $env:TEMP "mapanare_llvm_mingw_sdk_smoke.c"
$smokeExe = Join-Path $env:TEMP "mapanare_llvm_mingw_sdk_smoke.exe"
Set-Content -Path $smokeC -Value "#include <stdio.h>`nint main(void){puts(`"ok`");return 0;}" -Encoding ASCII

$prevPath = $env:PATH
$prevLib = $env:LIB
$prevInclude = $env:INCLUDE
try {
    $env:PATH = (Join-Path $OutDir "bin") + ";C:\Windows\System32;C:\Windows"
    Remove-Item Env:LIB -ErrorAction SilentlyContinue
    Remove-Item Env:INCLUDE -ErrorAction SilentlyContinue

    & (Join-Path $OutDir "bin\clang.exe") $smokeC -o $smokeExe
    if ($LASTEXITCODE -ne 0) {
        throw "LLVM-MinGW clang smoke compile failed (exit $LASTEXITCODE)"
    }
    $smokeOut = & $smokeExe
    if ($LASTEXITCODE -ne 0) {
        throw "LLVM-MinGW smoke binary failed (exit $LASTEXITCODE)"
    }
    if ($smokeOut -ne "ok") {
        throw "LLVM-MinGW smoke output mismatch: '$smokeOut'"
    }
    Write-Host "LLVM-MinGW SDK smoke: OK"
} finally {
    $env:PATH = $prevPath
    if ($null -ne $prevLib) { $env:LIB = $prevLib } else { Remove-Item Env:LIB -ErrorAction SilentlyContinue }
    if ($null -ne $prevInclude) { $env:INCLUDE = $prevInclude } else { Remove-Item Env:INCLUDE -ErrorAction SilentlyContinue }
    Remove-Item $smokeC, $smokeExe -ErrorAction SilentlyContinue
}
