# Kalshi Near-Term Paper Block Receipt - 2026-05-30

Status: near-term paper block executed locally; live trading remains blocked.

## Window

| Field | Value |
|---|---:|
| Window minutes | 20 |
| Markets pulled | 5000 |
| Candidates within window | 9 |
| Paper orders opened | 8 |
| Paper risk allocated | $4.76 |
| Real money spent | $0.00 |

## Boundary

- No authenticated Kalshi request was made.
- No real order was submitted.
- Only markets with a future known/expiry time inside the next window were eligible.
- Orders are paper maker limits at public YES bid and may be unfilled in simulation.

## Paper Block

| Rank | Ticker | Title | Limit | Max Loss | Minutes | Known Time | Status |
|---:|---|---|---:|---:|---:|---|---|
| 1 | KXAAAGASD-26MAY30-4.345 | Will average **gas prices** be above $4.345? | 40c | $0.40 | 1.63 | 2026-05-30T03:59:00.0000000Z | paper_open_unfilled |
| 2 | KXAAAGASD-26MAY30-4.340 | Will average **gas prices** be above $4.340? | 93c | $0.93 | 1.63 | 2026-05-30T03:59:00.0000000Z | paper_open_unfilled |
| 3 | KXAAAGASD-26MAY30-4.355 | Will average **gas prices** be above $4.355? | 18c | $0.18 | 1.63 | 2026-05-30T03:59:00.0000000Z | paper_open_unfilled |
| 4 | KXAAAGASD-26MAY30-4.350 | Will average **gas prices** be above $4.350? | 42c | $0.42 | 1.63 | 2026-05-30T03:59:00.0000000Z | paper_open_unfilled |
| 5 | KXNCAABBGAME-26MAY292000NIHCCC-CCC | Northern Illinois vs Coastal Carolina winner? | 14c | $0.14 | 2.63 | 2026-05-30T04:00:00.0000000Z | paper_open_unfilled |
| 6 | KXSPOTIFYD-26MAY29-HAT | Top USA Song on Spotify on May 29, 2026? | 96c | $0.96 | 1.63 | 2026-05-30T03:59:00.0000000Z | paper_open_unfilled |
| 7 | KXTEMPNYCH-26MAY3000-T69.99 | Will the temp in New York City be above 69.99Â° on May 30, 2026 at 12am EDT? | 97c | $0.97 | 2.63 | 2026-05-30T04:00:00.0000000Z | paper_open_unfilled |
| 8 | KXNCAABBGAME-26MAY292000NIHCCC-NIH | Northern Illinois vs Coastal Carolina winner? | 76c | $0.76 | 2.63 | 2026-05-30T04:00:00.0000000Z | paper_open_unfilled |

## Files

| Artifact | Path |
|---|---|
| Near-term paper block JSON | data/kalshi/kalshi-near-term-paper-block-latest.json |