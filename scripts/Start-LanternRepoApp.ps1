[CmdletBinding()]
param(
    [int]$Port = 4177,
    [switch]$NoBrowser,
    [switch]$RebootAfterLaunch,
    [int]$RebootDelaySeconds = 300
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$appScript = Join-Path $repoRoot 'scripts\Start-LanternGarageApp.ps1'
$appUrl = "http://127.0.0.1:$Port/"

if (-not (Test-Path $appScript)) {
    throw "Lantern dashboard launcher not found: $appScript"
}

Write-Host "Lantern OS repo root: $repoRoot"
Write-Host "Lantern OS dashboard: $appUrl"

try {
    $health = Invoke-WebRequest -UseBasicParsing -Uri "$appUrl/api/health" -TimeoutSec 2
    if ($health.StatusCode -eq 200 -and $health.Content -match "lantern-garage") {
        Write-Host "Lantern dashboard already running."
        if (-not $NoBrowser) { Start-Process $appUrl }
    }
    else {
        throw "Unexpected health response."
    }
}
catch {
    Write-Host "Starting Lantern dashboard on $appUrl"
    Start-Process -FilePath "powershell.exe" `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $appScript, "-Port", $Port) `
        -WorkingDirectory $repoRoot `
        -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 2
    if (-not $NoBrowser) { Start-Process $appUrl }
}

if ($RebootAfterLaunch) {
    if ($RebootDelaySeconds -lt 60) {
        throw "Refusing to schedule reboot with delay under 60 seconds. Use at least 60 seconds so it can be aborted."
    }
    Write-Warning "Scheduling Windows reboot in $RebootDelaySeconds seconds. Abort with: shutdown /a"
    shutdown /r /t $RebootDelaySeconds /c "Lantern OS requested reboot after local app launch. Abort with shutdown /a."
}
