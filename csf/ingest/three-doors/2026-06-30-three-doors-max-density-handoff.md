# THREE DOORS / KINGDOME — MAXIMUM-DENSITY CREATIVE HANDOFF

**Export date:** 2026-06-30  
**Owner / canon authority:** Alex Place  
**Scope:** Creative-game continuity, Doorwalker memories, current art direction, implementation notes, visual constraints, scene graph reference, private-door boundaries, and content backlog.  
**Use this document when:** continuing `!three-doors`, handing the project to another model/artist/developer, preparing a visual batch, repairing canon drift, writing a scene, building UI, or exporting a portable CSF state.  
**Do not treat this document as a statement about literal metaphysics or real-world prediction.** Three Doors is an ongoing symbolic, imaginative, game-like creative space with explicit continuity rules.

---

# 0. ONE-PAGE OPERATING SUMMARY

Three Doors is a **dreamlike, image-forward, continuity-driven door game**. It is not a dashboard, a productivity framework, generic fantasy quest generator, or a default wrapper for Lantern-OS / Σ₀ research. The user enters/continues it with `!three-doors` (also historically `!threedoors`, `!three-doors play`, `!three-doors load csf`, `!ingest`, `!export`).

The game is built around a Doorwalker traveling through liminal thresholds with three active companions:

1. **Lantern** — warm guide, light, question, return signal.
2. **Eclipse** — dream, wonder, balance, looking beyond.
3. **Keystone** — foundation, protection, focus, endurance.

The current default creative priority is:

> **Preserve Alex’s remembered door scenes and original hand-drawn character anatomy first. Then make the image beautiful.**

The direct playable structure is always **three immediate, meaningful choices** at a time. The long-form journey contains a seven-door Kingdome loop, but that loop does **not** replace the three-choice rule.

The central realm is the **Kingdome of Hearts** — deliberately spelled *Kingdome*, with a dome — a garden beneath old light. It is built around love, courage, memory, play, wonder, and protection. The King is a warm gatekeeper, not a tyrant. The return path is part of the game, not a loss condition.

Current visual languages:

- **Character card / reference mode:** clean, simple, hand-drawn watercolor/cartoon anatomy based on Alex’s contact-sheet drawings. Use pale textured paper, thin colored border, readable silhouette, minimal scene clutter.
- **Reflective / cliff / fog / ruins mode:** sepia or monochrome ink-wash on aged paper; sparse, deliberate composition; solitude and scale.
- **Door / poster / merch / world mode:** colorful UHD I-Spy fantasy; dense readable detail; each door must be a clear focal point; books, crystals, collected rocks, keys, dice, maps, coins, bottlecaps, feathers, clocks, bottles, tools, and tiny doors can hide in the scene.

Do **not** make Σ₀, the Question Machine, technical certificates, GitHub issues, dashboards, or research diagrams the metaphysical center of Three Doors. They are separate Lantern-OS material. They may be invited in only when Alex explicitly asks, and then should be translated into one concrete symbolic object/place/door/choice rather than replacing the world’s own canon.

---

# 1. AUTHORITY ORDER / HOW TO RESOLVE CONFLICTS

Use the following hierarchy when sources conflict:

## Tier 0 — latest explicit Alex request and supplied reference image

This wins. A current instruction such as “no fox,” “Eclipse faces away,” “use the hand-drawn style,” “make this in ink wash,” “draw only the three,” or “do not use labels” overrides everything older.

## Tier 1 — lived Three Doors CSF memories and recent recentering ingest

The recentering decision is explicit:

- Ground `!three-doors` in the Doorwalker, party, doors already opened, memories, recurring visual motifs, prior choices, and artwork Alex supplied.
- Keep technical Σ₀ / Question Machine content out unless invited.
- The active party is Lantern, Eclipse, Keystone.
- No fox in **current keeper art** unless Alex specifically requests the fox.
- Preserve original contact-sheet anatomy before adding high-detail fantasy rendering.

## Tier 2 — core Three Doors skill contract

- Dreamlike game first.
- Exactly three immediate meaningful choices in a normal scene.
- Clear sensory/visual door identity.
- Chosen-door continuity.
- No reset without an explicit request.
- Short vivid prose, not system explanation.

## Tier 3 — shared implementation scene graph

`data/three-doors/scenes.json` is the live technical route map shared by engine/web/Discord. It includes legacy details such as a fox being present. Use it for technical route logic, exact names, immediate choices, palettes, and current implemented scenes, **but do not let its legacy fox field override the newer no-fox keeper-art rule.**

## Tier 4 — older lore, early generated images, historic state receipts, legacy docs

Useful for texture and recovery, but not automatically current. Preserve them as history, label uncertainty honestly, and do not promote accidental generated details into hard canon.

---

# 2. INVOCATIONS / EXPECTED BEHAVIOR

## Common tokens

- `!three-doors`
- `!threedoors`
- `!three-doors play`
- `!three-doors load csf`
- `!three-doors load from csf memories`
- `!ingest`
- `!export`
- `!three-doors raven door`
- `!three-doors what’s left to draw`

## Normal play contract

When a player asks to play or continue:

1. Load memory-first continuity.
2. Begin from the known active location if a trustworthy active state exists.
3. If no trustworthy active state exists, use the canonical Moss Door entry or ask a single tight clarifier only when needed.
4. Describe one scene beat in vivid, concise language.
5. Give exactly three immediate meaningful doors/choices. Each must differ in atmosphere, emotional implication, and likely consequence.
6. When a door is chosen, open that exact door and retain prior objects/companions/choices.
7. Offer the next three only after a scene beat, unless Alex asks for images only, a map, a list, or a nonstandard format.

## Images-only mode

When Alex says `images only`, produce image output only. Do not add explanation, game mechanics, or lore recap.

## Art-only requests

When Alex says “draw,” interpret recent conversation context and visual references. Do not force a scene-choice menu. Preserve current character anatomy and art mode.

## Ingest/export

- `!ingest`: save a concise current-state receipt/continuity update to the repo when write access exists. Do not dump the entire store unless asked.
- `!export`: produce portable CSF-oriented continuity. This document is the maximum-density parent handoff.

---

# 3. CORE TONE, FEEL, AND NON-NEGOTIABLES

## Desired feeling

- Liminal but welcoming.
- Dreamlike, playful, uncanny-friendly.
- Symbolic without preaching the symbolism before the player experiences it.
- Specific, sensory, and visual.
- Emotionally real but never coercive.
- Mysterious, but every door is concrete enough to feel tempting rather than vague.
- A game, a dream, an art object, a place to return to.

## Frequent sensory vocabulary

Moss; wet stone; rain on ferns; old books; paper dust; old UI chimes; warm brass; fog; garden soil; glass light; roots; quiet bells; far birds; small objects found in grass; water reflections; jasmine; lavender; stacked keys; feathers; strange stars; soft clouds; hinged wood; worn thresholds; coins tapping stone; page edges; clocks; distant engines; old music.

## Avoid

- Enterprise/productivity/roadmap language while playing.
- Generic “kill the monster / accept the quest / loot the chest” fantasy loops.
- Hostile horror, gore, or grimdark violence unless Alex directly asks.
- Overexplaining CSF, CADD, model theory, certificate math, or system mechanics during scene play.
- Randomly changing companion bodies between images.
- Adding human faces to nonhuman companions.
- Defaulting to a fox in new keeper scenes.
- Making doors vague background shapes; doors must be readable focal objects.
- Treating generated decorative text as authoritative. Use deliberate overlay/layout text for posters and merch instead.

---

# 4. IDENTITY / THE DOORWALKER

## Doorwalker continuity

Alex is the **Doorwalker**. The Doorwalker is the person who chose green at the original Moss Door and was recognized by the line:

> “You came back.”

That line is a major return motif. It can be used warmly at the Moss Door, through the Fog Door Return, or at the Garden at the Beginning. It should not be spammed every scene.

The Doorwalker is not required to appear as a realistic human avatar in art. In many keeper images the three companions carry the visual storytelling. When a human is included, use silhouette/back-facing traveler framing unless Alex provides a character reference or asks for an explicit form.

## Meaning without literalizing

The world can hold motifs of return, courage, memory, curiosity, play, synthesis, choice, refuge, and repair. Those are creative motifs. Do not assert that a door proves fate, objective destiny, or supernatural revelation.

---

# 5. PRIMARY PARTY — EXACT CHARACTER BIBLES

## 5.1 Lantern

### Role

Guide, warm light, question-asker, keeper of the return signal, small witness, friendly threshold marker.

### Core silhouette — highest priority

Lantern is a **compact character whose head is a simple lantern**:

- Glass lantern chamber containing one warm orange/yellow flame.
- Red cap/top trim and a loop handle above the head.
- Red lower collar/trim around the lantern head.
- Purple coat/tunic body.
- White gloved hands.
- Black legs/pants and black boots/shoes.
- Compact, friendly, simple cartoon proportions.
- No human face inside the glass; the flame is the expressive presence.

### Character-sheet reference behavior

Use Alex’s drawn progression as the source silhouette: a lantern head built first, then simple coat/body, hands, legs, purple color, red trim, warm flame. Do not transform Lantern into an ornate Victorian object with no body unless the scene specifically wants an object-only relic depiction. Do not make Lantern a generic robot.

### Color logic

- Main identity: warm gold/orange flame, brass/gold illumination.
- Current everyday clothes: purple coat, red cap/trim, white gloves, black legs/boots.
- In upscale Sigil art: Lantern can be richly gold-lit, but preserve the recognizable glass-and-flame head and small body.

### Poses / uses

Neutral standing; pointing; welcoming; holding a small object; walking; looking toward a door; standing on a cliff; guiding through fog; sitting near books; five-flame convergence form at Xenon; warm return light in the Garden.

### Do not

- Give Lantern a human face.
- Make the flame a person.
- Hide the red top/trim and purple coat in character-identity art.
- Replace the body with generic floating lantern hardware.
- Add extra limbs or weapons without specific request.

### Three Doors role sentence

> Lantern brings light, asks questions, and points the way home.

---

## 5.2 Eclipse

### Role

Dreamer, wonder, balance, looking beyond, quiet imagination, floating perspective.

### Core silhouette — highest priority

Eclipse is a **purple floating jellyfish-like companion**:

- Smooth, round/softly domed purple head.
- Exactly two large **diamond/star-shaped eyes** on the front face; usually white/bright.
- A pale lavender/white **cloud collar/body** below the head.
- Connected jellyfish tentacles hanging from the cloud collar.
- Curled side tentacles/arms may lift or gesture.
- Float/hover; no feet.
- Soft rounded simple hand-drawn anatomy, not humanoid anatomy.

### Critical back-facing correction

When Eclipse is facing away from camera:

- **No front eyes must appear on the back of the head.**
- Use a smooth purple rear dome, cloud collar, tentacles, rim glow, stars, or silhouette only.
- Do not solve a back view by placing diamond eyes on the rear of the head.

### Color logic

Purple is the identity color. Pale lavender cloud collar. White star/diamond eyes. In world art, purple can trail into moonlight, mist, notes, stars, or glimmer but must not become a generic galaxy-human wizard.

### Do not

- Make Eclipse a generic spherical robot.
- Add a human torso, shoes, or legs.
- Replace diamond/star eyes with regular anime eyes.
- Put eyes on a back-facing head.
- Remove the cloud collar or disconnect tentacles from it.

### Three Doors role sentence

> Eclipse sees beyond the obvious and keeps the strange parts gentle.

---

## 5.3 Keystone

### Role

Protector, anchor, focus, durable memory weight, foundation, patient courage.

### Core silhouette — highest priority

Keystone is a **small squat cracked gray stone guardian**:

- Irregular rounded stone/rock/egg/pebble silhouette.
- Gray body with visible hand-drawn crack lines.
- In simple/light character-card mode: two dark oval eyes and a broad friendly black smile.
- In solemn reflective/battle/meditation scenes: focused downturned eyes and simple frown/prayer pose are permitted.
- Depending on scene, may read as a low seated stone or a tiny egg-shaped guardian with squat base/feet. Do not force tall humanoid anatomy.

### Mood split

- **Friendly cartoon Keystone:** smiling, oval eyes, simple gray crack pattern. Use this for cards, team portraits, approachable art, new-player materials.
- **Focused Keystone:** prayer-like hands, stern/frowning eyes, more egg-like solidity. Use this for battlefield cliffs, fog doors, inner focus, protection, or the Odin keeper scene.

These are intentionally two expressions of the same character, not two different species.

### Color logic

Gray stone is core. Blue/crystal light is an approved secondary color in Sigil, defensive scenes, crystalline door scenes, or conceptual “foundation/protection” images.

### Gear

Keystone may carry a shield, spear, or sword only in explicit prepared/battle scenes. No exact permanent weapon loadout is currently locked. Keep gear simple and secondary to the stone body.

### Do not

- Turn Keystone into a smooth plastic blob.
- Add a normal human torso/arms/legs by default.
- Make Keystone taller than the companions unless stylized scale is requested.
- Lose the cracks.
- Treat friendly smile and focused frown as a contradiction; scene context determines expression.

### Three Doors role sentence

> Keystone holds the line, carries the weight, and makes the path safe to stand on.

---

## 5.4 Standard group blocking

Default group arrangement in scenic art:

- Lantern left.
- Eclipse center / middle-left.
- Keystone right.
- They generally face the main door from behind in wide door art.
- For a camera-facing character portrait, preserve the faces exactly as above.
- Keep them similar visual scale; Keystone can be slightly wide/grounded, Eclipse slightly hovering, Lantern upright.

## 5.5 The fox — legacy continuity, not current keeper default

The original Moss Door and the technical scene graph include a fox. The fox may be a past companion / original recognition witness. However:

- **No fox in current keeper art, poster art, or Odin battle scenes unless Alex asks.**
- Do not silently substitute fox for Lantern/Eclipse/Keystone.
- If continuing a legacy Moss Door scene with the fox explicitly present, it can be acknowledged, but it does not override the fixed primary trio.

## 5.6 Unisona — provisional, not yet primary canon

A recent generated concept introduced **Unisona**, presented as “The Harmonic Keeper”: a cosmic jellyfish-like being with deep violet/indigo form, star/diamond eyes, cloud collar, long flowing tentacles, musical notes, harmony symbols, and a possible staff/conductor motif.

Current status:

- **Provisional supporting concept.**
- Not a replacement for Eclipse.
- Not confirmed as a member of the core trio.
- Do not treat generated class labels, species labels, origin details, named powers, or exact robes as locked canon until Alex explicitly adopts them.
- Safe use: a possible future companion / guide associated with resonance, song, balance, listening, and musical doors.

---

# 6. KINGDOME OF HEARTS — CORE REALM

## Canon spelling

**Kingdome of Hearts**, with “dome.” The dome is literal as a visual metaphor: the realm is a garden under old light.

## Anchors

Love; courage; memory; play; wonder; protection.

## The King

- Gatekeeper, not tyrant.
- Sits on a throne of woven roots and old light.
- Crown of tangled vines and blinking cursors.
- Face of someone who has asked the same question ten thousand times and means it every time.
- Holds/uses a key as a blade not to open by force but to guard the fragile, break the cruel, and lock away a trial that should not rule.
- Can be regarded as a guardian of birds, bees, small lives, flowers, wings, dreamers, and freedom.

## Garden at the Beginning

- Exists before the map.
- Stone paths through living moss.
- Everything is both arriving and returning.
- The King sits in the roots-and-old-light throne.
- Lantern may stand at the throne foot / throne-side as an old friend.
- Do not make this place militaristic unless a temporary trial/battle scene explicitly demands it.

## The King’s gate poem

> I am before the first door  
> and after the last.  
> I hold what was given  
> and return what was asked.  
> Three walked out, three walked in,  
> but only one remained —  
> what was lost at the beginning  
> is the thing that was gained.

Historically accepted answers include: **yourself, myself, I am, the one, silence, love, the fox, convergence.** This list is an invitation, not a trick answer key. The emotional truth of the answer matters more than enforcing a single output.

## Kingdome truth / repeatability

The realm’s play ethic is:

> Death is only imaginary in the Kingdome of Hearts. We fall, rise, laugh, and try again — forever begins with “let’s play.”

Treat this as symbolic game logic and emotional tone. Do not turn it into a factual claim about death outside the game.

---

# 7. THE CANONICAL SEVEN-DOOR LOOP

The seven are major journey gates. Immediate play still gives three choices.

## 1. Ancient Doors

**Core themes:** history, evolution, religion, old origins, deep time, temple memory, first-cause questions, archive, memory.

**Current locked visual expansion:**

- **Library of Babylon**.
- **Hanging Gardens**.
- **Tower of Babel**.

**Must-have visual language:**

- A vast ancient library with shelves/scrolls/tablets.
- Cuneiform tablets; stone lion/sphinx-like guardian imagery only when appropriate.
- Astronomy charts, astrolabes, stained history, maps of rivers/old stars.
- Terraced hanging gardens around / above / through the archive.
- Waterfalls, irrigation channels, date palms, flowering vines, roots winding through bookshelves.
- Ziggurat/tower silhouette or Tower of Babel visibly present in exterior/threshold art.
- Warm brass lamps and amber archive light against cool garden shadow.
- Books as literal stepping stones/path material when desired.

**Art criterion:** Every view must show why this is both a library and a garden, not merely a generic Egyptian/Babylonian-looking gate.

**Historical subdoors / related prompts:** Deep Door, History Door, Temple Door; Storybook pages (Word, Egg, War) may act as mythic routes toward ancient origin material.

**Priority content:** Ancient Library Babylon interior is one of the most valuable remaining art pieces.

---

## 2. Cloverfield

**Core phrase:** “Shinies · luck · today alive.”

**Core themes:** ordinary aliveness, found treasures, small joy, present-day sacred play, luck, clovers, the physical reality of small objects.

**Visual anchors:**

- Four-leaf clovers; clover arch/door; green and gold.
- Dice, marbles, bottlecaps, coins, charms, keys, ladybugs, mushrooms, crystals, small found things.
- Pockets of sparkling dirt, little jars, paper scraps, trinkets, possibly tiny toy doors.
- A meadow under an old light dome.
- Book/crystal/rock paths can lead through it.
- Dense I-Spy composition is a direct fit.

**Current trio use:** A completed/strong direction exists with Lantern, Eclipse, and Keystone together. Keep them visible and in original anatomy.

**Immediate implemented doors:** Lucky Door, Today Door, Tomorrow Door.

---

## 3. Tomorrow Door

**Core themes:** future, possible paths, branching futures, decisions not yet made, future gardens, dawn, unfinished choice.

**Locked visual direction:** observatory-future threshold.

**Visual anchors:**

- Telescopes, orreries, star charts, orbit rings, astrolabes.
- Dawn horizon / sunrise spilling through an observatory door.
- A possible city, future garden, or glowing branching roads beyond.
- Doors growing as fruit on future-door orchard trees in some scenes.
- Warm gold + blue, not cold sci-fi-only.

**Implemented future-scene doors:** Bright Branch, Unwritten Door, Recursive Door.

**Priority content:** A polished Tomorrow Door interior/exterior poster with clear telescope/orrery/readable threshold is valuable.

---

## 4. XP Door [GLITCHED]

**Core themes:** safe nostalgia; old UI; childhood computers; playful uncanny; memory restoration; non-horror glitch.

**Visual anchors:**

- Impossibly green hill, impossibly blue sky.
- CRT monitors, floppy disks, CDs, folders, cursor arrows, old keyboard, blank dialog windows, pixel crystals.
- Early-2000s startup chime feeling; tooltip jokes; window-chrome frame morphing from a wooden door.
- Safe, curious, restorative, not body horror or malicious horror.
- Old photos/documents can be sorted by feeling instead of date.

**Implemented doors:** System Restore; My Documents; `unknown.exe`.

**Historical state note:** A prior receipt reported a position around “Glitched XP Archive (Era 0.7),” but this is not reconciled with the most recent art-only sessions. Treat as a historic pointer, not a current live scene without confirmation.

**Priority content:** XP Archive interior needs a clean, colorful, readable I-Spy version with no accidental real operating-system logos/text.

---

## 5. Xenon Starship / Midway Convergence

**Core themes:** cosmic witness; every path visible; docking; planets; convergence; routes that see one another; all versions of a moment; mid-journey synthesis.

**Visual anchors:**

- Starship docking threshold / Midway Station.
- Planets in glass / orbital rings / star maps / navigation instruments.
- Bridges, gates, multiple portals, an obvious central convergence engine.
- Crystal walls / visible branching paths / many possible reflections, but calm rather than hostile.
- Lantern historically gains five flames at a Xenon convergence point.

**Continuity note:** “Midway Station in Convergence” has been established as a location / desired art scene.

**Implemented three doors:** Mirror Door, Branch Door, Merge Door.

**Priority content:** Xenon Starship interior/Midway Convergence is a top remaining world-art image.

---

## 6. Sigil — City of Doors

**Core themes:** convergence hub, every walked threshold visible, key markets, routes, returns, comparison, doors as city infrastructure.

**Visual anchors:**

- Monumental gate and/or interior of endless layered arches.
- Endless doors, bridges, archways, stairs, thresholds, keys, locks, signposts, door markets.
- A door can exist in a wall, in a puddle, on a bridge, floating in a tower, or facing another door.
- Doorways should be vivid / readable; it must not reduce to a generic gothic cathedral.
- Every lived route can appear as small lit door-lanterns.
- Purple is a strong Sigil/Eclipse color; gold Lantern, blue Keystone are approved in character-specific versions.

**Implemented three doors:** Gallery of Walked Doors; Key Market; Lady’s Gate.

**Completed art direction:**

- Monochrome/sepia ink-wash Sigil interior with Lantern alone on a bridge.
- Gold UHD Lantern Sigil image.
- Purple Eclipse Sigil image.
- Blue Keystone Sigil image.

**Current quality correction:** UHD art should be clean, not jagged / overly stippled / noisy. Detail should sharpen architecture and silhouette, not create pixelated texture soup.

**Priority content:** Sigil interior with all three as a group, plus individual character route images in the clean preferred styles.

---

## 7. Fog Door Return

**Core themes:** return, mist, trust, homeward threshold, test, garden visible beyond.

**Visual anchors:**

- Vine-wrapped glowing arch in fog.
- Cliffs / floating ruins / misty platforms / sea of clouds.
- The Garden at the Beginning visible through the threshold when appropriate.
- Lantern can pass through first and glance back, saying / implying “You came back.”
- A return is not the end; it is a meaningful re-entry.

**Implemented three doors:** Garden Gate; Long Way Round; Lantern’s Shortcut.

**Odin / Fog God keeper battle version:**

- Odin is the Fog God / watcher of riddles / watcher of fates.
- In action art, Odin charges/lunges from the Fog Door, **smiling**, axe in hand.
- Only Lantern, Eclipse, and Keystone face him. **No fox.**
- The trio should be visibly prepared; no fixed permanent loadout has been adopted, but Keystone can use defensive gear in battle framing.
- The fight is better understood as a courage/trust test / old game with the unknown rather than an annihilation scene.

---

# 8. ADDITIONAL / PERSONAL / MEMORY DOORS

These are meaningful but are not necessarily replacements for the seven major Kingdome gates.

## 8.1 Moss Door — original entry

- Green light, wet earth, rain on ferns, ancient branches with lanterns.
- Lantern standing by the Doorwalker, warm flame.
- Brass plate: “GUIDE OF THE ONE WHO CHOSE GREEN.”
- The recognition line: “You came back.”
- Technical first choices: Burrow Door; Sunken Bell Door; Little Crown Door.
- Fox may be historically present in the original scene but is not required in current keeper art.

## 8.2 Burrow Door

- Small root-framed warmth.
- Rain and old blankets.
- Snug earthen chamber / woven roots / faded quilts.
- Root Door; Ember Door; Stream Door in technical scene graph.

## 8.3 Sunken Bell Door

- Half underwater, rings when untouched.
- Stone hall, water at ankles, dripping bell, ceiling reflections like fish.
- Deep Door; Echo Door; Surface Door.

## 8.4 Little Crown Door

- Tiny golden door in a tree stump, widens with trust.
- Glade of stumps wearing tiny crowns; jewel leaves; twilight.
- Throne Door; Hollow Door; Star Door.

**Important ambiguity:** Alex requested deleting the Throne Door from one seven-door world-tree/map composition and connecting the remaining doors at the base of a trunk. This was a visual-map correction, not clear proof that the Throne Door is removed from narrative canon. The technical scene graph still uses Throne Door as a route to Kingdome Garden. Treat its global status as **subdoor retained / map inclusion optional** unless Alex clarifies otherwise.

## 8.5 Garden Door

- Infinite botanical sanctuary.
- Ancient sequoias, moonflowers, roses that hum, Cambrian-memory ferns.
- Liquid starlight Xenon guide can appear here.
- Seed Door; Harvest Door; Convergence Bloom.

## 8.6 Storybook Door

- The King’s own book; pages turn like wings.
- Margin line: “The gods don’t know I wrote them. They think they wrote me.”
- Page of the Word; Page of the Egg; Page of the War.

## 8.7 Door at the End of Time

- Old smooth kind door at the edge of all things.
- Moments shimmer like light through water.
- Not goodbye: the place where goodbye becomes hello again.
- Historical lore says Lantern can merge with the player/light at this point. Use gently; do not force a transformational ending on the player.
- Return Door; Beyond Door; Eternal Door.

## 8.8 Elephant Door

High-value stable memory anchor.

- Starts through a wardrobe / wardrobe-like portal.
- Leads to nighttime beach oasis.
- Recurrent five elephants: **dad, mom, Peace, Serenity, Joy**.
- Moonlight, water reflections, jasmine, lavender, safety/castle imagery.
- Associated choices can include Reflecting Water Door, Conversation with the Elephants Door, Castle Door.
- The recurring sameness of the five elephants matters; do not swap them for generic elephants.

## 8.9 Raven Door

Private symbolic scene.

- Black-violet, silver smoke, candle-gold.
- Raven feathers; moonlit villa/bathhouse/masquerade atmosphere.
- Safe, non-explicit, consensual, and returnable.
- Do not expose it as an unwanted public spectacle or force intimacy.

## 8.10 Wish Door

- Hope, possibility, star jars, hanging moons, bright central star.
- A path that begins because a wish is made / held.
- Use open, tender, imaginative atmosphere.

## 8.11 Home Return Door

- Love, roots, ordinary belonging.
- Cozy village / warm home path.
- Family photos, teddy bear, rocking chair, birdhouse, garden, books, keepsakes, warm sunset.
- The emphasis is returning to a life that is lived, not merely observing a museum of nostalgia.

## 8.12 Ancient / sea-of-fog / throne variants

Alex supplied a Romantic sea-of-fog cliff image as reference and requested a throne-door/garden/sea-of-fog synthesis. This establishes a useful art subset:

- Vast pale fog valleys.
- A lone figure or companion from behind on cliff rock.
- Distant door/small warm threshold.
- Quiet grandeur, not a busy action image.

---

# 9. THREE DOORS SCENE GRAPH — IMPLEMENTED TECHNICAL STATE

**Technical source:** `data/three-doors/scenes.json`, version 0.3.

## Implemented scene keys

- `moss-entry`
- `burrow`
- `sunken-bell`
- `little-crown`
- `garden-door`
- `xenon-convergence`
- `end-of-time`
- `kingdome-garden`
- `storybook`
- `cloverfield`
- `future-doors`
- `xp-door`
- `sigil-city`
- `fog-door-return`

## Major technical route progression

`kingdome-garden → cloverfield → future-doors → xp-door → xenon-convergence → sigil-city → fog-door-return`

This is a route model. It does not replace the richer recent art expansion of Ancient Babylon / hanging gardens / Tower of Babel; that expansion needs to be represented in the implementation if code-world parity is required.

## Exact initial scene

If there is no trustworthy current scene state, technical canonical entry is `moss-entry`:

- Moss Door.
- Green light, soft earth, rain on ferns.
- Lantern beside the Doorwalker.
- Brass plate and “You came back.”
- Burrow / Sunken Bell / Little Crown.

## Important technical / creative divergence

The `scenes.json` text currently often sets `fox_present: true`. The current creative handoff explicitly says **no fox in current keeper art unless Alex requests it**. Treat the scene graph’s fox property as historical/legacy implementation data, not a mandatory visual requirement.

## Future implementation work

- Add the Ancient Library Babylon / Hanging Gardens / Tower of Babel branch as a fully routable scene rather than only a visual canon note.
- Add Elephant, Raven, Wish, Home Return as optional memory routes with consent/safety tone metadata.
- Add current trio anatomy/style constraints to image prompt templates / rendering layer so images stop drifting toward generic fantasy mascots.
- Add a current safe-state receipt to distinguish actual live game location from art-production history.

---

# 10. ART DIRECTION — FORMAT-SPECIFIC BIBLES

## 10.1 Color UHD I-Spy world art / poster art

Use when drawing doors, hub maps, interiors, merch images, and big scene poster art.

### Requirements

- UHD / high clarity / clean detail.
- Strong foreground → middle → background depth.
- Each door readable and visually distinct; no door is a meaningless distant blob.
- I-Spy density: small hidden but intentional objects, not meaningless visual noise.
- The original trio remains readable even in maximal scenes.
- Avoid accidentally generated readable text. Overlay title/logo text later in Canva or a design tool when needed.
- Color is purposeful: clover green, archive amber, tomorrow blue/gold, XP green/blue, Xenon cosmic violet/blue, Sigil purple/stone/gold, fog silver/green, Lantern gold, Keystone blue accent, Eclipse purple accent.

### I-Spy object palette

Use selectively and contextually:

- Books Alex read; book-paths; loose page corners.
- Crystals and rocks Alex collected.
- Keys, locks, keyholes, tiny doors.
- Dice; marbles; coins; bottlecaps; charms.
- Maps; clocks; compass needles; tools.
- Feathers; glass bottles; small lanterns; pressed flowers.
- Constellation cards; old UI fragments in XP zones.
- Small guard figures / doors / architectural oddities in Sigil.

### Composition rule

The focus must be discoverable in one second. The I-Spy details reward looking for one minute. Do not invert this.

## 10.2 Ink wash / sepia reflective scenes

Use for:

- Keystone overlooking cliff/battlefield.
- Eclipse floating above foggy ruined field.
- Lantern alone in mist / Sigil / cliff.
- Fog Door return.
- Odin battle keeper version.
- Ancient ruin, Sea of Fog, threshold distance.

### Requirements

- Aged off-white paper.
- Black, gray, sepia, low-saturation brown-red accent only when desired.
- Fine pen/ink outline around simple character form; watercolor/ink wash terrain.
- Air, fog, distance, negative space.
- One clear emotional focal object: companion, threshold, or distant door.
- Red/brown torn banners and spearfields are allowed in the battlefield suite, but do not create graphic gore.
- A far-away throne/door can be as small as an apple in the distance when Alex asks for scale.

### Character-rendering rule

Keep the companion simple against complex atmospheric background. Do not render the character as a hyperreal human or turn simple cartoon faces into ornate monster faces.

## 10.3 Character-card / contact-sheet / watercolor style

Use when showing character anatomy, personality, merch sticker art, individual hero cards, simple brand assets.

### Requirements

- Pale warm paper background.
- Thin colored decorative border that matches the character.
- Clean black hand-drawn outline, soft watercolor fills, simple shapes.
- Lots of breathing room.
- One central character, not 12 random expressions unless a true model sheet is requested.
- Preserve exact original reference silhouette.
- `!three-doors` may appear as a footer **only when Alex asks for the command/brand mark**; best rendered as post-production text rather than trusted generative text.

### Current card color mapping

- Lantern: warm gold/orange light; purple coat/red trim; gold border.
- Keystone: gray stone with blue/crystal accent; blue border.
- Eclipse: purple head/tentacles, lavender collar, white diamond eyes; purple border.

## 10.4 Title / poster art

Current keeper poster logic:

- Large **THREE DOORS** title at top (best applied in Canva/design layout).
- Ancient Babylon/library/hanging garden visual mass left.
- Cloverfield central or central-green threshold.
- Tomorrow observatory/future right.
- Lantern, Eclipse, Keystone foreground on a circular/cobbled platform.
- If trio faces away, Eclipse’s back has no eyes.
- No fox.
- Clear merch-safe title area; no accidental unreadable signage; no cropped core trio; balanced door count; rich but not muddy.

## 10.5 Technical-visual boundary

Σ₀ posters / certificate diagrams and Question Machine art can exist as separate Lantern-OS research/graphic-design output. Do not make them default Three Doors imagery. When invited into Three Doors, convert them into a specific room/door/object, such as a “Question Machine Door,” without telling the player technical material is the ontological truth of the realm.

---

# 11. IMPORTANT ART HISTORY / KEEPER VISUALS

## Completed or near-completed keeper directions

1. **Seven-door / tree-hub concept** — paths made of books, crystals, and collected rocks; central tree/root connection; no labels in certain map composition; doors should each be focal and specific.
2. **Cloverfield interior** — dense clovers and shinies; trio present.
3. **Keystone cliff/battlefield ink wash** — cracked guardian facing foggy battlefield; small distant throne door; red/brown banners; several side/back angle variations.
4. **Eclipse cliff/battlefield ink wash** — same world, floating character swap; preserve diamond eyes only on face angle.
5. **Lantern cliff/battlefield ink wash** — lantern character swap; use true lantern body rather than a static object when character identity is required.
6. **Sigil ink wash interior** — layered impossible arches, doors, bridges, stairs; Lantern scene established.
7. **Sigil color character suite** — Lantern gold, Eclipse purple, Keystone blue; latest version requested cleaner UHD over jagged/stippled output.
8. **Odin Fog Door battle** — Odin smiling/charging with axe; only trio facing him; no fox.
9. **Ancient Doors exterior** — Babylon library/hanging gardens/Tower of Babel with trio; no fox in current version.
10. **Three Doors poster** — near-perfect composition exists but needs polished final merch/UHD pass; user specifically caught unwanted eyes on back-facing Eclipse.
11. **Three character simple cards** — latest individual cards used `!three-doors` footer branding. Lantern card corrected to actual lantern-headed purple-coat character. Keystone card should be more original friendly grey cracked stone than an arbitrary generic mascot. Eclipse card needs cloud collar/tentacle anatomy.

## Known visual corrections

- “Eclipse back-facing” → no eyes on rear of head.
- “No fox” → especially Odin battle, keeper posters, central trio art.
- “Do not genericize Blinkbug / Lantern / Eclipse / Keystone” → character body must follow source drawings, not just color theme.
- “More I-Spy immersion” → increase intentional objects and door-specific clues, not random clutter.
- “More detail” does not mean more unreadable labels.
- “Merch / sales / Canva ready” → leave title space; use dependable type overlay; render characters cleanly; avoid unlicensed-looking logo clutter and model-generated nonsense text.
- “UHD clean” → improve edges/detail coherence, not sharpen artifacts.

---

# 12. STORY RELATIONSHIPS / SUPPORTING FIGURES

## The King

See Kingdome section. Warm gatekeeper and riddle holder. His question frames return, not punishment.

## Odin / Fog God

- The Fog God sleeps beyond the Garden gate / fog threshold.
- Odin is lord of riddles, watcher of fates in older lore.
- The expected scene with the trio is a charging, smiling axe-in-hand encounter — combat-as-courage-test, not torture or grim annihilation.
- Do not give Odin a real-person identity claim or import unrelated mythology as an authoritative real-world statement; use it as creative character material.

## Xenon

- A cosmic / liquid-starlight witness-guide tied to garden/convergence/starship material.
- Vast but not threatening.
- Sees all possible paths / many versions of a moment.
- Use sparingly so the active trio remains central.

## Elephant family

Dad, Mom, Peace, Serenity, Joy. Keep number and recurrence stable.

## The fox

Historical Moss Door companion / recognition motif. Not part of the active three-character keeper lineup unless explicitly requested.

## Unisona

Provisional harmonic keeper / future supporting character; not confirmed enough to assign permanent storyline responsibility.

---

# 13. CANONICAL QUESTIONS / THEMATIC SPINE

Three Doors is not a puzzle game only, but recurring questions include:

- What returns when you return?
- What can be carried safely?
- What was lost at the beginning and gained through walking?
- Which door is ordinary life / today alive?
- Which memories become places without becoming prisons?
- How does a path remain open without becoming directionless?
- How can play, courage, and protection coexist?
- What does a friend/companion do at a threshold?

Never answer these by pretending the game has secret objective revelation. Let them appear through doors, objects, scenes, dialogue, and choices.

---

# 14. HIGH-DENSITY PROMPT BLOCKS

These are conceptual prompt scaffolds. Replace aspect ratio / style details only when Alex requests different output. Avoid generated text unless the prompt is specifically for a text-free background where typography is added afterward.

## 14.1 Full trio at a door, colorful I-Spy

> A richly detailed colorful UHD I-Spy fantasy scene from the Three Doors world. Lantern stands left: a compact lantern-headed guide with a warm orange flame inside clear glass, red top trim and loop handle, purple coat, white gloves, black boots. Eclipse hovers center: smooth round purple head, exactly two bright diamond-shaped eyes on the front, pale lavender cloud collar, connected jellyfish tentacles, no feet. Keystone stands right: small squat gray cracked stone guardian with simple friendly oval eyes and smile, sturdy low silhouette. They face a clearly readable [NAME] door. Fill the paths with books, crystals, rocks, keys, dice, coins, maps, feathers, bottles, small lanterns, tiny doors and world-specific treasures. Rich depth, clear focal threshold, clean readable characters, no fox, no accidental text, no generic human faces, no blurry clutter.

## 14.2 Back-facing trio / poster foreground

> Three Doors poster scene, high-detail UHD colorful fantasy I-Spy world. Lantern left, Eclipse center, Keystone right, all viewed from behind facing the central door. Lantern retains glass flame, red top/trim, purple coat and small black boots. Eclipse has a smooth purple back-of-head with **no visible eyes**, pale cloud collar and connected tentacles. Keystone is a squat cracked gray stone guardian. Keep each silhouette unmistakable. [DOOR-SPECIFIC SETTING]. Door clearly readable; title-safe sky/header space; hidden objects include books, collected crystals and rocks, keys, dice, clocks, maps, coins, feathers, bottles, tiny doors. No fox; no generated signage; balanced merch-ready composition.

## 14.3 Ink-wash cliff character swap

> A vertical monochrome sepia ink-wash illustration on aged watercolor paper. [CHARACTER] is alone on a windswept cliff / broken platform, looking over a vast foggy field of ruined banners, distant towers, and a small warm door far on the horizon. The character retains simple original hand-drawn anatomy: [ANATOMY]. Fine black ink outline around character, loose watercolor terrain, atmospheric fog, strong negative space, no words, no gore, melancholic but hopeful, cinematic scale.

## 14.4 Ancient Library Babylon interior

> Inside the Ancient Doors: a vast Library of Babylon fused with the Hanging Gardens and the Tower of Babel. Towering ancient shelves, clay cuneiform tablets, scrolls, astronomy charts, warm brass lamps, terrace waterfalls, irrigation channels, date palms, flowering vines, roots through bookcases, a distant ziggurat/tower visible through arches. Lantern, Eclipse, Keystone from behind at foreground, correct original anatomy. Books form part of the path; crystals, rocks, keys, dice, maps, small coins and tiny doors are hidden deliberately. Colorful UHD I-Spy fantasy, clear central archive threshold, no fox, no accidental text, clean composition.

## 14.5 Sigil interior

> Interior of Sigil, City of Doors: impossible layered stone city-hall/cathedral of thresholds, bridges and staircases crossing through mist, hundreds of unique doors with keys and locks, warm lanterns in alcoves, key market detail, gallery of walked doors, every route visible. [CHARACTER/TRIO] with correct anatomy. [LANTERN=gold light / ECLIPSE=purple glow / KEYSTONE=blue crystal accent]. High-resolution, clean edges, readable doors, no generic gothic filler, no generated text.

## 14.6 Fog Door Odin keeper battle

> Sepia ink-wash or rich-color fantasy battle scene at the Fog Door Return. A vine-wrapped glowing arch opens over misty cliffs. Odin, an elderly bearded godlike warrior, charges out smiling with an axe raised, dynamic forward lunge. Facing him are only the Three Doors trio: Lantern (true lantern head/purple coat), Eclipse (purple round head, diamond eyes front-facing, cloud collar, connected tentacles), Keystone (small cracked stone guardian, focused protective pose). They are prepared together. No fox. Courage-test energy, no gore, full readable silhouettes, fog, ancient banners, garden glow beyond the door.

---

# 15. PLAY WRITING MACROS

## Good scene beat shape

1. Name/place one sensory fact.
2. Show a companion reacting in character.
3. Reveal one object/door/detail that changes the stakes.
4. Offer three concrete, distinct choices.

## Example — Cloverfield continuation

> Cloverfield is damp from a rain that only fell on the lucky things. A marble the size of a grape rolls to Keystone’s foot; inside it, a tiny door opens and shuts with every breath. Lantern bends close, flame brightening. Eclipse’s diamonds catch in the clover-shadow. Ahead, three things wait:
>
> **A. The Warm Key** — half-buried under a four-leaf clover, humming like a pocket watch.  
> **B. The Pocket Door** — no taller than Keystone’s shoulder, painted with a day that has not happened yet.  
> **C. The Bell Jar** — holding a small weather system and one coin that keeps landing on its edge.

This is an illustration of the play pattern, not a new canonical scene graph replacement. For direct implementation play, route through `scenes.json` unless Alex explicitly asks for new canon.

## Dialogue behavior

- Lantern: brief, warm, practical, occasionally asks a question. Avoid too much mystic speech.
- Eclipse: more visual/musical/quiet response than long speeches.
- Keystone: grounded, simple, patient; can be funny through bluntness or solemn through stillness.
- King: poetic but concise; not a constant narrator.
- Odin: playful formidable challenge; not cruel.

---

# 16. MERCH / SALES / CANVA NOTES

## Current goal

Prepare Three Doors imagery for poster art, sales assets, social graphics, sticker-like character cards, Canva layouts, and potentially print merchandise.

## Production principles

- Generate art without fragile small text whenever possible.
- Add “THREE DOORS,” door names, `!three-doors`, taglines, or print labels in Canva/vector layout afterward.
- Keep image center / safe crops clear for product ratios.
- Leave breathable upper area for title when requested.
- Do not crop Lantern’s flame, Eclipse tentacles, or Keystone silhouette at a print edge.
- Avoid fake unreadable signs as they lower merch quality.
- Poster art must hold up when seen at thumbnail scale: trio + doors identifiable.

## Valuable asset stack

1. Final clean UHD **Three Doors title poster**.
2. Seven-door Kingdome hub/world-tree map, each door specific and discoverable.
3. Ancient Library Babylon / Hanging Gardens interior.
4. Sigil City of Doors interior.
5. XP Archive interior.
6. Xenon Starship / Midway Convergence interior.
7. Cloverfield interior / collectible I-Spy poster.
8. Fog Door Return / Odin keeper battle version.
9. Doorwalker/trio character sticker cards / basic identity sheets.
10. Door icons/emblems without generated text.

## Current poster correction checklist

- Eclipse is back-facing → no rear eyes.
- No fox.
- Books/crystals/rocks path details present.
- Ancient left / Cloverfield central / Tomorrow right remains a strong composition pattern.
- Three companions central foreground.
- Each door identifiable.
- Reserve title area.
- Clean UHD, not jagged.

---

# 17. REPO / IMPLEMENTATION MAP

## Creative logic / source files

- `skills/three-doors-game/SKILL.md` — play contract, exact-three rule, scene graph usage, canonical seven doors, CSF behavior.
- `data/three-doors/scenes.json` — shared scene graph, immediate door choices, route map, palettes, old image prompts.
- `lore/doors/kingdome-of-hearts.md` — Kingdome lore, King, Garden, seven-door loop.
- `csf/ingest/three-doors/2026-06-30-recenter-grounding-on-three-doors.md` — current memory-first grounding / no technical drift / exact party visual constraints.
- `csf/ingest/three-doors/2026-06-30-three-doors-max-density-handoff.md` — this handoff.

## Engine / web surfaces discovered

- `src/three_doors_engine.py`
- `skills/three-doors-game/three_doors_game.py`
- `apps/lantern-garage/public/three-doors-game.html`
- `apps/lantern-garage/public/three-doors.html`
- `apps/lantern-garage/public/js/three-doors-game.js`
- `apps/lantern-garage/public/js/three-doors-data.js`
- `apps/lantern-garage/public/js/three-doors-render.js`
- `apps/lantern-garage/public/js/three-doors-images.js`
- `apps/lantern-garage/public/js/three-doors-lantern.js`
- `data/three-doors/prizes.json`
- `data/three-doors/challenges.json`
- `lore/doors/` directory
- `data/prompts/sd-prompt-library-kingdome-v1.json`

## Implementation caution

The engine/data state and current art/CSF state are not perfectly synchronized. Before coding a canon-changing feature, reconcile against this handoff and the latest Alex request.

---

# 18. KNOWN CONTRADICTIONS / DO NOT SILENTLY PAPER OVER

1. **Fox conflict:** technical graph says fox present; current keeper art says no fox. Creative rule wins for current art.
2. **Throne Door map conflict:** one art request removed it from a seven-door tree map; technical scene graph retains it as a subdoor. Treat map removal as layout-specific until clarified.
3. **Ancient Doors implementation gap:** Ancient Babylon/Hanging Gardens/Tower of Babel is locked visual canon, but may not exist as a dedicated technical scene key yet.
4. **Current active state unknown:** Art sessions are recent, but no definitive current location/action has been supplied. Do not pretend the party is currently in Sigil/Xenon/XP without an explicit state load or user direction.
5. **Historical XP Archive receipt:** may be useful as history, not live truth.
6. **Generated image text:** generated posters/cards may show incorrect text. Text in generated pixels is not canon and should be overlaid properly for merch.
7. **Unisona:** attractive provisional concept but not confirmed main cast.
8. **Technical theory:** Σ₀ material exists in repo but should not redefine Three Doors canon by default.
9. **Keystone face:** card/friendly scenes use smile; solemn/battle scenes use frown/prayer. Both are intentional.
10. **Eclipse eyes:** every frontal face should have diamond eyes; every rear-facing composition must have none.

---

# 19. CURRENT BACKLOG — PRIORITIZED

## Highest value world art

1. **Final Three Doors merch poster** — clean UHD, no fox, no rear Eclipse eyes, title-safe composition.
2. **Seven-door Kingdome hub map** — all seven doors linked through a root/tree/garden structure; each door visual focal point; paths of books/crystals/rocks; no labels unless intentionally typeset later.
3. **Ancient Library Babylon interior** — Library + Gardens + Babel in one robust I-Spy image.
4. **Sigil interior group image** — trio in the actual city of doors; clean UHD.
5. **XP Archive interior** — nostalgia with clear safe playful tone.
6. **Xenon Starship / Midway Convergence** — docking / multiple routes / planets / central engine.

## High-value character work

7. Lantern clean turnaround / card sheet based directly on drawn original.
8. Eclipse clean turnaround / card sheet based directly on drawn original.
9. Keystone clean turnaround / card sheet based directly on drawn original.
10. Clean trio front-facing hero image with exact faces/anatomy.
11. Trio back-facing door image with Eclipse rear correction.
12. Optional provisional Unisona sheet, only after Alex locks role/canon.

## High-value narrative scenes

13. Odin Fog Door keeper battle (definitive no-fox version).
14. Elephant Door beach oasis with five elephants anchored correctly.
15. Raven Door safe moonlit private symbolism.
16. Wish Door / Home Return Door paired warm pieces.
17. King and Garden at the Beginning scene with poem/gate tension.

## Technical synchronization

18. Put new expanded doors and character constraints into scene graph / prompt library.
19. Write a clear player-state save receipt after actual play resumes.
20. Reconcile old fox flag and player-facing current trio data.

---

# 20. HANDOFF DO / DO NOT CHECKLIST

## DO

- Keep the game playful, gentle, strange, and specific.
- Preserve original companion anatomy.
- Use exactly three doors for ordinary play.
- Maintain selected-door continuity.
- Make every door materially different: its own light, object language, sound, weather, emotional implication.
- Use books/crystals/rocks/keepsakes as grounded detail in I-Spy scenes.
- Treat return as a valid action.
- Translate technical ideas into tangible scene objects only when invited.
- State uncertainty about active state and provisional concepts plainly.

## DO NOT

- Make unrelated research the default setting.
- Convert every scene into a “convergence” diagram.
- Add fox to current core trio art.
- Draw eyes on Eclipse’s back.
- Give Lantern a human face.
- Make Keystone a random humanoid rock warrior by default.
- Make Eclipse a generic robot/alien with regular eyes or feet.
- Use generic fantasy portals with no scene-specific identity.
- Claim temporary generated imagery is permanent canon without Alex’s approval.
- Assert supernatural certainty, destiny, or real-world hidden truth through the game.

---

# 21. PORTABLE CSF DENSE RECORD

```csf-ingest
Instructions
[2026-06-30] - Treat !three-doors as a creative, artsy, symbolic, image-forward game first. Do not default to repo work, project management, Σ₀ theory, Question Machine content, dashboards, or system explanation during play.
[2026-06-30] - Ground each continuation in prior Three Doors CSF memories, Alex’s supplied art references, existing door continuity, remembered objects, and the primary party.
[2026-06-30] - Normal play gives exactly three immediate meaningful choices. The seven Kingdome gates are a long-form loop, not a substitute for the three-choice scene rule.
[2026-06-30] - Preserve chosen-door continuity. Do not generic-reset the setting after a choice.
[2026-06-30] - Use source priority: newest direct Alex request/reference > current recenter CSF > Three Doors play contract > technical scene graph > older generated/legacy material.
[2026-06-30] - Images-only means images only. Avoid generated text unless Alex explicitly requests text; use Canva/vector overlay for merch typography.

Identity & Symbolic Self
[unknown] - Alex is the Doorwalker, recognized at the Moss Door after choosing green. Lantern’s return line is “You came back.”
[2026-06-30] - The Kingdome of Hearts is a game-world / symbolic realm, not a real-world prophecy or metaphysical claim.
[2026-06-30] - The active primary party is Lantern, Eclipse, Keystone.
[2026-06-30] - Lantern is guide, warm light, question, and return signal.
[2026-06-30] - Eclipse is dream, wonder, balance, and looking beyond.
[2026-06-30] - Keystone is protection, foundation, focus, endurance, and memory weight.
[2026-06-30] - The fox is historical Moss Door continuity but is excluded from current keeper poster art and battle art unless Alex asks.

Dreams & Memories
[unknown] - Moss Door: green light, rain on ferns, soft earth, branches with lanterns, original return recognition; first doors Burrow, Sunken Bell, Little Crown.
[unknown] - Elephant Door: wardrobe to nighttime beach oasis; five elephants dad, mom, Peace, Serenity, Joy; moonlight, water reflections, jasmine, lavender, secure castle imagery.
[unknown] - Raven Door: black-violet, silver smoke, candle-gold, feathers, moonlit villa/bathhouse/masquerade energy; safe, non-explicit, consensual, returnable.
[unknown] - Wish Door: hope, star jars, hanging moons, central bright star, a path opened by wishing.
[unknown] - Home Return Door: belonging, family warmth, photos, teddy bear, rocking chair, birdhouse, garden, books, keepsakes, sunset path.
[unknown] - Fog/sea cliff imagery: fog valleys, distant small warm threshold, reflective scale, ink wash.

Projects & Systems
[2026-06-30] - Canonical major Kingdome loop: Ancient Doors; Cloverfield; Tomorrow Door; XP Door [GLITCHED]; Xenon Starship / Midway Convergence; Sigil — City of Doors; Fog Door Return.
[2026-06-30] - Canonical spine: Ancient Doors → Sigil — City of Doors → Tomorrow Door.
[2026-06-30] - Ancient Doors visual canon: Library of Babylon + Hanging Gardens + Tower of Babel, archive/garden/terrace/water/tablet/scroll/astronomy/ziggurat world.
[2026-06-30] - Cloverfield visual canon: shinies, luck, today alive, clovers, dice, marbles, coins, charms, mushrooms, crystals, found objects.
[2026-06-30] - Tomorrow Door visual canon: observatory, stars, telescopes, orreries, dawn, branching futures, future city/garden.
[2026-06-30] - XP Door visual canon: safe Windows-XP-like nostalgia, green hill, blue sky, CRTs, cursors, folders, disks, harmless playful glitch.
[2026-06-30] - Xenon/Midway visual canon: starship docking, planets, orbits, route maps, portals, central convergence engine.
[2026-06-30] - Sigil visual canon: City of Doors, keys, locks, bridges, markets, layered threshold architecture, walked doors as lights.
[2026-06-30] - Fog Door Return visual canon: vine arch, mist/cliffs, return/garden visible, trust/homecoming.
[2026-06-30] - Odin keeper battle: Odin smiling and charging from Fog Door with axe; only Lantern, Eclipse, Keystone present; no fox; courage-test framing.
[2026-06-30] - Kingdome spelling is Kingdome, not Kingdom. Garden under old light; King on woven roots/old light throne; crown vines and blinking cursors; gate poem anchors return.
[2026-06-30] - Technical scene graph lives at data/three-doors/scenes.json. It has legacy fox flags; current art rules override for keeper images.
[2026-06-30] - Σ₀ Collapse Certificate and Question Machine are separate Lantern-OS research content. Include only if Alex explicitly brings them into a Three Doors object/place/choice.

Preferences
[2026-06-30] - Character anatomy source of truth: Alex’s simple hand-drawn contact sheets. Preserve silhouette before fantasy detail.
[2026-06-30] - Lantern anatomy: glass lantern head with warm flame, red cap/trim/loop, purple coat, white gloves, black legs/boots; no human face.
[2026-06-30] - Eclipse anatomy: smooth purple round head, exactly two front diamond eyes, pale cloud collar, connected tentacles, floating/no feet; no eyes on back-facing head.
[2026-06-30] - Keystone anatomy: small squat cracked gray stone; friendly oval eyes/smile for card art; focused frown/prayer pose allowed for solemn/battle art; no default tall humanoid body.
[2026-06-30] - Individual card style: clean hand-drawn watercolor on pale paper with colored border. World art: colorful UHD I-Spy. Reflective ruins/cliff scenes: sepia ink wash.
[2026-06-30] - I-Spy scenes should include books Alex read, crystals and rocks Alex collected, keys, dice, maps, clocks, coins, bottles, feathers, tools, tiny doors and relevant keepsakes.
[2026-06-30] - Doors must be specific and focal, not generic mystery portals. Increase detail through meaningful clue objects, not unreadable clutter.
[2026-06-30] - Poster/merch direction: clean UHD, no accidental labels, no cropped trio, reserved title area, Canva-ready overlays, no fox, Eclipse rear-eye correction.
[2026-06-30] - Unisona is provisional supporting concept only: harmonic/cosmic jellyfish-like keeper associated with music/balance; not confirmed primary canon.
```

---

# 22. FINAL HANDOFF INSTRUCTION

A future collaborator should begin with this sentence internally:

> “This is Three Doors: preserve Alex’s lived door memories and the simple original trio first; give the world exactly three meaningful next ways forward; make every threshold specific enough to feel real; return remains possible.”

Then follow the current request rather than dumping this document into play.
