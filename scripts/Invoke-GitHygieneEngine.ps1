param(
    [string[]]$RepoPaths = @(
        "D:\tmp\lantern-os",
        "C:\tmp\human-flourishing-frameworks-scan",
        "C:\Users\alexp\Documents\gm-agent-orchestrator"
    ),
    [string]$OutputPath = "D:\tmp\lantern-os\data\automation\git-hygiene-results.json",
    [int]$AutoCommitThreshold = 10,
    [switch]$DryRun,
    [switch]$RunOnce,
    [switch]$EnableAutoCommit
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
    
    $logPath = "D:\tmp\lantern-os\data\automation\git-hygiene.log"
    Add-Content -Path $logPath -Value "[$timestamp] [$Level] $Message" -ErrorAction SilentlyContinue
}

function Test-GitRepo {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        return @{ valid = $false; reason = "path-not-found" }
    }
    
    Push-Location $Path -ErrorAction SilentlyContinue
    try {
        git rev-parse --git-dir 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $repoName = Split-Path $Path -Leaf
            return @{ valid = $true; name = $repoName }
        }
        return @{ valid = $false; reason = "not-git-repo" }
    }
    finally {
        Pop-Location -ErrorAction SilentlyContinue
    }
}

function Get-RepoStatus {
    param([string]$Path, [string]$Name)
    
    Push-Location $Path
    try {
        # Get git status
        $statusOutput = git status --porcelain 2>$null
        $untracked = @()
        $modified = @()
        $staged = @()
        
        foreach ($line in $statusOutput) {
            if ($line -match '^\?\?\s+(.+)$') {
                $untracked += $Matches[1]
            }
            elseif ($line -match '^\s?M\s+(.+)$') {
                $modified += $Matches[1]
            }
            elseif ($line -match '^[AMRD].\s+(.+)$') {
                $staged += $Matches[1]
            }
        }
        
        # Get current branch
        $branch = git branch --show-current 2>$null
        
        # Get last commit info
        $lastCommit = git log -1 --format="%h|%s|%ci" 2>$null
        $lastCommitParts = $lastCommit -split '\|'
        
        # Check for unpushed commits
        $unpushed = 0
        try {
            $null = git rev-parse "origin/$branch" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $unpushed = git log "origin/$branch..HEAD" --oneline 2>$null | Measure-Object | Select-Object -ExpandProperty Count
            }
        }
        catch {
            $unpushed = 0
        }
        
        return @{
            name = $Name
            path = $Path
            branch = $branch
            clean = ($untracked.Count -eq 0 -and $modified.Count -eq 0)
            untrackedCount = $untracked.Count
            modifiedCount = $modified.Count
            stagedCount = $staged.Count
            totalChanges = $untracked.Count + $modified.Count + $staged.Count
            unpushedCommits = $unpushed
            lastCommitHash = if ($lastCommitParts.Count -gt 0) { $lastCommitParts[0] } else { "unknown" }
            lastCommitMessage = if ($lastCommitParts.Count -gt 1) { $lastCommitParts[1] } else { "unknown" }
            lastCommitDate = if ($lastCommitParts.Count -gt 2) { $lastCommitParts[2] } else { "unknown" }
            untrackedFiles = $untracked
            modifiedFiles = $modified
            stagedFiles = $staged
        }
    }
    finally {
        Pop-Location
    }
}

function Test-CommitWorthy {
    param([object]$Status, [int]$Threshold)
    
    # Don't auto-commit if:
    # - Too many changes (potential bulk issue)
    # - Has untracked files (needs review)
    # - Already has staged files
    # - Unpushed commits exist (previous work not synced)
    
    $reasons = @()
    
    if ($Status.totalChanges -gt $Threshold) {
        $reasons += "too-many-changes"
    }
    
    if ($Status.untrackedCount -gt 0) {
        $reasons += "has-untracked"
    }
    
    if ($Status.stagedCount -gt 0) {
        $reasons += "already-staged"
    }
    
    if ($Status.unpushedCommits -gt 0) {
        $reasons += "unpushed-commits"
    }
    
    return @{
        canAutoCommit = $reasons.Count -eq 0 -and $Status.modifiedCount -gt 0
        reasons = $reasons
        safeToCommit = ($Status.totalChanges -le 5 -and $Status.untrackedCount -eq 0)
    }
}

function Invoke-SafeCommit {
    param([string]$Path, [string]$Name, [switch]$DryRun)
    
    Push-Location $Path
    try {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
        $message = "Auto-commit: hygiene sync $timestamp [fleet-engine]"
        
        if ($DryRun) {
            Write-Log "DRY RUN: Would commit in $Name with message: $message"
            return @{ success = $true; dryRun = $true; message = $message }
        }
        
        git add -A 2>$null
        git commit -m $message 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Successfully committed in $Name"
            return @{ success = $true; message = $message }
        }
        else {
            Write-Log "Commit failed in $Name" "ERROR"
            return @{ success = $false; error = "commit-failed" }
        }
    }
    finally {
        Pop-Location
    }
}

function Get-HygieneRecommendations {
    param([array]$Statuses)
    
    $recommendations = @()
    $totalChanges = 0
    foreach ($s in $Statuses) {
        if ($s -and $s.ContainsKey('totalChanges')) {
            $totalChanges += $s.totalChanges
        }
    }
    
    if ($totalChanges -eq 0) {
        $recommendations += @{
            priority = "low"
            action = "all-clean"
            description = "All repositories are clean"
        }
    }
    else {
        $dirtyRepos = $Statuses | Where-Object { -not $_.clean }
        
        foreach ($repo in $dirtyRepos) {
            if ($repo.untrackedCount -gt 10) {
                $recommendations += @{
                    priority = "high"
                    action = "review-untracked"
                    repo = $repo.name
                    description = "Repository has $($repo.untrackedCount) untracked files requiring operator review"
                }
            }
            
            if ($repo.modifiedCount -gt 0 -and $repo.untrackedCount -eq 0 -and $repo.totalChanges -le 5) {
                $recommendations += @{
                    priority = "medium"
                    action = "safe-to-commit"
                    repo = $repo.name
                    description = "Repository has $($repo.modifiedCount) modified files, safe for auto-commit"
                }
            }
            
            if ($repo.unpushedCommits -gt 5) {
                $recommendations += @{
                    priority = "high"
                    action = "push-required"
                    repo = $repo.name
                    description = "Repository has $($repo.unpushedCommits) unpushed commits"
                }
            }
        }
    }
    
    return $recommendations
}

function Invoke-GitHygieneEngine {
    Write-Log "=== Git Hygiene Engine Started ==="
    
    if ($DryRun) {
        Write-Log "DRY RUN MODE"
    }
    
    $repoStatuses = @()
    $actions = @()
    
    foreach ($repoPath in $RepoPaths) {
        $repoTest = Test-GitRepo -Path $repoPath
        
        if (-not $repoTest.valid) {
            Write-Log "Skipping invalid repo: $repoPath ($($repoTest.reason))" "WARN"
            continue
        }
        
        $status = Get-RepoStatus -Path $repoPath -Name $repoTest.name
        $repoStatuses += $status
        
        Write-Log "$($status.name): $($status.totalChanges) changes, clean=$($status.clean)"
        
        if (-not $status.clean -and $EnableAutoCommit) {
            $commitTest = Test-CommitWorthy -Status $status -Threshold $AutoCommitThreshold
            
            if ($commitTest.canAutoCommit) {
                $commitResult = Invoke-SafeCommit -Path $repoPath -Name $status.name -DryRun:$DryRun
                $actions += @{
                    repo = $status.name
                    action = "auto-commit"
                    result = $commitResult
                }
            }
            else {
                Write-Log "Cannot auto-commit $($status.name): $($commitTest.reasons -join ', ')"
                $actions += @{
                    repo = $status.name
                    action = "skipped"
                    reasons = $commitTest.reasons
                }
            }
        }
    }
    
    $recommendations = Get-HygieneRecommendations -Statuses $repoStatuses
    
    # Calculate metrics before hashtable
    $totalChanges = 0
    foreach ($s in $repoStatuses) {
        if ($s -and $s.ContainsKey('totalChanges')) {
            $totalChanges += $s.totalChanges
        }
    }
    $cleanRepos = ($repoStatuses | Where-Object { $_.clean -eq $true }).Count
    $dirtyRepos = $repoStatuses.Count - $cleanRepos
    
    $results = @{
        generatedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        engine = "Git Hygiene Engine v1.0"
        mode = if ($DryRun) { "dry-run" } else { "live" }
        reposChecked = $repoStatuses.Count
        totalChanges = $totalChanges
        cleanRepos = $cleanRepos
        dirtyRepos = $dirtyRepos
        repoStatuses = $repoStatuses
        actions = $actions
        recommendations = $recommendations
        autoCommitEnabled = $EnableAutoCommit
        nextAction = if ($dirtyRepos -gt 0) { 
            "Review dirty repos and clear uncommitted changes" 
        } else { 
            "All repositories clean - no action required" 
        }
    }
    
    if (-not $DryRun) {
        $outputDir = Split-Path $OutputPath -Parent
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }
        
        $results | ConvertTo-Json -Depth 10 | Set-Content $OutputPath
        Write-Log "Results written to $OutputPath"
    }
    
    Write-Log "=== Summary ==="
    Write-Log "Repos: $($results.reposChecked), Clean: $($results.cleanRepos), Dirty: $($results.dirtyRepos)"
    Write-Log "Total changes: $($results.totalChanges)"
    Write-Log "Next: $($results.nextAction)"
    
    return $results
}

# Main
if ($RunOnce -or -not $RunOnce) {
    Invoke-GitHygieneEngine
}
