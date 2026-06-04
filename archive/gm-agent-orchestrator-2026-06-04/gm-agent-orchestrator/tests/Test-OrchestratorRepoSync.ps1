[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$syncScript = Join-Path $Root "scripts/Invoke-OrchestratorRepoSync.ps1"
if (!(Test-Path $syncScript)) {
    throw "Repository sync script was not found: $syncScript"
}

$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $syncScript -Root $Root -PlanOnly
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    throw "Invoke-OrchestratorRepoSync.ps1 exited with code $exitCode."
}

$jsonText = ($output | Out-String).Trim()
if ([string]::IsNullOrWhiteSpace($jsonText)) {
    throw "Invoke-OrchestratorRepoSync.ps1 wrote no stdout. Expected JSON."
}

try {
    $result = $jsonText | ConvertFrom-Json -ErrorAction Stop
}
catch {
    throw "Invoke-OrchestratorRepoSync.ps1 stdout is not valid JSON: $($_.Exception.Message)"
}

foreach ($field in @("ok", "generatedAt", "action", "root", "remote", "branch", "mode", "command", "before", "after", "changed", "dirty")) {
    if ($null -eq $result.PSObject.Properties[$field]) {
        throw "Repository sync JSON is missing required top-level field: $field"
    }
}

if ($result.action -ne "sync_repository") {
    throw "Unexpected repository sync action: $($result.action)"
}

if ($result.mode -ne "ff-only") {
    throw "Repository sync must default to ff-only mode. Actual: $($result.mode)"
}

if ($result.planOnly -ne $true) {
    throw "Plan-only validation expected planOnly=true."
}

if ($result.changed -ne $false) {
    throw "Plan-only validation must not change the repository."
}

Write-Host "Validated repository sync plan-only JSON contract."
