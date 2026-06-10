#!/usr/bin/env python3
"""
Generate fine-tuning datasets from model usage logs.

Converts usage records into instruction-following format for QLoRA fine-tuning.

Usage:
    python scripts/generate-finetune-dataset.py \
        --input models/training-data/model-usage-export.jsonl \
        --output models/lantern-csf-dream/training-data.jsonl \
        --model lantern-csf-dream
"""

import argparse
import json
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Generate fine-tuning dataset from usage logs")
    parser.add_argument("--input", type=str, required=True, help="Input usage JSONL path")
    parser.add_argument("--output", type=str, required=True, help="Output training dataset path")
    parser.add_argument("--model", type=str, required=True, help="Target model ID")
    return parser.parse_args()


def build_instruction_record(record, model_id):
    """Convert a usage record into an instruction-following training sample."""
    action = record.get("action", "generate")
    metadata = record.get("metadata", {})

    if model_id == "lantern-csf-dream":
        instruction = "Analyze this dream for symbols and suggest 3 doors."
        input_text = metadata.get("entryText", "Dream text not available")
        output = json.dumps({
            "doors": metadata.get("doors", []),
            "symbols": metadata.get("symbols", []),
        })
    elif model_id == "lantern-pcsf":
        instruction = "Emit a PCSF receipt for this model call."
        input_text = f"Model: {metadata.get('modelId', 'unknown')}, Provider: {metadata.get('provider', 'unknown')}"
        output = json.dumps({
            "privacyBoundary": metadata.get("privacyBoundary", "local_private"),
            "claimBoundary": metadata.get("claimBoundary", "grounded"),
        })
    elif model_id == "lantern-convergance":
        instruction = "Make a promote/hold/archive decision for this work step."
        input_text = f"Model call: {metadata.get('modelId', 'unknown')}, Action: {action}"
        output = json.dumps({
            "decision": metadata.get("decision", "hold"),
            "confidence": 0.8,
        })
    else:
        return None

    return {
        "instruction": instruction,
        "input": input_text,
        "output": output,
        "timestamp": record.get("timestamp"),
        "model": model_id,
    }


def main():
    args = parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return 1

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    records_generated = 0
    with open(args.input, "r", encoding="utf-8") as inf, open(args.output, "w", encoding="utf-8") as outf:
        for line in inf:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if record.get("modelId") != args.model:
                    continue
                training_record = build_instruction_record(record, args.model)
                if training_record:
                    outf.write(json.dumps(training_record) + "\n")
                    records_generated += 1
            except (json.JSONDecodeError, KeyError):
                continue

    print(f"Generated {records_generated} training records for {args.model}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    exit(main())
