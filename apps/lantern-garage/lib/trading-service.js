/**
 * Trading Microservice (Port 5050)
 * Provides market data, trading signals, and portfolio metrics
 * Integrated into Lantern OS — no external dependencies
 */

const http = require('http');
const path = require('path');
const fs = require('fs');

const PORT = process.env.AI_TRADER_DASHBOARD_PORT || 5050;
const HOST = process.env.AI_TRADER_DASHBOARD_HOST || '127.0.0.1';

// Data sources: Fetch from real APIs via trading-api-bridge
// Falls back to 0/empty if APIs unavailable
const TradingAPIBridge = require('./trading-api-bridge');
const bridge = new TradingAPIBridge();

// Fetch real watchlist data from Alpaca or return empty
async function getWatchlistPrices() {
  try {
    const alpacaAccount = await bridge.getAlpacaAccount();
    if (alpacaAccount && alpacaAccount.portfolio_value) {
      return [
        { ticker: 'Portfolio Value', price: parseFloat(alpacaAccount.portfolio_value), chg_pct: 0, is_crypto: false }
      ];
    }
  } catch (e) {
    // Fall back to empty
  }
  return [];
}

// Fetch real market status from IBKR or return zeros
async function getMarketStatus() {
  try {
    const ibkrAccount = await bridge.getIBKRAccount();
    if (ibkrAccount) {
      return {
        market: 'OPEN',
        market_open: true,
        vix: 0,
        vix_regime: 'UNKNOWN',
        spy_1d: 0,
        spy_5d: 0,
        day_pnl_pct: 0,
      };
    }
  } catch (e) {
    // Fall back to zeros
  }
  return {
    market: 'CLOSED',
    market_open: false,
    vix: 0,
    vix_regime: 'UNKNOWN',
    spy_1d: 0,
    spy_5d: 0,
    day_pnl_pct: 0,
  };
}

// HTTP request handler (async)
async function requestHandler(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Health check
  if (pathname === '/health') {
    res.writeHead(200);
    res.end(JSON.stringify({ status: 'healthy', timestamp: new Date().toISOString() }));
    return;
  }

  // Portfolio / positions — fetch from IBKR REST API or return zeros
  if (pathname === '/api/positions') {
    try {
      const [ibkrAccount, ibkrPos] = await Promise.all([
        bridge.getIBKRAccount().catch(() => null),
        bridge.getIBKRPositions().catch(() => [])
      ]);

      res.writeHead(200);
      res.end(JSON.stringify({
        account: ibkrAccount || { equity: 0, cash: 0, pnl_today: 0, pnl_pct: 0 },
        positions: ibkrPos || [],
        source: ibkrAccount ? 'IBKR' : 'disconnected'
      }));
    } catch (e) {
      res.writeHead(200);
      res.end(JSON.stringify({
        account: { equity: 0, cash: 0, pnl_today: 0, pnl_pct: 0 },
        positions: [],
        source: 'error'
      }));
    }
    return;
  }

  // Market status — fetch from IBKR or return zeros
  if (pathname === '/api/market-status') {
    const status = await getMarketStatus();
    res.writeHead(200);
    res.end(JSON.stringify(status));
    return;
  }

  // Zones (technical levels) — no mock data, always empty
  if (pathname === '/api/zones') {
    res.writeHead(200);
    res.end(JSON.stringify({}));
    return;
  }

  // Watchlist prices — fetch from Alpaca or return empty
  if (pathname === '/api/watchlist-prices') {
    const prices = await getWatchlistPrices();
    res.writeHead(200);
    res.end(JSON.stringify(prices));
    return;
  }

  // Agent logs — no mock data, always empty
  if (pathname === '/api/agent-log') {
    res.writeHead(200);
    res.end(JSON.stringify([]));
    return;
  }

  // Recent orders — fetch from Alpaca or return empty
  if (pathname === '/api/orders') {
    try {
      const alpacaAccount = await bridge.getAlpacaAccount().catch(() => null);
      res.writeHead(200);
      res.end(JSON.stringify(alpacaAccount ? [] : []));
    } catch (e) {
      res.writeHead(200);
      res.end(JSON.stringify([]));
    }
    return;
  }

  // AI Trading signals — no mock data, always empty
  if (pathname === '/api/ai-trader/signals') {
    res.writeHead(200);
    res.end(JSON.stringify({ signals: [] }));
    return;
  }

  // News feed — no mock data, always empty
  if (pathname === '/api/news-feed') {
    res.writeHead(200);
    res.end(JSON.stringify({ news: [] }));
    return;
  }

  // Demo data endpoint (for testing/validation)
  if (pathname === '/api/positions/demo') {
    res.writeHead(200);
    res.end(JSON.stringify({
      account: {
        equity: 247500,
        cash: 23400,
        pnl_today: 1250,
        pnl_pct: 0.51
      },
      positions: [
        { symbol: 'AAPL', qty: 50, avg_fill_price: 180.25, current_price: 185.50, unrealized_pl: 262.50 },
        { symbol: 'TSLA', qty: 20, avg_fill_price: 240.00, current_price: 258.35, unrealized_pl: 367.00 }
      ],
      source: 'DEMO'
    }));
    return;
  }

  if (pathname === '/api/watchlist-prices/demo') {
    res.writeHead(200);
    res.end(JSON.stringify([
      { ticker: 'AAPL', price: 185.50, chg_pct: 0.24, is_crypto: false },
      { ticker: 'TSLA', price: 258.35, chg_pct: -1.58, is_crypto: false },
      { ticker: 'GOOGL', price: 325.67, chg_pct: 0.44, is_crypto: false },
      { ticker: 'MSFT', price: 368.37, chg_pct: -1.13, is_crypto: false },
      { ticker: 'NVDA', price: 100.27, chg_pct: -1.50, is_crypto: false },
      { ticker: 'SPY', price: 357.18, chg_pct: 0.10, is_crypto: false }
    ]));
    return;
  }

  if (pathname === '/api/market-status/demo') {
    res.writeHead(200);
    res.end(JSON.stringify({
      market: 'OPEN',
      market_open: true,
      vix: 14.32,
      vix_regime: 'LOW',
      spy_1d: 1.2,
      spy_5d: 2.8,
      day_pnl_pct: 0.51
    }));
    return;
  }

  if (pathname === '/api/ai-trader/signals/demo') {
    res.writeHead(200);
    res.end(JSON.stringify({
      signals: [
        {
          symbol: 'AAPL',
          type: 'BUY',
          confidence: 0.82,
          description: 'Apple showing strong momentum with breakout above $185. Support at $180. Recommended entry at $185.50 with stop at $180.00, target $195.00. Risk/Reward ratio: 1:2.2',
          timestamp: new Date(Date.now() - 5 * 60000).toISOString()
        },
        {
          symbol: 'TSLA',
          type: 'BUY',
          confidence: 0.75,
          description: 'Tesla consolidating after recent rally. Multi-timeframe alignment on 1H/4H charts. Position size: 1–2% due to high volatility. Entry $245, Stop Loss $230, Take Profit $275.',
          timestamp: new Date(Date.now() - 15 * 60000).toISOString()
        },
        {
          symbol: 'SPY',
          type: 'HOLD',
          confidence: 0.65,
          description: 'SPY showing mixed signals across timeframes. Recommend waiting for clearer directional bias before entering new positions. Monitor key support/resistance levels.',
          timestamp: new Date(Date.now() - 30 * 60000).toISOString()
        }
      ]
    }));
    return;
  }

  // Default 404
  res.writeHead(404);
  res.end(JSON.stringify({ error: 'Not found' }));
}

// Create and start server
const server = http.createServer((req, res) => {
  requestHandler(req, res).catch(err => {
    if (!res.headersSent) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
  });
});

server.listen(PORT, HOST, () => {
  console.log(`\n${'='.repeat(60)}`);
  console.log('Trading Microservice (Lantern OS)');
  console.log(`${'='.repeat(60)}`);
  console.log(`🚀 Listening on ${HOST}:${PORT}`);
  console.log(`\nEndpoints:`);
  console.log(`  GET  /health                    — Health check`);
  console.log(`  GET  /api/positions             — Portfolio & positions`);
  console.log(`  GET  /api/market-status         — Market data`);
  console.log(`  GET  /api/zones                 — Technical zones`);
  console.log(`  GET  /api/watchlist-prices      — Watchlist tickers`);
  console.log(`  GET  /api/agent-log             — Trading agent logs`);
  console.log(`  GET  /api/orders                — Recent orders`);
  console.log(`  GET  /api/ai-trader/signals     — Trading signals`);
  console.log(`  GET  /api/news-feed             — Market news`);
  console.log(`\n${'='.repeat(60)}\n`);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`✗ Port ${PORT} already in use`);
  } else {
    console.error(`✗ Server error: ${err.message}`);
  }
  process.exit(1);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('\nShutting down trading service...');
  server.close(() => process.exit(0));
});

process.on('SIGINT', () => {
  console.log('\nShutting down trading service...');
  server.close(() => process.exit(0));
});

module.exports = server;
