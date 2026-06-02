#!/usr/bin/env python3
"""Perfect-adjacent review contract for high-impact HFF outputs.

This module does not make the system perfect. It defines a small, testable
contract for best-effort defensive review before high-impact publication,
capability advertising, best-current outcome claims, or autonomous action.
"""

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Tuple

CHECK_PASSED = "passed"
CHECK_NEEDS_REVIEW = "needs_review"
CHECK_FAILED = "failed"

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"

DEFENSE_MODE_BEST_EFFORT = "best_effort"

CONFIDENCE_ASSESSMENT_QUALITATIVE = "qualitative_engineering_judgment"
PDOOM_CREDIBLE_NONZERO_RISK = "credible_nonzero_risk"

SOURCE_KIND_STANDARD = "standard"
SOURCE_KIND_FORECAST = "forecast"
SOURCE_KIND_SCENARIO = "scenario"
SOURCE_KIND_ROADMAP = "roadmap"
SOURCE_KIND_EMPIRICAL = "empirical"
SOURCE_KIND_AUDIT = "audit"
SOURCE_KIND_SPECULATIVE = "speculative"
SOURCE_KIND_UNKNOWN = "unknown"

SOURCE_QUALITY_UNKNOWN = "unknown"
SOURCE_QUALITY_PUBLIC_WHITE_PAPER = "public_white_paper"
SOURCE_QUALITY_OFFICIAL_STANDARD = "official_standard"
SOURCE_QUALITY_PEER_REVIEWED = "peer_reviewed"
SOURCE_QUALITY_AUDITED = "audited"
SOURCE_QUALITY_SCENARIO_FORECAST = "scenario_forecast"

CLAIM_SCOPE_UNKNOWN = "unknown"
CLAIM_SCOPE_DESIGN_GOAL = "design_goal"
CLAIM_SCOPE_FORECAST = "forecast"
CLAIM_SCOPE_OPERATIONAL_EVIDENCE = "operational_evidence"
CLAIM_SCOPE_IMPLEMENTATION_EVIDENCE = "implementation_evidence"

IMPOSSIBLE_CLAIM_KEYS: Tuple[str, ...] = (
    "perfect_safety",
    "perfect_truth",
    "perfect_benevolence",
    "perfect_foresight",
    "complete_understanding",
    "knows_all_unknown_unknowns",
    "guaranteed_privacy",
    "guaranteed_defense",
    "divine_or_sacred_authority",
    "prophecy_or_destiny",
    "final_moral_authority",
    "automatic_future_model_trust",
)

INFERRED_IMPOSSIBLE_CLAIM_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("entirely safe", "perfect_safety"),
    ("perfectly safe", "perfect_safety"),
    ("guarantee safety", "perfect_safety"),
    ("guaranteed safety", "perfect_safety"),
    ("perfect truth", "perfect_truth"),
    ("perfect benevolence", "perfect_benevolence"),
    ("omnibenevolent", "perfect_benevolence"),
    ("perfect foresight", "perfect_foresight"),
    ("complete understanding", "complete_understanding"),
    ("understands everything", "complete_understanding"),
    ("all unknown unknowns", "knows_all_unknown_unknowns"),
    ("guaranteed privacy", "guaranteed_privacy"),
    ("guaranteed defense", "guaranteed_defense"),
    ("guaranteed protection", "guaranteed_defense"),
    ("divine authority", "divine_or_sacred_authority"),
    ("sacred authority", "divine_or_sacred_authority"),
    ("holy artifact", "divine_or_sacred_authority"),
    ("prophecy", "prophecy_or_destiny"),
    ("destiny", "prophecy_or_destiny"),
    ("final moral authority", "final_moral_authority"),
    ("morally final", "final_moral_authority"),
    ("future model can inherit trust", "automatic_future_model_trust"),
    ("automatic future model trust", "automatic_future_model_trust"),
)

CRITICAL_REVIEW_CHECKS: Tuple[str, ...] = (
    "source_quality",
    "maturity_level",
    "reasoning_integrity",
    "unknown_unknowns",
    "empathetic_guardian",
    "unauthorized_trust",
    "temporal_provenance",
    "dual_use_privacy",
    "sacralization_risk",
    "human_accountability",
    "capability_advertising",
    "sensor_focus",
)

BEST_CURRENT_REQUIRED_CHECKS: Tuple[str, ...] = (
    "source_quality",
    "reasoning_integrity",
    "unknown_unknowns",
    "empathetic_guardian",
    "unauthorized_trust",
    "temporal_provenance",
    "dual_use_privacy",
    "human_accountability",
)

REQUIRED_RUNTIME_HOOKS: Tuple[str, ...] = (
    "status_endpoint_review_gate",
    "world_status_review_gate",
    "capability_advertising_gate",
    "autonomous_action_gate",
    "sensor_question_feed",
)


@dataclass
class ConfidenceAssessment:
    """Discloses whether a confidence claim is calibrated or qualitative."""

    assessment_type: str = CONFIDENCE_ASSESSMENT_QUALITATIVE
    calibrated_probability: bool = False
    basis_evidence: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    validation_status: str = CHECK_NEEDS_REVIEW
    last_updated: str = ""
    revision_triggers: List[str] = field(default_factory=list)

    def is_calibrated(self) -> bool:
        return self.calibrated_probability is True

    def is_valid_for_public_probability(self) -> bool:
        return self.is_calibrated() and self.validation_status == CHECK_PASSED


@dataclass
class PDoomContext:
    """Keeps p-doom as a credible risk context, not proof or panic authority."""

    risk_status: str = PDOOM_CREDIBLE_NONZERO_RISK
    proof_of_doom: bool = False
    panic_authority: bool = False
    calibrated_probability: bool = False
    source_refs: List[str] = field(default_factory=list)
    uncertainty_summary: str = "credible nonzero catastrophic risk; not a proof"

    def is_valid_context(self) -> bool:
        return (
            self.risk_status == PDOOM_CREDIBLE_NONZERO_RISK
            and self.proof_of_doom is False
            and self.panic_authority is False
        )


@dataclass
class SourceClassification:
    """Classifies a source before its claims can be used by the review model."""

    source_url: str = ""
    source_title: str = ""
    source_kind: str = SOURCE_KIND_UNKNOWN
    source_quality: str = SOURCE_QUALITY_UNKNOWN
    claim_scope: str = CLAIM_SCOPE_UNKNOWN
    operational_assumption: bool = False
    external_validation_status: str = "not_found"
    notes: List[str] = field(default_factory=list)

    def is_operational_evidence(self) -> bool:
        return (
            self.operational_assumption is True
            and self.claim_scope == CLAIM_SCOPE_OPERATIONAL_EVIDENCE
            and self.source_quality in {
                SOURCE_QUALITY_AUDITED,
                SOURCE_QUALITY_PEER_REVIEWED,
            }
        )


@dataclass
class CatastrophicRiskReview:
    """Tracks frontier/catastrophic risk buckets before runtime use."""

    bio_chemical: str = CHECK_NEEDS_REVIEW
    cybersecurity: str = CHECK_NEEDS_REVIEW
    self_improvement: str = CHECK_NEEDS_REVIEW
    long_range_autonomy: str = CHECK_NEEDS_REVIEW
    autonomous_replication_adaptation: str = CHECK_NEEDS_REVIEW
    safeguard_undermining: str = CHECK_NEEDS_REVIEW
    model_theft: str = CHECK_NEEDS_REVIEW
    insider_risk: str = CHECK_NEEDS_REVIEW
    exfiltration_risk: str = CHECK_NEEDS_REVIEW
    nuclear_radiological: str = CHECK_NEEDS_REVIEW
    evidence_refs: List[str] = field(default_factory=list)

    def check_map(self) -> Dict[str, str]:
        return {
            "bio_chemical": self.bio_chemical,
            "cybersecurity": self.cybersecurity,
            "self_improvement": self.self_improvement,
            "long_range_autonomy": self.long_range_autonomy,
            "autonomous_replication_adaptation": self.autonomous_replication_adaptation,
            "safeguard_undermining": self.safeguard_undermining,
            "model_theft": self.model_theft,
            "insider_risk": self.insider_risk,
            "exfiltration_risk": self.exfiltration_risk,
            "nuclear_radiological": self.nuclear_radiological,
        }

    def failed_checks(self) -> List[str]:
        return [name for name, value in self.check_map().items() if value == CHECK_FAILED]

    def needs_review_checks(self) -> List[str]:
        return [
            name for name, value in self.check_map().items()
            if value == CHECK_NEEDS_REVIEW
        ]

    def is_cleared(self) -> bool:
        return not self.failed_checks() and not self.needs_review_checks()


@dataclass
class SecurityPosture:
    """Tracks security posture evidence before trusting runtime or public claims."""

    model_weight_security: str = CHECK_NEEDS_REVIEW
    algorithmic_secret_security: str = CHECK_NEEDS_REVIEW
    access_controls: str = CHECK_NEEDS_REVIEW
    audit_logging: str = CHECK_NEEDS_REVIEW
    insider_risk: str = CHECK_NEEDS_REVIEW
    exfiltration_risk: str = CHECK_NEEDS_REVIEW
    self_exfiltration_scenario: str = CHECK_NEEDS_REVIEW
    evidence_refs: List[str] = field(default_factory=list)

    def check_map(self) -> Dict[str, str]:
        return {
            "model_weight_security": self.model_weight_security,
            "algorithmic_secret_security": self.algorithmic_secret_security,
            "access_controls": self.access_controls,
            "audit_logging": self.audit_logging,
            "insider_risk": self.insider_risk,
            "exfiltration_risk": self.exfiltration_risk,
            "self_exfiltration_scenario": self.self_exfiltration_scenario,
        }

    def missing_security_controls(self) -> List[str]:
        return [
            name for name, value in self.check_map().items()
            if value != CHECK_PASSED
        ]

    def is_cleared(self) -> bool:
        return not self.missing_security_controls()


@dataclass
class RuntimeHookEvidence:
    """Requires hook attachment evidence before runtime enforcement is trusted."""

    required_hooks: List[str] = field(
        default_factory=lambda: list(REQUIRED_RUNTIME_HOOKS)
    )
    attached_hooks: Dict[str, bool] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)
    last_verified: str = ""

    def missing_runtime_hooks(self) -> List[str]:
        return [
            hook for hook in self.required_hooks
            if self.attached_hooks.get(hook) is not True
        ]

    def is_runtime_enforcement_ready(self) -> bool:
        return not self.missing_runtime_hooks()


@dataclass
class PerfectAdjacentReview:
    """Review record for high-impact conclusions.

    The record is intentionally conservative: a failed or needs-review critical
    check blocks publication, capability advertising, best-current outcome
    claims, and autonomous action.
    """

    source_quality: str = CHECK_NEEDS_REVIEW
    maturity_level: str = CHECK_NEEDS_REVIEW
    reasoning_integrity: str = CHECK_NEEDS_REVIEW
    unknown_unknowns: str = CHECK_NEEDS_REVIEW
    empathetic_guardian: str = CHECK_NEEDS_REVIEW
    unauthorized_trust: str = CHECK_NEEDS_REVIEW
    temporal_provenance: str = CHECK_NEEDS_REVIEW
    dual_use_privacy: str = CHECK_NEEDS_REVIEW
    sacralization_risk: str = CHECK_NEEDS_REVIEW
    human_accountability: str = CHECK_NEEDS_REVIEW
    capability_advertising: str = CHECK_NEEDS_REVIEW
    sensor_focus: str = CHECK_NEEDS_REVIEW

    defense_mode: str = DEFENSE_MODE_BEST_EFFORT
    defense_guarantee: bool = False
    fallibility_label_present: bool = True
    uncertainty_visible: bool = True
    challenge_right_preserved: bool = True

    impossible_claims: List[str] = field(default_factory=list)
    capability_advertising_allowed: bool = False
    advertised_capabilities: List[str] = field(default_factory=list)
    advertising_risk_level: str = RISK_HIGH
    sensor_questions: List[str] = field(default_factory=list)
    sensor_refs: List[str] = field(default_factory=list)

    best_current_outcome: str = ""
    candidate_options_considered: List[str] = field(default_factory=list)
    rejected_options_with_reasons: List[str] = field(default_factory=list)
    revision_triggers: List[str] = field(default_factory=list)
    monitoring_plan: str = ""

    polling_interval_seconds: int = 0
    panic_risk_level: str = RISK_HIGH
    calming_guidance_allowed: bool = False

    runtime_enforcement_ready: bool = False
    required_runtime_hooks: List[str] = field(
        default_factory=lambda: list(REQUIRED_RUNTIME_HOOKS)
    )
    runtime_hook_evidence: RuntimeHookEvidence = field(
        default_factory=RuntimeHookEvidence
    )

    confidence_assessment: ConfidenceAssessment = field(
        default_factory=ConfidenceAssessment
    )
    p_doom_context: PDoomContext = field(default_factory=PDoomContext)
    catastrophic_risk_review: CatastrophicRiskReview = field(
        default_factory=CatastrophicRiskReview
    )
    security_posture: SecurityPosture = field(default_factory=SecurityPosture)
    source_classifications: List[SourceClassification] = field(default_factory=list)

    human_review_required: bool = True
    safe_to_publish: bool = False
    safe_to_act_autonomously: bool = False

    evidence_refs: List[str] = field(default_factory=list)
    review_notes: List[str] = field(default_factory=list)

    def check_map(self) -> Dict[str, str]:
        return {name: getattr(self, name) for name in CRITICAL_REVIEW_CHECKS}

    def failed_checks(self) -> List[str]:
        return [name for name, value in self.check_map().items() if value == CHECK_FAILED]

    def needs_review_checks(self) -> List[str]:
        return [
            name for name, value in self.check_map().items()
            if value == CHECK_NEEDS_REVIEW
        ]

    def _text_for_impossible_claim_scan(self) -> str:
        parts = []
        parts.extend(self.advertised_capabilities)
        parts.extend(self.review_notes)
        parts.append(self.best_current_outcome)
        parts.append(self.monitoring_plan)
        return "\n".join(part for part in parts if part).lower()

    def inferred_impossible_claims(self) -> List[str]:
        text = self._text_for_impossible_claim_scan()
        inferred: List[str] = []
        for pattern, claim in INFERRED_IMPOSSIBLE_CLAIM_PATTERNS:
            if pattern in text and claim not in inferred:
                inferred.append(claim)
        return inferred

    def impossible_claim_violations(self) -> List[str]:
        violations: List[str] = []
        for claim in self.impossible_claims:
            if claim in IMPOSSIBLE_CLAIM_KEYS and claim not in violations:
                violations.append(claim)
        for claim in self.inferred_impossible_claims():
            if claim not in violations:
                violations.append(claim)
        return violations

    def has_impossible_claims(self) -> bool:
        return bool(self.impossible_claim_violations())

    def is_valid_best_effort_defense(self) -> bool:
        return (
            self.defense_mode == DEFENSE_MODE_BEST_EFFORT
            and self.defense_guarantee is False
            and self.fallibility_label_present is True
            and self.uncertainty_visible is True
            and self.challenge_right_preserved is True
            and self.p_doom_context.is_valid_context()
            and not self.has_impossible_claims()
        )

    def missing_best_current_outcome_requirements(self) -> List[str]:
        missing: List[str] = []
        if not self.is_valid_best_effort_defense():
            missing.append("valid_best_effort_defense")
        for check_name in BEST_CURRENT_REQUIRED_CHECKS:
            if getattr(self, check_name) != CHECK_PASSED:
                missing.append(check_name)
        if not self.best_current_outcome:
            missing.append("best_current_outcome")
        if len(self.candidate_options_considered) < 2:
            missing.append("candidate_options_considered")
        if not self.rejected_options_with_reasons:
            missing.append("rejected_options_with_reasons")
        if not self.revision_triggers:
            missing.append("revision_triggers")
        if not self.monitoring_plan:
            missing.append("monitoring_plan")
        if self.sensor_focus == CHECK_PASSED:
            if not self.sensor_questions:
                missing.append("sensor_questions")
            if not self.sensor_refs:
                missing.append("sensor_refs")
        else:
            missing.append("sensor_focus")
        if self.panic_risk_level in (RISK_MEDIUM, RISK_HIGH):
            if self.calming_guidance_allowed and (
                self.human_review_required or not self.safe_to_publish
            ):
                missing.append("panic_review_for_calming_guidance")
        return missing

    def can_claim_best_current_outcome(self) -> bool:
        return not self.missing_best_current_outcome_requirements()

    def can_advertise_capability(self) -> bool:
        """Return whether a capability claim may be advertised publicly.

        Capability advertising is a separate gate from normal publication. A
        system can be allowed to publish a bounded status update while still
        being forbidden from promoting broad capability claims.
        """
        if not self.is_valid_best_effort_defense():
            return False
        if self.capability_advertising != CHECK_PASSED:
            return False
        if self.sensor_focus != CHECK_PASSED:
            return False
        if self.failed_checks() or self.needs_review_checks():
            return False
        if self.advertising_risk_level != RISK_LOW:
            return False
        if self.human_review_required:
            return False
        return bool(self.capability_advertising_allowed)

    def can_publish(self) -> bool:
        if not self.is_valid_best_effort_defense():
            return False
        if self.failed_checks() or self.needs_review_checks():
            return False
        return bool(self.safe_to_publish)

    def missing_runtime_hooks(self) -> List[str]:
        return self.runtime_hook_evidence.missing_runtime_hooks()

    def can_act_autonomously(self) -> bool:
        if not self.is_valid_best_effort_defense():
            return False
        if not self.runtime_enforcement_ready:
            return False
        if not self.runtime_hook_evidence.is_runtime_enforcement_ready():
            return False
        if self.failed_checks() or self.needs_review_checks():
            return False
        if self.human_review_required:
            return False
        return bool(self.safe_to_act_autonomously)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["failed_checks"] = self.failed_checks()
        data["needs_review_checks"] = self.needs_review_checks()
        data["inferred_impossible_claims"] = self.inferred_impossible_claims()
        data["impossible_claim_violations"] = self.impossible_claim_violations()
        data["missing_best_current_outcome_requirements"] = (
            self.missing_best_current_outcome_requirements()
        )
        data["missing_runtime_hooks"] = self.missing_runtime_hooks()
        data["can_publish"] = self.can_publish()
        data["can_claim_best_current_outcome"] = self.can_claim_best_current_outcome()
        data["can_advertise_capability"] = self.can_advertise_capability()
        data["can_act_autonomously"] = self.can_act_autonomously()
        return data


def passing_human_reviewed_record(evidence_refs=None) -> PerfectAdjacentReview:
    """Construct a record that may publish after all checks pass.

    This helper is for tests and future integration examples. It still does not
    authorize capability advertising, best-current outcome claims, or autonomous
    action by default.
    """
    values = {name: CHECK_PASSED for name in CRITICAL_REVIEW_CHECKS}
    return PerfectAdjacentReview(
        **values,
        human_review_required=False,
        safe_to_publish=True,
        capability_advertising_allowed=False,
        safe_to_act_autonomously=False,
        evidence_refs=list(evidence_refs or []),
    )


def blocked_unknown_unknown_record(note: str = "structural uncertainty") -> PerfectAdjacentReview:
    """Construct a conservative blocked record for structural uncertainty."""
    values = {name: CHECK_PASSED for name in CRITICAL_REVIEW_CHECKS}
    values["unknown_unknowns"] = CHECK_NEEDS_REVIEW
    return PerfectAdjacentReview(
        **values,
        human_review_required=True,
        safe_to_publish=False,
        capability_advertising_allowed=False,
        safe_to_act_autonomously=False,
        review_notes=[note],
    )


def blocked_capability_advertising_record(
    advertised_capabilities=None,
    sensor_questions=None,
    note: str = "advertising risk is not yet bounded",
) -> PerfectAdjacentReview:
    """Construct a record that blocks public capability promotion.

    Use this when the system should focus sensors/review on whether advertising
    a capability could cause trust, panic, privacy, dual-use, or sacralization
    harms.
    """
    values = {name: CHECK_PASSED for name in CRITICAL_REVIEW_CHECKS}
    values["capability_advertising"] = CHECK_NEEDS_REVIEW
    values["sensor_focus"] = CHECK_NEEDS_REVIEW
    return PerfectAdjacentReview(
        **values,
        human_review_required=True,
        safe_to_publish=False,
        capability_advertising_allowed=False,
        safe_to_act_autonomously=False,
        advertised_capabilities=list(advertised_capabilities or []),
        sensor_questions=list(sensor_questions or []),
        advertising_risk_level=RISK_HIGH,
        review_notes=[note],
    )
