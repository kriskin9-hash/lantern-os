#!/usr/bin/env node

/**
 * GPT Web API Server
 * Lightweight Playwright-based ChatGPT automation service
 * Listens on localhost:3000 (or PORT env var)
 * POST /api/chat - Send message to ChatGPT, get response
 */

const express = require('express');
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;
const HEADLESS = process.env.HEADLESS === 'false' ? false : true;
const SESSION_DIR = path.join(__dirname, '.sessions');

// Ensure sessions directory exists
if (!fs.existsSync(SESSION_DIR)) {
  fs.mkdirSync(SESSION_DIR, { recursive: true });
}

const app = express();
app.use(express.json());

let browser = null;
let context = null;
let page = null;

/**
 * Initialize browser and authenticate to ChatGPT
 */
async function initializeBrowser() {
  if (browser) return;

  console.log('[GPT Web API] Launching browser...');

  // Try to use existing .chatgpt-profile (pre-authenticated Chrome profile)
  const profilePath = path.join(process.env.USERPROFILE || process.env.HOME, '.chatgpt-profile');
  const sessionPath = path.join(SESSION_DIR, 'chatgpt-session.json');
  let useProfile = false;

  if (fs.existsSync(profilePath)) {
    console.log('[GPT Web API] Using existing Chrome profile:', profilePath);
    context = await chromium.launchPersistentContext(profilePath, {
      headless: HEADLESS
    });
    browser = context.browser();
    useProfile = true;
  } else {
    // Fall back to fresh browser
    browser = await chromium.launch({ headless: HEADLESS });
    let storageState = undefined;

    if (fs.existsSync(sessionPath)) {
      try {
        storageState = JSON.parse(fs.readFileSync(sessionPath, 'utf-8'));
        console.log('[GPT Web API] Using saved session');
      } catch (e) {
        console.warn('[GPT Web API] Failed to load saved session:', e.message);
      }
    }

    context = await browser.newContext({ storageState });
  }

  page = useProfile ? await context.newPage() : page;

  console.log('[GPT Web API] Navigating to ChatGPT...');
  try {
    await page.goto('https://chat.openai.com', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
  } catch (e) {
    console.warn('[GPT Web API] Navigation timeout, continuing...');
  }

  // Check if authentication is needed
  const url = page.url();
  if (url.includes('login') || url.includes('auth')) {
    console.log('[GPT Web API] Authentication required');
    console.log('[GPT Web API] Please log in in the browser window (timeout: 5 minutes)');

    // Wait up to 5 minutes for user to authenticate
    let authenticated = false;
    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(10000);
      const currentUrl = page.url();

      if (!currentUrl.includes('login') && !currentUrl.includes('auth')) {
        console.log('[GPT Web API] Authentication successful');
        authenticated = true;
        break;
      }
    }

    if (!authenticated) {
      throw new Error('Authentication timeout (5 minutes)');
    }
  }

  // Save session for future use
  const newStorageState = await context.storageState();
  fs.writeFileSync(sessionPath, JSON.stringify(newStorageState, null, 2));
  console.log('[GPT Web API] Session saved');

  // Wait for chat interface to be ready
  try {
    // Try multiple selectors to handle different ChatGPT versions
    const selectors = [
      'textarea[placeholder*="message" i]',
      'input[placeholder*="message" i]',
      '[contenteditable="true"]',
      'textarea',
      '[role="textbox"]'
    ];

    let found = false;
    for (const selector of selectors) {
      try {
        await page.waitForSelector(selector, { timeout: 5000 });
        console.log('[GPT Web API] Chat interface ready (using selector: ' + selector + ')');
        found = true;
        break;
      } catch (e) {
        // Continue to next selector
      }
    }

    if (!found) {
      // Take screenshot for debugging
      const screenshotPath = path.join(SESSION_DIR, 'debug-screenshot.png');
      await page.screenshot({ path: screenshotPath });
      console.log('[GPT Web API] Screenshot saved for debugging: ' + screenshotPath);
      throw new Error('No suitable input element found. See debug screenshot: ' + screenshotPath);
    }
  } catch (e) {
    throw new Error('Chat interface not found: ' + e.message);
  }
}

/**
 * Send message to ChatGPT and get response
 */
async function sendMessageToGPT(message) {
  if (!page) {
    throw new Error('Browser not initialized');
  }

  try {
    // Find and focus input field (try multiple selectors)
    const selectors = [
      'textarea[placeholder*="message" i]',
      'input[placeholder*="message" i]',
      '[contenteditable="true"]',
      'textarea',
      '[role="textbox"]'
    ];

    let input = null;
    let usedSelector = null;

    for (const selector of selectors) {
      input = await page.$(selector);
      if (input) {
        usedSelector = selector;
        console.log(`[GPT Web API] Found input field using selector: ${selector}`);
        break;
      }
    }

    if (!input) {
      throw new Error('Message input field not found');
    }

    // Type message (handle both textarea/input and contenteditable)
    console.log(`[GPT Web API] Sending message: ${message.substring(0, 50)}...`);
    await input.focus();

    // For contenteditable, clear previous text
    if (usedSelector === '[contenteditable="true"]') {
      await input.evaluate(el => el.textContent = '');
      await input.type(message, { delay: 10 });
    } else {
      // For textarea/input, clear value
      await input.evaluate(el => el.value = '');
      await input.type(message, { delay: 10 });
    }

    // Send message (Ctrl+Enter or just Enter)
    await page.keyboard.press('Enter');

    // Wait for response to appear
    console.log('[GPT Web API] Waiting for response...');
    await page.waitForTimeout(3000); // Give it time to start generating

    // Extract actual text response from ChatGPT DOM
    let response = '';
    let attempts = 0;
    const maxAttempts = 60; // 60 attempts * 500ms = 30 seconds

    while (attempts < maxAttempts) {
      try {
        // Simple extraction: get innerText of main conversation area
        const assistantResponse = await page.evaluate(() => {
          // Try to find the main conversation area
          let mainArea = document.querySelector('main') ||
                        document.querySelector('[role="main"]') ||
                        document.querySelector('.overflow-hidden') ||
                        document.body;

          if (!mainArea) {
            return null;
          }

          // Get all text
          let fullText = mainArea.innerText || mainArea.textContent || '';

          // Split into lines and find assistant messages (longer blocks of text after user input)
          let lines = fullText.split('\n').filter(line => line.trim().length > 0);

          // Find the last substantial message block (should be assistant response)
          for (let i = lines.length - 1; i >= 0; i--) {
            let line = lines[i].trim();
            // Skip UI elements
            if (line.length > 20 &&
                !line.includes('Copy') &&
                !line.includes('Regenerate') &&
                !line.includes('Edit') &&
                !line.includes('Delete') &&
                !line.includes('Like') &&
                !line.includes('Dislike') &&
                !line.match(/^(test|hello|what|how)/i)) { // Skip short prompts
              return line;
            }
          }

          // Fallback: get last 500 chars that aren't UI
          let text = fullText.substring(Math.max(0, fullText.length - 2000));
          text = text.replace(/Copy|Regenerate|Edit|Delete|Like|Dislike/g, '').trim();
          return text.substring(Math.max(0, text.length - 500));
        });

        if (assistantResponse && assistantResponse.trim().length > 10) {
          response = assistantResponse;
          console.log('[GPT Web API] Response extracted (length: ' + assistantResponse.length + ')');
          break;
        }
      } catch (e) {
        console.log('[GPT Web API] Extraction attempt ' + (attempts + 1) + ' failed');
        // Continue trying
      }

      await page.waitForTimeout(500);
      attempts++;
    }

    if (!response) {
      throw new Error('No response received from ChatGPT after 30 seconds');
    }

    return response;

  } catch (error) {
    console.error('[GPT Web API] Error sending message:', error.message);
    throw error;
  }
}

/**
 * POST /api/chat - Send message and get response
 */
app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;

    if (!message || typeof message !== 'string' || message.trim() === '') {
      return res.status(400).json({
        error: 'Message is required and must be a non-empty string'
      });
    }

    // Initialize browser on first request
    if (!browser) {
      await initializeBrowser();
    }

    // Send message and get response
    const response = await sendMessageToGPT(message.trim());

    res.json({
      response,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('[GPT Web API] Request error:', error.message);
    res.status(500).json({
      error: error.message || 'Failed to get response from ChatGPT'
    });
  }
});

/**
 * GET /health - Health check
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    browser: browser ? 'running' : 'stopped',
    port: PORT
  });
});

/**
 * Graceful shutdown
 */
async function shutdown() {
  console.log('[GPT Web API] Shutting down...');
  if (browser) {
    await browser.close();
  }
  process.exit(0);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

/**
 * Start server
 */
app.listen(PORT, () => {
  console.log(`[GPT Web API] Server running on http://localhost:${PORT}`);
  console.log(`[GPT Web API] POST /api/chat - Send message to ChatGPT`);
  console.log(`[GPT Web API] GET /health - Health check`);
  console.log(`[GPT Web API] Headless mode: ${HEADLESS}`);
});
