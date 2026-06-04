[CmdletBinding()]
param(
    [string]$OrchestratorRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ReposConfigPath = "",
    [switch]$JsonOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (!(Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Invoke-CommandSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = ""
    )

    try {
        $oldLocation = Get-Location
        if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
            Push-Location $WorkingDirectory
        }

        try {
            $output = & $Executable @Arguments 2>&1
            $exitCode = $LASTEXITCODE
            if ($null -eq $exitCode) { $exitCode = 0 }

            return [pscustomobject]@{
                ok = ($exitCode -eq 0)
                exitCode = [int]$exitCode
                output = @($output | ForEach-Object { $_.ToString() })
            }
        }
        finally {
            if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
                Pop-Location
            }
        }
    }
    catch {
        return [pscustomobject]@{
            ok = $false
            exitCode = -1
            output = @($_.Exception.Message)
        }
    }
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (!(Test-Path -LiteralPath $Path)) {
        throw "Missing JSON file: $Path"
    }
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

$root = (Resolve-Path -LiteralPath $OrchestratorRoot).Path
if ([string]::IsNullOrWhiteSpace($ReposConfigPath)) {
    $localConfig = Join-Path $root "config\repos.json"
    $exampleConfig = Join-Path $root "config\repos.example.json"
    if (Test-Path -LiteralPath $localConfig) {
        $ReposConfigPath = $localConfig
    }
    else {
        $ReposConfigPath = $exampleConfig
    }
}

$statusDir = Join-Path $root "status"
$reportDir = Join-Path $root "reports\audit"
Ensure-Directory -Path $statusDir
Ensure-Directory -Path $reportDir

$reposConfig = Read-JsonFile -Path $ReposConfigPath
$repos = @($reposConfig.repos)

$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
$ghCmd = Get-Command gh -ErrorAction SilentlyContinue

$ghAuth = $null
if ($null -ne $ghCmd) {
    $ghAuth = Invoke-CommandSafe -Executable "gh" -Arguments @("auth", "status")
}

$repoResults = @()
foreach ($repo in $repos) {
    $localPath = [string]$repo.localPath
    $exists = Test-Path -LiteralPath $localPath
    $isGitRepo = $false
    $branch = ""
    $remote = @()
    $statusShort = @()
    $fetchDryRun = $null

    if ($exists -and $null -ne $gitCmd) {
        $gitDir = Join-Path $localPath ".git"
        $isGitRepo = Test-Path -LiteralPath $gitDir
        $branch = ((Invoke-CommandSafe -Executable "git" -Arguments @("branch", "--show-current") -WorkingDirectory $localPath).output -join "`n").Trim()
        $remote = (Invoke-CommandSafe -Executable "git" -Arguments @("remote", "-v") -WorkingDirectory $localPath).output
        $statusShort = (Invoke-CommandSafe -Executable "git" -Arguments @("status", "--short") -WorkingDirectory $localPath).output
        $fetchDryRun = Invoke-CommandSafe -Executable "git" -Arguments @("fetch", "--dry-run") -WorkingDirectory $localPath
    }

    $remoteMatches = $false
    if ($remote.Count -gt 0) {
        $remoteText = $remote -join "`n"
        $remoteMatches = $remoteText -match [regex]::Escape([string]$repo.fullName)
    }

    $repoResults += [pscustomobject]@{
        name = [string]$repo.name
        fullName = [string]$repo.fullName
        lane = [string]$repo.lane
        localPath = $localPath
        exists = $exists
        isGitRepo = $isGitRepo
        branch = $branch
        expectedDefaultBranch = [string]$repo.defaultBranch
        remoteMatches = $remoteMatches
        gitStatusShort = $statusShort
        dirty = ($statusShort.Count -gt 0)
        fetchDryRunOk = if ($null -ne $fetchDryRun) { $fetchDryRun.ok } else { $false }
        fetchDryRunOutput = if ($null -ne $fetchDryRun) { $fetchDryRun.output } else { @("not run") }
    }
}

$blockers = @()
if ($null -eq $claudeCmd) { $blockers += "Claude executable not found on PATH." }
if ($null -eq $gitCmd) { $blockers += "Git executable not found on PATH." }
if ($null -eq $ghCmd) { $blockers += "GitHub CLI executable not found on PATH; issue updates will be unavailable." }
elseif ($null -ne $ghAuth -and -not $ghAuth.ok) { $blockers += "GitHub CLI is present but not authenticated." }

foreach ($repoResult in $repoResults) {
    if (-not $repoResult.exists) { $blockers += "Missing repo path: $($repoResult.localPath)" }
    elseif (-not $repoResult.isGitRepo) { $blockers += "Path is not a git repo: $($repoResult.localPath)" }
    elseif (-not $repoResult.remoteMatches) { $blockers += "Remote does not match expected repo for $($repoResult.name)." }
    elseif (-not $repoResult.fetchDryRunOk) { $blockers += "Git fetch dry-run failed for $($repoResult.name)." }
}

$result = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    orchestratorRoot = $root
    reposConfigPath = (Resolve-Path -LiteralPath $ReposConfigPath).Path
    claudeOnPath = ($null -ne $claudeCmd)
    claudePath = if ($null -ne $claudeCmd) { $claudeCmd.Source } else { "" }
    gitOnPath = ($null -ne $gitCmd)
    ghOnPath = ($null -ne $ghCmd)
    ghAuthOk = if ($null -ne $ghAuth) { $ghAuth.ok } else { $false }
    repos = $repoResults
    blockers = $blockers
    ok = ($blockers.Count -eq 0)
}

$jsonPath = Join-Path $statusDir "claude-cross-repo-access.json"
$result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$reportPath = Join-Path $reportDir ((Get-Date -Format "yyyyMMdd-HHmmss") + "-claude-cross-repo-access.md")
$lines = @()
$lines += "# Claude Cross-Repo Access Audit"
$lines += ""
$lines += ("Generated: {0}" -f $result.generatedAt)
$lines += ("Root: {0}" -f $result.orchestratorRoot)
$lines += ("Config: {0}" -f $result.reposConfigPath)
$lines += ("Claude on PATH: {0}" -f $result.claudeOnPath)
$lines += ("Git on PATH: {0}" -f $result.gitOnPath)
$lines += ("gh on PATH: {0}" -f $result.ghOnPath)
$lines += ("gh auth ok: {0}" -f $result.ghAuthOk)
$lines += ("Overall ok: {0}" -f $result.ok)
$lines += ""
$lines += "## Repos"
$lines += ""
foreach ($repoResult in $repoResults) {
    $lines += ("### {0}" -f $repoResult.fullName)
    $lines += ("- Lane: {0}" -f $repoResult.lane)
    $lines += ("- Path: {0}" -f $repoResult.localPath)
    $lines += ("- Exists: {0}" -f $repoResult.exists)
    $lines += ("- Git repo: {0}" -f $repoResult.isGitRepo)
    $lines += ("- Branch: {0}" -f $repoResult.branch)
    $lines += ("- Remote matches: {0}" -f $repoResult.remoteMatches)
    $lines += ("- Dirty: {0}" -f $repoResult.dirty)
    $lines += ("- Fetch dry-run ok: {0}" -f $repoResult.fetchDryRunOk)
    $lines += ""
}
$lines += "## Blockers"
$lines += ""
if ($blockers.Count -eq 0) {
    $lines += "No blockers detected."
}
else {
    foreach ($blocker in $blockers) { $lines += ("- {0}" -f $blocker) }
}
$lines | Set-Content -LiteralPath $reportPath -Encoding UTF8

if ($JsonOnly) {
    $result | ConvertTo-Json -Depth 20
}
else {
    Write-Host "Claude cross-repo access audit complete." -ForegroundColor Green
    Write-Host "JSON: $jsonPath"
    Write-Host "Report: $reportPath"
    if ($blockers.Count -gt 0) {
        Write-Host "Blockers detected: $($blockers.Count)" -ForegroundColor Yellow
    }
    else {
        Write-Host "No blockers detected." -ForegroundColor Green
    }
}
