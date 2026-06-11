/**
 * Trading API Routes
 * Serves market data, AI recommendations, and broker integration
 * Integrates with independent AI trader microservice
 */

const http = require('http');
const TradingAPIBridge = require('../lib/trading-api-bridge');
const { recordOrder, recordSignal, queryRecentTradingRecords } = require('../lib/trading-memory');

const AI_TRADER_HOST = process.env.AI_TRADER_HOST || '127.0.0.1';
const AI_TRADER_PORT = process.env.AI_TRADER_PORT || 5555;

const AI_TRADER_DASHBOARD_HOST = process.env.AI_TRADER_DASHBOARD_HOST || '127.0.0.1';
const AI_TRADER_DASHBOARD_PORT = process.env.AI_TRADER_DASHBOARD_PORT || 5050;

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

/**
 * Helper to call the AI Trader dashboard service (dashboard.py, port 5050)
 */
function callDashboard(path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: AI_TRADER_DASHBOARD_HOST,
      port: AI_TRADER_DASHBOARD_PORT,
      path,
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      timeout: 10000
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error('Invalid JSON response from trading dashboard service'));
        }
      });
    });

    req.on('error', err => reject(err));
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Trading dashboard service timeout'));
    });

    req.end();
  });
}

// Proxy map for the LanternOS-hosted /trading.html and /trading-news.html
// pages, which talk to a single origin (this server) instead of the
// AI Trader dashboard's own port (5050).
const DASHBOARD_PROXY_ROUTES = {
  '/api/trading/dashboard/positions': '/api/positions',
  '/api/trading/dashboard/market-status': '/api/market-status',
  '/api/trading/dashboard/zones': '/api/zones',
  '/api/trading/dashboard/watchlist-prices': '/api/watchlist-prices',
  '/api/trading/dashboard/agent-log': '/api/agent-log',
  '/api/trading/dashboard/orders': '/api/orders',
  '/api/trading/dashboard/news-feed': '/api/news-feed',
};

module.exports = async function tradingRoutes(req, res, url, deps) {
  const { sendJson } = deps;
  const bridge = new TradingAPIBridge();

  // ── /trading.html + /trading-news.html dashboard proxy routes ─────────────
  // GET /api/trading/dashboard/{positions,market-status,zones,watchlist-prices,agent-log,orders,news-feed}
  if (req.method === 'GET' && DASHBOARD_PROXY_ROUTES[url.pathname]) {
    try {
      const proxyPath = DASHBOARD_PROXY_ROUTES[url.pathname];
      const data = await callDashboard(proxyPath);
      // CSF memory wiring: write orders and agent-log to CSF on state change
      if (proxyPath === '/api/orders' && Array.isArray(data?.orders || data)) {
        const orders = data.orders || data;
        for (const o of orders) { recordOrder(o).catch(() => {}); }
      }
      if (proxyPath === '/api/agent-log' && Array.isArray(data?.logs || data)) {
        const logs = data.logs || data;
        for (const s of logs) { recordSignal(s).catch(() => {}); }
      }
      sendJson(res, data, 200);
    } catch (error) {
      sendJson(res, { error: error.message }, 502);
    }
    return true;
  }

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

  // GET /api/trading/csf-records
  // Query recent trading CSF memory records (orders + signals)
  if (url.pathname === '/api/trading/csf-records' && req.method === 'GET') {
    try {
      const limit = parseInt(url.searchParams.get('limit') || '50', 10);
      const records = queryRecentTradingRecords(limit);
      sendJson(res, { records, count: records.length }, 200);
    } catch (error) {
      sendJson(res, { error: 'CSF query failed', details: error.message }, 500);
    }
    return true;
  }

  // GET /api/trading/settings
  // Get API key status (shows which are configured, no secrets exposed)
  // IBKR is always true — configured via Claude Code MCP (read-only market data)
  if (url.pathname === '/api/trading/settings' && req.method === 'GET') {
    const providers = {
      anthropic: !!process.env.ANTHROPIC_API_KEY,
      openai: !!process.env.OPENAI_API_KEY,
      gemini: !!process.env.GEMINI_API_KEY,
      ibkr: true, // Always configured via Claude Code MCP
      alpaca: !!process.env.ALPACA_API_KEY,
      kalshi: !!process.env.KALSHI_API_KEY,
    };
    sendJson(res, {
      configured: providers,
      mcp: {
        ibkr: 'Claude Code MCP: read-only quotes, positions, orderbook, risk data'
      }
    }, 200);
    return true;
  }

  // POST /api/trading/settings
  // Update API keys (only in memory for this session, recommend setting via .env)
  if (url.pathname === '/api/trading/settings' && req.method === 'POST') {
    try {
      const body = await deps.collectRequestBody(req);
      const payload = body ? JSON.parse(body) : {};
      const updated = [];

      if (payload.anthropic) {
        process.env.ANTHROPIC_API_KEY = payload.anthropic;
        updated.push('anthropic');
      }
      if (payload.openai) {
        process.env.OPENAI_API_KEY = payload.openai;
        updated.push('openai');
      }
      if (payload.gemini) {
        process.env.GEMINI_API_KEY = payload.gemini;
        updated.push('gemini');
      }
      if (payload.alpaca) {
        process.env.ALPACA_API_KEY = payload.alpaca;
        updated.push('alpaca');
      }
      if (payload.kalshi) {
        process.env.KALSHI_API_KEY = payload.kalshi;
        updated.push('kalshi');
      }
      if (payload.ibkr_account && payload.ibkr_password) {
        process.env.IBKR_ACCOUNT_ID = payload.ibkr_account;
        process.env.IBKR_PASSWORD = payload.ibkr_password;
        updated.push('ibkr');
      }

      sendJson(res, {
        ok: true,
        updated,
        message: updated.length > 0
          ? `Updated ${updated.join(', ')} (session only; add to .env to persist)`
          : 'No keys updated'
      }, 200);
    } catch (error) {
      sendJson(res, { error: 'Settings update failed', details: error.message }, 400);
    }
    return true;
  }

  return false;
};
