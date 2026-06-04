<#
.SYNOPSIS
Create an action item for the orchestrator queue.

.DESCRIPTION
Creates a new task in the orchestrator queue through the local queue task helper.
This is the compatible write path for delegators and connector wrappers that
need to add work without moving an existing task file.

The script keeps the historical name used by the meta-orchestrator docs while
routing to New-OrchestratorQueueTask.ps1, which returns structured JSON.

.PARAMETER Title
Brief one-line action item title.

.PARAMETER Body
Markdown body for the action item. Prefer this for connector-provided task text.

.PARAMETER Reason
Compatibility alias for older callers. Used when Body is omitted.

.PARAMETER Priority
Priority: P0, P1, or P2. Default: P1.

.PARAMETER Owner
Target agent: claude, codex, gemini, gpt, human, or operator-intake. Default: claude.

.PARAMETER BlockedBy
Optional task or issue this item depends on.

.PARAMETER Root
Repository root. Defaults to the parent directory of this script.

.PARAMETER DryRun
Validate and show the task that would be written without creating it.

.EXAMPLE
.\scripts\New-ActionItemViaMcp.ps1 -Title "Add unit tests for validator" -Priority P1 -Owner codex

.EXAMPLE
$body = "## Problem`nConnector can read status but could not create queue work."
.\scripts\New-ActionItemViaMcp.ps1 `
    -Title "Expose connector queue task action" `
    -Body $body `
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

$helper = Join-Path $PSScriptRoot "New-OrchestratorQueueTask.ps1"
if (!(Test-Path $helper)) {
    throw "Missing queue task helper: $helper"
}

$args = @(
    "-Title", $Title,
    "-Priority", $Priority,
    "-Owner", $Owner
)

if (![string]::IsNullOrWhiteSpace($Body)) {
    $args += @("-Body", $Body)
}
else {
    $args += @("-Reason", $Reason)
}

if (![string]::IsNullOrWhiteSpace($BlockedBy)) {
    $args += @("-BlockedBy", $BlockedBy)
}

if (![string]::IsNullOrWhiteSpace($Root)) {
    $args += @("-Root", $Root)
}

if ($DryRun) {
    $args += "-DryRun"
}

$result = & $helper @args
if ($LASTEXITCODE -ne 0) {
    throw "Queue task helper failed with exit code $LASTEXITCODE"
}

$json = $result | Out-String
$parsed = $json | ConvertFrom-Json -ErrorAction Stop

Write-Host "Action item queued" -ForegroundColor Green
Write-Host ""
Write-Host "  Task: $($parsed.relativePath)" -ForegroundColor Cyan
Write-Host "  Title: $($parsed.title)"
Write-Host "  Priority: $($parsed.priority)"
Write-Host "  Owner: @$($parsed.owner)"
Write-Host "  Dry run: $($parsed.dryRun)"
if ($parsed.audit -and $parsed.audit.path) {
    Write-Host "  Audit: $($parsed.audit.path)"
}
if ($parsed.blockedBy) {
    Write-Host "  Depends on: $($parsed.blockedBy)"
}
Write-Host ""
Write-Host "Log this in AGENT_LOG.md:"
Write-Host "  Action Item Created: [$($parsed.relativePath)] - $($parsed.title) (priority: $($parsed.priority), owner: $($parsed.owner), audit: $($parsed.audit.path))" -ForegroundColor Gray

return $parsed
