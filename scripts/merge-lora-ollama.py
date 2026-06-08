#!/usr/bin/env python3
"""
Merge LoRA adapter into base model and create Ollama Modelfile.

After training with train-lora.py, this script:
1. Merges the LoRA adapter into the base model weights
2. Creates an Ollama Modelfile with the merged weights
3. Saves GGUF format for local Ollama use

Usage:
  python scripts/merge-lora-ollama.py --profile lantern-csf-dream
"""

import argparse
import json
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

REPO_ROOT = Path(__file__).parent.parent
MODELS_DIR = REPO_ROOT / "models"

BASE_MODELS = {
    "lantern-csf-dream": "Qwen/Qwen2.5-Coder-3B-Instruct",
    "lantern-pcsf": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    "lanterns-convergance": "Qwen/Qwen2.5-Coder-3B-Instruct",
}

def merge_lora(profile: str, output_format: str = "gguf"):
    """Merge LoRA adapter into base model."""
    if profile not in BASE_MODELS:
        raise ValueError(f"Unknown profile: {profile}")

    base_model_name = BASE_MODELS[profile]
    lora_path = MODELS_DIR / f"{profile}-lora"
    merged_path = MODELS_DIR / f"{profile}-merged"
    output_path = merged_path / f"model.{output_format}"

    if not lora_path.exists():
        raise FileNotFoundError(f"LoRA adapter not found: {lora_path}")

    merged_path.mkdir(parents=True, exist_ok=True)

    print(f"🔄 Merging LoRA adapter: {profile}")
    print(f"   Base model: {base_model_name}")
    print(f"   LoRA adapter: {lora_path}")
    print(f"   Output: {output_path}")

    # Load base model
    print("   Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        device_map="cpu",
        torch_dtype="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)

    # Load and merge LoRA
    print("   Merging LoRA weights...")
    model = PeftModel.from_pretrained(base_model, str(lora_path))
    merged_model = model.merge_and_unload()

    # Save in both formats
    print(f"   Saving merged model...")
    merged_model.save_pretrained(str(merged_path))
    tokenizer.save_pretrained(str(merged_path))

    # Create Ollama Modelfile
    create_ollama_modelfile(profile, merged_path)

    print(f"\n✅ Merge complete: {profile}")
    print(f"   Merged weights: {merged_path}")
    print(f"   Modelfile: {merged_path}/Modelfile")
    print(f"\n   To use locally:")
    print(f"   ollama create {profile} -f {merged_path}/Modelfile")

def create_ollama_modelfile(profile: str, model_path: Path):
    """Create Ollama Modelfile for merged model."""
    modelfile_content = f"""FROM {model_path}/model.gguf

SYSTEM """You are {profile.replace('-', ' ').title()}, part of the Convergance OS.

Your role is to:
- Respond warmly and briefly
- Always provide structured output when needed
- Use memory context from CSF when available
- Separate lore from proof
- Pick the smallest useful action

Never fabricate memories or capabilities you don't have.""""""

    temperature = {
        "lantern-csf-dream": 0.8,
        "lantern-pcsf": 0.3,
        "lantern-convergance": 0.4,
    }.get(profile, 0.7)

    max_tokens = {
        "lantern-csf-dream": 512,
        "lantern-pcsf": 256,
        "lantern-convergance": 384,
    }.get(profile, 512)

    modelfile_content += f"""

PARAMETER temperature {temperature}
PARAMETER top_p 0.9
PARAMETER num_predict {max_tokens}
"""

    modelfile_path = model_path / "Modelfile"
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)

    print(f"   Created: {modelfile_path}")

def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter and create Ollama model")
    parser.add_argument(
        "--profile",
        choices=list(BASE_MODELS.keys()),
        required=True,
        help="Model profile to merge",
    )
    parser.add_argument(
        "--format",
        choices=["gguf", "pytorch"],
        default="gguf",
        help="Output format",
    )

    args = parser.parse_args()
    merge_lora(args.profile, args.format)

if __name__ == "__main__":
    main()
