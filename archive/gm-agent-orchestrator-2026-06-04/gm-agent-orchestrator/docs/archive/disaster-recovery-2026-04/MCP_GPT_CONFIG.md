# GPT Instance MCP Connector Configuration

Archived from root during cleanup. The original contained a concrete bearer token, which is redacted here. Rotate any token that appeared in the previous root document.

**Status:** Historical configuration note  
**Token Generated:** Yes  
**Token Value:** `redacted-in-archive`  
**MCP Server:** Running on port 8787 or 8788 depending on local configuration

---

## Quick Setup for GPT Instance

Use a current token from the local `ORCH_MCP_TOKEN` environment variable. Do not store live bearer tokens in repository docs.

---

## MCP Server Configuration

- **Host:** 127.0.0.1 (localhost)
- **Endpoint:** `http://127.0.0.1:<port>/mcp`
- **Method:** POST
- **Content-Type:** application/json

---

## GPT Connector Shape

```json
{
  "endpoint": "http://127.0.0.1:<port>/mcp",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer <redacted-local-token>",
    "Content-Type": "application/json"
  }
}
```

---

## Token Security

- Store live tokens in the local environment, not version control.
- Rotate tokens that have appeared in repository history or logs.
- Prefer current operator runbooks over this archived note.

---

## Historical Value Preserved

This note preserves the connector setup shape and the lesson that GPT must send a bearer token to reach the local MCP server.
