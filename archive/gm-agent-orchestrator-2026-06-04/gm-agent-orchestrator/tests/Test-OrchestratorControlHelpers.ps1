[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$taskActionScript = Join-Path $Root "scripts/Invoke-OrchestratorTaskAction.ps1"
$agentActionScript = Join-Path $Root "scripts/Invoke-OrchestratorAgentAction.ps1"

foreach ($script in @($taskActionScript, $agentActionScript)) {
    if (!(Test-Path $script)) {
        throw "Required control helper script was not found: $script"
    }
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("gm-orch-control-test-{0}" -f ([guid]::NewGuid().ToString("N")))
try {
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "tasks\active") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "tasks\queue") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "tasks\done") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "tasks\failed") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot "scripts") | Out-Null

    Copy-Item $agentActionScript (Join-Path $tempRoot "scripts\Invoke-OrchestratorAgentAction.ps1")
    Copy-Item $taskActionScript (Join-Path $tempRoot "scripts\Invoke-OrchestratorTaskAction.ps1")
    "Write-Host 'stub start'" | Set-Content -Path (Join-Path $tempRoot "scripts\Start-GmAgentOrchestrator.ps1") -Encoding UTF8

    $taskPath = Join-Path $tempRoot "tasks\active\gpt-main__000-orch-mvp-smoke.md"
    "# Smoke task" | Set-Content -Path $taskPath -Encoding UTF8

    $taskOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tempRoot "scripts\Invoke-OrchestratorTaskAction.ps1") -Root $tempRoot -Action requeue_task -TaskPath "tasks\active\gpt-main__000-orch-mvp-smoke.md" -Reason "contract test" -DryRun
    $taskJson = ($taskOutput | Out-String).Trim() | ConvertFrom-Json -ErrorAction Stop

    foreach ($field in @("ok", "action", "generatedAt", "root", "dryRun", "requestedTaskPath", "sourcePath", "destinationPath", "beforeCounts", "afterCounts")) {
        if ($null -eq $taskJson.PSObject.Properties[$field]) { throw "Task action JSON missing required field: $field" }
    }
    if ($taskJson.action -ne "requeue_task") { throw "Unexpected task action: $($taskJson.action)" }
    if ($taskJson.dryRun -ne $true) { throw "Task action dryRun must be true in test." }
    if ($taskJson.beforeCounts.active -ne 1) { throw "Expected one active task before dry-run requeue." }
    if ($taskJson.afterCounts.active -ne 1) { throw "Dry-run requeue must not move the active task." }

    $agentOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tempRoot "scripts\Invoke-OrchestratorAgentAction.ps1") -Root $tempRoot -Action start_agent -SlotName gpt-main -DryRun
    $agentJson = ($agentOutput | Out-String).Trim() | ConvertFrom-Json -ErrorAction Stop

    foreach ($field in @("ok", "action", "slot", "generatedAt", "root", "dryRun", "command", "beforeCounts", "afterCounts")) {
        if ($null -eq $agentJson.PSObject.Properties[$field]) { throw "Agent action JSON missing required field: $field" }
    }
    if ($agentJson.action -ne "start_agent") { throw "Unexpected agent action: $($agentJson.action)" }
    if ($agentJson.slot -ne "gpt-main") { throw "Unexpected agent slot: $($agentJson.slot)" }
    if ($agentJson.dryRun -ne $true) { throw "Agent action dryRun must be true in test." }

    $queueCreationTest = Join-Path $Root "tests\Test-QueueTaskCreation.ps1"
    $safeRunnerTest = Join-Path $Root "tests\Test-SafePowerShellRunner.ps1"
    foreach ($testScript in @($queueCreationTest, $safeRunnerTest)) {
        if (!(Test-Path -LiteralPath $testScript -PathType Leaf)) {
            throw "Required regression test was not found: $testScript"
        }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $testScript -Root $Root
        if ($LASTEXITCODE -ne 0) {
            throw "Regression test failed: $testScript"
        }
    }

    Write-Host "Validated orchestrator control helper JSON contracts."
}
finally {
    Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
