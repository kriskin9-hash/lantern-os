#!/usr/bin/env python3
r"""
Generate Three Doors images using local Stable Diffusion
Style: Abstract, mystical, dreamlike (not cartoonish)
Based on training data from C:\Users\alexp\OneDrive\Desktop\imagesandreports
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict
import requests
import base64
import time

class DoorImageGenerator:
    """Generate mystical door images using local Stable Diffusion"""
    
    def __init__(self, sd_url="http://127.0.0.1:7860", output_dir="data/images/three-doors"):
        self.sd_url = sd_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Stable Diffusion model chain (try multiple if available)
        self.sd_models = [
            "dreamshaper_xl",
            "sd_xl_base_1.0",
            "realistic_vision_v5",
            "deliberate_v3"
        ]
        
        # Door style prompts based on training data (abstract, mystical, not cartoonish)
        self.door_styles = {
            "elephant": {
                "positive": "mystical elephant door, ancient stone archway with carved elephant motifs, moonlit oasis scene through doorway, ethereal fog, glowing blue light, dreamlike atmosphere, cinematic lighting, dark fantasy, high detail, 8k",
                "negative": "cartoon, anime, bright colors, childish, cute, simple, low detail, blurry"
            },
            "garden": {
                "positive": "enchanted garden door, overgrown stone doorway with glowing vines, bioluminescent plants, starry night sky visible through arch, magical atmosphere, soft purple and green lighting, mystical forest, ethereal, high detail, 8k",
                "negative": "cartoon, anime, bright daylight, childish, cute, simple, low detail, blurry"
            },
            "cosmic": {
                "positive": "cosmic void door, swirling nebula and starlight through ancient archway, deep space colors, ethereal energy, mystical portal, dark blue and purple hues, dreamlike transcendence, cinematic, high detail, 8k",
                "negative": "cartoon, anime, bright colors, childish, cute, simple, low detail, blurry"
            },
            "water": {
                "positive": "reflecting water door, tranquil pool surface as doorway, moonlight ripples, underwater scene visible through surface, peaceful serenity, silver and blue tones, dreamlike meditation, cinematic, high detail, 8k",
                "negative": "cartoon, anime, bright colors, childish, cute, simple, low detail, blurry"
            },
            "ancient": {
                "positive": "ancient temple door, weathered stone archway with mysterious symbols, golden light seeping through cracks, sacred atmosphere, dust motes dancing in light beams, mystical runes, dark fantasy, high detail, 8k",
                "negative": "cartoon, anime, bright colors, childish, cute, simple, low detail, blurry"
            }
        }
    
    def check_sd_server(self) -> bool:
        """Check if Stable Diffusion server is running and get available models"""
        try:
            response = requests.get(f"{self.sd_url}/sdapi/v1/sd-models", timeout=2)
            if response.status_code == 200:
                models = response.json()
                print(f"[SD] Server running. Available models: {[m['title'] for m in models]}")
                return True
            return False
        except:
            return False
    
    def generate_door(self, door_type: str, custom_prompt: str = None) -> str:
        """Generate a single door image using SD model chain"""
        if not self.check_sd_server():
            print(f"[ERROR] Stable Diffusion server not running at {self.sd_url}")
            print("  Start with: python -m launch --api")
            return None
        
        style = self.door_styles.get(door_type, self.door_styles["cosmic"])
        prompt = custom_prompt or style["positive"]
        negative = style["negative"]
        
        # Try each SD model in sequence
        for sd_model in self.sd_models:
            print(f"[SD] Trying model: {sd_model}")
            
            payload = {
                "prompt": prompt,
                "negative_prompt": negative,
                "steps": 25,
                "width": 768,
                "height": 512,
                "cfg_scale": 7.5,
                "seed": -1,
                "sampler_name": "DPM++ 2M Karras",
                "override_settings": {
                    "sd_model_checkpoint": sd_model
                }
            }
            
            try:
                response = requests.post(f"{self.sd_url}/sdapi/v1/txt2img", json=payload, timeout=120)
                response.raise_for_status()
                result = response.json()
                
                # Decode base64 image
                image_data = base64.b64decode(result["images"][0])
                
                # Save to file
                timestamp = int(time.time())
                filename = f"{door_type}-door-{timestamp}-{sd_model.replace('/', '_')}.png"
                filepath = self.output_dir / filename
                
                with open(filepath, "wb") as f:
                    f.write(image_data)
                
                print(f"[OK] Generated with {sd_model}: {filepath}")
                return str(filepath)
                
            except Exception as e:
                print(f"[SD] Model {sd_model} failed: {e}")
                continue  # Try next model
        
        print(f"[ERROR] All SD models failed for {door_type}")
        return None
    
    def generate_three_doors(self, door_types: List[str] = None) -> List[str]:
        """Generate 3 doors for the Three Doors game"""
        if door_types is None:
            door_types = ["elephant", "garden", "cosmic"]
        
        print(f"\n[GENERATE] Creating 3 mystical doors...")
        print(f"  Output: {self.output_dir}")
        
        if not self.check_sd_server():
            print(f"[ERROR] Stable Diffusion server not running")
            print("  Start Automatic1111 with: python -m launch --api")
            return []
        
        results = []
        for door_type in door_types:
            print(f"\n  Generating {door_type} door...")
            filepath = self.generate_door(door_type)
            if filepath:
                results.append(filepath)
        
        return results
    
    def generate_from_text(self, door_description: str) -> str:
        """Generate door from custom text description"""
        prompt = f"mystical door, {door_description}, dreamlike atmosphere, ethereal lighting, dark fantasy, high detail, 8k"
        negative = "cartoon, anime, bright colors, childish, cute, simple, low detail, blurry"
        
        return self.generate_door("custom", prompt)


def main():
    """Main entry point"""
    import sys
    
    generator = DoorImageGenerator()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            # Check server status
            if generator.check_sd_server():
                print("[OK] Stable Diffusion server is running")
            else:
                print("[ERROR] Stable Diffusion server not running")
                print("  Start with: python -m launch --api")
        
        elif sys.argv[1] == "generate":
            # Generate 3 default doors
            generator.generate_three_doors()
        
        elif sys.argv[1] == "custom":
            # Generate from custom prompt
            if len(sys.argv) > 2:
                description = " ".join(sys.argv[2:])
                generator.generate_from_text(description)
            else:
                print("Usage: python generate-door-images.py custom <description>")
        
        else:
            # Generate specific door type
            door_type = sys.argv[1]
            generator.generate_door(door_type)
    else:
        # Default: generate 3 doors
        generator.generate_three_doors()


if __name__ == "__main__":
    main()
