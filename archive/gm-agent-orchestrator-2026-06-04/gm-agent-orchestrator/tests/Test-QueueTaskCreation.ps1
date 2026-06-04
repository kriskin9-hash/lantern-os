[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$createScript = Join-Path $Root "scripts\New-OrchestratorQueueTask.ps1"
$statusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"

if (-not (Test-Path -LiteralPath $createScript -PathType Leaf)) {
    throw "Queue creation script was not found: $createScript"
}

if (-not (Test-Path -LiteralPath $statusScript -PathType Leaf)) {
    throw "Status script was not found: $statusScript"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-queue-create-test-{0}" -f [Guid]::NewGuid().ToString("N"))

function Normalize-TestPath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    return $Path -replace "\\", "/"
}

function New-TestRoot {
    param([string]$Path)

    foreach ($relativePath in @(
        "tasks\queue",
        "tasks\active",
        "tasks\done",
        "tasks\failed",
        "logs",
        "locks",
        "status",
        "reports\dashboard",
        "config"
    )) {
        New-Item -ItemType Directory -Force -Path (Join-Path $Path $relativePath) | Out-Null
    }

    @'
{
  "fallbackWaitMinutes": 300,
  "maxResumeCycles": 4,
  "slots": [
    {
      "name": "operator-intake",
      "agent": "human-interface",
      "role": "operator-intake",
      "enabled": true,
      "branch": "agent/operator-intake",
      "command": {
        "start": ["powershell", "-NoProfile", "-Command", "Write-Output intake"],
        "resume": ["powershell", "-NoProfile", "-Command", "Write-Output intake"]
      }
    },
    {
      "name": "claude-main",
      "agent": "claude",
      "role": "implementation-review",
      "enabled": true,
      "branch": "agent/claude-main",
      "command": {
        "start": ["powershell", "-NoProfile", "-Command", "Write-Output claude"],
        "resume": ["powershell", "-NoProfile", "-Command", "Write-Output claude"]
      }
    }
  ]
}
'@ | Set-Content -LiteralPath (Join-Path $Path "config\agents.json") -Encoding UTF8

    @'
{
  "worktreeRoot": "worktrees"
}
'@ | Set-Content -LiteralPath (Join-Path $Path "config\projects.json") -Encoding UTF8
}

function Invoke-QueueCreate {
    param([string[]]$Arguments)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $createScript @Arguments 2>&1
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

function Convert-OutputJson {
    param([string]$Output)

    $trimmed = $Output.Trim()
    if (-not $trimmed.StartsWith("{")) {
        throw "Expected JSON object output. Actual output: $Output"
    }

    return $trimmed | ConvertFrom-Json -ErrorAction Stop
}

try {
    New-TestRoot -Path $tempRoot

    $body = @'
## Problem
Connector callers need to stock the orchestrator queue without pasting local PowerShell.

## Required behavior
- Accept title/body inputs.
- Write to tasks/queue.
- Return created path and audit metadata.

## Acceptance criteria
- Created task appears in queue summary.
- Control action is audited.
'@

    $created = Invoke-QueueCreate -Arguments @(
        "-Root", $tempRoot,
        "-Title", "P0: Connector stocked queue task",
        "-Body", $body,
        "-Priority", "P0",
        "-Owner", "operator-intake"
    )

    if ($created.exitCode -ne 0) {
        throw "Queue creation failed: $($created.output)"
    }

    $createdJson = Convert-OutputJson -Output $created.output
    if (-not $createdJson.ok) { throw "Expected ok=true from queue creation." }
    if ($createdJson.relativePath -ne "tasks/queue/p0-connector-stocked-queue-task.md") { throw "Unexpected created path: $($createdJson.relativePath)" }
    if ($createdJson.audit.path -notmatch "logs/control-actions/.+create_queue_task\.json") { throw "Expected audit path in logs/control-actions, got: $($createdJson.audit.path)" }
    if ($createdJson.bodySource -ne "body") { throw "Expected bodySource=body, got $($createdJson.bodySource)." }
    if ($createdJson.afterCounts.queue -ne ($createdJson.beforeCounts.queue + 1)) { throw "Queue count did not increase by one." }

    $taskPath = Join-Path $tempRoot $createdJson.relativePath.Replace("/", "\")
    if (-not (Test-Path -LiteralPath $taskPath -PathType Leaf)) { throw "Expected created task file: $taskPath" }
    $taskText = Get-Content -LiteralPath $taskPath -Raw
    if ($taskText -notmatch "## Problem" -or $taskText -notmatch "Owner: operator-intake") { throw "Created task did not preserve connector body and metadata." }

    $auditPath = Join-Path $tempRoot $createdJson.audit.path.Replace("/", "\")
    if (-not (Test-Path -LiteralPath $auditPath -PathType Leaf)) { throw "Expected audit file: $auditPath" }
    $audit = Get-Content -LiteralPath $auditPath -Raw | ConvertFrom-Json -ErrorAction Stop
    if ($audit.action -ne "create_queue_task" -or (Normalize-TestPath -Path $audit.relativePath) -ne $createdJson.relativePath) { throw "Audit record did not capture create_queue_task and relative path." }

    $statusOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $statusScript -Root $tempRoot 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Status script failed: $($statusOutput -join "`n")" }
    $status = (($statusOutput | Out-String).Trim()) | ConvertFrom-Json -ErrorAction Stop
    $queued = @($status.tasks.queue | Where-Object { (Normalize-TestPath -Path $_.path) -eq $createdJson.relativePath })
    if ($queued.Count -ne 1) { throw "Created task did not appear in queue summary." }

    $reasonCompat = Invoke-QueueCreate -Arguments @(
        "-Root", $tempRoot,
        "-Title", "P1: Reason compatibility path",
        "-Reason", "Compatibility callers still provide reason text.",
        "-Priority", "P1",
        "-Owner", "claude"
    )

    if ($reasonCompat.exitCode -ne 0) { throw "Reason compatibility creation failed: $($reasonCompat.output)" }
    $reasonJson = Convert-OutputJson -Output $reasonCompat.output
    if ($reasonJson.bodySource -ne "reason_template") { throw "Expected bodySource=reason_template for compatibility path." }

    $bad = Invoke-QueueCreate -Arguments @(
        "-Root", $tempRoot,
        "-Title", "Malformed body should fail",
        "-Body", "This body has no Markdown heading."
    )

    if ($bad.exitCode -eq 0) { throw "Malformed connector body should fail validation." }
    if ($bad.output -notmatch "Markdown heading") { throw "Malformed body failure should mention Markdown heading. Actual: $($bad.output)" }

    Write-Host "Queue task creation tests passed."
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
