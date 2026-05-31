<#
.SYNOPSIS
    Run the full Lantern OS automation test suite.

.DESCRIPTION
    Executes all automated tests including:
    - Python pytest suite
    - PowerShell script tests
    - MCP connector validation
    - Convergence loop validation
    - Trade chat unit tests

.PARAMETER TestCategory
    Specific test category to run (all, python, powershell, mcp, convergence, trade-chat)

.PARAMETER OutputPath
    Path to write test results JSON

.EXAMPLE
    .\scripts\Invoke-LanternAutomationTestSuite.ps1
#>
[CmdletBinding()]
param(
    [ValidateSet("all", "python", "powershell", "mcp", "convergence", "trade-chat")]
    [string]$TestCategory = "all",
    
    [string]$OutputPath = (Join-Path $PSScriptRoot ".." "manifests" "validation" "AUTOMATION-TEST-LATEST.json")
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$results = @{
    generatedAt = (Get-Date).ToString("o")
    testCategory = $TestCategory
    results = @{}
}

function Test-PythonSuite {
    Write-Host "Running Python pytest suite..." -ForegroundColor Cyan
    $pythonResult = python -m pytest tests -q --tb=no 2>&1
    $results.results.python = @{
        passed = $LASTEXITCODE -eq 0
        output = $pythonResult
        exitCode = $LASTEXITCODE
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Python tests failed" -ForegroundColor Red
    } else {
        Write-Host "Python tests passed" -ForegroundColor Green
    }
}

function Test-PowerShellSuite {
    Write-Host "Running PowerShell script tests..." -ForegroundColor Cyan
    $psTests = @(
        "Test-HotSwapVmReceipt.ps1",
        "Test-HouseThinker.ps1",
        "Test-SoloMiningSkill.ps1"
    )
    $psResults = @()
    foreach ($test in $psTests) {
        $testPath = Join-Path $PSScriptRoot $test
        if (Test-Path $testPath) {
            try {
                & $testPath
                $psResults += @{ test = $test; passed = $true }
            } catch {
                $psResults += @{ test = $test; passed = $false; error = $_.Exception.Message }
            }
        }
    }
    $results.results.powershell = @{
        tests = $psResults
        allPassed = ($psResults | Where-Object { -not $_.passed }).Count -eq 0
    }
}

function Test-McpConnector {
    Write-Host "Running MCP connector validation..." -ForegroundColor Cyan
    try {
        & (Join-Path $PSScriptRoot "Test-LanternMcpConnector.ps1") -OutputPath (Join-Path $repoRoot "manifests" "validation" "MCP-CONNECTOR-LATEST.json")
        $results.results.mcp = @{ passed = $true }
        Write-Host "MCP connector validation passed" -ForegroundColor Green
    } catch {
        $results.results.mcp = @{ passed = $false; error = $_.Exception.Message }
        Write-Host "MCP connector validation failed" -ForegroundColor Red
    }
}

function Test-ConvergenceLoop {
    Write-Host "Running convergence loop validation..." -ForegroundColor Cyan
    try {
        $loopResult = & (Join-Path $PSScriptRoot "Invoke-LanternConvergenceLoop.ps1") | ConvertFrom-Json
        $results.results.convergence = @{
            passed = $loopResult.issueCount -eq 0
            issueCount = $loopResult.issueCount
            nextAction = $loopResult.nextAction
        }
        if ($loopResult.issueCount -eq 0) {
            Write-Host "Convergence loop passed" -ForegroundColor Green
        } else {
            Write-Host "Convergence loop found $($loopResult.issueCount) issues" -ForegroundColor Yellow
        }
    } catch {
        $results.results.convergence = @{ passed = $false; error = $_.Exception.Message }
        Write-Host "Convergence loop validation failed" -ForegroundColor Red
    }
}

function Test-TradeChat {
    Write-Host "Running trade chat unit tests..." -ForegroundColor Cyan
    $tradeChatPath = Join-Path $repoRoot "apps" "lantern-trade-chat"
    if (Test-Path $tradeChatPath) {
        Push-Location $tradeChatPath
        try {
            python -m pytest tests -q --tb=no 2>&1
            $results.results.tradeChat = @{
                passed = $LASTEXITCODE -eq 0
                exitCode = $LASTEXITCODE
            }
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Trade chat tests passed" -ForegroundColor Green
            } else {
                Write-Host "Trade chat tests failed" -ForegroundColor Red
            }
        } finally {
            Pop-Location
        }
    } else {
        $results.results.tradeChat = @{ passed = $false; error = "Trade chat app not found" }
    }
}

# Run selected tests
switch ($TestCategory) {
    "all" {
        Test-PythonSuite
        Test-PowerShellSuite
        Test-McpConnector
        Test-ConvergenceLoop
        Test-TradeChat
    }
    "python" { Test-PythonSuite }
    "powershell" { Test-PowerShellSuite }
    "mcp" { Test-McpConnector }
    "convergence" { Test-ConvergenceLoop }
    "trade-chat" { Test-TradeChat }
}

# Write results
$outputDir = Split-Path $OutputPath -Parent
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}
$results | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputPath -Encoding utf8

Write-Host "`nTest results written to: $OutputPath" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor Cyan
foreach ($key in $results.results.Keys) {
    $passed = if ($null -ne $results.results[$key].passed) { $results.results[$key].passed } else { $results.results[$key].allPassed }
    $status = if ($passed) { "PASS" } else { "FAIL" }
    $color = if ($passed) { "Green" } else { "Red" }
    Write-Host "  $key : $status" -ForegroundColor $color
}

exit 0
