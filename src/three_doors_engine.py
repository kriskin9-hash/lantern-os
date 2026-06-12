"""Three-Doors Kingdome Game Engine — CSF v07 Backend"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.csf.v07.csf_file import CSFFileWriter, CSFFileReader

STAGES = [
    "garden-at-beginning", "present-day", "future-doors", "xp-door",
    "xenon-starship", "sigil-city-of-doors", "fog-door-return",
]
ARCHETYPES = ["seeker", "healer", "explorer"]
AGENTS = ["lantern", "blinkbug", "keystone", "waterfall", "xenon", "founder"]


class ThreeDoorsGameState:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.loop_number = 1
        self.stage_number = 0
        self.archetype = "seeker"
        self.agent = "lantern"
        self.observations: List[Dict[str, Any]] = []
        self.symbols: Dict[str, Any] = {}
        self.created_at = time.time()
        self.last_updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id, "loop": self.loop_number,
            "stage": self.stage_number, "archetype": self.archetype,
            "agent": self.agent, "observations": self.observations,
            "symbols": self.symbols,
            "created_at": self.created_at, "last_updated_at": self.last_updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreeDoorsGameState":
        state = cls(data["user_id"])
        state.loop_number = data.get("loop", 1)
        state.stage_number = data.get("stage", 0)
        state.archetype = data.get("archetype", "seeker")
        state.agent = data.get("agent", "lantern")
        state.observations = data.get("observations", [])
        state.symbols = data.get("symbols", {})
        state.created_at = data.get("created_at", time.time())
        state.last_updated_at = data.get("last_updated_at", time.time())
        return state


class ThreeDoorsEngine:
    """Game engine — initialized per user, stores in CSF v07."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.data_dir = Path("./data/csf")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.agent = "lantern"

    def _get_csf_path(self) -> Path:
        return self.data_dir / f"{self.user_id}.csf"

    def _get_json_backup_path(self) -> Path:
        return self.data_dir / f"{self.user_id}.json"

    def _load_state(self) -> ThreeDoorsGameState:
        csf_path = self._get_csf_path()
        if csf_path.exists():
            try:
                reader = CSFFileReader(csf_path)
                if reader.delta_stream:
                    data = json.loads(reader.delta_stream.decode("utf-8"))
                    return ThreeDoorsGameState.from_dict(data)
            except Exception as e:
                print(f"Warning: Failed to load CSF: {e}")
                json_path = self._get_json_backup_path()
                if json_path.exists():
                    try:
                        with open(json_path) as f:
                            return ThreeDoorsGameState.from_dict(json.load(f))
                    except Exception:
                        pass
        return ThreeDoorsGameState(self.user_id)

    def _save_state(self, state: ThreeDoorsGameState) -> None:
        state.last_updated_at = time.time()
        state_json = json.dumps(state.to_dict()).encode("utf-8")
        try:
            writer = CSFFileWriter()
            writer.set_delta_stream(state_json, len(state_json))
            writer.write(self._get_csf_path())
        except Exception as e:
            print(f"Warning: Failed to write CSF: {e}")
        with open(self._get_json_backup_path(), "w") as f:
            json.dump(state.to_dict(), f, indent=2)

    def start_game(self) -> Dict[str, Any]:
        state = self._load_state()
        state.agent = self.agent if self.agent in AGENTS else "lantern"
        scene = self._generate_scene(state)
        self._save_state(state)
        return scene

    def choose_door(self, choice: str) -> Dict[str, Any]:
        state = self._load_state()
        state.observations.append({
            "type": "door_choice",
            "timestamp": time.time(),
            "stage": state.stage_number,
            "data": {"choice": choice, "agent": state.agent},
        })
        state.stage_number += 1

        if state.stage_number >= len(STAGES):
            if state.observations:
                symbol_key = f"archetype={state.archetype}_agent={state.agent}"
                state.symbols[symbol_key] = {
                    "frequency": state.symbols.get(symbol_key, {}).get("frequency", 0) + 1,
                    "loop": state.loop_number,
                    "timestamp": time.time(),
                }
            state.loop_number += 1
            state.stage_number = 0
            state.observations = []

        scene = self._generate_scene(state)
        self._save_state(state)
        return scene

    def reset(self) -> None:
        csf_path = self._get_csf_path()
        json_path = self._get_json_backup_path()
        if csf_path.exists():
            csf_path.unlink()
        if json_path.exists():
            json_path.unlink()

    def _generate_scene(self, state: ThreeDoorsGameState) -> Dict[str, Any]:
        stage = STAGES[state.stage_number] if state.stage_number < len(STAGES) else STAGES[0]
        text = self._generate_text(stage, state)
        doors = self._generate_doors(stage, state)
        return {
            "user_id": state.user_id, "loop": state.loop_number,
            "stage": state.stage_number, "stage_name": stage,
            "scene_key": f"{stage}-loop{state.loop_number}",
            "text": text, "doors": doors,
            "fox_present": (state.stage_number % 2 == 0) or state.archetype == "explorer",
            "archetype": state.archetype, "agent": state.agent,
            "symbols": state.symbols,
        }

    def _generate_text(self, stage: str, state: ThreeDoorsGameState) -> str:
        texts = {
            "garden-at-beginning": "The King's opening poem echoes through ancient paths. Each word a seed, each image a door waiting to bloom.",
            "present-day": "Cloverfield - lucky doors, today alive. The scent of grass and possibility mingles with the weight of the present moment.",
            "future-doors": "Branches of possibility stretch before you, each limb heavy with unwritten futures. You see them shimmer and dance at the edge of certainty, calling to your deepest hopes and fears. Time spirals outward. What you choose here echoes forward.",
            "xp-door": "A Windows XP liminal landscape glitches with nostalgia - blue-screen reveries, the hum of dial-up eternity, folders within folders containing forgotten dreams. The air tastes like memory. Pixels drift like snowfall. Everything feels close and infinitely far away.",
            "xenon-starship": "Convergence - all timelines visible at once. The ship hums with the weight of infinite choice. You stand at the still center where all moments exist simultaneously, a nexus of every decision ever made and unmade. The King's throne rises in the distance.",
            "sigil-city-of-doors": "Synthesis hub. The King returns. Fractal architecture blooms in all directions - doors opening into doors, symbols reflecting into symbols, your own patterns made manifest in architecture. Every choice you've made is written in light here. The city knows you.",
            "fog-door-return": "Fog coils past the gate. The escape hatch. Loops back. You feel the pull of return, the gentle spiral that will carry you back to the beginning - not to forget, but to remember with new eyes.",
        }
        text = texts.get(stage, "You stand in the Kingdome.")
        agent_flavor = {
            "lantern": " Light guides the way.",
            "blinkbug": " Something glitches playfully.",
            "keystone": " Doors align with intention.",
            "waterfall": " Water flows through choices.",
            "xenon": " All possibilities shimmer.",
            "founder": " The root of all lies here.",
        }
        text += agent_flavor.get(state.agent, "")
        if state.symbols:
            text += f" You carry {len(state.symbols)} crystallized patterns."
        return text

    def _generate_doors(self, stage: str, state: ThreeDoorsGameState) -> list:
        """
        Phase 3 Refactored: Generate personalized 3-5 doors.
        Pipeline: Load → Archetype filter → Agent filter → Symbol unlocks → Observation weight → Return
        """
        base_doors = self._load_stage_doors(stage)
        if not base_doors:
            return [
                {"name": "The Lost Door", "label": "A", "description": "Unknown path."},
                {"name": "The Return Door", "label": "B", "description": "Way back."},
                {"name": "The Wait Door", "label": "C", "description": "Stay a moment."},
            ]

        for door in base_doors:
            door.setdefault("unlocked_by", "default")
            door.setdefault("archetype_match", [])
            door.setdefault("agent_affinity", {})

        archetype_filtered = [
            door for door in base_doors
            if not door.get("archetype_match") or state.archetype in door.get("archetype_match", [])
        ]
        if not archetype_filtered:
            archetype_filtered = base_doors

        agent_filtered = self._apply_agent_filter(archetype_filtered, state.agent, stage)
        agent_filtered = self._apply_symbol_unlocks(agent_filtered, state.symbols, stage, state.archetype, state.agent)

        if state.observations:
            agent_filtered = self._apply_observation_weighting(agent_filtered, state.observations, stage)

        final_doors = agent_filtered[:5]
        if len(final_doors) < 3:
            final_doors = agent_filtered + base_doors
            final_doors = final_doors[:5]

        for i, door in enumerate(final_doors):
            door["label"] = chr(65 + i)

        return final_doors

    def _load_stage_doors(self, stage: str) -> list:
        """Load base doors for stage with archetype matching."""
        doors_by_stage = {
            "garden-at-beginning": [
                {"name": "The Storybook Door", "label": "A", "description": "The Kings own book.", "archetype_match": []},
                {"name": "The Cloverfield Door", "label": "B", "description": "Green and gold. Luck and today.", "archetype_match": []},
                {"name": "The Fog Door Return", "label": "C", "description": "The way back.", "archetype_match": []},
            ],
            "present-day": [
                {"name": "The Burrow Door", "label": "A", "description": "Deep roots, comfortable dark.", "archetype_match": ["healer", "explorer"]},
                {"name": "The Sunken Bell Door", "label": "B", "description": "Ringing underwater songs.", "archetype_match": []},
                {"name": "The Little Crown Door", "label": "C", "description": "Small, precious, overlooked.", "archetype_match": ["seeker"]},
            ],
            "future-doors": [
                {"name": "The Root Door", "label": "A", "description": "What grows beneath.", "archetype_match": ["healer"]},
                {"name": "The Ember Door", "label": "B", "description": "What burns forward.", "archetype_match": ["explorer"]},
                {"name": "The Stream Door", "label": "C", "description": "What flows ahead.", "archetype_match": []},
            ],
            "xp-door": [
                {"name": "The Deep Door", "label": "A", "description": "Windows crashing softly.", "archetype_match": []},
                {"name": "The Echo Door", "label": "B", "description": "Voices from the past.", "archetype_match": ["seeker"]},
                {"name": "The Surface Door", "label": "C", "description": "Desktop blue. Eternal.", "archetype_match": []},
            ],
            "xenon-starship": [
                {"name": "The Throne Door", "label": "A", "description": "Convergence center.", "archetype_match": []},
                {"name": "The Hollow Door", "label": "B", "description": "Void of all time.", "archetype_match": ["explorer"]},
                {"name": "The Star Door", "label": "C", "description": "Light born here.", "archetype_match": ["seeker"]},
            ],
            "sigil-city-of-doors": [
                {"name": "The Synthesis Door", "label": "A", "description": "All paths meet.", "archetype_match": []},
                {"name": "The Mirror Door", "label": "B", "description": "Your own reflection.", "archetype_match": []},
                {"name": "The Archive Door", "label": "C", "description": "Every version stored.", "archetype_match": []},
            ],
            "fog-door-return": [
                {"name": "The Gate Door", "label": "A", "description": "The garden calls again.", "archetype_match": []},
                {"name": "The Loop Door", "label": "B", "description": "Endless return.", "archetype_match": []},
                {"name": "The Exit Door", "label": "C", "description": "The way out.", "archetype_match": []},
            ],
        }
        return [dict(d) for d in doors_by_stage.get(stage, [])]

    def _apply_agent_filter(self, doors: list, agent: str, stage: str) -> list:
        """Reorder doors by agent persona (6 distinct filtering strategies)."""
        result = [dict(d) for d in doors]

        if agent == "lantern":
            return result
        elif agent == "blinkbug":
            return result[1:] + [result[0]] if len(result) > 1 else result
        elif agent == "keystone":
            return sorted(result, key=lambda d: d.get("agent_affinity", {}).get("keystone", 1.0), reverse=True)
        elif agent == "waterfall":
            return list(reversed(result))
        elif agent == "xenon":
            return sorted(result, key=lambda d: d.get("name", "").lower())
        elif agent == "founder":
            roots = [d for d in result if "root" in d.get("name", "").lower() or "origin" in d.get("description", "").lower()]
            return roots + [d for d in result if d not in roots]
        return result

    def _apply_symbol_unlocks(self, doors: list, symbols: dict, stage: str, archetype: str, agent: str) -> list:
        """Unlock hidden doors based on consolidated symbols."""
        result = [dict(d) for d in doors]
        if not symbols:
            return result

        symbol_key = f"archetype={archetype}_agent={agent}"
        frequency = symbols.get(symbol_key, {}).get("frequency", 0)
        max_frequency = max([s.get("frequency", 0) for s in symbols.values()] if symbols else [0])

        if frequency >= 2:
            result.append({
                "name": "The Hidden Door (You've Been Here Before)",
                "label": "H",
                "description": "A familiar feeling. Your echo from before.",
                "unlocked_by": f"symbol:{symbol_key}",
                "archetype_match": [],
            })

        if max_frequency >= 3:
            result.append({
                "name": "The Crystalline Door",
                "label": "X",
                "description": "Your patterns have solidified. Step through.",
                "unlocked_by": "symbol:high_frequency",
                "archetype_match": [],
            })

        if len(symbols) > 5:
            result.append({
                "name": "The Infinite Door",
                "label": "∞",
                "description": "All your choices converge here.",
                "unlocked_by": "symbol:convergence",
                "archetype_match": [],
            })

        return result

    def _apply_observation_weighting(self, doors: list, observations: list, stage: str) -> list:
        """Boost doors matching themes from current loop's choices."""
        result = [dict(d) for d in doors]
        if not observations:
            return result

        recent_choices = [o["data"].get("choice") for o in observations if o["type"] == "door_choice"]
        theme_words = {"A": "first", "B": "middle", "C": "last"}
        for i, door in enumerate(result):
            door["weight"] = 1.0 + (0.1 * recent_choices.count(chr(65 + i)))

        return sorted(result, key=lambda d: d.get("weight", 1.0), reverse=True)

    def to_api_response(self, scene: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not scene:
            return {
                "error": "scene_generation_failed", "user_id": self.user_id,
                "loop": 1, "stage": 0, "stage_name": "", "scene_key": "",
                "text": "", "doors": [], "fox_present": False,
                "archetype": "seeker", "agent": self.agent,
                "symbols": {}, "image_available": False, "image_prompt": "",
            }
        return {
            **scene,
            "image_available": False, "image_prompt": "",
        }
