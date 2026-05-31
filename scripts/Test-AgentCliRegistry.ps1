# Validate 36 local agent slots, CLI registry, and no paid dispatch.
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..").Path
$agentsPath = Join-Path $Root "config\agents.json"
$registryPath = Join-Path $Root "config\agent-cli-registry.json"
$runner = Join-Path $Root "scripts\Start-LanternLocalAgentRing.ps1"
$proofPath = Join-Path $Root "manifests\validation\LIVE-FLEET-PROOF-LATEST.json"
$receiptDir = Join-Path $Root "data\automation\agent-ring"

$config = Get-Content $agentsPath -Raw | ConvertFrom-Json
$registry = Get-Content $registryPath -Raw | ConvertFrom-Json

$enabledSlots = @($config.slots | Where-Object { $_.enabled })
$registryAgents = @($registry.agents)
$badConfig = @($config.slots | Where-Object { $_.cli -ne "none" -or $_.tokenBudget -ne 0 -or $_.spendPolicy -ne "no_paid_api_calls" })
$badRegistry = @($registryAgents | Where-Object { $_.paidAccount -ne $false -or $_.network -ne $false -or $_.tokenBudget -ne 0 -or $_.dispatchMode -ne "local_receipt_only" })

& powershell -NoProfile -ExecutionPolicy Bypass -File $runner -RunOnce -RunLoopReceiptOnce | Out-Null
if ($LASTEXITCODE -ne 0) { throw "local agent ring runner failed" }

$proof = Get-Content $proofPath -Raw | ConvertFrom-Json
$receipts = @(Get-ChildItem -Path $receiptDir -Filter "ring-*.json" -File)
$receiptObjects = @($receipts | ForEach-Object { Get-Content $_.FullName -Raw | ConvertFrom-Json })
$badReceipt = @($receiptObjects | Where-Object { $_.paidDispatch -ne $false -or $_.tokenBudget -ne 0 -or $_.cli -ne "none" -or $_.workType -ne "convergence_step_receipt" })

$ok = (
    $enabledSlots.Count -eq 36 -and
    $registryAgents.Count -eq 36 -and
    $registry.paidCliDispatchAllowed -eq $false -and
    $badConfig.Count -eq 0 -and
    $badRegistry.Count -eq 0 -and
    $proof.ok -eq $true -and
    $proof.ringSlotsAssigned -eq 36 -and
    $proof.ringSlotsHealthy -eq 36 -and
    $proof.paidCliDispatchAllowed -eq $false -and
    $receipts.Count -eq 36 -and
    $badReceipt.Count -eq 0
)

$result = [ordered]@{
    ok = $ok
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    enabledSlots = $enabledSlots.Count
    registryAgents = $registryAgents.Count
    receipts = $receipts.Count
    badConfig = $badConfig.Count
    badRegistry = $badRegistry.Count
    badReceipt = $badReceipt.Count
    paidCliDispatchAllowed = $proof.paidCliDispatchAllowed
    claimBoundary = $proof.claimBoundary
}
$result | ConvertTo-Json -Depth 5
if (-not $ok) { exit 1 }
