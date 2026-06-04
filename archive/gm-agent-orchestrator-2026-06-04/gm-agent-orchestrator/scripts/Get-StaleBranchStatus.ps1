[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$BaseBranch = "master",
    [int]$StaleDays = 2,
    [switch]$IncludeMerged,
    [switch]$NoFetch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

function Invoke-GitLines {
    param([string[]]$Arguments)

    $output = @(& git -C $Root @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $exitCode`: $($output -join "`n")"
    }

    return @($output | ForEach-Object { [string]$_ })
}

function Invoke-GitText {
    param([string[]]$Arguments)

    return ((Invoke-GitLines -Arguments $Arguments) -join "`n").Trim()
}

function Test-GitRef {
    param([string]$Ref)

    $output = @(& git -C $Root rev-parse --verify --quiet "$Ref^{commit}" 2>&1)
    return ($LASTEXITCODE -eq 0)
}

function Get-BaseRef {
    if (Test-GitRef -Ref $BaseBranch) { return $BaseBranch }
    $remoteBase = "origin/$BaseBranch"
    if (Test-GitRef -Ref $remoteBase) { return $remoteBase }
    throw "Base branch ref not found: $BaseBranch or $remoteBase"
}

function Get-AgentFromBranch {
    param([string]$BranchName)

    if ($BranchName -match "^(?<agent>[^/]+)/") { return $Matches.agent }
    if ($BranchName -match "^(?<agent>chatgpt|codex|claude|gemini|aider)[-_]") { return $Matches.agent }
    if ($BranchName -match "(?<agent>chatgpt|codex|claude|gemini|aider)") { return $Matches.agent }
    return "unknown"
}

function Get-ExceptionFromRefText {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
    if ($Text -notmatch "EXCEPTION TYPE:\s*(?<type>[^`r`n]+)") { return $null }

    return [pscustomobject]@{
        type = $Matches.type.Trim()
        ownerNextActor = $(if ($Text -match "OWNER / NEXT ACTOR:\s*(?<value>[^`r`n]+)") { $Matches.value.Trim() } else { "" })
        why = $(if ($Text -match "WHY IT CANNOT BE COMPLETED NOW:\s*(?<value>[^`r`n]+)") { $Matches.value.Trim() } else { "" })
        safeNextAction = $(if ($Text -match "SAFE NEXT ACTION:\s*(?<value>[^`r`n]+)") { $Matches.value.Trim() } else { "" })
        recheckTrigger = $(if ($Text -match "RECHECK TRIGGER:\s*(?<value>[^`r`n]+)") { $Matches.value.Trim() } else { "" })
    }
}

function Get-BranchStatus {
    param(
        [string]$BranchName,
        [string]$RefName,
        [string]$BaseRef,
        [bool]$RemoteOnly
    )

    $lastCommitIso = Invoke-GitText -Arguments @("log", "-1", "--format=%cI", $RefName)
    $lastCommitSubject = Invoke-GitText -Arguments @("log", "-1", "--format=%s", $RefName)
    $lastCommitSha = Invoke-GitText -Arguments @("rev-parse", $RefName)
    $aheadBehindText = Invoke-GitText -Arguments @("rev-list", "--left-right", "--count", "$BaseRef...$RefName")
    $aheadBehind = @($aheadBehindText -split "\s+")
    $behindBase = [int]$aheadBehind[0]
    $aheadBase = [int]$aheadBehind[1]
    $mergedToBase = $false
    if ($aheadBase -eq 0) { $mergedToBase = $true }

    $ageDays = [Math]::Round(((Get-Date) - ([datetime]$lastCommitIso)).TotalDays, 2)
    $agent = Get-AgentFromBranch -BranchName $BranchName
    $staleReasons = @()
    if ($ageDays -ge $StaleDays) { $staleReasons += "last_progress_${StaleDays}_or_more_days_old" }
    if ($aheadBase -eq 0 -and -not $IncludeMerged) { $staleReasons += "already_merged_or_no_unique_commits" }
    if ($BranchName -match "(?i)(stale|abandon|superseded)") { $staleReasons += "branch_name_marks_stale" }

    $exception = Get-ExceptionFromRefText -Text $lastCommitSubject
    $hasException = $null -ne $exception

    return [pscustomobject]@{
        branch = $BranchName
        ref = $RefName
        remoteOnly = [bool]$RemoteOnly
        agent = $agent
        lastCommitSha = $lastCommitSha
        lastCommitAt = $lastCommitIso
        ageDays = $ageDays
        aheadBase = $aheadBase
        behindBase = $behindBase
        mergedToBase = [bool]$mergedToBase
        stale = [bool]($staleReasons.Count -gt 0 -and -not $hasException)
        staleReasons = $staleReasons
        exception = $exception
        nextAction = $(if ($hasException) { "Recheck recorded exception before assigning unrelated work to $agent." } elseif ($staleReasons.Count -gt 0) { "Open, update, merge, close, or record an exception for this branch before unrelated work continues." } else { "No stale branch action required." })
    }
}

if (-not (Test-Path (Join-Path $Root ".git"))) {
    throw "Root is not a git repository: $Root"
}

if (-not $NoFetch) {
    try { Invoke-GitLines -Arguments @("fetch", "--prune", "origin") | Out-Null }
    catch { Write-Warning $_.Exception.Message }
}

$currentBranch = Invoke-GitText -Arguments @("rev-parse", "--abbrev-ref", "HEAD")
$baseRef = Get-BaseRef

$localBranches = @(Invoke-GitLines -Arguments @("for-each-ref", "--format=%(refname:short)", "refs/heads") |
    Where-Object { $_ -and $_ -ne $BaseBranch } |
    Sort-Object -Unique)

$remoteBranches = @(Invoke-GitLines -Arguments @("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin") |
    Where-Object { $_ -and $_ -notmatch "^origin/HEAD$" -and $_ -ne "origin/$BaseBranch" } |
    Sort-Object -Unique)

$entriesByBranch = @{}
foreach ($branch in $localBranches) {
    $entriesByBranch[$branch] = [pscustomobject]@{ branch = $branch; ref = $branch; remoteOnly = $false }
}

foreach ($remoteRef in $remoteBranches) {
    $branch = $remoteRef -replace "^origin/", ""
    if (-not $entriesByBranch.ContainsKey($branch)) {
        $entriesByBranch[$branch] = [pscustomobject]@{ branch = $branch; ref = $remoteRef; remoteOnly = $true }
    }
}

$branchEntries = @($entriesByBranch.Values | Sort-Object branch)
$branches = @()
foreach ($entry in $branchEntries) {
    try {
        $status = Get-BranchStatus -BranchName $entry.branch -RefName $entry.ref -BaseRef $baseRef -RemoteOnly $entry.remoteOnly
        if ($IncludeMerged -or -not $status.mergedToBase) { $branches += $status }
    }
    catch {
        $branches += [pscustomobject]@{
            branch = $entry.branch
            ref = $entry.ref
            remoteOnly = [bool]$entry.remoteOnly
            agent = Get-AgentFromBranch -BranchName $entry.branch
            stale = $true
            staleReasons = @("status_check_failed")
            error = $_.Exception.Message
            nextAction = "Inspect this branch manually; stale discovery could not read it."
        }
    }
}

$staleBranches = @($branches | Where-Object { $_.stale })
$exceptions = @($branches | Where-Object { $null -ne $_.exception })
$byAgent = @($branches | Group-Object agent | ForEach-Object {
    [pscustomobject]@{
        agent = $_.Name
        branchCount = $_.Count
        staleCount = @($_.Group | Where-Object { $_.stale }).Count
        exceptionCount = @($_.Group | Where-Object { $null -ne $_.exception }).Count
        branches = @($_.Group | ForEach-Object { $_.branch })
    }
})

[pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    root = $Root
    baseBranch = $BaseBranch
    baseRef = $baseRef
    currentBranch = $currentBranch
    staleDays = $StaleDays
    branchCount = $branches.Count
    staleCount = $staleBranches.Count
    exceptionCount = $exceptions.Count
    branches = $branches
    byAgent = $byAgent
    nextAction = $(if ($staleBranches.Count -gt 0) { "Cull stale branches or record exceptions before unrelated non-P0 work continues." } else { "No stale branches detected by local git state." })
} | ConvertTo-Json -Depth 20
