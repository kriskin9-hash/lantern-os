[CmdletBinding()]
param(
    [string]$TaskName = "GM Agent Orchestrator Headless Wake Test",
    [string]$SlotName = "headless",
    [int]$RecentLogCount = 3
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$logDir = Join-Path $root "logs\$SlotName"
$queueDir = Join-Path $root "tasks\queue"
$activeDir = Join-Path $root "tasks\active"
$doneDir = Join-Path $root "tasks\done"
$failedDir = Join-Path $root "tasks\failed"

Write-Host "gm-agent-orchestrator wake status"
Write-Host "Root: $root"
Write-Host "Slot: $SlotName"
Write-Host ""

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -eq $task) {
    Write-Host "Scheduled task: missing"
}
else {
    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host "Scheduled task: $TaskName"
    Write-Host "  State: $($task.State)"
    Write-Host "  LastRunTime: $($taskInfo.LastRunTime)"
    Write-Host "  LastTaskResult: $($taskInfo.LastTaskResult)"
    Write-Host "  NextRunTime: $($taskInfo.NextRunTime)"
}

Write-Host ""
Write-Host "Task folders:"
foreach ($dir in @($queueDir, $activeDir, $doneDir, $failedDir)) {
    if (Test-Path $dir) {
        $count = @(Get-ChildItem $dir -Filter "*.md" -File -ErrorAction SilentlyContinue).Count
        Write-Host "  $(Split-Path $dir -Leaf): $count"
    }
    else {
        Write-Host "  $(Split-Path $dir -Leaf): missing"
    }
}

Write-Host ""
Write-Host "Recent logs:"
if (!(Test-Path $logDir)) {
    Write-Host "  no log dir yet: $logDir"
    exit 0
}

$logs = Get-ChildItem $logDir -Filter "*.log" -File | Sort-Object LastWriteTime -Descending | Select-Object -First $RecentLogCount
if ($logs.Count -eq 0) {
    Write-Host "  no logs yet"
    exit 0
}

foreach ($log in $logs) {
    Write-Host ""
    Write-Host "--- $($log.Name) | $($log.LastWriteTime) ---"
    Get-Content $log.FullName -Tail 40
}

Write-Host ""
Write-Host "Interpretation:"
Write-Host "  pass: scheduled task LastTaskResult is 0, a task moved to done, and latest log shows validation passed or Done."
Write-Host "  fail: task moved to failed, LastTaskResult is non-zero, or latest log shows Runner failure / Non-token failure / Validation failed."
Write-Host "  pending: task is still active or latest log shows rate/token limited sleeping."

