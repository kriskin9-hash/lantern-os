#!/usr/bin/env python3
"""
Generate training dataset for Convergance OS v1 fine-tuning.

Builds 500-2,000 sanitized instruction tuples from:
- Existing dream logs (anonymized)
- RAG seeds (sanitized)
- CSF/CADD examples
- Three Doors patterns
- PCSF receipts

Output: training_data/lantern-v1-dataset.jsonl
Format: {"instruction": "...", "input": "...", "output": "..."}
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
RAG_SEEDS = REPO_ROOT / "rag" / "seeds"
TRAINING_DIR = REPO_ROOT / "training_data"
OUTPUT_FILE = TRAINING_DIR / "lantern-v1-dataset.jsonl"

# Ensure output directory exists
TRAINING_DIR.mkdir(exist_ok=True)

def anonymize_text(text: str) -> str:
    """Remove PII and identifiers."""
    # Remove emails
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", text)
    # Remove specific names (customize as needed)
    text = re.sub(r"\b(Alex|Courtney|alex-place)\b", "[PERSON]", text, flags=re.IGNORECASE)
    # Remove URLs
    text = re.sub(r"https?://[^\s]+", "[URL]", text)
    # Remove file paths
    text = re.sub(r"[/\\][\w\-./\\]+", "[PATH]", text)
    return text

def load_dream_examples() -> List[Dict]:
    """Load anonymized dream journal entries as examples."""
    examples = []
    dream_logs = DATA_DIR / "dream_journal"

    if dream_logs.exists():
        for jsonl_file in dream_logs.glob("*.jsonl"):
            try:
                with open(jsonl_file) as f:
                    for line in f:
                        entry = json.loads(line)
                        if "text" in entry:
                            examples.append({
                                "instruction": "User shares a dream memory",
                                "input": anonymize_text(entry["text"][:200]),
                                "output": f"I remember this moment. You've explored {entry.get('mood', 'mysterious')} territory before.\n\n[DOORS: Deeper reflection | Next chapter | Waking integration]",
                                "type": "dream_chat",
                                "source": "dream_journal"
                            })
            except Exception as e:
                print(f"Skipped {jsonl_file}: {e}")

    return examples

def load_rag_seed_examples() -> List[Dict]:
    """Load sanitized examples from RAG seeds."""
    examples = []

    if RAG_SEEDS.exists():
        for md_file in RAG_SEEDS.glob("*.md"):
            try:
                with open(md_file) as f:
                    content = f.read()
                    # Extract code blocks as input/output pairs
                    blocks = re.findall(r"```(?:text|json)?\n(.*?)```", content, re.DOTALL)
                    for i, block in enumerate(blocks[:3]):  # Limit 3 per file
                        if len(block.strip()) > 50:
                            examples.append({
                                "instruction": f"Process convergence-fitted data from {md_file.stem}",
                                "input": block.strip()[:300],
                                "output": "Data ingested and indexed into CSF archive with evidence classification.",
                                "type": "rag_ingest",
                                "source": str(md_file.stem)
                            })
            except Exception as e:
                print(f"Skipped {md_file}: {e}")

    return examples

def load_three_doors_examples() -> List[Dict]:
    """Generate Three Doors training examples."""
    examples = [
        {
            "instruction": "User enters a dream scene and asks what happens next",
            "input": "I'm standing in a library filled with glowing books. What can I do?",
            "output": "You run your hand along the shelves. Some volumes pulse with light, calling to you.\n\n[DOORS: Follow the brightest light | Open a random volume | Climb the spiral staircase]",
            "type": "three_doors",
            "source": "generated"
        },
        {
            "instruction": "User navigates through fantasy doors",
            "input": "I choose the door with the moon symbol",
            "output": "You push through silver-carved doors into a moonlit garden. The air shimmers with possibility.\n\n[DOORS: Approach the fountain | Explore the hedge maze | Call out to see who's here]",
            "type": "three_doors",
            "source": "generated"
        },
        {
            "instruction": "User explores a symbolic location",
            "input": "Tell me more about the bathhouse we visited before",
            "output": "The mosaic doors glow faintly. Shelby's footsteps echo in the steam-filled corridors. The water is always the right temperature.\n\n[DOORS: Enter the steam chamber | Visit the mirror pool | Find the meditation alcove]",
            "type": "three_doors",
            "source": "generated"
        },
    ]
    return examples

def load_pcsf_receipt_examples() -> List[Dict]:
    """Generate PCSF receipt training examples."""
    examples = [
        {
            "instruction": "Generate a PCSF capacity receipt for a chat request",
            "input": "User asked a question about DreamChat routing",
            "output": json.dumps({
                "timestamp": datetime.now().isoformat(),
                "capacityClass": "designed_capacity",
                "provider": "local",
                "metered": False,
                "privacyBoundary": "internal",
                "localProof": "ollama_running",
                "providerProof": "not_used",
                "fallbackUsed": False,
                "claimBoundary": "live"
            }),
            "type": "pcsf_receipt",
            "source": "generated"
        },
        {
            "instruction": "Generate a PCSF receipt when using cloud provider",
            "input": "User requested response from Gemini API",
            "output": json.dumps({
                "timestamp": datetime.now().isoformat(),
                "capacityClass": "observed_capacity",
                "provider": "gemini",
                "metered": True,
                "privacyBoundary": "external",
                "localProof": "not_used",
                "providerProof": "gemini_api_response",
                "fallbackUsed": False,
                "claimBoundary": "live"
            }),
            "type": "pcsf_receipt",
            "source": "generated"
        },
    ]
    return examples

def load_convergance_examples() -> List[Dict]:
    """Generate convergence loop receipt examples."""
    examples = [
        {
            "instruction": "Identify the next safest action in a convergence step",
            "input": "Step 1: Inspect repo state. Found 3 stale branches and 1 broken test.",
            "output": "Step 2: Identify sources. Stale branches are safe to prune. The broken test blocks validation. Next action: delete the 3 stale branches (smallest bounded action).",
            "type": "convergance_action",
            "source": "generated"
        },
        {
            "instruction": "Emit a convergence receipt for a completed step",
            "input": "Completed: Map claims to evidence for the API changes",
            "output": json.dumps({
                "step": 6,
                "stepName": "Map claims to evidence",
                "evidence": ["API changes tested", "backward compatibility verified"],
                "claims": ["API is stable", "no breaking changes"],
                "validation": "pass",
                "rollback": "revert commit abc123",
                "nextAction": "classify capability and boundary for deployment"
            }),
            "type": "convergance_action",
            "source": "generated"
        },
    ]
    return examples

def main():
    print("🔨 Generating training dataset for Convergance OS v1...")

    all_examples = []

    # Load from all sources
    print("  • Loading dream examples...")
    all_examples.extend(load_dream_examples())

    print("  • Loading RAG seed examples...")
    all_examples.extend(load_rag_seed_examples())

    print("  • Generating Three Doors examples...")
    all_examples.extend(load_three_doors_examples())

    print("  • Generating PCSF receipt examples...")
    all_examples.extend(load_pcsf_receipt_examples())

    print("  • Generating convergence examples...")
    all_examples.extend(load_convergance_examples())

    # Deduplicate and validate
    seen = set()
    unique_examples = []
    for ex in all_examples:
        key = (ex.get("instruction", ""), ex.get("input", "")[:50])
        if key not in seen:
            seen.add(key)
            unique_examples.append(ex)

    print(f"  • Total examples: {len(unique_examples)} (deduplicated)")

    # Write to JSONL
    with open(OUTPUT_FILE, "w") as f:
        for ex in unique_examples:
            f.write(json.dumps(ex) + "\n")

    print(f"\n✅ Dataset written to {OUTPUT_FILE}")
    print(f"   Size: {len(unique_examples)} examples")
    print(f"   Types: {set(ex['type'] for ex in unique_examples)}")

    # Summary stats
    by_type = {}
    for ex in unique_examples:
        t = ex.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    print("\n  Distribution:")
    for t, count in sorted(by_type.items()):
        print(f"    - {t}: {count}")

if __name__ == "__main__":
    main()
