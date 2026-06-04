[CmdletBinding()]
param(
    [string]$Root = "",
    [int]$Port = 8787
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} else {
    $Root = (Resolve-Path $Root).Path
}

function Invoke-McpTool {
    param([string]$Name, [object]$Arguments)
    $body = @{
        jsonrpc = "2.0"
        id = [guid]::NewGuid().ToString("n")
        method = "tools/call"
        params = @{ name = $Name; arguments = $Arguments }
    } | ConvertTo-Json -Depth 30
    return Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $body
}

$scenarios = @(
    @{ symbol = "SPY"; buy_venue = "ibkr"; sell_venue = "venueb"; quantity = 50; fee_model = "conservative" },
    @{ symbol = "SPY"; buy_venue = "ibkr"; sell_venue = "venueb"; quantity = 100; fee_model = "conservative" },
    @{ symbol = "QQQ"; buy_venue = "ibkr"; sell_venue = "venueb"; quantity = 80; fee_model = "conservative" }
)

$first = @()
$second = @()

foreach ($s in $scenarios) {
    $resp = Invoke-McpTool -Name "simulate_spread_trade" -Arguments $s
    if ($resp.PSObject.Properties["error"]) { throw ("simulate_spread_trade JSON-RPC error: " + ($resp.error | ConvertTo-Json -Depth 10 -Compress)) }
    $obj = ([string]$resp.result.content[0].text | ConvertFrom-Json)
    if ($obj.ok -ne $true) { throw "simulate_spread_trade must return ok=true" }
    $first += [pscustomobject]@{ symbol=$obj.simulation.symbol; quantity=[double]$obj.simulation.quantity; netPnl=[double]$obj.simulation.netPnl; netEdgeBps=[double]$obj.simulation.netEdgeBps }
}

foreach ($s in $scenarios) {
    $resp = Invoke-McpTool -Name "simulate_spread_trade" -Arguments $s
    if ($resp.PSObject.Properties["error"]) { throw ("simulate_spread_trade JSON-RPC error: " + ($resp.error | ConvertTo-Json -Depth 10 -Compress)) }
    $obj = ([string]$resp.result.content[0].text | ConvertFrom-Json)
    if ($obj.ok -ne $true) { throw "simulate_spread_trade must return ok=true" }
    $second += [pscustomobject]@{ symbol=$obj.simulation.symbol; quantity=[double]$obj.simulation.quantity; netPnl=[double]$obj.simulation.netPnl; netEdgeBps=[double]$obj.simulation.netEdgeBps }
}

for ($i=0; $i -lt $first.Count; $i++) {
    if ($first[$i].symbol -ne $second[$i].symbol) { throw "Replay symbol mismatch at index $i" }
    if ($first[$i].quantity -ne $second[$i].quantity) { throw "Replay quantity mismatch at index $i" }
    if ([math]::Abs($first[$i].netPnl - $second[$i].netPnl) -gt 1e-9) { throw "Replay netPnl mismatch at index $i" }
    if ([math]::Abs($first[$i].netEdgeBps - $second[$i].netEdgeBps) -gt 1e-9) { throw "Replay netEdgeBps mismatch at index $i" }
}

Write-Host "Validated deterministic replay for simulate_spread_trade across fixed scenarios."
