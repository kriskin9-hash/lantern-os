#!/usr/bin/env python3
"""
AI Trader REST API Server
Exposes trading state and controls via Flask on port 5555
"""

import logging
import json
from datetime import datetime
from flask import Flask, jsonify, request

log = logging.getLogger(__name__)

# Will be injected by main.py
SHARED_STATE = {}

def create_api_app(shared_state):
    """Factory function to create Flask app with shared state."""
    global SHARED_STATE
    SHARED_STATE = shared_state

    app = Flask(__name__)

    # Health check
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'uptime': SHARED_STATE.get('uptime', 0),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200

    # Trading status
    @app.route('/api/status', methods=['GET'])
    def status():
        try:
            return jsonify({
                'market_open': SHARED_STATE.get('market_open', False),
                'equity': SHARED_STATE.get('equity', 0.0),
                'positions': SHARED_STATE.get('positions_count', 0),
                'paused': SHARED_STATE.get('paused', False),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            log.error(f'Error fetching status: {e}')
            return jsonify({'error': str(e)}), 500

    # Watchlist
    @app.route('/api/watchlist', methods=['GET'])
    def watchlist():
        try:
            return jsonify({
                'watchlist': SHARED_STATE.get('watchlist', []),
                'paused': SHARED_STATE.get('paused', False),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            log.error(f'Error fetching watchlist: {e}')
            return jsonify({'error': str(e)}), 500

    # Zones (market analysis per ticker)
    @app.route('/api/zones', methods=['GET'])
    def zones():
        try:
            zones_data = SHARED_STATE.get('zones', {})
            return jsonify({
                'zones': zones_data,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            log.error(f'Error fetching zones: {e}')
            return jsonify({'error': str(e)}), 500

    # Trading signals
    @app.route('/api/signals', methods=['GET'])
    def signals():
        try:
            limit = int(request.args.get('limit', 10))
            signals_list = SHARED_STATE.get('signals', [])
            return jsonify({
                'signals': signals_list[-limit:] if signals_list else [],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            log.error(f'Error fetching signals: {e}')
            return jsonify({'error': str(e)}), 500

    # Open positions
    @app.route('/api/positions', methods=['GET'])
    def positions():
        try:
            positions_list = SHARED_STATE.get('positions', [])
            return jsonify({
                'positions': positions_list,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            log.error(f'Error fetching positions: {e}')
            return jsonify({'error': str(e)}), 500

    # Alerts
    @app.route('/api/alerts', methods=['GET'])
    def alerts():
        try:
            limit = int(request.args.get('limit', 20))
            alerts_list = SHARED_STATE.get('alerts', [])
            return jsonify({
                'alerts': alerts_list[-limit:] if alerts_list else [],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            log.error(f'Error fetching alerts: {e}')
            return jsonify({'error': str(e)}), 500

    # Control: pause trading
    @app.route('/api/control/pause', methods=['POST'])
    def pause_trading():
        api_key = request.headers.get('X-API-Key', '')
        if not _verify_api_key(api_key):
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            SHARED_STATE['paused'] = True
            log.info('Trading paused via API')
            return jsonify({
                'status': 'paused',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            log.error(f'Error pausing trading: {e}')
            return jsonify({'error': str(e)}), 500

    # Control: resume trading
    @app.route('/api/control/resume', methods=['POST'])
    def resume_trading():
        api_key = request.headers.get('X-API-Key', '')
        if not _verify_api_key(api_key):
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            SHARED_STATE['paused'] = False
            log.info('Trading resumed via API')
            return jsonify({
                'status': 'resumed',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            log.error(f'Error resuming trading: {e}')
            return jsonify({'error': str(e)}), 500

    # Control: close position
    @app.route('/api/control/close-position', methods=['POST'])
    def close_position():
        api_key = request.headers.get('X-API-Key', '')
        if not _verify_api_key(api_key):
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            symbol = request.args.get('symbol')
            if not symbol:
                return jsonify({'error': 'Missing symbol parameter'}), 400

            # Signal to main trading loop that this position should be closed
            SHARED_STATE['close_position_queue'] = SHARED_STATE.get('close_position_queue', [])
            if symbol not in SHARED_STATE['close_position_queue']:
                SHARED_STATE['close_position_queue'].append(symbol)

            log.info(f'Close position requested for {symbol}')
            return jsonify({
                'status': 'close_requested',
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            log.error(f'Error closing position: {e}')
            return jsonify({'error': str(e)}), 500

    return app


def _verify_api_key(api_key):
    """Verify API key from environment."""
    import os
    expected_key = os.getenv('AI_TRADER_API_KEY')
    if not expected_key:
        return True  # No key configured, allow all
    return api_key == expected_key


def run_api_server(shared_state, host='0.0.0.0', port=5555):
    """Run the Flask API server."""
    app = create_api_app(shared_state)
    log.info(f'Starting AI Trader API on {host}:{port}')
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
