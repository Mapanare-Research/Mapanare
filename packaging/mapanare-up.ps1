# mapanare-up — Mapanare version manager for Windows
# Like pyenv but for Mapanare.
#
# Usage:
#   mapanare-up install <version|latest>
#   mapanare-up list
#   mapanare-up default <version>
#   mapanare-up current
#   mapanare-up uninstall <version>
#   mapanare-up help

param([string]$Command = "help", [string]$Arg = "")
$ErrorActionPreference = "Stop"

$Script:Version = "0.1.0"
$Repo = "Mapanare-Research/Mapanare"
$MapanareHome = if ($env:MAPANARE_HOME) { $env:MAPANARE_HOME } else { "$env:USERPROFILE\.mapanare" }
$VersionsDir = "$MapanareHome\versions"
$BinDir = "$MapanareHome\bin"
$DefaultFile = "$MapanareHome\default"

# Ensure directories
New-Item -ItemType Directory -Path $VersionsDir -Force | Out-Null
New-Item -ItemType Directory -Path $BinDir -Force | Out-Null

function Resolve-Latest {
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -UseBasicParsing
    return $release.tag_name -replace '^v', ''
}

function Strip-V { param([string]$v) return $v -replace '^v', '' }
function Ensure-V { param([string]$v) if ($v -match '^v') { return $v } else { return "v$v" } }

function Cmd-Install {
    param([string]$ver)

    if ($ver -eq "latest") {
        Write-Host "Resolving latest version..."
        $ver = Resolve-Latest
        Write-Host "Latest: $ver"
    }

    $verClean = Strip-V $ver
    $verTag = Ensure-V $ver
    $dest = "$VersionsDir\$verClean"

    if ((Test-Path "$dest\mapanare.exe") -or (Test-Path "$dest\mnc.exe")) {
        Write-Host "Version $verClean is already installed."
        return
    }

    $artifact = "mapanare-win-x64.zip"
    $url = "https://github.com/$Repo/releases/download/$verTag/$artifact"

    Write-Host ""
    Write-Host "  mapanare-up install" -ForegroundColor Cyan
    Write-Host "  Version:  $verClean"
    Write-Host "  Platform: windows-x64"
    Write-Host ""

    $tmp = Join-Path $env:TEMP "mapanare-up-$(Get-Random)"
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null

    try {
        Write-Host "Downloading $artifact..."
        Invoke-WebRequest -Uri $url -OutFile "$tmp\$artifact" -UseBasicParsing

        Write-Host "Extracting..."
        Expand-Archive -Path "$tmp\$artifact" -DestinationPath $tmp -Force

        New-Item -ItemType Directory -Path $dest -Force | Out-Null
        Copy-Item -Path "$tmp\mapanare\*" -Destination $dest -Recurse -Force

        if (-not (Test-Path $DefaultFile)) {
            Set-Content -Path $DefaultFile -Value $verClean
            Write-Host "Set $verClean as default (first install)"
        }

        Write-Host ""
        Write-Host "Installed Mapanare $verClean to $dest" -ForegroundColor Green
    } finally {
        Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
    }

    # Add bin to PATH if not already
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$BinDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$BinDir", "User")
        $env:Path = "$env:Path;$BinDir"
        Write-Host "Added $BinDir to PATH. Restart your terminal for it to take effect."
    }
}

function Cmd-List {
    $defaultVer = if (Test-Path $DefaultFile) { Get-Content $DefaultFile } else { "" }

    $versions = Get-ChildItem -Path $VersionsDir -Directory -ErrorAction SilentlyContinue
    if (-not $versions) {
        Write-Host "No versions installed. Run: mapanare-up install latest"
        return
    }

    Write-Host "Installed versions:"
    Write-Host ""
    foreach ($v in $versions) {
        if ($v.Name -eq $defaultVer) {
            Write-Host "  * $($v.Name) (default)"
        } else {
            Write-Host "    $($v.Name)"
        }
    }
}

function Cmd-Default {
    param([string]$ver)
    $verClean = Strip-V $ver
    if (-not (Test-Path "$VersionsDir\$verClean")) {
        Write-Host "Error: Version $verClean is not installed." -ForegroundColor Red
        return
    }
    Set-Content -Path $DefaultFile -Value $verClean
    Write-Host "Default set to $verClean"
}

function Cmd-Current {
    # Walk up for .mapanare-version
    $d = Get-Location
    while ($d -and $d.Path -ne [System.IO.Path]::GetPathRoot($d.Path)) {
        $vf = Join-Path $d.Path ".mapanare-version"
        if (Test-Path $vf) {
            $v = Get-Content $vf
            Write-Host "$v (via .mapanare-version)"
            return
        }
        $d = Split-Path $d.Path -Parent | Get-Item -ErrorAction SilentlyContinue
    }
    if ($env:MAPANARE_VERSION) {
        Write-Host "$env:MAPANARE_VERSION (via `$MAPANARE_VERSION)" ; return
    }
    if (Test-Path $DefaultFile) {
        $v = Get-Content $DefaultFile
        Write-Host "$v (default)" ; return
    }
    Write-Host "No active version. Run: mapanare-up install latest"
}

function Cmd-Uninstall {
    param([string]$ver)
    $verClean = Strip-V $ver
    $dest = "$VersionsDir\$verClean"
    if (-not (Test-Path $dest)) {
        Write-Host "Error: Version $verClean is not installed." -ForegroundColor Red
        return
    }
    Remove-Item -Recurse -Force $dest
    Write-Host "Uninstalled Mapanare $verClean"
    if ((Test-Path $DefaultFile) -and ((Get-Content $DefaultFile) -eq $verClean)) {
        Remove-Item $DefaultFile
        Write-Host "Warning: $verClean was the default. Run 'mapanare-up default <version>' to set a new one." -ForegroundColor Yellow
    }
}

function Cmd-Help {
    Write-Host "mapanare-up $Script:Version - Mapanare version manager" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  mapanare-up install <version|latest>   Install a version"
    Write-Host "  mapanare-up list                       List installed versions"
    Write-Host "  mapanare-up default <version>          Set the global default"
    Write-Host "  mapanare-up current                    Show active version"
    Write-Host "  mapanare-up uninstall <version>        Remove a version"
    Write-Host "  mapanare-up help                       Show this help"
    Write-Host ""
    Write-Host "Version resolution (in order):"
    Write-Host "  1. .mapanare-version file (walks up from current directory)"
    Write-Host "  2. `$MAPANARE_VERSION environment variable"
    Write-Host "  3. ~\.mapanare\default file"
}

# Dispatch
switch ($Command) {
    "install"    { if (-not $Arg) { Write-Host "Usage: mapanare-up install <version|latest>"; exit 1 }; Cmd-Install $Arg }
    "list"       { Cmd-List }
    "ls"         { Cmd-List }
    "default"    { if (-not $Arg) { Write-Host "Usage: mapanare-up default <version>"; exit 1 }; Cmd-Default $Arg }
    "current"    { Cmd-Current }
    "uninstall"  { if (-not $Arg) { Write-Host "Usage: mapanare-up uninstall <version>"; exit 1 }; Cmd-Uninstall $Arg }
    "remove"     { if (-not $Arg) { Write-Host "Usage: mapanare-up uninstall <version>"; exit 1 }; Cmd-Uninstall $Arg }
    "help"       { Cmd-Help }
    "--help"     { Cmd-Help }
    "--version"  { Write-Host "mapanare-up $Script:Version" }
    default      { Write-Host "Unknown command: $Command. Run 'mapanare-up help'." -ForegroundColor Red; exit 1 }
}
