import { test, expect } from '@playwright/test';

/**
 * Lantern Desktop Surfaces - Browser E2E Tests
 * 
 * Tests for desktop HTML surfaces:
 * - Day one pocket art
 * - Desktop index
 * - Other desktop UI components
 */

test.describe('Lantern Desktop Surfaces', () => {
  test('desktop index loads', async ({ page }) => {
    await page.goto('http://localhost:8080/desktop');
    await expect(page.locator('html')).toBeVisible();
  });

  test('day one pocket art loads', async ({ page }) => {
    await page.goto('http://localhost:8080/desktop/day-one-pocketart.html');
    await expect(page.locator('html')).toBeVisible();
  });

  test('desktop surfaces have no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('http://localhost:8080/desktop');
    await page.waitForLoadState('networkidle');
    
    expect(errors).toHaveLength(0);
  });

  test('desktop surfaces have visible content', async ({ page }) => {
    await page.goto('http://localhost:8080/desktop');
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.length).toBeGreaterThan(0);
  });
});
