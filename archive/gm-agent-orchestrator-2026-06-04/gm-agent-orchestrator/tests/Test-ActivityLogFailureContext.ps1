[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$statusScript = Join-Path $Root 'scripts\Get-OrchestratorStatus.ps1'
if (!(Test-Path $statusScript)) {
    throw "Status script was not found: $statusScript"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-activity-test-{0}" -f [Guid]::NewGuid().ToString('N'))

try {
    foreach ($relativePath in @(
        'config',
        'tasks\queue',
        'tasks\active',
        'tasks\done',
        'tasks\failed',
        'logs\codex-main',
        'status',
        'reports\dashboard'
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot $relativePath) | Out-Null
    }

    @'
{
  "slots": [
    {
      "name": "codex-main",
      "agent": "codex",
      "role": "implementation",
      "enabled": true,
      "branch": "feature/test"
    }
  ]
}
'@ | Set-Content -Path (Join-Path $tempRoot 'config\agents.json') -Encoding UTF8

    @'
{
  "worktreeRoot": ""
}
'@ | Set-Content -Path (Join-Path $tempRoot 'config\projects.json') -Encoding UTF8

    @'
# Surface actionable failure context in dashboard activity log

Improve failed activity entries.
'@ | Set-Content -Path (Join-Path $tempRoot 'tasks\failed\codex-main__codex-impl-issue-070-activity-log-failure-context.md') -Encoding UTF8

    @'
===== 2026-04-26 codex exec =====
Runner failure: OpenAI Codex v0.125.0-alpha.3
Validation failed. ExitCode=1. Command=tests/Test-OrchestratorStatusJson.ps1
'@ | Set-Content -Path (Join-Path $tempRoot 'logs\codex-main\20260426-000000-codex-main.log') -Encoding UTF8

    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $statusScript -Root $tempRoot 2>&1
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "Get-OrchestratorStatus.ps1 failed with exit code $exitCode. Output: $($output -join "`n")"
    }

    $status = ($output -join "`n") | ConvertFrom-Json
    $entries = @($status.activityLog)

    if ($entries.Count -ne 1) {
        throw "Expected exactly one activityLog entry; got $($entries.Count)."
    }

    $entry = $entries[0]

    if ($entry.slot -ne 'codex-main') {
        throw "Expected slot codex-main; got $($entry.slot)."
    }

    if ($entry.issue -ne 70) {
        throw "Expected issue 70; got $($entry.issue)."
    }

    if ($entry.taskTitle -ne 'Surface actionable failure context in dashboard activity log') {
        throw "Unexpected task title: $($entry.taskTitle)"
    }

    if ($entry.failureType -ne 'validation_failed') {
        throw "Expected validation_failed failureType; got $($entry.failureType)."
    }

    if ($entry.latestImportantLogLine -notmatch 'Validation failed') {
        throw "Expected latestImportantLogLine to include validation failure; got $($entry.latestImportantLogLine)."
    }

    if ($entry.nextRecommendedAction -notmatch 'fix the first validation failure') {
        throw "Expected actionable next recommendation; got $($entry.nextRecommendedAction)."
    }

    if ($entry.worktreeSummary -notmatch 'worktree root is not configured') {
        throw "Expected worktree summary to be present; got $($entry.worktreeSummary)."
    }

    if ($entry.detailText -notmatch 'Task: Surface actionable failure context in dashboard activity log \(#70\)') {
        throw "Expected detailText to include task title and issue number; got $($entry.detailText)."
    }

    Write-Host 'Activity log failure context test passed.'
}
finally {
    Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
