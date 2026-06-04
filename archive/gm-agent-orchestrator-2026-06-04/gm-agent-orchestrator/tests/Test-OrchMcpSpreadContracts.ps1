[CmdletBinding()]
param(
    [string]$Root = "",
    [int]$Port = 8787
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $Root = (Resolve-Path $Root).Path
}

$listBody = @{ jsonrpc = "2.0"; id = "list"; method = "tools/list"; params = @{} } | ConvertTo-Json -Depth 10
$list = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $listBody
$tool = @($list.result.tools | Where-Object { $_.name -eq "rank_spread_opportunities" } | Select-Object -First 1)
if ($tool.Count -lt 1) { throw "tools/list missing rank_spread_opportunities" }
if (@($tool[0].inputSchema.required) -notcontains "universe") { throw "rank_spread_opportunities must require universe" }
if (@($tool[0].inputSchema.required) -notcontains "venues") { throw "rank_spread_opportunities must require venues" }
$simTool = @($list.result.tools | Where-Object { $_.name -eq "simulate_spread_trade" } | Select-Object -First 1)
if ($simTool.Count -lt 1) { throw "tools/list missing simulate_spread_trade" }
if (@($simTool[0].inputSchema.required) -notcontains "symbol") { throw "simulate_spread_trade must require symbol" }
if (@($simTool[0].inputSchema.required) -notcontains "buy_venue") { throw "simulate_spread_trade must require buy_venue" }
if (@($simTool[0].inputSchema.required) -notcontains "sell_venue") { throw "simulate_spread_trade must require sell_venue" }
if (@($simTool[0].inputSchema.required) -notcontains "quantity") { throw "simulate_spread_trade must require quantity" }
$gateTool = @($list.result.tools | Where-Object { $_.name -eq "get_spread_execution_readiness" } | Select-Object -First 1)
if ($gateTool.Count -lt 1) { throw "tools/list missing get_spread_execution_readiness" }
$profitTool = @($list.result.tools | Where-Object { $_.name -eq "get_spread_profitability_snapshot" } | Select-Object -First 1)
if ($profitTool.Count -lt 1) { throw "tools/list missing get_spread_profitability_snapshot" }
$planTool = @($list.result.tools | Where-Object { $_.name -eq "plan_spread_live_micro_experiment" } | Select-Object -First 1)
if ($planTool.Count -lt 1) { throw "tools/list missing plan_spread_live_micro_experiment" }
$steeringStateTool = @($list.result.tools | Where-Object { $_.name -eq "get_live_steering_state" } | Select-Object -First 1)
if ($steeringStateTool.Count -lt 1) { throw "tools/list missing get_live_steering_state" }
$steerTool = @($list.result.tools | Where-Object { $_.name -eq "steer_live_spread_trade" } | Select-Object -First 1)
if ($steerTool.Count -lt 1) { throw "tools/list missing steer_live_spread_trade" }
$packetTool = @($list.result.tools | Where-Object { $_.name -eq "get_spread_operator_packet" } | Select-Object -First 1)
if ($packetTool.Count -lt 1) { throw "tools/list missing get_spread_operator_packet" }

$callBody = @{
    jsonrpc = "2.0"
    id = "rank"
    method = "tools/call"
    params = @{
        name = "rank_spread_opportunities"
        arguments = @{
            universe = @("SPY", "QQQ")
            venues = @("ibkr", "venueb")
            min_net_edge_bps = 0
            fee_model = "conservative"
        }
    }
} | ConvertTo-Json -Depth 20

$resp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $callBody
if ($resp.PSObject.Properties["error"]) {
    throw ("rank_spread_opportunities returned JSON-RPC error: " + ($resp.error | ConvertTo-Json -Depth 10 -Compress))
}
$text = [string]$resp.result.content[0].text
$obj = $text | ConvertFrom-Json
if ($obj.ok -ne $true) { throw "rank_spread_opportunities must return ok=true in fixture environment." }
if ($null -eq $obj.opportunities) { throw "rank_spread_opportunities must return opportunities array." }

$simBody = @{
    jsonrpc = "2.0"
    id = "sim"
    method = "tools/call"
    params = @{
        name = "simulate_spread_trade"
        arguments = @{
            symbol = "SPY"
            buy_venue = "ibkr"
            sell_venue = "venueb"
            quantity = 100
            fee_model = "conservative"
        }
    }
} | ConvertTo-Json -Depth 20

$simResp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $simBody
if ($simResp.PSObject.Properties["error"]) {
    throw ("simulate_spread_trade returned JSON-RPC error: " + ($simResp.error | ConvertTo-Json -Depth 10 -Compress))
}
$simText = [string]$simResp.result.content[0].text
$simObj = $simText | ConvertFrom-Json
if ($simObj.ok -ne $true) { throw "simulate_spread_trade must return ok=true in fixture environment." }
if ($null -eq $simObj.simulation) { throw "simulate_spread_trade must return simulation object." }
if ($null -eq $simObj.simulation.netPnl) { throw "simulate_spread_trade simulation must include netPnl." }

$gateBody = @{
    jsonrpc = "2.0"
    id = "gate"
    method = "tools/call"
    params = @{
        name = "get_spread_execution_readiness"
        arguments = @{
            universe = @("SPY", "QQQ")
            venues = @("ibkr", "venueb")
            max_quote_age_ms = 10000
        }
    }
} | ConvertTo-Json -Depth 20

$gateResp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $gateBody
if ($gateResp.PSObject.Properties["error"]) {
    throw ("get_spread_execution_readiness returned JSON-RPC error: " + ($gateResp.error | ConvertTo-Json -Depth 10 -Compress))
}
$gateText = [string]$gateResp.result.content[0].text
$gateObj = $gateText | ConvertFrom-Json
if ($gateObj.ok -ne $true) { throw "get_spread_execution_readiness must return ok=true." }
if ($gateObj.status -notin @("ready", "held")) { throw "get_spread_execution_readiness must return status=ready|held." }
if ($null -eq $gateObj.blockers) { throw "get_spread_execution_readiness must include blockers array." }
if ($null -eq $gateObj.deploymentSuccessClaimAllowed) { throw "get_spread_execution_readiness must include deploymentSuccessClaimAllowed." }

$profitBody = @{
    jsonrpc = "2.0"
    id = "profit"
    method = "tools/call"
    params = @{
        name = "get_spread_profitability_snapshot"
        arguments = @{
            universe = @("SPY", "QQQ")
            venues = @("ibkr", "venueb")
            quantity = 100
        }
    }
} | ConvertTo-Json -Depth 20

$profitResp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $profitBody
if ($profitResp.PSObject.Properties["error"]) {
    throw ("get_spread_profitability_snapshot returned JSON-RPC error: " + ($profitResp.error | ConvertTo-Json -Depth 10 -Compress))
}
$profitText = [string]$profitResp.result.content[0].text
$profitObj = $profitText | ConvertFrom-Json
if ($profitObj.ok -ne $true) { throw "get_spread_profitability_snapshot must return ok=true." }
if ($null -eq $profitObj.profitability) { throw "get_spread_profitability_snapshot must include profitability." }
if ($profitObj.profitability.claim -notin @("not_proven", "provisional_paper_positive")) { throw "Unexpected profitability.claim value." }
if ($null -eq $profitObj.profitability.profitabilityProvenNow) { throw "get_spread_profitability_snapshot must include profitabilityProvenNow." }

$planBody = @{
    jsonrpc = "2.0"
    id = "plan"
    method = "tools/call"
    params = @{
        name = "plan_spread_live_micro_experiment"
        arguments = @{
            universe = @("SPY", "QQQ")
            venues = @("ibkr", "venueb")
            quantity = 100
            max_loss_usd = 15
            max_notional_usd = 1500
        }
    }
} | ConvertTo-Json -Depth 20

$planResp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $planBody
if ($planResp.PSObject.Properties["error"]) {
    throw ("plan_spread_live_micro_experiment returned JSON-RPC error: " + ($planResp.error | ConvertTo-Json -Depth 10 -Compress))
}
$planText = [string]$planResp.result.content[0].text
$planObj = $planText | ConvertFrom-Json
if ($planObj.ok -ne $true) { throw "plan_spread_live_micro_experiment must return ok=true." }
if ($planObj.status -notin @("hold", "ready_to_execute_guarded")) { throw "Unexpected plan_spread_live_micro_experiment status." }
if ($null -eq $planObj.guardrails) { throw "plan_spread_live_micro_experiment must include guardrails." }
if ($null -eq $planObj.evidence) { throw "plan_spread_live_micro_experiment must include evidence." }

$steerBody = @{
    jsonrpc = "2.0"
    id = "steer"
    method = "tools/call"
    params = @{
        name = "steer_live_spread_trade"
        arguments = @{
            symbol = "SPY"
            buy_venue = "ibkr"
            sell_venue = "venueb"
            realized_pnl_usd = 0
            slippage_overshoot_bps = 0
            fill_latency_ms = 300
            loss_floor_usd = 0
        }
    }
} | ConvertTo-Json -Depth 20
$steerResp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $steerBody
if ($steerResp.PSObject.Properties["error"]) {
    throw ("steer_live_spread_trade returned JSON-RPC error: " + ($steerResp.error | ConvertTo-Json -Depth 10 -Compress))
}
$steerObj = ([string]$steerResp.result.content[0].text) | ConvertFrom-Json
if ($steerObj.ok -ne $true) { throw "steer_live_spread_trade must return ok=true." }
if ($steerObj.action -notin @("enter", "hold", "reduce", "exit_now", "kill_switch")) { throw "Unexpected steer_live_spread_trade action." }
if ($null -eq $steerObj.thresholds) { throw "steer_live_spread_trade must include thresholds." }
if ([double]$steerObj.thresholds.lossFloorUsd -ne 0.0) { throw "steer_live_spread_trade must enforce 0 USD floor by default/argument." }
if ([double]$steerObj.thresholds.exitEdgeFloorBps -ne 0.2) { throw "steer_live_spread_trade default exitEdgeFloorBps must be 0.2." }
if ($steerObj.action -ne "enter") { throw "At breakeven with positive simulated edge and readiness ok, steer_live_spread_trade should return enter." }

$stateBody = @{
    jsonrpc = "2.0"
    id = "state"
    method = "tools/call"
    params = @{
        name = "get_live_steering_state"
        arguments = @{
            universe = @("SPY", "QQQ")
            venues = @("ibkr", "venueb")
            quantity = 100
        }
    }
} | ConvertTo-Json -Depth 20
$stateResp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $stateBody
if ($stateResp.PSObject.Properties["error"]) {
    throw ("get_live_steering_state returned JSON-RPC error: " + ($stateResp.error | ConvertTo-Json -Depth 10 -Compress))
}
$stateObj = ([string]$stateResp.result.content[0].text) | ConvertFrom-Json
if ($stateObj.ok -ne $true) { throw "get_live_steering_state must return ok=true." }
if ($stateObj.recommendedMode -notin @("hold", "execute_guarded")) { throw "Unexpected get_live_steering_state recommendedMode." }

$packetBody = @{
    jsonrpc = "2.0"
    id = "packet"
    method = "tools/call"
    params = @{
        name = "get_spread_operator_packet"
        arguments = @{
            symbol = "SPY"
            buy_venue = "ibkr"
            sell_venue = "venueb"
            realized_pnl_usd = 0
            slippage_overshoot_bps = 0.2
            fill_latency_ms = 280
            loss_floor_usd = 0
        }
    }
} | ConvertTo-Json -Depth 20
$packetResp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $packetBody
if ($packetResp.PSObject.Properties["error"]) {
    throw ("get_spread_operator_packet returned JSON-RPC error: " + ($packetResp.error | ConvertTo-Json -Depth 10 -Compress))
}
$packetObj = ([string]$packetResp.result.content[0].text) | ConvertFrom-Json
if ($packetObj.ok -ne $true) { throw "get_spread_operator_packet must return ok=true." }
if ([string]::IsNullOrWhiteSpace([string]$packetObj.githubCommentMarkdown)) { throw "get_spread_operator_packet must include githubCommentMarkdown." }

Write-Host "Validated spread MCP contracts and runtime responses (ranking + simulation + readiness + profitability + live plan + steering)."
