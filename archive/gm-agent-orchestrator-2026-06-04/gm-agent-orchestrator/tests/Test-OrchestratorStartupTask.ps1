[CmdletBinding()]
param(
    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    $Root = (Resolve-Path (Join-Path $scriptDir "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$script = Join-Path $Root "scripts\Register-OrchestratorStartupTask.ps1"
if (-not (Test-Path $script)) {
    throw "Startup task registration script not found: $script"
}

# Test Plan Mode / Dry Run (Default)
Write-Host "Testing Dry Run behavior..."
$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $Root 2>&1
if ($LASTEXITCODE -ne 0) { throw "Dry Run failed: $($output -join "`n")" }
$plan = $output | Out-String | ConvertFrom-Json
if ($plan.action -ne "register") { throw "Expected register action in dry-run JSON" }
if ($plan.applied) { throw "Expected applied=false for dry-run registration" }
if ($plan.arguments -notmatch "Start-OrchestratorServices.ps1" -or $plan.arguments -notmatch "-Once") { throw "Expected startup task to run Start-OrchestratorServices.ps1 -Once" }

# Test Status behavior
Write-Host "Testing Status behavior..."
$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $Root -Status 2>&1
if ($LASTEXITCODE -ne 0) { throw "Status check failed: $($output -join "`n")" }
try {
    $status = $output | Out-String | ConvertFrom-Json
    if ($status.action -ne "status") { throw "Expected status action" }
    if ($null -eq $status.status.registered) { throw "Expected 'registered' property in status payload" }
}
catch {
    throw "Status output is not valid JSON: $($output -join "`n")"
}

# Test Unregister Dry Run
Write-Host "Testing Unregister Dry Run..."
$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Root $Root -Unregister 2>&1
if ($LASTEXITCODE -ne 0) { throw "Unregister Dry Run failed: $($output -join "`n")" }
$unregisterPlan = $output | Out-String | ConvertFrom-Json
if ($unregisterPlan.action -ne "unregister") { throw "Expected unregister action in dry-run JSON" }
if ($unregisterPlan.applied) { throw "Expected applied=false for dry-run unregister" }

Write-Host "Startup task registration tests passed (Logic only, no mutation)."
