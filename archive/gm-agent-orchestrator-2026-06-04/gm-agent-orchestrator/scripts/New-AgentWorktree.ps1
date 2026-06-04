[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRepo,

    [Parameter(Mandatory = $true)]
    [string]$WorktreePath,

    [Parameter(Mandatory = $true)]
    [string]$Branch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git not found on PATH."
}

if (!(Test-Path $ProjectRepo)) {
    throw "Project repo does not exist: $ProjectRepo"
}

$ProjectRepo = (Resolve-Path $ProjectRepo).Path

if (Test-Path $WorktreePath) {
    Write-Host "Worktree exists: $WorktreePath"
    exit 0
}

Push-Location $ProjectRepo
try {
    git show-ref --verify --quiet "refs/heads/$Branch"
    $branchExists = ($LASTEXITCODE -eq 0)

    if ($branchExists) {
        git worktree add $WorktreePath $Branch
    }
    else {
        git worktree add -b $Branch $WorktreePath HEAD
    }

    if ($LASTEXITCODE -ne 0) {
        throw "git worktree add failed for $Branch"
    }
}
finally {
    Pop-Location
}
