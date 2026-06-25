"""Convergence loop hooks: instrument all execution steps through Σ₀.

The six-stage loop becomes the *default* path for every action:
  Observe → Remember → Reason → Act → Verify → Converge

Hooks capture:
1. Inputs (Observe stage) — what triggered this?
2. Context retrieval (Remember stage) — what do we know?
3. Decision (Reason stage) — what should we do?
4. Execution (Act stage) — did it work?
5. Validation (Verify stage) — did we expect this?
6. Learning (Converge stage) — record the pattern

Each hook lifecycle produces a ConvergenceRecord with full grounding.

Reference: CONVERGANCE-SIGMA0-BRIEFING.md, SIGMA0-COLLAPSE-CERTIFICATE.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import json
import uuid
from functools import wraps


@dataclass
class HookContext:
    """Context carried through a single Convergence loop cycle.

    Accumulates data as the six stages execute, producing a final ConvergenceRecord.
    """
    id: str = field(default_factory=lambda: f"hook-{uuid.uuid4().hex[:8]}")
    stage: str = "init"  # Current stage: observe, remember, reason, act, verify, converge
    timestamp: datetime = field(default_factory=datetime.now)

    # Stage 1: Observe — inputs + trigger
    trigger: Optional[str] = None  # "git-push", "test-run", "api-call", etc.
    inputs: Dict[str, Any] = field(default_factory=dict)
    input_hash: Optional[str] = None

    # Stage 2: Remember — context retrieval
    retrieved_memories: List[str] = field(default_factory=list)  # Memory IDs
    relevant_context: Dict[str, Any] = field(default_factory=dict)

    # Stage 3: Reason — decision formation
    hypothesis: Optional[str] = None  # What we think should happen
    reasoning_trace: List[str] = field(default_factory=list)  # Decision steps

    # Stage 4: Act — execution
    action: Optional[str] = None  # What we executed
    action_args: Dict[str, Any] = field(default_factory=dict)

    # Stage 5: Verify — outcome validation
    expected_output: Optional[Any] = None
    actual_output: Optional[Any] = None
    verification_passed: bool = False
    verification_notes: Optional[str] = None

    # Stage 6: Converge — grounding + record
    grounding_signals: List[str] = field(default_factory=list)
    confidence: float = 0.5
    source: str = "convergence-hook"

    def advance_stage(self, stage: str) -> None:
        """Move to next stage."""
        self.stage = stage
        if stage not in ["observe", "remember", "reason", "act", "verify", "converge"]:
            raise ValueError(f"Unknown stage: {stage}")

    def to_convergence_record(self) -> Dict[str, Any]:
        """Convert context to ConvergenceRecord fields."""
        return {
            "id": self.id,
            "hypothesis": self.hypothesis or f"Triggered by {self.trigger}",
            "evidence_ids": self.retrieved_memories,
            "result": {
                "action": self.action,
                "expected": self.expected_output,
                "actual": self.actual_output,
                "verified": self.verification_passed,
            },
            "confidence": self.confidence,
            "reasoner": "convergence-hook",
            "timestamp": self.timestamp.isoformat(),
            "verified": self.verification_passed,
            "verification_notes": self.verification_notes,
            "source": self.source,
            "applied_evidence": self.grounding_signals,
        }


class ConvergenceHookManager:
    """Central registry for Convergence loop hooks across all stages.

    Wires six-stage loop as the default path for every action.
    """

    def __init__(self, kernel_or_memory_path: Optional[Any] = None):
        """Initialize hook manager.

        Args:
            kernel_or_memory_path: Convergence kernel or path to memory JSONL
        """
        self.kernel = kernel_or_memory_path
        self.hooks: Dict[str, List[Callable]] = {
            "observe": [],
            "remember": [],
            "reason": [],
            "act": [],
            "verify": [],
            "converge": [],
        }
        self.active_contexts: Dict[str, HookContext] = {}
        self.records: List[Dict[str, Any]] = []

    def register(self, stage: str, hook: Callable) -> None:
        """Register a hook for a stage.

        Args:
            stage: One of observe, remember, reason, act, verify, converge
            hook: Callable(context: HookContext) -> None
        """
        if stage not in self.hooks:
            raise ValueError(f"Unknown stage: {stage}")
        self.hooks[stage].append(hook)

    def execute_stage(self, context: HookContext, stage: str) -> HookContext:
        """Execute all hooks registered for a stage.

        Args:
            context: HookContext accumulating loop data
            stage: Stage name

        Returns: Updated context
        """
        context.advance_stage(stage)

        for hook in self.hooks[stage]:
            try:
                hook(context)
            except Exception as e:
                context.reasoning_trace.append(f"Hook error in {stage}: {e}")

        return context

    def run_loop(
        self,
        trigger: str,
        inputs: Dict[str, Any],
        action_fn: Callable,
    ) -> Dict[str, Any]:
        """Execute a complete six-stage Convergence loop.

        Args:
            trigger: What triggered this (e.g., "git-push", "test-run")
            inputs: Input data to the action
            action_fn: Callable that performs the Act stage

        Returns: ConvergenceRecord as dict
        """
        context = HookContext(trigger=trigger, inputs=inputs)
        self.active_contexts[context.id] = context

        # Stage 1: Observe
        context = self.execute_stage(context, "observe")

        # Stage 2: Remember
        context = self.execute_stage(context, "remember")

        # Stage 3: Reason
        context = self.execute_stage(context, "reason")

        # Stage 4: Act
        context = self.execute_stage(context, "act")
        try:
            if action_fn:
                context.actual_output = action_fn(**context.action_args)
        except Exception as e:
            context.verification_notes = f"Action failed: {e}"
            context.verification_passed = False

        # Stage 5: Verify
        context = self.execute_stage(context, "verify")

        # Stage 6: Converge
        context = self.execute_stage(context, "converge")

        # Convert to record and store
        record = context.to_convergence_record()
        self.records.append(record)

        return record

    def observe_hook(self, capture_inputs: bool = True) -> Callable:
        """Decorator: automatically capture inputs (Observe stage).

        Usage:
            @hook_manager.observe_hook()
            def my_function(x, y):
                return x + y
        """
        def decorator(fn: Callable) -> Callable:
            @wraps(fn)
            def wrapper(*args, **kwargs):
                context = HookContext(trigger=fn.__name__)
                context.inputs = {"args": args, "kwargs": kwargs}
                self.active_contexts[context.id] = context

                # Execute action
                result = fn(*args, **kwargs)

                # Store outcome
                context.actual_output = result
                context.confidence = 0.7
                self.records.append(context.to_convergence_record())

                return result
            return wrapper
        return decorator

    def track_stage(self, stage: str, description: str = "") -> Callable:
        """Decorator: track progress through a loop stage.

        Usage:
            @hook_manager.track_stage("verify", "Testing output")
            def verify_result(result):
                assert result is not None
        """
        def decorator(fn: Callable) -> Callable:
            @wraps(fn)
            def wrapper(context: HookContext) -> None:
                context.reasoning_trace.append(f"{stage}: {description}")
                try:
                    fn(context)
                except AssertionError as e:
                    context.verification_passed = False
                    context.verification_notes = str(e)
                except Exception as e:
                    context.verification_notes = f"Error: {e}"
            return wrapper
        return decorator

    def metrics(self) -> Dict[str, Any]:
        """Report hook execution metrics."""
        if not self.records:
            return {
                "total_records": 0,
                "average_confidence": 0.0,
                "grounded_fraction": 0.0,
            }

        total = len(self.records)
        grounded = sum(
            1 for r in self.records
            if r.get("applied_evidence") and len(r["applied_evidence"]) > 0
        )
        avg_conf = sum(r.get("confidence", 0) for r in self.records) / total

        return {
            "total_records": total,
            "average_confidence": avg_conf,
            "grounded_fraction": grounded / total if total > 0 else 0.0,
            "grounded_count": grounded,
            "ungrounded_count": total - grounded,
        }


# Global hook manager instance
_hook_manager: Optional[ConvergenceHookManager] = None


def get_hook_manager() -> ConvergenceHookManager:
    """Get the global hook manager (lazy init)."""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = ConvergenceHookManager()
    return _hook_manager


def reset_hook_manager() -> None:
    """Reset the global hook manager (for testing)."""
    global _hook_manager
    _hook_manager = None


# Built-in hooks for common stages

def log_observation(context: HookContext) -> None:
    """Built-in Observe hook: log what triggered this."""
    context.reasoning_trace.append(f"Triggered by: {context.trigger}")


def retrieve_context(context: HookContext) -> None:
    """Built-in Remember hook: stub for memory retrieval."""
    # In a full implementation, this would query the kernel's memory
    context.reasoning_trace.append("Memory retrieval: (stub)")


def form_hypothesis(context: HookContext) -> None:
    """Built-in Reason hook: form hypothesis from context."""
    if context.trigger and context.inputs:
        context.hypothesis = f"Process {context.trigger} with inputs {list(context.inputs.keys())}"


def plan_action(context: HookContext) -> None:
    """Built-in Act hook: decide what action to take."""
    context.action = context.hypothesis
    context.action_args = context.inputs


def validate_output(context: HookContext) -> None:
    """Built-in Verify hook: validate actual vs expected output."""
    if context.actual_output is not None:
        context.verification_passed = True


def record_convergence(context: HookContext) -> None:
    """Built-in Converge hook: finalize convergence record."""
    if context.verification_passed:
        context.confidence = min(0.9, context.confidence + 0.2)


def install_default_hooks(manager: ConvergenceHookManager) -> None:
    """Wire up the built-in hooks for all stages."""
    manager.register("observe", log_observation)
    manager.register("remember", retrieve_context)
    manager.register("reason", form_hypothesis)
    manager.register("act", plan_action)
    manager.register("verify", validate_output)
    manager.register("converge", record_convergence)
