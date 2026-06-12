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
        # Test that agent changes door order (by name, not label, since labels get reassigned)
        engine.agent = "blinkbug"
        scene_blinkbug = engine.start_game()
        doors_blinkbug = [d["name"] for d in scene_blinkbug["doors"]]

        engine.agent = "lantern"
        scene_lantern = engine.start_game()
        doors_lantern = [d["name"] for d in scene_lantern["doors"]]

        # Blinkbug rotates doors (different order by name)
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


class TestPhase4NarrationIntegration:
    """Test Phase 4: Narration Integration for stages 2, 3, 5 and agent flavor appending."""

    @pytest.fixture
    def temp_data_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def engine(self, temp_data_dir):
        engine = ThreeDoorsEngine("test-user")
        engine.data_dir = Path(temp_data_dir)
        return engine

    def test_generate_text_stages_2_3_5_have_rich_narration(self, engine):
        """Verify stages 2, 3, 5 have >100 char narration (not stubs)."""
        state = ThreeDoorsGameState("test-user")
        state.agent = "lantern"

        # Stage 2: future-doors
        text_stage_2 = engine._generate_text("future-doors", state)
        assert len(text_stage_2) > 100, f"Stage 2 narration too short: {len(text_stage_2)} chars"
        assert "Branches of possibility" in text_stage_2
        assert "futures" in text_stage_2.lower() or "unwritten" in text_stage_2.lower()

        # Stage 3: xp-door
        text_stage_3 = engine._generate_text("xp-door", state)
        assert len(text_stage_3) > 100, f"Stage 3 narration too short: {len(text_stage_3)} chars"
        assert "Windows XP" in text_stage_3 or "XP" in text_stage_3
        assert "liminal" in text_stage_3.lower() or "nostalgia" in text_stage_3.lower()

        # Stage 5: sigil-city-of-doors
        text_stage_5 = engine._generate_text("sigil-city-of-doors", state)
        assert len(text_stage_5) > 100, f"Stage 5 narration too short: {len(text_stage_5)} chars"
        assert "Synthesis hub" in text_stage_5 or "King" in text_stage_5
        assert "doors" in text_stage_5.lower()

    def test_agent_flavor_narration_appends_all_agents(self, engine):
        """Test all 6 agent flavors append to narration without truncation."""
        state = ThreeDoorsGameState("test-user")

        for agent in AGENTS:
            state.agent = agent
            text = engine._generate_text("future-doors", state)

            # Verify agent flavor is appended
            assert text.endswith((".",".",".")) or len(text) > 150, f"Agent {agent} flavor not properly appended"

            # Verify minimum length (base narration + agent flavor)
            assert len(text) > 100, f"Text for agent {agent} too short: {len(text)} chars"

            # Verify agent flavor is present (check for agent-specific suffix)
            agent_flavors = {
                "lantern": "Light guides the way",
                "blinkbug": "glitches playfully",
                "keystone": "Doors align",
                "waterfall": "Water flows",
                "xenon": "possibilities shimmer",
                "founder": "root of all",
            }
            flavor = agent_flavors[agent]
            assert flavor in text, f"Agent flavor for {agent} not found in: {text}"

    def test_agent_flavor_narration_with_symbols(self, engine):
        """Test agent flavor appends correctly with symbol tracking."""
        state = ThreeDoorsGameState("test-user")
        state.agent = "xenon"
        state.symbols = {
            "archetype=seeker_agent=xenon": {"frequency": 3, "loop": 2},
            "archetype=explorer_agent=founder": {"frequency": 1, "loop": 1},
        }

        text = engine._generate_text("sigil-city-of-doors", state)

        # Verify symbol count is appended
        assert "crystallized patterns" in text
        assert "2 crystallized patterns" in text

        # Verify length is not truncated
        assert len(text) > 150, f"Text with symbols too short: {len(text)} chars"

    def test_no_stub_text_remains_in_all_stages(self, engine):
        """Verify no 1-sentence stubs remain. All 7 stages have rich narration."""
        state = ThreeDoorsGameState("test-user")
        state.agent = "lantern"

        stub_indicators = {
            "garden-at-beginning": ["The King's opening poem", "seed", "bloom"],  # OK - rich
            "present-day": ["Cloverfield", "scent"],  # OK - rich
            "future-doors": ["shimmer", "futures", "spirals"],  # Verify rich content
            "xp-door": ["Windows XP", "liminal", "pixels"],  # Verify rich content
            "xenon-starship": ["Convergence", "timelines", "throne"],  # OK - rich
            "sigil-city-of-doors": ["Synthesis", "Fractal", "King returns"],  # Verify rich content
            "fog-door-return": ["Fog coils", "escape", "spiral"],  # OK - rich
        }

        for stage in STAGES:
            text = engine._generate_text(stage, state)

            # Remove agent flavor suffix to test base narration
            agent_flavor_end = text.rfind('.')
            base_text = text[:agent_flavor_end + 1] if agent_flavor_end > 0 else text

            # Verify base narration is substantial (not a one-liner stub)
            # A proper narration should be multiple sentences or multi-line
            sentences = [s.strip() for s in base_text.split('.') if s.strip()]
            assert len(sentences) >= 2, f"Stage {stage} appears to be single sentence: {base_text}"
            assert len(base_text) > 100, f"Stage {stage} base narration too short: {len(base_text)} chars"

            # Verify stage-specific content (multiple keywords)
            if stage in stub_indicators:
                indicators = stub_indicators[stage]
                found_count = sum(1 for indicator in indicators if indicator.lower() in text.lower())
                assert found_count >= 2, f"Stage {stage} missing rich content. Found {found_count}/{len(indicators)} keywords. Text: {text}"

    def test_narration_character_count_reasonable_for_display(self, engine):
        """Verify character counts are reasonable for UI display (not too short, not too long)."""
        state = ThreeDoorsGameState("test-user")
        state.agent = "waterfall"

        for stage in STAGES:
            text = engine._generate_text(stage, state)

            # Min: meaningful narration (> 60 chars)
            assert len(text) > 60, f"Stage {stage} narration too short: {len(text)} chars"

            # Max: readable on mobile (< 500 chars, to fit in ~8 lines at 60 chars/line)
            assert len(text) < 500, f"Stage {stage} narration too long: {len(text)} chars"

    def test_all_agents_with_all_stages_no_errors(self, engine):
        """Comprehensive test: all 6 agents x all 7 stages = 42 combinations."""
        state = ThreeDoorsGameState("test-user")

        combination_count = 0
        for stage in STAGES:
            for agent in AGENTS:
                state.agent = agent
                text = engine._generate_text(stage, state)

                # Basic sanity checks
                assert isinstance(text, str), f"Stage {stage}, Agent {agent}: not a string"
                assert len(text) > 0, f"Stage {stage}, Agent {agent}: empty text"
                assert len(text) > 60, f"Stage {stage}, Agent {agent}: too short ({len(text)} chars)"

                combination_count += 1

        assert combination_count == 42, f"Expected 42 combinations, got {combination_count}"

    def test_agent_flavor_consistency_across_stages(self, engine):
        """Verify each agent's flavor suffix is consistent across all stages."""
        state = ThreeDoorsGameState("test-user")

        agent_expected_suffix = {
            "lantern": "Light guides the way.",
            "blinkbug": "Something glitches playfully.",
            "keystone": "Doors align with intention.",
            "waterfall": "Water flows through choices.",
            "xenon": "All possibilities shimmer.",
            "founder": "The root of all lies here.",
        }

        for agent, expected_suffix in agent_expected_suffix.items():
            state.agent = agent

            # Test across multiple stages (not just one)
            for stage in ["garden-at-beginning", "future-doors", "sigil-city-of-doors"]:
                text = engine._generate_text(stage, state)
                assert expected_suffix in text, \
                    f"Agent {agent} suffix missing in stage {stage}. Text: {text}"

    def test_symbol_tracking_affects_narration(self, engine):
        """Verify symbols affect narration text (crystallized patterns count appended)."""
        state = ThreeDoorsGameState("test-user")
        state.agent = "founder"

        # Without symbols
        text_no_symbols = engine._generate_text("future-doors", state)
        assert "crystallized patterns" not in text_no_symbols

        # With 3 symbols
        state.symbols = {
            "pattern1": {"frequency": 1, "loop": 1},
            "pattern2": {"frequency": 2, "loop": 2},
            "pattern3": {"frequency": 1, "loop": 1},
        }
        text_with_symbols = engine._generate_text("future-doors", state)
        assert "crystallized patterns" in text_with_symbols
        assert "3 crystallized patterns" in text_with_symbols

        # Verify symbol count increases with more symbols
        assert len(text_with_symbols) > len(text_no_symbols)

    def test_narration_in_full_scene_generation(self, engine):
        """Integration test: verify narration appears correctly in full scene response."""
        engine.start_game()
        scene = engine.start_game()

        # Scene should have text field
        assert "text" in scene
        text = scene["text"]

        # Should contain narration + agent flavor + optional symbols
        assert len(text) > 100
        assert isinstance(text, str)

        # Verify it's not just a stub
        assert any(keyword in text for keyword in
                   ["King", "doors", "light", "glitch", "water", "root", "fog", "possibility"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
