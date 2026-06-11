#!/usr/bin/env python3
"""
Three Doors LoRA Trainer
Collects images from gameplay and fine-tunes SD LoRA on the dream-world aesthetic.

Usage:
    python scripts/train-three-doors-lora.py \
        --image_dir data/images/generated-doors \
        --output_dir data/models/lora/three-doors-2026-06-11 \
        --manifest data/training/lora-training.jsonl

Requirements:
    pip install diffusers accelerate peft safetensors transformers Pillow torch
    (CUDA GPU strongly recommended — 8GB+ VRAM for SDXL, 4GB for SD1.5)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

def check_deps():
    missing = []
    for pkg in ["torch", "diffusers", "peft", "accelerate", "safetensors", "PIL"]:
        try:
            __import__(pkg if pkg != "PIL" else "PIL.Image")
        except ImportError:
            missing.append(pkg if pkg != "PIL" else "Pillow")
    return missing

def load_manifest(manifest_path):
    entries = []
    p = Path(manifest_path)
    if not p.exists():
        return entries
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries

def prepare_dataset(image_dir, manifest_path):
    """Return list of (image_path, caption) pairs."""
    image_dir = Path(image_dir)
    samples = []

    # Load manifest for rich captions
    manifest = {e["id"]: e for e in load_manifest(manifest_path)}

    for img_path in sorted(image_dir.glob("*.jpg")):
        caption_path = img_path.with_suffix(".txt")
        entry_id = img_path.stem

        if caption_path.exists():
            caption = caption_path.read_text(encoding="utf-8").strip()
        elif entry_id in manifest:
            caption = manifest[entry_id].get("prompt", "three doors dreamworld, fantasy dreamscape")
        else:
            caption = "three doors dreamworld, mystical fantasy door, painterly, cinematic"

        samples.append((str(img_path), caption))

    return samples

def train_lora_diffusers(image_dir, output_dir, manifest_path, args):
    """Fine-tune LoRA using diffusers + peft + accelerate."""
    import torch
    from PIL import Image
    from torch.utils.data import Dataset, DataLoader
    from diffusers import AutoencoderKL, UNet2DConditionModel, DDPMScheduler
    from transformers import CLIPTextModel, CLIPTokenizer
    from peft import LoraConfig, get_peft_model
    import torch.nn.functional as F

    samples = prepare_dataset(image_dir, manifest_path)
    print(f"[Training] {len(samples)} images in dataset")
    if not samples:
        print("[Training] No images found. Play more scenes first!")
        return False

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    print(f"[Training] Device: {device} | dtype: {dtype}")

    base_model = args.base_model
    print(f"[Training] Loading base model: {base_model}")
    print(f"[Training] (First run downloads ~4GB — subsequent runs use cache)")

    tokenizer = CLIPTokenizer.from_pretrained(base_model, subfolder="tokenizer")
    text_encoder = CLIPTextModel.from_pretrained(base_model, subfolder="text_encoder", torch_dtype=dtype).to(device)
    vae = AutoencoderKL.from_pretrained(base_model, subfolder="vae", torch_dtype=dtype).to(device)
    unet = UNet2DConditionModel.from_pretrained(base_model, subfolder="unet", torch_dtype=dtype).to(device)
    noise_scheduler = DDPMScheduler.from_pretrained(base_model, subfolder="scheduler")

    # Apply LoRA to attention layers
    lora_config = LoraConfig(
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        target_modules=["to_q", "to_v", "to_k", "to_out.0"],
        lora_dropout=0.05,
        bias="none",
    )
    unet = get_peft_model(unet, lora_config)
    unet.print_trainable_parameters()

    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)

    optimizer = torch.optim.AdamW(unet.parameters(), lr=args.lr, weight_decay=0.01)

    class DoorDataset(Dataset):
        def __init__(self, samples, tokenizer, size=512):
            self.samples = samples
            self.tokenizer = tokenizer
            self.size = size
        def __len__(self): return len(self.samples)
        def __getitem__(self, i):
            img_path, caption = self.samples[i]
            img = Image.open(img_path).convert("RGB").resize((self.size, self.size))
            pixel_values = torch.tensor(
                [(c / 127.5 - 1.0) for c in img.getdata()],
                dtype=dtype
            ).reshape(3, self.size, self.size)
            # Reshape from HWC to CHW
            import numpy as np
            arr = np.array(img).astype(np.float32) / 127.5 - 1.0
            pixel_values = torch.from_numpy(arr).permute(2, 0, 1).to(dtype)

            tokens = self.tokenizer(
                caption,
                padding="max_length",
                max_length=self.tokenizer.model_max_length,
                truncation=True,
                return_tensors="pt",
            )
            return {"pixel_values": pixel_values, "input_ids": tokens.input_ids.squeeze(0)}

    dataset = DoorDataset(samples, tokenizer, size=args.resolution)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)

    unet.train()
    global_step = 0
    print(f"[Training] Starting {args.epochs} epochs, batch_size={args.batch_size}, lr={args.lr}")

    for epoch in range(args.epochs):
        epoch_loss = 0.0
        for step, batch in enumerate(loader):
            pixel_values = batch["pixel_values"].to(device)
            input_ids = batch["input_ids"].to(device)

            with torch.no_grad():
                latents = vae.encode(pixel_values).latent_dist.sample() * vae.config.scaling_factor
                encoder_hidden_states = text_encoder(input_ids)[0]

            noise = torch.randn_like(latents)
            timesteps = torch.randint(0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],), device=device).long()
            noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

            noise_pred = unet(noisy_latents, timesteps, encoder_hidden_states).sample
            loss = F.mse_loss(noise_pred.float(), noise.float(), reduction="mean")

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(unet.parameters(), 1.0)
            optimizer.step()

            epoch_loss += loss.item()
            global_step += 1

            if step % 10 == 0:
                print(f"[Training] Epoch {epoch+1}/{args.epochs} step {step+1}/{len(loader)} loss={loss.item():.4f}")

        avg_loss = epoch_loss / max(len(loader), 1)
        print(f"[Training] Epoch {epoch+1} complete — avg loss: {avg_loss:.4f}")

        # Save checkpoint each epoch
        ckpt_path = output_dir / f"checkpoint-epoch{epoch+1}"
        unet.save_pretrained(ckpt_path)
        print(f"[Training] Checkpoint saved: {ckpt_path}")

    # Save final LoRA weights
    final_path = output_dir / "three-doors-final.safetensors"
    unet.save_pretrained(output_dir / "final")
    try:
        from safetensors.torch import save_file
        lora_state = {k: v for k, v in unet.state_dict().items() if "lora" in k}
        save_file(lora_state, final_path)
        print(f"[Training] LoRA weights saved: {final_path}")
    except Exception as e:
        print(f"[Training] safetensors save skipped: {e}")

    # Write adapter config
    adapter_config = {
        "base_model": base_model,
        "lora_rank": args.lora_rank,
        "lora_alpha": args.lora_alpha,
        "resolution": args.resolution,
        "trained_on": len(samples),
        "epochs": args.epochs,
        "trained_at": datetime.now().isoformat(),
    }
    with open(output_dir / "adapter_config.json", "w") as f:
        json.dump(adapter_config, f, indent=2)

    # Remove pid file — signals training complete
    pid_path = output_dir / "training.pid"
    if pid_path.exists():
        pid_path.unlink()

    print(f"\n[Training] Complete! LoRA saved to {output_dir}")
    print(f"[Training] Load with: pipe.load_lora_weights('{output_dir}/final')")
    return True


def main():
    parser = argparse.ArgumentParser(description="Train Three Doors LoRA from gameplay images")
    parser.add_argument("--image_dir", default="data/images/generated-doors")
    parser.add_argument("--output_dir", default="data/models/lora/three-doors-latest")
    parser.add_argument("--manifest", default="data/training/lora-training.jsonl")
    parser.add_argument("--base_model", default="runwayml/stable-diffusion-v1-5",
                        help="HuggingFace model ID or local path. SDXL: stabilityai/stable-diffusion-xl-base-1.0")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--lora_rank", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--resolution", type=int, default=512)
    args = parser.parse_args()

    print("=" * 60)
    print("Three Doors LoRA Trainer")
    print("=" * 60)

    missing = check_deps()
    if missing:
        print(f"\n[ERROR] Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install " + " ".join(missing))
        print("  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        sys.exit(1)

    samples = prepare_dataset(args.image_dir, args.manifest)
    if not samples:
        print(f"\n[ERROR] No training images found in {args.image_dir}")
        print("Play more Three Doors scenes to collect images first.")
        sys.exit(1)

    print(f"\n[Info] Found {len(samples)} training images")
    print(f"[Info] Output: {args.output_dir}")
    print(f"[Info] Base model: {args.base_model}")
    print()

    success = train_lora_diffusers(args.image_dir, args.output_dir, args.manifest, args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
