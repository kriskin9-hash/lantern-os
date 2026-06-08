#!/usr/bin/env python3
"""
LoRA fine-tuning for Convergance OS v1 models.

Fine-tunes qwen2.5-coder base models using QLoRA (4-bit quantization + LoRA adapters).
Outputs adapters to models/lantern-*-lora/ for merging into Ollama.

Usage:
  python scripts/train-lora.py --profile lantern-csf-dream --epochs 3
  python scripts/train-lora.py --profile lantern-pcsf --batch-size 4
"""

import json
import argparse
from pathlib import Path
from typing import Optional
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_dataset

REPO_ROOT = Path(__file__).parent.parent
TRAINING_DATA = REPO_ROOT / "training_data" / "lantern-v1-dataset.jsonl"
MODELS_DIR = REPO_ROOT / "models"

# Model configurations for each profile
PROFILE_CONFIG = {
    "lantern-csf-dream": {
        "base_model": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "lora_target_modules": ["q_proj", "v_proj", "k_proj", "o_proj", "up_proj", "down_proj"],
        "lora_rank": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "output_dir": MODELS_DIR / "lantern-csf-dream-lora",
    },
    "lantern-pcsf": {
        "base_model": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "lora_target_modules": ["q_proj", "v_proj", "k_proj", "o_proj", "up_proj", "down_proj"],
        "lora_rank": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "output_dir": MODELS_DIR / "lantern-pcsf-lora",
    },
    "lantern-convergance": {
        "base_model": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "lora_target_modules": ["q_proj", "v_proj", "k_proj", "o_proj", "up_proj", "down_proj"],
        "lora_rank": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "output_dir": MODELS_DIR / "lantern-convergance-lora",
    },
}

def setup_bnb_config():
    """Configure 4-bit quantization for QLoRA."""
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

def setup_lora_config(profile: str) -> LoraConfig:
    """Create LoRA adapter configuration."""
    config = PROFILE_CONFIG[profile]
    return LoraConfig(
        r=config["lora_rank"],
        lora_alpha=config["lora_alpha"],
        target_modules=config["lora_target_modules"],
        lora_dropout=config["lora_dropout"],
        bias="none",
        task_type="CAUSAL_LM",
    )

def load_dataset_from_jsonl(file_path: Path):
    """Load training data from JSONL file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Training data not found: {file_path}")

    data = []
    with open(file_path) as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    print(f"✓ Loaded {len(data)} training examples from {file_path}")
    return data

def format_instruction(example):
    """Format instruction tuple for training."""
    instruction = example.get("instruction", "")
    input_text = example.get("input", "")
    output_text = example.get("output", "")

    if input_text:
        text = f"Instruction: {instruction}\n\nInput: {input_text}\n\nOutput: {output_text}"
    else:
        text = f"Instruction: {instruction}\n\nOutput: {output_text}"

    return {"text": text}

def train(
    profile: str,
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-4,
    max_grad_norm: float = 0.3,
    warmup_ratio: float = 0.03,
):
    """Fine-tune a model using QLoRA."""
    if profile not in PROFILE_CONFIG:
        raise ValueError(f"Unknown profile: {profile}")

    config = PROFILE_CONFIG[profile]
    output_dir = config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🚀 Training {profile}")
    print(f"   Base model: {config['base_model']}")
    print(f"   Output: {output_dir}")
    print(f"   Epochs: {epochs}, Batch size: {batch_size}")

    # Load training data
    raw_data = load_dataset_from_jsonl(TRAINING_DATA)
    formatted_data = [format_instruction(ex) for ex in raw_data]

    # Create dataset
    dataset = load_dataset("json", data_files={"train": TRAINING_DATA}, split="train")
    dataset = dataset.map(format_instruction, remove_columns=["instruction", "input", "output"], batched=False)

    # Load model with QLoRA quantization
    print("   Loading model with 4-bit quantization...")
    bnb_config = setup_bnb_config()
    model = AutoModelForCausalLM.from_pretrained(
        config["base_model"],
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    # Prepare for LoRA
    model = prepare_model_for_kbit_training(model)
    lora_config = setup_lora_config(profile)
    model = get_peft_model(model, lora_config)

    # Setup tokenizer
    tokenizer = AutoTokenizer.from_pretrained(config["base_model"], trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=batch_size,
        num_train_epochs=epochs,
        learning_rate=learning_rate,
        warmup_ratio=warmup_ratio,
        max_grad_norm=max_grad_norm,
        save_strategy="epoch",
        save_total_limit=2,
        logging_steps=10,
        seed=42,
    )

    # Train
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=512,
        packing=False,
    )

    print("   Starting training...")
    trainer.train()

    # Save adapter
    print(f"   Saving LoRA adapter to {output_dir}...")
    model.save_pretrained(str(output_dir))

    print(f"\n✅ Training complete: {profile}")
    print(f"   Adapter: {output_dir}/adapter_config.json")
    print(f"   Weights: {output_dir}/adapter_model.bin")
    print(f"\n   Next: Merge adapter into base model for Ollama")
    print(f"   python scripts/merge-lora-ollama.py --profile {profile}")

def main():
    parser = argparse.ArgumentParser(description="Fine-tune Convergance OS models with LoRA")
    parser.add_argument(
        "--profile",
        choices=list(PROFILE_CONFIG.keys()),
        required=True,
        help="Model profile to train",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--warmup-ratio", type=float, default=0.03, help="Warmup ratio")
    parser.add_argument("--max-grad-norm", type=float, default=0.3, help="Max gradient norm")

    args = parser.parse_args()

    train(
        profile=args.profile,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        max_grad_norm=args.max_grad_norm,
    )

if __name__ == "__main__":
    main()
