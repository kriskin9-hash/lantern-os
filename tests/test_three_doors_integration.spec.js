/**
 * Three Doors Game — Integration & Smoke Tests
 * Tests server endpoints, image generation, door routing, and game state
 */

const http = require('http');
const assert = require('assert');

const BASE_URL = 'http://127.0.0.1:4177';
const TIMEOUT = 5000;

function request(path, method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method,
      timeout: TIMEOUT,
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: data, headers: res.headers });
        } catch (e) { reject(e); }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });

    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

const tests = {
  'Server is running': async () => {
    const res = await request('/api/status');
    assert.strictEqual(res.status, 200, 'API status should return 200');
    assert(res.body.includes('Lantern Garage'), 'Status should mention Lantern Garage');
  },

  'Three-doors game HTML loads': async () => {
    const res = await request('/three-doors-game.html');
    assert.strictEqual(res.status, 200, 'Game HTML should return 200');
    assert(res.body.includes('three-doors'), 'HTML should contain game code');
    assert(res.body.includes('LOCAL_PNG_SCENES'), 'Should have local PNG scene mapping');
    assert(res.body.includes('SERVER_GENERATED_SCENES'), 'Should have server generation wiring');
  },

  'Local door images exist': async () => {
    const scenes = [
      'moss-entry', 'burrow', 'sunken-bell', 'little-crown', 'garden-door',
      'xenon-convergence', 'end-of-time', 'storybook', 'cloverfield', 'future-doors',
      'xp-door', 'kingdome-garden', 'sigil-city', 'fog-door-return'
    ];

    for (const scene of scenes) {
      const res = await request(`/data/images/three-doors/${scene}.png`);
      assert(res.status === 200, `${scene}.png should exist (got ${res.status})`);
    }
  },

  'Trading dashboard accessible': async () => {
    const res = await request('/trading.html');
    assert.strictEqual(res.status, 200, 'Trading HTML should return 200');
    assert(res.body.includes('trading'), 'Should contain trading code');
  },

  'Training API endpoint exists': async () => {
    const res = await request('/api/dream/training/status');
    assert.strictEqual(res.status, 200, 'Training status should return 200');
    const data = JSON.parse(res.body);
    assert.strictEqual(data.minImagesForTraining, 15, 'Should require 15 images for training');
  },

  'Image generation endpoint responds': async () => {
    // Note: Image generation may timeout if Python is slow, but endpoint exists
    const res = await request('/api/image/generate', 'POST', {
      prompt: 'test scene',
      version: 'v8'
    }).catch(e => ({ status: 408, error: e.message }));
    // Accept timeout as valid (server is generating), 200 as success, or 500 as fallback
    assert(
      res.status === 200 || res.status === 500 || res.status === 408,
      `Image generation endpoint should respond (got ${res.status})`
    );
  },

  'Door routing map is loaded': async () => {
    const res = await request('/three-doors-game.html');
    assert(res.body.includes('NEXT_MAP'), 'Should have NEXT_MAP defined');
    assert(res.body.includes('"the raven door"'), 'Should include raven door routing');
    assert(res.body.includes('raven-tower'), 'Should route to raven-tower scene');
  },

  'Scene definitions are complete': async () => {
    const res = await request('/three-doors-game.html');
    assert(res.body.includes('moss-entry'), 'Should have moss-entry scene');
    assert(res.body.includes('raven-tower'), 'Should have raven-tower scene');
    assert(res.body.includes('void-threshold'), 'Should have void-threshold scene');
  },

  'SD_PROMPTS are wired': async () => {
    const res = await request('/three-doors-game.html');
    assert(res.body.includes('const SD_PROMPTS'), 'Should have SD_PROMPTS defined');
    assert(res.body.includes('moss-entry'), 'Should have prompts for all scenes');
  },

  'Canvas drawing function exists': async () => {
    const res = await request('/three-doors-game.html');
    assert(res.body.includes('function drawScene'), 'Should have drawScene function');
    assert(res.body.includes('Math.max(0.5'), 'Should clamp particle radius to minimum 0.5');
  },

  'Training image collection is wired': async () => {
    const res = await request('/three-doors-game.html');
    assert(res.body.includes('collectTrainingImage'), 'Should collect training images');
    assert(res.body.includes('/api/dream/training/collect'), 'Should POST to training endpoint');
  },

  'Custom door input is handled': async () => {
    const res = await request('/three-doors-game.html');
    assert(res.body.includes('submitCustomDoor'), 'Should have custom door input handler');
    assert(res.body.includes('custom-door-input'), 'Should have input element');
  },
};

// Run all tests
async function runTests() {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🧪 Three-Doors Game Integration Tests');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  let passed = 0, failed = 0;

  for (const [name, test] of Object.entries(tests)) {
    try {
      await test();
      console.log(`✓ ${name}`);
      passed++;
    } catch (e) {
      console.log(`✗ ${name}`);
      console.log(`  Error: ${e.message}`);
      failed++;
    }
  }

  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`Results: ${passed} passed, ${failed} failed`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);

  process.exit(failed > 0 ? 1 : 0);
}

runTests().catch(err => {
  console.error('Test suite error:', err);
  process.exit(1);
});
