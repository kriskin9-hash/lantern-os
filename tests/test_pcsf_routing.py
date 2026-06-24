from convergence_io.pcsf import ProviderRegistry, ProviderState
from convergence_io.pcsf_routing import (
    EvidenceContract,
    ExecutionBoundary,
    ExecutionReceipt,
    FailureClass,
    ProviderCapability,
    RouteEngine,
    RouteRequest,
    RouteStatus,
)


def registry_with(*provider_ids: str) -> ProviderRegistry:
    registry = ProviderRegistry()
    for priority, provider_id in enumerate(provider_ids):
        registry.register(provider_id, priority=priority)
        registry.get(provider_id).state = ProviderState.AVAILABLE
    return registry


def engine() -> RouteEngine:
    registry = registry_with("ollama", "anthropic")
    return RouteEngine(
        registry,
        [
            ProviderCapability(
                provider_id="ollama",
                model_id="ouro:latest",
                boundary=ExecutionBoundary.LOCAL,
                capabilities={"chat", "code"},
                estimated_cost_usd=0.0,
            ),
            ProviderCapability(
                provider_id="anthropic",
                model_id="claude-sonnet",
                boundary=ExecutionBoundary.CLOUD_APPROVED,
                capabilities={"chat", "code", "tools", "json"},
                estimated_cost_usd=0.25,
            ),
        ],
    )


def evidence() -> EvidenceContract:
    return EvidenceContract(
        required_artifacts=("test_report",),
        required_checks=("tests_pass",),
        require_exit_code_zero=True,
    )


def test_local_task_selects_local_provider_and_never_offers_cloud():
    decision = engine().decide(
        RouteRequest(
            task_id="K-1",
            intent="fix_code",
            boundary=ExecutionBoundary.LOCAL,
            required_capabilities={"chat", "code"},
            verification=evidence(),
        )
    )
    assert decision.status is RouteStatus.ALLOWED
    assert decision.selected.provider_id == "ollama"
    assert decision.fallbacks == ()


def test_hybrid_task_requires_explicit_cloud_approval_when_local_lacks_capability():
    decision = engine().decide(
        RouteRequest(
            task_id="K-2",
            intent="tool_review",
            boundary=ExecutionBoundary.HYBRID,
            required_capabilities={"chat", "code", "tools"},
            verification=evidence(),
        )
    )
    assert decision.status is RouteStatus.ESCALATION_REQUIRED
    assert decision.failure_class is FailureClass.CLOUD_APPROVAL_REQUIRED


def test_cloud_approval_requires_secret_scan_before_egress():
    decision = engine().decide(
        RouteRequest(
            task_id="K-3",
            intent="tool_review",
            boundary=ExecutionBoundary.CLOUD_APPROVED,
            required_capabilities={"chat", "code", "tools"},
            cloud_approved=True,
            secret_scan_passed=False,
            verification=evidence(),
        )
    )
    assert decision.status is RouteStatus.BLOCKED
    assert decision.failure_class is FailureClass.SECRET_SCAN_REQUIRED


def test_approved_cloud_task_can_select_cloud_route():
    decision = engine().decide(
        RouteRequest(
            task_id="K-4",
            intent="tool_review",
            boundary=ExecutionBoundary.CLOUD_APPROVED,
            required_capabilities={"chat", "code", "tools"},
            cloud_approved=True,
            secret_scan_passed=True,
            verification=evidence(),
        )
    )
    assert decision.status is RouteStatus.ALLOWED
    assert decision.selected.provider_id == "anthropic"


def test_explicit_cost_ceiling_blocks_paid_cloud_route():
    decision = engine().decide(
        RouteRequest(
            task_id="K-4B",
            intent="tool_review",
            boundary=ExecutionBoundary.CLOUD_APPROVED,
            required_capabilities={"chat", "code", "tools"},
            max_cost_usd=0.0,
            cloud_approved=True,
            secret_scan_passed=True,
            verification=evidence(),
        )
    )
    assert decision.status is RouteStatus.BLOCKED
    assert decision.failure_class is FailureClass.BUDGET_EXCEEDED


def test_missing_evidence_contract_fails_closed():
    decision = engine().decide(
        RouteRequest(
            task_id="K-5",
            intent="fix_code",
            required_capabilities={"chat", "code"},
        )
    )
    assert decision.status is RouteStatus.BLOCKED
    assert decision.failure_class is FailureClass.VERIFICATION_PLAN_REQUIRED


def test_evidence_assessment_requires_artifacts_checks_and_exit_code():
    route = engine().decide(
        RouteRequest(
            task_id="K-6",
            intent="fix_code",
            required_capabilities={"chat", "code"},
            verification=evidence(),
        )
    ).selected
    assessment = engine().assess_evidence(
        evidence(),
        ExecutionReceipt(
            task_id="K-6",
            route=route,
            status="completed",
            exit_code=0,
            artifact_hashes={"test_report": "sha256:abc"},
            checks={"tests_pass": True},
        ),
    )
    assert assessment.complete
    assert assessment.reasons == ()


def test_evidence_assessment_rejects_incomplete_receipt():
    route = engine().decide(
        RouteRequest(
            task_id="K-7",
            intent="fix_code",
            required_capabilities={"chat", "code"},
            verification=evidence(),
        )
    ).selected
    assessment = engine().assess_evidence(
        evidence(),
        ExecutionReceipt(task_id="K-7", route=route, status="failed", exit_code=1),
    )
    assert not assessment.complete
    assert "required zero exit code was not observed" in assessment.reasons
    assert any("missing required artifacts" in reason for reason in assessment.reasons)
