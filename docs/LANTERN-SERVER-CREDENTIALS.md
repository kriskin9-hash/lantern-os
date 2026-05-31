# Lantern Server Credentials

Status: operator credentials received 2026-05-31  
Storage: `.env.lantern` (gitignored - never commit)

---

## Active API Keys (Kalshi Dashboard)

| Name | Key ID | Created | Last Used | Purpose |
|------|--------|---------|-----------|---------|
| **lantern-os** | `key_ExBi5a2nwYrZ5Pq2` | May 31, 2026 | Never | **Current production key** |
| Lantern MCP Admin | `key_TARnVoQleMPkFa5y` | May 29, 2026 | Never | MCP admin operations |
| claudekey | `key_yrsCwpHSs1S5Kihc` | Apr 25, 2026 | May 30, 2026 | Claude integration (legacy) |
| securekey | `key_lqvmMZPbkihCCR5q` | Apr 25, 2026 | Never | General secure operations |

**Use this key:** `lantern-os` (key_ExBi5a2nwYrZ5Pq2) - newest, all permissions, designated for Lantern OS v1.0.0

---

## Credential Storage

**File:** `.env.lantern` (create in repo root)

```text
# Lantern Server API Credentials
# Key: lantern-os (May 31, 2026)
# Operator: Alex Place
# Permissions: All

LANTERN_API_KEY_ID=key_ExBi5a2nwYrZ5Pq2
LANTERN_API_SECRET=sk-...qMMA
LANTERN_API_ENVIRONMENT=production
```

---

## Security

- `.env.lantern` is gitignored (never commit)
- **Rotate quarterly** - 4 keys active, monitor usage
- Never share `sk-` prefix secrets in chat/logs
- Revoke legacy keys after migration complete

---

## Usage

Load in scripts:
```powershell
$env:LANTERN_API_KEY_ID = (Get-Content .env.lantern | Select-String "LANTERN_API_KEY_ID=").ToString().Split("=")[1]
```

Or use `dotenv` libraries in Python/Node.

---

*Operator-approved credential storage*
