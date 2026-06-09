#!/usr/bin/env python3
"""Merge trained LoRA weights with base Stable Diffusion model.

Creates a merged model that can be used directly without loading LoRA separately.
Outputs to models/csf-image/merged/ for Ollama deployment.

Usage:
    python scripts/merge-lora-weights.py
"""

import torch
from diffusers import StableDiffusionPipeline
from peft import PeftModel
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LORA_PATH = REPO_ROOT / "models" / "csf-image" / "checkpoints" / "lantern-door-lora-final.safetensors"
OUTPUT_DIR = REPO_ROOT / "models" / "csf-image" / "merged"


def main():
    print("Loading base model: Stable Diffusion 1.5...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # Load base model
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
    )

    print(f"Loading LoRA weights from: {LORA_PATH}")
    # Load LoRA using PEFT
    unet = pipe.unet
    unet = PeftModel.from_pretrained(unet, str(LORA_PATH))
    
    # Merge LoRA weights
    print("Merging LoRA weights...")
    unet = unet.merge_and_unload()
    pipe.unet = unet

    # Save merged model
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Saving merged model to: {OUTPUT_DIR}")
    pipe.save_pretrained(str(OUTPUT_DIR))

    print("\n✓ Merge complete!")
    print(f"Merged model saved to: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("1. Convert to GGUF for Ollama (requires llama.cpp)")
    print("2. Or use directly with diffusers")


if __name__ == "__main__":
    main()
