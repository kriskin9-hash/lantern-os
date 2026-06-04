# Lantern Desktop — Accessible Setup Tutorial

**Font size:** 18pt minimum | **Contrast:** WCAG AAA | **Keyboard:** Tab only, no mouse required

---

## 🎯 GOAL: Sign into Lantern and Connect Your AI

You will:
1. Open Lantern Desktop
2. See provider cards (Claude, Gemini, etc.)
3. Enter your API key ONE TIME
4. Click Ready
5. Start chatting

**Time: 5 minutes | Difficulty: EASY**

---

## STEP 1: OPEN LANTERN DESKTOP

**Visual Guide:**
```
┌─────────────────────────────────────┐
│ Windows Start Menu                  │
│                                     │
│ Search: "Lantern"                  │
│ Click: "Lantern Desktop" (big icon)│
│                                     │
└─────────────────────────────────────┘
                    ↓
         [App window opens]
```

**Keyboard:** 
- Press `Windows Key`
- Type `lantern`
- Press `Enter`

**Audio Description:**
> The Windows Start menu opens. You type "L-A-N-T-E-R-N" on your keyboard. The Lantern Desktop app icon appears. You press Enter to launch it.

---

## STEP 2: LANTERN AUTH SCREEN APPEARS

**What you see:**
```
┌────────────────────────────────────────────────┐
│  🔐 Lantern Provider Authentication             │
│  Sign in to connect your LLM providers          │
│                                                 │
│  ┌──────────────┐ ┌──────────────┐             │
│  │ 🧠 Claude    │ │ 🎨 Gemini    │             │
│  │ ⭕ Not Set   │ │ ⭕ Not Set   │             │
│  └──────────────┘ └──────────────┘             │
│                                                 │
│  ┌──────────────┐ ┌──────────────┐             │
│  │ ⚡ DeepSeek  │ │ 💻 LM Studio │             │
│  │ ⭕ Not Set   │ │ ⭕ Not Set   │             │
│  └──────────────┘ └──────────────┘             │
│                                                 │
│  [View Config] [Set Primary] [Set Fallback]    │
│                             [✅ Ready] [Cancel]│
└────────────────────────────────────────────────┘
```

**Audio Description:**
> You see a window titled "Lantern Provider Authentication." Below that, five large cards in a grid. Each card shows an emoji icon and a provider name: Claude (brain), Gemini (palette), DeepSeek (lightning), LM Studio (computer), and Ollama (llama). Under each name it says "Not Set" with a red circle. At the bottom are buttons for View Config, Set Primary, Set Fallback, Ready, and Cancel.

---

## STEP 3: SELECT CLAUDE (EASIEST TO START)

**Keyboard Navigation:**
- Press `Tab` four times to reach the Claude card
- Press `Enter` to open Claude setup form

**Mouse (if needed):**
- Click the Claude card (big blue box with 🧠 icon)

**Visual:**
```
Current focus:         After pressing Tab:
┌──────────────┐       ┌──────────────┐
│ 🧠 Claude    │       │ 🧠 Claude    │ ← FOCUSED (blue border)
│ ⭕ Not Set   │       │ ⭕ Not Set   │
└──────────────┘       └──────────────┘
```

**Audio Description:**
> You press the Tab key on your keyboard four times. Each press moves focus to the next button. When you reach the Claude card, it highlights with a blue border. You press Enter to select it.

---

## STEP 4: ENTER YOUR CLAUDE API KEY

**What appears:**
```
┌────────────────────────────────────────────┐
│  Configure Anthropic Claude                 │
│                                             │
│  Get your API key from:                     │
│  👉 https://console.anthropic.com/          │
│                                             │
│  API Key: [•••••••••••••••••••••]            │
│           ↑ (dots hide your key)            │
│                                             │
│  [Save Provider Credentials]                │
└────────────────────────────────────────────┘
```

**How to get your Claude API key (4 clicks):**
1. Open browser → https://console.anthropic.com/
2. Sign in with your Google account
3. Click "API Keys" on the left
4. Click "Create Key" button
5. Copy the long string (starts with `sk-ant-`)
6. Come back to Lantern window

**Entering the key — Keyboard only:**
- Press `Tab` once (moves to API Key field)
- Paste: `Ctrl+V` (your key)
- Press `Tab` (moves to Save button)
- Press `Enter` (saves)

**Audio Description:**
> The form now shows "Configure Anthropic Claude" at the top. Below that, blue text with a link to console.anthropic.com. Then a text field labeled "API Key" with dots hiding what you typed. Below that, a big button that says "Save Provider Credentials."

> To get your key: Open a web browser. Go to console.anthropic.com. Sign in. Click API Keys on the left side. Click Create Key. A long code appears. Copy it. Come back to Lantern. Click in the API Key box. Paste your code. Click Save Provider Credentials.

---

## STEP 5: SUCCESS — CLAUDE IS CONFIGURED ✅

**What you see:**
```
┌──────────────────────────────────────────┐
│  ✅ Anthropic Claude configured!          │
│                                           │
│  Credentials saved securely at:           │
│  C:\Users\YourName\.lantern\credentials\  │
│                                           │
│                        [OK]               │
└──────────────────────────────────────────┘
```

**Audio Description:**
> A green checkmark appears. The message says "Anthropic Claude configured. Credentials saved securely." There's an OK button.

**Press:**
- `Enter` (closes the popup)

---

## STEP 6: YOU'RE BACK AT THE MAIN SCREEN

**Now Claude shows ✅ instead of ⭕:**
```
BEFORE:                    AFTER:
┌──────────────┐           ┌──────────────┐
│ 🧠 Claude    │           │ 🧠 Claude    │
│ ⭕ Not Set   │     →     │ ✅ Configured│
└──────────────┘           └──────────────┘
```

**Audio Description:**
> Back at the main screen. The Claude card now shows a green checkmark instead of a red circle. It says "✅ Configured."

---

## STEP 7: SET CLAUDE AS YOUR PRIMARY PROVIDER

**Why:** This tells Lantern "Use Claude first when I chat"

**Keyboard:**
- Press `Tab` until blue box is around `[Set Primary Provider]` button
- Press `Enter`

**Visual:**
```
[View Config] [Set Primary] ← FOCUS HERE [Set Fallback]
```

**What happens:**
```
┌──────────────────────────────────────────┐
│  Set Primary Provider                     │
│                                           │
│  Select from available providers:         │
│  • claude                                 │
│                                           │
│                        [OK]               │
└──────────────────────────────────────────┘
```

**Keyboard in the popup:**
- Press `Down Arrow` to select `claude`
- Press `Enter` to confirm

**Audio Description:**
> You press Tab until the "Set Primary Provider" button is highlighted. You press Enter. A new window appears asking you to select a provider. You see "claude" in a list. You press Down Arrow if needed to highlight it, then press Enter.

**Success:**
```
✅ Primary provider set to: claude
```

---

## STEP 8: CLICK "✅ READY" TO START CHATTING

**Keyboard:**
- Press `Tab` until blue box is around `[✅ Ready]` button (bottom right)
- Press `Enter`

**Visual:**
```
┌────────────────────────────────────────────┐
│  Lantern — Provider Authentication         │
│                                             │
│  [View Config] [Set Primary] [Set Fallback]│
│                             [✅ Ready] ← HERE
└────────────────────────────────────────────┘
```

**What happens next:**
- Auth window closes
- Main Lantern Chat window opens
- You see a chat box ready to type

**Audio Description:**
> You press Tab to move focus to the green "Ready" button in the bottom right. You press Enter. The authentication window closes. The main Lantern Chat window appears with a text box where you can type your questions.

---

## STEP 9: START CHATTING ✅

**Chat interface:**
```
┌──────────────────────────────────────────┐
│  Lantern Chat                             │
│                                           │
│  ┌──────────────────────────────────────┐│
│  │ (previous messages appear here)      ││
│  │                                      ││
│  └──────────────────────────────────────┘│
│                                           │
│  Type your question:                      │
│  [Type here... ........................]  │
│  [Send]                                  │
└──────────────────────────────────────────┘
```

**To send a message:**
- Type: `What is the capital of France?`
- Keyboard: Press `Ctrl+Enter` to send
- Or click `[Send]` button

**Audio Description:**
> The chat window now shows a text box at the bottom that says "Type your question." You type your question. You press Ctrl+Enter to send it. Claude's response appears above your message.

---

## 🎯 YOU DID IT! YOU'RE CHATTING WITH CLAUDE ✅

---

## ⌨️ QUICK KEYBOARD REFERENCE

| Action | Key |
|--------|-----|
| Move to next button | `Tab` |
| Move to previous button | `Shift+Tab` |
| Click/activate button | `Enter` |
| Send chat message | `Ctrl+Enter` |
| Paste API key | `Ctrl+V` |
| Cancel dialog | `Esc` |

---

## 🆘 ACCESSIBILITY FEATURES IN LANTERN

### Screen Reader Support
- All buttons have labels (ARIA)
- Form fields have descriptions
- Status updates announced
- Error messages read aloud

### Keyboard Navigation
- **Tab only** — navigate through all controls
- **No mouse required** — everything keyboard accessible
- **Focus visible** — blue border shows where you are
- **Large target size** — buttons are big (easy to click if using mouse)

### Visual Accessibility
- **High contrast** — white text on dark background (WCAG AAA)
- **Large text** — 14-18pt minimum font size
- **Clear labels** — every button says exactly what it does
- **Emoji + text** — visual + text for icons

### Cognitive Accessibility
- **One step at a time** — this tutorial breaks it into 9 simple steps
- **Plain language** — no jargon (no "credentials," just "save")
- **Visual progress** — checkmarks show what's done (✅ vs ⭕)
- **Undo friendly** — can go back and fix mistakes

---

## 📞 NEED HELP?

If you get stuck:

1. **Can't find the API key field?**
   - Press `Tab` repeatedly. You'll cycle through every button.
   - When the blue border is on the field, type your key.

2. **API key not working?**
   - Make sure you copied the ENTIRE key (starts with `sk-ant-`)
   - No extra spaces before or after
   - Go back to console.anthropic.com, make a NEW key if unsure

3. **Claude not responding?**
   - Check internet connection
   - Try asking a simple question first: "Hello"
   - If still stuck, run: `python scripts/lantern-provider-auth.py status`

4. **Want to add Gemini too?**
   - Follow the same steps (Step 3 again) but click Gemini card instead
   - Get key from: https://makersuite.google.com/
   - Set as fallback (so Claude tries first, Gemini as backup)

---

## 🎵 AUDIO GUIDE (Text to Speech)

Copy this text and paste into a text-to-speech app for audio walkthrough:

```
Step one: Open Windows Start menu. Type Lantern. Press Enter.

Step two: Wait for Lantern Desktop to open. You see five provider cards.

Step three: Press Tab four times to reach Claude. Press Enter.

Step four: Click on the link to console-dot-anthropic-dot-com. Sign in. 
Go to API Keys. Create a new key. Copy it. Come back to Lantern. 
Paste the key in the API Key field. Click Save Provider Credentials.

Step five: A green checkmark appears. Click OK.

Step six: The Claude card now shows a checkmark instead of a circle.

Step seven: Press Tab to reach Set Primary Provider. Press Enter. 
Select Claude. Press Enter.

Step eight: Press Tab to reach the Ready button. Press Enter.

Step nine: Type a question. Press Ctrl+Enter to send. Claude responds.

Done. You are now chatting with Claude.
```

---

**Last updated:** 2026-05-25  
**Tested with:** Screen readers (NVDA), keyboard-only, high contrast mode  
**Accessibility:** WCAG 2.1 Level AAA
