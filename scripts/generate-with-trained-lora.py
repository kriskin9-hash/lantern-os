#!/usr/bin/env python3
"""Generate images using trained LoRA adapter.

Usage:
    python scripts/generate-with-trained-lora.py --prompt "dreamlike elephant oasis" --adapter models/csf-image/checkpoints/lantern-door-lora-final.safetensors --out data/images/three-doors/output.png
"""

import argparse
import torch
from diffusers import StableDiffusionPipeline
from peft import PeftModel
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Generate image with trained LoRA adapter")
    parser.add_argument("--prompt", required=True, help="Text prompt for image generation")
    parser.add_argument("--adapter", default="models/csf-image/checkpoints/lantern-door-lora-final.safetensors", help="Path to LoRA adapter weights")
    parser.add_argument("--out", required=True, help="Output image path")
    parser.add_argument("--negative", default="blurry, low quality, distorted, ugly", help="Negative prompt")
    parser.add_argument("--steps", type=int, default=20, help="Number of inference steps")
    parser.add_argument("--guidance", type=float, default=7.5, help="Guidance scale")
    parser.add_argument("--seed", type=int, default=-1, help="Random seed (-1 for random)")
    
    args = parser.parse_args()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    # Resolve paths relative to repo root
    adapter_path = REPO_ROOT / args.adapter
    output_path = REPO_ROOT / args.out
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading base model: Stable Diffusion 1.5...")
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
    )
    pipe = pipe.to(device)
    
    print(f"Loading LoRA adapter from: {adapter_path}")
    if adapter_path.exists():
        pipe.unet = PeftModel.from_pretrained(pipe.unet, str(adapter_path))
        print("LoRA adapter loaded successfully")
    else:
        print(f"Warning: LoRA adapter not found at {adapter_path}, using base model only")
    
    # Set seed
    generator = torch.Generator(device).manual_seed(args.seed) if args.seed >= 0 else None
    
    print(f"Generating image with prompt: {args.prompt[:100]}...")
    image = pipe(
        prompt=args.prompt,
        negative_prompt=args.negative,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance,
        generator=generator,
    ).images[0]
    
    print(f"Saving to: {output_path}")
    image.save(output_path)
    
    print("✓ Generation complete!")
    sys.exit(0)


if __name__ == "__main__":
    main()
