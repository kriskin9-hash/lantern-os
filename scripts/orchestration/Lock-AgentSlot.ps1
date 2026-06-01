[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SlotName,

    [string]$Reason = "manual agent session",
    [string]$Owner = "Alex",
    [int]$TtlMinutes = 0,
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

$locksDir = Join-Path $Root "locks"
New-Item -ItemType Directory -Force -Path $locksDir | Out-Null

$now = Get-Date
$expiresAt = $null
if ($TtlMinutes -gt 0) {
    $expiresAt = $now.AddMinutes($TtlMinutes).ToString("o")
}

$payload = [pscustomobject]@{
    slot = $SlotName
    owner = $Owner
    reason = $Reason
    createdAt = $now.ToString("o")
    expiresAt = $expiresAt
    machine = $env:COMPUTERNAME
}

$path = Join-Path $locksDir ("{0}.manual.lock" -f $SlotName)
$payload | ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding UTF8

Write-Host "Locked $SlotName for manual use: $path"
Write-Host "Reason: $Reason"
