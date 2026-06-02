[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$StrategyPath = ""
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

if ([string]::IsNullOrWhiteSpace($StrategyPath)) {
    $StrategyPath = Join-Path $Root "config\queue-strategies\default.cost-optimized.json"
}
elseif (-not [System.IO.Path]::IsPathRooted($StrategyPath)) {
    $StrategyPath = Join-Path $Root $StrategyPath
}

function Read-JsonOrNull {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }
    catch { return $null }
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

function Test-UrgentTask {
    param([string]$Name, [string]$Text)
    return (("$Name`n$Text") -match "(?i)(\bp0\b|priority\s*:\s*p0|\burgent\b|\basap\b|\bsev0\b)")
}

function Get-TaskFiles {
    param([string]$State)
    $dir = Join-Path $Root ("tasks\{0}" -f $State)
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { return @() }
    return @(Get-ChildItem -LiteralPath $dir -File | Where-Object { $_.Name -ne ".gitkeep" } | Sort-Object Name)
}

function Get-TaskText {
    param([System.IO.FileInfo]$File)
    try { return Get-Content -LiteralPath $File.FullName -Raw -ErrorAction Stop }
    catch { return "" }
}

function Get-TaskKind {
    param([string]$Name, [string]$Text)
    $haystack = ("$Name`n$Text").ToLowerInvariant()
    if ($haystack -match "test|validation|fixture") { return "test" }
    if ($haystack -match "implement|feature|script|function|code|fix|bug|refactor") { return "implementation" }
    if ($haystack -match "doc|readme|handoff|report|status|queue|audit") { return "documentation" }
    if ($haystack -match "triage|classif|summar|routing|log") { return "status" }
    return "unknown"
}

function Test-SensitiveTask {
    param([string]$Name, [string]$Text)
    return (("$Name`n$Text") -match "(?i)secret|token|credential|production|deploy|billing")
}

function Get-SlotForKind {
    param([string]$Kind, $Strategy)
    if ($Kind -in @("documentation", "status", "unknown")) { return "free_tier_agent" }
    if ($Kind -in @("test", "implementation")) { return "capable_agent" }
    return "human_review"
}

function Quote-CommandArg {
    param([string]$Value)
    return '"' + ($Value -replace '"', '\"') + '"'
}

function New-Recommendation {
    param(
        [string]$Action,
        [string]$TaskName = "",
        [string]$From = "",
        [string]$To = "",
        [string]$Slot = "",
        [string]$Reason,
        [ValidateSet("low", "medium", "high")][string]$Risk = "low",
        [bool]$RequiresHuman = $false,
        [string]$Command = "",
        $Strategy
    )

    [pscustomobject]@{
        ok = $true
        generatedAt = (Get-Date).ToString("o")
        strategyName = if ($Strategy -and $Strategy.name) { [string]$Strategy.name } else { "none" }
        costMode = if ($Strategy -and $Strategy.costMode) { [string]$Strategy.costMode } else { "unspecified" }
        recommendedAction = $Action
        taskName = $TaskName
        from = $From
        to = $To
        slot = $Slot
        reason = $Reason
        risk = $Risk
        requiresHuman = $RequiresHuman
        command = $Command
    }
}

$strategy = Read-JsonOrNull -Path $StrategyPath
$urgentOnly = (Get-EnvSwitch -Name "ORCH_URGENT_ONLY") -or (Get-EnvSwitch -Name "ORCH_URGENT_P0_ONLY")
$active = @(Get-TaskFiles -State "active")
$failed = @(Get-TaskFiles -State "failed")
$queue = @(Get-TaskFiles -State "queue")

if (@($active).Count -gt 0) {
    $task = $active[0]
    $command = "powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Get-OrchestratorStatus.ps1 -Root {0}" -f (Quote-CommandArg -Value $Root)
    New-Recommendation -Action "inspect" -TaskName $task.Name -From "active" -To "active" -Reason "Active work exists, so inspect current state before claiming more queue work." -Risk "medium" -RequiresHuman $false -Command $command -Strategy $strategy | ConvertTo-Json -Depth 8
    exit 0
}

if (@($failed).Count -gt 0) {
    $task = $failed[0]
    New-Recommendation -Action "inspect" -TaskName $task.Name -From "failed" -To "failed" -Reason "Failed task exists and no active work is present; inspect failure evidence before retrying to avoid repeated token burn." -Risk "medium" -RequiresHuman $false -Command "" -Strategy $strategy | ConvertTo-Json -Depth 8
    exit 0
}

if (@($queue).Count -gt 0) {
    if ($urgentOnly) {
        $urgentQueue = @()
        foreach ($item in $queue) {
            $itemText = Get-TaskText -File $item
            if (Test-UrgentTask -Name $item.Name -Text $itemText) {
                $urgentQueue += [pscustomobject]@{ file = $item; text = $itemText }
            }
        }

        if ($urgentQueue.Count -eq 0) {
            New-Recommendation -Action "none" -Reason "Urgent-only mode is enabled, but no P0/urgent task is currently queued." -Risk "low" -RequiresHuman $false -Command "" -Strategy $strategy | ConvertTo-Json -Depth 8
            exit 0
        }

        $task = $urgentQueue[0].file
        $text = [string]$urgentQueue[0].text
    }
    else {
        $task = $queue[0]
        $text = Get-TaskText -File $task
    }

    $kind = Get-TaskKind -Name $task.Name -Text $text
    if (Test-SensitiveTask -Name $task.Name -Text $text) {
        New-Recommendation -Action "inspect" -TaskName $task.Name -From "queue" -To "queue" -Slot "human_review" -Reason "Queued task mentions sensitive, production, deploy, credential, token, billing, or secret terms; strategy requires human review instead of automatic routing." -Risk "high" -RequiresHuman $true -Command "" -Strategy $strategy | ConvertTo-Json -Depth 8
        exit 0
    }

    $slot = Get-SlotForKind -Kind $kind -Strategy $strategy
    $risk = if ($kind -in @("documentation", "status", "unknown")) { "low" } else { "medium" }
    $reason = if ($kind -in @("documentation", "status", "unknown")) {
        "No active tasks. First queued task appears to be docs/status/queue work, so default.cost-optimized prefers local/free routing before paid high-context agents."
    }
    else {
        "No active tasks. First queued task appears to require code-capable handling, so default.cost-optimized avoids local read-only routing."
    }
    $command = "powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Move-OrchestratorTask.ps1 -From queue -To active -TaskName {0} -Slot {1} -Root {2} -DryRun" -f (Quote-CommandArg -Value $task.Name), (Quote-CommandArg -Value $slot), (Quote-CommandArg -Value $Root)
    New-Recommendation -Action "claim" -TaskName $task.Name -From "queue" -To "active" -Slot $slot -Reason $reason -Risk $risk -RequiresHuman $false -Command $command -Strategy $strategy | ConvertTo-Json -Depth 8
    exit 0
}

New-Recommendation -Action "none" -Reason "No active, failed, or queued tasks were found." -Risk "low" -RequiresHuman $false -Command "" -Strategy $strategy | ConvertTo-Json -Depth 8
