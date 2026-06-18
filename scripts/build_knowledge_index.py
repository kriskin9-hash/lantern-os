"""
Build the base Knowledge Center grounding index.

Turns the Knowledge Center's source docs into a compact, retrievable corpus the
LLM (and the deterministic/near router) can ground on — one record per doc
*section*, with a heading path and a trimmed snippet. Output:

    data/knowledge/index.jsonl   # [{id, doc, path, heading, level, text, tokens}]
    data/knowledge/index.meta.json

Run:
    python scripts/build_knowledge_index.py
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "data" / "knowledge"

# The base Knowledge Center corpus (what knowledgecenter.html links + core docs).
KC_DOCS = [
    "README.md", "QUICKSTART.md", "AGENTS.md", "CLAUDE.md", "SECURITY.md",
    "SKILLS.md", "PROVIDERS.md", "CONTRIBUTING.md",
    "docs/SIGMA0-COLLAPSE-CERTIFICATE.md",
    "docs/SIGMA0-QUANTUM-RELATIVITY-ANALYSIS.md",
    "docs/TESSERACT-CONVERGENCE-LOOP.md",
    "docs/CSF-FORMAT-SPECIFICATION.md",
    "docs/LANTERN-SIGMA0-CODER.md",
]

MAX_SECTION_CHARS = 1200


def split_sections(md: str):
    """Split markdown into (level, heading, body) sections by ATX headings."""
    lines = md.splitlines()
    sections, cur_head, cur_level, buf = [], "(intro)", 0, []
    for ln in lines:
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            if buf:
                sections.append((cur_level, cur_head, "\n".join(buf).strip()))
            cur_level, cur_head, buf = len(m.group(1)), m.group(2).strip(), []
        else:
            buf.append(ln)
    if buf:
        sections.append((cur_level, cur_head, "\n".join(buf).strip()))
    return [(lv, h, b) for lv, h, b in sections if b]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for rel in KC_DOCS:
        p = REPO / rel
        if not p.exists():
            continue
        md = p.read_text(encoding="utf-8", errors="replace")
        for lv, heading, body in split_sections(md):
            text = re.sub(r"\n{3,}", "\n\n", body)[:MAX_SECTION_CHARS]
            rid = hashlib.sha1(f"{rel}#{heading}".encode()).hexdigest()[:12]
            records.append({
                "id": rid, "doc": rel, "path": f"{rel}#{heading}",
                "heading": heading, "level": lv, "text": text,
                "tokens": max(1, len(text) // 4),
            })

    idx = OUT_DIR / "index.jsonl"
    with open(idx, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    meta = {
        "built_at": time.time(),
        "docs": [d for d in KC_DOCS if (REPO / d).exists()],
        "sections": len(records),
        "sha256": hashlib.sha256(idx.read_bytes()).hexdigest(),
    }
    (OUT_DIR / "index.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"knowledge index: {len(records)} sections from {len(meta['docs'])} docs -> {idx}")
    print(f"  sha256={meta['sha256'][:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
