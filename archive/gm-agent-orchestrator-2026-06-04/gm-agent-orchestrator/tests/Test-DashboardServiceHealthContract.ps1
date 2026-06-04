[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    $Root = (Resolve-Path (Join-Path $scriptDir "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$script = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
if (-not (Test-Path $script)) {
    throw "Orchestrator status script not found: $script"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-status-contract-test-{0}" -f [Guid]::NewGuid().ToString("N"))
try {
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "status") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "tasks\queue") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "tasks\active") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "tasks\done") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "tasks\failed") | Out-Null

    # Mock server-health.json
    $healthPath = Join-Path $tempRoot "status\server-health.json"
    @{
        generatedAt = (Get-Date).ToString("o")
        state = "degraded"
        ok = $false
        servers = @(
            @{ name = "mcp"; state = "offline"; ok = $false; nextAction = "Start MCP." }
        )
        localServices = @()
        nextAction = "Restore offline server(s): mcp."
    } | ConvertTo-Json -Depth 20 | Set-Content -Path $healthPath -Encoding UTF8

    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $tempRoot 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Status script failed: $($output -join "`n")" }

    $status = $output | Out-String | ConvertFrom-Json
    if ($null -eq $status.serviceHealth) { throw "Expected 'serviceHealth' in status output" }
    if ($status.serviceHealth.state -ne "degraded") { throw "Expected serviceHealth.state 'degraded'" }
    if ($status.serviceHealth.servers[0].name -ne "mcp") { throw "Expected server name 'mcp' in serviceHealth" }
    if (-not $status.serviceHealth.fresh) { throw "Expected fresh service health snapshot to remain fresh." }

    $artifactPath = Join-Path $tempRoot "status\orchestrator.json"
    $artifactBytes = [System.IO.File]::ReadAllBytes($artifactPath)
    if ($artifactBytes.Length -ge 3 -and $artifactBytes[0] -eq 239 -and $artifactBytes[1] -eq 187 -and $artifactBytes[2] -eq 191) {
        throw "Expected orchestrator.json to be written without a UTF-8 BOM."
    }

    @'
{
  "generatedAt": "2026-05-29T00:00:00-04:00",
  "intervalSeconds": 180,
  "state": "online",
  "ok": true,
  "servers": [
    { "name": "mcp", "state": "online", "ok": true, "nextAction": "No action required." }
  ],
  "localServices": [],
  "nextAction": "No action required."
}
'@ | Set-Content -Path $healthPath -Encoding UTF8

    $staleOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $tempRoot 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Status script stale snapshot run failed: $($staleOutput -join "`n")" }

    $staleStatus = $staleOutput | Out-String | ConvertFrom-Json
    if ($staleStatus.serviceHealth.state -ne "stale") { throw "Expected stale serviceHealth.state when server-health snapshot is old." }
    if ($staleStatus.serviceHealth.ok) { throw "Expected stale service health snapshot to force ok=false." }
    if ($staleStatus.serviceHealth.fresh) { throw "Expected stale service health snapshot to report fresh=false." }
    if ($staleStatus.serviceHealth.nextAction -notmatch "Monitor-ServerHealthPulse") {
        throw "Expected stale service health nextAction to direct the operator to refresh the pulse."
    }

    Write-Host "Dashboard service health contract tests passed."
}
finally {
    Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
