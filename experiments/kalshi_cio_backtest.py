"""
Kalshi CIO Backtest -- Momentum-Aware Divergence Model (Issue #424)

Root cause of old AR(1) failure (June 13 backtest, 20 resolved MLB markets):
  - AR(1) fixed-point accuracy: 40% correct direction  (below 50% coin-flip)
  - Root cause: AR(1) assumes mean-reversion (|lambda| < 1).
                Game prices TREND monotonically to 0 or 1, not mean-revert.
  - The fixed-point estimator fired when price wobbled mid-game (~0.50),
    estimated p* ~= 0.50, which is anti-correlated with the final outcome.

Momentum-Aware Divergence Model
=================================
Two regimes, selected by time_to_close_hours:

  IN-GAME  (<4h to close): fast-moving prices during active game.
    WINDOW=40  (~4 min)  MIN_MOVE=0.12  -- large in-game score swings.

  PRE-GAME (>=4h to close): slow pre-game line drift.
    WINDOW=200 (~20 min) MIN_MOVE=0.03  -- meaningful line moves only.

Algorithm:
  1. Select regime by time_to_close.
  2. Take last WINDOW snapshots of yes_mid prices.
  3. Fit OLS linear slope.
  4. Gate: if |slope x window| < MIN_MOVE -> no signal.
  5. Certify endpoint: p* = 1.0 if slope > 0, else p* = 0.0.
  6. Edge = p* - current_price.

Interface (unchanged from old module):
  Snapshot(yes_ask, no_ask)
  MarketTrajectory(snapshots, outcome, close_ts=None)
  CIOConvergenceModel().predict(traj) -> (p_star: float, has_signal: bool)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime, timezone

# ---- In-game regime (game actively playing) ----
INGAME_WINDOW    = 40    # snapshots  (~4 min at 6s)
INGAME_MIN_MOVE  = 0.12  # 12 cents projected -- big score swing

# ---- Pre-game regime (market open but game not started) ----
PREGAME_WINDOW   = 1000  # snapshots  (~100 min = 1.7h at 6s)
PREGAME_MIN_MOVE = 0.03  # 3 cents projected -- meaningful line drift

INGAME_HORIZON_H = 4.0   # hours: markets < this are treated as in-game
MIN_POINTS       = 6     # absolute minimum snapshots before any signal


# ---- Data classes --------------------------------------------------------

@dataclass
class Snapshot:
    """Single 6-second price observation (yes_ask, no_ask in 0-1 scale)."""
    yes_ask: float
    no_ask:  float

    @property
    def yes_mid(self) -> float:
        s = self.yes_ask + self.no_ask
        return self.yes_ask / s if s > 0 else 0.5


@dataclass
class MarketTrajectory:
    """Ordered sequence of snapshots for one market."""
    snapshots: List[Snapshot]
    outcome:   int                 # 1=YES won, 0=NO won, -1=unknown
    close_ts:  Optional[str] = None  # ISO-8601 close time (for regime selection)


# ---- Model ---------------------------------------------------------------

class CIOConvergenceModel:
    """
    Momentum-aware divergence model replacing the broken AR(1) fixed-point.

    Selects IN-GAME or PRE-GAME regime by hours to close_ts.
    Falls back to in-game constants when close_ts is unknown.
    """

    @staticmethod
    def _hours_to_close(close_ts: Optional[str]) -> Optional[float]:
        if not close_ts:
            return None
        try:
            ct = datetime.fromisoformat(close_ts.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return max(0.0, (ct - now).total_seconds() / 3600)
        except Exception:
            return None

    @staticmethod
    def _linear_slope(prices: List[float]) -> float:
        n = len(prices)
        if n < 2:
            return 0.0
        x_mean = (n - 1) / 2.0
        y_mean = sum(prices) / n
        num = sum((i - x_mean) * (p - y_mean) for i, p in enumerate(prices))
        den = sum((i - x_mean) ** 2 for i in range(n))
        return num / den if den > 1e-12 else 0.0

    def predict(self, traj: MarketTrajectory) -> Tuple[float, bool]:
        """
        Returns (p_star, has_signal).
          p_star in {0.0, 1.0} -- certified endpoint attractor.
          has_signal True when momentum gate passes.
        """
        snaps = traj.snapshots
        if len(snaps) < MIN_POINTS:
            return 0.5, False

        # Regime selection
        h = self._hours_to_close(traj.close_ts)
        if h is not None and h >= INGAME_HORIZON_H:
            window   = PREGAME_WINDOW
            min_move = PREGAME_MIN_MOVE
        else:
            window   = INGAME_WINDOW
            min_move = INGAME_MIN_MOVE

        window = min(window, len(snaps))
        prices = [s.yes_mid for s in snaps[-window:]]

        slope         = self._linear_slope(prices)
        proj_move     = abs(slope * window)

        if proj_move < min_move:
            return 0.5, False

        p_star = 1.0 if slope > 0 else 0.0
        return p_star, True

