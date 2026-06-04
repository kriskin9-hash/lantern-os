[CmdletBinding()]
param(
    [string]$Root = "",
    [int]$IssueLimit = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    return Get-Content -Path $Path -Raw | ConvertFrom-Json
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Invoke-GhJson {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    try {
        $output = & gh @Arguments 2>&1
        $exit = $LASTEXITCODE
        if ($null -eq $exit) { $exit = 0 }

        return [pscustomobject]@{
            ok = ($exit -eq 0)
            exitCode = [int]$exit
            text = (@($output) | ForEach-Object { $_.ToString() }) -join "`n"
        }
    }
    catch {
        return [pscustomobject]@{
            ok = $false
            exitCode = -1
            text = $_.Exception.Message
        }
    }
}

function Get-RepoPriority {
    param([Parameter(Mandatory = $true)][object]$Repo)

    $fullName = [string]$Repo.fullName
    $trackerIssue = [int]$Repo.priorityTrackerIssue
    $repoName = [string]$Repo.name
    $lane = [string]$Repo.lane

    $tracker = $null
    $openIssues = @()
    $blockers = @()

    $trackerResult = Invoke-GhJson -Arguments @("issue", "view", $trackerIssue.ToString(), "--repo", $fullName, "--json", "number,title,url,state,updatedAt,labels")
    if ($trackerResult.ok) {
        try { $tracker = $trackerResult.text | ConvertFrom-Json }
        catch { $blockers += "Could not parse tracker issue #$trackerIssue for $fullName." }
    }
    else {
        $blockers += "Could not read tracker issue #$trackerIssue for $fullName. $($trackerResult.text)"
    }

    $listResult = Invoke-GhJson -Arguments @("issue", "list", "--repo", $fullName, "--state", "open", "--limit", $IssueLimit.ToString(), "--json", "number,title,url,updatedAt,labels")
    if ($listResult.ok) {
        try { $openIssues = @($listResult.text | ConvertFrom-Json) }
        catch { $blockers += "Could not parse open issue list for $fullName." }
    }
    else {
        $blockers += "Could not list open issues for $fullName. $($listResult.text)"
    }

    $p0Issues = @($openIssues | Where-Object {
        $labels = @($_.labels | ForEach-Object { $_.name })
        ($labels -contains "P0") -or ($_.title -match "(?i)\bP0\b|BLOCKER")
    })

    $topIssue = $null
    if ($p0Issues.Count -gt 0) {
        $topIssue = $p0Issues | Sort-Object updatedAt -Descending | Select-Object -First 1
    }
    elseif ($openIssues.Count -gt 0) {
        $topIssue = $openIssues | Sort-Object updatedAt -Descending | Select-Object -First 1
    }

    $recommendedAgent = "ChatGPT"
    $recommendedAction = "Review tracker and prepare a compact task packet."
    if ($lane -eq "orchestrator-infrastructure") {
        $recommendedAgent = "ChatGPT/Codex"
        $recommendedAction = "Fix dashboard/queue/priority reporting before expanding agents."
    }
    elseif ($lane -eq "game-early-access") {
        $recommendedAgent = "Codex"
        $recommendedAction = "Run the next compact Early Access test/tooling task from the tracker."
    }
    elseif ($lane -eq "room-editor-tooling") {
        $recommendedAgent = "Codex/Claude review"
        $recommendedAction = "Fix room preview parity or produce a compact blocker report."
    }

    if ($null -ne $topIssue) {
        $recommendedAction = "Work issue #$($topIssue.number): $($topIssue.title)"
    }

    return [pscustomobject]@{
        name = $repoName
        fullName = $fullName
        lane = $lane
        localPath = [string]$Repo.localPath
        priorityTrackerIssue = $trackerIssue
        tracker = $tracker
        counts = [pscustomobject]@{
            open = @($openIssues).Count
            p0 = @($p0Issues).Count
            blockers = @($blockers).Count
        }
        topIssue = $topIssue
        recommendedAgent = $recommendedAgent
        recommendedAction = $recommendedAction
        blockers = $blockers
    }
}

$configPath = Join-Path $Root "config\repos.json"
if (-not (Test-Path -LiteralPath $configPath)) {
    $configPath = Join-Path $Root "config\repos.example.json"
}

$statusDir = Join-Path $Root "status"
$reportDir = Join-Path $Root "reports\priority"
Ensure-Directory -Path $statusDir
Ensure-Directory -Path $reportDir

$ghFound = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)
$config = Read-JsonFile -Path $configPath
$repos = @($config.repos)

$repoResults = @()
$globalBlockers = @()
if (-not $ghFound) {
    $globalBlockers += "GitHub CLI gh was not found on PATH."
}
else {
    foreach ($repo in $repos) {
        $repoResults += Get-RepoPriority -Repo $repo
    }
}

$recommendedRepo = $null
if ($repoResults.Count -gt 0) {
    $recommendedRepo = $repoResults |
        Sort-Object @{ Expression = { if ($_.lane -eq "orchestrator-infrastructure") { 0 } else { 1 } } }, @{ Expression = { $_.counts.blockers }; Descending = $true }, @{ Expression = { $_.counts.p0 }; Descending = $true } |
        Select-Object -First 1
}

$nextAction = "Run this report again after fixing GitHub CLI access."
if ($recommendedRepo) {
    $nextAction = "$($recommendedRepo.fullName): $($recommendedRepo.recommendedAction)"
}

$result = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    sourceConfig = $configPath.Replace($Root, "").TrimStart("\")
    ghFound = $ghFound
    state = $(if ($globalBlockers.Count -gt 0) { "blocked" } else { "ready" })
    nextAction = [pscustomobject]@{
        action = $nextAction
        owner = $(if ($recommendedRepo) { $recommendedRepo.recommendedAgent } else { "Alex" })
        when = "now"
        blockedBy = $(if ($globalBlockers.Count -gt 0) { "missing gh" } else { "none" })
    }
    repos = $repoResults
    blockers = $globalBlockers
    honestyCheck = [pscustomobject]@{
        verified = @("Generated from configured repo list and GitHub CLI issue metadata.")
        assumed = @("Issue labels and tracker contents are sufficient for a first-pass priority order.")
    }
}

$statusPath = Join-Path $statusDir "priority.json"
$result | ConvertTo-Json -Depth 20 | Set-Content -Path $statusPath -Encoding UTF8

$reportPath = Join-Path $reportDir "latest.md"
$lines = @()
$lines += "# Cross-Repo Priority Report"
$lines += ""
$lines += "Generated: $($result.generatedAt)"
$lines += "State: $($result.state)"
$lines += ""
$lines += "## Next action"
$lines += ""
$lines += "- Action: $($result.nextAction.action)"
$lines += "- Owner: $($result.nextAction.owner)"
$lines += "- When: $($result.nextAction.when)"
$lines += "- Blocked by: $($result.nextAction.blockedBy)"
$lines += ""
$lines += "## Repos"
$lines += ""
foreach ($repo in $repoResults) {
    $lines += "### $($repo.fullName)"
    $lines += ""
    $lines += "- Lane: $($repo.lane)"
    $lines += "- Open issues checked: $($repo.counts.open)"
    $lines += "- P0/blocker count: $($repo.counts.p0)"
    $lines += "- Recommended agent: $($repo.recommendedAgent)"
    $lines += "- Recommended action: $($repo.recommendedAction)"
    if ($repo.topIssue) { $lines += "- Top issue: #$($repo.topIssue.number) $($repo.topIssue.title)" }
    if ($repo.blockers.Count -gt 0) {
        $lines += "- Blockers:"
        foreach ($blocker in $repo.blockers) { $lines += "  - $blocker" }
    }
    $lines += ""
}
if ($globalBlockers.Count -gt 0) {
    $lines += "## Global blockers"
    $lines += ""
    foreach ($blocker in $globalBlockers) { $lines += "- $blocker" }
    $lines += ""
}
$lines += "## Honesty check"
$lines += ""
$lines += "Verified: generated from GitHub CLI issue metadata."
$lines += "Assumed: labels/tracker issues are enough for first-pass routing; local dashboard state may be fresher."

$lines | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "Wrote $statusPath"
Write-Host "Wrote $reportPath"
Write-Host "Next: $($result.nextAction.action)"
