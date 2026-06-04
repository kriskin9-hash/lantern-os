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

$statusScript = Join-Path $Root "scripts\Get-OrchestratorStatus.ps1"
if (-not (Test-Path -LiteralPath $statusScript -PathType Leaf)) {
    throw "Status script not found: $statusScript"
}

$content = Get-Content -LiteralPath $statusScript -Raw

$helper = @'
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

'@

if ($content -notmatch 'function\s+Get-QueueRecommendationOrNull') {
    $anchor = '$queueDir = Join-Path $Root "tasks\queue";'
    $index = $content.IndexOf($anchor, [System.StringComparison]::Ordinal)
    if ($index -lt 0) {
        throw "Could not find queue directory anchor in Get-OrchestratorStatus.ps1"
    }
    $content = $content.Insert($index, $helper)
}

if ($content -notmatch '\$queueRecommendation\s*=\s*Get-QueueRecommendationOrNull') {
    $anchor = '$queueTasks = @(Get-FileSummary $queueDir); $activeTasks = @(Get-FileSummary $activeDir); $doneTasks = @(Get-FileSummary $doneDir); $failedTasks = @(Get-FileSummary $failedDir); $limitMap = Get-AgentLimitMap; $slotConfigMap = Get-AgentSlotConfigMap; $worktreeRoot = Get-WorktreeRoot'
    $index = $content.IndexOf($anchor, [System.StringComparison]::Ordinal)
    if ($index -lt 0) {
        throw "Could not find task summary anchor in Get-OrchestratorStatus.ps1"
    }
    $insertAt = $index + $anchor.Length
    $content = $content.Insert($insertAt, "`r`n`$queueRecommendation = Get-QueueRecommendationOrNull")
}

if ($content -notmatch 'queueRecommendation\s*=\s*\$queueRecommendation') {
    $anchor = '    availability = $availability'
    $index = $content.IndexOf($anchor, [System.StringComparison]::Ordinal)
    if ($index -lt 0) {
        throw "Could not find availability field anchor in Get-OrchestratorStatus.ps1"
    }
    $insertAt = $index + $anchor.Length
    $content = $content.Insert($insertAt, "`r`n    queueRecommendation = `$queueRecommendation")
}

Set-Content -LiteralPath $statusScript -Value $content -Encoding UTF8

$syntax = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "tests\Test-PowerShellSyntax.ps1") -Root $Root 2>&1
if ($LASTEXITCODE -ne 0) {
    $syntaxText = ($syntax | ForEach-Object { $_.ToString() }) -join "`n"
    throw "PowerShell syntax validation failed after patch:`n$syntaxText"
}

$statusJson = & powershell -NoProfile -ExecutionPolicy Bypass -File $statusScript -Root $Root 2>&1
if ($LASTEXITCODE -ne 0) {
    $statusText = ($statusJson | ForEach-Object { $_.ToString() }) -join "`n"
    throw "Get-OrchestratorStatus.ps1 failed after patch:`n$statusText"
}

$status = (($statusJson | ForEach-Object { $_.ToString() }) -join "`n") | ConvertFrom-Json
if ($null -eq $status.PSObject.Properties['queueRecommendation']) {
    throw "Status JSON did not include queueRecommendation after patch."
}

Write-Host "Patched Get-OrchestratorStatus.ps1 with queueRecommendation."
$status.queueRecommendation | ConvertTo-Json -Depth 8
