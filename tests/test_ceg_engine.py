"""Tests for CEG Engine v0.3 — issue #388"""
import pytest
from src.ceg_engine import (
    CEG, CEGNode, CEGEdge, NodeType, ResourceKind, EdgeType,
    ExecutionContract, PCSF, TimeDilationField, HotSwapRegistry,
    AAPFTrace, CEGExecutor, SystemState, SwapTrigger, build_provider_graph,
)

PROVIDERS = {
    "claude":  {"latency_ms": 800,  "cost": 0.003, "health": 1.0},
    "gemini":  {"latency_ms": 600,  "cost": 0.001, "health": 0.9},
    "ollama":  {"latency_ms": 2000, "cost": 0.000, "health": 0.7},
    "broken":  {"latency_ms": 500,  "cost": 0.002, "health": 0.0},
}


# ── CEG graph ────────────────────────────────────────────────────────────────

def test_ceg_add_and_get_node():
    g = CEG()
    n = CEGNode(id="a", node_type=NodeType.RESOURCE, kind=ResourceKind.LLM, health=1.0)
    g.add_node(n)
    assert g.get_node("a") is n

def test_ceg_remove_node_cleans_edges():
    g = CEG()
    a = CEGNode(id="a")
    b = CEGNode(id="b")
    g.add_node(a); g.add_node(b)
    g.add_edge(CEGEdge(source="a", target="b", edge_type=EdgeType.REQUIRES))
    g.remove_node("a")
    assert g.get_node("a") is None
    assert g.neighbors("a") == []

def test_ceg_neighbors_filtered_by_edge_type():
    g = CEG()
    g.add_node(CEGNode(id="a"))
    g.add_node(CEGNode(id="b"))
    g.add_node(CEGNode(id="c"))
    g.add_edge(CEGEdge(source="a", target="b", edge_type=EdgeType.REQUIRES))
    g.add_edge(CEGEdge(source="a", target="c", edge_type=EdgeType.BLOCKS))
    assert len(g.neighbors("a", EdgeType.REQUIRES)) == 1
    assert len(g.neighbors("a", EdgeType.BLOCKS)) == 1
    assert len(g.neighbors("a")) == 2

def test_build_provider_graph():
    g = build_provider_graph(PROVIDERS)
    nodes = g.resource_nodes()
    assert len(nodes) == 4
    ids = {n.id for n in nodes}
    assert "claude" in ids and "broken" in ids


# ── ExecutionContract ────────────────────────────────────────────────────────

def test_contract_from_message_quick():
    c = ExecutionContract.from_message("quick answer please")
    assert c.max_cost <= 0.05
    assert c.max_latency_ms <= 3000

def test_contract_from_message_default():
    c = ExecutionContract.from_message("tell me about the project")
    assert c.max_cost > 0.05

def test_contract_overrides():
    c = ExecutionContract.from_message("quick", max_cost=0.10)
    assert c.max_cost == 0.10


# ── PCSF ─────────────────────────────────────────────────────────────────────

def test_pcsf_selects_feasible_node():
    g = build_provider_graph(PROVIDERS)
    pcsf = PCSF()
    contract = ExecutionContract(intent="test", max_cost=0.01, max_latency_ms=5000)
    path = pcsf.select(g, contract)
    assert path.feasible
    assert len(path.nodes) == 1
    assert path.nodes[0].id != "broken"

def test_pcsf_excludes_unhealthy():
    g = build_provider_graph({"dead": {"latency_ms": 100, "cost": 0.0, "health": 0.0}})
    pcsf = PCSF()
    contract = ExecutionContract(intent="test")
    path = pcsf.select(g, contract)
    assert not path.feasible

def test_pcsf_excludes_over_budget():
    g = build_provider_graph({"expensive": {"latency_ms": 100, "cost": 0.5, "health": 1.0}})
    pcsf = PCSF()
    contract = ExecutionContract(intent="test", max_cost=0.001)
    path = pcsf.select(g, contract)
    assert not path.feasible

def test_pcsf_excludes_forbidden():
    g = build_provider_graph(PROVIDERS)
    pcsf = PCSF()
    ids = [n.id for n in g.resource_nodes()]
    contract = ExecutionContract(intent="test", forbidden_resources=ids)
    path = pcsf.select(g, contract)
    assert not path.feasible

def test_pcsf_prefers_low_cost():
    g = build_provider_graph({
        "cheap": {"latency_ms": 700, "cost": 0.0001, "health": 1.0},
        "pricey": {"latency_ms": 700, "cost": 0.01,   "health": 1.0},
    })
    pcsf = PCSF()
    contract = ExecutionContract(intent="test")
    path = pcsf.select(g, contract)
    assert path.nodes[0].id == "cheap"


# ── TimeDilationField ─────────────────────────────────────────────────────────

def test_dilation_high_uncertainty_slows():
    df = TimeDilationField()
    node = CEGNode(health=1.0)
    d_high = df.compute(node, uncertainty=0.9, cost_pressure=0.5, confidence=0.1)
    d_low  = df.compute(node, uncertainty=0.1, cost_pressure=0.5, confidence=0.9)
    assert d_high > d_low

def test_dilation_bounded():
    df = TimeDilationField()
    node = CEGNode(health=0.01)
    d = df.compute(node, uncertainty=1.0, cost_pressure=1.0, confidence=0.0)
    assert 0.1 <= d <= 5.0

def test_dilation_updates_node_field():
    df = TimeDilationField()
    node = CEGNode(health=1.0)
    df.compute(node, uncertainty=0.5, cost_pressure=0.5, confidence=0.5)
    assert node.dilation != 1.0  # was updated

def test_dilation_scaled_cost():
    df = TimeDilationField()
    node = CEGNode(health=1.0)
    node.dilation = 2.0
    assert df.scaled_cost(0.5, node) == pytest.approx(1.0)


# ── HotSwapRegistry ──────────────────────────────────────────────────────────

def test_swap_replaces_node():
    g = build_provider_graph({"old": {"latency_ms": 100, "cost": 0.1, "health": 0.1}})
    trace = AAPFTrace()
    swapper = HotSwapRegistry(g, trace)
    new = CEGNode(id="new", node_type=NodeType.RESOURCE, kind=ResourceKind.LLM,
                  cost_per_call=0.001, latency_ms=500, health=0.95)
    evt = swapper.swap("old", new, SwapTrigger.CAPABILITY_DEGRADATION)
    assert evt.success
    assert g.get_node("old") is None
    assert g.get_node("new") is not None

def test_swap_nonexistent_node_fails_gracefully():
    g = CEG()
    trace = AAPFTrace()
    swapper = HotSwapRegistry(g, trace)
    new = CEGNode(id="x")
    evt = swapper.swap("ghost", new, SwapTrigger.LATENCY_VIOLATION)
    assert not evt.success

def test_rollback_restores_old_node():
    g = build_provider_graph({"old": {"latency_ms": 100, "cost": 0.1, "health": 0.2}})
    trace = AAPFTrace()
    swapper = HotSwapRegistry(g, trace)
    new = CEGNode(id="new", node_type=NodeType.RESOURCE, kind=ResourceKind.LLM, health=0.9)
    swapper.swap("old", new, SwapTrigger.COST_SPIKE)
    ok = swapper.rollback("new")
    assert ok
    assert g.get_node("old") is not None
    assert g.get_node("new") is None

def test_swap_trigger_detection_health():
    g = build_provider_graph({"sick": {"latency_ms": 100, "cost": 0.001, "health": 0.1}})
    trace = AAPFTrace()
    swapper = HotSwapRegistry(g, trace)
    node = g.get_node("sick")
    contract = ExecutionContract(intent="test")
    trigger = swapper.check_triggers(node, contract)
    assert trigger == SwapTrigger.CAPABILITY_DEGRADATION

def test_swap_trigger_detection_latency():
    g = build_provider_graph({"slow": {"latency_ms": 100, "cost": 0.001, "health": 1.0}})
    trace = AAPFTrace()
    swapper = HotSwapRegistry(g, trace)
    node = g.get_node("slow")
    contract = ExecutionContract(intent="test")
    trigger = swapper.check_triggers(node, contract, observed_latency_ms=9000)
    assert trigger == SwapTrigger.LATENCY_VIOLATION


# ── AAPFTrace ─────────────────────────────────────────────────────────────────

def test_trace_emit_returns_id():
    t = AAPFTrace()
    eid = t.emit("test_event", {"key": "val"})
    assert isinstance(eid, str) and len(eid) > 0

def test_trace_replay_full():
    t = AAPFTrace()
    t.emit("e1", {})
    t.emit("e2", {})
    events = t.replay()
    assert len(events) == 2

def test_trace_causal_chain():
    t = AAPFTrace()
    root = t.emit("root", {})
    child = t.emit("child", {}, causal_parent=root)
    leaf = t.emit("leaf", {}, causal_parent=child)
    chain = t.causal_chain(leaf)
    assert [e["id"] for e in chain] == [root, child, leaf]


# ── CEGExecutor ───────────────────────────────────────────────────────────────

def test_executor_runs_single_step():
    g = build_provider_graph({"claude": {"latency_ms": 500, "cost": 0.003, "health": 1.0}})
    executor = CEGExecutor(graph=g)
    contract = ExecutionContract(intent="hello")
    calls = []
    def step_fn(node, c):
        calls.append(node.id)
        return {"reply": "hi", "done": True}
    result = executor.run(contract, step_fn)
    assert result["steps"] == 1
    assert calls == ["claude"]

def test_executor_no_feasible_path():
    g = build_provider_graph({"dead": {"latency_ms": 100, "cost": 0.0, "health": 0.0}})
    executor = CEGExecutor(graph=g)
    contract = ExecutionContract(intent="test")
    result = executor.run(contract, lambda n, c: {"done": True})
    assert "error" in result

def test_executor_emits_aapf_events():
    g = build_provider_graph({"claude": {"latency_ms": 500, "cost": 0.003, "health": 1.0}})
    trace = AAPFTrace()
    executor = CEGExecutor(graph=g, trace=trace)
    contract = ExecutionContract(intent="trace test")
    executor.run(contract, lambda n, c: {"done": True})
    types = {e["type"] for e in trace.replay()}
    assert "execution_start" in types
    assert "step_done" in types
    assert "execution_complete" in types


# ── SystemState ───────────────────────────────────────────────────────────────

def test_system_state_transition():
    g = build_provider_graph({"claude": {"latency_ms": 500, "cost": 0.003, "health": 1.0}})
    state = SystemState(graph=g)
    evt = {"type": "step_done", "ts": "2026-01-01T00:00:00Z",
           "data": {"node_id": "claude", "elapsed_ms": 412.0}}
    state2 = state.transition(evt)
    assert "claude" in state2.resource_state
    assert state2.resource_state["claude"]["elapsed_ms"] == 412.0

def test_system_state_non_step_event_is_noop():
    g = CEG()
    state = SystemState(graph=g)
    state2 = state.transition({"type": "swap", "data": {}})
    assert state2.resource_state == {}
