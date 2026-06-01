[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string[]]$ChangedPath = @(),
    [switch]$AsJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path $Root).Path
$rulesPath = Join-Path $Root 'docs\hook-opportunity-rules.yml'
if (-not (Test-Path -LiteralPath $rulesPath -PathType Leaf)) {
    throw "Missing hook opportunity rules: $rulesPath"
}

function Test-PathPattern {
    param(
        [Parameter(Mandatory = $true)] [string]$Path,
        [Parameter(Mandatory = $true)] [string]$Pattern
    )

    $normalizedPath = ($Path -replace '\\', '/')
    $normalizedPattern = ($Pattern -replace '\\', '/')
    $escapedPattern = [regex]::Escape($normalizedPattern)
    $escapedPattern = $escapedPattern.Replace('\*\*/', '(.*/)?')
    $escapedPattern = $escapedPattern.Replace('\*\*', '.*')
    $escapedPattern = $escapedPattern.Replace('\*', '[^/]*')
    $regex = '^' + $escapedPattern + '$'
    return $normalizedPath -match $regex
}

function Test-AnyPathMatches {
    param(
        [string[]]$Paths,
        [string[]]$Patterns
    )

    foreach ($path in $Paths) {
        foreach ($pattern in $Patterns) {
            if (Test-PathPattern -Path $path -Pattern $pattern) { return $true }
        }
    }
    return $false
}

function New-HookOpportunity {
    param(
        [Parameter(Mandatory = $true)] [string]$Id,
        [Parameter(Mandatory = $true)] [string]$Title,
        [Parameter(Mandatory = $true)] [string]$Reason,
        [Parameter(Mandatory = $true)] [string]$Suggestion
    )

    return [pscustomobject]@{
        id = $Id
        severity = 'advisory'
        title = $Title
        reason = $Reason
        suggestion = $Suggestion
    }
}

$paths = @($ChangedPath | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($paths.Count -eq 0) {
    $gitPaths = @(git -C $Root diff --name-only origin/master...HEAD 2>$null)
    if ($LASTEXITCODE -eq 0 -and $gitPaths.Count -gt 0) {
        $paths = $gitPaths
    }
}

$opportunities = @()

$deterministicTriggers = @(
    'scripts/**/*.ps1',
    'config/**/*.json',
    '.github/workflows/**/*.yml',
    '.claude/hooks/**/*.ps1',
    'docs/**/*.md'
)

if (Test-AnyPathMatches -Paths $paths -Patterns $deterministicTriggers) {
    $opportunities += New-HookOpportunity -Id 'deterministic-first' -Title 'Prefer deterministic validation before token-heavy review' -Reason 'Changed files include paths that are often validated by static analysis, schema parsing, regex, diff inspection, logs, status files, or contract tests.' -Suggestion 'Add or reuse deterministic validation before invoking model/tool-heavy review; reserve agents for semantic judgment, ambiguity, architecture, risk, or tradeoffs.'
}

$scriptChanged = Test-AnyPathMatches -Paths $paths -Patterns @('scripts/**/*.ps1')
$testChanged = Test-AnyPathMatches -Paths $paths -Patterns @('tests/**/*.ps1')
if ($scriptChanged -and -not $testChanged) {
    $opportunities += New-HookOpportunity -Id 'script-change-needs-test' -Title 'Script changes should have deterministic validation' -Reason 'A script changed without a matching tests/*.ps1 change.' -Suggestion 'Consider adding or updating a PowerShell contract test for deterministic behavior.'
}

$mcpChanged = Test-AnyPathMatches -Paths $paths -Patterns @('scripts/*Mcp*.ps1', 'scripts/*Tool*.ps1', 'config/**/*mcp*.json')
$mcpTestChanged = Test-AnyPathMatches -Paths $paths -Patterns @('tests/*Mcp*.ps1', 'tests/*Tool*.ps1', 'tests/*Capability*.ps1')
if ($mcpChanged -and -not $mcpTestChanged) {
    $opportunities += New-HookOpportunity -Id 'mcp-change-needs-contract' -Title 'MCP and tool boundary changes need contract coverage' -Reason 'MCP/tool boundary files changed without an obvious contract-test companion.' -Suggestion 'Consider schema, capability-state, or safe-tool contract coverage.'
}

$queueChanged = Test-AnyPathMatches -Paths $paths -Patterns @('scripts/*Queue*.ps1', 'scripts/*Task*.ps1', 'scripts/*AgentAction*.ps1', 'scripts/*OrchestratorAgent*.ps1')
$queueTestChanged = Test-AnyPathMatches -Paths $paths -Patterns @('tests/*Queue*.ps1', 'tests/*Task*.ps1', 'tests/*Agent*.ps1')
if ($queueChanged -and -not $queueTestChanged) {
    $opportunities += New-HookOpportunity -Id 'queue-dispatch-change-needs-dry-run' -Title 'Queue and dispatch changes need dry-run coverage' -Reason 'Queue, task, dispatch, or agent startup code changed without an obvious dry-run contract-test companion.' -Suggestion 'Consider a dry-run contract test that proves no queue movement or agent launch occurs before safety gates pass.'
}

$configChanged = Test-AnyPathMatches -Paths $paths -Patterns @('config/**/*.json')
$configTestChanged = Test-AnyPathMatches -Paths $paths -Patterns @('tests/*Config*.ps1', 'tests/*Safety*.ps1')
if ($configChanged -and -not $configTestChanged) {
    $opportunities += New-HookOpportunity -Id 'config-change-needs-safety-check' -Title 'Config changes need safety validation' -Reason 'JSON config changed without an obvious config/safety test companion.' -Suggestion 'Consider schema or safety validation for changed config.'
}

$hookChanged = Test-AnyPathMatches -Paths $paths -Patterns @('.claude/hooks/**/*.ps1')
$hookTestChanged = Test-AnyPathMatches -Paths $paths -Patterns @('tests/*Hook*.ps1')
if ($hookChanged -and -not $hookTestChanged) {
    $opportunities += New-HookOpportunity -Id 'hook-change-needs-hook-contract' -Title 'Hook changes need hook contract tests' -Reason 'A local hook changed without an obvious hook contract test companion.' -Suggestion 'Consider a deterministic hook contract test.'
}

$result = [pscustomobject]@{
    ok = $true
    mode = 'advisory'
    deterministicFirst = $true
    changedPathCount = $paths.Count
    changedPaths = $paths
    opportunities = @($opportunities)
}

if ($AsJson) {
    $result | ConvertTo-Json -Depth 10
    return
}

if ($opportunities.Count -eq 0) {
    Write-Host 'No hook opportunities detected.'
    return
}

Write-Host 'Hook opportunities detected:'
foreach ($item in $opportunities) {
    Write-Host "- [$($item.severity)] $($item.id): $($item.title)"
    Write-Host "  $($item.suggestion)"
}
