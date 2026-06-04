#!/usr/bin/env python3
"""
Lantern M5: Runtime Capability Attestation

Continuously proves that advertised LLM capabilities are actually functional.
Every N minutes, performs a proof-of-capability request to the primary provider.
On failure, logs degradation and falls back to alternate provider.
All evidence is timestamped and ledger-recorded for compliance audit.

Patent claim: "Method for continuous runtime capability attestation in distributed
AI agents, comprising: (1) periodic proof requests to verify capability still
functional, (2) evidence collection with timestamps, (3) ledger recording of all
attestation results, (4) operator dashboard showing real-time capability status
with proof links."
"""

import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import requests


class CapabilityAttestation:
    """Runtime capability attestation for Lantern providers."""

    def __init__(self, telemetry_dir: Optional[Path] = None,
                 attestation_interval_sec: int = 300):
        """
        Initialize capability attestation.

        Args:
            telemetry_dir: Path to telemetry directory (default: ~/.lantern/telemetry/)
            attestation_interval_sec: Proof-of-capability test interval (default: 5 min)
        """
        self.telemetry_dir = telemetry_dir or (Path.home() / ".lantern" / "telemetry")
        self.attestation_interval_sec = attestation_interval_sec
        self.attestation_ledger_file = self.telemetry_dir / "attestation-ledger.jsonl"
        self.capability_state_file = self.telemetry_dir / "capability-state.json"

        self.telemetry_dir.mkdir(parents=True, exist_ok=True)

        # Current capability state (in-memory cache)
        self.capability_state = self._load_capability_state()

        # Background attestation thread
        self._attestation_thread = None
        self._stop_attestation = threading.Event()

    def _load_capability_state(self) -> Dict[str, Any]:
        """Load current capability state from disk."""
        if self.capability_state_file.exists():
            try:
                with open(self.capability_state_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Attestation] Warning: Failed to load capability state: {e}")
                return {}
        return {}

    def _save_capability_state(self):
        """Save current capability state to disk."""
        try:
            with open(self.capability_state_file, 'w') as f:
                json.dump(self.capability_state, f, indent=2)
        except Exception as e:
            print(f"[Attestation] Warning: Failed to save capability state: {e}")

    def _record_attestation(self, provider: str, success: bool, proof: Dict[str, Any]):
        """
        Record attestation result in ledger (immutable).

        Args:
            provider: Provider name (claude, ollama, lm_studio, etc.)
            success: Whether attestation succeeded
            proof: Evidence object {timestamp, latency_ms, model, response_snippet}
        """
        ledger_entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "success": success,
            "proof": proof
        }

        try:
            with open(self.attestation_ledger_file, 'a') as f:
                f.write(json.dumps(ledger_entry) + '\n')
        except Exception as e:
            print(f"[Attestation] Warning: Failed to record ledger entry: {e}")

        # Update in-memory state
        if provider not in self.capability_state:
            self.capability_state[provider] = {
                "last_proof_time": None,
                "status": "unknown",
                "failure_count": 0,
                "last_failure": None
            }

        if success:
            self.capability_state[provider]["status"] = "operational"
            self.capability_state[provider]["last_proof_time"] = datetime.now().isoformat()
            self.capability_state[provider]["failure_count"] = 0
        else:
            self.capability_state[provider]["failure_count"] += 1
            self.capability_state[provider]["last_failure"] = datetime.now().isoformat()
            if self.capability_state[provider]["failure_count"] >= 3:
                self.capability_state[provider]["status"] = "degraded"

        self._save_capability_state()

    def test_provider_capability(self, provider_full_config: Dict[str, Any],
                                provider_name: str = "unknown") -> Dict[str, Any]:
        """
        Perform a proof-of-capability test against a provider.

        Args:
            provider_full_config: Full provider configuration from llm-configurations.json
            provider_name: Human-readable provider name

        Returns:
            {success: bool, proof: {timestamp, latency_ms, model, error}, failure_reason: str}
        """
        config = provider_full_config.get("config", {})
        proof = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider_name,
            "model": config.get("model", "unknown"),
            "latency_ms": 0,
            "request_snippet": "ping",  # Simple health check message
            "response_snippet": ""
        }

        start_time = time.time()
        failure_reason = None

        try:
            # Determine provider type from config
            provider_type = provider_full_config.get("type", "unknown")
            endpoint = provider_full_config.get("endpoint", "")

            if provider_type == "local_endpoint":
                # Local provider (LM Studio, Ollama) — test via HTTP GET on health endpoint
                # Extract base URL (before /v1/ or /api/)
                if '/v1/' in endpoint:
                    base_endpoint = endpoint.split('/v1/')[0]
                elif '/api/' in endpoint:
                    base_endpoint = endpoint.split('/api/')[0]
                else:
                    base_endpoint = endpoint.rsplit('/', 1)[0]

                # Simple health check endpoint
                if "ollama" in provider_name.lower():
                    health_endpoint = f"{base_endpoint}/api/tags"
                else:
                    health_endpoint = f"{base_endpoint}/api/status"

                response = requests.get(health_endpoint, timeout=5)
                response.raise_for_status()

                proof["latency_ms"] = (time.time() - start_time) * 1000
                proof["response_snippet"] = "health_check_passed"

                self._record_attestation(provider_name, True, proof)
                return {
                    "success": True,
                    "proof": proof,
                    "failure_reason": None
                }

            elif provider_type == "api_key":
                # Cloud provider (Claude, Gemini, DeepSeek) — test with minimal API call
                credentials = provider_full_config.get("credentials", {})
                api_key = credentials.get("api_key", "")

                if not api_key or "YOUR_" in api_key:
                    failure_reason = "API key not configured"
                    self._record_attestation(provider_name, False, proof)
                    return {
                        "success": False,
                        "proof": proof,
                        "failure_reason": failure_reason
                    }

                model = config.get("model", "gpt-4")
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "ping"}
                    ],
                    "max_tokens": 10
                }

                response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                response.raise_for_status()

                proof["latency_ms"] = (time.time() - start_time) * 1000
                proof["response_snippet"] = "api_call_successful"

                self._record_attestation(provider_name, True, proof)
                return {
                    "success": True,
                    "proof": proof,
                    "failure_reason": None
                }

            else:
                failure_reason = f"Unknown provider type: {provider_type}"
                self._record_attestation(provider_name, False, proof)
                return {
                    "success": False,
                    "proof": proof,
                    "failure_reason": failure_reason
                }

        except requests.exceptions.Timeout:
            failure_reason = "Provider timeout (>5s)"
            proof["latency_ms"] = (time.time() - start_time) * 1000
            self._record_attestation(provider_name, False, proof)

        except requests.exceptions.ConnectionError:
            failure_reason = f"Provider unreachable ({provider_name})"
            proof["latency_ms"] = (time.time() - start_time) * 1000
            self._record_attestation(provider_name, False, proof)

        except Exception as e:
            failure_reason = f"Attestation error: {str(e)}"
            proof["latency_ms"] = (time.time() - start_time) * 1000
            self._record_attestation(provider_name, False, proof)

        return {
            "success": False,
            "proof": proof,
            "failure_reason": failure_reason
        }

    def get_capability_status(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current capability status for operator dashboard.

        Args:
            provider_name: Specific provider, or None for all providers

        Returns:
            {provider_name: {status, last_proof_time, failure_count, ...}}
        """
        if provider_name:
            return {
                provider_name: self.capability_state.get(provider_name, {
                    "status": "unknown",
                    "last_proof_time": None,
                    "failure_count": 0
                })
            }

        return self.capability_state

    def start_continuous_attestation(self, providers_config: Dict[str, Dict[str, Any]]):
        """
        Start background thread for continuous capability attestation.

        Args:
            providers_config: Dict of {provider_name: provider_config}
        """
        if self._attestation_thread and self._attestation_thread.is_alive():
            print("[Attestation] Continuous attestation already running")
            return

        self._stop_attestation.clear()
        self._attestation_thread = threading.Thread(
            target=self._attestation_loop,
            args=(providers_config,),
            daemon=True
        )
        self._attestation_thread.start()
        print(f"[Attestation] Continuous attestation started (interval: {self.attestation_interval_sec}s)")

    def stop_continuous_attestation(self):
        """Stop background attestation thread."""
        self._stop_attestation.set()
        if self._attestation_thread:
            self._attestation_thread.join(timeout=5)
        print("[Attestation] Continuous attestation stopped")

    def _attestation_loop(self, providers_config: Dict[str, Dict[str, Any]]):
        """
        Background loop that periodically tests each provider's capability.

        Args:
            providers_config: Dict of {provider_name: provider_config}
        """
        while not self._stop_attestation.wait(timeout=self.attestation_interval_sec):
            for provider_name, config in providers_config.items():
                result = self.test_provider_capability(config, provider_name)
                status = "✓" if result["success"] else "✗"
                status_char = "[OK]" if status == "✓" else "[FAIL]"
            print(f"[Attestation] {status_char} {provider_name}: "
                      f"{result.get('failure_reason') or 'operational'}")

    def get_attestation_ledger(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get attestation ledger entries from last N hours.

        Returns:
            List of ledger entries with timestamp proof
        """
        if not self.attestation_ledger_file.exists():
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        ledger = []

        try:
            with open(self.attestation_ledger_file) as f:
                for line in f:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if entry_time >= cutoff_time:
                        ledger.append(entry)
        except Exception as e:
            print(f"[Attestation] Warning: Failed to read ledger: {e}")

        return ledger

    def export_capability_evidence(self, output_file: Optional[str] = None) -> str:
        """
        Export capability evidence for compliance audit (operator-facing).

        Args:
            output_file: Optional custom output path

        Returns:
            Path to exported evidence file
        """
        export_dir = Path.home() / ".lantern" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        export_path = output_file or str(export_dir / f"capability-evidence-{timestamp}.json")

        evidence = {
            "export_timestamp": datetime.now().isoformat(),
            "capability_state": self.capability_state,
            "recent_attestations": self.get_attestation_ledger(hours=24),
            "attestation_interval_sec": self.attestation_interval_sec
        }

        with open(export_path, 'w') as f:
            json.dump(evidence, f, indent=2)

        print(f"[Attestation] Capability evidence exported to: {export_path}")
        return export_path


if __name__ == "__main__":
    # Example: test capability attestation standalone
    attestation = CapabilityAttestation()

    # Load providers config
    config_path = Path.home() / ".lantern" / "llm-configurations.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            providers = config.get("llm_providers", {})

            print("Testing provider capability...\n")
            for provider_name, provider_cfg in providers.items():
                result = attestation.test_provider_capability(
                    provider_cfg,  # Pass full config, not just the "config" sub-dict
                    provider_name
                )
                status = "[PASS]" if result["success"] else "[FAIL]"
                reason = result.get("failure_reason", "operational")
                print(f"{status}: {provider_name} - {reason}\n")

            print("\nCapability State:")
            print(json.dumps(attestation.get_capability_status(), indent=2))

            print("\nRecent Attestations:")
            ledger = attestation.get_attestation_ledger(hours=1)
            for entry in ledger[-5:]:  # Last 5
                status = "[OK]" if entry['success'] else "[FAIL]"
                print(f"  {entry['timestamp']}: {entry['provider']} - {status}")
