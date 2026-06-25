"""
build_capability_dataset.py — Capability training data for the local Ouro model (#1100).

Produces instruction-tuning trajectories for general user tasks:
  - web lookup (web_search + web_fetch tool calls)
  - document creation (create_document tool calls)
  - user workspace operations (workspace_write/read/list)
  - job-application skill orchestration

WHY: The existing Ouro adapter was trained on *coding sessions*, so it drives
coding tasks well but cannot reliably generate tool calls for user-facing
capabilities. This dataset provides `{instruction, input, output}` rows where
`output` is the expected tool call (in <tool_call>...</tool_call> format, matching
the train/serve parity requirement from tool-runner.js renderToolPreamble()).

FORMAT: {"instruction": str, "input": str, "output": str}
  - instruction: the user's request
  - input: (optional) additional context
  - output: the expected model response (may include a <tool_call>)

The outputs are NOT execution-verified (web/doc tools have side effects), but
they are *structurally verified*: every <tool_call> is valid JSON with a name
that matches the live tool registry.

Usage:
    python scripts/build_capability_dataset.py            # writes dataset
    python scripts/build_capability_dataset.py --validate # also validates JSON
    python scripts/build_capability_dataset.py --count    # prints row count

Output: models/lantern-sigma0-coder/capability-dataset.jsonl
"""
import argparse
import json
import os
import sys

OUT_DIR = "models/lantern-sigma0-coder"
OUT_PATH = os.path.join(OUT_DIR, "capability-dataset.jsonl")

LIVE_TOOLS = {
    "web_search", "web_fetch",
    "workspace_write", "workspace_read", "workspace_list",
    "create_document",
    "Read", "LS", "Glob", "Grep", "Bash", "PowerShell", "Write", "Edit",
}


def _tc(name: str, input_: dict) -> str:
    """Render a <tool_call> block (matches renderToolPreamble format)."""
    return f'<tool_call>{{"name": "{name}", "input": {json.dumps(input_, separators=(",", ": "))}}}</tool_call>'


def _row(instruction: str, output: str, input_: str = "") -> dict:
    return {"instruction": instruction.strip(), "input": input_.strip(), "output": output.strip()}


# ── Web search trajectories ───────────────────────────────────────────────────

WEB_SEARCH_ROWS = [
    _row(
        "Search the web for the current Python version.",
        _tc("web_search", {"query": "current Python version 2026", "max_results": 3}),
    ),
    _row(
        "Look up who founded Anthropic.",
        _tc("web_search", {"query": "who founded Anthropic", "max_results": 3}),
    ),
    _row(
        "Find recent news about large language models.",
        _tc("web_search", {"query": "large language model news 2026", "max_results": 5}),
    ),
    _row(
        "What is the current price of Bitcoin?",
        _tc("web_search", {"query": "Bitcoin price today 2026", "max_results": 3}),
    ),
    _row(
        "Search for open-source alternatives to GPT-4.",
        _tc("web_search", {"query": "open source alternatives GPT-4 2026", "max_results": 5}),
    ),
    _row(
        "Look up the latest research on RAG (Retrieval Augmented Generation).",
        _tc("web_search", {"query": "retrieval augmented generation RAG research 2026", "max_results": 5}),
    ),
    _row(
        "Find information about the TypeScript 5 release.",
        _tc("web_search", {"query": "TypeScript 5 release notes features", "max_results": 3}),
    ),
    _row(
        "What happened at Google I/O this year?",
        _tc("web_search", {"query": "Google IO 2026 announcements", "max_results": 5}),
    ),
]

# ── Web fetch trajectories ────────────────────────────────────────────────────

WEB_FETCH_ROWS = [
    _row(
        "Fetch the content of the Python documentation homepage.",
        _tc("web_fetch", {"url": "https://docs.python.org/3/", "max_chars": 2000}),
    ),
    _row(
        "Read the README at https://github.com/anthropics/anthropic-sdk-python.",
        _tc("web_fetch", {"url": "https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/README.md", "max_chars": 3000}),
    ),
    _row(
        "Get the content of this job posting: https://example.com/jobs/senior-engineer",
        _tc("web_fetch", {"url": "https://example.com/jobs/senior-engineer", "max_chars": 4000}),
    ),
    _row(
        "Fetch and summarize the Wikipedia article about the Turing Test.",
        _tc("web_fetch", {"url": "https://en.wikipedia.org/wiki/Turing_test", "max_chars": 3000}),
    ),
]

# ── Workspace trajectories ────────────────────────────────────────────────────

WORKSPACE_ROWS = [
    _row(
        "Save my notes about the job interview to a file.",
        _tc("workspace_write", {"path": "notes/interview-notes.md", "content": "Interview notes:\n- Asked about distributed systems\n- Discussed LLM experience\n"}),
    ),
    _row(
        "List everything in my workspace.",
        _tc("workspace_list", {"path": ""}),
    ),
    _row(
        "Read the file I saved earlier at notes/interview-notes.md.",
        _tc("workspace_read", {"path": "notes/interview-notes.md"}),
    ),
    _row(
        "Save a draft cover letter to workspace.",
        _tc("workspace_write", {"path": "cover-letters/acme-draft.md", "content": "Dear Hiring Manager,\n\nI am applying for the Senior Engineer role...\n"}),
    ),
    _row(
        "Show me what's in the resumes folder in my workspace.",
        _tc("workspace_list", {"path": "resumes"}),
    ),
]

# ── Document generation trajectories ─────────────────────────────────────────

CREATE_DOC_ROWS = [
    _row(
        "Create a resume for John Doe, a software engineer.",
        _tc("create_document", {
            "template": "resume",
            "fields": {
                "name": "John Doe",
                "email": "john@example.com",
                "summary": "Experienced software engineer with 8 years in backend development.",
                "skills": ["Python", "Go", "PostgreSQL", "Docker", "Kubernetes"],
                "experience": [
                    {"title": "Senior Engineer", "company": "Acme Corp", "dates": "2022–2026",
                     "bullets": ["Led API platform migration", "Reduced latency by 40%"]},
                ],
            },
        }),
    ),
    _row(
        "Write a cover letter for a data scientist position at Google.",
        _tc("create_document", {
            "template": "cover_letter",
            "fields": {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "company": "Google",
                "role": "Senior Data Scientist",
                "body_paragraphs": [
                    "My background in ML infrastructure and LLM fine-tuning aligns well with this role.",
                    "I have shipped production ML systems serving millions of users.",
                ],
            },
        }),
    ),
    _row(
        "Generate a resume template.",
        _tc("create_document", {
            "template": "resume",
            "fields": {"name": "Your Name", "email": "you@example.com", "summary": "Brief professional summary."},
        }),
    ),
    _row(
        "Make a cover letter for me applying to the startup Acme as a product manager.",
        _tc("create_document", {
            "template": "cover_letter",
            "fields": {
                "name": "Alex Place",
                "company": "Acme",
                "role": "Product Manager",
                "body_paragraphs": ["I bring a track record of shipping 0→1 products in fast-paced environments."],
            },
        }),
    ),
]

# ── Plain-text responses (capability boundary awareness) ─────────────────────
# The model should say "I'll search for that" or similar before calling a tool,
# and should refuse to fabricate search results.

REFUSAL_ROWS = [
    _row(
        "What is the stock price of Apple right now?",
        "I don't have real-time data. Let me search for that.\n"
        + _tc("web_search", {"query": "Apple AAPL stock price today", "max_results": 3}),
    ),
    _row(
        "What happened in the news today?",
        "I'll search for today's news.\n"
        + _tc("web_search", {"query": "top news today 2026-06-24", "max_results": 5}),
    ),
]


def build_dataset() -> list:
    rows = (
        WEB_SEARCH_ROWS
        + WEB_FETCH_ROWS
        + WORKSPACE_ROWS
        + CREATE_DOC_ROWS
        + REFUSAL_ROWS
    )
    return rows


def validate_rows(rows: list) -> list[str]:
    """Validate that every <tool_call> in each row has a known tool name and valid JSON."""
    import re
    errors = []
    tc_re = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)
    for i, row in enumerate(rows):
        for m in tc_re.finditer(row.get("output", "")):
            try:
                obj = json.loads(m.group(1))
            except json.JSONDecodeError as e:
                errors.append(f"row {i}: invalid JSON in tool_call: {e}")
                continue
            name = obj.get("name", "")
            if name not in LIVE_TOOLS:
                errors.append(f"row {i}: unknown tool '{name}' (output: {m.group(0)[:80]})")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Build capability training dataset (#1100)")
    parser.add_argument("--validate", action="store_true", help="Validate tool call JSON before writing")
    parser.add_argument("--count", action="store_true", help="Print row count and exit")
    args = parser.parse_args()

    rows = build_dataset()

    if args.count:
        print(f"{len(rows)} rows")
        return

    if args.validate:
        errors = validate_rows(rows)
        if errors:
            print(f"VALIDATION FAILED ({len(errors)} error(s)):", file=sys.stderr)
            for e in errors:
                print(f"  {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Validated {len(rows)} rows — all tool calls OK")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
