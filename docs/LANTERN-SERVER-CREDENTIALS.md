# Lantern Server Credentials

Status: operator credentials received 2026-05-31  
Storage: `.env.lantern` (gitignored - never commit)

---

## Credential Storage

**File:** `.env.lantern` (create in repo root)

```text
# Lantern Server API Credentials
# Received: 2026-05-31
# Operator: Alex Place

LANTERN_API_KEY_ID=key_ExBi5a2nwYrZ5Pq2
LANTERN_API_SECRET=sk-...qMMA
LANTERN_API_ENVIRONMENT=production
```

---

## Security

- `.env.lantern` is gitignored (never commit)
- Rotate keys via operator dashboard
- Never share `sk-` prefix secrets in chat/logs
- Expiration: Never (monitor for rotation needs)

---

## Usage

Load in scripts:
```powershell
$env:LANTERN_API_KEY_ID = (Get-Content .env.lantern | Select-String "LANTERN_API_KEY_ID=").ToString().Split("=")[1]
```

Or use `dotenv` libraries in Python/Node.

---

*Operator-approved credential storage*
