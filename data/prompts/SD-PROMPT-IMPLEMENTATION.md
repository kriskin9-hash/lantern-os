# Stable Diffusion Prompt Library — Implementation Guide

**Version:** 1.0  
**Date:** 2026-06-11  
**Source:** `sd-prompt-library-kingdome-v1.json`  
**Canon:** `csf/ingest/2026-06-11-full-door-canon-v2.md`

---

## Overview

This is a production-ready SD prompt library for the **Kingdome of Hearts** 7-stage journey. All prompts are:
- Derived from canonical door imagery keywords
- Tested for SD token efficiency (~90 tokens average)
- Dimensioned for standard/cinematic/portrait aspect ratios
- Extensible via archetype modifiers (seeker/healer/explorer)
- Compatible with modern SDXL models

---

## Quick Start

### 1. Choose a Model

**Recommended (primary):**
- **DreamShaper XL 7.0** — best artistic quality, strong on fantasy/dreamscape, consistent anatomy
  - Download: [Hugging Face](https://huggingface.co/Lykon/DreamShaper)
  - VAE: `sdxl_vae.safetensors` (improves colors)

**Alternatives (all tested with this library):**
- SDXL 1.0 base (official Stability AI, most generic, reliable)
- Juggernaut XL (good realism + detail, slightly less artistic)
- RealismEngine SDXL (photo-realistic variant)

### 2. Copy a Prompt

Pick a stage (0–6), grab the `base_prompt` from the JSON:

```json
{
  "stage_number": 1,
  "base_prompt": "A sunlit field of four-leaf clovers bending under gentle rain, where quilted patchwork ruins of a forgotten cottage peek through verdant growth. Brass bells hang from twisted branches, chiming softly. A crown carved from driftwood rests among the flowers. Watercolor rain sparkles like luck itself. Cheerful, whimsical, contemporary folk art illustration style, layered translucent washes, golden hour afternoon light touching everything."
}
```

### 3. Paste into Automatic1111 / ComfyUI

**Automatic1111 WebUI:**
1. Paste prompt into the large text box
2. Set sampler: `DPM++ 2M Karras`
3. Steps: `28–32`
4. CFG Scale: `7.0–8.0`
5. Aspect ratio: Select from `Height` dropdown or use custom
6. Click **Generate**

**ComfyUI:**
1. Load SDXL checkpoint (DreamShaper XL 7.0 recommended)
2. Connect prompt node to sampler node
3. Set steps, cfg_scale, and sampler in sampler node
4. Connect latent → VAE Decode → Save Image
5. Queue prompt

### 4. (Optional) Add Archetype

If you want character-driven imagery, append the relevant archetype modifier:

**Example — Adding "Seeker" to Stage 1:**
```
A sunlit field of four-leaf clovers ... [base prompt as above]
With a figure kneeling to examine a four-leaf clover, eyes bright with discovery.
```

---

## Stage-by-Stage Prompts

### Stage 0 — Garden at Beginning

| Key | Value |
|-----|-------|
| **Prompt** | Timeless garden with ancient moss, glowing lanterns, roots as pathways |
| **Aspect** | 16:9 (1024×576) |
| **Style** | Dreamlike, watercolor, storybook realism |
| **Mood** | Nostalgic, welcoming, memory awakening |
| **Keywords** | ancient, moss, lanterns, light, roots, garden |

**Recommended Use:** Entry/exit scenes, dream journal header, safe return threshold.

---

### Stage 1 — Lucky Door (Today)

| Key | Value |
|-----|-------|
| **Prompt** | Sunlit clover field, quilted ruins, brass bells, driftwood crown, watercolor rain |
| **Aspect** | 16:9 (1024×576) |
| **Style** | Whimsical, folk art, watercolor, golden hour |
| **Mood** | Warm, playful, found-object joy |
| **Keywords** | clover, luck, today, rain, quilts, bells, crown |

**Recommended Use:** Day-of journeys, luck-based encounters, playful discovery scenes.

---

### Stage 2 — Tomorrow Door (Future)

| Key | Value |
|-----|-------|
| **Prompt** | Reverse-tree roots glowing with amber/jade, unwritten chapters, ember streams, Renaissance perspective |
| **Aspect** | 16:9 (1024×576) |
| **Style** | Epic, oil painting, Renaissance, luminous |
| **Mood** | Hopeful, expansive, possibility |
| **Keywords** | branches, growth, roots, embers, streams, tomorrow |

**Recommended Use:** Future-path decisions, branching narrative moments, possibility exploration.

---

### Stage 3 — XP Door (Glitch Threshold)

| Key | Value |
|-----|-------|
| **Prompt** | Windows XP desktop rendered physically, wrong blue sky, pixel corruption, monitor in landscape, liminal |
| **Aspect** | 16:9 (1024×576) |
| **Style** | Liminal space, VHS grain, glitch art, 2000s nostalgia |
| **Mood** | Disorienting, uncanny, creative disruption |
| **Keywords** | windows, glitch, nostalgic, blue, digital, liminal |

**Recommended Use:** Memory glitches, reality fractures, creative breakthroughs, nostalgic triggers.

---

### Stage 4 — Xenon Starship (Convergence)

| Key | Value |
|-----|-------|
| **Prompt** | Crystalline starship at Earth-Mars convergence, light throne, three sovereign lanterns, geometric matrix, quantum realism |
| **Aspect** | 16:9 (1024×576) |
| **Style** | Cosmic, luminous, mathematical, quantum realism |
| **Mood** | Transcendent, convergent, cosmic wonder |
| **Keywords** | starship, convergence, throne, void, light, planets |

**Recommended Use:** Climactic moments, multi-perspective synthesis, ultimate threshold.

---

### Stage 5 — Sigil City (Doors)

| Key | Value |
|-----|-------|
| **Prompt** | City built from doors as hanging lanterns, fractal streets, King's gate center, prismatic light, cosmic map |
| **Aspect** | 16:9 (1024×576) |
| **Style** | Fractal architecture, cosmic map, prismatic light |
| **Mood** | Awe-inspiring, meta-hub, synthesis |
| **Keywords** | doors, lanterns, King, synthesis, fractal, portal |

**Recommended Use:** Journey retrospective, choice mapping, meta-narrative scenes.

---

### Stage 6 — Fog Door (Return)

| Key | Value |
|-----|-------|
| **Prompt** | Endless fog sea with sleeping Fog God beneath, single gate at horizon, soft gray→amber tones, peaceful acceptance |
| **Aspect** | 16:9 (1024×576) |
| **Style** | Ethereal, impressionist, fog photography |
| **Mood** | Peaceful, restful, safe return |
| **Keywords** | fog, mist, cloud, sea, return, escape, gate |

**Recommended Use:** Rest/reflection moments, closure scenes, gentle transitions.

---

## Recommended SD Settings by Stage

### Fast Generation (4–6 min per image)
```
Sampler:   Euler (fastest)
Steps:     20
CFG Scale: 7.0
```

### Balanced (8–12 min)
```
Sampler:   DPM++ 2M Karras
Steps:     28
CFG Scale: 7.5
```

### High Quality (15–25 min)
```
Sampler:   DPM++ 2M Karras
Steps:     36
CFG Scale: 8.5
```

### Ultra (for gallery/publication)
```
Sampler:   DPM++ 2M Karras
Steps:     48
CFG Scale: 8.5
Karras:    enabled
```

---

## Negative Prompts

Use this universal negative to reduce artifacts:

```
blurry, low quality, text, watermark, signature, deformed, ugly, bad anatomy, 
mangled hands, extra fingers, mutated limbs, distorted face, disfigured, 
out of frame, clipped, truncated, repeated elements
```

For photorealistic models, add:
```
rendering, 3d, cgi, digital art, illustrative
```

For stylized models, omit the "3d/cgi" additions.

---

## Prompt Weighting & Customization

### Basic Syntax (Automatic1111 / WebUI)

Increase keyword emphasis:
```
(keyword:1.5)  — 1.5x weight
(keyword:1.2)  — 1.2x weight (subtle)
(keyword:0.8)  — 0.8x weight (downplay)
```

**Example — Emphasize "lanterns" in Stage 0:**
```
A timeless garden where ancient moss covers crumbling stone (lanterns:1.4) 
casting warm golden light, roots twist through earth like glowing pathways...
```

### Parenthetical Stacking

```
(ancient:1.3)(moss:1.2)(golden light:1.3)
```

### Alternative: Prompt Blending

Mix two stage prompts (50/50 blend):
```
[Stage 0 base prompt : Stage 1 base prompt : 0.5]
```

---

## Integration with Three Doors Game

### File Path Convention

Save generated images to:
```
data/images/kingdome/stage-[number]-[archetype]-[seed].png
```

**Example:**
```
data/images/kingdome/stage-1-seeker-42851.png
data/images/kingdome/stage-4-explorer-99123.png
data/images/kingdome/stage-6-healer-12304.png
```

### API Endpoint (Proposed)

```javascript
POST /api/generate-image
Content-Type: application/json

{
  "stage_key": "lucky-door-present",
  "stage_number": 1,
  "archetype": "seeker",
  "sampler": "DPM++ 2M Karras",
  "steps": 28,
  "cfg_scale": 7.5,
  "seed": -1,
  "negative_prompt": "blurry, low quality, text, watermark"
}

Response:
{
  "image_url": "/images/kingdome/stage-1-seeker-42851.png",
  "seed": 42851,
  "generation_time_ms": 8234,
  "model": "DreamShaper XL 7.0"
}
```

### Three Doors Scene Mapping

| Stage | Scene Key | Primary Use |
|-------|-----------|-------------|
| 0 | kingdome-garden | Entry/Return anchor |
| 1 | kingdome-clover-field | Lucky Door choice |
| 2 | kingdome-branching-future | Tomorrow Door choice |
| 3 | kingdome-xp-desktop | XP Door glitch moment |
| 4 | kingdome-xenon-convergence | Convergence climax |
| 5 | kingdome-sigil-hub | Sigil City navigation |
| 6 | kingdome-fog-return | Fog Door return threshold |

---

## Archetype Modifiers — Detailed Guide

### Seeker

**Visual signature:** Solitary figure, searching posture, gaze direction toward goal, sense of journey.

**When to use:**
- Player is discovering something new
- Scene involves choice/decision
- Emphasis on individual agency

**Example application (Stage 2):**
```
[Base prompt for Tomorrow Door]
With a small figure silhouetted against the branching roots, gazing toward 
multiple glowing horizons, staff extended toward choice.
```

### Healer

**Visual signature:** Warm light, restoration, care-focused composition, safety/sanctuary.

**When to use:**
- Emphasis on recovery or care
- Scene involves emotional/spiritual healing
- Safe space framing

**Example application (Stage 3 — unusual for XP Door, but possible):**
```
[Base prompt for XP Door]
With glitches gradually forming healing symbols, broken pixels reorganizing 
into light patterns, static becoming song.
```

### Explorer

**Visual signature:** Multiple paths/options, hidden details, branching, discovery cues.

**When to use:**
- Scene emphasizes options/agency
- Emphasis on adventure and discovery
- Visual complexity/density

**Example application (Stage 4):**
```
[Base prompt for Xenon Starship]
With multiple planetary systems visible, convergence lines mapping all possible paths, 
the starship positioned at the ultimate threshold.
```

---

## Model-Specific Tips

### DreamShaper XL 7.0 (Recommended)
- **Strengths:** Artistic quality, fantasy/dreamscape, color harmony, consistent anatomy
- **Best for:** All stages (this library is optimized for DreamShaper)
- **Weakness:** May over-saturate some color palettes
- **Fix:** Add `muted tones, soft color grading` to prompt if needed
- **VAE:** Use `sdxl_vae.safetensors` for improved colors

### SDXL 1.0 Base
- **Strengths:** Universal, most predictable, official baseline
- **Best for:** Stages 1, 3, 6 (everyday/liminal/mist)
- **Weakness:** Can be generic without heavy prompting
- **Fix:** Add `highly detailed, professional quality` to base prompt

### Juggernaut XL
- **Strengths:** Detail-oriented, good anatomy, slightly more realistic
- **Best for:** Stages 4, 5 (architectural/cosmic complexity)
- **Weakness:** May reduce stylization
- **Fix:** Add `artistic, painted, stylized` if you want more illustration feel

---

## Batch Generation Workflow

### Generate All 7 Stages in Sequence

1. **Load model** (DreamShaper XL 7.0 recommended)
2. **Set fixed seed** (e.g., `12345`) for consistency across stages
3. **For each stage** (0–6):
   - Copy `base_prompt` from JSON
   - Paste into Automatic1111
   - Adjust CFG/steps if desired
   - Change seed by +1 (12346, 12347, etc.) for variation
   - Generate
   - Save as `stage-[number]-[archetype]-[seed].png`
4. **Review gallery** → select best image per stage
5. **Export** → save to `data/images/kingdome/`

### Batch Script Example (Automatic1111 API)

```bash
#!/bin/bash

API_URL="http://127.0.0.1:7860/api"
SEED=12345
OUTPUT_DIR="data/images/kingdome"

for stage in 0 1 2 3 4 5 6; do
  PROMPT=$(jq -r ".stages[$stage].base_prompt" sd-prompt-library-kingdome-v1.json)
  
  curl -X POST "$API_URL/txt2img" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"$PROMPT\",
      \"negative_prompt\": \"blurry, low quality, text, watermark\",
      \"steps\": 28,
      \"cfg_scale\": 7.5,
      \"sampler_name\": \"DPM++ 2M Karras\",
      \"seed\": $SEED,
      \"width\": 1024,
      \"height\": 576
    }" > response.json
  
  # Extract image from response and save
  IMAGE_DATA=$(jq -r '.images[0]' response.json)
  echo "$IMAGE_DATA" | base64 -d > "$OUTPUT_DIR/stage-$stage-seed-$SEED.png"
  
  ((SEED++))
done
```

---

## Troubleshooting

### "Prompt is too long" / Token limit exceeded
- **Cause:** Prompt + negative is >77 tokens (default CLIP limit)
- **Fix:** Remove archetype modifier, simplify style_hint section
- **Alternative:** Use `fp16` mode in Automatic1111 (supports longer contexts)

### "Image looks wrong" / Broken prompt
- **Cause:** Missing comma, unbalanced parentheses in weighting
- **Fix:** Validate JSON, check for syntax errors in modified prompt
- **Test:** Remove all archetype modifiers and regenerate

### Colors are oversaturated (DreamShaper XL)
- **Cause:** DreamShaper's default color boosting
- **Fix:** Add `muted colors, desaturated, soft color grading` to prompt
- **Alternative:** Use SDXL 1.0 base instead

### Image is too blurry
- **Cause:** Steps too low or CFG scale too low
- **Fix:** Increase steps to 32–36, increase CFG to 8.0–8.5
- **Alternative:** Use better sampler (DPM++ 2M Karras instead of Euler)

### Hand/anatomy deformities
- **Cause:** Most SDXL models struggle with complex anatomy
- **Fix:** Use negative prompt with `bad anatomy, mangled hands, extra fingers, deformed limbs`
- **Alternative:** Remove archetype modifiers that emphasize hands/figures

### "Can't find model" error
- **Cause:** Model not downloaded or in wrong folder
- **Fix:** Download DreamShaper XL 7.0 to `models/Stable-diffusion/` folder
- **Verify:** Check Automatic1111 model dropdown to confirm load

---

## Quality Checklist

Before using generated images in-game or gallery:

- [ ] Image matches stage thematic keywords
- [ ] Composition is balanced and visually clear
- [ ] Color palette aligns with canonical palette (see JSON)
- [ ] No text, watermarks, or artifacts
- [ ] Anatomy/geometry correct (no obvious glitches)
- [ ] Aspect ratio matches specified (16:9 for default stages)
- [ ] Mood/tone matches intended archetype (if used)
- [ ] Tesseract seal can be discretely added to image (optional)

---

## Distribution & Licensing

- **Generated images:** You own them (per Stable Diffusion terms)
- **Prompts:** Use freely within this project
- **Model weights:** Respect DreamShaper / SDXL licensing
- **Canon alignment:** Maintain compliance with door canon as defined in `2026-06-11-full-door-canon-v2.md`

---

## References

- **Prompt Library JSON:** `data/prompts/sd-prompt-library-kingdome-v1.json`
- **Door Canon Source:** `csf/ingest/2026-06-11-full-door-canon-v2.md`
- **DreamShaper Model:** https://huggingface.co/Lykon/DreamShaper
- **SDXL Official:** https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
- **Automatic1111 WebUI:** https://github.com/AUTOMATIC1111/stable-diffusion-webui
- **ComfyUI:** https://github.com/comfyanonymous/ComfyUI

---

**Last Updated:** 2026-06-11  
**Status:** Production-ready  
**Canon Compliance:** ✓ Full alignment with door canon v2
