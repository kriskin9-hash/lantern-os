"""LANTERN-MEMORY: Persistent accumulated learning via append-only JSONL.

Wraps existing JSONL logs (conversations, observations, convergence records)
as a queryable Memory interface with confidence scoring and evidence tracking.

Implements the Remember stage of the Convergence Loop.
Each memory entry is immutable — confidence may shift, content never changes.

Reference: CONVERGANCE-SIGMA0-BRIEFING.md, convergence-core-mapping.md
"""

import json
import itertools
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict


@dataclass
class MemoryEntry:
    """Single entry in persistent memory log."""
    id: str
    timestamp: datetime
    source: str  # tool/agent that created this
    confidence: float  # 0.0-1.0: trustworthiness
    content: Dict[str, Any]  # the actual data
    evidence_ids: List[str] = None  # which memories support this?

    def __post_init__(self):
        if self.evidence_ids is None:
            self.evidence_ids = []

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "confidence": self.confidence,
            "content": self.content,
            "evidence_ids": self.evidence_ids,
        }


class MemoryStore:
    """Queryable interface over append-only JSONL logs.

    Manages multiple log files and provides unified query API.
    All appends are immutable; queries filter by pattern/confidence.
    """

    def __init__(self, memory_dir: str = "data"):
        """Initialize memory store with directory containing JSONL logs.

        Args:
            memory_dir: Directory containing JSONL files
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Known log files (can expand)
        self.logs = {
            "conversations": self.memory_dir / "conversations" / "garage-conversations.jsonl",
            "observations": self.memory_dir / "observations.jsonl",
            "convergence": self.memory_dir / "convergence-records.jsonl",
            "dreams": self.memory_dir / "dreams.jsonl",
            "trading": self.memory_dir / "trading-history.jsonl",
        }

        # Ensure directories exist
        for log_path in self.logs.values():
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if not log_path.exists():
                log_path.touch()

        self.cache: Dict[str, MemoryEntry] = {}
        # Monotonic suffix so two appends from the same source can never collide
        # on an ID. datetime.now().timestamp() has coarse resolution on Windows
        # (~15ms system tick), so rapid same-source appends would otherwise share
        # a timestamp -> identical ID -> the first entry is silently lost.
        self._id_counter = itertools.count()
        self._load_cache()

    def _load_cache(self) -> None:
        """Load all memories into cache."""
        for log_name, log_path in self.logs.items():
            if not log_path.exists():
                continue

            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            # Parse timestamp if present
                            if "timestamp" in data and isinstance(data["timestamp"], str):
                                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                            elif "timestamp" not in data:
                                data["timestamp"] = datetime.now()

                            # Create memory entry with log source
                            mem_id = data.get("id", f"{log_name}-{len(self.cache)}")
                            source = data.get("source", log_name)
                            confidence = data.get("confidence", 0.9)
                            content = data.get("content", data)
                            evidence_ids = data.get("evidence_ids", [])

                            entry = MemoryEntry(
                                id=mem_id,
                                timestamp=data["timestamp"],
                                source=source,
                                confidence=confidence,
                                content=content,
                                evidence_ids=evidence_ids,
                            )
                            self.cache[mem_id] = entry
                        except (json.JSONDecodeError, KeyError):
                            continue
            except Exception as e:
                print(f"Error loading {log_path}: {e}")

    def append(
        self,
        source: str,
        content: Dict[str, Any],
        confidence: float = 0.9,
        evidence_ids: Optional[List[str]] = None,
        log_type: str = "observations",
    ) -> MemoryEntry:
        """Append new memory entry to log.

        Args:
            source: Origin (tool/agent name)
            content: The data to store
            confidence: Trust level (0.0-1.0)
            evidence_ids: Supporting memories
            log_type: Which log file to append to

        Returns: MemoryEntry with assigned ID
        """
        mem_id = f"{source}-{datetime.now().timestamp()}-{next(self._id_counter)}"
        timestamp = datetime.now()
        evidence_ids = evidence_ids or []

        # Clamp confidence
        confidence = max(0.0, min(1.0, confidence))

        # Create entry
        entry = MemoryEntry(
            id=mem_id,
            timestamp=timestamp,
            source=source,
            confidence=confidence,
            content=content,
            evidence_ids=evidence_ids,
        )

        # Persist to log
        log_path = self.logs.get(log_type, self.logs["observations"])
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as e:
            print(f"Error appending to {log_path}: {e}")

        # Add to cache
        self.cache[mem_id] = entry
        return entry

    def query(
        self,
        pattern: str,
        min_confidence: float = 0.5,
        order_by: Optional[str] = None,
        limit: int = 10,
        source_filter: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Query memory by pattern and confidence.

        Args:
            pattern: Text pattern to search (checked in source and content)
            min_confidence: Minimum confidence threshold
            order_by: Sort by 'timestamp', 'confidence', or None
            limit: Maximum results
            source_filter: Restrict to specific source

        Returns: List of matching MemoryEntry objects
        """
        pattern_lower = pattern.lower()
        results = []

        for entry in self.cache.values():
            # Filter by confidence
            if entry.confidence < min_confidence:
                continue

            # Filter by source
            if source_filter and source_filter.lower() not in entry.source.lower():
                continue

            # Pattern match on source
            if pattern_lower in entry.source.lower():
                results.append(entry)
                continue

            # Pattern match on content
            try:
                content_str = json.dumps(entry.content, default=str).lower()
                if pattern_lower in content_str:
                    results.append(entry)
            except (TypeError, ValueError):
                if pattern_lower in str(entry.content).lower():
                    results.append(entry)

        # Sort if requested
        if order_by == "timestamp":
            results.sort(key=lambda m: m.timestamp)
        elif order_by == "confidence":
            results.sort(key=lambda m: m.confidence, reverse=True)

        return results[:limit]

    def get_by_id(self, mem_id: str) -> Optional[MemoryEntry]:
        """Retrieve memory by ID."""
        return self.cache.get(mem_id)

    def update_confidence(self, mem_id: str, new_confidence: float) -> bool:
        """Update confidence of existing memory (post-verification).

        Args:
            mem_id: ID of memory to update
            new_confidence: New confidence value (0.0-1.0)

        Returns: True if successful
        """
        if mem_id not in self.cache:
            return False

        entry = self.cache[mem_id]
        entry.confidence = max(0.0, min(1.0, new_confidence))
        return True

    def statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        entries = list(self.cache.values())
        if not entries:
            return {
                "total_entries": 0,
                "average_confidence": 0.0,
                "by_source": {},
            }

        avg_confidence = sum(e.confidence for e in entries) / len(entries)

        by_source = {}
        for entry in entries:
            if entry.source not in by_source:
                by_source[entry.source] = {"count": 0, "avg_confidence": 0.0}
            by_source[entry.source]["count"] += 1

        # Recalculate avg per source
        for source in by_source:
            matching = [e for e in entries if e.source == source]
            by_source[source]["avg_confidence"] = (
                sum(e.confidence for e in matching) / len(matching)
            )

        return {
            "total_entries": len(entries),
            "average_confidence": avg_confidence,
            "by_source": by_source,
            "high_confidence_count": len([e for e in entries if e.confidence >= 0.85]),
        }

    def export_csv(self, output_path: str = "data/memory-export.csv") -> None:
        """Export memory to CSV for analysis."""
        import csv

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["ID", "Timestamp", "Source", "Confidence", "Content", "Evidence IDs"]
            )

            for entry in sorted(
                self.cache.values(), key=lambda e: e.timestamp, reverse=True
            ):
                writer.writerow(
                    [
                        entry.id,
                        entry.timestamp.isoformat(),
                        entry.source,
                        entry.confidence,
                        json.dumps(entry.content),
                        ",".join(entry.evidence_ids),
                    ]
                )

        print(f"Memory exported to {output_path}")


# Global memory store instance
_memory_store: Optional[MemoryStore] = None


def get_memory_store(memory_dir: str = "data") -> MemoryStore:
    """Get or create global memory store singleton."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore(memory_dir)
    return _memory_store


def reset_memory_store() -> None:
    """Reset memory store (for testing)."""
    global _memory_store
    _memory_store = None
