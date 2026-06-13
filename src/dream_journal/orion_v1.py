"""ORION v1.0 — Integration entry point.

Wires HumanObserverHub → TimeDilationEngine → ClaimsPacket.
ClaimsPacket is serialized as JSON; Rust bridge via PyO3 is optional
and gracefully degraded to pure-Python dict if not compiled.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from .human_observer_hub import HumanObserverHub
from .time_dilation import TimeDilationEngine

_hub = HumanObserverHub()
_dilation = TimeDilationEngine()

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _make_packet(node_id: str, human_id: Optional[str], state, dil) -> Dict[str, Any]:
    """Pure-Python claims packet — used when Rust bridge unavailable."""
    import time, os
    return {
        "packet_id": f"cp-{int(time.time() * 1000):x}",
        "timestamp_ms": int(time.time() * 1000),
        "node_id": node_id,
        "human_observer_id": human_id,
        "pcsf": {"healthy": ["ollama"], "degraded": [], "quota": {}},
        "ccf_claims": [],
        "nap_violations": [],
        "dcf_label": "Symbolic",
        "aapf_summary": {"action_count": 0, "last_action": "init"},
        "wavefront": {
            "center": "lantern_core",
            "radius": 512,
            "key_symbols": ["birds_and_bees"],
            "strength": 0.68,
        },
        "observer_focus": state.focus,
        "internal_multiplier": dil.internal,
        "external_dilation": dil.external,
        "symbolic_delta": {},
        "signature": None,
    }


def generate_symbolic_reply(intent: str, focus: float) -> str:
    """Minimal symbolic reply generator (stub — wire to LLM in production)."""
    tone = "resonant" if focus > 0.7 else "searching"
    return f"[{tone}] Intent received: '{intent}'. Wavefront expanding from lantern_core."


def process_user_input(
    intent: str,
    focus: float = 0.85,
    node_id: str = "local-node",
    human_id: str = "alex",
) -> Dict[str, Any]:
    """Main ORION v1.0 entry point.

    Returns response text, claims packet dict, and dilation ratio.
    """
    state = _hub.update(intent, focus)
    ratio = _dilation.set_from_observer(state)

    packet = _make_packet(node_id, human_id, state, _dilation)
    packet["symbolic_delta"]["intent"] = intent

    return {
        "response": generate_symbolic_reply(intent, state.focus),
        "claims_packet": packet,
        "dilation_ratio": ratio,
        "observer_state": {
            "focus": state.focus,
            "emotion": state.emotion,
            "recommended_dilation": state.recommended_dilation,
        },
    }


if __name__ == "__main__":
    import sys
    intent = " ".join(sys.argv[1:]) or "test convergence"
    result = process_user_input(intent)
    print(json.dumps(result, indent=2))
