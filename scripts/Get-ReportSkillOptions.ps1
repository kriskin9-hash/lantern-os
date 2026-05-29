param(
    [string]$Root = "",
    [string]$Format = "table"
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$configPath = Join-Path $Root "manifests/report-skill-options.json"
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "Missing options config: $configPath"
}

$cfg = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json

if ($Format -eq "json") {
    $cfg | ConvertTo-Json -Depth 8
    exit 0
}

$cfg.options | Select-Object id,label,renderer,description | Format-Table -AutoSize
