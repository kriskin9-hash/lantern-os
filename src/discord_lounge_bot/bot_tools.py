"""
Tool registry for Lantern Discord bot.
Agents SDK pattern: explicit tool metadata for tier gating, validation, tracing.
"""

TOOLS = {
    # Public tier (everyone)
    "status": {
        "name": "status",
        "description": "Lantern OS health summary",
        "tier": "public",
        "parameters": {},
        "returns": {"status": "str", "timestamp": "str", "service": "str"},
    },
    "help": {
        "name": "help",
        "description": "List available commands for your tier",
        "tier": "public",
        "parameters": {},
        "returns": {"commands": "dict"},
    },
    "subscribe": {
        "name": "subscribe",
        "description": "Subscription and payment info",
        "tier": "public",
        "parameters": {},
        "returns": {"tiers": "list[dict]"},
    },
    "music": {
        "name": "music",
        "description": "Browse public domain music from Internet Archive",
        "tier": "public",
        "parameters": {"query": "str(optional)"},
        "returns": {"songs": "list[dict]"},
    },
    "art": {
        "name": "art",
        "description": "View art panels and pixel collections",
        "tier": "public",
        "parameters": {},
        "returns": {"panels": "list[dict]"},
    },
    "movies": {
        "name": "movies",
        "description": "Browse public domain films",
        "tier": "public",
        "parameters": {"query": "str(optional)"},
        "returns": {"films": "list[dict]"},
    },
    # Supporter tier ($20/mo)
    "dream": {
        "name": "dream",
        "description": "Save a dream to your private notebook",
        "tier": "supporter",
        "parameters": {"text": "str(max 2000)"},
        "returns": {"entry_id": "str", "timestamp": "str"},
    },
    "note": {
        "name": "note",
        "description": "Save a note to your private notebook",
        "tier": "supporter",
        "parameters": {"text": "str(max 2000)", "mood": "str(optional)"},
        "returns": {"entry_id": "str", "timestamp": "str"},
    },
    "recall": {
        "name": "recall",
        "description": "Retrieve notebook entries by query",
        "tier": "supporter",
        "parameters": {"query": "str(optional)", "limit": "int(default 5)"},
        "returns": {"entries": "list[dict]"},
    },
    "wish": {
        "name": "wish",
        "description": "Save a wish or goal",
        "tier": "supporter",
        "parameters": {"text": "str(max 2000)", "timeframe": "str(optional)"},
        "returns": {"entry_id": "str"},
    },
    "prompt": {
        "name": "prompt",
        "description": "Get a guided reflection prompt",
        "tier": "supporter",
        "parameters": {"topic": "str(optional)"},
        "returns": {"prompt": "str", "guidance": "str"},
    },
    "mirror": {
        "name": "mirror",
        "description": "Reflect on a recent entry",
        "tier": "supporter",
        "parameters": {"entry_id": "str"},
        "returns": {"reflection": "str"},
    },
    "wallet": {
        "name": "wallet",
        "description": "View subscription status and usage",
        "tier": "supporter",
        "parameters": {},
        "returns": {"tier": "str", "features_unlocked": "list[str]"},
    },
    "odds": {
        "name": "odds",
        "description": "View Kalshi paper trade opportunities",
        "tier": "supporter",
        "parameters": {"limit": "int(default 5)"},
        "returns": {"tickets": "list[dict]"},
    },
    "talk": {
        "name": "talk",
        "description": "Chat with Claude via Discord",
        "tier": "supporter",
        "parameters": {"text": "str(max 2000)"},
        "returns": {"response": "str", "tokens_used": "int"},
    },
    # Pilot tier ($200/mo)
    "queue": {
        "name": "queue",
        "description": "View work queue and task status (requires MCP)",
        "tier": "pilot",
        "parameters": {"limit": "int(default 10)"},
        "returns": {"queue_depth": "int", "tasks": "list[dict]"},
        "requires_mcp": True,
    },
    "intake": {
        "name": "intake",
        "description": "Submit a task to the work queue (requires MCP)",
        "tier": "pilot",
        "parameters": {"description": "str(max 2000)", "priority": "str(low|medium|high)"},
        "returns": {"task_id": "str", "status": "str"},
        "requires_mcp": True,
    },
    "skill": {
        "name": "skill",
        "description": "Deploy and manage skills/workflows",
        "tier": "pilot",
        "parameters": {"action": "str(list|enable|disable)"},
        "returns": {"skills": "list[dict]"},
    },
    "workspace": {
        "name": "workspace",
        "description": "Access pilot workspace features",
        "tier": "pilot",
        "parameters": {},
        "returns": {"workspace_url": "str"},
    },
    "sing": {
        "name": "sing",
        "description": "Play Frank Sinatra music in voice",
        "tier": "pilot",
        "parameters": {"song": "str(optional)"},
        "returns": {"now_playing": "str"},
    },
    "nextsong": {
        "name": "nextsong",
        "description": "Skip to next song",
        "tier": "pilot",
        "parameters": {},
        "returns": {"now_playing": "str"},
    },
    "stop": {
        "name": "stop",
        "description": "Stop music playback",
        "tier": "pilot",
        "parameters": {},
        "returns": {"status": "str"},
    },
    "leave": {
        "name": "leave",
        "description": "Disconnect from voice channel",
        "tier": "pilot",
        "parameters": {},
        "returns": {"status": "str"},
    },
    "converge": {
        "name": "converge",
        "description": "Run a convergence loop (internal)",
        "tier": "pilot",
        "parameters": {"mode": "str(test|validate|live)"},
        "returns": {"result": "str"},
    },
    "rag-status": {
        "name": "rag-status",
        "description": "Check RAG indexing and retrieval status",
        "tier": "pilot",
        "parameters": {},
        "returns": {"indexed_documents": "int", "last_update": "str"},
    },
    "place": {
        "name": "place",
        "description": "Place a trade on Kalshi (paper only)",
        "tier": "pilot",
        "parameters": {"ticket_id": "str", "side": "str(yes|no)", "limit_cents": "int"},
        "returns": {"trade_id": "str", "status": "str"},
    },
    "character": {
        "name": "character",
        "description": "Persistent character roleplay (optional)",
        "tier": "pilot",
        "parameters": {"character": "str", "action": "str"},
        "returns": {"response": "str"},
    },
    "symbol": {
        "name": "symbol",
        "description": "Generate a ternary ID or symbol",
        "tier": "pilot",
        "parameters": {"seed": "str(optional)"},
        "returns": {"symbol": "str"},
    },
    # Founder tier (internal only)
    "dispatch": {
        "name": "dispatch",
        "description": "Dispatch work to orchestrator (Founder only)",
        "tier": "founder",
        "parameters": {"agent": "str", "task": "str"},
        "returns": {"dispatch_id": "str"},
        "requires_mcp": True,
    },
    "controls": {
        "name": "controls",
        "description": "Access bot controls and settings",
        "tier": "founder",
        "parameters": {"action": "str"},
        "returns": {"result": "str"},
    },
    "boot-check": {
        "name": "boot-check",
        "description": "Check orchestrator boot status",
        "tier": "founder",
        "parameters": {},
        "returns": {"status": "str", "slots_online": "int"},
        "requires_mcp": True,
    },
    "release-gate": {
        "name": "release-gate",
        "description": "Control release gates and deployments",
        "tier": "founder",
        "parameters": {"action": "str"},
        "returns": {"result": "str"},
    },
}

TIER_HIERARCHY = {
    "public": 0,
    "supporter": 1,
    "pilot": 2,
    "founder": 3,
}


def get_tool(tool_name: str) -> dict | None:
    """Get tool metadata by name."""
    return TOOLS.get(tool_name)


def get_tools_for_tier(tier: str) -> list[dict]:
    """Get all tools available for a given tier."""
    tier_level = TIER_HIERARCHY.get(tier, 0)
    return [
        tool
        for tool in TOOLS.values()
        if TIER_HIERARCHY.get(tool["tier"], 0) <= tier_level
    ]


def can_access_tool(user_tier: str, tool_name: str) -> bool:
    """Check if user tier can access a tool."""
    tool = get_tool(tool_name)
    if not tool:
        return False
    user_level = TIER_HIERARCHY.get(user_tier, 0)
    tool_level = TIER_HIERARCHY.get(tool["tier"], 0)
    return user_level >= tool_level
