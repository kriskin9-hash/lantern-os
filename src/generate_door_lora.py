#!/usr/bin/env python3
"""
Generate door image using trained LoRA weights
Called from Node.js /api/dream/doors/image endpoint
"""

import sys
import json
import base64
from pathlib import Path
import torch
from diffusers import StableDiffusionPipeline

def generate_door_image(prompt: str, lora_path: str = "models/csf-image/checkpoints/lantern-door-lora-final.safetensors") -> dict:
    """Generate door image using trained LoRA"""
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    try:
        # Load base model
        pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            use_safetensors=True
        )
        
        # Load LoRA weights
        lora_path = Path(lora_path)
        if lora_path.exists():
            pipe.load_lora_weights(str(lora_path))
        else:
            return {"error": f"LoRA weights not found at {lora_path}"}
        
        # Memory optimizations
        if device == "cuda":
            pipe.enable_attention_slicing()
            pipe.enable_vae_slicing()
        
        pipe = pipe.to(device)
        
        # Generate image
        negative_prompt = "cartoon, anime, bright colors, childish, cute, simple, low detail, blurry, distorted"
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=25,
            guidance_scale=7.5,
            height=512,
            width=768
        ).images[0]
        
        # Convert to base64
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "success": True,
            "image": image_base64,
            "device": device,
            "prompt": prompt
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Read request from stdin
    req = json.loads(sys.stdin.read())
    prompt = req.get("prompt", "")
    lora_path = req.get("loraPath", "models/csf-image/checkpoints/lantern-door-lora-final.safetensors")
    
    if not prompt:
        print(json.dumps({"error": "No prompt provided"}))
        sys.exit(1)
    
    result = generate_door_image(prompt, lora_path)
    print(json.dumps(result))
