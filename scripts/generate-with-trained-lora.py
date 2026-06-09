#!/usr/bin/env python3
r"""
Generate door images using trained LoRA weights
Loads Stable Diffusion 1.5 + trained lantern-door-lora
"""

import torch
from diffusers import StableDiffusionPipeline
from pathlib import Path
import time
from typing import List

class TrainedLoRAGenerator:
    """Generate images using trained LoRA weights"""
    
    def __init__(self, lora_path="models/csf-image/checkpoints/lantern-door-lora-final.safetensors", output_dir="data/images/generated-doors"):
        self.lora_path = Path(lora_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Door style prompts matching training data
        self.prompts = [
            "mystical door, ancient stone archway, ethereal fog, glowing light, dreamlike atmosphere, cinematic lighting, dark fantasy, high detail, 8k",
            "enchanted garden door, overgrown stone doorway, glowing vines, bioluminescent plants, starry night sky, magical atmosphere, soft purple and green lighting",
            "cosmic void door, swirling nebula and starlight through ancient archway, deep space colors, ethereal energy, mystical portal, dark blue and purple hues",
            "reflecting water door, tranquil pool surface as doorway, moonlight ripples, underwater scene visible through surface, peaceful serenity, silver and blue tones",
            "ancient temple door, weathered stone archway with mysterious symbols, golden light seeping through cracks, sacred atmosphere, dust motes dancing in light beams"
        ]
        
        self.negative_prompt = "cartoon, anime, bright colors, childish, cute, simple, low detail, blurry, distorted"
    
    def load_model(self):
        """Load SD 1.5 with trained LoRA"""
        print("\n[LOAD] Loading Stable Diffusion 1.5 with trained LoRA...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[DEVICE] Using: {device}")
        
        # Load base model
        pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            use_safetensors=True
        )
        
        # Load LoRA weights
        print(f"[LORA] Loading trained weights from: {self.lora_path}")
        try:
            pipe.load_lora_weights(str(self.lora_path))
            print("[LORA] Weights loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load LoRA: {e}")
            print("[FALLBACK] Using base model without LoRA")
        
        # Memory optimizations
        if device == "cuda":
            pipe.enable_attention_slicing()
            pipe.enable_vae_slicing()
        
        pipe = pipe.to(device)
        return pipe
    
    def generate_batch(self, num_images: int = 5) -> List[str]:
        """Generate a batch of door images"""
        print(f"\n[GENERATE] Creating {num_images} door images...")
        print(f"[OUTPUT] {self.output_dir}")
        
        pipe = self.load_model()
        results = []
        
        for i in range(num_images):
            prompt = self.prompts[i % len(self.prompts)]
            print(f"\n[{i+1}/{num_images}] Generating: {prompt[:50]}...")
            
            try:
                image = pipe(
                    prompt=prompt,
                    negative_prompt=self.negative_prompt,
                    num_inference_steps=25,
                    guidance_scale=7.5,
                    height=512,
                    width=768
                ).images[0]
                
                # Save image
                timestamp = int(time.time())
                filename = f"door-{i+1}-{timestamp}.png"
                filepath = self.output_dir / filename
                image.save(filepath)
                
                print(f"[OK] Saved: {filepath}")
                results.append(str(filepath))
                
            except Exception as e:
                print(f"[ERROR] Generation failed: {e}")
        
        return results
    
    def generate_custom(self, prompt: str, num_variations: int = 1) -> List[str]:
        """Generate from custom prompt"""
        print(f"\n[CUSTOM] Generating {num_variations} image(s) from: {prompt}")
        
        pipe = self.load_model()
        results = []
        
        for i in range(num_variations):
            try:
                image = pipe(
                    prompt=prompt,
                    negative_prompt=self.negative_prompt,
                    num_inference_steps=25,
                    guidance_scale=7.5,
                    height=512,
                    width=768
                ).images[0]
                
                timestamp = int(time.time())
                filename = f"custom-{i+1}-{timestamp}.png"
                filepath = self.output_dir / filename
                image.save(filepath)
                
                print(f"[OK] Saved: {filepath}")
                results.append(str(filepath))
                
            except Exception as e:
                print(f"[ERROR] Generation failed: {e}")
        
        return results


def main():
    """Main entry point"""
    import sys
    
    generator = TrainedLoRAGenerator()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "custom" and len(sys.argv) > 2:
            prompt = " ".join(sys.argv[2:])
            generator.generate_custom(prompt)
        else:
            try:
                num = int(sys.argv[1])
                generator.generate_batch(num)
            except ValueError:
                print("Usage: python generate-with-trained-lora.py [number] or 'custom <prompt>'")
    else:
        # Default: generate 5 images
        generator.generate_batch(5)


if __name__ == "__main__":
    main()
