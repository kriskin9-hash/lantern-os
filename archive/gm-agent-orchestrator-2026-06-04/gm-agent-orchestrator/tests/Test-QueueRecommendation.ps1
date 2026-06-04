[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$recommendScript = Join-Path $Root 'scripts\Get-QueueRecommendation.ps1'
if (-not (Test-Path $recommendScript)) {
    throw "Queue recommendation script was not found: $recommendScript"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-queue-recommendation-test-{0}" -f [Guid]::NewGuid().ToString('N'))

function New-TestTaskRoot {
    param([string]$Path)

    foreach ($relativePath in @(
        'tasks\queue',
        'tasks\active',
        'tasks\done',
        'tasks\failed',
        'tasks\hold',
        'config\queue-strategies'
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $Path $relativePath) | Out-Null
    }

    @'
{
  "name": "default.cost-optimized",
  "costMode": "minimize_paid_tokens",
  "preferredOrder": [
    "local_readonly",
    "free_tier_agent",
    "low_cost_agent",
    "paid_high_context_agent",
    "human_review"
  ]
}
'@ | Set-Content -Path (Join-Path $Path 'config\queue-strategies\default.cost-optimized.json') -Encoding UTF8
}

function Invoke-Recommendation {
    param([string]$Path)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $recommendScript -Root $Path 2>&1
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }

        if ($exitCode -ne 0) {
            throw "Recommendation command failed: $($output -join "`n")"
        }

        return (($output | ForEach-Object { $_.ToString() }) -join "`n") | ConvertFrom-Json
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Clear-Tasks {
    param([string]$Path)
    foreach ($state in @('queue', 'active', 'done', 'failed', 'hold')) {
        $dir = Join-Path $Path ("tasks\{0}" -f $state)
        Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | Remove-Item -Force
    }
}

try {
    New-TestTaskRoot -Path $tempRoot

    $none = Invoke-Recommendation -Path $tempRoot
    if ($none.recommendedAction -ne 'none') { throw "Expected none with empty queues; got $($none.recommendedAction)." }
    if (-not $none.ok) { throw 'Expected ok=true for empty queues.' }
    if ($none.strategyName -ne 'default.cost-optimized') { throw "Unexpected strategyName: $($none.strategyName)" }
    if ($none.costMode -ne 'minimize_paid_tokens') { throw "Unexpected costMode: $($none.costMode)" }

    '# Active task' | Set-Content -Path (Join-Path $tempRoot 'tasks\active\codex__010-active.md') -Encoding UTF8
    '# Queued task' | Set-Content -Path (Join-Path $tempRoot 'tasks\queue\020-docs.md') -Encoding UTF8
    $active = Invoke-Recommendation -Path $tempRoot
    if ($active.recommendedAction -ne 'inspect') { throw "Expected inspect when active exists; got $($active.recommendedAction)." }
    if ($active.taskName -ne 'codex__010-active.md') { throw "Unexpected active task: $($active.taskName)" }
    if ($active.from -ne 'active') { throw "Expected from=active; got $($active.from)." }

    Clear-Tasks -Path $tempRoot
    '# Failed task' | Set-Content -Path (Join-Path $tempRoot 'tasks\failed\030-failed.md') -Encoding UTF8
    $failed = Invoke-Recommendation -Path $tempRoot
    if ($failed.recommendedAction -ne 'inspect') { throw "Expected inspect for failed task; got $($failed.recommendedAction)." }
    if ($failed.from -ne 'failed') { throw "Expected from=failed; got $($failed.from)." }
    if ($failed.risk -ne 'medium') { throw "Expected medium risk for failed task; got $($failed.risk)." }

    Clear-Tasks -Path $tempRoot
    '# Documentation update' | Set-Content -Path (Join-Path $tempRoot 'tasks\queue\040-docs-status.md') -Encoding UTF8
    $docs = Invoke-Recommendation -Path $tempRoot
    if ($docs.recommendedAction -ne 'claim') { throw "Expected claim for queued docs task; got $($docs.recommendedAction)." }
    if ($docs.slot -ne 'free_tier_agent') { throw "Expected free_tier_agent for docs task; got $($docs.slot)." }
    if ($docs.command -notmatch 'Move-OrchestratorTask.ps1') { throw "Expected safe movement command suggestion; got $($docs.command)." }
    if ($docs.command -notmatch '-DryRun') { throw 'Suggested command must be dry-run only.' }

    Clear-Tasks -Path $tempRoot
    '# Implement script fix' | Set-Content -Path (Join-Path $tempRoot 'tasks\queue\050-implement-script.md') -Encoding UTF8
    $code = Invoke-Recommendation -Path $tempRoot
    if ($code.recommendedAction -ne 'claim') { throw "Expected claim for queued implementation task; got $($code.recommendedAction)." }
    if ($code.slot -ne 'capable_agent') { throw "Expected capable_agent for implementation task; got $($code.slot)." }
    if ($code.risk -ne 'medium') { throw "Expected medium risk for implementation task; got $($code.risk)." }

    Clear-Tasks -Path $tempRoot
    '# Rotate production token' | Set-Content -Path (Join-Path $tempRoot 'tasks\queue\060-production-token.md') -Encoding UTF8
    $sensitive = Invoke-Recommendation -Path $tempRoot
    if ($sensitive.recommendedAction -ne 'inspect') { throw "Expected inspect for sensitive task; got $($sensitive.recommendedAction)." }
    if (-not $sensitive.requiresHuman) { throw 'Expected requiresHuman=true for sensitive task.' }
    if ($sensitive.slot -ne 'human_review') { throw "Expected human_review slot; got $($sensitive.slot)." }
    if ($sensitive.risk -ne 'high') { throw "Expected high risk for sensitive task; got $($sensitive.risk)." }

    $global:LASTEXITCODE = 0
    Write-Host 'Queue recommendation tests passed.'
}
finally {
    Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
