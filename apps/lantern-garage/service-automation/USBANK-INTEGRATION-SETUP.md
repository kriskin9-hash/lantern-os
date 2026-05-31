# U.S. Bank API Integration Setup

**Purpose:** Connect bank account to outreach program for transparent operational cost reporting  
**API:** U.S. Bank Data Toolbox - Retail Banking APIs  
**Status:** Configuration required before use  

---

## Simple Answer

This integration enables transparent operational cost reporting by connecting Lantern OS outreach program to U.S. Bank's Data Toolbox API. It retrieves actual transaction data to show infrastructure costs (AWS, OpenAI, API tokens) in real-time on a public dashboard.

---

## What It Actually Does

- **Authenticates** with U.S. Bank using OAuth 2.0 authorization flow
- **Retrieves** account balances and transaction history
- **Filters** transactions for infrastructure-related costs (AWS, OpenAI, API, tokens)
- **Displays** transparent cost data on outreach dashboard
- **Caches** data for 24 hours to reduce API calls

---

## Setup Steps

### 1. Obtain U.S. Bank Developer Credentials

1. Visit [U.S. Bank Developer Portal](https://developer.usbank.com/)
2. Register for a developer account
3. Create a new application in the portal
4. Note your `Client ID` and `Client Secret`
5. Set your redirect URI (e.g., `http://localhost:3000/auth/callback`)

### 2. Configure API Credentials

Edit `service-automation/usbank-config.json`:

```json
{
  "clientId": "YOUR_ACTUAL_CLIENT_ID",
  "clientSecret": "YOUR_ACTUAL_CLIENT_SECRET",
  "redirectUri": "http://localhost:3000/auth/callback",
  "environment": "sandbox",
  "accessToken": null,
  "refreshToken": null,
  "accountId": null
}
```

Replace `YOUR_USBANK_CLIENT_ID` and `YOUR_USBANK_CLIENT_SECRET` with actual credentials from the developer portal.

### 3. Install Dependencies

```bash
cd apps/lantern-garage
npm install express
```

### 4. Start the Cost Transparency Server

```bash
node service-automation/cost-transparency-server.js
```

The server will start on port 3000 by default.

### 5. Connect Bank Account

1. Open `http://localhost:3000/outreach-dashboard` in your browser
2. Click "Connect Bank Account"
3. Complete the OAuth authorization flow in the popup window
4. Verify your account when prompted
5. View your transparent cost data

---

## API Endpoints

Once the server is running, these endpoints are available:

- `GET /api/health` - Health check
- `GET /api/auth/start` - Initiate OAuth authorization
- `GET /api/auth/callback?code=...&state=...` - OAuth callback handler
- `POST /api/auth/verify` - Verify account (requires `accountId` in body)
- `GET /api/auth/test` - Test connection status
- `GET /api/costs/summary?days=30` - Get operational cost summary
- `GET /api/costs/cached` - Get cached cost data
- `GET /api/transactions?days=30` - Get raw transaction data
- `GET /outreach-dashboard` - Cost transparency dashboard UI

---

## Security Considerations

- **Never commit** `usbank-config.json` with real credentials to version control
- **Use environment variables** for production deployments
- **Keep secrets** secure and rotate them regularly
- **Use HTTPS** in production (not HTTP)
- **Implement rate limiting** to prevent API abuse
- **Log security events** for audit trails

---

## Data Filtering Logic

The system automatically identifies infrastructure costs by filtering transactions with descriptions containing:

- `aws` (Amazon Web Services)
- `openai` (OpenAI API)
- `api` (API charges)
- `token` (Token usage fees)

This filtering happens in `usbank-api-client.js` in the `getOperationalCostSummary()` method.

---

## Troubleshooting

### "No access token" error

Complete the OAuth authorization flow by clicking "Connect Bank Account" in the dashboard.

### "Account verification failed"

Ensure you have provided a valid `accountId` after OAuth completion. The account ID is provided by U.S. Bank during the authorization flow.

### "Connection test failed"

Check that your API credentials are correct and that you have completed the OAuth flow successfully.

### API rate limits

U.S. Bank API may have rate limits. The system caches data for 24 hours to reduce API calls.

---

## Production Deployment

For production use:

1. **Use environment variables** instead of config file:
   ```javascript
   const clientId = process.env.USBANK_CLIENT_ID;
   const clientSecret = process.env.USBANK_CLIENT_SECRET;
   ```

2. **Enable HTTPS** for all endpoints

3. **Implement proper session management** for OAuth state

4. **Add rate limiting** middleware

5. **Set up monitoring** for API errors and rate limits

6. **Configure CORS** appropriately for your domain

---

## Validation Path

**Before Public Display:**
- Verify OAuth flow works in sandbox environment
- Test transaction filtering logic with sample data
- Confirm cost dashboard displays accurate figures
- Review security settings for production use

**After Deployment:**
- Monitor API usage and costs
- Verify data accuracy against bank statements
- Update filtering logic as needed
- Rotate credentials periodically

---

## Next Safe Action

1. Obtain U.S. Bank developer credentials
2. Configure `usbank-config.json` with credentials
3. Test OAuth flow in sandbox environment
4. Verify transaction data retrieval
5. Review cost dashboard for accuracy
6. Deploy to production with security hardening

---

## Appendix: File Structure

```
apps/lantern-garage/
├── service-automation/
│   ├── usbank-api-client.js          # Main API client
│   ├── bank-auth-flow.js             # OAuth authentication flow
│   ├── cost-transparency-server.js   # Express server
│   └── usbank-config.json           # API credentials (DO NOT COMMIT)
└── public/
    └── outreach-cost-dashboard.html  # Transparency dashboard UI
```

---

## Operator Boundary

Do not display real financial data publicly without:
- Explicit operator approval
- Verification that data is accurate
- Confirmation that sensitive information is redacted
- Security review of production deployment
