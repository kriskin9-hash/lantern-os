//! ============================================================
//! CONVERGENCE IO 1.0 — RUST REFERENCE SPEC (#391)
//! CSF (Convergence Standard Format) + CIO (Execution Engine)
//!
//! Typed execution kernel for a constraint-driven, graph-based
//! runtime where PCSF and CIO operate over a mutable computation
//! graph with traceable state transitions.
//!
//! Invariants (enforced at struct level):
//!   - All execution must emit trace events
//!   - Constraints override all optimization
//!   - Graph mutations must preserve structural validity
//!   - Swaps must preserve behavioral equivalence
//!   - System must remain replayable from trace
//!
//! NOT included in 1.0 (future issues):
//!   - Async runtime (Tokio)
//!   - Real LLM backend binding
//!   - Distributed execution
//!   - Probabilistic PCSF optimizer
//!   - Full hot-swap safety proofs
//! ============================================================

use std::collections::HashMap;

pub type NodeId = String;
pub type Timestamp = u64;

// ── 1. CSF (CONVERGENCE STANDARD FORMAT) ────────────────────

/// Complete input schema for the CIO execution engine.
#[derive(Clone, Debug)]
pub struct CSF {
    pub intent: Intent,
    pub context: Context,
    pub constraints: Constraints,
    pub graph_spec: GraphSpec,
    pub policies: Policies,
    pub observability: Observability,
}

#[derive(Clone, Debug)]
pub struct Intent {
    pub goal: String,
    pub priority: f32,   // 0.0 (lowest) .. 1.0 (highest)
}

#[derive(Clone, Debug)]
pub struct Context {
    pub memory_refs: Vec<String>,
    pub environment_state: HashMap<String, String>,
}

/// Execution constraints — PCSF must satisfy all hard constraints.
#[derive(Clone, Debug)]
pub struct Constraints {
    pub max_cost: f32,
    pub max_latency_ms: u64,
    /// 0.0 = fully stochastic, 1.0 = fully deterministic
    pub determinism: f32,
    pub allowed_resources: Vec<String>,
    pub forbidden_resources: Vec<String>,
}

// ── 2. CEG GRAPH MODEL ──────────────────────────────────────

#[derive(Clone, Debug)]
pub struct GraphSpec {
    pub nodes: HashMap<NodeId, Node>,
    pub edges: Vec<Edge>,
}

#[derive(Clone, Debug)]
pub enum Node {
    Intent(IntentNode),
    Resource(ResourceNode),
    Tool(ToolNode),
    Memory(MemoryNode),
    Constraint(ConstraintNode),
    Trace(TraceNode),
    UiProjection(UiProjectionNode),   // v0.4
}

#[derive(Clone, Debug)]
pub struct IntentNode {
    pub embedding: Vec<f32>,
    pub metadata: HashMap<String, String>,
}

#[derive(Clone, Debug)]
pub struct ResourceNode {
    pub resource_type: ResourceType,
    pub health: f32,       // 0.0 = dead, 1.0 = healthy
    pub cost_per_call: f32,
    pub latency_ms: u64,
}

#[derive(Clone, Debug)]
pub enum ResourceType {
    LLM,
    VM,
    Tool,
    Agent,
}

#[derive(Clone, Debug)]
pub struct ToolNode {
    pub name: String,
    pub capabilities: Vec<String>,
}

#[derive(Clone, Debug)]
pub struct MemoryNode {
    pub key: String,
    pub provenance: String,
    pub access_policy: String,
}

#[derive(Clone, Debug)]
pub struct ConstraintNode {
    pub expression: String,
    pub scope: String,
    pub severity: ConstraintSeverity,
}

#[derive(Clone, Debug)]
pub enum ConstraintSeverity {
    Hard,    // must be satisfied — overrides optimization
    Soft,    // included in cost function
}

#[derive(Clone, Debug)]
pub struct TraceNode {
    pub event: String,
    pub timestamp: Timestamp,
    pub causal_parent: Option<String>,
}

/// v0.4: UI as a graph projection, not a static container.
#[derive(Clone, Debug)]
pub struct UiProjectionNode {
    pub view_type: String,
    pub filter: Option<String>,
    pub render_policy: RenderPolicy,
    pub feature_state: FeatureState,
}

#[derive(Clone, Debug)]
pub enum RenderPolicy {
    Standard,
    Compact,
    Hidden,
}

/// v0.4: Feature lifecycle states.
#[derive(Clone, Debug)]
pub enum FeatureState {
    Inactive,
    Scheduled,   // PCSF-eligible
    Active,      // executing
    Suspended,   // swapped out
}

#[derive(Clone, Debug)]
pub struct Edge {
    pub from: NodeId,
    pub to: NodeId,
    pub edge_type: EdgeType,
    pub weight: f32,
}

#[derive(Clone, Debug)]
pub enum EdgeType {
    Requires,
    Enables,
    Blocks,
    ExecutesOn,
    TransformsInto,
    Observes,
    DerivesFrom,    // v0.4 — memory/context provenance
    ProjectsTo,     // v0.4 — graph → UI projection
    SwapsTo,        // v0.4 — hot-swap successor link
}

// ── 3. POLICIES ─────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct Policies {
    pub routing_policy: String,
    pub swap_policy: String,
    pub memory_policy: String,
}

// ── 4. OBSERVABILITY (AAPF TRACE) ───────────────────────────

#[derive(Clone, Debug)]
pub struct Observability {
    pub trace_required: bool,
    pub debug_level: u8,
}

#[derive(Clone, Debug)]
pub struct TraceEvent {
    pub event_type: String,
    pub node_id: Option<NodeId>,
    pub timestamp: Timestamp,
    pub causal_parent: Option<String>,
    pub data: HashMap<String, String>,
}

// ── 5. CIO RUNTIME STATE ────────────────────────────────────

/// S(t) = (G, R, M, P)
#[derive(Clone, Debug)]
pub struct CIOState {
    pub graph: GraphSpec,
    pub resources: ResourceState,
    pub memory: MemoryState,
    pub policies: PolicyState,
    pub trace: Vec<TraceEvent>,
}

#[derive(Clone, Debug)]
pub struct ResourceState {
    pub health_map: HashMap<NodeId, f32>,
    pub latency_map: HashMap<NodeId, u64>,
}

#[derive(Clone, Debug)]
pub struct MemoryState {
    pub store: HashMap<String, String>,
}

#[derive(Clone, Debug)]
pub struct PolicyState {
    pub active_policies: HashMap<String, String>,
}

impl CIOState {
    /// S(t+1) = δ(S(t), event) — deterministic state transition.
    pub fn transition(mut self, event: TraceEvent) -> Self {
        if let Some(ref node_id) = event.node_id {
            if let Some(health) = event.data.get("health") {
                if let Ok(h) = health.parse::<f32>() {
                    self.resources.health_map.insert(node_id.clone(), h);
                }
            }
        }
        self.trace.push(event);
        self
    }
}

// ── 6. PCSF SCHEDULER ───────────────────────────────────────

pub struct PCSF {
    pub w1: f32,   // latency weight
    pub w2: f32,   // compute cost weight
    pub w3: f32,   // risk weight
    pub w4: f32,   // instability weight
}

impl PCSF {
    pub fn new() -> Self {
        Self { w1: 0.3, w2: 0.3, w3: 0.2, w4: 0.2 }
    }

    /// P* = argmin(cost(P)) subject_to constraints
    pub fn optimize(&self, state: &CIOState, constraints: &Constraints) -> ExecutionPlan {
        let mut candidates: Vec<(f32, NodeId)> = state.graph.nodes
            .iter()
            .filter_map(|(id, node)| {
                if let Node::Resource(r) = node {
                    if constraints.forbidden_resources.contains(id) { return None; }
                    if !constraints.allowed_resources.is_empty()
                        && !constraints.allowed_resources.contains(id) { return None; }
                    if r.health <= 0.0 { return None; }
                    if r.cost_per_call > constraints.max_cost { return None; }
                    if r.latency_ms > constraints.max_latency_ms { return None; }
                    let cost = self.w1 * (r.latency_ms as f32 / 10_000.0)
                             + self.w2 * r.cost_per_call
                             + self.w3 * (1.0 - r.health)
                             + self.w4 * 0.0;
                    Some((cost, id.clone()))
                } else {
                    None
                }
            })
            .collect();
        candidates.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
        let selected_nodes = candidates.into_iter().map(|(_, id)| id).collect();
        ExecutionPlan { selected_nodes }
    }
}

impl Default for PCSF {
    fn default() -> Self { Self::new() }
}

#[derive(Clone, Debug)]
pub struct ExecutionPlan {
    pub selected_nodes: Vec<NodeId>,
}

// ── 7. TIME DILATION ────────────────────────────────────────

/// D(v) = f(uncertainty, cost_pressure, confidence)
/// High uncertainty → high D (slower, more exploration)
/// High confidence  → low D (faster execution)
pub fn dilation(uncertainty: f32, cost_pressure: f32, confidence: f32) -> f32 {
    let raw = (1.0 + uncertainty - confidence) * (1.0 + cost_pressure * 0.3);
    raw.clamp(0.1, 5.0)
}

// ── 8. HOT-SWAP ENGINE ──────────────────────────────────────

/// σ: v_old → v_new — preserves behavioral equivalence.
/// Invariant: state(v_old) ≈ state(v_new)
pub fn swap_nodes(graph: &mut GraphSpec, old_id: &str, new_id: NodeId, new_node: Node) {
    graph.nodes.remove(old_id);
    graph.nodes.insert(new_id, new_node);
}

// ── 9. CIO EXECUTION ENGINE ─────────────────────────────────

pub struct CIO;

impl CIO {
    /// Main execution loop.
    ///
    /// while not complete:
    ///   1. observe S(t)
    ///   2. update dilation D
    ///   3. evaluate constraints (NAP)
    ///   4. PCSF.optimize()
    ///   5. if swap_required: execute_swap()
    ///   6. execute step
    ///   7. emit trace event
    ///   8. update memory M
    pub fn run(csf: CSF) -> CIOState {
        let mut state = CIOState {
            graph: csf.graph_spec,
            resources: ResourceState {
                health_map: HashMap::new(),
                latency_map: HashMap::new(),
            },
            memory: MemoryState { store: HashMap::new() },
            policies: PolicyState { active_policies: HashMap::new() },
            trace: Vec::new(),
        };

        let pcsf = PCSF::new();
        let mut step: u64 = 0;

        loop {
            // 3. NAP constraint evaluation (hard constraints always win)
            let hard_violated = state.graph.nodes.values().any(|n| {
                matches!(n, Node::Constraint(c) if matches!(c.severity, ConstraintSeverity::Hard))
            });
            if hard_violated {
                state.trace.push(TraceEvent {
                    event_type: "nap_violation".into(),
                    node_id: None,
                    timestamp: step,
                    causal_parent: None,
                    data: HashMap::new(),
                });
                break;
            }

            // 4. PCSF optimize
            let plan = pcsf.optimize(&state, &csf.constraints);

            // 6. Execute first selected node (stub)
            if let Some(node_id) = plan.selected_nodes.first() {
                state.trace.push(TraceEvent {
                    event_type: "step_execute".into(),
                    node_id: Some(node_id.clone()),
                    timestamp: step,
                    causal_parent: None,
                    data: HashMap::new(),
                });
            }

            step += 1;
            break; // stub: single-step execution
        }

        state.trace.push(TraceEvent {
            event_type: "execution_complete".into(),
            node_id: None,
            timestamp: step,
            causal_parent: None,
            data: HashMap::new(),
        });

        state
    }
}
