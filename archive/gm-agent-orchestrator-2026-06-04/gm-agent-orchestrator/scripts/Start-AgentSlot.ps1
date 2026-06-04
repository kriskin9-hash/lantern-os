[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OrchestratorRoot,

    [Parameter(Mandatory = $true)]
    [string]$WorktreePath,

    [Parameter(Mandatory = $true)]
    [string]$SlotJsonBase64,

    [Parameter(Mandatory = $true)]
    [string]$ProjectJsonBase64,

    [int]$FallbackWaitMinutes = 300,

    [int]$MaxResumeCycles = 4,

    [string]$ClaimedTaskRelativePath = "",

    [switch]$RunOnce,

    [switch]$Headless
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function ConvertFrom-Base64Json {
    param([Parameter(Mandatory = $true)][string]$Value)

    $json = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Value))
    return $json | ConvertFrom-Json
}

function Read-JsonFileOrNull {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    if (!(Test-Path $Path)) { return $null }

    return Get-Content $Path -Raw | ConvertFrom-Json
}

function ConvertTo-ProcessArgumentString {
    param([string[]]$Arguments)

    $escaped = foreach ($argument in @($Arguments)) {
        if ($null -eq $argument) { continue }

        $text = [string]$argument
        if ($text -eq "") {
            '""'
            continue
        }

        if ($text -notmatch '[\s"]') {
            $text
            continue
        }

        '"' + ($text -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
    }

    return ($escaped -join ' ')
}

function Get-SlotRole {
    if ($null -ne $script:Slot.PSObject.Properties["role"] -and -not [string]::IsNullOrWhiteSpace([string]$script:Slot.role)) {
        return [string]$script:Slot.role
    }

    return "unspecified"
}

function Get-EnvSwitch {
    param([string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($value)) { return $false }

    switch -Regex ($value.Trim().ToLowerInvariant()) {
        "^(1|true|yes|on)$" { return $true }
        default { return $false }
    }
}

function Test-UrgentOnlyMode {
    return (Get-EnvSwitch -Name "ORCH_URGENT_ONLY") -or (Get-EnvSwitch -Name "ORCH_URGENT_P0_ONLY")
}

function Test-CodexTokenSaverMode {
    if ([string]$script:Slot.agent -ne "codex") {
        return $false
    }

    return (Get-EnvSwitch -Name "ORCH_CODEX_TOKEN_SAVER") -or (Get-EnvSwitch -Name "ORCH_DESKTOP_TOKEN_SAVER")
}

function Invoke-CheckedProbe {
    param(
        [Parameter(Mandatory = $true)] [string]$Exe,
        [Parameter(Mandatory = $true)] [string[]]$Args,
        [int]$TimeoutSeconds = 15
    )

    $temp = [System.IO.Path]::GetTempFileName()
    $out = "$temp.out"
    $err = "$temp.err"

    try {
        $p = Start-Process -FilePath $Exe -ArgumentList (ConvertTo-ProcessArgumentString -Arguments $Args) -NoNewWindow -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
        $null = $p.Handle
        $done = $p.WaitForExit($TimeoutSeconds * 1000)
        
        $stdout = if (Test-Path $out) { Get-Content $out -Raw } else { "" }
        $stderr = if (Test-Path $err) { Get-Content $err -Raw } else { "" }
        $exitCode = if ($done) { $p.ExitCode } else { try { $p.Kill() } catch {}; $null }

        return [pscustomobject]@{
            exitCode = $exitCode
            timedOut = -not $done
            stdout   = $stdout
            stderr   = $stderr
            combined = ("$stdout`n$stderr").Trim()
        }
    }
    finally {
        Remove-Item -Path $temp, $out, $err -Force -ErrorAction SilentlyContinue
    }
}
function Invoke-NativeCommandCaptured {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [Parameter(Mandatory = $true)][string[]]$Args,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [int]$TimeoutSeconds = 0
    )

    $temp = [System.IO.Path]::GetTempFileName()
    $out = "$temp.out"
    $err = "$temp.err"

    try {
        $process = Start-Process -FilePath $Exe `
            -ArgumentList (ConvertTo-ProcessArgumentString -Arguments $Args) `
            -WorkingDirectory $WorkingDirectory `
            -NoNewWindow `
            -PassThru `
            -RedirectStandardOutput $out `
            -RedirectStandardError $err
        $null = $process.Handle

        if ($TimeoutSeconds -gt 0) {
            $done = $process.WaitForExit($TimeoutSeconds * 1000)
            if (-not $done) {
                try { $process.Kill() } catch {}
                $stdout = if (Test-Path $out) { Get-Content $out -Raw } else { "" }
                $stderr = if (Test-Path $err) { Get-Content $err -Raw } else { "" }
                return [pscustomobject]@{
                    exitCode = $null
                    timedOut = $true
                    stdout = $stdout
                    stderr = $stderr
                    combined = ("$stdout`n$stderr").Trim()
                }
            }
        }
        else {
            $process.WaitForExit()
        }

        $stdout = if (Test-Path $out) { Get-Content $out -Raw } else { "" }
        $stderr = if (Test-Path $err) { Get-Content $err -Raw } else { "" }

        return [pscustomobject]@{
            exitCode = $process.ExitCode
            timedOut = $false
            stdout = $stdout
            stderr = $stderr
            combined = ("$stdout`n$stderr").Trim()
        }
    }
    finally {
        Remove-Item -Path $temp, $out, $err -Force -ErrorAction SilentlyContinue
    }
}

function Resolve-ProcessCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [Parameter(Mandatory = $true)][string[]]$Args
    )

    $command = Get-Command $Exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $command) {
        throw "Agent executable not found on PATH: $Exe"
    }

    $resolvedExe = if ([string]::IsNullOrWhiteSpace([string]$command.Source)) { $Exe } else { [string]$command.Source }
    $resolvedArgs = @($Args)

    # Prefer native wrappers when available; PowerShell shim scripts commonly
    # transform benign stderr output into NativeCommandError records.
    if ($command.CommandType -eq "ExternalScript") {
        $scriptPath = $resolvedExe
        $cmdSibling = [System.IO.Path]::ChangeExtension($scriptPath, ".cmd")
        if (Test-Path -LiteralPath $cmdSibling -PathType Leaf) {
            # .cmd/.bat files are not directly executable when using redirected stdio;
            # run them through cmd.exe so probes and agent runs work reliably.
            $resolvedExe = "cmd.exe"
            $resolvedArgs = @("/c", $cmdSibling) + @($Args)
        }
        else {
            $resolvedExe = "powershell.exe"
            $resolvedArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath) + @($Args)
        }
    }

    return [pscustomobject]@{
        exe = $resolvedExe
        args = @($resolvedArgs)
    }
}

function Add-OutputBlockToLog {
    param(
        [Parameter(Mandatory = $true)][string]$LogFile,
        [string]$Label,
        [string]$Text
    )

    if ([string]::IsNullOrWhiteSpace($Text)) { return }
    Add-LogLine -Path $LogFile -Message "`n----- $Label -----"
    foreach ($line in ($Text -split "`r?`n")) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            Add-LogLine -Path $LogFile -Message $line
            if (-not $Headless) { Write-Host $line }
        }
    }
}

function Write-Slot {
    param([string]$Message)

    if (-not $Headless) {
        Write-Host ("[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $script:SlotName, $Message)
    }
}

function Add-LogLine {
    param(
        [string]$Path,
        [string]$Message
    )

    Add-Content -Path $Path -Value $Message -Encoding UTF8
}

function Test-RateLimited {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }

    return $Text -match "(?i)(rate limit|usage limit|extra usage|out of .*usage|token limit|tokens?.*replenish|quota exceeded|too many requests|try again later|limit reached|credit limit|reached.*limit|resets? at|reset time|replenish|capacity|429)"
}

function Get-WaitSeconds {
    param([string]$Text)

    if ($Text -match "(?i)(\d+)\s*(?:h|hr|hrs|hour|hours)\b") {
        return ([int]$Matches[1] * 3600) + 60
    }

    if ($Text -match "(?i)(\d+)\s*(?:m|min|mins|minute|minutes)\b") {
        return ([int]$Matches[1] * 60) + 30
    }

    if ($Text -match "(?i)(?:reset|resets|try again|replenish(?:es)?)\D{0,30}\b(?:at|after)\s+(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?") {
        $hour = [int]$Matches[1]
        $minute = 0
        if ($Matches[2]) { $minute = [int]$Matches[2] }
        $ampm = $Matches[3]

        if ($ampm) {
            if ($ampm.ToUpperInvariant() -eq "PM" -and $hour -lt 12) { $hour += 12 }
            if ($ampm.ToUpperInvariant() -eq "AM" -and $hour -eq 12) { $hour = 0 }
        }

        $now = Get-Date
        $target = Get-Date -Hour $hour -Minute $minute -Second 0
        if ($target -le $now) { $target = $target.AddDays(1) }

        return [Math]::Max(60, [int]($target - $now).TotalSeconds + 60)
    }

    return [Math]::Max(60, $FallbackWaitMinutes * 60)
}

function Write-SlotStatus {
    param(
        [Parameter(Mandatory = $true)][string]$State,
        [string]$Reason = "",
        [string]$NextAction = "",
        [string]$UnderlyingReason = "",
        [string]$ClaimState = ""
    )

    $statusDir = Join-Path $OrchestratorRoot "status"
    New-Item -ItemType Directory -Force -Path $statusDir | Out-Null

    $payload = [pscustomobject]@{
        slot             = $script:SlotName
        agent            = [string]$script:Slot.agent
        role             = Get-SlotRole
        state            = $State
        reason           = $Reason
        underlyingReason = $UnderlyingReason
        claimState       = $ClaimState
        nextAction       = $NextAction
        updatedAt        = (Get-Date).ToString("o")
    }

    $path = Join-Path $statusDir ("{0}.json" -f $script:SlotName)
    $payload | ConvertTo-Json -Depth 8 | Set-Content -Path $path -Encoding UTF8
}

function Read-SlotStatus {
    $path = Join-Path (Join-Path $OrchestratorRoot "status") ("{0}.json" -f $script:SlotName)
    return Read-JsonFileOrNull -Path $path
}

function Get-ManualSlotLock {
    $path = Join-Path (Join-Path $OrchestratorRoot "locks") ("{0}.manual.lock" -f $script:SlotName)
    if (!(Test-Path $path)) { return $null }

    try {
        $lock = Get-Content $path -Raw | ConvertFrom-Json
        $expired = $false
        if ($null -ne $lock.expiresAt -and -not [string]::IsNullOrWhiteSpace([string]$lock.expiresAt)) {
            $expired = ([datetime]$lock.expiresAt) -lt (Get-Date)
        }

        return [pscustomobject]@{
            path = $path
            slot = [string]$lock.slot
            owner = [string]$lock.owner
            reason = [string]$lock.reason
            createdAt = [string]$lock.createdAt
            expiresAt = $lock.expiresAt
            expired = $expired
            machine = [string]$lock.machine
        }
    }
    catch {
        return [pscustomobject]@{
            path = $path
            slot = $script:SlotName
            owner = "unknown"
            reason = "manual lock file could not be parsed"
            createdAt = ""
            expiresAt = $null
            expired = $false
            machine = "unknown"
        }
    }
}

function Test-SlotUnlocked {
    $lock = Get-ManualSlotLock
    if ($null -eq $lock) { return $true }

    if ($lock.expired) {
        Write-Slot "Manual lock is expired but still present: $($lock.path)"
        Write-SlotStatus -State "blocked" -Reason "manual_lock_expired" -NextAction "Unlock $script:SlotName or renew the manual lock before starting the slot."
        return $false
    }

    Write-Slot "Manual lock active. No task claimed. Owner=$($lock.owner). Reason=$($lock.reason)"
    Write-SlotStatus -State "locked" -Reason "manual_lock" -NextAction "Unlock $script:SlotName when the manual session is done."
    return $false
}

function Test-AgentReady {
    if ($null -ne $script:LastPreflightOk -and ((Get-Date) - $script:LastPreflightOk).TotalSeconds -lt 300) {
        return $true
    }

    $cmdSpec = @($script:Slot.command.start)
    if ($cmdSpec.Count -lt 1) {
        Write-Slot "Preflight: agent command spec is empty."
        Write-SlotStatus -State "blocked" -Reason "agent_command_missing" -NextAction "Fix config\agents.json command.start for slot $script:SlotName"
        return $false
    }

    $exe = [string]$cmdSpec[0]
    if (!(Get-Command $exe -ErrorAction SilentlyContinue)) {
        Write-Slot "Preflight: agent executable not on PATH: $exe"
        Write-SlotStatus -State "blocked" -Reason "agent_executable_missing" -NextAction "Install $exe and ensure it is on PATH for the scheduled task user"
        return $false
    }

    if ([string]$script:Slot.agent -eq "codex") {
        try {
            # Ensure this runner user can read the bound worktree before claim/start.
            $gitProbe = Invoke-NativeCommandCaptured -Exe "git" -Args @("-C", $WorktreePath, "status", "--short", "--branch") -WorkingDirectory $OrchestratorRoot -TimeoutSeconds 20
            $gitText = [string]$gitProbe.combined
            if ($gitText -match "(?i)dubious ownership|safe.directory") {
                Write-Slot "Preflight: codex worktree is not trusted for this user (git safe.directory)."
                Write-SlotStatus -State "blocked" -Reason "codex_worktree_untrusted" -NextAction ("Run: git config --global --add safe.directory `"{0}`" for the slot runner user, then rerun." -f $WorktreePath)
                return $false
            }
            if ($gitProbe.timedOut -or ($null -ne $gitProbe.exitCode -and [int]$gitProbe.exitCode -ne 0)) {
                $hint = if ([string]::IsNullOrWhiteSpace($gitText)) { "git status probe failed" } else { $gitText.Split("`n")[0] }
                Write-Slot "Preflight: codex git probe failed: $hint"
                Write-SlotStatus -State "blocked" -Reason "codex_git_probe_failed" -NextAction "Fix codex runner git/worktree access, then rerun."
                return $false
            }
        }
        catch {
            Write-Slot "Preflight: codex git probe threw: $($_.Exception.Message)"
            Write-SlotStatus -State "blocked" -Reason "codex_git_probe_error" -NextAction "Fix codex runner git/worktree access, then rerun."
            return $false
        }
    }

    if ([string]$script:Slot.agent -eq "claude") {
        try {
            $probeCommand = Resolve-ProcessCommand -Exe $exe -Args @("--dangerously-skip-permissions", "--print", "Reply with exactly the single word: PROBE_OK_7Q3")
            $probe = Invoke-CheckedProbe -Exe $probeCommand.exe -Args @($probeCommand.args)
            $probeText = $probe.combined

            if ($probeText -match "(?i)(rate limit|usage limit|extra usage|token limit|quota exceeded|too many requests|try again later)") {
                Write-Slot "Preflight: claude is currently rate limited (will wait in main loop)."
                return $true
            }

            if ($probe.exitCode -eq 0 -and $probeText -match "PROBE_OK_7Q3") {
                # passes through to bottom of preflight
            }
            elseif ($probe.exitCode -ne 0 -or $probeText -match "(?i)(not\s+logged\s+in|please\s+log\s+in|please\s+sign\s+in|unauthorized|invalid\s+api\s*key|missing\s+api\s*key|authentication\s+failed|credentials?\s+(invalid|missing|expired))") {
                Write-Slot "Preflight: claude auth probe failed (exit=$($probe.exitCode)). Output: $($probeText.Substring(0,[Math]::Min(200,$probeText.Length)))"
                Write-SlotStatus -State "blocked" -Reason "claude_auth_failed" -NextAction "Run claude /login, then rerun Start-ClaudeSlot.ps1"
                return $false
            }
            else {
                Write-Slot "Preflight: claude probe didn't return sentinel but no auth error. Treating as healthy. Output: $($probeText.Substring(0,[Math]::Min(200,$probeText.Length)))"
            }
        }
        catch {
            Write-Slot "Preflight: claude probe threw: $($_.Exception.Message)"
            Write-SlotStatus -State "blocked" -Reason "claude_probe_error" -NextAction "Run claude /login, then rerun Start-ClaudeSlot.ps1"
            return $false
        }
    }

    if ([string]$script:Slot.agent -eq "gemini") {
        try {
            Write-Slot "Preflight: probing gemini..."
            $probeCommand = Resolve-ProcessCommand -Exe $exe -Args @("-p", "Reply exactly GEMINI_PREFLIGHT_OK", "--skip-trust")
            $probe = Invoke-CheckedProbe -Exe $probeCommand.exe -Args @($probeCommand.args)
            $probeText = $probe.combined

            if ($probeText -match "(?i)(rate limit|usage limit|token limit|quota exceeded|too many requests|try again later)") {
                Write-Slot "Preflight: gemini is currently rate limited (will wait in main loop)."
                return $true
            }

            if ($probeText -match "GEMINI_PREFLIGHT_OK") {
                return $true
            }

            Write-Slot "Preflight: gemini auth probe failed (exit=$($probe.exitCode)). Output: $probeText"
            Write-SlotStatus -State "blocked" -Reason "gemini_auth_failed" -NextAction "Run gemini login, then rerun Start-GeminiSlot.ps1"
            return $false
        }
        catch {
            $err = $_.Exception.Message
            Write-Slot "Preflight: gemini probe threw: $err"
            Write-SlotStatus -State "blocked" -Reason "gemini_probe_error: $err" -NextAction "Ensure gemini is installed and authenticated."
            return $false
        }
    }

    Write-SlotStatus -State "online"
    $script:LastPreflightOk = Get-Date
    return $true
}

function Invoke-TaskMovement {
    param(
        [Parameter(Mandatory = $true)][string]$From,
        [Parameter(Mandatory = $true)][string]$To,
        [Parameter(Mandatory = $true)][string]$TaskName,
        [string]$Reason = "agent slot queue movement"
    )

    $moveScript = Join-Path $OrchestratorRoot "scripts\Move-OrchestratorTask.ps1"
    if (-not (Test-Path $moveScript)) {
        throw "Task movement helper was not found: $moveScript"
    }

    return & $moveScript `
        -Root $OrchestratorRoot `
        -From $From `
        -To $To `
        -TaskName $TaskName `
        -Slot $script:SlotName `
        -Reason $Reason `
        -PassThru
}

function Join-RootRelativePath {
    param([string]$RelativePath)

    if ([string]::IsNullOrWhiteSpace($RelativePath)) {
        throw "RelativePath is required."
    }

    return Join-Path $OrchestratorRoot $RelativePath
}

function Claim-Task {
    $claimScript = Join-Path $OrchestratorRoot "scripts\Claim-OrchestratorQueueTask.ps1"
    if (!(Test-Path -LiteralPath $claimScript -PathType Leaf)) {
        throw "Claim selector helper was not found: $claimScript"
    }

    $slotRole = Get-SlotRole
    $claimParams = @{
        Root = $OrchestratorRoot
        SlotName = $script:SlotName
        Role = $slotRole
        Capabilities = @($slotRole, [string]$script:Slot.agent)
        PassThru = $true
    }

    if (Test-UrgentOnlyMode) {
        $claimParams["UrgentOnly"] = $true
    }

    $claim = & $claimScript @claimParams

    if ($null -eq $claim) {
        Write-Slot "No claim result returned by queue selector."
        Write-SlotStatus -State "blocked" -Reason "claim_selector_no_result" -NextAction "Inspect Claim-OrchestratorQueueTask.ps1 and queue state."
        return $null
    }

    if (-not $claim.ok) {
        Write-Slot "Queue selector failed: $($claim.error)"
        Write-SlotStatus -State "blocked" -Reason "claim_selector_failed" -NextAction $claim.error
        return $null
    }

    if ($claim.state -eq "claimed") {
        return Join-RootRelativePath -RelativePath ([string]$claim.activePath)
    }

    if ($claim.state -eq "no_compatible_task") {
        Write-Slot "No compatible queued task for slot $script:SlotName."
        Write-SlotStatus -State "idle" -Reason "no_compatible_task" -NextAction "Queue a compatible task for $script:SlotName or update slot capabilities."
        return $null
    }

    if ($claim.state -eq "no_urgent_task") {
        Write-Slot "Urgent-only mode is enabled and no urgent queued task is available for $script:SlotName."
        Write-SlotStatus -State "idle" -Reason "no_urgent_task" -NextAction "Queue a P0/urgent task or disable ORCH_URGENT_ONLY."
        return $null
    }

    if ($claim.state -eq "no_queued_tasks") {
        Write-Slot "No queued task. Sleeping."
        Write-SlotStatus -State "idle" -Reason "no_queued_tasks" -NextAction "Queue work before starting $script:SlotName."
        return $null
    }

    Write-Slot "Queue selector returned non-claim state: $($claim.state)"
    Write-SlotStatus -State "idle" -Reason ([string]$claim.state) -NextAction "Inspect queue selector output."
    return $null
}

function Install-Contract {
    param([string]$TaskPath)

    $contractSource = Join-Path $OrchestratorRoot "docs\agent-contract.md"
    if (!(Test-Path $contractSource)) {
        throw "Missing agent contract: $contractSource"
    }

    Copy-Item $contractSource (Join-Path $WorktreePath "AGENT_RESUME.md") -Force
    Copy-Item $TaskPath (Join-Path $WorktreePath "TASK_QUEUE.md") -Force

    $agentLog = Join-Path $WorktreePath "AGENT_LOG.md"
    if (!(Test-Path $agentLog)) {
        "# AGENT_LOG.md`n" | Set-Content -Path $agentLog -Encoding UTF8
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $WorktreePath "agent-logs") | Out-Null
}

function Normalize-TaskText {
    param([string]$Text)

    if ($null -eq $Text) { return "" }
    return (($Text -replace "`r`n", "`n") -replace "`r", "`n").TrimEnd("`n")
}

function Test-InstalledTaskQueueMatchesClaim {
    param([Parameter(Mandatory = $true)][string]$TaskPath)

    $installedTaskPath = Join-Path $WorktreePath "TASK_QUEUE.md"
    if (!(Test-Path -LiteralPath $installedTaskPath -PathType Leaf)) {
        return [pscustomobject]@{
            ok = $false
            reason = "TASK_QUEUE.md missing after contract install."
            installedTaskPath = $installedTaskPath
        }
    }

    $claimedText = Normalize-TaskText -Text (Get-Content -LiteralPath $TaskPath -Raw -ErrorAction Stop)
    $installedText = Normalize-TaskText -Text (Get-Content -LiteralPath $installedTaskPath -Raw -ErrorAction Stop)

    if ($claimedText -ne $installedText) {
        return [pscustomobject]@{
            ok = $false
            reason = "Installed TASK_QUEUE.md does not equal claimed active task content."
            installedTaskPath = $installedTaskPath
        }
    }

    return [pscustomobject]@{
        ok = $true
        reason = ""
        installedTaskPath = $installedTaskPath
    }
}

function Get-AgentCommandSpec {
    param([bool]$Resume)

    if ($Resume -and $null -ne $script:Slot.command.resume) {
        return @($script:Slot.command.resume)
    }

    return @($script:Slot.command.start)
}

function Extract-ErrorMessage {
    param([string]$Output)

    if ([string]::IsNullOrWhiteSpace($Output)) { return $null }

    if ($Output -match "(?i)insufficient.quota|quota.exceeded|billing|payment") {
        $match = [regex]::Matches($Output, "(?i)(insufficient.quota|quota.exceeded|.*billing.*|.*payment.*error.*)")
        if ($match.Count -gt 0) {
            return $match[0].Value.Trim()
        }
    }

    if ($Output -match "(?i)unauthorized|auth.*fail|401|credential|api.*key") {
        $match = [regex]::Matches($Output, "(?i)(unauthorized|auth\w*\s*fail\w*|401.*|credential.*|api.*key.*)")
        if ($match.Count -gt 0) {
            return $match[0].Value.Trim()
        }
    }

    if ($Output -match "(?i)timeout|connection|refused|unreachable") {
        $match = [regex]::Matches($Output, "(?i)(timeout\w*|connection\w*|refused|unreachable)")
        if ($match.Count -gt 0) {
            return $match[0].Value.Trim()
        }
    }

    $lines = @($Output -split "`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($lines.Count -gt 0) {
        $lastLine = $lines[-1]
        if ($lastLine.Length -gt 200) {
            return $lastLine.Substring(0, 197) + "..."
        }
        return $lastLine
    }

    return $null
}

function Invoke-Agent {
    param(
        [bool]$Resume,
        [string]$LogFile
    )

    $slotRole = Get-SlotRole
    if (Test-CodexTokenSaverMode) {
        $prompt = "Read AGENT_RESUME.md and TASK_QUEUE.md. Slot '$script:SlotName', role '$slotRole'. Execute only the assigned task. Keep output and file reads compact to save tokens. Prefer targeted edits and cheapest relevant validation. Update AGENT_LOG.md and stop after one completed task or first failed validation."
    }
    else {
        $prompt = "Read AGENT_RESUME.md and TASK_QUEUE.md. You are slot '$script:SlotName' with role '$slotRole'. Use the role only to guide execution style; it does not expand scope or delegation authority. Continue only the assigned task. Use local GameMaker tooling when helpful. Do not ask permission unless blocked. Split work into small commits, validate, update AGENT_LOG.md, then stop after one completed task or one failed validation cycle."
    }
    $cmdSpec = Get-AgentCommandSpec -Resume:$Resume

    if ($cmdSpec.Count -lt 1) {
        throw "Agent command spec is empty for slot $script:SlotName."
    }

    $exe = [string]$cmdSpec[0]
    $args = @()

    for ($i = 1; $i -lt $cmdSpec.Count; $i++) {
        $token = ([string]$cmdSpec[$i]).Replace("{prompt}", $prompt)
        # {task_path} — absolute path to the active task file claimed by the orchestrator.
        # Useful for browser/external runners that need the task content directly.
        $activeTaskPath = if (-not [string]::IsNullOrWhiteSpace([string]$script:ActiveTaskPath)) { [string]$script:ActiveTaskPath } else { "" }
        $token = $token.Replace("{task_path}", $activeTaskPath)
        # {orchestratorRoot} — absolute path to the orchestrator repo root.
        # Use this in agents.json command specs to reference scripts by absolute path
        # so the runner finds them regardless of which agent worktree it executes in.
        $token = $token.Replace("{orchestratorRoot}", $OrchestratorRoot)
        $args += $token
    }

    $resolvedCommand = Resolve-ProcessCommand -Exe $exe -Args $args

    # Map slot-specific API key env vars to the canonical name the CLI expects.
    # Pattern: CLAUDE_MAIN_API_KEY → ANTHROPIC_API_KEY for the claude slot.
    # This lets each slot carry its own key without polluting the shared ANTHROPIC_API_KEY.
    $slotKeyVar = "CLAUDE_$($script:SlotName.ToUpper().Replace('-','_'))_API_KEY"
    $slotKey = [System.Environment]::GetEnvironmentVariable($slotKeyVar)
    if (-not [string]::IsNullOrWhiteSpace($slotKey)) {
        $env:ANTHROPIC_API_KEY = $slotKey
        Add-LogLine -Path $LogFile -Message "Using $slotKeyVar for ANTHROPIC_API_KEY."
    }

    Add-LogLine -Path $LogFile -Message "`n===== $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") $($resolvedCommand.exe) $($resolvedCommand.args -join ' ') ====="

    $result = Invoke-NativeCommandCaptured -Exe $resolvedCommand.exe -Args @($resolvedCommand.args) -WorkingDirectory $WorktreePath
    Add-OutputBlockToLog -LogFile $LogFile -Label "stdout" -Text ([string]$result.stdout)
    Add-OutputBlockToLog -LogFile $LogFile -Label "stderr" -Text ([string]$result.stderr)

    if ($result.timedOut) {
        return @{
            ExitCode = 124
            Output = [string]$result.combined
            ErrorMessage = "Agent process timed out"
        }
    }

    return @{
        ExitCode = [int]$result.exitCode
        Output = [string]$result.combined
        ErrorMessage = Extract-ErrorMessage -Output ([string]$result.combined)
    }
}

function Invoke-ValidationCommand {
    param(
        [string]$Command,
        [string]$LogFile
    )

    $expandedCommand = $Command.Replace("{worktreePath}", $WorktreePath).Replace("{orchestratorRoot}", $OrchestratorRoot)
    Add-LogLine -Path $LogFile -Message "`n===== validation: $expandedCommand ====="

    Push-Location $WorktreePath
    try {
        $result = Invoke-NativeCommandCaptured -Exe "cmd.exe" -Args @("/c", $expandedCommand) -WorkingDirectory $WorktreePath
        $lines = New-Object System.Collections.Generic.List[string]

        foreach ($line in @([string]$result.stdout -split "`r?`n")) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $lines.Add($line)
            Add-LogLine -Path $LogFile -Message $line
            if (-not $Headless) { Write-Host $line }
        }

        foreach ($line in @([string]$result.stderr -split "`r?`n")) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $lines.Add($line)
            Add-LogLine -Path $LogFile -Message $line
            if (-not $Headless) { Write-Host $line }
        }

        $exit = if ($result.timedOut) { 124 } else { $result.exitCode }
        if ($null -eq $exit) { $exit = 1 }

        return @{
            ExitCode = [int]$exit
            Output = [string]$result.combined
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-ProjectValidation {
    param([string]$LogFile)

    if ($null -eq $script:ProjectProfile -or $null -eq $script:ProjectProfile.validation) {
        Add-LogLine -Path $LogFile -Message "No project validation commands configured."
        return $true
    }

    $commands = @($script:ProjectProfile.validation)
    if ($commands.Count -eq 0) {
        Add-LogLine -Path $LogFile -Message "Project validation command list is empty."
        return $true
    }

    foreach ($command in $commands) {
        if ([string]::IsNullOrWhiteSpace([string]$command)) { continue }

        $result = Invoke-ValidationCommand -Command ([string]$command) -LogFile $LogFile
        if ($result.ExitCode -ne 0) {
            Add-LogLine -Path $LogFile -Message "Validation failed. ExitCode=$($result.ExitCode). Command=$command"
            return $false
        }
    }

    Add-LogLine -Path $LogFile -Message "All configured validation commands passed."
    return $true
}

function Move-TaskSafe {
    param(
        [string]$TaskPath,
        [string]$DestinationDir
    )

    $name = Split-Path $TaskPath -Leaf
    $sourceParent = (Split-Path $TaskPath -Parent)
    $destinationParent = (Resolve-Path $DestinationDir).Path

    $stateByPath = @{
        (Resolve-Path $script:QueueDir).Path = "queue"
        (Resolve-Path $script:ActiveDir).Path = "active"
        (Resolve-Path $script:DoneDir).Path = "done"
        (Resolve-Path $script:FailedDir).Path = "failed"
    }

    $sourceKey = (Resolve-Path $sourceParent).Path
    if (-not $stateByPath.ContainsKey($sourceKey)) {
        throw "Unsupported source task directory: $sourceParent"
    }

    if (-not $stateByPath.ContainsKey($destinationParent)) {
        throw "Unsupported destination task directory: $DestinationDir"
    }

    $toState = [string]$stateByPath[$destinationParent]
    $movement = Invoke-TaskMovement -From ([string]$stateByPath[$sourceKey]) -To $toState -TaskName $name -Reason ("runner move to {0}" -f $toState)
    return Join-RootRelativePath -RelativePath ([string]$movement.destinationPath)
}

$script:Slot = ConvertFrom-Base64Json -Value $SlotJsonBase64
$script:Project = ConvertFrom-Base64Json -Value $ProjectJsonBase64
$script:SlotName = $script:Slot.name
$script:LastPreflightOk = $null
$script:ActiveTaskPath = ""

if (!(Test-Path $OrchestratorRoot)) { throw "OrchestratorRoot not found: $OrchestratorRoot" }
if (!(Test-Path $WorktreePath)) { throw "WorktreePath not found: $WorktreePath" }

$profilePath = $null
if ($null -ne $script:Project.profilePath -and -not [string]::IsNullOrWhiteSpace($script:Project.profilePath)) {
    $profilePath = Join-Path $OrchestratorRoot ([string]$script:Project.profilePath)
}
$script:ProjectProfile = Read-JsonFileOrNull -Path $profilePath

$script:QueueDir = Join-Path $OrchestratorRoot "tasks\queue"
$script:ActiveDir = Join-Path $OrchestratorRoot "tasks\active"
$script:DoneDir = Join-Path $OrchestratorRoot "tasks\done"
$script:FailedDir = Join-Path $OrchestratorRoot "tasks\failed"
$script:LogDir = Join-Path $OrchestratorRoot "logs\$script:SlotName"

foreach ($dir in @($script:QueueDir, $script:ActiveDir, $script:DoneDir, $script:FailedDir, $script:LogDir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Slot "Online. Role: $(Get-SlotRole). Worktree: $WorktreePath"
if ($null -ne $script:ProjectProfile) {
    Write-Slot "Loaded project profile: $($script:ProjectProfile.name)"
}
else {
    Write-Slot "No project profile loaded. Validation commands will be skipped."
}

if (Test-UrgentOnlyMode) {
    Write-Slot "Urgent-only claim mode enabled (ORCH_URGENT_ONLY/ORCH_URGENT_P0_ONLY)."
}
if (Test-CodexTokenSaverMode) {
    Write-Slot "Codex Desktop token-saver prompt mode enabled."
}

while ($true) {
    if (-not (Test-SlotUnlocked)) {
        if ($RunOnce) { exit 3 }
        Start-Sleep -Seconds 60
        continue
    }

    $taskPath = $null
    if (-not [string]::IsNullOrWhiteSpace($ClaimedTaskRelativePath)) {
        $candidateTaskPath = Join-RootRelativePath -RelativePath $ClaimedTaskRelativePath
        if (Test-Path -LiteralPath $candidateTaskPath -PathType Leaf) {
            Write-Slot "Using claimed active task path from orchestrator action: $ClaimedTaskRelativePath"
            $taskPath = $candidateTaskPath
            $script:ActiveTaskPath = $candidateTaskPath
            $ClaimedTaskRelativePath = ""
        }
        else {
            Write-Slot "Claimed task path was not found: $ClaimedTaskRelativePath"
            Write-SlotStatus -State "blocked" -Reason "claimed_task_path_missing" -NextAction "Verify claimed active task path before launch."
            if ($RunOnce) { exit 2 }
            Start-Sleep -Seconds 60
            continue
        }
    }

    if ($null -eq $taskPath) {
        $taskPath = Claim-Task
    }

    if ($null -eq $taskPath) {
        Write-Slot "No queued task. Sleeping."
        if ($RunOnce) { exit 0 }
        Start-Sleep -Seconds 60
        continue
    }

    if (-not (Test-AgentReady)) {
        $preflightStatus = Read-SlotStatus
        $underlyingReason = "preflight_failed_unknown"
        $underlyingNextAction = "Inspect status and slot preflight output."

        if ($null -ne $preflightStatus) {
            if (-not [string]::IsNullOrWhiteSpace([string]$preflightStatus.reason)) {
                $underlyingReason = [string]$preflightStatus.reason
            }
            if (-not [string]::IsNullOrWhiteSpace([string]$preflightStatus.nextAction)) {
                $underlyingNextAction = [string]$preflightStatus.nextAction
            }
        }

        Write-Slot "Preflight blocked after claim. Returning task to queue: $(Split-Path $taskPath -Leaf). Underlying reason: $underlyingReason"
        Move-TaskSafe -TaskPath $taskPath -DestinationDir $script:QueueDir | Out-Null
        Write-SlotStatus `
            -State "blocked" `
            -Reason "agent_preflight_blocked_after_claim" `
            -UnderlyingReason $underlyingReason `
            -ClaimState "returned_to_queue_after_claim" `
            -NextAction ("Task was returned to queue after claim. Underlying preflight reason: {0}. {1}" -f $underlyingReason, $underlyingNextAction)
        if ($RunOnce) { exit 2 }
        Start-Sleep -Seconds 60
        continue
    }

    $taskName = Split-Path $taskPath -Leaf
    $logFile = Join-Path $script:LogDir ("{0}-{1}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $taskName)

    Write-Slot "Claimed task: $taskName"
    Write-SlotStatus -State "active" -Reason $taskName -NextAction "Let $script:SlotName finish the active task or inspect the dashboard if it stalls."
    Install-Contract -TaskPath $taskPath
    $taskQueueMatch = Test-InstalledTaskQueueMatchesClaim -TaskPath $taskPath
    if (-not $taskQueueMatch.ok) {
        $mismatchReason = [string]$taskQueueMatch.reason
        Write-Slot "Task queue install mismatch detected before launch: $mismatchReason"
        Add-LogLine -Path $logFile -Message "Task queue install mismatch detected before launch: $mismatchReason"
        Move-TaskSafe -TaskPath $taskPath -DestinationDir $script:QueueDir | Out-Null
        Write-SlotStatus `
            -State "blocked" `
            -Reason "task_queue_mismatch_before_launch" `
            -UnderlyingReason $mismatchReason `
            -ClaimState "returned_to_queue_after_claim" `
            -NextAction "Fix slot/worktree project binding so TASK_QUEUE.md matches the claimed active task before launch."
        if ($RunOnce) { exit 2 }
        Start-Sleep -Seconds 60
        continue
    }

    $resume = $false
    $finished = $false

    for ($cycle = 0; $cycle -le $MaxResumeCycles; $cycle++) {
        Add-LogLine -Path $logFile -Message "`n--- cycle=$cycle resume=$resume ---"

        try {
            $result = Invoke-Agent -Resume:$resume -LogFile $logFile
        }
        catch {
            $exceptionMsg = $_.Exception.Message
            $failureDetails = "Exception: $exceptionMsg"
            if ($null -ne $_.Exception.InnerException) {
                $failureDetails += " | Inner: $($_.Exception.InnerException.Message)"
            }

            Add-LogLine -Path $logFile -Message "Runner failure: $failureDetails"
            Add-LogLine -Path $logFile -Message "Full error details: $($_ | Out-String)"
            Write-Slot "Runner failure: $exceptionMsg"
            Move-TaskSafe -TaskPath $taskPath -DestinationDir $script:FailedDir | Out-Null
            Write-SlotStatus -State "blocked" -Reason "runner_failure" -NextAction "See latest $script:SlotName log for runner error details. Fix and requeue when ready."
            $finished = $true
            break
        }

        if (Test-RateLimited $result.Output) {
            $wait = Get-WaitSeconds $result.Output
            Write-Slot "Rate/token limited. Sleeping $([Math]::Round($wait / 60, 1)) minutes."
            Write-SlotStatus -State "sleeping" -Reason "token_or_rate_limit" -NextAction "Wait for $script:SlotName limit reset, then let the runner resume."
            Add-LogLine -Path $logFile -Message "Rate/token limited. Sleeping $wait seconds."
            if ($RunOnce) {
                Write-Slot "RunOnce mode: returning claimed task to queue instead of sleeping."
                Move-TaskSafe -TaskPath $taskPath -DestinationDir $script:QueueDir | Out-Null
                Write-SlotStatus `
                    -State "sleeping" `
                    -Reason "token_or_rate_limit" `
                    -UnderlyingReason "rate_limited_runonce_requeued" `
                    -ClaimState "returned_to_queue_after_claim" `
                    -NextAction "Task was returned to queue after rate/token limit in RunOnce mode. Retry after limit reset."
                $finished = $true
                break
            }
            Start-Sleep -Seconds $wait
            $resume = $true
            continue
        }

        if ($result.ExitCode -eq 0) {
            $validationPassed = Invoke-ProjectValidation -LogFile $logFile
            if ($validationPassed) {
                Move-TaskSafe -TaskPath $taskPath -DestinationDir $script:DoneDir | Out-Null
                Write-Slot "Done: $taskName"
                Write-SlotStatus -State "done" -Reason $taskName -NextAction "Review the done task summary in the dashboard."
            }
            else {
                Move-TaskSafe -TaskPath $taskPath -DestinationDir $script:FailedDir | Out-Null
                Write-Slot "Failed validation: $taskName"
                Write-SlotStatus -State "blocked" -Reason "validation_failed" -NextAction "Fix the first validation failure shown in the latest log."
            }

            $finished = $true
            break
        }

        $errorMsg = $result.ErrorMessage
        if ([string]::IsNullOrWhiteSpace($errorMsg)) {
            $errorMsg = "See log for details"
        }

        $failureReason = "agent_exit_$($result.ExitCode)"
        $logMessage = "Non-zero exit from agent. ExitCode=$($result.ExitCode). Error: $errorMsg"
        Add-LogLine -Path $logFile -Message $logMessage
        Move-TaskSafe -TaskPath $taskPath -DestinationDir $script:FailedDir | Out-Null
        Write-Slot "Failed: $taskName - $errorMsg"
        Write-SlotStatus -State "blocked" -Reason $failureReason -NextAction "Review error in latest log: $errorMsg - Then fix and rerun the task."
        $finished = $true
        break
    }

    if (-not $finished) {
        Add-LogLine -Path $logFile -Message "Failed after max resume cycles."
        Move-TaskSafe -TaskPath $taskPath -DestinationDir $script:FailedDir | Out-Null
        Write-Slot "Failed after max resume cycles: $taskName"
        Write-SlotStatus -State "blocked" -Reason "max_resume_cycles" -NextAction "Review the latest $script:SlotName log and decide whether to requeue or split the task."
    }

    if ($RunOnce) { exit 0 }
}
