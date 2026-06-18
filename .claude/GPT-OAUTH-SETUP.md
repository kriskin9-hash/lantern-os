# Connect Lantern OS MCP to ChatGPT (Custom GPT) via OAuth 2.0

## Prerequisites

1. Lantern OS OAuth MCP server running:
   ```bash
   python src/mcp_server/server_oauth.py
   # → http://127.0.0.1:8772
   ```

2. The server must be reachable from the internet OR you use a tunnel (ngrok, Cloudflare Tunnel, etc.)

## Step 1: Get a Client ID

Open your browser or use curl:
```bash
curl "http://127.0.0.1:8772/oauth/register?client_name=MyGPT&redirect_uri=https://oauth.pstmn.io/v1/callback"
```

Save the `client_id`. The `client_secret` is not needed for public clients.

## Step 2: Configure the Custom GPT

1. Go to ChatGPT → Explore GPTs → Create
2. Click **Configure** tab
3. Under **Actions**, click **Add action**
4. Choose **Import from URL** or paste the OpenAPI schema
5. Set the schema URL to:
   ```
   http://YOUR_HOST:8772/.well-known/mcp
   ```
   Or paste the full schema from `.claude/gpt-oauth-mcp-schema.yaml`

## Step 3: Set Authentication

1. In the GPT Configure panel, click **Authentication**
2. Select **OAuth**
3. Fill in:
   - **Client ID**: (from Step 1)
   - **Client Secret**: (leave blank for public client)
   - **Authorization URL**: `http://YOUR_HOST:8772/oauth/authorize`
   - **Token URL**: `http://YOUR_HOST:8772/oauth/token`
   - **Scope**: `mcp`
   - **Token Exchange Method**: `Default (POST request)`

4. Click **Save**

## Step 4: Test

In the GPT chat, say:
```
What tools do you have access to?
```

GPT should call `tools/list` and show:
- `queue_status`
- `task_intake`
- `dispatch_work`
- `boot_check`
- `list_skills`
- `get_status`
- `render_report_pdf`

## Step 5: Try a Tool

```
Check the Lantern system status
```

GPT will call `get_status` and return:
```json
{
  "status": "healthy",
  "slots_online": 3,
  "queue_depth": 0,
  "version": "1.0.0"
}
```

## Troubleshooting

### "Cannot reach server"
- The GPT server can't reach `localhost`. Use ngrok:
  ```bash
  ngrok http 8772
  ```
  Then use the ngrok HTTPS URL everywhere.

### "Invalid client_id"
- The client was registered on a different host. Re-register with the public URL:
  ```bash
  curl "https://YOUR_NGROK.ngrok.io/oauth/register?client_name=MyGPT&redirect_uri=https://oauth.pstmn.io/v1/callback"
  ```

### "Token expired"
- Default token TTL is 60 minutes. GPT should auto-refresh. If not, re-authenticate.

## Security Checklist

- [ ] `MCP_OAUTH_JWT_SECRET` is set to a strong random value
- [ ] Server is behind HTTPS in production (ngrok or reverse proxy)
- [ ] Auto-registration is disabled for production (remove the auto-register block in `server_oauth.py` line ~470)
- [ ] Token TTL is appropriate for your use case
