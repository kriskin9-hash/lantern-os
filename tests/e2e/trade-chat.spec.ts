import { test, expect } from '@playwright/test';

/**
 * Lantern Trade Chat - Browser E2E Tests
 * 
 * Tests for the Kalshi trading chat interface:
 * - Login flow (GitHub OAuth)
 * - Chat interface
 * - Order parsing and preview
 * - Safety gates display
 * - Balance display
 */

test.describe('Lantern Trade Chat', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to trade chat (requires local server running)
    await page.goto('http://localhost:8080');
  });

  test('loads main interface', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Lantern Trade Chat');
    await expect(page.locator('#loginBtn')).toBeVisible();
    await expect(page.locator('#msg')).toBeVisible();
  });

  test('shows login button when not authenticated', async ({ page }) => {
    await expect(page.locator('#loginBtn')).toHaveText('Sign in with GitHub');
  });

  test('displays safety status strip', async ({ page }) => {
    await expect(page.locator('#statusStrip')).toBeVisible();
    await expect(page.locator('#envVal')).toBeVisible();
    await expect(page.locator('#liveVal')).toBeVisible();
    await expect(page.locator('#killVal')).toBeVisible();
  });

  test('chat input accepts order commands', async ({ page }) => {
    const msgInput = page.locator('#msg');
    await msgInput.fill('buy 1 yes on TICKER at 40c');
    await expect(msgInput).toHaveValue('buy 1 yes on TICKER at 40c');
  });

  test('shows help hint text', async ({ page }) => {
    await expect(page.locator('.hint')).toContainText('Dry-run by default');
    await expect(page.locator('.hint')).toContainText('live');
  });

  test('displays transcript area', async ({ page }) => {
    await expect(page.locator('#transcript')).toBeVisible();
  });

  test('composer form has send button', async ({ page }) => {
    await expect(page.locator('button[type="submit"]')).toHaveText('Send');
  });
});

test.describe('Trade Chat - Safety Gates', () => {
  test('kill switch status is visible', async ({ page }) => {
    await page.goto('http://localhost:8080');
    const killVal = page.locator('#killVal');
    await expect(killVal).toBeVisible();
    // Kill switch should show as active/disarmed
    const text = await killVal.textContent();
    expect(text).toMatch(/active|disarmed/i);
  });

  test('live trading status is visible', async ({ page }) => {
    await page.goto('http://localhost:8080');
    const liveVal = page.locator('#liveVal');
    await expect(liveVal).toBeVisible();
    // Live should be disabled by default
    const text = await liveVal.textContent();
    expect(text).toMatch(/off|disabled|no/i);
  });
});
