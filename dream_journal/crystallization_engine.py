"""
Lantern Crystallization Engine v1.1
Native CSF-native loop with externalized prompts.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class DreamCrystallizationEngine:
    def __init__(self, base_path: str = "dream_journal"):
        self.base = Path(base_path)
        self.raw_dir = self.base / "raw"
        self.csf_dir = self.base / "csf"
        self.crystallized_dir = self.csf_dir / "crystallized"
        self.prompt_dir = self.base / "templates" / "prompts"

        for p in [self.raw_dir, self.crystallized_dir]:
            p.mkdir(parents=True, exist_ok=True)

        # Load prompts
        self.prompt_parse = (self.prompt_dir / "parse.md").read_text()
        self.prompt_reflect = (self.prompt_dir / "reflect.md").read_text()
        self.prompt_crystallize = (self.prompt_dir / "crystallize.md").read_text()

    async def process_new_dream(self, user_id: int, raw_text: str, character: str = "default"):
        # 1. Observe
        dream_csf = self._create_raw_csf(user_id, raw_text, character)

        # 2. Execute (Parse)
        parsed = self._parse_dream(dream_csf)

        # 3. Reflect
        relevant = self._find_relevant_memories(parsed)

        # 4. Crystallize
        new_skill = None
        if self._should_crystallize(relevant):
            new_skill = await self._crystallize(parsed, relevant)
            if new_skill:
                self._save_crystallized_skill(new_skill)

        # 5. Reuse
        return {
            "dream_id": dream_csf["id"],
            "parsed": parsed,
            "relevant_skills": relevant,
            "new_skill": new_skill,
            "response_context": self._build_response_context(parsed, relevant)
        }

    def _create_raw_csf(self, user_id: int, text: str, character: str) -> Dict:
        dream_id = f"dream_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        csf = {
            "id": dream_id,
            "user_id": user_id,
            "character": character,
            "timestamp": datetime.utcnow().isoformat(),
            "raw_text": text,
            "format": "CSF-raw-v1"
        }
        (self.raw_dir / f"{dream_id}.jsonl").write_text(json.dumps(csf) + "\n")
        return csf

    def _parse_dream(self, dream_csf: Dict) -> Dict:
        # In full version: call LLM with self.prompt_parse
        text = dream_csf["raw_text"].lower()
        return {
            "symbols": [w for w in ["lantern", "door", "fog", "light", "shadow"] if w in text],
            "emotions": [w for w in ["fear", "joy", "longing", "calm"] if w in text],
            "anchors": ["God Fog Door"] if "fog" in text or "door" in text else []
        }

    def _find_relevant_memories(self, parsed: Dict) -> List[Dict]:
        # In full version: semantic search over crystallized/
        return []

    def _should_crystallize(self, relevant: List[Dict]) -> bool:
        return True  # v1: always attempt

    async def _crystallize(self, parsed: Dict, relevant: List[Dict]) -> Optional[Dict]:
        skill = {
            "id": f"skill_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.utcnow().isoformat(),
            "symbols": parsed.get("symbols", []),
            "anchors": parsed.get("anchors", []),
            "insight": "When fog appears near a door, pause and name one anchor before proceeding.",
            "version": 1,
            "format": "CSF-crystallized-v1"
        }
        return skill

    def _save_crystallized_skill(self, skill: Dict):
        path = self.crystallized_dir / f"{skill['id']}.csf.json"
        path.write_text(json.dumps(skill, indent=2))

    def _build_response_context(self, parsed: Dict, relevant: List[Dict]) -> str:
        symbols = ", ".join(parsed.get("symbols", []))
        return f"Relevant symbols: {symbols}. Recall crystallized patterns where available."


engine = DreamCrystallizationEngine()