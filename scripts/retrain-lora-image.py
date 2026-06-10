#!/usr/bin/env python3
"""
Re-train the Three Doors image LoRA model with new data.

Usage:
    python scripts/retrain-lora-image.py \
        --data models/csf-image/training-data-v2.jsonl \
        --output models/csf-image/checkpoints/lantern-door-lora-v2.safetensors \
        --epochs 5
"""

import argparse
import json
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Re-train image LoRA model")
    parser.add_argument("--data", type=str, required=True, help="Training data JSONL path (text_prompt, image_path)")
    parser.add_argument("--output", type=str, default="models/csf-image/checkpoints/lantern-door-lora-v2.safetensors", help="Output LoRA weights path")
    parser.add_argument("--base-model", type=str, default="runwayml/stable-diffusion-v1-5", help="Base SD model")
    parser.add_argument("--epochs", type=int, default=5, help="Training epochs")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size")
    parser.add_argument("--r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha")
    return parser.parse_args()


def load_image_training_data(data_path):
    """Load image training data from JSONL."""
    records = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError:
                continue
    print(f"Loaded {len(records)} image training samples")
    return records


def main():
    args = parse_args()

    try:
        import torch
        from diffusers import StableDiffusionPipeline
        from peft import LoraConfig, get_peft_model
        from torchvision import transforms
        from PIL import Image
    except ImportError as e:
        print(f"Error: Missing dependency {e}")
        print("Install with: pip install torch diffusers accelerate peft safetensors torchvision Pillow")
        return 1

    if not os.path.exists(args.data):
        print(f"Error: Training data not found: {args.data}")
        return 1

    records = load_image_training_data(args.data)
    if not records:
        print("No training records found")
        return 1

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(repo_root, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Loading base model: {args.base_model}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    pipe = StableDiffusionPipeline.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        safety_checker=None,
    ).to(device)

    # Configure LoRA
    lora_config = LoraConfig(
        r=args.r,
        lora_alpha=args.lora_alpha,
        target_modules=["to_q", "to_v"],
        lora_dropout=0.05,
        bias="none",
    )

    pipe.unet = get_peft_model(pipe.unet, lora_config)
    print(f"LoRA config: r={args.r}, alpha={args.lora_alpha}")

    # Prepare training
    optimizer = torch.optim.AdamW(pipe.unet.parameters(), lr=args.lr)
    transform = transforms.Compose([
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5]),
    ])

    print(f"Starting training: epochs={args.epochs}, lr={args.lr}, batch={args.batch_size}")
    pipe.unet.train()

    for epoch in range(args.epochs):
        epoch_loss = 0.0
        for i, record in enumerate(records):
            prompt = record.get("text_prompt", "")
            image_path = record.get("image_path", "")

            if not os.path.exists(image_path):
                continue

            try:
                image = Image.open(image_path).convert("RGB")
                image_tensor = transform(image).unsqueeze(0).to(device)
            except Exception:
                continue

            # Forward pass
            text_input = pipe.tokenizer(prompt, padding="max_length", max_length=77, truncation=True, return_tensors="pt")
            text_embeddings = pipe.text_encoder(text_input.input_ids.to(device))[0]

            latents = pipe.vae.encode(image_tensor).latent_dist.sample()
            latents = latents * pipe.vae.config.scaling_factor

            noise = torch.randn_like(latents)
            timesteps = torch.randint(0, pipe.scheduler.config.num_train_timesteps, (1,), device=device).long()
            noisy_latents = pipe.scheduler.add_noise(latents, noise, timesteps)

            noise_pred = pipe.unet(noisy_latents, timesteps, text_embeddings).sample
            loss = torch.nn.functional.mse_loss(noise_pred, noise)

            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            epoch_loss += loss.item()

        avg_loss = epoch_loss / max(len(records), 1)
        print(f"  Epoch {epoch + 1}/{args.epochs}: loss={avg_loss:.4f}")

    # Save LoRA weights
    pipe.unet.save_pretrained(output_path)
    print(f"LoRA weights saved to {output_path}")

    # Also save as safetensors if possible
    try:
        from safetensors.torch import save_file
        lora_state = {k: v for k, v in pipe.unet.state_dict().items() if "lora" in k}
        safetensors_path = output_path.replace(".safetensors", "") + ".safetensors"
        save_file(lora_state, safetensors_path)
        print(f"Safetensors saved to {safetensors_path}")
    except ImportError:
        print("safetensors not available, skipping .safetensors export")

    return 0


if __name__ == "__main__":
    exit(main())
