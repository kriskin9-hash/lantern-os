#!/usr/bin/env python3
r"""
Train LoRA on actual door images from C:\Users\alexp\OneDrive\Desktop\imagesandreports
Fine-tunes Stable Diffusion XL to generate mystical door images
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import torch
from diffusers import StableDiffusionXLPipeline, DDPMScheduler
from diffusers.training_utils import set_seed
from peft import LoraConfig, get_peft_model
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torchvision.transforms as transforms

class DoorImageDataset(Dataset):
    """Dataset for door images with captions"""
    
    def __init__(self, image_dir: str, captions: List[str]):
        self.image_dir = Path(image_dir)
        self.captions = captions
        self.transform = transforms.Compose([
            transforms.Resize((512, 512)),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5])
        ])
        
        # Load all PNG/JPG images
        self.images = list(self.image_dir.glob("*.png")) + list(self.image_dir.glob("*.jpg"))
        print(f"[Dataset] Found {len(self.images)} images in {image_dir}")
        
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        image_path = self.images[idx]
        image = Image.open(image_path).convert("RGB")
        image = self.transform(image)
        
        # Use caption or default
        caption = self.captions[idx % len(self.captions)]
        
        return {"image": image, "caption": caption}

class DoorLoRATrainer:
    """Train LoRA on door images"""
    
    def __init__(self, image_dir: str, output_dir: str = "models/csf-image/checkpoints"):
        self.image_dir = Path(image_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Door style captions
        self.captions = [
            "mystical door, ancient stone archway, ethereal fog, glowing light, dreamlike atmosphere, cinematic lighting, dark fantasy, high detail, 8k",
            "enchanted garden door, overgrown stone doorway, glowing vines, bioluminescent plants, starry night sky, magical atmosphere, soft purple and green lighting",
            "cosmic void door, swirling nebula and starlight through ancient archway, deep space colors, ethereal energy, mystical portal, dark blue and purple hues",
            "reflecting water door, tranquil pool surface as doorway, moonlight ripples, underwater scene visible through surface, peaceful serenity, silver and blue tones",
            "ancient temple door, weathered stone archway with mysterious symbols, golden light seeping through cracks, sacred atmosphere, dust motes dancing in light beams"
        ]
        
    def prepare_dataset(self) -> DataLoader:
        """Create dataset and dataloader"""
        if not self.image_dir.exists():
            print(f"[ERROR] Image directory not found: {self.image_dir}")
            return None
        
        dataset = DoorImageDataset(self.image_dir, self.captions)
        dataloader = DataLoader(dataset, batch_size=2, shuffle=True, num_workers=0)
        return dataloader
    
    def train(self, epochs: int = 3, learning_rate: float = 1e-4):
        """Execute LoRA training"""
        print("\n" + "="*60)
        print("[DOOR LORA TRAINING]")
        print("="*60)
        
        # Check for GPU - use GPU if available with memory optimizations
        if torch.cuda.is_available():
            device = torch.device("cuda")
            print(f"[Device] Using: {device}")
            print(f"[GPU] {torch.cuda.get_device_name(0)}")
            print("[INFO] GPU training with memory optimizations enabled")
        else:
            device = torch.device("cpu")
            print(f"[Device] Using: {device}")
            print("[INFO] CPU training - will be slow")
        
        # Prepare dataset
        print("\n[Dataset] Loading door images...")
        dataloader = self.prepare_dataset()
        if dataloader is None:
            return False
        
        # Load base model (use SD 1.5 for smaller footprint ~4GB vs SDXL ~13GB)
        print("\n[Model] Loading Stable Diffusion 1.5...")
        print("[Model] This will download ~4GB on first run...")
        
        try:
            from diffusers import StableDiffusionPipeline
            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16" if device.type == "cuda" else None
            )
            # Enable memory optimizations
            if device.type == "cuda":
                pipe.enable_attention_slicing()
                pipe.enable_vae_slicing()
            pipe = pipe.to(device)
            print("[Model] Base model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Configure LoRA
        print("\n[LoRA] Configuring LoRA adapters...")
        lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["to_q", "to_v"],
            lora_dropout=0.05,
            bias="none"
        )
        
        # Add LoRA to model
        pipe.unet = get_peft_model(pipe.unet, lora_config)
        pipe.unet.print_trainable_parameters()
        
        # Training setup
        optimizer = torch.optim.AdamW(pipe.unet.parameters(), lr=learning_rate)
        
        print(f"\n[Training] Configuration:")
        print(f"  • Epochs: {epochs}")
        print(f"  • Batch size: 2")
        print(f"  • Learning rate: {learning_rate}")
        print(f"  • LoRA rank: 16")
        print(f"  • Device: {device}")
        
        # Training loop
        print("\n[Training] Starting training loop...")
        global_step = 0
        
        for epoch in range(epochs):
            print(f"\n[Epoch {epoch+1}/{epochs}]")
            epoch_loss = 0
            
            for batch_idx, batch in enumerate(dataloader):
                images = batch["image"].to(device)
                if device.type == "cuda":
                    images = images.to(torch.float16)
                captions = batch["caption"]
                
                # Encode images to latents
                with torch.no_grad():
                    latents = pipe.vae.encode(images).latent_dist.sample() * 0.18215
                
                # Add noise
                noise = torch.randn_like(latents)
                timesteps = torch.randint(0, 1000, (latents.shape[0],), device=device).long()
                noisy_latents = pipe.scheduler.add_noise(latents, noise, timesteps)
                
                # Get text embeddings
                text_inputs = pipe.tokenizer(
                    captions,
                    padding="max_length",
                    max_length=77,
                    truncation=True,
                    return_tensors="pt"
                ).to(device)
                text_embeddings = pipe.text_encoder(text_inputs.input_ids)[0]
                
                # Predict noise
                model_pred = pipe.unet(noisy_latents, timesteps, text_embeddings).sample
                
                # Calculate loss
                loss = torch.nn.functional.mse_loss(model_pred.float(), noise.float(), reduction="mean")
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                global_step += 1
                
                if global_step % 10 == 0:
                    print(f"  Step {global_step}: Loss = {loss.item():.4f}")
            
            avg_loss = epoch_loss / len(dataloader)
            print(f"[Epoch {epoch+1}] Average loss: {avg_loss:.4f}")
            
            # Save checkpoint
            checkpoint_path = self.output_dir / f"checkpoint-epoch-{epoch+1}.safetensors"
            pipe.unet.save_pretrained(checkpoint_path)
            print(f"[Checkpoint] Saved: {checkpoint_path}")
        
        # Save final LoRA weights
        final_path = self.output_dir / "lantern-door-lora-final.safetensors"
        pipe.unet.save_pretrained(final_path)
        print(f"\n[Success] Final LoRA weights saved: {final_path}")
        
        return True

def main():
    """Main entry point"""
    import sys
    
    # Use the door images directory
    image_dir = r"C:\Users\alexp\OneDrive\Desktop\imagesandreports"
    
    trainer = DoorLoRATrainer(image_dir)
    
    # Train for 3 epochs
    success = trainer.train(epochs=3, learning_rate=1e-4)
    
    if success:
        print("\n" + "="*60)
        print("[TRAINING COMPLETE]")
        print("="*60)
        print("\n[Next Steps]")
        print("1. LoRA weights saved to: models/csf-image/checkpoints/")
        print("2. To use in generation, load LoRA with base SDXL model")
        print("3. Test generation with your trained style")
    else:
        print("\n[ERROR] Training failed")

if __name__ == "__main__":
    main()
