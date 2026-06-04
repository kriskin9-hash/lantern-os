<#
.SYNOPSIS
Create a new task by opening a GitHub issue with the 'orchestrator' label.

.DESCRIPTION
This script replaces manual PowerShell task creation with GitHub issues,
eliminating elevation prompts and creating a persistent audit trail.

.PARAMETER Title
Brief one-line task title (required).

.PARAMETER Description
Detailed task description (optional).

.PARAMETER Priority
Task priority: P0 (critical), P1 (high), P2 (normal), P3 (low).
Default: P1

.PARAMETER Owner
Target agent: claude, codex, gemini, gpt, or human.
Default: claude

.PARAMETER Labels
Additional GitHub labels to add (in addition to 'orchestrator').

.EXAMPLE
.\New-TaskViaGitHub.ps1 -Title "Implement dark mode" -Priority P1 -Owner codex

.EXAMPLE
$description = @"
- Add theme selector to UI
- Update CSS for dark colors
- Test in both modes
"@
.\New-TaskViaGitHub.ps1 -Title "Dark mode UI" -Description $description -Priority P1

.NOTES
Requires: GitHub CLI (gh) installed and authenticated
Cost: Zero PowerShell elevation prompts
Audit: All tasks visible in GitHub issues
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Title,

    [Parameter()]
    [string]$Description = "",

    [Parameter()]
    [ValidateSet("P0", "P1", "P2", "P3")]
    [string]$Priority = "P1",

    [Parameter()]
    [ValidateSet("claude", "codex", "gemini", "gpt", "human")]
    [string]$Owner = "claude",

    [Parameter()]
    [string[]]$Labels = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is not installed or not in PATH. Install from: https://cli.github.com/"
}

$createdAt = Get-Date -Format 'o'
$descriptionText = if ([string]::IsNullOrWhiteSpace($Description)) { "No description provided." } else { $Description }

$bodyLines = @(
    "## Task Metadata",
    "- **Priority:** $Priority",
    "- **Owner:** @$Owner",
    "- **Created:** $createdAt",
    "",
    "## Description",
    $descriptionText,
    "",
    "## Instructions",
    "This task will be picked up by the orchestrator and assigned to the designated agent.",
    "See docs/agent-contract.md for execution requirements.",
    "",
    "## Acceptance Criteria",
    "- [ ] Task understood",
    "- [ ] Work completed",
    "- [ ] Changes pushed and PR opened",
    "- [ ] Validation passed"
)
$body = $bodyLines -join [Environment]::NewLine

$allLabels = @("orchestrator", "priority/$Priority", "owner/$Owner") + $Labels

Write-Host "Creating task via GitHub..." -ForegroundColor Cyan
try {
    $result = & gh issue create `
        --title $Title `
        --body $body `
        --labels ($allLabels -join ",") `
        --repo "." `
        2>&1

    if ($LASTEXITCODE -eq 0) {
        $issueUrl = $result | Select-Object -Last 1
        Write-Host "Task created successfully" -ForegroundColor Green
        Write-Host "  URL: $issueUrl"
        Write-Host ""
        Write-Host "Task metadata:" -ForegroundColor Cyan
        Write-Host "  Priority: $Priority"
        Write-Host "  Owner: $Owner"
        Write-Host "  Labels: $($allLabels -join ', ')"
        return @{
            Success = $true
            Url = $issueUrl
            Title = $Title
        }
    }

    throw "GitHub issue creation failed: $result"
}
catch {
    Write-Error "Failed to create task: $($_.Exception.Message)"
    return @{
        Success = $false
        Error = $_.Exception.Message
    }
}
