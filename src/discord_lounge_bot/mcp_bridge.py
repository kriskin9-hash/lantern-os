"""
Lantern OS MCP Bridge — Discord Bot to MCP Server Integration

Purpose: Connect Discord bot slash commands to MCP server endpoints
via aiohttp HTTP client (lightweight, no SDK dependency).

Endpoints used:
  GET  /health         — orchestrator status
  POST /messages       — JSON-RPC tool calls
  GET  /sse            — SSE connection (optional, for async events)
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None


class MCPBridge:
    """Bridge between Discord bot and MCP server endpoints."""

    def __init__(self, mcp_url: str = None, timeout_sec: float = 5.0):
        """Initialize MCP bridge with orchestrator endpoint."""
        self.mcp_url = mcp_url or os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8771")
        self.timeout = timeout_sec
        self.last_error = None
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Query /health endpoint from MCP server for status."""
        endpoint = f"{self.mcp_url}/health"
        try:
            if not AIOHTTP_AVAILABLE:
                return {
                    "status": "offline",
                    "reason": "aiohttp not installed; install with: pip install aiohttp",
                    "timestamp": self.now_utc()
                }

            session = await self._get_session()
            async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "status": "online",
                        "timestamp": self.now_utc(),
                        "data": data
                    }
                else:
                    self.last_error = f"Status {resp.status}"
                    return {
                        "status": "error",
                        "reason": f"Server returned {resp.status}",
                        "timestamp": self.now_utc()
                    }
        except asyncio.TimeoutError:
            self.last_error = "Timeout"
            return {
                "status": "timeout",
                "reason": f"MCP server did not respond within {self.timeout}s",
                "timestamp": self.now_utc()
            }
        except Exception as e:
            self.last_error = str(e)
            return {
                "status": "error",
                "reason": str(e),
                "timestamp": self.now_utc()
            }

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an MCP tool via JSON-RPC."""
        if arguments is None:
            arguments = {}
        endpoint = f"{self.mcp_url}/messages"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            }
        }
        try:
            if not AIOHTTP_AVAILABLE:
                return {"status": "offline", "reason": "aiohttp not installed"}

            session = await self._get_session()
            async with session.post(
                endpoint,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as resp:
                data = await resp.json()
                if "result" in data:
                    return {
                        "status": "ok",
                        "result": data["result"],
                    }
                elif "error" in data:
                    return {
                        "status": "error",
                        "reason": data["error"].get("message", "unknown"),
                    }
                return {"status": "unknown", "data": data}
        except asyncio.TimeoutError:
            return {"status": "timeout", "reason": f"Timeout after {self.timeout}s"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    async def get_queue_tasks(self, limit: int = 10) -> Dict[str, Any]:
        """Query task queue from MCP server via tool call."""
        result = await self.call_tool("queue_status", {"limit": limit})
        if result.get("status") == "ok":
            content = result["result"].get("content", [])
            if content:
                try:
                    tasks_data = json.loads(content[0]["text"])
                    return {
                        "status": "online",
                        "tasks": tasks_data.get("tasks", []),
                        "count": tasks_data.get("queue_depth", 0),
                        "timestamp": self.now_utc()
                    }
                except (json.JSONDecodeError, KeyError):
                    pass
        return {
            "status": result.get("status", "error"),
            "tasks": [],
            "count": 0,
            "reason": result.get("reason", "unknown"),
            "timestamp": self.now_utc()
        }

    async def submit_task(self, description: str, priority: str = "medium") -> Dict[str, Any]:
        """Submit a task via MCP tool."""
        result = await self.call_tool("task_intake", {"description": description, "priority": priority})
        if result.get("status") == "ok":
            content = result["result"].get("content", [])
            if content:
                try:
                    return json.loads(content[0]["text"])
                except json.JSONDecodeError:
                    pass
        return {"status": result.get("status", "error"), "reason": result.get("reason", "unknown")}

    async def dispatch_work(self, agent: str, task: str) -> Dict[str, Any]:
        """Dispatch work to an orchestrator agent."""
        result = await self.call_tool("dispatch_work", {"agent": agent, "task": task})
        if result.get("status") == "ok":
            content = result["result"].get("content", [])
            if content:
                try:
                    return json.loads(content[0]["text"])
                except json.JSONDecodeError:
                    pass
        return {"status": result.get("status", "error"), "reason": result.get("reason", "unknown")}

    async def boot_check(self) -> Dict[str, Any]:
        """Check orchestrator boot status."""
        result = await self.call_tool("boot_check")
        if result.get("status") == "ok":
            content = result["result"].get("content", [])
            if content:
                try:
                    return json.loads(content[0]["text"])
                except json.JSONDecodeError:
                    pass
        return {"status": result.get("status", "error"), "reason": result.get("reason", "unknown")}

    def format_status_embed(self, status_data: Dict[str, Any]) -> str:
        """Format orchestrator status for Discord embed."""
        if status_data.get("status") == "online":
            data = status_data.get("data", {})
            return (
                f"✅ **Orchestrator Online**\n"
                f"Slots: {data.get('slots_online', 'N/A')}\n"
                f"Queue Depth: {data.get('queue_depth', 'N/A')}\n"
                f"Version: {data.get('version', 'N/A')}"
            )
        elif status_data.get("status") == "timeout":
            return "⏱️ **Orchestrator Timeout** — slow response, check manually"
        else:
            return f"❌ **Orchestrator Offline** — {status_data.get('reason', 'unknown error')}"

    def format_queue_embed(self, queue_data: Dict[str, Any]) -> str:
        """Format task queue for Discord embed."""
        if queue_data.get("status") == "online":
            tasks = queue_data.get("tasks", [])
            if not tasks:
                return "📭 **Queue Empty** — no pending tasks"
            lines = [f"📋 **Queue ({queue_data.get('count', 0)} tasks)**"]
            for task in tasks[:5]:
                task_id = task.get("id", "unknown")[:8]
                task_title = task.get("description", "untitled")[:40]
                priority = task.get("priority", "?")
                lines.append(f"  • `{task_id}` [{priority}] — {task_title}")
            if len(tasks) > 5:
                lines.append(f"  ... and {len(tasks) - 5} more")
            return "\n".join(lines)
        else:
            return f"❌ **Queue Error** — {queue_data.get('reason', 'unknown')}"

    @staticmethod
    def now_utc() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Global bridge instance
_bridge: Optional[MCPBridge] = None


def get_bridge() -> MCPBridge:
    global _bridge
    if _bridge is None:
        _bridge = MCPBridge()
    return _bridge


def set_bridge(bridge: MCPBridge):
    global _bridge
    _bridge = bridge
