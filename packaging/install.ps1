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

# ---------- Add to PATH ----------
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    Write-Host "Adding $InstallDir to user PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
    $env:Path = "$env:Path;$InstallDir"
}

# ---------- Verify ----------
Write-Host ""
$MapanareBin = Join-Path $InstallDir "mapanare.exe"
if (Test-Path $MapanareBin) {
    Write-Host "Installed successfully!" -ForegroundColor Green
    Write-Host ""
    & $MapanareBin --version
    Write-Host ""
    Write-Host "Get started:"
    Write-Host "  mapanare init myproject"
    Write-Host "  cd myproject"
    Write-Host "  mapanare run main.mn       # compile & run"
    Write-Host "  mapanare check main.mn     # type-check only"
    Write-Host "  mapanare build main.mn     # native binary (requires LLVM)"
    Write-Host ""
    Write-Host "You may need to restart your terminal for PATH changes to take effect."
} else {
    Write-Host "Error: Installation failed - binary not found at $MapanareBin" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
