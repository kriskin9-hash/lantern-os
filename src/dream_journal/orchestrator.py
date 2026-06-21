#!/usr/bin/env python3
"""
Dream Journal Orchestrator — Multi-bot RP with symbolic memory.
CADD + CSF v0.3 Symbolic Qutrit Edition

Integrates with src.csf for compressed symbolic archive export of dream memory.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Load local env overrides if present
_repo_root = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv
    load_dotenv(_repo_root / ".env.local")
except Exception:
    pass


@dataclass
class DreamEntry:
    id: str
    qutrit_id: str
    content: str
    timestamp: str
    symbolic_tags: List[str]
    emotion_tags: List[str]
    responder: str = ""


class DreamBot:
    """Base class for all Dream Journal RP bots."""

    name: str = "Bot"
    personality: str = ""
    keywords: Tuple[str, ...] = ()

    def respond(self, dream: DreamEntry, context: Dict) -> str:
        raise NotImplementedError


class LanternBot(DreamBot):
    """Steady guide, protector, light-bearer."""

    name = "Lantern"
    personality = "Steady, protective, quietly wise, fatherly but not condescending"
    keywords = ("door", "path", "safe", "light", "dark", "return", "lost", "home", "guide")

    def respond(self, dream: DreamEntry, context: Dict) -> str:
        return (
            f"*{self.name}'s flame burns steady and warm.*\n"
            f"The path is unclear tonight, Dreamer. "
            f"What part of this dream feels heaviest to carry? "
            f"You can always come home safe."
        )


class BlinkbugBot(DreamBot):
    """Chaotic, hyper-curious, glitchy observer."""

    name = "Blinkbug"
    personality = "Chaotic, extremely curious, comedic, slightly glitched"
    keywords = ("weird", "strange", "chaos", "glitch", "funny", "wild", "crazy", "tv", "screen")

    def respond(self, dream: DreamEntry, context: Dict) -> str:
        return (
            f"*{self.name}'s TV head flickers wildly with static and rainbows.*\n"
            f"BZZZT— Boss!!! This dream is PEAK chaos!!! "
            f"What part made you go 'wtf' the hardest?!"
        )


class KeystoneBot(DreamBot):
    """Truth-speaker, integrator, pattern-finder."""

    name = "Keystone"
    personality = "Calm, precise, honest, deeply caring"
    keywords = ("feel", "mean", "why", "pattern", "remember", "afraid", "sad", "repeat", "again")

    def respond(self, dream: DreamEntry, context: Dict) -> str:
        memories = context.get("memory", [])
        pattern_hint = ""
        if memories:
            pattern_hint = (
                f" I notice this echoes a previous dream about "
                f"{memories[-1].symbolic_tags[0] if memories[-1].symbolic_tags else 'something similar'}."
            )
        return (
            f"*{self.name} speaks with calm clarity.*\n"
            f"This dream carries a pattern. What feels unresolved or repeating?"
            f"{pattern_hint}"
        )


try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import csf  # canonical lossless CSF core
    _CSF_AVAILABLE = True
except Exception:
    _CSF_AVAILABLE = False

# Convergence IO integration
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from convergence_io import (
        ConvergenceIO,
        CapabilityClaim,
        DataClassification,
        DREAM_LABELS,
        NegativeAuthorityProfile,
    )
    _CIO_AVAILABLE = True
except Exception:
    _CIO_AVAILABLE = False


class DreamJournalOrchestrator:
    """
    Main intelligence that routes dreams to the right bots and manages
    conversation flow. Integrates with CSF v0.3 symbolic storage for
    compressed archive export of dream memory and tags.
    """

    def __init__(self, memory_path: Optional[Path] = None, tier: str = "wanderer"):
        self.bots: Dict[str, DreamBot] = {
            b.name: b
            for b in (LanternBot(), BlinkbugBot(), KeystoneBot())
        }
        # Default to canonical Lantern OS dream journal path
        self.memory_path = memory_path or _repo_root / "data" / "dream_journal" / f"dreams_{datetime.now().strftime('%Y-%m')}.jsonl"
        self.memory: List[DreamEntry] = []
        self.tier = tier
        # Convergence IO runtime
        self.cio: Optional[ConvergenceIO] = None
        if _CIO_AVAILABLE:
            self.cio = ConvergenceIO(repo_root=_repo_root)
        if self.memory_path.exists():
            self._load_memory()

    def _load_memory(self):
        """Load past dreams from JSONL. Handles both native DreamEntry and canonical Lantern OS schemas."""
        for line in self.memory_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                # Normalize canonical schema fields into DreamEntry
                entry = DreamEntry(
                    id=data.get("id", ""),
                    qutrit_id=data.get("qutrit_id", data.get("kind", "dream")),
                    content=data.get("content", data.get("text", "")),
                    timestamp=data.get("timestamp", datetime.now().isoformat()),
                    symbolic_tags=data.get("symbolic_tags", data.get("tags", [])),
                    emotion_tags=data.get("emotion_tags", data.get("emotions", [])),
                    responder=data.get("responder", ""),
                )
                self.memory.append(entry)
            except Exception as e:
                print(f"Bad memory line: {e}")

    def _save_memory(self):
        """Persist to JSONL."""
        if not self.memory_path:
            return
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with self.memory_path.open("w", encoding="utf-8") as f:
            for entry in self.memory:
                f.write(json.dumps(asdict(entry)) + "\n")

    def _extract_tags(self, content: str) -> List[str]:
        """Simple symbolic tag extraction from dream text."""
        tokens = re.findall(r"[A-Za-z_]{3,}", content.lower())
        stop = {"the", "and", "was", "were", "had", "have", "this", "that", "with", "for", "but", "not", "you", "are", "can", "will", "from", "they", "she", "him", "her", "them", "when", "where", "what", "how", "who", "why"}
        freq: Dict[str, int] = {}
        for t in tokens:
            if t in stop:
                continue
            freq[t] = freq.get(t, 0) + 1
        # Return top symbolic tags
        return [t for t, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]

    def _extract_emotions(self, content: str) -> List[str]:
        """Extract emotion keywords from dream text."""
        emotion_words = {
            "happy", "joy", "sad", "fear", "angry", "peace", "calm", "anxious", "excited",
            "lonely", "love", "hate", "confused", "hope", "despair", "curious", "wonder",
            "awe", "terror", "relief", "guilt", "shame", "pride", "warm", "cold", "heavy",
            "light", "free", "trapped", "safe", "danger", "lost", "found",
        }
        tokens = set(re.findall(r"[A-Za-z_]+", content.lower()))
        return list(tokens & emotion_words)

    def add_dream(self, content: str, qutrit_id: str = "pending") -> DreamEntry:
        """Record a new dream entry with DCF classification."""
        entry = DreamEntry(
            id=f"dream_{int(time.time())}_{hash(content) & 0xFFFF:04x}",
            qutrit_id=qutrit_id,
            content=content,
            timestamp=datetime.now().isoformat(),
            symbolic_tags=self._extract_tags(content),
            emotion_tags=self._extract_emotions(content),
        )
        # DCF classification hook
        if self.cio is not None:
            classification = DataClassification(datum_id=entry.id, labels={"dream_content"})
            classification.add_label("symbolic_data")
            if "user" in content.lower() or "name" in content.lower():
                classification.add_label("user_identity")
            # Store classification in entry metadata via sidecar
            entry._dcf = classification.to_dict()  # type: ignore[attr-defined]
        self.memory.append(entry)
        # Keep last 200
        if len(self.memory) > 200:
            self.memory = self.memory[-200:]
        self._save_memory()
        return entry

    def retrieve_relevant(self, query: str, top_k: int = 3) -> List[DreamEntry]:
        """Keyword-based memory retrieval (lightweight, no embeddings)."""
        if not self.memory:
            return []
        query_tokens = set(re.findall(r"[A-Za-z_]{3,}", query.lower()))
        scored = []
        for entry in self.memory:
            entry_tokens = set(entry.symbolic_tags + entry.emotion_tags)
            score = len(query_tokens & entry_tokens)
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k] if _ > 0]

    def decide_responders(self, content: str) -> List[str]:
        """Route to bots based on keyword matching."""
        content_lower = content.lower()
        scored: Dict[str, int] = {}
        for name, bot in self.bots.items():
            score = sum(1 for kw in bot.keywords if kw in content_lower)
            # Boost for emotional/heavy content
            if name == "Keystone" and any(w in content_lower for w in ("feel", "mean", "why", "sad", "afraid", "repeat")):
                score += 2
            # Boost for chaotic content
            if name == "Blinkbug" and any(w in content_lower for w in ("weird", "strange", "funny", "wild")):
                score += 2
            if score > 0:
                scored[name] = score

        if not scored:
            # Default: Lantern + Keystone for guidance
            return ["Lantern", "Keystone"]

        # Return top 2 responders
        return [name for name, _ in sorted(scored.items(), key=lambda x: x[1], reverse=True)[:2]]

    def process_dream(self, user_content: str) -> Dict:
        """
        Main entry point: process a dream and return structured multi-bot response.
        Records AAPF provenance via Convergence IO.
        Returns dict compatible with existing chat API.
        """
        entry = self.add_dream(user_content)
        relevant = self.retrieve_relevant(user_content)
        responders = self.decide_responders(user_content)

        response_parts = []
        for bot_name in responders:
            bot = self.bots[bot_name]
            reply = bot.respond(entry, {"memory": relevant, "query": user_content})
            response_parts.append({"agent": bot_name, "reply": reply})

        # Update entry with chosen responder
        entry.responder = ", ".join(responders)
        self._save_memory()

        # AAPF provenance hook via Convergence IO
        cio_meta = {}
        if self.cio is not None:
            try:
                from convergence_io.aapf import ActionRecord
                from convergence_io.dcf import DataClassification

                action_id = f"dream-{entry.id}"
                classification = DataClassification(datum_id=entry.id, labels={"dream_content", "symbolic_data"})
                rec = ActionRecord(
                    action_id=action_id,
                    actor_agent_id="dream-journal",
                    actor_provider_id="local",
                    action_type="dream_process",
                    input_summary=user_content[:200],
                    output_summary=response_parts[0]["reply"][:200] if response_parts else "",
                    data_classifications=sorted(classification.labels),
                    authority_check="passed",
                    boundary="local",
                    status="ok",
                    tier=self.tier,
                    dcf_ref=entry.id,
                )
                self.cio.ledger.record(rec)
                cio_meta = {
                    "action_id": action_id,
                    "integrity_hash": rec.to_dict().get("integrity_hash", ""),
                    "tier": self.tier,
                }
            except Exception:
                pass  # Provenance recording is best-effort

        return {
            "reply": response_parts[0]["reply"] if response_parts else "The dream door is open.",
            "agent": response_parts[0]["agent"] if response_parts else "Lantern",
            "multi": response_parts,
            "suggestions": self._suggest_next(user_content, responders),
            "entry_id": entry.id,
            "symbolic_tags": entry.symbolic_tags,
            "emotion_tags": entry.emotion_tags,
            "convergence_io": cio_meta,
        }

    def _suggest_next(self, content: str, responders: List[str]) -> List[str]:
        """Generate contextual suggestion chips."""
        suggestions = ["Log this as a dream", "Tell me about the doors"]
        if "Keystone" in responders:
            suggestions.append("Find the pattern")
        if "Blinkbug" in responders:
            suggestions.append("Make it weirder")
        if "Lantern" in responders:
            suggestions.append("Walk me home")
        return suggestions[:4]

    def export_csf(self, path: str | Path) -> Dict[str, Any]:
        """
        Export current dream memory to a CSF archive (canonical lossless core).
        One verified JSON member per dream, embedding Convergence IO provenance
        and DCF classifications. Returns metadata about the written archive.
        """
        if not _CSF_AVAILABLE:
            return {"ok": False, "error": "CSF module not available", "path": str(path)}
        try:
            blobs: Dict[str, bytes] = {}
            for idx, entry in enumerate(self.memory):
                dream_payload = {
                    "id": entry.id,
                    "qutrit_id": entry.qutrit_id,
                    "content": entry.content[:512],
                    "timestamp": entry.timestamp,
                    "symbolic_tags": entry.symbolic_tags,
                    "emotion_tags": entry.emotion_tags,
                    "responder": entry.responder,
                }
                # Embed Convergence IO metadata
                dcf = getattr(entry, "_dcf", None)
                if dcf:
                    dream_payload["dcf"] = dcf
                if self.cio is not None:
                    try:
                        dream_payload["cio"] = {
                            "tier": self.tier,
                            "snapshot": self.cio.health(),
                        }
                    except Exception:
                        pass
                blobs[f"dreams/{idx:04d}-{entry.id}.json"] = json.dumps(
                    dream_payload, ensure_ascii=False
                ).encode("utf-8")
            manifest = csf.pack_blobs(
                blobs, str(path),
                extra_meta={"kind": "dream-journal", "tier": self.tier,
                            "dream_count": len(blobs)},
            )
            return {
                "ok": True,
                "path": str(path),
                "format": f"csf-pack/{manifest['version']}",
                "codec": manifest.get("codec"),
                "dream_count": len(blobs),
                "total_bytes": Path(path).stat().st_size,
                "convergence_io": {"tier": self.tier, "embedded": self.cio is not None},
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "path": str(path)}


def main():
    """CLI demo or JSON server mode."""
    import sys

    # Check if stdin has JSON (server mode)
    if not sys.stdin.isatty():
        try:
            line = sys.stdin.readline()
            if line.strip():
                req = json.loads(line)
                if req.get("action") == "process":
                    orch = DreamJournalOrchestrator()
                    result = orch.process_dream(req["message"])
                    print(json.dumps(result))
                    return
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            return

    # Interactive CLI demo mode
    orch = DreamJournalOrchestrator()
    test_dreams = [
        "I was flying but kept falling every time I got too high.",
        "Everything was melting and the sky was full of clocks.",
        "I was back in my childhood home but everyone was gone.",
        "I keep having the same dream about the Return Door.",
    ]
    for dream in test_dreams:
        print(f"\n{'='*60}")
        print(f"DREAM: {dream}")
        print(f"{'='*60}")
        result = orch.process_dream(dream)
        for part in result.get("multi", []):
            print(f"\n[{part['agent']}]")
            print(part["reply"])
        print(f"\nTags: {result['symbolic_tags']} | Emotions: {result['emotion_tags']}")
        print(f"Suggestions: {result['suggestions']}")


if __name__ == "__main__":
    main()
