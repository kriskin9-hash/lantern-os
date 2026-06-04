# MCP Connector Diagnostic Report

Archived from root during cleanup. This note preserves the authentication/root-cause lesson without storing any live bearer token.

**Historical issue:** GPT instance could reach the local MCP endpoint but could not authenticate.

---

## Preserved findings

- MCP server was listening on localhost.
- Unauthenticated requests returned `401 Unauthorized`.
- The connector needed an `Authorization: Bearer <token>` header.
- `ORCH_MCP_TOKEN` should be stored in the local environment, not in repository docs.
- `-NoAuth` was documented as an immediate workaround but is less secure and should not be the default.

---

## Safe connector shape

```text
Endpoint: http://127.0.0.1:<port>/mcp
Method: POST
Authorization: Bearer <redacted-local-token>
```

---

## Security note

Rotate any token that appeared in root-level MCP configuration notes, chat logs, screenshots, or repository history. Prefer current operator runbooks over this archived diagnostic.
