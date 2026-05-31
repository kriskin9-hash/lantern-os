# Validate the 36-slot local worker ring and no-paid-dispatch guard.
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..").Path
$runner = Join-Path $Root "scripts\Start-LanternLocalAgentRing.ps1"
$proofPath = Join-Path $Root "manifests\validation\LIVE-FLEET-PROOF-LATEST.json"
$receiptDir = Join-Path $Root "data\automation\agent-ring"

& powershell -NoProfile -ExecutionPolicy Bypass -File $runner -RunOnce | Out-Host
if ($LASTEXITCODE -ne 0) { throw "local agent ring runner failed" }

$proof = Get-Content $proofPath -Raw | ConvertFrom-Json
$receipts = @(Get-ChildItem -Path $receiptDir -Filter "ring-*.json" -File)
$badReceipt = @($receipts | ForEach-Object { Get-Content $_.FullName -Raw | ConvertFrom-Json } | Where-Object { $_.paidDispatch -ne $false -or $_.tokenBudget -ne 0 -or $_.cli -ne "none" })

$ok = ($proof.ok -eq $true -and $proof.ringSlotsAssigned -eq 36 -and $proof.ringSlotsHealthy -eq 36 -and $proof.paidCliDispatchAllowed -eq $false -and $receipts.Count -eq 36 -and $badReceipt.Count -eq 0)
$result = [ordered]@{
    ok = $ok
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    proofOk = $proof.ok
    ringSlotsAssigned = $proof.ringSlotsAssigned
    ringSlotsHealthy = $proof.ringSlotsHealthy
    receiptCount = $receipts.Count
    badReceiptCount = $badReceipt.Count
    paidCliDispatchAllowed = $proof.paidCliDispatchAllowed
    claimBoundary = $proof.claimBoundary
}
$result | ConvertTo-Json -Depth 5
if (-not $ok) { exit 1 }
