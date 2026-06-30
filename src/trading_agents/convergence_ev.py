"""
convergence_ev.py — Σ₀ expected-value decision layer over Riley's signals.

Riley's WAIT/GOOD/PERFECT tiers and "extreme-zones-only" gates exist to manage
HUMAN error — they keep a discretionary trader from overtrading and from acting
on partial confirmation. Keystone doesn't need that crutch: it can weigh every
piece of evidence at once and act on EXPECTED VALUE.

This module turns a candidate trade into a Convergence Record (one of Keystone's
four core objects):  hypothesis + evidence + confidence + result.  Riley's
detectors (zone, 1-min structure shift, candle pattern, trend) stay — but as
WEIGHTED EVIDENCE, not pass/fail gates. The decision is:

    p_win   = base_rate + Σ wᵢ·(signalᵢ − 0.5)        # transparent linear model
    EV (R)  = p_win·target_R − (1 − p_win)·1R          # risk one R to make target_R
    ENTER   iff EV ≥ EV_MIN and p_win ≥ P_MIN          # no discretionary tiers

Every record carries `why` (the evidence that moved it) so the call is auditable
— the External-Reality Rule: [claim, evidence, confidence, source]. Pure +
dependency-free so it unit-tests without Alpaca or the rest of the engine.
"""

from __future__ import annotations

# Evidence weights. Each signal is normalised to [0,1] where 0.5 = neutral; the
# weight is how many probability-points a fully-confirming signal (1.0) adds.
# Tunable via the engine; they need not sum to 1 (p_win is clamped).
WEIGHTS = {
    "llm":       0.18,   # Grok/Claude directional conviction
    "zone":      0.14,   # at a real S/R zone, scaled by strength/touches
    "structure": 0.16,   # 1-min structure shift confirmed (the key Riley trigger)
    "pattern":   0.12,   # A/B/C candle pattern grade
    "trend":     0.10,   # higher-tf trend agrees with the trade direction
    "news":      0.10,   # ticker news sentiment agrees with direction
    "backtest":  0.00,   # folded into base_rate instead (see below)
}

EV_MIN = 0.15   # require ≥ +0.15R edge after costs to act
P_MIN  = 0.45   # and at least a 45% hit-rate, so a huge target can't carry junk
P_CLAMP = (0.05, 0.95)


def _clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def _grade_to_signal(grade):
    return {"A": 1.0, "B": 0.75, "C": 0.6}.get(str(grade or "").upper(), 0.5)


def score_convergence(ev: dict) -> dict:
    """
    Score one candidate trade. `ev` (all optional, neutral defaults):
      direction:        "BULLISH" | "BEARISH"
      llm_conf:         0..100   Grok/Claude confidence
      in_zone:          bool
      zone_strength:    0..100
      zone_touches:     int
      structure_shifted:bool
      structure_conf:   0..100
      pattern_grade:    "A"|"B"|"C"|None
      trend_aligned:    bool      higher-tf trend matches direction
      trend_conflicts:  bool      higher-tf trend OPPOSES direction (counter-trend)
      news_sentiment:   -1..1     +ve = bullish news (signed to direction below)
      backtest_winrate: 0..1      historical hit-rate of this setup (base rate)
      target_r:         float     reward/risk multiple (tp% / |stop%|)

    Returns: {p_win, ev_r, target_r, decision: "ENTER"|"SKIP", signals, why, record}
    """
    direction = str(ev.get("direction", "NEUTRAL")).upper()
    target_r = float(ev.get("target_r") or 2.0)

    # ── Normalise each piece of evidence to [0,1] (0.5 = neutral) ──────────────
    llm = _clamp((float(ev.get("llm_conf", 50)) / 100.0), 0.0, 1.0)

    if ev.get("in_zone"):
        strength = _clamp(float(ev.get("zone_strength", 50)) / 100.0, 0.0, 1.0)
        touch_bonus = min(0.15, 0.05 * max(0, int(ev.get("zone_touches", 0)) - 1))
        zone = _clamp(0.5 + 0.5 * strength + touch_bonus, 0.0, 1.0)
    else:
        zone = 0.4  # not at a level — mild negative, not disqualifying

    if ev.get("structure_shifted"):
        structure = _clamp(0.6 + 0.4 * (float(ev.get("structure_conf", 60)) / 100.0), 0.0, 1.0)
    else:
        structure = 0.45

    pattern = _grade_to_signal(ev.get("pattern_grade"))

    if ev.get("trend_conflicts"):
        trend = 0.2          # fighting the higher-tf trend
    elif ev.get("trend_aligned"):
        trend = 0.85
    else:
        trend = 0.5

    # News sentiment is signed to the trade direction: bullish news helps a long,
    # hurts a short. Magnitude in [0,1] from |sentiment|.
    raw_news = _clamp(float(ev.get("news_sentiment", 0.0)), -1.0, 1.0)
    signed = raw_news if direction == "BULLISH" else -raw_news if direction == "BEARISH" else 0.0
    news = _clamp(0.5 + 0.5 * signed, 0.0, 1.0)

    signals = {"llm": llm, "zone": zone, "structure": structure,
               "pattern": pattern, "trend": trend, "news": news}

    # ── p_win = base_rate + Σ wᵢ·(signalᵢ − 0.5) ──────────────────────────────
    base_rate = _clamp(float(ev.get("backtest_winrate", 0.5)), 0.2, 0.8)
    p = base_rate
    for k, s in signals.items():
        p += WEIGHTS.get(k, 0.0) * (s - 0.5) * 2.0  # ×2 → a full signal moves ~1·weight
    p_win = _clamp(p, *P_CLAMP)

    ev_r = p_win * target_r - (1.0 - p_win) * 1.0

    # External-Reality Rule: nothing is accepted without evidence. A bare +EV from
    # an optimistic reward:risk is NOT enough — require at least ONE grounding
    # signal (a real level, a structure shift, a pattern, trend agreement, or a
    # meaningful news lean). This replaces Riley's WAIT/PERFECT discipline tiers
    # with a single evidence floor, not a checklist.
    has_evidence = (
        bool(ev.get("in_zone"))
        or bool(ev.get("structure_shifted"))
        or _grade_to_signal(ev.get("pattern_grade")) > 0.5
        or bool(ev.get("trend_aligned"))
        or abs(raw_news) >= 0.2
    )
    decision = "ENTER" if (has_evidence and ev_r >= EV_MIN and p_win >= P_MIN) else "SKIP"

    # ── Evidence string: the signals that pulled the decision, strongest first ──
    contrib = sorted(
        ((k, WEIGHTS.get(k, 0.0) * (s - 0.5)) for k, s in signals.items()),
        key=lambda kv: abs(kv[1]), reverse=True,
    )
    label = {"llm": "LLM conviction", "zone": "zone", "structure": "1-min structure",
             "pattern": "pattern", "trend": "trend", "news": "news"}
    why = []
    for k, c in contrib:
        if abs(c) < 0.005:
            continue
        why.append(("+" if c > 0 else "-") + label[k])

    record = {
        "type": "convergence_record",
        "hypothesis": {"direction": direction, "target_r": round(target_r, 2)},
        "evidence": {k: round(v, 3) for k, v in signals.items()},
        "confidence": {"p_win": round(p_win, 4), "base_rate": round(base_rate, 3)},
        "ev_r": round(ev_r, 3),
        "decision": decision,
        "result": None,   # filled on close (Verify/Converge)
        "source": "convergence_ev",
    }

    return {
        "p_win": round(p_win, 4),
        "ev_r": round(ev_r, 4),
        "target_r": round(target_r, 3),
        "decision": decision,
        "signals": {k: round(v, 3) for k, v in signals.items()},
        "why": why[:4],
        "record": record,
    }
