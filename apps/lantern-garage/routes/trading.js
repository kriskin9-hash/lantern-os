/**
 * Trading API Routes
 * Serves market data, AI recommendations, and broker integration
 * Integrates with independent AI trader microservice
 */

const http = require('http');
const TradingAPIBridge = require('../lib/trading-api-bridge');

const AI_TRADER_HOST = process.env.AI_TRADER_HOST || '127.0.0.1';
const AI_TRADER_PORT = process.env.AI_TRADER_PORT || 5555;

/**
 * Helper to call AI trader microservice
 */
function callAITrader(path, method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: AI_TRADER_HOST,
      port: AI_TRADER_PORT,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      timeout: 10000
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            data: data ? JSON.parse(data) : null
          });
        } catch (e) {
          reject(new Error('Invalid JSON response from AI trader'));
        }
      });
    });

    req.on('error', err => reject(err));
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('AI trader service timeout'));
    });

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

module.exports = async function tradingRoutes(req, res, url, deps) {
  const { sendJson } = deps;
  const bridge = new TradingAPIBridge();

  // GET /api/trading/status
  // Returns real-time status of all connected APIs
  if (url.pathname === '/api/trading/status' && req.method === 'GET') {
    try {
      const data = await bridge.getDashboardData();
      sendJson(res, data, 200);
    } catch (error) {
      sendJson(res, { error: error.message }, 500);
    }
    return true;
  }

  // GET /api/trading/ibkr/account
  // Returns IBKR account details
  if (url.pathname === '/api/trading/ibkr/account' && req.method === 'GET') {
    try {
      const account = await bridge.getIBKRAccount();
      sendJson(res, { account }, 200);
    } catch (error) {
      sendJson(res, { error: 'IBKR Gateway not available', details: error.message }, 503);
    }
    return true;
  }

  // GET /api/trading/ibkr/positions
  // Returns IBKR open positions
  if (url.pathname === '/api/trading/ibkr/positions' && req.method === 'GET') {
    try {
      const positions = await bridge.getIBKRPositions();
      sendJson(res, { positions }, 200);
    } catch (error) {
      sendJson(res, { error: 'Failed to fetch positions', details: error.message }, 503);
    }
    return true;
  }

  // GET /api/trading/kalshi/events
  // Returns KALSHI open events for prediction markets
  if (url.pathname === '/api/trading/kalshi/events' && req.method === 'GET') {
    try {
      const events = await bridge.getKALSHIEvents();
      sendJson(res, { events }, 200);
    } catch (error) {
      sendJson(res, { error: 'Failed to fetch KALSHI events', details: error.message }, 503);
    }
    return true;
  }

  // GET /api/trading/alpaca/account
  // Returns Alpaca paper trading account
  if (url.pathname === '/api/trading/alpaca/account' && req.method === 'GET') {
    try {
      const account = await bridge.getAlpacaAccount();
      sendJson(res, { account }, 200);
    } catch (error) {
      sendJson(res, { error: 'Alpaca not available', details: error.message }, 503);
    }
    return true;
  }

  // ── AI Trader Integration Routes ──────────────────────────────────────────

  // GET /api/trading/ai-trader/health
  // Check AI trader microservice health
  if (url.pathname === '/api/trading/ai-trader/health' && req.method === 'GET') {
    try {
      const result = await callAITrader('/health');
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, {
        error: 'AI trader service unavailable',
        details: error.message,
        endpoint: `http://${AI_TRADER_HOST}:${AI_TRADER_PORT}`
      }, 503);
    }
    return true;
  }

  // GET /api/trading/ai-trader/signals
  // Get recent AI-generated trading signals
  if (url.pathname === '/api/trading/ai-trader/signals' && req.method === 'GET') {
    try {
      const limit = url.searchParams.get('limit') || 10;
      const result = await callAITrader(`/api/ai-trader/signals?limit=${limit}`);
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Failed to fetch signals', details: error.message }, 500);
    }
    return true;
  }

  // POST /api/trading/ai-trader/signals/generate
  // Manually trigger signal generation
  if (url.pathname === '/api/trading/ai-trader/signals/generate' && req.method === 'POST') {
    try {
      const body = await deps.collectRequestBody(req);
      const payload = body ? JSON.parse(body) : {};
      const result = await callAITrader('/api/ai-trader/signals/generate', 'POST', payload);
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Signal generation failed', details: error.message }, 500);
    }
    return true;
  }

  // GET /api/trading/ai-trader/portfolio
  // Get current portfolio state from AI trader
  if (url.pathname === '/api/trading/ai-trader/portfolio' && req.method === 'GET') {
    try {
      const result = await callAITrader('/api/ai-trader/portfolio');
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Portfolio fetch failed', details: error.message }, 500);
    }
    return true;
  }

  // GET /api/trading/ai-trader/trades
  // Get trade history from AI trader
  if (url.pathname === '/api/trading/ai-trader/trades' && req.method === 'GET') {
    try {
      const limit = url.searchParams.get('limit') || 50;
      const result = await callAITrader(`/api/ai-trader/trades?limit=${limit}`);
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Trade history fetch failed', details: error.message }, 500);
    }
    return true;
  }

  // POST /api/trading/ai-trader/trades
  // Log a new trade
  if (url.pathname === '/api/trading/ai-trader/trades' && req.method === 'POST') {
    try {
      const body = await deps.collectRequestBody(req);
      const payload = body ? JSON.parse(body) : {};
      const result = await callAITrader('/api/ai-trader/trades', 'POST', payload);
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Trade logging failed', details: error.message }, 500);
    }
    return true;
  }

  // GET /api/trading/ai-trader/metrics
  // Get performance metrics
  if (url.pathname === '/api/trading/ai-trader/metrics' && req.method === 'GET') {
    try {
      const result = await callAITrader('/api/ai-trader/metrics');
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Metrics fetch failed', details: error.message }, 500);
    }
    return true;
  }

  // POST /api/trading/ai-trader/scanner/start
  // Start background signal scanner
  if (url.pathname === '/api/trading/ai-trader/scanner/start' && req.method === 'POST') {
    try {
      const result = await callAITrader('/api/ai-trader/scanner/start', 'POST');
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Scanner start failed', details: error.message }, 500);
    }
    return true;
  }

  // POST /api/trading/ai-trader/scanner/stop
  // Stop background signal scanner
  if (url.pathname === '/api/trading/ai-trader/scanner/stop' && req.method === 'POST') {
    try {
      const result = await callAITrader('/api/ai-trader/scanner/stop', 'POST');
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Scanner stop failed', details: error.message }, 500);
    }
    return true;
  }

  // GET /api/trading/ai-trader/scanner/status
  // Get scanner status
  if (url.pathname === '/api/trading/ai-trader/scanner/status' && req.method === 'GET') {
    try {
      const result = await callAITrader('/api/ai-trader/scanner/status');
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Scanner status check failed', details: error.message }, 500);
    }
    return true;
  }

  // GET /api/trading/ai-trader/status
  // Get complete AI trader system status
  if (url.pathname === '/api/trading/ai-trader/status' && req.method === 'GET') {
    try {
      const result = await callAITrader('/api/ai-trader/status');
      sendJson(res, result.data, result.status);
    } catch (error) {
      sendJson(res, { error: 'Status check failed', details: error.message }, 503);
    }
    return true;
  }

  return false;
};
