"""
MemOS Bridge — wires MemOS (MemTensor/MemoryOS) into the Lantern OS
convergence IO layer as the semantic retrieval backend for CSF archives.

Architecture:
  Lantern CSF (compressed symbolic archive)
       ↓  ingest_dream_entry()
  MemCube (MemOS plaintext memory layer)
       ↓  search()
  TesseractEngine._convergence_rag()   ← replaces flat readRecentDreams()

MemOS Apache 2.0: https://github.com/MemTensor/MemOS
Install: pip install MemoryOS
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
DREAM_JOURNAL_DIR = DATA_DIR / "dream_journal"
MEMOS_CUBE_DIR = DATA_DIR / "memos_cube"

# ── MemOS availability guard ──────────────────────────────────────────────────
try:
    from memos.mem_cube.general import GeneralMemCube  # type: ignore
    from memos.mem_os.main import MemOS  # type: ignore
    _MEMOS_AVAILABLE = True
except Exception:
    GeneralMemCube = None  # type: ignore
    MemOS = None  # type: ignore
    _MEMOS_AVAILABLE = False


def memos_available() -> bool:
    return _MEMOS_AVAILABLE


# ── Dream entry → MemCube plaintext format ───────────────────────────────────

def _entry_to_mem_text(entry: Dict[str, Any]) -> str:
    """Convert a dream journal entry to MemOS plaintext memory format.

    MemOS plaintext memory: editabile, shareable text with provenance metadata.
    We encode the CTF symbol layer (tags + symbols) as structured text so the
    embedding model can reason about the symbolic vocabulary.
    """
    parts = [f"[dream:{entry.get('id','?')}] {entry.get('text', '')}"]
    if entry.get("tags"):
        parts.append(f"tags: {', '.join(entry['tags'])}")
    if entry.get("symbols"):
        parts.append(f"symbols: {', '.join(entry['symbols'])}")
    if entry.get("emotions"):
        parts.append(f"emotions: {', '.join(entry['emotions'])}")
    if entry.get("lucidity"):
        parts.append(f"lucidity: {entry['lucidity']}")
    if entry.get("kind") and entry["kind"] != "dream":
        parts.append(f"kind: {entry['kind']}")
    ts = entry.get("timestamp", "")
    if ts:
        parts.append(f"recorded: {ts[:10]}")
    return " | ".join(parts)


# ── MemOS MemCube manager ─────────────────────────────────────────────────────

class LanternMemCube:
    """
    Wraps MemOS MemoryOS to provide semantic retrieval over the dream journal.

    Falls back to keyword search if MemOS is not installed.

    Usage:
        cube = LanternMemCube()
        cube.ingest_all()                     # first-time load
        results = cube.search("fog door")     # semantic query
    """

    def __init__(self, user_id: str = "dreamer", llm_model: str = "gemini"):
        self.user_id = user_id
        self.llm_model = llm_model
        self._mos: Optional[Any] = None
        self._entries: List[Dict] = []
        self._load_entries()

    def _load_entries(self) -> None:
        if not DREAM_JOURNAL_DIR.exists():
            return
        for f in sorted(DREAM_JOURNAL_DIR.glob("*.jsonl")):
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    self._entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        self._entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    def _init_memos(self) -> bool:
        if not _MEMOS_AVAILABLE:
            return False
        if self._mos is not None:
            return True
        try:
            MEMOS_CUBE_DIR.mkdir(parents=True, exist_ok=True)
            api_key = (
                os.environ.get("GEMINI_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or os.environ.get("ANTHROPIC_API_KEY")
                or ""
            )
            from memos.configs.mem_os import MemOSConfig  # type: ignore
            cfg = MemOSConfig(
                user_id=self.user_id,
                storage_path=str(MEMOS_CUBE_DIR),
            )
            self._mos = MemOS(cfg)
            return True
        except Exception as exc:
            print(f"[memos_bridge] MemOS init failed: {exc}")
            return False

    def ingest_all(self) -> int:
        """Ingest all dream journal entries into MemOS plaintext memory."""
        if not self._init_memos():
            return 0
        ingested = 0
        for entry in self._entries:
            try:
                self._mos.add(
                    user_id=self.user_id,
                    messages=[{"role": "user", "content": _entry_to_mem_text(entry)}],
                )
                ingested += 1
            except Exception:
                pass
        return ingested

    def ingest_entry(self, entry: Dict[str, Any]) -> bool:
        """Ingest a single new dream entry after it's saved."""
        if not self._init_memos():
            return False
        try:
            self._mos.add(
                user_id=self.user_id,
                messages=[{"role": "user", "content": _entry_to_mem_text(entry)}],
            )
            return True
        except Exception:
            return False

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search over dream memories.
        Returns list of {text, score, entry_id} dicts.

        Falls back to keyword substring match if MemOS unavailable.
        """
        if self._init_memos():
            try:
                results = self._mos.get_memory(
                    user_id=self.user_id,
                    query=query,
                )
                # Normalise MemOS result format to our schema
                out = []
                for r in (results or [])[:limit]:
                    if isinstance(r, dict):
                        out.append({"text": r.get("memory", str(r)), "source": "memos"})
                    else:
                        out.append({"text": str(r), "source": "memos"})
                return out
            except Exception as exc:
                print(f"[memos_bridge] MemOS search error: {exc}")

        # Keyword fallback
        q = query.lower()
        matches = [
            e for e in self._entries
            if q in (e.get("text") or "").lower()
            or any(q in t for t in e.get("tags", []))
            or any(q in s for s in e.get("symbols", []))
        ]
        return [
            {"text": _entry_to_mem_text(e), "source": "keyword", "entry_id": e.get("id")}
            for e in matches[:limit]
        ]

    def get_context_for_prompt(self, query: str, limit: int = 3) -> str:
        """
        Returns a formatted string ready to inject into a system prompt.
        Used by TesseractEngine._convergence_rag() as a drop-in replacement
        for the flat readRecentDreams() approach.
        """
        results = self.search(query, limit=limit)
        if not results:
            return ""
        lines = [f"Memory [{i+1}]: {r['text']}" for i, r in enumerate(results)]
        return "Semantic dream memories (MemOS retrieval):\n" + "\n".join(lines)


# ── Singleton ─────────────────────────────────────────────────────────────────
_cube: Optional[LanternMemCube] = None

def get_cube(user_id: str = "dreamer") -> LanternMemCube:
    global _cube
    if _cube is None:
        _cube = LanternMemCube(user_id=user_id)
    return _cube
