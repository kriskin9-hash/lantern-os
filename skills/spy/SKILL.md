# !spy Skill — SPY Baseline Signal Engine

Status: research-first
Scope: SPY-focused signal generation and validation

## Mission

Create a deterministic baseline for SPY before attempting options, leverage, or broader universes.

SPY is treated as the reference instrument for validating Lantern OS intraday research.

## Core inputs

- SPY OHLCV
- VWAP
- Opening range high/low
- Volume profile
- VIX
- Economic calendar (CPI, FOMC, NFP)
- Previous day high/low
- Current day gap size

## Primary setups

### 1. VWAP Reclaim

Bullish:
- Price regains VWAP.
- Holds above VWAP.
- Volume confirms.

Bearish:
- Price loses VWAP.
- Holds below VWAP.
- Volume confirms.

### 2. Opening Range Breakout (ORB)

Bullish:
- Break and hold above opening range high.

Bearish:
- Break and hold below opening range low.

### 3. Gap Fade

Bullish:
- Gap down fails.
- Price reclaims key levels.

Bearish:
- Gap up fails.
- Price loses key levels.

## Signal scoring

| Component | Weight |
|---|---:|
| Regime alignment | 25 |
| VWAP status | 25 |
| Opening range status | 20 |
| Volume confirmation | 15 |
| VIX alignment | 10 |
| Calendar risk | 5 |

Maximum score: 100

## Confidence bands

| Score | Confidence |
|---:|---|
| 0-39 | Reject |
| 40-59 | Watch |
| 60-74 | Paper trade |
| 75-89 | Human review |
| 90-100 | Human review plus extra validation |

## Output

```yaml
skill: spy.baseline.signal.v1
symbol: SPY
regime: null
score: 0
confidence: reject
vwap_status: null
opening_range_status: null
volume_confirmation: false
vix_state: null
calendar_risk: null
direction_bias: bullish|bearish|neutral
action: reject|watch|paper_trade|human_review
```

## Hard rules

1. No live order generation.
2. No options recommendation without share-signal confirmation.
3. No trade during major calendar release windows unless specifically tested.
4. Every signal becomes a receipt.
5. Every receipt must include invalidation criteria.

## Success metric

The goal is not profit prediction.

The goal is producing a calibrated signal stream that survives:

- fees
- slippage
- drawdown review
- paper-trade validation
- human audit
