param(
    [string]$LanternRoot = "C:\tmp\lantern-os",
    [string]$Query = "",
    [int]$TimeoutSeconds = 30,
    [switch]$WriteReceipt
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Query)) {
    Write-Error "Query parameter is required. Usage: Invoke-ConvergenceFleetQuery.ps1 -Query 'your question'"
    exit 1
}

function Get-AgentSlots {
    param([string]$Root)
    $configPath = Join-Path $Root "config\agents.json"
    if (-not (Test-Path -LiteralPath $configPath)) {
        Write-Error "Agent config not found at $configPath"
        exit 1
    }
    $config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
    return @($config.slots | Where-Object { $_.enabled -eq $true } | ForEach-Object {
        [ordered]@{
            name = $_.name
            slot = $_.slot
            step = $_.step
            agent = $_.agent
            role = $_.role
            runtime = $_.runtime
            state = $_.state
        }
    })
}

function Invoke-McpAgentQuery {
    param(
        [string]$Slot,
        [string]$Query,
        [int]$TimeoutSeconds
    )
    try {
        # Try to call MCP tool for agent query
        # This would call the MCP service to get the agent's response
        # For now, return a placeholder that would be replaced with actual MCP call
        $mcpUrl = "http://127.0.0.1:8787"
        $body = @{
            slot = $Slot
            query = $Query
        } | ConvertTo-Json -Depth 3
        
        $response = Invoke-WebRequest -UseBasicParsing -Uri "$mcpUrl/api/agent/query" `
            -Method POST `
            -Body $body `
            -ContentType "application/json" `
            -TimeoutSec $TimeoutSeconds `
            -ErrorAction SilentlyContinue
        
        if ($response) {
            $content = $response.Content | ConvertFrom-Json
            return [ordered]@{
                slot = $Slot
                ok = $true
                response = $content.response
                error = $null
            }
        } else {
            return [ordered]@{
                slot = $Slot
                ok = $false
                response = $null
                error = "MCP service unavailable"
            }
        }
    } catch {
        return [ordered]@{
            slot = $Slot
            ok = $false
            response = $null
            error = $_.Exception.Message
        }
    }
}

$agentSlots = Get-AgentSlots -Root $LanternRoot
$results = @()

foreach ($slot in $agentSlots) {
    Write-Host "Querying agent slot $($slot.name) (role: $($slot.role))..."
    $result = Invoke-McpAgentQuery -Slot $slot.name -Query $Query -TimeoutSeconds $TimeoutSeconds
    $results += [ordered]@{
        slotName = $slot.name
        slotNumber = $slot.slot
        step = $slot.step
        agent = $slot.agent
        role = $slot.role
        ok = $result.ok
        response = $result.response
        error = $result.error
    }
}

$successfulResponses = @($results | Where-Object { $_.ok -eq $true })
$failedResponses = @($results | Where-Object { $_.ok -eq $false })

$result = [ordered]@{
    schema = "lantern.convergence_fleet_query.v1"
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    query = $Query
    fleetStatus = [ordered]@{
        totalSlots = $agentSlots.Count
        successfulResponses = $successfulResponses.Count
        failedResponses = $failedResponses.Count
    }
    responses = $results
    summary = if ($successfulResponses.Count -gt 0) {
        "Received $($successfulResponses.Count) responses from convergence fleet"
    } else {
        "No successful responses from convergence fleet"
    }
}

if ($WriteReceipt) {
    $outPath = Join-Path $LanternRoot "manifests\validation\CONVERGENCE-FLEET-QUERY-LATEST.json"
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outPath) | Out-Null
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outPath -Encoding UTF8
}

$result | ConvertTo-Json -Depth 8
