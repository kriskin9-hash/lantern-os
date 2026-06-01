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

$output = @(& git -C $Root status --short 2>&1)
$exitCode = $LASTEXITCODE
$text = ($output | Out-String).TrimEnd()
$lines = @()
if (-not [string]::IsNullOrWhiteSpace($text)) {
    $lines = @($text -split "`r?`n")
}

[pscustomobject]@{
    ok = ($exitCode -eq 0)
    exitCode = $exitCode
    root = $Root
    lineCount = $lines.Count
    statusShort = $lines
} | ConvertTo-Json -Depth 10
