"""
Guards against LLM model-ID drift — the class of bug that shipped silently
because `node --check` only validates JS *syntax*, not model *strings*.

Real failures this would have caught (2026-06-17):
  * auto-work called the dead model `grok-2-latest` → "Model not found"
  * stream-chat sent a request to `grok-4.3` but logged the receipt as `grok-2`
    (same function, two different `process.env.XAI_MODEL || "..."` fallbacks)
  * six different Grok model IDs scattered across eight files, no source of truth

RULE: runtime libs read default models from lib/provider-models.js via
modelFor(), never via a bare `|| "<model>"` literal fallback.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIB = REPO / "apps" / "lantern-garage" / "lib"
ROUTES = REPO / "apps" / "lantern-garage" / "routes"
SOURCE_OF_TRUTH = LIB / "provider-models.js"

# Core paths that must source defaults from provider-models.js (NOT swarm-
# orchestrator, which legitimately uses an explicit multi-model chain).
RUNTIME_LIBS = [
    LIB / "stream-chat.js",
    LIB / "self-edit-engine.js",
    ROUTES / "providers.js",
]

# Models known to be dead / deprecated — must never appear in runtime code.
DEAD_MODELS = ["grok-2-latest", "grok-1", "grok-beta"]

# A provider-key env var followed by a bare string fallback, e.g.
#   process.env.XAI_MODEL || "grok-2"
# This is the drift antipattern: each site picks its own default.
FALLBACK_ANTIPATTERN = re.compile(
    r'process\.env\.(?:XAI|OPENAI|ANTHROPIC|GEMINI)_MODEL\s*\|\|\s*["\'][^"\']+["\']'
)


def test_source_of_truth_exists_and_defines_all_providers():
    assert SOURCE_OF_TRUTH.exists(), "lib/provider-models.js (single source of truth) is missing"
    text = SOURCE_OF_TRUTH.read_text(encoding="utf-8")
    for provider in ("anthropic", "openai", "gemini", "xai"):
        assert re.search(rf'{provider}\s*:', text), f"provider-models.js DEFAULTS missing '{provider}'"
    # The dead model must not be the configured default.
    for dead in DEAD_MODELS:
        assert dead not in text, f"provider-models.js still defaults to dead model '{dead}'"


def test_no_dead_models_in_runtime():
    offenders = []
    for js in [SOURCE_OF_TRUTH, *RUNTIME_LIBS]:
        if not js.exists():
            continue
        text = js.read_text(encoding="utf-8")
        for dead in DEAD_MODELS:
            if dead in text:
                offenders.append(f"{js.relative_to(REPO)} contains dead model '{dead}'")
    assert not offenders, "Dead model IDs in runtime code:\n  " + "\n  ".join(offenders)


def test_runtime_libs_use_single_source_not_inline_fallbacks():
    """No `process.env.*_MODEL || "literal"` drift in the core runtime libs."""
    offenders = []
    for js in RUNTIME_LIBS:
        if not js.exists():
            continue
        for i, line in enumerate(js.read_text(encoding="utf-8").splitlines(), 1):
            if FALLBACK_ANTIPATTERN.search(line):
                offenders.append(f"{js.relative_to(REPO)}:{i}: {line.strip()}")
    assert not offenders, (
        "Inline model fallbacks bypass lib/provider-models.js (use modelFor()):\n  "
        + "\n  ".join(offenders)
    )
