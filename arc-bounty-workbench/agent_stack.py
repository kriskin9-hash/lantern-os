"""
ARC Agent Stack

Curiosity policy + map memory + action replay + failure compression.
Designed for ARC-AGI-3 interactive agent evaluation.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np


@dataclass
class AgentState:
    """Current state of the agent in the environment."""
    task_id: str
    step: int = 0
    observations: List[Any] = field(default_factory=list)
    actions: List[Any] = field(default_factory=list)
    rewards: List[float] = field(default_factory=list)
    map_memory: Dict[str, Any] = field(default_factory=dict)
    failure_log: List[Dict] = field(default_factory=list)
    best_hypothesis: Optional[Any] = None
    best_score: float = 0.0


class MapMemory:
    """Structured memory for explored states and patterns."""

    def __init__(self):
        self.state_map: Dict[str, Dict] = {}
        self.pattern_map: Dict[str, List] = {}

    def record_state(self, state_hash: str, observation: Any, action: Any, reward: float):
        self.state_map[state_hash] = {
            "observation": str(observation),
            "action": str(action),
            "reward": reward,
        }

    def record_pattern(self, pattern_key: str, evidence: Any):
        if pattern_key not in self.pattern_map:
            self.pattern_map[pattern_key] = []
        self.pattern_map[pattern_key].append(str(evidence))

    def has_seen(self, state_hash: str) -> bool:
        return state_hash in self.state_map

    def best_known_action(self, state_hash: str) -> Optional[Any]:
        entry = self.state_map.get(state_hash)
        if entry:
            return entry["action"]
        return None


class CuriosityPolicy:
    """
    Curiosity-driven exploration policy.
    Prefers states not yet visited in map memory.
    """

    def __init__(self, memory: MapMemory):
        self.memory = memory

    def score_action(self, state_hash: str, action: Any) -> float:
        """Score an action based on novelty (higher = more curious)."""
        action_hash = hashlib.md5(f"{state_hash}:{action}".encode()).hexdigest()
        if not self.memory.has_seen(action_hash):
            return 1.0  # novel
        return 0.0  # already seen

    def select_action(self, state_hash: str, candidates: List[Any]) -> Any:
        """Select the most novel action from candidates."""
        if not candidates:
            return None
        scores = [self.score_action(state_hash, a) for a in candidates]
        best_idx = int(np.argmax(scores))
        return candidates[best_idx]


class ActionReplay:
    """Replay successful action sequences."""

    def __init__(self):
        self.replay_buffer: List[Dict] = []
        self.max_size: int = 1000

    def add(self, state_hash: str, action: Any, reward: float, next_state_hash: str):
        entry = {
            "state": state_hash,
            "action": str(action),
            "reward": reward,
            "next_state": next_state_hash,
        }
        self.replay_buffer.append(entry)
        if len(self.replay_buffer) > self.max_size:
            self.replay_buffer.pop(0)

    def sample_high_reward(self, n: int = 5) -> List[Dict]:
        """Return top-n entries by reward."""
        sorted_buf = sorted(self.replay_buffer, key=lambda x: x["reward"], reverse=True)
        return sorted_buf[:n]


class FailureCompressor:
    """Compress and summarize failure modes."""

    def __init__(self):
        self.failures: List[Dict] = []

    def record_failure(self, task_id: str, hypothesis: Any, score: float, reason: str):
        self.failures.append({
            "task_id": task_id,
            "hypothesis": str(hypothesis),
            "score": score,
            "reason": reason,
        })

    def compress(self) -> Dict[str, int]:
        """Count failure reasons."""
        reasons: Dict[str, int] = {}
        for f in self.failures:
            reasons[f["reason"]] = reasons.get(f["reason"], 0) + 1
        return reasons

    def worst_tasks(self, n: int = 5) -> List[str]:
        """Return task IDs with most failures."""
        task_counts: Dict[str, int] = {}
        for f in self.failures:
            task_counts[f["task_id"]] = task_counts.get(f["task_id"], 0) + 1
        sorted_tasks = sorted(task_counts.items(), key=lambda x: x[1], reverse=True)
        return [t for t, _ in sorted_tasks[:n]]


class ARCAgent:
    """
    Full ARC agent stack:
    curiosity policy + map memory + action replay + failure compression.
    """

    def __init__(self, task_id: str):
        self.state = AgentState(task_id=task_id)
        self.memory = MapMemory()
        self.policy = CuriosityPolicy(self.memory)
        self.replay = ActionReplay()
        self.failures = FailureCompressor()

    def observe(self, observation: Any) -> str:
        """Record observation and return state hash."""
        obs_hash = hashlib.md5(str(observation).encode()).hexdigest()
        self.state.observations.append(observation)
        return obs_hash

    def act(self, state_hash: str, candidates: List[Any]) -> Any:
        """Select action using curiosity policy."""
        action = self.policy.select_action(state_hash, candidates)
        self.state.actions.append(action)
        return action

    def record_reward(self, state_hash: str, action: Any, reward: float, next_hash: str):
        self.state.rewards.append(reward)
        self.memory.record_state(state_hash, self.state.observations[-1], action, reward)
        self.replay.add(state_hash, action, reward, next_hash)
        if reward > self.state.best_score:
            self.state.best_score = reward
            self.state.best_hypothesis = action

    def record_failure(self, hypothesis: Any, score: float, reason: str):
        self.failures.record_failure(self.state.task_id, hypothesis, score, reason)

    def summary(self) -> Dict:
        return {
            "task_id": self.state.task_id,
            "steps": self.state.step,
            "best_score": self.state.best_score,
            "failure_summary": self.failures.compress(),
            "high_reward_replays": len(self.replay.sample_high_reward()),
        }


if __name__ == "__main__":
    agent = ARCAgent("test-task-001")
    obs_hash = agent.observe([[1, 2], [3, 4]])
    action = agent.act(obs_hash, ["rotate_90", "flip_h", "identity"])
    print(f"Selected action: {action}")
    print(f"Summary: {agent.summary()}")
