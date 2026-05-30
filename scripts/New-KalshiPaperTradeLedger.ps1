param(
    [string]$InputTicketsPath = "",
    [string]$OutputPositionsPath = "",
    [string]$OutputLedgerPath = "",
    [string]$OutputReceiptPath = "",
    [switch]$AllowLive
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $InputTicketsPath) {
    $InputTicketsPath = Join-Path $repoRoot "data\kalshi\kalshi-paper-trade-tickets-latest.json"
}
if (-not $OutputPositionsPath) {
    $OutputPositionsPath = Join-Path $repoRoot "data\kalshi\kalshi-paper-positions-latest.json"
}
if (-not $OutputLedgerPath) {
    $OutputLedgerPath = Join-Path $repoRoot "data\kalshi\kalshi-paper-ledger.jsonl"
}
if (-not $OutputReceiptPath) {
    $OutputReceiptPath = Join-Path $repoRoot "manifests\evidence\kalshi-paper-trade-execution-receipt-2026-05-30.md"
}

if ($AllowLive) {
    throw "Live trading is blocked from this script. Paper execution only; use Kalshi UI/API manually outside repo after separate approval."
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Text
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

if (-not (Test-Path -LiteralPath $InputTicketsPath)) {
    throw "Missing paper ticket input: $InputTicketsPath"
}

$ticketData = Get-Content -Raw -LiteralPath $InputTicketsPath | ConvertFrom-Json
if ($ticketData.liveTradingStatus -ne "blocked") {
    throw "Paper ticket input must keep liveTradingStatus blocked."
}

$openedAt = (Get-Date).ToUniversalTime().ToString("o")
$positions = New-Object System.Collections.Generic.List[object]
$ledgerLines = New-Object System.Collections.Generic.List[string]
$positionRank = 0

foreach ($ticket in @($ticketData.tickets)) {
    if ($ticket.status -ne "paper_only_requires_human_approval") {
        continue
    }
    $positionRank += 1
    $positionId = "PAPER-KALSHI-{0:yyyyMMddHHmmss}-{1:000}" -f ([datetime]::Parse($openedAt).ToUniversalTime()), $positionRank
    $entry = [ordered]@{
        schema = "lantern.kalshi.paper_position.v1"
        positionId = $positionId
        openedAt = $openedAt
        mode = "paper_only"
        sourceTicketRank = $ticket.rank
        ticker = $ticket.ticker
        title = $ticket.title
        side = $ticket.side
        action = $ticket.action
        count = $ticket.count
        paperLimitCents = $ticket.suggestedLimitCents
        paperMaxLossUsd = $ticket.paperMaxLossUsd
        closeTime = $ticket.closeTime
        daysToCloseAtOpen = $ticket.daysToClose
        whenKnown = $ticket.whenKnown
        status = "paper_open"
        liveOrderStatus = "not_submitted"
        realMoneyUsd = 0
        blockers = $ticket.blockers
    }
    $positions.Add($entry) | Out-Null

    $ledgerLine = [ordered]@{
        ts = $openedAt
        event = "paper_position_opened"
        positionId = $positionId
        ticker = $ticket.ticker
        side = $ticket.side
        count = $ticket.count
        paperLimitCents = $ticket.suggestedLimitCents
        paperMaxLossUsd = $ticket.paperMaxLossUsd
        liveOrderStatus = "not_submitted"
    }
    $ledgerLines.Add(($ledgerLine | ConvertTo-Json -Compress -Depth 6)) | Out-Null
}

$allocatedPaperRiskUsd = 0.0
foreach ($position in @($positions.ToArray())) {
    $allocatedPaperRiskUsd += [double]$position.paperMaxLossUsd
}
$allocatedPaperRiskUsd = [math]::Round($allocatedPaperRiskUsd, 2)
$payload = [ordered]@{
    schema = "lantern.kalshi.paper_positions.v1"
    generatedAt = $openedAt
    boundary = "Paper positions only. No authenticated Kalshi request, no real order, no custody, no guaranteed profit, no investment advice."
    sourceTickets = $InputTicketsPath
    liveTradingStatus = "blocked"
    realMoneyUsd = 0
    positionCount = $positions.Count
    allocatedPaperRiskUsd = $allocatedPaperRiskUsd
    budgetPolicy = $ticketData.budgetPolicy
    positions = $positions
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPositionsPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputLedgerPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputReceiptPath) | Out-Null

Write-Utf8NoBom -Path $OutputPositionsPath -Text ($payload | ConvertTo-Json -Depth 10)
$ledgerText = ($ledgerLines -join "`n") + "`n"
[System.IO.File]::AppendAllText($OutputLedgerPath, $ledgerText, (New-Object System.Text.UTF8Encoding($false)))

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Kalshi Paper Trade Execution Receipt - 2026-05-30")
$lines.Add("")
$lines.Add("Status: paper positions opened locally; live trading remains blocked.")
$lines.Add("")
$lines.Add("## Boundary")
$lines.Add("")
$lines.Add("- No authenticated Kalshi request was made.")
$lines.Add("- No real order was submitted.")
$lines.Add("- No wallet custody, pooled money, guaranteed profit, or investment advice.")
$lines.Add("- Real-money execution requires separate manual approval in the Kalshi UI/API outside repo/RAG.")
$lines.Add("")
$lines.Add("## Paper Execution Summary")
$lines.Add("")
$lines.Add("| Field | Value |")
$lines.Add("|---|---:|")
$lines.Add(("| Paper positions opened | {0} |" -f $positions.Count))
$lines.Add(("| Paper risk allocated | `${0:N2}` |" -f $allocatedPaperRiskUsd))
$lines.Add(("| Real money spent | `${0:N2}` |" -f 0))
$lines.Add(("| Bankroll model | `${0:N2}` |" -f $ticketData.budgetPolicy.bankrollUsd))
$lines.Add(("| Daily paper loss cap | `${0:N2}` |" -f $ticketData.budgetPolicy.maxDailyPaperLossUsd))
$lines.Add("")
$lines.Add("## Open Paper Positions")
$lines.Add("")
$lines.Add("| Rank | Ticker | Side | Limit | Paper Max Loss | Close Time | Status |")
$lines.Add("|---:|---|---|---:|---:|---|---|")
foreach ($position in @($positions.ToArray())) {
    $lines.Add(("| {0} | `{1}` | {2} | {3}c | `${4:N2}` | {5} | {6} |" -f $position.sourceTicketRank, $position.ticker, $position.side, $position.paperLimitCents, $position.paperMaxLossUsd, $position.closeTime, $position.status))
}
$lines.Add("")
$lines.Add("## Files")
$lines.Add("")
$lines.Add("| Artifact | Path |")
$lines.Add("|---|---|")
$lines.Add("| Paper positions JSON | `data/kalshi/kalshi-paper-positions-latest.json` |")
$lines.Add("| Append-only paper ledger | `data/kalshi/kalshi-paper-ledger.jsonl` |")
$lines.Add("| Source tickets | `data/kalshi/kalshi-paper-trade-tickets-latest.json` |")

Write-Utf8NoBom -Path $OutputReceiptPath -Text ($lines -join "`n")
$payload | ConvertTo-Json -Depth 10
