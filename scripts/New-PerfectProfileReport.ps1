param(
    [Parameter(Mandatory = $true)]
    [string]$PersonId,
    [Parameter(Mandatory = $true)]
    [string]$ReportTitle,
    [string]$Root = "",
    [string]$ProfilesDir = "profiles",
    [switch]$RenderPdf = $true
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$date = Get-Date -Format "yyyy-MM-dd"
$timestamp = (Get-Date).ToString("o")
$profilesPath = Join-Path $Root $ProfilesDir
$personPath = Join-Path $profilesPath $PersonId
$profileJson = Join-Path $personPath "profile.json"
$evolutionJsonl = Join-Path $personPath "report-evolution.jsonl"
$reportsDir = Join-Path $Root "reports"
$artifactsDir = Join-Path $Root "artifacts"

New-Item -ItemType Directory -Force -Path $personPath | Out-Null
New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null
New-Item -ItemType Directory -Force -Path $artifactsDir | Out-Null

if (-not (Test-Path -LiteralPath $profileJson)) {
    $defaultProfile = [ordered]@{
        personId = $PersonId
        displayName = $PersonId
        reportStyle = "founder_evidence_perfect"
        goals = @(
            "Increase decision quality with evidence",
            "Protect energy and execution consistency"
        )
        preferredSections = @(
            "Founder Signoff Line",
            "Executive Snapshot",
            "Wallet Truth",
            "Proven vs Planned",
            "Top Risks",
            "72-Hour Actions",
            "Decision"
        )
        evidencePaths = @(
            "data/wallet/local-cash-wallet.json",
            "data/wallet/ledger.jsonl",
            "manifests/validation/LANTERN-GARAGE-APP-LATEST.json"
        )
        styleReference = "C:/Users/alexp/Downloads/mookman11_p0_p3_perfect_closure.pdf"
    }
    ($defaultProfile | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $profileJson -Encoding UTF8
}

$profile = Get-Content -LiteralPath $profileJson -Raw | ConvertFrom-Json
$wallet = Get-Content -LiteralPath (Join-Path $Root "data/wallet/local-cash-wallet.json") -Raw | ConvertFrom-Json
$ledgerRaw = @()
if (Test-Path -LiteralPath (Join-Path $Root "data/wallet/ledger.jsonl")) {
    $ledgerRaw = Get-Content -LiteralPath (Join-Path $Root "data/wallet/ledger.jsonl") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
}
$latestEvent = "none"
if ($ledgerRaw.Count -gt 0) {
    try { $latestEvent = (($ledgerRaw[-1] | ConvertFrom-Json).event) } catch { $latestEvent = "parse_error" }
}
$clearedUsd = '$' + [string]$wallet.clearedCashUsd
$pendingUsd = '$' + [string]$wallet.pendingInvoiceUsd
$draftUsd = '$' + [string]$wallet.draftInvoiceUsd

$reportFile = "COMET-LEAP-{0}-PERFECT-REPORT-{1}.md" -f $PersonId.ToUpper(), $date
$reportPath = Join-Path $reportsDir $reportFile

$content = @"
# $ReportTitle

## Founder Signoff Line
$($profile.displayName) now has an updated !perfect report generated from their profile and live local evidence. Cleared cash remains factual at $clearedUsd and the latest ledger event is $latestEvent.

## Executive Snapshot
| Lane | Current State | Confidence | Evidence |
| --- | --- | --- | --- |
| Profile state | Profile-driven report structure is active | High | `profiles/$PersonId/profile.json` |
| Wallet state | Cleared $clearedUsd, pending $pendingUsd, draft $draftUsd | High | `data/wallet/local-cash-wallet.json` |
| Event stream | Latest event is $latestEvent | Medium-High | `data/wallet/ledger.jsonl` |
| Report pipeline | !perfect markdown-to-pdf pipeline available | High | `scripts/Build-PerfectArtPdf.ps1` |

## Wallet Truth
| Metric | Value |
| --- | --- |
| clearedCashUsd | $clearedUsd |
| pendingInvoiceUsd | $pendingUsd |
| draftInvoiceUsd | $draftUsd |

## Proven vs Planned
| Category | Proven Now | Planned Next |
| --- | --- | --- |
| Personalization | Profile exists for $PersonId | Tune section order and tone from usage feedback |
| Evolution | Persistent JSONL log tracks report generation | Add feedback scoring per section after each readout |
| Delivery | Markdown artifact generated now | Render and ship PDF packet each run |

## 72-Hour Actions
1. Add one profile-specific objective update to `profiles/$PersonId/profile.json`.
2. Record real outcome events in wallet ledger (sent, objection, cleared, refund).
3. Generate next report and compare deltas in evolution log.

## Decision
Keep this profile-evolving report loop active. Use local evidence first, then improve style and structure from each person-specific run.
"@

$content | Set-Content -LiteralPath $reportPath -Encoding UTF8

$evo = [ordered]@{
    timestamp = $timestamp
    personId = $PersonId
    reportTitle = $ReportTitle
    reportPath = ("reports/" + $reportFile)
    wallet = [ordered]@{
        clearedCashUsd = $wallet.clearedCashUsd
        pendingInvoiceUsd = $wallet.pendingInvoiceUsd
        draftInvoiceUsd = $wallet.draftInvoiceUsd
    }
    latestLedgerEvent = $latestEvent
}
($evo | ConvertTo-Json -Compress) | Add-Content -LiteralPath $evolutionJsonl -Encoding UTF8

if ($RenderPdf) {
    $pdfFile = [System.IO.Path]::GetFileNameWithoutExtension($reportFile) + ".pdf"
    $pdfOut = Join-Path $artifactsDir $pdfFile
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "scripts/Build-PerfectArtPdf.ps1") -Source ("reports/" + $reportFile) -Output ("artifacts/" + $pdfFile) | Out-Null
    $validator = Join-Path $Root "scripts/Validate-PerfectReportDesign.ps1"
    if (Test-Path -LiteralPath $validator) {
        powershell -NoProfile -ExecutionPolicy Bypass -File $validator -MarkdownPath ("reports/" + $reportFile) -PdfPath ("artifacts/" + $pdfFile) | Out-Null
    }
    Write-Output $pdfOut
}
else {
    Write-Output $reportPath
}
