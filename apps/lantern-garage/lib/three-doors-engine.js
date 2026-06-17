/**
 * Three Doors Game Engine — Unified Node.js implementation
 * Consolidated from Python three_doors_engine.py
 * Single source of truth: kingdome-garden with 7 hardcoded doors + STAGES progression
 */

const fs = require("fs");
const path = require("path");

// ── Import SCENES data from client-side source ──
// These are the canonical, hardcoded door definitions
const SCENES_SOURCE = path.join(__dirname, "..", "public", "js", "three-doors-data.js");

let SCENES = {};
let STAGES = [
  "kingdome-garden",   // 0: Garden at the Beginning — the King opens
  "cloverfield",       // 1: Present Day
  "future-doors",      // 2: Future Doors
  "xp-door",           // 3: XP Door [GLITCHED]
  "xenon-convergence", // 4: Xenon Starship — convergence
  "sigil-city",        // 5: Sigil, City of Doors — synthesis
  "fog-door-return",   // 6: Fog Door Return — the way back
];

let NEXT_MAP = {};
let SD_PROMPTS = {};

// ── Load SCENES from three-doors-data.js ──
function loadScenesData() {
  try {
    // Simple regex-based parser to extract SCENES object from JS
    const content = fs.readFileSync(SCENES_SOURCE, "utf-8");

    // Extract SCENES = { ... }
    const scenesMatch = content.match(/const SCENES = \{([\s\S]*?)\n\};/);
    const stagesMatch = content.match(/const STAGES = \[([\s\S]*?)\];/);
    const nextMapMatch = content.match(/const NEXT_MAP = \{([\s\S]*?)\};/);
    const sdPromptsMatch = content.match(/const SD_PROMPTS = \{([\s\S]*?)\};/);

    if (scenesMatch) {
      // Use eval in a controlled sandbox to parse the JS object
      // Production: use a proper JS parser
      const scenesCode = `({${scenesMatch[1]}})`;
      try {
        SCENES = eval(scenesCode);
      } catch (e) {
        console.warn("[Three Doors Engine] Could not parse SCENES via eval, using fallback");
        SCENES = buildScenesFallback();
      }
    } else {
      SCENES = buildScenesFallback();
    }

    console.log(`[Three Doors Engine] Loaded ${Object.keys(SCENES).length} scenes`);
  } catch (err) {
    console.warn(`[Three Doors Engine] Could not load SCENES from JS:`, err.message);
    SCENES = buildScenesFallback();
  }
}

// ── Fallback SCENES data (copy of the kingdome-garden essential scenes) ──
function buildScenesFallback() {
  return {
    "kingdome-garden": {
      text: "**The Throne Door** opens onto the Garden at the Beginning of the **Kingdome of Hearts**. Stone paths wind through living moss; everything here is both arriving and returning. On a throne of woven roots and old light sits **the King**, his crown made of tangled vines and blinking cursors, his face the face of someone who has asked the same question ten thousand times and means it every time. He looks at you the way someone looks at a door they've seen open before, and speaks:\n\n*\"I am before the first door / and after the last. / I hold what was given / and return what was asked. / Three walked out, three walked in, / but only one remained — / what was lost at the beginning / is the thing that was gained.\"*\n\nSeven door portals shimmer around the Garden's edge, each a different color of possibility.\n\nLantern stands at the foot of the throne as if its light has always lived here.",
      doors: [
        { name: "🪨 Ancient Doors", label: "A", description: "History · evolution · religion — The Deep Door, The History Door, The Temple Door" },
        { name: "🍀 The Cloverfield", label: "B", description: "Shinies · luck · today alive — Lucky finds, treasures, living-in-the-now" },
        { name: "🔭 Tomorrow Door", label: "C", description: "The world that's coming — Future paths, branching possibilities" },
        { name: "💾 The XP Door [GLITCHED]", label: "D", description: "Corrupted · nostalgic · liminal — Windows XP aesthetic, broken reality" },
        { name: "🪐 Xenon Starship ★", label: "E", description: "All planets · midway · converge — Midway point, planetary convergence" },
        { name: "🏙️ Sigil — City of Doors", label: "F", description: "Every door leads here — Meta-hub, collection point, inventory of traveled paths" },
        { name: "🌫️ Fog Door Return", label: "G", description: "The way back — Return to garden, final test with the King" },
      ],
      fox_present: true,
    },
    "cloverfield": {
      text: "**The Cloverfield Door** swings into a meadow of four-leaf green under a dome of old light. Small shinies glitter between the stems — coins, beads, a marble with a galaxy inside. Lantern's glow catches on something glinting and lingers, for the joy of it. Here the rule of the Kingdome holds plainly: *death is only imaginary — forever begins with \"let's play.\"*",
      doors: [
        { name: "The Lucky Door", label: "A", description: "Painted clover-green. Whatever you find behind it, you needed." },
        { name: "The Today Door", label: "B", description: "Warm and ordinary. The day you are actually in, alive." },
        { name: "The Tomorrow Door", label: "C", description: "Slightly ajar. The world that's coming, branching like roots." },
      ],
      fox_present: true,
    },
    "future-doors": {
      text: "Past the meadow, the path forks upward into **the Future Doors** — a ridge where tomorrow grows like an orchard. Each tree carries doors instead of fruit, and every door is slightly open, leaking weather from years that haven't happened yet. Lantern leans close to one and its flame throws bright sparks.",
      doors: [
        { name: "The Bright Branch", label: "A", description: "Warm gold light spills out. A future where the gardens won." },
        { name: "The Unwritten Door", label: "B", description: "Plain, unfinished wood. The hinge waits for your hand to decide." },
        { name: "The Recursive Door", label: "C", description: "Opens onto a hallway of itself, smaller each time, all the way down." },
      ],
      fox_present: true,
    },
    "xp-door": {
      text: "A hill of impossibly green grass under an impossibly blue sky — you know this place. **The XP Door [GLITCHED]** stands alone on the bliss-field, its frame flickering between wood and window chrome. A startup chime plays from nowhere, half a second too slow. Lantern's glow pixelates at the edges and it seems delighted about it. A tooltip floats over the door: *It is now safe to walk through your childhood.*",
      doors: [
        { name: "System Restore", label: "A", description: "Roll back to a saved point. The smell of an old summer loads first." },
        { name: "My Documents", label: "B", description: "Every picture you ever saved, sorted by feeling instead of date." },
        { name: "unknown.exe", label: "C", description: "Publisher: unknown. Lantern nods its flame. You run it anyway." },
      ],
      fox_present: true,
    },
    "xenon-convergence": {
      text: "You step through into **The Xenon Convergence Door** — a space where all versions of this moment exist at once. A vast Xenon presence surrounds you, *witnessing*. It says, *\"You are the sum of every path you chose. And all paths were always here, waiting.\"* Lantern burns with five flames now, each glowing with a different possible future.",
      doors: [
        { name: "The Mirror Door", label: "A", description: "Shows you as you were, as you are, as you might be. All at once." },
        { name: "The Branch Door", label: "B", description: "Splits into infinite versions, each one leading somewhere true." },
        { name: "The Merge Door", label: "C", description: "Where all paths collapse into a single point of perfect understanding." },
      ],
      fox_present: true,
    },
    "sigil-city": {
      text: "All paths converge in **Sigil, the City of Doors** — a ring of streets where every wall, archway, and puddle is a threshold somewhere else. Doors you have already opened hang here like lanterns, each one faintly lit with your own footsteps. At the center plaza, the **King** waits and says: *\"You have walked my thresholds. Every door you chose was also choosing you. What was lost at the beginning is the thing that was gained — do you see it yet?\"* Lantern stands at his throne-side like an old friend.",
      doors: [
        { name: "The Gallery of Walked Doors", label: "A", description: "Your whole path hung in one hall. It rearranges when you understand it." },
        { name: "The Key Market", label: "B", description: "Stalls of keys for doors not yet dreamed. One of them is warm." },
        { name: "The Lady's Gate", label: "C", description: "Silent, watched, absolutely fair. It opens only for what is safe to carry." },
      ],
      fox_present: true,
    },
    "fog-door-return": {
      text: "At the city's edge the streets dissolve into the **Sea of Fog and Clouds**, and there it is: **the Fog Door Return**, standing in the mist where the Fog God sleeps. Through its frame you can already see the Garden at the Beginning, green and waiting. Lantern passes through first — it always does — and its glow turns back to you. *\"You came back\"* it will say on the other side. It always says that. It is always true.",
      doors: [
        { name: "The Garden Gate", label: "A", description: "Straight home to the Beginning. The King will be glad — he always is." },
        { name: "The Long Way Round", label: "B", description: "Drift through the fog first. Arrive when you're ready, not before." },
        { name: "Lantern's Shortcut", label: "C", description: "Follow the steady flame through the mist. Trust is the fastest road." },
      ],
      fox_present: true,
    },
  };
}

// Load on module initialization
loadScenesData();

// ── Game State Persistence ──
// Per-player state persists as one JSON file under data/three-doors-state/,
// mirroring the original Python StatusCube (one file per player) so the
// 7-stage journey survives across requests and server restarts.
const STATE_DIR = path.join(__dirname, "..", "..", "..", "data", "three-doors-state");

function stateFile(userId) {
  const safe = String(userId).replace(/[^a-z0-9_-]/gi, "_").slice(0, 128) || "anon";
  return path.join(STATE_DIR, `${safe}.json`);
}

class PlayerState {
  constructor(userId) {
    this.userId = userId;
    this.stageIndex = 0;
    this.loopCount = 0;
    this.history = [];
    this.sceneKey = "kingdome-garden";
  }

  static load(userId) {
    const state = new PlayerState(userId);
    try {
      const raw = fs.readFileSync(stateFile(userId), "utf-8");
      const d = JSON.parse(raw);
      state.stageIndex = Number.isInteger(d.stageIndex) ? d.stageIndex : 0;
      state.loopCount = Number.isInteger(d.loopCount) ? d.loopCount : 0;
      state.history = Array.isArray(d.history) ? d.history : [];
      state.sceneKey = typeof d.sceneKey === "string" ? d.sceneKey : "kingdome-garden";
    } catch {
      // No saved state yet (or unreadable) — fresh game.
    }
    return state;
  }

  save() {
    try {
      fs.mkdirSync(STATE_DIR, { recursive: true });
      fs.writeFileSync(stateFile(this.userId), JSON.stringify({
        userId: this.userId,
        stageIndex: this.stageIndex,
        loopCount: this.loopCount,
        history: this.history,
        sceneKey: this.sceneKey,
        savedAt: new Date().toISOString(),
      }));
    } catch (e) {
      console.warn(`[Three Doors Engine] save failed for ${this.userId}:`, e.message);
    }
  }

  reset() {
    this.stageIndex = 0;
    this.loopCount = 0;
    this.history = [];
    this.sceneKey = "kingdome-garden";
    this.save();
  }
}

// ── Game Engine ──
class ThreeDoorsEngine {
  constructor(userId) {
    this.userId = userId;
    this.state = PlayerState.load(userId);
    this.agent = "";
  }

  _getSceneForStage(stageIndex) {
    const key = STAGES[stageIndex % STAGES.length];
    return { key, scene: SCENES[key] || SCENES["kingdome-garden"] };
  }

  _buildState() {
    const { key, scene } = this._getSceneForStage(this.state.stageIndex);
    return {
      scene_key: key,
      text: scene.text,
      doors: scene.doors,
      fox_present: scene.fox_present !== false,
      history: this.state.history,
      stage_index: this.state.stageIndex,
      stage_count: STAGES.length,
      loop_count: this.state.loopCount,
    };
  }

  startGame() {
    // Resume an in-progress journey if one is saved...
    if (this.state.history.length > 0) {
      return this._buildState();
    }
    // ...otherwise begin a new game at the Garden.
    this.state.stageIndex = 0;
    this.state.history = ["Entered the Garden at the Beginning"];
    this.state.sceneKey = "kingdome-garden";
    this.state.save();
    return this._buildState();
  }

  resetGame() {
    // Clear saved progress and start fresh from the Garden.
    this.state.reset();
    return this.startGame();
  }

  chooseDoor(choice) {
    const currentState = this._buildState();
    if (!currentState) return null;

    // Parse door choice: letter (A/B/C) or full name
    const choiceUpper = String(choice).toUpperCase().trim();
    let doorName = null;

    // Find by label (A/B/C)
    const door = currentState.doors.find(
      d => d.label.toUpperCase() === choiceUpper
    );
    if (door) {
      doorName = door.name;
    } else if (choiceUpper.length > 1) {
      // Assume it's a full door name
      doorName = choice;
    } else {
      return null; // Invalid choice
    }

    // Record choice and advance
    this.state.history.push(`Chose ${doorName}`);
    this.state.stageIndex = (this.state.stageIndex + 1) % STAGES.length;

    // Loop detection: when we wrap around
    if (this.state.stageIndex === 0) {
      this.state.loopCount += 1;
    }

    this.state.save();
    return this._buildState();
  }

  toApiResponse(state) {
    return {
      ...state,
      ok: true,
      timestamp: new Date().toISOString(),
    };
  }
}

module.exports = { ThreeDoorsEngine, SCENES, STAGES };
