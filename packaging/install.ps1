# Mapanare Language Installer for Windows
# Usage:
#   irm https://mapanare.dev/install.ps1 | iex
#   $env:MAPANARE_VERSION = "v4.0.0"; irm https://mapanare.dev/install.ps1 | iex
#
# v5.12.0 Wk.*: Windows installs default to the SDK ZIP so `mnc run`
# and `mnc build` work on clean machines. Set either
# $env:MAPANARE_NO_BUNDLED_TOOLCHAIN = "1" or the legacy
# $env:MAPANARE_NO_BUNDLED_LLVM = "1" before invoking to download the
# app-only minimal ZIP instead.
param(
    [string]$Version = "",
    [string]$InstallDir = ""
)
$ErrorActionPreference = "Stop"

$Repo = "Mapanare-Research/Mapanare"
if (-not $InstallDir) {
    $InstallDir = if ($env:MAPANARE_INSTALL_DIR) { $env:MAPANARE_INSTALL_DIR } else { "$env:LOCALAPPDATA\Mapanare\bin" }
}

# v5.12.0 Wk.*: bundled SDK artifact selection.
$UseBundledToolchain = $true
if ($env:MAPANARE_NO_BUNDLED_LLVM -in @("1", "true", "yes", "TRUE", "YES")) {
    $UseBundledToolchain = $false
}
if ($env:MAPANARE_NO_BUNDLED_TOOLCHAIN -in @("1", "true", "yes", "TRUE", "YES")) {
    $UseBundledToolchain = $false
}

# ---------- Resolve version ----------
if (-not $Version) {
    $Version = if ($env:MAPANARE_VERSION) { $env:MAPANARE_VERSION } else { "latest" }
}
if ($Version -ne "latest" -and $Version -notmatch "^v") {
    $Version = "v$Version"
}

if ($Version -eq "latest") {
    Write-Host "Fetching latest release..."
    try {
        $Release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -UseBasicParsing
        $Version = $Release.tag_name
    } catch {
        Write-Host "Error: Could not determine latest version." -ForegroundColor Red
        Write-Host "Set `$env:MAPANARE_VERSION = 'vX.Y.Z'` to install a specific version."
        exit 1
    }
}

# v5.11.0 Pk.1: artifact filenames include the version. v5.12.0 adds
# the canonical SDK name and keeps mapanare-${VersionTag}-win-x64.zip
# plus mapanare-win-x64.zip as compatibility aliases for old scripts and
# old releases.
$VersionTag = $Version -replace '^v', ''
$CandidateArtifacts = if ($UseBundledToolchain) {
    @(
        "mapanare-${VersionTag}-win-x64-sdk.zip",
        "mapanare-${VersionTag}-win-x64.zip",
        "mapanare-win-x64.zip"
    )
} else {
    @(
        "mapanare-${VersionTag}-win-x64-minimal.zip",
        "mapanare-win-x64-minimal.zip"
    )
}

$Artifact = $null
$DownloadUrl = $null
foreach ($candidate in $CandidateArtifacts) {
    $candidateUrl = "https://github.com/$Repo/releases/download/$Version/$candidate"
    try {
        Invoke-WebRequest -Uri $candidateUrl -Method Head -UseBasicParsing -ErrorAction Stop | Out-Null
        $Artifact = $candidate
        $DownloadUrl = $candidateUrl
        break
    } catch {
        Write-Host "  Asset not found: $candidate" -ForegroundColor Yellow
    }
}
if (-not $Artifact) {
    Write-Host "Error: no compatible Windows artifact found for $Version." -ForegroundColor Red
    exit 1
}

# ---------- Download & install ----------
$ToolchainStatus = if ($UseBundledToolchain) { "Windows SDK bundled (no separate install needed)" } else { "NOT bundled - clang/gcc required separately" }
$DownloadSize = if ($UseBundledToolchain) { "SDK ZIP (Mapanare + Windows SDK, target <150 MB)" } else { "Minimal ZIP (Mapanare only, target <25 MB)" }
Write-Host ""
Write-Host "  Mapanare Language Installer" -ForegroundColor Cyan
Write-Host "  Version:   $Version"
Write-Host "  Platform:  windows-x64"
Write-Host "  Target:    $InstallDir"
Write-Host "  Toolchain: $ToolchainStatus"
Write-Host "  Download:  $DownloadSize"
Write-Host ""

$TmpDir = Join-Path $env:TEMP "mapanare-install-$(Get-Random)"
New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null
$ZipPath = Join-Path $TmpDir $Artifact

try {
    Write-Host "Downloading $Artifact..."
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath -UseBasicParsing
} catch {
    Write-Host ""
    Write-Host "Error: Download failed." -ForegroundColor Red
    Write-Host "  URL: $DownloadUrl"
    Write-Host ""
    Write-Host "Possible causes:"
    Write-Host "  - Version $Version may not exist"
    Write-Host "  - Check releases: https://github.com/$Repo/releases"
    Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "Extracting..."
Expand-Archive -Path $ZipPath -DestinationPath $TmpDir -Force

# Install
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

Copy-Item -Path "$TmpDir\mapanare\*" -Destination $InstallDir -Recurse -Force

# v5.9.0 DX.6: alias mapanare.exe -> mnc.exe so users can invoke either
# name. Pre-v5.9.0 the docs and the binary disagreed: README + native
# CLI used `mnc`, install.ps1 + bundle used `mapanare`. Both names now
# point to the same PyInstaller-bundled Python CLI; PyInstaller doesn't
# look at argv[0] for command parsing, so the alias is transparent.
$MapanareBin = Join-Path $InstallDir "mapanare.exe"
$MncBin = Join-Path $InstallDir "mnc.exe"
if ((Test-Path $MapanareBin) -and -not (Test-Path $MncBin)) {
    Copy-Item -Path $MapanareBin -Destination $MncBin -Force
}

# ---------- Add to PATH ----------
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    Write-Host "Adding $InstallDir to user PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
    $env:Path = "$env:Path;$InstallDir"
}

# ---------- Verify ----------
Write-Host ""
if (Test-Path $MncBin) {
    Write-Host "Installed successfully!" -ForegroundColor Green
    Write-Host ""
    & $MncBin --version
    Write-Host ""

    $BundledCompiler = @(
        (Join-Path $InstallDir "sdk\bin\clang.exe"),
        (Join-Path $InstallDir "llvm\bin\clang.exe"),
        (Join-Path $InstallDir "llvm\clang.exe")
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($BundledCompiler) {
        if ($BundledCompiler -like "*\sdk\bin\clang.exe") {
            Write-Host "Bundled Windows SDK ready: $BundledCompiler"
        } else {
            Write-Host "Bundled LLVM toolchain ready: $BundledCompiler"
        }
    } else {
        Write-Host "No bundled Windows SDK. Install a compiler separately if ``mnc run`` reports it missing:" -ForegroundColor Yellow
        Write-Host "  winget install MartinStorsjo.LLVM-MinGW.UCRT"
    }
    Write-Host ""
    Write-Host "Get started:"
    Write-Host "  mnc init myproject"
    Write-Host "  cd myproject"
    Write-Host "  mnc run main.mn       # compile and run"
    Write-Host "  mnc build main.mn     # build native binary"
    Write-Host "  mnc --help            # see all commands"
    Write-Host ""
    Write-Host "(``mapanare`` is also installed as an alias for ``mnc``.)"
    Write-Host "You may need to restart your terminal for PATH changes to take effect."
} else {
    Write-Host "Error: Installation failed - binary not found at $MncBin" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
