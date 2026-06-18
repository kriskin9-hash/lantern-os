# Patreon OAuth 2.0 Integration

Lantern OS includes a built-in Patreon OAuth login system that gates the entire site and maps Patreon tiers to role-based access levels.

## Features

- **OAuth 2.0 with PKCE** — Secure authentication without storing passwords
- **Session Management** — Server-side session cookies with 7-day TTL
- **Role-Based Access Control** — Four access tiers: guest, supporter, founder, admin
- **Profile Page** — User can view their Patreon info and logout from `/profile.html`
- **Auto-Redirect** — Unauthenticated users redirected to `/auth.html`
- **No Vendor Lock-in** — Pure Node.js implementation, no external auth services

## Setup

### 1. Create a Patreon OAuth App

1. Go to https://www.patreon.com/portal/registration/register-oauth-application
2. Fill in the OAuth app form:
   - **App Name:** Lantern OS (or your custom name)
   - **Redirect URI:** `http://127.0.0.1:4177/api/auth/patreon/callback` (dev) or `https://your-domain.com/api/auth/patreon/callback` (production)
3. Accept terms and submit
4. Copy your **Client ID** and **Client Secret** — keep the secret safe!

### 2. Get Your Campaign ID

Your Campaign ID is in the URL of your Patreon campaign:
- URL: `https://www.patreon.com/c/{campaign_id}`
- Example: If your URL is `https://www.patreon.com/c/16143763`, your Campaign ID is `16143763`

### 3. Configure `.env`

Add these variables to your `.env` file:

```bash
# Patreon OAuth credentials
PATREON_CLIENT_ID=your_client_id_here
PATREON_CLIENT_SECRET=your_client_secret_here
PATREON_REDIRECT_URI=http://127.0.0.1:4177/api/auth/patreon/callback
PATREON_CAMPAIGN_ID=your_campaign_id_here

# Session secret (can be any random string)
SESSION_SECRET=your_session_secret_here
```

For production, set:
- `PATREON_REDIRECT_URI=https://your-domain.com/api/auth/patreon/callback`
- `NODE_ENV=production` (enables secure cookies over HTTPS)

### 4. Restart the Server

```bash
npm run dev --prefix apps/lantern-garage
```

The server will now:
- Redirect unauthenticated users to `/auth.html` (Patreon login page)
- Gate all pages behind OAuth
- Store sessions in memory (default) or connect a database for persistence

## Role Mapping

Patreon tiers are mapped to Lantern roles automatically based on tier IDs. The mapping is defined in `apps/lantern-garage/lib/patreon-auth.js`:

| Tier Name | Tier ID | Lantern Role | Access |
|-----------|---------|--------------|--------|
| Free | (not a member) | `guest` | Public pages only |
| Wanderer | 28764312 | `supporter` | Chat + features |
| Deep Dreamer | 28740619 | `founder` | All features |
| Synthesasia Guild | 28764307 | `admin` | Admin tools |

To customize tier mapping:
1. Edit `TIER_TO_ROLE` in `apps/lantern-garage/lib/patreon-auth.js`
2. Get tier IDs from your Patreon campaign settings → Tier management
3. Restart the server

## API Endpoints

All OAuth-related endpoints are in `apps/lantern-garage/routes/auth.js`:

### `GET /api/auth/session`
Returns current session info.

**Response (authenticated):**
```json
{
  "authenticated": true,
  "role": "supporter",
  "user": {
    "id": "12345",
    "name": "John Doe",
    "email": "john@example.com",
    "tier": "28764312"
  }
}
```

**Response (not authenticated):**
```json
{
  "authenticated": false,
  "role": "guest"
}
```

### `GET /api/auth/patreon/start`
Initiates OAuth flow. Query parameter: `returnTo` (optional, defaults to `/`).

**Redirects to:** Patreon OAuth consent screen

### `GET /api/auth/patreon/callback`
OAuth callback endpoint. Patreon redirects here with `code` and `state` parameters.

**Redirects to:** Original page or `/dream-chat.html`

### `POST /api/auth/logout`
Clears session and logs out user.

**Response:**
```json
{ "ok": true }
```

## Files

| File | Purpose |
|------|---------|
| `apps/lantern-garage/lib/patreon-auth.js` | Core OAuth logic: token exchange, user fetch, role mapping |
| `apps/lantern-garage/routes/auth.js` | Express-like route handlers for OAuth endpoints |
| `apps/lantern-garage/public/auth.html` | Patreon login page with tier cards |
| `apps/lantern-garage/public/profile.html` | User profile page with logout button |
| `apps/lantern-garage/public/js/auth-gate.js` | Client-side auth enforcement script |

## Troubleshooting

### "User fetch failed: Bad Request"
The Patreon API rejected the identity endpoint. Check:
1. Token is valid (token exchange succeeded but user fetch failed)
2. Scope is correct: `identity identity.memberships`
3. Bearer token is properly formatted in Authorization header

### Session not persisting
Sessions use in-memory storage by default. Restart clears all sessions. For production:
1. Connect a database store (e.g., `connect-mongo` or `connect-pg-simple`)
2. Add to `server.js`:
   ```javascript
   const store = require('connect-mongo')(session);
   const sessionMiddleware = session({
     store: new store({ url: 'mongodb://...' }),
     // ... rest of config
   });
   ```

### Cookies not being set
Check:
1. `httpOnly: true` is set (cookies are not accessible to JavaScript)
2. Domain/path match correctly (local dev uses `127.0.0.1:4177`)
3. Browser allows third-party cookies for local development

### OAuth redirect loop
Check `PATREON_REDIRECT_URI` matches:
1. The exact URL in your OAuth app settings (case-sensitive)
2. The URL in `handlePatreonStart()` callback

## Development vs. Production

| Setting | Dev | Prod |
|---------|-----|------|
| `PATREON_REDIRECT_URI` | `http://127.0.0.1:4177/api/auth/patreon/callback` | `https://your-domain.com/api/auth/patreon/callback` |
| `NODE_ENV` | (not set) | `production` |
| Cookies: `secure` | `false` | `true` (HTTPS only) |
| Session Store | Memory (cleared on restart) | Persistent database |
| Session Secret | Can be any string | Use `openssl rand -hex 32` |

## Security Considerations

1. **Client Secret** — Never expose to the browser. Keep in `.env` only.
2. **PKCE** — OAuth flow uses PKCE (Proof Key for Code Exchange) for additional security.
3. **HTTPS** — Set `secure: true` in cookie config when deploying to production.
4. **Same-Site** — Cookies use `sameSite: 'lax'` to prevent CSRF attacks.
5. **HTTP-Only** — Session cookies are `httpOnly` and cannot be accessed by JavaScript.

## Testing

### Test OAuth Flow in Browser
1. Open `http://127.0.0.1:4177`
2. Click "Continue with Patreon" button
3. Approve OAuth scope on Patreon
4. Check `/profile.html` to see your user info and role
5. Test logout button

### Test Session Persistence
```bash
# After logging in, in browser console:
fetch('/api/auth/session', { credentials: 'include' })
  .then(r => r.json())
  .then(console.log)
```

Should return your user info and role.

## Support

For issues or questions:
1. Check the server logs for `[AUTH]` debug messages
2. Review `.env` configuration (especially tier IDs)
3. Verify Patreon app settings match your redirect URI
4. Open an issue on GitHub with full error logs
