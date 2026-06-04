# Crash Cart MVP - End-to-End Test Procedure

**Objective:** Verify complete end-to-end functionality from operator.html dashboard through to ChatGPT response.

**Evidence Required:** Observable proof that message → GPT response appears on dashboard.

## Pre-Test Verification

✅ **Code Files Created:**
- `tools/gpt-web-api/server.js` (Playwright automation server)
- `tools/gpt-web-api/package.json` (Node.js dependencies)
- `scripts/Start-GptWebApiServer.ps1` (Service launcher)
- `dashboard/operator.html` (Emergency UI)
- `scripts/Start-Dashboard.ps1` (Updated with GPT Web API forwarding)

✅ **Configuration:**
- `config/local-services.json` (Service registry with gpt-web-api)
- All services configured for auto-start

✅ **Dependencies:**
- Node.js v24.15.0 - installed ✅
- Playwright - installed ✅
- Express.js - installed ✅

## Test Execution (On Your Desktop)

### Phase 1: Service Startup

**Step 1.1 - Start All Services**

Open PowerShell and run:
```powershell
cd C:\Users\alexp\Documents\gm-agent-orchestrator
.\scripts\Start-OrchestratorServices.ps1
```

Expected output:
```
Service gpt-web-api is offline. Starting...
Service dashboard is online. ...
Service mcp is online. ...
```

**Step 1.2 - Verify GPT Web API Browser Appears**

Within 10 seconds:
- [ ] Browser window opens (Chromium)
- [ ] Page loads https://chat.openai.com
- [ ] You see ChatGPT login screen (or you're already logged in)

**Step 1.3 - Complete Authentication (if needed)**

If you see login screen:
- [ ] Enter your ChatGPT credentials
- [ ] Complete any 2FA prompts
- [ ] Wait for main chat interface to load
- [ ] **Must complete within 5 minutes**

If you see chat interface:
- [ ] Close the browser window or minimize it
- [ ] GPT Web API server continues running in background

**Observable Evidence:** Screenshot of browser showing ChatGPT interface ready.

### Phase 2: Dashboard Testing

**Step 2.1 - Open Dashboard**

In a new browser tab (Chrome, Edge, Firefox, etc.):
```
http://localhost:8765/dashboard/operator.html
```

Expected: Red-themed emergency dashboard with:
- [ ] Title "⚠️ Crash Cart"
- [ ] Status: "Emergency Dashboard | All Lanes Blocked"
- [ ] Message input textarea
- [ ] SEND button
- [ ] Response display area

**Observable Evidence:** Screenshot of http://localhost:8765/dashboard/operator.html

**Step 2.2 - Send First Message**

1. Click in the message textarea
2. Type a test message:
   ```
   What is the capital of France?
   ```
3. Click SEND button
4. Watch the response div

Expected behavior:
- [ ] Message appears in textarea
- [ ] SEND button is clickable
- [ ] Response div shows "Sending..."
- [ ] After 3-5 seconds, response text appears

Example response:
```
The capital of France is Paris. It is the largest city in France 
and is known for its art, culture, cuisine, and architecture...
```

**Observable Evidence:** 
- Screenshot showing message input: "What is the capital of France?"
- Screenshot showing response: "The capital of France is Paris..."

**Step 2.3 - Send Second Message (Different Topic)**

Test another message to prove it's not cached:

1. Type:
   ```
   What is 2 + 2?
   ```
2. Click SEND
3. Verify response appears

Expected: Response shows "2 + 2 equals 4" or similar.

**Observable Evidence:** Screenshot of second message and response.

**Step 2.4 - Test Error Handling**

1. Type an empty message (just spaces)
2. Click SEND

Expected: Error message appears in response div saying message cannot be empty.

**Observable Evidence:** Screenshot showing error message.

### Phase 3: API-Level Testing

**Step 3.1 - Test GPT Web API Directly**

Open PowerShell and run:
```powershell
$msg = @{ message = "Hello, what is your name?" } | ConvertTo-Json
$response = Invoke-WebRequest -Uri "http://localhost:3000/api/chat" `
  -Method POST -Body $msg -ContentType "application/json"
$response.Content | ConvertFrom-Json | Format-List
```

Expected output:
```
response   : I'm Claude, an AI assistant made by Anthropic...
timestamp : 2026-05-02T23:30:45.123Z
```

**Observable Evidence:** PowerShell console output showing actual text response.

**Step 3.2 - Test Dashboard Forwarding**

Open PowerShell and run:
```powershell
$msg = @{ message = "Why is the sky blue?" } | ConvertTo-Json
$response = Invoke-WebRequest -Uri "http://localhost:8765/api/crash-cart" `
  -Method POST -Body $msg -ContentType "application/json"
$response.Content
```

Expected: JSON response with actual text.

**Observable Evidence:** PowerShell output showing response text.

**Step 3.3 - Check Service Health**

```powershell
# GPT Web API health
Invoke-WebRequest -Uri "http://localhost:3000/health" | Select-Object -ExpandProperty Content

# Dashboard health
Invoke-WebRequest -Uri "http://localhost:8765/api/status" | Select-Object -ExpandProperty Content | ConvertFrom-Json | Format-List
```

Expected: Both return status: "ok" or similar.

**Observable Evidence:** PowerShell output showing health checks pass.

## Success Criteria

All of the following must be TRUE:

- [ ] **Browser Auto-Started:** GPT Web API launched browser automatically
- [ ] **Authentication:** ChatGPT login completed (or already logged in)
- [ ] **Dashboard Loads:** http://localhost:8765/dashboard/operator.html displays correctly
- [ ] **Message Send:** SEND button works, loading state appears
- [ ] **Real Response:** Actual ChatGPT text appears (not screenshot paths, not errors)
- [ ] **Multiple Messages:** Tested with 2+ different messages, got different responses
- [ ] **Error Handling:** Empty message shows error message
- [ ] **API Endpoints:** Both /api/chat and /api/crash-cart return valid JSON
- [ ] **Service Health:** Health checks pass for gpt-web-api and dashboard

## What This Proves

✅ **End-to-End System Working:**
- Operator input → receives ChatGPT response on screen
- Uses real Playwright automation (not fragile pyautogui)
- Actual text returned (not screenshot paths)
- Session persists across requests
- Services auto-start via supervisor

✅ **Emergency Fallback Ready:**
- When all CLI agents (claude, codex, gemini) are blocked
- Operator can still get GPT responses via web interface
- Complete bypass of agent infrastructure

✅ **Observable Evidence Collected:**
- Screenshots of each step
- API response payloads
- Console output showing execution
- Health check confirmations

## Documentation for Future Use

Once tested successfully:
1. Services auto-start via `Start-OrchestratorServices.ps1`
2. Dashboard always available at http://localhost:8765/dashboard
3. Login required only on first run (session saved after)
4. Session file: `tools/gpt-web-api/.sessions/chatgpt-session.json`
5. To force re-login: delete session file and restart services

## Troubleshooting During Test

### "Cannot connect to http://localhost:3000"
- GPT Web API server didn't start
- Check PowerShell window for error messages
- Make sure Node.js and npm are installed globally

### "Chat interface not found"
- ChatGPT.com page structure changed
- Check browser window for what's actually displayed
- Update DOM selectors in `tools/gpt-web-api/server.js` if needed

### "Timeout waiting for authentication"
- You didn't log in within 5 minutes
- Restart services and log in faster
- Or pre-save session manually by running server.js directly

### "No response received"
- ChatGPT is slow or overloaded
- Wait 30+ seconds before assuming failure
- Check browser window to see if it's generating a response

### Dashboard shows "503 - GPT Web API unavailable"
- GPT Web API service isn't running
- Check that `gpt-web-api` service started
- Try starting it manually: `.\scripts\Start-GptWebApiServer.ps1 -Wait`

## Final Evidence Format

When reporting results, include:

1. **Screenshots:**
   - Dashboard with message sent
   - Dashboard showing response
   - Browser showing ChatGPT interface

2. **API Response:**
   ```json
   {
     "response": "Actual ChatGPT response text here...",
     "timestamp": "2026-05-02T..."
   }
   ```

3. **Console Output:**
   - Service supervisor startup
   - PowerShell API test responses
   - Health check confirmations

4. **Summary:**
   - Total messages sent: N
   - Success rate: N/N (100%)
   - Response time: X seconds (average)
   - Session persisted: Yes/No

---

**This test proves the Crash Cart MVP is production-ready for emergency fallback when all other agent lanes are blocked.**
