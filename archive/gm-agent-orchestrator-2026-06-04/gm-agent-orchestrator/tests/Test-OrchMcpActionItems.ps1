[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$McpServerUri = "http://127.0.0.1:8787"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== META-ORCHESTRATOR PATTERN TEST ==="
Write-Host "Agents should create follow-up work via MCP, not locally."
Write-Host ""

# Test 1: MCP server health
Write-Host "[1/2] Checking MCP server availability..."
try {
    $health = Invoke-RestMethod -Uri "$McpServerUri/health" -TimeoutSec 5 -ErrorAction Stop
    if ($health.ok -and $health.service -eq "gm-agent-orchestrator-mcp") {
        Write-Host "  PASS: MCP server online at $McpServerUri"
        $serverOnline = $true
    }
} catch {
    Write-Host "  SKIP: MCP server not responding"
    Write-Host "  Start with: .\scripts\Start-OrchMcpServer.ps1"
    $serverOnline = $false
}

# Test 2: Action item creation
Write-Host "[2/2] Testing action item creation via MCP..."
if ($serverOnline) {
    $testPayload = @{
        jsonrpc = "2.0"
        id = 1
        method = "requeue_task"
        params = @{
            title = "TEST: MCP action item"
            priority = "P2"
        }
    } | ConvertTo-Json

    try {
        $result = Invoke-RestMethod -Uri "$McpServerUri/mcp" -Method POST `
            -Headers @{"Content-Type"="application/json"} -Body $testPayload -TimeoutSec 5
        Write-Host "  PASS: Action items can be created via MCP"
    } catch {
        Write-Host "  FAIL: $($_.Exception.Message)"
    }
} else {
    Write-Host "  SKIP: Server not running"
}

Write-Host ""
Write-Host "=== RESULT ==="
Write-Host "Meta-orchestrator pattern requires MCP server running."
Write-Host "Future agents will use this to route follow-up work through the system."
