#!/usr/bin/env python3
"""End-to-end OAuth 2.0 + PKCE + MCP test for Lantern OS."""
import json
import urllib.request
import urllib.parse
import hashlib
import base64

BASE = "http://127.0.0.1:8772"

# Step 1: Register client
reg_url = f"{BASE}/oauth/register?client_name=TestGPT&redirect_uri=https://oauth.pstmn.io/v1/callback"
reg = json.loads(urllib.request.urlopen(reg_url).read())
print("[1] Registered client:", reg["client_id"])

# Step 2: Generate PKCE verifier and challenge
verifier = "test_verifier_abc123"
challenge = base64.urlsafe_b64encode(
    hashlib.sha256(verifier.encode()).digest()
).rstrip(b"=").decode()

# Step 3: Get authorization code (follow redirect)
auth_url = (
    f"{BASE}/oauth/authorize?"
    f"response_type=code&"
    f"client_id={reg['client_id']}&"
    f"redirect_uri=https://oauth.pstmn.io/v1/callback&"
    f"scope=mcp&"
    f"state=test&"
    f"code_challenge={challenge}&"
    f"code_challenge_method=S256"
)
resp = urllib.request.urlopen(auth_url)
redirect = resp.geturl()
print("[2] Redirect URL:", redirect)
code = urllib.parse.parse_qs(urllib.parse.urlparse(redirect).query)["code"][0]
print("[3] Auth code:", code[:20] + "...")

# Step 4: Exchange code for token
token_data = urllib.parse.urlencode({
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": "https://oauth.pstmn.io/v1/callback",
    "client_id": reg["client_id"],
    "code_verifier": verifier,
}).encode()
token = json.loads(urllib.request.urlopen(
    urllib.request.Request(f"{BASE}/oauth/token", data=token_data)
).read())
print("[4] Access token:", token["access_token"][:20] + "...")
print("    Token type:", token["token_type"])
print("    Expires in:", token["expires_in"])

# Step 5: Call protected /messages endpoint
req = urllib.request.Request(
    f"{BASE}/messages",
    data=json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1,
        "params": {},
    }).encode(),
    headers={
        "Authorization": f"Bearer {token['access_token']}",
        "Content-Type": "application/json",
    },
)
result = json.loads(urllib.request.urlopen(req).read())
tools = [t["name"] for t in result["result"]["tools"]]
print("[5] Available tools:", tools)

# Step 6: Call a tool
req2 = urllib.request.Request(
    f"{BASE}/messages",
    data=json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 2,
        "params": {
            "name": "get_status",
            "arguments": {},
        },
    }).encode(),
    headers={
        "Authorization": f"Bearer {token['access_token']}",
        "Content-Type": "application/json",
    },
)
result2 = json.loads(urllib.request.urlopen(req2).read())
status = json.loads(result2["result"]["content"][0]["text"])
print("[6] System status:", status["status"], "slots:", status["slots_online"])

print("\n=== ALL TESTS PASSED ===")
