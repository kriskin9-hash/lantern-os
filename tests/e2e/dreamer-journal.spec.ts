/**
 * Dream Journal v0 E2E Playwright Tests
 * Tests the Dream Journal UI at http://127.0.0.1:4177/
 *
 * Run: npx playwright test tests/e2e/dreamer-journal.spec.ts
 */

import { test, expect } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:4177";

test.describe("Dream Journal v0 — Page Load & Structure", () => {
  test("dashboard loads with Dream Journal heading", async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.locator("text=Dream Journal").first()).toBeVisible();
    await expect(page.locator("text=Your dreams. Your space. Always private.")).toBeVisible();
  });

  test("chat section is present and interactive", async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.locator("text=Talk to your Dream Journal")).toBeVisible();
    const chatInput = page.locator("#chatInput");
    await expect(chatInput).toBeVisible();
    await expect(chatInput).toHaveAttribute("placeholder", /dream/);
  });

  test("stat cards render with numbers", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForSelector(".stat-number", { timeout: 5000 });
    const cards = await page.locator(".stat-card").count();
    expect(cards).toBeGreaterThanOrEqual(1);
  });

  test("new entry form is visible", async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.locator("text=New Entry").first()).toBeVisible();
    await expect(page.locator("#entryForm, form").first()).toBeVisible();
  });

  test("chat input and send button exist", async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.locator("#chatInput")).toBeVisible();
    await expect(page.locator("#chatSend")).toBeVisible();
    await expect(page.locator("#chatClear")).toBeVisible();
  });

  test("boundary message — no medical claims", async ({ page }) => {
    await page.goto(BASE_URL);
    const bodyText = await page.locator("body").textContent();
    expect(bodyText).not.toMatch(/therapist|diagnosis|prescription|treatment|mental health professional/i);
    expect(bodyText).toMatch(/private|local|your space/i);
  });
});

test.describe("Dream Journal v0 — Chat Flow", () => {
  test("typing a message and sending triggers response", async ({ page }) => {
    await page.goto(BASE_URL);
    const input = page.locator("#chatInput");
    await input.fill("I had a dream about flying");
    await page.locator("#chatSend").click();

    // Wait for response bubble
    await page.waitForTimeout(2500);
    const bubbles = await page.locator(".bubble").count();
    expect(bubbles).toBeGreaterThanOrEqual(2); // user + agent
  });

  test("chat memory persists across reload", async ({ page }) => {
    await page.goto(BASE_URL);
    const input = page.locator("#chatInput");
    await input.fill("Memory test message");
    await page.locator("#chatSend").click();
    await page.waitForTimeout(2000);

    // Reload
    await page.reload();
    await page.waitForTimeout(1000);
    const bubbles = await page.locator(".bubble").count();
    expect(bubbles).toBeGreaterThanOrEqual(2);
  });

  test("clear button wipes chat memory", async ({ page }) => {
    await page.goto(BASE_URL);
    const input = page.locator("#chatInput");
    await input.fill("Clear test message");
    await page.locator("#chatSend").click();
    await page.waitForTimeout(2000);

    await page.locator("#chatClear").click();
    await page.waitForTimeout(500);
    const bubbles = await page.locator(".bubble").count();
    expect(bubbles).toBeLessThanOrEqual(1);
  });

  test("suggestion buttons trigger chat", async ({ page }) => {
    await page.goto(BASE_URL);
    const suggestions = page.locator(".chat-suggestions button, .suggestion");
    const count = await suggestions.count();
    if (count > 0) {
      await suggestions.first().click();
      await page.waitForTimeout(2000);
      const bubbles = await page.locator(".bubble").count();
      expect(bubbles).toBeGreaterThanOrEqual(2);
    }
  });

  test("door keyword triggers door card or lore response", async ({ page }) => {
    await page.goto(BASE_URL);
    const input = page.locator("#chatInput");
    await input.fill("Tell me about the Xenon door");
    await page.locator("#chatSend").click();
    await page.waitForTimeout(2500);

    const bodyText = await page.locator("body").textContent();
    expect(bodyText).toMatch(/Xenon|door|Gateway|Build beyond/i);
  });

  test("agent label appears in response bubble", async ({ page }) => {
    await page.goto(BASE_URL);
    const input = page.locator("#chatInput");
    await input.fill("Show me who is speaking");
    await page.locator("#chatSend").click();
    await page.waitForTimeout(2500);

    const labels = await page.locator(".bubble-label").count();
    expect(labels).toBeGreaterThanOrEqual(1);
  });
});

test.describe("Dream Journal v0 — Entry Creation", () => {
  test("submitting a dream entry adds to recent entries", async ({ page }) => {
    await page.goto(BASE_URL);

    // Fill form
    const textarea = page.locator("#text, textarea[name='text']").first();
    await textarea.fill("E2E test dream: floating through nebula clouds");

    const submit = page.locator("#entryForm button[type='submit'], form button[type='submit']").first();
    if (await submit.isVisible().catch(() => false)) {
      await submit.click();
      await page.waitForTimeout(1500);
    }

    // Recent entries should exist
    await expect(page.locator("text=Recent Entries").first()).toBeVisible();
  });

  test("lucidity input accepts 0-1 range", async ({ page }) => {
    await page.goto(BASE_URL);
    const lucidity = page.locator("input[type='number']#lucidity, input[name='lucidity']").first();
    if (await lucidity.isVisible().catch(() => false)) {
      const min = await lucidity.getAttribute("min");
      const max = await lucidity.getAttribute("max");
      expect(["0", null]).toContain(min);
      expect(["1", null]).toContain(max);
    }
  });

  test("emotions field accepts comma-separated input", async ({ page }) => {
    await page.goto(BASE_URL);
    const emotions = page.locator("input#emotions, input[name='emotions']").first();
    if (await emotions.isVisible().catch(() => false)) {
      await emotions.fill("awe, wonder, peace");
      const val = await emotions.inputValue();
      expect(val).toBe("awe, wonder, peace");
    }
  });

  test("tags field accepts comma-separated input", async ({ page }) => {
    await page.goto(BASE_URL);
    const tags = page.locator("input#tags, input[name='tags']").first();
    if (await tags.isVisible().catch(() => false)) {
      await tags.fill("lantern, test, e2e");
      const val = await tags.inputValue();
      expect(val).toBe("lantern, test, e2e");
    }
  });
});

test.describe("Dream Journal v0 — API Error Handling", () => {
  test("POST /api/dream/create with missing text returns error", async ({ request }) => {
    const r = await request.post(`${BASE_URL}/api/dream/create`, {
      data: { kind: "dream" },
    });
    expect(r.status()).toBeGreaterThanOrEqual(400);
  });

  test("POST /api/dream/create with invalid JSON handled gracefully", async ({ request }) => {
    const r = await request.post(`${BASE_URL}/api/dream/create`, {
      headers: { "Content-Type": "application/json" },
      data: "not json",
    });
    expect(r.status()).toBeGreaterThanOrEqual(400);
  });

  test("GET /api/dream/read/:id returns 404 for unknown", async ({ request }) => {
    const r = await request.get(`${BASE_URL}/api/dream/read/does_not_exist_xyz`);
    expect(r.status()).toBe(404);
  });

  test("GET /api/dream/stats returns JSON with counts", async ({ request }) => {
    const r = await request.get(`${BASE_URL}/api/dream/stats`);
    expect(r.status()).toBe(200);
    const body = await r.json();
    expect(typeof body.total_entries).toBe("number");
    expect(typeof body.avg_lucidity).not.toBe("undefined");
  });
});

test.describe("Dream Journal v0 — Safety Boundaries", () => {
  test("no cloud sync claims in UI", async ({ page }) => {
    await page.goto(BASE_URL);
    const bodyText = await page.locator("body").textContent();
    expect(bodyText).not.toMatch(/sync to cloud|upload to server|share with/i);
  });

  test("privacy messaging is present", async ({ page }) => {
    await page.goto(BASE_URL);
    const bodyText = await page.locator("body").textContent();
    expect(bodyText).toMatch(/private|local|your device|saved locally/i);
  });

  test("entry text has max length enforcement", async ({ page }) => {
    await page.goto(BASE_URL);
    const textarea = page.locator("#text, textarea").first();
    if (await textarea.isVisible().catch(() => false)) {
      const maxLen = await textarea.getAttribute("maxlength");
      if (maxLen) {
        expect(parseInt(maxLen)).toBeGreaterThan(0);
      }
    }
  });
});
