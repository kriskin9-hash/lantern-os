# Kalshi Selected Event Paper Order Receipt - 2026-05-30

Status: selected-event paper maker orders opened locally; live trading remains blocked.

## Event

| Field | Value |
|---|---|
| Event | Kansas City vs Texas |
| Subtitle | KC vs TEX (May 31) |
| Event ticker | KXMLBGAME-26MAY311435KCTEX |
| Market URL | https://kalshi.com/markets/kxmlbgame/professional-baseball-game/kxmlbgame-26may311435kctex |
| Mutually exclusive | True |

## Boundary

- No authenticated Kalshi request was made.
- No real order was submitted.
- Orders are paper maker limits at current public YES bid, so paper status is paper_open_unfilled until a simulated fill rule is added.
- Buying both sides at the ask would cross the spread and is rejected by this receipt.

## Paper Orders

| Rank | Ticker | Outcome | Bid | Ask | Paper Limit | Paper Max Loss | Close | Status |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | KXMLBGAME-26MAY311435KCTEX-KC | Kansas City | 0.47 | 0.49 | 47c | $0.47 | 2026-06-03T18:35:00Z | paper_open_unfilled |
| 2 | KXMLBGAME-26MAY311435KCTEX-TEX | Texas | 0.51 | 0.53 | 51c | $0.51 | 2026-06-03T18:35:00Z | paper_open_unfilled |

## Files

| Artifact | Path |
|---|---|
| Public event snapshot | data/kalshi/kalshi-selected-event-latest.json |
| Paper event orders | data/kalshi/kalshi-selected-event-paper-orders-latest.json |