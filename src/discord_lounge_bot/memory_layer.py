"""
Memory Layer for Dream Journal RP Bot (Goal 1)
Minimal persistent session memory with CSF export path.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


# Memory limits to prevent unbounded growth
_MAX_SESSIONS = 1000
_MAX_MESSAGES_PER_SESSION = 100
_MAX_SESSION_AGE_HOURS = 24


class SessionMemory:
    def __init__(self, user_id: int, character: str = "default"):
        self.user_id = user_id
        self.character = character
        self.created_at = datetime.utcnow().isoformat()
        self.messages: List[Dict] = []
        self.mode = "IC"

    def add_message(self, content: str, mode: str = "IC"):
        self.messages.append({
            "timestamp": datetime.utcnow().isoformat(),
            "mode": mode,
            "content": content
        })
        self.mode = mode
        # Limit message history to prevent unbounded growth
        if len(self.messages) > _MAX_MESSAGES_PER_SESSION:
            self.messages = self.messages[-_MAX_MESSAGES_PER_SESSION:]

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "character": self.character,
            "created_at": self.created_at,
            "message_count": len(self.messages),
            "messages": self.messages
        }

    def export_jsonl(self) -> str:
        """Export session as JSONL (one message per line)."""
        lines = [json.dumps(msg) for msg in self.messages]
        return "\n".join(lines)

    def export_csf_stub(self) -> Dict:
        """Placeholder for CSF export (to be wired to cadd_dollhouse_csf)."""
        return {
            "format": "CSF-v1-stub",
            "session": self.to_dict(),
            "note": "Replace with real CSF encoding when cadd_dollhouse_csf is integrated."
        }


class MemoryStore:
    """In-memory store for active sessions (replace with persistent backend later)."""
    def __init__(self):
        self.sessions: Dict[int, SessionMemory] = {}

    def get_or_create(self, user_id: int, character: str = "default") -> SessionMemory:
        # LRU eviction if too many sessions
        if user_id not in self.sessions and len(self.sessions) >= _MAX_SESSIONS:
            self._cleanup_old_sessions()
        if user_id not in self.sessions:
            self.sessions[user_id] = SessionMemory(user_id, character)
        return self.sessions[user_id]

    def end_session(self, user_id: int) -> Optional[SessionMemory]:
        return self.sessions.pop(user_id, None)

    def _cleanup_old_sessions(self) -> None:
        """Remove sessions older than MAX_SESSION_AGE_HOURS."""
        now = time.time()
        to_remove = []
        for user_id, session in self.sessions.items():
            try:
                created = datetime.fromisoformat(session.created_at).timestamp()
                age_hours = (now - created) / 3600
                if age_hours > _MAX_SESSION_AGE_HOURS:
                    to_remove.append(user_id)
            except (ValueError, AttributeError):
                to_remove.append(user_id)
        for user_id in to_remove:
            self.sessions.pop(user_id, None)


# Global store instance
memory_store = MemoryStore()