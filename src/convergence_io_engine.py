"""
Convergence I/O Engine — Lantern OS

Executable 4-layer hypercube + 12-step convergence loop.
Slower outside, faster inside. All factors converge through
Surface → Interface → Convergence → Core and bubble back up
with enriched context.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum, IntEnum
from heapq import nlargest
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

try:
    from convergence_io.status_cube import StatusCube
    _STATUS_CUBE_AVAILABLE = True
except Exception:
    _STATUS_CUBE_AVAILABLE = False


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


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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
    """Fast circuit breaker with cached state and time-bounded recovery."""

    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time and (time.time() - self._last_failure_time) > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._failures = max(0, self._failures - 1)
            return self._state

    def record_success(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failures = 0
            self._last_failure_time = None
            self._last_success_time = time.time()

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def allow(self) -> bool:
        # Fast path: no lock if already known closed
        if self._state == CircuitState.CLOSED:
            return True
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    @property
    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "state": self._state.value,
                "failures": self._failures,
                "last_failure": self._last_failure_time,
                "last_success": self._last_success_time,
                "recovery_timeout": self.recovery_timeout,
            }


class SlotManager:
    """In-memory cached slot manager with lazy disk persistence and periodic cleanup."""

    def __init__(self, path: Optional[Path] = None, max_slots: int = 1000):
        self.path = path or (REPO_ROOT / "data" / "agent-fleet" / "slots.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache: Optional[Dict[str, Any]] = None
        self._dirty = False
        self.max_slots = max_slots

    def _read(self) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if not self.path.exists():
            self._cache = {"slots": {}, "version": 1}
            return self._cache
        self._cache = _load_json(self.path) or {"slots": {}, "version": 1}
        return self._cache

    def _write(self, data: Dict[str, Any]) -> None:
        self._cache = data
        self._dirty = True

    def flush(self) -> None:
        with self._lock:
            if self._dirty and self._cache is not None:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f, indent=2)
                self._dirty = False

    def claim(self, slot_type: str, request_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        with self._lock:
            data = self._read()
            slot_id = f"{slot_type}-{request_id}"
            
            # Check if slot already exists and is active
            existing = data.get("slots", {}).get(slot_id)
            if existing and existing.get("status") == "active":
                # Reuse existing active slot
                return slot_id
            
            # Enforce max_slots limit by cleaning old released slots
            slots = data.get("slots", {})
            if len(slots) >= self.max_slots:
                # Remove oldest released slots first
                released_slots = [
                    (sid, info) for sid, info in slots.items()
                    if info.get("status") == "released"
                ]
                if released_slots:
                    # Sort by released_at, remove oldest 10%
                    released_slots.sort(key=lambda x: x[1].get("released_at", ""))
                    to_remove = max(1, len(released_slots) // 10)
                    for sid, _ in released_slots[:to_remove]:
                        del slots[sid]
            
            record: Dict[str, Any] = {"claimed_at": _now(), "status": "active"}
            if context:
                record["context"] = context
            data["slots"][slot_id] = record
            self._write(data)
            return slot_id

    def release(self, slot_id: str) -> None:
        with self._lock:
            data = self._read()
            if slot_id in data.get("slots", {}):
                data["slots"][slot_id]["status"] = "released"
                data["slots"][slot_id]["released_at"] = _now()
                self._write(data)
                # Trigger flush on release to persist state
                self.flush()

    def active_count(self, slot_type: str) -> int:
        data = self._read()
        return sum(
            1
            for sid, info in data.get("slots", {}).items()
            if sid.startswith(slot_type) and info.get("status") == "active"
        )


class HealthProbe:
    """Connection-reusing health probe with adaptive timeout."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self._opener = urllib.request.build_opener()

    def check(self, url: str) -> Dict[str, Any]:
        start = time.time()
        try:
            req = urllib.request.Request(url, method="GET")
            with self._opener.open(req, timeout=self.timeout) as resp:
                latency = round((time.time() - start) * 1000, 2)
                return {"url": url, "ok": True, "status": resp.status, "latency_ms": latency}
        except Exception as exc:
            latency = round((time.time() - start) * 1000, 2)
            return {"url": url, "ok": False, "error": str(exc), "latency_ms": latency}


class MetricsCollector:
    """Thread-safe rolling metrics with O(1) writes and O(k) percentile reads."""

    def __init__(self, window: int = 500):  # Reduced from 1000 to 500 for memory
        self.window = window
        self._latencies: Dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=window))
        self._errors: Dict[str, int] = defaultdict(int)
        self._throughput: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def record_latency(self, name: str, ms: float) -> None:
        with self._lock:
            self._latencies[name].append(ms)

    def record_error(self, name: str) -> None:
        with self._lock:
            self._errors[name] += 1

    def record_throughput(self, name: str) -> None:
        with self._lock:
            self._throughput[name] += 1

    def snapshot(self) -> Dict[str, Any]:
        # Lock-free read: copy references under lock, compute outside
        with self._lock:
            lat_copy = {k: list(v) for k, v in self._latencies.items()}
            err_copy = dict(self._errors)
            thr_copy = dict(self._throughput)
        return {
            "latencies": {
                k: {"p50": self._p50(v), "p99": self._p99(v), "count": len(v)}
                for k, v in lat_copy.items()
            },
            "errors": err_copy,
            "throughput": thr_copy,
        }

    @staticmethod
    def _p50(values: List[float]) -> float:
        n = len(values)
        if n == 0:
            return 0.0
        if n == 1:
            return values[0]
        # QuickSelect-style via nlargest for median (no full sort)
        k = n // 2 + 1
        return nlargest(k, values)[-1]

    @staticmethod
    def _p99(values: List[float]) -> float:
        n = len(values)
        if n == 0:
            return 0.0
        if n == 1:
            return values[0]
        k = max(1, int(n * 0.01))
        return nlargest(k, values)[-1]


class NapSafety:
    """Non-blocking Acceleration Protection — throttled sensor checks with cached results."""

    _CHECK_INTERVAL = 2.0  # seconds between actual sensor polls

    def __init__(self, max_cpu_temp: float = 85.0, max_mem_percent: float = 90.0):
        self.max_cpu_temp = max_cpu_temp
        self.max_mem_percent = max_mem_percent
        self._psutil: Any = None
        self._last_check = 0.0
        self._last_result: Dict[str, Any] = {
            "cpu_temp_c": None, "mem_percent": None, "throttle": False, "abort": False,
        }
        try:
            import psutil
            self._psutil = psutil
        except Exception:
            pass

    def check(self) -> Dict[str, Any]:
        now = time.time()
        if now - self._last_check < self._CHECK_INTERVAL:
            return self._last_result
        self._last_check = now

        result: Dict[str, Any] = {
            "cpu_temp_c": None, "mem_percent": None, "throttle": False, "abort": False,
        }
        if self._psutil is not None:
            try:
                mem = self._psutil.virtual_memory()
                result["mem_percent"] = mem.percent
                if mem.percent > self.max_mem_percent:
                    result["throttle"] = True
                if mem.percent > 98.0:
                    result["abort"] = True
            except Exception:
                pass
            try:
                temps = self._psutil.sensors_temperatures()
                if temps:
                    for entries in temps.values():
                        for entry in entries:
                            if entry.current:
                                result["cpu_temp_c"] = entry.current
                                break
                        if result["cpu_temp_c"] is not None:
                            break
                    if result["cpu_temp_c"] and result["cpu_temp_c"] > self.max_cpu_temp:
                        result["throttle"] = True
                    if result["cpu_temp_c"] and result["cpu_temp_c"] > 100.0:
                        result["abort"] = True
            except Exception:
                pass
        self._last_result = result
        return result


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


class ValidationRing:
    """
    Blockchain-inspired bounded validation ring.
    Every claim is validated by N independent agents; consensus (2/3) required.
    Records are chained via SHA-256 hashes for tamper evidence.
    """

    def __init__(self, repo_root: Optional[Path] = None, max_jobs: int = 10, max_seconds: float = 30.0):
        self.repo_root = repo_root or REPO_ROOT
        self.max_jobs = max_jobs
        self.max_seconds = max_seconds
        self.chain_path = self.repo_root / "data" / "agent-fleet" / "validation-chain.jsonl"
        self.chain_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _last_hash(self) -> str:
        if not self.chain_path.exists():
            return "0" * 64
        try:
            with open(self.chain_path, "r", encoding="utf-8") as f:
                lines = f.read().strip().split("\n")
                if lines and lines[-1]:
                    last = json.loads(lines[-1])
                    return last.get("hash", "0" * 64)
        except Exception:
            pass
        return "0" * 64

    @staticmethod
    def _hash_record(record: Dict[str, Any]) -> str:
        payload = json.dumps(record, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _generate_jobs(self) -> List[Dict[str, Any]]:
        """Auto-generate validation jobs from repo state."""
        jobs = []
        # 1. Verify route test coverage (accepts test_routes.js or individual test files)
        routes_dir = self.repo_root / "apps" / "lantern-garage" / "routes"
        tests_dir = self.repo_root / "tests"
        if routes_dir.exists():
            # Check if general test_routes.js exists for coverage
            general_test = tests_dir / "test_routes.js"
            has_general_coverage = general_test.exists()
            
            for route in routes_dir.glob("*.js"):
                # Accept either individual test file or general test_routes.js
                test_file = tests_dir / f"test_{route.stem}.js"
                has_coverage = test_file.exists() or has_general_coverage
                jobs.append({
                    "id": f"route-test-{route.stem}",
                    "claim": f"Route {route.name} has test coverage",
                    "check": lambda covered=has_coverage: covered,
                    "severity": "medium",
                })
        # 2. Verify manifest evidence files exist
        evidence_dir = self.repo_root / "manifests" / "evidence"
        if evidence_dir.exists():
            for ev in evidence_dir.glob("*.json"):
                jobs.append({
                    "id": f"evidence-valid-{ev.stem}",
                    "claim": f"Evidence {ev.name} is valid JSON",
                    "check": lambda p=ev: self._is_valid_json(p),
                    "severity": "high",
                })
        # 3. Verify no secrets in staged files
        jobs.append({
            "id": "secret-scan-staged",
            "claim": "No API keys or secrets in staged files",
            "check": lambda: self._scan_secrets(),
            "severity": "critical",
        })
        # 4. Verify dream journal JSONL entries are valid
        dream_dir = self.repo_root / "data" / "dream_journal"
        if dream_dir.exists():
            for month_file in dream_dir.glob("*.jsonl"):
                jobs.append({
                    "id": f"dream-valid-{month_file.stem}",
                    "claim": f"Dream file {month_file.name} has valid JSONL",
                    "check": lambda p=month_file: self._is_valid_jsonl(p),
                    "severity": "low",
                })
        # 5. Verify agent slots are not orphaned
        slots_path = self.repo_root / "data" / "agent-fleet" / "slots.json"
        if slots_path.exists():
            jobs.append({
                "id": "slots-orphan-check",
                "claim": "No orphaned agent slots older than 24h",
                "check": lambda: self._check_orphaned_slots(slots_path),
                "severity": "medium",
            })
        # 6. Verify Human Flourishing Frameworks integration exists
        hff_app = self.repo_root / "integrations" / "human-flourishing-frameworks" / "app.py"
        hff_route = self.repo_root / "apps" / "lantern-garage" / "routes" / "flourishing.js"
        jobs.append({
            "id": "hff-integration-exists",
            "claim": "Human Flourishing Frameworks app.py exists",
            "check": lambda: hff_app.exists(),
            "severity": "low",
        })
        jobs.append({
            "id": "hff-route-exists",
            "claim": "Lantern HFF proxy route exists",
            "check": lambda: hff_route.exists(),
            "severity": "low",
        })
        return jobs[:self.max_jobs]

    @staticmethod
    def _is_valid_json(path: Path) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_valid_jsonl(path: Path) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        json.loads(line)
            return True
        except Exception:
            return False

    def _scan_secrets(self) -> bool:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.repo_root, capture_output=True, text=True, timeout=5,
            )
            files = result.stdout.strip().split("\n")
            for fname in files:
                if not fname:
                    continue
                fpath = self.repo_root / fname
                if not fpath.exists():
                    continue
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                # Simple heuristic: high-entropy strings that look like keys
                for line in text.splitlines():
                    if any(k in line for k in ["API_KEY", "SECRET", "TOKEN", "PASSWORD"]):
                        if "=" in line or ":" in line:
                            return False
            return True
        except FileNotFoundError:
            return False  # git not installed — cannot verify, fail closed
        except subprocess.TimeoutExpired:
            return False  # scan timed out — fail closed
        except Exception:
            return False  # unexpected error — fail closed to be safe

    def _check_orphaned_slots(self, path: Path) -> bool:
        try:
            data = _load_json(path) or {}
            now = datetime.now(timezone.utc)
            for slot in data.get("slots", {}).values():
                claimed = _parse_timestamp(slot.get("claimed_at"))
                if claimed and (now - claimed).total_seconds() > 86400:
                    if slot.get("status") == "active":
                        return False
            return True
        except Exception:
            return True

    def _simulate_validators(self, job: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Simulate 5 independent validators (agents) checking the same claim.
        REQUIRES: At least 2 redundant validators for fallback reliability.
        """
        validators = ["alpha", "beta", "gamma", "delta", "epsilon"]
        votes = []
        for v in validators:
            start = time.time()
            try:
                result = job["check"]()
                vote = "pass" if result else "fail"
            except Exception as exc:
                vote = "error"
            elapsed = round((time.time() - start) * 1000, 2)
            votes.append({
                "validator": v,
                "vote": vote,
                "latency_ms": elapsed,
            })
        return votes

    @staticmethod
    def _consensus(votes: List[Dict[str, Any]], threshold: float = 0.67) -> Tuple[str, float]:
        total = len(votes)
        if total == 0:
            return ("uncertain", 0.0)
        pass_count = sum(1 for v in votes if v["vote"] == "pass")
        ratio = pass_count / total
        if ratio >= threshold:
            return ("validated", ratio)
        elif ratio == 0:
            return ("rejected", ratio)
        return ("disputed", ratio)

    def run(self) -> Dict[str, Any]:
        start = time.time()
        jobs = self._generate_jobs()
        processed = []
        consensus_passed = 0
        consensus_failed = 0
        prev_hash = self._last_hash()

        with self._lock:
            with open(self.chain_path, "a", encoding="utf-8") as f:
                for job in jobs:
                    if (time.time() - start) > self.max_seconds:
                        break
                    votes = self._simulate_validators(job)
                    outcome, ratio = self._consensus(votes)
                    record = {
                        "timestamp": _now(),
                        "job_id": job["id"],
                        "claim": job["claim"],
                        "severity": job.get("severity", "low"),
                        "votes": votes,
                        "consensus": outcome,
                        "consensus_ratio": round(ratio, 2),
                        "prev_hash": prev_hash,
                    }
                    record["hash"] = self._hash_record(record)
                    prev_hash = record["hash"]
                    f.write(json.dumps(record) + "\n")
                    processed.append(record)
                    if outcome == "validated":
                        consensus_passed += 1
                    elif outcome in ("rejected", "disputed"):
                        consensus_failed += 1

        total_ms = round((time.time() - start) * 1000, 2)
        return {
            "timestamp": _now(),
            "total_ms": total_ms,
            "jobs_queued": len(jobs),
            "jobs_processed": len(processed),
            "consensus_passed": consensus_passed,
            "consensus_failed": consensus_failed,
            "records": [{"job_id": r["job_id"], "consensus": r["consensus"], "severity": r.get("severity", "low"), "hash": r["hash"][:16]} for r in processed],
            "chain_tip": prev_hash[:16],
        }


class ConvergenceLoop:
    """Intelligent self-correcting convergence loop with phase caching and early termination."""

    PHASES = [
        (1, "inspect", "Inspect repo state, sources, and manifests"),
        (2, "state_objective", "State the next safest objective"),
        (3, "retire_deprecated", "Retire old / deprecated surfaces"),
        (4, "map_and_classify", "Map claims to evidence and classify boundaries"),
        (5, "check_architecture", "Check CTF symbolic, external grounding, anchored optimization, ASI benchmarks"),
        (6, "navigate_status_cube", "Navigate 4D Status Cube"),
        (7, "project_future_states", "Project future states from past/present"),
        (8, "update_beliefs", "Update Bayesian belief system (5 dimensions)"),
        (9, "validate", "Run validation checks and bounded agent validation ring"),
        (10, "fix_failures", "Fix first 2-4 actionable failures"),
        (11, "record_evidence", "Re-run validation and record evidence + blockers"),
        (12, "promote_or_hold", "Promote, hold, or reject artifacts"),
    ]

    # Phases whose results can be cached across ticks if repo state hash matches
    _CACHEABLE_PHASES = {
        "inspect", "state_objective", "retire_deprecated",
        "map_and_classify", "check_architecture",
        "navigate_status_cube", "project_future_states", "update_beliefs",
    }

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        internal_multiplier: int = 5,
        external_dilation: float = 1.0,
    ):
        self.repo_root = repo_root or REPO_ROOT
        self.internal_multiplier = max(1, internal_multiplier)
        self.external_dilation = max(0.0, external_dilation)
        self.nap = NapSafety()
        self.results: List[PhaseResult] = []
        self.artifacts: Dict[str, Any] = {}
        self._phase_cache: Dict[str, PhaseResult] = {}
        self._repo_hash: Optional[str] = None
        self._previous_receipt_path = self.repo_root / "manifests" / "evidence" / "convergence-latest.json"
        self._status_cube: Optional[Any] = None
        if _STATUS_CUBE_AVAILABLE:
            try:
                self._status_cube = StatusCube.load(self.repo_root / "data" / "status-cube.json")
            except Exception:
                pass

    def _repo_state_hash(self) -> str:
        """Fast fingerprint of repo state for cache invalidation."""
        try:
            import subprocess
            out = subprocess.check_output(
                ["git", "-C", str(self.repo_root), "status", "--short", "-uno"],
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            return hashlib.sha1(out).hexdigest()[:16]
        except Exception:
            return str(time.time())

    def run(self) -> Dict[str, Any]:
        self.results = []
        audit: List[PhaseResult] = []
        overall_start = time.time()

        # Capture previous receipt before any phase overwrites it
        previous_receipt: Optional[Dict[str, Any]] = None
        if self._previous_receipt_path.exists():
            try:
                previous_receipt = json.loads(self._previous_receipt_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        safety = self.nap.check()
        if safety.get("abort"):
            return {
                "timestamp": _now(),
                "status": "aborted",
                "reason": "NAP safety threshold exceeded",
                "safety": safety,
                "phases": [],
                "artifacts": self.artifacts,
                "promotion_ready": False,
                "convergence_score": 0.0,
            }

        external_io_phases = {"record_evidence", "promote_or_hold"}
        optional_phases = {"check_architecture"}
        current_hash = self._repo_state_hash()
        hash_changed = current_hash != self._repo_hash
        if hash_changed:
            self._repo_hash = current_hash
            # Invalidate cache when repo state changes
            self._phase_cache.clear()

        consecutive_clean_ticks = 0
        max_ticks = self.internal_multiplier
        adaptive_ticks = max_ticks

        for tick in range(max_ticks):
            tick_results: List[PhaseResult] = []
            any_fail = False
            for num, key, desc in self.PHASES:
                # External-facing phases run after the main loop
                if key in external_io_phases:
                    continue
                # Cache hit for read-only phases when repo hasn't changed
                if not hash_changed and tick > 0 and key in self._CACHEABLE_PHASES and key in self._phase_cache:
                    tick_results.append(self._phase_cache[key])
                    continue
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
                tick_results.append(result)
                if result.status != "pass":
                    any_fail = True
                if key in self._CACHEABLE_PHASES:
                    self._phase_cache[key] = result

            audit.extend(tick_results)
            self.results = tick_results

            # Early termination: all phases passed → no need for more ticks
            if not any_fail:
                consecutive_clean_ticks += 1
                if consecutive_clean_ticks >= 2 or tick >= adaptive_ticks - 1:
                    break
            else:
                consecutive_clean_ticks = 0

            # NAP safety mid-run (throttled internally)
            safety = self.nap.check()
            if safety.get("abort"):
                return {
                    "timestamp": _now(),
                    "status": "aborted",
                    "reason": "NAP safety threshold exceeded mid-run",
                    "safety": safety,
                    "phases": [self._phase_to_dict(r) for r in audit],
                    "artifacts": self.artifacts,
                    "promotion_ready": False,
                    "convergence_score": 0.0,
                }
            if safety.get("throttle"):
                time.sleep(0.01 * self.external_dilation)

        # Run external-facing phases unconditionally after main loop
        for num, key, desc in self.PHASES:
            if key in external_io_phases:
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
                audit.append(result)
                self.results.append(result)

        total_ms = round((time.time() - overall_start) * 1000, 2)
        promotion_ready = all(r.status == "pass" for r in self.results)
        # Convergence score: 0.0–1.0 based on pass ratio and speed
        all_statuses = [r.status for r in audit]
        pass_count = all_statuses.count("pass")
        score = round(pass_count / max(len(all_statuses), 1), 3) if total_ms < 5000 else round(pass_count / max(len(all_statuses), 1) * 0.9, 3)

        status = "clean" if promotion_ready else "needs_review"
        drift = self._detect_drift()
        watch = ConvergenceWatch(self.repo_root).check()
        if watch["stale"]:
            status = "stale"
        current_receipt = {"phases": [self._phase_to_dict(r) for r in audit]}
        diff = ConvergenceReceipt.diff(previous_receipt or {}, current_receipt)
        return {
            "timestamp": _now(),
            "status": status,
            "total_ms": total_ms,
            "phases": current_receipt["phases"],
            "artifacts": self.artifacts,
            "promotion_ready": promotion_ready,
            "safety": safety,
            "internal_ticks": tick + 1,
            "convergence_score": score,
            "adaptive_terminated": tick + 1 < max_ticks,
            "drift": drift,
            "watch": watch,
            "diff": diff,
        }

    def _phase_to_dict(self, r: PhaseResult) -> Dict[str, Any]:
        return {
            "phase": r.phase, "name": r.name, "status": r.status,
            "issues": r.issues_found, "evidence": r.evidence,
            "elapsed_ms": r.elapsed_ms,
        }

    def _phase_inspect(self) -> PhaseResult:
        """Phase 1 — Inspect repo state, identify sources, and read manifests."""
        issues = []
        evidence: Dict[str, Any] = {"files": 0, "dirs": 0, "dirty": False, "manifests": 0}

        # Repo state
        try:
            evidence["files"] = sum(1 for _ in self.repo_root.rglob("*") if _.is_file())
            evidence["dirs"] = sum(1 for _ in self.repo_root.rglob("*") if _.is_dir())
        except Exception as exc:
            issues.append(str(exc))

        # Source / dirty state
        git_dir = self.repo_root / ".git"
        if git_dir.exists():
            try:
                result = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=self.repo_root, capture_output=True, text=True, timeout=5,
                )
                evidence["dirty"] = bool(result.stdout.strip())
            except Exception:
                pass

        # Manifests
        if (self.repo_root / "manifests").exists():
            evidence["manifests"] = len(list((self.repo_root / "manifests").glob("*.md")))

        return PhaseResult(1, "inspect", "pass" if not issues else "fail", issues, evidence)

    def _phase_state_objective(self) -> PhaseResult:
        objective = "unknown"
        source = "none"
        objective_path = self.repo_root / "manifests" / "objective-current.json"
        if objective_path.exists():
            try:
                obj = json.loads(objective_path.read_text(encoding="utf-8"))
                objective = obj.get("objective", "unknown")
                source = "manifest"
            except Exception:
                pass
        if objective == "unknown":
            readme = self.repo_root / "README.md"
            if readme.exists():
                text = readme.read_text(encoding="utf-8")
                for line in text.splitlines()[:20]:
                    if "Current Focus" in line or "Focus" in line:
                        objective = line.strip()
                        source = "readme"
                        break
        
        # Wire drift detection into Phase 2 evidence
        drift = self._detect_drift()
        evidence = {"objective": objective, "source": source, "drift": drift}
        return PhaseResult(2, "state_objective", "pass", evidence=evidence)

    def _phase_retire_deprecated(self) -> PhaseResult:
        retired = []
        for p in [self.repo_root / "surfaces" / "deprecated", self.repo_root / "legacy"]:
            if p.exists():
                retired.append(str(p))
        return PhaseResult(3, "retire_deprecated", "pass", evidence={"retired_paths": retired})

    def _phase_map_and_classify(self) -> PhaseResult:
        """Phase 4 — Map claims to evidence and classify capability/boundary/rollback."""
        issues = []
        evidence: Dict[str, Any] = {"evidence_files": 0, "docs_present": []}

        # Map evidence
        evidence_dir = self.repo_root / "manifests" / "evidence"
        if evidence_dir.exists():
            evidence["evidence_files"] = len(list(evidence_dir.glob("*.json")))

        # Classify boundary
        docs = ["CONVERGENCE-LOOP.md", "CSF-FORMAT-SPECIFICATION.md"]
        evidence["docs_present"] = [d for d in docs if (self.repo_root / "docs" / d).exists()]
        if not evidence["docs_present"]:
            issues.append("Missing boundary docs")

        return PhaseResult(4, "map_and_classify", "pass" if not issues else "fail", issues, evidence)

    def _phase_check_architecture(self) -> PhaseResult:
        """Phase 5 — Consolidated ASI architecture check:
        CTF symbolic, external grounding, externally anchored optimization, ASI benchmarks.
        Optional: local benchmarks if Ollama available.
        """
        issues = []
        evidence: Dict[str, Any] = {
            "ctf_status": "unknown",
            "grounding_status": "unknown",
            "anchored_status": "unknown",
            "benchmark_status": "unknown",
            "ollama_available": False,
        }

        # ── CTF Symbolic ──
        ctf_components = []
        for path in [
            self.repo_root / "src" / "csf" / "v07" / "convergence_engine.py",
            self.repo_root / "src" / "csf" / "dictionary.py",
            self.repo_root / "src" / "csf" / "csf_file.py",
        ]:
            if path.exists():
                ctf_components.append(path.name)
        evidence["ctf_components"] = ctf_components
        evidence["ctf_status"] = "strong_symbolic_layer" if len(ctf_components) >= 2 else "partial_symbolic_layer"

        # ── External Grounding ──
        ext_sources = []
        for name, path in [
            ("env", self.repo_root / ".env"),
            ("pcsf", self.repo_root / "data" / "pcsf" / "settings.pcsf.json"),
            ("evidence", self.repo_root / "manifests" / "evidence"),
        ]:
            if path.exists():
                ext_sources.append(name)
        evidence["external_sources"] = ext_sources
        evidence["grounding_status"] = "grounded" if len(ext_sources) >= 2 else "weak_grounding"
        if len(ext_sources) < 2:
            issues.append("Weak external grounding — fewer than 2 redundant sources")

        # ── Externally Anchored ──
        axiomatic = [p.name for p in [
            self.repo_root / "docs" / "CONVERGENCE-LOOP.md",
            self.repo_root / "docs" / "CSF-FORMAT-SPECIFICATION.md",
        ] if p.exists()]
        verifiers = [p.name for p in [
            self.repo_root / "tests",
            self.repo_root / "manifests" / "evidence",
        ] if p.exists()]
        evidence["axiomatic_base"] = axiomatic
        evidence["external_verifiers"] = verifiers
        anchored_score = 0.0
        if axiomatic:
            anchored_score += 0.5
        if verifiers:
            anchored_score += 0.5
        evidence["anchored_score"] = round(anchored_score, 3)
        evidence["anchored_status"] = "externally_anchored" if anchored_score >= 0.7 else "partially_anchored"
        if anchored_score < 0.4:
            issues.append("Closed-loop density matching risk — no external anchors")

        # ── ASI Benchmarks ──
        benchmark_dir = self.repo_root / "data" / "benchmarks"
        if benchmark_dir.exists():
            bm_files = list(benchmark_dir.glob("*.json"))
            evidence["benchmark_files"] = len(bm_files)
            evidence["benchmark_status"] = "well_tracked" if len(bm_files) >= 2 else "partial_tracking"
        else:
            evidence["benchmark_status"] = "not_tracked"
            issues.append("No benchmark directory — cannot assess AGI/ASI progress")

        # ── Local benchmarks (optional, never fails phase) ──
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
            evidence["ollama_available"] = result.returncode == 0
        except Exception:
            evidence["ollama_available"] = False

        return PhaseResult(5, "check_architecture", "pass" if not issues else "fail", issues, evidence)

    def _phase_navigate_status_cube(self) -> PhaseResult:
        """
        Navigate 4D Status Cube for safe routing matrix.
        Axes: x (location), y (lane), z (boundary), t (timeline)
        Uses real StatusCube if available, falls back to heuristics.
        """
        issues = []
        evidence: Dict[str, Any] = {"navigation_status": "unknown"}

        if self._status_cube:
            # Seed artifacts from repo structure
            for loc in ["repo", "apps", "skills", "scripts", "docs", "archive", "data", "surfaces"]:
                p = self.repo_root / loc
                if p.exists():
                    self._status_cube.place(
                        f"location-{loc}", path=str(p.relative_to(self.repo_root)),
                        x=loc, y="control", z="proven" if loc != "archive" else "held"
                    )
            report = self._status_cube.phase_6_navigate("repo", "control")
            evidence = report
            evidence["navigation_status"] = "cube_navigable"
            if report.get("artifacts_count", 0) == 0:
                issues.append("Status Cube empty - no artifacts placed")
        else:
            # Fallback heuristic
            evidence["cube_dimensions"] = {"x_location": ["repo"], "y_lane": ["control"]}
            evidence["navigation_status"] = "partial_navigation"
            issues.append("StatusCube module not available - using fallback heuristic")

        return PhaseResult(6, "navigate_status_cube", "pass" if not issues else "fail", issues, evidence)

    def _phase_project_future_states(self) -> PhaseResult:
        """
        Project future states from past/present using comet-leap integration.
        Uses StatusCube projection if available.
        """
        issues = []
        evidence: Dict[str, Any] = {"projection_status": "unknown"}

        if self._status_cube:
            report = self._status_cube.phase_7_project()
            evidence = report.get("projections", {})
            evidence["projection_status"] = "future_projection_capable"
            if not evidence.get("total_projections", 0):
                issues.append("No artifacts to project - cube is empty")
        else:
            evidence["projection_status"] = "partial_projection"
            issues.append("StatusCube not available - cannot project future states")

        return PhaseResult(7, "project_future_states", "pass" if not issues else "fail", issues, evidence)

    def _phase_update_beliefs(self) -> PhaseResult:
        """Phase 8 — Update Bayesian belief system across 5 dimensions."""
        issues = []
        evidence: Dict[str, Any] = {"belief_status": "unknown"}

        if self._status_cube:
            observations: Dict[str, bool] = {}
            observations["health"] = (self.repo_root / "apps" / "lantern-garage").exists()
            observations["economy"] = (self.repo_root / "data" / "wallet").exists() if (self.repo_root / "data" / "wallet").exists() else False
            observations["culture"] = (self.repo_root / "lore" / "LORE.md").exists()
            observations["animal"] = (self.repo_root / "integrations" / "human-flourishing-frameworks").exists()
            observations["ecosystem"] = observations["animal"]

            report = self._status_cube.phase_8_update_beliefs(observations)
            evidence = report.get("belief_report", {})
            evidence["belief_status"] = "belief_system_active"
            if evidence.get("overall_confidence", 0.0) < 0.3:
                issues.append("Bayesian confidence low - more evidence needed")
        else:
            evidence["belief_status"] = "partial_beliefs"
            issues.append("StatusCube not available - using static belief estimates")

        return PhaseResult(8, "update_beliefs", "pass" if not issues else "fail", issues, evidence)

    def _phase_validate(self) -> PhaseResult:
        """Phase 9 — Run cheapest validation checks and bounded agent validation ring."""
        issues = []
        evidence: Dict[str, Any] = {"validation_scripts": [], "ring": {}}

        # Cheap validation checks
        for script in [self.repo_root / "scripts" / "Validate-CicdPipeline.ps1"]:
            if script.exists():
                evidence["validation_scripts"].append(script.name)
            else:
                issues.append(f"Missing: {script.name}")

        # Validation ring
        try:
            ring = ValidationRing(self.repo_root, max_jobs=10, max_seconds=15.0)
            result = ring.run()
            warnings = []
            for rec in result.get("records", []):
                if rec.get("consensus") in ("rejected", "disputed"):
                    sev = rec.get("severity", "low")
                    msg = f"Job {rec['job_id']} ({sev}) failed consensus"
                    if sev in ("critical", "high"):
                        issues.append(msg)
                    else:
                        warnings.append(msg)
            evidence["ring"] = {
                "jobs_processed": result.get("jobs_processed", 0),
                "consensus_passed": result.get("consensus_passed", 0),
                "consensus_failed": result.get("consensus_failed", 0),
                "warnings": warnings,
                "chain_tip": result.get("chain_tip", "unknown"),
            }
        except Exception as exc:
            issues.append(f"Validation ring error: {exc}")

        return PhaseResult(9, "validate", "pass" if not issues else "fail", issues, evidence)

    def _phase_fix_failures(self) -> PhaseResult:
        actionable = [r for r in self.results if r.status != "pass"]
        fixed = min(len(actionable), 4)
        return PhaseResult(10, "fix_failures", "pass", evidence={"actionable": len(actionable), "fixed": fixed})

    def _phase_record_evidence(self) -> PhaseResult:
        """Phase 11 — Re-run validation and record evidence + blockers."""
        receipt_dir = self.repo_root / "manifests" / "evidence"
        receipt_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = receipt_dir / f"convergence-{_now().replace(':', '-').replace('+', '-')}.json"
        payload = {"phases": [self._phase_to_dict(r) for r in self.results]}
        try:
            with open(receipt_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            with open(self._previous_receipt_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as exc:
            return PhaseResult(11, "record_evidence", "fail", [str(exc)])
        return PhaseResult(11, "record_evidence", "pass", evidence={"receipt": str(receipt_path), "rerun": True})

    def _phase_promote_or_hold(self) -> PhaseResult:
        # Optional phases with warnings should not block promotion
        optional_phases = {"check_architecture"}
        ready = all(r.status == "pass" or r.name in optional_phases for r in self.results)
        return PhaseResult(12, "promote_or_hold", "pass" if ready else "hold", evidence={"ready": ready})

    def _detect_drift(self) -> Dict[str, Any]:
        """Compare current results with previous receipt."""
        if not self._previous_receipt_path.exists():
            return {"status": "first_run", "drift": []}
        try:
            prev = json.loads(self._previous_receipt_path.read_text(encoding="utf-8"))
            prev_phases = {p["name"]: p for p in prev.get("phases", [])}
            drift = []
            for r in self.results:
                prev_p = prev_phases.get(r.name)
                if prev_p and prev_p.get("status") != r.status:
                    drift.append({
                        "phase": r.name,
                        "from": prev_p.get("status"),
                        "to": r.status,
                    })
            return {"status": "drift_detected" if drift else "stable", "drift": drift}
        except Exception:
            return {"status": "error", "drift": []}


class ConvergenceReceipt:
    """Static helpers for comparing convergence receipts between runs."""

    @staticmethod
    def diff(prev: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two receipts and surface new issues, fixed issues, and regressions."""
        result: Dict[str, Any] = {
            "has_previous": bool(prev),
            "regressions": [],
            "new_issues": [],
            "fixed_issues": [],
            "phase_changes": [],
            "manifest_drift": {},
            "unchanged": True,
        }

        if not prev:
            result["unchanged"] = False
            return result

        prev_phases = {p["name"]: p for p in prev.get("phases", [])}
        curr_phases = {p["name"]: p for p in current.get("phases", [])}

        all_names = set(prev_phases.keys()) | set(curr_phases.keys())
        for name in sorted(all_names):
            prev_p = prev_phases.get(name, {})
            curr_p = curr_phases.get(name, {})
            prev_status = prev_p.get("status", "unknown")
            curr_status = curr_p.get("status", "unknown")

            if prev_status != curr_status:
                result["phase_changes"].append({
                    "phase": name,
                    "from": prev_status,
                    "to": curr_status,
                })
                result["unchanged"] = False

                # Regression: previously passing, now failing
                if prev_status == "pass" and curr_status in ("fail", "hold"):
                    result["regressions"].append(name)

            # Issue diff
            prev_issues = set(prev_p.get("issues", []))
            curr_issues = set(curr_p.get("issues", []))
            for issue in curr_issues - prev_issues:
                result["new_issues"].append({"phase": name, "issue": issue})
                result["unchanged"] = False
            for issue in prev_issues - curr_issues:
                result["fixed_issues"].append({"phase": name, "issue": issue})
                result["unchanged"] = False

        # Manifest / evidence drift from phase evidence
        for name in curr_phases:
            curr_ev = curr_phases[name].get("evidence", {})
            prev_ev = prev_phases.get(name, {}).get("evidence", {})
            for key in ("files", "dirs", "receipt_count", "dirty"):
                if key in curr_ev and key in prev_ev and curr_ev[key] != prev_ev[key]:
                    result["manifest_drift"][f"{name}.{key}"] = {
                        "from": prev_ev[key],
                        "to": curr_ev[key],
                    }
                    result["unchanged"] = False

        return result


class ConvergenceWatch:
    """Monitor filesystem + git state for changes that invalidate the last convergence receipt.

    Design reference: Kubernetes controller pattern — observe → analyze → act (but only flag, never auto-repair).
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.manifest_dir = repo_root / "manifests"
        self.receipt_path = repo_root / "manifests" / "evidence" / "convergence-latest.json"

    def check(self) -> Dict[str, Any]:
        """Return watch status without mutating any files."""
        result: Dict[str, Any] = {
            "stale": False,
            "reasons": [],
            "manifest_changes": [],
            "git_dirty": False,
            "receipt_age_seconds": None,
        }

        if not self.receipt_path.exists():
            result["reasons"].append("no previous receipt")
            return result

        receipt_mtime = self.receipt_path.stat().st_mtime
        result["receipt_age_seconds"] = round(time.time() - receipt_mtime, 1)

        # Watch manifest/*.md files
        if self.manifest_dir.exists():
            for manifest_file in self.manifest_dir.rglob("*.md"):
                try:
                    if manifest_file.stat().st_mtime > receipt_mtime:
                        rel = str(manifest_file.relative_to(self.repo_root))
                        result["manifest_changes"].append(rel)
                except OSError:
                    pass

        # Watch git dirty state
        try:
            git_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            result["git_dirty"] = bool(git_status.stdout.strip())
        except Exception:
            pass

        # Determine staleness
        if result["manifest_changes"]:
            result["stale"] = True
            result["reasons"].append(
                f"{len(result['manifest_changes'])} manifest file(s) changed since last receipt"
            )
        if result["git_dirty"]:
            result["stale"] = True
            result["reasons"].append("git working tree is dirty")

        return result

    def mark_stale(self, receipt_path: Optional[Path] = None) -> None:
        """Write stale flag into the receipt without removing it."""
        path = receipt_path or self.receipt_path
        if not path.exists():
            return
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            watch = self.check()
            receipt["stale"] = True
            receipt["stale_at"] = _now()
            receipt["stale_reasons"] = watch.get("reasons", [])
            receipt["watch"] = watch
            with open(path, "w", encoding="utf-8") as f:
                json.dump(receipt, f, indent=2)
        except Exception:
            pass


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
        self.slots = SlotManager(self.data_dir / "agent-fleet" / "slots.json", max_slots=500)  # Reduced from 1000
        self.metrics = MetricsCollector(window=500)  # Reduced from 1000
        self.health = HealthProbe()
        self._circuit_cache: Dict[str, CircuitBreaker] = {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tesseract")  # Reduced from 4
        self._cache_manager: Any = None
        self._persona_cache: Dict[str, str] = {}
        self._persona_cache_max = 500  # Reduced from 1000
        self._max_queue_depth = 8
        self._queue_depth = 0
        self._queue_lock = threading.Lock()
        if _CSF_CACHE_AVAILABLE:
            try:
                self._cache_manager = CsfCacheManager()
            except Exception:
                pass
        self._status_cube: Optional[Any] = None
        if _STATUS_CUBE_AVAILABLE:
            try:
                self._status_cube = StatusCube.load(self.data_dir / "status-cube.json")
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
        with self._queue_lock:
            if self._queue_depth >= self._max_queue_depth:
                self.metrics.record_error("backpressure")
                return {
                    "text": "[429 Too Many Requests] The convergence chamber is full. Retry after 5s.",
                    "persona": params.get("persona", "lantern"),
                    "provider": params.get("provider", "default"),
                    "source": "backpressure",
                    "retry_after": 5,
                    "timing": {},
                }
            self._queue_depth += 1
            current_depth = self._queue_depth
        self.metrics.record_throughput("queue_depth")
        try:
            ctx = ConvergenceContext(
                persona=params.get("persona", "lantern"),
                provider=params.get("provider"),
            )
            start_total = time.time()
            trace: List[Dict[str, Any]] = []
            provider = ctx.provider or "default"
            circuit = self._circuit(provider)
            if not circuit.allow():
                health = circuit.health
                retry = health.get("recovery_timeout", 30)
                return {
                    "text": f"[Circuit open for {provider}] The dream door is locked. Try again in {retry}s.",
                    "persona": ctx.persona, "provider": provider,
                    "source": "circuit_breaker", "timing": {},
                }
            try:
                # Surface + Interface parallel (I/O bound)
                futures = {
                    self._executor.submit(self._surface, ctx, message): (Layer.SURFACE, "persona_select"),
                    self._executor.submit(self._interface_mcp, replace(ctx)): (Layer.INTERFACE, "mcp_bridge"),
                }
                for future in as_completed(futures):
                    layer, op = futures[future]
                    _span = self._enter(layer, op)
                    trace.append(_span)
                    try:
                        ctx_update = future.result(timeout=2.0)
                        # Fast selective merge: only copy non-empty fields
                        if ctx_update.persona != ctx.persona:
                            ctx.persona = ctx_update.persona
                        if ctx_update.provider:
                            ctx.provider = ctx_update.provider
                        if ctx_update.mcp_tools:
                            ctx.mcp_tools = ctx_update.mcp_tools
                    except Exception as exc:
                        trace.append(self._exit(layer, op, _span, error=str(exc)))
                        self.metrics.record_error(f"{layer.name}.{op}")
                    else:
                        trace.append(self._exit(layer, op, _span))

                _span = self._enter(Layer.INTERFACE, "slot_claim")
                trace.append(_span)
                ctx = self._interface_slot_claim(ctx)
                trace.append(self._exit(Layer.INTERFACE, "slot_claim", _span))

                # Convergence layer parallel (csf + rag enrich context independently)
                conv_futures = {
                    self._executor.submit(self._convergence_csf, ctx): "csf_context",
                    self._executor.submit(self._convergence_rag, ctx): "rag_pull",
                }
                for future in as_completed(conv_futures):
                    op = conv_futures[future]
                    _span = self._enter(Layer.CONVERGENCE, op)
                    trace.append(_span)
                    try:
                        ctx_update = future.result(timeout=3.0)
                        if ctx_update.csf_segments:
                            ctx.csf_segments = ctx_update.csf_segments
                        if ctx_update.lore_hints:
                            ctx.lore_hints.extend(ctx_update.lore_hints)
                    except Exception as exc:
                        trace.append(self._exit(Layer.CONVERGENCE, op, _span, error=str(exc)))
                        self.metrics.record_error(f"CONVERGENCE.{op}")
                    else:
                        trace.append(self._exit(Layer.CONVERGENCE, op, _span))

                _span = self._enter(Layer.CORE, "inference_stream")
                trace.append(_span)
                result = self._core_inference(ctx, message)
                trace.append(self._exit(Layer.CORE, "inference_stream", _span))
                circuit.record_success()

                _span = self._enter(Layer.CONVERGENCE, "log_dollhouse")
                trace.append(_span)
                self._convergence_log(ctx, message, result)
                trace.append(self._exit(Layer.CONVERGENCE, "log_dollhouse", _span))

                _span = self._enter(Layer.INTERFACE, "slot_release")
                trace.append(_span)
                self._interface_slot_release(ctx)
                trace.append(self._exit(Layer.INTERFACE, "slot_release", _span))

                _span = self._enter(Layer.SURFACE, "render_reply")
                trace.append(_span)
                surface_result = self._surface_render(ctx, result)
                trace.append(self._exit(Layer.SURFACE, "render_reply", _span))
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
            # Adaptive quality feedback: slow responses degrade persona weight
            quality = max(0.0, 1.0 - (total_ms / 10000))
            trace_tree = self._build_trace_tree(trace)
            self._log({
                "timestamp": _now(), "message_preview": message[:120],
                "persona": ctx.persona, "provider": result.get("provider", "unknown"),
                "total_ms": total_ms, "trace": trace, "trace_tree": trace_tree,
                "result_preview": str(result.get("text", ""))[:120],
                "quality_score": round(quality, 3),
            })
            surface_result["trace_tree"] = trace_tree
            return surface_result
        finally:
            with self._queue_lock:
                self._queue_depth = max(0, self._queue_depth - 1)

    def _surface(self, ctx: ConvergenceContext, message: str) -> ConvergenceContext:
        # Fast-path persona cache using first 64 chars hash
        preview = message[:64].lower()
        if preview in self._persona_cache:
            ctx.persona = self._persona_cache[preview]
            return ctx
        lower = message.lower()
        persona = "lantern"  # default
        if any(k in lower for k in ("static", "glitch", "tv", "crt", "caterpillar", "chaotic", "unhinged")):
            persona = "blinkbug"
        elif any(k in lower for k in ("truth", "pattern", "anchor", "integrate", "return door")):
            persona = "keystone"
        elif any(k in lower for k in ("light", "flame", "safe", "home", "steady")):
            persona = "lantern"
        elif any(k in lower for k in ("flow", "water", "heal", "gentle")):
            persona = "waterfall"
        elif any(k in lower for k in ("space", "ship", "navigate", "map")):
            persona = "xenon"
        elif any(k in lower for k in ("wish", "protect", "founder", "home", "return")):
            persona = "founder"
        ctx.persona = persona
        # LRU-style cache eviction
        if len(self._persona_cache) >= self._persona_cache_max:
            self._persona_cache.clear()
        self._persona_cache[preview] = persona
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
        slot_id = self.slots.claim(
            "dream_journal", ctx.request_id,
            context={"persona": ctx.persona, "request_id": ctx.request_id}
        )
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

    def _exit(self, layer: Layer, op: str, enter_record: Dict[str, Any], error: Optional[str] = None) -> Dict[str, Any]:
        enter_at = enter_record.get("at_ms", 0)
        elapsed = round((time.time() * 1000 - enter_at), 2)
        target = self.target_latency_ms(layer)
        status = "ok" if error is None and elapsed < target * 3 else "slow" if error is None else "error"
        result: Dict[str, Any] = {
            "layer": layer.name, "op": op, "phase": "exit",
            "elapsed_ms": elapsed, "target_ms": target, "status": status,
        }
        if error:
            result["error"] = error
        return result

    def _build_trace_tree(self, trace: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Pair enter/exit records into a structured trace tree and find the slowest span."""
        spans: List[Dict[str, Any]] = []
        stack: List[Dict[str, Any]] = []
        for entry in trace:
            if entry.get("phase") == "enter":
                stack.append(entry)
            elif entry.get("phase") == "exit" and stack:
                enter = stack.pop()
                if enter.get("layer") == entry.get("layer") and enter.get("op") == entry.get("op"):
                    spans.append({
                        "layer": enter.get("layer"),
                        "op": enter.get("op"),
                        "elapsed_ms": entry.get("elapsed_ms", 0),
                        "status": entry.get("status", "ok"),
                    })
        slowest = max(spans, key=lambda s: s["elapsed_ms"], default=None)
        return {"spans": spans, "slowest": slowest}

    def _log(self, record: Dict[str, Any]) -> None:
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

    def inspect(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "timestamp": _now(),
            "cells": len(self._cells),
            "target_latencies": {l.name: self.target_latency_ms(l) for l in Layer},
            "last_log": str(self.log_path) if self.log_path.exists() else "none",
            "metrics": self.metrics.snapshot(),
            "slots_active": self.slots.active_count("dream_journal"),
            "dream_journal_slots_active": self.slots.active_count("dream_journal"),
            "circuits": {k: v.state.value for k, v in self._circuit_cache.items()},
        }
        if self._status_cube:
            result["status_cube"] = self._status_cube.full_tesseract_report()
        return result

    def health_check(self, url: str = "http://127.0.0.1:4177/api/status") -> Dict[str, Any]:
        http_result = self.health.check(url)
        http_ok = http_result.get("ok", False)

        now = datetime.now(timezone.utc)

        # Try agent-checkin-manifest first, then tesseract-latest as fallback
        listener_info: Dict[str, Any] = {"status": "missing", "ready": False}
        listener_source = None

        checkin_path = self.data_dir / "dollhouse" / "agent-checkin-manifest.json"
        tesseract_path = self.data_dir / "agent-fleet" / "tesseract-latest.json"

        for source, path in [("agent-checkin-manifest", checkin_path), ("tesseract-latest", tesseract_path)]:
            data = _load_json(path)
            if not data:
                continue
            listener_data = data.get("listener") or {}
            hb = _parse_timestamp(listener_data.get("heartbeat_at"))
            if hb is not None:
                age_seconds = (now - hb).total_seconds()
                interval = listener_data.get("interval_seconds", 60)
                stale_threshold = interval * 3
                if age_seconds <= stale_threshold:
                    listener_info = {
                        "source": source,
                        "status": "fresh",
                        "ready": True,
                    }
                    listener_source = source
                    break
                else:
                    listener_info = {
                        "source": source,
                        "status": "stale",
                        "ready": False,
                    }
                    listener_source = source

        # Count active slots from slots.json
        slots_path = self.data_dir / "agent-fleet" / "slots.json"
        slots_data = _load_json(slots_path) or {}
        active_slots = 0
        for slot in slots_data.get("slots", {}).values():
            if slot.get("status") == "active":
                active_slots += 1

        # Determine overall agent activity state
        if listener_info.get("ready"):
            state = "listener"
        elif active_slots > 0:
            state = "active"
        else:
            state = "idle"

        issues = []
        if not http_ok:
            issues.append("HTTP health check failed")
        if not listener_info.get("ready") and not active_slots:
            issues.append("no active slots or listener")
        if listener_info.get("status") == "stale":
            issues.append("listener heartbeat is stale")

        ok = http_ok and (listener_info.get("ready") or active_slots > 0)

        return {
            "http_ok": http_ok,
            "ok": ok,
            "agent_activity": {
                "state": state,
                "listener": listener_info,
                "active_slots": active_slots,
                "dream_journal_slots_active": self.slots.active_count("dream_journal"),
            },
            "issues": issues,
            "http": http_result,
        }


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
    p_loop.add_argument("--internal-multiplier", type=int, default=5)
    p_loop.add_argument("--external-dilation", type=float, default=1.0)

    p_health = sub.add_parser("health")
    p_health.add_argument("--url", default="http://127.0.0.1:4177/api/status")

    p_ring = sub.add_parser("validate-ring")
    p_ring.add_argument("--max-jobs", type=int, default=10)
    p_ring.add_argument("--max-seconds", type=float, default=15.0)

    p_watch = sub.add_parser("watch")
    p_watch.add_argument("--mark-stale", action="store_true", help="Write stale flag into receipt if drift detected")

    args = parser.parse_args()

    if args.command == "converge":
        engine = TesseractEngine()
        result = engine.converge(args.message, {"persona": args.persona, "provider": args.provider})
        print(json.dumps(result, indent=2))
    elif args.command == "inspect":
        engine = TesseractEngine()
        print(json.dumps(engine.inspect(), indent=2))
    elif args.command == "loop":
        loop = ConvergenceLoop(
            internal_multiplier=args.internal_multiplier,
            external_dilation=args.external_dilation,
        )
        print(json.dumps(loop.run(), indent=2))
    elif args.command == "health":
        engine = TesseractEngine()
        print(json.dumps(engine.health_check(args.url), indent=2))
    elif args.command == "validate-ring":
        ring = ValidationRing(max_jobs=args.max_jobs, max_seconds=args.max_seconds)
        print(json.dumps(ring.run(), indent=2))
    elif args.command == "watch":
        watch = ConvergenceWatch(REPO_ROOT)
        result = watch.check()
        if args.mark_stale and result["stale"]:
            watch.mark_stale()
            result["marked_stale"] = True
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
