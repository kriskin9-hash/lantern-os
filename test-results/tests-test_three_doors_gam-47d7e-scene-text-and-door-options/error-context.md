# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\test_three_doors_game.spec.js >> Three Doors Game - UI Tests >> Game displays scene text and door options
- Location: tests\test_three_doors_game.spec.js:143:3

# Error details

```
TimeoutError: page.waitForSelector: Timeout 8000ms exceeded.
Call log:
  - waiting for locator('button[onclick*=\'chooseDoorsPath\']') to be visible

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e2]:
    - banner [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]: 💭
        - generic [ref=e6]: Dream Journal
      - generic [ref=e7]:
        - button "⚙️" [ref=e8] [cursor=pointer]
        - button "☀️" [ref=e9] [cursor=pointer]
    - generic [ref=e10]:
      - generic [ref=e12]: "!three-doors"
      - generic [ref=e14]: Dream interpreter ready to help...
    - generic [ref=e16]:
      - textbox "What's on your mind?" [ref=e17]
      - button "→" [active] [ref=e18] [cursor=pointer]
  - generic:
    - generic:
      - generic:
        - heading "Settings" [level=2]
        - button "×"
      - generic:
        - generic:
          - generic: AI Provider
          - combobox:
            - option "Auto (pick best)" [selected]
            - option "Claude"
            - option "ChatGPT"
            - option "Gemini"
            - option "Grok"
            - option "Local (Ollama)"
        - generic:
          - generic: API Keys
          - generic:
            - generic: ✦
            - generic:
              - generic: Claude
              - generic: connected
          - textbox "•••••••• (set — enter new key to replace)":
            - /placeholder: ••••••••  (set — enter new key to replace)
        - generic:
          - generic:
            - generic: 🌐
            - generic:
              - generic: Gemini
              - generic: connected
          - textbox "•••••••• (set — enter new key to replace)":
            - /placeholder: ••••••••  (set — enter new key to replace)
        - generic:
          - generic:
            - generic: ◈
            - generic:
              - generic: ChatGPT
              - generic: connected
          - textbox "•••••••• (set — enter new key to replace)":
            - /placeholder: ••••••••  (set — enter new key to replace)
        - generic:
          - generic:
            - generic: 𝕏
            - generic:
              - generic: Grok
              - generic: connected
          - textbox "•••••••• (set — enter new key to replace)":
            - /placeholder: ••••••••  (set — enter new key to replace)
        - separator
        - generic:
          - generic: Dream Actions
          - button "+ Record a Dream"
```

# Test source

```ts
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
  63  |     expect(state.text).toContain("Moss Door");
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
> 151 |     await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });
      |                ^ TimeoutError: page.waitForSelector: Timeout 8000ms exceeded.
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
  164 |     // Start game
  165 |     await input.fill("!three-doors");
  166 |     await sendBtn.click();
  167 | 
  168 |     // Wait for initial scene
  169 |     await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });
  170 | 
  171 |     // Get the initial button count
  172 |     let doorButtons = page.locator("button[onclick*='chooseDoorsPath']");
  173 |     const initialCount = await doorButtons.count();
  174 | 
  175 |     // Click first door
  176 |     const firstButton = doorButtons.nth(0);
  177 |     await firstButton.click();
  178 | 
  179 |     // Wait for new scene to render
  180 |     await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });
  181 | 
  182 |     // Should still have door buttons
  183 |     doorButtons = page.locator("button[onclick*='chooseDoorsPath']");
  184 |     const newCount = await doorButtons.count();
  185 |     expect(newCount).toBe(3);
  186 |   });
  187 | 
  188 |   test("Game shows fox presence indicator", async ({ page }) => {
  189 |     const input = page.locator("#input");
  190 |     const sendBtn = page.locator("#send-btn");
  191 | 
  192 |     await input.fill("!three-doors");
  193 |     await sendBtn.click();
  194 | 
  195 |     // Wait for game
  196 |     await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });
  197 | 
  198 |     // Look for fox indicator (🦊)
  199 |     const foxIndicator = page.locator("text=🦊");
  200 |     const isFoxVisible = await foxIndicator.isVisible().catch(() => false);
  201 | 
  202 |     // Fox should be mentioned in initial scene
  203 |     expect(isFoxVisible).toBeTruthy();
  204 |   });
  205 | 
  206 |   test("Can navigate through multiple doors without error", async ({ page }) => {
  207 |     const input = page.locator("#input");
  208 |     const sendBtn = page.locator("#send-btn");
  209 | 
  210 |     // Start game
  211 |     await input.fill("!three-doors");
  212 |     await sendBtn.click();
  213 | 
  214 |     await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });
  215 | 
  216 |     // Navigate through 3 doors sequentially
  217 |     for (let i = 0; i < 3; i++) {
  218 |       const buttons = page.locator("button[onclick*='chooseDoorsPath']");
  219 |       const isVisible = await buttons.nth(0).isVisible();
  220 | 
  221 |       if (isVisible) {
  222 |         await buttons.nth(i % 3).click();
  223 |         // Wait for next scene
  224 |         await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 6000 });
  225 |       }
  226 |     }
  227 | 
  228 |     // Page should still be functional
  229 |     const title = await page.title();
  230 |     expect(title).toBeTruthy();
  231 |   });
  232 | 
  233 |   test("Image prompts are visible in scene data", async ({ page }) => {
  234 |     const input = page.locator("#input");
  235 |     const sendBtn = page.locator("#send-btn");
  236 | 
  237 |     await input.fill("!three-doors");
  238 |     await sendBtn.click();
  239 | 
  240 |     await page.waitForSelector("button[onclick*='chooseDoorsPath']", { timeout: 8000 });
  241 | 
  242 |     // Look for image prompt indicator
  243 |     const promptIndicator = page.locator("text=/📸|Stable Diffusion|prompt/i");
  244 |     const isPromptVisible = await promptIndicator.isVisible().catch(() => false);
  245 | 
  246 |     // Prompt should be displayed
  247 |     expect(isPromptVisible).toBeTruthy();
  248 |   });
  249 | 
  250 |   test("Server responds to multiple concurrent game sessions", async ({ page }) => {
  251 |     // Run 3 API calls concurrently
```