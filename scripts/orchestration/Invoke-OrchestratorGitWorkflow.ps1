[CmdletBinding()]
param(
    [string]$Root = "",
    [Parameter(Mandatory = $true)]
    [ValidateSet("git_status", "worktree_risk", "create_branch", "stage_files", "commit_staged_changes", "push_current_branch", "open_pr")]
    [string]$Action,
    [string]$BranchName = "",
    [string]$PathsJson = "[]",
    [string]$Message = "",
    [string]$Remote = "origin",
    [string]$BaseBranch = "master",
    [string]$Title = "",
    [string]$Body = "",
    [switch]$DryRun
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

function Invoke-GitFixed {
    param([string[]]$Arguments)
    $output = @(& git -C $Root @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $text = (($output | ForEach-Object { $_.ToString() }) -join "`n").Trim()
    return [pscustomobject]@{ exitCode = $exitCode; output = $text; lines = @($output | ForEach-Object { $_.ToString() }) }
}

function Invoke-GhFixed {
    param([string[]]$Arguments)
    $output = @(& gh @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $text = (($output | ForEach-Object { $_.ToString() }) -join "`n").Trim()
    return [pscustomobject]@{ exitCode = $exitCode; output = $text; lines = @($output | ForEach-Object { $_.ToString() }) }
}

function Assert-ToolAvailable {
    param([string]$Name)
    if ($null -eq (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found on PATH: $Name"
    }
}

function Get-CurrentBranch {
    $branch = Invoke-GitFixed -Arguments @("branch", "--show-current")
    if ($branch.exitCode -ne 0) { throw "Unable to read current branch: $($branch.output)" }
    return $branch.output.Trim()
}

function Assert-NotProtectedBranch {
    param([string]$Branch)
    if ([string]::IsNullOrWhiteSpace($Branch)) { throw "Current branch is empty or detached; refusing write operation." }
    if ($Branch -in @("master", "main")) { throw "Refusing write operation on protected branch '$Branch'. Create a feature branch first." }
}

function Assert-ValidBranchName {
    param([string]$Branch)
    if ([string]::IsNullOrWhiteSpace($Branch)) { throw "Branch name is required." }
    if ($Branch -in @("master", "main")) { throw "Refusing to create protected branch '$Branch'." }
    if ($Branch -notmatch "^[A-Za-z0-9._/-]+$") { throw "Branch name contains unsupported characters: $Branch" }
    if ($Branch -match "\.\.|//|^/|/$") { throw "Branch name contains unsafe path segments: $Branch" }
}

function Get-RepoRelativePaths {
    if ([string]::IsNullOrWhiteSpace($PathsJson)) { return @() }
    $parsed = @($PathsJson | ConvertFrom-Json -ErrorAction Stop)
    $relativePaths = @()
    foreach ($item in $parsed) {
        $path = [string]$item
        if ([string]::IsNullOrWhiteSpace($path)) { continue }
        if ([System.IO.Path]::IsPathRooted($path)) { throw "Only repo-relative paths may be staged: $path" }
        if ($path -match "(^|[\\/])\.\.([\\/]|$)") { throw "Parent directory traversal is not allowed: $path" }
        if ($path -match "[*?]") { throw "Wildcards are not allowed in staged paths: $path" }
        $normalized = $path.Replace("\", "/").TrimStart("/")
        $full = [System.IO.Path]::GetFullPath((Join-Path $Root $normalized))
        $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
        if (-not $full.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Path resolves outside repository root: $path"
        }
        $relativePaths += $normalized
    }
    return @($relativePaths)
}

function Get-GitStatusSummary {
    $branch = Get-CurrentBranch
    $short = Invoke-GitFixed -Arguments @("status", "--short", "--branch")
    if ($short.exitCode -ne 0) { throw "git status failed: $($short.output)" }
    $porcelain = Invoke-GitFixed -Arguments @("status", "--porcelain")
    if ($porcelain.exitCode -ne 0) { throw "git porcelain status failed: $($porcelain.output)" }
    $staged = Invoke-GitFixed -Arguments @("diff", "--cached", "--name-only")
    if ($staged.exitCode -ne 0) { throw "git staged diff failed: $($staged.output)" }
    return [pscustomobject]@{
        branch = $branch
        isProtectedBranch = ($branch -in @("master", "main"))
        changedCount = @($porcelain.lines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
        stagedCount = @($staged.lines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
        status = $short.lines
        changedFiles = $porcelain.lines
        stagedFiles = $staged.lines
    }
}

$result = [ordered]@{
    ok = $true
    action = $Action
    root = $Root
    dryRun = [bool]$DryRun
    generatedAt = (Get-Date).ToString("o")
    command = @()
    status = $null
    output = ""
    error = ""
}

try {
    Assert-ToolAvailable -Name "git"

    switch ($Action) {
        "git_status" {
            $result.status = Get-GitStatusSummary
        }
        "worktree_risk" {
            $status = Get-GitStatusSummary
            $risk = "low"
            $warnings = @()
            if ($status.isProtectedBranch) { $risk = "high"; $warnings += "current branch is protected" }
            if ($status.changedCount -gt 0) { $risk = "medium"; $warnings += "worktree has uncommitted changes" }
            if ($status.stagedCount -gt 0) { $risk = "medium"; $warnings += "index has staged changes" }
            $result.status = [pscustomobject]@{ git = $status; risk = $risk; warnings = $warnings }
        }
        "create_branch" {
            Assert-ValidBranchName -Branch $BranchName
            $result.command = @("git", "-C", $Root, "checkout", "-b", $BranchName)
            if (-not $DryRun) {
                $created = Invoke-GitFixed -Arguments @("checkout", "-b", $BranchName)
                if ($created.exitCode -ne 0) { throw "git checkout -b failed: $($created.output)" }
                $result.output = $created.output
            }
            $result.status = Get-GitStatusSummary
        }
        "stage_files" {
            $branch = Get-CurrentBranch
            Assert-NotProtectedBranch -Branch $branch
            $paths = Get-RepoRelativePaths
            if (@($paths).Count -eq 0) { throw "At least one repo-relative path is required for stage_files." }
            $result.command = @("git", "-C", $Root, "add", "--") + @($paths)
            if (-not $DryRun) {
                $staged = Invoke-GitFixed -Arguments (@("add", "--") + @($paths))
                if ($staged.exitCode -ne 0) { throw "git add failed: $($staged.output)" }
                $result.output = $staged.output
            }
            $result.status = Get-GitStatusSummary
        }
        "commit_staged_changes" {
            $branch = Get-CurrentBranch
            Assert-NotProtectedBranch -Branch $branch
            if ([string]::IsNullOrWhiteSpace($Message)) { throw "Commit message is required." }
            $status = Get-GitStatusSummary
            if ($status.stagedCount -le 0) { throw "No staged files to commit." }
            $result.command = @("git", "-C", $Root, "commit", "-m", $Message)
            if (-not $DryRun) {
                $commit = Invoke-GitFixed -Arguments @("commit", "-m", $Message)
                if ($commit.exitCode -ne 0) { throw "git commit failed: $($commit.output)" }
                $result.output = $commit.output
            }
            $result.status = Get-GitStatusSummary
        }
        "push_current_branch" {
            $branch = Get-CurrentBranch
            Assert-NotProtectedBranch -Branch $branch
            if ([string]::IsNullOrWhiteSpace($Remote)) { throw "Remote is required." }
            if ($Remote -notmatch "^[A-Za-z0-9._-]+$") { throw "Remote contains unsupported characters: $Remote" }
            $result.command = @("git", "-C", $Root, "push", "-u", $Remote, $branch)
            if (-not $DryRun) {
                $push = Invoke-GitFixed -Arguments @("push", "-u", $Remote, $branch)
                if ($push.exitCode -ne 0) { throw "git push failed: $($push.output)" }
                $result.output = $push.output
            }
            $result.status = Get-GitStatusSummary
        }
        "open_pr" {
            Assert-ToolAvailable -Name "gh"
            $branch = Get-CurrentBranch
            Assert-NotProtectedBranch -Branch $branch
            if ([string]::IsNullOrWhiteSpace($Title)) { throw "PR title is required." }
            if ([string]::IsNullOrWhiteSpace($BaseBranch)) { $BaseBranch = "master" }
            if ($BaseBranch -notmatch "^[A-Za-z0-9._/-]+$") { throw "Base branch contains unsupported characters: $BaseBranch" }
            $result.command = @("gh", "pr", "create", "--base", $BaseBranch, "--head", $branch, "--title", $Title, "--body", $Body)
            if (-not $DryRun) {
                $createdPr = Invoke-GhFixed -Arguments @("pr", "create", "--base", $BaseBranch, "--head", $branch, "--title", $Title, "--body", $Body)
                if ($createdPr.exitCode -ne 0) { throw "gh pr create failed: $($createdPr.output)" }
                $result.output = $createdPr.output
            }
            $result.status = Get-GitStatusSummary
        }
    }
}
catch {
    $result.ok = $false
    $result.error = $_.Exception.Message
}

[Console]::Out.WriteLine(($result | ConvertTo-Json -Depth 80 -Compress))
