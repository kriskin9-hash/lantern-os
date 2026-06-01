#!/usr/bin/env python3
"""
Bayesian world model for tracking the state of flourishing.

Maintains probabilistic beliefs about outcomes across all domains and scopes.
Updates beliefs when new measurements arrive. Computes counterfactuals
("what would happen if we did X"). Identifies which interventions produce
the most flourishing.

This is a best-effort model. It is always wrong in some way. It knows it
is wrong -- uncertainty is a first-class concept, not an afterthought.
Every prediction carries error bars. Every recommendation carries caveats.
The model gets less wrong over time as more measurements arrive.

Limitations (honest accounting):
- Bayesian updating here is simplified. Real-world distributions are
  rarely Gaussian, and our prior selection is naive.
- Counterfactual reasoning is speculative. We estimate what might happen
  based on observed correlations, but correlation is not causation.
- Flourishing metrics are value-laden. The weights assigned to health,
  autonomy, fairness, etc. reflect choices, not objective truths.
  Different ethical frameworks would produce different weights.
- The model cannot observe what it does not measure. Unmeasured dimensions
  of flourishing (joy, meaning, beauty) are invisible to it.
- SQLite persistence is single-writer. Concurrent writes may fail.
"""

import hashlib
import json
import math
import os
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from sensors import Measurement, SensorRegistry


# ---------------------------------------------------------------------------
# SQLite persistence
# ---------------------------------------------------------------------------

_WORLD_DB = os.environ.get("WORLD_MODEL_DB_PATH", "./data/world_model.db")

BELIEF_ACTIVE = "active_belief"
BELIEF_STRONG = "strong_belief"
BELIEF_ACCEPTED_FACT = "accepted_fact"
BELIEF_CHALLENGED = "challenged_fact"
BELIEF_CONTESTED = "contested_belief"
BELIEF_IMMUTABLE_CONSTRAINT = "immutable_constraint"

DEFAULT_CONFIDENCE_FLOOR = 0.05
DEFAULT_HALF_LIFE_DAYS = 365.0
ACCEPTED_FACT_CONFIDENCE = 0.999
STRONG_BELIEF_CONFIDENCE = 0.95
MIN_ACCEPTED_FACT_EVIDENCE = 3


def _init_world_db(db_path: str = _WORLD_DB) -> None:
    """Create tables for beliefs and history if they do not exist."""
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS beliefs (
            entity          TEXT PRIMARY KEY,
            domain          TEXT NOT NULL,
            scope           TEXT NOT NULL,
            prior           REAL NOT NULL,
            posterior        REAL NOT NULL,
            uncertainty     REAL NOT NULL,
            evidence_json   TEXT NOT NULL DEFAULT '[]',
            last_updated    TEXT NOT NULL,
            history_json    TEXT NOT NULL DEFAULT '[]'
        )
    """)

    migrations = {
        "confidence": "REAL",
        "status": "TEXT DEFAULT 'active_belief'",
        "last_reinforced": "TEXT",
        "last_challenged": "TEXT",
        "reinforcement_count": "INTEGER DEFAULT 0",
        "contradiction_count": "INTEGER DEFAULT 0",
        "half_life_days": "REAL DEFAULT 365.0",
        "immutable": "INTEGER DEFAULT 0",
        "confirming_nodes_json": "TEXT NOT NULL DEFAULT '[]'",
    }
    for column, definition in migrations.items():
        try:
            c.execute(f"ALTER TABLE beliefs ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError:
            pass

    c.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            entity          TEXT NOT NULL,
            old_posterior    REAL NOT NULL,
            new_posterior    REAL NOT NULL,
            reason          TEXT NOT NULL,
            measurement_hash TEXT,
            corrected_at    TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS flourishing_configs (
            scope           TEXT PRIMARY KEY,
            components_json TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Belief — a probabilistic claim about the state of something
# ---------------------------------------------------------------------------


@dataclass
class Belief:
    """A probabilistic belief about some entity in the world.

    The model maintains beliefs about everything it has observed.
    Each belief has a prior (what we thought before evidence) and
    a posterior (what we think after evidence). The gap between
    them is informative: large shifts mean the evidence was surprising.

    Beliefs are always uncertain. A belief with uncertainty=0 is a
    red flag -- it means the model is overconfident about something.
    """

    entity: str
    """What this belief is about. A unique identifier like
    'hospital_xyz_diagnostic_accuracy', 'pacific_salmon_population',
    'shelter_cat_adoption_rate'."""

    domain: str
    """The domain: 'healthcare', 'ecology', 'animal_welfare', etc."""

    scope: str
    """What population this applies to."""

    prior: float
    """Belief before evidence. Between 0 and 1, where 0.5 means
    'we have no idea' (maximum entropy)."""

    posterior: float
    """Belief after evidence. Updated via Bayesian rule (simplified)."""

    uncertainty: float
    """How uncertain we are about this belief. 0=certain (never true
    in practice), 1=no idea."""

    confidence: float = 0.5
    """How much live support this belief currently has. Confidence can
    increase with independent reinforcement and erode with time or challenge."""

    status: str = BELIEF_ACTIVE
    """Lifecycle state: active, strong, accepted fact, challenged, or contested."""

    evidence: List[str] = field(default_factory=list)
    """Measurement hashes that informed this belief."""

    last_updated: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    """When this belief was last updated."""

    history: List[dict] = field(default_factory=list)
    """Previous posteriors -- the belief's evolution over time.
    Each entry: {'posterior': float, 'uncertainty': float,
    'updated_at': str, 'evidence_hash': str}."""

    last_reinforced: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    """When confidence was last reinforced by evidence or admitted nodes."""

    last_challenged: Optional[datetime] = None
    """When the belief was last challenged or contradicted."""

    reinforcement_count: int = 0
    contradiction_count: int = 0
    half_life_days: float = DEFAULT_HALF_LIFE_DAYS
    immutable: bool = False
    confirming_nodes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entity": self.entity,
            "domain": self.domain,
            "scope": self.scope,
            "prior": self.prior,
            "posterior": self.posterior,
            "uncertainty": self.uncertainty,
            "confidence": self.confidence,
            "status": self.status,
            "evidence": self.evidence,
            "last_updated": self.last_updated.isoformat(),
            "last_reinforced": self.last_reinforced.isoformat(),
            "last_challenged": (
                self.last_challenged.isoformat()
                if self.last_challenged
                else None
            ),
            "reinforcement_count": self.reinforcement_count,
            "contradiction_count": self.contradiction_count,
            "half_life_days": self.half_life_days,
            "immutable": self.immutable,
            "confirming_nodes": self.confirming_nodes,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Belief":
        updated = d.get("last_updated")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        elif updated is None:
            updated = datetime.now(timezone.utc)
        reinforced = d.get("last_reinforced")
        if isinstance(reinforced, str):
            reinforced = datetime.fromisoformat(reinforced)
        elif reinforced is None:
            reinforced = updated
        challenged = d.get("last_challenged")
        if isinstance(challenged, str):
            challenged = datetime.fromisoformat(challenged)
        elif challenged is None:
            challenged = None
        return cls(
            entity=d["entity"],
            domain=d["domain"],
            scope=d["scope"],
            prior=d["prior"],
            posterior=d["posterior"],
            uncertainty=d["uncertainty"],
            confidence=d.get("confidence", round(1.0 - d["uncertainty"], 4)),
            status=d.get("status", BELIEF_ACTIVE),
            evidence=d.get("evidence", []),
            last_updated=updated,
            history=d.get("history", []),
            last_reinforced=reinforced,
            last_challenged=challenged,
            reinforcement_count=d.get("reinforcement_count", 0),
            contradiction_count=d.get("contradiction_count", 0),
            half_life_days=d.get("half_life_days", DEFAULT_HALF_LIFE_DAYS),
            immutable=d.get("immutable", False),
            confirming_nodes=d.get("confirming_nodes", []),
        )


# ---------------------------------------------------------------------------
# Intervention — a possible action and its predicted effect
# ---------------------------------------------------------------------------


@dataclass
class Intervention:
    """A predicted intervention: what would happen if we did X?

    Every intervention prediction is speculative. The model estimates
    effects based on observed correlations, but it cannot run experiments.
    Side effects are particularly uncertain -- second-order consequences
    are notoriously hard to predict.
    """

    action: str
    """What would be done. Be specific: 'increase_screening_frequency',
    not 'improve_healthcare'."""

    target: str
    """What entity this intervention affects."""

    predicted_effect: float
    """Expected change in the target's flourishing score.
    Positive = improvement, negative = harm. This is a point estimate;
    the actual effect could be anywhere in the uncertainty range."""

    uncertainty: float
    """How uncertain we are about predicted_effect. High uncertainty
    means the intervention might help a lot, or might do nothing,
    or might even cause harm."""

    side_effects: List[dict] = field(default_factory=list)
    """Predicted second-order effects, each with its own uncertainty.
    Format: [{'target': str, 'effect': float, 'uncertainty': float,
    'description': str}]. These are even more speculative than the
    primary predicted_effect."""

    confidence: float = 0.5
    """How much evidence supports this prediction. 0=no evidence,
    1=strong evidence. Most interventions are in the 0.2-0.6 range
    because we rarely have strong causal evidence."""

    counterfactual: str = "unknown"
    """What happens if we DON'T do this. Often the status quo is also
    bad, and doing nothing is itself a choice with consequences."""

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "target": self.target,
            "predicted_effect": self.predicted_effect,
            "uncertainty": self.uncertainty,
            "side_effects": self.side_effects,
            "confidence": self.confidence,
            "counterfactual": self.counterfactual,
        }


# ---------------------------------------------------------------------------
# Prediction — the result of predict()
# ---------------------------------------------------------------------------


@dataclass
class Prediction:
    """The model's prediction about what an intervention would do.

    Always includes uncertainty bounds and caveats. A prediction
    without caveats is lying about how much it knows.
    """

    intervention: Intervention
    current_belief: Belief
    predicted_belief: dict  # what the belief would look like after
    confidence: float
    caveats: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "intervention": self.intervention.to_dict(),
            "current_belief": self.current_belief.to_dict(),
            "predicted_belief": self.predicted_belief,
            "confidence": self.confidence,
            "caveats": self.caveats,
        }


# ---------------------------------------------------------------------------
# FlourishingMetric — defines what "flourishing" means for a scope
# ---------------------------------------------------------------------------


class FlourishingMetric:
    """Defines and computes flourishing for a given scope.

    Flourishing is a weighted combination of components. The components
    and weights differ by scope:

    - For humans: health, autonomy, fairness, opportunity
    - For animals: health, safety, comfort, natural_behavior
    - For ecosystems: biodiversity, stability, resilience

    The weights themselves are beliefs -- they can be updated as the
    model learns what actually correlates with good outcomes. Initial
    weights are equal because we do not have strong evidence for
    preferring one component over another.

    This is explicitly value-laden. Different ethical frameworks
    would produce different components and weights. The model does
    not claim to have the right values -- it claims to be transparent
    about what values it is using.
    """

    # Default component sets by scope category
    DEFAULT_COMPONENTS = {
        "humans": {
            "health": {"weight": 0.25, "uncertainty": 0.3},
            "autonomy": {"weight": 0.25, "uncertainty": 0.3},
            "fairness": {"weight": 0.25, "uncertainty": 0.3},
            "opportunity": {"weight": 0.25, "uncertainty": 0.3},
        },
        "animals": {
            "health": {"weight": 0.25, "uncertainty": 0.3},
            "safety": {"weight": 0.25, "uncertainty": 0.3},
            "comfort": {"weight": 0.25, "uncertainty": 0.3},
            "natural_behavior": {"weight": 0.25, "uncertainty": 0.3},
        },
        "ecosystems": {
            "biodiversity": {"weight": 0.33, "uncertainty": 0.3},
            "stability": {"weight": 0.34, "uncertainty": 0.3},
            "resilience": {"weight": 0.33, "uncertainty": 0.3},
        },
    }

    def __init__(self, scope: str, components: Optional[Dict[str, dict]] = None):
        """
        Parameters
        ----------
        scope : str
            The scope this metric applies to.
        components : dict, optional
            Component definitions. If not provided, defaults are selected
            based on scope prefix (humans/animals/ecosystems).
            Format: {'component_name': {'weight': float, 'uncertainty': float}}
        """
        self.scope = scope

        if components is not None:
            self.components = components
        else:
            # Try to match scope prefix to defaults
            prefix = scope.split(":")[0].lower()
            self.components = dict(
                self.DEFAULT_COMPONENTS.get(prefix, {
                    "wellbeing": {"weight": 0.5, "uncertainty": 0.5},
                    "sustainability": {"weight": 0.5, "uncertainty": 0.5},
                })
            )

    def _find_component_beliefs(
        self, component: str, beliefs: Dict[str, "Belief"]
    ) -> List["Belief"]:
        """Find all beliefs that contribute to a flourishing component.

        Looks for beliefs whose entity key starts with "{scope}:{component}".
        This allows multiple sensors/sources to contribute to the same
        component. When multiple beliefs match, they are all used —
        the aggregate gives more weight to lower-uncertainty beliefs.

        Returns an empty list if no matching beliefs exist.
        """
        prefix = f"{self.scope}:{component}"
        return [
            b for key, b in beliefs.items()
            if key == prefix or key.startswith(prefix + ":")
        ]

    def compute(self, beliefs: Dict[str, "Belief"]) -> Measurement:
        """Compute aggregate flourishing score from component beliefs.

        Each component is looked up by prefix: all beliefs whose key starts
        with "{scope}:{component_name}" contribute, weighted by inverse
        uncertainty. Multiple sensors measuring the same component combine
        naturally -- more certain sources carry more weight.

        Missing components contribute maximum uncertainty.

        Returns a Measurement because flourishing is itself an observation
        with uncertainty, not a known truth.
        """
        total_score = 0.0
        total_weight = 0.0
        total_uncertainty_sq = 0.0
        missing_components = []
        found_components = []

        for name, config in self.components.items():
            weight = config["weight"]
            component_uncertainty = config["uncertainty"]

            matching = self._find_component_beliefs(name, beliefs)

            if matching:
                # Aggregate matching beliefs: weighted average by certainty
                if len(matching) == 1:
                    posterior = matching[0].posterior
                    belief_unc = matching[0].uncertainty
                else:
                    # Multiple sources: weight by inverse uncertainty
                    inv_weights = [
                        1.0 / max(b.uncertainty, 0.01) for b in matching
                    ]
                    total_inv = sum(inv_weights)
                    posterior = sum(
                        b.posterior * w for b, w in zip(matching, inv_weights)
                    ) / total_inv
                    # Best-case uncertainty from independent sources
                    belief_unc = min(b.uncertainty for b in matching)

                total_score += posterior * weight
                combined_unc = math.sqrt(
                    component_uncertainty ** 2 + belief_unc ** 2
                )
                total_uncertainty_sq += (weight * combined_unc) ** 2
                total_weight += weight
                found_components.append(name)
            else:
                # Missing component: assume 0.5 (no information) with
                # maximum uncertainty
                total_score += 0.5 * weight
                total_uncertainty_sq += (weight * 1.0) ** 2
                total_weight += weight
                missing_components.append(name)

        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0.5  # no data

        propagated_uncertainty = math.sqrt(total_uncertainty_sq)
        # Clamp to [0, 1]
        final_uncertainty = min(max(propagated_uncertainty, 0.0), 1.0)

        return Measurement(
            value=round(normalized_score, 4),
            uncertainty=round(final_uncertainty, 4),
            confidence_interval=(
                round(max(normalized_score - propagated_uncertainty, 0.0), 4),
                round(min(normalized_score + propagated_uncertainty, 1.0), 4),
            ),
            confounders=[
                "flourishing_definition_is_value_laden",
                "component_weights_are_assumptions",
            ],
            missing=[f"component_{c}_not_observed" for c in missing_components],
            source="world_model:flourishing_metric",
            methodology=f"weighted_sum_of_{len(self.components)}_components",
            scope=self.scope,
        )

    def update_weight(self, component: str, new_weight: float) -> None:
        """Update the weight of a component.

        Weights are renormalized after update so they sum to 1.
        This is how the model learns what actually matters for
        flourishing -- components that correlate with good outcomes
        get higher weights over time.
        """
        if component not in self.components:
            return
        self.components[component]["weight"] = max(new_weight, 0.01)
        # Renormalize
        total = sum(c["weight"] for c in self.components.values())
        for c in self.components.values():
            c["weight"] /= total

    def to_dict(self) -> dict:
        return {
            "scope": self.scope,
            "components": self.components,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FlourishingMetric":
        return cls(scope=d["scope"], components=d.get("components"))


# ---------------------------------------------------------------------------
# WorldModel — the core Bayesian model
# ---------------------------------------------------------------------------


class WorldModel:
    """Bayesian world model for tracking flourishing across all domains.

    Maintains beliefs about the state of the world. Updates beliefs
    when new measurements arrive. Predicts the effects of interventions.
    Tracks its own corrections so you can see when and how it was wrong.

    This model is always wrong somewhere. It does not pretend otherwise.
    Every output includes uncertainty. Every prediction includes caveats.
    The goal is to be less wrong over time, not to be right.
    """

    def __init__(
        self,
        sensors: Optional[SensorRegistry] = None,
        db_path: str = _WORLD_DB,
        required_confirming_nodes: Optional[List[str]] = None,
    ):
        self._db_path = db_path
        self.sensors = sensors or SensorRegistry()
        self.beliefs: Dict[str, Belief] = {}
        self.correction_log: List[dict] = []
        self._flourishing_metrics: Dict[str, FlourishingMetric] = {}
        if required_confirming_nodes is None:
            required_confirming_nodes = [
                n.strip()
                for n in os.environ.get("HFF_REQUIRED_CONFIRMING_NODES", "").split(",")
                if n.strip()
            ]
        self.required_confirming_nodes = sorted(set(required_confirming_nodes))

        _init_world_db(db_path)
        self._load_beliefs()
        self._load_corrections()
        self._load_flourishing_configs()

    # -- persistence -----------------------------------------------------------

    def _load_beliefs(self) -> None:
        """Load beliefs from SQLite."""
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute(
                "SELECT entity, domain, scope, prior, posterior, uncertainty, "
                "evidence_json, last_updated, history_json, confidence, "
                "status, last_reinforced, last_challenged, reinforcement_count, "
                "contradiction_count, half_life_days, immutable, "
                "confirming_nodes_json FROM beliefs"
            )
            for row in c.fetchall():
                entity, domain, scope, prior, posterior, uncertainty, \
                    evidence_json, last_updated, history_json, confidence, \
                    status, last_reinforced, last_challenged, \
                    reinforcement_count, contradiction_count, half_life_days, \
                    immutable, confirming_nodes_json = row
                self.beliefs[entity] = Belief(
                    entity=entity,
                    domain=domain,
                    scope=scope,
                    prior=prior,
                    posterior=posterior,
                    uncertainty=uncertainty,
                    confidence=(
                        confidence
                        if confidence is not None
                        else round(1.0 - uncertainty, 4)
                    ),
                    status=status or BELIEF_ACTIVE,
                    evidence=json.loads(evidence_json),
                    last_updated=datetime.fromisoformat(last_updated),
                    history=json.loads(history_json),
                    last_reinforced=(
                        datetime.fromisoformat(last_reinforced)
                        if last_reinforced
                        else datetime.fromisoformat(last_updated)
                    ),
                    last_challenged=(
                        datetime.fromisoformat(last_challenged)
                        if last_challenged
                        else None
                    ),
                    reinforcement_count=reinforcement_count or 0,
                    contradiction_count=contradiction_count or 0,
                    half_life_days=half_life_days or DEFAULT_HALF_LIFE_DAYS,
                    immutable=bool(immutable),
                    confirming_nodes=json.loads(confirming_nodes_json or "[]"),
                )
            conn.close()
        except Exception:
            pass  # fresh start if DB is missing or corrupt

    def _save_belief(self, belief: Belief) -> None:
        """Persist a single belief to SQLite."""
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute(
                """INSERT OR REPLACE INTO beliefs
                   (entity, domain, scope, prior, posterior, uncertainty,
                    evidence_json, last_updated, history_json, confidence,
                    status, last_reinforced, last_challenged,
                    reinforcement_count, contradiction_count, half_life_days,
                    immutable, confirming_nodes_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    belief.entity,
                    belief.domain,
                    belief.scope,
                    belief.prior,
                    belief.posterior,
                    belief.uncertainty,
                    json.dumps(belief.evidence),
                    belief.last_updated.isoformat(),
                    json.dumps(belief.history),
                    belief.confidence,
                    belief.status,
                    belief.last_reinforced.isoformat(),
                    (
                        belief.last_challenged.isoformat()
                        if belief.last_challenged
                        else None
                    ),
                    belief.reinforcement_count,
                    belief.contradiction_count,
                    belief.half_life_days,
                    1 if belief.immutable else 0,
                    json.dumps(belief.confirming_nodes),
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _load_corrections(self) -> None:
        """Load correction log from SQLite."""
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute(
                "SELECT entity, old_posterior, new_posterior, reason, "
                "measurement_hash, corrected_at FROM corrections "
                "ORDER BY id DESC LIMIT 500"
            )
            self.correction_log = [
                {
                    "entity": r[0],
                    "old_posterior": r[1],
                    "new_posterior": r[2],
                    "reason": r[3],
                    "measurement_hash": r[4],
                    "corrected_at": r[5],
                }
                for r in c.fetchall()
            ]
            conn.close()
        except Exception:
            pass

    def _save_correction(self, correction: dict) -> None:
        """Persist a correction to SQLite."""
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute(
                """INSERT INTO corrections
                   (entity, old_posterior, new_posterior, reason,
                    measurement_hash, corrected_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    correction["entity"],
                    correction["old_posterior"],
                    correction["new_posterior"],
                    correction["reason"],
                    correction.get("measurement_hash", ""),
                    correction["corrected_at"],
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _load_flourishing_configs(self) -> None:
        """Load flourishing metric configurations from SQLite."""
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute("SELECT scope, components_json FROM flourishing_configs")
            for row in c.fetchall():
                scope, components_json = row
                components = json.loads(components_json)
                self._flourishing_metrics[scope] = FlourishingMetric(
                    scope=scope, components=components
                )
            conn.close()
        except Exception:
            pass

    def _save_flourishing_config(self, metric: FlourishingMetric) -> None:
        """Persist a flourishing metric configuration."""
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute(
                """INSERT OR REPLACE INTO flourishing_configs
                   (scope, components_json, updated_at)
                   VALUES (?, ?, ?)""",
                (
                    metric.scope,
                    json.dumps(metric.components),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    # -- confidence lifecycle --------------------------------------------------

    def _required_nodes_confirmed(self, belief: Belief) -> bool:
        if not self.required_confirming_nodes:
            return False
        confirmed = set(belief.confirming_nodes)
        return set(self.required_confirming_nodes).issubset(confirmed)

    def _refresh_belief_status(self, belief: Belief) -> None:
        if belief.immutable:
            belief.status = BELIEF_IMMUTABLE_CONSTRAINT
            belief.confidence = max(belief.confidence, ACCEPTED_FACT_CONFIDENCE)
            belief.uncertainty = min(belief.uncertainty, 1.0 - belief.confidence)
            return

        if belief.contradiction_count > 0:
            belief.status = (
                BELIEF_CONTESTED
                if belief.contradiction_count > 1
                else BELIEF_CHALLENGED
            )
            return

        can_be_fact = (
            belief.confidence >= ACCEPTED_FACT_CONFIDENCE
            and len(belief.evidence) >= MIN_ACCEPTED_FACT_EVIDENCE
            and self._required_nodes_confirmed(belief)
        )
        if can_be_fact:
            belief.status = BELIEF_ACCEPTED_FACT
        elif belief.confidence >= STRONG_BELIEF_CONFIDENCE:
            belief.status = BELIEF_STRONG
        else:
            belief.status = BELIEF_ACTIVE

    def apply_confidence_decay(
        self,
        entity: str,
        now: Optional[datetime] = None,
    ) -> Optional[Belief]:
        """Decay confidence over time unless a belief is immutable.

        Stale beliefs become less action-worthy. The posterior is left alone;
        only confidence/uncertainty/status change.
        """
        belief = self.beliefs.get(entity)
        if belief is None:
            return None
        if belief.immutable:
            return belief

        now = now or datetime.now(timezone.utc)
        elapsed_days = max(
            0.0,
            (now - belief.last_reinforced).total_seconds() / 86400.0,
        )
        half_life = max(float(belief.half_life_days), 0.001)
        decay_factor = math.exp(-elapsed_days / half_life)
        decayed = DEFAULT_CONFIDENCE_FLOOR + (
            belief.confidence - DEFAULT_CONFIDENCE_FLOOR
        ) * decay_factor
        belief.confidence = round(max(DEFAULT_CONFIDENCE_FLOOR, min(0.999999, decayed)), 6)
        belief.uncertainty = round(max(0.000001, min(1.0, 1.0 - belief.confidence)), 6)
        self._refresh_belief_status(belief)
        self._save_belief(belief)
        return belief

    def reinforce_belief(
        self,
        entity: str,
        weight: float,
        node_id: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> Optional[Belief]:
        """Increase confidence from new evidence or an admitted node.

        Reinforcement approaches 1.0 asymptotically; it never sets certainty.
        """
        belief = self.beliefs.get(entity)
        if belief is None:
            return None

        now = now or datetime.now(timezone.utc)
        weight = max(0.0, min(1.0, float(weight)))
        gain = weight * (1.0 - belief.confidence)
        belief.confidence = round(min(0.999999, belief.confidence + gain), 6)
        belief.uncertainty = round(max(0.000001, 1.0 - belief.confidence), 6)
        belief.reinforcement_count += 1
        belief.last_reinforced = now
        if node_id and node_id not in belief.confirming_nodes:
            belief.confirming_nodes.append(node_id)
            belief.confirming_nodes.sort()
        self._refresh_belief_status(belief)
        self._save_belief(belief)
        return belief

    def add_immutable_constraint(
        self,
        constraint_id: str,
        statement: str,
        domain: str = "ethics",
        scope: str = "constitutional",
    ) -> Belief:
        """Add a non-agent-editable operating constraint.

        Immutable constraints are not empirical facts. They are constitutional
        rules for the system's behavior and do not decay or get overturned by
        ordinary node polling.
        """
        now = datetime.now(timezone.utc)
        entity = f"constraint:{constraint_id}"
        belief = Belief(
            entity=entity,
            domain=domain,
            scope=scope,
            prior=1.0,
            posterior=1.0,
            uncertainty=0.000001,
            confidence=0.999999,
            status=BELIEF_IMMUTABLE_CONSTRAINT,
            evidence=[hashlib.sha256(statement.encode("utf-8")).hexdigest()],
            last_updated=now,
            last_reinforced=now,
            reinforcement_count=1,
            half_life_days=36500.0,
            immutable=True,
            history=[{
                "statement": statement,
                "updated_at": now.isoformat(),
                "note": "constitutional_constraint_not_empirical_fact",
            }],
        )
        self.beliefs[entity] = belief
        self._save_belief(belief)
        return belief

    def challenge_belief(
        self,
        entity: str,
        weight: float,
        reason: str,
        now: Optional[datetime] = None,
    ) -> Optional[Belief]:
        """Lower confidence and mark a belief as challenged or contested."""
        belief = self.beliefs.get(entity)
        if belief is None:
            return None
        if belief.immutable:
            return belief

        now = now or datetime.now(timezone.utc)
        weight = max(0.0, min(1.0, float(weight)))
        loss = weight * belief.confidence
        belief.confidence = round(max(DEFAULT_CONFIDENCE_FLOOR, belief.confidence - loss), 6)
        belief.uncertainty = round(max(0.000001, min(1.0, 1.0 - belief.confidence)), 6)
        belief.contradiction_count += 1
        belief.last_challenged = now
        belief.history.append({
            "posterior": belief.posterior,
            "uncertainty": belief.uncertainty,
            "confidence": belief.confidence,
            "updated_at": now.isoformat(),
            "challenge_reason": reason,
        })
        if len(belief.history) > 100:
            belief.history = belief.history[-100:]
        self._refresh_belief_status(belief)
        self._save_belief(belief)
        return belief

    # -- Bayesian update -------------------------------------------------------

    def update(self, measurements: List[Measurement]) -> List[dict]:
        """Bayesian update of beliefs based on new measurements.

        For each measurement, finds or creates the corresponding belief
        and updates its posterior probability. Uses a simplified Bayesian
        update where the measurement value shifts the posterior toward
        the observed value, weighted by the measurement's certainty.

        This is NOT a full Bayesian update with proper likelihood functions.
        It is a useful approximation that captures the core idea: more
        certain evidence moves beliefs more, less certain evidence moves
        beliefs less.

        Returns a list of update records (what changed and by how much).
        """
        updates = []

        for m in measurements:
            entity_key = f"{m.scope}:{m.source}" if m.scope != "unspecified" else m.source

            # Determine observed value as a probability (0-1 scale)
            if isinstance(m.value, (int, float)):
                # Clamp to [0, 1] for probability interpretation
                observed = max(0.0, min(1.0, float(m.value)))
            else:
                # Non-numeric: treat as neutral observation
                observed = 0.5

            # How much to trust this measurement (inverse of uncertainty)
            trust = 1.0 - m.uncertainty

            if entity_key in self.beliefs:
                belief = self.beliefs[entity_key]
                self.apply_confidence_decay(entity_key)
                old_posterior = belief.posterior

                # Simplified Bayesian update:
                # new_posterior = old_posterior * (1 - trust) + observed * trust
                # This moves the posterior toward the observation,
                # proportional to how much we trust the measurement.
                new_posterior = old_posterior * (1.0 - trust) + observed * trust
                new_posterior = round(max(0.0, min(1.0, new_posterior)), 6)

                # Uncertainty decreases with more evidence (slowly)
                evidence_count = len(belief.evidence) + 1
                new_uncertainty = belief.uncertainty * (1.0 - trust * 0.1)
                new_uncertainty = round(max(0.05, min(1.0, new_uncertainty)), 4)

                # Record correction if the shift was significant
                shift = abs(new_posterior - old_posterior)
                now = datetime.now(timezone.utc)
                if shift > 0.05:
                    correction = {
                        "entity": entity_key,
                        "old_posterior": old_posterior,
                        "new_posterior": new_posterior,
                        "reason": f"measurement_shift_{shift:.4f}_from_{m.source}",
                        "measurement_hash": m.measurement_hash,
                        "corrected_at": now.isoformat(),
                    }
                    self.correction_log.insert(0, correction)
                    self._save_correction(correction)

                if shift > 0.35 and trust > 0.4:
                    belief.contradiction_count += 1
                    belief.last_challenged = now

                # Save history
                belief.history.append({
                    "posterior": old_posterior,
                    "uncertainty": belief.uncertainty,
                    "confidence": belief.confidence,
                    "updated_at": belief.last_updated.isoformat(),
                    "evidence_hash": m.measurement_hash,
                })
                # Keep history bounded
                if len(belief.history) > 100:
                    belief.history = belief.history[-100:]

                belief.posterior = new_posterior
                belief.uncertainty = new_uncertainty
                confidence_gain = trust * (1.0 - belief.confidence) * 0.5
                belief.confidence = round(
                    min(0.999999, belief.confidence + confidence_gain),
                    6,
                )
                belief.uncertainty = round(
                    max(0.000001, min(belief.uncertainty, 1.0 - belief.confidence)),
                    6,
                )
                belief.reinforcement_count += 1
                belief.last_reinforced = now
                belief.evidence.append(m.measurement_hash)
                belief.last_updated = now

            else:
                # New belief: prior is 0.5 (maximum entropy / no information)
                new_posterior = 0.5 * (1.0 - trust) + observed * trust
                new_posterior = round(max(0.0, min(1.0, new_posterior)), 6)
                initial_uncertainty = round(max(0.1, m.uncertainty), 4)
                now = datetime.now(timezone.utc)

                belief = Belief(
                    entity=entity_key,
                    domain=self._infer_domain(m),
                    scope=m.scope,
                    prior=0.5,
                    posterior=new_posterior,
                    uncertainty=initial_uncertainty,
                    confidence=round(max(DEFAULT_CONFIDENCE_FLOOR, 1.0 - initial_uncertainty), 6),
                    evidence=[m.measurement_hash],
                    history=[],
                    last_reinforced=now,
                    reinforcement_count=1,
                )

            self.beliefs[entity_key] = belief
            self._refresh_belief_status(belief)
            self._save_belief(belief)

            updates.append({
                "entity": entity_key,
                "posterior": belief.posterior,
                "uncertainty": belief.uncertainty,
                "confidence": belief.confidence,
                "status": belief.status,
                "evidence_count": len(belief.evidence),
                "measurement_hash": m.measurement_hash,
            })

        return updates

    def _infer_domain(self, m: Measurement) -> str:
        """Best-effort domain inference from a measurement.

        Looks at the scope and source for domain hints.
        Returns 'general' if it cannot determine the domain.
        This is a heuristic and will often be wrong.
        """
        text = f"{m.scope} {m.source} {m.methodology}".lower()
        domain_keywords = {
            "healthcare": ["health", "medical", "hospital", "patient", "diagnosis", "mortality", "daly", "disease", "life_expectancy"],
            "criminal_justice": ["criminal", "recidivism", "sentencing", "police", "court", "compas", "arrest"],
            "ecology": ["ecosystem", "species", "biodiversity", "habitat", "climate", "forest", "ocean", "planetary", "extinction", "resilience"],
            "animal_welfare": ["animal", "shelter", "adoption", "veterinary", "welfare", "livestock", "stereotyp", "slaughter", "captive"],
            "education": ["education", "school", "student", "learning", "academic", "childhood"],
            "economic": ["economic", "employment", "income", "poverty", "housing", "gini", "mobility", "wealth", "inequality"],
            "psychology": ["satisfaction", "wellbeing", "well-being", "autonomy", "happiness", "swls", "qoli", "sdt"],
            "social": ["social_capital", "trust", "freedom", "civic", "putnam"],
            "astrophysics": ["universe", "galactic", "solar", "planet", "habitable", "cmb", "planck", "gaia", "exoplanet", "biomass", "earth"],
        }
        for domain, keywords in domain_keywords.items():
            if any(kw in text for kw in keywords):
                return domain
        return "general"

    # -- queries ---------------------------------------------------------------

    def query(self, entity: str) -> Optional[Belief]:
        """What do we believe about entity X right now?

        Returns None if we have never observed this entity.
        The belief's uncertainty field tells you how much to trust
        the posterior -- high uncertainty means the model doesn't
        really know.
        """
        return self.beliefs.get(entity)

    def get_history(self, entity: str) -> List[dict]:
        """How has our belief about entity X evolved over time?

        Returns the history of posterior values. An empty history
        means we have only one data point. A volatile history
        (large swings) means the evidence is contradictory or
        the entity is genuinely unstable.
        """
        belief = self.beliefs.get(entity)
        if belief is None:
            return []
        # Include current state as the latest entry
        full_history = list(belief.history)
        full_history.append({
            "posterior": belief.posterior,
            "uncertainty": belief.uncertainty,
            "updated_at": belief.last_updated.isoformat(),
            "evidence_hash": belief.evidence[-1] if belief.evidence else "",
        })
        return full_history

    # -- predictions -----------------------------------------------------------

    def predict(self, intervention: Intervention) -> Prediction:
        """If we do intervention X, what happens?

        This is speculative. The model estimates effects based on
        current beliefs and the intervention's predicted effect.
        The prediction includes caveats because predictions are
        always wrong in some way.
        """
        current = self.beliefs.get(intervention.target)
        caveats = [
            "this_is_a_prediction_not_a_guarantee",
            "correlation_does_not_imply_causation",
            "second_order_effects_are_especially_uncertain",
        ]

        if current is None:
            # No data on this entity -- very uncertain prediction
            predicted = {
                "entity": intervention.target,
                "predicted_posterior": 0.5 + intervention.predicted_effect,
                "uncertainty": 0.9,
                "note": "no_prior_observations_for_this_entity",
            }
            caveats.append("no_baseline_data_exists_for_this_entity")
            return Prediction(
                intervention=intervention,
                current_belief=Belief(
                    entity=intervention.target,
                    domain="unknown",
                    scope="unknown",
                    prior=0.5,
                    posterior=0.5,
                    uncertainty=1.0,
                ),
                predicted_belief=predicted,
                confidence=0.1,
                caveats=caveats,
            )

        # Apply predicted effect to current posterior
        predicted_posterior = current.posterior + intervention.predicted_effect
        predicted_posterior = max(0.0, min(1.0, predicted_posterior))

        # Prediction uncertainty: current belief uncertainty + intervention uncertainty
        prediction_uncertainty = min(
            current.uncertainty + intervention.uncertainty * 0.5, 1.0
        )

        # Confidence degrades with uncertainty
        confidence = intervention.confidence * (1.0 - prediction_uncertainty * 0.5)

        if current.uncertainty > 0.7:
            caveats.append("baseline_belief_is_highly_uncertain")
        if intervention.uncertainty > 0.5:
            caveats.append("intervention_effect_is_poorly_understood")
        if len(intervention.side_effects) > 0:
            caveats.append(
                f"{len(intervention.side_effects)}_predicted_side_effects_each_with_own_uncertainty"
            )

        predicted = {
            "entity": intervention.target,
            "current_posterior": current.posterior,
            "predicted_posterior": round(predicted_posterior, 4),
            "predicted_change": round(intervention.predicted_effect, 4),
            "uncertainty": round(prediction_uncertainty, 4),
        }

        return Prediction(
            intervention=intervention,
            current_belief=current,
            predicted_belief=predicted,
            confidence=round(confidence, 4),
            caveats=caveats,
        )

    def counterfactual(self, entity: str, action: str) -> List[Intervention]:
        """What actions could improve this entity's flourishing?

        Generates a list of hypothetical interventions based on
        current beliefs. These are suggestions, not prescriptions.
        Each comes with uncertainty and caveats.

        If we have no data on the entity, we return generic interventions
        with very high uncertainty.
        """
        current = self.beliefs.get(entity)

        if current is None:
            return [
                Intervention(
                    action=f"{action}_with_monitoring",
                    target=entity,
                    predicted_effect=0.1,
                    uncertainty=0.9,
                    confidence=0.1,
                    counterfactual="unknown_baseline_no_data",
                    side_effects=[{
                        "target": f"{entity}_related_systems",
                        "effect": 0.0,
                        "uncertainty": 1.0,
                        "description": "completely_unknown_side_effects",
                    }],
                )
            ]

        interventions = []

        # Generate interventions based on current state
        if current.posterior < 0.5:
            # Entity is doing poorly -- suggest improvements
            interventions.append(Intervention(
                action=action,
                target=entity,
                predicted_effect=0.15,
                uncertainty=max(current.uncertainty, 0.4),
                confidence=min(0.5, 1.0 - current.uncertainty),
                counterfactual=f"without_action_posterior_likely_stays_at_{current.posterior:.2f}",
                side_effects=[{
                    "target": f"{current.domain}_related_entities",
                    "effect": 0.05,
                    "uncertainty": 0.7,
                    "description": "potential_positive_spillover",
                }],
            ))
        else:
            # Entity is doing okay -- suggest maintenance
            interventions.append(Intervention(
                action=f"maintain_{action}",
                target=entity,
                predicted_effect=0.05,
                uncertainty=max(current.uncertainty, 0.3),
                confidence=min(0.6, 1.0 - current.uncertainty),
                counterfactual=f"without_maintenance_posterior_may_decline_from_{current.posterior:.2f}",
                side_effects=[],
            ))

        # Always suggest monitoring as an intervention
        interventions.append(Intervention(
            action=f"increase_monitoring_of_{entity}",
            target=entity,
            predicted_effect=0.02,
            uncertainty=0.2,
            confidence=0.7,
            counterfactual="without_monitoring_problems_go_undetected",
            side_effects=[{
                "target": entity,
                "effect": -0.01,
                "uncertainty": 0.5,
                "description": "monitoring_has_small_observation_effect",
            }],
        ))

        return interventions

    # -- flourishing -----------------------------------------------------------

    def flourishing_score(self, scope: str) -> Measurement:
        """Compute aggregate flourishing for a scope.

        Uses the FlourishingMetric for this scope (or creates a default one).
        The result is uncertainty-weighted: components with more evidence
        contribute more to the score.

        The score is a number between 0 and 1, but the uncertainty
        range is what matters. A score of 0.7 with uncertainty 0.4
        means flourishing could plausibly be anywhere from 0.3 to 1.0.
        """
        if scope not in self._flourishing_metrics:
            self._flourishing_metrics[scope] = FlourishingMetric(scope)

        metric = self._flourishing_metrics[scope]
        return metric.compute(self.beliefs)

    def get_flourishing_metric(self, scope: str) -> FlourishingMetric:
        """Get or create the flourishing metric for a scope."""
        if scope not in self._flourishing_metrics:
            self._flourishing_metrics[scope] = FlourishingMetric(scope)
        return self._flourishing_metrics[scope]

    def set_flourishing_metric(
        self, scope: str, components: Dict[str, dict]
    ) -> None:
        """Set a custom flourishing metric for a scope."""
        metric = FlourishingMetric(scope=scope, components=components)
        self._flourishing_metrics[scope] = metric
        self._save_flourishing_config(metric)

    # -- anomaly detection / discovery -----------------------------------------

    def discover(self) -> List[dict]:
        """Find patterns in beliefs that suggest undiscovered causes.

        Looks for:
        1. Correlated movements: beliefs that change together may share
           a common cause.
        2. Outliers: beliefs with posteriors far from their priors may
           indicate surprising phenomena.
        3. High-uncertainty clusters: groups of beliefs where we know
           very little may indicate measurement gaps.
        4. Stale beliefs: beliefs that have not been updated recently
           may be based on outdated evidence.

        This is exploratory analysis, not causal inference.
        Patterns found here are hypotheses to investigate, not conclusions.
        """
        discoveries = []

        if not self.beliefs:
            return [{
                "type": "no_data",
                "description": "no beliefs exist yet -- nothing to analyze",
                "severity": "info",
            }]

        # 1. Outliers: beliefs far from prior (0.5)
        for entity, belief in self.beliefs.items():
            distance = abs(belief.posterior - belief.prior)
            if distance > 0.3 and belief.uncertainty < 0.5:
                discoveries.append({
                    "type": "outlier",
                    "entity": entity,
                    "description": (
                        f"posterior ({belief.posterior:.2f}) is far from "
                        f"prior ({belief.prior:.2f}) with relatively low "
                        f"uncertainty ({belief.uncertainty:.2f})"
                    ),
                    "severity": "interesting",
                    "posterior": belief.posterior,
                    "prior": belief.prior,
                    "distance": round(distance, 4),
                })

        # 2. High uncertainty clusters
        high_unc = [
            (e, b) for e, b in self.beliefs.items() if b.uncertainty > 0.7
        ]
        if len(high_unc) > 3:
            domains = set(b.domain for _, b in high_unc)
            discoveries.append({
                "type": "measurement_gap",
                "description": (
                    f"{len(high_unc)} beliefs have uncertainty > 0.7 "
                    f"across domains: {', '.join(domains)}. "
                    "more measurement is needed in these areas."
                ),
                "severity": "actionable",
                "entities": [e for e, _ in high_unc],
                "domains": list(domains),
            })

        # 3. Stale beliefs (not updated in simulated "long time" -- check
        # if last_updated is older than any other belief by a large margin)
        if len(self.beliefs) >= 2:
            update_times = [
                (e, b.last_updated) for e, b in self.beliefs.items()
            ]
            update_times.sort(key=lambda x: x[1])
            oldest_entity, oldest_time = update_times[0]
            newest_time = update_times[-1][1]
            gap = (newest_time - oldest_time).total_seconds()
            if gap > 3600:  # more than an hour stale relative to newest
                discoveries.append({
                    "type": "stale_belief",
                    "entity": oldest_entity,
                    "description": (
                        f"belief for '{oldest_entity}' has not been updated "
                        f"since {oldest_time.isoformat()}, which is the oldest "
                        "in the model. evidence may be outdated."
                    ),
                    "severity": "info",
                    "last_updated": oldest_time.isoformat(),
                })

        # 4. Correlated beliefs in the same domain
        by_domain: Dict[str, List[Belief]] = {}
        for belief in self.beliefs.values():
            by_domain.setdefault(belief.domain, []).append(belief)

        for domain, domain_beliefs in by_domain.items():
            if len(domain_beliefs) >= 3:
                posteriors = [b.posterior for b in domain_beliefs]
                avg = sum(posteriors) / len(posteriors)
                spread = max(posteriors) - min(posteriors)
                if spread < 0.1 and len(posteriors) >= 3:
                    discoveries.append({
                        "type": "correlated_beliefs",
                        "domain": domain,
                        "description": (
                            f"{len(domain_beliefs)} beliefs in '{domain}' "
                            f"have very similar posteriors (spread={spread:.3f}). "
                            "they may share a common underlying cause, or "
                            "the sensors may not be truly independent."
                        ),
                        "severity": "interesting",
                        "belief_count": len(domain_beliefs),
                        "average_posterior": round(avg, 4),
                        "spread": round(spread, 4),
                    })

        if not discoveries:
            discoveries.append({
                "type": "nothing_notable",
                "description": (
                    "no anomalies or patterns detected. this does NOT mean "
                    "everything is fine -- it means the model has not found "
                    "anything surprising in current data. there may be "
                    "important patterns in dimensions the model does not observe."
                ),
                "severity": "info",
            })

        return discoveries

    # -- status ----------------------------------------------------------------

    def status(self) -> dict:
        """Summary status of the world model.

        This is the model being honest about what it knows and
        what it does not know.
        """
        sensor_status = self.sensors.status()
        belief_count = len(self.beliefs)
        domains = list(set(b.domain for b in self.beliefs.values()))
        scopes = list(set(b.scope for b in self.beliefs.values()))

        avg_uncertainty = (
            sum(b.uncertainty for b in self.beliefs.values()) / belief_count
            if belief_count > 0
            else 1.0
        )
        avg_confidence = (
            sum(b.confidence for b in self.beliefs.values()) / belief_count
            if belief_count > 0
            else 0.0
        )
        belief_status_counts: Dict[str, int] = {}
        for belief in self.beliefs.values():
            belief_status_counts[belief.status] = (
                belief_status_counts.get(belief.status, 0) + 1
            )

        last_update = None
        if self.beliefs:
            last_update = max(
                b.last_updated for b in self.beliefs.values()
            ).isoformat()

        # Compute overall flourishing for common scopes.
        # Include parent scopes (e.g., "humans" from "humans:fairness")
        # because flourishing is defined at the top level and components
        # are sub-scopes.
        parent_scopes = set()
        for s in scopes:
            parts = s.split(":")
            if len(parts) >= 2:
                parent_scopes.add(parts[0])
        # Always include the three universal scopes
        parent_scopes.update(["humans", "animals", "ecosystems"])

        flourishing_scores = {}
        # Only compute flourishing at meaningful scope levels:
        # explicitly configured metrics + parent scopes derived from beliefs.
        # Sub-scopes (humans:fairness) are components, not standalone scopes.
        all_scopes = set(
            list(self._flourishing_metrics.keys()) + list(parent_scopes)
        )
        for scope in all_scopes:
            try:
                score = self.flourishing_score(scope)
                flourishing_scores[scope] = {
                    "score": score.value,
                    "uncertainty": score.uncertainty,
                }
            except Exception:
                pass

        return {
            "belief_count": belief_count,
            "sensor_count": sensor_status["total_sensors"],
            "domains": domains,
            "scopes": scopes,
            "average_uncertainty": round(avg_uncertainty, 4),
            "average_confidence": round(avg_confidence, 4),
            "belief_status_counts": belief_status_counts,
            "required_confirming_nodes": self.required_confirming_nodes,
            "last_update": last_update,
            "corrections_count": len(self.correction_log),
            "flourishing_scores": flourishing_scores,
            "disclaimer": (
                "this model is always wrong somewhere. uncertainty values "
                "are estimates, not guarantees. use this as one input among "
                "many, never as the sole basis for decisions affecting "
                "real beings."
            ),
        }


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile

    # Use a temp DB for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        test_db = f.name

    try:
        model = WorldModel(db_path=test_db)

        # Create some measurements
        m1 = Measurement(
            value=0.73,
            uncertainty=0.2,
            confidence_interval=(0.65, 0.81),
            sample_size=500,
            source="test_hospital",
            methodology="administrative_records",
            scope="healthcare:hospital_a",
        )

        m2 = Measurement(
            value=0.45,
            uncertainty=0.3,
            confidence_interval=(0.30, 0.60),
            sample_size=200,
            source="test_ecosystem",
            methodology="satellite_survey",
            scope="ecosystems:pacific_northwest",
        )

        # Update beliefs
        updates = model.update([m1, m2])
        assert len(updates) == 2
        print(f"[OK] Updated {len(updates)} beliefs")

        # Query
        belief = model.query("healthcare:hospital_a:test_hospital")
        assert belief is not None
        print(f"[OK] Query works: posterior={belief.posterior}, uncertainty={belief.uncertainty}")

        # Predict
        intervention = Intervention(
            action="increase_screening",
            target="healthcare:hospital_a:test_hospital",
            predicted_effect=0.1,
            uncertainty=0.4,
            confidence=0.5,
            counterfactual="accuracy_stays_at_current_level",
        )
        prediction = model.predict(intervention)
        assert prediction.confidence > 0
        print(f"[OK] Prediction works: confidence={prediction.confidence}")

        # Counterfactual
        interventions = model.counterfactual(
            "healthcare:hospital_a:test_hospital", "improve_diagnostics"
        )
        assert len(interventions) > 0
        print(f"[OK] Counterfactual generated {len(interventions)} interventions")

        # Flourishing
        score = model.flourishing_score("healthcare")
        print(f"[OK] Flourishing score: {score.value} (uncertainty: {score.uncertainty})")

        # Discovery
        discoveries = model.discover()
        print(f"[OK] Discovery found {len(discoveries)} patterns")

        # History
        history = model.get_history("healthcare:hospital_a:test_hospital")
        print(f"[OK] History has {len(history)} entries")

        # Status
        status = model.status()
        assert status["belief_count"] == 2
        print(f"[OK] Status: {status['belief_count']} beliefs, avg uncertainty {status['average_uncertainty']}")

        # Persistence: create a new model from same DB
        model2 = WorldModel(db_path=test_db)
        assert len(model2.beliefs) == 2
        print("[OK] Beliefs persisted and loaded from SQLite")

        print("\n[OK] All world model tests passed")

    finally:
        try:
            os.unlink(test_db)
        except Exception:
            pass
