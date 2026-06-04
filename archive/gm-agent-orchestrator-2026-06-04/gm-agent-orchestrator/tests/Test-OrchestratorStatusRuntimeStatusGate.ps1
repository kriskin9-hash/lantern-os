[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$statusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
if (-not (Test-Path -LiteralPath $statusScript -PathType Leaf)) {
    throw "Status script was not found: $statusScript"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-runtime-status-gate-{0}" -f [Guid]::NewGuid().ToString("N"))

try {
    foreach ($relativePath in @(
        "config",
        "tasks\queue",
        "tasks\active",
        "tasks\done",
        "tasks\failed",
        "logs\claude-main",
        "logs\operator-intake",
        "reports\dashboard",
        "status"
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot $relativePath) | Out-Null
    }

    @'
{
  "slots": [
    {
      "name": "claude-main",
      "agent": "claude",
      "role": "implementation-review",
      "branch": "agent/claude-main",
      "enabled": true
    },
    {
      "name": "operator-intake",
      "agent": "human-interface",
      "role": "operator-intake",
      "branch": "agent/operator-intake",
      "enabled": true
    }
  ]
}
'@ | Set-Content -LiteralPath (Join-Path $tempRoot "config\agents.json") -Encoding UTF8

    @'
{
  "worktreeRoot": ""
}
'@ | Set-Content -LiteralPath (Join-Path $tempRoot "config\projects.json") -Encoding UTF8

    @'
# Runtime status gate test queue item

Ensure stale slot runtime files do not silently revert to available.
'@ | Set-Content -LiteralPath (Join-Path $tempRoot "tasks\queue\runtime-status-gate.md") -Encoding UTF8

    @'
===== 2026-05-01 claude-main run =====
Failed to authenticate.
'@ | Set-Content -LiteralPath (Join-Path $tempRoot "logs\claude-main\20260501-000000-claude-main.log") -Encoding UTF8

    @'
===== 2026-05-01 operator-intake run =====
operator intake queue requires explicit task creation
'@ | Set-Content -LiteralPath (Join-Path $tempRoot "logs\operator-intake\20260501-000000-operator-intake.log") -Encoding UTF8

    (Get-Item -LiteralPath (Join-Path $tempRoot "logs\claude-main\20260501-000000-claude-main.log")).LastWriteTime = [datetime]"2026-05-01T00:00:00"
    (Get-Item -LiteralPath (Join-Path $tempRoot "logs\operator-intake\20260501-000000-operator-intake.log")).LastWriteTime = [datetime]"2026-05-01T00:00:00"

    @'
{
  "slot": "claude-main",
  "state": "blocked",
  "reason": "agent_preflight_blocked_after_claim",
  "nextAction": "Run claude /login, then rerun Start-ClaudeSlot.ps1",
  "updatedAt": "2026-05-29T09:53:44-04:00"
}
'@ | Set-Content -LiteralPath (Join-Path $tempRoot "status\claude-main.json") -Encoding UTF8

    @'
{
  "slot": "operator-intake",
  "state": "active",
  "reason": "operator-intake__ask-lantern-how-to-help-gpt.md",
  "nextAction": "Let operator-intake finish the active task or inspect the dashboard if it stalls.",
  "updatedAt": "2026-05-29T09:53:50-04:00"
}
'@ | Set-Content -LiteralPath (Join-Path $tempRoot "status\operator-intake.json") -Encoding UTF8

    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $statusScript -Root $tempRoot 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Get-OrchestratorStatus.ps1 failed with exit code $LASTEXITCODE. Output: $($output -join "`n")"
    }

    $status = ($output -join "`n") | ConvertFrom-Json -ErrorAction Stop

    if ($status.availability.availableCount -ne 0) {
        throw "Expected availableCount=0 when newer runtime status files block auto-wake; got $($status.availability.availableCount)."
    }
    if ($status.availability.nextHumanAction -match "Start an available slot on queued work") {
        throw "Expected runtime-gated status to avoid start-available guidance."
    }

    $claude = @($status.slots | Where-Object { $_.name -eq "claude-main" } | Select-Object -First 1)
    if ($null -eq $claude) { throw "claude-main slot summary missing." }
    if ($claude.state -ne "blocked") {
        throw "Expected claude-main state=blocked from runtime status; got $($claude.state)."
    }
    if ($claude.nextAction.action -notmatch "claude /login") {
        throw "Expected claude-main next action to carry runtime guidance; got $($claude.nextAction.action)."
    }

    $claudeAvailability = @($status.availability.slots | Where-Object { $_.slot -eq "claude-main" } | Select-Object -First 1)
    if ($null -eq $claudeAvailability) { throw "claude-main availability entry missing." }
    if ($claudeAvailability.wakeState -ne "needs_human") {
        throw "Expected claude-main wakeState=needs_human; got $($claudeAvailability.wakeState)."
    }

    $operator = @($status.slots | Where-Object { $_.name -eq "operator-intake" } | Select-Object -First 1)
    if ($null -eq $operator) { throw "operator-intake slot summary missing." }
    if ($operator.state -ne "stale") {
        throw "Expected operator-intake state=stale when runtime status says active but no task/runner evidence exists; got $($operator.state)."
    }

    Write-Host "Runtime status wake gate test passed."
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
