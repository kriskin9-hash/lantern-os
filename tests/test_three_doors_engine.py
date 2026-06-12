"""Integration tests for Three-Doors Kingdome CSF Backend (Phase 1)."""

import json
import time
import tempfile
from pathlib import Path
import pytest

from src.three_doors_engine import (
    ThreeDoorsEngine, ThreeDoorsGameState, STAGES, AGENTS, ARCHETYPES
)


class TestThreeDoorsGameState:
    """Test in-memory game state."""

    def test_new_state(self):
        state = ThreeDoorsGameState("test-user")
        assert state.user_id == "test-user"
        assert state.loop_number == 1
        assert state.stage_number == 0
        assert state.agent == "lantern"
        assert state.archetype == "seeker"

    def test_state_serialization(self):
        state = ThreeDoorsGameState("test-user")
        state.loop_number = 5
        state.stage_number = 3
        state.agent = "xenon"
        state.symbols = {"pattern1": {"frequency": 2}}

        data = state.to_dict()
        assert data["user_id"] == "test-user"
        assert data["loop"] == 5
        assert data["stage"] == 3
        assert data["agent"] == "xenon"
        assert data["symbols"] == {"pattern1": {"frequency": 2}}

    def test_state_deserialization(self):
        original = ThreeDoorsGameState("test-user")
        original.loop_number = 5
        original.agent = "blinkbug"

        data = original.to_dict()
        restored = ThreeDoorsGameState.from_dict(data)

        assert restored.user_id == "test-user"
        assert restored.loop_number == 5
        assert restored.agent == "blinkbug"


class TestThreeDoorsEngine:
    """Test game engine with CSF backend."""

    @pytest.fixture
    def temp_data_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def engine(self, temp_data_dir):
        # Monkey-patch the engine to use temp directory
        engine = ThreeDoorsEngine("test-user")
        engine.data_dir = Path(temp_data_dir)
        return engine

    def test_new_game_starts_at_stage_0(self, engine):
        scene = engine.start_game()
        assert scene["user_id"] == "test-user"
        assert scene["loop"] == 1
        assert scene["stage"] == 0
        assert scene["stage_name"] == "garden-at-beginning"

    def test_start_game_generates_doors(self, engine):
        scene = engine.start_game()
        assert "doors" in scene
        assert len(scene["doors"]) == 3
        assert all("name" in d and "label" in d for d in scene["doors"])

    def test_choose_door_advances_stage(self, engine):
        engine.start_game()
        scene = engine.choose_door("A")
        assert scene["stage"] == 1
        assert scene["loop"] == 1

    def test_stage_progression(self, engine):
        # Complete one full loop through all 7 stages
        for i in range(len(STAGES)):
            scene = engine.start_game() if i == 0 else scene
            assert scene["stage"] == i
            if i < len(STAGES) - 1:
                scene = engine.choose_door("A")

        # Should wrap back to stage 0 of next loop
        scene = engine.choose_door("A")
        assert scene["loop"] == 2
        assert scene["stage"] == 0

    def test_loop_consolidation(self, engine):
        # Play through one loop
        engine.start_game()
        for _ in range(len(STAGES) - 1):
            engine.choose_door("A")

        # Get state before wrapping
        state_before = engine._load_state()
        assert len(state_before.observations) > 0

        # Choose final door to trigger consolidation
        engine.choose_door("A")

        # Check that symbols were created
        state_after = engine._load_state()
        assert state_after.loop_number == 2
        assert len(state_after.symbols) > 0
        assert len(state_after.observations) == 0  # Cleared for new loop

    def test_csf_file_created(self, engine):
        engine.start_game()
        csf_path = engine._get_csf_path()
        assert csf_path.exists(), f"CSF file not created at {csf_path}"

    def test_csf_file_size_constraint(self, engine):
        # Play multiple loops
        for loop in range(5):
            engine.start_game()
            for stage in range(len(STAGES) - 1):
                engine.choose_door("A")
            engine.choose_door("A")  # Complete loop

        # Check file size is reasonable
        csf_path = engine._get_csf_path()
        file_size_kb = csf_path.stat().st_size / 1024
        # Should be under 10KB (accounting for CSF overhead + JSON + symbols)
        assert file_size_kb < 10, f"CSF file too large: {file_size_kb:.2f}KB"

    def test_agent_filters_doors(self, engine):
        # Test that agent changes door order
        engine.agent = "blinkbug"
        scene_blinkbug = engine.start_game()
        doors_blinkbug = [d["label"] for d in scene_blinkbug["doors"]]

        engine.agent = "lantern"
        scene_lantern = engine.start_game()
        doors_lantern = [d["label"] for d in scene_lantern["doors"]]

        # Blinkbug rotates doors
        assert doors_blinkbug != doors_lantern

    def test_archetype_persistence(self, engine):
        state = engine._load_state()
        state.archetype = "explorer"
        engine._save_state(state)

        # Reload and verify
        state2 = engine._load_state()
        assert state2.archetype == "explorer"

    def test_symbol_tracking(self, engine):
        engine.agent = "xenon"
        engine.start_game()

        # Play through one full loop to trigger consolidation
        for _ in range(len(STAGES) - 1):
            engine.choose_door("A")

        # Complete the loop (triggers consolidation)
        engine.choose_door("A")

        # Record the symbol
        state = engine._load_state()
        expected_key = "archetype=seeker_agent=xenon"
        assert expected_key in state.symbols

    def test_reset_clears_state(self, engine):
        engine.start_game()
        engine.choose_door("A")

        csf_path = engine._get_csf_path()
        assert csf_path.exists()

        engine.reset()
        assert not csf_path.exists()

        # New game after reset
        scene = engine.start_game()
        assert scene["loop"] == 1
        assert scene["stage"] == 0

    def test_api_response_format(self, engine):
        scene = engine.start_game()
        response = engine.to_api_response(scene)

        # Check required fields
        assert response["user_id"] == "test-user"
        assert response["loop"] == 1
        assert response["stage"] == 0
        assert "text" in response
        assert "doors" in response
        assert "image_available" in response

    def test_json_backup_created(self, engine):
        engine.start_game()
        json_path = engine._get_json_backup_path()
        assert json_path.exists()

        # Verify backup is valid JSON
        with open(json_path) as f:
            data = json.load(f)
        assert data["user_id"] == "test-user"

    def test_multiple_users_isolation(self, temp_data_dir):
        # Create two engines for different users
        engine1 = ThreeDoorsEngine("user1")
        engine1.data_dir = Path(temp_data_dir)

        engine2 = ThreeDoorsEngine("user2")
        engine2.data_dir = Path(temp_data_dir)

        # Play as different users
        scene1 = engine1.start_game()
        engine1.choose_door("A")

        scene2 = engine2.start_game()
        engine2.choose_door("B")

        # States should be isolated
        state1 = engine1._load_state()
        state2 = engine2._load_state()

        assert state1.user_id == "user1"
        assert state2.user_id == "user2"
        assert state1.stage_number == 1
        assert state2.stage_number == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
