"""Tests for CSF/CADD Memory Engine."""

import json
import os
import tempfile

import pytest

# Allow importing from src/csf
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from csf.memory_engine import (
    CubePartition,
    MemoryEngine,
    MemoryRecord,
    PrivacyScope,
    Tier,
    create_correction,
    create_entity,
    create_skill,
    create_trace,
    _next_cube,
)


class TestMemoryRecord:
    def test_checksum_computed(self):
        rec = create_trace("hello", "sess_1")
        assert rec.checksum
        assert rec.verify()

    def test_promotion_creates_new_record(self):
        trace = create_trace("hello", "sess_1", confidence=1.0)
        anchor = trace.promote(
            to_tier=Tier.ANCHOR,
            new_content={"text": "hello", "anchor_type": "keystone"},
            confidence=0.85,
            agent="keystone_agent",
        )
        assert anchor.tier == Tier.ANCHOR
        assert anchor.promoted_from == trace.memory_id
        assert "trace→anchor" in anchor.promotion_chain
        assert anchor.agents == ["keystone_agent"]
        assert anchor.confidence == 0.85

    def test_privacy_scope_enum(self):
        rec = create_trace("x", "s", privacy_scope=PrivacyScope.PRIVATE)
        assert rec.privacy_scope == PrivacyScope.PRIVATE


class TestNextCube:
    def test_trace_stays_raw(self):
        assert _next_cube(CubePartition.RAW, Tier.TRACE) == CubePartition.RAW

    def test_anchor_goes_refined(self):
        assert _next_cube(CubePartition.RAW, Tier.ANCHOR) == CubePartition.REFINED

    def test_skill_goes_canon(self):
        assert _next_cube(CubePartition.REFINED, Tier.SKILL) == CubePartition.CANON

    def test_export_goes_archive(self):
        assert _next_cube(CubePartition.CANON, Tier.EXPORT) == CubePartition.ARCHIVE


class TestMemoryEngine:
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            rec = create_trace("test", "sess_1", tags=["a", "b"])
            path = engine.write(rec)
            assert path.exists()
            loaded = engine.read(rec.memory_id)
            assert loaded is not None
            assert loaded.tier == Tier.TRACE
            assert loaded.verify()

    def test_query_by_tier(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            engine.write(create_trace("a", "s1"))
            engine.write(create_trace("b", "s2"))
            ent = create_entity("The Door", "symbol", "A threshold between worlds")
            engine.write(ent)
            traces = engine.query(tier=Tier.TRACE)
            assert len(traces) == 2
            entities = engine.query(tier=Tier.ENTITY)
            assert len(entities) == 1

    def test_query_by_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            engine.write(create_trace("x", "s1", tags=["door", "star"]))
            engine.write(create_trace("y", "s2", tags=["mirror"]))
            results = engine.query(tags=["door"])
            assert len(results) == 1

    def test_promote_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            trace = create_trace("I found a lantern in the fog", "sess_3")
            engine.write(trace)
            anchor = engine.promote(
                trace.memory_id,
                to_tier=Tier.ANCHOR,
                agent="convergence_loop",
                new_content={
                    "text": "I found a lantern in the fog",
                    "anchor_type": "lantern",
                    "attested_by": ["convergence_loop"],
                    "attestation_count": 1,
                },
                confidence=0.82,
            )
            assert anchor.tier == Tier.ANCHOR
            assert anchor.cube_partition == CubePartition.REFINED
            loaded = engine.read(anchor.memory_id)
            assert loaded is not None

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = MemoryEngine(base_path=tmp)
            engine.write(create_trace("a", "s1"))
            engine.write(create_trace("b", "s2"))
            engine.write(create_entity("Fog", "place", "A recurring location"))
            stats = engine.stats()
            assert stats["total"] == 3
            assert stats["by_tier"]["trace"] == 2
            assert stats["by_tier"]["entity"] == 1


class TestFactories:
    def test_create_entity(self):
        ent = create_entity("The Door", "symbol", "A threshold")
        assert ent.tier == Tier.ENTITY
        assert ent.content["name"] == "The Door"
        assert ent.cube_partition == CubePartition.REFINED

    def test_create_skill(self):
        skill = create_skill(
            "Dream Reflection",
            "Reflect on dream content and suggest symbolic interpretations",
            "skills/dream_reflection/SKILL.md",
        )
        assert skill.tier == Tier.SKILL
        assert skill.cube_partition == CubePartition.CANON
        assert not skill.content["tested"]

    def test_create_correction(self):
        trace = create_trace("old text", "sess_1")
        corr = create_correction(
            trace,
            corrected_field="text",
            new_value="corrected text",
            reason="typo",
            corrected_by="user",
        )
        assert corr.tier == Tier.CORRECTION
        assert corr.content["old_value"] == "old text"
        assert corr.content["new_value"] == "corrected text"
