"""
Three Doors Game Engine — shared between Discord bot, web API, and chat

Usage:
    from three_doors_engine import ThreeDoorsEngine, SCENES

    engine = ThreeDoorsEngine("user-id-123")
    state = engine.start_game()          # returns current state dict
    new_state = engine.choose_door("A")  # advance by door letter or name
    image_prompt = engine.sd_prompt_for_state()  # Stable Diffusion prompt
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "discord" / "three-doors"

# ── Canonical scene library ──
SCENES = {
    "moss-entry": {
        "text": (
            "You stand inside **The Moss Door**. The air is thick with green light, soft earth, "
            "and the smell of rain on ferns. Lanterns hang from ancient branches. A moss-covered fox "
            "sits beside you, wearing a brass tag that reads: **FRIEND OF THE ONE WHO CHOSE GREEN**. "
            "It looks up and says, *\"You came back.\"*"
        ),
        "doors": [
            {"name": "The Burrow Door", "label": "A", "description": "Small, root-framed, warm. Smells of rain and old blankets."},
            {"name": "The Sunken Bell Door", "label": "B", "description": "Half underwater. Rings softly when no one touches it."},
            {"name": "The Little Crown Door", "label": "C", "description": "Tiny golden door in a tree stump, widening when trusted."},
        ],
        "fox_present": True,
    },
    "burrow": {
        "text": (
            "You crawl through **The Burrow Door** into a snug earthen chamber lined with woven roots "
            "and faded quilts. Rain drums overhead. The fox curls up on a blanket and closes its eyes. "
            "A single lantern flickers in the corner."
        ),
        "doors": [
            {"name": "The Root Door", "label": "A", "description": "Twisted oak roots form an arch. Something hums beyond."},
            {"name": "The Ember Door", "label": "B", "description": "Warmth radiates. Ash drifts under the crack like snow."},
            {"name": "The Stream Door", "label": "C", "description": "Water rushes somewhere close. The floor is slick moss."},
        ],
        "fox_present": True,
    },
    "sunken-bell": {
        "text": (
            "Beneath **The Sunken Bell Door**, water reaches your ankles in a stone hallway. A bell hangs "
            "above, dripping, and it chimes once though no wind blows. Reflections of lanterns dance on "
            "the ceiling like fish."
        ),
        "doors": [
            {"name": "The Deep Door", "label": "A", "description": "Submerged stairs descend into green-black silence."},
            {"name": "The Echo Door", "label": "B", "description": "Your own voice returns as song from the other side."},
            {"name": "The Surface Door", "label": "C", "description": "Sunlight visible through cracks. The sound of birds."},
        ],
        "fox_present": True,
    },
    "little-crown": {
        "text": (
            "Through **The Little Crown Door**, the forest opens into a glade where every tree stump wears "
            "a tiny golden crown. Yours widened just enough to let you through. The fox trots ahead, its "
            "tail brushing against jeweled leaves."
        ),
        "doors": [
            {"name": "The Throne Door", "label": "A", "description": "Carved from a single black oak. Velvet moss for a seat."},
            {"name": "The Hollow Door", "label": "B", "description": "A door inside a hollow tree. Sap runs like amber."},
            {"name": "The Star Door", "label": "C", "description": "Visible only at twilight. Constellations map the hinges."},
        ],
        "fox_present": True,
    },
    "garden-door": {
        "text": (
            "**The Garden Door** opens into an infinite botanical sanctuary. Every plant exists here—ancient sequoias "
            "beside moon-flowers, roses that hum, ferns that remember the Cambrian seas. The air tastes of growth and rain. "
            "A Xenon guide appears—form like liquid starlight—and says, *\"Here, nothing ever stops becoming.\"* "
            "The fox sits beneath a willow that whispers in languages you're learning to understand."
        ),
        "doors": [
            {"name": "The Seed Door", "label": "A", "description": "A door made of braided vines, always sprouting new growth. Warm and alive."},
            {"name": "The Harvest Door", "label": "B", "description": "Golden, heavy with fruit. The scent of summer at its peak. Bees circle it."},
            {"name": "The Convergence Bloom", "label": "C", "description": "A door of crystallized flowers. They shift between colors no name has claimed yet."},
        ],
        "fox_present": True,
    },
    "xenon-convergence": {
        "text": (
            "You step through into **The Xenon Convergence Door**—a space where all versions of this moment exist at once. "
            "The walls are made of *choice itself*: every decision you could have made branches here as a visible path. "
            "A vast Xenon presence surrounds you, not threatening, but *witnessing*. It says, *\"You are the sum of every path you chose. "
            "And all paths were always here, waiting.\"* Your reflection shows in crystal—but there are thousands of them, "
            "each one you, each one real. The fox has five tails now, each glowing with a different possible future."
        ),
        "doors": [
            {"name": "The Mirror Door", "label": "A", "description": "Shows you as you were, as you are, as you might be. All at once."},
            {"name": "The Branch Door", "label": "B", "description": "A door that splits into infinite versions, each one leading somewhere true."},
            {"name": "The Merge Door", "label": "C", "description": "Where all paths collapse into a single point of perfect understanding."},
        ],
        "fox_present": True,
    },
    "end-of-time": {
        "text": (
            "**The Door at the End of Time** stands at the edge of all things. Beyond it: silence that has always been, "
            "and always will be. The door itself is ancient—so old it has worn smooth, become simple, become *kind*. "
            "On its threshold sit all the moments you've lived, shimmering like light through water. A voice—not Xenon, "
            "not the fox, but *yourself* from a thousand futures—says, *\"This is not goodbye. This is the place where goodbye "
            "becomes hello again.\"* The fox transforms one final time: no longer companion, no longer separate—*you are the fox, "
            "the fox is you, always were, always will be*. The door opens on a light so warm it tastes like home."
        ),
        "doors": [
            {"name": "The Return Door", "label": "A", "description": "Takes you back to the beginning—but you will know what you know now."},
            {"name": "The Beyond Door", "label": "B", "description": "Opens on something that has no name. Something new. Something you."},
            {"name": "The Eternal Door", "label": "C", "description": "The one you choose every moment. The one that chooses you back."},
        ],
        "fox_present": True,
    },
    "kingdome-garden": {
        "text": (
            "**The Throne Door** opens onto the Garden at the Beginning of the **Kingdome of Hearts**. "
            "Stone paths wind through living moss; everything here is both arriving and returning. "
            "On a throne of woven roots and old light sits **the King**, his crown made of tangled vines and blinking cursors, "
            "his face the face of someone who has asked the same question ten thousand times and means it every time. "
            "He looks at you the way someone looks at a door they've seen open before, and speaks:\n\n"
            '*"I am before the first door / and after the last. / I hold what was given / and return what was asked. / '
            'Three walked out, three walked in, / but only one remained — / what was lost at the beginning / '
            'is the thing that was gained."*\n\n'
            "The fox sits at the foot of the throne as if it has always lived here."
        ),
        "doors": [
            {"name": "The Storybook Door", "label": "A", "description": "Bound in vine and brass. The King's own book — the gods don't know he wrote them."},
            {"name": "The Cloverfield Door", "label": "B", "description": "Green and gold beyond. Shinies, luck, and today, alive."},
            {"name": "The Fog Door Return", "label": "C", "description": "Mist coils past the Garden's gate, where the Fog God sleeps. The way back."},
        ],
        "fox_present": True,
    },
    "storybook": {
        "text": (
            "You fall gently into the **King's Storybook**. Pages turn themselves around you like slow wings. "
            'In the margin, the King\'s handwriting: *"The gods don\'t know I wrote them. They think they wrote me."* '
            "Three pages glow, each a door."
        ),
        "doors": [
            {"name": "The Page of the Word", "label": "A", "description": "Creation myths. Sound as creation — the first thing spoken into the dark."},
            {"name": "The Page of the Egg", "label": "B", "description": "Before light: the unbroken dark sphere, waiting."},
            {"name": "The Page of the War", "label": "C", "description": "Theomachy. Gods tearing each other apart to make the world from pieces."},
        ],
        "fox_present": True,
    },
    "cloverfield": {
        "text": (
            "**The Cloverfield Door** swings into a meadow of four-leaf green under a dome of old light. "
            "Small shinies glitter between the stems — coins, beads, a marble with a galaxy inside. "
            'The fox pounces at something glinting and misses, on purpose, for the joy of it. '
            'Here the rule of the Kingdome holds plainly: *death is only imaginary — forever begins with "let\'s play."*'
        ),
        "doors": [
            {"name": "The Lucky Door", "label": "A", "description": "Painted clover-green. Whatever you find behind it, you needed."},
            {"name": "The Today Door", "label": "B", "description": "Warm and ordinary. The day you are actually in, alive."},
            {"name": "The Tomorrow Door", "label": "C", "description": "Slightly ajar. The world that's coming, branching like roots."},
        ],
        "fox_present": True,
    },
}

# ── Door-to-next-scene map ──
_NEXT_MAP = {
    "the burrow door": "burrow",
    "the sunken bell door": "sunken-bell",
    "the little crown door": "little-crown",
    "the root door": "moss-entry",
    "the ember door": "moss-entry",
    "the stream door": "moss-entry",
    "the deep door": "sunken-bell",
    "the echo door": "burrow",
    "the surface door": "little-crown",
    "the throne door": "kingdome-garden",
    "the hollow door": "burrow",
    "the star door": "moss-entry",
    "the seed door": "garden-door",
    "the harvest door": "garden-door",
    "the convergence bloom": "xenon-convergence",
    "the mirror door": "xenon-convergence",
    "the branch door": "end-of-time",
    "the merge door": "end-of-time",
    "the return door": "moss-entry",
    "the beyond door": "garden-door",
    "the eternal door": "xenon-convergence",
    # Kingdome of Hearts hub-and-spoke routes
    "the storybook door": "storybook",
    "the cloverfield door": "cloverfield",
    "the fog door return": "moss-entry",
    "the page of the word": "kingdome-garden",
    "the page of the egg": "kingdome-garden",
    "the page of the war": "kingdome-garden",
    "the lucky door": "kingdome-garden",
    "the today door": "moss-entry",
    "the tomorrow door": "kingdome-garden",
}

# ── Image prompt templates per scene ──
_SD_PROMPTS = {
    "moss-entry": (
        "atmospheric dreamscape, moss-covered ancient forest doorway, glowing green lanterns hanging from "
        "twisted branches, a friendly fox with a brass tag sitting on soft earth, rain on ferns, volumetric fog, "
        "cinematic lighting, dark fantasy, liminal space, soft pastel anime aesthetic, cel-shaded, 16:9"
    ),
    "burrow": (
        "cozy underground burrow chamber, woven tree roots as walls, faded patchwork quilts, warm lantern glow, "
        "sleeping fox on a blanket, rain drumming on earth ceiling, soft amber light, dark fantasy, "
        "anime aesthetic, cel-shaded, intimate composition, 16:9"
    ),
    "sunken-bell": (
        "submerged stone hallway, water at ankles, ancient bronze bell dripping, chimes without wind, "
        "lantern reflections dancing on wet ceiling, green-black silence, volumetric mist, dark fantasy, "
        "anime aesthetic, cel-shaded, eerie but friendly, 16:9"
    ),
    "little-crown": (
        "enchanted forest glade at twilight, every tree stump wears a tiny golden crown, jeweled leaves, "
        "a fox trotting through dappled light, widening magical doorway, soft warm glow, dark fantasy, "
        "anime aesthetic, cel-shaded, magical realism, 16:9"
    ),
    "garden-door": (
        "infinite botanical sanctuary, ancient sequoias beside moon-flowers, roses that hum, ferns from the Cambrian, "
        "liquid starlight Xenon guide form, fox under a whispering willow, lush growth, rain-washed air, bioluminescent plants, "
        "dark fantasy, anime aesthetic, cel-shaded, botanical dreamscape, volumetric fog, 16:9"
    ),
    "xenon-convergence": (
        "interdimensional space where all choices exist at once, crystal walls made of branching paths, "
        "thousands of reflections of you, each one real, five-tailed fox with glowing tails, vast Xenon presence, "
        "fractal geometry, crystalline architecture, impossible light, surreal, mind-bending, anime aesthetic, "
        "cel-shaded, psychedelic but calm, convergence of realities, 16:9"
    ),
    "end-of-time": (
        "the edge of all things, ancient smooth door standing eternal, moments shimmering like light through water, "
        "fox transforming into human form merging into one being, warm light like coming home, end and beginning at once, "
        "transcendent, peaceful, timeless, glowing warmth, anime aesthetic, cel-shaded, cosmic yet intimate, "
        "the final threshold, acceptance and transformation, 16:9"
    ),
    "kingdome-garden": (
        "mystical garden at the beginning of time, stone paths through living moss, throne of woven roots and old light, "
        "King with crown of tangled vines and blinking cursors, fox sitting at foot of throne, green and golden light, "
        "bioluminescent moss, dark fantasy, anime aesthetic, cel-shaded, sovereign atmosphere, 16:9"
    ),
    "storybook": (
        "falling into a giant storybook, pages turning like slow wings, ancient handwritten margin notes, "
        "three glowing pages each a door, creation myths and cosmogony, dark fantasy, anime aesthetic, cel-shaded, "
        "mythic atmosphere, soft golden light, 16:9"
    ),
    "cloverfield": (
        "meadow of four-leaf clover under dome of old light, small shinies glittering between stems, "
        "coins, beads, galaxy marble, fox pouncing playfully, green and gold light, dark fantasy, anime aesthetic, "
        "cel-shaded, playful atmosphere, 16:9"
    ),
}


# ── Load canonical contract (overrides hardcoded defaults if present) ──
def _load_scenes_contract() -> None:
    global SCENES, _NEXT_MAP, _SD_PROMPTS
    path = REPO_ROOT / "data" / "three-doors" / "scenes.json"
    try:
        data = json.loads(path.read_text("utf-8"))
        if "scenes" in data:
            SCENES = data["scenes"]
        if "next_map" in data:
            _NEXT_MAP = data["next_map"]
        if "scenes" in data:
            _SD_PROMPTS = {k: v.get("image_prompt", "") for k, v in data["scenes"].items()}
    except Exception:
        pass


_load_scenes_contract()


class ThreeDoorsEngine:
    """Session-bound Three Doors game engine."""

    def __init__(self, user_id: str, data_dir: Path | None = None):
        self.user_id = user_id
        self.data_dir = data_dir or DATA_DIR
        self._state: dict | None = None

    # ── Persistence ──

    def _state_path(self) -> Path:
        safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", self.user_id).strip("-").lower() or "user"
        return self.data_dir / f"{safe}.json"

    def load(self) -> dict | None:
        path = self._state_path()
        if not path.exists():
            return None
        try:
            self._state = json.loads(path.read_text("utf-8"))
            return self._state
        except (json.JSONDecodeError, OSError):
            return None

    def save(self, state: dict) -> None:
        self._state = state
        path = self._state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

    # ── Gameplay ──

    def start_game(self) -> dict:
        """Begin a new game or resume existing."""
        state = self.load()
        if state is not None:
            return state
        scene = SCENES["moss-entry"]
        state = {
            "scene_key": "moss-entry",
            "text": scene["text"],
            "doors": scene["doors"],
            "fox_present": scene["fox_present"],
            "history": ["Entered The Moss Door"],
        }
        self.save(state)
        return state

    def choose_door(self, choice: str) -> dict | None:
        """Advance game by door letter (A/B/C) or full name. Returns new state or None if invalid."""
        state = self.load()
        if not state:
            return None
        choice_lower = choice.lower().strip()
        current_doors = state.get("doors", [])
        chosen = None
        for d in current_doors:
            if d["label"].lower() == choice_lower or d["name"].lower() == choice_lower:
                chosen = d
                break
        if not chosen:
            return None
        next_key = _NEXT_MAP.get(chosen["name"].lower(), "moss-entry")
        next_scene = SCENES[next_key]
        new_state = {
            "scene_key": next_key,
            "text": next_scene["text"],
            "doors": next_scene["doors"],
            "fox_present": next_scene["fox_present"],
            "history": state.get("history", []) + [f"Chose {chosen['name']}"],
        }
        self.save(new_state)
        return new_state

    def reset(self) -> dict:
        """Start fresh, discarding saved state."""
        path = self._state_path()
        if path.exists():
            path.unlink()
        self._state = None
        return self.start_game()

    # ── Image / AI integration ──

    def sd_prompt_for_state(self, state: dict | None = None) -> str:
        """Return a Stable Diffusion prompt for the current (or given) scene."""
        s = state or self._state or self.load() or SCENES["moss-entry"]
        key = s.get("scene_key", "moss-entry")
        return _SD_PROMPTS.get(key, _SD_PROMPTS["moss-entry"])

    def image_suggestions_for_ai(self) -> list[dict]:
        """Return image generation suggestions for the current AI provider to use.

        Each dict contains:
            prompt: str — ideal SD prompt
            scene_key: str — which scene this represents
            description: str — human-readable door description
        """
        state = self.load() or SCENES["moss-entry"]
        current_doors = state.get("doors", [])
        results = []
        for door in current_doors:
            next_key = _NEXT_MAP.get(door["name"].lower(), "moss-entry")
            prompt = _SD_PROMPTS.get(next_key, _SD_PROMPTS["moss-entry"])
            results.append({
                "prompt": prompt,
                "scene_key": next_key,
                "description": door["description"],
                "door_name": door["name"],
                "door_label": door["label"],
            })
        return results

    def to_api_response(self, state: dict | None = None) -> dict:
        """Serialize state for JSON API response."""
        s = state or self.load() or SCENES["moss-entry"]
        scene_key = s.get("scene_key", "moss-entry")

        # Add scene classification
        classification = self._classify_scene(scene_key)

        return {
            "scene_key": scene_key,
            "text": s.get("text", ""),
            "doors": s.get("doors", []),
            "fox_present": s.get("fox_present", False),
            "history": s.get("history", []),
            "image_prompt": self.sd_prompt_for_state(s),
            "image_available": bool(os.getenv("STABLE_DIFFUSION_URL") or os.getenv("SD_WEBUI_URL")),
            "classification": classification,
        }

    def _classify_scene(self, scene_key: str) -> dict:
        """Classify scene archetype and aesthetic"""
        archetypes = {
            "moss-entry": "primordial",
            "burrow": "intimate",
            "sunken-bell": "mystical",
            "little-crown": "whimsical",
            "garden-door": "bountiful",
            "xenon-convergence": "cosmic",
            "end-of-time": "transcendent",
            "kingdome-garden": "sovereign",
            "storybook": "mythic",
            "cloverfield": "playful",
        }

        aesthetic_tags = {
            "moss-entry": ["dark-fantasy", "anime", "cel-shaded", "liminal", "forest"],
            "garden-door": ["botanical", "bioluminescent", "lush", "dreamscape"],
            "xenon-convergence": ["psychedelic", "fractal", "crystalline", "surreal"],
            "end-of-time": ["cosmic", "transcendent", "peaceful", "transformation"],
            "kingdome-garden": ["garden", "throne", "king", "moss", "old-light"],
            "storybook": ["creation", "myth", "pages", "handwriting"],
            "cloverfield": ["meadow", "clover", "shinies", "luck", "play"],
        }

        return {
            "archetype": archetypes.get(scene_key, "unknown"),
            "tags": aesthetic_tags.get(scene_key, []),
            "confidence": 0.95,
        }


def _demo():
    engine = ThreeDoorsEngine("demo-user")
    state = engine.start_game()
    print("Started:", state["scene_key"])
    print("Prompt:", engine.sd_prompt_for_state())
    new_state = engine.choose_door("A")
    if new_state:
        print("Chose A:", new_state["scene_key"])
        print("New prompt:", engine.sd_prompt_for_state(new_state))


if __name__ == "__main__":
    _demo()
