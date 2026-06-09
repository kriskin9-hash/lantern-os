#!/usr/bin/env python3
"""Test and validate the merged Stable Diffusion model.

Tests that the merged model can generate images correctly.
Provides deployment instructions for local SD servers.

Usage:
    python scripts/deploy-merged-sd-model.py
"""

import torch
from diffusers import StableDiffusionPipeline
from pathlib import Path
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
MERGED_MODEL_PATH = REPO_ROOT / "models" / "csf-image" / "merged"
OUTPUT_DIR = REPO_ROOT / "data" / "images" / "test-merged"


def test_merged_model():
    """Test the merged model by generating a sample image."""
    print("Loading merged model from:", MERGED_MODEL_PATH)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    pipe = StableDiffusionPipeline.from_pretrained(
        str(MERGED_MODEL_PATH),
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
    )

    if device == "cuda":
        pipe.enable_attention_slicing()
        pipe.enable_vae_slicing()

    pipe = pipe.to(device)

    # Test prompt
    prompt = "mystical door, ancient stone archway, ethereal fog, glowing light, dreamlike atmosphere"
    negative_prompt = "cartoon, anime, bright colors, childish, blurry, distorted"

    print(f"\nGenerating test image...")
    print(f"Prompt: {prompt}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    output_path = OUTPUT_DIR / f"test-merged-{timestamp}.png"

    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=25,
        guidance_scale=7.5,
        height=512,
        width=768
    ).images[0]

    image.save(output_path)
    print(f"✓ Test image saved to: {output_path}")

    return output_path


def print_deployment_instructions():
    """Print instructions for deploying the merged model."""
    print("\n" + "="*60)
    print("DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    print("\nThe merged model is ready for use with local SD servers.")
    print("\nOption 1: Use with ComfyUI")
    print("  1. Install ComfyUI: https://github.com/comfyanonymous/ComfyUI")
    print("  2. Copy merged model to ComfyUI/models/checkpoints/")
    print("  3. Start ComfyUI: python main.py --listen 127.0.0.1 --port 8188")
    print("  4. Set STABLE_DIFFUSION_URL=http://127.0.0.1:8188 in .env")
    print("\nOption 2: Use with Automatic1111")
    print("  1. Install Automatic1111: https://github.com/AUTOMATIC1111/stable-diffusion-webui")
    print("  2. Copy merged model to stable-diffusion-webui/models/Stable-diffusion/")
    print("  3. Start WebUI: webui.bat --api --listen 127.0.0.1 --port 7860")
    print("  4. Set STABLE_DIFFUSION_URL=http://127.0.0.1:7860 in .env")
    print("\nOption 3: Use directly with diffusers (Python)")
    print("  See scripts/generate-with-trained-lora.py for example")
    print("\nLantern OS Integration:")
    print("  - Route POST /api/dream/doors/image already exists in routes/dream.js")
    print("  - Set STABLE_DIFFUSION_URL in .env to enable image generation")
    print("  - Frontend integration in dream-chat.html uses this endpoint")
    print("="*60)


def main():
    try:
        test_image = test_merged_model()
        print("\n✓ Merged model test successful!")
        print_deployment_instructions()
        return 0
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        print("\nEnsure the merged model exists at:", MERGED_MODEL_PATH)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
