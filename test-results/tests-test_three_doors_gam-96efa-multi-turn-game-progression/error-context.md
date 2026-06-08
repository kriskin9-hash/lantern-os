# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\test_three_doors_game.spec.js >> Three Doors Game - API Tests >> API handles multi-turn game progression
- Location: tests\test_three_doors_game.spec.js:55:3

# Error details

```
Error: expect(received).toContain(expected) // indexOf

Expected substring: "Moss Door"
Received string:    "You crawl through **The Burrow Door** into a snug earthen chamber lined with woven roots and faded quilts. Rain drums overhead. The fox curls up on a blanket and closes its eyes. A single lantern flickers in the corner."
```

# Test source

```ts
  1   | /**
  2   |  * Three Doors Game Browser Tests (Playwright)
  3   |  * OSS stack tests using Playwright - tests the full game flow
  4   |  *
  5   |  * Run with server: npm start --prefix apps/lantern-garage
  6   |  * Then: npx playwright test tests/test_three_doors_game.spec.js --headed
  7   |  */
  8   | 
  9   | const { test, expect } = require("@playwright/test");
  10  | 
  11  | const BASE_URL = "http://127.0.0.1:4177";
  12  | const DREAM_CHAT_URL = `${BASE_URL}/dream-chat.html`;
  13  | 
  14  | test.describe("Three Doors Game - API Tests", () => {
  15  |   test("API returns valid initial game state", async ({ page }) => {
  16  |     const response = await page.request.post(`${BASE_URL}/api/dream/doors`, {
  17  |       data: { userId: "test-player-1", action: "start" }
  18  |     });
  19  | 
  20  |     expect(response.ok()).toBeTruthy();
  21  |     const data = await response.json();
  22  | 
  23  |     expect(data.text).toContain("Moss Door");
  24  |     expect(data.doors).toHaveLength(3);
  25  |     expect(data.fox_present).toBe(true);
  26  |     expect(data.scene_key).toBe("moss-entry");
  27  |     expect(data.history).toBeDefined();
  28  |   });
  29  | 
  30  |   test("API accepts door choice and returns new scene", async ({ page }) => {
  31  |     // Start game
  32  |     const startResp = await page.request.post(`${BASE_URL}/api/dream/doors`, {
  33  |       data: { userId: "test-player-2", action: "start" }
  34  |     });
  35  |     const startData = await startResp.json();
  36  |     const firstDoor = startData.doors[0];
  37  | 
  38  |     // Choose a door
  39  |     const choiceResp = await page.request.post(`${BASE_URL}/api/dream/doors`, {
  40  |       data: {
  41  |         userId: "test-player-2",
  42  |         action: "choose",
  43  |         choice: firstDoor.label
  44  |       }
  45  |     });
  46  | 
  47  |     expect(choiceResp.ok()).toBeTruthy();
  48  |     const choiceData = await choiceResp.json();
  49  | 
  50  |     expect(choiceData.text).toBeTruthy();
  51  |     expect(choiceData.doors).toHaveLength(3);
  52  |     expect(choiceData.text).not.toBe(startData.text); // Should be a different scene
  53  |   });
  54  | 
  55  |   test("API handles multi-turn game progression", async ({ page }) => {
  56  |     const userId = "test-player-3";
  57  | 
  58  |     // Turn 1: Start
  59  |     const turn1 = await page.request.post(`${BASE_URL}/api/dream/doors`, {
  60  |       data: { userId, action: "start" }
  61  |     });
  62  |     let state = await turn1.json();
> 63  |     expect(state.text).toContain("Moss Door");
      |                        ^ Error: expect(received).toContain(expected) // indexOf
  64  | 
  65  |     // Turn 2: Choose door C
  66  |     const turn2 = await page.request.post(`${BASE_URL}/api/dream/doors`, {
  67  |       data: { userId, action: "choose", choice: "C" }
  68  |     });
  69  |     state = await turn2.json();
  70  |     expect(state.text).toBeTruthy();
  71  | 
  72  |     // Turn 3: Choose another door
  73  |     const doorB = state.doors.find(d => d.label === "B");
  74  |     if (doorB) {
  75  |       const turn3 = await page.request.post(`${BASE_URL}/api/dream/doors`, {
  76  |         data: { userId, action: "choose", choice: doorB.label }
  77  |       });
  78  |       state = await turn3.json();
  79  |       expect(state.text).toBeTruthy();
  80  |       expect(state.history.length).toBeGreaterThan(1);
  81  |     }
  82  |   });
  83  | 
  84  |   test("Game engine includes Stable Diffusion image prompts", async ({ page }) => {
  85  |     const response = await page.request.post(`${BASE_URL}/api/dream/doors`, {
  86  |       data: { userId: "test-player-4", action: "start" }
  87  |     });
  88  | 
  89  |     const data = await response.json();
  90  |     expect(data.image_prompt).toBeTruthy();
  91  |     expect(typeof data.image_prompt).toBe("string");
  92  |     expect(data.image_prompt.length).toBeGreaterThan(20);
  93  |   });
  94  | 
  95  |   test("Image generation endpoint returns prompt data", async ({ page }) => {
  96  |     const response = await page.request.post(`${BASE_URL}/api/dream/doors/image`, {
  97  |       data: { userId: "test-player-5", doorIndex: 0 }
  98  |     });
  99  | 
  100 |     expect(response.ok()).toBeTruthy();
  101 |     const data = await response.json();
  102 | 
  103 |     expect(data).toHaveProperty("available");
  104 |     if (!data.available && data.suggestion) {
  105 |       expect(data.suggestion).toHaveProperty("prompt");
  106 |       expect(data.suggestion.prompt.length).toBeGreaterThan(20);
  107 |     }
  108 |   });
  109 | 
  110 |   test("Invalid choice returns error", async ({ page }) => {
  111 |     const response = await page.request.post(`${BASE_URL}/api/dream/doors`, {
  112 |       data: { userId: "test-player-6", action: "choose", choice: "Z" }
  113 |     });
  114 | 
  115 |     const data = await response.json();
  116 |     expect(data.error || !data.doors).toBeTruthy();
  117 |   });
  118 | });
  119 | 
  120 | test.describe("Three Doors Game - UI Tests", () => {
  121 |   test.beforeEach(async ({ page }) => {
  122 |     await page.goto(DREAM_CHAT_URL);
  123 |     await page.waitForSelector("#input", { timeout: 10000 });
  124 |   });
  125 | 
  126 |   test("Three Doors command launches game in Dream Chat", async ({ page }) => {
  127 |     const input = page.locator("#input");
  128 |     const sendBtn = page.locator("#send-btn");
  129 | 
  130 |     // Type and send the Three Doors command
  131 |     await input.fill("!three-doors");
  132 |     await sendBtn.click();
  133 | 
  134 |     // Wait for door buttons to appear
  135 |     await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });
  136 | 
  137 |     // Verify game loaded
  138 |     const doorButtons = page.locator("button[onclick*='chooseDoorsPath']");
  139 |     const count = await doorButtons.count();
  140 |     expect(count).toBe(3);
  141 |   });
  142 | 
  143 |   test("Game displays scene text and door options", async ({ page }) => {
  144 |     const input = page.locator("#input");
  145 |     const sendBtn = page.locator("#send-btn");
  146 | 
  147 |     await input.fill("!three-doors");
  148 |     await sendBtn.click();
  149 | 
  150 |     // Wait for game to load
  151 |     await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });
  152 | 
  153 |     // Check for scene content
  154 |     const bubbles = page.locator(".bubble");
  155 |     const bubbleText = await bubbles.nth(bubbles.count() - 1).textContent();
  156 | 
  157 |     expect(bubbleText).toContain("Door");
  158 |   });
  159 | 
  160 |   test("Can click door button and navigate to new scene", async ({ page }) => {
  161 |     const input = page.locator("#input");
  162 |     const sendBtn = page.locator("#send-btn");
  163 | 
```