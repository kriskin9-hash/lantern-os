#!/usr/bin/env python3
"""
telegram_bot.py — Telegram Bot
Sends trade alerts, 30-min portfolio updates, and accepts commands.

Commands:
  /status   — portfolio summary
  /positions — open positions
  /watchlist — current watchlist
  /add NVDA  — add ticker to watchlist
  /remove NVDA — remove ticker
  /pause    — pause trading
  /resume   — resume trading
  /scan     — trigger immediate scan
  /help     — show all commands
"""

import os, logging, threading, time
import requests
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

BASE_URL  = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ── Core send function ────────────────────────────────────────────────────────

def send_message(text: str, parse_mode: str = "Markdown") -> bool:
    """Send a message to your Telegram chat."""
    if not BOT_TOKEN or not CHAT_ID:
        log.warning("Telegram not configured — skipping message")
        return False
    try:
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id":    CHAT_ID,
                "text":       text,
                "parse_mode": parse_mode,
            },
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        log.error("Telegram send failed: %s", e)
        return False

def send_alert(text: str) -> bool:
    """Alias for send_message — used by agents."""
    return send_message(text)

# ── Portfolio summary ─────────────────────────────────────────────────────────

def build_portfolio_summary(alpaca) -> str:
    try:
        from agents import calculate_portfolio_delta
        account   = alpaca.get_account()
        positions = alpaca.list_positions()

        equity    = float(account.equity)
        cash      = float(account.cash)
        pnl_today = float(account.equity) - float(account.last_equity)
        pnl_emoji = "📈" if pnl_today >= 0 else "📉"

        lines = [
            f"📊 *Portfolio Update*",
            f"🕐 {datetime.now().strftime('%H:%M')} ET\n",
            f"💼 Equity:    ${equity:,.2f}",
            f"💵 Cash:      ${cash:,.2f}",
            f"{pnl_emoji} Today P&L: {'+'if pnl_today>=0 else ''}${pnl_today:,.2f}\n",
        ]

        if positions:
            lines.append(f"📌 *Open Positions ({len(positions)}):*")
            for p in positions:
                pnl = float(p.unrealized_pl)
                pct = float(p.unrealized_plpc) * 100
                em  = "🟢" if pnl >= 0 else "🔴"
                lines.append(
                    f"{em} {p.symbol}: {float(p.qty):.2f} shares | "
                    f"{'+'if pnl>=0 else ''}${pnl:.2f} ({pct:+.2f}%)"
                )
        else:
            lines.append("📌 No open positions")

        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Could not fetch portfolio: {e}"

def build_watchlist_message(watchlist: list) -> str:
    stocks = [t for t in watchlist if not t.endswith("USD") or len(t) <= 4]
    crypto = [t for t in watchlist if t not in stocks]
    lines  = ["👁 *Current Watchlist*\n"]
    if stocks:
        lines.append("📈 *Stocks:*\n" + "\n".join(f"  • {s}" for s in stocks))
    if crypto:
        lines.append("\n₿ *Crypto:*\n" + "\n".join(f"  • {c}" for c in crypto))
    return "\n".join(lines)

# ── Command handler ───────────────────────────────────────────────────────────

class TelegramCommandHandler:
    def __init__(self, alpaca, watchlist: list, scan_fn, paused_ref: list):
        self.alpaca      = alpaca
        self.watchlist   = watchlist   # mutable list shared with main
        self.scan_fn     = scan_fn     # function to trigger immediate scan
        self.paused      = paused_ref  # [False] — mutable so main.py sees changes
        self.last_offset = 0
        self._running    = False

    def handle(self, text: str) -> str:
        text = text.strip()
        tokens = text.split()
        cmd    = tokens[0].lower().replace("@", "").split("@")[0]
        args   = tokens[1:] if len(tokens) > 1 else []
        parts  = tokens  # full token list including cmd — used by some handlers

        if cmd == "/help":
            send_message(
                "🤖 *AI Trader — Portfolio & Analysis*\n"
                "/status — equity, cash, P&L summary\n"
                "/positions — all open positions with P&L\n"
                "/levels — stop/TP price levels per position\n"
                "/delta — portfolio delta exposure\n"
                "/kelly — Kelly position sizes per ticker\n"
                "/rsi — adaptive RSI thresholds  (e.g. /rsi AAPL)\n"
                "/drawdown — circuit breaker status\n"
                "/report — weekly performance report\n"
                "/graduate — live trading readiness check\n"
                "/lessons — learned from past losses\n"
            )
            send_message(
                "🤖 *AI Trader — Scanning & Research*\n"
                "/scan — trigger immediate market scan\n"
                "/review — AI narrative review of last scan\n"
                "/scan_detail — full reasoning from last scan\n"
                "/research — quick global market scan + picks\n"
                "/scan_watchlist — deep 3-stage ticker research\n"
                "/rotation — sector hot/cold flows\n"
                "/rsi TICKER — adaptive RSI thresholds for ticker\n"
            )
            send_message(
                "🤖 *AI Trader — Control*\n"
                "/pause — pause all new trades\n"
                "/resume — resume trading\n"
                "/close TICKER — close a position\n"
                "/close ALL — emergency close everything\n"
                "/shutdown — stop the bot\n"
                "/watchlist — current watchlist\n"
                "/add TICKER — add ticker to watchlist\n"
                "/remove TICKER — remove ticker\n"
                "/approve TICKER — approve research suggestion\n"
                "/approve ALL — approve all ADD suggestions\n"
                "/reject TICKER — reject suggestion\n"
                "/setlevels — backfill smart levels on open positions\n"
                "/synchistory — sync open positions to trade history DB\n"
            )
            return None

        elif cmd == "/status":
            return build_portfolio_summary(self.alpaca)

        elif cmd == "/positions":
            try:
                positions = self.alpaca.list_positions()
                if not positions:
                    return "📌 No open positions right now."
                lines = ["📌 *Open Positions:*\n"]
                for p in positions:
                    pnl = float(p.unrealized_pl)
                    pct = float(p.unrealized_plpc) * 100
                    em  = "🟢" if pnl >= 0 else "🔴"
                    lines.append(
                        f"{em} *{p.symbol}*\n"
                        f"   Qty: {float(p.qty):.4f}\n"
                        f"   Entry: ${float(p.avg_entry_price):.4f}\n"
                        f"   Now:   ${float(p.current_price):.4f}\n"
                        f"   P&L:   {'+'if pnl>=0 else ''}${pnl:.2f} ({pct:+.2f}%)\n"
                    )
                return "\n".join(lines)
            except Exception as e:
                return f"⚠️ Error: {e}"

        elif cmd == "/watchlist":
            return build_watchlist_message(self.watchlist)

        elif cmd == "/add":
            if not args:
                return "Usage: /add TICKER"
            ticker = args[0].upper()
            if ticker in self.watchlist:
                return f"✅ {ticker} is already on the watchlist."
            self.watchlist.append(ticker)
            return f"✅ Added *{ticker}* to watchlist.\nNow tracking {len(self.watchlist)} tickers."

        elif cmd == "/remove":
            if not args:
                return "Usage: /remove TICKER"
            ticker = args[0].upper()
            if ticker not in self.watchlist:
                return f"❌ {ticker} is not on the watchlist."
            self.watchlist.remove(ticker)
            return f"🗑 Removed *{ticker}* from watchlist.\nNow tracking {len(self.watchlist)} tickers."

        elif cmd == "/drawdown":
            try:
                account     = self.alpaca.get_account()
                equity      = float(account.equity)
                last_equity = float(account.last_equity)
                day_pct     = ((equity - last_equity) / last_equity) * 100
                day_usd     = equity - last_equity
                from main import DRAWDOWN_LIMIT_PCT
                remaining   = DRAWDOWN_LIMIT_PCT + day_pct
                status      = "🚨 TRIGGERED" if day_pct <= -DRAWDOWN_LIMIT_PCT else \
                              "⚠️ WARNING" if day_pct <= -DRAWDOWN_LIMIT_PCT * 0.7 else "✅ OK"
                return (
                    f"📉 *Drawdown Monitor*\n\n"
                    f"Today's P&L: {day_pct:+.2f}% (${day_usd:+,.2f})\n"
                    f"Circuit breaker: -{DRAWDOWN_LIMIT_PCT}%\n"
                    f"Remaining buffer: {remaining:.2f}%\n"
                    f"Status: {status}"
                )
            except Exception as e:
                return f"⚠️ Could not fetch drawdown data: {e}"

        elif cmd == "/shutdown":
            send_message(
                "🛑 *Shutting down AI Trader...*\n"
                "Send /launch to restart (if auto-launch is configured)."
            )
            import os, threading
            threading.Timer(2.0, lambda: os._exit(0)).start()
            return "🛑 Shutdown initiated."

        elif cmd == "/pause":
            self.paused[0] = True
            return "⏸ Trading *paused*. Send /resume to restart."

        elif cmd == "/resume":
            self.paused[0] = False
            return "▶️ Trading *resumed*. Scanning every 30 minutes."

        elif cmd == "/synchistory":
            from agents import log_trade_history, get_profile, alpaca as _alp
            import sqlite3
            try:
                positions = _alp.list_positions()
            except Exception as e:
                return f"Failed: {e}"
            if not positions:
                return "No open positions to sync."
            db = "lessons.db"
            synced, skipped = [], []
            for p in positions:
                sym   = p.symbol
                entry = float(p.avg_entry_price)
                qty   = float(p.qty)
                action = "BUY" if qty > 0 else "SELL"
                profile = get_profile(sym)
                # Check if already in DB
                con = sqlite3.connect(db)
                exists = con.execute(
                    "SELECT id FROM trade_history WHERE symbol=? AND status='open'",
                    (sym,)
                ).fetchone()
                con.close()
                if exists:
                    skipped.append(sym)
                    continue
                log_trade_history(sym, action, abs(qty), entry,
                    confidence=65, reasoning="Backfilled from open position",
                    style=profile["style"])
                synced.append(sym)
            parts = []
            if synced:  parts.append(f"✅ Synced: {', '.join(synced)}")
            if skipped: parts.append(f"⏭ Already tracked: {', '.join(skipped)}")
            return "\U0001f4cb *Trade history synced*\n\n" + "\n".join(parts)

        elif cmd == "/setlevels":
            from agents import (calculate_smart_levels, _position_adjustments,
                                get_profile, alpaca as _alp)
            try:
                positions = _alp.list_positions()
            except Exception as e:
                return f"Failed to fetch positions: {e}"
            if not positions:
                return "No open positions to set levels for."
            send_message("⚙️ Calculating smart levels for all positions...")
            results = []
            for p in positions:
                sym     = p.symbol
                entry   = float(p.avg_entry_price)
                current = float(p.current_price)
                qty     = float(p.qty)
                action  = "BUY" if qty > 0 else "SELL"
                profile = get_profile(sym)
                # Skip if already has smart price levels
                if "stop_price" in _position_adjustments.get(sym, {}):
                    results.append(f"⏭ {sym}: already has smart levels")
                    continue
                try:
                    levels = calculate_smart_levels(sym, entry, action, profile)
                    _position_adjustments[sym] = {
                        "stop_price": levels["stop_price"],
                        "tp_price":   levels["tp_price"],
                    }
                    from agents import save_position_state
                    save_position_state(sym, _position_adjustments[sym])
                    stop_pct = (levels["stop_price"] - entry) / entry * 100
                    tp_pct   = (levels["tp_price"]   - entry) / entry * 100
                    results.append(
                        f"✅ *{sym}*: Stop ${levels['stop_price']:.2f} ({stop_pct:+.1f}%) "
                        f"| TP ${levels['tp_price']:.2f} ({tp_pct:+.1f}%)"
                    )
                except Exception as e:
                    results.append(f"❌ {sym}: failed — {e}")
            return "⚙️ *Smart levels set:*\n\n" + "\n".join(results)

        elif cmd == "/review":
            from agents import (scan_all, alpaca as _alp, get_profile,
                                 get_adaptive_rsi_thresholds, _rsi_threshold_cache,
                                 claude, CLAUDE_SONNET, get_portfolio_equity,
                                 DEFAULT_WATCHLIST, is_crypto)
            results = getattr(scan_all, "_last_results", None)
            if not results:
                return "No scan data yet — wait for the next scan or send /scan."

            send_message("\U0001f50d Generating scan review\u2026")

            try:
                # Fetch live prices and RSI for all tickers
                ticker_data = []
                for t in DEFAULT_WATCHLIST:
                    if is_crypto(t):
                        continue
                    try:
                        bars  = _alp.get_bars(t, "5Min", limit=3, feed="iex").df
                        price = float(bars["close"].iloc[-1]) if not bars.empty else 0
                        chg5m = (bars["close"].iloc[-1] - bars["close"].iloc[0]) / bars["close"].iloc[0] * 100                                 if len(bars) >= 2 else 0
                    except:
                        price, chg5m = 0, 0

                    rsi_t = _rsi_threshold_cache.get(t, {"oversold": 35, "overbought": 65, "median": 50})

                    # Get Riley zone result from last scan if available
                    scan_r = next(
                        (r for r in results.get("analyzed", []) + results.get("skipped", [])
                         if r.get("ticker") == t), {}
                    )

                    ticker_data.append({
                        "ticker":           t,
                        "price":            round(price, 2),
                        "chg_5m":           round(chg5m, 2),
                        "direction":        scan_r.get("direction", "?"),
                        "confidence":       scan_r.get("confidence", "?"),
                        "catalyst":         scan_r.get("catalyst", ""),
                        "reason":           scan_r.get("reason", ""),
                        "riley_quality":    scan_r.get("riley_quality", ""),
                        "riley_zone":       scan_r.get("riley_zone", ""),
                        "riley_touches":    scan_r.get("riley_touches", 0),
                        "riley_structure":  scan_r.get("riley_structure", ""),
                        "trade_mode":       scan_r.get("trade_mode", ""),
                        "rsi_oversold":     rsi_t.get("oversold", 35),
                        "rsi_overbought":   rsi_t.get("overbought", 65),
                        "rsi_median":       rsi_t.get("median", 50),
                    })

                vix   = results.get("vix_regime", {})
                delta = results.get("portfolio_delta", {})
                equity = results.get("equity", get_portfolio_equity())
                ts    = results.get("timestamp", "recent")
                trades = results.get("trades", [])

                # Build rich ticker summary for Sonnet
                tickers_text = ""
                for td in ticker_data:
                    if not td["price"]:
                        continue
                    riley_info = ""
                    if td["riley_quality"]:
                        riley_info = (
                            f"    Riley: {td['riley_quality']} | "
                            f"Zone: {td['riley_zone']} ({td['riley_touches']} touches) | "
                            f"Structure: {td['riley_structure']}\n"
                        )
                    tickers_text += (
                        f"  {td['ticker']} @ ${td['price']} "
                        f"({td['chg_5m']:+.1f}% last 5min)\n"
                        f"    Signal: {td['direction']} {td['confidence']}% | "
                        f"Mode: {td['trade_mode'] or 'N/A'}\n"
                        f"{riley_info}"
                        f"    RSI: oversold<{td['rsi_oversold']:.0f} | "
                        f"overbought>{td['rsi_overbought']:.0f}\n"
                        f"    Why skipped: {td['reason'][:80] if td['reason'] else 'N/A'}\n"
                        f"    Catalyst: {td['catalyst'][:80] if td['catalyst'] else 'None'}\n"
                    )

                trades_text = ""
                if trades:
                    trades_text = "TRADES THIS SCAN:\n"
                    for t in trades:
                        trades_text += f"  {t.get('action')} {t.get('ticker')} @ ${t.get('price','?')} | {t.get('confidence','?')}% conf\n"
                else:
                    trades_text = "No trades executed this scan.\n"

                prompt = f"""You are a trading analyst reviewing a real market scan. Use ONLY the actual data provided below.
DO NOT invent information. If data is missing for a ticker, say so explicitly.

Scan time: {ts}
VIX: {vix.get('vix', 0):.1f} ({vix.get('regime', '?')})
Portfolio delta: {delta.get('net_delta_pct', 0):+.2f}% per 1% SPY move
Equity: ${equity:,.2f}

{trades_text}

ACTUAL TICKER DATA FROM THIS SCAN:
{tickers_text}

Write a concise review with these sections. Use ONLY the data above:

1. Market conditions (1-2 sentences using actual VIX and delta numbers)

2. Best setups RIGHT NOW (use actual Riley quality scores and zone data — IDEAL/GOOD = actionable, WAIT/NO/blank = not ready)

3. Why nothing traded (if no trades — explain specifically which Riley checks blocked each ticker using the actual reason field)

4. What to watch for next scan (specific price levels or RSI levels from the data above)

5. One sentence summary

Do NOT make up data. If riley_quality is blank, say the ticker didn't reach Riley analysis. Keep under 300 words."""

                resp = claude.messages.create(
                    model=CLAUDE_SONNET,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                review = resp.content[0].text.strip()

                return (
                    f"\U0001f4cb *Scan Review \u2014 {ts}*\n\n"
                    f"{review}\n\n"
                    f"_/scan to run a fresh scan_"
                )

            except Exception as e:
                return f"Review failed: {e}"

        elif cmd == "/scan_detail":
            from agents import scan_all
            results = getattr(scan_all, '_last_results', None)
            if not results:
                return "No scan results yet — run /scan first."
            lines = ["📋 *Full Scan Detail*\n"]
            for r in results.get("analyzed", []):
                ticker = r.get("ticker","?")
                conf   = r.get("confidence","?")
                reason = r.get("reason","")
                action = r.get("action","")
                status = r.get("status","")
                catalyst = r.get("catalyst","")
                risk_txt = r.get("risk","")
                lines.append(f"*{ticker}*")
                if conf: lines.append(f"  Confidence: {conf}%")
                if action: lines.append(f"  Signal: {action}")
                if status == "placed": lines.append(f"  ✅ ORDER PLACED")
                if reason: lines.append(f"  Reason: {reason[:100]}")
                if catalyst: lines.append(f"  Catalyst: {catalyst[:80]}")
                if risk_txt: lines.append(f"  Risk: {risk_txt[:80]}")
                lines.append("")
            for r in results.get("skipped", []):
                if r.get("confidence") is None:
                    ticker = r.get("ticker","?")
                    reason = r.get("reason","")
                    lines.append(f"⏭ *{ticker}*: {reason[:80]}")
            return "\n".join(lines) if len(lines) > 1 else "No detailed results available."

        elif cmd == "/scan":
            if self.paused[0]:
                return "⏸ Bot is paused. Send /resume first."
            from agents import is_market_hours, is_crypto
            market_open  = is_market_hours()
            stocks = [t for t in self.watchlist if not is_crypto(t)]
            crypto = [t for t in self.watchlist if is_crypto(t)]
            if market_open:
                active = self.watchlist
                detail = f"{len(stocks)} stocks + {len(crypto)} crypto"
            else:
                active = crypto
                detail = f"{len(crypto)} crypto only (market closed)"
            send_message(f"🔍 Scanning {len(active)} tickers — {detail}...")
            threading.Thread(
                target=self.scan_fn,
                args=(self.watchlist, send_alert),
                daemon=True
            ).start()
            return f"🔍 Scan started — {len(active)} tickers ({detail})"

        elif cmd == "/kelly":
            from agents import get_kelly_position_size, get_profile
            lines = ["📐 *Kelly Position Sizes:*\n"]
            for ticker in self.watchlist:
                profile = get_profile(ticker)
                size    = get_kelly_position_size(ticker, 75)
                lines.append(
                    f"*{ticker}*: {size:.1f}% "
                    f"(min {profile['min']}% / max {profile['max']}%)"
                )
            lines.append(
                "\n_Sizes update as trade history accumulates._\n"
                "_Showing at 75% confidence. Scales with actual win rate._"
            )
            return "\n".join(lines)

        elif cmd == "/approve":
            if not args:
                return "Usage: /approve TICKER  or  /approve ALL"
            from main import _pending_suggestions
            target = args[0].upper()
            added  = []
            if target == "ALL":
                for s in _pending_suggestions:
                    t = s["ticker"].upper()
                    if t not in self.watchlist:
                        self.watchlist.append(t)
                        added.append(t)
            else:
                if target not in self.watchlist:
                    self.watchlist.append(target)
                    added.append(target)
            if added:
                return (
                    f"✅ Added to watchlist: {', '.join(added)}\n"
                    f"Now tracking {len(self.watchlist)} tickers.\n"
                    f"Will appear in next scan cycle."
                )
            return f"⚠️ {target} is already on the watchlist."

        elif cmd == "/reject":
            if not args:
                return "Usage: /reject TICKER"
            return f"👍 Noted — {args[0].upper()} will not be added."

        elif cmd == "/research":
            if len(parts) < 2:
                return "Usage: /research TICKER — e.g. /research META"
            from agents import scan_for_new_tickers, DEFAULT_WATCHLIST
            ticker = parts[1].upper()
            send_message(f"\U0001f50d Researching {ticker}\u2026 (Grok + Sonnet deep analysis, ~30s)")
            try:
                # Run the research pipeline on just this one ticker
                suggestions, theme = scan_for_new_tickers(
                    DEFAULT_WATCHLIST + [ticker],  # exclude it from candidates
                )
                # Actually research it directly
                from agents import (alpaca as _alp, claude, CLAUDE_SONNET,
                                     grok, extract_json, log_agent)
                import json

                # Fetch data
                bars = _alp.get_bars(ticker, "1Hour", limit=48, feed="iex").df
                if bars.empty:
                    return f"No bar data available for {ticker} on Alpaca IEX feed."

                price    = float(bars["close"].iloc[-1])
                high_24h = float(bars["high"].iloc[-24:].max())
                low_24h  = float(bars["low"].iloc[-24:].min())
                chg_24h  = (price - float(bars["close"].iloc[-24])) / float(bars["close"].iloc[-24]) * 100
                atr      = float((bars["high"] - bars["low"]).iloc[-14:].mean())

                news_items = _alp.get_news(symbol=ticker, limit=8)
                news_text  = "\n".join([f"  - {n.headline}" for n in news_items][:5])                              if news_items else "  No recent news"

                # Grok sentiment
                grok_prompt = f"""Research {ticker} right now.
What is happening with this stock today? Any news, catalysts, X/Twitter buzz?
Is it bullish or bearish? What's the main driver?
Keep it brief — 3-4 sentences max."""
                grok_resp = grok.chat.completions.create(
                    model="grok-3-mini",
                    messages=[{"role": "user", "content": grok_prompt}],
                    max_tokens=200,
                )
                grok_summary = grok_resp.choices[0].message.content.strip()

                # Sonnet deep analysis
                sonnet_prompt = f"""Deep research on {ticker} for intraday trading.

Price: ${price:.2f} | 24h change: {chg_24h:+.2f}%
24h range: ${low_24h:.2f}—${high_24h:.2f} | ATR: ${atr:.2f}

News:
{news_text}

Market intelligence: {grok_summary}

Current watchlist for overlap check: {', '.join(DEFAULT_WATCHLIST)}

Provide a complete trading research report:
1. Setup quality (1-10) and why
2. Best entry condition (price + RSI + time of day)
3. Stop loss level with reasoning
4. Take profit target with reasoning
5. Main risks
6. Recommendation: ADD to watchlist / WATCH / SKIP

Be specific with price levels. Keep under 300 words."""

                sonnet_resp = claude.messages.create(
                    model=CLAUDE_SONNET,
                    max_tokens=400,
                    messages=[{"role": "user", "content": sonnet_prompt}]
                )
                report = sonnet_resp.content[0].text.strip()

                return (
                    f"\U0001f50d *Research: {ticker}* @ ${price:.2f}\n"
                    f"24h: {chg_24h:+.2f}% | Range ${low_24h:.2f}\u2014${high_24h:.2f}\n\n"
                    f"\U0001f426 *Grok:* {grok_summary}\n\n"
                    f"\U0001f4cb *Sonnet Analysis:*\n{report}\n\n"
                    f"_/approve {ticker} to add to watchlist_"
                )
            except Exception as e:
                return f"Research failed for {ticker}: {e}"

        elif cmd == "/scan_watchlist":
            send_message("🔍 Running watchlist scan now...")
            threading.Thread(
                target=lambda: __import__('main').job_watchlist_scan(),
                daemon=True
            ).start()
            return "🔍 Scanning for new opportunities..."

        elif cmd == "/rotation":
            from agents import scan_sector_rotation, SECTOR_NAMES
            r = scan_sector_rotation()
            if not r.get("summary"):
                return "📊 Sector rotation data not yet available — will load on next scan."
            lines = [f"🔄 *Sector Rotation* ({r.get('timestamp','')})\n"]
            lines.append(f"📡 {r.get('macro_theme','')}\n")
            lines.append(f"💡 {r.get('summary','')}\n")
            if r.get("hot"):
                lines.append("🔥 *Hot (inflows):*")
                for s in r["hot"]:
                    lines.append(f"  ✅ {SECTOR_NAMES.get(s, s)} (+8% conf)")
            if r.get("cold"):
                lines.append("❄️ *Cold (outflows):*")
                for s in r["cold"]:
                    lines.append(f"  ❌ {SECTOR_NAMES.get(s, s)} (-8% conf)")
            return "\n".join(lines)

        elif cmd == "/graduate":
            from agents import get_graduation_analysis
            grad         = get_graduation_analysis()
            meets_days   = grad.get("days_active", 0) >= 30
            meets_trades = grad.get("meets_trades",  False)
            meets_wr     = grad.get("meets_winrate", False)
            meets_sharpe = grad.get("meets_sharpe",  False)
            criteria = "\n".join([
                f"{'✅' if meets_days   else '❌'} 30+ days active: {grad.get('days_active',0)} days",
                f"{'✅' if meets_trades else '❌'} 20+ trades: {grad.get('trades',0)} completed",
                f"{'✅' if meets_wr     else '❌'} Win rate ≥ 55%: {grad.get('win_rate',0):.1f}%",
                f"{'✅' if meets_sharpe else '❌'} Sharpe ≥ 1.0: {grad.get('sharpe',0):.2f}",
            ])
            status  = "🎓 *READY TO GO LIVE*" if grad["ready"] else "📋 *Not ready yet*"
            missing = "🚀 All criteria met! Consider going live." if grad["ready"] \
                      else f"Reason: {grad.get('reason','keep accumulating trades')}"
            return f"{status}\n\n{criteria}\n\n{missing}"

        elif cmd == "/report":
            from agents import get_weekly_stats
            stats = get_weekly_stats()
            s     = stats.get("summary")
            if not s or s["total"] == 0:
                return "📅 *Weekly Report*\n\nNo completed trades in the last 7 days."
            pnl_emoji = "📈" if s["total_pnl"] >= 0 else "📉"
            lines = [
                "📅 *Weekly Report (last 7 days)*\n",
                f"🔢 Trades: {s['total']} | ✅ {s['wins']}W / ❌ {s['losses']}L",
                f"🎯 Win rate: {s['win_rate']}%",
                f"{pnl_emoji} P&L: ${s['total_pnl']:+.2f}",
                f"📊 Avg win: {s['avg_win']:+.2f}% | Avg loss: {s['avg_loss']:+.2f}%",
                f"🏆 Best: {s['best_trade']:+.2f}% | Worst: {s['worst_trade']:+.2f}%",
            ]
            lessons = stats.get("lessons", [])
            if lessons:
                lines.append("\n*Lessons:*")
                for l in lessons[:3]:
                    lines.append(f"• {l[0]}: {l[2]}")
            return "\n".join(lines)

        elif cmd == "/lessons":
            from agents import get_recent_lessons
            limit = int(args[0]) if args and args[0].isdigit() else 5
            lessons = get_recent_lessons(limit=limit)
            if not lessons:
                return "📚 No lessons recorded yet — lessons are saved after losing trades."
            lines = [f"📚 *Last {len(lessons)} Lessons Learned:*\n"]
            for i, l in enumerate(lessons, 1):
                lines.append(
                    f"*{i}. {l['symbol']}* ({l['pnl_pct']:+.1f}%)\n"
                    f"  🔍 {l['lesson']}\n"
                    f"  ⚠️ Avoid: {l['avoid']}\n"
                    f"  🏷 Pattern: {l['pattern']}\n"
                )
            return "\n".join(lines)

        elif cmd == "/rsi":
            from agents import get_adaptive_rsi_thresholds, DEFAULT_WATCHLIST, alpaca as _alp, is_crypto, _rsi_threshold_cache
            ticker = parts[1].upper() if len(parts) > 1 else None

            if ticker:
                send_message(f"\U0001f4ca Calculating RSI thresholds for {ticker}\u2026")
                try:
                    th = get_adaptive_rsi_thresholds(ticker)
                    try:
                        bars = _alp.get_bars(ticker, "5Min", limit=1, feed="iex").df
                        price = float(bars["close"].iloc[-1]) if not bars.empty else None
                        price_str = f"@ ${price:.2f}" if price else ""
                    except:
                        price_str = ""
                    return (
                        f"\U0001f4ca *RSI Thresholds \u2014 {ticker}* {price_str}\n\n"
                        f"Oversold:   <{th['oversold']:.0f} (p15) | Extreme: <{th['p10']:.0f} (p10)\n"
                        f"Overbought: >{th['overbought']:.0f} (p85) | Extreme: >{th['p90']:.0f} (p90)\n"
                        f"Median RSI: {th['median']:.0f}\n"
                        f"Source: {th['source']}\n\n"
                        f"_Personal thresholds based on 90d hourly RSI history._"
                    )
                except Exception as e:
                    return f"RSI calc failed for {ticker}: {e}"
            else:
                stocks = [t for t in DEFAULT_WATCHLIST if not is_crypto(t)]
                cached = {t: _rsi_threshold_cache[t] for t in stocks if t in _rsi_threshold_cache}
                if not cached:
                    return (
                        "\U0001f4ca No RSI thresholds cached yet \u2014 calculated during scans.\n\n"
                        "Run /rsi AAPL to fetch a specific ticker now."
                    )
                lines = ["\U0001f4ca *Cached RSI Thresholds*\n"]
                for t in stocks:
                    if t in cached:
                        th = cached[t]
                        lines.append(
                            f"*{t}*: <{th['oversold']:.0f} oversold | "
                            f">{th['overbought']:.0f} overbought | "
                            f"median {th['median']:.0f}"
                        )
                    else:
                        lines.append(f"*{t}*: not cached \u2014 run /rsi {t}")
                lines.append("\n_/rsi TICKER for full detail_")
                return "\n".join(lines)

        elif cmd == "/delta":
            from agents import calculate_portfolio_delta, get_portfolio_equity
            eq    = get_portfolio_equity()
            delta = calculate_portfolio_delta(eq)
            lines = ["\U0001f4d0 *Portfolio Delta*\n"]
            bar_len = 20
            net_pct = delta["net_delta_pct"]
            filled  = min(bar_len, int(abs(net_pct) / 15 * bar_len))
            bar = ("█" * filled) + ("░" * (bar_len - filled))
            direction = "LONG ▲" if net_pct > 0 else "SHORT ▼"
            lines.append(f"Net delta: {net_pct:+.2f}% per 1% SPY move")
            lines.append(f"Direction: {direction}")
            lines.append(f"[{bar}] {'⚠️ OVEREXPOSED' if delta['overexposed'] else '✅ OK'}")
            lines.append(f"")
            lines.append(f"Long exposure:  ${delta['long_delta_usd']:,.0f}/1% SPY")
            lines.append(f"Short exposure: ${delta['short_delta_usd']:,.0f}/1% SPY")
            lines.append(f"")
            lines.append("*Per position:*")
            for p in sorted(delta["positions"],
                            key=lambda x: abs(x["delta_usd"]), reverse=True):
                side_icon = "📈" if p["side"] == "long" else "📉"
                lines.append(
                    f"  {side_icon} {p['symbol']}: ${p['delta_usd']:+,.0f}/1% "
                    f"(β={p['beta']:.2f}, {p['delta_pct']:+.2f}% equity)"
                )
            if delta["alert"]:
                lines.append("\n" + delta["alert"])
            return "\n".join(lines)

        elif cmd == "/levels":
            from agents import _position_adjustments, get_profile, get_open_positions
            positions = get_open_positions()
            if not positions:
                return "📌 No open positions."
            lines = ["⚙️ *Current Levels:*\n"]
            try:
                alpaca_positions = {p.symbol: p for p in self.alpaca.list_positions()}
            except:
                alpaca_positions = {}
            for sym in positions:
                profile_key = sym.replace("/","") + "USD" if "/" in sym else sym
                profile = get_profile(profile_key)
                adj     = _position_adjustments.get(sym, {})
                p       = alpaca_positions.get(sym)
                entry   = float(p.avg_entry_price) if p else 0
                current = float(p.current_price)   if p else 0

                if "stop_price" in adj and entry > 0:
                    stop_p = adj["stop_price"]
                    tp_p   = adj["tp_price"]
                    stop_pct = (stop_p - entry) / entry * 100
                    tp_pct   = (tp_p   - entry) / entry * 100
                    is_trailing = stop_pct > profile["stop"]
                    trail_flag  = " 📌" if is_trailing else ""
                    locked = " ✅ profit locked" if stop_pct > 0 else \
                             " 🔒 breakeven" if stop_pct == 0 else ""
                    lines.append(
                        f"*{sym}*{trail_flag}{locked}\n"
                        f"  Stop: ${stop_p:.4f} ({stop_pct:+.1f}%)\n"
                        f"  TP:   ${tp_p:.4f} ({tp_pct:+.1f}%)\n"
                        f"  Now:  ${current:.4f} | {profile['style']}\n"
                    )
                else:
                    stop_pct = profile["stop"]
                    tp_pct   = profile["tp"]
                    lines.append(
                        f"*{sym}*\n"
                        f"  Stop: {stop_pct:+.1f}% | TP: +{tp_pct:.1f}%\n"
                        f"  (smart levels not yet set)\n"
                    )
            return "\n".join(lines)

        elif cmd == "/close":
            if not args:
                return "Usage: /close TICKER  or  /close ALL"
            target = args[0].upper()
            try:
                if target == "ALL":
                    # Cancel all open orders first to free locked shares
                    try:
                        self.alpaca.cancel_all_orders()
                    except Exception:
                        pass
                    import time; time.sleep(1)
                    self.alpaca.close_all_positions()
                    from agents import _position_adjustments
                    _position_adjustments.clear()
                    return "🚪 *All positions closed.*"
                else:
                    # Cancel any pending orders for this ticker first
                    try:
                        orders = self.alpaca.list_orders(status="open")
                        for o in orders:
                            if o.symbol == target:
                                self.alpaca.cancel_order(o.id)
                        import time; time.sleep(1)
                    except Exception:
                        pass
                    # Now close the position
                    self.alpaca.close_position(target)
                    from agents import _position_adjustments, clear_position_state
                    _position_adjustments.pop(target, None)
                    clear_position_state(target)
                    return f"🚪 *{target}* position closed."
            except Exception as e:
                # Try getting current position to give better error info
                try:
                    pos = self.alpaca.get_position(target)
                    qty = pos.qty
                    return (f"⚠️ Close failed for {target} (qty: {qty}): {e}\n"
                            f"Try /close ALL to force close everything.")
                except Exception:
                    return f"⚠️ {target} not found in open positions — may already be closed."

        else:
            return "❓ Unknown command. Send /help to see all commands."

    def poll(self):
        """Long-poll Telegram for incoming messages."""
        self._running = True
        log.info("Telegram command listener started")
        while self._running:
            try:
                resp = requests.get(
                    f"{BASE_URL}/getUpdates",
                    params={"offset": self.last_offset + 1, "timeout": 30},
                    timeout=40
                )
                if resp.status_code != 200:
                    time.sleep(5)
                    continue

                data = resp.json()
                for update in data.get("result", []):
                    self.last_offset = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    if text.startswith("/"):
                        reply = self.handle(text)
                        if reply:
                            send_message(reply)

            except Exception as e:
                log.error("Telegram poll error: %s", e)
                time.sleep(10)

    def start(self):
        """Start polling in a background thread."""
        t = threading.Thread(target=self.poll, daemon=True)
        t.start()
        return t

    def stop(self):
        self._running = False