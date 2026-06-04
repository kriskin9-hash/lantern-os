[CmdletBinding()]
param(
    [string]$OrchestratorRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [switch]$JsonOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path -LiteralPath $OrchestratorRoot).Path
$statusScript = Join-Path $root "scripts\Get-OrchestratorStatus.ps1"
$overviewPath = Join-Path $root "dashboard\overview.html"

if (!(Test-Path -LiteralPath $statusScript)) {
    throw "Missing status script: $statusScript"
}

if (!(Test-Path -LiteralPath $overviewPath)) {
    throw "Missing dashboard overview: $overviewPath"
}

$status = & $statusScript -Root $root
if ($null -eq $status) {
    throw "Get-OrchestratorStatus.ps1 returned no status object."
}

$checks = @()
function Add-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail
    )

    $script:checks += [pscustomobject]@{
        name = $Name
        passed = $Passed
        detail = $Detail
    }
}

$slots = @($status.slots)
$counts = $status.counts
$hasWorktree = @($slots | Where-Object { $null -ne $_.worktree }).Count -gt 0
$hasChangedFilesProperty = @($slots | Where-Object { $_.PSObject.Properties.Name -contains "changedFiles" }).Count -gt 0
$overview = Get-Content -LiteralPath $overviewPath -Raw

Add-Check -Name "status generatedAt" -Passed (-not [string]::IsNullOrWhiteSpace([string]$status.generatedAt)) -Detail ([string]$status.generatedAt)
Add-Check -Name "status counts" -Passed ($null -ne $counts -and $null -ne $counts.queue -and $null -ne $counts.active -and $null -ne $counts.failed) -Detail "queue=$($counts.queue) active=$($counts.active) failed=$($counts.failed)"
Add-Check -Name "slots visible" -Passed ($slots.Count -gt 0) -Detail "$($slots.Count) slot(s)"
Add-Check -Name "worktree status visible" -Passed $hasWorktree -Detail "worktree property present on at least one slot"
Add-Check -Name "changed files visible" -Passed $hasChangedFilesProperty -Detail "changedFiles property present on at least one slot"
Add-Check -Name "overview has regression section" -Passed ($overview -match "Testing & Regression") -Detail "dashboard/overview.html"
Add-Check -Name "overview has traces table" -Passed ($overview -match "<h2>Traces</h2>") -Detail "dashboard/overview.html"
Add-Check -Name "overview has changed files metric" -Passed ($overview -match "Changed Files") -Detail "dashboard/overview.html"

$failed = @($checks | Where-Object { -not $_.passed })
$result = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("o")
    root = $root
    passed = ($failed.Count -eq 0)
    failedCount = $failed.Count
    checks = $checks
}

if ($JsonOnly) {
    $result | ConvertTo-Json -Depth 10
}
else {
    foreach ($check in $checks) {
        $prefix = $(if ($check.passed) { "PASS" } else { "FAIL" })
        Write-Host ("[{0}] {1} - {2}" -f $prefix, $check.name, $check.detail)
    }

    if ($failed.Count -gt 0) {
        throw "Dashboard regression failed: $($failed.Count) check(s) failed."
    }

    Write-Host "Dashboard regression checks passed." -ForegroundColor Green
}
