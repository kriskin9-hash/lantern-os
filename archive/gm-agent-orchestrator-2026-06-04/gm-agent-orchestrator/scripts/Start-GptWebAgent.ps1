<#
.SYNOPSIS
GPT Web Fallback Agent - Browser-based task execution when CLI agents are blocked.

.DESCRIPTION
This agent launches a browser, logs into ChatGPT, and claims/executes tasks from the queue.
Uses Playwright for reliable browser automation.

.PARAMETER SlotName
Agent slot name. Default: gpt-web

.PARAMETER Root
Orchestrator root path. Default: parent of scripts directory

.PARAMETER QueuePath
Task queue directory. Default: tasks/queue

.PARAMETER DonePath
Completed tasks directory. Default: tasks/done

.PARAMETER FailedPath
Failed tasks directory. Default: tasks/failed

.PARAMETER Headless
Run browser in headless mode (no visible window). Default: $false

.PARAMETER MaxTasks
Maximum tasks to execute before stopping. Default: 1 (test mode)

.EXAMPLE
.\Start-GptWebAgent.ps1 -MaxTasks 5

.NOTES
Requires: Node.js with Playwright installed
Cost: One browser instance per execution
#>

[CmdletBinding()]
param(
    [string]$SlotName = "gpt-web",
    [string]$Root = "",
    [string]$QueuePath = "tasks/queue",
    [string]$DonePath = "tasks/done",
    [string]$FailedPath = "tasks/failed",
    [bool]$Headless = $false,
    [int]$MaxTasks = 1,
    # When the orchestrator has already claimed a task and moved it to tasks/active,
    # pass the full path here. The script will execute that file directly instead of
    # scanning the queue, and will NOT move it (the orchestrator lifecycle owns that).
    [string]$TaskFile = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$QueuePath = Join-Path $Root $QueuePath
$DonePath = Join-Path $Root $DonePath
$FailedPath = Join-Path $Root $FailedPath

Write-Host "=== GPT Web Fallback Agent ===" -ForegroundColor Cyan
Write-Host "Slot: $SlotName"
Write-Host "Queue: $QueuePath"
Write-Host "Max tasks: $MaxTasks"
Write-Host ""

if (!(Test-Path $QueuePath)) {
    Write-Error "Queue directory not found: $QueuePath"
    exit 1
}

New-Item -ItemType Directory -Force -Path $DonePath | Out-Null
New-Item -ItemType Directory -Force -Path $FailedPath | Out-Null

$playwrightScript = @'
const { chromium } = require('playwright');
const fs = require('fs');

async function main() {
    const taskFile = process.argv[2];
    const headless = process.argv[3] === 'true';

    if (!taskFile || !fs.existsSync(taskFile)) {
        console.error('Task file not found:', taskFile);
        process.exit(1);
    }

    const taskContent = fs.readFileSync(taskFile, 'utf-8');
    const browser = await chromium.launch({ headless });
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
        await page.goto('https://chat.openai.com', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);

        if (page.url().includes('login') || page.url().includes('auth')) {
            console.log('Not authenticated. Please log in manually in the opened browser.');
            console.log('Browser will wait for 5 minutes for authentication.');
            for (let i = 0; i < 30; i++) {
                await page.waitForTimeout(10000);
                if (!page.url().includes('login') && !page.url().includes('auth')) {
                    console.log('Authentication detected.');
                    break;
                }
            }
        }

        const inputSelector = 'textarea[placeholder*=message i], input[placeholder*=message i]';
        await page.waitForSelector(inputSelector, { timeout: 30000 });
        const input = await page.$(inputSelector);
        if (!input) {
            throw new Error('Could not find chat input field');
        }

        const taskTitle = taskContent.split('\n')[0];
        console.log('Executing task:', taskTitle);
        await input.focus();
        await input.type(taskContent);
        await page.keyboard.press('Control+Enter');
        console.log('Waiting for response...');
        await page.waitForTimeout(5000);

        const messages = await page.$$eval('[data-testid="conversation"] div[role="article"]', els => els.map(el => el.innerText));
        const response = messages.length > 0 ? messages[messages.length - 1] : '';
        if (!response) {
            throw new Error('No response received from ChatGPT');
        }

        console.log('TASK_COMPLETE');
        console.log('RESPONSE:', response.substring(0, 1000));
    }
    catch (error) {
        console.error('TASK_FAILED');
        console.error('ERROR:', error.message);
        process.exit(1);
    }
    finally {
        await browser.close();
    }
}

main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});
'@

Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    $nodeVersion = & node --version 2>&1
    Write-Host "Node.js: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Error "Node.js is not installed. Please install from https://nodejs.org/"
    exit 1
}

try {
    $playwrightTest = & npm ls playwright 2>&1 | Select-String "playwright"
    if (-not $playwrightTest) {
        Write-Host "Installing Playwright..." -ForegroundColor Yellow
        & npm install playwright
    }
    Write-Host "Playwright is available" -ForegroundColor Green
}
catch {
    Write-Error "Failed to verify Playwright installation"
    exit 1
}

$tasksProcessed = 0

# If a specific task file was pre-claimed by the orchestrator, execute it directly
# without scanning the queue and without moving the file (orchestrator owns lifecycle).
if (-not [string]::IsNullOrWhiteSpace($TaskFile)) {
    if (-not (Test-Path -LiteralPath $TaskFile -PathType Leaf)) {
        Write-Error "Specified -TaskFile not found: $TaskFile"
        exit 1
    }
    Write-Host "Executing pre-claimed task: $TaskFile" -ForegroundColor Cyan
    $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) ("gpt-agent-{0}.js" -f ([guid]::NewGuid()))
    Set-Content -Path $tempScript -Value $playwrightScript -Encoding UTF8
    try {
        $output = & node $tempScript $TaskFile ($Headless.ToString().ToLower()) 2>&1
        $isComplete = $output | Select-String "TASK_COMPLETE"
        if ($isComplete) {
            Write-Host "Task completed successfully" -ForegroundColor Green
            exit 0
        }
        else {
            $errorMsg = $output | Select-String "ERROR:" | Select-Object -First 1
            Write-Host "Task failed: $errorMsg" -ForegroundColor Red
            exit 1
        }
    }
    finally {
        if (Test-Path $tempScript) { Remove-Item $tempScript -Force -ErrorAction SilentlyContinue }
    }
}

while ($tasksProcessed -lt $MaxTasks) {
    $queuedTasks = @(Get-ChildItem $QueuePath -Filter "*.md" -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne ".gitkeep" } | Sort-Object CreationTime)

    if (@($queuedTasks).Count -eq 0) {
        Write-Host "No queued tasks." -ForegroundColor Gray
        break
    }

    $task = $queuedTasks[0]
    $taskPath = $task.FullName
    $taskName = $task.BaseName

    Write-Host ""
    Write-Host ("Task {0}/{1}: {2}" -f ($tasksProcessed + 1), $MaxTasks, $taskName) -ForegroundColor Cyan

    $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) ("gpt-agent-{0}.js" -f ([guid]::NewGuid()))
    Set-Content -Path $tempScript -Value $playwrightScript -Encoding UTF8

    try {
        $output = & node $tempScript $taskPath ($Headless.ToString().ToLower()) 2>&1
        $isComplete = $output | Select-String "TASK_COMPLETE"

        if ($isComplete) {
            Write-Host "Task completed successfully" -ForegroundColor Green
            $doneFile = Join-Path $DonePath $task.Name
            Move-Item -Path $taskPath -Destination $doneFile -Force
            $outputFile = Join-Path $DonePath ("{0}.output.txt" -f $taskName)
            $output | Set-Content -Path $outputFile -Encoding UTF8
            Write-Host "Result saved to: $doneFile" -ForegroundColor Gray
            $tasksProcessed++
        }
        else {
            Write-Host "Task failed" -ForegroundColor Red
            $errorMsg = $output | Select-String "ERROR:" | Select-Object -First 1
            if ($errorMsg) {
                Write-Host "Error: $errorMsg" -ForegroundColor Red
            }
            $failedFile = Join-Path $FailedPath $task.Name
            Move-Item -Path $taskPath -Destination $failedFile -Force
            $errorFile = Join-Path $FailedPath ("{0}.error.txt" -f $taskName)
            $output | Set-Content -Path $errorFile -Encoding UTF8
            Write-Host "Error saved to: $failedFile" -ForegroundColor Gray
            $tasksProcessed++
        }
    }
    catch {
        Write-Error "Exception executing task: $($_.Exception.Message)"
        $failedFile = Join-Path $FailedPath $task.Name
        Move-Item -Path $taskPath -Destination $failedFile -Force
        $tasksProcessed++
    }
    finally {
        if (Test-Path $tempScript) {
            Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Tasks processed: $tasksProcessed"
Write-Host ("Done: {0}" -f @(Get-ChildItem $DonePath -Filter "*.md" -File -ErrorAction SilentlyContinue).Count)
Write-Host ("Failed: {0}" -f @(Get-ChildItem $FailedPath -Filter "*.md" -File -ErrorAction SilentlyContinue).Count)
Write-Host ""

if ($tasksProcessed -gt 0) {
    Write-Host ("GPT web agent processed {0} task(s)" -f $tasksProcessed) -ForegroundColor Green
    exit 0
}

Write-Host "No tasks were processed" -ForegroundColor Yellow
exit 0
