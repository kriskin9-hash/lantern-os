[CmdletBinding()]
param(
    [string]$Root = "",
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$SlotName,
    [string]$Role = "",
    [string[]]$Capabilities = @(),
    [switch]$UrgentOnly,
    [string]$TaskPath = "",
    [string]$TaskName = "",
    [switch]$DryRun,
    [switch]$PassThru
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

function Get-EnvSwitch {
    param([string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($value)) { return $false }

    switch -Regex ($value.Trim().ToLowerInvariant()) {
        "^(1|true|yes|on)$" { return $true }
        default { return $false }
    }
}

$effectiveUrgentOnly = [bool]$UrgentOnly -or (Get-EnvSwitch -Name "ORCH_URGENT_ONLY") -or (Get-EnvSwitch -Name "ORCH_URGENT_P0_ONLY")

function Get-NormalizedCapabilities {
    $normalized = New-Object System.Collections.Generic.List[string]

    foreach ($item in @($Capabilities)) {
        if ([string]::IsNullOrWhiteSpace([string]$item)) { continue }
        foreach ($part in ([string]$item -split ',')) {
            $value = ([string]$part).Trim()
            if (-not [string]::IsNullOrWhiteSpace($value)) {
                [void]$normalized.Add($value)
            }
        }
    }

    return @($normalized)
}

function New-Result {
    param(
        [bool]$Ok,
        [string]$State,
        [string]$ErrorMessage = "",
        [object]$Extra = $null
    )

    $payload = [ordered]@{
        ok = $Ok
        state = $State
        slot = $SlotName
        role = $Role
        capabilities = @(Get-NormalizedCapabilities)
        urgentOnly = [bool]$effectiveUrgentOnly
        dryRun = [bool]$DryRun
        error = $ErrorMessage
        generatedAt = (Get-Date).ToString("o")
    }

    if ($null -ne $Extra) {
        foreach ($property in $Extra.PSObject.Properties) {
            $payload[$property.Name] = $property.Value
        }
    }

    return [pscustomobject]$payload
}

function Get-ExactTaskSelector {
    $values = @()

    if (-not [string]::IsNullOrWhiteSpace($TaskPath)) {
        $values += [pscustomobject]@{ name = "TaskPath"; value = ([string]$TaskPath).Trim() }
    }

    if (-not [string]::IsNullOrWhiteSpace($TaskName)) {
        $values += [pscustomobject]@{ name = "TaskName"; value = ([string]$TaskName).Trim() }
    }

    if ($values.Count -gt 1) {
        throw "Specify only one exact task selector: TaskPath or TaskName."
    }

    if ($values.Count -eq 0) { return "" }
    return [string]$values[0].value
}

function Resolve-ExactQueueTask {
    param(
        [Parameter(Mandatory = $true)][string]$Selector,
        [Parameter(Mandatory = $true)][string]$QueueDir
    )

    $queueRoot = (Resolve-Path -LiteralPath $QueueDir -ErrorAction Stop).Path
    $selectorText = ([string]$Selector).Trim()
    if ([string]::IsNullOrWhiteSpace($selectorText)) { return $null }

    if ([System.IO.Path]::IsPathRooted($selectorText)) {
        $candidatePath = $selectorText
    }
    elseif ($selectorText -notmatch "[\\/]") {
        $candidatePath = Join-Path $queueRoot $selectorText
    }
    else {
        $candidatePath = Join-Path $Root $selectorText
    }

    $candidateName = [System.IO.Path]::GetFileName($candidatePath)
    if ([string]::IsNullOrWhiteSpace($candidateName)) {
        throw "Exact task selector must name a task file under tasks\queue: $selectorText"
    }

    if ($candidateName -notlike "*.md") {
        throw "Exact task selector must name a markdown task under tasks\queue: $selectorText"
    }

    $candidateParent = Split-Path -Parent $candidatePath
    if ([string]::IsNullOrWhiteSpace($candidateParent) -or -not (Test-Path -LiteralPath $candidateParent -PathType Container)) {
        throw "Exact task selector must resolve directly under tasks\queue: $selectorText"
    }

    $resolvedParent = (Resolve-Path -LiteralPath $candidateParent -ErrorAction Stop).Path
    if (-not [string]::Equals($resolvedParent, $queueRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Exact task selector must resolve directly under tasks\queue: $selectorText"
    }

    $resolvedCandidate = Join-Path $resolvedParent $candidateName
    if (-not (Test-Path -LiteralPath $resolvedCandidate -PathType Leaf)) {
        throw "Queued task was not found: tasks\queue\$candidateName"
    }

    return Get-Item -LiteralPath $resolvedCandidate
}

function Get-TaskTitle {
    param([string]$Path)

    foreach ($line in @(Get-Content -LiteralPath $Path -TotalCount 50 -Encoding UTF8 -ErrorAction SilentlyContinue)) {
        $text = ([string]$line).Trim()
        if ([string]::IsNullOrWhiteSpace($text)) { continue }
        if ($text -match "^#\s*(.+)$") { return $Matches[1].Trim() }
        if ($text -match "^Title:\s*(.+)$") { return $Matches[1].Trim() }
    }

    return [System.IO.Path]::GetFileNameWithoutExtension($Path)
}

function Get-TaskMetadataText {
    param([string]$Path)

    $content = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
    return $content.ToLowerInvariant()
}

function Get-SlotCapabilitySet {
    $values = New-Object System.Collections.Generic.HashSet[string]([System.StringComparer]::OrdinalIgnoreCase)

    foreach ($item in @(Get-NormalizedCapabilities)) {
        if (-not [string]::IsNullOrWhiteSpace($item)) { [void]$values.Add(([string]$item).Trim()) }
    }

    if (-not [string]::IsNullOrWhiteSpace($Role)) { [void]$values.Add($Role.Trim()) }
    if ($SlotName -match "gemini") {
        foreach ($item in @("research", "validation", "web-grounded", "review")) { [void]$values.Add($item) }
    }

    return $values
}

function Test-UrgentTask {
    param(
        [string]$Name,
        [string]$Text
    )

    $haystack = ("$Name`n$Text")
    # Matches P0, explicit priority, or urgent/asap/sev0 unless preceded by "not "
    return ($haystack -match "(?i)(\bp0\b|priority\s*:\s*p0|\b(?<!not\s+)urgent\b|\basap\b|\bsev0\b)")
}

function Get-TaskScore {
    param([string]$Path, [System.Collections.Generic.HashSet[string]]$CapabilitySet)

    $name = ([System.IO.Path]::GetFileName($Path)).ToLowerInvariant()
    $text = Get-TaskMetadataText -Path $Path
    $isUrgent = Test-UrgentTask -Name $name -Text $text
    $score = 0
    $reasons = New-Object System.Collections.Generic.List[string]

    foreach ($cap in $CapabilitySet) {
        $needle = ([string]$cap).ToLowerInvariant()
        if ([string]::IsNullOrWhiteSpace($needle)) { continue }
        if ($name.Contains($needle) -or $text.Contains($needle)) {
            $score += 10
            [void]$reasons.Add("capability:$cap")
        }
    }

    if ($isUrgent) { $score += 5; [void]$reasons.Add("priority:urgent") }
    if ($text.Contains("disaster") -or $text.Contains("recovery")) { $score += 3; [void]$reasons.Add("recovery") }
    if ($text.Contains("handoff")) { $score += 2; [void]$reasons.Add("handoff") }

    $slotAgent = ""
    if ($SlotName -match "codex") { $slotAgent = "codex" }
    elseif ($SlotName -match "claude") { $slotAgent = "claude" }
    elseif ($SlotName -match "gemini") { $slotAgent = "gemini" }
    elseif ($SlotName -match "deepseek") { $slotAgent = "deepseek" }

    if (-not [string]::IsNullOrWhiteSpace($slotAgent)) {
        if ($text -match ("(?im)^\s*owner\s*:\s*{0}\b" -f [regex]::Escape($slotAgent))) {
            $score += 40
            [void]$reasons.Add("owner:$slotAgent")
        }
        if ($text -match ("(?im)^\s*role_owner\s*:\s*{0}\b" -f [regex]::Escape($slotAgent))) {
            $score += 40
            [void]$reasons.Add("role_owner:$slotAgent")
        }
        if ($text -match ("(?im)^\s*fallback_owner\s*:\s*{0}\b" -f [regex]::Escape($slotAgent))) {
            $score += 20
            [void]$reasons.Add("fallback_owner:$slotAgent")
        }
    }

    return [pscustomobject]@{
        path = $Path
        name = [System.IO.Path]::GetFileName($Path)
        title = Get-TaskTitle -Path $Path
        isUrgent = $isUrgent
        score = $score
        reasons = @($reasons)
    }
}

try {
    if (!(Test-Path -LiteralPath $Root -PathType Container)) { throw "Missing root: $Root" }

    $queueDir = Join-Path $Root "tasks\queue"
    $activeDir = Join-Path $Root "tasks\active"
    $moveScript = Join-Path $Root "scripts\Move-OrchestratorTask.ps1"

    if (!(Test-Path -LiteralPath $queueDir -PathType Container)) { throw "Missing queue directory: $queueDir" }
    if (!(Test-Path -LiteralPath $moveScript -PathType Leaf)) { throw "Missing movement helper: $moveScript" }
    New-Item -ItemType Directory -Force -Path $activeDir | Out-Null

    $exactSelector = Get-ExactTaskSelector
    $exactTask = $null
    if (-not [string]::IsNullOrWhiteSpace($exactSelector)) {
        $exactTask = Resolve-ExactQueueTask -Selector $exactSelector -QueueDir $queueDir
    }

    $tasks = @(Get-ChildItem -LiteralPath $queueDir -Filter "*.md" -File -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($tasks.Count -eq 0) {
        $result = New-Result -Ok $true -State "no_queued_tasks" -Extra ([pscustomobject]@{ queueCount = 0; selectedTask = $null })
    }
    else {
        $capabilitySet = Get-SlotCapabilitySet
        $selectionMode = "compatible"
        $scored = @($tasks | ForEach-Object { Get-TaskScore -Path $_.FullName -CapabilitySet $capabilitySet } | Sort-Object @{ Expression = "score"; Descending = $true }, @{ Expression = "name"; Descending = $false })

        if ($null -ne $exactTask) {
            $selectionMode = "exact"
            $selected = Get-TaskScore -Path $exactTask.FullName -CapabilitySet $capabilitySet
        }
        else {
            $eligible = $scored
            if ($effectiveUrgentOnly) {
                $eligible = @($scored | Where-Object { $_.isUrgent })
            }

            $selected = @($eligible | Where-Object { $_.score -gt 0 } | Select-Object -First 1)
            if ($selected.Count -gt 0) {
                $selected = $selected[0]
            }
            else {
                $selected = $null
            }
        }

        if ($null -eq $selected) {
            if ($effectiveUrgentOnly -and @($eligible).Count -eq 0) {
                $result = New-Result -Ok $true -State "no_urgent_task" -Extra ([pscustomobject]@{
                    queueCount = $tasks.Count
                    candidates = @($scored | Select-Object -First 10)
                })
            }
            else {
                $result = New-Result -Ok $true -State "no_compatible_task" -Extra ([pscustomobject]@{
                    queueCount = $tasks.Count
                    candidates = @($eligible | Select-Object -First 10)
                })
            }
        }
        elseif ($DryRun) {
            $movement = & $moveScript -Root $Root -From queue -To active -TaskName $selected.name -Slot $SlotName -Reason ("compatible claim by {0}" -f $SlotName) -DryRun -PassThru
            $result = New-Result -Ok $true -State "claim_dry_run" -Extra ([pscustomobject]@{
                queueCount = $tasks.Count
                selectionMode = $selectionMode
                exactTaskSelector = $exactSelector
                selectedTask = $selected
                movement = $movement
                activePath = [string]$movement.destinationPath
            })
        }
        else {
            $movement = & $moveScript -Root $Root -From queue -To active -TaskName $selected.name -Slot $SlotName -Reason ("compatible claim by {0}" -f $SlotName) -PassThru
            $result = New-Result -Ok $true -State "claimed" -Extra ([pscustomobject]@{
                queueCountBefore = $tasks.Count
                selectionMode = $selectionMode
                exactTaskSelector = $exactSelector
                selectedTask = $selected
                movement = $movement
                activePath = [string]$movement.destinationPath
            })
        }
    }
}
catch {
    $result = New-Result -Ok $false -State "error" -ErrorMessage $_.Exception.Message
}

if ($PassThru) { return $result }
$result | ConvertTo-Json -Depth 30
