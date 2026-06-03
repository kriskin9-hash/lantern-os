"""
Tesseract Convergence Engine — Lantern OS

4-layer hypercube execution model: slower outside, faster inside.
All factors converge through Surface → Interface → Convergence → Core
and bubble back up with enriched context.

Usage:
    from tesseract_convergence import TesseractEngine, Layer

    engine = TesseractEngine()
    result = engine.converge("Tell me about my dreams.", {
        "persona": "lantern",
        "provider": "anthropic",
    })
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
LOG_PATH = DATA_DIR / "agent-fleet" / "tesseract-convergence.jsonl"


class Layer(IntEnum):
    SURFACE = 0      # Human-facing: RP, web UI, greeting
    INTERFACE = 1  # MCP bridges, agent slots, health checks
    CONVERGENCE = 2  # CSF merge, RAG build, memory consolidation
    CORE = 3         # Fast inference, token streaming, kernels


@dataclass
class TesseractCell:
    layer: Layer
    x: int  # Compute axis
    y: int  # Memory axis
    z: int  # Agency axis
    w: int  # Lore axis
    latency_ms: float = 0.0
    status: str = "ok"

    def key(self) -> str:
        return f"{self.layer.value}-{self.x}-{self.y}-{self.z}-{self.w}"


@dataclass
class ConvergenceContext:
    persona: str = "lantern"
    provider: Optional[str] = None
    recent_dreams: List[Dict[str, Any]] = field(default_factory=list)
    mcp_tools: List[str] = field(default_factory=list)
    csf_segments: List[str] = field(default_factory=list)
    lore_hints: List[str] = field(default_factory=list)
    timing: Dict[str, float] = field(default_factory=dict)


class TesseractEngine:
    """
    Routes work through the 4 tesseract layers.
    Outer layers are slower and more deliberate.
    Inner layers are fast and fault-tolerant.
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self.data_dir = Path(data_dir or DATA_DIR)
        self.log_path = self.data_dir / "agent-fleet" / "tesseract-convergence.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._cells: Dict[str, TesseractCell] = {}
        self._init_cells()

    def _init_cells(self) -> None:
        # Initialize the 16 primary cells (4 layers × 4 primary intersections)
        for layer in Layer:
            for axis in range(4):
                cell = TesseractCell(layer=layer, x=axis, y=axis, z=axis, w=axis)
                self._cells[cell.key()] = cell

    # ------------------------------------------------------------------ #
    # Layer timing targets (slower outside, faster inside)
    # ------------------------------------------------------------------ #
    @staticmethod
    def target_latency_ms(layer: Layer) -> float:
        return {
            Layer.SURFACE: 500.0,
            Layer.INTERFACE: 150.0,
            Layer.CONVERGENCE: 50.0,
            Layer.CORE: 10.0,
        }.get(layer, 100.0)

    # ------------------------------------------------------------------ #
    # Convergence pipeline
    # ------------------------------------------------------------------ #
    def converge(
        self,
        message: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run message through the full tesseract convergence pipeline.
        Descends Surface → Interface → Convergence → Core,
        then bubbles back up with enriched context.
        """
        params = params or {}
        ctx = ConvergenceContext(
            persona=params.get("persona", "lantern"),
            provider=params.get("provider"),
        )
        start_total = time.time()
        trace: List[Dict[str, Any]] = []

        # ── Surface Layer ───────────────────────────────────────────────
        trace.append(self._enter(Layer.SURFACE, "persona_select"))
        ctx = self._surface(ctx, message)
        trace.append(self._exit(Layer.SURFACE, "persona_select", start_total))

        trace.append(self._enter(Layer.SURFACE, "recent_dreams_load"))
        ctx = self._surface_load_dreams(ctx)
        trace.append(self._exit(Layer.SURFACE, "recent_dreams_load", start_total))

        # ── Interface Layer ─────────────────────────────────────────────
        trace.append(self._enter(Layer.INTERFACE, "mcp_bridge"))
        ctx = self._interface_mcp(ctx)
        trace.append(self._exit(Layer.INTERFACE, "mcp_bridge", start_total))

        trace.append(self._enter(Layer.INTERFACE, "slot_claim"))
        ctx = self._interface_slot_claim(ctx)
        trace.append(self._exit(Layer.INTERFACE, "slot_claim", start_total))

        # ── Convergence Layer ───────────────────────────────────────────
        trace.append(self._enter(Layer.CONVERGENCE, "csf_context"))
        ctx = self._convergence_csf(ctx)
        trace.append(self._exit(Layer.CONVERGENCE, "csf_context", start_total))

        trace.append(self._enter(Layer.CONVERGENCE, "rag_pull"))
        ctx = self._convergence_rag(ctx)
        trace.append(self._exit(Layer.CONVERGENCE, "rag_pull", start_total))

        # ── Core Layer ──────────────────────────────────────────────────
        trace.append(self._enter(Layer.CORE, "inference_stream"))
        result = self._core_inference(ctx, message)
        trace.append(self._exit(Layer.CORE, "inference_stream", start_total))

        # ── Bubble back up: Convergence ─────────────────────────────────
        trace.append(self._enter(Layer.CONVERGENCE, "log_dollhouse"))
        self._convergence_log(ctx, message, result)
        trace.append(self._exit(Layer.CONVERGENCE, "log_dollhouse", start_total))

        # ── Bubble back up: Interface ───────────────────────────────────
        trace.append(self._enter(Layer.INTERFACE, "slot_release"))
        self._interface_slot_release(ctx)
        trace.append(self._exit(Layer.INTERFACE, "slot_release", start_total))

        # ── Bubble back up: Surface ─────────────────────────────────────
        trace.append(self._enter(Layer.SURFACE, "render_reply"))
        surface_result = self._surface_render(ctx, result)
        trace.append(self._exit(Layer.SURFACE, "render_reply", start_total))

        total_ms = round((time.time() - start_total) * 1000, 2)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_preview": message[:120],
            "persona": ctx.persona,
            "provider": ctx.provider,
            "total_ms": total_ms,
            "trace": trace,
            "result_preview": str(result.get("text", ""))[:120],
        }
        self._log(record)
        return surface_result

    # ------------------------------------------------------------------ #
    # Surface layer implementations (slow, deliberate)
    # ------------------------------------------------------------------ #
    def _surface(self, ctx: ConvergenceContext, message: str) -> ConvergenceContext:
        # Persona selection based on message keywords
        lower = message.lower()
        if any(k in lower for k in ["static", "glitch", "tv", "crt", "caterpillar", "chaotic", "unhinged"]):
            ctx.persona = "blinkbug"
        elif any(k in lower for k in ["truth", "pattern", "anchor", "integrate", "return door"]):
            ctx.persona = "keystone"
        elif any(k in lower for k in ["light", "flame", "safe", "home", "steady"]):
            ctx.persona = "lantern"
        elif any(k in lower for k in ["flow", "water", "heal", "gentle"]):
            ctx.persona = "waterfall"
        elif any(k in lower for k in ["space", "ship", "navigate", "map"]):
            ctx.persona = "xenon"
        elif any(k in lower for k in ["wish", "protect", "founder", "waynesville"]):
            ctx.persona = "founder"
        # Ingest operator lore into context for persona alignment
        try:
            from skills.operator_lore import get_lore_engine
            lore = get_lore_engine()
            ctx.lore_hints.append(lore.build_convergence_context(message, limit=3))
        except Exception:
            pass
        return ctx

    def _surface_load_dreams(self, ctx: ConvergenceContext) -> ConvergenceContext:
        dream_dir = DATA_DIR / "dream_journal"
        dreams: List[Dict[str, Any]] = []
        if dream_dir.exists():
            for file in sorted(dream_dir.glob("*.jsonl")):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                try:
                                    dreams.append(json.loads(line))
                                except Exception:
                                    pass
                except Exception:
                    pass
        dreams.sort(key=lambda d: str(d.get("timestamp", "")), reverse=True)
        ctx.recent_dreams = dreams[:5]
        return ctx

    def _surface_render(self, ctx: ConvergenceContext, core_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "text": core_result.get("text", ""),
            "persona": ctx.persona,
            "provider": core_result.get("provider", "unknown"),
            "source": core_result.get("source", "unknown"),
            "timing": ctx.timing,
            "suggestions": ["Log this as a dream", "Mirror a dream", "Tell me about the doors"],
        }

    # ------------------------------------------------------------------ #
    # Interface layer implementations (MCP, slots, bridges)
    # ------------------------------------------------------------------ #
    def _interface_mcp(self, ctx: ConvergenceContext) -> ConvergenceContext:
        # MCP bridge: discover available tools without blocking
        ctx.mcp_tools = ["get_agent_status", "dispatch_task", "ingest_rag"]
        return ctx

    def _interface_slot_claim(self, ctx: ConvergenceContext) -> ConvergenceContext:
        # Claim a dream journal slot for this provider
        slots_path = REPO_ROOT / "config" / "agent-slots.json"
        if slots_path.exists():
            try:
                with open(slots_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for slot in data.get("agents", []):
                    if "dream_journal" in slot.get("type", ""):
                        # Mark as conceptually active for this request
                        ctx.provider = ctx.provider or slot.get("type", "").replace("dream_journal_", "")
                        break
            except Exception:
                pass
        return ctx

    def _interface_slot_release(self, ctx: ConvergenceContext) -> None:
        pass  # Async release; nothing to block on

    # ------------------------------------------------------------------ #
    # Convergence layer implementations (CSF, RAG, memory)
    # ------------------------------------------------------------------ #
    def _convergence_csf(self, ctx: ConvergenceContext) -> ConvergenceContext:
        csf_dir = DATA_DIR / "dollhouse" / "csf"
        manifest_path = csf_dir / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                ctx.csf_segments = [s for s in manifest.get("paths", [])][:3]
            except Exception:
                pass
        return ctx

    def _convergence_rag(self, ctx: ConvergenceContext) -> ConvergenceContext:
        rag_path = DATA_DIR / "rag-house" / "flat-rag-house-latest.json"
        if rag_path.exists():
            try:
                with open(rag_path, "r", encoding="utf-8") as f:
                    rag = json.load(f)
                ctx.lore_hints = [
                    f"RAG sources: {len(rag.get('sources', []))}",
                    f"Recent conversations: {len(rag.get('recentConversations', []))}",
                ]
            except Exception:
                pass
        return ctx

    def _convergence_log(self, ctx: ConvergenceContext, message: str, result: Dict[str, Any]) -> None:
        # Best-effort log to dollhouse intake
        intake_dir = DATA_DIR / "rag-intake" / "tesseract-trace"
        intake_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "persona": ctx.persona,
            "message_preview": message[:200],
            "reply_preview": str(result.get("text", ""))[:200],
            "provider": result.get("provider", "unknown"),
        }
        with open(intake_dir / "trace.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    # ------------------------------------------------------------------ #
    # Core layer implementations (fast inference)
    # ------------------------------------------------------------------ #
    def _core_inference(self, ctx: ConvergenceContext, message: str) -> Dict[str, Any]:
        # Delegate to unified connector for fast multi-provider streaming
        try:
            from unified_agent_connector import get_connector
            connector = get_connector()
            out = []
            meta = {}
            context = self._build_core_context(ctx)
            gen = connector.stream(message, persona_id=ctx.persona, provider=ctx.provider, context=context)
            while True:
                try:
                    token = next(gen)
                    if isinstance(token, str):
                        out.append(token)
                    else:
                        meta = dict(token) if hasattr(token, "items") else {}
                except StopIteration as exc:
                    if exc.value and isinstance(exc.value, dict):
                        meta = exc.value
                    break
            return {
                "text": "".join(out),
                "provider": meta.get("provider", "unknown"),
                "source": meta.get("source", "unknown"),
                "persona": ctx.persona,
            }
        except Exception as exc:
            return {
                "text": f"[Core held: {exc}] The dream door stays open. What did you bring back?",
                "provider": "offline",
                "source": "core_fallback",
                "persona": ctx.persona,
            }

    def _build_core_context(self, ctx: ConvergenceContext) -> str:
        parts = []
        if ctx.recent_dreams:
            parts.append("Recent dreams:")
            for d in ctx.recent_dreams[:2]:
                parts.append(f"- {str(d.get('text') or d.get('content', ''))[:160]}")
        if ctx.lore_hints:
            parts.append("\n".join(ctx.lore_hints))
        if ctx.csf_segments:
            parts.append(f"CSF segments available: {len(ctx.csf_segments)}")
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    # Tracing & logging
    # ------------------------------------------------------------------ #
    def _enter(self, layer: Layer, op: str) -> Dict[str, Any]:
        return {"layer": layer.name, "op": op, "phase": "enter", "at_ms": round(time.time() * 1000, 2)}

    def _exit(self, layer: Layer, op: str, start: float) -> Dict[str, Any]:
        elapsed = round((time.time() - start) * 1000, 2)
        target = self.target_latency_ms(layer)
        status = "ok" if elapsed < target * 3 else "slow"
        return {"layer": layer.name, "op": op, "phase": "exit", "elapsed_ms": elapsed, "target_ms": target, "status": status}

    def _log(self, record: Dict[str, Any]) -> None:
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Inspection
    # ------------------------------------------------------------------ #
    def inspect(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cells": len(self._cells),
            "target_latencies": {l.name: self.target_latency_ms(l) for l in Layer},
            "last_log": str(self.log_path) if self.log_path.exists() else "none",
        }


# CLI entrypoint
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", default="Hello tesseract")
    parser.add_argument("--persona", default="lantern")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args()

    engine = TesseractEngine()
    if args.inspect:
        print(json.dumps(engine.inspect(), indent=2))
    else:
        result = engine.converge(args.message, {"persona": args.persona, "provider": args.provider})
        print(json.dumps(result, indent=2))
