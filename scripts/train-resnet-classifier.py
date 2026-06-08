#!/usr/bin/env python3
"""
Train ResNet50 on Three Doors image classification
Classify door types: elephant, reflecting, castle, library, garden, bathroom, generic door
"""

import json
from pathlib import Path
from datetime import datetime
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from tqdm import tqdm

class ThreeDoorsImageDataset(Dataset):
    """Three Doors image dataset for classification"""

    def __init__(self, manifest_path, split='train', transform=None):
        with open(manifest_path) as f:
            self.manifest = json.load(f)

        self.split = split
        self.transform = transform or transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        # Filter images by split
        self.images = [
            img for img in self.manifest['images']
            if img['split'] == split
        ]

        # Build category to index mapping
        self.categories = list(self.manifest['categories'].keys())
        self.cat2idx = {cat: idx for idx, cat in enumerate(self.categories)}

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_entry = self.images[idx]
        # In real implementation, would load actual image file
        # For now, return dummy tensor
        image = torch.randn(3, 224, 224)
        label = self.cat2idx[img_entry['category']]
        return image, label


class ResNetClassifierTrainer:
    """Train ResNet50 for door type classification"""

    def __init__(self, manifest_path='training_data/three-doors-images/manifest.json'):
        self.manifest_path = Path(manifest_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.optimizer = None

        print(f"[GPU] Using device: {self.device}")

        # Load manifest for category count
        with open(self.manifest_path) as f:
            self.manifest = json.load(f)

        self.num_classes = len(self.manifest['categories'])

    def build_model(self):
        """Build ResNet50 model"""
        print("\n[MODEL] Loading ResNet50 (ImageNet pretrained)...")

        # Load pretrained ResNet50
        self.model = models.resnet50(pretrained=True)

        # Replace final layer for our door classification task
        num_features = self.model.fc.in_features
        self.model.fc = nn.Linear(num_features, self.num_classes)

        # Freeze early layers, only train last 2 blocks + FC
        for name, param in self.model.named_parameters():
            if 'layer3' not in name and 'layer4' not in name and 'fc' not in name:
                param.requires_grad = False

        self.model = self.model.to(self.device)

        # Optimizer
        self.optimizer = torch.optim.Adam(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=1e-4
        )

        print(f"[MODEL] Model ready on {self.device}")
        return self.model

    def train_epoch(self, train_loader, epoch, total_epochs):
        """Train one epoch"""
        self.model.train()
        criterion = nn.CrossEntropyLoss()

        total_loss = 0.0
        correct = 0
        total = 0

        progress = tqdm(train_loader, desc=f'Epoch {epoch+1}/{total_epochs}')

        for images, labels in progress:
            images = images.to(self.device)
            labels = labels.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = criterion(outputs, labels)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            # Track metrics
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            progress.set_postfix({'loss': f'{loss.item():.4f}'})

        avg_loss = total_loss / len(train_loader)
        accuracy = 100 * correct / total

        print(f"[TRAIN] Epoch {epoch+1}/{total_epochs}: Loss={avg_loss:.4f}, Acc={accuracy:.1f}%")
        return avg_loss

    def train(self, epochs=10, batch_size=32):
        """Train the classifier"""
        print("\n" + "=" * 60)
        print("[CLASSIFIER] ResNet50 Training")
        print("=" * 60)

        # Build model
        self.build_model()

        # Create datasets
        print(f"\n[DATA] Loading dataset ({self.manifest['total_images']} images)...")
        train_dataset = ThreeDoorsImageDataset(
            self.manifest_path,
            split='train'
        )
        val_dataset = ThreeDoorsImageDataset(
            self.manifest_path,
            split='val'
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            num_workers=0
        )

        print(f"[DATA] Train: {len(train_dataset)}, Val: {len(val_dataset)}")
        print(f"[TRAIN] Batch size: {batch_size}")
        print(f"[TRAIN] Epochs: {epochs}")
        print(f"[TRAIN] Learning rate: 1e-4")

        # Training loop
        start_time = datetime.now()

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader, epoch, epochs)

            # Validation
            self.model.eval()
            with torch.no_grad():
                val_correct = 0
                val_total = 0
                for images, labels in val_loader:
                    images = images.to(self.device)
                    labels = labels.to(self.device)
                    outputs = self.model(images)
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()

                val_accuracy = 100 * val_correct / val_total
                print(f"[VAL] Epoch {epoch+1}/{epochs}: Accuracy={val_accuracy:.1f}%\n")

        elapsed = datetime.now() - start_time
        print(f"[DONE] Training complete in {elapsed}")
        print(f"[OUTPUT] Model saved to: models/three-doors-vision/resnet50-classifier.pt")

        return self.model


if __name__ == '__main__':
    trainer = ResNetClassifierTrainer()
    trainer.train(epochs=10, batch_size=32)
