"""
OpenAI Agents SDK MCP Connector for Lantern OS Discord Bot

Connects the Discord bot to MCP (Model Context Protocol) servers using the
openai-agents SDK. Allows slash commands to discover and invoke MCP tools.

Requires: openai-agents>=0.17.0
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from agents import Agent, Runner
    from agents.mcp import MCPServer, MCPServerSse
    OPENAI_AGENTS_AVAILABLE = True
except ImportError as e:
    OPENAI_AGENTS_AVAILABLE = False
    MCPServer = None
    MCPServerSse = None
    Agent = None
    Runner = None
    print(f"[INFO] openai-agents SDK not available: {e}")


class LanternMCPConnector:
    """
    Connector that manages MCP server connections and exposes
    tool discovery + invocation to Discord slash commands.
    """

    def __init__(self, mcp_server_url: Optional[str] = None):
        self.mcp_url = mcp_server_url or os.getenv(
            "MCP_SERVER_URL",
            "http://127.0.0.1:8770/sse"
        )
        self.server: Optional[MCPServerSse] = None
        self.connected = False
        self.tools: List[Dict[str, Any]] = []
        self.last_error: Optional[str] = None

    async def connect(self) -> bool:
        """Connect to the MCP server via SSE."""
        if not OPENAI_AGENTS_AVAILABLE:
            self.last_error = "openai-agents SDK not installed"
            return False

        try:
            self.server = MCPServerSse(self.mcp_url)
            await self.server.connect()
            self.connected = True
            # Discover available tools
            self.tools = await self._discover_tools()
            print(f"[MCP] Connected to {self.mcp_url} — {len(self.tools)} tools available")
            return True
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            print(f"[MCP] Connection failed: {e}")
            return False

    async def disconnect(self):
        """Gracefully close MCP connection."""
        if self.server:
            await self.server.disconnect()
            self.server = None
        self.connected = False
        self.tools = []

    async def _discover_tools(self) -> List[Dict[str, Any]]:
        """List tools exposed by the MCP server."""
        if not self.server:
            return []
        try:
            raw_tools = await self.server.list_tools()
            return [
                {
                    "name": t.name,
                    "description": t.description or "No description",
                    "input_schema": t.inputSchema if hasattr(t, "inputSchema") else {},
                }
                for t in raw_tools
            ]
        except Exception as e:
            self.last_error = str(e)
            return []

    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Invoke an MCP tool by name with JSON arguments."""
        if not self.connected or not self.server:
            return "[MCP] Not connected. Run `/mcp-connect` first."

        try:
            result = await self.server.invoke_tool(tool_name, arguments)
            # Result is typically a list of content items
            if isinstance(result, list):
                texts = []
                for item in result:
                    if isinstance(item, dict) and "text" in item:
                        texts.append(item["text"])
                    else:
                        texts.append(str(item))
                return "\n".join(texts)
            return str(result)
        except Exception as e:
            return f"[MCP] Tool invocation failed: {e}"

    def format_tools_embed(self) -> str:
        """Format discovered tools for Discord embed (max ~1900 chars)."""
        if not self.connected:
            return "MCP not connected."
        if not self.tools:
            return "Connected, but no tools discovered on server."

        lines = [f"MCP Server: {self.mcp_url}", f"Tools: {len(self.tools)}", ""]
        for t in self.tools[:15]:
            name = t["name"]
            desc = t["description"]
            if len(desc) > 80:
                desc = desc[:77] + "..."
            lines.append(f"`{name}` — {desc}")
        if len(self.tools) > 15:
            lines.append(f"... and {len(self.tools) - 15} more")
        return "\n".join(lines)


# Global connector instance (lazy-initialized)
_connector: Optional[LanternMCPConnector] = None


def get_mcp_connector() -> LanternMCPConnector:
    global _connector
    if _connector is None:
        _connector = LanternMCPConnector()
    return _connector
