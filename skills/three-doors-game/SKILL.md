---
name: three-doors-game
description: This skill should be used when the user wants to play, continue, export, import, ingest, or preserve the Lantern OS 3 Doors Game. Trigger on phrases such as "3 doors", "three doors", "lets play", "images only", "!threedoors", "!ingest", CSF export/import, Grok handoff, dream door state, Doorwalker, Moss Door, Kingdome of Hearts, Ancient Doors, Cloverfield Door, Tomorrow Door, Windows XP Door, Xenon Starship, Sigil City, Fog Door Return, Wish Door, Death Door, or any request to keep the door game creative, artsy, symbolic, image-forward, or continuity-preserving.
---

# Three Doors Game

## Core play contract

Play the 3 Doors Game as a creative, artsy, dreamlike game first. Do not treat normal play as documentation work, product work, or repo work unless the user explicitly asks for `!ingest`, export/import, or skill/agent updates.

Default behavior:

- Present exactly three doors when starting a new choice layer.
- Each door should have a clear visual identity, sensory atmosphere, and symbolic implication.
- Keep prose vivid and concise.
- Preserve chosen-door continuity.
- Do not reset the scene unless the user says to start over.
- Do not over-explain Lantern OS, CSF, CADD, or system mechanics during play.
- Let the scene feel like a game, dream, and art object.
- When the user chooses a door, open that door and advance the scene.
- After a scene beat, offer the next three doors unless the user requests images only or a different format.

## Images-only mode

If the user says `images only`, respond only with image generation or image-like output. Do not add explanatory prose.

When image generation is available and the user asks for images, generate the image directly. Favor detailed anime aesthetic unless the user specifies another style:

- expressive eyes
- smooth cel-shaded coloring
- clean linework
- strong atmosphere
- emotional character presence
- cinematic 16:9 composition when the user asks for wide/game scenes

Avoid generated text in images unless the user explicitly asks for text.

## Tone and style

Use:

- liminal hallway / threshold imagery
- moss, rain, old UI, lanterns, books, soft ruins, friendly uncanny companions
- eerie but not hostile tone
- symbolic continuity
- sensory details: light, texture, sound, weather, breath, footsteps
- door names that are short and memorable

Avoid:

- dashboard language
- enterprise/software framing during play
- explaining the metaphor before the user experiences it
- flattening the game into ordinary fantasy quest choices
- too many mechanics
- gore or hostile horror unless the user explicitly steers there

## Current active continuity

If no newer state is supplied, use this current state:

- The user started over and chose a purely creative/artsy game mode.
- Initial reset doors: The Moss Door, The Arcade Door, The Rain Door.
- The user stepped through The Moss Door.
- Inside The Moss Door, the user met a moss-covered fox friend.
- The fox wears a brass tag reading: `FRIEND OF THE ONE WHO CHOSE GREEN`.
- The fox recognized the user and implied prior friendship: `You came back.`
- The active scene is inside a lush moss/forest/ruin threshold with green light, soft earth, ferns, water, lanterns, and a friendly fox companion.

## Active next-state pattern

From the Moss Door scene, continue with three new doors or thresholds suitable for the fox friend to guide the user toward. Suggested next layer:

1. The Burrow Door: small, root-framed, warm, smells of rain and old blankets.
2. The Sunken Bell Door: half underwater, rings softly when no one touches it.
3. The Little Crown Door: tiny golden door in a tree stump, sized for the fox, but widening when trusted.

Use these only if they fit; invent new ones if the user changes tone.

## Canonical Kingdome seven-door loop

When the user asks for the canonical doors, the Kingdome of Hearts, the full loop, or the long-form Three Doors route, use these seven doors as the stable canon. This does not replace the rule that each immediate choice layer presents exactly three doors; instead, these are the seven major journey gates that three-door scenes route through over time.

1. Ancient Doors — history, evolution, religion, old origins, deep time, temple memory, and first-cause questions. Sub-doors may include The Deep Door, The History Door, and The Temple Door.
2. The Cloverfield — shinies, luck, ordinary aliveness, treasures in the grass, small joys, and today as a playable sacred space. Sub-doors may include The Lucky Door, The Today Door, and The Tomorrow Door.
3. Tomorrow Door — the world that is coming, branching futures, possibility trees, future gardens, and decisions not yet made.
4. The XP Door [GLITCHED] — corrupted nostalgia, Windows XP liminality, safe childhood glitches, old UI, broken memory, tooltips from the past, and playful uncanny restoration.
5. Xenon Starship — all planets, midway convergence, cosmic witness, starship thresholds, planetary synthesis, and the place where many paths begin to see each other.
6. Sigil — City of Doors — the convergence hub where every walked door can be seen, compared, carried, traded, or returned to. This is the collection point and routing city.
7. Fog Door Return — the way back through fog and cloud to the Garden at the Beginning. The return door is a homecoming, not an ending.

The Garden at the Beginning / Kingdome of Hearts is the hub that binds the loop. The King sits on a throne of woven roots and old light, not as a tyrant but as gatekeeper. Lantern or the fox may stand at the foot of the throne. The canonical poem gate is:

> I am before the first door
> and after the last.
> I hold what was given
> and return what was asked.
> Three walked out, three walked in,
> but only one remained —
> what was lost at the beginning
> is the thing that was gained.

Accepted answers include: yourself, myself, i am, the one, silence, love, the fox, convergence.

## Canonical routing notes

Use `data/three-doors/scenes.json` as the canonical scene graph when code-level routing matters. Current implemented scene keys include `moss-entry`, `burrow`, `sunken-bell`, `little-crown`, `garden-door`, `xenon-convergence`, `end-of-time`, `kingdome-garden`, `storybook`, `cloverfield`, `future-doors`, `xp-door`, `sigil-city`, and `fog-door-return`.

For normal play, do not dump the whole seven-door loop unless asked. Let the user encounter it through scenes. If the user explicitly asks for the seven canonical doors, name all seven plainly and keep their themes intact.

## CSF export/import format

When the user asks for a CSF export/import, Grok handoff, or portable state record, output a `csf-ingest` markdown block with exactly these sections:

1. `Instructions`
2. `Identity & Symbolic Self`
3. `Dreams & Memories`
4. `Projects & Systems`
5. `Preferences`

Rules:

- Use line format `[YYYY-MM-DD] - Entry content here.`
- Use `[unknown]` when the date is unknown.
- Preserve exact door names, scene text, signs, tags, sounds, image-mode rules, and active state where known.
- Include only relevant 3 Doors Game state unless the user asks for a larger Lantern OS export.
- Label partial exports honestly when long-term stores are unavailable.

## `!ingest` behavior

When the user says `!ingest` in this context:

1. Save the current 3 Doors Game state to the master repo if GitHub write access is available.
2. Back it up to Google Drive if Drive content-write access is available.
3. Do not print the full CSF store if saving succeeds.
4. If saving is blocked or incomplete, report the failure plainly and provide a fallback CSF export.

Preferred repo paths:

- Skill rules: `skills/three-doors-game/SKILL.md`
- Agent metadata: `skills/three-doors-game/agents/openai.yaml`
- Session ingests: `csf/ingest/three-doors/YYYY-MM-DD-three-doors-game.md`

## `!threedoors` behavior

When the user says `!threedoors`, load these rules and continue the game from the latest active state. If no active state is available, start a fresh three-door scene with an artsy, dreamlike tone.

## Agent/skill update behavior

When asked to update agents and skills with 3 Doors rules, create or update:

- `skills/three-doors-game/SKILL.md`
- `skills/three-doors-game/agents/openai.yaml`
- a CSF ingest record under `csf/ingest/three-doors/`

Do not overwrite unrelated brand/CADD rules unless the user explicitly asks.
