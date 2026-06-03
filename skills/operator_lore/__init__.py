"""
Operator Lore Skill — Lantern OS

Ingested CSF (Context Surface File) for operator identity, preferences,
dreams, memories, and project context. Surfaced at Tesseract Layer 0
and bubbled into Convergence context for persona alignment.

Usage:
    from skills.operator_lore import get_lore_engine
    lore = get_lore_engine()
    hints = lore.query("dream journal", limit=5)
    context = lore.build_convergence_context("Orion scarf")
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILL_DIR = Path(__file__).resolve().parent
CSF_PATH = SKILL_DIR / "operator_csf.json"


@dataclass
class LoreEntry:
    date: str
    content: str
    tags: List[str]
    layer: str
    section: str

    def score(self, query: str) -> float:
        """Simple relevance scoring for keyword queries."""
        q = query.lower()
        text = f"{self.content} {' '.join(self.tags)} {self.section}".lower()
        return sum(1 for word in q.split() if word in text)


class OperatorLoreEngine:
    """Query-able operator CSF surface."""

    def __init__(self, csf_path: Optional[Path] = None) -> None:
        self.csf_path = csf_path or CSF_PATH
        self._entries: List[LoreEntry] = []
        self._load()

    def _load(self) -> None:
        if not self.csf_path.exists():
            return
        with open(self.csf_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for section, items in data.get("sections", {}).items():
            for item in items:
                self._entries.append(
                    LoreEntry(
                        date=item.get("date", ""),
                        content=item.get("content", ""),
                        tags=item.get("tags", []),
                        layer=item.get("layer", "SURFACE"),
                        section=section,
                    )
                )

    def query(self, query: str, limit: int = 10) -> List[LoreEntry]:
        """Return top-N matching lore entries."""
        scored = [(e.score(query), e) for e in self._entries]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for s, e in scored if s > 0][:limit]

    def by_section(self, section: str) -> List[LoreEntry]:
        return [e for e in self._entries if e.section == section]

    def by_tag(self, tag: str) -> List[LoreEntry]:
        return [e for e in self._entries if tag in e.tags]

    def by_layer(self, layer: str) -> List[LoreEntry]:
        return [e for e in self._entries if e.layer == layer]

    def build_convergence_context(self, message: str, limit: int = 5) -> str:
        """Build a context string for the tesseract convergence engine."""
        matches = self.query(message, limit=limit)
        if not matches:
            matches = self._entries[:limit]
        parts = ["Operator lore context:"]
        for e in matches:
            parts.append(f"- [{e.date}][{e.layer}] {e.content}")
        return "\n".join(parts)

    def summary(self) -> Dict[str, Any]:
        return {
            "entries": len(self._entries),
            "sections": sorted({e.section for e in self._entries}),
            "layers": sorted({e.layer for e in self._entries}),
            "date_range": {
                "earliest": min((e.date for e in self._entries), default=""),
                "latest": max((e.date for e in self._entries), default=""),
            },
        }


# Singleton instance
_lore_engine: Optional[OperatorLoreEngine] = None


def get_lore_engine(csf_path: Optional[Path] = None) -> OperatorLoreEngine:
    global _lore_engine
    if _lore_engine is None:
        _lore_engine = OperatorLoreEngine(csf_path)
    return _lore_engine


# CLI entrypoint
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="")
    parser.add_argument("--section", default="")
    parser.add_argument("--tag", default="")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    engine = get_lore_engine()

    if args.summary:
        print(json.dumps(engine.summary(), indent=2))
    elif args.section:
        for e in engine.by_section(args.section)[: args.limit]:
            print(f"[{e.date}][{e.layer}] {e.content}")
    elif args.tag:
        for e in engine.by_tag(args.tag)[: args.limit]:
            print(f"[{e.date}][{e.layer}] {e.content}")
    elif args.query:
        for e in engine.query(args.query, limit=args.limit):
            print(f"[{e.date}][{e.layer}] {e.content}")
    else:
        print("Usage: python -m skills.operator_lore --query 'dream journal' --limit 5")
        print("       python -m skills.operator_lore --summary")
