[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$testScript = Join-Path $Root "scripts\Test-ResearchIngestion.ps1"
$updateScript = Join-Path $Root "scripts\Update-ResearchContext.ps1"

foreach ($required in @($testScript, $updateScript)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Missing required script: $required"
    }
}

$testJson = & powershell -NoProfile -ExecutionPolicy Bypass -File $testScript -Root $Root -AsJson
if ($LASTEXITCODE -ne 0) {
    throw "Test-ResearchIngestion.ps1 failed: $($testJson | Out-String)"
}

$testResult = ($testJson | Out-String).Trim() | ConvertFrom-Json -ErrorAction Stop
if ($testResult.ok -ne $true) {
    throw "Test-ResearchIngestion.ps1 reported ok=false."
}

$dryRunJson = & powershell -NoProfile -ExecutionPolicy Bypass -File $updateScript -Root $Root -DryRun
if ($LASTEXITCODE -ne 0) {
    throw "Update-ResearchContext.ps1 -DryRun failed: $($dryRunJson | Out-String)"
}

$dryRunResult = ($dryRunJson | Out-String).Trim() | ConvertFrom-Json -ErrorAction Stop
if ($dryRunResult.ok -ne $true) {
    throw "Update-ResearchContext dry-run reported ok=false."
}
if ($dryRunResult.dryRun -ne $true) {
    throw "Update-ResearchContext dry-run contract failed: dryRun flag expected true."
}
if ($null -eq $dryRunResult.coverage) {
    throw "Update-ResearchContext dry-run must return coverage."
}

Write-Host "Research ingestion contract passed."
