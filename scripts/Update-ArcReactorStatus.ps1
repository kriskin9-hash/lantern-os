param(
    [Parameter(Mandatory = $true, HelpMessage = "Evidence string matching one entry in raisesMovie2 or raisesHumanTrial")]
    [string[]]$Evidence,
    [string]$StatusPath = "data/arc-reactor/status.json",
    [string]$ReceiptDir = "manifests/evidence",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$statusFile = Join-Path $root $StatusPath
$receiptDirFull = Join-Path $root $ReceiptDir

if (-not (Test-Path $statusFile)) {
    Write-Error "status.json not found at $statusFile"
    exit 1
}

$status = Get-Content -LiteralPath $statusFile -Raw | ConvertFrom-Json

$movie2Before = [int]$status.movie2PublicPlatformConfidence
$trialBefore  = [int]$status.humanTrialDemoReadiness

$matched        = [System.Collections.Generic.List[string]]::new()
$unmatched      = [System.Collections.Generic.List[string]]::new()
$movie2Triggers = [System.Collections.Generic.List[string]]::new()
$trialTriggers  = [System.Collections.Generic.List[string]]::new()

foreach ($ev in $Evidence) {
    $evLower = $ev.ToLower()
    $hit = $false

    foreach ($gate in $status.raisesMovie2) {
        if ($gate.ToLower() -like "*$evLower*" -or $evLower -like "*$($gate.ToLower().Substring(0, [Math]::Min(20, $gate.Length)))*") {
            $movie2Triggers.Add($gate) | Out-Null
            $matched.Add($ev) | Out-Null
            $hit = $true
            break
        }
    }

    if (-not $hit) {
        foreach ($gate in $status.raisesHumanTrial) {
            if ($gate.ToLower() -like "*$evLower*" -or $evLower -like "*$($gate.ToLower().Substring(0, [Math]::Min(20, $gate.Length)))*") {
                $trialTriggers.Add($gate) | Out-Null
                $matched.Add($ev) | Out-Null
                $hit = $true
                break
            }
        }
    }

    if (-not $hit) {
        $unmatched.Add($ev) | Out-Null
    }
}

# Score increments: each matched movie2 gate = +2 points (cap 100), each trial gate = +3
$movie2Increment = $movie2Triggers.Count * 2
$trialIncrement  = $trialTriggers.Count * 3

$movie2After = [Math]::Min(100, $movie2Before + $movie2Increment)
$trialAfter  = [Math]::Min(100, $trialBefore  + $trialIncrement)

$brierReceipt = [ordered]@{
    generatedAt         = (Get-Date).ToString("o")
    evidenceClass       = "arc_reactor_status_update"
    evidenceProvided    = @($Evidence)
    matchedGates        = @($matched)
    unmatchedEvidence   = @($unmatched)
    movie2GatesTriggered = @($movie2Triggers)
    trialGatesTriggered  = @($trialTriggers)
    before = [ordered]@{
        movie2PublicPlatformConfidence = $movie2Before
        humanTrialDemoReadiness        = $trialBefore
    }
    after = [ordered]@{
        movie2PublicPlatformConfidence = $movie2After
        humanTrialDemoReadiness        = $trialAfter
    }
    delta = [ordered]@{
        movie2 = $movie2After - $movie2Before
        trial  = $trialAfter  - $trialBefore
    }
    dryRun = $DryRun.IsPresent
    boundary = "Scores rise only from evidence receipts and observed outcomes. ASI patterns remain architecture references, not capability claims."
}

Write-Host "`n=== Arc Reactor Status Update ===" -ForegroundColor Cyan
Write-Host "Evidence provided : $($Evidence.Count)" -ForegroundColor White
Write-Host "Matched gates     : $($matched.Count)" -ForegroundColor Green
if ($unmatched.Count -gt 0) {
    Write-Host "Unmatched evidence: $($unmatched.Count) (no score change)" -ForegroundColor Yellow
    foreach ($u in $unmatched) { Write-Host "  - $u" -ForegroundColor Yellow }
}
Write-Host ""
Write-Host "Movie 2 confidence: $movie2Before -> $movie2After (+$($movie2After - $movie2Before))" -ForegroundColor Cyan
Write-Host "Human trial ready : $trialBefore -> $trialAfter (+$($trialAfter - $trialBefore))" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`n[DRY RUN] No files written." -ForegroundColor Yellow
    $brierReceipt | ConvertTo-Json -Depth 6 | Write-Host
    exit 0
}

# Write updated status.json
$status.movie2PublicPlatformConfidence = $movie2After
$status.humanTrialDemoReadiness        = $trialAfter
$status.lastUpdatedAt                  = (Get-Date).ToString("o")
$status.lastEvidenceApplied            = @($Evidence)

$status | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statusFile -Encoding UTF8
Write-Host "`nUpdated $statusFile" -ForegroundColor Green

# Write Brier receipt
if (-not (Test-Path $receiptDirFull)) {
    New-Item -ItemType Directory -Path $receiptDirFull -Force | Out-Null
}
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$receiptFile = Join-Path $receiptDirFull "arc-reactor-update-$stamp.json"
$brierReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptFile -Encoding UTF8
Write-Host "Receipt written : $receiptFile" -ForegroundColor Green

exit 0
