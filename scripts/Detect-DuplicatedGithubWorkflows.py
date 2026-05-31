#!/usr/bin/env python3
"""
Detect duplicated GitHub Actions workflow logic across one or more repos.

Usage:
  python scripts/Detect-DuplicatedGithubWorkflows.py .
  python scripts/Detect-DuplicatedGithubWorkflows.py ../repo-a ../repo-b ../repo-c

Outputs:
  docs/manifests/workflow-duplication-audit.json
  docs/reports/WORKFLOW-DUPLICATION-AUDIT.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORKFLOW_DIR = Path(".github/workflows")

GOVERNANCE_KEYWORDS = [
    "convergence",
    "fleet",
    "manifest",
    "provenance",
    "telemetry",
    "slsa",
    "codeowners",
    "validation",
    "validate",
]

STEP_NAME_RE = re.compile(r"^\s*-\s+name:\s*(.+?)\s*$", re.IGNORECASE)
USES_RE = re.compile(r"^\s*uses:\s*(.+?)\s*$", re.IGNORECASE)
RUN_RE = re.compile(r"^\s*run:\s*(\|.*|>.*|.+?)\s*$", re.IGNORECASE)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"#.*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def classify_line(line: str) -> str | None:
    lower = line.lower()
    if any(word in lower for word in GOVERNANCE_KEYWORDS):
        return "governance"
    if "npm " in lower or "pytest" in lower or "dotnet " in lower or "go test" in lower:
        return "repo_specific_test_or_build"
    if "docker" in lower or "render" in lower or "deploy" in lower:
        return "deployment"
    return None


def extract_signals(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    normalized = normalize_text(raw)

    step_names: list[str] = []
    actions_used: list[str] = []
    run_lines: list[str] = []
    classifications: defaultdict[str, int] = defaultdict(int)

    for line in raw.splitlines():
        step_match = STEP_NAME_RE.match(line)
        if step_match:
            name = step_match.group(1).strip().strip('"').strip("'")
            step_names.append(name)
            classification = classify_line(name)
            if classification:
                classifications[classification] += 1

        uses_match = USES_RE.match(line)
        if uses_match:
            actions_used.append(uses_match.group(1).strip())

        run_match = RUN_RE.match(line)
        if run_match:
            run_line = run_match.group(1).strip()
            run_lines.append(run_line)
            classification = classify_line(run_line)
            if classification:
                classifications[classification] += 1

    governance_score = classifications["governance"]

    return {
        "path": str(path),
        "file_hash": sha256(normalized),
        "line_count": len(raw.splitlines()),
        "step_names": step_names,
        "actions_used": sorted(set(actions_used)),
        "run_line_count": len(run_lines),
        "classifications": dict(classifications),
        "governance_score": governance_score,
        "candidate_for_reuse": governance_score > 0,
    }


def find_workflows(repo: Path) -> list[Path]:
    workflow_dir = repo / WORKFLOW_DIR
    if not workflow_dir.exists():
        return []
    return sorted(
        [
            p
            for p in workflow_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".yml", ".yaml"}
        ]
    )


def audit(repos: list[Path]) -> dict[str, Any]:
    workflows: list[dict[str, Any]] = []

    for repo in repos:
        repo = repo.resolve()
        for workflow in find_workflows(repo):
            signal = extract_signals(workflow)
            signal["repo"] = repo.name
            signal["repo_path"] = str(repo)
            workflows.append(signal)

    by_hash: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for workflow in workflows:
        by_hash[workflow["file_hash"]].append(workflow)

    exact_duplicates = [
        {
            "hash": h,
            "count": len(items),
            "files": [{"repo": i["repo"], "path": i["path"]} for i in items],
        }
        for h, items in by_hash.items()
        if len(items) > 1
    ]

    governance_candidates = [
        {
            "repo": w["repo"],
            "path": w["path"],
            "governance_score": w["governance_score"],
            "step_names": w["step_names"],
            "actions_used": w["actions_used"],
        }
        for w in workflows
        if w["candidate_for_reuse"]
    ]

    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_count": len(repos),
        "workflow_count": len(workflows),
        "exact_duplicate_groups": exact_duplicates,
        "governance_reuse_candidates": governance_candidates,
        "workflows": workflows,
    }


def write_outputs(result: dict[str, Any], root: Path) -> None:
    manifest_dir = root / "docs" / "manifests"
    report_dir = root / "docs" / "reports"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = manifest_dir / "workflow-duplication-audit.json"
    md_path = report_dir / "WORKFLOW-DUPLICATION-AUDIT.md"

    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "# Workflow Duplication Audit",
        "",
        f"Generated: `{result['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Repositories scanned: `{result['repo_count']}`",
        f"- Workflows scanned: `{result['workflow_count']}`",
        f"- Exact duplicate groups: `{len(result['exact_duplicate_groups'])}`",
        f"- Governance reuse candidates: `{len(result['governance_reuse_candidates'])}`",
        "",
        "## Exact Duplicate Groups",
        "",
    ]

    if not result["exact_duplicate_groups"]:
        lines.append("No exact duplicate workflow files found.")
    else:
        for group in result["exact_duplicate_groups"]:
            lines.append(f"### Duplicate hash `{group['hash'][:12]}`")
            for file in group["files"]:
                lines.append(f"- `{file['repo']}`: `{file['path']}`")
            lines.append("")

    lines.extend(["", "## Governance Reuse Candidates", ""])

    if not result["governance_reuse_candidates"]:
        lines.append("No governance reuse candidates found.")
    else:
        for item in sorted(
            result["governance_reuse_candidates"],
            key=lambda x: x["governance_score"],
            reverse=True,
        ):
            lines.append(
                f"### `{item['repo']}` — `{item['path']}`"
            )
            lines.append(f"- Governance score: `{item['governance_score']}`")
            if item["step_names"]:
                lines.append("- Steps:")
                for step in item["step_names"]:
                    lines.append(f"  - `{step}`")
            if item["actions_used"]:
                lines.append("- Actions:")
                for action in item["actions_used"]:
                    lines.append(f"  - `{action}`")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "repos",
        nargs="+",
        help="Repo directories to scan",
    )
    args = parser.parse_args()

    repos = [Path(p) for p in args.repos]
    missing = [str(p) for p in repos if not p.exists()]
    if missing:
        raise SystemExit(f"Missing repo paths: {missing}")

    result = audit(repos)
    write_outputs(result, Path.cwd())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
