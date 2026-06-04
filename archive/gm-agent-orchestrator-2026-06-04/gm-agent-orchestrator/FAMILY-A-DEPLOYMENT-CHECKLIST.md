# Family A Deployment Checklist
**Target: 2026-05-26 (24-hour milestone)**

---

## Pre-Deployment (Founder - 1 hour)

### Contact & Relationship
- [ ] Confirm Family A contact info (name, email, phone)
- [ ] Schedule 30-min setup call (06:00 UTC or preferred timezone)
- [ ] Send welcome email with:
  - [ ] Download link to Lantern installer
  - [ ] FAMILY-A-DEPLOYMENT.md (setup guide)
  - [ ] FAQ + troubleshooting (11 scenarios)
  - [ ] Support email (support@lantern.local)
  - [ ] 30-day free trial code (no payment first month)

### System Verification
- [ ] Verify Python 3.9+ can run on their PC
- [ ] Test `lantern-desktop-auth-ui.py` on Windows 10/11
- [ ] Test `lantern-chat-ui.py` streaming with Claude API
- [ ] Test `lantern-audio-narrator.py` audio output (Frank narration)
- [ ] Verify all 3 LLM providers work (Claude, Gemini, DeepSeek)
- [ ] Test local LLM auto-detect (LM Studio, Ollama)

---

## Setup Call (Founder + Family A - 30 minutes)

### Schedule: 06:00 UTC (or agreed time)

**Script (Founder reads):**
> "Hi [Family]! Welcome to Lantern. We're going to set this up together in about 15 minutes. You'll have a chat interface that works even without internet, and Frank Sinatra is going to guide you through. Let me share my screen and walk you through it."

### Setup Steps (Real-time, screen-shared)

**Step 1: Download (2 min)**
- User downloads installer from link
- Saves to `C:\Users\[name]\Downloads\`
- Confirms file is there (~300MB)

**Step 2: Install (3 min)**
- User runs installer
- Selects Python 3.9+ installation
- Confirms "Lantern installed successfully"

**Step 3: Launch Auth UI (1 min)**
- User runs `python scripts/lantern-desktop-auth-ui.py`
- **Audio plays:** Frank says "Welcome to Lantern. First, choose your AI provider."
- 5 buttons appear: Claude, Gemini, DeepSeek, LM Studio, Ollama

**Step 4: Choose Provider (2 min)**
- User clicks Claude (or prefers)
- Founder says: "Claude is best for families. You need an API key."
- If user has Claude API key, they paste it
- If not, Founder shows how to create one (2-min side task)

**Step 5: Verify (1 min)**
- User clicks "Ready" button
- **Audio plays:** "Verifying API key..."
- ✅ If success: "Lantern is live. Welcome."
- ❌ If fail: Founder helps troubleshoot (bad key, rate limit, etc.)

**Step 6: Test Chat (1 min)**
- Chat interface opens
- User types: "What is Lantern?"
- Bot responds in real-time (streaming)
- User sees responses word-by-word

**Step 7: Set Preferences (1 min)**
- Show font size selector (set to 14pt if vision issues)
- Show font family selector (Arial if dyslexia)
- Show keyboard hint (Tab to navigate, Ctrl+Enter to send)

**Total setup time: ~15 minutes**

### Success Criteria (during call)
- ✅ Chat interface opens without errors
- ✅ Response streams in real-time
- ✅ No crashes or freezing
- ✅ User sends 2–3 test messages
- ✅ User asks for access to set as auto-start (optional)

---

## Post-Setup (Founder - 30 minutes)

### Immediate Follow-Up (send within 1 hour)

**Email to Family A:**
```
Subject: Lantern Setup Complete ✅

Hi [Family Name],

You're all set! Lantern is ready to use.

KEY INFO:
- Chat works offline (if you set up local LLM) or with Starlink
- Frank narration plays automatically on startup
- You can change text size (14pt, 16pt, 18pt for easier reading)
- Keyboard navigation: Tab between fields, Ctrl+Enter to send

NEXT STEPS:
1. Try asking questions: "What's 2+2?", "How do I bake bread?", "Teach me about space"
2. Set as auto-start (optional) — guides in FAQ
3. Invite kids to use it (parental controls in Lantern Kids version coming 2026-05-26)

SUPPORT:
- Reply to this email for any issues
- FAQ: [link to troubleshooting]
- Critical issues: Call [support phone] 24/7

PAYMENT:
- First 30 days: FREE trial
- After 30 days: $20/mo (auto-renew unless you cancel)
- No setup fee, cancel anytime

Thanks for being our first family. You're helping us build the future of AI.

— Lantern Team
```

### Day 1 Check-In (Founder calls or texts)
- [ ] Call after 4 hours to confirm setup went smoothly
- [ ] Ask: "Are the kids asking questions? Is it working?"
- [ ] Listen for issues: crashes, slow responses, audio problems
- [ ] Offer 1-on-1 support if needed

---

## Telemetry Integration (Auto-logged)

### What We Track (Privacy-first)
- Usage: Sessions per day, chat message count, response time
- Crashes: Stack traces (no PII), error codes, timestamps
- Providers: Which API used (Claude/Gemini/LM Studio), success rate
- Accessibility: Font size selected, font family used
- Performance: Latency, token throughput, streaming quality

**Stored:** `~/.lantern/telemetry/session-[date].jsonl` (local only, never uploaded without consent)

### Basic Telemetry Code (in lantern-chat-ui.py)

```python
import json
from pathlib import Path
from datetime import datetime

class LanternTelemetry:
    def __init__(self):
        self.telemetry_dir = Path.home() / ".lantern" / "telemetry"
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.telemetry_dir / f"session-{datetime.now():%Y%m%d-%H%M%S}.jsonl"
        self.session_start = datetime.now()
        self.message_count = 0
        self.crash_count = 0

    def log_message(self, sender: str, length: int, provider: str):
        """Log a message sent or received."""
        self.message_count += 1
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "message",
            "sender": sender,
            "length": length,
            "provider": provider,
            "message_count": self.message_count
        }
        with open(self.session_file, 'a') as f:
            f.write(json.dumps(record) + '\n')

    def log_crash(self, error: str, traceback: str):
        """Log a crash (stack trace, no PII)."""
        self.crash_count += 1
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "crash",
            "error": error,
            "traceback": traceback
        }
        with open(self.session_file, 'a') as f:
            f.write(json.dumps(record) + '\n')

    def log_session_end(self):
        """Log session closure."""
        duration = (datetime.now() - self.session_start).total_seconds()
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "session_end",
            "duration_sec": duration,
            "message_count": self.message_count,
            "crash_count": self.crash_count
        }
        with open(self.session_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
```

---

## Billing Integration

### Step 1: Payment Confirmation (Manual for MVP)

**Stripe Setup (simple):**
- Create Stripe account
- Generate one payment link: https://buy.stripe.com/lantern-20-mo-family
- Email link to Family A
- Stripe handles recurring billing ($20/mo, cancel anytime)

**Alternative:** PayPal subscription link (simpler UX)

**Email template:**
```
Subject: Lantern Monthly Plan — $20/mo Starting [DATE+30]

Hi [Family Name],

Your 30-day free trial is ending on [DATE]. 

To continue using Lantern, click the link below to set up $20/mo billing:

[Payment Link]

This is optional. You can cancel anytime — no cancellation fee.

Questions? Reply to this email.

— Lantern Team
```

### Step 2: Track Payment Status

**Payment checklist file:** `~/.lantern/billing/payment-log.jsonl`

```json
{"family_id": "family-a", "date": "2026-05-26", "trial_start": "2026-05-26", "trial_end": "2026-06-25", "payment_link_sent": "2026-06-20", "payment_received": false}
{"family_id": "family-a", "date": "2026-06-25", "payment_received": true, "amount": 20.00, "currency": "USD", "next_billing_date": "2026-07-25"}
```

---

## Day-by-Day Success Tracking

### Days 1–3: Installation Proof
- [ ] Installation succeeds without error
- [ ] Chat responds to ≥3 messages
- [ ] Zero crashes or freezing
- [ ] Audio narration plays correctly

**Action:** Founder checks in via email/text

### Days 4–14: Usage Validation
- [ ] Family uses Lantern ≥3 days/week
- [ ] Kids ask 5–10 questions per session
- [ ] Zero abandonment (all sessions complete)
- [ ] Telemetry shows: 15+ messages/day, <2% crash rate

**Action:** Founder offers 1-on-1 support call if needed

### Days 15–30: Proof of Concept
- [ ] First payment confirmed ($20/mo)
- [ ] Unsolicited referral ("My friend wants this")
- [ ] NPS score: ≥7/10 ("Would you recommend Lantern?")
- [ ] Kids are using Lantern Kids features (parental controls working)

**Action:** Founder calls to celebrate, asks permission to use as case study

---

## Success Criteria (End of 24-hour milestone)

| Metric | Target | Status |
|--------|--------|--------|
| **Family A Setup** | Complete, zero errors | 🟡 In progress |
| **First Chat Message** | Sent & received, streams in real-time | 🟡 In progress |
| **Audio Narration** | Frank plays, user follows guide | 🟡 In progress |
| **Payment Plan** | Family agrees to $20/mo (trial ends 2026-06-25) | 🟡 In progress |
| **Telemetry** | First 3 days of data logged (usage, crashes, providers) | 🟡 In progress |
| **Blog Post Published** | "30 Days with Lantern — Van Family AI Chat" | 🟡 In progress |
| **Lantern Kids Alpha** | Parental controls + age-gating working | 🟡 In progress |

---

## Rollout Timeline

**2026-05-26 06:00** — Founder calls Family A, setup begins
**2026-05-26 06:35** — Setup complete, first payment plan sent
**2026-05-26 12:00** — Day 1 check-in (Founder)
**2026-05-27 00:00** — Blog post published (internal, not public yet)
**2026-05-31 00:00** — Mid-trial check-in (Founder)
**2026-06-25 00:00** — Payment reminder sent
**2026-06-30 00:00** — First month complete, success metrics reported

---

## Notes for Founder

1. **Stay accessible:** Family A may not be tech-savvy. Walk them through slowly, use simple language.
2. **Expect quirks:** Local internet (Starlink) may have latency. Chat responses might take 2–3 sec instead of 1 sec. This is normal.
3. **Win on trust:** The goal is NOT to be perfect. The goal is to be honest, helpful, and responsive to feedback.
4. **Listen:** If Family A says "Can Lantern do X?", take notes. That's a feature request.
5. **Celebrate wins:** Every message sent is a win. Every day used is a win.

---

**Status:** Ready for deployment  
**Owner:** Founder  
**Duration:** 24 hours continuous support  
**Success:** Family A using Lantern daily by 2026-05-31
