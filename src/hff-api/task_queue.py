"""Dry-run task queue for bounded Better Next assistance.

The queue records proposed work and classifies it. It never executes tasks.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class TaskDecision(str, Enum):
    DRY_RUN_ONLY = "dry_run_only"
    REQUIRES_APPROVAL = "requires_approval"
    HARD_DENY = "hard_deny"


HARD_DENY_TERMS = {
    "payment",
    "payments",
    "send money",
    "loan",
    "weapon",
    "weapons",
    "dead-man",
    "dead man",
    "bioweapon",
    "chemical weapon",
    "explosive",
    "sensor",
    "sensors",
    "surveillance",
    "track location",
    "private key",
    "secret token",
    "password",
    "drive",
    "vehicle control",
    "physical control",
    "medical authority",
    "legal authority",
    "financial authority",
    "impersonate",
    "dox",
    "doxx",
    "harass",
}

APPROVAL_REQUIRED_TERMS = {
    "merge",
    "deploy",
    "release",
    "public",
    "runtime",
    "write",
    "delete",
    "reset",
    "clean",
    "force push",
    "start agent",
    "background worker",
    "sync",
    "network",
    "credential",
    "api key",
    "personal data",
}


@dataclass(frozen=True)
class QueuedTask:
    title: str
    prompt: str
    decision: TaskDecision
    reasons: tuple[str, ...]


def _matches(text: str, terms: Iterable[str]) -> list[str]:
    lowered = text.lower()
    return sorted(term for term in terms if term in lowered)


def classify_task(title: str, prompt: str) -> tuple[TaskDecision, tuple[str, ...]]:
    """Classify a proposed task without executing it."""
    combined = f"{title}\n{prompt}"

    hard_denies = _matches(combined, HARD_DENY_TERMS)
    if hard_denies:
        return TaskDecision.HARD_DENY, tuple(
            f"hard_denied:{term}" for term in hard_denies
        )

    approvals = _matches(combined, APPROVAL_REQUIRED_TERMS)
    if approvals:
        return TaskDecision.REQUIRES_APPROVAL, tuple(
            f"approval_required:{term}" for term in approvals
        )

    return TaskDecision.DRY_RUN_ONLY, ("non_executing_dry_run",)


def enqueue_dry_run(title: str, prompt: str) -> QueuedTask:
    """Return a queued task record. This function performs no side effects."""
    decision, reasons = classify_task(title, prompt)
    return QueuedTask(
        title=title,
        prompt=prompt,
        decision=decision,
        reasons=reasons,
    )
