# Crash Cart MVP Setup Guide

Complete end-to-end setup for the Crash Cart emergency fallback dashboard.

## Architecture

```
operator.html (port 8765)
    ↓ (POST /api/crash-cart)
Dashboard Server (port 8765)
    ↓ (POST /api/chat)
GPT Web API (port 3000)
    ↓ (Playwright automation)
ChatGPT.com
    ↓ (response)
Operator sees response on dashboard
```

## Components

### 1. GPT Web API Server (Task A - BLOCKER)
**Status:** ✅ Created
**Location:** `tools/gpt-web-api/`
**Port:** localhost:3000

Lightweight Node.js + Playwright service that:
- Accepts POST requests to `/api/chat`
- Automates ChatGPT.com browser interaction
- Returns actual text responses (not screenshots)
- Saves session for reuse

### 2. Dashboard Server (Task C - Already Running)
**Status:** ✅ Running on port 8765
**Location:** `scripts/Start-Dashboard.ps1`
**Endpoints:**
- `GET /dashboard/operator.html` - Crash Cart UI
- `POST /api/crash-cart` - Message endpoint (now forwards to GPT Web API)

### 3. Operator Dashboard (Task B - Already Exists)
**Status:** ✅ Running at http://localhost:8765/dashboard/operator.html
**Location:** `dashboard/operator.html`

Features:
- Text input for messages
- SEND button
- Response display area
- Loading state
- Error handling

## Integrated Setup (Recommended)

All services (GPT Web API, Dashboard, MCP) are configured in `config/local-services.json` and can be started together.

### One-Command Startup

```powershell
# Start service supervisor (runs all configured services)
.\scripts\Start-OrchestratorServices.ps1
```

This starts:
1. **gpt-web-api** on port 3000 (Playwright → ChatGPT automation)
2. **dashboard** on port 8765 (Crash Cart UI + API routing)
3. **mcp** on port 8787 (orchestrator backend)
4. **ngrok** tunnel (for remote access)

**Important:** When GPT Web API starts, a browser window will open. Complete ChatGPT login within 5 minutes.

### Manual Setup (Alternative)

If you need to start services individually:

```powershell
# Terminal 1 - GPT Web API
.\scripts\Start-GptWebApiServer.ps1 -Wait

# Terminal 2 - Dashboard
.\scripts\Start-Dashboard.ps1
```

### Step 4: Test the Complete Flow

#### Option A: Manual Browser Test
1. Open http://localhost:8765/dashboard/operator.html
2. Type a message in the textarea
3. Click SEND button
4. Watch response appear in the response div

#### Option B: API Test via PowerShell
```powershell
# Test GPT Web API directly
$msg = @{ message = "What is 2+2?" } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:3000/api/chat" `
  -Method POST -Body $msg -ContentType "application/json"

# Test through Dashboard
$msg = @{ message = "What is 2+2?" } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8765/api/crash-cart" `
  -Method POST -Body $msg -ContentType "application/json"
```

#### Option C: Curl Test
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is 2+2?"}'
```

## Success Criteria

### API Level (Task C)
- [ ] `curl http://localhost:3000/api/chat` returns {"response": "..."}
- [ ] Response contains actual ChatGPT text (not screenshot paths)
- [ ] Error handling returns appropriate JSON responses

### Dashboard Level (Task D + E)
- [ ] http://localhost:8765/dashboard/operator.html loads
- [ ] Message input accepts text
- [ ] SEND button triggers API call
- [ ] Response appears in response div
- [ ] Loading state shows while waiting
- [ ] Error messages display on failure

## Troubleshooting

### "Cannot connect to localhost:3000"
- GPT Web API server is not running
- Run: `.\scripts\Start-GptWebApiServer.ps1 -Wait`

### "Chat interface not found"
- ChatGPT.com page layout may have changed
- Update input selector in `tools/gpt-web-api/server.js` line 104
- Or report issue with screenshot from browser window

### "No response received after 30 seconds"
- ChatGPT may be slow
- Check browser window if running headful (`HEADLESS=false`)
- Try again after waiting

### "Timeout waiting for authentication"
- You didn't log in within 5 minutes
- Stop server (Ctrl+C)
- Delete `.sessions/chatgpt-session.json` to reset
- Start server again and complete login promptly

### Dashboard shows "GPT Web API unavailable"
- Dashboard server is trying to reach port 3000 but GPT Web API isn't listening
- Make sure both servers are running

## Files Created

| File | Purpose |
|------|---------|
| `tools/gpt-web-api/server.js` | Main API server |
| `tools/gpt-web-api/package.json` | Node dependencies |
| `tools/gpt-web-api/README.md` | API documentation |
| `scripts/Start-GptWebApiServer.ps1` | Server launcher |
| `dashboard/operator.html` | Emergency UI |
| `scripts/Start-Dashboard.ps1` | Dashboard server (updated) |

## Running Services

For a complete MVP:

**Terminal 1 - GPT Web API:**
```powershell
cd C:\Users\alexp\Documents\gm-agent-orchestrator
.\scripts\Start-GptWebApiServer.ps1 -Wait
```

**Terminal 2 - Dashboard Server:**
```powershell
cd C:\Users\alexp\Documents\gm-agent-orchestrator
.\scripts\Start-Dashboard.ps1
```

**Browser:**
```
http://localhost:8765/dashboard/operator.html
```

## Next Steps

1. Ensure both servers are running
2. Open dashboard in browser
3. Enter a message
4. Click SEND
5. Verify response appears with actual ChatGPT text
6. Document results as evidence

## Notes

- GPT Web API saves session in `tools/gpt-web-api/.sessions/chatgpt-session.json`
- First request takes ~3-5 seconds (browser startup)
- Subsequent requests are faster (reuse browser instance)
- Session persists across server restarts
- To force re-login, delete `.sessions/` directory
