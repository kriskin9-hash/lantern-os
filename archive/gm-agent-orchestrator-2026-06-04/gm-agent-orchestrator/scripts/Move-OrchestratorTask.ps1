[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("queue", "active", "done", "failed", "hold")]
    [string]$From,

    [Parameter(Mandatory = $true)]
    [ValidateSet("queue", "active", "done", "failed", "hold")]
    [string]$To,

    [Parameter(Mandatory = $true)]
    [string]$TaskName,

    [string]$Root = "",

    [string]$Slot = "",

    [string]$Reason = "",

    [string]$StrategyPath = "",

    [switch]$DryRun,

    [switch]$PassThru
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

if ($From -eq $To) {
    throw "From and To must be different task states."
}

if ([string]::IsNullOrWhiteSpace($TaskName)) {
    throw "TaskName is required."
}

if ($TaskName -match "[\\/]" -or $TaskName -match "\.\.") {
    throw "TaskName must be a file name, not a path: $TaskName"
}

if ([System.IO.Path]::GetFileName($TaskName) -ne $TaskName) {
    throw "TaskName must be a file name, not a path: $TaskName"
}

function Read-JsonOrNull {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    if (-not (Test-Path $Path)) { return $null }

    try { return Get-Content $Path -Raw | ConvertFrom-Json }
    catch { return $null }
}

function Get-TaskTitle {
    param([string]$Path)

    if (-not (Test-Path $Path)) { return "" }

    foreach ($line in @(Get-Content $Path -TotalCount 40 -ErrorAction SilentlyContinue)) {
        $text = ([string]$line).Trim()
        if ([string]::IsNullOrWhiteSpace($text)) { continue }
        if ($text -match "^#\s*(.+)$") { return $Matches[1].Trim() }
        if ($text -match "^Title:\s*(.+)$") { return $Matches[1].Trim() }
    }

    return [System.IO.Path]::GetFileNameWithoutExtension($Path)
}

function Get-TaskIssue {
    param([string]$Name)

    if ($Name -match "(?:^|[^0-9])0*([1-9][0-9]{0,4})(?:-|_)") {
        return [int]$Matches[1]
    }

    return $null
}

function Resolve-StateDir {
    param([string]$State)

    $path = Join-Path $Root ("tasks\{0}" -f $State)
    $resolvedParent = (Resolve-Path (Join-Path $Root "tasks") -ErrorAction Stop).Path

    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }

    $resolved = (Resolve-Path $path -ErrorAction Stop).Path
    if (-not $resolved.StartsWith($resolvedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Resolved task directory escaped tasks root: $resolved"
    }

    return $resolved
}

if ([string]::IsNullOrWhiteSpace($StrategyPath)) {
    $StrategyPath = Join-Path $Root "config\queue-strategies\default.cost-optimized.json"
}
elseif (-not [System.IO.Path]::IsPathRooted($StrategyPath)) {
    $StrategyPath = Join-Path $Root $StrategyPath
}

$strategy = Read-JsonOrNull -Path $StrategyPath
$strategyName = if ($strategy -and $strategy.name) { [string]$strategy.name } else { "none" }
$costMode = if ($strategy -and $strategy.costMode) { [string]$strategy.costMode } else { "unspecified" }
if ([string]::IsNullOrWhiteSpace($Reason)) {
    if ($strategy -and $strategy.movementPolicy -and $strategy.movementPolicy.defaultReason) {
        $Reason = [string]$strategy.movementPolicy.defaultReason
    }
    else {
        $Reason = "manual queue movement"
    }
}

$sourceDir = Resolve-StateDir -State $From
$destinationDir = Resolve-StateDir -State $To
$sourcePath = Join-Path $sourceDir $TaskName

if (-not (Test-Path $sourcePath)) {
    throw "Source task was not found: tasks\$From\$TaskName"
}

$sourceItem = Get-Item $sourcePath
if ($sourceItem.PSIsContainer) {
    throw "Source task is a directory, not a file: tasks\$From\$TaskName"
}

$destinationName = $TaskName
if ($To -eq "active" -and -not [string]::IsNullOrWhiteSpace($Slot) -and $TaskName -notlike "${Slot}__*") {
    $destinationName = "{0}__{1}" -f $Slot, $TaskName
}
elseif ($From -eq "active" -and $TaskName -match "^([^_]+(?:-[^_]+)*)__(.*)$") {
    $destinationName = $Matches[2]
}

if ($destinationName -match "[\\/]" -or $destinationName -match "\.\.") {
    throw "Resolved destination name is unsafe: $destinationName"
}

$destinationPath = Join-Path $destinationDir $destinationName
if (Test-Path $destinationPath) {
    throw "Destination already exists and will not be overwritten: tasks\$To\$destinationName"
}

$taskTitle = Get-TaskTitle -Path $sourcePath
$issue = Get-TaskIssue -Name $TaskName
$auditDir = Join-Path $Root "reports\queue-movements"
$auditPath = Join-Path $auditDir ("{0}.jsonl" -f (Get-Date -Format "yyyyMMdd"))

$movement = [pscustomobject]@{
    ok = $true
    dryRun = [bool]$DryRun
    generatedAt = (Get-Date).ToString("o")
    strategyName = $strategyName
    costMode = $costMode
    reason = $Reason
    slot = $Slot
    from = $From
    to = $To
    taskName = $TaskName
    destinationName = $destinationName
    taskTitle = $taskTitle
    issue = $issue
    sourcePath = $sourcePath.Replace($Root, "").TrimStart("\")
    destinationPath = $destinationPath.Replace($Root, "").TrimStart("\")
    auditPath = $auditPath.Replace($Root, "").TrimStart("\")
}

if ($DryRun) {
    if ($PassThru) { return $movement }
    $movement | ConvertTo-Json -Depth 8
    return
}

if ($PSCmdlet.ShouldProcess($TaskName, "Move task from $From to $To")) {
    New-Item -ItemType Directory -Force -Path $auditDir | Out-Null
    Move-Item -Path $sourcePath -Destination $destinationPath -ErrorAction Stop

    if (-not (Test-Path $destinationPath)) {
        throw "Move failed verification: destination was not created."
    }

    if (Test-Path $sourcePath) {
        throw "Move failed verification: source still exists."
    }

    ($movement | ConvertTo-Json -Depth 8 -Compress) | Add-Content -Path $auditPath -Encoding UTF8
}

if ($PassThru) {
    $movement
}
else {
    $movement | ConvertTo-Json -Depth 8
}
