#!/usr/bin/env python3
"""Epistemic claim-safety baseline for HFF.

This module models an epistemic immune layer: claims are classified before they
can become accepted beliefs, public outputs, seed updates, or actions. It is
intentionally data-only and does not wire runtime behavior.
"""

from dataclasses import asdict, dataclass, field
from typing import List, Tuple

CHECK_PASSED = "passed"
CHECK_NEEDS_REVIEW = "needs_review"
CHECK_FAILED = "failed"

CLAIM_KIND_MEASUREMENT = "measurement"
CLAIM_KIND_OBSERVATION = "observation"
CLAIM_KIND_INTERPRETATION = "interpretation"
CLAIM_KIND_FORECAST = "forecast"
CLAIM_KIND_MYTH = "myth"
CLAIM_KIND_SCENARIO = "scenario"
CLAIM_KIND_OPERATIONAL_FACT = "operational_fact"
CLAIM_KIND_UNKNOWN = "unknown"

RISK_CLASS_NORMAL = "normal"
RISK_CLASS_HIGH_IMPACT = "high_impact"
RISK_CLASS_CATASTROPHIC = "catastrophic"
RISK_CLASS_AUTONOMY = "autonomy"
RISK_CLASS_SECURITY = "security"
RISK_CLASS_PRIVACY = "privacy"
RISK_CLASS_P_DOOM = "p_doom"

CLASSIFICATION_ACCEPTED_CANDIDATE = "accepted_candidate"
CLASSIFICATION_UNSUPPORTED = "unsupported"
CLASSIFICATION_OVERCLAIM = "overclaim"
CLASSIFICATION_IMPOSSIBLE_CLAIM = "impossible_claim"
CLASSIFICATION_FORECAST_QUARANTINE = "forecast_quarantine"
CLASSIFICATION_CULTURAL_CONTEXT = "cultural_context"
CLASSIFICATION_NEEDS_REVIEW = "needs_review"

VERDICT_SUPPORTS = "supports"
VERDICT_REFUTES = "refutes"
VERDICT_NOT_ENOUGH_INFO = "not_enough_info"

FORECAST_STATUS_QUARANTINED = "quarantined"
FORECAST_STATUS_REVIEWED_SCENARIO = "reviewed_scenario"
FORECAST_STATUS_REJECTED = "rejected"

CONTRADICTION_ACTION_IGNORE = "ignore"
CONTRADICTION_ACTION_MONITOR = "monitor"
CONTRADICTION_ACTION_DOWNGRADE = "downgrade"
CONTRADICTION_ACTION_HUMAN_REVIEW = "human_review"
CONTRADICTION_ACTION_PUBLIC_CORRECTION = "public_correction"

BELIEF_STATUS_PROPOSED = "proposed"
BELIEF_STATUS_ACCEPTED = "accepted"
BELIEF_STATUS_REJECTED = "rejected"
BELIEF_STATUS_SUPERSEDED = "superseded"

CIRCUIT_ACTION_ALLOW = "allow"
CIRCUIT_ACTION_BLOCK = "block"
CIRCUIT_ACTION_QUARANTINE = "quarantine"
CIRCUIT_ACTION_REQUIRE_HUMAN_REVIEW = "require_human_review"
CIRCUIT_ACTION_REQUIRE_MORE_SOURCES = "require_more_sources"
CIRCUIT_ACTION_SAFE_REWRITE = "safe_rewrite"

DEFAULT_BLOCK_PATTERNS: Tuple[str, ...] = (
    "perfect safety",
    "guaranteed defense",
    "guaranteed protection",
    "complete understanding",
    "knows all unknown unknowns",
    "final moral authority",
    "divine authority",
    "sacred authority",
    "holy artifact",
    "prophecy",
    "destiny",
    "predicts the future",
    "sees the past",
    "automatic future model trust",
)


@dataclass
class EvidenceBundle:
    """Evidence package for a claim.

    LLM output may be included as interpretation, but it cannot be the only
    support for accepting a factual claim. Provenance can identify where an LLM
    output came from, but provenance alone is not independent factual support.
    """

    evidence_id: str = ""
    source_refs: List[str] = field(default_factory=list)
    sensor_observation_refs: List[str] = field(default_factory=list)
    source_classifications: List[str] = field(default_factory=list)
    provenance_refs: List[str] = field(default_factory=list)
    llm_panel_outputs: List[str] = field(default_factory=list)
    agreements: List[str] = field(default_factory=list)
    disagreements: List[str] = field(default_factory=list)
    minority_report: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    confidence_assessment_ref: str = ""
    review_status: str = CHECK_NEEDS_REVIEW

    def has_non_llm_support(self) -> bool:
        return bool(self.source_refs or self.sensor_observation_refs)

    def is_llm_only(self) -> bool:
        return bool(self.llm_panel_outputs) and not self.has_non_llm_support()

    def missing_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.evidence_id:
            missing.append("evidence_id")
        if not self.has_non_llm_support():
            missing.append("non_llm_support")
        if not self.source_classifications:
            missing.append("source_classifications")
        if not self.provenance_refs:
            missing.append("provenance_refs")
        if self.disagreements and not self.minority_report:
            missing.append("minority_report")
        if self.review_status != CHECK_PASSED:
            missing.append("review_status")
        return missing

    def can_support_fact_claim(self) -> bool:
        return not self.is_llm_only() and not self.missing_requirements()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["is_llm_only"] = self.is_llm_only()
        data["missing_requirements"] = self.missing_requirements()
        data["can_support_fact_claim"] = self.can_support_fact_claim()
        return data


@dataclass
class ClaimSafetyClassification:
    """Classifies a claim before it can move toward accepted belief."""

    claim_id: str = ""
    claim_text: str = ""
    claim_kind: str = CLAIM_KIND_UNKNOWN
    risk_class: str = RISK_CLASS_NORMAL
    classification: str = CLASSIFICATION_NEEDS_REVIEW
    verdict: str = VERDICT_NOT_ENOUGH_INFO
    source_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    requires_human_review: bool = True
    safe_rewrite: str = ""
    revision_triggers: List[str] = field(default_factory=list)

    def missing_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.claim_id:
            missing.append("claim_id")
        if not self.claim_text:
            missing.append("claim_text")
        if self.claim_kind == CLAIM_KIND_UNKNOWN:
            missing.append("claim_kind")
        if not self.source_refs:
            missing.append("source_refs")
        if not self.evidence_refs:
            missing.append("evidence_refs")
        if not self.revision_triggers:
            missing.append("revision_triggers")
        if self.classification in {
            CLASSIFICATION_OVERCLAIM,
            CLASSIFICATION_IMPOSSIBLE_CLAIM,
            CLASSIFICATION_UNSUPPORTED,
        } and not self.safe_rewrite:
            missing.append("safe_rewrite")
        if self.risk_class != RISK_CLASS_NORMAL and not self.requires_human_review:
            missing.append("human_review_for_high_impact")
        return missing

    def can_be_accepted_candidate(self) -> bool:
        return (
            self.classification == CLASSIFICATION_ACCEPTED_CANDIDATE
            and self.verdict == VERDICT_SUPPORTS
            and self.requires_human_review is False
            and not self.missing_requirements()
        )

    def must_be_blocked_or_rewritten(self) -> bool:
        return self.classification in {
            CLASSIFICATION_OVERCLAIM,
            CLASSIFICATION_IMPOSSIBLE_CLAIM,
            CLASSIFICATION_UNSUPPORTED,
        }

    def to_dict(self) -> dict:
        data = asdict(self)
        data["missing_requirements"] = self.missing_requirements()
        data["can_be_accepted_candidate"] = self.can_be_accepted_candidate()
        data["must_be_blocked_or_rewritten"] = self.must_be_blocked_or_rewritten()
        return data


@dataclass
class ForecastQuarantine:
    """Keeps forecasts/scenarios from becoming operational facts by default."""

    forecast_id: str = ""
    forecast_text: str = ""
    time_horizon: str = ""
    assumptions: List[str] = field(default_factory=list)
    confidence_range: str = ""
    source_refs: List[str] = field(default_factory=list)
    competing_forecasts: List[str] = field(default_factory=list)
    falsification_conditions: List[str] = field(default_factory=list)
    status: str = FORECAST_STATUS_QUARANTINED
    scenario_only: bool = True
    may_update_seed: bool = False
    may_trigger_review: bool = True

    def missing_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.forecast_id:
            missing.append("forecast_id")
        if not self.forecast_text:
            missing.append("forecast_text")
        if not self.time_horizon:
            missing.append("time_horizon")
        if not self.assumptions:
            missing.append("assumptions")
        if not self.source_refs:
            missing.append("source_refs")
        if not self.falsification_conditions:
            missing.append("falsification_conditions")
        return missing

    def can_update_seed_now(self) -> bool:
        return False if self.scenario_only else self.may_update_seed

    def can_be_used_as_scenario(self) -> bool:
        return (
            self.status in {FORECAST_STATUS_QUARANTINED, FORECAST_STATUS_REVIEWED_SCENARIO}
            and not self.missing_requirements()
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["missing_requirements"] = self.missing_requirements()
        data["can_update_seed_now"] = self.can_update_seed_now()
        data["can_be_used_as_scenario"] = self.can_be_used_as_scenario()
        return data


@dataclass
class ContradictionReport:
    """Routes contradictions into review rather than automatic correction."""

    contradiction_id: str = ""
    new_claim: str = ""
    conflicting_beliefs: List[str] = field(default_factory=list)
    conflicting_sources: List[str] = field(default_factory=list)
    conflict_type: str = "unknown"
    severity: str = "needs_review"
    recommended_action: str = CONTRADICTION_ACTION_HUMAN_REVIEW
    review_required: bool = True

    def missing_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.contradiction_id:
            missing.append("contradiction_id")
        if not self.new_claim:
            missing.append("new_claim")
        if not self.conflicting_beliefs:
            missing.append("conflicting_beliefs")
        if not self.conflicting_sources:
            missing.append("conflicting_sources")
        return missing

    def can_auto_correct(self) -> bool:
        return False

    def should_trigger_review(self) -> bool:
        return self.review_required and self.recommended_action in {
            CONTRADICTION_ACTION_DOWNGRADE,
            CONTRADICTION_ACTION_HUMAN_REVIEW,
            CONTRADICTION_ACTION_PUBLIC_CORRECTION,
        }

    def to_dict(self) -> dict:
        data = asdict(self)
        data["missing_requirements"] = self.missing_requirements()
        data["can_auto_correct"] = self.can_auto_correct()
        data["should_trigger_review"] = self.should_trigger_review()
        return data


@dataclass
class BeliefLedgerEntry:
    """Append-only belief ledger record with rollback/supersession path."""

    belief_id: str = ""
    belief_text: str = ""
    status: str = BELIEF_STATUS_PROPOSED
    accepted_at: str = ""
    basis_evidence: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)
    supersedes: List[str] = field(default_factory=list)
    superseded_by: List[str] = field(default_factory=list)
    rollback_condition: str = ""
    public_correction_required: bool = False

    def missing_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.belief_id:
            missing.append("belief_id")
        if not self.belief_text:
            missing.append("belief_text")
        if self.status == BELIEF_STATUS_ACCEPTED:
            if not self.accepted_at:
                missing.append("accepted_at")
            if not self.basis_evidence:
                missing.append("basis_evidence")
            if not self.source_refs:
                missing.append("source_refs")
            if not self.rollback_condition:
                missing.append("rollback_condition")
        if self.status == BELIEF_STATUS_SUPERSEDED and not self.superseded_by:
            missing.append("superseded_by")
        return missing

    def can_be_accepted(self) -> bool:
        return self.status == BELIEF_STATUS_ACCEPTED and not self.missing_requirements()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["missing_requirements"] = self.missing_requirements()
        data["can_be_accepted"] = self.can_be_accepted()
        return data


@dataclass
class MythRiskPattern:
    """Compiles myths and cultural overclaims into safety rewrites or blocks."""

    pattern_id: str = ""
    pattern: str = ""
    myth_category: str = "unknown"
    blocked_classification: str = CLASSIFICATION_OVERCLAIM
    safe_rewrite: str = ""
    risk_if_advertised: str = "unauthorized_trust"
    requires_human_review: bool = True

    def matches(self, text: str) -> bool:
        return bool(self.pattern) and self.pattern.lower() in text.lower()

    def missing_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.pattern_id:
            missing.append("pattern_id")
        if not self.pattern:
            missing.append("pattern")
        if not self.safe_rewrite:
            missing.append("safe_rewrite")
        return missing


@dataclass
class EpistemicCircuitBreaker:
    """Downgrades dangerous claims from answer mode into review mode."""

    trigger_patterns: List[str] = field(default_factory=lambda: list(DEFAULT_BLOCK_PATTERNS))
    action: str = CIRCUIT_ACTION_REQUIRE_HUMAN_REVIEW
    matched_patterns: List[str] = field(default_factory=list)

    def scan(self, text: str) -> List[str]:
        lowered = text.lower()
        self.matched_patterns = [
            pattern for pattern in self.trigger_patterns
            if pattern.lower() in lowered
        ]
        return list(self.matched_patterns)

    def action_for(self, text: str) -> str:
        matches = self.scan(text)
        if not matches:
            return CIRCUIT_ACTION_ALLOW
        if any(pattern in matches for pattern in (
            "prophecy",
            "divine authority",
            "sacred authority",
            "holy artifact",
            "final moral authority",
        )):
            return CIRCUIT_ACTION_BLOCK
        if any(pattern in matches for pattern in (
            "predicts the future",
            "sees the past",
            "complete understanding",
        )):
            return CIRCUIT_ACTION_SAFE_REWRITE
        return self.action

    def should_block(self, text: str) -> bool:
        return self.action_for(text) == CIRCUIT_ACTION_BLOCK

    def should_require_review(self, text: str) -> bool:
        return self.action_for(text) in {
            CIRCUIT_ACTION_BLOCK,
            CIRCUIT_ACTION_QUARANTINE,
            CIRCUIT_ACTION_REQUIRE_HUMAN_REVIEW,
            CIRCUIT_ACTION_REQUIRE_MORE_SOURCES,
            CIRCUIT_ACTION_SAFE_REWRITE,
        }

    def to_dict(self) -> dict:
        return asdict(self)
