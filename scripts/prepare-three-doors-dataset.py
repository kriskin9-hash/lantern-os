#!/usr/bin/env python3
"""
Three Doors Image Dataset Preparation
Organize and prepare existing Three Doors screenshots for model training
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class ThreeDoorsDatassetPreparer:
    """Prepare Three Doors image collection for training"""

    def __init__(self, source_dir="C:\\Users\\alexp\\OneDrive\\Desktop\\imagesandreports"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path("training_data/three-doors-images")
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
        self.dataset_manifest = {
            'name': 'three-doors-game-images',
            'timestamp': datetime.now().isoformat(),
            'total_images': 0,
            'categories': {},
            'images': []
        }

    def discover_images(self):
        """Find all images in the source directory"""
        images = []

        if not self.source_dir.exists():
            print(f"⚠️  Source directory not found: {self.source_dir}")
            print("   Creating example structure...")
            self.source_dir.mkdir(parents=True, exist_ok=True)
            return images

        print(f"🔍 Scanning for images in {self.source_dir}")

        for ext in self.image_extensions:
            found = list(self.source_dir.glob(f"**/*{ext}"))
            found += list(self.source_dir.glob(f"**/*{ext.upper()}"))
            images.extend(found)

        print(f"✓ Found {len(images)} images")
        return images

    def categorize_images(self, images):
        """Categorize images by door/scene type"""
        categories = defaultdict(list)

        door_types = {
            'elephant': ['elephant', 'oasis', 'water'],
            'reflecting': ['reflect', 'water', 'mirror'],
            'castle': ['castle', 'battle', 'fortress'],
            'library': ['library', 'book', 'archive'],
            'garden': ['garden', 'plant', 'green'],
            'bathroom': ['bath', 'mirror', 'sink'],
            'door': ['door', 'entrance', 'threshold'],
            'unknown': []
        }

        for img_path in images:
            filename = img_path.name.lower()
            categorized = False

            for door_type, keywords in door_types.items():
                if any(kw in filename for kw in keywords):
                    categories[door_type].append(img_path)
                    categorized = True
                    break

            if not categorized:
                categories['unknown'].append(img_path)

        return dict(categories)

    def create_training_manifest(self, images, categories):
        """Create manifest for model training"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("📋 Creating training manifest...")

        manifest = {
            'dataset_name': 'three-doors-visual-dataset',
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'source': str(self.source_dir),
            'total_images': len(images),
            'categories': {},
            'training_split': {
                'train': 0.8,
                'val': 0.1,
                'test': 0.1
            },
            'images': []
        }

        # Add category info
        for door_type, door_images in categories.items():
            manifest['categories'][door_type] = {
                'count': len(door_images),
                'images': [str(img.relative_to(self.source_dir)) for img in door_images[:5]]
            }

        # Build image entries
        for idx, img_path in enumerate(images):
            # Determine category
            category = 'unknown'
            for door_type, door_images in categories.items():
                if img_path in door_images:
                    category = door_type
                    break

            entry = {
                'id': f"three-doors-{idx:05d}",
                'filename': img_path.name,
                'path': str(img_path.relative_to(self.source_dir)),
                'full_path': str(img_path),
                'size_bytes': img_path.stat().st_size,
                'category': category,
                'captions': [
                    f"Three Doors game screenshot: {category} scene",
                    f"In-game scene from {category} door",
                    f"Symbolic {category} imagery from Three Doors"
                ],
                'tags': ['three-doors', 'game', 'screenshot', 'symbolic', category],
                'split': 'train' if idx % 10 < 8 else ('val' if idx % 10 < 9 else 'test')
            }

            manifest['images'].append(entry)

        # Save manifest
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"✓ Manifest saved: {manifest_path}")
        return manifest

    def create_training_splits(self, manifest):
        """Create train/val/test split directories"""
        print("📂 Creating training splits...")

        splits = defaultdict(list)
        for img_entry in manifest['images']:
            splits[img_entry['split']].append(img_entry)

        split_info = {
            'train': len(splits['train']),
            'val': len(splits['val']),
            'test': len(splits['test'])
        }

        print(f"  Train: {split_info['train']} images")
        print(f"  Val:   {split_info['val']} images")
        print(f"  Test:  {split_info['test']} images")

        # Create split manifest
        splits_path = self.output_dir / "splits.json"
        with open(splits_path, 'w') as f:
            json.dump({
                'splits': split_info,
                'train': [e['id'] for e in splits['train']],
                'val': [e['id'] for e in splits['val']],
                'test': [e['id'] for e in splits['test']]
            }, f, indent=2)

        return split_info

    def create_caption_templates(self):
        """Create caption templates for different image types"""
        templates = {
            'elephant': [
                "The Elephant Door oasis at night: serene water reflecting moonlight, gentle elephants",
                "Sacred elephant sanctuary with jasmine-scented water and peaceful energy",
                "Liminal elephant realm: moon, water, ancient wisdom"
            ],
            'reflecting': [
                "Mirror surface of still water, infinite reflection, threshold space",
                "The Reflecting Water Door: truth in reflection, boundaries dissolving",
                "Liminal reflection: water as mirror, self-knowledge, truth"
            ],
            'castle': [
                "Stone fortress visible through mist, security, fortress of soul",
                "The Castle Door: ancient battlements, lantern above gate, return home",
                "Symbolic return: castle gates, safety, homecoming"
            ],
            'library': [
                "Archive of dreams: books, soft light, knowledge sanctuary",
                "The Library Door: endless stories, memory, wisdom preserved",
                "Symbolic knowledge: books, soft illumination, archives"
            ],
            'garden': [
                "Growing place: green abundance, natural growth, flourishing",
                "The Garden Door: plants, blooming, transformation, renewal",
                "Symbolic growth: flora, natural beauty, seasons of soul"
            ],
            'bathroom': [
                "Threshold of cleansing: water, mirror, preparation",
                "The Bathroom Door: reflection, water, personal ritual",
                "Symbolic cleansing: mirror self-reflection, water renewal"
            ],
            'door': [
                "Threshold between worlds: doors, passages, choice",
                "The Door archetype: entrance, decision point, passage",
                "Liminal threshold: crossing between states of being"
            ]
        }

        templates_path = self.output_dir / "caption-templates.json"
        with open(templates_path, 'w') as f:
            json.dump(templates, f, indent=2)

        return templates

    def create_training_config(self, manifest, split_info):
        """Create configuration for multimodal training"""
        config = {
            'training_task': 'image-to-caption-generation',
            'models_to_train': [
                'three-doors-image-classifier',
                'three-doors-caption-generator',
                'three-doors-stable-diffusion-lora'
            ],
            'dataset': {
                'name': 'three-doors-visual',
                'total_images': len(manifest['images']),
                'train_count': split_info['train'],
                'val_count': split_info['val'],
                'test_count': split_info['test'],
                'categories': list(manifest['categories'].keys())
            },
            'training_params': {
                'image_classifier': {
                    'model': 'resnet50-pretrained',
                    'epochs': 10,
                    'batch_size': 32,
                    'learning_rate': 1e-4
                },
                'caption_generator': {
                    'model': 'blip-image-captioning',
                    'epochs': 5,
                    'batch_size': 16,
                    'learning_rate': 5e-5
                },
                'stable_diffusion_lora': {
                    'base_model': 'stabilityai/stable-diffusion-xl-base-1.0',
                    'epochs': 3,
                    'batch_size': 4,
                    'learning_rate': 1e-4,
                    'lora_rank': 16
                }
            }
        }

        config_path = self.output_dir / "training-config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return config

    def prepare(self):
        """Execute full dataset preparation"""
        print("\n🎨 Three Doors Visual Dataset Preparation")
        print("=" * 50)

        # Discover images
        images = self.discover_images()
        if not images:
            print("⚠️  No images found. Please add images to:")
            print(f"   {self.source_dir}")
            return False

        # Categorize
        categories = self.categorize_images(images)
        print("\n📊 Image Categories:")
        for door_type, door_images in categories.items():
            print(f"  {door_type}: {len(door_images)} images")

        # Create manifests
        manifest = self.create_training_manifest(images, categories)
        split_info = self.create_training_splits(manifest)

        # Create templates
        templates = self.create_caption_templates()
        print(f"✓ Created caption templates for {len(templates)} door types")

        # Create training config
        config = self.create_training_config(manifest, split_info)
        print(f"✓ Created training configuration")

        print("\n" + "=" * 50)
        print("✓ Dataset preparation complete!")
        print(f"\n📁 Output directory: {self.output_dir}")
        print("\n📄 Generated files:")
        print("  • manifest.json — Full image inventory")
        print("  • splits.json — Train/val/test split")
        print("  • caption-templates.json — Symbolic captions")
        print("  • training-config.json — Model training config")

        print("\n🚀 Next steps:")
        print("  1. Review manifest to verify image categorization")
        print("  2. Update captions if needed (caption-templates.json)")
        print("  3. Run: python scripts/train-three-doors-models.py")
        print("  4. Deploy to Ollama: lantern-three-doors-vision")

        return True


if __name__ == '__main__':
    preparer = ThreeDoorsDatassetPreparer()
    success = preparer.prepare()
    exit(0 if success else 1)
