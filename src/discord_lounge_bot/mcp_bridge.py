"""
Lantern OS MCP Bridge — Discord Bot to Orchestrator Integration

Purpose: Connect Discord bot slash commands to MCP server endpoints
Author: Founder
Generated: 2026-06-01
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

# Load local env overrides if present
_repo_root = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv
    load_dotenv(_repo_root / ".env.local")
except Exception:
    pass

try:
    import aiohttp
except ImportError:
    aiohttp = None


class MCPBridge:
    """Bridge between Discord bot and MCP server endpoints."""

    def __init__(self, mcp_url: str = None, timeout_sec: float = 5.0):
        """Initialize MCP bridge with orchestrator endpoint."""
        self.mcp_url = mcp_url or os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8770")
        self.timeout = timeout_sec
        self.last_error = None

    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Query /health endpoint from MCP server for status."""
        endpoint = f"{self.mcp_url}/health"
        try:
            if aiohttp is None:
                return {
                    "status": "offline",
                    "reason": "aiohttp not installed; install with: pip install aiohttp",
                    "timestamp": self.now_utc()
                }

            async with aiohttp.ClientSession() as session:
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

    async def get_queue_tasks(self, limit: int = 10) -> Dict[str, Any]:
        """Query task queue from MCP server (uses health endpoint as placeholder)."""
        endpoint = f"{self.mcp_url}/health"
        try:
            if aiohttp is None:
                return {
                    "status": "offline",
                    "tasks": [],
                    "reason": "aiohttp not installed",
                    "timestamp": self.now_utc()
                }

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}?limit={limit}", timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "online",
                            "tasks": data.get("tasks", []),
                            "count": len(data.get("tasks", [])),
                            "timestamp": self.now_utc()
                        }
                    else:
                        return {
                            "status": "error",
                            "tasks": [],
                            "reason": f"Server returned {resp.status}",
                            "timestamp": self.now_utc()
                        }
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "tasks": [],
                "reason": f"Timeout after {self.timeout}s",
                "timestamp": self.now_utc()
            }
        except Exception as e:
            return {
                "status": "error",
                "tasks": [],
                "reason": str(e),
                "timestamp": self.now_utc()
            }

    async def log_user_action(self, user_id: str, action: str, details: str = "") -> Dict[str, Any]:
        """Log Discord user action to MCP server (optional)."""
        endpoint = f"{self.mcp_url}/api/logs"
        payload = {
            "source": "discord",
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": self.now_utc()
        }
        try:
            if aiohttp is None:
                return {"status": "offline", "logged": False}

            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                    if resp.status in (200, 201):
                        return {"status": "ok", "logged": True}
                    else:
                        return {"status": "error", "logged": False, "reason": f"Status {resp.status}"}
        except Exception as e:
            return {"status": "error", "logged": False, "reason": str(e)}

    def format_status_embed(self, status_data: Dict[str, Any]) -> str:
        """Format orchestrator status for Discord embed."""
        if status_data.get("status") == "online":
            data = status_data.get("data", {})
            return (
                f" **Orchestrator Online**\n"
                f"Active Slots: {data.get('active_slots', 'N/A')}\n"
                f"Queue Pending: {data.get('pending_tasks', 'N/A')}\n"
                f"Uptime: {data.get('uptime_hours', 'N/A')}h"
            )
        elif status_data.get("status") == "timeout":
            return "⏱️ **Orchestrator Timeout** — slow response, check manually"
        else:
            return f" **Orchestrator Offline** — {status_data.get('reason', 'unknown error')}"

    def format_queue_embed(self, queue_data: Dict[str, Any]) -> str:
        """Format task queue for Discord embed."""
        if queue_data.get("status") == "online":
            tasks = queue_data.get("tasks", [])
            if not tasks:
                return " **Queue Empty** — no pending tasks"
            lines = [f" **Queue ({queue_data.get('count', 0)} tasks)**"]
            for task in tasks[:5]:  # Show first 5
                task_id = task.get("id", "unknown")[:8]
                task_title = task.get("title", "untitled")[:40]
                lines.append(f"  • `{task_id}` — {task_title}")
            if len(tasks) > 5:
                lines.append(f"  ... and {len(tasks) - 5} more")
            return "\n".join(lines)
        else:
            return f" **Queue Error** — {queue_data.get('reason', 'unknown')}"

    @staticmethod
    def now_utc() -> str:
        """Return current UTC timestamp."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Global bridge instance
_bridge: Optional[MCPBridge] = None


def get_bridge() -> MCPBridge:
    """Get or create global MCP bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = MCPBridge()
    return _bridge


def set_bridge(bridge: MCPBridge):
    """Set global MCP bridge instance."""
    global _bridge
    _bridge = bridge
