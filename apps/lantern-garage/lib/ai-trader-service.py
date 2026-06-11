#!/usr/bin/env python3
"""
AI Trader Microservice — Flask API for trading signals and analytics
Exposes independent AI trader agents via REST API
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import threading

# Import the bridge
sys.path.insert(0, str(Path(__file__).parent))
from ai_trader_bridge import get_bridge, AITraderBridge

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
log = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Get bridge instance
bridge = get_bridge()

# Background scanner thread
_scanner_thread = None
_scanner_running = False


def background_scanner():
    """Continuously scan for trading signals"""
    global _scanner_running
    import time

    while _scanner_running:
        try:
            log.info("Scanning for trading signals...")
            signals = bridge.generate_signals()

            if signals:
                log.info(f"Generated {len(signals)} signals")
                for signal in signals:
                    bridge.log_signal(signal)
                    log.info(f"  {signal.symbol}: {signal.action} (Confidence: {signal.confidence}%)")
            else:
                log.debug("No high-confidence signals generated")

            time.sleep(30)  # Scan every 30 seconds

        except Exception as e:
            log.error(f"Scanner error: {e}")
            time.sleep(60)


# ── API Routes ─────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'AI Trader Microservice',
        'agents_available': bridge.agents_available,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/ai-trader/signals', methods=['GET'])
def get_signals():
    """Get pending trading signals"""
    try:
        limit = request.args.get('limit', 10, type=int)
        signals = bridge.get_signal_history(limit)
        return jsonify({
            'signals': signals,
            'count': len(signals),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        log.error(f"Signal fetch error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-trader/signals/generate', methods=['POST'])
def generate_signals():
    """Manually trigger signal generation"""
    try:
        data = request.get_json() or {}
        watchlist = data.get('watchlist', None)

        signals = bridge.generate_signals(watchlist)

        signal_dicts = [s.to_dict() for s in signals]

        return jsonify({
            'generated': len(signal_dicts),
            'signals': signal_dicts,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        log.error(f"Signal generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-trader/portfolio', methods=['GET'])
def get_portfolio():
    """Get current portfolio state"""
    try:
        portfolio = bridge.get_portfolio_state()
        return jsonify(portfolio)
    except Exception as e:
        log.error(f"Portfolio fetch error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-trader/trades', methods=['GET'])
def get_trades():
    """Get trade history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        trades = bridge.get_trade_history(limit)
        return jsonify({
            'trades': trades,
            'count': len(trades),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        log.error(f"Trade history error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-trader/trades', methods=['POST'])
def log_trade():
    """Log a new trade"""
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol')
        entry = data.get('entry', type=float)
        quantity = data.get('quantity', type=float)
        exit_price = data.get('exit_price', type=float)
        pnl = data.get('pnl', type=float)

        if not symbol or not entry or not quantity:
            return jsonify({'error': 'Missing required fields'}), 400

        bridge.log_trade(symbol, entry, quantity, exit_price, pnl)

        return jsonify({
            'status': 'logged',
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        log.error(f"Trade logging error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-trader/metrics', methods=['GET'])
def get_metrics():
    """Get performance metrics"""
    try:
        metrics = bridge.get_performance_metrics()
        return jsonify(metrics)
    except Exception as e:
        log.error(f"Metrics error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-trader/scanner/start', methods=['POST'])
def start_scanner():
    """Start background signal scanner"""
    global _scanner_thread, _scanner_running

    if _scanner_running:
        return jsonify({'status': 'already running'})

    try:
        _scanner_running = True
        _scanner_thread = threading.Thread(target=background_scanner, daemon=True)
        _scanner_thread.start()

        return jsonify({
            'status': 'started',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        log.error(f"Scanner start error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai-trader/scanner/stop', methods=['POST'])
def stop_scanner():
    """Stop background signal scanner"""
    global _scanner_running

    _scanner_running = False

    return jsonify({
        'status': 'stopped',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/ai-trader/scanner/status', methods=['GET'])
def scanner_status():
    """Get scanner status"""
    return jsonify({
        'running': _scanner_running,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/ai-trader/status', methods=['GET'])
def status():
    """Get comprehensive system status"""
    try:
        portfolio = bridge.get_portfolio_state()
        metrics = bridge.get_performance_metrics()

        return jsonify({
            'agents_available': bridge.agents_available,
            'scanner_running': _scanner_running,
            'portfolio': portfolio,
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        log.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('AI_TRADER_PORT', 5555))
    host = os.getenv('AI_TRADER_HOST', '127.0.0.1')

    log.info(f"Starting AI Trader Microservice on {host}:{port}")
    log.info(f"Agents available: {bridge.agents_available}")

    app.run(host=host, port=port, debug=False, threaded=True)
