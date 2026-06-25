"""
Tests for the three-doors-game skill module (#1099)

Run: python -m pytest tests/test_three_doors_skill.py -q --tb=short
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_scene_graph():
    return {
        "start": {
            "id": "start",
            "name": "The Beginning",
            "prose": "Three doors wait.",
            "doors": ["moss-entry", "arcade"],
        },
        "moss-entry": {
            "id": "moss-entry",
            "name": "The Moss Door",
            "prose": "Green light. A fox.",
            "doors": ["burrow", "sunken-bell"],
            "fox_present": True,
        },
        "arcade": {
            "id": "arcade",
            "name": "The Arcade Door",
            "prose": "Neon bleeds under the edge.",
            "doors": ["start"],
        },
        "burrow": {
            "id": "burrow",
            "name": "The Burrow Door",
            "prose": "Small and warm.",
            "doors": ["start"],
        },
        "sunken-bell": {
            "id": "sunken-bell",
            "name": "The Sunken Bell Door",
            "prose": "Half underwater.",
            "doors": ["start"],
        },
    }


def _default_state():
    return {
        "current_scene": "start",
        "history": [],
        "fox_present": False,
        "images_only": False,
        "notes": "",
        "created": "2026-06-24T00:00:00",
        "updated": "2026-06-24T00:00:00",
    }


# Import after defining helpers so we can mock paths
import sys
import importlib

# We need to import the module; it reads real files.
# Patch the scene graph and player state paths to use in-memory data.

@pytest.fixture(autouse=True)
def mock_fs(tmp_path, monkeypatch):
    """Redirect scene graph + player state to tmp_path for isolation."""
    scene_path = tmp_path / "scenes.json"
    state_path = tmp_path / "player-state.json"

    scene_path.write_text(
        json.dumps({"version": "test", "scenes": _mock_scene_graph()}),
        encoding="utf-8",
    )
    # Don't pre-create state_path — let load_player_state use defaults

    monkeypatch.setattr(_mod, "_SCENE_GRAPH_PATH", scene_path)
    monkeypatch.setattr(_mod, "_PLAYER_STATE_PATH", state_path)
    return tmp_path


import importlib.util, pathlib as _pl
_skill_path = _pl.Path(__file__).parent.parent / "skills" / "three-doors-game" / "three_doors_game.py"
_spec = importlib.util.spec_from_file_location("three_doors_game", _skill_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

load_scene_graph = _mod.load_scene_graph
get_scene = _mod.get_scene
list_scene_ids = _mod.list_scene_ids
load_player_state = _mod.load_player_state
save_player_state = _mod.save_player_state
get_active_scene = _mod.get_active_scene
list_choices = _mod.list_choices
enter_scene = _mod.enter_scene
reset_game = _mod.reset_game
set_images_only = _mod.set_images_only
export_csf = _mod.export_csf


# ── load_scene_graph ──────────────────────────────────────────────────────────

def test_load_scene_graph_returns_dict():
    graph = load_scene_graph()
    assert isinstance(graph, dict)
    assert "start" in graph
    assert "moss-entry" in graph


def test_load_scene_graph_has_expected_scenes():
    graph = load_scene_graph()
    for key in ["start", "moss-entry", "arcade", "burrow"]:
        assert key in graph


# ── get_scene ─────────────────────────────────────────────────────────────────

def test_get_scene_returns_scene_dict():
    scene = get_scene("moss-entry")
    assert isinstance(scene, dict)
    assert "doors" in scene


def test_get_scene_raises_on_unknown():
    with pytest.raises(KeyError):
        get_scene("nonexistent-door-xyz")


def test_get_scene_includes_fox_field():
    scene = get_scene("moss-entry")
    assert scene.get("fox_present") is True


# ── list_scene_ids ────────────────────────────────────────────────────────────

def test_list_scene_ids_is_sorted():
    ids = list_scene_ids()
    assert ids == sorted(ids)


def test_list_scene_ids_contains_start():
    assert "start" in list_scene_ids()


# ── load_player_state ─────────────────────────────────────────────────────────

def test_load_player_state_returns_defaults_when_no_file():
    state = load_player_state()
    assert state["current_scene"] == "start"
    assert state["history"] == []
    assert state["fox_present"] is False


def test_load_player_state_has_required_keys():
    state = load_player_state()
    for key in ["current_scene", "history", "fox_present", "images_only", "notes"]:
        assert key in state


# ── save / load round-trip ────────────────────────────────────────────────────

def test_save_and_reload_state(tmp_path):
    state = load_player_state()
    state["current_scene"] = "arcade"
    state["notes"] = "test note"
    save_player_state(state)
    reloaded = load_player_state()
    assert reloaded["current_scene"] == "arcade"
    assert reloaded["notes"] == "test note"


# ── get_active_scene ──────────────────────────────────────────────────────────

def test_get_active_scene_returns_tuple():
    scene_id, scene = get_active_scene()
    assert isinstance(scene_id, str)
    assert isinstance(scene, dict)


def test_get_active_scene_default_is_start():
    scene_id, _ = get_active_scene()
    assert scene_id == "start"


# ── list_choices ──────────────────────────────────────────────────────────────

def test_list_choices_returns_list():
    choices = list_choices()
    assert isinstance(choices, list)


def test_list_choices_has_doors_at_start():
    choices = list_choices()
    assert len(choices) > 0


def test_list_choices_each_has_name():
    choices = list_choices()
    for c in choices:
        assert "name" in c or "id" in c


# ── enter_scene ───────────────────────────────────────────────────────────────

def test_enter_scene_moves_to_destination():
    state = enter_scene("moss-entry")
    assert state["current_scene"] == "moss-entry"


def test_enter_scene_records_history():
    enter_scene("moss-entry")
    state = load_player_state()
    assert "start" in state["history"]


def test_enter_scene_sets_fox_present():
    state = enter_scene("moss-entry")
    assert state["fox_present"] is True


def test_enter_scene_raises_on_unknown():
    with pytest.raises(KeyError):
        enter_scene("nonexistent-xyz")


# ── reset_game ────────────────────────────────────────────────────────────────

def test_reset_game_returns_to_start():
    enter_scene("moss-entry")
    state = reset_game()
    assert state["current_scene"] == "start"


def test_reset_game_clears_history():
    enter_scene("moss-entry")
    state = reset_game()
    assert state["history"] == []


def test_reset_game_clears_fox():
    enter_scene("moss-entry")
    reset_game()
    state = load_player_state()
    assert state["fox_present"] is False


# ── set_images_only ───────────────────────────────────────────────────────────

def test_set_images_only_true():
    state = set_images_only(True)
    assert state["images_only"] is True


def test_set_images_only_false():
    set_images_only(True)
    state = set_images_only(False)
    assert state["images_only"] is False


# ── export_csf ────────────────────────────────────────────────────────────────

def test_export_csf_returns_string():
    result = export_csf("TestPlayer")
    assert isinstance(result, str)


def test_export_csf_contains_csf_ingest_block():
    result = export_csf("TestPlayer")
    assert "```csf-ingest" in result
    assert "```" in result


def test_export_csf_contains_player_name():
    result = export_csf("Jane Smith")
    assert "Jane Smith" in result


def test_export_csf_contains_active_scene():
    result = export_csf()
    assert "start" in result.lower() or "beginning" in result.lower()


def test_export_csf_contains_available_doors():
    result = export_csf()
    # Should mention available doors at 'start'
    assert "door" in result.lower()


def test_export_csf_after_scene_change():
    enter_scene("moss-entry")
    result = export_csf("Player")
    assert "moss" in result.lower() or "Moss" in result
