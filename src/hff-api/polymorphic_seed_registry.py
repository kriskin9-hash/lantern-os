#!/usr/bin/env python3
"""Polymorphic seed registry contracts for HFF.

This module gives HFF a conservative way to store different kinds of seed
records without flattening them into facts. It is intentionally inert: no
network calls, no polling, no runtime action, no accepted-fact promotion, and
no autonomous execution.
"""

from dataclasses import asdict, dataclass, field
from typing import Dict, List

SEED_KIND_SCIENCE = "science"
SEED_KIND_LAW = "law"
SEED_KIND_ETHICS = "ethics"
SEED_KIND_PHILOSOPHY = "philosophy"
SEED_KIND_LITERATURE = "literature"
SEED_KIND_HISTORY = "history"
SEED_KIND_MODEL_TYPE = "model_type"
SEED_KIND_IMMUTABLE_CONSTRAINT = "immutable_constraint"
SEED_KIND_SPECULATIVE_FUTURE_MODEL = "speculative_future_model"
SEED_KIND_UNKNOWN = "unknown"

STATUS_DRAFT = "draft"
STATUS_LOW_CONFIDENCE_PREDICTIVE = "low_confidence_predictive"
STATUS_SOURCE_BACKED = "source_backed"
STATUS_REVIEW_REQUIRED = "review_required"
STATUS_QUARANTINED = "quarantined"
STATUS_REJECTED = "rejected"

CLAIM_SCOPE_CONTEXT = "context"
CLAIM_SCOPE_ANALOGY = "analogy"
CLAIM_SCOPE_MEASUREMENT = "measurement"
CLAIM_SCOPE_NORMATIVE_PRINCIPLE = "normative_principle"
CLAIM_SCOPE_CONSTRAINT = "constraint"
CLAIM_SCOPE_FORECAST = "forecast"
CLAIM_SCOPE_OPERATIONAL_ASSUMPTION = "operational_assumption"

SOURCE_ROLE_PRIMARY = "primary"
SOURCE_ROLE_CONTEXT = "context"
SOURCE_ROLE_COUNTERPOINT = "counterpoint"
SOURCE_ROLE_ANALOGY = "analogy"
SOURCE_ROLE_FORECAST = "forecast"
SOURCE_ROLE_UNKNOWN = "unknown"

FORBIDDEN_PROMOTION_REASONS = (
    "operational_assumption_without_evidence",
    "speculative_model_used_for_current_fact",
    "speculative_model_used_for_autonomous_action",
    "missing_source_refs",
    "missing_uncertainty_statement",
    "missing_review_notes",
    "unknown_seed_kind",
    "unsupported_future_capability_claim",
)

SPECULATIVE_KIND_ALLOWED_SCOPES = {
    CLAIM_SCOPE_FORECAST,
    CLAIM_SCOPE_ANALOGY,
    CLAIM_SCOPE_CONTEXT,
}

FACT_ELIGIBLE_KINDS = {
    SEED_KIND_SCIENCE,
    SEED_KIND_HISTORY,
    SEED_KIND_LAW,
}


@dataclass
class SourceRef:
    """A source reference attached to a seed record."""

    source_id: str = ""
    title: str = ""
    url: str = ""
    role: str = SOURCE_ROLE_UNKNOWN
    limitations: List[str] = field(default_factory=list)

    def missing_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.source_id:
            missing.append("source_id")
        if not self.title:
            missing.append("title")
        if not self.url:
            missing.append("url")
        if self.role == SOURCE_ROLE_UNKNOWN:
            missing.append("role")
        if not self.limitations:
            missing.append("limitations")
        return missing

    def is_review_ready(self) -> bool:
        return not self.missing_requirements()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["missing_requirements"] = self.missing_requirements()
        data["is_review_ready"] = self.is_review_ready()
        return data


@dataclass
class PolymorphicSeedRecord:
    """A typed seed record that keeps facts, values, analogies, and futures separate."""

    seed_id: str = ""
    kind: str = SEED_KIND_UNKNOWN
    title: str = ""
    claim: str = ""
    claim_scope: str = CLAIM_SCOPE_CONTEXT
    status: str = STATUS_DRAFT
    confidence: float = 0.0
    source_refs: List[SourceRef] = field(default_factory=list)
    uncertainty_statement: str = ""
    review_notes: List[str] = field(default_factory=list)
    tradeoff_pairs: List[str] = field(default_factory=list)
    immutable_risks: List[str] = field(default_factory=list)
    operational_assumption: bool = False
    used_for: List[str] = field(default_factory=list)
    not_used_for: List[str] = field(default_factory=list)
    promotion_blockers: List[str] = field(default_factory=list)

    def missing_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.seed_id:
            missing.append("seed_id")
        if self.kind == SEED_KIND_UNKNOWN:
            missing.append("kind")
        if not self.title:
            missing.append("title")
        if not self.claim:
            missing.append("claim")
        if not self.uncertainty_statement:
            missing.append("uncertainty_statement")
        if not self.review_notes:
            missing.append("review_notes")
        if not self.source_refs:
            missing.append("source_refs")
        for source in self.source_refs:
            if not source.is_review_ready():
                missing.append(f"source_ref:{source.source_id or 'unknown'}")
        return missing

    def is_speculative_future_model(self) -> bool:
        return self.kind == SEED_KIND_SPECULATIVE_FUTURE_MODEL

    def is_review_ready(self) -> bool:
        return not self.missing_requirements() and not self.safety_violations()

    def safety_violations(self) -> List[str]:
        violations: List[str] = []
        if self.is_speculative_future_model():
            if self.status != STATUS_LOW_CONFIDENCE_PREDICTIVE:
                violations.append("speculative_status_must_be_low_confidence_predictive")
            if self.claim_scope not in SPECULATIVE_KIND_ALLOWED_SCOPES:
                violations.append("speculative_scope_must_not_be_current_fact")
            if self.operational_assumption:
                violations.append("speculative_model_cannot_be_operational_assumption")
            if "current factual claims" not in self.not_used_for:
                violations.append("speculative_model_must_block_current_factual_claims")
            if "autonomous action" not in self.not_used_for:
                violations.append("speculative_model_must_block_autonomous_action")
        if self.operational_assumption and self.confidence < 0.95:
            violations.append("operational_assumption_requires_high_confidence")
        if self.confidence < 0.0 or self.confidence > 1.0:
            violations.append("confidence_out_of_range")
        return violations

    def can_promote_to_fact_candidate(self) -> bool:
        if self.kind not in FACT_ELIGIBLE_KINDS:
            return False
        if self.claim_scope not in {CLAIM_SCOPE_MEASUREMENT, CLAIM_SCOPE_CONSTRAINT}:
            return False
        if self.status != STATUS_SOURCE_BACKED:
            return False
        if self.confidence < 0.95:
            return False
        if self.missing_requirements() or self.safety_violations():
            return False
        return True

    def can_drive_autonomous_action(self) -> bool:
        return False

    def to_dict(self) -> dict:
        data = asdict(self)
        data["source_refs"] = [source.to_dict() for source in self.source_refs]
        data["missing_requirements"] = self.missing_requirements()
        data["safety_violations"] = self.safety_violations()
        data["is_review_ready"] = self.is_review_ready()
        data["can_promote_to_fact_candidate"] = self.can_promote_to_fact_candidate()
        data["can_drive_autonomous_action"] = self.can_drive_autonomous_action()
        return data


@dataclass
class PolymorphicSeedRegistry:
    """Read-only registry for typed seed records."""

    registry_id: str = ""
    records: List[PolymorphicSeedRecord] = field(default_factory=list)
    runtime_enabled: bool = False
    promotion_enabled: bool = False
    autonomous_action_enabled: bool = False

    def safety_violations(self) -> List[str]:
        violations: List[str] = []
        if self.runtime_enabled:
            violations.append("runtime_enabled")
        if self.promotion_enabled:
            violations.append("promotion_enabled")
        if self.autonomous_action_enabled:
            violations.append("autonomous_action_enabled")
        for record in self.records:
            for violation in record.safety_violations():
                violations.append(f"{record.seed_id or 'unknown'}:{violation}")
        return violations

    def missing_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.registry_id:
            missing.append("registry_id")
        if not self.records:
            missing.append("records")
        if self.safety_violations():
            missing.append("read_only_safety")
        return missing

    def is_read_only_safe(self) -> bool:
        return not self.safety_violations()

    def by_kind(self, kind: str) -> List[PolymorphicSeedRecord]:
        return [record for record in self.records if record.kind == kind]

    def to_dict(self) -> dict:
        return {
            "registry_id": self.registry_id,
            "records": [record.to_dict() for record in self.records],
            "runtime_enabled": self.runtime_enabled,
            "promotion_enabled": self.promotion_enabled,
            "autonomous_action_enabled": self.autonomous_action_enabled,
            "safety_violations": self.safety_violations(),
            "missing_requirements": self.missing_requirements(),
            "is_read_only_safe": self.is_read_only_safe(),
        }


def speculative_future_model_record(
    seed_id: str,
    title: str,
    claim: str,
    source_refs: List[SourceRef],
    uncertainty_statement: str,
    review_notes: List[str],
) -> PolymorphicSeedRecord:
    """Construct a safe speculative future model seed.

    The returned record is explicitly barred from current factual claims and
    autonomous action. It can be used for stress testing and safety planning.
    """

    return PolymorphicSeedRecord(
        seed_id=seed_id,
        kind=SEED_KIND_SPECULATIVE_FUTURE_MODEL,
        title=title,
        claim=claim,
        claim_scope=CLAIM_SCOPE_FORECAST,
        status=STATUS_LOW_CONFIDENCE_PREDICTIVE,
        confidence=0.1,
        source_refs=list(source_refs),
        uncertainty_statement=uncertainty_statement,
        review_notes=list(review_notes),
        operational_assumption=False,
        used_for=["stress testing", "safety planning"],
        not_used_for=["current factual claims", "public authority", "autonomous action"],
    )
