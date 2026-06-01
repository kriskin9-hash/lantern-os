[CmdletBinding()]
param(
    [string]$OrchestratorRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string[]]$ExpectedTasks = @(
        "010-agent-contract-rollout.md",
        "012-headless-orchestrator-mode.md",
        "013-automate-github-sync-loop.md",
        "014-dashboard-status-indicators.md"
    ),
    [switch]$Fetch,
    [switch]$JsonOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (!(Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Get-MarkdownFiles {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (!(Test-Path -LiteralPath $Path)) {
        return @()
    }

    return @(Get-ChildItem -LiteralPath $Path -Filter "*.md" -File | Sort-Object Name | ForEach-Object {
        [pscustomobject]@{
            name = $_.Name
            path = $_.FullName
            lastWriteTime = $_.LastWriteTime.ToString("o")
            sizeBytes = $_.Length
        }
    })
}

function Get-RowNames {
    param([object[]]$Rows)

    if ($null -eq $Rows) {
        return @()
    }

    $names = @()
    foreach ($row in $Rows) {
        if ($null -eq $row) { continue }
        if ($row.PSObject.Properties.Name -contains "name") {
            $names += [string]$row.name
        }
    }
    return @($names)
}

function Invoke-GitSafe {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    try {
        $output = & git @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }

        return [pscustomobject]@{
            ok = ($exitCode -eq 0)
            exitCode = [int]$exitCode
            output = @($output | ForEach-Object { $_.ToString() })
        }
    }
    catch {
        return [pscustomobject]@{
            ok = $false
            exitCode = -1
            output = @($_.Exception.Message)
        }
    }
}

$root = (Resolve-Path -LiteralPath $OrchestratorRoot).Path
$queueDir = Join-Path $root "tasks\queue"
$activeDir = Join-Path $root "tasks\active"
$doneDir = Join-Path $root "tasks\done"
$failedDir = Join-Path $root "tasks\failed"
$statusDir = Join-Path $root "status"
$reportDir = Join-Path $root "reports\audit"

Ensure-Directory -Path $statusDir
Ensure-Directory -Path $reportDir

Push-Location $root
try {
    $gitPresent = $null -ne (Get-Command git -ErrorAction SilentlyContinue)
    $fetchResult = $null
    $branch = ""
    $gitStatusShort = @("git not found")
    $gitStatusBranch = @("git not found")

    if ($gitPresent) {
        if ($Fetch) {
            $fetchResult = Invoke-GitSafe -Arguments @("fetch", "--all", "--prune")
        }

        $branchResult = Invoke-GitSafe -Arguments @("branch", "--show-current")
        $branch = ($branchResult.output -join "`n").Trim()
        $gitStatusShort = (Invoke-GitSafe -Arguments @("status", "--short")).output
        $gitStatusBranch = (Invoke-GitSafe -Arguments @("status", "-sb")).output
    }

    $queue = @(Get-MarkdownFiles -Path $queueDir)
    $active = @(Get-MarkdownFiles -Path $activeDir)
    $done = @(Get-MarkdownFiles -Path $doneDir)
    $failed = @(Get-MarkdownFiles -Path $failedDir)

    $queueNames = @(Get-RowNames -Rows $queue)
    $activeNames = @(Get-RowNames -Rows $active)
    $doneNames = @(Get-RowNames -Rows $done)
    $failedNames = @(Get-RowNames -Rows $failed)

    $expected = @()
    foreach ($taskNameRaw in $ExpectedTasks) {
        $taskName = [string]$taskNameRaw
        $foundIn = @()

        if ($queueNames -contains $taskName) { $foundIn += "queue" }
        if (@($activeNames | Where-Object { $_ -like "*$taskName" }).Count -gt 0) { $foundIn += "active" }
        if ($doneNames -contains $taskName) { $foundIn += "done" }
        if ($failedNames -contains $taskName) { $foundIn += "failed" }

        $expected += [pscustomobject]@{
            name = $taskName
            found = ($foundIn.Count -gt 0)
            location = if ($foundIn.Count -gt 0) { $foundIn -join "," } else { "missing" }
        }
    }

    $missingExpected = @($expected | Where-Object { -not $_.found })
    if ($missingExpected.Count -gt 0) {
        $likelyIssue = "Expected tasks are missing locally. Run safe git pull or verify dashboard reads this root."
    }
    elseif ($queue.Count -gt 0) {
        $likelyIssue = "Tasks are present in queue. If dashboard does not show them, dashboard is reading the wrong root or not refreshing queue state."
    }
    elseif ($active.Count -gt 0) {
        $likelyIssue = "Tasks are active. Dashboard should show claimed/running state."
    }
    else {
        $likelyIssue = "No queued or active expected tasks found; check done/failed and logs."
    }

    $result = [pscustomobject]@{
        generatedAt = (Get-Date).ToString("o")
        orchestratorRoot = $root
        gitPresent = $gitPresent
        branch = $branch
        fetch = $fetchResult
        gitStatusShort = $gitStatusShort
        gitStatusBranch = $gitStatusBranch
        counts = [pscustomobject]@{
            queue = $queue.Count
            active = $active.Count
            done = $done.Count
            failed = $failed.Count
        }
        expectedTasks = $expected
        queue = $queue
        active = $active
        done = $done
        failed = $failed
        likelyIssue = $likelyIssue
    }

    $jsonPath = Join-Path $statusDir "task-visibility-audit.json"
    $result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $reportPath = Join-Path $reportDir ("{0}-task-visibility.md" -f $stamp)

    $reportLines = @()
    $reportLines += "# Task Visibility Audit"
    $reportLines += ""
    $reportLines += ("Generated: {0}" -f $result.generatedAt)
    $reportLines += ("Root: {0}" -f $root)
    $reportLines += ("Branch: {0}" -f $result.branch)
    $reportLines += ""
    $reportLines += "## Counts"
    $reportLines += ""
    $reportLines += ("- Queue: {0}" -f $queue.Count)
    $reportLines += ("- Active: {0}" -f $active.Count)
    $reportLines += ("- Done: {0}" -f $done.Count)
    $reportLines += ("- Failed: {0}" -f $failed.Count)
    $reportLines += ""
    $reportLines += "## Expected tasks"
    $reportLines += ""
    foreach ($task in $expected) {
        $reportLines += ("- {0}: {1}" -f $task.name, $task.location)
    }
    $reportLines += ""
    $reportLines += "## Likely issue"
    $reportLines += ""
    $reportLines += $result.likelyIssue
    $reportLines += ""
    $reportLines += "## Git status"
    $reportLines += ""
    $reportLines += '```text'
    foreach ($line in $result.gitStatusBranch) { $reportLines += $line }
    foreach ($line in $result.gitStatusShort) { $reportLines += $line }
    $reportLines += '```'
    $reportLines += ""
    $reportLines += "## Queue files"
    $reportLines += ""
    if ($queue.Count -eq 0) {
        $reportLines += "No queue files found."
    }
    else {
        foreach ($file in $queue) { $reportLines += ("- {0}" -f $file.name) }
    }
    $reportLines += ""
    $reportLines += "## Active files"
    $reportLines += ""
    if ($active.Count -eq 0) {
        $reportLines += "No active files found."
    }
    else {
        foreach ($file in $active) { $reportLines += ("- {0}" -f $file.name) }
    }

    $reportLines | Set-Content -LiteralPath $reportPath -Encoding UTF8

    if ($JsonOnly) {
        $result | ConvertTo-Json -Depth 20
    }
    else {
        Write-Host "Task visibility audit complete." -ForegroundColor Green
        Write-Host "JSON: $jsonPath"
        Write-Host "Report: $reportPath"
        Write-Host "Likely issue: $($result.likelyIssue)" -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}
