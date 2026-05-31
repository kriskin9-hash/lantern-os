import { test, expect } from '@playwright/test';

/**
 * Lantern OS Static Surfaces - Browser E2E Tests
 * 
 * Tests for static HTML surfaces:
 * - Shareholder index
 * - Desktop surfaces
 * - Dashboard surfaces
 */

test.describe('Static Surfaces', () => {
  test('shareholder index loads', async ({ page }) => {
    await page.goto('http://localhost:8080/shareholder-index');
    await expect(page.locator('html')).toBeVisible();
  });

  test('desktop surface loads', async ({ page }) => {
    await page.goto('http://localhost:8080/desktop');
    await expect(page.locator('html')).toBeVisible();
  });

  test('dashboard loads', async ({ page }) => {
    await page.goto('http://localhost:8080/dashboard');
    await expect(page.locator('html')).toBeVisible();
  });

  test('static surfaces have no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('http://localhost:8080/shareholder-index');
    await page.waitForLoadState('networkidle');
    
    expect(errors).toHaveLength(0);
  });
});
