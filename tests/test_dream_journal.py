"""
Test suite for skills/dream_journal

Covers:
- DreamJournal (structured logging, retrieval, mirror prompts, notebook ingest)
- BayesianFallacyDetector (heuristic fallacy detection)
- DreamCharacter (memory persistence, speak)
- CognitiveJournal (facade wiring talk / analyze / status)
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add skills/dream_journal to path so imports resolve without package setup
_SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills" / "dream_journal"
sys.path.insert(0, str(_SKILLS_DIR))

from dream_journal import DreamJournal
from cognitive_layer import (
    BayesianFallacyDetector,
    DreamCharacter,
    CognitiveJournal,
    get_cognitive_journal,
)


# --------------------------------------------------------------------------- #
# DreamJournal tests
# --------------------------------------------------------------------------- #

class TestDreamJournal:

    @pytest.fixture
    def journal(self, tmp_path):
        """Fresh DreamJournal using a temp directory."""
        dj = DreamJournal(data_dir=str(tmp_path / "dream_journal"))
        # Point dreamer notebooks at a temp location too
        dj.dreamer_notebooks_dir = tmp_path / "dreamer" / "notebooks"
        return dj

    def test_log_dream_returns_entry(self, journal):
        entry = journal.log_dream("I flew over a silver city.", lucidity=0.7)
        assert entry["content"] == "I flew over a silver city."
        assert entry["lucidity"] == 0.7
        assert entry["source"] == "dream_journal_skill"
        assert "id" in entry
        assert "timestamp" in entry

    def test_log_dream_normalizes_lucidity_above_one(self, journal):
        entry = journal.log_dream("Test", lucidity=8)
        assert entry["lucidity"] == 0.8

    def test_log_dream_caps_lucidity(self, journal):
        entry = journal.log_dream("Test", lucidity=15)
        assert entry["lucidity"] == 1.0

    def test_log_dream_defaults(self, journal):
        entry = journal.log_dream("Bare dream.")
        assert entry["lucidity"] == 0.0
        assert entry["emotions"] == []
        assert entry["tags"] == []
        assert entry["linked_goals"] == []
        assert entry["sfi_impact"] == {"meaning": 0.0, "purpose": 0.0, "character": 0.0}

    def test_log_dream_persists_to_jsonl(self, journal):
        journal.log_dream("Persisted dream.")
        month_file = journal.data_dir / f"dreams_{__import__('datetime').datetime.now().strftime('%Y-%m')}.jsonl"
        assert month_file.exists()
        lines = [json.loads(line) for line in month_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) == 1
        assert lines[0]["content"] == "Persisted dream."

    def test_get_recent_respects_limit(self, journal):
        for i in range(5):
            journal.log_dream(f"Dream {i}")
        recent = journal.get_recent(limit=3)
        assert len(recent) == 3
        # Should be newest last
        assert recent[-1]["content"] == "Dream 4"

    def test_mirror_prompt_with_no_data(self, journal):
        prompt = journal.mirror_prompt()
        assert "No dreams logged yet" in prompt

    def test_mirror_prompt_from_structured_entry(self, journal):
        journal.log_dream("I met a fox in the snow.", emotions=["wonder"], tags=["snow", "fox"])
        prompt = journal.mirror_prompt()
        assert "fox in the snow" in prompt
        assert "wonder" in prompt
        assert "snow" in prompt
        assert "structured_dream_journal" in prompt

    def test_ingest_from_dreamer_notebooks_empty(self, journal):
        assert journal.ingest_from_dreamer_notebooks() == []

    def test_ingest_from_dreamer_notebooks_reads_dream_kind(self, journal):
        notebook_dir = journal.dreamer_notebooks_dir
        notebook_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "id": "n1",
            "timestamp": "2026-01-01T00:00:00",
            "kind": "dream",
            "text": "Notebook dream text",
            "mood": "melancholy",
            "tags": ["stars"],
        }
        notebook_file = notebook_dir / "user-123.jsonl"
        notebook_file.write_text(json.dumps(record) + "\n", encoding="utf-8")

        results = journal.ingest_from_dreamer_notebooks(limit=5)
        assert len(results) == 1
        assert results[0]["content"] == "Notebook dream text"
        assert results[0]["mood"] == "melancholy"

    def test_ingest_skips_non_dream_kind(self, journal):
        notebook_dir = journal.dreamer_notebooks_dir
        notebook_dir.mkdir(parents=True, exist_ok=True)
        record = {"id": "n1", "kind": "note", "text": "Just a note"}
        notebook_file = notebook_dir / "user-456.jsonl"
        notebook_file.write_text(json.dumps(record) + "\n", encoding="utf-8")
        assert journal.ingest_from_dreamer_notebooks() == []


# --------------------------------------------------------------------------- #
# BayesianFallacyDetector tests
# --------------------------------------------------------------------------- #

class TestBayesianFallacyDetector:

    @pytest.fixture
    def detector(self):
        return BayesianFallacyDetector()

    def test_false_dichotomy(self, detector):
        result = detector.detect("You are either with us or against us.")
        types = [r["fallacy"] for r in result]
        assert "False Dichotomy" in types

    def test_appeal_to_emotion(self, detector):
        result = detector.detect("It feels terrifying and beautiful at once.")
        types = [r["fallacy"] for r in result]
        assert "Appeal To Emotion" in types

    def test_hasty_generalization(self, detector):
        result = detector.detect("Everyone always lies.")
        types = [r["fallacy"] for r in result]
        assert "Hasty Generalization" in types

    def test_circular_reasoning(self, detector):
        result = detector.detect("It is true because I said so because it is true.")
        types = [r["fallacy"] for r in result]
        assert "Circular Reasoning" in types

    def test_no_fallacy_in_plain_text(self, detector):
        result = detector.detect("The cat sat on the mat.")
        assert result == []

    def test_probability_above_threshold(self, detector):
        result = detector.detect("You are either with us or against us.")
        for r in result:
            assert r["probability"] >= detector.threshold

    def test_notes_present(self, detector):
        result = detector.detect("It is terrifying.")
        for r in result:
            assert "note" in r
            assert len(r["note"]) > 0


# --------------------------------------------------------------------------- #
# DreamCharacter tests
# --------------------------------------------------------------------------- #

class TestDreamCharacter:

    @pytest.fixture
    def char(self, tmp_path):
        return DreamCharacter("The Fox", "wise, cautious", tmp_path)

    def test_remember_adds_memory(self, char):
        char.remember("Saw a red tower.")
        assert len(char.memory) == 1
        assert char.memory[0]["event"] == "Saw a red tower."
        assert "timestamp" in char.memory[0]

    def test_remember_persists_to_disk(self, char):
        char.remember("Event one")
        assert char.save_path.exists()
        data = json.loads(char.save_path.read_text(encoding="utf-8"))
        assert data["name"] == "The Fox"
        assert len(data["memory"]) == 1

    def test_load_memory_restores_state(self, tmp_path):
        char = DreamCharacter("The Fox", "wise, cautious", tmp_path)
        char.remember("Old memory")
        del char

        char2 = DreamCharacter("The Fox", "wise, cautious", tmp_path)
        assert len(char2.memory) == 1
        assert char2.memory[0]["event"] == "Old memory"

    def test_speak_fox_format(self, char):
        text = char.speak("What do you seek?")
        assert "The Fox tilts its head" in text
        assert "What do you seek?" in text

    def test_speak_tower_format(self, tmp_path):
        tower = DreamCharacter("The Old Tower", "ancient, watchful", tmp_path)
        text = tower.speak("Echo...")
        assert "The Old Tower stands silent" in text
        assert "Echo..." in text

    def test_speak_generic_format(self, tmp_path):
        generic = DreamCharacter("Raven", "mysterious", tmp_path)
        text = generic.speak("Caw.")
        assert "Raven says:" in text

    def test_memory_hint_after_remembering(self, char):
        char.remember("First talk")
        text = char.speak("Hello")
        assert "1 memories" in text

    def test_source_in_memory(self, char):
        char.remember("Test", source="user_42")
        assert char.memory[0]["source"] == "user_42"


# --------------------------------------------------------------------------- #
# CognitiveJournal tests
# --------------------------------------------------------------------------- #

class TestCognitiveJournal:

    @pytest.fixture
    def cog(self, tmp_path):
        return CognitiveJournal(data_dir=str(tmp_path / "dreams"))

    def test_analyze_returns_list(self, cog):
        result = cog.analyze("Everyone always lies.")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_analyze_empty(self, cog):
        result = cog.analyze("Just a plain sentence.")
        assert result == []

    def test_talk_fox(self, cog):
        response = cog.talk("fox", "Who are you?", user_id="tester")
        assert "The Fox" in response
        assert "Who are you?" in response
        assert len(cog.characters["fox"].memory) == 1
        assert cog.characters["fox"].memory[0]["source"] == "tester"

    def test_talk_tower(self, cog):
        response = cog.talk("tower", "What do you watch?")
        assert "The Old Tower" in response

    def test_talk_unknown_character(self, cog):
        response = cog.talk("dragon", "Rawr")
        assert "Unknown character" in response
        assert "fox, tower" in response.lower()

    def test_character_status(self, cog):
        cog.talk("fox", "Hello")
        status = cog.character_status()
        assert "Dream Characters:" in status
        assert "The Fox: 1 memories" in status
        assert "The Old Tower: 0 memories" in status

    def test_characters_persisted(self, tmp_path):
        cog1 = CognitiveJournal(data_dir=str(tmp_path / "dreams"))
        cog1.talk("fox", "Persistent memory test")
        del cog1

        cog2 = CognitiveJournal(data_dir=str(tmp_path / "dreams"))
        assert len(cog2.characters["fox"].memory) == 1
        assert cog2.characters["fox"].memory[0]["event"] == "Persistent memory test"


# --------------------------------------------------------------------------- #
# get_cognitive_journal singleton tests
# --------------------------------------------------------------------------- #

class TestSingleton:

    def test_singleton_returns_same_instance(self, tmp_path, monkeypatch):
        # Override the default data dir so we don't pollute the repo
        monkeypatch.setattr(
            "cognitive_layer._cognitive_journal",
            CognitiveJournal(data_dir=str(tmp_path / "cog")),
        )
        a = get_cognitive_journal()
        b = get_cognitive_journal()
        assert a is b
