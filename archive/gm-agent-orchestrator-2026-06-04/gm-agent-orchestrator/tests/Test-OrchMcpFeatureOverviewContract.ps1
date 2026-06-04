<#
.SYNOPSIS
Contract test for the get_mcp_feature_overview tool.

.DESCRIPTION
Validates that the static feature-overview shape in
scripts/Start-OrchMcpServer.Tools.ps1 stays truthful relative to the dynamic
tool registration in Get-ToolsList (Tools.ps1) and Get-GitWorkflowToolSchemas
(Start-OrchMcpServer.GitWorkflowTools.ps1).

The overview lies if any of the following are true:

1. A tool is reported as missing (missingOpsGaps) while it is actually
   registered and exposed.
2. A tool listed in a feature group (groups.*) is not registered.
3. A registered tool is not surfaced in any feature group.

This test parses the source files with regex rather than sourcing them,
mirroring the style of Test-OrchMcpServerContracts.ps1.
#>

[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$toolsScript = Join-Path $Root "scripts/Start-OrchMcpServer.Tools.ps1"
$gitWorkflowToolsScript = Join-Path $Root "scripts/Start-OrchMcpServer.GitWorkflowTools.ps1"

foreach ($path in @($toolsScript, $gitWorkflowToolsScript)) {
    if (!(Test-Path $path)) { throw "Required source file not found: $path" }
}

$toolsContent = Get-Content $toolsScript -Raw
$gitWorkflowContent = Get-Content $gitWorkflowToolsScript -Raw

function Get-RegisteredToolNames {
    param([string]$Content)
    $names = @()
    foreach ($match in [regex]::Matches($Content, 'name\s*=\s*"([a-zA-Z][a-zA-Z0-9_]*)"')) {
        $names += $match.Groups[1].Value
    }
    return $names
}

function Get-NamedStringArray {
    param(
        [string]$Content,
        [string]$Identifier
    )
    $pattern = "$Identifier\s*=\s*@\(([^)]*)\)"
    $match = [regex]::Match($Content, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if (!$match.Success) { throw "Could not locate array assignment for: $Identifier" }
    $body = $match.Groups[1].Value
    $values = @()
    foreach ($m in [regex]::Matches($body, '"([a-zA-Z][a-zA-Z0-9_]*)"')) {
        $values += $m.Groups[1].Value
    }
    return $values
}

$baseRegistered = Get-RegisteredToolNames -Content $toolsContent
$gitWorkflowRegistered = Get-RegisteredToolNames -Content $gitWorkflowContent
$registered = @($baseRegistered + $gitWorkflowRegistered) | Select-Object -Unique

if ($registered.Count -lt 1) {
    throw "Failed to parse any registered tool names from Tools.ps1; the contract test pattern may be out of date."
}

$missingOpsGaps = Get-NamedStringArray -Content $toolsContent -Identifier "missingOpsGaps"

$groupIdentifiers = @(
    "status",
    "taskOps",
    "agentOps",
    "gitAndGitHubOps",
    "powershellOps",
    "serviceOps",
    "gameMakerOps",
    "marketData"
)

$grouped = @{}
$allGrouped = @()
foreach ($identifier in $groupIdentifiers) {
    $names = Get-NamedStringArray -Content $toolsContent -Identifier $identifier
    if ($names.Count -lt 1) { throw "Feature-overview group '$identifier' must list at least one tool." }
    $grouped[$identifier] = $names
    $allGrouped += $names
}

# 1. No tool may be both registered and reported as a missing gap.
$registeredSet = [System.Collections.Generic.HashSet[string]]::new()
foreach ($name in $registered) { [void]$registeredSet.Add($name) }

$lyingGaps = @($missingOpsGaps | Where-Object { $registeredSet.Contains($_) })
if ($lyingGaps.Count -gt 0) {
    throw ("get_mcp_feature_overview lies: missingOpsGaps still lists tools that are actually registered: " + ($lyingGaps -join ", "))
}

# 2. Every group entry must resolve to a registered tool.
$ungroupedKnown = @()
foreach ($identifier in $groupIdentifiers) {
    foreach ($name in $grouped[$identifier]) {
        if (!$registeredSet.Contains($name)) {
            $ungroupedKnown += "$identifier/$name"
        }
    }
}
if ($ungroupedKnown.Count -gt 0) {
    throw ("get_mcp_feature_overview groups reference tools that are not registered: " + ($ungroupedKnown -join ", "))
}

# 3. Every registered tool must be surfaced in some group.
$groupedSet = [System.Collections.Generic.HashSet[string]]::new()
foreach ($name in $allGrouped) { [void]$groupedSet.Add($name) }

$orphans = @($registered | Where-Object { -not $groupedSet.Contains($_) })
if ($orphans.Count -gt 0) {
    throw ("get_mcp_feature_overview groups omit registered tools: " + ($orphans -join ", "))
}

# 4. missingOpsGaps must not duplicate entries.
$gapDupes = @($missingOpsGaps | Group-Object | Where-Object { $_.Count -gt 1 } | ForEach-Object { $_.Name })
if ($gapDupes.Count -gt 0) {
    throw ("missingOpsGaps contains duplicates: " + ($gapDupes -join ", "))
}

Write-Host "Validated get_mcp_feature_overview against Get-ToolsList and Get-GitWorkflowToolSchemas."
Write-Host ("  registered tools: {0}" -f $registered.Count)
Write-Host ("  grouped tools:    {0}" -f $allGrouped.Count)
Write-Host ("  missing gaps:     {0}" -f $missingOpsGaps.Count)
