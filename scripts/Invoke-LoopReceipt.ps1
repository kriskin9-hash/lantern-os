param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$ReceiptDir = "manifests/evidence",
    [string]$LoopScript = "scripts/Invoke-LanternConvergenceLoop.ps1",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$receiptDirFull = Join-Path $Root $ReceiptDir
$loopScriptFull = Join-Path $Root $LoopScript

if (-not (Test-Path $loopScriptFull)) {
    Write-Error "Convergence loop script not found: $loopScriptFull"
    exit 1
}

Write-Host "=== Loop Receipt Generator ===" -ForegroundColor Cyan
Write-Host "Running convergence loop..." -ForegroundColor White

# Capture loop output
$rawOutput = & $loopScriptFull 2>&1
$exitCode  = $LASTEXITCODE

# Extract JSON block from output (loop emits JSON to stdout)
$jsonLines = $rawOutput | Where-Object { $_ -is [string] }
$jsonBlock = ($jsonLines -join "`n").Trim()

$loopResult = $null
try {
    $loopResult = $jsonBlock | ConvertFrom-Json
} catch {
    Write-Host "Warning: could not parse loop JSON output. Storing raw." -ForegroundColor Yellow
}

$stamp     = Get-Date -Format "yyyyMMdd-HHmmss"
$receiptId = "loop-receipt-$stamp"

$receipt = [ordered]@{
    receiptId       = $receiptId
    generatedAt     = (Get-Date).ToString("o")
    evidenceClass   = "convergence_loop_run"
    exitCode        = $exitCode
    passed          = ($exitCode -eq 0)
    issueCount      = if ($loopResult) { [int]$loopResult.issueCount } else { $null }
    nextAction      = if ($loopResult) { $loopResult.nextAction } else { $null }
    leadingIssues   = if ($loopResult) { $loopResult.leadingIssues } else { $null }
    held            = if ($loopResult) { $loopResult.held } else { $null }
    sourceRepos     = if ($loopResult) { $loopResult.sourceRepos } else { $null }
    rawOutputLines  = @($jsonLines)
    loopScript      = $LoopScript
    dryRun          = $DryRun.IsPresent
    boundary        = "Receipt is evidence only. No score updates applied here. Use Update-ArcReactorStatus.ps1 for confidence changes."
}

Write-Host ""
Write-Host "Loop exit code : $exitCode" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })
if ($loopResult) {
    Write-Host "Issues found   : $($loopResult.issueCount)" -ForegroundColor $(if ($loopResult.issueCount -eq 0) { "Green" } else { "Yellow" })
    Write-Host "Next action    : $($loopResult.nextAction)" -ForegroundColor White
}

if ($DryRun) {
    Write-Host "`n[DRY RUN] Would write receipt to $receiptDirFull\$receiptId.json" -ForegroundColor Yellow
    $receipt | ConvertTo-Json -Depth 8 | Write-Host
    exit 0
}

if (-not (Test-Path $receiptDirFull)) {
    New-Item -ItemType Directory -Path $receiptDirFull -Force | Out-Null
}

$receiptFile = Join-Path $receiptDirFull "$receiptId.json"
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptFile -Encoding UTF8

Write-Host "`nReceipt written: $receiptFile" -ForegroundColor Green

# Also update a LATEST pointer for easy diffing
$latestFile = Join-Path $receiptDirFull "loop-receipt-LATEST.json"
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $latestFile -Encoding UTF8
Write-Host "Latest updated : $latestFile" -ForegroundColor Green

exit $exitCode
