[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$TaskName = "p0-expose-openapi-schema-for-chatgpt-connector.md",
    [string]$SlotName = "headless",
    [switch]$SkipGitPull,
    [switch]$NoStart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function New-Result {
    param(
        [bool]$Ok,
        [string]$State,
        [string]$ErrorMessage = "",
        [hashtable]$Extra = @{}
    )

    $payload = [ordered]@{
        ok = $Ok
        state = $State
        error = $ErrorMessage
        root = $Root
        slot = $SlotName
        taskName = $TaskName
        generatedAt = (Get-Date).ToString("o")
    }

    foreach ($key in $Extra.Keys) { $payload[$key] = $Extra[$key] }
    [pscustomobject]$payload
}

function Invoke-CapturedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $Root,
        [int]$TimeoutSeconds = 0
    )

    $temp = [System.IO.Path]::GetTempFileName()
    $out = "$temp.out"
    $err = "$temp.err"

    try {
        $process = Start-Process -FilePath $FilePath `
            -ArgumentList $Arguments `
            -WorkingDirectory $WorkingDirectory `
            -NoNewWindow `
            -PassThru `
            -RedirectStandardOutput $out `
            -RedirectStandardError $err

        if ($TimeoutSeconds -gt 0) {
            $done = $process.WaitForExit($TimeoutSeconds * 1000)
            if (-not $done) {
                try { $process.Kill() } catch {}
            }
        }
        else {
            $process.WaitForExit()
            $done = $true
        }

        $stdout = if (Test-Path -LiteralPath $out) { Get-Content -LiteralPath $out -Raw } else { "" }
        $stderr = if (Test-Path -LiteralPath $err) { Get-Content -LiteralPath $err -Raw } else { "" }

        return [pscustomobject]@{
            exitCode = if ($done) { $process.ExitCode } else { $null }
            timedOut = -not $done
            stdout = $stdout
            stderr = $stderr
            combined = ("$stdout`n$stderr").Trim()
        }
    }
    finally {
        Remove-Item -LiteralPath $temp,$out,$err -Force -ErrorAction SilentlyContinue
    }
}

function Test-PowerShellFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $Path), [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) {
        $message = ($errors | ForEach-Object { $_.Message }) -join "; "
        throw ("Parser failed for {0}: {1}" -f $Path, $message)
    }
}

function Get-Counts {
    $states = @("queue", "active", "done", "failed")
    $counts = [ordered]@{}
    foreach ($state in $states) {
        $dir = Join-Path $Root "tasks\$state"
        $counts[$state] = if (Test-Path -LiteralPath $dir -PathType Container) { @(Get-ChildItem -LiteralPath $dir -Filter "*.md" -File -ErrorAction SilentlyContinue).Count } else { 0 }
    }
    [pscustomobject]$counts
}

function Get-RelativePathOrNull {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    return (Resolve-Path -LiteralPath $Path).Path.Replace($Root, "").TrimStart("\")
}

try {
    if (!(Test-Path -LiteralPath $Root -PathType Container)) { throw "Missing root: $Root" }
    Set-Location $Root

    $auditDir = Join-Path $Root "logs\control-actions"
    New-Item -ItemType Directory -Force -Path $auditDir | Out-Null

    $steps = New-Object System.Collections.Generic.List[object]
    $gitPull = $null

    if (-not $SkipGitPull) {
        $pull = Invoke-CapturedCommand -FilePath "git" -Arguments @("pull", "--ff-only", "origin", "master") -WorkingDirectory $Root
        $gitPull = [pscustomobject]@{
            exitCode = $pull.exitCode
            timedOut = $pull.timedOut
            stdout = $pull.stdout
            stderr = $pull.stderr
        }
        $steps.Add([pscustomobject]@{ step = "git_pull"; gitPull = $gitPull })

        if ($pull.timedOut) { throw "git pull timed out" }
        if ($null -eq $pull.exitCode) { throw "git pull did not return an exit code" }
        if ([int]$pull.exitCode -ne 0) { throw ("git pull failed with exit code {0}: {1}" -f $pull.exitCode, $pull.combined) }
    }
    else {
        $gitPull = [pscustomobject]@{ skipped = $true; exitCode = $null; stdout = ""; stderr = "" }
        $steps.Add([pscustomobject]@{ step = "git_pull"; skipped = $true })
    }

    $patcher = Join-Path $Root "scripts\Patch-StartAgentSlotNativeCapture.ps1"
    if (Test-Path -LiteralPath $patcher -PathType Leaf) {
        $patch = Invoke-CapturedCommand -FilePath "powershell" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $patcher, "-Root", $Root) -WorkingDirectory $Root
        $steps.Add([pscustomobject]@{ step = "patch_native_capture"; exitCode = $patch.exitCode; output = $patch.combined })
        if ($patch.exitCode -ne 0) { throw "Native capture patch failed: $($patch.combined)" }
    }
    else {
        $steps.Add([pscustomobject]@{ step = "patch_native_capture"; skipped = $true; reason = "patcher_not_found" })
    }

    $filesToValidate = @(
        "scripts\Start-AgentSlot.ps1",
        "scripts\Start-GmAgentOrchestrator.ps1",
        "scripts\Invoke-OpenHandsAgent.ps1"
    )

    foreach ($relative in $filesToValidate) {
        $path = Join-Path $Root $relative
        Test-PowerShellFile -Path $path
        $steps.Add([pscustomobject]@{ step = "parser_check"; path = $relative; ok = $true })
    }

    $wrapper = Join-Path $Root "scripts\Invoke-OpenHandsAgent.ps1"
    $version = Invoke-CapturedCommand -FilePath "powershell" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $wrapper, "--version") -WorkingDirectory $Root -TimeoutSeconds 60
    $steps.Add([pscustomobject]@{ step = "openhands_version"; exitCode = $version.exitCode; output = $version.combined })
    if ($version.exitCode -ne 0) { throw "OpenHands wrapper version check failed: $($version.combined)" }

    $before = Get-Counts

    $queuePath = Join-Path $Root ("tasks\queue\{0}" -f $TaskName)
    $activePath = Join-Path $Root ("tasks\active\{0}__{1}" -f $SlotName, $TaskName)
    $failedPath = Join-Path $Root ("tasks\failed\{0}" -f $TaskName)
    $activeTaskPresent = Test-Path -LiteralPath $activePath -PathType Leaf

    if ($activeTaskPresent) {
        $steps.Add([pscustomobject]@{ step = "active_task_guard"; state = "active_task_present"; path = "tasks\active\$SlotName`__$TaskName" })
        $afterRequeue = Get-Counts
        $afterStart = $afterRequeue
    }
    else {
        if (Test-Path -LiteralPath $queuePath -PathType Leaf) {
            $steps.Add([pscustomobject]@{ step = "requeue_task"; state = "already_in_queue"; path = "tasks\queue\$TaskName" })
        }
        elseif (Test-Path -LiteralPath $failedPath -PathType Leaf) {
            $moveScript = Join-Path $Root "scripts\Move-OrchestratorTask.ps1"
            if (!(Test-Path -LiteralPath $moveScript -PathType Leaf)) { throw "Missing move helper: $moveScript" }
            $move = Invoke-CapturedCommand -FilePath "powershell" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $moveScript, "-Root", $Root, "-From", "failed", "-To", "queue", "-TaskName", $TaskName, "-Slot", $SlotName, "-Reason", "one-shot disaster recovery requeue") -WorkingDirectory $Root
            $steps.Add([pscustomobject]@{ step = "requeue_task"; exitCode = $move.exitCode; output = $move.combined })
            if ($move.exitCode -ne 0) { throw "Requeue failed: $($move.combined)" }
        }
        else {
            $steps.Add([pscustomobject]@{ step = "requeue_task"; state = "task_not_found_in_failed_or_queue"; task = $TaskName })
        }

        $afterRequeue = Get-Counts

        if (-not $NoStart) {
            $startScript = Join-Path $Root "scripts\Start-GmAgentOrchestrator.ps1"
            $start = Invoke-CapturedCommand -FilePath "powershell" -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $startScript, "-SlotName", $SlotName, "-RunOnce", "-Headless", "-Supervised") -WorkingDirectory $Root -TimeoutSeconds 900
            $steps.Add([pscustomobject]@{ step = "start_headless_supervised"; exitCode = $start.exitCode; timedOut = $start.timedOut; output = $start.combined })
        }
        else {
            $steps.Add([pscustomobject]@{ step = "start_headless_supervised"; skipped = $true; reason = "NoStart" })
        }

        $afterStart = Get-Counts
    }

    $statusPath = Join-Path $Root ("status\{0}.json" -f $SlotName)
    $status = if (Test-Path -LiteralPath $statusPath -PathType Leaf) { Get-Content -LiteralPath $statusPath -Raw } else { "" }

    $latestLog = @(Get-ChildItem -LiteralPath (Join-Path $Root "logs\$SlotName") -Filter "*.log" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
    $latestLogTail = ""
    $latestLogPath = $null
    if ($latestLog.Count -gt 0) {
        $latestLogPath = $latestLog[0].FullName
        $latestLogTail = (Get-Content -LiteralPath $latestLogPath -Tail 120 -ErrorAction SilentlyContinue) -join "`n"
    }

    $auditPayload = [pscustomobject]@{
        ok = $true
        action = "Invoke-HeadlessDisasterRecovery"
        slot = $SlotName
        taskName = $TaskName
        gitPull = $gitPull
        before = $before
        afterRequeue = $afterRequeue
        afterStart = $afterStart
        activeTaskPresent = $activeTaskPresent
        statusPath = Get-RelativePathOrNull -Path $statusPath
        status = $status
        latestLogPath = Get-RelativePathOrNull -Path $latestLogPath
        latestLogTail = $latestLogTail
        steps = @($steps)
        generatedAt = (Get-Date).ToString("o")
    }

    $auditPath = Join-Path $auditDir ("{0}-headless_disaster_recovery.json" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
    $auditPayload | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath $auditPath -Encoding UTF8

    $state = if ($activeTaskPresent) { "active_task_preserved" } else { "completed" }
    $result = New-Result -Ok $true -State $state -Extra @{
        gitPull = $gitPull
        before = $before
        afterRequeue = $afterRequeue
        afterStart = $afterStart
        activeTaskPresent = $activeTaskPresent
        statusPath = Get-RelativePathOrNull -Path $statusPath
        latestLogPath = Get-RelativePathOrNull -Path $latestLogPath
        auditPath = Get-RelativePathOrNull -Path $auditPath
        latestLogTail = $latestLogTail
        steps = @($steps)
    }
}
catch {
    $errorAuditPath = Join-Path (Join-Path $Root "logs\control-actions") ("{0}-headless_disaster_recovery_error.json" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
    [pscustomobject]@{
        ok = $false
        action = "Invoke-HeadlessDisasterRecovery"
        slot = $SlotName
        taskName = $TaskName
        error = $_.Exception.Message
        gitPull = $gitPull
        generatedAt = (Get-Date).ToString("o")
    } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $errorAuditPath -Encoding UTF8

    $result = New-Result -Ok $false -State "error" -ErrorMessage $_.Exception.Message -Extra @{ gitPull = $gitPull; auditPath = Get-RelativePathOrNull -Path $errorAuditPath }
}

$result | ConvertTo-Json -Depth 50
