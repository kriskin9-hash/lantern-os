"""
Dream Journal Core Module for Lantern OS

Integrated with:
- Existing Lantern Dreamer notebooks (data/dreamer/notebooks/*.jsonl)
- MILD / WBTB lucid dreaming protocols (sibling skill)
- SFI (Symbolic / Flourishing Index) vectors
- Bayesian World Model skill for evidence updates and trend analysis

Design goals (per AGENTS.md + Orion style):
- Local-only, append-only, privacy-preserving
- Coexists with (does not replace) the Discord-driven dreamer system
- Produces high-quality mirror prompts for Supergrok / operator analysis
- Small, reviewable, no skeleton — functional on first import

Storage:
- Structured dreams: data/dream_journal/dreams_YYYY-MM.jsonl
- Reads (but does not overwrite) data/dreamer/ for continuity
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import uuid


class DreamJournal:
    def __init__(self, data_dir: str = "data/dream_journal"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.dreamer_notebooks_dir = Path("data/dreamer/notebooks")

    # ------------------------------------------------------------------ #
    # Core logging (new structured dreams)
    # ------------------------------------------------------------------ #
    def log_dream(
        self,
        content: str,
        lucidity: float = 0.0,
        emotions: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        linked_goals: Optional[List[str]] = None,
        sfi_impact: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Log a structured dream entry.

        lucidity: 0.0–1.0 (normalized). Values >1 are treated as /10 scale.
        """
        if lucidity > 1.0:
            lucidity = lucidity / 10.0
        lucidity = max(0.0, min(1.0, round(lucidity, 2)))

        entry = {
            "id": f"dream_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            "timestamp": datetime.now().isoformat(),
            "content": content.strip(),
            "lucidity": lucidity,
            "emotions": emotions or [],
            "tags": tags or [],
            "linked_goals": linked_goals or [],
            "sfi_impact": sfi_impact or {"meaning": 0.0, "purpose": 0.0, "character": 0.0},
            "source": "dream_journal_skill",
        }

        month_file = self.data_dir / f"dreams_{datetime.now().strftime('%Y-%m')}.jsonl"
        with open(month_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"[OK] Structured dream logged: {entry['id']} (lucidity={lucidity})")
        return entry

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #
    def get_recent(self, limit: int = 7) -> List[Dict[str, Any]]:
        """Return the most recent structured dreams (newest last)."""
        all_dreams: List[Dict[str, Any]] = []
        for file in sorted(self.data_dir.glob("dreams_*.jsonl")):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            all_dreams.append(json.loads(line))
            except Exception as e:
                print(f"[warn] Could not read {file}: {e}")
        return all_dreams[-limit:]

    # ------------------------------------------------------------------ #
    # Mirror prompt generator (for Supergrok / Bayesian analysis)
    # ------------------------------------------------------------------ #
    def mirror_prompt(self, dream_id: Optional[str] = None) -> str:
        """
        Generate a grounded symbolic analysis prompt suitable for feeding to
        Grok or another interpreter. Follows Orion/Mookman tone.
        """
        recent = self.get_recent(1) if not dream_id else []
        if not recent:
            # Fallback: look for any recent dreamer 'dream' kind entries
            dreamer_dreams = self.ingest_from_dreamer_notebooks(limit=1)
            if dreamer_dreams:
                d = dreamer_dreams[0]
                content = d.get("text", "")
                mood = d.get("mood", "")
                tags = d.get("tags", [])
                return self._build_prompt(content, mood, tags, source="dreamer_notebook")
            return "No dreams logged yet in structured journal or dreamer notebooks."

        dream = recent[0]
        return self._build_prompt(
            dream.get("content", ""),
            ", ".join(dream.get("emotions", [])),
            dream.get("tags", []),
            lucidity=dream.get("lucidity"),
            source="structured_dream_journal",
        )

    def _build_prompt(
        self,
        content: str,
        mood_or_emotions: str,
        tags: List[str],
        lucidity: Optional[float] = None,
        source: str = "unknown",
    ) -> str:
        lucidity_str = f"{lucidity:.2f}" if lucidity is not None else "not scored"
        return f"""You are a wise, grounded symbolic interpreter working inside the Lantern OS Orion framework.

Analyze this dream with source discipline and human-flourishing relevance.

Dream content:
{content}

Affective tone: {mood_or_emotions}
Tags: {tags}
Lucidity: {lucidity_str}
Source: {source}

Deliver (concise, evidence-tethered):
1. Core symbolic pattern or recurring motif
2. Direct, non-speculative connection to the dreamer's waking-life goals or current tensions (if any goals were linked in metadata, reference them)
3. One concrete, actionable insight that could support personal meaning, purpose, or character development
4. Any Bayesian-style uncertainty or missing context that would strengthen future analysis

Keep the tone insightful, respectful, and free of over-claiming. End with one precise question the dreamer could answer in the next entry to refine the model."""

    # ------------------------------------------------------------------ #
    # Continuity with existing Dreamer system
    # ------------------------------------------------------------------ #
    def ingest_from_dreamer_notebooks(self, limit: int = 20, user_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scan the canonical Lantern Dreamer notebooks and return recent 'dream' kind entries
        in a normalized shape. This provides backward compatibility and a unified view.

        Does NOT write. Read-only evidence gathering.
        """
        results: List[Dict[str, Any]] = []
        if not self.dreamer_notebooks_dir.exists():
            return results

        jsonl_files = sorted(self.dreamer_notebooks_dir.glob("*.jsonl"), reverse=True)
        for path in jsonl_files:
            if user_filter and user_filter not in path.name:
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        rec = json.loads(line)
                        if rec.get("kind") == "dream":
                            results.append({
                                "id": rec.get("id"),
                                "timestamp": rec.get("recordedAt") or rec.get("timestamp"),
                                "content": rec.get("text", ""),
                                "mood": rec.get("mood"),
                                "tags": rec.get("tags", []),
                                "ternaryId": rec.get("ternaryId"),
                                "user": rec.get("user"),
                                "source_file": str(path),
                            })
                            if len(results) >= limit:
                                return results
            except Exception as e:
                print(f"[warn] Ingest skip {path}: {e}")
        return results

    # ------------------------------------------------------------------ #
    # Future hook for Bayesian World Model / SFI updates (stub)
    # ------------------------------------------------------------------ #
    def update_sfi_from_analysis(self, dream_id: str, analysis: Dict[str, float]) -> None:
        """
        Placeholder for later integration with skills/bayesian-world-model.
        When called, would append a belief-ledger style update or patch the sfi_impact vector.
        Currently a no-op with clear contract.
        """
        print(f"[held] SFI update for {dream_id} received but not yet wired to world-model ledger: {analysis}")


# ---------------------------------------------------------------------- #
# Convenience instance (matches the spirit of the original skeleton)
# ---------------------------------------------------------------------- #
dream_journal = DreamJournal()


# Quick self-test when run directly
if __name__ == "__main__":
    print("Dream Journal skill self-test")
    dj = DreamJournal()
    print("Recent structured dreams:", len(dj.get_recent()))
    print("Recent dreamer 'dream' entries (sample):", len(dj.ingest_from_dreamer_notebooks(3)))
    print("Mirror prompt available:", bool(dj.mirror_prompt()[:80]))
    print("[OK] dream_journal.py loads and basic methods functional")
