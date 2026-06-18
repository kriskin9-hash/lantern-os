#!/usr/bin/env python3
"""
price_watcher.py — Continuous Price Monitor

Runs every 30 seconds in a background thread.
No AI calls — pure price math.

Triggers when:
  - Any held position moves ±2% within 5 minutes → emergency action
  - Any watchlist ticker moves +2% fast → wake up AI for opportunity scan

Actions:
  - Crash (-2% in 5 min on held position) → close immediately + notify
  - Spike (+2% in 5 min on held position) → close if above TP + notify
  - Big move on unwatched ticker → trigger full AI scan
"""

import time
import logging
import threading
from datetime import datetime
from collections import deque

log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
WATCH_INTERVAL_SEC = 30    # check prices every 30 seconds
WINDOW_MINUTES     = 5     # look back this many minutes for the move
MAX_HISTORY        = 20    # max price snapshots to keep per ticker
ALERT_COOLDOWN_MIN = 10    # don't re-alert same ticker within 10 min

# ── Per-asset trigger thresholds ──────────────────────────────────────────────
# Threshold = fraction of the asset stop loss that triggers a warning.
# e.g. AAPL stop=-4% → trigger at 50% of stop = -2% move in 5 min
# Crypto has wider stops so triggers are naturally wider too.
# Entry opportunity threshold = half the take profit target.
#
# These are derived automatically from each asset's profile — no hardcoding.

def get_trigger_pcts(profile: dict) -> tuple[float, float]:
    """
    Returns (crash_trigger_pct, spike_trigger_pct) for a given asset profile.
    crash_trigger = 50% of stop loss (negative)
    spike_trigger = 33% of take profit (positive)
    Minimum crash trigger: -1.0% | Minimum spike: +1.5%
    """
    crash = max(abs(profile["stop"]) * 0.50, 1.0)   # at least 1%
    spike = max(profile["tp"]        * 0.33, 1.5)   # at least 1.5%
    return -crash, spike

# ── Price history ─────────────────────────────────────────────────────────────
_price_history: dict[str, deque] = {}
_watcher_running = False
_last_alert: dict[str, datetime] = {}


def _get_price_safe(ticker: str, alpaca, is_crypto_fn, alpaca_symbol_fn) -> float:
    """Fetch price without raising — returns 0 on failure."""
    try:
        if is_crypto_fn(ticker):
            sym  = alpaca_symbol_fn(ticker)
            bars = alpaca.get_crypto_bars(sym, "1Min", limit=2).df
            if bars.empty:
                return 0.0
            return float(bars["close"].iloc[-1])
        else:
            bar = alpaca.get_latest_bar(ticker, feed="iex")
            return float(bar.c)
    except:
        return 0.0


def _pct_move(old: float, new: float) -> float:
    if old <= 0:
        return 0.0
    return ((new - old) / old) * 100


def _on_cooldown(ticker: str) -> bool:
    last = _last_alert.get(ticker)
    if last is None:
        return False
    elapsed = (datetime.now() - last).total_seconds() / 60
    return elapsed < ALERT_COOLDOWN_MIN


def _mark_alerted(ticker: str):
    _last_alert[ticker] = datetime.now()


def _get_window_price(ticker: str) -> float | None:
    """Get price from WINDOW_MINUTES ago for this ticker."""
    if ticker not in _price_history:
        return None
    history = _price_history[ticker]
    cutoff  = time.time() - (WINDOW_MINUTES * 60)
    # Find oldest price within the window
    for ts, price in history:
        if ts >= cutoff:
            return price
    return None


class PriceWatcher:
    def __init__(self, alpaca, watchlist: list, notify_fn,
                 scan_trigger_fn, get_positions_fn,
                 is_crypto_fn, alpaca_symbol_fn,
                 get_profile_fn, close_position_fn,
                 is_market_hours_fn):
        self.alpaca           = alpaca
        self.watchlist        = watchlist
        self.notify           = notify_fn
        self.trigger_scan     = scan_trigger_fn   # fn() → triggers full AI scan
        self.get_positions    = get_positions_fn
        self.is_crypto        = is_crypto_fn
        self.alpaca_symbol    = alpaca_symbol_fn
        self.get_profile      = get_profile_fn
        self.close_position   = close_position_fn
        self.is_market_hours  = is_market_hours_fn
        self._thread          = None
        self._scan_cooldown   = {}  # {ticker: last_scan_trigger_time}
        self.SCAN_COOLDOWN_MIN = 15  # don't retrigger scan for same ticker within 15 min

    def _should_watch(self, ticker: str) -> bool:
        """Only watch crypto 24/7 and stocks during market hours."""
        if self.is_crypto(ticker):
            return True
        return self.is_market_hours()

    def _scan_on_cooldown(self, ticker: str) -> bool:
        last = self._scan_cooldown.get(ticker)
        if last is None:
            return False
        elapsed = (datetime.now() - last).total_seconds() / 60
        return elapsed < self.SCAN_COOLDOWN_MIN

    def _check_ticker(self, ticker: str, positions: dict):
        """Check one ticker using per-asset thresholds derived from its profile."""
        price = _get_price_safe(
            ticker, self.alpaca, self.is_crypto, self.alpaca_symbol)
        if price <= 0:
            return

        now = time.time()
        if ticker not in _price_history:
            _price_history[ticker] = deque(maxlen=MAX_HISTORY)
        _price_history[ticker].append((now, price))

        window_price = _get_window_price(ticker)
        if window_price is None or window_price <= 0:
            return

        move_pct = _pct_move(window_price, price)

        # Get per-asset thresholds
        profile_key        = ticker.replace("/","") + "USD" if "/" in ticker else ticker
        profile            = self.get_profile(profile_key)
        crash_thr, spike_thr = get_trigger_pcts(profile)

        # Not significant for this asset — skip silently
        if crash_thr < move_pct < spike_thr:
            return

        log.info("[WATCHER] %s %+.2f%% in %dmin (crash<%.1f%% spike>+%.1f%%)",
                 ticker, move_pct, WINDOW_MINUTES, crash_thr, spike_thr)

        is_held = any(
            ticker.replace("/","").upper() == k.replace("/","").upper()
            for k in positions
        )

        if _on_cooldown(ticker):
            return

        if is_held:
            pos_sym = next(
                (k for k in positions
                 if ticker.replace("/","").upper() == k.replace("/","").upper()),
                None
            )
            try:
                pos     = positions[pos_sym]
                qty     = float(pos.qty) if hasattr(pos, "qty") else 0
                pnl_pct = float(pos.unrealized_plpc) * 100 \
                          if hasattr(pos, "unrealized_plpc") else 0
            except:
                qty, pnl_pct = 0, 0

            if move_pct <= crash_thr:
                if pnl_pct <= profile["stop"]:
                    self.close_position(
                        pos_sym, qty,
                        f"Emergency stop — dropped {move_pct:+.1f}% in {WINDOW_MINUTES}min",
                        self.notify, 0, price, pnl_pct
                    )
                else:
                    pct_to_stop = abs(pnl_pct - profile["stop"])
                    self.notify(
                        f"⚠️ *Flash Drop: {ticker}*\n"
                        f"📉 Fell {move_pct:+.1f}% in {WINDOW_MINUTES}min\n"
                        f"💰 P&L: {pnl_pct:+.1f}% | Stop: {profile['stop']}% "
                        f"({pct_to_stop:.1f}% away)\n🤖 AI review triggered..."
                    )
                    if not self._scan_on_cooldown(ticker):
                        self._scan_cooldown[ticker] = datetime.now()
                        threading.Thread(target=self.trigger_scan, daemon=True).start()

            elif move_pct >= spike_thr:
                if pnl_pct >= profile["tp"]:
                    self.close_position(
                        pos_sym, qty,
                        f"Flash take profit — spiked {move_pct:+.1f}% in {WINDOW_MINUTES}min",
                        self.notify, 0, price, pnl_pct
                    )
                else:
                    pct_to_tp = profile["tp"] - pnl_pct
                    self.notify(
                        f"🚀 *Flash Spike: {ticker}*\n"
                        f"📈 Up {move_pct:+.1f}% in {WINDOW_MINUTES}min\n"
                        f"💰 P&L: {pnl_pct:+.1f}% | TP: +{profile['tp']}% "
                        f"({pct_to_tp:.1f}% away)\n🤖 AI review triggered..."
                    )
                    if not self._scan_on_cooldown(ticker):
                        self._scan_cooldown[ticker] = datetime.now()
                        threading.Thread(target=self.trigger_scan, daemon=True).start()

            _mark_alerted(ticker)

        else:
            if move_pct >= spike_thr:
                # Spike up = potential SHORT reversal (exhaustive move)
                self.notify(
                    f"⚡ *Spike Alert: {ticker}*\n"
                    f"📈 Up {move_pct:+.1f}% in {WINDOW_MINUTES}min\n"
                    f"🔄 Watching for SHORT reversal at resistance..."
                )
            elif move_pct <= crash_thr:
                # Flash drop = potential LONG reversal (exhaustive move)
                self.notify(
                    f"⚡ *Flash Drop: {ticker}*\n"
                    f"📉 Down {move_pct:+.1f}% in {WINDOW_MINUTES}min\n"
                    f"🔄 Watching for LONG reversal at support..."
                )
            _mark_alerted(ticker)
            if not self._scan_on_cooldown(ticker):
                self._scan_cooldown[ticker] = datetime.now()
                threading.Thread(target=self.trigger_scan, daemon=True).start()

    def _watch_loop(self):
        """Main watch loop — runs every 30 seconds."""
        global _watcher_running
        log.info("[WATCHER] Price watcher started — checking every %ds", WATCH_INTERVAL_SEC)

        while _watcher_running:
            try:
                positions = self.get_positions()
                for ticker in self.watchlist:
                    if self._should_watch(ticker):
                        self._check_ticker(ticker, positions)
            except Exception as e:
                log.error("[WATCHER] Loop error: %s", e)

            time.sleep(WATCH_INTERVAL_SEC)

    def start(self):
        global _watcher_running
        _watcher_running = True
        self._thread = threading.Thread(
            target=self._watch_loop, daemon=True, name="PriceWatcher")
        self._thread.start()
        log.info("[WATCHER] Started")

    def stop(self):
        global _watcher_running
        _watcher_running = False