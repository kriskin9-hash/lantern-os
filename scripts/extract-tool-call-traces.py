#!/usr/bin/env python3
"""
Extract AGENTIC tool-call traces from Claude Code session transcripts for Sigma0
Ouro training -- the "like Claude Code does" signal that the text-only
extract-session-pairs.py throws away.

Where extract-session-pairs.py keeps only assistant *text* turns, this captures the
decision the agent actually makes: given the running context (user request + prior
assistant turns + prior tool results), emit the next assistant action -- which is
usually a tool call with its arguments. tool_use / tool_result blocks are
serialized as compact text tags so a plain causal LM (Ouro) can learn them.

One training example per assistant turn that contains substantive action (a
tool_use, or >40 chars of text). instruction = bounded recent context; output =
that assistant turn (text + serialized tool calls). Alpaca {instruction,input,output}.

Usage:
    python scripts/extract-tool-call-traces.py \
        --out models/lantern-sigma0-coder/tool-call-traces.jsonl
    python scripts/extract-tool-call-traces.py --dry-run
"""
import argparse
import glob
import json
import os
from pathlib import Path

DEFAULT_SESSIONS_GLOB = str(Path.home() / ".claude" / "projects" / "*")
DEFAULT_OUT = "models/lantern-sigma0-coder/tool-call-traces.jsonl"

SYSTEM = ("You are the Sigma0 Ouro coding agent for Lantern OS. Given the conversation "
          "so far, decide the next action: respond, or call a tool with arguments. "
          "Tool calls are written as [tool: NAME] followed by a compact JSON of inputs.")

# Bounds (chars) -- the trainer also truncates to 1024 tokens, these keep examples lean.
MAX_CTX_CHARS = 3000
MAX_OUT_CHARS = 2000
MAX_TOOL_INPUT_CHARS = 600
MAX_TOOL_RESULT_CHARS = 500


def _clip(s, n):
    s = s or ""
    return s if len(s) <= n else s[:n] + " ...[clipped]"


def serialize_assistant(content):
    """Assistant turn -> text incl. tool calls as [tool: NAME] {json}."""
    if isinstance(content, str):
        return content.strip()
    parts = []
    for b in content if isinstance(content, list) else []:
        if not isinstance(b, dict):
            continue
        t = b.get("type")
        if t == "text":
            txt = b.get("text", "").strip()
            if txt:
                parts.append(txt)
        elif t == "tool_use":
            name = b.get("name", "?")
            inp = json.dumps(b.get("input", {}), ensure_ascii=False)
            parts.append(f"[tool: {name}] {_clip(inp, MAX_TOOL_INPUT_CHARS)}")
    return "\n".join(parts).strip()


def serialize_user(content):
    """User turn -> human text, or serialized tool_result(s)."""
    if isinstance(content, str):
        return content.strip()
    texts, results = [], []
    for b in content if isinstance(content, list) else []:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text":
            txt = b.get("text", "").strip()
            if txt:
                texts.append(txt)
        elif b.get("type") == "tool_result":
            c = b.get("content", "")
            if isinstance(c, list):
                c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
            results.append(f"[tool_result] {_clip(str(c).strip(), MAX_TOOL_RESULT_CHARS)}")
    if texts:
        return "\n".join(texts).strip()
    return "\n".join(results).strip()


def turn_has_action(content):
    """Keep turns that are real actions: a tool_use, or substantive text."""
    if isinstance(content, str):
        return len(content.strip()) > 40
    if not isinstance(content, list):
        return False
    for b in content:
        if isinstance(b, dict):
            if b.get("type") == "tool_use":
                return True
            if b.get("type") == "text" and len(b.get("text", "").strip()) > 40:
                return True
    return False


def build_examples(records, ctx_turns):
    """Walk a session in file (chronological) order, build context-windowed examples."""
    # Linear transcript of (role, serialized_text). Skip empty.
    transcript = []
    for r in records:
        typ = r.get("type")
        content = r.get("message", {}).get("content", "")
        if typ == "assistant":
            s = serialize_assistant(content)
            transcript.append(("assistant", s, content))
        elif typ == "user":
            s = serialize_user(content)
            transcript.append(("user", s, content))

    examples = []
    for i, (role, s, raw) in enumerate(transcript):
        if role != "assistant" or not turn_has_action(raw):
            continue
        # context = previous N turns (excluding the target assistant turn)
        start = max(0, i - ctx_turns)
        ctx_lines = []
        for (r2, s2, _) in transcript[start:i]:
            if not s2:
                continue
            tag = "User" if r2 == "user" else "Assistant"
            ctx_lines.append(f"{tag}: {s2}")
        instruction = _clip("\n".join(ctx_lines).strip(), MAX_CTX_CHARS)
        output = _clip(s, MAX_OUT_CHARS)
        if not instruction or not output:
            continue
        examples.append({"instruction": instruction, "input": "", "output": output})
    return examples


def load_session(path):
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions-glob", default=DEFAULT_SESSIONS_GLOB,
                    help="glob of session DIRS (each containing *.jsonl)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--ctx-turns", type=int, default=6,
                    help="how many prior turns of context per example")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    files = []
    for d in glob.glob(a.sessions_glob):
        files.extend(glob.glob(os.path.join(d, "*.jsonl")))
    print(f"session files: {len(files)}")

    all_ex = []
    tool_examples = 0
    for path in files:
        ex = build_examples(load_session(path), a.ctx_turns)
        for e in ex:
            if "[tool: " in e["output"]:
                tool_examples += 1
        all_ex.extend(ex)

    # dedup on (instruction[:200], output[:200])
    seen, deduped = set(), []
    for e in all_ex:
        k = (e["instruction"][:200], e["output"][:200])
        if k not in seen:
            seen.add(k)
            deduped.append(e)

    print(f"raw examples: {len(all_ex)} | after dedup: {len(deduped)}")
    print(f"examples whose target contains a tool call: {tool_examples}")
    if deduped:
        avg_in = sum(len(e['instruction']) for e in deduped) / len(deduped)
        avg_out = sum(len(e['output']) for e in deduped) / len(deduped)
        print(f"avg instruction chars: {avg_in:.0f} | avg output chars: {avg_out:.0f}")

    if a.dry_run:
        print("\n--- sample example ---")
        if deduped:
            ex = deduped[len(deduped) // 2]
            print("INSTRUCTION:\n", ex["instruction"][:600])
            print("\nOUTPUT:\n", ex["output"][:600])
        return

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for e in deduped:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"\nwrote {len(deduped)} examples -> {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
