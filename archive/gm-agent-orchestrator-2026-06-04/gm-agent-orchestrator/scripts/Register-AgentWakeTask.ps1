[CmdletBinding()]
param(
    [string]$TaskName = "GM Agent Orchestrator Headless Wake Test",
    [string]$At = "05:52",
    [string]$ProjectName = "child-of-levistus",
    [string]$SlotName = "headless",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$startScript = Join-Path $PSScriptRoot "Start-GmAgentOrchestrator.ps1"

if (!(Test-Path $startScript)) {
    throw "Missing orchestrator start script: $startScript"
}

if ($At -notmatch "^\d{1,2}:\d{2}$") {
    throw "At must be HH:mm, for example 05:52"
}

$hour, $minute = $At.Split(":") | ForEach-Object { [int]$_ }
if ($hour -lt 0 -or $hour -gt 23 -or $minute -lt 0 -or $minute -gt 59) {
    throw "At must be a valid 24-hour local time."
}

$now = Get-Date
$runAt = Get-Date -Hour $hour -Minute $minute -Second 0
if ($runAt -le $now) {
    $runAt = $runAt.AddDays(1)
}

$argList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$startScript`"",
    "-ProjectName", "`"$ProjectName`"",
    "-SlotName", "`"$SlotName`"",
    "-RunOnce"
)

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument ($argList -join " ") `
    -WorkingDirectory $root

$trigger = New-ScheduledTaskTrigger -Once -At $runAt

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 10)

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing -and -not $Force) {
    throw "Scheduled task already exists: $TaskName. Re-run with -Force to replace it."
}

if ($existing -and $Force) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Starts one headless gm-agent-orchestrator wake test."

Write-Host "Registered one-off scheduled task: $TaskName"
Write-Host "Run time: $runAt"
Write-Host "Working directory: $root"
Write-Host "Command: powershell.exe $($argList -join ' ')"

