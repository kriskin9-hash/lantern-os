[CmdletBinding()]
param(
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
if (!(Test-Path $locksDir)) {
    @() | ConvertTo-Json
    exit 0
}

$now = Get-Date
$locks = @(Get-ChildItem $locksDir -Filter "*.manual.lock" -File -ErrorAction SilentlyContinue | ForEach-Object {
    $raw = Get-Content $_.FullName -Raw
    $json = $raw | ConvertFrom-Json
    $expired = $false
    if ($null -ne $json.expiresAt -and -not [string]::IsNullOrWhiteSpace([string]$json.expiresAt)) {
        $expired = ([datetime]$json.expiresAt) -lt $now
    }

    [pscustomobject]@{
        slot = [string]$json.slot
        owner = [string]$json.owner
        reason = [string]$json.reason
        createdAt = [string]$json.createdAt
        expiresAt = $json.expiresAt
        expired = $expired
        machine = [string]$json.machine
        path = $_.FullName.Replace($Root, "").TrimStart("\")
    }
})

$locks | ConvertTo-Json -Depth 5
