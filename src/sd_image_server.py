#!/usr/bin/env python3
"""Minimal Stable Diffusion API Server for Lantern OS.

In-house implementation using diffusers with merged model.
No external web UI dependencies - just a simple REST API.

Usage:
    python src/sd_image_server.py

Environment:
    SD_MODEL_PATH - Path to merged model (default: models/csf-image/merged)
    SD_PORT - Server port (default: 7860)
    SD_HOST - Server host (default: 127.0.0.1)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import Response
    import uvicorn
    from diffusers import StableDiffusionPipeline
    import torch
    from PIL import Image
    import io
    import base64
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install fastapi uvicorn diffusers torch pillow")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = REPO_ROOT / "models" / "csf-image" / "merged"

app = FastAPI(title="Lantern OS Image Server", version="1.0.0")

# Global pipeline (lazy loaded)
_pipeline: Optional[StableDiffusionPipeline] = None


def get_pipeline() -> StableDiffusionPipeline:
    """Get or create the SD pipeline."""
    global _pipeline
    if _pipeline is None:
        model_path = Path(os.environ.get("SD_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
        if not model_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Model not found at {model_path}. Run: python scripts/merge-lora-weights.py"
            )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading model from {model_path} on {device}...")

        _pipeline = StableDiffusionPipeline.from_pretrained(
            str(model_path),
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            use_safetensors=True,
        )

        if device == "cuda":
            _pipeline.enable_attention_slicing()
            _pipeline.enable_vae_slicing()

        _pipeline = _pipeline.to(device)
        print("Model loaded successfully")
    return _pipeline


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "model_loaded": _pipeline is not None}


@app.post("/generate")
async def generate(request: dict):
    """Generate image from prompt."""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt is required")

        negative_prompt = request.get("negative_prompt", "cartoon, anime, blurry, distorted")
        steps = request.get("steps", 25)
        guidance_scale = request.get("guidance_scale", 7.5)
        width = request.get("width", 768)
        height = request.get("height", 512)

        pipe = get_pipeline()

        print(f"Generating: {prompt[:50]}...")
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            height=height,
            width=width,
        ).images[0]

        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return {
            "image": f"data:image/png;base64,{img_str}",
            "prompt": prompt,
            "steps": steps,
            "guidance_scale": guidance_scale,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the server."""
    host = os.environ.get("SD_HOST", "127.0.0.1")
    port = int(os.environ.get("SD_PORT", "7860"))

    print(f"Starting Lantern OS Image Server on http://{host}:{port}")
    print(f"Model path: {os.environ.get('SD_MODEL_PATH', DEFAULT_MODEL_PATH)}")
    print(f"Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
