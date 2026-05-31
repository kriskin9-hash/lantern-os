import { test, expect } from '@playwright/test';

/**
 * Lantern Garage - Browser E2E Tests
 * 
 * Tests for the garage payment bridge interface:
 * - Main interface loading
 * - Payment flow UI
 * - Service automation display
 */

test.describe('Lantern Garage', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to garage (requires local server running)
    await page.goto('http://localhost:8080/garage');
  });

  test('loads main interface', async ({ page }) => {
    await expect(page.locator('h1, h2')).toBeVisible();
  });

  test('displays payment bridge section', async ({ page }) => {
    // Check for payment-related UI elements
    const paymentSection = page.locator('text=payment').or(page.locator('[class*="payment"]'));
    await expect(paymentSection.first()).toBeVisible();
  });

  test('displays service automation section', async ({ page }) => {
    // Check for service automation UI elements
    const serviceSection = page.locator('text=service').or(page.locator('[class*="service"]'));
    await expect(serviceSection.first()).toBeVisible();
  });
});
