"""
Lantern Crystallization Engine (LCE) v1.0
CSF-native, lightweight, self-improving memory engine for Dream Journal.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid


class LanternCrystallizationEngine:
    def __init__(self, model: str = "qwen3:14b", base_path: str = "dream_journal"):
        self.model = model
        self.base = Path(base_path)
        self.raw_dir = self.base / "raw"
        self.csf_dir = self.base / "csf"
        self.crystallized_dir = self.csf_dir / "crystallized"
        self.symbols_dir = self.csf_dir / "symbols"
        self.anchors_dir = self.csf_dir / "anchors"
        self.index_dir = self.csf_dir / "index"

        for p in [self.raw_dir, self.crystallized_dir, self.symbols_dir, self.anchors_dir, self.index_dir]:
            p.mkdir(parents=True, exist_ok=True)

    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # 1. Observe
    def create_raw_dream_csf(self, raw_text: str, metadata: Optional[Dict] = None) -> Dict:
        dream_id = self._generate_id("dream")
        csf = {
            "concept": "dream_entry",
            "id": dream_id,
            "date": datetime.utcnow().isoformat(),
            "raw_text": raw_text,
            "symbols": [],
            "emotions": [],
            "people": [],
            "anchors": [],
            "crystallized": False,
            "metadata": metadata or {}
        }
        return csf

    def save_csf(self, csf: Dict, relative_path: str):
        path = self.csf_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(csf, indent=2), encoding="utf-8")

    # 2. Parse
    async def parse_dream(self, dream_csf: Dict) -> Dict:
        # Placeholder — in production this calls the LLM with the parse prompt
        text = dream_csf["raw_text"].lower()
        parsed = {
            "symbols": [s for s in ["lantern_head", "god_fog_door", "mermaid_courtney"] if s in text],
            "emotions": [e for e in ["awe", "curiosity", "unease", "fear", "joy"] if e in text],
            "anchors": [a for a in ["convergence", "return_safe", "god_fog_door"] if a in text],
        }
        return parsed

    # 3. Reflect
    async def reflect(self, parsed: Dict) -> List[Dict]:
        # Placeholder — semantic search over crystallized skills
        return []

    def should_crystallize(self, relevant: List[Dict]) -> bool:
        return True  # v1: always attempt crystallization

    # 4. Crystallize
    async def crystallize(self, parsed: Dict, relevant: List[Dict]) -> Dict:
        skill_id = self._generate_id("skill")
        skill = {
            "concept": "crystallized_skill",
            "id": skill_id,
            "name": f"skill_{datetime.utcnow().strftime('%Y%m%d')}",
            "type": "symbolic_anchor",
            "description": "Auto-generated symbolic insight from dream.",
            "triggers": parsed.get("anchors", []),
            "insight": "When this pattern appears, pause and name the dominant anchor.",
            "usage_prompt": "What is trying to emerge through this symbol right now?",
            "relations": parsed.get("symbols", []),
            "version": 1,
            "last_updated": datetime.utcnow().isoformat(),
            "confidence": 0.75
        }
        return skill

    def save_crystallized_skill(self, skill: Dict):
        path = self.crystallized_dir / f"{skill['id']}.csf.json"
        path.write_text(json.dumps(skill, indent=2), encoding="utf-8")

    # 5. Index & Reuse
    def update_index(self, dream_csf: Dict, skill: Optional[Dict] = None):
        index_file = self.index_dir / "dream_index.jsonl"
        entry = {
            "dream_id": dream_csf["id"],
            "timestamp": dream_csf["date"],
            "symbols": dream_csf.get("symbols", []),
            "anchors": dream_csf.get("anchors", []),
            "crystallized_skill": skill["id"] if skill else None
        }
        with open(index_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    async def generate_contextual_response(self, parsed: Dict, relevant: List[Dict], skill: Optional[Dict]) -> Dict:
        context = {
            "symbols": parsed.get("symbols", []),
            "anchors": parsed.get("anchors", []),
            "crystallized_skill": skill,
            "relevant_past_skills": [r.get("id") for r in relevant]
        }
        return context

    async def process_dream(self, raw_text: str, metadata: Optional[Dict] = None):
        # Full loop
        dream_csf = self.create_raw_dream_csf(raw_text, metadata)
        self.save_csf(dream_csf, f"dreams/{dream_csf['id']}.csf")

        parsed = await self.parse_dream(dream_csf)
        relevant = await self.reflect(parsed)

        skill = None
        if self.should_crystallize(relevant):
            skill = await self.crystallize(parsed, relevant)
            self.save_crystallized_skill(skill)

        self.update_index(dream_csf, skill)

        return await self.generate_contextual_response(parsed, relevant, skill)


# Global instance
engine = LanternCrystallizationEngine()