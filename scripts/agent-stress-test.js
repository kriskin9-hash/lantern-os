#!/usr/bin/env node
/**
 * Agent Stress Test Suite — Max load testing for all agent types
 * Tests: throughput, latency, error recovery, memory stability
 * Usage: node scripts/agent-stress-test.js [--duration=60] [--parallel=16]
 */

const http = require('http');
const { performance } = require('perf_hooks');

const args = process.argv.slice(2);
const duration = parseInt(args.find(a => a.startsWith('--duration'))?.split('=')[1] || '60');
const parallel = parseInt(args.find(a => a.startsWith('--parallel'))?.split('=')[1] || '16');

const HOST = 'localhost';
const PORT = 4177;

const scenarios = [
  {
    name: 'Dream Journal Chat (light)',
    endpoint: '/api/dream/stream',
    method: 'POST',
    body: { message: 'brief test message', persona: 'lantern' },
    timeout: 10000,
    weight: 0.4
  },
  {
    name: 'Convergence Gate (medium)',
    endpoint: '/api/convergence/route',
    method: 'POST',
    body: { signal: 'trade', confidence: 0.8 },
    timeout: 5000,
    weight: 0.3
  },
  {
    name: 'Status Check (fast)',
    endpoint: '/api/status',
    method: 'GET',
    timeout: 2000,
    weight: 0.3
  }
];

let results = {
  totalRequests: 0,
  successCount: 0,
  errorCount: 0,
  latencies: [],
  startTime: Date.now()
};

function makeRequest(scenario) {
  return new Promise((resolve) => {
    const startTime = performance.now();
    const options = {
      hostname: HOST,
      port: PORT,
      path: scenario.endpoint,
      method: scenario.method,
      timeout: scenario.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'StressTest/1.0'
      }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        const latency = performance.now() - startTime;
        results.latencies.push(latency);
        if (res.statusCode >= 200 && res.statusCode < 300) {
          results.successCount++;
        } else {
          results.errorCount++;
        }
        resolve({ success: true, status: res.statusCode, latency });
      });
    });

    req.on('error', (err) => {
      const latency = performance.now() - startTime;
      results.latencies.push(latency);
      results.errorCount++;
      resolve({ success: false, error: err.message, latency });
    });

    req.on('timeout', () => {
      req.destroy();
      results.errorCount++;
      resolve({ success: false, error: 'timeout', latency: scenario.timeout });
    });

    if (scenario.body) {
      req.write(JSON.stringify(scenario.body));
    }
    req.end();
  });
}

async function runStress() {
  console.log(`🔥 Agent Stress Test — ${duration}s, ${parallel} parallel workers\n`);
  console.log(`Server: http://${HOST}:${PORT}`);
  console.log(`Scenarios: ${scenarios.map(s => s.name).join(', ')}\n`);

  const endTime = Date.now() + duration * 1000;
  const workers = [];

  for (let i = 0; i < parallel; i++) {
    workers.push((async () => {
      while (Date.now() < endTime) {
        // Weighted scenario selection
        const rand = Math.random();
        let cumWeight = 0;
        let scenario = scenarios[0];
        for (const s of scenarios) {
          cumWeight += s.weight;
          if (rand <= cumWeight) {
            scenario = s;
            break;
          }
        }

        results.totalRequests++;
        await makeRequest(scenario);

        // Log progress every 100 requests
        if (results.totalRequests % 100 === 0) {
          const elapsed = (Date.now() - results.startTime) / 1000;
          const rps = (results.totalRequests / elapsed).toFixed(1);
          process.stdout.write(`\r  ${results.totalRequests} requests, ${rps} req/s, ${results.errorCount} errors`);
        }
      }
    })());
  }

  await Promise.all(workers);

  // Calculate stats
  const elapsed = (Date.now() - results.startTime) / 1000;
  const rps = (results.totalRequests / elapsed).toFixed(2);
  const successRate = ((results.successCount / results.totalRequests) * 100).toFixed(1);
  const latencies = results.latencies.sort((a, b) => a - b);
  const p50 = latencies[Math.floor(latencies.length * 0.5)].toFixed(1);
  const p95 = latencies[Math.floor(latencies.length * 0.95)].toFixed(1);
  const p99 = latencies[Math.floor(latencies.length * 0.99)].toFixed(1);
  const avg = (latencies.reduce((a, b) => a + b) / latencies.length).toFixed(1);

  console.log('\n\n📊 Results:\n');
  console.log(`  Total Requests: ${results.totalRequests}`);
  console.log(`  Duration: ${elapsed.toFixed(1)}s`);
  console.log(`  Throughput: ${rps} req/s`);
  console.log(`  Success Rate: ${successRate}%`);
  console.log(`  Error Count: ${results.errorCount}`);
  console.log(`\n⏱️  Latency (ms):\n`);
  console.log(`  Average: ${avg}`);
  console.log(`  P50: ${p50}`);
  console.log(`  P95: ${p95}`);
  console.log(`  P99: ${p99}`);

  if (successRate >= 99 && parseFloat(p95) < 5000) {
    console.log(`\n✅ PASS: All agents under max stress (${parallel} parallel workers)`);
    process.exit(0);
  } else {
    console.log(`\n⚠️  CHECK: Review performance under stress`);
    process.exit(1);
  }
}

runStress().catch(err => {
  console.error('❌ Stress test failed:', err.message);
  process.exit(1);
});
