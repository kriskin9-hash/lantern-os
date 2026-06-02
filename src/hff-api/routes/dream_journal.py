"""
Dream Journal API Routes for Lantern OS

Exposes Dream Journal v2 endpoints via Flask blueprint.
Endpoints:
  POST /api/dreams/         — Log a dream
  GET  /api/dreams/recent   — Get recent dreams
  GET  /api/dreams/mirror/<id> — Generate mirror prompt
  POST /api/dreams/character/<name> — Talk to a character
"""

import sys
import os
from pathlib import Path
from flask import Blueprint, request, jsonify

# Add skills to path
_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "skills" / "dream_journal"))

try:
    from cognitive_layer import get_cognitive_journal
    COGNITIVE_AVAILABLE = True
except ImportError as e:
    COGNITIVE_AVAILABLE = False
    print(f"[WARN] Cognitive layer not available: {e}")
    get_cognitive_journal = None

dream_bp = Blueprint('dream_journal', __name__, url_prefix='/api/dreams')


def _get_journal():
    """Lazy-init cognitive journal."""
    if get_cognitive_journal:
        return get_cognitive_journal()
    return None


@dream_bp.route('/', methods=['POST'])
def log_dream():
    """Log a dream and run fallacy detection."""
    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify({"error": "content_required"}), 400

    journal = _get_journal()
    fallacies = journal.analyze(content) if journal else []

    return jsonify({
        "status": "logged",
        "content_preview": content[:120],
        "fallacies_detected": len(fallacies),
        "fallacies": fallacies,
    }), 201


@dream_bp.route('/recent', methods=['GET'])
def get_recent():
    """Get recent dreams (placeholder — wired to cognitive layer)."""
    journal = _get_journal()
    if not journal:
        return jsonify({"entries": [], "note": "cognitive_layer_unavailable"})

    # TODO: wire to actual dream_journal.py get_recent() when available
    return jsonify({
        "entries": [],
        "characters": journal.character_status(),
    })


@dream_bp.route('/mirror/<int:dream_id>', methods=['GET'])
def get_mirror(dream_id):
    """Generate a mirror prompt for a dream entry."""
    journal = _get_journal()
    if not journal:
        return jsonify({"error": "cognitive_layer_unavailable"}), 503

    # Placeholder: return character status as mirror context
    return jsonify({
        "dream_id": dream_id,
        "prompt": "Reflect on the symbols and emotions in this dream. What patterns recur?",
        "characters": journal.character_status(),
    })


@dream_bp.route('/character/<name>', methods=['POST'])
def talk_to_character(name):
    """Talk to a persistent dream character."""
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    user_id = data.get('user_id', 'api_user')

    if not message:
        return jsonify({"error": "message_required"}), 400

    journal = _get_journal()
    if not journal:
        return jsonify({"error": "cognitive_layer_unavailable"}), 503

    response = journal.talk(name, message, user_id=user_id)
    return jsonify({
        "character": name,
        "message": message,
        "response": response,
    })


@dream_bp.route('/health', methods=['GET'])
def health():
    """Dream Journal API health check."""
    return jsonify({
        "status": "ok",
        "cognitive_layer": COGNITIVE_AVAILABLE,
    })
