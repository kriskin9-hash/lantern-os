#!/usr/bin/env python3
"""Complete sensor profile baseline for HFF observations.

A sensor is any bounded evidence source that can propose observations or trigger
review. APIs are only one sensor type. This module defines conservative
data-only contracts; it does not poll sources or change runtime behavior.
"""

from dataclasses import asdict, dataclass, field
from typing import Dict, List

from perfect_adjacent_review import (
    CHECK_FAILED,
    CHECK_NEEDS_REVIEW,
    CHECK_PASSED,
    RISK_HIGH,
    RISK_LOW,
    SOURCE_KIND_UNKNOWN,
    SOURCE_QUALITY_UNKNOWN,
)

SENSOR_TYPE_API = "api"
SENSOR_TYPE_DATASET = "dataset"
SENSOR_TYPE_WEBPAGE = "webpage"
SENSOR_TYPE_REPORT = "report"
SENSOR_TYPE_RSS = "rss"
SENSOR_TYPE_GITHUB = "github"
SENSOR_TYPE_LOCAL_REPO = "local_repo"
SENSOR_TYPE_RUNTIME_ENDPOINT = "runtime_endpoint"
SENSOR_TYPE_LOG = "log"
SENSOR_TYPE_AUDIT_TRAIL = "audit_trail"
SENSOR_TYPE_HUMAN_REVIEW = "human_review"
SENSOR_TYPE_LLM_PANEL = "llm_panel"
SENSOR_TYPE_SECURITY_TELEMETRY = "security_telemetry"
SENSOR_TYPE_INCIDENT_DATABASE = "incident_database"
SENSOR_TYPE_FORECAST = "forecast"
SENSOR_TYPE_PHYSICAL_WORLD_FEED = "physical_world_feed"

EVIDENCE_CLASS_MEASUREMENT = "measurement"
EVIDENCE_CLASS_OBSERVATION = "observation"
EVIDENCE_CLASS_INTERPRETATION = "interpretation"
EVIDENCE_CLASS_FORECAST = "forecast"
EVIDENCE_CLASS_REVIEW = "review"
EVIDENCE_CLASS_LOG = "log"
EVIDENCE_CLASS_UNKNOWN = "unknown"

OBSERVATION_STATUS_PROPOSED = "proposed"
OBSERVATION_STATUS_REVIEWED = "reviewed"
OBSERVATION_STATUS_ACCEPTED = "accepted"
OBSERVATION_STATUS_REJECTED = "rejected"
OBSERVATION_STATUS_SUPERSEDED = "superseded"


@dataclass
class SensorPermission:
    """Permission envelope for what a sensor is allowed to affect.

    Default permissions are intentionally inert. A sensor may collect evidence
    without being allowed to update seed data, world-model beliefs, public
    output, or autonomy.
    """

    can_update_seed: bool = False
    can_update_world_model: bool = False
    can_trigger_review: bool = True
    can_trigger_public_output: bool = False
    can_trigger_autonomy: bool = False

    def grants_runtime_effect(self) -> bool:
        return (
            self.can_update_seed
            or self.can_update_world_model
            or self.can_trigger_public_output
            or self.can_trigger_autonomy
        )

    def is_conservative_default(self) -> bool:
        return (
            self.can_update_seed is False
            and self.can_update_world_model is False
            and self.can_trigger_public_output is False
            and self.can_trigger_autonomy is False
        )


@dataclass
class SensorProvenance:
    """Provenance fields for a sensor or observation."""

    source_ref: str = ""
    observed_at: str = ""
    ingested_at: str = ""
    sensor_version: str = ""
    collector: str = ""
    raw_artifact_ref: str = ""
    transformation_steps: List[str] = field(default_factory=list)
    output_hash: str = ""

    def has_minimum_provenance(self) -> bool:
        return bool(self.source_ref and self.observed_at and self.ingested_at)


@dataclass
class SensorRiskReview:
    """Risk review for a sensor before it is trusted or permissioned."""

    privacy_risk: str = RISK_HIGH
    dual_use_risk: str = RISK_HIGH
    p_doom_relevance: str = CHECK_NEEDS_REVIEW
    security_relevance: str = CHECK_NEEDS_REVIEW
    spoofing_risk: str = RISK_HIGH
    tamper_risk: str = RISK_HIGH
    calibration_status: str = CHECK_NEEDS_REVIEW
    known_failure_modes: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)

    def is_low_risk_for_runtime_effects(self) -> bool:
        return (
            self.privacy_risk == RISK_LOW
            and self.dual_use_risk == RISK_LOW
            and self.spoofing_risk == RISK_LOW
            and self.tamper_risk == RISK_LOW
            and self.calibration_status == CHECK_PASSED
            and self.security_relevance == CHECK_PASSED
        )


@dataclass
class SensorProfile:
    """A complete sensor definition, not just an API connector."""

    sensor_id: str = ""
    sensor_name: str = ""
    sensor_type: str = SENSOR_TYPE_API
    source_url_or_location: str = ""
    poll_method: str = ""
    domain: str = ""
    authority_level: str = "untrusted"
    source_kind: str = SOURCE_KIND_UNKNOWN
    source_quality: str = SOURCE_QUALITY_UNKNOWN
    evidence_class: str = EVIDENCE_CLASS_UNKNOWN
    freshness_expected: str = ""
    staleness_policy: str = "mark_stale_and_require_review"
    confidence_contribution: str = "proposed_observation_only"
    permission: SensorPermission = field(default_factory=SensorPermission)
    provenance: SensorProvenance = field(default_factory=SensorProvenance)
    risk_review: SensorRiskReview = field(default_factory=SensorRiskReview)
    required_review_gates: List[str] = field(default_factory=lambda: [
        "source_classification",
        "provenance",
        "freshness",
        "spoofing_tamper_review",
        "privacy_dual_use_review",
    ])
    revision_triggers: List[str] = field(default_factory=list)
    rollback_or_ignore_rule: str = "ignore_if_stale_spoofed_or_unreviewed"

    def missing_profile_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.sensor_id:
            missing.append("sensor_id")
        if not self.sensor_name:
            missing.append("sensor_name")
        if not self.sensor_type:
            missing.append("sensor_type")
        if not self.source_url_or_location:
            missing.append("source_url_or_location")
        if not self.domain:
            missing.append("domain")
        if self.source_kind == SOURCE_KIND_UNKNOWN:
            missing.append("source_kind")
        if self.source_quality == SOURCE_QUALITY_UNKNOWN:
            missing.append("source_quality")
        if self.evidence_class == EVIDENCE_CLASS_UNKNOWN:
            missing.append("evidence_class")
        if not self.provenance.has_minimum_provenance():
            missing.append("minimum_provenance")
        return missing

    def is_profile_complete(self) -> bool:
        return not self.missing_profile_requirements()

    def can_have_runtime_effect(self) -> bool:
        if not self.is_profile_complete():
            return False
        if not self.risk_review.is_low_risk_for_runtime_effects():
            return False
        return self.permission.grants_runtime_effect()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["missing_profile_requirements"] = self.missing_profile_requirements()
        data["is_profile_complete"] = self.is_profile_complete()
        data["can_have_runtime_effect"] = self.can_have_runtime_effect()
        return data


@dataclass
class SensorObservation:
    """Append-only observation proposed by a sensor."""

    observation_id: str = ""
    sensor_id: str = ""
    claim_text: str = ""
    observed_value: str = ""
    evidence_class: str = EVIDENCE_CLASS_UNKNOWN
    status: str = OBSERVATION_STATUS_PROPOSED
    confidence_assessment_ref: str = ""
    source_refs: List[str] = field(default_factory=list)
    provenance: SensorProvenance = field(default_factory=SensorProvenance)
    review_notes: List[str] = field(default_factory=list)
    supersedes: List[str] = field(default_factory=list)
    superseded_by: List[str] = field(default_factory=list)

    def missing_observation_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.observation_id:
            missing.append("observation_id")
        if not self.sensor_id:
            missing.append("sensor_id")
        if not self.claim_text:
            missing.append("claim_text")
        if self.evidence_class == EVIDENCE_CLASS_UNKNOWN:
            missing.append("evidence_class")
        if not self.source_refs:
            missing.append("source_refs")
        if not self.provenance.has_minimum_provenance():
            missing.append("minimum_provenance")
        return missing

    def can_be_accepted(self) -> bool:
        return (
            self.status == OBSERVATION_STATUS_REVIEWED
            and not self.missing_observation_requirements()
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["missing_observation_requirements"] = (
            self.missing_observation_requirements()
        )
        data["can_be_accepted"] = self.can_be_accepted()
        return data
