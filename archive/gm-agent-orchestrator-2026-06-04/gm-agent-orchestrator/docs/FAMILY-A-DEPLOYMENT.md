# Family A Deployment — Lantern Setup Guide

**Version:** 1.0  
**Date:** 2026-05-25  
**Target:** Off-grid families (vans, buses, farms) with Starlink internet  
**Setup Time:** 15 minutes  
**Support:** Email support + voice tutorial included  

---

## What You're Getting

**Lantern Desktop** — Local-first AI chat for your family. No cloud tracking. Works on Starlink.

- **Chat with AI** — Kids ask Claude/Gemini homework questions. Parents get thoughtful answers.
- **Offline-First** — Works even if Starlink drops. Local AI models included (optional).
- **Private** — Nothing leaves your computer. No ads. No data harvesting.
- **Audio Tutorial** — Frank Sinatra walks you through setup in 5 minutes.
- **Monthly:** $20/mo (billed via Stripe or PayPal)

---

## Prerequisites (5 min check)

### System Requirements
- **Windows PC:** Windows 10 or newer
- **RAM:** 4GB minimum (8GB recommended)
- **SSD Space:** 2GB free for app + models
- **Python:** Version 3.9+ (pre-installed on newer Windows)
- **Internet:** Starlink or any broadband (needed for cloud AI setup only; local models work offline)

### Check Your System
Open Command Prompt and paste these commands:

```bash
python --version
```

Expected: `Python 3.9.X` or higher

If you see `'python' is not recognized`, [download Python 3.9+](https://www.python.org/downloads/) and install it.

### Get API Keys (10 min, skip if using local models)

**Option A: Claude (Recommended)**
1. Go to https://console.anthropic.com/
2. Click "Sign in" (use your Google account)
3. Go to API Keys → Create Key
4. Copy the key (starts with `sk-ant-`)
5. **Save it in a text file — you'll need it in 10 minutes**

**Option B: Google Gemini (Free tier available)**
1. Go to https://makersuite.google.com/
2. Click "Create API Key"
3. Select your project
4. Copy the key
5. **Save it in a text file**

**Option C: Local LLM (No API key needed)**
- If you have [LM Studio](https://lmstudio.ai/) or [Ollama](https://ollama.ai/) running, Lantern will auto-detect it.

---

## Installation (5 minutes)

### Step 1: Get the Code
Open Command Prompt and paste:

```bash
cd Documents
git clone https://github.com/alex-place/gm-agent-orchestrator.git
cd gm-agent-orchestrator
```

If `git` is not installed, [download Git](https://git-scm.com/download/win) first.

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Launch Lantern
Double-click:
```
scripts/start-lantern-chat.bat
```

Or paste in Command Prompt:
```bash
python scripts/lantern-desktop-auth-ui.py
```

---

## First Run (5 minutes)

### Step 1: Hear the Welcome Message
Frank Sinatra's voice will greet you: *"Welcome to Lantern. I'm Frank. Let's set up your AI chat in five minutes."*

(If you don't hear audio, no problem — the app still works.)

### Step 2: Choose Your AI Provider
You'll see 5 buttons:

- **Claude** ← Recommended. Most capable. Needs API key.
- **Gemini** ← Fast and free tier available.
- **DeepSeek** ← Alternative, lower cost.
- **Local LM Studio** ← Offline. No API key needed.
- **Local Ollama** ← Offline. No API key needed.

**Click Claude** (or your choice).

### Step 3: Enter Your API Key
If you chose Claude or Gemini, paste your API key:

- Clear the field
- Ctrl+V to paste your API key
- Click "Save Provider Credentials"
- You should see ✅ (green checkmark) next to Claude

### Step 4: Set Primary Provider
Click "Set Primary Provider" and choose **Claude**.

(If you want a fallback, click "Set Fallback Provider" and choose **Gemini**.)

### Step 5: Click "Ready"
The chat interface will open.

### Step 6: Send Your First Message
Type: `Hello, what's the capital of France?`

Press **Ctrl+Enter** (or click Send).

Watch the response stream word-by-word. No waiting.

---

## Troubleshooting

### "Python not found"
**Solution:** Download Python 3.9+ from https://www.python.org/downloads/. During install, check the box **"Add Python to PATH"**.

### "Cannot connect to Claude"
**Solution:**
1. Check your API key is copied correctly (no extra spaces)
2. Verify internet connection (ping google.com from Command Prompt)
3. Try Gemini instead (different API endpoint)
4. Wait 30 seconds and try again (API rate limiting)

### "LM Studio not starting"
**Solution:**
1. LM Studio is optional. Use Claude/Gemini instead.
2. If you want local inference, [install LM Studio](https://lmstudio.ai/), download a model, and click "Start Server".
3. Then restart Lantern.

### "Starlink latency is too high"
**Expected:** 100–600ms on Starlink (normal).  
**Lantern handles it:** Responses still stream, just slower than fiber. No timeouts.

### "App crashes on startup"
**Solution:**
1. Check Command Prompt for error messages (don't close it)
2. Copy the error message
3. Email support@lantern.local with the error

---

## Daily Use

### Chat with Your Kids
Open Lantern, type questions:
- "Help me with my math homework"
- "What's photosynthesis?"
- "Write a story about a dragon"
- "Explain quantum computing simply"

Responses stream instantly. No waiting for the full answer.

### Switch AI Providers
Open Lantern → Click "Set Primary Provider" → Choose a different AI.

### Offline Mode (if using local LLM)
If Starlink drops:
1. LM Studio or Ollama keeps working (if installed)
2. Chat continues locally, no internet needed
3. When internet returns, cloud APIs work again

---

## Privacy & Security

### What Lantern Sees
- Your questions (sent to the AI provider you choose)
- Nothing else (no files, browsing, camera)

### Where Your Data Lives
- Local: On your PC's `~/.lantern/` directory (encrypted)
- Cloud: Only if you choose Claude/Gemini (encrypted in transit)

### What We Don't Do
- ❌ No ads
- ❌ No tracking
- ❌ No selling data
- ❌ No accessing your files
- ❌ No recording audio (unless you enable Lantern Kids voice feature)

---

## Monthly Cost & Billing

### How Much?
- **$20/mo** for Lantern Desktop (billed monthly via Stripe or PayPal)
- First month: Free trial (7 days, no card needed)

### How to Pay?
1. After your 7-day trial, Lantern will prompt you to add a payment method
2. Choose Stripe (credit card) or PayPal
3. Auto-renews monthly; cancel anytime

### What If I Don't Want Lantern Kids?
That's fine. Lanterns Desktop (chat only) stays $20/mo.

**Lantern Kids** (parental review, age-gating) is $30/mo per child (optional add-on).

---

## Support

### Email
**support@lantern.local**

Include:
- What happened (e.g., "Chat won't connect")
- Error message (copy from Command Prompt)
- Windows version (type `winver` in Command Prompt)

### Response Time
- **Critical** (can't launch): 2 hours
- **High** (app crashes): 4 hours
- **Normal** (questions): 24 hours

---

## Next Steps

1. ✅ **Install Lantern** (this guide)
2. 💬 **Chat with your kids** (try asking questions)
3. 📧 **Email feedback** (what could be better?)
4. 💳 **Subscribe** ($20/mo after trial)

---

## FAQ

**Q: Do I need Starlink?**  
A: Nope. Any internet works (fiber, cable, mobile hotspot). Starlink users: we've tested it; expect 150–400ms latency (normal for Starlink).

**Q: Can I use Lantern offline?**  
A: Yes, if you install [LM Studio](https://lmstudio.ai/) or [Ollama](https://ollama.ai/). Cloud APIs (Claude, Gemini) need internet.

**Q: Is Lantern safe for kids?**  
A: Yes. For extra safety, use **Lantern Kids** ($30/mo per child). Parents see all questions + answers before the child does.

**Q: Can I cancel anytime?**  
A: Yes. No contract. Cancel from your billing portal anytime.

**Q: What if I have an old Windows PC?**  
A: Windows 7–9 aren't supported. Windows 10+ required.

---

## Video Walkthrough (Optional)

[Link to YouTube walkthrough coming soon]

---

**Welcome to Lantern. Enjoy learning.**

*Questions? Email support@lantern.local*

---

**Version:** 1.0 | **Date:** 2026-05-25 | **Status:** Ready for Family A Deployment
