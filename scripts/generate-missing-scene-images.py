#!/usr/bin/env python3
"""Generate missing Three Doors scene images with the local merged CSF-image
model (models/csf-image/merged) — fully offline, no cloud provider.

Usage:
    python scripts/generate-missing-scene-images.py [--model PATH] [--steps N] [--force]

Renders every scene in three_doors_engine._SD_PROMPTS that has no PNG yet in
apps/lantern-garage/public/data/images/three-doors/. Seeds are derived from the
scene key so output is reproducible.
"""

import argparse
import hashlib
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

OUTPUT_DIR = REPO_ROOT / "apps" / "lantern-garage" / "public" / "data" / "images" / "three-doors"
DEFAULT_MODEL = REPO_ROOT / "models" / "csf-image" / "merged"
NEGATIVE = "blurry, low quality, distorted, ugly, text, watermark"


def scene_seed(key: str) -> int:
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=str(DEFAULT_MODEL), help="Diffusers pipeline directory")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--guidance", type=float, default=7.5)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--force", action="store_true", help="Regenerate even if PNG exists")
    parser.add_argument("--only", nargs="*", help="Limit to these scene keys")
    args = parser.parse_args()

    from three_doors_engine import _SD_PROMPTS

    keys = args.only or sorted(_SD_PROMPTS)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    todo = [k for k in keys
            if k in _SD_PROMPTS and (args.force or not (OUTPUT_DIR / f"{k}.png").exists())]
    if not todo:
        print("All scene images already exist; nothing to do.")
        return 0
    print(f"Scenes to render: {todo}")

    import torch
    from diffusers import StableDiffusionPipeline

    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Error: model not found at {model_path}")
        return 1

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    print(f"Loading {model_path} on {device}...")
    pipe = StableDiffusionPipeline.from_pretrained(
        str(model_path), torch_dtype=dtype, safety_checker=None)
    pipe = pipe.to(device)

    for i, key in enumerate(todo, 1):
        out = OUTPUT_DIR / f"{key}.png"
        prompt = _SD_PROMPTS[key]
        gen = torch.Generator(device).manual_seed(scene_seed(key))
        t0 = time.time()
        print(f"[{i}/{len(todo)}] {key} (seed {scene_seed(key)})...")
        image = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE,
            num_inference_steps=args.steps,
            guidance_scale=args.guidance,
            width=args.width,
            height=args.height,
            generator=gen,
        ).images[0]
        image.save(out)
        print(f"  saved {out.relative_to(REPO_ROOT)} in {time.time() - t0:.0f}s")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
