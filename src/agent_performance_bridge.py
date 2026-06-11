"""
Agent Performance Bridge — Python wrapper for Node.js agent-performance.js

Allows Convergence IO (Python) to query the performance leaderboard
and record agent calls from the Node.js streaming/chat services.
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, List, Any


class AgentPerformanceBridge:
    """Bridge to agent-performance.js running in Node.js"""

    def __init__(self, base_url: str = "http://127.0.0.1:4177"):
        self.base_url = base_url
        self.timeout = 5

    def get_top_agents_for_task(
        self, task_type: str, lookback_days: int = 7, limit: int = 3
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Query leaderboard for top agents for a given task type.

        Args:
            task_type: Task type ("code-gen", "reasoning", "creative", etc.)
            lookback_days: How far back to look (default 7)
            limit: Max results to return (default 3)

        Returns:
            List of top agents with scores, or None if unavailable
        """
        try:
            url = f"{self.base_url}/api/agent-performance/leaderboard?taskType={task_type}&topN={limit}"
            with urllib.request.urlopen(url, timeout=self.timeout) as res:
                data = json.loads(res.read().decode())
                return data.get("agents", []) if isinstance(data, dict) else data
        except (urllib.error.URLError, json.JSONDecodeError, Exception) as e:
            # Non-fatal: leaderboard unavailable, fall back to defaults
            return None

    def record_agent_call_from_convergence(
        self,
        agent_id: str,
        task_type: str,
        validation_passed: bool,
        latency_ms: float,
        cost_usd: float = 0.0,
        convergence_step: int = 0,
        step_name: str = "",
    ) -> bool:
        """
        Record an agent call from Convergence phase.

        Args:
            agent_id: Agent that was selected (e.g., "claude-sonnet", "ollama")
            task_type: Task type for this phase (from leaderboard query)
            validation_passed: Did Convergence validation pass?
            latency_ms: How long the phase took
            cost_usd: Cost of the LLM call (if applicable)
            convergence_step: Which step (1-12) in the convergence loop
            step_name: Human-readable step name

        Returns:
            True if recorded successfully, False if bridge unavailable
        """
        try:
            url = f"{self.base_url}/api/agent-performance/record"
            payload = json.dumps({
                "agentId": agent_id,
                "taskType": task_type,
                "success": validation_passed,
                "latencyMs": latency_ms,
                "costUsd": cost_usd,
                "convergenceStep": convergence_step,
                "convergenceStepName": step_name,
            }).encode()

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                return res.status == 200
        except (urllib.error.URLError, json.JSONDecodeError, Exception):
            # Non-fatal: recording failed, continue
            return False

    def retire_agent(
        self, agent_id: str, task_type: str, reason: str
    ) -> bool:
        """
        Mark an agent as retired for a given task type.

        Args:
            agent_id: Agent to retire
            task_type: Task type to retire for
            reason: Reason for retirement

        Returns:
            True if retirement recorded, False if unavailable
        """
        try:
            url = f"{self.base_url}/api/agent-performance/retire"
            payload = json.dumps({
                "agentId": agent_id,
                "taskType": task_type,
                "reason": reason,
            }).encode()

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                return res.status == 200
        except (urllib.error.URLError, json.JSONDecodeError, Exception):
            return False


# Singleton instance
_bridge: Optional[AgentPerformanceBridge] = None


def get_bridge() -> AgentPerformanceBridge:
    """Get or create the singleton bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = AgentPerformanceBridge()
    return _bridge
