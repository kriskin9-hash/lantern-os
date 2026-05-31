import { test, expect } from '@playwright/test';

/**
 * Lantern Dashboard - Browser E2E Tests
 * 
 * Tests for dashboard surfaces:
 * - Convergence dashboard
 * - Main dashboard
 * - Status displays
 */

test.describe('Lantern Dashboard', () => {
  test('main dashboard loads', async ({ page }) => {
    await page.goto('http://localhost:8080/dashboard');
    await expect(page.locator('html')).toBeVisible();
  });

  test('convergence dashboard loads', async ({ page }) => {
    await page.goto('http://localhost:8080/dashboard/convergence-dashboard.html');
    await expect(page.locator('html')).toBeVisible();
  });

  test('dashboard has no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('http://localhost:8080/dashboard');
    await page.waitForLoadState('networkidle');
    
    expect(errors).toHaveLength(0);
  });

  test('dashboard displays status information', async ({ page }) => {
    await page.goto('http://localhost:8080/dashboard');
    // Check for status-related content
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.length).toBeGreaterThan(0);
  });
});
