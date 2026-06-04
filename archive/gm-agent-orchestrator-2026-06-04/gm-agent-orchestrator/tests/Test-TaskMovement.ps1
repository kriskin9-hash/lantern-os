[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$moveScript = Join-Path $Root 'scripts\Move-OrchestratorTask.ps1'
if (-not (Test-Path $moveScript)) {
    throw "Move script was not found: $moveScript"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-task-movement-test-{0}" -f [Guid]::NewGuid().ToString('N'))

function New-TestTaskRoot {
    param([string]$Path)

    foreach ($relativePath in @(
        'tasks\queue',
        'tasks\active',
        'tasks\done',
        'tasks\failed',
        'tasks\hold',
        'config\queue-strategies',
        'reports\queue-movements'
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $Path $relativePath) | Out-Null
    }

    @'
{
  "name": "default.cost-optimized",
  "costMode": "minimize_paid_tokens",
  "movementPolicy": {
    "defaultReason": "queue strategy movement",
    "forbidOverwrite": true,
    "forbidPathTraversal": true
  }
}
'@ | Set-Content -Path (Join-Path $Path 'config\queue-strategies\default.cost-optimized.json') -Encoding UTF8
}

function Invoke-MoveTask {
    param([string[]]$Arguments)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $moveScript @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }

        return [pscustomobject]@{
            exitCode = [int]$exitCode
            output = ($output | ForEach-Object { $_.ToString() }) -join "`n"
        }
    }
    catch {
        return [pscustomobject]@{
            exitCode = 1
            output = $_.Exception.Message
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

try {
    New-TestTaskRoot -Path $tempRoot

    $taskPath = Join-Path $tempRoot 'tasks\queue\070-test-task.md'
    @'
# Queue movement test

Preserve this content.
'@ | Set-Content -Path $taskPath -Encoding UTF8

    $dryRun = Invoke-MoveTask -Arguments @('-Root', $tempRoot, '-From', 'queue', '-To', 'active', '-TaskName', '070-test-task.md', '-Slot', 'codex-main', '-DryRun')
    if ($dryRun.exitCode -ne 0) {
        throw "DryRun failed: $($dryRun.output)"
    }

    $dryRunJson = $dryRun.output | ConvertFrom-Json
    if (-not $dryRunJson.dryRun) { throw 'Expected dryRun output to be true.' }
    if ($dryRunJson.destinationName -ne 'codex-main__070-test-task.md') { throw "Unexpected dry-run destination: $($dryRunJson.destinationName)" }
    if (-not (Test-Path $taskPath)) { throw 'DryRun should not move source file.' }

    $move = Invoke-MoveTask -Arguments @('-Root', $tempRoot, '-From', 'queue', '-To', 'active', '-TaskName', '070-test-task.md', '-Slot', 'codex-main', '-Reason', 'test claim')
    if ($move.exitCode -ne 0) {
        throw "Move queue->active failed: $($move.output)"
    }

    $activePath = Join-Path $tempRoot 'tasks\active\codex-main__070-test-task.md'
    if (-not (Test-Path $activePath)) { throw 'Expected active task to exist after move.' }
    if (Test-Path $taskPath) { throw 'Expected source queue task to be removed after move.' }
    if ((Get-Content $activePath -Raw) -notmatch 'Preserve this content') { throw 'Task content was not preserved.' }

    $auditFiles = @(Get-ChildItem (Join-Path $tempRoot 'reports\queue-movements') -Filter '*.jsonl' -File)
    if ($auditFiles.Count -ne 1) { throw "Expected one audit file; got $($auditFiles.Count)." }
    $auditEntry = Get-Content $auditFiles[0].FullName -Raw | ConvertFrom-Json
    if ($auditEntry.from -ne 'queue' -or $auditEntry.to -ne 'active') { throw 'Audit entry did not record source/destination.' }
    if ($auditEntry.strategyName -ne 'default.cost-optimized') { throw "Unexpected strategyName in audit: $($auditEntry.strategyName)" }
    if ($auditEntry.reason -ne 'test claim') { throw "Unexpected audit reason: $($auditEntry.reason)" }

    $doneMove = Invoke-MoveTask -Arguments @('-Root', $tempRoot, '-From', 'active', '-To', 'done', '-TaskName', 'codex-main__070-test-task.md', '-Reason', 'test done')
    if ($doneMove.exitCode -ne 0) {
        throw "Move active->done failed: $($doneMove.output)"
    }

    $donePath = Join-Path $tempRoot 'tasks\done\070-test-task.md'
    if (-not (Test-Path $donePath)) { throw 'Expected done task to strip slot prefix.' }
    if (Test-Path $activePath) { throw 'Expected active source to be removed.' }

    $conflictSource = Join-Path $tempRoot 'tasks\queue\conflict.md'
    $conflictDestination = Join-Path $tempRoot 'tasks\done\conflict.md'
    '# conflict source' | Set-Content -Path $conflictSource -Encoding UTF8
    '# existing destination' | Set-Content -Path $conflictDestination -Encoding UTF8

    $conflict = Invoke-MoveTask -Arguments @('-Root', $tempRoot, '-From', 'queue', '-To', 'done', '-TaskName', 'conflict.md')
    if ($conflict.exitCode -eq 0) {
        throw 'Expected destination conflict to fail.'
    }
    if ($conflict.output -notmatch 'Destination already exists') {
        throw "Expected destination conflict message; got: $($conflict.output)"
    }
    if (-not (Test-Path $conflictSource)) { throw 'Conflict should leave source in place.' }

    $unsafe = Invoke-MoveTask -Arguments @('-Root', $tempRoot, '-From', 'queue', '-To', 'done', '-TaskName', '..\escape.md')
    if ($unsafe.exitCode -eq 0) {
        throw 'Expected path traversal task name to fail.'
    }
    if ($unsafe.output -notmatch 'TaskName must be a file name') {
        throw "Expected unsafe path message; got: $($unsafe.output)"
    }

    $global:LASTEXITCODE = 0
    Write-Host 'Task movement tests passed.'
}
finally {
    Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

