# GPT Web API Server

Lightweight Playwright-based ChatGPT API server for Crash Cart emergency fallback.

## Setup

```bash
cd tools/gpt-web-api
npm install
```

## Start Server

### From PowerShell
```powershell
.\scripts\Start-GptWebApiServer.ps1 -Wait
```

Or without blocking:
```powershell
.\scripts\Start-GptWebApiServer.ps1
```

### From Node.js directly
```bash
npm start                    # Headless mode (no visible browser)
HEADLESS=false npm start     # Visible browser
```

## API Endpoints

### POST /api/chat
Send message to ChatGPT and get response.

**Request:**
```json
{
  "message": "What is the capital of France?"
}
```

**Response:**
```json
{
  "response": "The capital of France is Paris...",
  "timestamp": "2026-05-02T23:30:45.123Z"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "browser": "running",
  "port": 3000
}
```

## Authentication

On first run, the server will:
1. Launch a Chromium browser
2. Navigate to https://chat.openai.com
3. Detect if authentication is needed
4. Wait up to 5 minutes for manual login
5. Save session for future requests

Subsequent requests use the saved session and don't require additional login.

## Testing

```bash
# Test from command line
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is 2+2?"}'

# Or using PowerShell
$body = @{ message = "What is 2+2?" } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:3000/api/chat" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

## Environment Variables

- `PORT` - Server port (default: 3000)
- `HEADLESS` - Run browser in headless mode (default: true)

## Crash Cart Integration

The Crash Cart dashboard (`/dashboard/operator.html`) sends messages to `/api/crash-cart` on the Dashboard server (port 8765), which forwards them to this GPT Web API service.

Full flow:
1. Operator enters message in `operator.html`
2. Clicks SEND button
3. Dashboard server (`localhost:8765`) receives request at `/api/crash-cart`
4. Dashboard server forwards to GPT Web API (`localhost:3000/api/chat`)
5. GPT Web API responds with actual ChatGPT response text
6. Dashboard displays response to operator

## Troubleshooting

### "ChatGPT-web API unavailable"
Start the server first:
```powershell
.\scripts\Start-GptWebApiServer.ps1 -Wait
```

### "Chat interface not found"
- ChatGPT.com may have changed the DOM structure
- Check browser window (if running headful) for issues
- May need to update input selector in server.js

### "No response received after 30 seconds"
- ChatGPT may be slow or overloaded
- Try again after waiting
- May need to increase timeout in server.js

### Browser won't authenticate
- Make sure you complete ChatGPT login within 5 minutes
- Check if ChatGPT requires additional verification (email, etc.)
- Session is saved in `.sessions/chatgpt-session.json` - delete to force re-login

## Notes

- First request takes longer (browser startup + authentication)
- Subsequent requests are faster (reuses browser instance)
- Server keeps browser open for connection pooling
- Sessions are saved locally in `.sessions/`
- Headless mode (default) runs faster but no visual feedback
- Set `HEADLESS=false` to see browser interaction for debugging
