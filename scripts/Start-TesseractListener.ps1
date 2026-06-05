param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [int]$IntervalSeconds = 60,
    [switch]$Once,
    [switch]$Status
)

$ErrorActionPreference = "Stop"

# Resolve the *real* Python executable to avoid shim wrappers (uv, pyenv, etc.)
# spawning a parent/child process pair.
$python = & python -c "import sys; print(sys.executable)"
if (-not $python -or -not (Test-Path $python)) {
    $python = (Get-Command python).Source
}
$scriptPath = Join-Path $Root "scripts\agent_inspector.py"
$reportPath = Join-Path $Root "data\agent-fleet\tesseract-latest.json"
$stdoutPath = Join-Path $Root "data\agent-fleet\tesseract-listener.stdout.log"
$stderrPath = Join-Path $Root "data\agent-fleet\tesseract-listener.stderr.log"
$lockPath = Join-Path $Root "data\agent-fleet\tesseract-listener.lock.json"

$existing = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -like "*agent_inspector.py*" -and $_.CommandLine -like "*--listener*"
}

if ($Status) {
    if (Test-Path $lockPath) {
        $lock = Get-Content $lockPath -Raw | ConvertFrom-Json
        Write-Host "Listener lock:" -ForegroundColor Green
        Write-Host "  PID: $($lock.pid)"
        Write-Host "  Acquired: $($lock.acquired_at)"
        Write-Host "  IntervalSeconds: $($lock.interval_seconds)"
    }
    if ($existing) {
        Write-Host "Listener process count: $(@($existing).Count)" -ForegroundColor Green
    } else {
        Write-Host "Listener not running." -ForegroundColor Yellow
    }
    exit 0
}

if ($Once) {
    & $python $scriptPath --once --refresh-checkins --interval $IntervalSeconds --report $reportPath
    exit $LASTEXITCODE
}

if ($existing) {
    Write-Host "Listener already running." -ForegroundColor Yellow
    $existing | Select-Object ProcessId, CommandLine
    exit 0
}

New-Item -ItemType Directory -Force -Path (Split-Path $stdoutPath) | Out-Null

$process = Start-Process `
    -FilePath $python `
    -ArgumentList @($scriptPath, "--listener", "--interval", $IntervalSeconds, "--report", $reportPath) `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -WindowStyle Hidden `
    -PassThru

Write-Host "Listener started." -ForegroundColor Green
Write-Host "PID: $($process.Id)"
Write-Host "Report: $reportPath"
