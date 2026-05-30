param(
    [string]$InputPath = "",
    [string]$OutputPath = "",
    [string]$ReceiptPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $InputPath) {
    $InputPath = Join-Path $repoRoot "data\kalshi\kalshi-near-term-paper-block-latest.json"
}
if (-not $OutputPath) {
    $OutputPath = Join-Path $repoRoot "data\kalshi\kalshi-near-term-paper-block-pl-latest.json"
}
if (-not $ReceiptPath) {
    $ReceiptPath = Join-Path $repoRoot "manifests\evidence\kalshi-near-term-paper-block-pl-receipt-2026-05-30.md"
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Text
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

function Get-MarketDetail {
    param([string]$Ticker)
    $uri = "https://external-api.kalshi.com/trade-api/v2/markets/$Ticker"
    return (Invoke-RestMethod -Uri $uri -TimeoutSec 15).market
}

if (-not (Test-Path -LiteralPath $InputPath)) {
    throw "Missing near-term paper block: $InputPath"
}

$block = Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json
$resolvedAt = (Get-Date).ToUniversalTime()
$rows = New-Object System.Collections.Generic.List[object]
$settledCount = 0
$openCount = 0
$unknownCount = 0
$totalPaperCostUsd = 0.0
$totalPaperPayoutUsd = 0.0
$totalPaperPnlUsd = 0.0
$nextCheckAfterUtc = $null

foreach ($order in @($block.orders)) {
    $detail = $null
    $marketStatus = "unknown"
    $marketResult = "unknown"
    $settlementValue = $null
    $paperCostUsd = [math]::Round([double]$order.paperMaxLossUsd, 2)
    $paperPayoutUsd = 0.0
    $paperPnlUsd = 0.0
    $paperOutcome = "unknown"

    try {
        $detail = Get-MarketDetail -Ticker $order.ticker
        $marketStatus = [string]$detail.status
        $marketResult = [string]$detail.result
        $settlementValue = [string]$detail.settlement_value_dollars
    } catch {
        $marketStatus = "fetch_failed"
        $marketResult = "unknown"
    }

    if ($marketStatus -in @("finalized", "settled") -and $marketResult -in @("yes", "no")) {
        $settledCount += 1
        if ($marketResult -eq "yes") {
            $paperPayoutUsd = 1.0
            $paperPnlUsd = [math]::Round(1.0 - $paperCostUsd, 2)
            $paperOutcome = "paper_win"
        } else {
            $paperPayoutUsd = 0.0
            $paperPnlUsd = -1 * $paperCostUsd
            $paperOutcome = "paper_loss"
        }
    } elseif ($marketStatus -in @("active", "initialized")) {
        $openCount += 1
        $paperOutcome = "unsettled"
        $candidateTime = $null
        foreach ($field in @("soonestKnownTime", "expectedExpirationTime", "closeTime")) {
            if ($order.$field) {
                try {
                    $candidateTime = ([datetimeoffset]::Parse([string]$order.$field)).UtcDateTime
                    break
                } catch {}
            }
        }
        if ($candidateTime -and ($null -eq $nextCheckAfterUtc -or $candidateTime -lt $nextCheckAfterUtc)) {
            $nextCheckAfterUtc = $candidateTime
        }
    } else {
        $unknownCount += 1
        $paperOutcome = "unknown"
    }

    $totalPaperCostUsd = [math]::Round($totalPaperCostUsd + $paperCostUsd, 2)
    $totalPaperPayoutUsd = [math]::Round($totalPaperPayoutUsd + $paperPayoutUsd, 2)
    $totalPaperPnlUsd = [math]::Round($totalPaperPnlUsd + $paperPnlUsd, 2)

    $rows.Add([ordered]@{
        ticker = $order.ticker
        title = $order.title
        paperLimitCents = $order.paperLimitCents
        paperCostUsd = $paperCostUsd
        marketStatus = $marketStatus
        marketResult = $marketResult
        settlementValueDollars = $settlementValue
        paperPayoutUsd = [math]::Round($paperPayoutUsd, 2)
        paperPnlUsd = [math]::Round($paperPnlUsd, 2)
        paperOutcome = $paperOutcome
    })
}

$summary = [ordered]@{
    schema = "lantern.kalshi.near_term_paper_pl.v1"
    resolvedAt = $resolvedAt.ToString("o")
    sourceGeneratedAt = $block.generatedAt
    boundary = "Paper P/L only. Public Kalshi market data, no authenticated request, no real order, no custody, no guaranteed profit, no investment advice."
    liveTradingStatus = "blocked"
    realMoneyUsd = 0
    paperOrderCount = $rows.Count
    settledCount = $settledCount
    openCount = $openCount
    unknownCount = $unknownCount
    totalPaperCostUsd = [math]::Round($totalPaperCostUsd, 2)
    totalPaperPayoutUsd = [math]::Round($totalPaperPayoutUsd, 2)
    totalPaperPnlUsd = [math]::Round($totalPaperPnlUsd, 2)
    nextCheckAfterUtc = if ($nextCheckAfterUtc) { $nextCheckAfterUtc.ToString("o") } else { $null }
    orders = $rows
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReceiptPath) | Out-Null
$json = $summary | ConvertTo-Json -Depth 8
Write-Utf8NoBom -Path $OutputPath -Text $json

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Kalshi Near-Term Paper P/L Receipt - 2026-05-30")
$lines.Add("")
$lines.Add("Status: paper-only public-data settlement check; live trading remains blocked.")
$lines.Add("")
$lines.Add("## Summary")
$lines.Add("")
$lines.Add("| Field | Value |")
$lines.Add("|---|---:|")
$lines.Add(("| Paper orders | {0} |" -f $rows.Count))
$lines.Add(("| Settled | {0} |" -f $settledCount))
$lines.Add(("| Open | {0} |" -f $openCount))
$lines.Add(("| Unknown | {0} |" -f $unknownCount))
$lines.Add(("| Paper cost | `${0:N2}` |" -f $totalPaperCostUsd))
$lines.Add(("| Paper payout | `${0:N2}` |" -f $totalPaperPayoutUsd))
$lines.Add(("| Paper P/L | `${0:N2}` |" -f $totalPaperPnlUsd))
$lines.Add(("| Real money spent | `${0:N2}` |" -f 0))
if ($nextCheckAfterUtc) {
    $lines.Add(("| Next check after | {0} |" -f $nextCheckAfterUtc.ToString("o")))
}
$lines.Add("")
$lines.Add("## Boundary")
$lines.Add("")
$lines.Add("- No authenticated Kalshi request was made.")
$lines.Add("- No real order was submitted.")
$lines.Add("- No custody, guaranteed profit, or investment advice is implied.")
$lines.Add("- Paper P/L assumes a YES paper buy at the recorded paper limit and `$1.00` gross payout if the market result is yes.")
$lines.Add("")
$lines.Add("## Orders")
$lines.Add("")
$lines.Add("| Ticker | Result | Cost | Payout | P/L | Outcome |")
$lines.Add("|---|---|---:|---:|---:|---|")
foreach ($row in @($rows.ToArray())) {
    $lines.Add(("| `{0}` | {1} | `${2:N2}` | `${3:N2}` | `${4:N2}` | {5} |" -f $row.ticker, $row.marketResult, $row.paperCostUsd, $row.paperPayoutUsd, $row.paperPnlUsd, $row.paperOutcome))
}
$lines.Add("")
$lines.Add("## Files")
$lines.Add("")
$lines.Add("| Artifact | Path |")
$lines.Add("|---|---|")
$lines.Add("| Paper P/L JSON | data/kalshi/kalshi-near-term-paper-block-pl-latest.json |")
$lines.Add("| Source paper block | data/kalshi/kalshi-near-term-paper-block-latest.json |")

Write-Utf8NoBom -Path $ReceiptPath -Text ($lines -join "`r`n")
$summary | ConvertTo-Json -Depth 8
