"""
MCP stdio-to-SSE bridge for Windsurf / Cascade IDE integration.

This script runs the Lantern OS MCP HTTP server in a background thread,
then bridges stdio JSON-RPC messages to the SSE endpoint.

Usage:
    python scripts/mcp_stdio_bridge.py
"""

import sys
import json
import time
import threading
import urllib.request
import urllib.error
import subprocess
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load local env overrides if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(REPO_ROOT, ".env.local"))
except Exception:
    pass

MCP_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8771")


def _ensure_server():
    """Start the Lantern OS MCP server if not already running."""
    try:
        req = urllib.request.Request(f"{MCP_URL}/health", method="GET")
        urllib.request.urlopen(req, timeout=2)
        return
    except urllib.error.URLError:
        pass

    # Start server in background
    proc = subprocess.Popen(
        [sys.executable, os.path.join(REPO_ROOT, "src", "mcp_server", "server.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=REPO_ROOT,
    )
    # Wait for it to come up
    for _ in range(30):
        try:
            req = urllib.request.Request(f"{MCP_URL}/health", method="GET")
            urllib.request.urlopen(req, timeout=1)
            return
        except urllib.error.URLError:
            time.sleep(0.5)
    print(f"[mcp-bridge] Warning: server did not start on {MCP_URL}", file=sys.stderr)


def _send_rpc(method: str, params: dict = None) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(f"{MCP_URL}/messages", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())
    except Exception as e:
        return {"jsonrpc": "2.0", "id": 1, "error": {"code": -32603, "message": str(e)}}


def main():
    _ensure_server()

    # Send initialize response
    init_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "lantern-os-mcp", "version": "1.0.0"},
        },
    }
    print(json.dumps(init_response), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            method = msg.get("method", "")
            params = msg.get("params", {})

            if method == "tools/list":
                result = _send_rpc("tools/list", params)
            elif method.startswith("tools/call"):
                result = _send_rpc("tools/call", params)
            else:
                result = _send_rpc(method, params)

            print(json.dumps(result), flush=True)
        except Exception as e:
            error = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32603, "message": str(e)}}
            print(json.dumps(error), flush=True)


if __name__ == "__main__":
    main()
