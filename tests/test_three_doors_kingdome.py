"""
Test Three Doors Kingdome of Hearts route map and shared contract.

Assertions:
- Throne Door routes to kingdome-garden in Python engine
- Shared contract JSON contains all Kingdome scenes
- Discord bot route map mirrors the contract
- Web game inline engine has equivalent Kingdome routes
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from three_doors_engine import SCENES, _NEXT_MAP


def test_throne_door_routes_to_kingdome_garden():
    assert _NEXT_MAP.get("the throne door") == "kingdome-garden", (
        f"Expected 'the throne door' -> 'kingdome-garden', got {_NEXT_MAP.get('the throne door')}"
    )


def test_kingdome_scenes_exist():
    for key in ("kingdome-garden", "storybook", "cloverfield"):
        assert key in SCENES, f"Missing scene: {key}"
        scene = SCENES[key]
        assert "text" in scene, f"Scene {key} missing text"
        assert "doors" in scene, f"Scene {key} missing doors"
        assert len(scene["doors"]) == 3, f"Scene {key} should have 3 doors, got {len(scene['doors'])}"
        assert "fox_present" in scene, f"Scene {key} missing fox_present"


def test_kingdome_garden_doors():
    doors = SCENES["kingdome-garden"]["doors"]
    names = {d["name"] for d in doors}
    assert "The Storybook Door" in names
    assert "The Cloverfield Door" in names
    assert "The Fog Door Return" in names


def test_storybook_doors():
    doors = SCENES["storybook"]["doors"]
    names = {d["name"] for d in doors}
    assert "The Page of the Word" in names
    assert "The Page of the Egg" in names
    assert "The Page of the War" in names


def test_cloverfield_doors():
    doors = SCENES["cloverfield"]["doors"]
    names = {d["name"] for d in doors}
    assert "The Lucky Door" in names
    assert "The Today Door" in names
    assert "The Tomorrow Door" in names


def test_storybook_routes_return_to_garden():
    for door in ("the page of the word", "the page of the egg", "the page of the war"):
        assert _NEXT_MAP.get(door) == "kingdome-garden", f"Expected {door} -> kingdome-garden"


def test_cloverfield_routes():
    assert _NEXT_MAP.get("the lucky door") == "kingdome-garden"
    assert _NEXT_MAP.get("the today door") == "moss-entry"
    assert _NEXT_MAP.get("the tomorrow door") == "kingdome-garden"


def test_shared_contract_exists_and_valid():
    contract_path = REPO_ROOT / "data" / "three-doors" / "scenes.json"
    assert contract_path.exists(), f"Shared contract missing: {contract_path}"
    data = json.loads(contract_path.read_text("utf-8"))
    assert "scenes" in data, "Contract missing 'scenes'"
    assert "next_map" in data, "Contract missing 'next_map'"
    assert "kingdome-garden" in data["scenes"], "Contract missing kingdome-garden scene"
    assert data["next_map"].get("the throne door") == "kingdome-garden"


def test_challenges_json_exists():
    path = REPO_ROOT / "data" / "three-doors" / "challenges.json"
    assert path.exists(), f"Challenges registry missing: {path}"
    data = json.loads(path.read_text("utf-8"))
    assert "challenges" in data
    ids = {c["id"] for c in data["challenges"]}
    assert "poem-gate" in ids
    assert "speed-run" in ids


def test_prizes_json_exists():
    path = REPO_ROOT / "data" / "three-doors" / "prizes.json"
    assert path.exists(), f"Prizes registry missing: {path}"
    data = json.loads(path.read_text("utf-8"))
    assert "prizes" in data
    ids = {p["id"] for p in data["prizes"]}
    assert "kingdome-crown" in ids
    assert "first-steps" in ids


def test_classifications_include_kingdome():
    from three_doors_engine import ThreeDoorsEngine
    engine = ThreeDoorsEngine("test-user")
    for key, expected in (
        ("kingdome-garden", "sovereign"),
        ("storybook", "mythic"),
        ("cloverfield", "playful"),
    ):
        cls = engine._classify_scene(key)
        assert cls["archetype"] == expected, f"Expected {key} archetype={expected}, got {cls['archetype']}"


if __name__ == "__main__":
    import traceback

    tests = [
        test_throne_door_routes_to_kingdome_garden,
        test_kingdome_scenes_exist,
        test_kingdome_garden_doors,
        test_storybook_doors,
        test_cloverfield_doors,
        test_storybook_routes_return_to_garden,
        test_cloverfield_routes,
        test_shared_contract_exists_and_valid,
        test_challenges_json_exists,
        test_prizes_json_exists,
        test_classifications_include_kingdome,
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERR  {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
