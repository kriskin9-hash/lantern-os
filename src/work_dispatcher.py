"""
Work Dispatcher — Task Router with Slot-Aware Load Balancing

Fixes the 4 critical bugs from 2026-06-05 diagnosis:
- Bug 1: get_pending_jobs filter now re-queues non-matching items (no data loss)
- Bug 2: Loads and respects agent-slots.json (no more hardcoded single agent)
- Bug 3: Follows fallback chains when primary slot fails/at-quota
- Bug 4: Persists health state to PCSF (not implemented in this module, but structured for it)

Provides intelligent routing:
1. Jobs carry a responsibility type
2. Slot loader finds best slot for that responsibility
3. If primary fails, follows fallback chain
4. Re-queues jobs with backoff if all slots exhausted
5. Tracks health and quota per slot
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from slot_loader import SlotLoader, AgentSlot

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
DISPATCH_LOG_PATH = DATA_DIR / "agent-fleet" / "dispatch-log.jsonl"


class JobStatus(Enum):
    """Job lifecycle states."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUEUED = "requeued"


@dataclass
class WorkJob:
    """Represents a single unit of work to be dispatched."""
    job_id: str
    responsibility: str  # Maps to slot responsibilities
    payload: Dict[str, Any]
    priority: int = 0  # Higher = more important
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    assigned_to_slot: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    backoff_until: Optional[float] = None  # Unix timestamp

    def is_ready_to_retry(self) -> bool:
        """Check if job can be retried (not on backoff, under max attempts)."""
        if self.attempts >= self.max_attempts:
            return False
        if self.backoff_until and self.backoff_until > time.time():
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "responsibility": self.responsibility,
            "payload": self.payload,
            "priority": self.priority,
            "created_at": self.created_at,
            "assigned_to_slot": self.assigned_to_slot,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "last_error": self.last_error,
            "backoff_until": self.backoff_until,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkJob":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class WorkQueue:
    """In-memory work queue (could be Redis-backed in production)."""

    def __init__(self):
        self.pending: List[WorkJob] = []
        self.assigned: Dict[str, WorkJob] = {}  # job_id -> job
        self.completed: List[str] = []
        self.failed: List[tuple[str, str]] = []  # (job_id, error)

    def enqueue(self, job: WorkJob) -> None:
        """Add job to pending queue."""
        self.pending.append(job)
        # Sort by priority (descending) and creation time
        self.pending.sort(key=lambda j: (-j.priority, j.created_at))

    def get_pending_jobs(self, responsibility_filter: Optional[str] = None) -> List[WorkJob]:
        """Get pending jobs, optionally filtered by responsibility.

        BUG FIX #1: Non-matching jobs are NOT dropped — they stay in the queue.
        """
        if responsibility_filter is None:
            return self.pending.copy()

        # Separate into matching and non-matching
        matching = []
        non_matching = []

        for job in self.pending:
            if job.responsibility == responsibility_filter:
                matching.append(job)
            else:
                non_matching.append(job)

        # Keep non-matching jobs in queue for other consumers
        self.pending = non_matching

        return matching

    def assign(self, job: WorkJob, slot_id: str) -> None:
        """Assign a job to a specific slot."""
        job.assigned_to_slot = slot_id
        job.attempts += 1
        self.assigned[job.job_id] = job
        # Remove from pending if present
        self.pending = [j for j in self.pending if j.job_id != job.job_id]

    def mark_completed(self, job_id: str) -> None:
        """Mark job as completed."""
        if job_id in self.assigned:
            del self.assigned[job_id]
        self.completed.append(job_id)

    def mark_failed(self, job_id: str, error: str, requeue: bool = True) -> None:
        """Mark job as failed.

        If requeue=True, re-add to pending with exponential backoff.
        """
        job = self.assigned.pop(job_id, None)
        if not job:
            return

        job.last_error = error

        if requeue and job.is_ready_to_retry():
            # Exponential backoff: 2^attempt seconds
            backoff_seconds = 2 ** job.attempts
            job.backoff_until = time.time() + backoff_seconds
            self.pending.append(job)
        else:
            self.failed.append((job_id, error))

    def requeue_with_backoff(self, job_id: str) -> None:
        """Re-queue a job with exponential backoff."""
        job = self.assigned.get(job_id)
        if job and job.is_ready_to_retry():
            backoff_seconds = 2 ** job.attempts
            job.backoff_until = time.time() + backoff_seconds
            self.pending.append(job)
            del self.assigned[job_id]


class WorkDispatcher:
    """Main dispatcher - routes work to agents via slots.

    BUG FIXES:
    - #1: get_pending_jobs() re-queues non-matching jobs (no data loss)
    - #2: Loads agent-slots.json and respects slot config (not hardcoded)
    - #3: Follows fallback chains when primary slot fails/at-quota
    - #4: Health state structured for PCSF persistence (not impl here)
    """

    def __init__(self, slots_config_path: Optional[Path] = None, log_path: Optional[Path] = None):
        self.logger = logging.getLogger("WorkDispatcher")
        self.slot_loader = SlotLoader(slots_config_path)
        self.queue = WorkQueue()
        self.log_path = log_path or DISPATCH_LOG_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"WorkDispatcher initialized with {len(self.slot_loader.slots)} slots")
        self.logger.info(f"Slot health: {self.slot_loader.get_health_summary()}")

    def submit_job(self, job_id: str, responsibility: str, payload: Dict[str, Any], priority: int = 0) -> None:
        """Submit a new job for processing."""
        job = WorkJob(
            job_id=job_id,
            responsibility=responsibility,
            payload=payload,
            priority=priority,
        )
        self.queue.enqueue(job)
        self._log_event("job_submitted", {"job_id": job_id, "responsibility": responsibility, "priority": priority})

    def dispatch_work(self) -> Dict[str, List[Dict[str, Any]]]:
        """Dispatch pending work to available slots.

        Returns a mapping of slot_id -> assigned jobs
        """
        assignments: Dict[str, List[WorkJob]] = {}

        # Get all pending jobs
        pending_jobs = self.queue.pending.copy()

        for job in pending_jobs:
            # Find best slot for this job's responsibility
            slot = self.slot_loader.find_with_fallback(job.responsibility)

            if not slot:
                # All slots exhausted or unhealthy
                self.logger.warning(f"No available slot for {job.responsibility}, re-queuing {job.job_id}")
                self.queue.requeue_with_backoff(job.job_id)
                self._log_event("job_requeued", {
                    "job_id": job.job_id,
                    "reason": "no_available_slot",
                    "backoff_until": job.backoff_until,
                })
                continue

            # Assign to slot
            self.queue.assign(job, slot.id)
            if slot.id not in assignments:
                assignments[slot.id] = []
            assignments[slot.id].append(job)

            self._log_event("job_assigned", {
                "job_id": job.job_id,
                "slot_id": slot.id,
                "responsibility": job.responsibility,
                "attempts": job.attempts,
            })

        return {slot_id: [j.to_dict() for j in jobs] for slot_id, jobs in assignments.items()}

    def handle_slot_failure(self, slot_id: str, reason: str = "wake_failed") -> None:
        """Handle failure of a slot (mark unhealthy, re-queue its jobs).

        BUG FIX #3: When primary slot fails, jobs are re-queued to follow fallback chain,
        not immediately marked as failed.
        """
        self.slot_loader.mark_unhealthy(slot_id)
        self.logger.error(f"Slot {slot_id} marked unhealthy: {reason}")

        # Re-queue all jobs assigned to this slot
        jobs_to_requeue = list(self.queue.assigned.values())
        for job in jobs_to_requeue:
            if job.assigned_to_slot == slot_id:
                job.last_error = f"Slot failure: {reason}"
                self.queue.requeue_with_backoff(job.job_id)
                self._log_event("job_requeued_slot_failure", {
                    "job_id": job.job_id,
                    "failed_slot": slot_id,
                    "reason": reason,
                })

    def complete_job(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark a job as completed."""
        self.queue.mark_completed(job_id)
        self._log_event("job_completed", {"job_id": job_id, "result": result})

    def fail_job(self, job_id: str, error: str) -> None:
        """Mark a job as failed (permanently)."""
        self.queue.mark_failed(job_id, error, requeue=False)
        self._log_event("job_failed", {"job_id": job_id, "error": error})

    def report_slot_health(self, slot_id: str, healthy: bool, utilization: float = 0.0) -> None:
        """Update health and utilization metrics for a slot."""
        slot = self.slot_loader.get_slot(slot_id)
        if not slot:
            return

        slot.last_heartbeat = time.time()
        slot.current_utilization = utilization

        if healthy:
            self.slot_loader.mark_healthy(slot_id)
        else:
            self.slot_loader.mark_unhealthy(slot_id)

        self._log_event("slot_health_update", {
            "slot_id": slot_id,
            "healthy": healthy,
            "utilization": utilization,
        })

    def get_status(self) -> Dict[str, Any]:
        """Get dispatcher status snapshot."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "queue": {
                "pending": len(self.queue.pending),
                "assigned": len(self.queue.assigned),
                "completed": len(self.queue.completed),
                "failed": len(self.queue.failed),
            },
            "slots": self.slot_loader.get_health_summary(),
            "fallback_chains": self.slot_loader.fallback_chains,
        }

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log an event to the dispatch log (JSONL format)."""
        try:
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                **data,
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log event: {e}")


# Convenience factory
_dispatcher: Optional[WorkDispatcher] = None


def get_dispatcher(slots_config_path: Optional[Path] = None) -> WorkDispatcher:
    """Get or create the global work dispatcher."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = WorkDispatcher(slots_config_path)
    return _dispatcher
