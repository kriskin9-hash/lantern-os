/**
 * Unified System Overview API
 * Single endpoint aggregating all operational dashboard data
 * Used by: operations.html (orchestration, agents, leaderboard, settings tabs)
 *
 * Combines data from:
 * - Queue status (pending, assigned, completed, failed)
 * - Agent slots and health
 * - Node mesh registration
 * - Provider configuration and health
 * - Tesseract fleet data
 * - Performance leaderboard
 */

const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

let _cacheData = null;
let _cacheTime = 0;
const CACHE_TTL_MS = 30000; // 30-second cache

function getQueueStats(repoRoot) {
  const stats = { pending: 0, assigned: 0, completed: 0, failed: 0 };
  const baseDir = path.join(repoRoot, 'data', 'agent-work-queue');

  ['pending', 'assigned', 'completed', 'failed'].forEach(status => {
    const statusDir = path.join(baseDir, status);
    if (fs.existsSync(statusDir)) {
      // Look for JSONL files and count entries
      const jsonlFiles = fs.readdirSync(statusDir).filter(f => f.endsWith('.jsonl'));
      jsonlFiles.forEach(file => {
        try {
          const content = fs.readFileSync(path.join(statusDir, file), 'utf8');
          const lines = content.trim().split('\n').filter(l => l.length > 0);
          stats[status] += lines.length;
        } catch (e) {
          // Skip malformed files
        }
      });
    }
  });

  const total = stats.pending + stats.assigned + stats.completed + stats.failed;
  const successRate = total > 0 ? Math.round((stats.completed / total) * 100) : 0;

  return { ...stats, totalIssues: total, successRate };
}

function getNodeMesh(repoRoot) {
  const meshDir = path.join(repoRoot, 'data', 'nodes');
  const nodes = [];
  let aliveCount = 0;

  if (fs.existsSync(meshDir)) {
    const nodeFiles = fs.readdirSync(meshDir).filter(f => f.endsWith('.json'));
    nodeFiles.forEach(file => {
      try {
        const nodeData = JSON.parse(fs.readFileSync(path.join(meshDir, file), 'utf8'));
        const heartbeatAge = Date.now() - (nodeData.lastHeartbeat ? new Date(nodeData.lastHeartbeat).getTime() : 0);
        const isAlive = heartbeatAge < 120000; // 2 minutes

        nodes.push({
          id: nodeData.nodeId || file.replace('.json', ''),
          hostname: nodeData.hostname || 'unknown',
          uptime_ms: nodeData.uptimeMs || 0,
          heartbeat_age_ms: heartbeatAge,
          status: isAlive ? 'alive' : 'stale'
        });

        if (isAlive) aliveCount++;
      } catch (e) {
        // Skip malformed node files
      }
    });
  }

  return { nodes, nodeCount: nodes.length, aliveCount };
}

function getTesseractFleet(repoRoot) {
  const tessPath = path.join(repoRoot, 'data', 'agent-fleet', 'tesseract-latest.json');
  let tessData = { slots: [], live_workers: 0, status: 'unknown' };

  if (fs.existsSync(tessPath)) {
    try {
      tessData = JSON.parse(fs.readFileSync(tessPath, 'utf8'));
    } catch (e) {
      // Return empty structure on parse error
    }
  }

  return tessData;
}

function getProviderStatus() {
  // Stub: Would read from provider health tracking
  return {
    configured: [
      { name: 'anthropic', model: 'claude-opus', status: 'unknown' },
      { name: 'gemini', model: 'gemini-pro', status: 'unknown' },
      { name: 'openai', model: 'gpt-4o-mini', status: 'unknown' }
    ],
    health: {
      gemini: { status: 'unknown', lastCheck: null },
      anthropic: { status: 'unknown', lastCheck: null },
      openai: { status: 'unknown', lastCheck: null },
      xai: { status: 'unknown', lastCheck: null }
    },
    memory: { entries: 0, sizeBytes: 0 }
  };
}

function getVersionInfo(repoRoot) {
  try {
    const commit = execSync('git rev-parse HEAD', { cwd: repoRoot, encoding: 'utf8' }).trim().slice(0, 7);
    const branch = execSync('git rev-parse --abbrev-ref HEAD', { cwd: repoRoot, encoding: 'utf8' }).trim();
    const tag = execSync('git describe --tags --always', { cwd: repoRoot, encoding: 'utf8' }).trim();
    const date = execSync('git log -1 --format=%cI', { cwd: repoRoot, encoding: 'utf8' }).trim();

    return { commit, branch, tag, date };
  } catch (e) {
    return { commit: 'unknown', branch: 'unknown', tag: 'unknown', date: new Date().toISOString() };
  }
}

function getAggregatedSystemOverview(repoRoot) {
  const now = Date.now();

  // Return cached data if fresh
  if (_cacheData && (now - _cacheTime) < CACHE_TTL_MS) {
    return _cacheData;
  }

  // Aggregate all data
  const queue = getQueueStats(repoRoot);
  const mesh = getNodeMesh(repoRoot);
  const tesseract = getTesseractFleet(repoRoot);
  const providers = getProviderStatus();
  const version = getVersionInfo(repoRoot);

  _cacheData = {
    timestamp: new Date().toISOString(),
    system: {
      health: queue.successRate > 50 ? 'healthy' : queue.totalIssues === 0 ? 'idle' : 'degraded',
      version,
      readiness: {
        chat: 'ready',
        agents: tesseract.slots && tesseract.slots.length > 0 ? 'ready' : 'offline',
        queue: queue.totalIssues > 0 ? 'working' : 'idle',
        providers: providers.configured.length > 0 ? 'ready' : 'unconfigured'
      }
    },
    agents: {
      personas: [
        { id: 'keystone', name: 'Keystone', symbol: '⚙️', role: 'technical_auditor' },
        { id: 'lantern', name: 'Lantern', symbol: '🔦', role: 'dreamer' },
        { id: 'blinkbug', name: 'Blinkbug', symbol: '🐛', role: 'debugger' },
        { id: 'waterfall', name: 'Waterfall', symbol: '💧', role: 'flow' },
        { id: 'xenon', name: 'Xenon', symbol: '✨', role: 'explorer' },
        { id: 'founder', name: 'Founder', symbol: '👑', role: 'architect' }
      ],
      slots: tesseract.slots || [],
      workers: {}, // Stub: Would aggregate from mesh data
      stats: {
        totalActive: tesseract.live_workers || 0,
        totalIdle: (tesseract.slots || []).length - (tesseract.live_workers || 0),
        avgLatencyMs: 0,
        successRate: queue.successRate
      }
    },
    queue,
    providers,
    mesh,
    leaderboard: {
      topByType: {}, // Stub: Would fetch from agent-performance routes
      topOverall: [] // Stub: Would fetch from agent-performance routes
    }
  };

  _cacheTime = now;
  return _cacheData;
}

module.exports = async function systemOverviewRoutes(req, res, url, deps) {
  const { sendJson, repoRoot } = deps;

  if (url.pathname === '/api/system/overview' && req.method === 'GET') {
    try {
      const overview = getAggregatedSystemOverview(repoRoot);
      sendJson(res, { ok: true, data: overview });
    } catch (err) {
      console.error('[System Overview] Error:', err);
      sendJson(res, { ok: false, error: err.message }, 500);
    }
    return true;
  }

  return false;
};
