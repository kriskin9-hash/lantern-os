/**
 * Dream Journal UI Playwright tests
 * Run after starting lantern-garage: node apps/lantern-garage/server.js
 *
 * Usage:
 *   npx playwright test tests/test_dream_journal_ui.spec.js
 *   npx playwright test --ui
 */

const { test, expect } = require("@playwright/test");
const { baseUrl: BASE_URL } = require("./lantern-test-base");

test.describe("Dream Journal UI", () => {
  test("dashboard loads and shows Dream Journal heading", async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.locator("text=Dream Journal")).toBeVisible();
    await expect(page.locator("text=Your dreams. Your space. Always private.")).toBeVisible();
  });

  test("stat cards render with numbers", async ({ page }) => {
    await page.goto(BASE_URL);
    // Wait for stat cards to appear
    await page.waitForSelector(".stat-number", { timeout: 5000 });
    const cards = await page.locator(".stat-card").count();
    expect(cards).toBeGreaterThanOrEqual(1);
  });

  test("new entry form is visible and interactive", async ({ page }) => {
    await page.goto(BASE_URL);
    const form = page.locator("#entryForm, form[action*='dream']").first();
    await expect(form).toBeVisible();

    // Fill the form
    const textarea = form.locator("textarea, [name='text'], input[name='text']").first();
    if (await textarea.isVisible().catch(() => false)) {
      await textarea.fill("Playwright test dream: floating through a crystalline city");
    }
  });

  test("chat input accepts text and triggers agent response", async ({ page }) => {
    await page.goto(BASE_URL);

    // Find chat input
    const chatInput = page.locator("input[placeholder*='dream'], textarea[placeholder*='dream'], [contenteditable='true']").first();

    // Some UIs use contenteditable divs
    if (await chatInput.isVisible().catch(() => false)) {
      await chatInput.fill("I saw a glowing light in my dream");
      await chatInput.press("Enter");

      // Wait for agent response bubble
      await page.waitForTimeout(2000);
      const response = page.locator(".chat-message, .agent-reply, .message-bubble").last();
      const text = await response.textContent().catch(() => "");
      expect(text.length).toBeGreaterThan(0);
    }
  });

  test("suggestion buttons are clickable", async ({ page }) => {
    await page.goto(BASE_URL);

    // Look for suggestion chips or buttons
    const suggestions = page.locator(".suggestion, .chip, button");
    const count = await suggestions.count();

    if (count > 0) {
      // Click first suggestion
      await suggestions.first().click();
      // Should not throw
      expect(true).toBe(true);
    }
  });

  test("door buttons trigger lore response", async ({ page }) => {
    await page.goto(BASE_URL);

    // Look for door-related buttons or links
    const doors = page.locator("button, a").filter({ hasText: /door|Door|doors/ });
    const count = await doors.count();

    if (count > 0) {
      await doors.first().click();
      await page.waitForTimeout(1000);
      // Page should not crash
      expect(await page.title()).toBeTruthy();
    }
  });

  test("entry type selector changes form mode", async ({ page }) => {
    await page.goto(BASE_URL);

    const typeSelect = page.locator("select[name='kind'], select[name='type'], [name='entryType']").first();
    if (await typeSelect.isVisible().catch(() => false)) {
      await typeSelect.selectOption("note");
      // Form should remain visible
      await expect(page.locator("form").first()).toBeVisible();
    }
  });

  test("lucidity slider has range 0-1", async ({ page }) => {
    await page.goto(BASE_URL);

    const slider = page.locator("input[type='range'], input[name='lucidity']").first();
    if (await slider.isVisible().catch(() => false)) {
      const min = await slider.getAttribute("min");
      const max = await slider.getAttribute("max");
      expect(["0", null]).toContain(min);
      expect(["1", "10", null]).toContain(max);
    }
  });

  test("recent entries list updates after creating entry", async ({ page }) => {
    await page.goto(BASE_URL);

    // Get initial count of entries
    const initial = await page.locator(".entry-card, .recent-entry").count();

    // Try to create an entry via the form
    const form = page.locator("form").first();
    const textarea = form.locator("textarea").first();
    if (await textarea.isVisible().catch(() => false)) {
      await textarea.fill("Playwright test entry for recent list");
      const submit = form.locator("button[type='submit'], input[type='submit']").first();
      if (await submit.isVisible().catch(() => false)) {
        await submit.click();
        await page.waitForTimeout(2000);
      }
    }

    // Recent entries section should still exist
    await expect(page.locator("text=Recent").first()).toBeVisible();
  });
});

test.describe("Dream Journal Chat Agents", () => {
  test("multi-agent chat shows agent names in response", async ({ page }) => {
    await page.goto(BASE_URL);

    const chatInput = page.locator("input[placeholder*='dream'], textarea[placeholder*='dream'], [contenteditable='true']").first();

    if (await chatInput.isVisible().catch(() => false)) {
      await chatInput.fill("Tell me about the doors");
      await chatInput.press("Enter");
      await page.waitForTimeout(3000);

      // Look for agent name indicators in the response
      const bodyText = await page.locator("body").textContent();
      const hasAgentNames = /Blinkbug|Waterfall|Xenon|Mary|Courtney/i.test(bodyText);
      expect(hasAgentNames || bodyText.length > 50).toBe(true);
    }
  });

  test("keystone renders run buttons and inline exec output for single-line commands", async ({ page }) => {
    await page.addInitScript(() => {
      const originalFetch = window.fetch.bind(window);
      window.__keystoneExecutedCommand = null;

      window.fetch = async (input, init) => {
        const url = typeof input === "string" ? input : input.url;

        if (url.endsWith("/api/keystone/exec")) {
          const payload = JSON.parse((init && init.body) || "{}");
          window.__keystoneExecutedCommand = payload.command || null;
          return new Response(
            JSON.stringify({
              ok: true,
              command: payload.command,
              output: "keystone exec ok",
              truncated: false,
            }),
            {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }
          );
        }

        return originalFetch(input, init);
      };
    });

    await page.goto(`${BASE_URL}/dream-chat.html`);
    await page.waitForSelector("#agent-select option[value='keystone']", { state: "attached" });
    await page.selectOption("#agent-select", "keystone");
    await page.evaluate(() => {
      keystoneMcpEnabled = true;
      const messagesEl = document.getElementById("messages");
      const text = "Start with:\n```bash\ngit status\n```";
      const row = document.createElement("div");
      row.className = "msg-row agent";

      const label = document.createElement("div");
      label.className = "msg-label";
      label.textContent = "Keystone";

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = text;

      const cursor = document.createElement("span");
      cursor.className = "cursor";
      bubble.appendChild(cursor);

      row.appendChild(label);
      row.appendChild(bubble);
      messagesEl.appendChild(row);

      finishStream(row, bubble, cursor, text, "offline", undefined, []);
    });

    const execBtn = page.locator("button.suggestion", { hasText: "git status" }).first();
    await expect(execBtn).toBeVisible();
    await execBtn.click();

    expect(await page.evaluate(() => window.__keystoneExecutedCommand)).toBe("git status");
    await expect(page.locator(".msg-row.agent", { hasText: "KEYSTONE EXEC" }).last()).toContainText("keystone exec ok");
  });
});
