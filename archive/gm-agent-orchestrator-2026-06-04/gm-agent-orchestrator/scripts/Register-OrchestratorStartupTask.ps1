[CmdletBinding()]
param(
    [string]$Root = "",
    [switch]$Apply,
    [switch]$Status,
    [switch]$Unregister
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$TaskName = "OrchestratorServiceSupervisor"
$ScriptPath = Join-Path $Root "scripts\Start-OrchestratorServices.ps1"
$ActionCommand = "powershell.exe"
$ActionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -Once -EnforceHeadlessMode"

function New-TaskResult {
    param(
        [string]$Action,
        [bool]$Applied,
        [object]$Status,
        [string]$NextAction,
        [string]$Message = "",
        [string]$ErrorMessage = ""
    )

    return [pscustomobject]@{
        taskName = $TaskName
        action = $Action
        applied = $Applied
        trigger = [pscustomobject]@{
            type = "AtLogOn"
            delaySeconds = 60
        }
        command = $ActionCommand
        arguments = $ActionArgs
        workingDirectory = $Root
        status = $Status
        nextAction = $NextAction
        message = $Message
        error = $ErrorMessage
    }
}

function Get-TaskStatus {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        $taskInfo = $null
        try { $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop }
        catch {}

        return [pscustomobject]@{
            registered = $true
            state = $task.State
            lastRunTime = $(if ($null -ne $taskInfo) { $taskInfo.LastRunTime } else { $null })
            nextRunTime = $(if ($null -ne $taskInfo) { $taskInfo.NextRunTime } else { $null })
            action = $task.Actions[0].Execute + " " + $task.Actions[0].Arguments
        }
    }
    catch {
        return [pscustomobject]@{
            registered = $false
            state = "NotRegistered"
        }
    }
}

if ($Status) {
    $taskStatus = Get-TaskStatus
    New-TaskResult -Action "status" -Applied $false -Status $taskStatus -NextAction $(if ($taskStatus.registered) { "No action required." } else { "Run with -Apply to register the startup supervisor task." }) | ConvertTo-Json -Depth 20
    return
}

if ($Unregister) {
    if (-not $Apply) {
        New-TaskResult -Action "unregister" -Applied $false -Status (Get-TaskStatus) -NextAction "Run with -Apply to unregister the startup supervisor task." -Message "Dry run: would unregister scheduled task." | ConvertTo-Json -Depth 20
        return
    }
    
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        New-TaskResult -Action "unregister" -Applied $true -Status (Get-TaskStatus) -NextAction "No action required." -Message "Successfully unregistered scheduled task." | ConvertTo-Json -Depth 20
    }
    catch {
        New-TaskResult -Action "unregister" -Applied $true -Status (Get-TaskStatus) -NextAction "Inspect Windows Task Scheduler state." -ErrorMessage $_.Exception.Message | ConvertTo-Json -Depth 20
    }
    return
}

$currentStatus = Get-TaskStatus
if ($currentStatus.registered) {
    if (-not $Apply) {
        New-TaskResult -Action "register" -Applied $false -Status $currentStatus -NextAction "Run with -Apply to re-register with current settings." -Message "Dry run: task is already registered." | ConvertTo-Json -Depth 20
        return
    }
}

if (-not $Apply) {
    New-TaskResult -Action "register" -Applied $false -Status $currentStatus -NextAction "Run with -Apply to register the startup supervisor task." -Message "Dry run: would register scheduled task." | ConvertTo-Json -Depth 20
    return
}

# Registration logic
$trigger = New-ScheduledTaskTrigger -AtLogOn -RandomDelay (New-TimeSpan -Seconds 60)
$action = New-ScheduledTaskAction -Execute $ActionCommand -Argument $ActionArgs -WorkingDirectory $Root
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances Ignore

try {
    Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Settings $settings -Force
    New-TaskResult -Action "register" -Applied $true -Status (Get-TaskStatus) -NextAction "No action required." -Message "Successfully registered scheduled task." | ConvertTo-Json -Depth 20
}
catch {
    New-TaskResult -Action "register" -Applied $true -Status (Get-TaskStatus) -NextAction "Inspect Windows Task Scheduler permissions and task state." -ErrorMessage $_.Exception.Message | ConvertTo-Json -Depth 20
    exit 1
}
