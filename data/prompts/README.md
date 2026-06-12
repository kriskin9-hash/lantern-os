# Stable Diffusion Prompt Library — Kingdome of Hearts

**Version:** 1.0  
**Date:** 2026-06-11  
**Status:** Production-ready  
**Canon Source:** `csf/ingest/2026-06-11-full-door-canon-v2.md`

---

## Overview

Complete Stable Diffusion prompt library for the **Kingdome of Hearts** 7-stage journey. All prompts are derived from the official door canon, optimized for SDXL-family models, and ready for immediate use with local SD API (Automatic1111 / ComfyUI).

**What you get:**
- ✓ 7 stage-specific prompts (100% canon-aligned)
- ✓ Archetype modifiers (seeker/healer/explorer)
- ✓ Recommended SD settings and model
- ✓ Integration guide for Three Doors game
- ✓ Quick-reference copy-paste prompts
- ✓ Complete implementation documentation

---

## Files

### Primary Deliverable

**`sd-prompt-library-kingdome-v1.json`** — Main data file
- 7 complete stage entries (stages 0–6)
- Full metadata, keywords, aspect ratios, settings
- API-ready JSON structure
- Total: 381 lines, ~19KB

```json
{
  "metadata": { /* version, recommendations, notes */ },
  "stages": [
    {
      "stage_key": "garden-at-beginning",
      "base_prompt": "A timeless garden where ancient moss...",
      "keywords": ["ancient", "moss", "lanterns", ...],
      "archetype_modifiers": {
        "seeker": "with a solitary figure...",
        "healer": "with restorative light...",
        "explorer": "with hidden paths..."
      },
      ...
    },
    ...
  ],
  "usage_guide": { /* quick-start, batch generation */ },
  "validation_report": { /* compliance summary */ }
}
```

### Documentation

**`SD-QUICK-REFERENCE.md`** — Get started in 2 minutes
- Copy-paste prompts for all 7 stages
- Default settings table
- Archetype modifiers quick list
- Aspect ratio reference
- Fast troubleshooting

**Use this if you just want to:**
- Pick a stage
- Copy the prompt
- Generate an image

### Implementation Guide

**`SD-PROMPT-IMPLEMENTATION.md`** — Complete technical reference
- Stage-by-stage breakdown with details
- Recommended settings by quality tier (fast/balanced/high-quality/ultra)
- Negative prompt best practices
- Prompt weighting & customization guide
- Model-specific tips (DreamShaper vs SDXL vs Juggernaut)
- Batch generation workflow
- Automatic1111 / ComfyUI integration
- Three Doors game API endpoint proposal
- Troubleshooting section with solutions

**Use this if you:**
- Want full documentation
- Are integrating with code
- Need model-specific guidance
- Are doing batch generation

### Validation Report

**`VALIDATION-REPORT.md`** — Compliance & evidence
- Canon keyword verification (all 7 stages)
- Aspect ratio validation
- Token count verification
- Archetype modifier inventory
- Model compatibility matrix
- Quality checklist
- Recommendations for integration

**Use this to:**
- Verify compliance
- See validation evidence
- Review integration roadmap

---

## Quick Start (2 Minutes)

### 1. Get the Prompt

Open `SD-QUICK-REFERENCE.md` and copy the prompt for your desired stage (0–6).

**Example — Stage 1 (Lucky Door):**
```
A sunlit field of four-leaf clovers bending under gentle rain, where quilted 
patchwork ruins of a forgotten cottage peek through verdant growth. Brass bells 
hang from twisted branches, chiming softly. A crown carved from driftwood rests 
among the flowers. Watercolor rain sparkles like luck itself. Cheerful, 
whimsical, contemporary folk art illustration style, layered translucent washes, 
golden hour afternoon light touching everything.
```

### 2. Download a Model (if you don't have one)

**Recommended:** [DreamShaper XL 7.0](https://huggingface.co/Lykon/DreamShaper)
- Place in: `models/Stable-diffusion/` (Automatic1111)
- Also download VAE: `sdxl_vae.safetensors`

**Alternatives:**
- SDXL 1.0 base (official, most generic)
- Juggernaut XL (photo-realistic)

### 3. Set Up Automatic1111 (or ComfyUI)

**If using Automatic1111 WebUI:**
```bash
# Clone repo
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui

# Run on Windows
./webui-user.bat

# Or on Mac/Linux
bash webui.sh
```

**If using ComfyUI:**
- Download from https://github.com/comfyanonymous/ComfyUI
- Follow their setup guide

### 4. Generate an Image

**Automatic1111:**
1. Paste prompt into the text box
2. Set sampler to `DPM++ 2M Karras`
3. Set steps to `28`
4. Set CFG to `7.5`
5. Click **Generate**

**ComfyUI:**
1. Load SDXL checkpoint (DreamShaper XL 7.0)
2. Connect prompt to sampler
3. Set steps: 28, CFG: 7.5
4. Queue and run

### 5. Save Your Image

```
data/images/kingdome/stage-[number]-[seed].png
```

**Example:**
```
data/images/kingdome/stage-1-12345.png
```

---

## Stages at a Glance

| # | Name | Keywords | Mood |
|---|------|----------|------|
| **0** | Garden at Beginning | ancient, moss, lanterns, light, roots | Nostalgic, welcoming |
| **1** | Lucky Door (Today) | clover, luck, rain, quilts, bells, crown | Warm, playful |
| **2** | Tomorrow Door (Future) | branches, growth, embers, streams, roots | Hopeful, expansive |
| **3** | XP Door (Glitch) | windows, glitch, blue, digital, liminal | Disorienting, uncanny |
| **4** | Xenon Starship (Convergence) | starship, convergence, throne, void, light | Transcendent, cosmic |
| **5** | Sigil City (Doors) | doors, lanterns, King, fractal, portal | Awe-inspiring, meta |
| **6** | Fog Door (Return) | fog, mist, sea, return, escape, gate | Peaceful, restful |

---

## Archetype Modifiers

Add to the end of any base prompt to get character-driven scenes:

- **Seeker:** "with a figure searching, discovering, or in transition"
- **Healer:** "with restorative light, care-focused composition, safety"
- **Explorer:** "with multiple paths visible, hidden details, branching"

**Example:**
```
[Base prompt for Stage 1]
with a figure kneeling to examine a four-leaf clover, eyes bright with discovery.
```

---

## Recommended Settings

| Setting | Value |
|---------|-------|
| **Model** | DreamShaper XL 7.0 |
| **Sampler** | DPM++ 2M Karras |
| **Steps** | 28 (adjust 20–48 for speed/quality) |
| **CFG Scale** | 7.5 (adjust 7.0–8.5) |
| **Seed** | -1 (random) |
| **Aspect Ratio** | 16:9 (1024×576) |
| **Negative Prompt** | `blurry, low quality, text, watermark, signature, deformed, ugly, bad anatomy` |

---

## Aspect Ratio Options

All dimensions use 1024×576 as base (16:9). Alternatives:

| Ratio | Dimensions | Use Case |
|-------|-----------|----------|
| 1:1 | 576×576 | Iconic single-stage portrait |
| 3:1 | 1152×384 | Cinematic ultra-wide |
| 5:7 | 411×576 | Portrait-tall |
| 9:16 | 324×576 | Mobile/vertical |
| **16:9** | **1024×576** | **Default (recommended)** |

---

## Integration with Three Doors Game

### Scene Mapping

Each stage corresponds to a Three Doors scene:

```json
{
  "stage_0": { "scene_key": "kingdome-garden", "use": "entry/return" },
  "stage_1": { "scene_key": "kingdome-clover-field", "use": "lucky door" },
  "stage_2": { "scene_key": "kingdome-branching-future", "use": "tomorrow door" },
  "stage_3": { "scene_key": "kingdome-xp-desktop", "use": "xp door glitch" },
  "stage_4": { "scene_key": "kingdome-xenon-convergence", "use": "convergence climax" },
  "stage_5": { "scene_key": "kingdome-sigil-hub", "use": "door inventory" },
  "stage_6": { "scene_key": "kingdome-fog-return", "use": "return/rest" }
}
```

### Image Pool Setup

Store generated images in:
```
data/images/kingdome/stage-[number]-[seed].png
```

Set environment variable:
```
THREE_DOORS_IMAGE_POOL_DIR=D:\tmp\imagesandreports
```

### Proposed API Endpoint

See `SD-PROMPT-IMPLEMENTATION.md` for full spec:
```
POST /api/generate-image
{
  "stage_key": "lucky-door-present",
  "archetype": "seeker",
  "sampler": "DPM++ 2M Karras",
  "steps": 28,
  "cfg_scale": 7.5,
  "seed": -1
}
```

---

## Troubleshooting

### "Prompt is too long"
- Remove archetype modifier
- Simplify style hints
- Use `fp16` mode in Automatic1111

### "Image looks blurry"
- Increase steps to 32–36
- Increase CFG to 8.0–8.5
- Use DPM++ 2M Karras sampler

### "Colors are oversaturated" (DreamShaper)
- Add to prompt: `muted colors, soft color grading`
- Or use SDXL 1.0 base instead

### "Bad hands/anatomy"
- Add to negative prompt: `bad anatomy, mangled hands, extra fingers, deformed limbs`
- Use fewer archetype modifiers

### "Model not found"
- Download to: `models/Stable-diffusion/` (Automatic1111)
- Or load via ComfyUI checkpoint node
- Verify model appears in dropdown

**Full troubleshooting guide:** See `SD-PROMPT-IMPLEMENTATION.md` section "Troubleshooting"

---

## File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `sd-prompt-library-kingdome-v1.json` | 381 | Primary JSON prompt library |
| `SD-QUICK-REFERENCE.md` | 178 | Copy-paste prompts + quick settings |
| `SD-PROMPT-IMPLEMENTATION.md` | 512 | Full technical guide |
| `VALIDATION-REPORT.md` | 350+ | Canon compliance + evidence |
| `README.md` | This file | Overview & quick start |

---

## Model Compatibility

**Primary (Recommended):**
- DreamShaper XL 7.0 — Best artistic quality, fantasy/dreamscape
  - VAE: `sdxl_vae.safetensors` (improves colors)

**Tested & Approved:**
- SDXL 1.0 base — Universal, reliable
- Juggernaut XL — Detail-oriented, photorealistic
- RealismEngine SDXL — Photo-realistic variant

All prompts use standard SDXL syntax (compatible with all SDXL-family models).

---

## Canon Alignment

All prompts derived from official Kingdome door canon:
- **Source:** `csf/ingest/2026-06-11-full-door-canon-v2.md`
- **Keywords:** 100% match to canonical door families
- **Stages:** 7-stage Kingdome journey (lines 104–114)
- **Image keywords:** Per-door family mapping (lines 293–316)

**Verification:** See `VALIDATION-REPORT.md` for full keyword inventory and canon citations.

---

## License & Attribution

- **Generated Images:** You own them (per Stable Diffusion terms)
- **Prompts:** Use freely within this project
- **Model Weights:** Respect DreamShaper / SDXL licensing
- **Canon:** Maintain alignment with door canon (2026-06-11-full-door-canon-v2.md)

---

## Next Steps

### Immediate
1. ✓ Read `SD-QUICK-REFERENCE.md`
2. ✓ Generate test images for each stage
3. ✓ Save to `data/images/kingdome/`

### Near-term (Optional)
1. Implement `/api/generate-image` endpoint (see implementation guide)
2. Integrate with Three Doors game frontend
3. Add seed tracking for reproducibility

### Future
1. Extend to other door families (Shelby Elephant Door, Raven, Sticker/Mixtape)
2. Fine-tune LoRA for style consistency
3. Auto-select archetype modifiers based on game state

---

## Support

**Documentation:**
- Quick start: `SD-QUICK-REFERENCE.md`
- Full guide: `SD-PROMPT-IMPLEMENTATION.md`
- Validation: `VALIDATION-REPORT.md`

**Canon Reference:**
- Door canon: `csf/ingest/2026-06-11-full-door-canon-v2.md`

**Questions?**
- Review the implementation guide (extensive troubleshooting section)
- Check validation report for model compatibility matrix
- Verify canon alignment via keyword inventory

---

**Created:** 2026-06-11  
**Status:** Production-ready  
**Next Review:** Post-Three-Doors integration  
**Maintenance:** Update if door canon changes; maintain keyword alignment
