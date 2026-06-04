[CmdletBinding()]
param(
    [string]$Root = "",
    [int]$Port = 8787,
    [string]$Symbol = "SPY",
    [string]$BuyVenue = "ibkr",
    [string]$SellVenue = "venueb",
    [string]$TelemetryPath = "",
    [string]$ActionOutputPath = "",
    [int]$PollMs = 300,
    [int]$MaxIterations = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

if ([string]::IsNullOrWhiteSpace($TelemetryPath)) {
    $TelemetryPath = Join-Path $Root "artifacts\market-data\live-steering-telemetry.json"
}
elseif (-not [System.IO.Path]::IsPathRooted($TelemetryPath)) {
    $TelemetryPath = Join-Path $Root $TelemetryPath
}

if (-not [string]::IsNullOrWhiteSpace($ActionOutputPath) -and -not [System.IO.Path]::IsPathRooted($ActionOutputPath)) {
    $ActionOutputPath = Join-Path $Root $ActionOutputPath
}

if ($PollMs -lt 100) { $PollMs = 100 }

function Read-Telemetry {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [pscustomobject]@{
            realized_pnl_usd = 0
            slippage_overshoot_bps = 0
            fill_latency_ms = 0
            loss_floor_usd = 0
            exit_edge_floor_bps = 0.2
            max_slippage_overshoot_bps = 2.0
        }
    }
    try {
        return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        throw "Telemetry file is invalid JSON: $Path"
    }
}

$iteration = 0
while ($true) {
    if ($MaxIterations -gt 0 -and $iteration -ge $MaxIterations) { break }
    $iteration++

    $telemetry = Read-Telemetry -Path $TelemetryPath
    $args = [ordered]@{
        symbol = $Symbol
        buy_venue = $BuyVenue
        sell_venue = $SellVenue
        realized_pnl_usd = [double]$telemetry.realized_pnl_usd
        slippage_overshoot_bps = [double]$telemetry.slippage_overshoot_bps
        fill_latency_ms = [int]$telemetry.fill_latency_ms
        loss_floor_usd = [double]$telemetry.loss_floor_usd
        exit_edge_floor_bps = [double]$telemetry.exit_edge_floor_bps
        max_slippage_overshoot_bps = [double]$telemetry.max_slippage_overshoot_bps
    }

    $body = @{
        jsonrpc = "2.0"
        id = "steer-loop-$iteration"
        method = "tools/call"
        params = @{
            name = "steer_live_spread_trade"
            arguments = $args
        }
    } | ConvertTo-Json -Depth 20

    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $body
    if ($resp.PSObject.Properties["error"]) {
        throw ("steer_live_spread_trade JSON-RPC error: " + ($resp.error | ConvertTo-Json -Depth 10 -Compress))
    }
    $obj = ([string]$resp.result.content[0].text) | ConvertFrom-Json
    $out = [pscustomobject]@{
        generatedAt = (Get-Date).ToString("o")
        iteration = $iteration
        action = $obj.action
        reasons = @($obj.reasons)
        telemetry = $obj.telemetry
        state = $obj.state
        thresholds = $obj.thresholds
    }
    if (-not [string]::IsNullOrWhiteSpace($ActionOutputPath)) {
        $parent = Split-Path -Parent $ActionOutputPath
        if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        ($out | ConvertTo-Json -Depth 20) | Set-Content -LiteralPath $ActionOutputPath
    }
    $out | ConvertTo-Json -Depth 10 -Compress | Write-Output
    Start-Sleep -Milliseconds $PollMs
}
