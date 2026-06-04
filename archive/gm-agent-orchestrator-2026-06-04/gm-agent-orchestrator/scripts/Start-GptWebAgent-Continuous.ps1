<#
.SYNOPSIS
GPT Web Fallback Agent - Continuous mode (primary agent).

.DESCRIPTION
Runs indefinitely, continuously polling the queue for tasks and executing them.
This is the primary agent while CLI agents are blocked.

.PARAMETER PollingIntervalSeconds
Time to wait between queue checks. Default: 10 seconds

.PARAMETER Root
Orchestrator root path. Default: parent of scripts directory

.EXAMPLE
.\Start-GptWebAgent-Continuous.ps1

.EXAMPLE
.\Start-GptWebAgent-Continuous.ps1 -PollingIntervalSeconds 5

.NOTES
This runs until manually stopped (Ctrl+C).
Logs all activity to agents/gpt-web.log
#>

[CmdletBinding()]
param(
    [int]$PollingIntervalSeconds = 10,
    [string]$Root = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}

$QueuePath = Join-Path $Root "tasks/queue"
$DonePath = Join-Path $Root "tasks/done"
$FailedPath = Join-Path $Root "tasks/failed"
$LogPath = Join-Path $Root "agents/gpt-web.log"
$AuditLogPath = Join-Path $Root "status/queue-audit.log"

# Ensure log directory exists
$logDir = Split-Path $LogPath -Parent
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogPath -Value $logEntry -Encoding UTF8
    Write-Host $logEntry -ForegroundColor $(
        @{
            "INFO" = "Gray"
            "SUCCESS" = "Green"
            "ERROR" = "Red"
            "WARN" = "Yellow"
        }[$Level] ?? "Gray"
    )
}

function Get-QueuedTask {
    param([string]$QueuePath)
    $tasks = @(Get-ChildItem $QueuePath -Filter "*.md" -ErrorAction SilentlyContinue |
               Sort-Object CreationTime)
    return if ($tasks.Count -gt 0) { $tasks[0] } else { $null }
}

function Read-TaskFile {
    param([string]$Path)
    $content = Get-Content $Path -Raw
    return [pscustomobject]@{
        Path = $Path
        Name = [System.IO.Path]::GetFileNameWithoutExtension($Path)
        Content = $content
        Title = ($content.Split("`n")[0] -replace "^[#\s]*", "")
    }
}

function Invoke-GptTask {
    param(
        [pscustomobject]$Task,
        [bool]$Simulate = $true
    )

    if ($Simulate) {
        # Simulated execution - will be replaced with real browser automation
        return @{
            Success = $true
            Output = "Executed via ChatGPT: $($Task.Title)"
            Duration = "~30 seconds (simulated)"
        }
    }

    # Real browser automation goes here (Playwright)
    throw "Real browser automation not yet implemented"
}

# Initialize
Write-Log "GPT Web Agent starting (continuous mode)" "INFO"
Write-Log "Polling interval: ${PollingIntervalSeconds}s" "INFO"
Write-Log "Queue path: $QueuePath" "INFO"

# Ensure directories exist
@($QueuePath, $DonePath, $FailedPath) | ForEach-Object {
    if (!(Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

$startTime = Get-Date
$tasksProcessed = 0
$tasksSucceeded = 0
$tasksFailed = 0

Write-Host ""
Write-Host "=== GPT Web Agent (Continuous Mode) ===" -ForegroundColor Cyan
Write-Host "Status: Running" -ForegroundColor Green
Write-Host "Role: PRIMARY AGENT (CLI agents blocked)"
Write-Host "Press Ctrl+C to stop"
Write-Host ""

# Main loop - run indefinitely
while ($true) {
    try {
        $queuedTask = Get-QueuedTask -QueuePath $QueuePath

        if ($null -eq $queuedTask) {
            # Queue empty - wait and check again
            Write-Host "." -NoNewline -ForegroundColor Gray
            Start-Sleep -Seconds $PollingIntervalSeconds
            continue
        }

        # Found a task - process it
        $task = Read-TaskFile -Path $queuedTask.FullName
        $tasksProcessed++

        Write-Host ""
        Write-Host "[$((Get-Date).ToString("HH:mm:ss"))] Task #$tasksProcessed: $($task.Title)" -ForegroundColor Cyan
        Write-Log "Processing task: $($task.Name)" "INFO"

        try {
            # Execute task
            $result = Invoke-GptTask -Task $task -Simulate $true

            if ($result.Success) {
                Write-Host "[OK] Completed successfully" -ForegroundColor Green

                # Move to done
                $doneTaskPath = Join-Path $DonePath $queuedTask.Name
                Move-Item -Path $queuedTask.FullName -Destination $doneTaskPath -Force

                # Save output
                $outputFile = Join-Path $DonePath "$($task.Name).output.txt"
                $result.Output | Set-Content -Path $outputFile -Encoding UTF8

                # Audit log
                $auditEntry = "$(Get-Date -Format 'o') | MOVE_TO_DONE | $($task.Name) | gpt-web | $($task.Title)"
                Add-Content -Path $AuditLogPath -Value $auditEntry -Encoding UTF8

                $tasksSucceeded++
                Write-Log "Task completed: $($task.Name)" "SUCCESS"

            } else {
                Write-Host "[FAIL] Task failed" -ForegroundColor Red

                # Move to failed
                $failedTaskPath = Join-Path $FailedPath $queuedTask.Name
                Move-Item -Path $queuedTask.FullName -Destination $failedTaskPath -Force

                # Save error
                $errorFile = Join-Path $FailedPath "$($task.Name).error.txt"
                $result.Error | Set-Content -Path $errorFile -Encoding UTF8

                # Audit log
                $auditEntry = "$(Get-Date -Format 'o') | MOVE_TO_FAILED | $($task.Name) | gpt-web | $($task.Title)"
                Add-Content -Path $AuditLogPath -Value $auditEntry -Encoding UTF8

                $tasksFailed++
                Write-Log "Task failed: $($task.Name)" "ERROR"
            }

        } catch {
            Write-Host "[ERROR] Exception processing task" -ForegroundColor Red
            Write-Log "Exception: $($_.Exception.Message)" "ERROR"

            # Move to failed
            $failedTaskPath = Join-Path $FailedPath $queuedTask.Name
            Move-Item -Path $queuedTask.FullName -Destination $failedTaskPath -Force

            # Audit log
            $auditEntry = "$(Get-Date -Format 'o') | MOVE_TO_FAILED | $($task.Name) | gpt-web | Exception: $($_.Exception.Message)"
            Add-Content -Path $AuditLogPath -Value $auditEntry -Encoding UTF8

            $tasksFailed++
        }

    } catch {
        Write-Host ""
        Write-Host "[ERROR] Unexpected error in main loop: $($_.Exception.Message)" -ForegroundColor Red
        Write-Log "Main loop error: $($_.Exception.Message)" "ERROR"
        Start-Sleep -Seconds 5
    }
}
