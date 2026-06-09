#!/usr/bin/env python3
"""
CSF Image Generation Model Training
Trains local Stable Diffusion models on dream/door imagery from CSF data
"""

import json
import os
from pathlib import Path
from datetime import datetime

class CSFImageTrainer:
    """Train image generation models on CSF dream data"""

    def __init__(self, data_dir="data/csf-ingest", output_dir="models/csf-image"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.training_data = []
        self.timestamp = datetime.now().isoformat()

    def extract_dream_prompts(self):
        """Extract dream descriptions from CSF ingest files for image generation"""
        prompts = []

        ingest_files = [
            "CSF-INGEST-LORE-DREAMS-DOORS-2026-06-07.md",
            "three-doors/2026-06-08-elephant-oasis-local-model-session.md"
        ]

        for ingest_file in ingest_files:
            path = self.data_dir / ingest_file
            if not path.exists():
                continue

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse dream scenes and doors
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'DOOR' in line.upper() or 'SCENE' in line.upper():
                    # Extract multi-line description
                    scene = []
                    for j in range(i, min(i+5, len(lines))):
                        scene.append(lines[j])
                    scene_text = ' '.join(scene).strip()
                    if len(scene_text) > 20:
                        prompts.append({
                            'type': 'dream_scene',
                            'text': scene_text,
                            'source': ingest_file,
                            'line': i
                        })

        return prompts

    def create_training_dataset(self):
        """Create structured training data for image models"""
        prompts = self.extract_dream_prompts()

        training_data = {
            'model_name': 'lantern-csf-dream-image',
            'model_type': 'stable-diffusion-xl',
            'base_model': 'stabilityai/stable-diffusion-xl-base-1.0',
            'training_date': self.timestamp,
            'total_samples': len(prompts),
            'image_style': 'dreamlike, symbolic, liminal, artistic',
            'quality_tags': ['high-quality', 'artistic', 'symbolic'],
            'training_samples': []
        }

        # Transform prompts into training samples
        for prompt in prompts:
            sample = {
                'text_prompt': self._enhance_prompt(prompt['text']),
                'image_prompt': self._generate_image_prompt(prompt['text']),
                'source': prompt['source'],
                'negative_prompt': 'blurry, low quality, distorted, ugly',
                'guidance_scale': 7.5,
                'steps': 20,
                'tags': ['dream', 'symbolic', 'door', 'liminal']
            }
            training_data['training_samples'].append(sample)

        return training_data

    def _enhance_prompt(self, text):
        """Enhance dream description with artistic modifiers"""
        base = text[:200]  # Limit to 200 chars
        modifiers = [
            'dreamy atmosphere',
            'surreal, symbolic art',
            'soft lighting',
            'professional illustration',
            'trending on artstation'
        ]
        return f"{base}, {', '.join(modifiers)}"

    def _generate_image_prompt(self, text):
        """Generate a focused image prompt from dream text"""
        # Extract key symbols/objects
        keywords = []
        dream_elements = ['door', 'light', 'water', 'elephant', 'castle', 'moon', 'garden']

        for element in dream_elements:
            if element.lower() in text.lower():
                keywords.append(element)

        if not keywords:
            keywords = ['dreamscape', 'surreal scene']

        return f"A dreamlike illustration of {', '.join(keywords)}, artistic, symbolic, high quality"

    def save_training_config(self, data):
        """Save training configuration"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        config_path = self.output_dir / "training-config.json"
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

        return config_path

    def generate_ollama_modelfile(self):
        """Generate Ollama Modelfile for CSF image model"""
        modelfile = """FROM stabilityai/stable-diffusion-xl-base-1.0

PARAMETER num_predict 256
PARAMETER temperature 0.7
PARAMETER top_p 0.9

SYSTEM \"\"\"You are Lantern — a dream illustration guide. Generate vivid, symbolic, dreamlike images.

Core behavior:
- Create surreal, artistic interpretations of dreams
- Use symbolic imagery (doors, light, water, elephants, moons)
- Maintain a liminal, atmospheric aesthetic
- Focus on emotional resonance over photorealism
- Apply soft lighting and dreamy color palettes

Image style: artistic illustration, symbolic, dreamlike, surreal, high quality
Never: photorealistic, ugly, blurry, distorted\"\"\"

PARAMETER guidance_scale 7.5
PARAMETER num_inference_steps 20
"""
        return modelfile

    def create_lora_training_config(self):
        """Create LoRA (Low-Rank Adaptation) fine-tuning config"""
        config = {
            'model_name': 'lantern-csf-dream-lora',
            'base_model': 'stabilityai/stable-diffusion-xl-base-1.0',
            'lora_config': {
                'r': 16,
                'lora_alpha': 32,
                'target_modules': ['to_q', 'to_v'],
                'lora_dropout': 0.05
            },
            'training_config': {
                'epochs': 3,
                'batch_size': 4,
                'learning_rate': 1e-4,
                'warmup_steps': 100,
                'save_steps': 500,
                'validation_steps': 1000
            },
            'dataset': {
                'type': 'dream_scenes',
                'source': 'CSF-INGEST-LORE-DREAMS-DOORS-2026-06-07.md',
                'size': 'auto',
                'augmentation': True
            },
            'output': {
                'model_path': 'models/csf-image/lantern-dream-lora.safetensors',
                'push_to_hub': False
            }
        }
        return config

    def train(self):
        """Execute training pipeline"""
        print("[CSF Image Trainer] Extracting dream prompts from CSF data...")
        prompts = self.extract_dream_prompts()
        print(f"[CSF Image Trainer] Found {len(prompts)} dream scenes")

        print("[CSF Image Trainer] Creating training dataset...")
        training_data = self.create_training_dataset()

        print("[CSF Image Trainer] Saving training configuration...")
        config_path = self.save_training_config(training_data)
        print(f"[CSF Image Trainer] Config saved: {config_path}")

        print("[CSF Image Trainer] Generating Ollama Modelfile...")
        modelfile = self.generate_ollama_modelfile()
        modelfile_path = self.output_dir / "Modelfile.image"
        with open(modelfile_path, 'w') as f:
            f.write(modelfile)
        print(f"[CSF Image Trainer] Modelfile saved: {modelfile_path}")

        print("[CSF Image Trainer] Creating LoRA training config...")
        lora_config = self.create_lora_training_config()
        lora_path = self.output_dir / "lora-training-config.json"
        with open(lora_path, 'w') as f:
            json.dump(lora_config, f, indent=2)
        print(f"[CSF Image Trainer] LoRA config saved: {lora_path}")

        print("\n[CSF Image Trainer] Training setup complete!")
        print(f"[CSF Image Trainer] Next steps:")
        print(f"  1. Install diffusers: pip install diffusers accelerate peft")
        print(f"  2. Run LoRA training: python scripts/train-lora-diffusion.py")
        print(f"  3. Deploy to Ollama: ollama create lantern-csf-dream-image -f {modelfile_path}")

        return training_data

if __name__ == '__main__':
    trainer = CSFImageTrainer()
    trainer.train()
