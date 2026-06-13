#!/usr/bin/env python3
"""
Generate the first grounded Lantern OS v1 training dataset.

This script intentionally does not invent examples. It reads committed source
files, splits them into source-grounded records, rejects likely secrets, assigns
privacy/evidence metadata, and writes JSONL plus a manifest.

Default output is local-only under data/training/. Review outputs before any
training run or commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_SOURCES = [
    "content/dream-journal/ingest-2026-06-07.md",
    "data/csf-ingest/CSF-INGEST-LORE-DREAMS-DOORS-2026-06-07.md",
    "apps/lantern-garage/lib/convergance-os/profiles.js",
    "models/lantern-csf-dream/Modelfile",
    "models/lantern-pcsf/Modelfile",
    "models/lantern-convergance/Modelfile",
]

SECRET_PATTERNS = [
    ("discord_token", re.compile(r"[MN][A-Za-z\d_-]{23,}\.[A-Za-z\d_-]{6,}\.[A-Za-z\d_-]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("bearer_token_literal", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{16,}", re.IGNORECASE)),
    ("env_secret_assignment", re.compile(r"(?i)\b(API_KEY|TOKEN|SECRET|PASSWORD)\b\s*=\s*[^\s#]+")),
]

SECTION_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class TrainingRecord:
    instruction: str
    input: str
    output: str
    tags: List[str]
    source: str
    section: str
    privacy: str
    evidenceClass: str
    sourceHash: str


@dataclass
class RejectedRecord:
    source: str
    section: str
    reason: str
    matchedPatterns: List[str]
    sourceHash: str


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_source(path: str) -> str:
    full_path = REPO_ROOT / path
    if not full_path.exists():
        raise FileNotFoundError(f"source not found: {path}")
    return full_path.read_text(encoding="utf-8")


def detect_secrets(text: str) -> List[str]:
    matches: List[str] = []
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            matches.append(name)
    return matches


def split_markdown_sections(text: str, source: str) -> List[Tuple[str, str]]:
    if source.endswith(".js") or source.endswith("Modelfile"):
        return [(Path(source).name, text.strip())]

    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return [(Path(source).name, text.strip())]

    sections: List[Tuple[str, str]] = []
    for idx, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((title, body))
    return sections


def privacy_for_source(source: str) -> str:
    if source.startswith("content/dream-journal/"):
        return "private-local-only"
    if source.startswith("data/csf-ingest/"):
        return "private-local-only"
    return "public-safe"


def tags_for_source(source: str, section: str) -> List[str]:
    tags = ["lantern-v1", "source-grounded"]
    lower = f"{source} {section}".lower()
    if "dream" in lower or "door" in lower:
        tags.append("lantern-csf-dream")
    if "pcsf" in lower or "provider" in lower or "capacity" in lower:
        tags.append("lantern-pcsf")
    if "converg" in lower or "receipt" in lower:
        tags.append("lantern-convergance")
    if "modelfile" in lower or source.startswith("models/"):
        tags.append("model-contract")
    if "profiles.js" in source:
        tags.append("profile-contract")
    return sorted(set(tags))


def instruction_for_source(source: str) -> str:
    if source.startswith("content/dream-journal/"):
        return (
            "Preserve this Dream Journal canon as source-grounded local context. "
            "Do not treat it as proof, command, or public data."
        )
    if source.startswith("data/csf-ingest/"):
        return (
            "Preserve this CSF/CADD symbolic memory as source-grounded local context. "
            "Keep lore separate from proof and respect privacy boundaries."
        )
    if "profiles.js" in source:
        return (
            "Use this Lantern model profile contract as a behavior target for routing, "
            "capacity, and response-style evaluation."
        )
    if source.startswith("models/"):
        return (
            "Use this Ollama Modelfile as a v0 behavior reference, not as evidence "
            "that a fine-tuned model exists."
        )
    return "Preserve this source-grounded Lantern OS training context without inventing details."


def make_record(source: str, section: str, body: str) -> TrainingRecord:
    source_hash = sha256_text(body)
    return TrainingRecord(
        instruction=instruction_for_source(source),
        input=json.dumps(
            {
                "source": source,
                "section": section,
                "boundary": privacy_for_source(source),
            },
            ensure_ascii=False,
        ),
        output=body,
        tags=tags_for_source(source, section),
        source=source,
        section=section,
        privacy=privacy_for_source(source),
        evidenceClass="source-derived",
        sourceHash=source_hash,
    )


def build_records(sources: Iterable[str], min_chars: int) -> Tuple[List[TrainingRecord], List[RejectedRecord]]:
    accepted: List[TrainingRecord] = []
    rejected: List[RejectedRecord] = []

    for source in sources:
        text = read_source(source)
        for section, body in split_markdown_sections(text, source):
            body = body.strip()
            source_hash = sha256_text(body)
            if len(body) < min_chars:
                rejected.append(
                    RejectedRecord(source, section, "too_short", [], source_hash)
                )
                continue
            secret_matches = detect_secrets(body)
            if secret_matches:
                rejected.append(
                    RejectedRecord(source, section, "secret_pattern_detected", secret_matches, source_hash)
                )
                continue
            accepted.append(make_record(source, section, body))

    # Stable deterministic order.
    accepted.sort(key=lambda r: (r.source, r.section, r.sourceHash))
    rejected.sort(key=lambda r: (r.source, r.section, r.sourceHash))
    return accepted, rejected


def split_train_validation(records: List[TrainingRecord], validation_mod: int = 7) -> Tuple[List[TrainingRecord], List[TrainingRecord]]:
    train: List[TrainingRecord] = []
    validation: List[TrainingRecord] = []
    for record in records:
        bucket = int(record.sourceHash[:8], 16) % 10
        if bucket == validation_mod:
            validation.append(record)
        else:
            train.append(record)
    if records and not validation:
        validation.append(records[-1])
        train = records[:-1]
    return train, validation


def write_jsonl(path: Path, rows: Iterable[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate grounded Lantern OS v1 JSONL training data.")
    parser.add_argument("--out-dir", default="data/training/lantern-v1", help="Output directory, relative to repo root.")
    parser.add_argument("--source", action="append", dest="sources", help="Source path to include. Repeatable. Defaults to curated v1 sources.")
    parser.add_argument("--min-chars", type=int, default=80, help="Reject sections shorter than this many chars.")
    parser.add_argument("--dry-run", action="store_true", help="Print manifest only; do not write files.")
    args = parser.parse_args()

    sources = args.sources or DEFAULT_SOURCES
    accepted, rejected = build_records(sources, args.min_chars)
    train, validation = split_train_validation(accepted)

    out_dir = REPO_ROOT / args.out_dir
    train_path = out_dir / "lantern-v1.train.jsonl"
    validation_path = out_dir / "lantern-v1.validation.jsonl"
    rejected_path = out_dir / "rejected-records.jsonl"
    manifest_path = out_dir / "lantern-v1.manifest.json"

    manifest = {
        "dataset": "lantern-v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "generator": "src/training/generate_training_dataset.py",
        "sources": sources,
        "counts": {
            "accepted": len(accepted),
            "train": len(train),
            "validation": len(validation),
            "rejected": len(rejected),
        },
        "privacyCounts": {},
        "evidenceClassCounts": {},
        "outputs": {
            "train": str(train_path.relative_to(REPO_ROOT)),
            "validation": str(validation_path.relative_to(REPO_ROOT)),
            "rejected": str(rejected_path.relative_to(REPO_ROOT)),
            "manifest": str(manifest_path.relative_to(REPO_ROOT)),
        },
        "promotionBoundary": "This dataset is source-derived but not automatically approved for model v1 training. Review rejected records, privacy labels, and sample outputs before training.",
    }

    for record in accepted:
        manifest["privacyCounts"][record.privacy] = manifest["privacyCounts"].get(record.privacy, 0) + 1
        manifest["evidenceClassCounts"][record.evidenceClass] = manifest["evidenceClassCounts"].get(record.evidenceClass, 0) + 1

    if args.dry_run:
        print(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    write_jsonl(train_path, train)
    write_jsonl(validation_path, validation)
    write_jsonl(rejected_path, rejected)
    write_json(manifest_path, manifest)

    print(f"accepted={len(accepted)} train={len(train)} validation={len(validation)} rejected={len(rejected)}")
    print(f"manifest={manifest_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
