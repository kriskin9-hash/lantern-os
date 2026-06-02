#Requires -Version 5.0
<#
.SYNOPSIS
    Test Lantern Orchestrator Dependency: MCP readiness, agent slots, and dispatch gates.

.DESCRIPTION
    Validates that the MCP server is running, all agent slots are registered,
    tool discovery is working, and the fleet is ready for dispatch.

    Safety gate: This script must pass before dispatch can be unlocked.

.PARAMETER MCP_SERVER_URL
    URL of the MCP server (default: http://127.0.0.1:8787)

.PARAMETER TIMEOUT_SECONDS
    Timeout for each health check (default: 10)

.EXAMPLE
    .\Test-LanternOrchestratorDependency.ps1
    .\Test-LanternOrchestratorDependency.ps1 -MCP_SERVER_URL "http://localhost:8787" -TIMEOUT_SECONDS 15
#>

param(
    [string]$MCP_SERVER_URL = "http://127.0.0.1:8787",
    [int]$TIMEOUT_SECONDS = 10
)

$ErrorActionPreference = "Continue"
$results = @{
    pass = @()
    fail = @()
    warn = @()
}

function Test-EndpointHealth {
    param(
        [string]$Url,
        [int]$Timeout
    )
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $Timeout -ErrorAction Stop
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Test-AgentSlots {
    param([string]$Url)
    $slots = @("claude", "codex", "gemini", "gpt")
    $registered = @()
    foreach ($slot in $slots) {
        $checkUrl = "$Url/agents/$slot/health"
        if (Test-EndpointHealth -Url $checkUrl -Timeout 5) {
            $registered += $slot
        }
    }
    return $registered
}

Write-Host "`n=== Lantern Orchestrator Dependency Validation ===" -ForegroundColor Cyan

# Test 1: MCP Server Online
Write-Host "`n[1/5] MCP Server Health..." -NoNewline
if (Test-EndpointHealth -Url "$MCP_SERVER_URL/health" -Timeout $TIMEOUT_SECONDS) {
    Write-Host " ✓ PASS" -ForegroundColor Green
    $results.pass += "MCP server responding"
} else {
    Write-Host " ✗ FAIL" -ForegroundColor Red
    $results.fail += "MCP server not responding at $MCP_SERVER_URL"
    exit 1
}

# Test 2: Agent Slots Registered
Write-Host "[2/5] Agent Slot Discovery..." -NoNewline
$registeredSlots = Test-AgentSlots -Url $MCP_SERVER_URL
if ($registeredSlots.Count -eq 4) {
    Write-Host " ✓ PASS (All 4 slots)" -ForegroundColor Green
    $results.pass += "All 4 agent slots registered: $($registeredSlots -join ', ')"
} else {
    Write-Host " ! WARN ($($registeredSlots.Count)/4 slots)" -ForegroundColor Yellow
    $results.warn += "$($registeredSlots.Count) of 4 slots registered: $($registeredSlots -join ', ')"
}

# Test 3: Tool Discovery
Write-Host "[3/5] Tool Registry..." -NoNewline
try {
    $toolsUrl = "$MCP_SERVER_URL/tools/list"
    $toolsResponse = Invoke-WebRequest -Uri $toolsUrl -TimeoutSec 5 -ErrorAction Stop
    $toolCount = ($toolsResponse.Content | ConvertFrom-Json).tools.Count
    if ($toolCount -gt 0) {
        Write-Host " ✓ PASS ($toolCount tools)" -ForegroundColor Green
        $results.pass += "Tool discovery working ($toolCount tools available)"
    } else {
        Write-Host " ! WARN (0 tools)" -ForegroundColor Yellow
        $results.warn += "Tool registry is empty; pending agent registration"
    }
} catch {
    Write-Host " ! WARN (discovery unavailable)" -ForegroundColor Yellow
    $results.warn += "Tool discovery endpoint not yet available"
}

# Test 4: Stale Slot Cleanup
Write-Host "[4/5] Stale Slot Cleanup..." -NoNewline
try {
    $cleanupUrl = "$MCP_SERVER_URL/orchestrator/stale-slots"
    if (Test-EndpointHealth -Url $cleanupUrl -Timeout 5) {
        Write-Host " ✓ PASS" -ForegroundColor Green
        $results.pass += "Stale slot cleanup functional"
    } else {
        Write-Host " ! WARN (not yet active)" -ForegroundColor Yellow
        $results.warn += "Stale slot cleanup not yet active"
    }
} catch {
    Write-Host " ! INFO (expected during rebuild)" -ForegroundColor Yellow
    $results.warn += "Stale slot cleanup check skipped (expected during rebuild)"
}

# Test 5: Dispatch Gate Status
Write-Host "[5/5] Dispatch Gate Authorization..." -NoNewline
if ($registeredSlots.Count -eq 4) {
    Write-Host " ✓ PASS (Ready to unlock)" -ForegroundColor Green
    $results.pass += "Dispatch gate ready to unlock (all slots registered)"
} else {
    Write-Host " ✗ HELD (Waiting for slots)" -ForegroundColor Red
    $results.fail += "Dispatch gate held: $($registeredSlots.Count) of 4 slots must register"
}

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $($results.pass.Count)" -ForegroundColor Green
Write-Host "Warnings: $($results.warn.Count)" -ForegroundColor Yellow
Write-Host "Failed: $($results.fail.Count)" -ForegroundColor Red

Write-Host "`nDetails:" -ForegroundColor Cyan
$results.pass | ForEach-Object { Write-Host "  ✓ $_" -ForegroundColor Green }
$results.warn | ForEach-Object { Write-Host "  ! $_" -ForegroundColor Yellow }
$results.fail | ForEach-Object { Write-Host "  ✗ $_" -ForegroundColor Red }

$status = if ($results.fail.Count -eq 0 -and $registeredSlots.Count -eq 4) {
    "READY FOR DISPATCH"
} elseif ($results.fail.Count -eq 0) {
    "FLEET REBUILD IN PROGRESS"
} else {
    "VALIDATION FAILED"
}

Write-Host "`nStatus: $status`n" -ForegroundColor $(if ($status -eq "READY FOR DISPATCH") { "Green" } elseif ($status -eq "VALIDATION FAILED") { "Red" } else { "Yellow" })

exit $(if ($results.fail.Count -eq 0) { 0 } else { 1 })
