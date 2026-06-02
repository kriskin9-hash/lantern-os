<#
.SYNOPSIS
GPT Web Fallback Agent - Simplified version for testing queue interaction.

.DESCRIPTION
This is a proof-of-concept version that demonstrates claiming and processing
queue items. It uses simulated browser automation (placeholder for Playwright).

To make it real, replace the Invoke-GptTask function with actual browser automation.

.PARAMETER MaxTasks
Maximum tasks to process. Default: 1

.EXAMPLE
.\Start-GptWebAgent-Simple.ps1 -MaxTasks 5

.NOTES
This version validates the queue integration. Real browser automation comes next.
#>

[CmdletBinding()]
param(
    [int]$MaxTasks = 1,
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

Write-Host "=== GPT Web Agent (Test Mode) ===" -ForegroundColor Cyan
Write-Host "Root: $Root"
Write-Host "Queue: $QueuePath"
Write-Host "Mode: Queue integration test"
Write-Host ""

# Ensure directories exist
@($QueuePath, $DonePath, $FailedPath) | ForEach-Object {
    if (!(Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

function Get-QueuedTask {
    param([string]$QueuePath)

    $tasks = @(Get-ChildItem $QueuePath -Filter "*.md" -ErrorAction SilentlyContinue |
               Sort-Object CreationTime)

    if ($tasks.Count -gt 0) {
        return $tasks[0]
    }
    return $null
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

    Write-Host "  Title: $($Task.Title)" -ForegroundColor Gray
    Write-Host "  Processing..." -ForegroundColor Yellow

    if ($Simulate) {
        # Simulated execution - replace with real browser automation
        Write-Host "  [SIMULATED] Would launch browser to ChatGPT" -ForegroundColor DarkGray
        Write-Host "  [SIMULATED] Would paste task: $($Task.Title)" -ForegroundColor DarkGray
        Write-Host "  [SIMULATED] Would wait for response" -ForegroundColor DarkGray

        # Return success with dummy output
        return @{
            Success = $true
            Output = "Simulated response from ChatGPT: Task executed successfully."
            Duration = "~30 seconds (simulated)"
        }
    }

    # Real implementation would go here with Playwright
    <#
    # TODO: Implement real browser automation
    # 1. Launch Chrome with --remote-debugging-port
    # 2. Connect via CDP
    # 3. Navigate to chat.openai.com
    # 4. Authenticate if needed
    # 5. Paste task content
    # 6. Wait for response
    # 7. Collect output
    #>

    throw "Real browser automation not yet configured"
}

# Main loop
$tasksProcessed = 0
$tasksSucceeded = 0
$tasksFailed = 0

Write-Host "Scanning queue..." -ForegroundColor Yellow

while ($tasksProcessed -lt $MaxTasks) {
    $queuedTask = Get-QueuedTask -QueuePath $QueuePath

    if ($null -eq $queuedTask) {
        Write-Host "No queued tasks found." -ForegroundColor Gray
        break
    }

    $task = Read-TaskFile -Path $queuedTask.FullName
    $taskNum = $tasksProcessed + 1

    Write-Host ""
    Write-Host "Task $taskNum/$MaxTasks" -ForegroundColor Cyan
    Write-Host "File: $($queuedTask.Name)" -ForegroundColor Gray

    try {
        # Execute task
        $result = Invoke-GptTask -Task $task -Simulate $true

        if ($result.Success) {
            Write-Host "[OK] Success" -ForegroundColor Green
            Write-Host "  Output: $($result.Output.Substring(0, [Math]::Min(60, $result.Output.Length)))..." -ForegroundColor Gray

            # Move to done
            $doneTaskPath = Join-Path $DonePath $queuedTask.Name
            Move-Item -Path $queuedTask.FullName -Destination $doneTaskPath -Force

            # Save output
            $outputFile = Join-Path $DonePath "$($task.Name).output.txt"
            $result.Output | Set-Content -Path $outputFile -Encoding UTF8

            $tasksSucceeded++
        } else {
            Write-Host "[FAIL] Failed" -ForegroundColor Red
            Write-Host "  Error: $($result.Error)" -ForegroundColor Red

            # Move to failed
            $failedTaskPath = Join-Path $FailedPath $queuedTask.Name
            Move-Item -Path $queuedTask.FullName -Destination $failedTaskPath -Force

            # Save error
            $errorFile = Join-Path $FailedPath "$($task.Name).error.txt"
            $result.Error | Set-Content -Path $errorFile -Encoding UTF8

            $tasksFailed++
        }
    } catch {
        Write-Host "[ERROR] Exception" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red

        # Move to failed
        $failedTaskPath = Join-Path $FailedPath $queuedTask.Name
        Move-Item -Path $queuedTask.FullName -Destination $failedTaskPath -Force

        $tasksFailed++
    }

    $tasksProcessed++
}

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "Processed: $tasksProcessed"
Write-Host "Succeeded: $tasksSucceeded" -ForegroundColor Green
Write-Host "Failed: $tasksFailed" -ForegroundColor Red
Write-Host ""
Write-Host "Queue now contains:" -ForegroundColor Yellow
$remaining = @(Get-ChildItem $QueuePath -Filter "*.md" -ErrorAction SilentlyContinue)
if ($remaining.Count -gt 0) {
    $remaining | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
} else {
    Write-Host "  (empty)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done:" -ForegroundColor Yellow
$done = @(Get-ChildItem $DonePath -Filter "*.md" -ErrorAction SilentlyContinue)
if ($done.Count -gt 0) {
    $done | ForEach-Object { Write-Host "  [DONE] $($_.Name)" -ForegroundColor Green }
} else {
    Write-Host "  (empty)" -ForegroundColor Gray
}

if ($tasksSucceeded -gt 0) {
    Write-Host ""
    Write-Host "[SUCCESS] Processed $tasksSucceeded task(s)" -ForegroundColor Green
    exit 0
} elseif ($tasksProcessed -gt 0) {
    Write-Host ""
    Write-Host "[PARTIAL] Processed $tasksProcessed task(s) with failures" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host ""
    Write-Host "[INFO] No tasks to process" -ForegroundColor Gray
    exit 0
}
