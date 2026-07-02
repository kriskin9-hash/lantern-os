/**
 * Start AI Trader as a child process
 * Monitors health and restarts on failure
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');
const os = require('os');
const crypto = require('crypto');

// Best-effort .env load so a standalone run (`node scripts/start-ai-trader.js`) sees
// ALPACA_API_KEY for the per-account lock. When spawned by server.js the env is already
// populated; dotenv won't override existing vars, so this is a no-op there.
try { require('dotenv').config({ path: path.resolve(__dirname, '..', '.env') }); } catch (_) {}

// The trader now runs FULLY INTERNALLY from src/trading_agents/orchestrator.py — no
// external C:\Independant AI Trader dependency. Override AI_TRADER_PATH only to point at a
// different checkout of the orchestrator package.
const AI_TRADER_PATH = process.env.AI_TRADER_PATH || path.join(__dirname, '..', 'src', 'trading_agents');
const AI_TRADER_ENTRY = process.env.AI_TRADER_ENTRY || 'orchestrator.py';
const AI_TRADER_HOST = process.env.AI_TRADER_HOST || '127.0.0.1';
const AI_TRADER_PORT = process.env.AI_TRADER_PORT || 5555;
const logsDir = path.join(__dirname, '..', 'logs');

// ── Per-account run lock ──────────────────────────────────────────────────────
// The trader is bound to ONE Alpaca account (its API key, read from env by main.py /
// agents.py). The SAME account must never run on two servers at once — they would place
// opposing orders on the shared account and churn it. DIFFERENT accounts hash to DIFFERENT
// lock files and may run concurrently. The lock is held by THIS manager process for the
// trader's lifetime and released on exit; a stale lock (dead owner) is taken over.
const _acctHash = process.env.ALPACA_API_KEY
  ? crypto.createHash('sha256').update(process.env.ALPACA_API_KEY).digest('hex').slice(0, 12)
  : 'no-key';
const LOCK_PATH = path.join(os.tmpdir(), `lantern-ai-trader-${_acctHash}.lock`);
let _lockHeld = false;

function acquireAccountLock() {
  const mine = JSON.stringify({ pid: process.pid, host: os.hostname(),
    port: AI_TRADER_PORT, acct: _acctHash, startedAt: new Date().toISOString() });
  try {
    const fd = fs.openSync(LOCK_PATH, 'wx'); // atomic create-exclusive
    fs.writeSync(fd, mine); fs.closeSync(fd);
    _lockHeld = true;
    return { ok: true };
  } catch (e) {
    if (e.code !== 'EEXIST') return { ok: false, reason: `lock error: ${e.message}` };
    let owner = {};
    try { owner = JSON.parse(fs.readFileSync(LOCK_PATH, 'utf8')); } catch (_) {}
    if (owner.pid && owner.host === os.hostname()) {
      try { process.kill(owner.pid, 0); // 0 = liveness probe, doesn't signal
        return { ok: false, reason: `account already running here (pid ${owner.pid} since ${owner.startedAt})` };
      } catch (_) { /* owner dead → stale lock, fall through and take over */ }
    } else if (owner.pid) {
      return { ok: false, reason: `account locked by host ${owner.host} (pid ${owner.pid}); refusing duplicate` };
    }
    try { fs.writeFileSync(LOCK_PATH, mine); _lockHeld = true; return { ok: true, tookOver: true }; }
    catch (e2) { return { ok: false, reason: `could not claim stale lock: ${e2.message}` }; }
  }
}

function releaseAccountLock() {
  if (!_lockHeld) return;
  try {
    const o = JSON.parse(fs.readFileSync(LOCK_PATH, 'utf8'));
    if (o.pid === process.pid) fs.unlinkSync(LOCK_PATH);
  } catch (_) { /* already gone / unreadable */ }
  _lockHeld = false;
}
process.on('exit', releaseAccountLock);

// Ensure logs directory exists
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

const logStream = fs.createWriteStream(path.join(logsDir, 'ai-trader.log'), { flags: 'a' });

let aiTraderProcess = null;
let isHealthy = false;
let startupTime = Date.now();
let restartCount = 0;
const MAX_RESTARTS_PER_HOUR = 5;

function log(message) {
  const timestamp = new Date().toISOString();
  const fullMessage = `[${timestamp}] ${message}\n`;
  process.stdout.write(fullMessage);
  logStream.write(fullMessage);
}

function checkHealth() {
  return new Promise((resolve) => {
    const options = {
      hostname: AI_TRADER_HOST,
      port: AI_TRADER_PORT,
      path: '/health',
      method: 'GET',
      timeout: 3000,
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve(res.statusCode === 200 && parsed.status === 'healthy');
        } catch (e) {
          resolve(false);
        }
      });
    });

    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

async function waitForHealth(maxAttempts = 30, delayMs = 500) {
  for (let i = 0; i < maxAttempts; i++) {
    const healthy = await checkHealth();
    if (healthy) {
      log(`✓ AI Trader health check passed`);
      isHealthy = true;
      return true;
    }
    if (i < maxAttempts - 1) {
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }
  }
  log(`✗ AI Trader failed health checks after ${maxAttempts * delayMs / 1000}s`);
  return false;
}

async function startAITrader() {
  // ── Singleton guard ────────────────────────────────────────────────────────
  // The AI Trader is ONE service (its health server owns AI_TRADER_PORT / 5555).
  // Both dual-boot servers (stable 4177 + dev 4178) and autostart each run this
  // manager, so without this guard we spawn 2-3 copies of `python main.py` — and
  // multiple trading loops on the SAME Alpaca account place opposing orders and
  // churn the account to death on market-order spread + fees (observed 2026-07-02:
  // 3 instances, rapid BUY→SELL round-trips, negative day P&L). If a trader is
  // already healthy, DO NOT spawn a duplicate — attach as a passive monitor.
  if (await checkHealth()) {
    log(`✓ AI Trader already healthy on ${AI_TRADER_HOST}:${AI_TRADER_PORT} — NOT spawning a duplicate (singleton guard).`);
    isHealthy = true;
    return;
  }

  // Per-account lock: refuse to spawn a second trader for the SAME Alpaca account.
  const lock = acquireAccountLock();
  if (!lock.ok) {
    log(`✗ Not starting AI Trader — ${lock.reason}. (account ${_acctHash}; per-account singleton)`);
    return;
  }
  if (lock.tookOver) log(`↺ Took over a stale account lock for ${_acctHash}.`);

  log(`Starting AI Trader (attempt ${restartCount + 1})... (account ${_acctHash})`);

  // Pass environment variables to AI Trader
  const childEnv = {
    ...process.env,
    // Alpaca credentials
    ALPACA_API_KEY: process.env.ALPACA_API_KEY || '',
    ALPACA_SECRET_KEY: process.env.ALPACA_SECRET_KEY || '',
    // Trading config
    PORTFOLIO_VALUE: process.env.PORTFOLIO_VALUE || '100000',
    CONFIDENCE_THRESH: process.env.CONFIDENCE_THRESH || '60',
    // Telegram (optional)
    TELEGRAM_BOT_TOKEN: process.env.TELEGRAM_BOT_TOKEN || '',
    TELEGRAM_CHAT_ID: process.env.TELEGRAM_CHAT_ID || '',
  };

  aiTraderProcess = spawn('python', [AI_TRADER_ENTRY], {
    cwd: AI_TRADER_PATH,
    stdio: ['inherit', 'pipe', 'pipe'],
    detached: false,
    // PYTHONPATH so the package's `from agents import ...` etc. resolve regardless of cwd.
    env: { ...childEnv, PYTHONPATH: AI_TRADER_PATH },
  });

  // Log both stdout and stderr
  aiTraderProcess.stdout.pipe(logStream);
  aiTraderProcess.stderr.pipe(logStream);

  aiTraderProcess.on('error', (err) => {
    log(`✗ AI Trader spawn error: ${err.message}`);
    isHealthy = false;
    scheduleRestart();
  });

  aiTraderProcess.on('exit', (code, signal) => {
    log(`AI Trader exited with code ${code}, signal ${signal}`);
    isHealthy = false;
    if (code !== 0 && code !== null) {
      scheduleRestart();
    }
  });

  // Wait for health check
  waitForHealth().then((healthy) => {
    if (!healthy) {
      log(`Warning: AI Trader health check failed`);
      isHealthy = false;
    }
  });
}

function scheduleRestart() {
  const now = Date.now();
  const hourAgo = now - 60 * 60 * 1000;
  
  if (startupTime > hourAgo) {
    restartCount++;
    if (restartCount > MAX_RESTARTS_PER_HOUR) {
      log(`✗ Too many restarts (${restartCount}) in the last hour. Giving up.`);
      process.exit(1);
    }
  } else {
    restartCount = 1;
    startupTime = now;
  }

  const delayMs = Math.min(1000 * Math.pow(2, restartCount - 1), 30000);
  log(`Scheduling AI Trader restart in ${delayMs}ms...`);
  setTimeout(startAITrader, delayMs);
}

// Health check loop (every 30s)
setInterval(async () => {
  const healthy = await checkHealth();
  if (healthy !== isHealthy) {
    isHealthy = healthy;
    const status = healthy ? '✓ healthy' : '✗ unhealthy';
    log(`AI Trader status: ${status}`);
  }
}, 30000);

// Start the process
log('='.repeat(60));
log('AI Trader Process Manager Started');
log(`AI_TRADER_PATH: ${AI_TRADER_PATH}`);
log(`AI_TRADER_HOST: ${AI_TRADER_HOST}`);
log(`AI_TRADER_PORT: ${AI_TRADER_PORT}`);
log('='.repeat(60));

if (!fs.existsSync(path.join(AI_TRADER_PATH, AI_TRADER_ENTRY))) {
  log(`AI_TRADER_PATH (${AI_TRADER_PATH}) has no ${AI_TRADER_ENTRY} — internal orchestrator missing. Skipping (set LANTERN_DISABLE_TRADING=1 to silence this manager entirely).`);
  process.exit(0);
}

startAITrader();

// Graceful shutdown
process.on('SIGTERM', () => {
  log('SIGTERM received, shutting down AI Trader...');
  if (aiTraderProcess) {
    aiTraderProcess.kill('SIGTERM');
  }
  setTimeout(() => process.exit(0), 5000);
});

process.on('SIGINT', () => {
  log('SIGINT received, shutting down AI Trader...');
  if (aiTraderProcess) {
    aiTraderProcess.kill('SIGINT');
  }
  setTimeout(() => process.exit(0), 5000);
});

module.exports = { startAITrader, isHealthy: () => isHealthy };
