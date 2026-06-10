#!/usr/bin/env python3
"""
Extract model usage data from metrics JSONL logs for retraining.

Usage:
    python scripts/extract-model-usage.py --days 30 --model lantern-csf-dream
    python scripts/extract-model-usage.py --days 7 --all
"""

import argparse
import json
import os
from datetime import datetime, timedelta


def parse_args():
    parser = argparse.ArgumentParser(description="Extract model usage data for retraining")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back")
    parser.add_argument("--model", type=str, help="Filter by model ID")
    parser.add_argument("--all", action="store_true", help="Export all models")
    parser.add_argument("--output", type=str, default="models/training-data/model-usage-export.jsonl", help="Output path")
    return parser.parse_args()


def load_usage_records(metrics_dir, days_back):
    """Load model-usage.jsonl records within the time window."""
    cutoff = datetime.now() - timedelta(days=days_back)
    records = []

    usage_path = os.path.join(metrics_dir, "model-usage.jsonl")
    if not os.path.exists(usage_path):
        return records

    with open(usage_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                ts = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
                if ts >= cutoff:
                    records.append(record)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    return records


def export_records(records, output_path):
    """Write filtered records to output JSONL."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    print(f"Exported {len(records)} records to {output_path}")


def summarize_records(records):
    """Print summary statistics."""
    by_model = {}
    for r in records:
        model = r.get("modelId", "unknown")
        by_model.setdefault(model, []).append(r)

    print("\n--- Usage Summary ---")
    for model, model_records in sorted(by_model.items()):
        calls = len(model_records)
        errors = sum(1 for r in model_records if r.get("metadata", {}).get("status") == "failed")
        latencies = [r["metadata"]["latencyMs"] for r in model_records if isinstance(r.get("metadata", {}).get("latencyMs"), (int, float))]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        print(f"  {model}: {calls} calls, {errors} errors, {avg_latency:.0f}ms avg latency")
    print()


def main():
    args = parse_args()
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metrics_dir = os.path.join(repo_root, "data", "metrics")

    records = load_usage_records(metrics_dir, args.days)

    if args.model:
        records = [r for r in records if r.get("modelId") == args.model]

    summarize_records(records)
    export_records(records, os.path.join(repo_root, args.output))


if __name__ == "__main__":
    main()
