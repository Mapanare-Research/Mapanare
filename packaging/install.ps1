# Mapanare Language Installer for Windows
# Usage:
#   irm https://mapanare.dev/install.ps1 | iex
#   $env:MAPANARE_VERSION = "v4.0.0"; irm https://mapanare.dev/install.ps1 | iex
param(
    [string]$Version = "",
    [string]$InstallDir = ""
)
$ErrorActionPreference = "Stop"

$Repo = "Mapanare-Research/Mapanare"
if (-not $InstallDir) {
    $InstallDir = if ($env:MAPANARE_INSTALL_DIR) { $env:MAPANARE_INSTALL_DIR } else { "$env:LOCALAPPDATA\Mapanare\bin" }
}
$Artifact = "mapanare-win-x64.zip"

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

$DownloadUrl = "https://github.com/$Repo/releases/download/$Version/$Artifact"

# ---------- Download & install ----------
Write-Host ""
Write-Host "  Mapanare Language Installer" -ForegroundColor Cyan
Write-Host "  Version:  $Version"
Write-Host "  Platform: windows-x64"
Write-Host "  Target:   $InstallDir"
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
