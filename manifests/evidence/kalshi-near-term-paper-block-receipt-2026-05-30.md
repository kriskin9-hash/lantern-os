# Kalshi Near-Term Paper Block Receipt - 2026-05-30

Status: near-term paper block executed locally; live trading remains blocked.

## Window

| Field | Value |
|---|---:|
| Window minutes | 20 |
| Markets pulled | 5000 |
| Candidates within window | 7 |
| Paper orders opened | 7 |
| Paper risk allocated | $1.55 |
| Real money spent | $0.00 |

## Boundary

- No authenticated Kalshi request was made.
- No real order was submitted.
- Only markets with a future known/expiry time inside the next window were eligible.
- Orders are paper maker limits at public YES bid and may be unfilled in simulation.

## Paper Block

| Rank | Ticker | Title | Limit | Max Loss | Minutes | Known Time | Status |
|---:|---|---|---:|---:|---:|---|---|
| 1 | KXSOL15M-26MAY300015-15 | SOL price up in next 15 mins? | 17c | $0.17 | 7.83 | 2026-05-30T04:15:00.0000000Z | paper_open_unfilled |
| 2 | KXETH15M-26MAY300015-15 | ETH price up in next 15 mins? | 6c | $0.06 | 7.83 | 2026-05-30T04:15:00.0000000Z | paper_open_unfilled |
| 3 | KXBTC15M-26MAY300015-15 | BTC price up in next 15 mins? | 6c | $0.06 | 7.83 | 2026-05-30T04:15:00.0000000Z | paper_open_unfilled |
| 4 | KXXRP15M-26MAY300015-15 | XRP price up in next 15 mins? | 11c | $0.11 | 7.83 | 2026-05-30T04:15:00.0000000Z | paper_open_unfilled |
| 5 | KXHYPE15M-26MAY300015-15 | HYPE price up in next 15 mins? | 8c | $0.08 | 7.83 | 2026-05-30T04:15:00.0000000Z | paper_open_unfilled |
| 6 | KXDOGE15M-26MAY300015-15 | DOGE price up in next 15 mins? | 13c | $0.13 | 7.83 | 2026-05-30T04:15:00.0000000Z | paper_open_unfilled |
| 7 | KXBNB15M-26MAY300015-15 | BNB price up in next 15 mins? | 94c | $0.94 | 7.83 | 2026-05-30T04:15:00.0000000Z | paper_open_unfilled |

## Files

| Artifact | Path |
|---|---|
| Near-term paper block JSON | data/kalshi/kalshi-near-term-paper-block-latest.json |