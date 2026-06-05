"""
Lantern OS CSF/CADD Memory Engine
Mirrors MemOS tiers: Trace, Correction, Anchor, Entity, Relation, Ritual, Skill, Export.

Design principles:
- Local-first: all records stored in JSONL under data/csf_memory/
- Inspectable: every record is human-readable JSON with full lineage
- Cube-partitioned: raw → refined → canon → archive
- Confidence-calibrated: Brier-style 0.0–1.0 scores on every record
- Privacy-scoped: private | internal | public | export_safe

Promotion flow:
    trace → anchor (attestation)
    trace → correction (human or agent fixes)
    anchor → entity (extracted into world model)
    entity → relation (linked to other entities)
    anchor → ritual (repeated pattern recognized)
    ritual → skill (crystallized, tested, reusable)
    skill → export (cleared for external release)
"""

import hashlib
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Tier(str, Enum):
    TRACE = "trace"
    CORRECTION = "correction"
    ANCHOR = "anchor"
    ENTITY = "entity"
    RELATION = "relation"
    RITUAL = "ritual"
    SKILL = "skill"
    EXPORT = "export"


class PrivacyScope(str, Enum):
    PRIVATE = "private"
    INTERNAL = "internal"
    PUBLIC = "public"
    EXPORT_SAFE = "export_safe"


class CubePartition(str, Enum):
    RAW = "raw"
    REFINED = "refined"
    CANON = "canon"
    ARCHIVE = "archive"


@dataclass
class MemoryRecord:
    memory_id: str
    tier: Tier
    created_at: str
    updated_at: str
    content: Dict[str, Any]
    confidence: float = 0.0
    privacy_scope: PrivacyScope = PrivacyScope.PRIVATE
    source_surface: str = ""
    promoted_from: Optional[str] = None
    promotion_chain: List[str] = field(default_factory=list)
    cube_partition: CubePartition = CubePartition.RAW
    tags: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)
    checksum: str = ""
    vector_embedding: Optional[List[float]] = None

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        """SHA-256 of canonical JSON (excludes checksum itself)."""
        payload = {k: v for k, v in asdict(self).items() if k != "checksum"}
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify(self) -> bool:
        return self.checksum == self._compute_checksum()

    def promote(
        self,
        to_tier: Tier,
        new_content: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        privacy_scope: Optional[PrivacyScope] = None,
        agent: str = "system",
    ) -> "MemoryRecord":
        """Create a promoted copy with updated tier and lineage."""
        chain = list(self.promotion_chain)
        chain.append(f"{self.tier.value}→{to_tier.value}")
        return MemoryRecord(
            memory_id=f"{self.memory_id}_{to_tier.value}_{_ts()}",
            tier=to_tier,
            created_at=self.created_at,
            updated_at=_now(),
            content=new_content or dict(self.content),
            confidence=confidence if confidence is not None else max(self.confidence - 0.05, 0.0),
            privacy_scope=privacy_scope or self.privacy_scope,
            source_surface=self.source_surface,
            promoted_from=self.memory_id,
            promotion_chain=chain,
            cube_partition=_next_cube(self.cube_partition, to_tier),
            tags=list(self.tags),
            agents=list(self.agents) + [agent],
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tier"] = self.tier.value
        d["privacy_scope"] = self.privacy_scope.value
        d["cube_partition"] = self.cube_partition.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryRecord":
        d = dict(d)
        d["tier"] = Tier(d.pop("tier"))
        d["privacy_scope"] = PrivacyScope(d.pop("privacy_scope"))
        d["cube_partition"] = CubePartition(d.pop("cube_partition"))
        return cls(**d)


class MemoryEngine:
    """Local-first cube-partitioned memory store."""

    def __init__(self, base_path: Optional[str] = None):
        self.base = Path(base_path or os.environ.get("CSF_MEMORY_PATH", "data/csf_memory"))
        self.base.mkdir(parents=True, exist_ok=True)
        for part in CubePartition:
            (self.base / part.value).mkdir(exist_ok=True)

    def _path(self, record: MemoryRecord) -> Path:
        tier_dir = self.base / record.cube_partition.value / record.tier.value
        tier_dir.mkdir(parents=True, exist_ok=True)
        return tier_dir / f"{record.memory_id}.json"

    def _registry_path(self, partition: CubePartition) -> Path:
        return self.base / f"{partition.value}.jsonl"

    def write(self, record: MemoryRecord) -> Path:
        record.updated_at = _now()
        record.checksum = record._compute_checksum()
        path = self._path(record)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        self._append_registry(record)
        return path

    def _append_registry(self, record: MemoryRecord):
        reg = self._registry_path(record.cube_partition)
        with open(reg, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False, default=str) + "\n")

    def read(self, memory_id: str) -> Optional[MemoryRecord]:
        for part in CubePartition:
            for tier in Tier:
                path = self.base / part.value / tier.value / f"{memory_id}.json"
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        return MemoryRecord.from_dict(json.load(f))
        return None

    def query(
        self,
        tier: Optional[Tier] = None,
        partition: Optional[CubePartition] = None,
        privacy_scope: Optional[PrivacyScope] = None,
        tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        source_surface: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        results: List[MemoryRecord] = []
        partitions = [partition] if partition else list(CubePartition)
        for part in partitions:
            reg = self._registry_path(part)
            if not reg.exists():
                continue
            with open(reg, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = MemoryRecord.from_dict(json.loads(line))
                    except Exception:
                        continue
                    if tier and rec.tier != tier:
                        continue
                    if privacy_scope and rec.privacy_scope != privacy_scope:
                        continue
                    if min_confidence and rec.confidence < min_confidence:
                        continue
                    if source_surface and rec.source_surface != source_surface:
                        continue
                    if tags and not any(t in rec.tags for t in tags):
                        continue
                    results.append(rec)
                    if len(results) >= limit:
                        return results
        return results

    def promote(
        self,
        memory_id: str,
        to_tier: Tier,
        agent: str = "system",
        new_content: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        privacy_scope: Optional[PrivacyScope] = None,
    ) -> MemoryRecord:
        """Promote a record to a higher tier."""
        rec = self.read(memory_id)
        if not rec:
            raise ValueError(f"Memory not found: {memory_id}")
        promoted = rec.promote(
            to_tier=to_tier,
            new_content=new_content,
            confidence=confidence,
            privacy_scope=privacy_scope,
            agent=agent,
        )
        self.write(promoted)
        return promoted

    def stats(self) -> Dict[str, Any]:
        """Cube and tier coverage statistics."""
        stats = {"total": 0, "by_partition": {}, "by_tier": {}, "by_privacy": {}}
        for part in CubePartition:
            reg = self._registry_path(part)
            if not reg.exists():
                continue
            with open(reg, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = MemoryRecord.from_dict(json.loads(line))
                    except Exception:
                        continue
                    stats["total"] += 1
                    stats["by_partition"][part.value] = stats["by_partition"].get(part.value, 0) + 1
                    stats["by_tier"][rec.tier.value] = stats["by_tier"].get(rec.tier.value, 0) + 1
                    stats["by_privacy"][rec.privacy_scope.value] = stats["by_privacy"].get(rec.privacy_scope.value, 0) + 1
        return stats


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _next_cube(current: CubePartition, target_tier: Tier) -> CubePartition:
    """Determine cube partition based on tier promotion."""
    if target_tier == Tier.EXPORT:
        return CubePartition.ARCHIVE
    if target_tier in (Tier.SKILL, Tier.RITUAL):
        return CubePartition.CANON
    if target_tier in (Tier.ENTITY, Tier.RELATION, Tier.ANCHOR):
        return CubePartition.REFINED
    return current


def create_trace(
    text: str,
    session_id: str,
    surface: str = "dream-chat",
    role: str = "user",
    confidence: float = 1.0,
    privacy_scope: PrivacyScope = PrivacyScope.PRIVATE,
    tags: Optional[List[str]] = None,
) -> MemoryRecord:
    """Factory: create a raw trace record."""
    return MemoryRecord(
        memory_id=f"trace_{uuid.uuid4().hex[:8]}_{_ts()}",
        tier=Tier.TRACE,
        created_at=_now(),
        updated_at=_now(),
        content={
            "text": text,
            "session_id": session_id,
            "timestamp": _now(),
            "surface": surface,
            "role": role,
            "raw_input": text,
        },
        confidence=confidence,
        privacy_scope=privacy_scope,
        source_surface=surface,
        tags=tags or [],
    )


def create_correction(
    original: MemoryRecord,
    corrected_field: str,
    new_value: Any,
    reason: str,
    corrected_by: str = "user",
    confidence: float = 0.9,
) -> MemoryRecord:
    """Factory: create a correction record from an existing memory."""
    return original.promote(
        to_tier=Tier.CORRECTION,
        new_content={
            "original_memory_id": original.memory_id,
            "corrected_field": corrected_field,
            "old_value": original.content.get(corrected_field),
            "new_value": new_value,
            "reason": reason,
            "corrected_by": corrected_by,
            "correction_type": "factual",
        },
        confidence=confidence,
        agent=corrected_by,
    )


def create_entity(
    name: str,
    entity_type: str,
    description: str,
    confidence: float = 0.7,
    privacy_scope: PrivacyScope = PrivacyScope.INTERNAL,
    source_trace_id: Optional[str] = None,
) -> MemoryRecord:
    """Factory: create an entity from scratch or promoted from trace."""
    rec = MemoryRecord(
        memory_id=f"ent_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}",
        tier=Tier.ENTITY,
        created_at=_now(),
        updated_at=_now(),
        content={
            "name": name,
            "entity_type": entity_type,
            "description": description,
            "aliases": [],
            "first_seen_at": _now(),
            "occurrence_count": 1,
        },
        confidence=confidence,
        privacy_scope=privacy_scope,
        cube_partition=CubePartition.REFINED,
    )
    if source_trace_id:
        rec.promoted_from = source_trace_id
        rec.promotion_chain = [f"trace→entity"]
    return rec


def create_skill(
    name: str,
    capability: str,
    implementation_ref: str,
    confidence: float = 0.8,
    privacy_scope: PrivacyScope = PrivacyScope.INTERNAL,
    source_ritual_id: Optional[str] = None,
) -> MemoryRecord:
    """Factory: create a crystallized skill record."""
    rec = MemoryRecord(
        memory_id=f"skill_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}",
        tier=Tier.SKILL,
        created_at=_now(),
        updated_at=_now(),
        content={
            "name": name,
            "capability": capability,
            "implementation_ref": implementation_ref,
            "tested": False,
            "test_results": [],
            "crystallized_at": _now(),
        },
        confidence=confidence,
        privacy_scope=privacy_scope,
        cube_partition=CubePartition.CANON,
    )
    if source_ritual_id:
        rec.promoted_from = source_ritual_id
        rec.promotion_chain = [f"ritual→skill"]
    return rec
