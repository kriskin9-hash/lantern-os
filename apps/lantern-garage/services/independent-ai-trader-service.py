#!/usr/bin/env python3
"""
Independent AI Trader Service — Phase 4B Integration
Wraps profitable agents.py + main.py as black-box alpha engine.

This service:
- Runs trader independently (DO NOT modify strategy logic)
- Intercepts decisions and routes to Lantern OS
- Applies safety gates (stability index check)
- Logs all decisions to audit trail
- Streams events to dashboard

Key principle:
> We do NOT rewrite or retrain the trader.
> We ONLY wrap, observe, gate, and route its decisions.
"""

import json
import sys
import os
import requests
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent dirs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class IndependentAITraderService:
    """
    Wraps independent AI trader and routes to Lantern OS.
    """

    def __init__(self, lantern_api_base="http://127.0.0.1:4177"):
        self.api_base = lantern_api_base
        self.trader_process = None
        self.session_id = str(uuid.uuid4())[:8]
        self.decision_count = 0

        # Ensure log directory exists
        self.log_dir = Path(__file__).parent.parent.parent.parent / "data" / "trading"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.log_dir / "independent-ai-trades.jsonl"
        self.decision_log = self.log_dir / "independent-ai-decisions.jsonl"

    def start_trader(self, mode: str = "paper"):
        """
        Start the independent AI trader process.

        Args:
            mode: "paper" (paper trading) or "dry_run"
        """
        print(f"[Trader Service] Starting independent AI trader in {mode} mode...")

        try:
            # Find main.py
            root = Path(__file__).parent.parent.parent.parent
            main_py = root / "main.py"

            if not main_py.exists():
                print(f"[Trader Service] ERROR: main.py not found at {main_py}")
                return False

            # Start trader process with Lantern integration enabled
            self.trader_process = subprocess.Popen(
                [sys.executable, str(main_py), "--mode", mode, "--lantern-integration", "true"],
                cwd=str(root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            print(f"[Trader Service] Trader process started (PID: {self.trader_process.pid})")
            return True

        except Exception as e:
            print(f"[Trader Service] ERROR starting trader: {e}")
            return False

    def check_safety_gate(self) -> Dict[str, Any]:
        """
        Check if system is stable enough to execute trades.

        Returns:
            {
              "allowed": bool,
              "stability_index": float,
              "status": str
            }
        """
        try:
            # Fetch consistency report (includes stability index)
            resp = requests.get(
                f"{self.api_base}/api/trading/consistency-report",
                timeout=2
            )

            if resp.status_code != 200:
                print("[Trader Service] Safety gate: API error, blocking")
                return {"allowed": False, "stability_index": 0, "status": "api_error"}

            report = resp.json()
            stability_index = float(report["systemHealth"]["stabilityIndex"])

            # Hard gate: only execute if stability >= 0.80
            allowed = stability_index >= 0.8

            return {
                "allowed": allowed,
                "stability_index": stability_index,
                "status": report["systemHealth"]["status"]
            }

        except Exception as e:
            print(f"[Trader Service] Safety gate check failed: {e}")
            return {"allowed": False, "stability_index": 0, "status": "exception"}

    def process_decision(
        self,
        ticker: str,
        action: str,  # BUY, SELL, NO_TRADE, EXIT
        confidence: float,
        strategy: str = "alpha-model",
        reasoning: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Process a decision from the independent AI trader.

        Returns:
            {
              "executed": bool,
              "reason": str,
              "traceId": str,
              "engineResponse": {...}
            }
        """
        self.decision_count += 1
        decision_id = f"d-{self.session_id}-{self.decision_count}"

        # Check safety gate first
        safety = self.check_safety_gate()

        decision_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "decisionId": decision_id,
            "ticker": ticker,
            "action": action,
            "confidence": confidence,
            "strategy": strategy,
            "reasoning": reasoning or [],
            "safetyGate": safety
        }

        # Log decision
        self._log_decision(decision_log)

        # If action is NO_TRADE, skip execution
        if action == "NO_TRADE":
            return {
                "executed": False,
                "reason": "trader_no_trade",
                "decision_id": decision_id,
                "engine_response": None
            }

        # If safety gate blocks, skip execution
        if not safety["allowed"]:
            print(f"[Trader Service] Safety gate BLOCKED trade: {ticker} {action} (stability: {safety['stability_index']:.2f})")
            return {
                "executed": False,
                "reason": f"safety_gate_blocked ({safety['status']})",
                "decision_id": decision_id,
                "stability_index": safety["stability_index"],
                "engine_response": None
            }

        # Route decision to Lantern OS Trade State Engine
        try:
            # Convert action to engine format
            engine_action = "BUY" if action == "BUY" else "SELL" if action == "SELL" else None

            if not engine_action:
                return {
                    "executed": False,
                    "reason": f"invalid_action ({action})",
                    "decision_id": decision_id,
                    "engine_response": None
                }

            # Submit paper trade via Trade State Engine API
            order_payload = {
                "ticker": ticker,
                "side": engine_action,
                "quantity": 1,  # TODO: make configurable
                "type": "market",
                "mode": "paper",  # IMPORTANT: paper trading only
                "external_agent": "independent-ai-trader",
                "confidence": confidence,
                "strategy": strategy,
                "decision_id": decision_id
            }

            resp = requests.post(
                f"{self.api_base}/api/trading/kalshi/order",
                json=order_payload,
                timeout=5
            )

            engine_response = resp.json() if resp.status_code == 200 else None

            if resp.status_code == 200 and engine_response.get("success"):
                # Log successful trade
                trade_log = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "traceId": engine_response.get("traceId"),
                    "source": "independent-ai-trader",
                    "ticker": ticker,
                    "action": action,
                    "confidence": confidence,
                    "strategy": strategy,
                    "paper": True,
                    "executed": True,
                    "engine_response": engine_response
                }
                self._log_trade(trade_log)

                print(f"[Trader Service] Paper trade executed: {ticker} {action} (confidence: {confidence:.2f})")

                return {
                    "executed": True,
                    "reason": "executed",
                    "decision_id": decision_id,
                    "trace_id": engine_response.get("traceId"),
                    "engine_response": engine_response
                }
            else:
                return {
                    "executed": False,
                    "reason": "engine_error",
                    "decision_id": decision_id,
                    "engine_response": engine_response
                }

        except Exception as e:
            print(f"[Trader Service] Error submitting trade: {e}")
            return {
                "executed": False,
                "reason": f"exception ({str(e)})",
                "decision_id": decision_id,
                "engine_response": None
            }

    def stream_decision_event(
        self,
        decision_id: str,
        ticker: str,
        action: str,
        status: str,  # executed, blocked, error
        confidence: float
    ):
        """
        Stream decision event to dashboard via SSE.
        """
        event = {
            "type": "TRADER_DECISION",
            "source": "independent-ai-trader",
            "decisionId": decision_id,
            "ticker": ticker,
            "action": action,
            "status": status,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            # Would normally stream via WebSocket or SSE
            # For now, just log it
            print(f"[Trader Service] Event: {json.dumps(event)}")
        except Exception as e:
            print(f"[Trader Service] Error streaming event: {e}")

    def _log_trade(self, trade_log: Dict[str, Any]):
        """Append trade to immutable log."""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(trade_log) + "\n")
        except Exception as e:
            print(f"[Trader Service] Error logging trade: {e}")

    def _log_decision(self, decision_log: Dict[str, Any]):
        """Append decision to decision log."""
        try:
            with open(self.decision_log, "a") as f:
                f.write(json.dumps(decision_log) + "\n")
        except Exception as e:
            print(f"[Trader Service] Error logging decision: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "session_id": self.session_id,
            "decisions_processed": self.decision_count,
            "trader_running": self.trader_process is not None and self.trader_process.poll() is None,
            "api_base": self.api_base,
            "log_dir": str(self.log_dir)
        }


def main():
    """
    Entry point for running service standalone.

    Usage:
        python independent-ai-trader-service.py [--api-base http://127.0.0.1:4177]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Independent AI Trader Service")
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:4177",
        help="Lantern OS API base URL"
    )
    parser.add_argument(
        "--mode",
        default="paper",
        choices=["paper", "dry_run"],
        help="Trading mode"
    )

    args = parser.parse_args()

    service = IndependentAITraderService(lantern_api_base=args.api_base)

    print("[Trader Service] Starting...")
    print(json.dumps(service.get_status(), indent=2))

    # Start trader
    if not service.start_trader(mode=args.mode):
        print("[Trader Service] Failed to start trader")
        return 1

    print("[Trader Service] Running... Press Ctrl+C to stop")

    try:
        # Keep service running
        while True:
            time.sleep(1)

            # Check if trader process is still alive
            if service.trader_process and service.trader_process.poll() is not None:
                print("[Trader Service] Trader process exited")
                break

    except KeyboardInterrupt:
        print("\n[Trader Service] Shutting down...")
        if service.trader_process:
            service.trader_process.terminate()
            service.trader_process.wait(timeout=5)

    print("[Trader Service] Stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
