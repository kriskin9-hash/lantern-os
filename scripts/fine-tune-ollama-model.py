#!/usr/bin/env python3
"""
Fine-tune a Lantern OS text model using QLoRA (Unsloth) and deploy to Ollama.

Usage:
    python scripts/fine-tune-ollama-model.py \
        --model lantern-csf-dream \
        --data models/lantern-csf-dream/training-data.jsonl \
        --epochs 3
"""

import argparse
import json
import os
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune Lantern OS model with QLoRA")
    parser.add_argument("--model", type=str, required=True, help="Model ID (e.g., lantern-csf-dream)")
    parser.add_argument("--data", type=str, required=True, help="Training data JSONL path")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=2, help="Per-device batch size")
    parser.add_argument("--output-dir", type=str, help="Adapter output directory (default: models/<model>/adapters/)")
    parser.add_argument("--skip-ollama", action="store_true", help="Skip Ollama deployment")
    return parser.parse_args()


def check_unsloth():
    """Verify unsloth is available."""
    try:
        import unsloth
        print(f"Unsloth version: {unsloth.__version__}")
        return True
    except ImportError:
        print("Error: unsloth not installed. Install with:")
        print("  pip install unsloth")
        return False


def load_training_data(data_path):
    """Load instruction-following training data."""
    records = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                # Format as alpaca-style
                prompt = f"### Instruction:\n{record['instruction']}\n\n### Input:\n{record['input']}\n\n### Response:\n{record['output']}"
                records.append({"text": prompt})
            except (json.JSONDecodeError, KeyError):
                continue
    print(f"Loaded {len(records)} training samples from {data_path}")
    return records


def get_base_model(model_id):
    """Map Lantern model ID to HuggingFace base model."""
    mapping = {
        "lantern-csf-dream": "unsloth/mistral-7b-v0.2",
        "lantern-pcsf": "unsloth/Qwen2.5-Coder-7B",
        "lantern-convergance": "unsloth/Qwen2.5-Coder-14B",
    }
    return mapping.get(model_id, "unsloth/mistral-7b-v0.2")


def main():
    args = parse_args()

    if not check_unsloth():
        return 1

    if not os.path.exists(args.data):
        print(f"Error: Training data not found: {args.data}")
        return 1

    from unsloth import FastLanguageModel
    from datasets import Dataset
    from trl import SFTTrainer
    from transformers import TrainingArguments

    base_model = get_base_model(args.model)
    output_dir = args.output_dir or f"models/{args.model}/adapters"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading base model: {base_model}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=2048,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
    )

    records = load_training_data(args.data)
    dataset = Dataset.from_list(records)

    print(f"Starting QLoRA fine-tuning: epochs={args.epochs}, lr={args.lr}")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        args=TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            learning_rate=args.lr,
            logging_steps=10,
            save_strategy="epoch",
            fp16=True,
        ),
    )

    trainer.train()

    # Save adapter
    adapter_path = os.path.join(output_dir, "final")
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    print(f"Adapter saved to {adapter_path}")

    # Merge and save full model for Ollama
    if not args.skip_ollama:
        merged_path = os.path.join(output_dir, "merged")
        print(f"Merging adapter into full model...")
        model.save_pretrained_merged(merged_path, tokenizer, save_method="merged_16bit")

        # Create Ollama Modelfile
        modelfile_path = os.path.join(merged_path, "Modelfile")
        with open(modelfile_path, "w", encoding="utf-8") as f:
            f.write(f"FROM {merged_path}\n")
            f.write(f'SYSTEM """Lantern OS fine-tuned model: {args.model}"""\n')
        print(f"Created {modelfile_path}")

        # Deploy to Ollama
        ollama_model = f"{args.model}-v2"
        print(f"Deploying to Ollama as {ollama_model}...")
        result = subprocess.run(
            ["ollama", "create", ollama_model, "-f", modelfile_path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Successfully deployed to Ollama: {ollama_model}")
        else:
            print(f"Ollama deploy failed: {result.stderr}")
            return 1

    return 0


if __name__ == "__main__":
    exit(main())
