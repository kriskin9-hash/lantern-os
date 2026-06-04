[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $Root "scripts\Get-StaleBranchStatus.ps1"
if (-not (Test-Path $script)) {
    throw "Stale branch status script was not found: $script"
}

function Invoke-Git {
    param(
        [string]$Repo,
        [string[]]$Arguments
    )

    $output = @(& git -C $Repo @Arguments 2>$null)
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed: $($output -join "`n")"
    }
    return $output
}

$repo = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-stale-branch-test-{0}" -f [Guid]::NewGuid().ToString("N"))
$remote = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-stale-branch-remote-{0}.git" -f [Guid]::NewGuid().ToString("N"))
$clone = Join-Path ([System.IO.Path]::GetTempPath()) ("orch-stale-branch-clone-{0}" -f [Guid]::NewGuid().ToString("N"))
try {
    New-Item -ItemType Directory -Force -Path $repo | Out-Null
    Invoke-Git -Repo $repo -Arguments @("init", "-b", "master") | Out-Null
    Invoke-Git -Repo $repo -Arguments @("config", "user.email", "test@example.invalid") | Out-Null
    Invoke-Git -Repo $repo -Arguments @("config", "user.name", "Test Agent") | Out-Null

    "base" | Set-Content -Path (Join-Path $repo "README.md") -Encoding UTF8
    Invoke-Git -Repo $repo -Arguments @("add", "README.md") | Out-Null
    Invoke-Git -Repo $repo -Arguments @("commit", "--quiet", "-m", "base") | Out-Null

    Invoke-Git -Repo $repo -Arguments @("checkout", "--quiet", "-b", "chatgpt/stale-work") | Out-Null
    "stale" | Set-Content -Path (Join-Path $repo "stale.txt") -Encoding UTF8
    Invoke-Git -Repo $repo -Arguments @("add", "stale.txt") | Out-Null
    Invoke-Git -Repo $repo -Arguments @("commit", "--quiet", "-m", "old stale work") | Out-Null
    Invoke-Git -Repo $repo -Arguments @("commit", "--quiet", "--amend", "--no-edit", "--date", "2000-01-01T00:00:00Z") | Out-Null

    Invoke-Git -Repo $repo -Arguments @("checkout", "--quiet", "master") | Out-Null
    Invoke-Git -Repo $repo -Arguments @("checkout", "--quiet", "-b", "codex/exception-work") | Out-Null
    "exception" | Set-Content -Path (Join-Path $repo "exception.txt") -Encoding UTF8
    Invoke-Git -Repo $repo -Arguments @("add", "exception.txt") | Out-Null
    Invoke-Git -Repo $repo -Arguments @("commit", "--quiet", "-m", "EXCEPTION TYPE: P0 interruption") | Out-Null
    Invoke-Git -Repo $repo -Arguments @("commit", "--quiet", "--amend", "--no-edit", "--date", "2000-01-01T00:00:00Z") | Out-Null

    Invoke-Git -Repo $repo -Arguments @("checkout", "--quiet", "master") | Out-Null

    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $repo -BaseBranch master -StaleDays 1 -NoFetch 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Stale branch status script failed: $($output -join "`n")"
    }

    $status = (($output | Out-String).Trim() | ConvertFrom-Json)
    if ($status.branchCount -lt 2) {
        throw "Expected at least two discovered branches, got $($status.branchCount)."
    }
    if (@($status.branches | Where-Object { $_.branch -eq "chatgpt/stale-work" -and $_.stale }).Count -ne 1) {
        throw "Expected chatgpt/stale-work to be reported stale."
    }
    if (@($status.branches | Where-Object { $_.branch -eq "codex/exception-work" -and -not $_.stale -and $null -ne $_.exception }).Count -ne 1) {
        throw "Expected codex/exception-work to carry an exception instead of stale=true."
    }
    if (@($status.byAgent | Where-Object { $_.agent -eq "chatgpt" -and $_.staleCount -ge 1 }).Count -ne 1) {
        throw "Expected byAgent summary to include chatgpt stale count."
    }
    if ([string]::IsNullOrWhiteSpace([string]$status.nextAction)) {
        throw "Expected nextAction to be populated."
    }

    Invoke-Git -Repo $repo -Arguments @("init", "--bare", $remote) | Out-Null
    Invoke-Git -Repo $repo -Arguments @("remote", "add", "origin", $remote) | Out-Null
    Invoke-Git -Repo $repo -Arguments @("push", "--quiet", "origin", "master", "chatgpt/stale-work", "codex/exception-work") | Out-Null
    Invoke-Git -Repo $repo -Arguments @("clone", "--quiet", $remote, $clone) | Out-Null
    Invoke-Git -Repo $clone -Arguments @("checkout", "--quiet", "master") | Out-Null

    $remoteOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $clone -BaseBranch master -StaleDays 1 -NoFetch 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Stale branch status script failed for remote-only clone: $($remoteOutput -join "`n")"
    }

    $remoteStatus = (($remoteOutput | Out-String).Trim() | ConvertFrom-Json)
    if (@($remoteStatus.branches | Where-Object { $_.branch -eq "chatgpt/stale-work" -and $_.ref -eq "origin/chatgpt/stale-work" -and $_.remoteOnly -and $_.stale }).Count -ne 1) {
        throw "Expected remote-only chatgpt/stale-work to be addressable as origin/chatgpt/stale-work and stale."
    }

    Write-Host "Validated stale branch status contract."
}
finally {
    Remove-Item -Path $repo,$remote,$clone -Recurse -Force -ErrorAction SilentlyContinue
}





