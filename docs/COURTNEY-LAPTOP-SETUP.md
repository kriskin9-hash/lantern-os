# Courtney's Laptop Setup — Lantern OS + Windsurf + Trading

This guide sets up all three components on a Windows laptop: Lantern OS (main dashboard), Windsurf (AI editor), and Kalshi trade chat. Takes about 20 minutes.

---

## What You Get

| App | URL | Purpose |
|-----|-----|---------|
| Lantern Garage | http://127.0.0.1:4177 | Dashboard, Dreamer journal, Imagniverse, wallet |
| Imagniverse | http://127.0.0.1:4177/imagniverse | 20-panel status cube / system architecture |
| Trade Chat | http://127.0.0.1:8080 | Kalshi paper/live trading (paper mode by default) |
| Windsurf | local app | AI code editor, hooks wired automatically |

---

## Step 1: Install Prerequisites

Run these in PowerShell (check each with the version command):

| Tool | Download | Version Check |
|------|----------|---------------|
| Node.js 20+ | https://nodejs.org | `node --version` |
| Python 3.8+ | https://python.org (check "Add to PATH") | `python --version` |
| Git | https://git-scm.com | `git --version` |
| Windsurf | https://windsurf.ai | Launch after install |

---

## Step 2: Clone the Repo

```powershell
mkdir C:\tmp -ErrorAction SilentlyContinue
cd C:\tmp
git clone https://github.com/alex-place/lantern-os.git
cd lantern-os
```

---

## Step 3: One-Command Startup

The full-stack startup script handles npm install, starts both servers, runs the confidence report, and opens the browser:

```powershell
cd C:\tmp\lantern-os
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternFullStack.ps1
```

On first run this takes ~2 minutes (npm install). After that, ~10 seconds.

**Expected output:**
```
Lantern Garage: ONLINE at http://127.0.0.1:4177
Trade Chat: Skipping — .env file not configured (normal on first run)
Feature Confidence:
  Trading App (Kalshi)             85%  production_ready_gated
  Dream Journal (Dreamer)          95%  production_ready
  Imagniverse (Status Cube)        90%  production_ready
  Outreach Tracking               N/A  not_in_scope_for_courtney_laptop
  Payment & Invoice System         40%  backend_exists_ui_missing
Overall Confidence: 85% — GREEN LIGHT
```

---

## Step 4: Open Windsurf

1. Launch Windsurf
2. Open folder: `C:\tmp\lantern-os`
3. Done — `.windsurf/hooks.json` is auto-detected, safety hooks activate

Hooks validate file writes, MCP tool use, and command execution. No manual configuration needed.

---

## Step 5: First-Time Flow

1. Open http://127.0.0.1:4177
2. Click **Imagniverse** (top nav) — browse all 20 panels to orient yourself
3. Click **Dreamer** (sidebar) — create your first entry (type: dream, any text, any tags)
4. View the timeline and matrix in the Dreamer dashboard
5. Run `!confidence` from the chat box to get the live feature confidence report

---

## Step 6: Trading Setup (When Ready)

### 6.1 Create Kalshi Demo Account

1. Go to https://demo-api.kalshi.co
2. Sign up (free, no real money)
3. Go to Account Settings → API keys
4. Copy: Key ID and Private Key (PEM format)

### 6.2 Create GitHub OAuth App

1. GitHub → Settings → Developer settings → OAuth Apps → New OAuth App
2. Fill in:
   - Homepage URL: `http://127.0.0.1:8080`
   - Authorization callback URL: `http://127.0.0.1:8080/auth/callback`
3. Copy: Client ID and Client Secret

### 6.3 Configure Trade Chat

Create `C:\tmp\lantern-os\apps\lantern-trade-chat\.env`:

```
KALSHI_API_KEY_ID=your_key_id_here
KALSHI_PRIVATE_KEY=your_pem_key_here
KALSHI_ENVIRONMENT=demo
GITHUB_OAUTH_CLIENT_ID=your_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_client_secret
LANTERN_LIVE_ENABLED=0
LANTERN_SESSION_SECRET=any_32_char_random_string_here
```

Then restart the full stack:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternFullStack.ps1
```

### 6.4 Test Paper Trading

1. Open http://127.0.0.1:8080
2. Login with GitHub
3. Check balance (should show demo account balance)
4. Type a paper order: `buy 1 yes on HIGHNY24-T61 at 40c`
5. Confirm the order preview and submit
6. Check order history — confirms paper execution

---

## Live Trading Gate

**Do not enable live trading without completing all of these:**

- [ ] 10+ paper trades placed and reviewed
- [ ] Order history confirms all expected trades
- [ ] Alex approves removing kill switch
- [ ] Set `LANTERN_LIVE_ENABLED=1` in .env
- [ ] Delete `C:\tmp\lantern-os\data\kalshi\LIVE-KILL-SWITCH`
- [ ] First live order: $1–5 max

The kill switch file (`data/kalshi/LIVE-KILL-SWITCH`) blocks all live orders at the code level even if `LANTERN_LIVE_ENABLED=1`. Both gates must be cleared.

---

## Feature Status Quick Reference

| Feature | Confidence | What Works | What Doesn't |
|---------|-----------|------------|--------------|
| Trading App | 85% | Paper orders, balance, history, safety gates | Live execution (gated), IBKR (not yet built) |
| Dream Journal | 95% | All 8 entry types, search, stats, matrix, tasks | Nothing missing |
| Imagniverse | 90% | All 20 panels, navigation, docs | None |
| Outreach Tracking | N/A | Backend events already logged | Not needed locally |
| Payment System | 40% | Backend API, wallet state, ledger | No UI to view/send invoices, no Stripe keys |

---

## Run !confidence Report

From the dashboard chat box, type `!confidence` and press Send. It runs `Build-LanternConfidenceReport.ps1`, checks all live services, and returns a JSON report with per-feature confidence scores.

To run directly:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\Build-LanternConfidenceReport.ps1 `
  -LanternRoot "C:\tmp\lantern-os" `
  -WriteReceipt
```

Output saved to: `manifests/validation/LANTERN-CONFIDENCE-LATEST.json`

---

## Troubleshooting

**"Port 4177 already in use"**
```powershell
netstat -ano | findstr :4177
taskkill /PID <the PID shown> /F
```

**"Cannot find module 'express'"**
```powershell
cd C:\tmp\lantern-os\apps\lantern-garage
npm install
```

**"GitHub OAuth login redirects but fails"**
- Check the callback URL in your GitHub OAuth App settings matches exactly: `http://127.0.0.1:8080/auth/callback`
- Verify `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` in .env

**"Kalshi balance returns 401"**
- Verify `KALSHI_API_KEY_ID` is correct
- Verify `KALSHI_PRIVATE_KEY` is the full PEM block (include `-----BEGIN/END PRIVATE KEY-----`)
- Ensure `KALSHI_ENVIRONMENT=demo` (not `prod`)

---

## Daily Startup (After First Setup)

Just run:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\tmp\lantern-os\scripts\Start-LanternFullStack.ps1
```

Or create a desktop shortcut with that command.
