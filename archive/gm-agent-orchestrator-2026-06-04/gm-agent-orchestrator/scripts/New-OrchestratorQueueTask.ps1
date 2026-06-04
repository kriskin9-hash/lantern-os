<#
.SYNOPSIS
Create a new orchestrator queue task markdown file.

.DESCRIPTION
Creates a task file in tasks/queue using the same durable queue format that
agent slots already consume. This is the local write path for delegators and
connectors that need to add work without moving an existing task file.

The script performs conservative validation, avoids overwriting existing tasks,
writes an audit record, and returns JSON so connector wrappers can expose it as
an action safely.

.PARAMETER Title
Brief one-line task title.

.PARAMETER Body
Markdown body for the task. Connector callers should use this field when they
already have structured task text.

.PARAMETER Reason
Compatibility alias for older callers. When Body is omitted, Reason becomes the
Objective section in the generated task template.

.PARAMETER Priority
Priority: P0, P1, or P2. Default: P1.

.PARAMETER Owner
Target owner: claude, codex, gemini, gpt, human, or operator-intake. Default: claude.

.PARAMETER BlockedBy
Optional task or issue this task depends on.

.PARAMETER Root
Repository root. Defaults to the parent directory of this script.

.PARAMETER DryRun
Validate and show the file that would be written without creating it. Dry runs
still write an audit record for connector/control-plane traceability.

.EXAMPLE
.\scripts\New-OrchestratorQueueTask.ps1 `
    -Title "Add connector write action for sleeping Claude" `
    -Body "## Problem`nConnector can read status but cannot create queue work." `
    -Priority P1 `
    -Owner claude
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$Title,

    [Parameter()]
    [string]$Body = "",

    [Parameter()]
    [string]$Reason = "Follow-up work discovered during execution",

    [Parameter()]
    [ValidateSet("P0", "P1", "P2")]
    [string]$Priority = "P1",

    [Parameter()]
    [ValidateSet("claude", "codex", "gemini", "gpt", "human", "operator-intake")]
    [string]$Owner = "claude",

    [Parameter()]
    [string]$BlockedBy = "",

    [Parameter()]
    [string]$Root = "",

    [Parameter()]
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function ConvertTo-Slug {
    param([Parameter(Mandatory)][string]$Value)

    $slug = $Value.ToLowerInvariant()
    $slug = [regex]::Replace($slug, "[^a-z0-9]+", "-")
    $slug = $slug.Trim("-")
    if ([string]::IsNullOrWhiteSpace($slug)) { return "task" }
    if ($slug.Length -gt 60) { return $slug.Substring(0, 60).Trim("-") }
    return $slug
}

function Test-SafeTitle {
    param([Parameter(Mandatory)][string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Title is required." }
    if ($Value.Length -gt 180) { throw "Title must be 180 characters or fewer." }
    if ($Value -match "[\r\n\x00]") { throw "Title must be a single line and must not contain NUL bytes." }
}

function Test-SafeBodyText {
    param(
        [Parameter(Mandatory)][string]$Value,
        [bool]$RequireMarkdownHeading = $false
    )

    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Task body is required." }
    if ($Value.Length -gt 20000) { throw "Task body must be 20000 characters or fewer." }
    if ($Value.IndexOf([char]0) -ge 0) { throw "Task body must not contain NUL bytes." }
    if ($Value -match "[\x01-\x08\x0B\x0C\x0E-\x1F]") { throw "Task body contains unsupported control characters." }
    if ($RequireMarkdownHeading -and $Value -notmatch "(?m)^#{1,6}\s+\S") { throw "Task body must contain at least one Markdown heading." }
}

function Get-RelativePath {
    param([string]$Path, [string]$RootPath)
    if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $fullRoot = [System.IO.Path]::GetFullPath($RootPath).TrimEnd("\")
    if ($fullPath.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $fullPath.Substring($fullRoot.Length).TrimStart("\") -replace "\\", "/"
    }
    return $fullPath
}

function Get-CountMap {
    param([string]$RootPath)

    $states = @("queue", "active", "done", "failed")
    $map = [ordered]@{}
    foreach ($state in $states) {
        $dir = Join-Path $RootPath ("tasks\{0}" -f $state)
        $items = @()
        if (Test-Path $dir) {
            $items = @(Get-ChildItem $dir -File -Filter "*.md" -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne ".gitkeep" })
        }
        $map[$state] = $items.Count
    }
    return [pscustomobject]$map
}

function Get-Sha256Hex {
    param([Parameter(Mandatory)][string]$Value)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        $hash = $sha.ComputeHash($bytes)
        return (($hash | ForEach-Object { $_.ToString("x2") }) -join "")
    }
    finally {
        $sha.Dispose()
    }
}

function Write-AuditEvent {
    param(
        [Parameter(Mandatory)][string]$RootPath,
        [Parameter(Mandatory)][object]$Payload
    )

    $dir = Join-Path $RootPath "logs\control-actions"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
    $path = Join-Path $dir ("{0}-create_queue_task.json" -f $stamp)
    $i = 0
    while (Test-Path $path) {
        $i++
        $path = Join-Path $dir ("{0}-{1}-create_queue_task.json" -f $stamp, $i)
    }

    $Payload | ConvertTo-Json -Depth 20 | Set-Content -Path $path -Encoding UTF8
    return $path
}

function New-MarkdownTask {
    param(
        [string]$TaskTitle,
        [string]$TaskBody,
        [string]$TaskReason,
        [string]$TaskPriority,
        [string]$TaskOwner,
        [string]$Dependency,
        [string]$CreatedTimestamp
    )

    $lines = @(
        "# $TaskTitle",
        "",
        "Priority: $TaskPriority",
        "Owner: $TaskOwner",
        "Created: $CreatedTimestamp",
        "Source: connector-action",
        ""
    )

    if (![string]::IsNullOrWhiteSpace($Dependency)) {
        $lines += "Blocked by: $Dependency"
        $lines += ""
    }

    if (![string]::IsNullOrWhiteSpace($TaskBody)) {
        $lines += $TaskBody.Trim()
        return ($lines -join [Environment]::NewLine) + [Environment]::NewLine
    }

    $lines += @(
        "## Objective",
        $TaskReason,
        "",
        "## Requirements",
        "1. Read `AGENTS.md` and `docs/agent-contract.md` before editing.",
        "2. Keep the change scoped to this task.",
        "3. Preserve existing public script parameters unless a breaking change is explicitly required.",
        "4. Run the cheapest relevant validation first.",
        "",
        "## Acceptance Criteria",
        "- The intended change is implemented or the blocker is documented clearly.",
        "- Validation command output is recorded in `AGENT_LOG.md` or the task handoff.",
        "- Work is committed on a feature branch and opened as a pull request before being marked done.",
        "",
        "## Notes",
        "Created through the queue task creation helper."
    )

    return ($lines -join [Environment]::NewLine) + [Environment]::NewLine
}

Test-SafeTitle -Value $Title
$bodyWasProvided = -not [string]::IsNullOrWhiteSpace($Body)
if ($bodyWasProvided) {
    Test-SafeBodyText -Value $Body -RequireMarkdownHeading $true
}
else {
    Test-SafeBodyText -Value $Reason -RequireMarkdownHeading $false
}

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd("\")
$queueDir = Join-Path $Root "tasks\queue"
if (!(Test-Path $queueDir)) {
    throw "Queue directory does not exist: $queueDir"
}

$queueDirFull = [System.IO.Path]::GetFullPath($queueDir).TrimEnd("\")
if (-not $queueDirFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Queue directory must be inside orchestrator root."
}

$slug = ConvertTo-Slug -Value $Title
$fileName = "$slug.md"
$taskPath = [System.IO.Path]::GetFullPath((Join-Path $queueDir $fileName))

if (-not $taskPath.StartsWith($queueDirFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to write outside tasks/queue."
}

if (Test-Path $taskPath) {
    throw "Refusing to overwrite existing task: $taskPath"
}

$createdTimestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$content = New-MarkdownTask -TaskTitle $Title -TaskBody $Body -TaskReason $Reason -TaskPriority $Priority -TaskOwner $Owner -Dependency $BlockedBy -CreatedTimestamp $createdTimestamp
$contentHash = Get-Sha256Hex -Value $content
$beforeCounts = Get-CountMap -RootPath $Root

$result = [ordered]@{
    ok = $true
    action = "create_queue_task"
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    dryRun = [bool]$DryRun
    path = $taskPath
    relativePath = Get-RelativePath -Path $taskPath -RootPath $Root
    title = $Title
    priority = $Priority
    owner = $Owner
    blockedBy = $BlockedBy
    bodySource = $(if ($bodyWasProvided) { "body" } else { "reason_template" })
    contentSha256 = $contentHash
    beforeCounts = $beforeCounts
    afterCounts = $null
    auditPath = ""
    audit = $null
}

if (!$DryRun) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($taskPath, $content, $utf8NoBom)
}

$result.afterCounts = Get-CountMap -RootPath $Root
$auditPayload = [pscustomobject]$result
$auditPath = Write-AuditEvent -RootPath $Root -Payload $auditPayload
$result.auditPath = $auditPath
$result.audit = [pscustomobject]@{
    path = Get-RelativePath -Path $auditPath -RootPath $Root
    action = "create_queue_task"
    contentSha256 = $contentHash
    dryRun = [bool]$DryRun
    generatedAt = $result.generatedAt
}

[pscustomobject]$result | ConvertTo-Json -Depth 20
