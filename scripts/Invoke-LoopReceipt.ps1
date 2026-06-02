param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$LoopJsonPath = "",
    [string]$OutDir = "manifests/validation",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$outPath = Join-Path $Root $OutDir
if (-not (Test-Path -LiteralPath $outPath)) {
    New-Item -ItemType Directory -Path $outPath -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-ddTHH-mm-ss"
$receiptFile = Join-Path $outPath "LOOP-RECEIPT-$timestamp.json"

$loopResult = $null
if ($LoopJsonPath -and (Test-Path -LiteralPath $LoopJsonPath)) {
    $loopResult = Get-Content -LiteralPath $LoopJsonPath -Raw | ConvertFrom-Json
} else {
    # Build a minimal receipt from current repo state
    $loopResult = [pscustomobject]@{
        generatedAt = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
        mode = "local"
        method = "Lantern OS 12-step convergence loop"
        note = "Receipt generated without external loop JSON."
    }
}

$receipt = [pscustomobject]@{
    generatedAt = (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz")
    receiptFor = "Lantern OS Convergence Loop"
    loopResult = $loopResult
    root = $Root
    operatorApprovalRequired = $true
    nextAction = "Review loop issues, fix first 2-4, rerun."
}

$json = $receipt | ConvertTo-Json -Depth 10

if ($DryRun) {
    Write-Host "=== Dry Run ===" -ForegroundColor Yellow
    Write-Host $json
} else {
    Set-Content -LiteralPath $receiptFile -Value $json -Encoding UTF8
    Write-Host "Loop receipt written: $receiptFile" -ForegroundColor Green
}
