# CSF Ingestion — Stable Diffusion Door Image Generation

**Status:** queued  
**Priority:** 2 — highest visual impact, requires local GPU  
**Estimated effort:** 4–6 hours (+ GPU setup)  
**Source:** [Stable Diffusion Local Setup 2026](https://coderoasis.com/stable-diffusion-local-setup-guide-2026/), [Towards AI SDXL guide](https://towardsai.net/p/l/your-first-steps-into-ai-art-generate-images-with-python-and-stable-diffusion-xl-free-with-a-local-llm/)

## Problem

The three-doors banner uses Canvas-drawn art. Replace with AI-generated atmospheric images per door, making each door visually distinct and rooted in dream imagery.

## Hardware Requirements
- SD 1.5: 4GB VRAM minimum (GTX 1070 / RTX 2060+)
- SDXL / DreamShaper XL: 6GB VRAM (RTX 3060+)
- CPU fallback: possible but slow (~60s/image)

## Proposed Implementation

**Backend:** New route `POST /api/dream/doors/image` in `routes/dream.js`:
```js
// Calls local ComfyUI or Automatic1111 API
// Prompt template per door: "atmospheric dreamscape, {door_text}, glowing doorway,
//   fog, cinematic lighting, dark fantasy, --ar 3:1 --style dream"
// Returns base64 PNG or URL
```

**Frontend:** `dream-chat.html` — if SD server is available, fetch images for each door and draw them on canvas behind the glyph art. Falls back to current gradient Canvas if `STABLE_DIFFUSION_URL` is not set.

**.env additions:**
```
STABLE_DIFFUSION_URL=http://127.0.0.1:7860
SD_MODEL=dreamshaper_xl
SD_STEPS=20
SD_WIDTH=512
SD_HEIGHT=192
```

## Files to Change
- `apps/lantern-garage/routes/dream.js` — add `POST /api/dream/doors/image`
- `apps/lantern-garage/public/dream-chat.html` — `drawDoorsBanner()` optional SD fetch
- `.env.example` — add SD vars
- `data/pcsf/settings.pcsf.json` — add SD keys
- `data/pcsf/health.pcsf.json` — add `sd_server` health check

## Model Recommendation
DreamShaper XL — handles atmospheric, fog, fantasy doorways well. LoRA for dream aesthetic available on CivitAI.
