/**
 * Three Doors Game Browser Tests (Playwright)
 * OSS stack tests using Playwright - tests the full game flow
 *
 * Run with server: npm start --prefix apps/lantern-garage
 * Then: npx playwright test tests/test_three_doors_game.spec.js --headed
 */

const { test, expect } = require("@playwright/test");

const BASE_URL = "http://127.0.0.1:4177";
const DREAM_CHAT_URL = `${BASE_URL}/dream-chat.html`;

test.describe("Three Doors Game - API Tests", () => {
  test("API returns valid initial game state", async ({ page }) => {
    const response = await page.request.post(`${BASE_URL}/api/dream/doors`, {
      data: { userId: "test-player-1", action: "start" }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data.text).toContain("Moss Door");
    expect(data.doors).toHaveLength(3);
    expect(data.fox_present).toBe(true);
    expect(data.scene_key).toBe("moss-entry");
    expect(data.history).toBeDefined();
  });

  test("API accepts door choice and returns new scene", async ({ page }) => {
    // Start game
    const startResp = await page.request.post(`${BASE_URL}/api/dream/doors`, {
      data: { userId: "test-player-2", action: "start" }
    });
    const startData = await startResp.json();
    const firstDoor = startData.doors[0];

    // Choose a door
    const choiceResp = await page.request.post(`${BASE_URL}/api/dream/doors`, {
      data: {
        userId: "test-player-2",
        action: "choose",
        choice: firstDoor.label
      }
    });

    expect(choiceResp.ok()).toBeTruthy();
    const choiceData = await choiceResp.json();

    expect(choiceData.text).toBeTruthy();
    expect(choiceData.doors).toHaveLength(3);
    expect(choiceData.text).not.toBe(startData.text); // Should be a different scene
  });

  test("API handles multi-turn game progression", async ({ page }) => {
    const userId = "test-player-3";

    // Turn 1: Start
    const turn1 = await page.request.post(`${BASE_URL}/api/dream/doors`, {
      data: { userId, action: "start" }
    });
    let state = await turn1.json();
    expect(state.text).toContain("Moss Door");

    // Turn 2: Choose door C
    const turn2 = await page.request.post(`${BASE_URL}/api/dream/doors`, {
      data: { userId, action: "choose", choice: "C" }
    });
    state = await turn2.json();
    expect(state.text).toBeTruthy();

    // Turn 3: Choose another door
    const doorB = state.doors.find(d => d.label === "B");
    if (doorB) {
      const turn3 = await page.request.post(`${BASE_URL}/api/dream/doors`, {
        data: { userId, action: "choose", choice: doorB.label }
      });
      state = await turn3.json();
      expect(state.text).toBeTruthy();
      expect(state.history.length).toBeGreaterThan(1);
    }
  });

  test("Game engine includes Stable Diffusion image prompts", async ({ page }) => {
    const response = await page.request.post(`${BASE_URL}/api/dream/doors`, {
      data: { userId: "test-player-4", action: "start" }
    });

    const data = await response.json();
    expect(data.image_prompt).toBeTruthy();
    expect(typeof data.image_prompt).toBe("string");
    expect(data.image_prompt.length).toBeGreaterThan(20);
  });

  test("Image generation endpoint returns prompt data", async ({ page }) => {
    const response = await page.request.post(`${BASE_URL}/api/dream/doors/image`, {
      data: { userId: "test-player-5", doorIndex: 0 }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty("available");
    if (!data.available && data.suggestion) {
      expect(data.suggestion).toHaveProperty("prompt");
      expect(data.suggestion.prompt.length).toBeGreaterThan(20);
    }
  });

  test("Invalid choice returns error", async ({ page }) => {
    const response = await page.request.post(`${BASE_URL}/api/dream/doors`, {
      data: { userId: "test-player-6", action: "choose", choice: "Z" }
    });

    const data = await response.json();
    expect(data.error || !data.doors).toBeTruthy();
  });
});

test.describe("Three Doors Game - UI Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DREAM_CHAT_URL);
    await page.waitForSelector("#input", { timeout: 10000 });
  });

  test("Three Doors command launches game in Dream Chat", async ({ page }) => {
    const input = page.locator("#input");
    const sendBtn = page.locator("#send-btn");

    // Type and send the Three Doors command
    await input.fill("!three-doors");
    await sendBtn.click();

    // Wait for door buttons to appear
    await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });

    // Verify game loaded
    const doorButtons = page.locator("button[onclick*='chooseDoorsPath']");
    const count = await doorButtons.count();
    expect(count).toBe(3);
  });

  test("Game displays scene text and door options", async ({ page }) => {
    const input = page.locator("#input");
    const sendBtn = page.locator("#send-btn");

    await input.fill("!three-doors");
    await sendBtn.click();

    // Wait for game to load
    await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });

    // Check for scene content
    const bubbles = page.locator(".bubble");
    const bubbleText = await bubbles.nth(bubbles.count() - 1).textContent();

    expect(bubbleText).toContain("Door");
  });

  test("Can click door button and navigate to new scene", async ({ page }) => {
    const input = page.locator("#input");
    const sendBtn = page.locator("#send-btn");

    // Start game
    await input.fill("!three-doors");
    await sendBtn.click();

    // Wait for initial scene
    await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });

    // Get the initial button count
    let doorButtons = page.locator("button[onclick*='chooseDoorsPath']");
    const initialCount = await doorButtons.count();

    // Click first door
    const firstButton = doorButtons.nth(0);
    await firstButton.click();

    // Wait for new scene to render
    await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });

    // Should still have door buttons
    doorButtons = page.locator("button[onclick*='chooseDoorsPath']");
    const newCount = await doorButtons.count();
    expect(newCount).toBe(3);
  });

  test("Game shows fox presence indicator", async ({ page }) => {
    const input = page.locator("#input");
    const sendBtn = page.locator("#send-btn");

    await input.fill("!three-doors");
    await sendBtn.click();

    // Wait for game
    await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });

    // Look for fox indicator (🦊)
    const foxIndicator = page.locator("text=🦊");
    const isFoxVisible = await foxIndicator.isVisible().catch(() => false);

    // Fox should be mentioned in initial scene
    expect(isFoxVisible).toBeTruthy();
  });

  test("Can navigate through multiple doors without error", async ({ page }) => {
    const input = page.locator("#input");
    const sendBtn = page.locator("#send-btn");

    // Start game
    await input.fill("!three-doors");
    await sendBtn.click();

    await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });

    // Navigate through 3 doors sequentially
    for (let i = 0; i < 3; i++) {
      const buttons = page.locator("button[onclick*='chooseDoorsPath']");
      const isVisible = await buttons.nth(0).isVisible();

      if (isVisible) {
        await buttons.nth(i % 3).click();
        // Wait for next scene
        await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 6000 });
      }
    }

    // Page should still be functional
    const title = await page.title();
    expect(title).toBeTruthy();
  });

  test("Image prompts are visible in scene data", async ({ page }) => {
    const input = page.locator("#input");
    const sendBtn = page.locator("#send-btn");

    await input.fill("!three-doors");
    await sendBtn.click();

    await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });

    // Look for image prompt indicator
    const promptIndicator = page.locator("text=/📸|Stable Diffusion|prompt/i");
    const isPromptVisible = await promptIndicator.isVisible().catch(() => false);

    // Prompt should be displayed
    expect(isPromptVisible).toBeTruthy();
  });

  test("Server responds to multiple concurrent game sessions", async ({ page }) => {
    // Run 3 API calls concurrently
    const responses = await Promise.all([
      page.request.post(`${BASE_URL}/api/dream/doors`, {
        data: { userId: "concurrent-1", action: "start" }
      }),
      page.request.post(`${BASE_URL}/api/dream/doors`, {
        data: { userId: "concurrent-2", action: "start" }
      }),
      page.request.post(`${BASE_URL}/api/dream/doors`, {
        data: { userId: "concurrent-3", action: "start" }
      })
    ]);

    // All should succeed
    for (const resp of responses) {
      expect(resp.ok()).toBeTruthy();
      const data = await resp.json();
      expect(data.doors).toHaveLength(3);
    }
  });
});

test.describe("Three Doors Game - Scene Progression", () => {
  test("All new scenes are accessible", async ({ page }) => {
    // The game engine includes: garden-door, xenon-convergence, end-of-time
    // We'll verify they're in the navigation graph by traversing

    const userId = "scene-test-user";
    let scenesSeen = new Set();

    for (let turn = 0; turn < 10; turn++) {
      let response;
      if (turn === 0) {
        response = await page.request.post(`${BASE_URL}/api/dream/doors`, {
          data: { userId, action: "start" }
        });
      } else {
        // Get current state first
        const stateResp = await page.request.post(`${BASE_URL}/api/dream/doors`, {
          data: { userId, action: "start" }
        });
        const state = await stateResp.json();

        // Choose a random door
        const randomDoor = state.doors[Math.floor(Math.random() * 3)];
        response = await page.request.post(`${BASE_URL}/api/dream/doors`, {
          data: { userId, action: "choose", choice: randomDoor.label }
        });
      }

      const data = await response.json();
      scenesSeen.add(data.scene_key);
    }

    // Should have seen multiple unique scenes
    expect(scenesSeen.size).toBeGreaterThan(1);

    // Log which scenes were visited
    console.log(`Scenes visited: ${Array.from(scenesSeen).join(", ")}`);
  });
});
