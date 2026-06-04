[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function Get-RelativePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    return $Path.Replace($Root, "").TrimStart("\")
}

function Remove-UnsafeControlChars {
    param([string]$Text)
    if ($null -eq $Text) { return "" }
    return ([regex]::Replace($Text, "[\x00-\x08\x0B\x0C\x0E-\x1F]", ""))
}

function Resolve-OrchestratorPath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    if ([System.IO.Path]::IsPathRooted($Path)) { return $Path }
    return Join-Path $Root $Path
}

function Read-JsonFileOrNull {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    if (!(Test-Path $Path)) { return $null }
    try { return Get-Content $Path -Raw | ConvertFrom-Json }
    catch { return $null }
}

function Get-ConfigPath {
    param([string]$Name)
    $local = Join-Path $Root ("config\{0}.json" -f $Name)
    $example = Join-Path $Root ("config\{0}.example.json" -f $Name)
    if (Test-Path $local) { return $local }
    if (Test-Path $example) { return $example }
    return ""
}

function Get-TaskTitle {
    param([string]$Path)
    if (!(Test-Path $Path)) { return "Unknown task" }
    try {
        $lines = Get-Content $Path -TotalCount 40 -Encoding UTF8 -ErrorAction Stop
        foreach ($line in $lines) {
            $text = ([string]$line).Trim()
            if ([string]::IsNullOrWhiteSpace($text)) { continue }
            if ($text -match "^#\s*(.+)$") { return $Matches[1].Trim() }
            if ($text -match "^Title:\s*(.+)$") { return $Matches[1].Trim() }
        }
    }
    catch {}
    return [System.IO.Path]::GetFileNameWithoutExtension($Path)
}

function Get-TaskIssue {
    param([string]$Name)
    if ($Name -match "(?:^|[^0-9])0*([1-9][0-9]{0,4})(?:-|_)") { return [int]$Matches[1] }
    return $null
}

function Get-FileSummary {
    param([string]$Path)
    if (!(Test-Path $Path)) { return @() }
    return @(Get-ChildItem $Path -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne ".gitkeep" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 20 |
        ForEach-Object {
            [pscustomobject]@{
                name = $_.Name
                title = Get-TaskTitle -Path $_.FullName
                issue = Get-TaskIssue -Name $_.Name
                path = Get-RelativePath -Path $_.FullName
                bytes = $_.Length
                lastWriteTime = $_.LastWriteTime.ToString("o")
                ageMinutes = [Math]::Round(((Get-Date) - $_.LastWriteTime).TotalMinutes, 1)
            }
        })
}

function Get-LatestLog {
    param([string]$Path)
    if (!(Test-Path $Path)) { return $null }
    $log = Get-ChildItem $Path -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -eq $log) { return $null }
    $tailLines = @()
    try { $tailLines = @(Get-Content $log.FullName -Tail 60 -ErrorAction Stop) }
    catch { $tailLines = @("Could not read log tail: $($_.Exception.Message)") }
    $tail = Remove-UnsafeControlChars -Text ($tailLines -join "`n")
    $important = "No important log line found yet."
    for ($i = $tailLines.Count - 1; $i -ge 0; $i--) {
        $line = Remove-UnsafeControlChars -Text (([string]$tailLines[$i]).Trim())
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line -match "(?i)(failed|blocked|error|limit|auth|missing|claimed|done|validation|sleeping|rate|quota|MCP|server|executable|fatal|exception|locked|commit|modified|changed)") {
            $important = $line
            break
        }
    }
    return [pscustomobject]@{
        name = $log.Name
        path = Get-RelativePath -Path $log.FullName
        lastWriteTime = $log.LastWriteTime.ToString("o")
        ageMinutes = [Math]::Round(((Get-Date) - $log.LastWriteTime).TotalMinutes, 1)
        importantLine = (Remove-UnsafeControlChars -Text $important)
        tail = $tail
    }
}

function Get-LogTaskName {
    param([string]$LogName)
    if ([string]::IsNullOrWhiteSpace($LogName)) { return "" }
    if ($LogName -match "^\d{8}-\d{6}-(.+)\.log$") { return [string]$Matches[1] }
    return ""
}

function Get-SlotRuntimeStatus {
    param([string]$SlotName)
    $path = Join-Path (Join-Path $Root "status") ("{0}.json" -f $SlotName)
    $status = Read-JsonFileOrNull -Path $path
    if ($null -eq $status) { return $null }
    return [pscustomobject]@{
        slot = [string]$status.slot
        state = [string]$status.state
        reason = [string]$status.reason
        underlyingReason = $(if ($null -eq $status.PSObject.Properties["underlyingReason"]) { "" } else { [string]$status.underlyingReason })
        claimState = $(if ($null -eq $status.PSObject.Properties["claimState"]) { "" } else { [string]$status.claimState })
        nextAction = [string]$status.nextAction
        updatedAt = [string]$status.updatedAt
        path = Get-RelativePath -Path $path
    }
}

function Get-SlotRunnerEvidence {
    param([string]$SlotName)
    $matches = @()
    try {
        $matches = @(Get-CimInstance Win32_Process -ErrorAction Stop |
            Where-Object {
                $_.Name -match '^powershell(\.exe)?$' -and
                [string]$_.CommandLine -match 'Start-AgentSlot|Start-GmAgentOrchestrator' -and
                [string]$_.CommandLine -match [regex]::Escape($SlotName)
            })
    }
    catch {
        return [pscustomobject]@{ count = 0; recent = $false; processIds = @(); error = $_.Exception.Message }
    }

    $recent = $false
    $ids = @()
    foreach ($match in $matches) {
        $ids += [int]$match.ProcessId
        if ($null -ne $match.CreationDate) {
            $ageMinutes = ((Get-Date) - $match.CreationDate).TotalMinutes
            if ($ageMinutes -le 15) { $recent = $true }
        }
    }

    return [pscustomobject]@{
        count = @($matches).Count
        recent = $recent
        processIds = @($ids)
        error = ""
    }
}

function Get-BlockerFromText {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }

    if ($Text -match "(?i)(insufficient.quota|quota.exceeded|billing|payment|exceeded.*quota)") {
        return [pscustomobject]@{ kind = "quota_failed"; label = "API quota or billing limit exceeded"; severity = "blocked"; nextAction = "Check API account billing/quota, then rerun the slot." }
    }
    if ($Text -match "(?i)(\b404\b|model not found|api(?:\s+endpoint)?\s+not found|resource not found)") {
        return [pscustomobject]@{ kind = "api_endpoint_or_model_failed"; label = "API endpoint or model failed"; severity = "blocked"; nextAction = "Verify the configured API endpoint and model, then rerun the slot." }
    }
    if ($Text -match "(?i)(Cannot validate argument on parameter 'Command'|invalid.*command|unknown command)") {
        return [pscustomobject]@{ kind = "runner_config_failed"; label = "Runner command/config failed"; severity = "blocked"; nextAction = "Fix the slot command configuration before rerunning the slot." }
    }
    if ($Text -match "(?i)(rate limit|usage limit|token limit|too many requests|limit reached|tokens?.*replenish|429)") {
        return [pscustomobject]@{ kind = "token_limit"; label = "Token or usage limit"; severity = "sleeping"; nextAction = "Wait for the agent limit to reset, then rerun the slot." }
    }
    if ($Text -match "(?i)\b(auth|authentication|credentials|login|sign.?in|401|unauthorized)\b") {
        $logText = ""
        if ($latestLog) {
            $logText = @(
                [string]$latestLog.importantLine
                [string]$latestLog.tail
            ) -join "`n"
        }

        $failureKind = "auth_failed"
        $failureLabel = "Agent sign-in/auth failed"
        $failureNextAction = "Run the agent login command, then rerun the slot."

        if ($logText -match "out of extra usage|quota|rate limit|token") {
            $failureKind = "quota_or_token_limit"
            $failureLabel = "Agent quota/token limit"
            $failureNextAction = "Wait for quota reset or switch to the local MCP/PowerShell recovery path."
        }
        elseif ($logText -match "NativeCommandError|FullyQualifiedErrorId|RemoteException") {
            $failureKind = "powershell_native_command_error"
            $failureLabel = "PowerShell native command error"
            $failureNextAction = "Inspect raw stdout/stderr and avoid treating native command wrapper noise as auth failure."
        }
        elseif ($logText -match "not recognized as the name of a cmdlet|CommandNotFoundException") {
            $failureKind = "command_not_found"
            $failureLabel = "Command not found"
            $failureNextAction = "Verify the script or executable path before rerunning."
        }

        return [pscustomobject]@{ kind = $failureKind; label = $failureLabel; severity = "blocked"; nextAction = $failureNextAction }
    }
    if ($Text -match "(?i)(MCP|server|run-room-editor-mcp|missing.*tool|executable not found|not found on PATH)") {
        return [pscustomobject]@{ kind = "missing_tool"; label = "Missing tool or MCP server"; severity = "blocked"; nextAction = "Fix the missing tool path or server config, then rerun the slot." }
    }
    if ($Text -match "(?i)\bvalidation failed\b" -or $Text -match "(?i)\bfailed validation\b(?!\s+cycle)") {
        return [pscustomobject]@{ kind = "validation_failed"; label = "Validation failed"; severity = "blocked"; nextAction = "Open the latest log, fix the first validation failure, then rerun validation." }
    }
    if ($Text -match "(?i)(Non-token failure|Runner failure|exception|fatal|crash)") {
        return [pscustomobject]@{ kind = "runner_failed"; label = "Runner or agent crashed"; severity = "blocked"; nextAction = "Open the latest slot log and fix the runner failure before requeueing work." }
    }
    return $null
}

function Get-ManualSlotLock {
    param([string]$SlotName)
    $path = Join-Path (Join-Path $Root "locks") ("{0}.manual.lock" -f $SlotName)
    if (!(Test-Path $path)) { return $null }
    try {
        $lock = Get-Content $path -Raw | ConvertFrom-Json
        $expired = $false
        if ($null -ne $lock.expiresAt -and -not [string]::IsNullOrWhiteSpace([string]$lock.expiresAt)) { $expired = ([datetime]$lock.expiresAt) -lt (Get-Date) }
        return [pscustomobject]@{ slot = [string]$lock.slot; owner = [string]$lock.owner; reason = [string]$lock.reason; createdAt = [string]$lock.createdAt; expiresAt = $lock.expiresAt; expired = $expired; machine = [string]$lock.machine; path = Get-RelativePath -Path $path }
    }
    catch {
        return [pscustomobject]@{ slot = $SlotName; owner = "unknown"; reason = "manual lock file could not be parsed"; createdAt = ""; expiresAt = $null; expired = $false; machine = "unknown"; path = Get-RelativePath -Path $path }
    }
}

function Get-AgentLimitMap {
    $map = @{}
    $source = Get-ConfigPath -Name "agent-limits"
    $config = Read-JsonFileOrNull -Path $source
    if ($null -eq $config -or $null -eq $config.limits) { return $map }
    foreach ($limit in @($config.limits)) {
        if ($null -eq $limit.slot -or [string]::IsNullOrWhiteSpace([string]$limit.slot)) { continue }
        $map[[string]$limit.slot] = [pscustomobject]@{ slot = [string]$limit.slot; state = [string]$limit.state; reason = [string]$limit.reason; resetAt = [string]$limit.resetAt; message = [string]$limit.message; source = Get-RelativePath -Path $source }
    }
    return $map
}

function Get-AgentSlotConfigMap {
    $map = @{}
    $source = Get-ConfigPath -Name "agents"
    $config = Read-JsonFileOrNull -Path $source
    if ($null -eq $config -or $null -eq $config.slots) { return $map }
    foreach ($slot in @($config.slots)) {
        if ($null -eq $slot.name -or [string]::IsNullOrWhiteSpace([string]$slot.name)) { continue }
        $map[[string]$slot.name] = [pscustomobject]@{ name = [string]$slot.name; agent = [string]$slot.agent; role = $(if ($null -eq $slot.PSObject.Properties["role"]) { "" } else { [string]$slot.role }); enabled = [bool]$slot.enabled; branch = [string]$slot.branch; source = $(if ([string]::IsNullOrWhiteSpace($source)) { "" } else { Get-RelativePath -Path $source }) }
    }
    return $map
}

function Get-WorktreeRoot {
    $source = Get-ConfigPath -Name "projects"
    $config = Read-JsonFileOrNull -Path $source
    if ($null -eq $config -or $null -eq $config.worktreeRoot) { return "" }
    return Resolve-OrchestratorPath -Path ([string]$config.worktreeRoot)
}

function Get-WorktreeSummary {
    param([string]$SlotName, [string]$WorktreeRoot)
    if ([string]::IsNullOrWhiteSpace($WorktreeRoot)) { return [pscustomobject]@{ path = ""; exists = $false; branch = ""; changedCount = 0; changedFiles = @(); summary = "worktree root is not configured"; error = "" } }
    $path = Join-Path $WorktreeRoot $SlotName
    if (!(Test-Path $path)) { return [pscustomobject]@{ path = $path; exists = $false; branch = ""; changedCount = 0; changedFiles = @(); summary = "worktree is not prepared"; error = "" } }
    $branch = ""; $statusLines = @(); $errorText = ""
    try {
        $branch = (& git -C $path rev-parse --abbrev-ref HEAD 2>$null) -join "`n"
        $statusLines = @(& git -C $path status --short 2>&1)
        if ($LASTEXITCODE -ne 0) { $errorText = ($statusLines -join "`n") }
    }
    catch { $errorText = $_.Exception.Message }
    $changedFiles = @()
    foreach ($line in @($statusLines)) {
        $text = [string]$line
        if ([string]::IsNullOrWhiteSpace($text) -or $text.Length -lt 4) { continue }
        $changedFiles += [pscustomobject]@{ status = $text.Substring(0, 2).Trim(); path = $text.Substring(3).Trim() }
    }
    $count = @($changedFiles).Count
    $summary = $(if ($count -eq 0) { "clean worktree" } elseif ($count -eq 1) { "1 changed file" } else { "$count changed files" })
    $sample = @($changedFiles | Select-Object -First 5 | ForEach-Object { "$($_.status) $($_.path)" })
    if ($sample.Count -gt 0) { $summary = "${summary}: $($sample -join '; ')" }
    return [pscustomobject]@{ path = $path; exists = $true; branch = $branch.Trim(); changedCount = $count; changedFiles = $changedFiles; summary = $summary; error = $errorText }
}

function Get-SlotSummary {
    param([string]$SlotName, [object]$SlotConfig, [object]$Worktree, [object[]]$ActiveTasks, [object[]]$DoneTasks, [object[]]$FailedTasks, [object]$LatestLog, [object]$ManualLock, [object]$Limit, [object]$RuntimeStatus, [object]$RunnerEvidence)
    $slotActive = @($ActiveTasks | Where-Object { $_.name -like "${SlotName}*" })
    $slotFailed = @($FailedTasks | Where-Object { $_.name -like "${SlotName}*" })
    $currentTask = $null
    if ($slotActive.Count -gt 0) { $currentTask = $slotActive | Sort-Object lastWriteTime -Descending | Select-Object -First 1 }
    elseif ($slotFailed.Count -gt 0) { $currentTask = $slotFailed | Sort-Object lastWriteTime -Descending | Select-Object -First 1 }
    $blocker = $null
    $logTaskName = $(if ($LatestLog) { Get-LogTaskName -LogName ([string]$LatestLog.name) } else { "" })
    $latestLogMatchesCurrentTask = ($LatestLog -and $currentTask -and $logTaskName -eq [string]$currentTask.name)
    $latestLogIsRecent = ($LatestLog -and $LatestLog.ageMinutes -le 10)
    $hasRunnerEvidence = ($RunnerEvidence -and $RunnerEvidence.count -gt 0)
    if ($LatestLog -and ($latestLogIsRecent -or ($slotActive.Count -gt 0 -and $latestLogMatchesCurrentTask))) {
        $blocker = Get-BlockerFromText -Text (($LatestLog.importantLine + "`n" + $LatestLog.tail))
    }
    $agent = ""; $role = ""; $enabled = $null
    if ($SlotConfig) { $agent = [string]$SlotConfig.agent; $role = [string]$SlotConfig.role; $enabled = [bool]$SlotConfig.enabled }
    $worktreeText = $(if ($Worktree) { [string]$Worktree.summary } else { "worktree status unavailable" })
    $state = "idle"; $statusText = "$SlotName is idle. Worktree: $worktreeText."; $nextAction = "No action needed for $SlotName until a suitable task is queued."; $blockedBy = "none"; $owner = "orchestrator"; $when = "now"
    if ($enabled -eq $false) { $state = "disabled"; $statusText = "$SlotName is disabled in agent config. Worktree: $worktreeText."; $nextAction = "Enable $SlotName in config before routing work."; $blockedBy = "disabled" }
    if ($null -ne $currentTask -and $slotActive.Count -gt 0) {
        $state = "active"; $statusText = "$SlotName is working on $($currentTask.title). Worktree: $worktreeText."; $nextAction = "Let $SlotName finish or check the dashboard if it has been active too long."
        $hasFreshTaskLog = ($latestLogIsRecent -and $latestLogMatchesCurrentTask)
        if ($currentTask.ageMinutes -ge 5 -and -not $hasFreshTaskLog -and -not $hasRunnerEvidence) {
            $state = "stale"
            $statusText = "$SlotName claimed $($currentTask.title) but no fresh runner evidence is visible. Worktree: $worktreeText."
            $nextAction = "Check for a live $SlotName runner process and a fresh log for the claimed task before trusting any quota or sleeping status."
            $blockedBy = "claimed_but_no_fresh_log"
            $owner = "Alex"
        }
        elseif ($currentTask.ageMinutes -ge 30 -and -not $hasFreshTaskLog) {
            $state = "stale"; $statusText = "$SlotName may be stuck on $($currentTask.title). Worktree: $worktreeText."; $nextAction = "Review the latest $SlotName log and either requeue or fail the stale active task."; $blockedBy = "stale active task"; $owner = "Alex"
        }
    }
    elseif ($LatestLog -and $LatestLog.ageMinutes -lt 10) { $state = "recent"; $statusText = "$SlotName ran recently. Worktree: $worktreeText."; $nextAction = "Check whether the task moved to done or failed before rerunning $SlotName."; $owner = "Alex" }
    if ($blocker) { $state = $blocker.severity; $statusText = "$SlotName is $($blocker.severity): $($blocker.label). Worktree: $worktreeText."; $nextAction = $blocker.nextAction; $blockedBy = $blocker.label; $owner = "Alex" }
    $runtimeStatusIsRecent = $false
    if ($RuntimeStatus -and -not [string]::IsNullOrWhiteSpace([string]$RuntimeStatus.updatedAt)) {
        try { $runtimeStatusIsRecent = (((Get-Date) - ([datetime]$RuntimeStatus.updatedAt)).TotalMinutes -le 10) }
        catch { $runtimeStatusIsRecent = $false }
    }
    $allowLimitOverride = ($Limit -and ($latestLogIsRecent -or $runtimeStatusIsRecent) -and ($slotActive.Count -eq 0 -or $latestLogMatchesCurrentTask -or ($RunnerEvidence -and $RunnerEvidence.count -gt 0)))
    if ($allowLimitOverride) {
        $state = $(if ([string]::IsNullOrWhiteSpace([string]$Limit.state)) { "sleeping" } else { [string]$Limit.state })
        $resetText = $(if ([string]::IsNullOrWhiteSpace([string]$Limit.resetAt)) { "until its limit resets" } else { "until $($Limit.resetAt)" })
        $statusText = "$SlotName is sleeping: $($Limit.message). Worktree: $worktreeText."; $nextAction = "Do not wake $SlotName $resetText. Route urgent work to another available agent."; $blockedBy = "$SlotName usage limit"; $owner = "orchestrator"; $when = $(if ([string]::IsNullOrWhiteSpace([string]$Limit.resetAt)) { "after reset" } else { "after $($Limit.resetAt)" })
    }
    if ($ManualLock) {
        $state = $(if ($ManualLock.expired) { "stale" } else { "locked" })
        $statusText = $(if ($ManualLock.expired) { "$SlotName has an expired manual lock from $($ManualLock.owner). Worktree: $worktreeText." } else { "$SlotName is locked by $($ManualLock.owner): $($ManualLock.reason). Worktree: $worktreeText." })
        $nextAction = $(if ($ManualLock.expired) { "Unlock $SlotName or renew the manual lock before routing work." } else { "Unlock $SlotName when the manual session is done." })
        $blockedBy = $(if ($ManualLock.expired) { "expired manual lock" } else { "manual lock" }); $owner = "Alex"; $when = $(if ($ManualLock.expired) { "now" } else { "after manual session" })
    }
    $runtimeState = $(if ($RuntimeStatus) { [string]$RuntimeStatus.state } else { "" })
    $runtimeReason = $(if ($RuntimeStatus) { [string]$RuntimeStatus.reason } else { "" })
    $runtimeNextAction = $(if ($RuntimeStatus) { [string]$RuntimeStatus.nextAction } else { "" })
    if ($RuntimeStatus -and $slotActive.Count -eq 0 -and -not $latestLogIsRecent -and -not $hasRunnerEvidence -and $runtimeState -in @("active", "blocked", "sleeping", "stale", "locked")) {
        if ($runtimeState -eq "active") {
            $state = "stale"
            $statusText = "$SlotName still shows active in runtime status but no active task or runner evidence is visible. Worktree: $worktreeText."
            $nextAction = "Inspect $($RuntimeStatus.path) and the latest $SlotName log before waking the slot."
            $blockedBy = "stale runtime status"
            $owner = "Alex"
            $when = "now"
        }
        else {
            $state = $runtimeState
            $blockedBy = $(if ([string]::IsNullOrWhiteSpace($runtimeReason)) { "runtime status requires review" } else { $runtimeReason })
            $statusText = "$SlotName is $runtimeState per runtime status. Worktree: $worktreeText."
            $nextAction = $(if ([string]::IsNullOrWhiteSpace($runtimeNextAction)) { "Inspect $($RuntimeStatus.path) before waking the slot." } else { $runtimeNextAction })
            $owner = "Alex"
            $when = "now"
        }
    }
    return [pscustomobject]@{ name = $SlotName; agent = $agent; role = $role; enabled = $enabled; state = $state; statusText = $statusText; currentTask = $currentTask; latestLog = $LatestLog; blocker = $blocker; manualLock = $ManualLock; limit = $Limit; runtimeStatus = $RuntimeStatus; runnerEvidence = $RunnerEvidence; worktree = $Worktree; changedFiles = $(if ($Worktree) { $Worktree.changedFiles } else { @() }); nextAction = [pscustomobject]@{ action = $nextAction; owner = $owner; when = $when; blockedBy = $blockedBy } }
}

function Get-SlotAvailability {
    param([object]$Slot)
    $wakeState = "available"; $wakeAt = $null; $safeToWake = $true; $reason = "idle and available"; $nextAction = "Start this slot when work is ready."; $sortAt = [datetime]::MinValue
    if ([string]::IsNullOrWhiteSpace([string]$Slot.agent) -and $null -eq $Slot.enabled) {
        $wakeState = "needs_review"
        $safeToWake = $false
        $reason = "slot is not configured in config\\agents.json"
        $nextAction = "Do not auto-wake this slot. Remove stale logs/locks or add a valid slot config first."
        $sortAt = [datetime]::MaxValue
    }
    elseif ($Slot.enabled -eq $false -or $Slot.state -eq "disabled") { $wakeState = "disabled"; $safeToWake = $false; $reason = "slot is disabled"; $nextAction = "Enable the slot before routing work."; $sortAt = [datetime]::MaxValue }
    elseif ($Slot.manualLock) { $wakeState = $(if ($Slot.manualLock.expired) { "needs_human" } else { "locked" }); $safeToWake = $false; $wakeAt = $Slot.manualLock.expiresAt; $reason = $(if ($Slot.manualLock.expired) { "expired manual lock" } else { "manual lock: $($Slot.manualLock.reason)" }); $nextAction = $Slot.nextAction.action; $sortAt = $(if ($wakeAt) { [datetime]$wakeAt } else { [datetime]::MaxValue }) }
    elseif ($Slot.limit) { $wakeState = $(if ([string]::IsNullOrWhiteSpace([string]$Slot.limit.resetAt)) { "waiting_unknown" } else { "scheduled" }); $safeToWake = $false; $wakeAt = $(if ([string]::IsNullOrWhiteSpace([string]$Slot.limit.resetAt)) { $null } else { [string]$Slot.limit.resetAt }); $reason = $(if ([string]::IsNullOrWhiteSpace([string]$Slot.limit.message)) { "usage limit" } else { [string]$Slot.limit.message }); $nextAction = $Slot.nextAction.action; $sortAt = $(if ($wakeAt) { [datetime]$wakeAt } else { [datetime]::MaxValue }) }
    elseif ($Slot.state -eq "active" -or $Slot.state -eq "recent") { $wakeState = "busy"; $safeToWake = $false; $reason = $Slot.statusText; $nextAction = $Slot.nextAction.action; $sortAt = [datetime]::MaxValue }
    elseif ($Slot.state -eq "stale" -or $Slot.state -eq "blocked") { $wakeState = "needs_human"; $safeToWake = $(if ($Slot.worktree -and $Slot.worktree.changedCount -eq 0) { $true } else { $false }); $reason = $Slot.nextAction.blockedBy; $nextAction = $Slot.nextAction.action; $sortAt = [datetime]::MinValue }
    elseif ($Slot.state -eq "idle") { $sortAt = [datetime]::MinValue }
    else { $wakeState = "needs_review"; $safeToWake = $false; $reason = $Slot.statusText; $nextAction = $Slot.nextAction.action; $sortAt = [datetime]::MaxValue }
    return [pscustomobject]@{ slot = $Slot.name; agent = $Slot.agent; state = $Slot.state; wakeState = $wakeState; wakeAt = $wakeAt; safeToWake = $safeToWake; reason = $reason; nextAction = $nextAction; sortAt = $sortAt.ToString("o") }
}

function Get-ActivityLogEntry {
    param([object]$Slot)

    $isProblem = $Slot.state -in @("blocked", "sleeping", "stale", "locked")
    if (-not $isProblem) { return $null }

    $task = $Slot.currentTask
    $taskTitle = $(if ($task) { [string]$task.title } else { "No active task identified" })
    $issue = $(if ($task -and $null -ne $task.issue) { [int]$task.issue } else { $null })
    $latest = $(if ($Slot.latestLog -and -not [string]::IsNullOrWhiteSpace([string]$Slot.latestLog.importantLine)) { [string]$Slot.latestLog.importantLine } else { "No important log line found yet." })
    $failureType = $(if ($Slot.blocker) { [string]$Slot.blocker.kind } elseif ($Slot.nextAction) { [string]$Slot.nextAction.blockedBy } else { [string]$Slot.state })
    $blockerLabel = $(if ($Slot.blocker) { [string]$Slot.blocker.label } elseif ($Slot.nextAction) { [string]$Slot.nextAction.blockedBy } else { [string]$Slot.state })
    $worktreeSummary = $(if ($Slot.worktree) { [string]$Slot.worktree.summary } else { "worktree status unavailable" })
    $next = $(if ($Slot.nextAction) { [string]$Slot.nextAction.action } else { "Review the latest slot log." })
    $headline = "{0} {1}: {2}" -f $Slot.name, $Slot.state, $blockerLabel
    $issueText = $(if ($issue) { " (#$issue)" } else { "" })

    return [pscustomobject]@{
        slot = [string]$Slot.name
        state = [string]$Slot.state
        taskTitle = $taskTitle
        issue = $issue
        failureType = $failureType
        blockerLabel = $blockerLabel
        latestImportantLogLine = $latest
        nextRecommendedAction = $next
        worktreeSummary = $worktreeSummary
        logPath = $(if ($Slot.latestLog) { [string]$Slot.latestLog.path } else { "" })
        updatedAt = $(if ($Slot.latestLog) { [string]$Slot.latestLog.lastWriteTime } else { (Get-Date).ToString("o") })
        headline = $headline
        detailText = @(
            $headline,
            "Task: $taskTitle$issueText",
            "Latest: $latest",
            "Worktree: $worktreeSummary",
            "Next: $next"
        ) -join "`n"
    }
}

function Get-AvailabilitySummary {
    param([object[]]$Slots, [int]$QueueCount = 0)
    $availabilitySlots = @($Slots | ForEach-Object { Get-SlotAvailability -Slot $_ })
    $available = @($availabilitySlots | Where-Object { $_.wakeState -eq "available" -and $_.safeToWake })
    $needsHuman = @($availabilitySlots | Where-Object { $_.wakeState -eq "needs_human" })
    $scheduled = @($availabilitySlots | Where-Object { $_.wakeState -eq "scheduled" -and $_.wakeAt } | Sort-Object { [datetime]$_.wakeAt })
    $next = $null
    if ($QueueCount -eq 0 -and $needsHuman.Count -gt 0) { $next = $needsHuman | Select-Object -First 1 }
    elseif ($available.Count -gt 0) { $next = $available | Select-Object -First 1 }
    elseif ($needsHuman.Count -gt 0) { $next = $needsHuman | Select-Object -First 1 }
    elseif ($scheduled.Count -gt 0) { $next = $scheduled | Select-Object -First 1 }
    $nextHumanAction = $(if ($QueueCount -eq 0 -and $needsHuman.Count -gt 0) { ($needsHuman | Select-Object -First 1).nextAction } elseif ($QueueCount -eq 0) { "No queued work is ready. Do not start an idle slot until a task is queued." } elseif ($available.Count -gt 0) { "Start an available slot on queued work." } elseif ($needsHuman.Count -gt 0) { ($needsHuman | Select-Object -First 1).nextAction } elseif ($scheduled.Count -gt 0) { "Wait for the next scheduled slot wake time." } else { "No safe wake action is visible. Review blocked slots and dirty worktrees." })
    return [pscustomobject]@{ availableCount = $available.Count; nextWakeAt = $(if ($next) { $next.wakeAt } else { $null }); nextWakeSlot = $(if ($next) { $next.slot } else { $null }); nextWakeState = $(if ($next) { $next.wakeState } else { "none" }); nextHumanAction = $nextHumanAction; slots = @($availabilitySlots | Select-Object slot, agent, state, wakeState, wakeAt, safeToWake, reason, nextAction) }
}

function Get-QueueRecommendationOrNull {
    $script = Join-Path $Root "scripts\Get-QueueRecommendation.ps1"
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { return $null }
    try {
        $json = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $Root 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        return (($json | ForEach-Object { $_.ToString() }) -join "`n") | ConvertFrom-Json
    }
    catch { return $null }
}

function Get-LatestSupervisedLaunchEvidence {
    param([string]$SlotName)

    if ([string]::IsNullOrWhiteSpace($SlotName)) { return $null }
    $dir = Join-Path $Root "logs\control-actions"
    if (!(Test-Path -LiteralPath $dir -PathType Container)) { return $null }

    $candidates = @(
        Get-ChildItem -LiteralPath $dir -File -Filter "*-supervised_slot_launch-$SlotName.json" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
    )
    if ($candidates.Count -eq 0 -or $null -eq $candidates[0]) { return $null }

    try {
        $raw = Get-Content -LiteralPath $candidates[0].FullName -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        return [pscustomobject]@{
            mode = [string]$raw.mode
            processId = $(if ($null -eq $raw.PSObject.Properties["processId"]) { $null } else { $raw.processId })
            exitCode = $(if ($null -eq $raw.PSObject.Properties["exitCode"]) { $null } else { $raw.exitCode })
            runOnce = $(if ($null -eq $raw.PSObject.Properties["runOnce"]) { $null } else { $raw.runOnce })
            headless = $(if ($null -eq $raw.PSObject.Properties["headless"]) { $null } else { $raw.headless })
            stdoutPath = $(if ($null -eq $raw.PSObject.Properties["stdoutPath"]) { "" } else { [string]$raw.stdoutPath })
            stderrPath = $(if ($null -eq $raw.PSObject.Properties["stderrPath"]) { "" } else { [string]$raw.stderrPath })
            generatedAt = $(if ($null -eq $raw.PSObject.Properties["generatedAt"]) { "" } else { [string]$raw.generatedAt })
            auditPath = Get-RelativePath -Path $candidates[0].FullName
        }
    }
    catch {
        return $null
    }
}

function Get-BridgeValidationStatus {
    param(
        [object[]]$QueueTasks,
        [object[]]$ActiveTasks,
        [object[]]$DoneTasks,
        [object[]]$FailedTasks,
        [object[]]$Slots
    )

    $knownStates = @("A", "B", "C", "unresolved")
    $taskPattern = "(?i)chatgpt[-_ ]bridge|bridge[-_ ]tool[-_ ]visibility|validate[-_ ]chatgpt[-_ ]bridge"
    $candidate = @(
        @($ActiveTasks | Where-Object { $_.name -match $taskPattern })
        @($FailedTasks | Where-Object { $_.name -match $taskPattern })
        @($QueueTasks | Where-Object { $_.name -match $taskPattern })
        @($DoneTasks | Where-Object { $_.name -match $taskPattern })
    ) | ForEach-Object { $_ } | Sort-Object ageMinutes | Select-Object -First 1

    $taskPath = ""
    if ($candidate) { $taskPath = [string]$candidate.path }

    $slotWithSignal = @($Slots | Where-Object {
            $_.currentTask -and
            (
                [string]$_.currentTask.name -match $taskPattern -or
                [string]$_.currentTask.title -match $taskPattern
            )
        } | Select-Object -First 1)

    $logPath = ""
    $blocker = "Bridge validation evidence is missing."
    $next = "Use the manual ChatGPT fallback prompt and capture A/B/C bridge evidence."

    if ($slotWithSignal.Count -gt 0) {
        $slot = $slotWithSignal[0]
        if ($slot.latestLog -and -not [string]::IsNullOrWhiteSpace([string]$slot.latestLog.path)) {
            $logPath = [string]$slot.latestLog.path
        }
        if ($slot.nextAction -and -not [string]::IsNullOrWhiteSpace([string]$slot.nextAction.blockedBy)) {
            $blocker = [string]$slot.nextAction.blockedBy
        }
        if ($slot.nextAction -and -not [string]::IsNullOrWhiteSpace([string]$slot.nextAction.action)) {
            $next = [string]$slot.nextAction.action
        }
    }

    $state = "unresolved"
    if ($slotWithSignal.Count -gt 0 -and $slotWithSignal[0].latestLog -and $slotWithSignal[0].latestLog.importantLine) {
        $important = [string]$slotWithSignal[0].latestLog.importantLine
        if ($important -match "(?i)\bclassification[:=\s]+([ABC])\b") {
            $state = [string]$Matches[1].ToUpperInvariant()
        }
    }
    if ($knownStates -notcontains $state) { $state = "unresolved" }

    $prompt = @(
        "You are the manual fallback handler for gm-agent-orchestrator RC1 bridge validation.",
        "Task path: $taskPath",
        "Log path: $logPath",
        "Current blocker: $blocker",
        "Return exactly one classification: A, B, or C.",
        "Also provide the shortest evidence lines that justify the classification."
    ) -join "`n"

    return [pscustomobject]@{
        state = $state
        taskPath = $taskPath
        logPath = $logPath
        blocker = $blocker
        nextAction = $next
        chatgptFallbackPrompt = $prompt
    }
}

function ConvertTo-ArrayValue {
    param([object]$Value)

    if ($null -eq $Value) { return ,@() }
    if ($Value -is [System.Collections.IDictionary]) { return ,@() }
    return ,@($Value)
}
$queueDir = Join-Path $Root "tasks\queue"; $activeDir = Join-Path $Root "tasks\active"; $doneDir = Join-Path $Root "tasks\done"; $failedDir = Join-Path $Root "tasks\failed"; $logsDir = Join-Path $Root "logs"; $statusDir = Join-Path $Root "status"; $reportsDir = Join-Path $Root "reports\dashboard"
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null
$queueTasks = @(Get-FileSummary $queueDir); $activeTasks = @(Get-FileSummary $activeDir); $doneTasks = @(Get-FileSummary $doneDir); $failedTasks = @(Get-FileSummary $failedDir); $limitMap = Get-AgentLimitMap; $slotConfigMap = Get-AgentSlotConfigMap; $worktreeRoot = Get-WorktreeRoot
$queueRecommendation = Get-QueueRecommendationOrNull
$slotNames = New-Object System.Collections.Generic.HashSet[string]
foreach ($key in $slotConfigMap.Keys) { $slotNames.Add([string]$key) | Out-Null }
foreach ($task in @($activeTasks)) { if ($task.name -match "^([^_]+(?:-[^_]+)*)__") { $slotNames.Add($Matches[1]) | Out-Null } }
foreach ($key in $limitMap.Keys) { $slotNames.Add([string]$key) | Out-Null }
$locksDir = Join-Path $Root "locks"
if (Test-Path $locksDir) { foreach ($lockFile in @(Get-ChildItem $locksDir -Filter "*.manual.lock" -File -ErrorAction SilentlyContinue)) { $slotNames.Add(($lockFile.BaseName -replace "\.manual$", "")) | Out-Null } }
$slots = @()
foreach ($slotName in @($slotNames) | Sort-Object) {
    $latestLog = Get-LatestLog -Path (Join-Path $logsDir $slotName); $manualLock = Get-ManualSlotLock -SlotName $slotName; $limit = $(if ($limitMap.ContainsKey($slotName)) { $limitMap[$slotName] } else { $null }); $slotConfig = $(if ($slotConfigMap.ContainsKey($slotName)) { $slotConfigMap[$slotName] } else { $null }); $worktree = Get-WorktreeSummary -SlotName $slotName -WorktreeRoot $worktreeRoot; $runtimeStatus = Get-SlotRuntimeStatus -SlotName $slotName; $runnerEvidence = Get-SlotRunnerEvidence -SlotName $slotName
    $slotSummary = Get-SlotSummary -SlotName $slotName -SlotConfig $slotConfig -Worktree $worktree -ActiveTasks $activeTasks -DoneTasks $doneTasks -FailedTasks $failedTasks -LatestLog $latestLog -ManualLock $manualLock -Limit $limit -RuntimeStatus $runtimeStatus -RunnerEvidence $runnerEvidence
    $slotSummary | Add-Member -NotePropertyName launchEvidence -NotePropertyValue (Get-LatestSupervisedLaunchEvidence -SlotName $slotName) -Force
    $slots += $slotSummary
}
$availability = Get-AvailabilitySummary -Slots $slots -QueueCount $queueTasks.Count
$activityLog = @($slots | ForEach-Object { Get-ActivityLogEntry -Slot $_ } | Where-Object { $null -ne $_ } | Sort-Object updatedAt -Descending)
$bridgeValidation = Get-BridgeValidationStatus -QueueTasks $queueTasks -ActiveTasks $activeTasks -DoneTasks $doneTasks -FailedTasks $failedTasks -Slots $slots

# Service Health Integration
$serverHealthPath = Join-Path $statusDir "server-health.json"
$serviceHealth = [pscustomobject]@{
    generatedAt = ""
    ageMinutes = $null
    freshnessThresholdMinutes = 5
    fresh = $false
    state = "unknown"
    ok = $false
    servers = @()
    localServices = @()
    mcpCapability = $null
    nextAction = "Start Monitor-ServerHealthPulse.ps1"
}
if (Test-Path $serverHealthPath) {
    try {
        $pulse = Get-Content $serverHealthPath -Raw | ConvertFrom-Json
        $pulseGeneratedAt = $(if ($null -eq $pulse.PSObject.Properties["generatedAt"]) { "" } else { [string]$pulse.generatedAt })
        $pulseIntervalSeconds = 180
        if ($null -ne $pulse.PSObject.Properties["intervalSeconds"]) {
            try { $pulseIntervalSeconds = [Math]::Max(30, [int]$pulse.intervalSeconds) }
            catch { $pulseIntervalSeconds = 180 }
        }
        $pulseFreshnessThresholdMinutes = [Math]::Max(5, [Math]::Ceiling(($pulseIntervalSeconds * 2) / 60.0))
        $pulseAgeMinutes = $null
        $pulseIsFresh = $false
        if (-not [string]::IsNullOrWhiteSpace($pulseGeneratedAt)) {
            try {
                $pulseAgeMinutes = [Math]::Round(((Get-Date) - ([datetime]$pulseGeneratedAt)).TotalMinutes, 1)
                $pulseIsFresh = $pulseAgeMinutes -le $pulseFreshnessThresholdMinutes
            }
            catch {
                $pulseAgeMinutes = $null
                $pulseIsFresh = $false
            }
        }

        $serviceHealthState = [string]$pulse.state
        $serviceHealthOk = [bool]$pulse.ok
        $serviceHealthNextAction = [string]$pulse.nextAction
        if (-not $pulseIsFresh) {
            $serviceHealthState = "stale"
            $serviceHealthOk = $false
            $serviceHealthNextAction = "Restart Monitor-ServerHealthPulse.ps1 and refresh status/services.json before trusting service health."
        }

        $serviceHealth = [pscustomobject]@{
            generatedAt = $pulseGeneratedAt
            ageMinutes = $pulseAgeMinutes
            freshnessThresholdMinutes = $pulseFreshnessThresholdMinutes
            fresh = $pulseIsFresh
            state = $serviceHealthState
            ok = $serviceHealthOk
            servers = $pulse.servers
            localServices = $(if ($null -eq $pulse.PSObject.Properties["localServices"]) { @() } else { $pulse.localServices })
            mcpCapability = $(if ($null -eq $pulse.PSObject.Properties["mcpCapability"]) { $null } else { $pulse.mcpCapability })
            nextAction = $serviceHealthNextAction
        }
    }
    catch {}
}

$state = "idle"
if ($failedTasks.Count -gt 0) { $state = "needs_attention" }
if ($activeTasks.Count -gt 0) { $state = "active" }
if ($queueTasks.Count -gt 0 -and $activeTasks.Count -eq 0) { $state = "queued" }
if (@($slots | Where-Object { $_.state -in @("blocked", "sleeping", "stale", "locked") }).Count -gt 0) { $state = "needs_attention" }
$priorityWarnings = @()
if (@($queueTasks | Where-Object { $_.name -match "000-example-task" }).Count -gt 0) { $priorityWarnings += "Example task is still in queue and may be claimed before real P0 work." }
if (@($activeTasks | Where-Object { $_.ageMinutes -ge 30 }).Count -gt 0) { $priorityWarnings += "One or more active tasks are stale." }
if (@($slots | Where-Object { $_.state -eq "sleeping" }).Count -gt 0) { $priorityWarnings += "One or more agents are usage-limited. Do not keep trying to wake sleeping slots." }
if (@($slots | Where-Object { $_.worktree -and $_.worktree.changedCount -gt 0 }).Count -gt 0) { $priorityWarnings += "One or more agent worktrees have uncommitted changes. Review changed files before rerouting or resetting slots." }
$nextActionText = $availability.nextHumanAction; $nextOwner = $(if ($availability.nextWakeState -eq "scheduled") { "orchestrator" } else { "Alex" }); $nextWhen = $(if ($availability.nextWakeAt) { "after $($availability.nextWakeAt)" } else { "now" }); $nextBlockedBy = $(if ($availability.nextWakeSlot) { $availability.nextWakeSlot } else { "none" })
$status = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    worktreeRoot = $worktreeRoot
    state = $state
    headline = $(if ($availability.nextWakeSlot) { "Next slot: $($availability.nextWakeSlot) is $($availability.nextWakeState). $($availability.nextHumanAction)" } elseif ($activeTasks.Count -gt 0) { "Agents have active work." } elseif ($queueTasks.Count -gt 0) { "Work is queued but no active task is visible." } else { "No active agent work is visible." })
    serviceHealth = $serviceHealth
    availability = $availability
    queueRecommendation = $queueRecommendation
    nextAction = [pscustomobject]@{ action = $nextActionText; owner = $nextOwner; when = $nextWhen; blockedBy = $nextBlockedBy }
    priorityWarnings = $priorityWarnings
    activityLog = $activityLog
    bridgeValidation = $bridgeValidation
    watcher = [pscustomobject]@{ state = "not_wired"; statusText = "Watcher status is not wired yet. Manual pull/wake may still be needed." }
    counts = [pscustomobject]@{ queue = $queueTasks.Count; active = $activeTasks.Count; done = $doneTasks.Count; failed = $failedTasks.Count }
    tasks = [pscustomobject]@{ queue = $queueTasks; active = $activeTasks; done = $doneTasks; failed = $failedTasks }
    slots = $slots
}

# Normalize collection fields so JSON output shape remains stable for MCP consumers.
$status.priorityWarnings = ConvertTo-ArrayValue -Value $status.priorityWarnings
$status.activityLog = ConvertTo-ArrayValue -Value $status.activityLog
$status.availability.slots = ConvertTo-ArrayValue -Value $status.availability.slots
$status.tasks.queue = ConvertTo-ArrayValue -Value $status.tasks.queue
$status.tasks.active = ConvertTo-ArrayValue -Value $status.tasks.active
$status.tasks.done = ConvertTo-ArrayValue -Value $status.tasks.done
$status.tasks.failed = ConvertTo-ArrayValue -Value $status.tasks.failed
$status.slots = ConvertTo-ArrayValue -Value $status.slots
foreach ($slot in @($status.slots)) {
    if ($null -eq $slot) { continue }
    if ($slot.PSObject.Properties["changedFiles"]) { $slot.changedFiles = ConvertTo-ArrayValue -Value $slot.changedFiles }
    if ($slot.PSObject.Properties["worktree"] -and $slot.worktree) {
        if ($slot.worktree.PSObject.Properties["changedFiles"]) {
            $slot.worktree.changedFiles = ConvertTo-ArrayValue -Value $slot.worktree.changedFiles
        }
    }
    if ($slot.PSObject.Properties["runnerEvidence"] -and $slot.runnerEvidence) {
        if ($slot.runnerEvidence.PSObject.Properties["processIds"]) {
            $slot.runnerEvidence.processIds = ConvertTo-ArrayValue -Value $slot.runnerEvidence.processIds
        }
    }
}

$jsonPath = Join-Path $statusDir "orchestrator.json"
$json = $status | ConvertTo-Json -Depth 30
[System.IO.File]::WriteAllText($jsonPath, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output $json
