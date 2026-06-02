"""
Lantern OS MCP Server
FastAPI + SSE transport for Model Context Protocol.

Endpoints:
  GET /sse        — SSE connection for MCP clients
  POST /messages  — Message endpoint for client→server RPC
  GET /health     — Health check

Tools exposed:
  queue_status    — View work queue depth and tasks
  task_intake     — Submit a task to the queue
  dispatch_work   — Dispatch to an orchestrator agent
  boot_check      — Check orchestrator boot status
  list_skills     — List available skills
  get_status      — Overall system status
"""

import os
import sys
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

# FastAPI + SSE
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import StreamingResponse, JSONResponse
    from starlette.background import BackgroundTask
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError as e:
    FASTAPI_AVAILABLE = False
    print(f"[FATAL] fastapi/uvicorn not installed: {e}")
    sys.exit(1)

# Optional: OpenAI Agents SDK for native MCP server support
try:
    from agents.mcp.server import MCPServer as AgentsMCPServer
    from agents.mcp.server import MCPServerSse as AgentsMCPServerSse
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False

app = FastAPI(title="Lantern OS MCP Server", version="1.0.0")

# ── In-memory state (replace with Redis/DB in production) ──
_task_queue: List[Dict[str, Any]] = []
_skills_db: Dict[str, Dict[str, Any]] = {
    "dream_journal": {"enabled": True, "version": "1.0.0"},
    "archive_curator": {"enabled": True, "version": "1.0.0"},
    "voice_curator": {"enabled": True, "version": "1.0.0"},
    "kalshi_bridge": {"enabled": False, "version": "0.1.0"},
}
_boot_status = {
    "status": "online",
    "slots_online": 3,
    "started_at": datetime.now(timezone.utc).isoformat(),
    "version": "1.0.0",
}
_mcp_sessions: Dict[str, asyncio.Queue] = {}

# ── SSE / MCP Protocol Helpers ──

async def _event_stream(session_id: str):
    """Yield SSE events for a given MCP session."""
    queue = asyncio.Queue()
    _mcp_sessions[session_id] = queue
    try:
        # Send endpoint event
        endpoint_url = os.getenv("MCP_MESSAGES_ENDPOINT", "/messages")
        yield f"event: endpoint\ndata: {endpoint_url}?session_id={session_id}\n\n"

        while True:
            msg = await queue.get()
            if msg is None:  # shutdown signal
                break
            data = json.dumps(msg)
            yield f"event: message\ndata: {data}\n\n"
    finally:
        _mcp_sessions.pop(session_id, None)


async def _send_to_session(session_id: str, message: Dict[str, Any]):
    """Send a JSON-RPC message to a connected session."""
    queue = _mcp_sessions.get(session_id)
    if queue:
        await queue.put(message)


# ── Tool Implementations ──

def _tool_queue_status(limit: int = 10) -> Dict[str, Any]:
    tasks = _task_queue[:limit]
    return {
        "queue_depth": len(_task_queue),
        "tasks": tasks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _tool_task_intake(description: str, priority: str = "medium") -> Dict[str, Any]:
    task_id = str(uuid.uuid4())[:8]
    task = {
        "id": task_id,
        "description": description,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _task_queue.append(task)
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    _task_queue.sort(key=lambda t: priority_order.get(t["priority"], 1))
    return {
        "task_id": task_id,
        "status": "submitted",
        "queue_position": len(_task_queue),
    }


def _tool_dispatch_work(agent: str, task: str) -> Dict[str, Any]:
    dispatch_id = str(uuid.uuid4())[:8]
    return {
        "dispatch_id": dispatch_id,
        "agent": agent,
        "task": task,
        "status": "dispatched",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _tool_boot_check() -> Dict[str, Any]:
    return _boot_status


def _tool_list_skills() -> Dict[str, Any]:
    return {
        "skills": [
            {"name": k, **v}
            for k, v in _skills_db.items()
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _tool_get_status() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "uptime_seconds": 0,  # Would calculate from boot time in prod
        "queue_depth": len(_task_queue),
        "slots_online": _boot_status["slots_online"],
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── JSON-RPC Dispatch ──

TOOLS_REGISTRY = {
    "queue_status": _tool_queue_status,
    "task_intake": _tool_task_intake,
    "dispatch_work": _tool_dispatch_work,
    "boot_check": _tool_boot_check,
    "list_skills": _tool_list_skills,
    "get_status": _tool_get_status,
}


def _handle_jsonrpc(req: Dict[str, Any]) -> Dict[str, Any]:
    """Handle a single JSON-RPC request."""
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "lantern-os-mcp",
                    "version": "1.0.0",
                },
                "capabilities": {
                    "tools": {},
                    "logging": {},
                },
            },
        }

    if method == "tools/list":
        tools = []
        for name, fn in TOOLS_REGISTRY.items():
            import inspect
            sig = inspect.signature(fn)
            parameters = {
                "type": "object",
                "properties": {},
                "required": [],
            }
            for param_name, param in sig.parameters.items():
                if param_name in ("limit",):
                    parameters["properties"][param_name] = {
                        "type": "integer",
                        "default": param.default if param.default is not inspect.Parameter.empty else 10,
                    }
                elif param_name in ("description", "agent", "task", "priority"):
                    parameters["properties"][param_name] = {
                        "type": "string",
                        "default": param.default if param.default is not inspect.Parameter.empty else "",
                    }
                else:
                    parameters["properties"][param_name] = {
                        "type": "string",
                        "default": param.default if param.default is not inspect.Parameter.empty else "",
                    }
                if param.default is inspect.Parameter.empty:
                    parameters["required"].append(param_name)
            tools.append({
                "name": name,
                "description": (fn.__doc__ or "").strip(),
                "inputSchema": parameters,
            })
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": tools},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        fn = TOOLS_REGISTRY.get(tool_name)
        if not fn:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool '{tool_name}' not found",
                },
            }
        try:
            result = fn(**tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, default=str)}],
                    "isError": False,
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True,
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' not found"},
    }


# ── HTTP Endpoints ──

@app.get("/health")
async def health():
    return {
        "status": "online",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "slots_online": _boot_status["slots_online"],
        "queue_depth": len(_task_queue),
    }


@app.get("/sse")
async def sse_endpoint(request: Request):
    session_id = request.query_params.get("session_id", str(uuid.uuid4()))
    return StreamingResponse(
        _event_stream(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/messages")
async def messages_endpoint(request: Request):
    """Receive JSON-RPC messages from MCP client."""
    session_id = request.query_params.get("session_id", "")
    try:
        body = await request.json()
    except Exception:
        body = {}

    if isinstance(body, list):
        # Batch request
        results = [_handle_jsonrpc(req) for req in body]
        # Fire-and-forget responses back to client via SSE
        for resp in results:
            await _send_to_session(session_id, resp)
        return JSONResponse({"status": "batch processed"})
    else:
        result = _handle_jsonrpc(body)
        await _send_to_session(session_id, result)
        return JSONResponse(result)


@app.get("/")
async def root():
    return {
        "name": "Lantern OS MCP Server",
        "version": "1.0.0",
        "endpoints": ["/sse", "/messages", "/health"],
        "tools": list(TOOLS_REGISTRY.keys()),
    }


# ── Main ──

if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8771"))
    host = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    print(f"[MCP] Lantern OS MCP Server starting on http://{host}:{port}")
    print(f"[MCP] Tools: {list(TOOLS_REGISTRY.keys())}")
    uvicorn.run(app, host=host, port=port, log_level="info")
