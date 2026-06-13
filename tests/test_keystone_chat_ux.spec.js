/**
 * Keystone Chat UX Playwright tests — keystone-debug.html
 *
 * Drives the debug console as a real user would:
 *   - page load, quick test cases, routing info display, stats counter
 *   - mocks /api/dream/chat/stream so tests run without a live AI provider
 *
 * Usage:
 *   npx playwright test tests/test_keystone_chat_ux.spec.js
 *   npx playwright test tests/test_keystone_chat_ux.spec.js --ui
 *
 * Requires: server running at BASE_URL (node apps/lantern-garage/server.js)
 */

const { test, expect } = require("@playwright/test");
const { baseUrl: BASE_URL } = require("./lantern-test-base");

const PAGE = `${BASE_URL}/keystone-debug.html`;

// Intercept fetch() at the JS level before page load — reliable for streaming APIs.
// page.route() doesn't support ReadableStream bodies so SSE parsing breaks.
async function mockFetch(page, { streamOk = true } = {}) {
  await page.addInitScript(({ streamOk }) => {
    const orig = window.fetch.bind(window);
    window.__mockStats = { keystoneCalls: 0, claudeCalls: 0, errors: 0 };

    window.fetch = async (input, init) => {
      const url = typeof input === "string" ? input : input.url;

      if (url.includes("/api/dream/chat/stream")) {
        if (!streamOk) {
          return new Response("Internal Server Error", { status: 500 });
        }

        const events = [
          `data: ${JSON.stringify({ type: "route", agent: "keystone", intent: "technical", label: "refactor,audit" })}\n\n`,
          `data: ${JSON.stringify({ type: "token", text: "Keystone here. " })}\n\n`,
          `data: ${JSON.stringify({ type: "token", text: "Analysing repo state now." })}\n\n`,
          `data: [DONE]\n\n`,
        ].join("");

        const encoder = new TextEncoder();
        const encoded = encoder.encode(events);

        const stream = new ReadableStream({
          start(controller) {
            controller.enqueue(encoded);
            controller.close();
          },
        });

        return new Response(stream, {
          status: 200,
          headers: { "Content-Type": "text/event-stream" },
        });
      }

      if (url.includes("/api/dream/chat") && !url.includes("stream")) {
        return new Response(
          JSON.stringify({ reply: "Claude Code mock reply." }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }

      return orig(input, init);
    };
  }, { streamOk });
}

test.describe("Keystone debug console — page load", () => {
  test("loads with correct title and header", async ({ page }) => {
    await page.goto(PAGE);
    await expect(page).toHaveTitle(/Keystone/i);
    await expect(page.locator("h1")).toContainText("KEYSTONE");
  });

  test("all stat counters start at zero", async ({ page }) => {
    await page.goto(PAGE);
    await expect(page.locator("#statKeystone")).toHaveText("0");
    await expect(page.locator("#statClaude")).toHaveText("0");
    await expect(page.locator("#statErrors")).toHaveText("0");
    await expect(page.locator("#statLatency")).toHaveText("0ms");
  });

  test("routing info placeholders render before any call", async ({ page }) => {
    await page.goto(PAGE);
    await expect(page.locator("#routingAgent")).toHaveText("—");
    await expect(page.locator("#routingIntent")).toHaveText("—");
    await expect(page.locator("#routingKeywords")).toHaveText("—");
    await expect(page.locator("#routingConfidence")).toHaveText("—");
  });

  test("response panels show ready state on load", async ({ page }) => {
    await page.goto(PAGE);
    await expect(page.locator("#keystoneResponse")).toContainText("Ready");
    await expect(page.locator("#claudeResponse")).toContainText("Ready");
  });

  test("four quick test cases are clickable", async ({ page }) => {
    await page.goto(PAGE);
    const cases = page.locator(".test-case");
    await expect(cases).toHaveCount(4);
    // Each should be visible
    for (let i = 0; i < 4; i++) {
      await expect(cases.nth(i)).toBeVisible();
    }
  });
});

test.describe("Keystone debug console — prompt input", () => {
  test("textarea accepts typed input", async ({ page }) => {
    await page.goto(PAGE);
    await page.fill("#prompt", "audit the convergence loop");
    await expect(page.locator("#prompt")).toHaveValue("audit the convergence loop");
  });

  test("clicking a quick test case sets the prompt textarea", async ({ page }) => {
    await page.goto(PAGE);
    // Click the GitHub issue test case
    await page.locator(".test-case").first().click();
    const val = await page.locator("#prompt").inputValue();
    expect(val.length).toBeGreaterThan(0);
  });

  test("clicking each quick test case populates a non-empty prompt", async ({ page }) => {
    await page.goto(PAGE);
    const cases = page.locator(".test-case");
    const count = await cases.count();
    for (let i = 0; i < count; i++) {
      await cases.nth(i).click();
      const val = await page.locator("#prompt").inputValue();
      expect(val.trim().length).toBeGreaterThan(0);
    }
  });

  test("mode radio buttons switch between keystone / auto / claude", async ({ page }) => {
    await page.goto(PAGE);
    // Default: keystone checked
    await expect(page.locator('input[name="mode"][value="keystone"]')).toBeChecked();

    await page.locator('input[name="mode"][value="auto"]').check();
    await expect(page.locator('input[name="mode"][value="auto"]')).toBeChecked();

    await page.locator('input[name="mode"][value="claude"]').check();
    await expect(page.locator('input[name="mode"][value="claude"]')).toBeChecked();
  });
});

test.describe("Keystone debug console — Test Keystone flow", () => {
  test.beforeEach(async ({ page }) => {
    await mockFetch(page, { streamOk: true });
  });

  test("clicking Test Keystone populates the response panel", async ({ page }) => {
    await page.goto(PAGE);
    await page.fill("#prompt", "refactor the queue manager");
    await page.click("button:has-text('Test Keystone')");

    await expect(page.locator("#keystoneResponse")).not.toHaveText("Ready for input...", { timeout: 8000 });
    const text = await page.locator("#keystoneResponse").textContent();
    expect(text.trim().length).toBeGreaterThan(0);
  });

  test("routing info updates after Keystone call", async ({ page }) => {
    await page.goto(PAGE);
    await page.fill("#prompt", "refactor the queue manager");
    await page.click("button:has-text('Test Keystone')");

    await expect(page.locator("#routingAgent")).not.toHaveText("—", { timeout: 8000 });
    await expect(page.locator("#routingAgent")).toHaveText("keystone");
    await expect(page.locator("#routingIntent")).toHaveText("technical");
    await expect(page.locator("#routingKeywords")).toHaveText("refactor,audit");
  });

  test("Keystone call counter increments", async ({ page }) => {
    await page.goto(PAGE);
    await page.fill("#prompt", "What work needs to be done?");
    await page.click("button:has-text('Test Keystone')");

    await expect(page.locator("#statKeystone")).not.toHaveText("0", { timeout: 8000 });
    await expect(page.locator("#statKeystone")).toHaveText("1");
  });

  test("latency stat shows a real value after call", async ({ page }) => {
    await page.goto(PAGE);
    await page.fill("#prompt", "audit the convergence loop");
    await page.click("button:has-text('Test Keystone')");

    await expect(page.locator("#statLatency")).not.toHaveText("0ms", { timeout: 8000 });
    const latencyText = await page.locator("#statLatency").textContent();
    expect(latencyText).toMatch(/\d+ms/);
  });

  test("error counter stays zero on successful call", async ({ page }) => {
    await page.goto(PAGE);
    await page.fill("#prompt", "Tell me a story");
    await page.click("button:has-text('Test Keystone')");

    await expect(page.locator("#statKeystone")).not.toHaveText("0", { timeout: 8000 });
    await expect(page.locator("#statErrors")).toHaveText("0");
  });

  test("response accumulates streamed tokens", async ({ page }) => {
    await page.goto(PAGE);
    await page.fill("#prompt", "Check GitHub issue #350");
    await page.click("button:has-text('Test Keystone')");

    await expect(page.locator("#keystoneResponse")).toContainText("Keystone here", { timeout: 8000 });
    await expect(page.locator("#keystoneResponse")).toContainText("Analysing repo state");
  });

  test("two sequential calls increment counter to 2", async ({ page }) => {
    await page.goto(PAGE);

    await page.fill("#prompt", "first call");
    await page.click("button:has-text('Test Keystone')");
    await expect(page.locator("#statKeystone")).toHaveText("1", { timeout: 8000 });

    await page.fill("#prompt", "second call");
    await page.click("button:has-text('Test Keystone')");
    await expect(page.locator("#statKeystone")).toHaveText("2", { timeout: 8000 });
  });
});

test.describe("Keystone debug console — error handling", () => {
  test("error counter increments when stream fails", async ({ page }) => {
    await mockFetch(page, { streamOk: false });
    await page.goto(PAGE);
    await page.fill("#prompt", "trigger error");
    await page.click("button:has-text('Test Keystone')");

    await expect(page.locator("#statErrors")).not.toHaveText("0", { timeout: 8000 });
    await expect(page.locator("#keystoneResponse")).toContainText("ERROR");
  });
});

test.describe("Keystone debug console — Claude Code flow", () => {
  test.beforeEach(async ({ page }) => {
    await mockFetch(page, { streamOk: true });
  });

  test("Test Claude Code populates the claude response panel", async ({ page }) => {
    await page.goto(PAGE);
    await page.fill("#prompt", "Tell me a story");
    await page.click("button:has-text('Test Claude Code')");

    await expect(page.locator("#claudeResponse")).not.toHaveText("Ready for input...", { timeout: 8000 });
    await expect(page.locator("#claudeResponse")).toContainText("Claude Code mock reply");
  });

  test("Claude call counter increments", async ({ page }) => {
    await page.goto(PAGE);
    await page.fill("#prompt", "Tell me a story");
    await page.click("button:has-text('Test Claude Code')");

    await expect(page.locator("#statClaude")).toHaveText("1", { timeout: 8000 });
  });
});
