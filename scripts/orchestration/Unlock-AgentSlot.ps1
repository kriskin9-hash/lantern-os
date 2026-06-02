[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SlotName,

    [string]$Root = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path "$PSScriptRoot\..").Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$path = Join-Path (Join-Path $Root "locks") ("{0}.manual.lock" -f $SlotName)

if (!(Test-Path $path)) {
    Write-Host "No manual lock exists for $SlotName."
    exit 0
}

Remove-Item $path -Force
Write-Host "Unlocked $SlotName."
