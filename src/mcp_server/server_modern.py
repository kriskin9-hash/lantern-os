"""
Lantern OS modern MCP compatibility launcher.

This file keeps the existing Lantern OS FastAPI MCP server intact and adds the
connector contract used by modern ChatGPT/MCP probes:

  GET  /status
  GET  /capabilities
  GET  /tools
  GET  /receipts
  GET  /mcp
  POST /mcp
  GET  /mcp/sse

The legacy transport remains available through /sse and /messages because those
routes are still registered by src/mcp_server/server.py.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

# Import the existing server and reuse its app/tool registry instead of forking
# behavior. This preserves the legacy /sse + /messages path while adding /mcp.
from server import (  # type: ignore
    TOOLS_REGISTRY,
    REPO_ROOT,
    _STARTED_AT,
    _handle_jsonrpc,
    _load_fleet_status,
    app,
)

SERVER_NAME = "lantern-os-mcp"
SERVER_VERSION = "1.1.0-modern-compat"
PROTOCOL_VERSION = "2025-03-26"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonrpc(method: str, params: Dict[str, Any] | None = None, request_id: str = "rest") -> Dict[str, Any]:
    return _handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
    )


def _normalize_jsonrpc_request(body: Any) -> Any:
    """Accept strict MCP JSON-RPC plus common connector aliases.

    Some connector clients send `arguments` or `input` at the top level instead
    of `params`, and some send `tool` instead of `name` inside tools/call. The
    legacy server only accepts strict `params.name`, so normalize here.
    """
    if isinstance(body, list):
        return [_normalize_jsonrpc_request(item) for item in body]
    if not isinstance(body, dict):
        return body

    normalized = dict(body)
    normalized.setdefault("jsonrpc", "2.0")

    if "params" not in normalized:
        if "arguments" in normalized:
            normalized["params"] = normalized["arguments"]
        elif "input" in normalized:
            normalized["params"] = normalized["input"]

    params = normalized.get("params")
    if normalized.get("method") == "tools/call" and isinstance(params, dict):
        if "name" not in params and "tool" in params:
            params = dict(params)
            params["name"] = params["tool"]
            normalized["params"] = params

    return normalized


def _tool_descriptors() -> List[Dict[str, Any]]:
    result = _jsonrpc("tools/list", request_id="tools-list")
    if "error" in result:
        return []
    return list(result.get("result", {}).get("tools", []))


def _receipt_files() -> List[Dict[str, Any]]:
    directories: Iterable[Path] = (
        REPO_ROOT / "manifests" / "validation",
        REPO_ROOT / "reports",
    )
    receipts: List[Dict[str, Any]] = []
    for directory in directories:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("**/*"), key=lambda p: p.stat().st_mtime, reverse=True):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".json", ".md", ".txt"}:
                continue
            try:
                rel = path.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = str(path)
            receipts.append(
                {
                    "path": rel,
                    "size": path.stat().st_size,
                    "modifiedAt": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                }
            )
            if len(receipts) >= 25:
                return receipts
    return receipts


def _status_payload() -> Dict[str, Any]:
    fleet = _load_fleet_status()
    started = datetime.fromisoformat(_STARTED_AT)
    uptime = int((datetime.now(timezone.utc) - started).total_seconds())
    tools = _tool_descriptors()
    return {
        "ok": True,
        "service": SERVER_NAME,
        "version": SERVER_VERSION,
        "protocolVersion": PROTOCOL_VERSION,
        "status": "online",
        "startedAt": _STARTED_AT,
        "uptimeSeconds": uptime,
        "generatedAt": _now(),
        "repoRoot": str(REPO_ROOT),
        "transport": {
            "modern": {
                "mcp": "/mcp",
                "mcpSse": "/mcp/sse",
                "tools": "/tools",
                "capabilities": "/capabilities",
                "status": "/status",
                "receipts": "/receipts",
            },
            "legacy": {
                "sse": "/sse",
                "messages": "/messages",
            },
        },
        "toolsCount": len(tools),
        "fleet": fleet,
        "connectorBoundary": "local-first; remote/tunnel claims require receipts and tool descriptor validation",
    }


def _capabilities_payload() -> Dict[str, Any]:
    tools = _tool_descriptors()
    tool_names = [tool.get("name", "") for tool in tools]
    write_like = [
        name
        for name in tool_names
        if name in {
            "task_intake",
            "dispatch_work",
            "mesh_register_peer",
            "mesh_donate",
            "mesh_prune",
            "update_lantern_os",
        }
    ]
    return {
        "ok": True,
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {
            "tools": True,
            "resources": True,
            "logging": True,
            "restDiscovery": True,
            "jsonRpcPost": True,
            "sseDiscovery": True,
        },
        "routes": {
            "health": "/health",
            "status": "/status",
            "capabilities": "/capabilities",
            "tools": "/tools",
            "mcp": "/mcp",
            "mcpSse": "/mcp/sse",
            "legacySse": "/sse",
            "legacyMessages": "/messages",
        },
        "tools": {
            "count": len(tools),
            "names": tool_names,
            "writeLike": write_like,
        },
        "safety": {
            "readOnlyDiscovery": True,
            "mutatingToolsRequireExplicitToolCall": True,
            "noShellByDefault": True,
            "receiptEndpoint": "/receipts",
            "boundary": "Do not treat live worker counts, tunnels, writes, or private data access as proven without local receipts.",
        },
        "generatedAt": _now(),
    }


async def _modern_sse_event() -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id": None,
        "result": {
            "endpoint": "/mcp",
            "transport": "sse-discovery",
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        },
    }
    yield f"event: endpoint\ndata: {json.dumps(payload)}\n\n"


@app.get("/status")
async def status_endpoint() -> Dict[str, Any]:
    return _status_payload()


@app.get("/capabilities")
async def capabilities_endpoint() -> Dict[str, Any]:
    return _capabilities_payload()


@app.get("/tools")
async def tools_endpoint() -> Dict[str, Any]:
    return {"tools": _tool_descriptors(), "generatedAt": _now()}


@app.get("/receipts")
async def receipts_endpoint() -> Dict[str, Any]:
    receipts = _receipt_files()
    return {
        "ok": True,
        "count": len(receipts),
        "receipts": receipts,
        "generatedAt": _now(),
    }


@app.get("/mcp")
async def mcp_get_endpoint(request: Request):
    accept = request.headers.get("accept", "")
    if "text/event-stream" in accept:
        return StreamingResponse(
            _modern_sse_event(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    return _status_payload()


@app.get("/mcp/sse")
async def mcp_sse_endpoint() -> StreamingResponse:
    return StreamingResponse(
        _modern_sse_event(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/mcp")
async def mcp_post_endpoint(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            status_code=400,
        )

    normalized = _normalize_jsonrpc_request(body)
    if isinstance(normalized, list):
        return JSONResponse([_handle_jsonrpc(item) for item in normalized])
    return JSONResponse(_handle_jsonrpc(normalized))


if __name__ == "__main__":
    import os

    port = int(os.getenv("MCP_SERVER_PORT", "8771"))
    host = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=port, log_level="info")
