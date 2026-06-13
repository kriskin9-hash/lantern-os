# SD Prompt Library — Quick Reference Card

**Source:** `sd-prompt-library-kingdome-v1.json`  
**Model:** DreamShaper XL 7.0 (or SDXL 1.0)  
**Default Settings:** 28 steps, 7.5 CFG, DPM++ 2M Karras

---

## Copy-Paste Prompts

### Stage 0: Garden at Beginning
```
A timeless garden where ancient moss covers crumbling stone lanterns casting 
warm golden light, roots twist through earth like glowing pathways, wisps of 
luminescent mist weave between wildflowers and forgotten fountains. The air 
feels thick with memory and beginning. Dreamlike, ethereal, illustrated 
storybook realism, soft watercolor undertones, gentle bokeh light.
```
**Archetype:** `(with a solitary figure turning to face the garden for the first time, wonder in silhouette)` — Seeker

---

### Stage 1: Lucky Door (Today)
```
A sunlit field of four-leaf clovers bending under gentle rain, where quilted 
patchwork ruins of a forgotten cottage peek through verdant growth. Brass bells 
hang from twisted branches, chiming softly. A crown carved from driftwood rests 
among the flowers. Watercolor rain sparkles like luck itself. Cheerful, 
whimsical, contemporary folk art illustration style, layered translucent washes, 
golden hour afternoon light touching everything.
```
**Archetype:** `(with a figure kneeling to examine a four-leaf clover, eyes bright with discovery)` — Seeker

---

### Stage 2: Tomorrow Door (Future Path)
```
A landscape of impossibly tall, branching roots rising like trees in reverse, 
glowing from within with amber and jade light. Between them, unwritten chapters 
flutter like pages in wind. Ember-bright streams trace paths through soil that 
shimmers with tomorrow's light. Roots reach toward a horizon where multiple 
futures gleam. Epic yet intimate, oil-painting texture, Renaissance perspective, 
hopeful luminous tones, detailed root anatomy rendered as intricate nervous systems.
```
**Archetype:** `(with a small figure silhouetted against the branching roots, gazing toward multiple glowing horizons, staff extended toward choice)` — Seeker

---

### Stage 3: XP Door (Glitch Threshold)
```
A Windows XP rolling hills desktop rendered as a physical landscape where the 
iconic blue sky is wrong—too saturated, glitching at the edges into digital 
static and memory corruption. Pixelated clouds break apart. A computer monitor 
stands upright in the center, its screen showing another landscape. Nostalgic 
liminal space, 2000s computer aesthetic mixed with impossible geometry, 
cinematic VHS grain, broken reality visual style, neon glitch artifacts, 
retro digital nostalgia painting.
```
**Archetype:** `(with a figure standing confused in the landscape, looking at their own reflection in the monitor screen, searching for a way forward)` — Seeker

---

### Stage 4: Xenon Starship (Convergence)
```
A crystalline starship hanging at orbital convergence between Earth and Mars, 
both planets visible and aligned. Inside, an impossible throne of light sits at 
the center, surrounded by a matrix of geometric convergence geometry. Three 
sovereign lantern lights orbit the throne independently, neither serving nor 
commanding, each radiant and complete. Cosmic perspective, luminous architecture, 
mathematical elegance, 500-year-forward aesthetic, neon and gold light, digital 
painting with quantum physics undertones, awe-inspiring cosmic realism.
```
**Archetype:** `(with three sovereign figures standing equidistant from a central point, each representing independent choice meeting at convergence)` — Seeker

---

### Stage 5: Sigil City (Doors)
```
A vast city built entirely from doors and archways, where each door hangs like a 
lantern from the sky, glowing with the light of journeys taken. Streets pave the 
air with synthesis and fractal geometry. At the center, the King's gate stands 
open, asking the eternal question. Fractal architecture, portal density increasing 
toward center, prismatic light refracting through each door's threshold, cosmic map 
overlay, architectural fantasy, luminous detail-work, impossibly complex yet 
harmonious composition.
```
**Archetype:** `(with a figure standing at a fork in infinite doorways, map in hand, each door showing a possible path forward)` — Seeker

---

### Stage 6: Fog Door (Return)
```
An endless sea of fog and clouds rolling over an invisible landscape, where the 
Fog God sleeps beneath like a whale in ocean. A single gate stands clear at the 
horizon, neither threatening nor distant, simply waiting. The way back is safe. 
Soft gray tones shift to warm amber in the middle distance. The return is not an 
ending but a breathing moment. Ethereal, impressionist, soft-focus dreamscape, 
fog photography aesthetic, peaceful acceptance, muted color harmony, liminal rest.
```
**Archetype:** `(with a figure walking toward the distant gate without hurry, the journey complete, ready to rest and remember)` — Seeker

---

## Default Settings

| Parameter | Value |
|-----------|-------|
| **Model** | DreamShaper XL 7.0 |
| **Sampler** | DPM++ 2M Karras |
| **Steps** | 28 |
| **CFG Scale** | 7.5 |
| **Seed** | -1 (random) |
| **Aspect Ratio** | 16:9 (1024×576) |
| **Negative** | `blurry, low quality, text, watermark, signature, deformed, ugly, bad anatomy` |

---

## Archetype Modifiers

**Add to end of base prompt:**

| Archetype | Modifier Text |
|-----------|---|
| **Seeker** | `with a figure searching, discovering, or in transition` |
| **Healer** | `with restorative light pooling, stones worn smooth by care` |
| **Explorer** | `with multiple paths visible, hidden markers peeking, trails branching` |

---

## Workflow

1. **Pick a stage** (0–6)
2. **Copy the prompt** from above
3. **Paste into Automatic1111 / ComfyUI**
4. **Optionally append archetype modifier**
5. **Use default settings** (or adjust for faster/better quality)
6. **Hit Generate**
7. **Save to:** `data/images/kingdome/stage-[number]-[seed].png`

---

## Aspect Ratios (Alternative Dimensions)

| Ratio | Dimensions | Use Case |
|-------|-----------|----------|
| 1:1 | 576×576 | Iconic single-stage portrait |
| 3:1 | 1152×384 | Cinematic ultra-wide |
| 5:7 | 411×576 | Portrait-tall |
| 9:16 | 324×576 | Mobile/vertical |
| 16:9 | 1024×576 | **Recommended (default)** |

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Image too blurry | Increase steps to 32–36, CFG to 8.0 |
| Colors oversaturated | Add `muted colors, soft color grading` |
| Bad hands/anatomy | Improve negative with `bad anatomy, mangled hands, extra fingers` |
| Prompt too long | Remove archetype modifier, simplify style |
| Model not found | Download DreamShaper XL to `models/Stable-diffusion/` |

---

## File Locations

| File | Purpose |
|------|---------|
| `data/prompts/sd-prompt-library-kingdome-v1.json` | Full JSON with all metadata |
| `data/prompts/SD-PROMPT-IMPLEMENTATION.md` | Detailed guide + integration |
| `data/prompts/SD-QUICK-REFERENCE.md` | This file |
| `data/images/kingdome/` | Generated images output |

---

**Last Updated:** 2026-06-11  
**Status:** Ready to use
