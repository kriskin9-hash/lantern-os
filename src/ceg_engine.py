"""
CEG Engine — Convergence Execution Graph (v0.3)

Implements the formal execution substrate from issue #388:
  G = (V, E, D, τ, S, H)

Modules:
  - Node taxonomy (Intent, Resource, Constraint, Authority, Memory, Trace)
  - CEG graph engine with typed edges
  - ExecutionContract compiler
  - PCSF optimizer (cost-minimizing path selection + continuous reopt)
  - TimeDilationField (per-node D(v) = f(uncertainty, cost_pressure, confidence))
  - HotSwapRegistry (σ: v_old → v_new with rollback and AAPF trace events)
  - AAPFTrace (causal execution log — fully reconstructable)
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
AAPF_LOG = REPO_ROOT / "data" / "agent-fleet" / "ceg-aapf.jsonl"


# ── Node taxonomy ────────────────────────────────────────────────────────────

class NodeType(str, Enum):
    INTENT      = "intent"
    RESOURCE    = "resource"
    CONSTRAINT  = "constraint"
    AUTHORITY   = "authority"
    MEMORY      = "memory"
    TRACE       = "trace"


class ResourceKind(str, Enum):
    LLM   = "LLM"
    VM    = "VM"
    TOOL  = "TOOL"
    AGENT = "AGENT"


class EdgeType(str, Enum):
    REQUIRES    = "requires"
    ENABLES     = "enables"
    BLOCKS      = "blocks"
    EXECUTES_ON = "executes_on"


@dataclass
class CEGNode:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    node_type: NodeType = NodeType.RESOURCE
    metadata: Dict[str, Any] = field(default_factory=dict)

    # IntentNode fields
    embedding: Optional[List[float]] = None

    # ResourceNode fields
    kind: Optional[ResourceKind] = None
    capabilities: Set[str] = field(default_factory=set)
    cost_per_call: float = 0.0
    latency_ms: float = 0.0
    health: float = 1.0          # 0.0 = dead, 1.0 = healthy

    # ConstraintNode fields
    predicate: Optional[Callable[[Any], bool]] = None
    scope: str = "global"
    severity: str = "hard"       # "hard" | "soft"

    # AuthorityNode fields
    policy_set: List[str] = field(default_factory=list)
    identity_scope: str = ""

    # MemoryNode fields
    content: Optional[Any] = None
    provenance: str = ""
    access_policy: str = "open"

    # Runtime dilation field (set by TimeDilationField)
    dilation: float = 1.0

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CEGNode) and self.id == other.id


@dataclass
class CEGEdge:
    source: str      # node id
    target: str      # node id
    edge_type: EdgeType = EdgeType.REQUIRES
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── Execution Contract ───────────────────────────────────────────────────────

@dataclass
class ExecutionContract:
    intent: str
    max_cost: float = float("inf")
    max_latency_ms: int = 10_000
    determinism: float = 0.8       # 0.0 = fully stochastic, 1.0 = deterministic
    memory_policy: str = "persist"
    external_io_policy: str = "allow"
    allowed_resources: List[str] = field(default_factory=list)
    forbidden_resources: List[str] = field(default_factory=list)

    @classmethod
    def from_message(cls, message: str, **overrides: Any) -> "ExecutionContract":
        """Compile a natural-language message into an ExecutionContract."""
        low = message.lower()
        # Heuristic cost/latency limits based on message signals
        max_cost = 0.05 if any(w in low for w in ("quick", "fast", "brief")) else 0.20
        max_latency = 3000 if any(w in low for w in ("quick", "fast", "brief")) else 10_000
        determinism = 0.9 if any(w in low for w in ("exact", "precise", "deterministic")) else 0.7
        return cls(
            intent=message,
            max_cost=overrides.get("max_cost", max_cost),
            max_latency_ms=overrides.get("max_latency_ms", max_latency),
            determinism=overrides.get("determinism", determinism),
            **{k: v for k, v in overrides.items() if k not in ("max_cost", "max_latency_ms", "determinism")},
        )


# ── Convergence Execution Graph ──────────────────────────────────────────────

class CEG:
    """
    G = (V, E, D, τ, S, H)
    Immutable node/edge store with thread-safe mutation via add_node/add_edge.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, CEGNode] = {}
        self._edges: List[CEGEdge] = []
        self._lock = threading.RLock()

    def add_node(self, node: CEGNode) -> CEGNode:
        with self._lock:
            self._nodes[node.id] = node
        return node

    def add_edge(self, edge: CEGEdge) -> None:
        with self._lock:
            self._edges.append(edge)

    def get_node(self, node_id: str) -> Optional[CEGNode]:
        return self._nodes.get(node_id)

    def neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[CEGNode]:
        with self._lock:
            result = []
            for e in self._edges:
                if e.source == node_id and (edge_type is None or e.edge_type == edge_type):
                    n = self._nodes.get(e.target)
                    if n:
                        result.append(n)
            return result

    def resource_nodes(self) -> List[CEGNode]:
        with self._lock:
            return [n for n in self._nodes.values() if n.node_type == NodeType.RESOURCE]

    def constraint_nodes(self) -> List[CEGNode]:
        with self._lock:
            return [n for n in self._nodes.values() if n.node_type == NodeType.CONSTRAINT and n.severity == "hard"]

    def remove_node(self, node_id: str) -> None:
        with self._lock:
            self._nodes.pop(node_id, None)
            self._edges = [e for e in self._edges if e.source != node_id and e.target != node_id]

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "nodes": [{"id": n.id, "type": n.node_type, "health": n.health, "dilation": n.dilation}
                          for n in self._nodes.values()],
                "edges": [{"src": e.source, "tgt": e.target, "type": e.edge_type} for e in self._edges],
            }


# ── Time Dilation Field ──────────────────────────────────────────────────────

class TimeDilationField:
    """
    D(v) = f(uncertainty, cost_pressure, confidence)
    cost(e) *= D(source_node)

    High uncertainty  → D > 1 (slow region, explore more deeply)
    High confidence   → D < 1 (fast region)
    """

    def compute(self, node: CEGNode, uncertainty: float = 0.5,
                cost_pressure: float = 0.5, confidence: float = 0.5) -> float:
        health_factor = max(0.1, 1.0 - (1.0 - node.health) * 0.5)
        raw = (1.0 + uncertainty - confidence) * (1.0 + cost_pressure * 0.3) / health_factor
        dilation = max(0.1, min(5.0, raw))
        node.dilation = round(dilation, 3)
        return node.dilation

    def update_graph(self, graph: CEG, uncertainty: float = 0.5,
                     cost_pressure: float = 0.5) -> None:
        for node in graph.resource_nodes():
            confidence = node.health
            self.compute(node, uncertainty, cost_pressure, confidence)

    def scaled_cost(self, base_cost: float, node: CEGNode) -> float:
        return base_cost * node.dilation


# ── PCSF — Priority Constraint Satisfaction Framework ────────────────────────

@dataclass
class ExecutionPath:
    nodes: List[CEGNode]
    cost: float = 0.0
    feasible: bool = True
    reason: str = ""


class PCSF:
    """
    P* = argmin(cost(P)) subject_to constraints

    Cost(P) = w1*latency + w2*compute_cost + w3*risk + w4*instability

    Continuously re-optimizes: P(t+Δt) = reoptimize(P(t), G, S, D)
    """

    def __init__(self, w1: float = 0.3, w2: float = 0.3,
                 w3: float = 0.2, w4: float = 0.2) -> None:
        self.w1, self.w2, self.w3, self.w4 = w1, w2, w3, w4
        self._last_path: Optional[ExecutionPath] = None
        self._lock = threading.Lock()

    def cost(self, node: CEGNode) -> float:
        latency   = node.latency_ms / 10_000
        compute   = node.cost_per_call
        risk      = max(0.0, 1.0 - node.health)
        instab    = max(0.0, node.dilation - 1.0) / 4.0
        raw = (self.w1 * latency + self.w2 * compute +
               self.w3 * risk   + self.w4 * instab)
        return round(raw * node.dilation, 6)

    def _satisfies(self, node: CEGNode, contract: ExecutionContract) -> Tuple[bool, str]:
        if contract.forbidden_resources and node.id in contract.forbidden_resources:
            return False, f"node {node.id} forbidden"
        if contract.allowed_resources and node.id not in contract.allowed_resources:
            return False, f"node {node.id} not in allowed list"
        if node.health <= 0.0:
            return False, f"node {node.id} unhealthy"
        if node.cost_per_call > contract.max_cost:
            return False, f"cost {node.cost_per_call} > max {contract.max_cost}"
        if node.latency_ms > contract.max_latency_ms:
            return False, f"latency {node.latency_ms}ms > max {contract.max_latency_ms}ms"
        return True, ""

    def select(self, graph: CEG, contract: ExecutionContract) -> ExecutionPath:
        candidates = graph.resource_nodes()
        feasible = []
        for node in candidates:
            ok, reason = self._satisfies(node, contract)
            if ok:
                feasible.append((self.cost(node), node))
        if not feasible:
            return ExecutionPath(nodes=[], cost=float("inf"), feasible=False,
                                 reason="no feasible resource nodes")
        feasible.sort(key=lambda x: x[0])
        best_cost, best_node = feasible[0]
        path = ExecutionPath(nodes=[best_node], cost=best_cost, feasible=True)
        with self._lock:
            self._last_path = path
        return path

    def reoptimize(self, graph: CEG, contract: ExecutionContract,
                   dilation: TimeDilationField, state: Dict[str, Any]) -> ExecutionPath:
        uncertainty = state.get("uncertainty", 0.5)
        cost_pressure = state.get("cost_pressure", 0.5)
        dilation.update_graph(graph, uncertainty, cost_pressure)
        return self.select(graph, contract)


# ── Hot-Swap Registry ────────────────────────────────────────────────────────

class SwapTrigger(str, Enum):
    CAPABILITY_DEGRADATION = "capability_degradation"
    LATENCY_VIOLATION      = "latency_violation"
    COST_SPIKE             = "cost_spike"
    AUTHORITY_REVOCATION   = "authority_revocation"
    IMPROVED_CANDIDATE     = "improved_candidate"


@dataclass
class SwapEvent:
    timestamp: str
    from_node: str
    to_node: str
    trigger: SwapTrigger
    reason: str
    success: bool
    rollback_state: Optional[Dict[str, Any]] = None


class HotSwapRegistry:
    """
    σ: v_old → v_new — runtime node replacement preserving semantic continuity.
    H = { candidate_set, swap_policy, trigger_rules, rollback_state }
    """

    def __init__(self, graph: CEG, trace: "AAPFTrace") -> None:
        self._graph = graph
        self._trace = trace
        self._swap_policy: Dict[str, Any] = {
            "health_threshold": 0.3,
            "latency_threshold_ms": 8_000,
            "cost_spike_factor": 2.0,
        }
        self._rollback: Dict[str, CEGNode] = {}
        self._lock = threading.Lock()

    def check_triggers(self, node: CEGNode, contract: ExecutionContract,
                       observed_latency_ms: float = 0.0) -> Optional[SwapTrigger]:
        p = self._swap_policy
        if node.health < p["health_threshold"]:
            return SwapTrigger.CAPABILITY_DEGRADATION
        if observed_latency_ms > p["latency_threshold_ms"]:
            return SwapTrigger.LATENCY_VIOLATION
        if node.cost_per_call > contract.max_cost * p["cost_spike_factor"]:
            return SwapTrigger.COST_SPIKE
        return None

    def swap(self, old_id: str, new_node: CEGNode,
             trigger: SwapTrigger, reason: str = "") -> SwapEvent:
        with self._lock:
            old = self._graph.get_node(old_id)
            ts = _ts()
            if old is None:
                evt = SwapEvent(ts, old_id, new_node.id, trigger, reason, success=False)
                self._trace.emit("swap", evt.__dict__)
                return evt
            # Save rollback state
            self._rollback[new_node.id] = old
            # Semantic continuity: copy state-bearing fields
            new_node.capabilities = new_node.capabilities or old.capabilities
            new_node.health = max(new_node.health, 0.1)
            # Execute swap
            self._graph.remove_node(old_id)
            self._graph.add_node(new_node)
            evt = SwapEvent(ts, old_id, new_node.id, trigger, reason, success=True,
                            rollback_state={"health": old.health, "cost": old.cost_per_call})
            self._trace.emit("swap", evt.__dict__)
            return evt

    def rollback(self, swapped_node_id: str) -> bool:
        with self._lock:
            original = self._rollback.pop(swapped_node_id, None)
            if original is None:
                return False
            self._graph.remove_node(swapped_node_id)
            self._graph.add_node(original)
            self._trace.emit("rollback", {"node_id": swapped_node_id,
                                          "restored_id": original.id, "ts": _ts()})
            return True


# ── AAPF Trace System ────────────────────────────────────────────────────────

class AAPFTrace:
    """
    Full causal execution graph. All decisions are recorded.
    Invariant: all execution must be reconstructable from trace.
    """

    def __init__(self, log_path: Optional[Path] = None) -> None:
        self._log_path = log_path or AAPF_LOG
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def emit(self, event_type: str, data: Dict[str, Any],
             causal_parent: Optional[str] = None) -> str:
        event_id = str(uuid.uuid4())[:8]
        event: Dict[str, Any] = {
            "id": event_id,
            "type": event_type,
            "ts": _ts(),
            "data": data,
        }
        if causal_parent:
            event["parent"] = causal_parent
        with self._lock:
            self._events.append(event)
            try:
                with open(self._log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
            except OSError:
                pass
        return event_id

    def replay(self, since_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if since_id is None:
                return list(self._events)
            try:
                idx = next(i for i, e in enumerate(self._events) if e["id"] == since_id)
                return list(self._events[idx:])
            except StopIteration:
                return list(self._events)

    def causal_chain(self, leaf_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            chain = []
            current = leaf_id
            event_map = {e["id"]: e for e in self._events}
            while current and current in event_map:
                evt = event_map[current]
                chain.insert(0, evt)
                current = evt.get("parent")
            return chain


# ── CEG Execution Loop ───────────────────────────────────────────────────────

class CEGExecutor:
    """
    Main execution loop:
      while not complete:
          update_dilation(D)
          PCSF.reoptimize(G, S, D)
          if swap_required(H): execute_swap()
          execute_step()
          emit_trace()
    """

    def __init__(self, graph: Optional[CEG] = None,
                 trace: Optional[AAPFTrace] = None) -> None:
        self.graph = graph or CEG()
        self.trace = trace or AAPFTrace()
        self.dilation = TimeDilationField()
        self.pcsf = PCSF()
        self.swapper = HotSwapRegistry(self.graph, self.trace)
        self._state: Dict[str, Any] = {
            "uncertainty": 0.5,
            "cost_pressure": 0.3,
        }

    def run(self, contract: ExecutionContract,
            step_fn: Callable[[CEGNode, ExecutionContract], Dict[str, Any]],
            max_steps: int = 10) -> Dict[str, Any]:
        """
        Execute the contract against the graph using PCSF-selected resources.
        step_fn(node, contract) → {"reply": str, "done": bool, ...}
        """
        root_id = self.trace.emit("execution_start", {
            "intent": contract.intent[:120],
            "max_cost": contract.max_cost,
            "max_latency_ms": contract.max_latency_ms,
        })

        results: List[Dict[str, Any]] = []
        last_id = root_id

        for step in range(max_steps):
            path = self.pcsf.reoptimize(self.graph, contract, self.dilation, self._state)

            if not path.feasible or not path.nodes:
                self.trace.emit("execution_failed", {"reason": path.reason,
                                                      "step": step}, causal_parent=last_id)
                return {"error": f"no feasible path: {path.reason}", "steps": step}

            node = path.nodes[0]
            step_start = time.monotonic()

            step_id = self.trace.emit("step_start", {
                "step": step, "node_id": node.id,
                "node_kind": node.kind, "cost": path.cost,
                "dilation": node.dilation,
            }, causal_parent=last_id)

            try:
                result = step_fn(node, contract)
            except Exception as exc:
                node.health = max(0.0, node.health - 0.2)
                self._state["uncertainty"] = min(1.0, self._state["uncertainty"] + 0.1)
                self.trace.emit("step_error", {"node_id": node.id, "error": str(exc)},
                                causal_parent=step_id)
                continue

            elapsed_ms = (time.monotonic() - step_start) * 1000

            # Check swap triggers after each step
            trigger = self.swapper.check_triggers(node, contract, elapsed_ms)
            if trigger:
                self.trace.emit("swap_triggered", {"node_id": node.id,
                                                    "trigger": trigger}, causal_parent=step_id)
                # Caller can replace nodes in graph before next iteration

            self.trace.emit("step_done", {
                "step": step, "node_id": node.id,
                "elapsed_ms": round(elapsed_ms, 1),
                "done": result.get("done", False),
            }, causal_parent=step_id)

            # Update state from result signals
            if result.get("confidence"):
                self._state["uncertainty"] = max(0.0, 1.0 - result["confidence"])
            if result.get("cost"):
                self._state["cost_pressure"] = min(1.0, result["cost"] / max(contract.max_cost, 0.01))

            results.append(result)
            last_id = step_id

            if result.get("done"):
                break

        self.trace.emit("execution_complete", {
            "steps": len(results),
            "graph": self.graph.snapshot(),
        }, causal_parent=last_id)

        return {"results": results, "steps": len(results),
                "graph_snapshot": self.graph.snapshot()}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _ts() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def build_provider_graph(providers: Dict[str, Dict[str, Any]]) -> CEG:
    """
    Convenience: build a CEG from a provider-cache dict.
    providers = {"claude": {"latency_ms": 800, "cost": 0.003, "health": 1.0}, ...}
    """
    graph = CEG()
    for name, info in providers.items():
        node = CEGNode(
            id=name,
            node_type=NodeType.RESOURCE,
            kind=ResourceKind.LLM,
            capabilities={"chat", "stream"},
            cost_per_call=info.get("cost", 0.01),
            latency_ms=info.get("latency_ms", 1000),
            health=info.get("health", 1.0),
            metadata=info,
        )
        graph.add_node(node)
    return graph


# ── System State Model ───────────────────────────────────────────────────────

@dataclass
class SystemState:
    """S(t) = (G, memory, resource_state, policy_state)"""
    graph: CEG
    memory: Dict[str, Any] = field(default_factory=dict)
    resource_state: Dict[str, Any] = field(default_factory=dict)
    policy_state: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_ts)

    def transition(self, trace_event: Dict[str, Any]) -> "SystemState":
        """S(t+1) = δ(S(t), execution_trace)"""
        new_resource_state = dict(self.resource_state)
        if trace_event.get("type") == "step_done":
            node_id = trace_event.get("data", {}).get("node_id")
            if node_id:
                new_resource_state[node_id] = {
                    "last_used": trace_event.get("ts"),
                    "elapsed_ms": trace_event.get("data", {}).get("elapsed_ms"),
                }
        return SystemState(
            graph=self.graph,
            memory=self.memory,
            resource_state=new_resource_state,
            policy_state=self.policy_state,
            timestamp=_ts(),
        )
