param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$statusFile = Join-Path $Root "data/automation/health-status.json"
$statusDir  = Split-Path $statusFile -Parent
if (-not (Test-Path $statusDir)) { New-Item -ItemType Directory -Path $statusDir -Force | Out-Null }

# Git dirty check
Push-Location $Root -ErrorAction SilentlyContinue
try {
    $gitStatus = git status --porcelain 2>$null
    $gitDirty  = ($gitStatus -and $gitStatus.Trim().Length -gt 0)
    $gitBranch = (git rev-parse --abbrev-ref HEAD 2>$null)
    $gitCommit = (git rev-parse --short HEAD 2>$null)
} catch {
    $gitDirty  = $null
    $gitBranch = $null
    $gitCommit = $null
} finally {
    Pop-Location -ErrorAction SilentlyContinue
}

# Disk space — use Get-PSDrive (no WMI dependency)
try {
    $drive = Get-PSDrive -Name (Split-Path $Root -Qualifier).TrimEnd(':') -ErrorAction Stop
    $freeGB = [Math]::Round($drive.Free / 1GB, 2)
    $usedGB = [Math]::Round($drive.Used / 1GB, 2)
} catch {
    $freeGB = $null
    $usedGB = $null
}

# Network check (non-blocking, short timeout)
try {
    $networkOk = Test-Connection github.com -Count 1 -Quiet -ErrorAction SilentlyContinue
} catch {
    $networkOk = $false
}

# Required scripts present
$requiredScripts = @(
    "scripts/Invoke-LanternConvergenceLoop.ps1",
    "scripts/Invoke-LoopReceipt.ps1",
    "scripts/Update-ArcReactorStatus.ps1",
    "scripts/Sync-RagAndPdf.ps1",
    "scripts/Invoke-AssetDiscoveryEngine.ps1",
    "scripts/Invoke-StyleConvergence.ps1"
)
$missingScripts = @($requiredScripts | Where-Object { -not (Test-Path (Join-Path $Root $_)) })

$health = [ordered]@{
    generatedAt    = (Get-Date).ToString("o")
    evidenceClass  = "health_check"
    root           = $Root
    git = [ordered]@{
        dirty  = $gitDirty
        branch = $gitBranch
        commit = $gitCommit
    }
    disk = [ordered]@{
        freeGB = $freeGB
        usedGB = $usedGB
        lowDisk = ($freeGB -ne $null -and $freeGB -lt 5)
    }
    network = [ordered]@{
        githubReachable = $networkOk
    }
    scripts = [ordered]@{
        required = $requiredScripts.Count
        missing  = $missingScripts.Count
        missingList = @($missingScripts)
    }
    status = $(
        if ($missingScripts.Count -gt 0) { "warn" }
        elseif ($freeGB -ne $null -and $freeGB -lt 5) { "warn" }
        else { "ok" }
    )
}

Write-Host "=== Health Check ===" -ForegroundColor Cyan
Write-Host "Git        : branch=$($health.git.branch)  dirty=$($health.git.dirty)  commit=$($health.git.commit)"
Write-Host "Disk       : free=$($health.disk.freeGB) GB  used=$($health.disk.usedGB) GB" -ForegroundColor $(if ($health.disk.lowDisk) { 'Red' } else { 'Green' })
Write-Host "Network    : github=$($health.network.githubReachable)"
Write-Host "Scripts    : $($health.scripts.required - $health.scripts.missing)/$($health.scripts.required) present" -ForegroundColor $(if ($health.scripts.missing -gt 0) { 'Yellow' } else { 'Green' })
foreach ($s in $missingScripts) { Write-Host "  MISSING: $s" -ForegroundColor Red }
Write-Host "Status     : $($health.status)" -ForegroundColor $(if ($health.status -eq 'ok') { 'Green' } else { 'Yellow' })

if (-not $DryRun) {
    $health | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statusFile -Encoding UTF8
}

exit $(if ($health.status -eq 'ok') { 0 } else { 1 })
