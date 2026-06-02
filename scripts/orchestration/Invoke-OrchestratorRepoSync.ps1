[CmdletBinding()]
param(
    [string]$Root = "",
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$Remote = "origin",
    [ValidatePattern("^[A-Za-z0-9._/-]+$")]
    [string]$Branch = "master",
    [ValidateSet("ff-only")]
    [string]$Mode = "ff-only",
    [switch]$AllowDirty,
    [switch]$DryRun,
    [switch]$PlanOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function Invoke-RepoGit {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    $output = @(& git -C $Root @Arguments 2>&1)
    return [pscustomobject]@{
        exitCode = $LASTEXITCODE
        output = @($output | ForEach-Object { [string]$_ })
    }
}

$result = [ordered]@{
    ok = $true
    generatedAt = (Get-Date).ToString("o")
    action = "sync_repository"
    root = $Root
    remote = $Remote
    branch = $Branch
    mode = $Mode
    dryRun = [bool]$DryRun
    planOnly = [bool]$PlanOnly
    allowDirty = [bool]$AllowDirty
    command = @()
    before = ""
    after = ""
    changed = $false
    dirty = $false
    stdout = @()
    error = ""
}

try {
    $inside = Invoke-RepoGit -Arguments @("rev-parse", "--is-inside-work-tree")
    if ($inside.exitCode -ne 0 -or (@($inside.output) -join "`n").Trim() -ne "true") {
        throw "Root is not inside a Git work tree: $Root"
    }

    $before = Invoke-RepoGit -Arguments @("rev-parse", "HEAD")
    if ($before.exitCode -ne 0) { throw "Could not read current HEAD." }
    $result.before = (@($before.output) | Select-Object -First 1).Trim()

    $status = Invoke-RepoGit -Arguments @("status", "--porcelain")
    if ($status.exitCode -ne 0) { throw "Could not read Git status." }
    $dirtyLines = @($status.output | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) })
    $result.dirty = ($dirtyLines.Count -gt 0)
    if ($result.dirty -and -not $AllowDirty) {
        throw "Refusing to sync with a dirty orchestrator checkout. Commit, stash, or rerun with -AllowDirty."
    }

    if ($DryRun) {
        $result.command = @("git", "-C", $Root, "fetch", "--dry-run", $Remote, $Branch)
    }
    else {
        $result.command = @("git", "-C", $Root, "pull", "--ff-only", $Remote, $Branch)
    }

    if ($PlanOnly) {
        $result.stdout = @("Plan only. No repository sync was executed.")
        $result.after = $result.before
    }
    else {
        $syncArgs = $(if ($DryRun) { @("fetch", "--dry-run", $Remote, $Branch) } else { @("pull", "--ff-only", $Remote, $Branch) })
        $sync = Invoke-RepoGit -Arguments $syncArgs
        $result.stdout = @($sync.output)
        if ($sync.exitCode -ne 0) { throw "Repository sync failed." }

        $after = Invoke-RepoGit -Arguments @("rev-parse", "HEAD")
        if ($after.exitCode -ne 0) { throw "Could not read updated HEAD." }
        $result.after = (@($after.output) | Select-Object -First 1).Trim()
    }

    $result.changed = ($result.before -ne $result.after)
}
catch {
    $result.ok = $false
    $result.error = $_.Exception.Message
    if ([string]::IsNullOrWhiteSpace([string]$result.after)) { $result.after = $result.before }
}

[pscustomobject]$result | ConvertTo-Json -Depth 20
