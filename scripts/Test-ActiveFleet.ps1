# Validate local active agent fleet configuration without dispatching paid CLIs.

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..").Path
$configPath = Join-Path $Root "config\agents.json"
$activeConfigPath = Join-Path $Root "config\active-processing.json"
$receiptPath = Join-Path $Root "manifests\validation\LIVE-FLEET-PROOF-LATEST.json"

Write-Host "=== Active Agent Fleet Config Test ===" -ForegroundColor Cyan

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$activeConfig = Get-Content $activeConfigPath -Raw | ConvertFrom-Json
$enabledSlots = @($config.slots | Where-Object { $_.enabled })
$paidSlots = @($config.slots | Where-Object { $_.cli -ne "none" -or $_.tokenBudget -ne 0 -or $_.spendPolicy -ne "no_paid_api_calls" })
$duplicateSlots = @($config.slots | Group-Object slot | Where-Object { $_.Count -gt 1 })
$duplicateNames = @($config.slots | Group-Object name | Where-Object { $_.Count -gt 1 })
$stepGroups = @($config.slots | Group-Object step | Where-Object { $_.Count -ne 3 })

$ok = (
    $config.designedRingSlots -eq 36 -and
    $enabledSlots.Count -eq 36 -and
    $activeConfig.activeProcessing.maxActiveSlots -eq 36 -and
    $activeConfig.activeProcessing.allowPaidCliDispatch -eq $false -and
    $paidSlots.Count -eq 0 -and
    $duplicateSlots.Count -eq 0 -and
    $duplicateNames.Count -eq 0 -and
    $stepGroups.Count -eq 0
)

$receipt = [ordered]@{
    schema = "lantern.live_fleet_proof.v1"
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    ok = $ok
    orchestratorBaseUrl = "local_config_only"
    mcpHealth = "not_observed"
    toolsVisible = @()
    workerPoolTarget = $config.poolTarget
    activeWorkers = 0
    idleWorkers = $enabledSlots.Count
    queuedJobs = 0
    failedWorkers = 0
    ringSlotsAssigned = $enabledSlots.Count
    ringSlotsHealthy = if ($ok) { $enabledSlots.Count } else { 0 }
    consensusReceipts = @()
    paidCliDispatchAllowed = $activeConfig.activeProcessing.allowPaidCliDispatch
    churnGuard = $config.paidAccountPolicy.churnGuard
    claimBoundary = "local_36_slot_config_ready_not_live_paid_cli_workers"
    failures = @(
        if ($config.designedRingSlots -ne 36) { "designedRingSlots_not_36" }
        if ($enabledSlots.Count -ne 36) { "enabled_slot_count_not_36" }
        if ($paidSlots.Count -ne 0) { "paid_cli_or_token_budget_configured" }
        if ($duplicateSlots.Count -ne 0) { "duplicate_slot_numbers" }
        if ($duplicateNames.Count -ne 0) { "duplicate_slot_names" }
        if ($stepGroups.Count -ne 0) { "steps_do_not_have_three_slots" }
        if ($activeConfig.activeProcessing.allowPaidCliDispatch -ne $false) { "paid_cli_dispatch_not_disabled" }
    )
}

$receipt | ConvertTo-Json -Depth 8 | Set-Content -Path $receiptPath -Encoding utf8
$receipt | ConvertTo-Json -Depth 8

if (-not $ok) { exit 1 }
