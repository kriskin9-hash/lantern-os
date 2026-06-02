import { defineConfig, devices } from '@playwright/test';

/**
 * Lantern OS Playwright Configuration
 * 
 * Browser testing for Lantern OS surfaces:
 * - Trade chat app (Kalshi integration)
 * - Garage app (payment bridge)
 * - Desktop surfaces
 * - Static HTML surfaces
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:8080',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'python -m http.server 8080 --directory ../surfaces',
    url: 'http://localhost:8080',
    reuseExistingServer: !!process.env.CI,
  },
});
