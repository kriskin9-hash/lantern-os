"""
Slim Dream Journal Flask API
Minimal endpoint for logging, retrieving, and analyzing dreams
"""

from flask import Flask, jsonify, request
from datetime import datetime
import json
import os
from pathlib import Path

try:
    from skills.dream_journal import DreamAgent
    HAS_DREAM_AGENT = True
except ImportError:
    HAS_DREAM_AGENT = False

app = Flask(__name__)

# Dream storage directory
DREAMS_DIR = Path("/app/data/dreams")
DREAMS_DIR.mkdir(parents=True, exist_ok=True)

if HAS_DREAM_AGENT:
    try:
        dream_agent = DreamAgent(data_dir=str(DREAMS_DIR))
    except Exception:
        dream_agent = None
else:
    dream_agent = None

def get_dream_file(year_month):
    """Get path to monthly dream journal file"""
    return DREAMS_DIR / f"dreams_{year_month}.jsonl"

@app.route("/", methods=["GET"])
def index():
    """Root endpoint - service info"""
    return jsonify({
        "service": "dream-journal",
        "status": "ready",
        "endpoints": [
            "/health",
            "/dreams/log",
            "/dreams/recent",
            "/dreams/mirror-prompt",
            "/dreams/stats",
            "/dreams/agent/mirror"
        ]
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "dream-journal"}), 200

@app.route("/dreams/log", methods=["POST"])
def log_dream():
    """
    Log a new dream
    
    Request body:
    {
        "content": "dream narrative",
        "lucidity": 0.65,
        "emotions": ["awe", "curiosity"],
        "tags": ["door", "river"],
        "linked_goals": ["lantern-revenue"]
    }
    """
    data = request.get_json()
    
    if not data or "content" not in data:
        return jsonify({"error": "Missing 'content' field"}), 400
    
    # Create dream record
    now = datetime.utcnow()
    dream_id = f"dream_{now.strftime('%Y%m%d_%H%M%S')}"
    
    dream = {
        "id": dream_id,
        "timestamp": now.isoformat(),
        "content": data["content"],
        "lucidity": float(data.get("lucidity", 0.5)),
        "emotions": data.get("emotions", []),
        "tags": data.get("tags", []),
        "linked_goals": data.get("linked_goals", []),
        "sfi_impact": data.get("sfi_impact", {"meaning": 0, "purpose": 0, "character": 0})
    }
    
    # Append to monthly file
    month = now.strftime("%Y-%m")
    dream_file = get_dream_file(month)
    
    with open(dream_file, "a") as f:
        f.write(json.dumps(dream) + "\n")
    
    return jsonify({"id": dream_id, "message": "Dream logged successfully"}), 201

@app.route("/dreams/recent", methods=["GET"])
def get_recent_dreams():
    """Get recent dreams (default: 10)"""
    limit = int(request.args.get("limit", 10))
    
    dreams = []
    
    # Read all JSONL files in reverse chronological order
    for dream_file in sorted(DREAMS_DIR.glob("dreams_*.jsonl"), reverse=True):
        with open(dream_file, "r") as f:
            for line in f:
                if line.strip():
                    dreams.append(json.loads(line))
    
    return jsonify({"dreams": dreams[-limit:]}), 200

@app.route("/dreams/<dream_id>", methods=["GET"])
def get_dream(dream_id):
    """Retrieve a specific dream"""
    for dream_file in DREAMS_DIR.glob("dreams_*.jsonl"):
        with open(dream_file, "r") as f:
            for line in f:
                if line.strip():
                    dream = json.loads(line)
                    if dream["id"] == dream_id:
                        return jsonify(dream), 200
    
    return jsonify({"error": "Dream not found"}), 404

@app.route("/dreams/mirror-prompt", methods=["POST"])
def mirror_prompt():
    """
    Generate interpretation prompt for a dream
    
    Request body: {"dream_id": "dream_20260601_123456"}
    or use most recent if no ID provided
    """
    data = request.get_json() or {}
    dream_id = data.get("dream_id")
    
    # Find dream
    dream = None
    for dream_file in DREAMS_DIR.glob("dreams_*.jsonl"):
        with open(dream_file, "r") as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    if dream_id is None or d["id"] == dream_id:
                        dream = d
    
    if not dream:
        return jsonify({"error": "Dream not found"}), 404
    
    # Generate prompt
    prompt = f"""Interpret this dream with focus on personal growth and waking-life connection:

**Dream Content:** {dream['content']}

**Lucidity Score:** {dream['lucidity']}/1.0
**Emotions:** {', '.join(dream['emotions']) if dream['emotions'] else 'None recorded'}
**Tags/Symbols:** {', '.join(dream['tags']) if dream['tags'] else 'None recorded'}
**Linked Goals:** {', '.join(dream['linked_goals']) if dream['linked_goals'] else 'None recorded'}

Please provide:
1. Symbolic interpretation of key elements
2. Connection to waking-life goals or challenges
3. One actionable insight for personal development
4. Lucidity-building practice suggestions (if applicable)

Use concise, grounded analysis."""
    
    return jsonify({
        "dream_id": dream["id"],
        "prompt": prompt,
        "model_suggestion": "Use with Claude, Grok, or local LLM"
    }), 200

@app.route("/dreams/agent/mirror", methods=["POST"])
def agent_mirror():
    """
    Ask the local Dreamer agent to mirror dream text.

    This is intentionally an agent-runtime endpoint. If Ollama or an approved
    SDK-backed agent is unavailable, the response is held instead of pretending
    that a template is the Dreamer.
    """
    if not HAS_DREAM_AGENT or dream_agent is None:
        return jsonify({"error": "Dream agent not available", "held": True}), 503
    
    data = request.get_json() or {}
    text = data.get("content") or data.get("text")

    if not text and data.get("dream_id"):
        for dream_file in DREAMS_DIR.glob("dreams_*.jsonl"):
            with open(dream_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        dream = json.loads(line)
                        if dream["id"] == data["dream_id"]:
                            text = dream.get("content")
                            break
            if text:
                break

    if not text:
        return jsonify({"error": "Missing content, text, or valid dream_id"}), 400

    try:
        result = dream_agent.mirror(str(text))
        status = 503 if result.held else 200
        return jsonify({
            "reply": result.reply,
            "source": result.source,
            "agent_runtime": result.agent_runtime,
            "held": result.held,
            "fallacies": result.fallacies,
            "recent_count": result.recent_count,
        }), status
    except Exception as e:
        return jsonify({"error": str(e), "held": True}), 503

@app.route("/dreams/stats", methods=["GET"])
def dream_stats():
    """Get dream journal statistics"""
    dreams = []
    
    for dream_file in DREAMS_DIR.glob("dreams_*.jsonl"):
        with open(dream_file, "r") as f:
            for line in f:
                if line.strip():
                    dreams.append(json.loads(line))
    
    if not dreams:
        return jsonify({"count": 0, "avg_lucidity": 0}), 200
    
    avg_lucidity = sum(d["lucidity"] for d in dreams) / len(dreams)
    
    return jsonify({
        "total_dreams": len(dreams),
        "avg_lucidity": round(avg_lucidity, 2),
        "earliest": dreams[0]["timestamp"] if dreams else None,
        "latest": dreams[-1]["timestamp"] if dreams else None
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
