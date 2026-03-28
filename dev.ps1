# Mapanare dev launcher.
#
# Usage:
#   .\dev.ps1                  # validate (default)
#   .\dev.ps1 validate         # watch Python files and validate on changes
#   .\dev.ps1 test             # run pytest once
#   .\dev.ps1 lint             # run all linters once
#   .\dev.ps1 fmt              # auto-format and fix
#   .\dev.ps1 e2e              # run e2e tests only
#   .\dev.ps1 bench            # run benchmarks

param(
    [ValidateSet("validate", "test", "lint", "fmt", "e2e", "bench")]
    [string]$Mode = "validate"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogFile = Join-Path $Root "error.log"

# --- Shared lint function (defined first so all modes can call it) ---
function Write-Log {
    param([string]$Message)
    $Message | Out-File -Append -Encoding utf8 $script:LogFile
}

function Invoke-AllChecks {
    # Overwrite log file each run
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$ts] Running checks...`n" | Out-File -Encoding utf8 $LogFile

    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] " -ForegroundColor DarkGray -NoNewline
    Write-Host "Running checks..." -ForegroundColor Cyan
    Write-Host ""

    $allPassed = $true

    # --- black (format check) ---
    Write-Host "  black           " -ForegroundColor Cyan -NoNewline
    $savedEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $out = & black --check --target-version py311 . 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedEAP
    if ($exitCode -eq 0) {
        Write-Host "ok" -ForegroundColor Green
        Write-Log "[black] ok"
    } else {
        $savedEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        & black --target-version py311 . 2>&1 | Out-Null
        $ErrorActionPreference = $savedEAP
        $fixed = ($out | Select-String "would reformat").Count
        Write-Host "fixed $fixed files" -ForegroundColor Yellow
        Write-Log "[black] fixed $fixed files"
        $out | ForEach-Object { Write-Log "  $_" }
    }

    # --- ruff check ---
    Write-Host "  ruff check      " -ForegroundColor Cyan -NoNewline
    $savedEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $out = & ruff check . 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedEAP
    if ($exitCode -eq 0) {
        Write-Host "ok" -ForegroundColor Green
        Write-Log "[ruff] ok"
    } else {
        $savedEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $fixOut = & ruff check --fix . 2>&1
        $fixExit = $LASTEXITCODE
        $ErrorActionPreference = $savedEAP
        if ($fixExit -eq 0) {
            $fixed = ($out | Select-String "^\[").Count
            Write-Host "fixed $fixed issues" -ForegroundColor Yellow
            Write-Log "[ruff] fixed $fixed issues"
            $out | ForEach-Object { Write-Log "  $_" }
        } else {
            Write-Host "fail" -ForegroundColor Red
            $allPassed = $false
            $fixOut | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
            Write-Log "[ruff] FAIL"
            $fixOut | ForEach-Object { Write-Log "  $_" }
        }
    }

    # --- mypy ---
    Write-Host "  mypy            " -ForegroundColor Cyan -NoNewline
    $savedEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $out = & mypy mapanare/ runtime/ 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedEAP
    if ($exitCode -eq 0) {
        Write-Host "ok" -ForegroundColor Green
        Write-Log "[mypy] ok"
    } else {
        $allPassed = $false
        $errCount = ($out | Select-String "^Found \d+ error").Count
        if ($errCount -gt 0) {
            $summary = ($out | Select-String "^Found \d+ error").Line
            Write-Host "fail ($summary)" -ForegroundColor Red
            Write-Log "[mypy] FAIL ($summary)"
        } else {
            Write-Host "fail" -ForegroundColor Red
            Write-Log "[mypy] FAIL"
        }
        $out | Where-Object { $_ -match "error:" } | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        $out | ForEach-Object { Write-Log "  $_" }
    }

    # --- C runtime (gcc) ---
    Write-Host "  gcc (C runtime) " -ForegroundColor Cyan -NoNewline
    $gccPath = Get-Command gcc -ErrorAction SilentlyContinue
    if ($gccPath) {
        $savedEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $testExe = Join-Path $Root "test_c_runtime.exe"
        $out = & gcc -O2 -g -pthread `
            "$Root\tests\native\test_c_runtime.c" `
            "$Root\runtime\native\mapanare_core.c" `
            "$Root\runtime\native\mapanare_runtime.c" `
            -o $testExe 2>&1
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $savedEAP
        if ($exitCode -ne 0) {
            $allPassed = $false
            Write-Host "compile fail" -ForegroundColor Red
            $out | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
            Write-Log "[gcc] COMPILE FAIL"
            $out | ForEach-Object { Write-Log "  $_" }
        } else {
            $savedEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
            $out = & $testExe 2>&1
            $exitCode = $LASTEXITCODE
            $ErrorActionPreference = $savedEAP
            if ($exitCode -eq 0) {
                $passCount = ($out | Select-String "\[PASS\]").Count
                Write-Host "ok ($passCount passed)" -ForegroundColor Green
                Write-Log "[gcc] ok ($passCount passed)"
            } else {
                $allPassed = $false
                Write-Host "fail" -ForegroundColor Red
                $out | Where-Object { $_ -match "FAIL|error|abort" } | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
                Write-Log "[gcc] FAIL"
                $out | ForEach-Object { Write-Log "  $_" }
            }
            Remove-Item $testExe -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "skip (gcc not found)" -ForegroundColor DarkGray
        Write-Log "[gcc] skip (gcc not found)"
    }

    # --- pytest ---
    Write-Host "  pytest          " -ForegroundColor Cyan -NoNewline
    $savedEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $out = & pytest --tb=short -q 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $savedEAP
    if ($exitCode -eq 0) {
        $passLine = ($out | Select-String "passed").Line
        if ($passLine) {
            Write-Host "ok ($passLine)" -ForegroundColor Green
            Write-Log "[pytest] ok ($passLine)"
        } else {
            Write-Host "ok" -ForegroundColor Green
            Write-Log "[pytest] ok"
        }
    } else {
        $allPassed = $false
        $failLine = ($out | Select-String "failed|error").Line | Select-Object -First 1
        if ($failLine) {
            Write-Host "fail ($failLine)" -ForegroundColor Red
        } else {
            Write-Host "fail" -ForegroundColor Red
        }
        $out | Where-Object { $_ -match "FAILED|ERROR" } | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        Write-Log "[pytest] FAIL"
        $out | ForEach-Object { Write-Log "  $_" }
    }

    Write-Host ""
    return $allPassed
}

# --- fmt mode ---
if ($Mode -eq "fmt") {
    Write-Host "[dev] Auto-formatting..." -ForegroundColor Cyan
    & black --target-version py311 .
    & ruff check --fix .
    Write-Host "[dev] Done." -ForegroundColor Green
    return
}

# --- test mode ---
if ($Mode -eq "test") {
    Write-Host "[dev] Running tests..." -ForegroundColor Cyan
    & pytest tests/ -v
    return
}

# --- e2e mode ---
if ($Mode -eq "e2e") {
    Write-Host "[dev] Running e2e tests..." -ForegroundColor Cyan
    & pytest tests/e2e/ -v
    return
}

# --- bench mode ---
if ($Mode -eq "bench") {
    Write-Host "[dev] Running benchmarks..." -ForegroundColor Cyan
    & python -m benchmarks.run_all
    return
}

# --- lint mode (one-shot) ---
if ($Mode -eq "lint") {
    Invoke-AllChecks
    return
}

# --- validate mode (watch + lint) ---
if ($Mode -eq "validate") {
    $mapaPath = "$Root\mapanare"
    $runtimePath = "$Root\runtime"
    $testsPath = "$Root\tests"
    $stdlibPath = "$Root\stdlib"

    Write-Host "[dev] Watching for lint + type + test errors" -ForegroundColor Cyan
    Write-Host "[dev]   Compiler : $mapaPath" -ForegroundColor DarkGray
    Write-Host "[dev]   Runtime  : $runtimePath" -ForegroundColor DarkGray
    Write-Host "[dev]   Tests    : $testsPath" -ForegroundColor DarkGray
    Write-Host "[dev]   Stdlib   : $stdlibPath" -ForegroundColor DarkGray
    Write-Host "[dev] Press Ctrl+C to stop." -ForegroundColor DarkGray
    Write-Host ""

    Invoke-AllChecks

    $watchers = @()
    $watchDirs = @($mapaPath, $runtimePath, $testsPath, $stdlibPath) | Where-Object { Test-Path $_ }

    foreach ($dir in $watchDirs) {
        foreach ($filter in @("*.py", "*.c", "*.h")) {
            $w = [System.IO.FileSystemWatcher]::new($dir, $filter)
            $w.IncludeSubdirectories = $true
            $w.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor
                              [System.IO.NotifyFilters]::FileName -bor
                              [System.IO.NotifyFilters]::CreationTime
            $w.EnableRaisingEvents = $true
            $watchers += $w
        }
    }

    $script:lastChange = [datetime]::MinValue
    $lastRun = [datetime]::MinValue

    $handler = {
        $script:lastChange = Get-Date
    }

    foreach ($w in $watchers) {
        Register-ObjectEvent $w Changed -Action $handler | Out-Null
        Register-ObjectEvent $w Created -Action $handler | Out-Null
        Register-ObjectEvent $w Renamed -Action $handler | Out-Null
    }

    try {
        while ($true) {
            Start-Sleep -Milliseconds 500
            if ($script:lastChange -ne [datetime]::MinValue -and
                ((Get-Date) - $script:lastChange).TotalMilliseconds -gt 800 -and
                $script:lastChange -ne $lastRun) {
                $lastRun = $script:lastChange
                Invoke-AllChecks
            }
        }
    } finally {
        foreach ($w in $watchers) {
            $w.Dispose()
        }
        Get-EventSubscriber | Unregister-Event
        Write-Host "[dev] Watcher stopped." -ForegroundColor Green
    }
}
