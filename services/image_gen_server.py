#!/usr/bin/env python3
"""
Three Doors Game - Lightweight Image Generation Server
Uses Hugging Face Diffusers for fast, local image generation

Install: pip install diffusers transformers torch pillow
Run: python services/image_gen_server.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse, FileResponse
    import uvicorn
except ImportError:
    logger.error("[IMG] FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

app = FastAPI(title="Three Doors Image Generation", version="1.0.0")

# Paths
REPO_ROOT = Path(__file__).parent.parent
CACHE_DIR = REPO_ROOT / "data" / "images" / "three-doors"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Try to import diffusers, but make it optional
try:
    from diffusers import StableDiffusionPipeline
    import torch
    HAS_DIFFUSERS = True
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[IMG] Using device: {DEVICE}")
except ImportError:
    HAS_DIFFUSERS = False
    logger.warning("[IMG] Diffusers not installed. Run: pip install diffusers transformers torch")

# Scene prompts
SCENE_PROMPTS = {
    "moss-entry": (
        "atmospheric dreamscape, moss-covered ancient forest doorway, glowing green lanterns hanging from "
        "twisted branches, a friendly fox with a brass tag sitting on soft earth, rain on ferns, volumetric fog, "
        "cinematic lighting, dark fantasy, liminal space, soft pastel anime aesthetic, cel-shaded, 16:9"
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
}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "image-gen",
        "diffusers_available": HAS_DIFFUSERS,
        "device": DEVICE if HAS_DIFFUSERS else None,
    }

@app.get("/api/scenes")
async def list_scenes():
    """List available scenes and their prompts"""
    return {
        scene: {
            "prompt": prompt[:100] + "...",
            "full_prompt": prompt,
            "cached": (CACHE_DIR / f"{scene}.png").exists()
        }
        for scene, prompt in SCENE_PROMPTS.items()
    }

@app.post("/api/generate")
async def generate_image(request_data: dict):
    """Generate an image from a prompt"""
    scene_key = request_data.get("scene_key", "moss-entry")
    custom_prompt = request_data.get("prompt", "")

    # Use custom prompt or default from scene
    prompt = custom_prompt or SCENE_PROMPTS.get(scene_key, "")
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")

    # Check cache
    cached_path = CACHE_DIR / f"{scene_key}.png"
    if cached_path.exists():
        return {
            "success": True,
            "cached": True,
            "scene_key": scene_key,
            "path": f"/images/three-doors/{scene_key}.png",
            "generated_at": cached_path.stat().st_mtime
        }

    if not HAS_DIFFUSERS:
        return {
            "success": False,
            "reason": "diffusers_not_available",
            "message": "Image generation library not installed",
            "install_command": "pip install diffusers transformers torch pillow",
            "scene_key": scene_key,
            "prompt_ready": True,
            "prompt": prompt[:150] + "..."
        }

    try:
        logger.info(f"[IMG] Generating image for scene: {scene_key}")
        logger.info(f"[IMG] Prompt: {prompt[:80]}...")

        # Load pipeline (with caching)
        model_id = "runwayml/stable-diffusion-v1-5"  # Lightweight model
        logger.info(f"[IMG] Loading model: {model_id}")

        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32)
        pipe = pipe.to(DEVICE)

        # Generate with reduced steps for speed
        logger.info(f"[IMG] Generating image (20 steps)...")
        image = pipe(
            prompt,
            num_inference_steps=20,
            guidance_scale=7.5,
            height=512,
            width=768
        ).images[0]

        # Save
        image.save(cached_path)
        logger.info(f"[IMG] Saved to: {cached_path}")

        return {
            "success": True,
            "cached": False,
            "scene_key": scene_key,
            "path": f"/images/three-doors/{scene_key}.png",
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"[IMG] Generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "scene_key": scene_key,
            "message": "Image generation failed. Check logs for details."
        }

@app.get("/images/three-doors/{filename}")
async def get_image(filename: str):
    """Serve cached images"""
    image_path = CACHE_DIR / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path, media_type="image/png")

if __name__ == "__main__":
    port = int(__import__("os").getenv("IMAGE_GEN_PORT", 5555))

    print(f"""
╔════════════════════════════════════════════════════════════════╗
║ Three Doors Image Generation Server (Python)                  ║
╠════════════════════════════════════════════════════════════════╣
║ Status: Starting                                               ║
║ Port:   {port}                                                    ║
║ Diffusers: {("✓ Available" if HAS_DIFFUSERS else "✗ Not installed")}                                  ║
║ Device:    {DEVICE if HAS_DIFFUSERS else "N/A"}                                                 ║
╠════════════════════════════════════════════════════════════════╣
║ Endpoints:                                                     ║
║   GET  /health              - Service status                  ║
║   GET  /api/scenes          - List available scenes           ║
║   POST /api/generate        - Generate image from prompt      ║
║   GET  /images/...          - Retrieve cached images          ║
╠════════════════════════════════════════════════════════════════╣
║ If diffusers not available, install with:                     ║
║   pip install diffusers transformers torch pillow             ║
║                                                                ║
║ Models will be cached in ~/.cache/huggingface/                ║
║ First generation takes ~2 min (5GB+ download), then cached    ║
╚════════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
