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

// Mock market data
const MARKET_DATA = {
  sp500: { value: '5,843.25', change: 1.2 },
  nasdaq: { value: '18,427.44', change: 0.8 },
  vix: { value: '14.32', change: -0.15 },
  eurusd: { value: '1.1245', change: 0.05 },
  btcusd: { value: '$67,432', change: 2.3 },
  gold: { value: '$2,087', change: 0.3 },
};

// Mock portfolio
const PORTFOLIO = {
  account: {
    equity: 247500,
    cash: 23400,
    pnl_today: 1250,
    pnl_pct: 0.51,
  },
  positions: [],
};

// Mock zones (price levels for technical analysis)
const ZONES = {
  AAPL: {
    confidence: 82,
    direction: 'BULLISH',
    zones: [
      { type: 'SUPPORT', mid: 180, strength: 85, touches: 3, tier: 'today' },
      { type: 'RESISTANCE', mid: 195, strength: 70, touches: 2, tier: 'weekly' },
    ],
  },
  TSLA: {
    confidence: 75,
    direction: 'BULLISH',
    zones: [
      { type: 'SUPPORT', mid: 230, strength: 75, touches: 2, tier: 'today' },
      { type: 'RESISTANCE', mid: 275, strength: 65, touches: 1, tier: 'weekly' },
    ],
  },
  SPY: {
    confidence: 65,
    direction: 'NEUTRAL',
    zones: [],
  },
};

// Mock signals
const SIGNALS = [
  {
    symbol: 'AAPL',
    type: 'BUY',
    confidence: 0.82,
    description: 'Apple showing strong momentum with breakout above $185. Support at $180.',
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  {
    symbol: 'TSLA',
    type: 'BUY',
    confidence: 0.75,
    description: 'Tesla consolidating after recent rally. Multi-timeframe alignment.',
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
  },
  {
    symbol: 'SPY',
    type: 'HOLD',
    confidence: 0.65,
    description: 'SPY showing mixed signals. Wait for clearer direction.',
    timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
  },
];

// Mock agent logs
const AGENT_LOGS = [
  {
    time: new Date(Date.now() - 2 * 60000).toLocaleTimeString(),
    agent: 'claude',
    type: 'claude',
    body: 'AAPL breakout signal confirmed',
  },
  {
    time: new Date(Date.now() - 5 * 60000).toLocaleTimeString(),
    agent: 'grok',
    type: 'grok',
    body: 'TSLA volatility spike detected',
  },
  {
    time: new Date(Date.now() - 8 * 60000).toLocaleTimeString(),
    agent: 'risk',
    type: 'risk',
    body: 'Portfolio margin utilization: 45%',
  },
];

// Mock recent orders
const RECENT_ORDERS = [
  {
    symbol: 'AAPL',
    side: 'buy',
    qty: 10,
    price: 185.50,
    status: 'filled',
    filled_at: new Date(Date.now() - 60 * 60000).toLocaleString(),
  },
  {
    symbol: 'SPY',
    side: 'buy',
    qty: 5,
    price: 550.25,
    status: 'filled',
    filled_at: new Date(Date.now() - 120 * 60000).toLocaleString(),
  },
];

// Generate watchlist prices
function getWatchlistPrices() {
  const symbols = ['AAPL', 'TSLA', 'GOOGL', 'MSFT', 'NVDA', 'SPY', 'QQQ', 'IWM'];
  return symbols.map(symbol => ({
    ticker: symbol,
    price: 100 + Math.random() * 300,
    chg_pct: (Math.random() - 0.5) * 4,
    is_crypto: false,
  }));
}

// Generate market status
function getMarketStatus() {
  const hour = new Date().getHours();
  const isMarketOpen = hour >= 9 && hour < 16; // 9am-4pm EST simplification

  return {
    market: isMarketOpen ? 'OPEN' : 'CLOSED',
    market_open: isMarketOpen,
    vix: 14.32,
    vix_regime: 'LOW',
    spy_1d: 1.2,
    spy_5d: 2.8,
    day_pnl_pct: 0.51,
  };
}

// HTTP request handler
function requestHandler(req, res) {
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

  // Portfolio / positions
  if (pathname === '/api/positions') {
    res.writeHead(200);
    res.end(JSON.stringify({ account: PORTFOLIO.account, positions: PORTFOLIO.positions }));
    return;
  }

  // Market status
  if (pathname === '/api/market-status') {
    res.writeHead(200);
    res.end(JSON.stringify(getMarketStatus()));
    return;
  }

  // Zones (technical levels)
  if (pathname === '/api/zones') {
    res.writeHead(200);
    res.end(JSON.stringify(ZONES));
    return;
  }

  // Watchlist prices
  if (pathname === '/api/watchlist-prices') {
    res.writeHead(200);
    res.end(JSON.stringify(getWatchlistPrices()));
    return;
  }

  // Agent logs
  if (pathname === '/api/agent-log') {
    res.writeHead(200);
    res.end(JSON.stringify(AGENT_LOGS));
    return;
  }

  // Recent orders
  if (pathname === '/api/orders') {
    res.writeHead(200);
    res.end(JSON.stringify(RECENT_ORDERS));
    return;
  }

  // AI Trading signals
  if (pathname === '/api/ai-trader/signals') {
    const limit = parseInt(url.searchParams.get('limit') || '10', 10);
    res.writeHead(200);
    res.end(JSON.stringify({ signals: SIGNALS.slice(0, limit) }));
    return;
  }

  // News feed (placeholder)
  if (pathname === '/api/news-feed') {
    res.writeHead(200);
    res.end(JSON.stringify({
      news: [
        {
          title: 'Fed Rate Decision',
          source: 'CNBC',
          timestamp: new Date().toISOString(),
          impact: 'HIGH',
        },
      ],
    }));
    return;
  }

  // Default 404
  res.writeHead(404);
  res.end(JSON.stringify({ error: 'Not found' }));
}

// Create and start server
const server = http.createServer(requestHandler);

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
