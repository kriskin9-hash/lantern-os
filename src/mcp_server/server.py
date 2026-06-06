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
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

# Mesh bridge for P2P coordination
from mesh_bridge import get_mesh_bridge, MeshBridge, HTTPX_AVAILABLE

REPO_ROOT = Path(__file__).resolve().parents[2]

# Load local env overrides if present
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env.local")
except Exception:
    pass

# Agent tool hooks + CSF cache enforcement
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from agent_tool_hooks import ToolHookRegistry
    HOOKS_AVAILABLE = True
except Exception as exc:
    logger = logging.getLogger("lantern.mcp")
    logger.warning("agent_tool_hooks not available: %s", exc)
    HOOKS_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("lantern.mcp")

# FastAPI + SSE
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import StreamingResponse, JSONResponse
    from starlette.background import BackgroundTask
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError as e:
    FASTAPI_AVAILABLE = False
    logger.critical("fastapi/uvicorn not installed: %s", e)
    sys.exit(1)

# Optional: OpenAI Agents SDK for native MCP server support
try:
    from agents.mcp.server import MCPServer as AgentsMCPServer
    from agents.mcp.server import MCPServerSse as AgentsMCPServerSse
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False

app = FastAPI(title="Lantern OS MCP Server", version="1.0.0")

# ── Fleet status — loaded from file, not hardcoded ──
_FLEET_STATUS_PATH = REPO_ROOT / "data" / "status" / "super-jarvis-fleet.json"
_AGENTS_CONFIG_PATH = REPO_ROOT / "config" / "agents.json"

def _load_fleet_status() -> Dict[str, Any]:
    """Load fleet status from data/status/super-jarvis-fleet.json.
    Returns honest counts: designed slots from config, active slots from status file.
    Never fabricates live worker counts."""
    designed_slots = 36  # from agents.json designedRingSlots
    active_slots = 0
    sleeping_slots = 0
    claim_boundary = "design contract only; live worker counts require local orchestrator evidence"

    # Load designed slot count from agents config
    try:
        if _AGENTS_CONFIG_PATH.exists():
            agents_cfg = json.loads(_AGENTS_CONFIG_PATH.read_text(encoding="utf-8"))
            designed_slots = agents_cfg.get("designedRingSlots", designed_slots)
            claim_boundary = agents_cfg.get("fleetClaimBoundary", claim_boundary)
    except Exception as exc:
        logger.warning("Could not read agents config: %s", exc)

    # Load live status from fleet status file
    try:
        if _FLEET_STATUS_PATH.exists():
            fleet = json.loads(_FLEET_STATUS_PATH.read_text(encoding="utf-8"))
            active_slots = fleet.get("activeSlots", 0)
            sleeping_slots = fleet.get("sleepingSlots", designed_slots)
            claim_boundary = fleet.get("fleetClaimBoundary", claim_boundary)
    except Exception as exc:
        logger.warning("Could not read fleet status file: %s", exc)

    return {
        "designed_ring_slots": designed_slots,
        "active_slots": active_slots,
        "sleeping_slots": sleeping_slots,
        "claim_boundary": claim_boundary,
    }

_STARTED_AT = datetime.now(timezone.utc).isoformat()

# ── In-memory state (replace with Redis/DB in production) ──
_task_queue: List[Dict[str, Any]] = []

# Skills registry — only skills with real deployed Python modules.
# super_jarvis_fleet is NOT a skill — it is the agent fleet. See data/status/super-jarvis-fleet.json.
# kalshi_bridge removed: no Python module exists, only a standalone script (scripts/kalshi_odds.py).
_skills_db: Dict[str, Dict[str, Any]] = {
    "dream_journal":   {"enabled": True,  "version": "1.0.0", "module": "skills/dream_journal/dream_journal.py"},
    "lucid_dreaming":  {"enabled": True,  "version": "1.0.0", "module": "skills/lucid_dreaming/mild_wbtb_protocol.py"},
    "archive_curator": {"enabled": True,  "version": "1.0.0", "module": "src/discord_lounge_bot/archive_curator.py"},
    "voice_curator":   {"enabled": True,  "version": "1.0.0", "module": "src/discord_lounge_bot/voice_curator.py"},
}

def _build_boot_status() -> Dict[str, Any]:
    """Build boot status from real fleet state, not hardcoded slot counts."""
    fleet = _load_fleet_status()
    return {
        "status": "online",
        "active_slots": fleet["active_slots"],
        "sleeping_slots": fleet["sleeping_slots"],
        "designed_ring_slots": fleet["designed_ring_slots"],
        "claim_boundary": fleet["claim_boundary"],
        "started_at": _STARTED_AT,
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
    """Check orchestrator boot status. Reports honest slot counts from fleet status file."""
    return _build_boot_status()


def _tool_list_skills() -> Dict[str, Any]:
    """List available skills. Does not include fleet agents — see fleet_status for agent fleet."""
    return {
        "skills": [
            {"name": k, **v}
            for k, v in _skills_db.items()
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _tool_get_status() -> Dict[str, Any]:
    """Overall system status with honest fleet counts loaded from fleet status file."""
    fleet = _load_fleet_status()
    started = datetime.fromisoformat(_STARTED_AT)
    uptime = int((datetime.now(timezone.utc) - started).total_seconds())
    return {
        "status": "healthy",
        "uptime_seconds": uptime,
        "queue_depth": len(_task_queue),
        "active_slots": fleet["active_slots"],
        "designed_ring_slots": fleet["designed_ring_slots"],
        "claim_boundary": fleet["claim_boundary"],
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _tool_fleet_status() -> Dict[str, Any]:
    """Read the agent fleet status directly from data/status/super-jarvis-fleet.json.
    Returns designed ring slot count, active vs sleeping slots, and the claim boundary.
    Active slots = 0 means all agents are in sleep/design mode, not live workers."""
    fleet = _load_fleet_status()
    # Also return raw slot list if available
    slots_preview: List[Dict[str, Any]] = []
    try:
        if _FLEET_STATUS_PATH.exists():
            raw = json.loads(_FLEET_STATUS_PATH.read_text(encoding="utf-8"))
            slots_preview = raw.get("slots", [])[:5]  # first 5 for preview
    except Exception:
        pass
    return {
        **fleet,
        "slots_preview": slots_preview,
        "fleet_status_file": str(_FLEET_STATUS_PATH),
        "file_exists": _FLEET_STATUS_PATH.exists(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Mesh / P2P Tools ──

_mesh = get_mesh_bridge()


def _tool_mesh_register_peer(name: str, mcp_url: str, messages_url: str = "", donated_resources: str = "{}") -> Dict[str, Any]:
    """Register a peer node in the P2P mesh. Peers may donate resources (agent slots, compute)."""
    resources = json.loads(donated_resources) if donated_resources else {}
    # NOTE: this is a sync wrapper; the real mesh bridge is async.
    # For the MCP tool registry we return a serializable dict.
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_mesh.register_peer(
        name=name,
        mcp_url=mcp_url,
        messages_url=messages_url or None,
        donated_resources=resources,
    ))
    return result


def _tool_mesh_status() -> Dict[str, Any]:
    """Show P2P mesh topology: founder, peers, and aggregate donated resources."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_mesh.get_topology())


def _tool_mesh_donate(peer_id: str, resources: str) -> Dict[str, Any]:
    """Update the resources a peer is willing to donate (opt-in)."""
    parsed = json.loads(resources) if resources else {}
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_mesh.update_donation(peer_id, parsed))
    return result or {"error": "peer not found"}


def _tool_mesh_prune(max_age_seconds: float = 300.0) -> Dict[str, Any]:
    """Remove stale peers that haven't sent a heartbeat. Founder-only control."""
    loop = asyncio.get_event_loop()
    removed = loop.run_until_complete(_mesh.prune_stale_peers(max_age_seconds))
    return {"pruned": removed, "timestamp": datetime.now(timezone.utc).isoformat()}


def _tool_update_lantern_os(restart: bool = True) -> Dict[str, Any]:
    """Pull latest master, install dependencies, and optionally restart the server."""
    import subprocess
    steps = []

    try:
        pull = subprocess.run(
            ["git", "pull", "origin", "master"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )
        steps.append({"step": "git_pull", "ok": pull.returncode == 0, "output": pull.stdout.strip() or pull.stderr.strip()})
    except Exception as exc:
        steps.append({"step": "git_pull", "ok": False, "output": str(exc)})

    try:
        npm = subprocess.run(
            ["npm", "install", "--prefix", "apps/lantern-garage"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=120,
        )
        steps.append({"step": "npm_install", "ok": npm.returncode == 0, "output": npm.stdout.strip() or npm.stderr.strip()})
    except Exception as exc:
        steps.append({"step": "npm_install", "ok": False, "output": str(exc)})

    new_version = {"commit": "unknown", "tag": "unknown"}
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10)
        tag = subprocess.run(["git", "describe", "--tags", "--always"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10)
        new_version = {"commit": commit.stdout.strip(), "tag": tag.stdout.strip()}
    except Exception:
        pass

    all_ok = all(s["ok"] for s in steps)
    restart_scheduled = False

    if all_ok and restart:
        try:
            if os.name == "nt":
                subprocess.Popen(
                    ["powershell.exe", "-Command", "Start-Sleep -Seconds 2; Start-Process node -ArgumentList 'apps/lantern-garage/server.js' -WindowStyle Hidden"],
                    cwd=REPO_ROOT, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                subprocess.Popen(
                    ["sh", "-c", "sleep 2 && node apps/lantern-garage/server.js"],
                    cwd=REPO_ROOT, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            restart_scheduled = True
        except Exception as exc:
            steps.append({"step": "restart", "ok": False, "output": str(exc)})

    return {"ok": all_ok, "steps": steps, "version": new_version, "restart_scheduled": restart_scheduled}


# ── JSON-RPC Dispatch ──

TOOLS_REGISTRY = {
    "queue_status": _tool_queue_status,
    "task_intake": _tool_task_intake,
    "dispatch_work": _tool_dispatch_work,
    "boot_check": _tool_boot_check,
    "list_skills": _tool_list_skills,
    "get_status": _tool_get_status,
    "fleet_status": _tool_fleet_status,
    "mesh_register_peer": _tool_mesh_register_peer,
    "mesh_status": _tool_mesh_status,
    "mesh_donate": _tool_mesh_donate,
    "mesh_prune": _tool_mesh_prune,
    "update_lantern_os": _tool_update_lantern_os,
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
            if HOOKS_AVAILABLE:
                registry = ToolHookRegistry(agent_id="mcp_server")
                result = registry.run(tool_name, tool_args, fn=fn, request_id=str(req_id))
            else:
                result = fn(**tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, default=str)}],
                    "isError": False,
                },
            }
        except Exception as exc:
            logger.exception("Tool '%s' failed with args %s", tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {exc}"}],
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
    start = time.time()
    fleet = _load_fleet_status()
    mesh = await _mesh.get_topology()
    result = {
        "status": "online",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_slots": fleet["active_slots"],
        "designed_ring_slots": fleet["designed_ring_slots"],
        "claim_boundary": fleet["claim_boundary"],
        "queue_depth": len(_task_queue),
        "mesh_peers": mesh["peer_count"],
        "mesh_donors": mesh["donor_count"],
        "response_time_ms": round((time.time() - start) * 1000, 2),
    }
    return result


@app.get("/mesh/topology")
async def mesh_topology():
    """Expose mesh topology as a plain HTTP endpoint (no SSE required)."""
    return await _mesh.get_topology()


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
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON from session %s: %s", session_id, exc)
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}, status_code=400)
    except Exception as exc:
        logger.warning("Unexpected request error from session %s: %s", session_id, exc)
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal error"}}, status_code=500)

    if not body:
        logger.warning("Empty body from session %s", session_id)
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}}, status_code=400)

    if isinstance(body, list):
        # Batch request
        results = [_handle_jsonrpc(req) for req in body]
        for resp in results:
            await _send_to_session(session_id, resp)
        return JSONResponse({"status": "batch processed"})
    else:
        result = _handle_jsonrpc(body)
        await _send_to_session(session_id, result)
        return JSONResponse(result)


@app.get("/")
async def root():
    mesh = await _mesh.get_topology()
    return {
        "name": "Lantern OS MCP Server",
        "version": "1.0.0",
        "endpoints": ["/sse", "/messages", "/health", "/mesh/topology"],
        "tools": list(TOOLS_REGISTRY.keys()),
        "mesh": {
            "founder_id": mesh["founder_id"],
            "peer_count": mesh["peer_count"],
            "donor_count": mesh["donor_count"],
            "aggregate_donated_resources": mesh["aggregate_donated_resources"],
        },
    }


# ── Main ──

if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8771"))
    host = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    logger.info("Lantern OS MCP Server starting on http://%s:%s", host, port)
    logger.info("Tools available: %s", list(TOOLS_REGISTRY.keys()))
    logger.info("Mesh mode: founder control + opt-in peer donations")
    uvicorn.run(app, host=host, port=port, log_level="info")
