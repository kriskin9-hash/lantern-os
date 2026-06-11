#!/usr/bin/env python3
"""
AI Trader Bridge — Connects independent AI trader to Lantern OS
Bridges agents, signals, and trade data between systems
"""

import os
import sys
import json
import logging
import threading
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add independent AI trader to path
TRADER_PATH = Path("C:/independant ai trader")
if TRADER_PATH.exists():
    sys.path.insert(0, str(TRADER_PATH))

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

# Try to import agents from independent AI trader
try:
    from agents import (
        scan_all, agent_log, DEFAULT_WATCHLIST,
        get_portfolio_equity, get_open_positions,
        get_profile, close_position, is_market_hours,
        is_crypto, ASSET_PROFILES
    )
    AGENTS_AVAILABLE = True
except ImportError as e:
    log.warning(f"Independent AI trader agents not available: {e}")
    AGENTS_AVAILABLE = False


class TradeSignal:
    """Represents a single trading signal"""

    def __init__(self, symbol: str, action: str, confidence: int,
                 entry: float, stop_loss: float, take_profit: float,
                 position_size: float, rationale: str, agent_scores: Dict[str, int]):
        self.symbol = symbol
        self.action = action  # BUY, SELL, HOLD
        self.confidence = confidence  # 0-100
        self.entry = entry
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_size = position_size
        self.rationale = rationale
        self.agent_scores = agent_scores  # {trend: 75, momentum: 68, ...}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'action': self.action,
            'confidence': self.confidence,
            'entry': self.entry,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'rationale': self.rationale,
            'agent_scores': self.agent_scores,
            'timestamp': self.timestamp
        }


class AITraderBridge:
    """Bridges independent AI trader with Lantern OS"""

    def __init__(self):
        self.agents_available = AGENTS_AVAILABLE
        self.signal_queue: List[TradeSignal] = []
        self.trades_db = Path("C:/Users/krisk/Desktop/lanternOS/data/trades/execution.db")
        self.trades_db.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize trades database"""
        try:
            with sqlite3.connect(self.trades_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS signals (
                        id INTEGER PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        action TEXT NOT NULL,
                        confidence INTEGER,
                        entry REAL,
                        stop_loss REAL,
                        take_profit REAL,
                        position_size REAL,
                        rationale TEXT,
                        agent_scores TEXT,
                        timestamp TEXT,
                        status TEXT DEFAULT 'pending',
                        execution_price REAL,
                        execution_time TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        entry REAL NOT NULL,
                        entry_time TEXT,
                        exit REAL,
                        exit_time TEXT,
                        quantity REAL,
                        pnl REAL,
                        pnl_pct REAL,
                        status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            log.error(f"Database initialization failed: {e}")

    def generate_signals(self, watchlist: List[str] = None) -> List[TradeSignal]:
        """
        Generate trading signals using independent AI trader agents
        """
        if not self.agents_available:
            log.warning("Agents not available, returning empty signals")
            return []

        if watchlist is None:
            watchlist = list(DEFAULT_WATCHLIST)

        signals = []

        try:
            # Run multi-agent scan
            results = scan_all(watchlist, max_concurrent=5)

            for symbol, score_data in results.items():
                if score_data.get('confidence', 0) < 60:
                    continue

                agent_scores = {
                    'trend': score_data.get('trend_score', 0),
                    'momentum': score_data.get('momentum_score', 0),
                    'volatility': score_data.get('volatility_score', 0),
                    'risk': score_data.get('risk_score', 0),
                }

                profile = get_profile(symbol)
                action = score_data.get('action', 'HOLD')

                if action in ['BUY', 'SELL']:
                    entry = score_data.get('entry_price', score_data.get('current_price'))
                    stop_loss = entry * (1 - profile['stop'] / 100)
                    take_profit = entry * (1 + profile['tp'] / 100)

                    signal = TradeSignal(
                        symbol=symbol,
                        action=action,
                        confidence=score_data.get('confidence', 0),
                        entry=entry,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        position_size=score_data.get('position_size', 1.0),
                        rationale=score_data.get('rationale', ''),
                        agent_scores=agent_scores
                    )
                    signals.append(signal)

        except Exception as e:
            log.error(f"Signal generation failed: {e}")

        with self.lock:
            self.signal_queue.extend(signals)

        return signals

    def get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state from Alpaca"""
        try:
            equity = get_portfolio_equity()
            positions = get_open_positions()

            return {
                'equity': equity,
                'positions': [
                    {
                        'symbol': p['symbol'],
                        'quantity': p['qty'],
                        'entry_price': p['avg_fill_price'],
                        'current_price': p['current_price'],
                        'unrealized_pl': p['unrealized_pl'],
                        'unrealized_plpc': p['unrealized_plpc']
                    }
                    for p in positions
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            log.error(f"Portfolio fetch failed: {e}")
            return {}

    def log_signal(self, signal: TradeSignal, status: str = 'pending'):
        """Log signal to database"""
        try:
            with sqlite3.connect(self.trades_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO signals
                    (symbol, action, confidence, entry, stop_loss, take_profit,
                     position_size, rationale, agent_scores, timestamp, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.symbol,
                    signal.action,
                    signal.confidence,
                    signal.entry,
                    signal.stop_loss,
                    signal.take_profit,
                    signal.position_size,
                    signal.rationale,
                    json.dumps(signal.agent_scores),
                    signal.timestamp,
                    status
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            log.error(f"Signal logging failed: {e}")
            return None

    def log_trade(self, symbol: str, entry: float, quantity: float,
                  exit_price: float = None, pnl: float = None):
        """Log executed trade to database"""
        try:
            with sqlite3.connect(self.trades_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO trades
                    (symbol, entry, entry_time, exit, exit_time, quantity, pnl, pnl_pct, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    entry,
                    datetime.utcnow().isoformat(),
                    exit_price,
                    datetime.utcnow().isoformat() if exit_price else None,
                    quantity,
                    pnl,
                    (pnl / (entry * quantity) * 100) if pnl and entry * quantity else None,
                    'closed' if exit_price else 'open'
                ))
                conn.commit()
        except Exception as e:
            log.error(f"Trade logging failed: {e}")

    def get_trade_history(self, limit: int = 50) -> List[dict]:
        """Get recent trade history"""
        try:
            with sqlite3.connect(self.trades_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM trades
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            log.error(f"History fetch failed: {e}")
            return []

    def get_signal_history(self, limit: int = 50) -> List[dict]:
        """Get recent signal history"""
        try:
            with sqlite3.connect(self.trades_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM signals
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    d = dict(row)
                    if d['agent_scores']:
                        d['agent_scores'] = json.loads(d['agent_scores'])
                    results.append(d)
                return results
        except Exception as e:
            log.error(f"Signal history fetch failed: {e}")
            return []

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate trading performance metrics"""
        try:
            with sqlite3.connect(self.trades_db) as conn:
                cursor = conn.cursor()

                # Win rate
                cursor.execute('''
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
                    FROM trades WHERE status = 'closed'
                ''')
                result = cursor.fetchone()
                total, wins = result if result else (0, 0)
                win_rate = (wins / total * 100) if total > 0 else 0

                # Total P&L
                cursor.execute('SELECT SUM(pnl) as total_pnl FROM trades')
                total_pnl = cursor.fetchone()[0] or 0

                # Average trade
                cursor.execute('''
                    SELECT
                        AVG(pnl) as avg_pnl,
                        AVG(pnl_pct) as avg_pnl_pct
                    FROM trades WHERE status = 'closed'
                ''')
                result = cursor.fetchone()
                avg_pnl, avg_pnl_pct = result if result else (0, 0)

                # R Multiple (assuming 1R = stop loss distance)
                cursor.execute('''
                    SELECT
                        SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as total_wins,
                        SUM(CASE WHEN pnl < 0 THEN ABS(pnl) ELSE 0 END) as total_losses
                    FROM trades WHERE status = 'closed'
                ''')
                wins_sum, losses_sum = cursor.fetchone()
                r_multiple = (wins_sum / losses_sum) if losses_sum and losses_sum > 0 else 0

                return {
                    'total_trades': total,
                    'winning_trades': wins,
                    'win_rate_pct': round(win_rate, 2),
                    'total_pnl': round(total_pnl, 2),
                    'avg_pnl': round(avg_pnl, 2) if avg_pnl else 0,
                    'avg_pnl_pct': round(avg_pnl_pct, 2) if avg_pnl_pct else 0,
                    'r_multiple': round(r_multiple, 2),
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            log.error(f"Metrics calculation failed: {e}")
            return {}


# Global bridge instance
_bridge = None

def get_bridge() -> AITraderBridge:
    """Get or create the AI trader bridge"""
    global _bridge
    if _bridge is None:
        _bridge = AITraderBridge()
    return _bridge


if __name__ == '__main__':
    # Test the bridge
    logging.basicConfig(level=logging.INFO)
    bridge = get_bridge()

    print("\n=== Independent AI Trader Bridge ===")
    print(f"Agents available: {bridge.agents_available}")

    if bridge.agents_available:
        print("\n--- Generating signals ---")
        signals = bridge.generate_signals(['AAPL', 'MSFT', 'BTCUSD'])

        for signal in signals:
            print(f"\n{signal.symbol} - {signal.action} (Confidence: {signal.confidence}%)")
            print(f"  Entry: ${signal.entry:.2f}")
            print(f"  Stop: ${signal.stop_loss:.2f}")
            print(f"  Target: ${signal.take_profit:.2f}")
            print(f"  Agents: {signal.agent_scores}")

            bridge.log_signal(signal)

    print("\n--- Portfolio State ---")
    portfolio = bridge.get_portfolio_state()
    print(json.dumps(portfolio, indent=2))

    print("\n--- Performance ---")
    metrics = bridge.get_performance_metrics()
    print(json.dumps(metrics, indent=2))
