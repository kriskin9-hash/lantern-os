"""Integration tests for Three-Doors Kingdome CSF Backend (Phase 1 + Phase 4)."""

import tempfile
from pathlib import Path
import pytest

from src.three_doors_engine import ThreeDoorsEngine, STAGES, SCENES


class TestThreeDoorsEngine:
    """Test game engine with CSF backend."""

    @pytest.fixture
    def temp_data_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def engine(self, temp_data_dir):
        return ThreeDoorsEngine("test-user", data_dir=temp_data_dir)

    def test_new_game_starts_at_stage_0(self, engine):
        scene = engine.start_game()
        assert scene["scene_key"] == STAGES[0]
        assert scene["stage_index"] == 0
        assert scene["loop_count"] == 0

    def test_start_game_generates_doors(self, engine):
        scene = engine.start_game()
        assert "doors" in scene
        assert len(scene["doors"]) == 3
        assert all("name" in d and "label" in d for d in scene["doors"])

    def test_start_game_returns_text(self, engine):
        scene = engine.start_game()
        assert "text" in scene
        assert len(scene["text"]) > 50

    def test_choose_door_advances_stage(self, engine):
        engine.start_game()
        scene = engine.choose_door("A")
        assert scene["stage_index"] == 1
        assert scene["loop_count"] == 0

    def test_stage_progression(self, engine):
        engine.start_game()
        for expected in range(1, len(STAGES)):
            scene = engine.choose_door("A")
            assert scene["stage_index"] == expected

        # Final stage wrap: loop 1 begins at stage 0
        scene = engine.choose_door("A")
        assert scene["loop_count"] == 1
        assert scene["stage_index"] == 0

    def test_loop_consolidation_creates_symbols(self, engine):
        engine.start_game()
        for _ in range(len(STAGES)):
            engine.choose_door("A")
        assert len(engine.cube.symbols) > 0

    def test_loop_consolidation_clears_observations(self, engine):
        engine.start_game()
        for _ in range(len(STAGES)):
            engine.choose_door("A")
        # Observations are pruned after consolidation
        assert len(engine.cube.observations) == 0

    def test_csf_file_created(self, engine):
        engine.start_game()
        csf_path = engine.cube._path()
        assert csf_path.exists(), f"CSF file not created at {csf_path}"

    def test_csf_file_size_constraint_after_5_loops(self, engine):
        """5 loops should stay well under 10 KB."""
        engine.start_game()
        for _ in range(5 * len(STAGES)):
            engine.choose_door("A")
        csf_path = engine.cube._path()
        size_kb = csf_path.stat().st_size / 1024
        assert size_kb < 10, f"CSF file too large after 5 loops: {size_kb:.2f} KB"

    def test_csf_file_size_constraint_after_100_loops(self, engine):
        """CSF must stay under 10 KB after 100 loops (baseline consolidates)."""
        engine.start_game()
        for _ in range(100 * len(STAGES)):
            engine.choose_door("A")
        csf_path = engine.cube._path()
        size_kb = csf_path.stat().st_size / 1024
        assert size_kb < 10, f"CSF file too large after 100 loops: {size_kb:.2f} KB"

    def test_reset_clears_state(self, engine):
        engine.start_game()
        for _ in range(len(STAGES)):
            engine.choose_door("A")
        # After one full loop there should be symbols
        assert len(engine.cube.symbols) > 0
        assert engine.cube.loop_count == 1

        # reset() wipes the cube and starts a fresh game
        scene = engine.reset()
        assert scene["loop_count"] == 0
        assert scene["stage_index"] == 0
        assert len(engine.cube.symbols) == 0

    def test_api_response_format(self, engine):
        scene = engine.start_game()
        response = engine.to_api_response(scene)
        for key in ("scene_key", "text", "doors", "image_available", "loop_count", "stage_index"):
            assert key in response, f"Missing key: {key}"

    def test_multiple_users_isolation(self, temp_data_dir):
        engine1 = ThreeDoorsEngine("user1", data_dir=temp_data_dir)
        engine2 = ThreeDoorsEngine("user2", data_dir=temp_data_dir)

        engine1.start_game()
        engine1.choose_door("A")
        engine1.choose_door("A")  # stage 2

        engine2.start_game()
        engine2.choose_door("A")  # stage 1

        # Reload from disk to verify each user's CSF is independent
        fresh1 = ThreeDoorsEngine("user1", data_dir=temp_data_dir)
        fresh2 = ThreeDoorsEngine("user2", data_dir=temp_data_dir)
        fresh1.start_game()
        fresh2.start_game()

        assert fresh1.cube.stage_index == 2
        assert fresh2.cube.stage_index == 1
        assert fresh1.cube.user_id == "user1"
        assert fresh2.cube.user_id == "user2"

    def test_symbol_tracking_with_agent(self, engine):
        engine.agent = "xenon"
        engine.start_game()
        for _ in range(len(STAGES)):
            engine.choose_door("A")
        # Agent affinity symbol crystallises when ≥ half the choices use the agent
        assert any("xenon" in k for k in engine.cube.symbols), (
            f"No xenon symbol found. Symbols: {list(engine.cube.symbols)}"
        )

    def test_choose_door_invalid_returns_none(self, engine):
        engine.start_game()
        assert engine.choose_door("not a real door name here") is None

    def test_archetype_defaults_to_seeker(self, engine):
        engine.start_game()
        assert engine.cube.archetype == "seeker"

    def test_agent_field_propagates_into_observations(self, engine):
        engine.agent = "lantern"
        engine.start_game()
        engine.choose_door("A")
        obs = engine.cube.observations
        assert len(obs) == 1
        assert obs[0]["agent"] == "lantern"


class TestSceneTextQuality:
    """Verify scene text for all 7 stages is rich narration, not stubs (Phase 4)."""

    def test_all_stage_scenes_defined(self):
        for stage in STAGES:
            assert stage in SCENES, f"Stage {stage!r} not defined in SCENES"

    def test_all_stage_texts_are_substantial(self):
        for stage in STAGES:
            text = SCENES[stage].get("text", "")
            assert len(text) > 100, f"Stage {stage!r} text too short: {len(text)} chars"

    def test_stage_texts_have_multiple_sentences(self):
        for stage in STAGES:
            # Strip markdown emphasis markers before splitting
            raw = SCENES[stage].get("text", "").replace("*", "").replace("_", "")
            sentences = [s.strip() for s in raw.split(".") if s.strip()]
            assert len(sentences) >= 2, f"Stage {stage!r} appears single-sentence"

    def test_stage_specific_keywords(self):
        """Each stage contains its identifying lore keywords."""
        expected = {
            "kingdome-garden": ["King", "Garden", "throne"],
            "cloverfield": ["Cloverfield", "shini", "luck"],
            "future-doors": ["future", "orchard", "door"],
            "xp-door": ["XP", "bliss", "glitch"],
            "xenon-convergence": ["Xenon", "choice", "path"],
            "sigil-city": ["Sigil", "City", "door"],
            "fog-door-return": ["Fog", "Garden", "return"],
        }
        for stage, keywords in expected.items():
            text = SCENES[stage].get("text", "").lower()
            found = sum(1 for kw in keywords if kw.lower() in text)
            assert found >= 2, (
                f"Stage {stage!r} missing lore keywords — expected ≥2 of {keywords}"
            )

    def test_all_stages_have_3_doors(self):
        for stage in STAGES:
            doors = SCENES[stage].get("doors", [])
            assert len(doors) == 3, f"Stage {stage!r} has {len(doors)} doors, expected 3"

    def test_text_length_reasonable_for_display(self):
        """Text should fit in a mobile view (< 1500 chars per stage)."""
        for stage in STAGES:
            text = SCENES[stage].get("text", "")
            assert len(text) < 1500, f"Stage {stage!r} text too long: {len(text)} chars"

    def test_42_agent_stage_combinations_via_engine(self, tmp_path):
        """All 6 agents × 7 stages: engine produces non-empty text for every combination."""
        agents = ["lantern", "blinkbug", "keystone", "waterfall", "xenon", "founder"]
        count = 0
        for agent in agents:
            engine = ThreeDoorsEngine("combo-test", data_dir=tmp_path)
            engine.agent = agent
            scene = engine.start_game()
            # Walk all 7 stages
            for i in range(len(STAGES)):
                text = scene["text"]
                assert isinstance(text, str) and len(text) > 60, (
                    f"Agent {agent}, stage {i}: empty or too-short text"
                )
                count += 1
                if i < len(STAGES) - 1:
                    scene = engine.choose_door("A")
            engine.reset()
        assert count == 42, f"Expected 42 combinations, got {count}"
