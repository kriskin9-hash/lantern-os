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
            "garden-at-beginning": "The King's opening poem echoes through ancient paths.",
            "present-day": "Cloverfield—lucky doors, today alive.",
            "future-doors": "Branches of possibility stretch before you.",
            "xp-door": "A Windows XP liminal landscape glitches with nostalgia.",
            "xenon-starship": "Convergence—all timelines visible at once.",
            "sigil-city-of-doors": "Synthesis hub. The King returns. Fractal architecture.",
            "fog-door-return": "Fog coils past the gate. The escape hatch. Loops back.",
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
        doors_by_stage = {
            "garden-at-beginning": [
                {"name": "The Storybook Door", "label": "A", "description": "The Kings own book."},
                {"name": "The Cloverfield Door", "label": "B", "description": "Green and gold. Luck and today."},
                {"name": "The Fog Door Return", "label": "C", "description": "The way back."},
            ],
            "present-day": [
                {"name": "The Burrow Door", "label": "A", "description": "Deep roots, comfortable dark."},
                {"name": "The Sunken Bell Door", "label": "B", "description": "Ringing underwater songs."},
                {"name": "The Little Crown Door", "label": "C", "description": "Small, precious, overlooked."},
            ],
            "future-doors": [
                {"name": "The Root Door", "label": "A", "description": "What grows beneath."},
                {"name": "The Ember Door", "label": "B", "description": "What burns forward."},
                {"name": "The Stream Door", "label": "C", "description": "What flows ahead."},
            ],
            "xp-door": [
                {"name": "The Deep Door", "label": "A", "description": "Windows crashing softly."},
                {"name": "The Echo Door", "label": "B", "description": "Voices from the past."},
                {"name": "The Surface Door", "label": "C", "description": "Desktop blue. Eternal."},
            ],
            "xenon-starship": [
                {"name": "The Throne Door", "label": "A", "description": "Convergence center."},
                {"name": "The Hollow Door", "label": "B", "description": "Void of all time."},
                {"name": "The Star Door", "label": "C", "description": "Light born here."},
            ],
            "sigil-city-of-doors": [
                {"name": "The Synthesis Door", "label": "A", "description": "All paths meet."},
                {"name": "The Mirror Door", "label": "B", "description": "Your own reflection."},
                {"name": "The Archive Door", "label": "C", "description": "Every version stored."},
            ],
            "fog-door-return": [
                {"name": "The Gate Door", "label": "A", "description": "The garden calls again."},
                {"name": "The Loop Door", "label": "B", "description": "Endless return."},
                {"name": "The Exit Door", "label": "C", "description": "The way out."},
            ],
        }
        doors = doors_by_stage.get(stage, [])
        if state.agent == "blinkbug":
            doors = doors[1:] + [doors[0]]
        elif state.agent == "xenon":
            doors = sorted(doors, key=lambda d: d["label"])
        return doors

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
