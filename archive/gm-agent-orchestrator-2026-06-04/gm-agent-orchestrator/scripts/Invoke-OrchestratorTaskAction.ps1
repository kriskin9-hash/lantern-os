[CmdletBinding()]
param(
    [string]$Root = "",
    [Parameter(Mandatory = $true)]
    [ValidateSet("requeue_task", "fail_task", "complete_task")]
    [string]$Action,
    [Parameter(Mandatory = $true)]
    [string]$TaskPath,
    [string]$Reason = "",
    [switch]$DryRun,
    [switch]$AllowDirty
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function Get-CountMap {
    $queue = Join-Path $Root "tasks\queue"
    $active = Join-Path $Root "tasks\active"
    $done = Join-Path $Root "tasks\done"
    $failed = Join-Path $Root "tasks\failed"
    return [pscustomobject]@{
        queue = @($(if (Test-Path $queue) { Get-ChildItem $queue -File -Filter "*.md" -ErrorAction SilentlyContinue })).Count
        active = @($(if (Test-Path $active) { Get-ChildItem $active -File -Filter "*.md" -ErrorAction SilentlyContinue })).Count
        done = @($(if (Test-Path $done) { Get-ChildItem $done -File -Filter "*.md" -ErrorAction SilentlyContinue })).Count
        failed = @($(if (Test-Path $failed) { Get-ChildItem $failed -File -Filter "*.md" -ErrorAction SilentlyContinue })).Count
    }
}

function Write-AuditEvent {
    param([object]$Payload)
    $dir = Join-Path $Root "logs\control-actions"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $path = Join-Path $dir ("{0}-{1}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $Action)
    $Payload | ConvertTo-Json -Depth 20 | Set-Content -Path $path -Encoding UTF8
    return $path
}

function Get-CleanTaskName {
    param([string]$Name)
    return ($Name -replace "^[^_]+(?:-[^_]+)*__", "")
}

$result = [ordered]@{
    ok = $true
    action = $Action
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    dryRun = [bool]$DryRun
    allowDirty = [bool]$AllowDirty
    requestedTaskPath = $TaskPath
    sourcePath = ""
    destinationPath = ""
    reason = $Reason
    beforeCounts = $null
    afterCounts = $null
    auditPath = ""
    error = ""
}

try {
    $source = if ([System.IO.Path]::IsPathRooted($TaskPath)) { $TaskPath } else { Join-Path $Root $TaskPath }
    $source = [System.IO.Path]::GetFullPath($source)
    $rootFull = [System.IO.Path]::GetFullPath($Root)
    if (-not $source.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Task path must be inside orchestrator root." }
    if (!(Test-Path $source)) { throw "Task file not found: $source" }
    if ([System.IO.Path]::GetExtension($source) -ne ".md") { throw "Task file must be a markdown file." }

    $leaf = Split-Path $source -Leaf
    $cleanLeaf = Get-CleanTaskName -Name $leaf
    $destDir = switch ($Action) {
        "requeue_task" { Join-Path $Root "tasks\queue" }
        "fail_task" { Join-Path $Root "tasks\failed" }
        "complete_task" { Join-Path $Root "tasks\done" }
    }
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    $dest = Join-Path $destDir $cleanLeaf
    if ((Test-Path $dest) -and -not $DryRun) { throw "Destination already exists: $dest" }

    $result.sourcePath = $source
    $result.destinationPath = $dest
    $result.beforeCounts = Get-CountMap

    if (-not $DryRun) {
        Move-Item -Path $source -Destination $dest -ErrorAction Stop
    }

    $result.afterCounts = Get-CountMap
    $result.auditPath = Write-AuditEvent -Payload ([pscustomobject]$result)
}
catch {
    $result.ok = $false
    $result.error = $_.Exception.Message
    if ($null -eq $result.beforeCounts) { $result.beforeCounts = Get-CountMap }
    $result.afterCounts = Get-CountMap
}

[pscustomobject]$result | ConvertTo-Json -Depth 20
