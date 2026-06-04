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

$installerPath = Join-Path $Root "scripts\Install-GitHookEnforcement.ps1"
if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Hook installer script missing: $installerPath"
}

$scriptText = Get-Content -LiteralPath $installerPath -Raw
foreach ($needle in @(
    "Resolve-HookScript",
    "Preferred",
    "Fallback",
    "Skipped",
    "idempotent"
)) {
    if ($scriptText -notmatch [regex]::Escape($needle)) {
        throw "Hook installer missing required tolerant-install text: $needle"
    }
}

$statusOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $installerPath -Status 2>&1
if ($LASTEXITCODE -ne 0) {
    throw ("Hook installer status mode failed: {0}" -f ($statusOutput -join [Environment]::NewLine))
}

if (($statusOutput | Out-String) -notmatch "Git Hook Enforcement Status") {
    throw "Hook installer status output missing expected header."
}

Write-Host "Git hook installer contract passed."
