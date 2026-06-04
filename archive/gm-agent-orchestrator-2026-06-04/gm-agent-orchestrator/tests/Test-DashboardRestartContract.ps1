[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script = Join-Path $Root 'scripts\Restart-DashboardServer.ps1'
if (-not (Test-Path $script)) {
    throw "Restart script was not found: $script"
}

$content = Get-Content $script -Raw

if ($content -match '\(Get-Command\s+pwsh\s+-ErrorAction\s+SilentlyContinue\)\.Source') {
    throw 'Restart script must not dereference .Source directly from a possibly-null Get-Command result.'
}

if ($content -notmatch 'function\s+Resolve-PowerShellCommandPath') {
    throw 'Restart script must resolve the PowerShell executable through Resolve-PowerShellCommandPath.'
}

if ($content -notmatch '\$null\s+-ne\s+\$pwshCommand') {
    throw 'Restart script must null-check the pwsh command before reading Source.'
}

if ($content -notmatch 'Get-Command\s+powershell\s+-ErrorAction\s+Stop') {
    throw 'Restart script must fall back to Windows PowerShell when pwsh is unavailable.'
}

Write-Host 'Validated dashboard restart PowerShell resolution contract.'
