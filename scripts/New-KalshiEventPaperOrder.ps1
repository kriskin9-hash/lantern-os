param(
    [string]$EventTicker = "KXMLBGAME-26MAY311435KCTEX",
    [string]$MarketUrl = "https://kalshi.com/markets/kxmlbgame/professional-baseball-game/kxmlbgame-26may311435kctex",
    [double]$BudgetUsd = 50.0,
    [double]$MaxDailyLossPct = 0.10,
    [double]$MaxPerOrderLossPct = 0.02,
    [string]$OutputEventPath = "",
    [string]$OutputOrdersPath = "",
    [string]$OutputReceiptPath = "",
    [switch]$AllowLive
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutputEventPath) {
    $OutputEventPath = Join-Path $repoRoot "data\kalshi\kalshi-selected-event-latest.json"
}
if (-not $OutputOrdersPath) {
    $OutputOrdersPath = Join-Path $repoRoot "data\kalshi\kalshi-selected-event-paper-orders-latest.json"
}
if (-not $OutputReceiptPath) {
    $OutputReceiptPath = Join-Path $repoRoot "manifests\evidence\kalshi-selected-event-paper-order-receipt-2026-05-30.md"
}

if ($AllowLive) {
    throw "Live trading is blocked from this script. This creates paper maker orders only; real orders require separate manual operator action outside repo/RAG."
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Text
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

function Convert-DollarString {
    param([object]$Value)
    if ($null -eq $Value) { return $null }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    return [double]::Parse($text, [System.Globalization.CultureInfo]::InvariantCulture)
}

$apiUrl = "https://external-api.kalshi.com/trade-api/v2/events/$($EventTicker.ToUpperInvariant())?with_nested_markets=true"
$response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 20
$event = $response.event
$markets = @($event.markets)
if ($markets.Count -eq 0) {
    throw "No public nested markets found for event ticker: $EventTicker"
}

$fetchedAt = (Get-Date).ToUniversalTime().ToString("o")
$maxDailyPaperLossUsd = [math]::Round($BudgetUsd * $MaxDailyLossPct, 2)
$maxPerOrderPaperLossUsd = [math]::Round($BudgetUsd * $MaxPerOrderLossPct, 2)
$allocatedPaperRiskUsd = 0.0
$orders = New-Object System.Collections.Generic.List[object]
$rank = 0

foreach ($market in @($markets | Where-Object { $_.status -eq "active" })) {
    $bid = Convert-DollarString $market.yes_bid_dollars
    $ask = Convert-DollarString $market.yes_ask_dollars
    if ($null -eq $bid -or $bid -le 0) { continue }
    $limitCents = [int][math]::Floor($bid * 100)
    $paperMaxLossUsd = [math]::Round($limitCents / 100.0, 2)
    if ($paperMaxLossUsd -gt $maxPerOrderPaperLossUsd) { continue }
    if (($allocatedPaperRiskUsd + $paperMaxLossUsd) -gt $maxDailyPaperLossUsd) { continue }

    $rank += 1
    $allocatedPaperRiskUsd = [math]::Round($allocatedPaperRiskUsd + $paperMaxLossUsd, 2)
    $spread = if ($null -ne $ask -and $ask -ge $bid) { [math]::Round($ask - $bid, 4) } else { $null }
    $mid = if ($null -ne $ask -and $ask -ge $bid) { [math]::Round(($ask + $bid) / 2, 4) } else { $bid }
    $orders.Add([ordered]@{
        rank = $rank
        eventTicker = $event.event_ticker
        ticker = $market.ticker
        title = $market.title
        yesSubTitle = $market.yes_sub_title
        side = "yes"
        action = "paper_buy_limit_maker"
        orderStatus = "paper_open_unfilled"
        count = 1
        paperLimitCents = $limitCents
        paperMaxLossUsd = $paperMaxLossUsd
        yesBid = $bid
        yesAsk = $ask
        yesMid = $mid
        spread = $spread
        openInterest = Convert-DollarString $market.open_interest_fp
        volume24h = Convert-DollarString $market.volume_24h_fp
        closeTime = $market.close_time
        expectedExpirationTime = $market.expected_expiration_time
        rulesPrimary = $market.rules_primary
        rulesSecondary = $market.rules_secondary
        liveOrderStatus = "not_submitted"
        realMoneyUsd = 0
        outcomeConfidence = "not_estimated"
        blocker = "no_independent_posterior_probability_no_live_execution"
    }) | Out-Null
}

$eventPayload = [ordered]@{
    schema = "lantern.kalshi.selected_event_public_snapshot.v1"
    generatedAt = $fetchedAt
    eventTicker = $event.event_ticker
    title = $event.title
    subTitle = $event.sub_title
    category = $event.category
    marketUrl = $MarketUrl
    apiUrl = $apiUrl
    mutuallyExclusive = $event.mutually_exclusive
    boundary = "Public data snapshot only. No authenticated Kalshi request and no real order."
    markets = $markets
}

$orderPayload = [ordered]@{
    schema = "lantern.kalshi.event_paper_orders.v1"
    generatedAt = $fetchedAt
    eventTicker = $event.event_ticker
    marketUrl = $MarketUrl
    boundary = "Paper maker orders only. No authenticated Kalshi request, no real order, no custody, no guaranteed profit, no investment advice."
    liveTradingStatus = "blocked"
    realMoneyUsd = 0
    budgetPolicy = [ordered]@{
        bankrollUsd = $BudgetUsd
        maxDailyPaperLossPct = $MaxDailyLossPct
        maxDailyPaperLossUsd = $maxDailyPaperLossUsd
        maxPerOrderPaperLossPct = $MaxPerOrderLossPct
        maxPerOrderPaperLossUsd = $maxPerOrderPaperLossUsd
        allocatedPaperRiskUsd = $allocatedPaperRiskUsd
        remainingDailyPaperRiskUsd = [math]::Round([math]::Max(0, $maxDailyPaperLossUsd - $allocatedPaperRiskUsd), 2)
        liveSpendUsd = 0
    }
    paperOrderCount = $orders.Count
    orders = $orders
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputEventPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputOrdersPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputReceiptPath) | Out-Null
Write-Utf8NoBom -Path $OutputEventPath -Text ($eventPayload | ConvertTo-Json -Depth 10)
Write-Utf8NoBom -Path $OutputOrdersPath -Text ($orderPayload | ConvertTo-Json -Depth 10)

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Kalshi Selected Event Paper Order Receipt - 2026-05-30")
$lines.Add("")
$lines.Add("Status: selected-event paper maker orders opened locally; live trading remains blocked.")
$lines.Add("")
$lines.Add("## Event")
$lines.Add("")
$lines.Add("| Field | Value |")
$lines.Add("|---|---|")
$lines.Add(("| Event | {0} |" -f $event.title))
$lines.Add(("| Subtitle | {0} |" -f $event.sub_title))
$lines.Add(("| Event ticker | `{0}` |" -f $event.event_ticker))
$lines.Add(("| Market URL | {0} |" -f $MarketUrl))
$lines.Add(("| Mutually exclusive | {0} |" -f $event.mutually_exclusive))
$lines.Add("")
$lines.Add("## Boundary")
$lines.Add("")
$lines.Add("- No authenticated Kalshi request was made.")
$lines.Add("- No real order was submitted.")
$lines.Add("- Orders are paper maker limits at current public YES bid, so paper status is `paper_open_unfilled` until a simulated fill rule is added.")
$lines.Add("- Buying both sides at the ask would cross the spread and is rejected by this receipt.")
$lines.Add("")
$lines.Add("## Paper Orders")
$lines.Add("")
$lines.Add("| Rank | Ticker | Outcome | Bid | Ask | Paper Limit | Paper Max Loss | Close | Status |")
$lines.Add("|---:|---|---|---:|---:|---:|---:|---|---|")
foreach ($order in @($orders.ToArray())) {
    $lines.Add(("| {0} | `{1}` | {2} | {3:N2} | {4:N2} | {5}c | `${6:N2}` | {7} | {8} |" -f $order.rank, $order.ticker, $order.yesSubTitle, $order.yesBid, $order.yesAsk, $order.paperLimitCents, $order.paperMaxLossUsd, $order.closeTime, $order.orderStatus))
}
$lines.Add("")
$lines.Add("## Files")
$lines.Add("")
$lines.Add("| Artifact | Path |")
$lines.Add("|---|---|")
$lines.Add("| Public event snapshot | `data/kalshi/kalshi-selected-event-latest.json` |")
$lines.Add("| Paper event orders | `data/kalshi/kalshi-selected-event-paper-orders-latest.json` |")

Write-Utf8NoBom -Path $OutputReceiptPath -Text ($lines -join "`n")
$orderPayload | ConvertTo-Json -Depth 10
