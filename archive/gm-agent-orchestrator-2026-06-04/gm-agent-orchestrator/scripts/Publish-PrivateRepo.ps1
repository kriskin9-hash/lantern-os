[CmdletBinding()]
param(
    [string]$RepoFullName = "alex-place/gm-agent-orchestrator",
    [switch]$SkipPush
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path

function Invoke-CheckedGit {
    param([string[]]$Args)

    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Test-GhRepoExists {
    param([string]$FullName)

    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $null = gh repo view $FullName 2>$null
        return ($LASTEXITCODE -eq 0)
    }
    finally {
        $ErrorActionPreference = $oldPreference
    }
}

function Ensure-OriginRemote {
    param([string]$FullName)

    $originUrl = "https://github.com/$FullName.git"

    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $null = git remote get-url origin 2>$null
        $hasOrigin = ($LASTEXITCODE -eq 0)
    }
    finally {
        $ErrorActionPreference = $oldPreference
    }

    if ($hasOrigin) {
        Invoke-CheckedGit -Args @("remote", "set-url", "origin", $originUrl)
    }
    else {
        Invoke-CheckedGit -Args @("remote", "add", "origin", $originUrl)
    }
}

if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git not found on PATH."
}

if (!(Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) not found on PATH. Install it or create the private repo manually."
}

Push-Location $root
try {
    if (!(Test-Path ".git")) {
        Invoke-CheckedGit -Args @("init")
    }

    Invoke-CheckedGit -Args @("add", ".")

    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        Invoke-CheckedGit -Args @("commit", "-m", "chore: scaffold gm-agent-orchestrator")
    }
    else {
        Write-Host "No staged changes to commit."
    }

    if ($SkipPush) {
        Write-Host "SkipPush set. Local repo initialized only."
        return
    }

    if (Test-GhRepoExists -FullName $RepoFullName) {
        Write-Host "GitHub repo already exists: $RepoFullName"
        Ensure-OriginRemote -FullName $RepoFullName
        Invoke-CheckedGit -Args @("push", "-u", "origin", "HEAD")
    }
    else {
        Write-Host "GitHub repo not found. Creating private repo: $RepoFullName"
        gh repo create $RepoFullName --private --source . --remote origin --push
        if ($LASTEXITCODE -ne 0) {
            throw "gh repo create failed with exit code $LASTEXITCODE"
        }
    }

    Write-Host "Published private repo: $RepoFullName"
}
finally {
    Pop-Location
}
