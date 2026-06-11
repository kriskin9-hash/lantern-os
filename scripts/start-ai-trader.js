/**
 * Start AI Trader as a child process
 * Monitors health and restarts on failure
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

const AI_TRADER_PATH = process.env.AI_TRADER_PATH || 'C:\Independant AI Trader';
const AI_TRADER_HOST = process.env.AI_TRADER_HOST || '127.0.0.1';
const AI_TRADER_PORT = process.env.AI_TRADER_PORT || 5555;
const logsDir = path.join(__dirname, '..', 'logs');

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

function startAITrader() {
  log(`Starting AI Trader (attempt ${restartCount + 1})...`);

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

  aiTraderProcess = spawn('python', ['main.py'], {
    cwd: AI_TRADER_PATH,
    stdio: ['inherit', 'pipe', 'pipe'],
    detached: false,
    env: childEnv,
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
