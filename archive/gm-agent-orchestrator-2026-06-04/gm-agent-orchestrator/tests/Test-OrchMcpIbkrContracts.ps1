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

function Invoke-McpTool {
    param([string]$Name, [object]$Arguments)
    $body = @{
        jsonrpc = "2.0"
        id = [guid]::NewGuid().ToString("n")
        method = "tools/call"
        params = @{ name = $Name; arguments = $Arguments }
    } | ConvertTo-Json -Depth 20
    return Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $body
}

function Get-ToolResultText {
    param(
        [object]$Response,
        [string]$ToolName
    )
    if ($null -eq $Response) { throw "Null response from MCP for tool: $ToolName" }
    if ($Response.PSObject.Properties["error"]) {
        $err = $Response.error
        throw ("MCP returned JSON-RPC error for {0}: {1}" -f $ToolName, ($err | ConvertTo-Json -Depth 20 -Compress))
    }
    if (-not $Response.PSObject.Properties["result"]) { throw "MCP response missing result for tool: $ToolName" }
    if (-not $Response.result.PSObject.Properties["content"]) { throw "MCP result missing content for tool: $ToolName" }
    $content = @($Response.result.content)
    if ($content.Count -lt 1) { throw "MCP content array was empty for tool: $ToolName" }
    return [string]$content[0].text
}

$toolsBody = @{ jsonrpc = "2.0"; id = "list"; method = "tools/list"; params = @{} } | ConvertTo-Json -Depth 10
$toolsResponse = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/mcp" -Method Post -ContentType "application/json" -Body $toolsBody
$tools = @($toolsResponse.result.tools)

$required = @("get_ibkr_quotes", "get_ibkr_orderbook", "get_ibkr_positions", "get_ibkr_account_risk")
foreach ($name in $required) {
    $tool = @($tools | Where-Object { $_.name -eq $name } | Select-Object -First 1)
    if ($tool.Count -lt 1) { throw "tools/list missing required IBKR tool: $name" }
    if ($null -eq $tool[0].inputSchema) { throw "IBKR tool is missing inputSchema: $name" }
    if ($tool[0].inputSchema.additionalProperties -ne $false) { throw "IBKR tool must set inputSchema.additionalProperties=false: $name" }
}

$quotes = Invoke-McpTool -Name "get_ibkr_quotes" -Arguments @{ symbols = @("SPY"); asset_class = "equity"; max_quote_age_ms = 10000 }
$quotesText = Get-ToolResultText -Response $quotes -ToolName "get_ibkr_quotes"
$quotesObj = $quotesText | ConvertFrom-Json
if ($quotesObj.ok -eq $true) {
    if ($null -eq $quotesObj.quotes -or @($quotesObj.quotes).Count -lt 1) { throw "get_ibkr_quotes ok=true must include at least one quote." }
}
else {
    if ($quotesObj.error -notin @("ibkr_unavailable", "stale_data", "invalid_symbol")) { throw "Unexpected error from get_ibkr_quotes: $($quotesObj.error)" }
    if ([string]::IsNullOrWhiteSpace([string]$quotesObj.nextAction)) { throw "get_ibkr_quotes error result must include nextAction guidance." }
}

$positions = Invoke-McpTool -Name "get_ibkr_positions" -Arguments @{}
$positionsText = Get-ToolResultText -Response $positions -ToolName "get_ibkr_positions"
$positionsObj = $positionsText | ConvertFrom-Json
if ($positionsObj.ok -eq $true) {
    if (-not $positionsObj.PSObject.Properties["positions"]) { throw "get_ibkr_positions ok=true must include positions." }
}
else {
    if ($positionsObj.error -notin @("ibkr_unavailable", "stale_data")) { throw "Unexpected error from get_ibkr_positions: $($positionsObj.error)" }
    if ([string]::IsNullOrWhiteSpace([string]$positionsObj.generatedAt)) { throw "get_ibkr_positions error result must include generatedAt." }
}

Write-Host "Validated IBKR MCP contract surface (registration + safe unavailable envelope)."
