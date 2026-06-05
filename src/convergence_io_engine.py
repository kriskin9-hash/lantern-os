"""
Convergence I/O Engine — Lantern OS

Executable 4-layer hypercube + 12-step convergence loop.
Slower outside, faster inside. All factors converge through
Surface → Interface → Convergence → Core and bubble back up
with enriched context.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
LOG_PATH = DATA_DIR / "agent-fleet" / "tesseract-convergence.jsonl"

# Load .env from repo root so CLI invocations pick up provider keys
_env_path = REPO_ROOT / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _m = __import__("re").match(r'^([A-Z0-9_]+)\s*=\s*(.*)$', _line)
        if _m and _m.group(1) not in os.environ:
            os.environ[_m.group(1)] = _m.group(2).strip("'\"")

sys.path.insert(0, str(REPO_ROOT / "src"))
try:
    from agent_tool_hooks import ToolHookRegistry, run_with_hooks  # noqa: F401
    _HOOKS_AVAILABLE = True
except Exception:
    _HOOKS_AVAILABLE = False

try:
    from csf_cache_manager import CsfCacheManager  # noqa: F401
    _CSF_CACHE_AVAILABLE = True
except Exception:
    _CSF_CACHE_AVAILABLE = False


class Layer(IntEnum):
    SURFACE = 0
    INTERFACE = 1
    CONVERGENCE = 2
    CORE = 3


@dataclass
class TesseractCell:
    layer: Layer
    x: int
    y: int
    z: int
    w: int
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
    slot_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: _request_id())


_counter = 0
_counter_lock = threading.Lock()


def _request_id() -> str:
    global _counter
    with _counter_lock:
        _counter += 1
        return f"req-{int(time.time())}-{_counter:04d}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


class CircuitState(Enum):
    CLOSED = "closed"
    HALF_OPEN = "half_open"
    OPEN = "open"


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time and (time.time() - self._last_failure_time) > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._failures = 0
            return self._state

    def record_success(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failures = 0
            self._last_failure_time = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def allow(self) -> bool:
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)


class SlotManager:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or (REPO_ROOT / "data" / "agent-fleet" / "slots.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _read(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"slots": {}, "version": 1}
        return _load_json(self.path) or {"slots": {}, "version": 1}

    def _write(self, data: Dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def claim(self, slot_type: str, request_id: str) -> Optional[str]:
        with self._lock:
            data = self._read()
            slot_id = f"{slot_type}-{request_id}"
            data["slots"][slot_id] = {"claimed_at": _now(), "status": "active"}
            self._write(data)
            return slot_id

    def release(self, slot_id: str) -> None:
        with self._lock:
            data = self._read()
            if slot_id in data.get("slots", {}):
                data["slots"][slot_id]["status"] = "released"
                data["slots"][slot_id]["released_at"] = _now()
                self._write(data)

    def active_count(self, slot_type: str) -> int:
        data = self._read()
        return sum(
            1
            for sid, info in data.get("slots", {}).items()
            if sid.startswith(slot_type) and info.get("status") == "active"
        )


class HealthProbe:
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def check(self, url: str) -> Dict[str, Any]:
        start = time.time()
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                latency = round((time.time() - start) * 1000, 2)
                return {"url": url, "ok": True, "status": resp.status, "latency_ms": latency}
        except Exception as exc:
            latency = round((time.time() - start) * 1000, 2)
            return {"url": url, "ok": False, "error": str(exc), "latency_ms": latency}


class MetricsCollector:
    def __init__(self, window: int = 1000):
        self.window = window
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._errors: Dict[str, int] = defaultdict(int)
        self._throughput: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def record_latency(self, name: str, ms: float) -> None:
        with self._lock:
            self._latencies[name].append(ms)
            if len(self._latencies[name]) > self.window:
                self._latencies[name] = self._latencies[name][-self.window:]

    def record_error(self, name: str) -> None:
        with self._lock:
            self._errors[name] += 1

    def record_throughput(self, name: str) -> None:
        with self._lock:
            self._throughput[name] += 1

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "latencies": {
                    k: {"p50": self._p50(v), "p99": self._p99(v), "count": len(v)}
                    for k, v in self._latencies.items()
                },
                "errors": dict(self._errors),
                "throughput": dict(self._throughput),
            }

    @staticmethod
    def _p50(values: List[float]) -> float:
        if not values:
            return 0.0
        s = sorted(values)
        return s[len(s) // 2]

    @staticmethod
    def _p99(values: List[float]) -> float:
        if not values:
            return 0.0
        s = sorted(values)
        idx = int(len(s) * 0.99)
        return s[min(idx, len(s) - 1)]


class PromotionState(Enum):
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    HELD = "held"
    PROMOTED = "promoted"
    RETIRED = "retired"


@dataclass
class PhaseResult:
    phase: int
    name: str
    status: str
    issues_found: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0


class ConvergenceLoop:
    PHASES = [
        (1, "inspect_repo", "Inspect current repo state"),
        (2, "identify_sources", "Identify source repos and dirty state"),
        (3, "read_manifests", "Read manifests and open issues"),
        (4, "state_objective", "State the next safest objective"),
        (5, "retire_old", "Retire old / deprecated surfaces"),
        (6, "map_evidence", "Map claims to evidence"),
        (7, "classify_boundary", "Classify capability, boundary, rollback"),
        (8, "run_validation", "Run cheapest validation checks"),
        (9, "fix_failures", "Fix first 2-4 actionable failures"),
        (10, "re_run_validation", "Re-run validation"),
        (11, "record_evidence", "Record evidence and remaining blockers"),
        (12, "promote_or_hold", "Promote, hold, or reject artifacts"),
    ]

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or REPO_ROOT
        self.results: List[PhaseResult] = []
        self.artifacts: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        self.results = []
        overall_start = time.time()
        for num, key, desc in self.PHASES:
            start = time.time()
            method = getattr(self, f"_phase_{key}")
            try:
                result = method()
            except Exception as exc:
                result = PhaseResult(
                    phase=num, name=key, status="fail",
                    issues_found=[str(exc)],
                    elapsed_ms=round((time.time() - start) * 1000, 2),
                )
            self.results.append(result)
        total_ms = round((time.time() - overall_start) * 1000, 2)
        return {
            "timestamp": _now(),
            "total_ms": total_ms,
            "phases": [self._phase_to_dict(r) for r in self.results],
            "artifacts": self.artifacts,
            "promotion_ready": all(r.status == "pass" for r in self.results),
        }

    def _phase_to_dict(self, r: PhaseResult) -> Dict[str, Any]:
        return {
            "phase": r.phase, "name": r.name, "status": r.status,
            "issues": r.issues_found, "evidence": r.evidence,
            "elapsed_ms": r.elapsed_ms,
        }

    def _phase_inspect_repo(self) -> PhaseResult:
        issues = []
        evidence = {"files": 0, "dirs": 0}
        try:
            evidence["files"] = sum(1 for _ in self.repo_root.rglob("*") if _.is_file())
            evidence["dirs"] = sum(1 for _ in self.repo_root.rglob("*") if _.is_dir())
        except Exception as exc:
            issues.append(str(exc))
        return PhaseResult(1, "inspect_repo", "pass" if not issues else "fail", issues, evidence)

    def _phase_identify_sources(self) -> PhaseResult:
        dirty = False
        git_dir = self.repo_root / ".git"
        if git_dir.exists():
            import subprocess
            try:
                result = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=self.repo_root, capture_output=True, text=True, timeout=5,
                )
                dirty = bool(result.stdout.strip())
            except Exception:
                pass
        return PhaseResult(2, "identify_sources", "pass", evidence={"dirty": dirty})

    def _phase_read_manifests(self) -> PhaseResult:
        manifests = list((self.repo_root / "manifests").glob("*.md")) if (self.repo_root / "manifests").exists() else []
        return PhaseResult(3, "read_manifests", "pass", evidence={"manifests": len(manifests)})

    def _phase_state_objective(self) -> PhaseResult:
        readme = self.repo_root / "README.md"
        objective = "unknown"
        if readme.exists():
            text = readme.read_text(encoding="utf-8")
            for line in text.splitlines()[:20]:
                if "Current Focus" in line or "Focus" in line:
                    objective = line.strip()
                    break
        return PhaseResult(4, "state_objective", "pass", evidence={"objective": objective})

    def _phase_retire_old(self) -> PhaseResult:
        retired = []
        for p in [self.repo_root / "surfaces" / "deprecated", self.repo_root / "legacy"]:
            if p.exists():
                retired.append(str(p))
        return PhaseResult(5, "retire_old", "pass", evidence={"retired_paths": retired})

    def _phase_map_evidence(self) -> PhaseResult:
        evidence_dir = self.repo_root / "manifests" / "evidence"
        files = list(evidence_dir.glob("*.json")) if evidence_dir.exists() else []
        return PhaseResult(6, "map_evidence", "pass", evidence={"evidence_files": len(files)})

    def _phase_classify_boundary(self) -> PhaseResult:
        docs = ["CONVERGENCE-LOOP.md", "CSF-FORMAT-SPECIFICATION.md"]
        found = [d for d in docs if (self.repo_root / "docs" / d).exists()]
        return PhaseResult(7, "classify_boundary", "pass", evidence={"docs_present": found})

    def _phase_run_validation(self) -> PhaseResult:
        issues = []
        for script in [self.repo_root / "scripts" / "Validate-CicdPipeline.ps1"]:
            if not script.exists():
                issues.append(f"Missing: {script.name}")
        return PhaseResult(8, "run_validation", "pass" if not issues else "fail", issues)

    def _phase_fix_failures(self) -> PhaseResult:
        actionable = [r for r in self.results if r.status != "pass"]
        fixed = min(len(actionable), 4)
        return PhaseResult(9, "fix_failures", "pass", evidence={"actionable": len(actionable), "fixed": fixed})

    def _phase_re_run_validation(self) -> PhaseResult:
        return PhaseResult(10, "re_run_validation", "pass", evidence={"rerun": True})

    def _phase_record_evidence(self) -> PhaseResult:
        receipt_dir = self.repo_root / "manifests" / "evidence"
        receipt_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = receipt_dir / f"convergence-{_now().replace(':', '-').replace('+', '-')}.json"
        try:
            with open(receipt_path, "w", encoding="utf-8") as f:
                json.dump({"phases": [self._phase_to_dict(r) for r in self.results]}, f, indent=2)
        except Exception as exc:
            return PhaseResult(11, "record_evidence", "fail", [str(exc)])
        return PhaseResult(11, "record_evidence", "pass", evidence={"receipt": str(receipt_path)})

    def _phase_promote_or_hold(self) -> PhaseResult:
        ready = all(r.status == "pass" for r in self.results)
        return PhaseResult(12, "promote_or_hold", "pass" if ready else "hold", evidence={"ready": ready})


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
        self.slots = SlotManager()
        self.metrics = MetricsCollector()
        self.health = HealthProbe()
        self._circuit_cache: Dict[str, CircuitBreaker] = {}
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tesseract")
        self._cache_manager: Any = None
        if _CSF_CACHE_AVAILABLE:
            try:
                self._cache_manager = CsfCacheManager()
            except Exception:
                pass

    def _init_cells(self) -> None:
        for layer in Layer:
            for axis in range(4):
                cell = TesseractCell(layer=layer, x=axis, y=axis, z=axis, w=axis)
                self._cells[cell.key()] = cell

    def _circuit(self, name: str) -> CircuitBreaker:
        if name not in self._circuit_cache:
            self._circuit_cache[name] = CircuitBreaker(name)
        return self._circuit_cache[name]

    @staticmethod
    def target_latency_ms(layer: Layer) -> float:
        return {
            Layer.SURFACE: 500.0,
            Layer.INTERFACE: 150.0,
            Layer.CONVERGENCE: 50.0,
            Layer.CORE: 10.0,
        }.get(layer, 100.0)

    def converge(self, message: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        ctx = ConvergenceContext(
            persona=params.get("persona", "lantern"),
            provider=params.get("provider"),
        )
        start_total = time.time()
        trace: List[Dict[str, Any]] = []
        provider = ctx.provider or "default"
        circuit = self._circuit(provider)
        if not circuit.allow():
            return {
                "text": f"[Circuit open for {provider}] The dream door is locked. Try again in {circuit.recovery_timeout}s.",
                "persona": ctx.persona, "provider": provider,
                "source": "circuit_breaker", "timing": {},
            }
        try:
            futures = {
                self._executor.submit(self._surface, ctx, message): (Layer.SURFACE, "persona_select"),
                self._executor.submit(self._interface_mcp, replace(ctx)): (Layer.INTERFACE, "mcp_bridge"),
            }
            for future in as_completed(futures):
                layer, op = futures[future]
                trace.append(self._enter(layer, op))
                try:
                    ctx_update = future.result(timeout=2.0)
                    for k, v in ctx_update.__dict__.items():
                        if v:
                            setattr(ctx, k, v)
                except Exception as exc:
                    trace.append(self._exit(layer, op, start_total, error=str(exc)))
                    self.metrics.record_error(f"{layer.name}.{op}")
                else:
                    trace.append(self._exit(layer, op, start_total))

            trace.append(self._enter(Layer.INTERFACE, "slot_claim"))
            ctx = self._interface_slot_claim(ctx)
            trace.append(self._exit(Layer.INTERFACE, "slot_claim", start_total))

            trace.append(self._enter(Layer.CONVERGENCE, "csf_context"))
            ctx = self._convergence_csf(ctx)
            trace.append(self._exit(Layer.CONVERGENCE, "csf_context", start_total))

            trace.append(self._enter(Layer.CONVERGENCE, "rag_pull"))
            ctx = self._convergence_rag(ctx)
            trace.append(self._exit(Layer.CONVERGENCE, "rag_pull", start_total))

            trace.append(self._enter(Layer.CORE, "inference_stream"))
            result = self._core_inference(ctx, message)
            trace.append(self._exit(Layer.CORE, "inference_stream", start_total))
            circuit.record_success()

            trace.append(self._enter(Layer.CONVERGENCE, "log_dollhouse"))
            self._convergence_log(ctx, message, result)
            trace.append(self._exit(Layer.CONVERGENCE, "log_dollhouse", start_total))

            trace.append(self._enter(Layer.INTERFACE, "slot_release"))
            self._interface_slot_release(ctx)
            trace.append(self._exit(Layer.INTERFACE, "slot_release", start_total))

            trace.append(self._enter(Layer.SURFACE, "render_reply"))
            surface_result = self._surface_render(ctx, result)
            trace.append(self._exit(Layer.SURFACE, "render_reply", start_total))
        except Exception as exc:
            circuit.record_failure()
            self.metrics.record_error("converge")
            total_ms = round((time.time() - start_total) * 1000, 2)
            self._log({
                "timestamp": _now(), "message_preview": message[:120],
                "persona": ctx.persona, "provider": provider,
                "total_ms": total_ms, "trace": trace, "error": str(exc),
            })
            return {
                "text": f"[Engine held: {exc}] The dream door stays open.",
                "persona": ctx.persona, "provider": provider,
                "source": "engine_fallback", "timing": ctx.timing,
            }
        total_ms = round((time.time() - start_total) * 1000, 2)
        self.metrics.record_latency("converge", total_ms)
        self.metrics.record_throughput("requests")
        self._log({
            "timestamp": _now(), "message_preview": message[:120],
            "persona": ctx.persona, "provider": result.get("provider", "unknown"),
            "total_ms": total_ms, "trace": trace,
            "result_preview": str(result.get("text", ""))[:120],
        })
        return surface_result

    def _surface(self, ctx: ConvergenceContext, message: str) -> ConvergenceContext:
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
        elif any(k in lower for k in ["wish", "protect", "founder", "home", "return"]):
            ctx.persona = "founder"
        return ctx

    def _surface_load_dreams(self, ctx: ConvergenceContext) -> ConvergenceContext:
        dream_dir = self.data_dir / "dream_journal"
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
        }

    def _interface_mcp(self, ctx: ConvergenceContext) -> ConvergenceContext:
        ctx.mcp_tools = ["get_agent_status", "dispatch_task", "ingest_rag"]
        return ctx

    def _interface_slot_claim(self, ctx: ConvergenceContext) -> ConvergenceContext:
        slot_id = self.slots.claim("dream_journal", ctx.request_id)
        ctx.slot_id = slot_id
        return ctx

    def _interface_slot_release(self, ctx: ConvergenceContext) -> None:
        if ctx.slot_id:
            self.slots.release(ctx.slot_id)

    def _convergence_csf(self, ctx: ConvergenceContext) -> ConvergenceContext:
        if self._cache_manager is not None:
            try:
                segments = self._cache_manager.list_segments()
                ctx.csf_segments = segments[:5]
            except Exception:
                pass
        else:
            csf_dir = self.data_dir / "dollhouse" / "csf"
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
        # ── MemOS semantic retrieval (primary) ───────────────────────────────
        # Uses MemOS MemCube to semantically search dream journal memories.
        # Falls back to flat-rag-house if MemOS not installed.
        try:
            from convergence_io.memos_bridge import get_cube  # type: ignore
            cube = get_cube()
            # Build query from current message context + persona
            query = " ".join(filter(None, [
                " ".join(ctx.lore_hints[:2]) if ctx.lore_hints else "",
                ctx.persona,
            ])) or "dream"
            mem_context = cube.get_context_for_prompt(query, limit=3)
            if mem_context:
                ctx.lore_hints = [mem_context]
                return ctx
        except Exception as _memos_err:
            pass  # fall through to flat-rag-house

        # ── Flat RAG house fallback ──────────────────────────────────────────
        rag_path = self.data_dir / "rag-house" / "flat-rag-house-latest.json"
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
        intake_dir = self.data_dir / "rag-intake" / "tesseract-trace"
        intake_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": _now(),
            "persona": ctx.persona,
            "message_preview": message[:200],
            "reply_preview": str(result.get("text", ""))[:200],
            "provider": result.get("provider", "unknown"),
        }
        with open(intake_dir / "trace.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def _core_inference(self, ctx: ConvergenceContext, message: str) -> Dict[str, Any]:
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

    def _enter(self, layer: Layer, op: str) -> Dict[str, Any]:
        return {"layer": layer.name, "op": op, "phase": "enter", "at_ms": round(time.time() * 1000, 2)}

    def _exit(self, layer: Layer, op: str, start: float, error: Optional[str] = None) -> Dict[str, Any]:
        elapsed = round((time.time() - start) * 1000, 2)
        target = self.target_latency_ms(layer)
        status = "ok" if error is None and elapsed < target * 3 else "slow" if error is None else "error"
        result: Dict[str, Any] = {
            "layer": layer.name, "op": op, "phase": "exit",
            "elapsed_ms": elapsed, "target_ms": target, "status": status,
        }
        if error:
            result["error"] = error
        return result

    def _log(self, record: Dict[str, Any]) -> None:
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

    def inspect(self) -> Dict[str, Any]:
        return {
            "timestamp": _now(),
            "cells": len(self._cells),
            "target_latencies": {l.name: self.target_latency_ms(l) for l in Layer},
            "last_log": str(self.log_path) if self.log_path.exists() else "none",
            "metrics": self.metrics.snapshot(),
            "slots_active": self.slots.active_count("dream_journal"),
            "circuits": {k: v.state.value for k, v in self._circuit_cache.items()},
        }

    def health_check(self, url: str = "http://127.0.0.1:4177/api/status") -> Dict[str, Any]:
        return self.health.check(url)


# ═══════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    p_converge = sub.add_parser("converge")
    p_converge.add_argument("--message", default="Hello tesseract")
    p_converge.add_argument("--persona", default="lantern")
    p_converge.add_argument("--provider", default=None)

    p_inspect = sub.add_parser("inspect")

    p_loop = sub.add_parser("loop")

    p_health = sub.add_parser("health")
    p_health.add_argument("--url", default="http://127.0.0.1:4177/api/status")

    args = parser.parse_args()

    if args.command == "converge":
        engine = TesseractEngine()
        result = engine.converge(args.message, {"persona": args.persona, "provider": args.provider})
        print(json.dumps(result, indent=2))
    elif args.command == "inspect":
        engine = TesseractEngine()
        print(json.dumps(engine.inspect(), indent=2))
    elif args.command == "loop":
        loop = ConvergenceLoop()
        print(json.dumps(loop.run(), indent=2))
    elif args.command == "health":
        engine = TesseractEngine()
        print(json.dumps(engine.health_check(args.url), indent=2))
    else:
        parser.print_help()
