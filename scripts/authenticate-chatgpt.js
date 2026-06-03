#!/usr/bin/env node
/**
 * ChatGPT Authentication Script for Lantern OS GPT Web API
 *
 * Launches a visible Chrome browser, navigates to chat.openai.com,
 * and saves the authenticated profile to ~/.chatgpt-profile.
 *
 * Usage:
 *   node scripts/authenticate-chatgpt.js
 *
 * After auth, the GPT Web API (port 3000) will auto-detect the profile
 * and skip the login prompt on subsequent starts.
 */

const { chromium } = require('playwright');
const path = require('path');
const os = require('os');

const profilePath = path.join(os.homedir(), '.chatgpt-profile');

(async () => {
  console.log('[Auth] Lantern OS — ChatGPT Authentication');
  console.log('[Auth] Profile will be saved to:', profilePath);

  const context = await chromium.launchPersistentContext(profilePath, {
    headless: false,
    viewport: { width: 1280, height: 800 }
  });

  const page = await context.newPage();
  console.log('[Auth] Navigating to chat.openai.com...');

  try {
    await page.goto('https://chat.openai.com', {
      waitUntil: 'networkidle',
      timeout: 60000
    });
  } catch (e) {
    console.warn('[Auth] Navigation timeout (60s), continuing anyway...');
  }

  const url = page.url();
  if (url.includes('login') || url.includes('auth')) {
    console.log('[Auth] Please log in to ChatGPT in the browser window.');
    console.log('[Auth] After you are fully logged in and see the chat interface,');
    console.log('[Auth] press Enter in this terminal to save the session.');
  } else {
    console.log('[Auth] Already authenticated! Press Enter to save and exit.');
  }

  process.stdin.setRawMode(true);
  process.stdin.resume();
  process.stdin.setEncoding('utf8');

  process.stdin.once('data', async () => {
    await context.close();
    console.log('[Auth] Session saved to:', profilePath);
    console.log('[Auth] You can now start the GPT Web API headlessly:');
    console.log('  npm start --prefix integrations/gm-agent-orchestrator/tools/gpt-web-api');
    process.exit(0);
  });
})();
