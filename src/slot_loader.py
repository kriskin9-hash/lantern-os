"""
Agent Slot Loader & Configuration Parser

Loads `.claude/agent-slots.json` and provides intelligent slot management:
- Load and parse slot configuration with validation
- Build responsibility-to-slot affinity map
- Construct fallback chains from slot metadata
- Track health checks and quota utilization
- Select best-fit slot for incoming task type
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
SLOTS_CONFIG_PATH = REPO_ROOT.parent / ".claude" / "agent-slots.json"


@dataclass
class QuotaTracking:
    """Quota configuration for a slot."""
    enabled: bool = True
    windowSize: int = 86400  # seconds (1 day)
    maxTokensPerWindow: int = 2000000
    fallbackAgent: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuotaTracking":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class HealthCheck:
    """Health check configuration for a slot."""
    interval: int = 60  # seconds
    timeout: int = 10  # seconds

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealthCheck":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SlotCapabilities:
    """Capabilities of a slot."""
    maxTokens: int = 1000000
    batchSize: int = 10
    parallelTasks: int = 4
    supportedTools: List[str] = field(default_factory=lambda: ["all"])

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SlotCapabilities":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AgentSlot:
    """Represents a single agent slot configuration."""
    id: str
    agent: str
    provider: str
    model: str
    status: str = "ready"
    capabilities: SlotCapabilities = field(default_factory=SlotCapabilities)
    quotaTracking: QuotaTracking = field(default_factory=QuotaTracking)
    responsibilities: List[str] = field(default_factory=list)
    syncInterval: int = 300
    healthCheck: HealthCheck = field(default_factory=HealthCheck)
    health_state: Optional[str] = None
    last_heartbeat: Optional[float] = None
    current_utilization: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSlot":
        """Parse slot from JSON dictionary."""
        slot = cls(
            id=data.get("id", ""),
            agent=data.get("agent", ""),
            provider=data.get("provider", ""),
            model=data.get("model", ""),
            status=data.get("status", "ready"),
            responsibilities=data.get("responsibilities", []),
            syncInterval=data.get("syncInterval", 300),
        )

        if "capabilities" in data:
            slot.capabilities = SlotCapabilities.from_dict(data["capabilities"])

        if "quotaTracking" in data:
            slot.quotaTracking = QuotaTracking.from_dict(data["quotaTracking"])

        if "healthCheck" in data:
            slot.healthCheck = HealthCheck.from_dict(data["healthCheck"])

        return slot

    def is_healthy(self) -> bool:
        """Check if slot is healthy and ready for work."""
        return self.status == "ready" and self.health_state != "unhealthy"

    def can_handle_responsibility(self, responsibility: str) -> bool:
        """Check if this slot can handle a given responsibility."""
        return responsibility in self.responsibilities or "general_tasks" in self.responsibilities

    def is_at_quota(self) -> bool:
        """Check if slot has reached its quota threshold (80%)."""
        return self.quotaTracking.enabled and self.current_utilization >= 0.80


class SlotLoader:
    """Load and manage agent slot configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or SLOTS_CONFIG_PATH
        self.slots: Dict[str, AgentSlot] = {}
        self.responsibility_map: Dict[str, List[AgentSlot]] = {}
        self.fallback_chains: Dict[str, List[str]] = {}
        self.version = "1.0.0"

        if self.config_path.exists():
            self._load_config()

    def _load_config(self) -> None:
        """Load and parse the slots configuration file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.version = data.get("version", "1.0.0")

            # Parse all slots
            for slot_data in data.get("slots", []):
                slot = AgentSlot.from_dict(slot_data)
                self.slots[slot.id] = slot

                # Build responsibility map: each responsibility → list of capable slots
                for resp in slot.responsibilities:
                    if resp not in self.responsibility_map:
                        self.responsibility_map[resp] = []
                    self.responsibility_map[resp].append(slot)

            # Build fallback chains: slot_id → [fallback_ids]
            for slot_id, slot in self.slots.items():
                chain = self._build_fallback_chain(slot.id)
                if chain:
                    self.fallback_chains[slot_id] = chain

        except Exception as e:
            raise ValueError(f"Failed to load agent slots configuration: {e}")

    def _build_fallback_chain(self, slot_id: str, visited: Optional[Set[str]] = None) -> List[str]:
        """Build the full fallback chain for a slot (prevents cycles)."""
        if visited is None:
            visited = set()

        if slot_id in visited:
            return []  # Cycle detected

        slot = self.slots.get(slot_id)
        if not slot or not slot.quotaTracking.fallbackAgent:
            return []

        visited.add(slot_id)
        next_slot_id = slot.quotaTracking.fallbackAgent

        chain = [next_slot_id]
        chain.extend(self._build_fallback_chain(next_slot_id, visited))
        return chain

    def get_slot(self, slot_id: str) -> Optional[AgentSlot]:
        """Get a slot by ID."""
        return self.slots.get(slot_id)

    def find_best_slot(self, responsibility: str) -> Optional[AgentSlot]:
        """Find the best healthy slot for a given responsibility.

        Returns the first healthy slot that can handle the responsibility.
        Prioritizes primary slots and respects quota limits.
        """
        capable_slots = self.responsibility_map.get(responsibility, [])

        # Filter to healthy slots that haven't hit quota
        available = [s for s in capable_slots if s.is_healthy() and not s.is_at_quota()]

        return available[0] if available else None

    def find_with_fallback(self, responsibility: str) -> Optional[AgentSlot]:
        """Find best slot for responsibility, following fallback chain if needed.

        1. Try to find a healthy primary slot
        2. If all primaries are unhealthy/at-quota, follow fallback chains
        3. Return the first healthy fallback slot found
        4. If all fail, return None (caller should re-queue or error)
        """
        # First try: primary slots for this responsibility
        primary = self.find_best_slot(responsibility)
        if primary:
            return primary

        # Second try: follow fallback chains from primary slots
        primary_slots = self.responsibility_map.get(responsibility, [])
        for primary_slot in primary_slots:
            chain = self.fallback_chains.get(primary_slot.id, [])
            for fallback_id in chain:
                fallback_slot = self.get_slot(fallback_id)
                if fallback_slot and fallback_slot.is_healthy() and not fallback_slot.is_at_quota():
                    return fallback_slot

        return None

    def list_all_slots(self) -> List[AgentSlot]:
        """Get all configured slots."""
        return list(self.slots.values())

    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of all slots' health status."""
        return {
            slot_id: {
                "status": slot.status,
                "health": slot.health_state or "unknown",
                "utilization": slot.current_utilization,
                "model": slot.model,
                "provider": slot.provider,
            }
            for slot_id, slot in self.slots.items()
        }

    def update_utilization(self, slot_id: str, tokens_used: int) -> None:
        """Update token utilization for a slot."""
        slot = self.get_slot(slot_id)
        if slot and slot.quotaTracking.enabled:
            max_tokens = slot.quotaTracking.maxTokensPerWindow
            slot.current_utilization = min(1.0, tokens_used / max_tokens) if max_tokens > 0 else 0.0

    def mark_unhealthy(self, slot_id: str) -> None:
        """Mark a slot as unhealthy."""
        slot = self.get_slot(slot_id)
        if slot:
            slot.health_state = "unhealthy"

    def mark_healthy(self, slot_id: str) -> None:
        """Mark a slot as healthy."""
        slot = self.get_slot(slot_id)
        if slot:
            slot.health_state = "healthy"

    def to_dict(self) -> Dict[str, Any]:
        """Export current state as dictionary."""
        return {
            "version": self.version,
            "slots": [asdict(slot) for slot in self.slots.values()],
            "responsibility_map": {
                resp: [s.id for s in slots]
                for resp, slots in self.responsibility_map.items()
            },
            "fallback_chains": self.fallback_chains,
            "health_summary": self.get_health_summary(),
        }
