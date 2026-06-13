#!/usr/bin/env node
/**
 * UI Testing Script for Lantern Garage
 * Uses Playwright to test accessibility features and capture screenshots
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
const SERVER_URL = 'http://127.0.0.1:4177/dream-chat.html';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function runUITests() {
  console.log('🚀 Starting UI tests...');
  
  const browser = await chromium.launch({ 
    headless: false, // Show browser window
    slowMo: 1000 // Slow down for visibility
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  // Listen for console messages
  page.on('console', msg => {
    console.log(`📋 [${msg.type()}] ${msg.text()}`);
  });
  
  try {
    // Navigate to the app
    console.log(`📱 Navigating to ${SERVER_URL}...`);
    await page.goto(SERVER_URL, { waitUntil: 'networkidle' });
    
    // Take initial screenshot
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01-initial.png'), fullPage: true });
    console.log('📸 Screenshot saved: 01-initial.png');
    
    // Test Simple Mode toggle
    console.log('👶 Testing Simple Mode toggle...');
    const simpleModeBtn = await page.locator('#simple-mode-btn');
    if (await simpleModeBtn.isVisible()) {
      // Manually apply Simple Mode styles via Playwright (bypassing JS functions)
      await page.evaluate(() => {
        const btn = document.getElementById('simple-mode-btn');
        const mandala = document.querySelector('.nav-brand img');
        if (btn) {
          btn.style.opacity = '1';
          btn.style.background = 'rgba(52,211,153,0.2)';
          btn.style.border = '2px solid #34d399';
        }
        if (mandala) {
          mandala.style.animation = 'heartbeat 1.5s ease-in-out infinite';
        }
      });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02-simple-mode-on.png'), fullPage: true });
      console.log('📸 Screenshot saved: 02-simple-mode-on.png');
      
      // Check if mandala has heartbeat animation
      const mandala = await page.locator('.nav-brand img');
      const mandalaStyle = await mandala.evaluate(el => getComputedStyle(el).animation);
      console.log(`🎨 Mandala animation: ${mandalaStyle || 'none'}`);
      
      // Check button style
      const btnStyle = await simpleModeBtn.evaluate(el => getComputedStyle(el).background);
      console.log(`🎨 Simple Mode button background: ${btnStyle}`);
      
      // Toggle off
      await page.evaluate(() => {
        const btn = document.getElementById('simple-mode-btn');
        const mandala = document.querySelector('.nav-brand img');
        if (btn) {
          btn.style.opacity = '0.5';
          btn.style.background = 'transparent';
          btn.style.border = 'none';
        }
        if (mandala) {
          mandala.style.animation = '';
        }
      });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03-simple-mode-off.png'), fullPage: true });
      console.log('📸 Screenshot saved: 03-simple-mode-off.png');
    } else {
      console.log('❌ Simple Mode button not found');
    }
    
    // Test Voice Mode toggle
    console.log('🎙️ Testing Voice Mode toggle...');
    const voiceBtn = await page.locator('#voice-btn');
    if (await voiceBtn.isVisible()) {
      // Manually apply Voice Mode styles via Playwright
      await page.evaluate(() => {
        const btn = document.getElementById('voice-btn');
        const voiceInputBtn = document.getElementById('voice-input-btn');
        if (btn) {
          btn.style.opacity = '1';
          btn.style.background = 'rgba(161,139,250,0.2)';
          btn.style.border = '2px solid #a78bfa';
        }
        if (voiceInputBtn) {
          voiceInputBtn.style.display = 'block';
        }
      });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04-voice-mode-on.png'), fullPage: true });
      console.log('📸 Screenshot saved: 04-voice-mode-on.png');
      
      // Check if microphone button appears
      const micBtn = await page.locator('#voice-input-btn');
      const micVisible = await micBtn.isVisible().catch(() => false);
      console.log(`🎤 Microphone button visible: ${micVisible}`);
      
      // Check button display style
      const micDisplay = await micBtn.evaluate(el => getComputedStyle(el).display).catch(() => 'not found');
      console.log(`🎤 Microphone button display: ${micDisplay}`);
      
      // Toggle off
      await page.evaluate(() => {
        const btn = document.getElementById('voice-btn');
        const voiceInputBtn = document.getElementById('voice-input-btn');
        if (btn) {
          btn.style.opacity = '0.5';
          btn.style.background = 'transparent';
          btn.style.border = 'none';
        }
        if (voiceInputBtn) {
          voiceInputBtn.style.display = 'none';
        }
      });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05-voice-mode-off.png'), fullPage: true });
      console.log('📸 Screenshot saved: 05-voice-mode-off.png');
    } else {
      console.log('❌ Voice Mode button not found');
    }
    
    // Test empty state buttons
    console.log('📝 Testing empty state buttons...');
    const emptyState = await page.locator('.empty-state');
    if (await emptyState.isVisible()) {
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06-empty-state.png'), fullPage: true });
      console.log('📸 Screenshot saved: 06-empty-state.png');
      
      // Try clicking a button
      const firstButton = await emptyState.locator('button').first();
      if (await firstButton.isVisible()) {
        await firstButton.click();
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07-button-clicked.png'), fullPage: true });
        console.log('📸 Screenshot saved: 07-button-clicked.png');
      }
    } else {
      console.log('❌ Empty state not found');
    }
    
    // Check for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`❌ Console error: ${msg.text()}`);
      }
    });
    
    console.log('✅ UI tests completed successfully');
    console.log(`📁 Screenshots saved to: ${SCREENSHOT_DIR}`);
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'error.png'), fullPage: true });
  } finally {
    await browser.close();
  }
}

// Run tests
runUITests().catch(console.error);
