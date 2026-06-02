"""
Chat Memory Integration - Wire Lantern chat interface into superfleet-memory system.

This module provides integration between the Lantern chat interface and the
cryptographic audit chain + anti-entropy memory system. All chat interactions
are logged to the memory system with cryptographic verification.
"""

import sys
import os
from datetime import datetime, timezone
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add the apps directory to the path so we can import superfleet-memory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'apps'))

from superfleet_memory import (
    CryptographicAuditChain,
    AntiEntropyMemory,
    BayesianFallacyDetector,
    NarrativeIdentity
)


class ChatMemoryIntegration:
    """
    Integrates Lantern chat with the superfleet-memory system.

    Handles:
    - Logging chat messages to the cryptographic audit chain
    - Tracking conversations in episodic memory (dreams/events)
    - Updating semantic memory with learned beliefs from chat
    - Detecting fallacies in user statements using Bayesian detection
    - Verifying integrity of the full conversation history
    """

    def __init__(self, audit_chain_path: str = None, memory_state_path: str = None):
        """
        Initialize the chat memory integration.

        Args:
            audit_chain_path: Path to store the cryptographic audit chain
            memory_state_path: Path to store the anti-entropy memory state
        """
        self.audit_chain_path = audit_chain_path or os.path.expanduser('~/.lantern/audit-chain')
        self.memory_state_path = memory_state_path or os.path.expanduser('~/.lantern/memory-state')

        # Create directories if they don't exist
        os.makedirs(self.audit_chain_path, exist_ok=True)
        os.makedirs(self.memory_state_path, exist_ok=True)

        # Initialize memory system components
        self.audit_chain = CryptographicAuditChain()
        self.memory = AntiEntropyMemory()
        self.fallacy_detector = BayesianFallacyDetector()
        self.identity = NarrativeIdentity()

        # Load existing state if it exists
        self._load_state()

    def _load_state(self):
        """Load persisted memory and audit chain state."""
        chain_file = os.path.join(self.audit_chain_path, 'chain.json')
        memory_file = os.path.join(self.memory_state_path, 'memory.json')
        identity_file = os.path.join(self.memory_state_path, 'identity.json')

        # Load audit chain
        if os.path.exists(chain_file):
            try:
                with open(chain_file, 'r') as f:
                    chain_data = json.load(f)
                    # Restore the chain from exported format
                    if 'entries' in chain_data:
                        self.audit_chain.entries = chain_data['entries']
                        self.audit_chain.current_key = chain_data.get('current_key', self.audit_chain.current_key)
            except Exception as e:
                print(f"Warning: Could not load audit chain: {e}")

        # Load memory
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                    # Restore memory from exported format
                    if 'episodic' in memory_data:
                        self.memory.episodic_layer = memory_data['episodic']
                    if 'semantic' in memory_data:
                        self.memory.semantic_layer = memory_data['semantic']
                    if 'procedural' in memory_data:
                        self.memory.procedural_layer = memory_data['procedural']
                    if 'narrative' in memory_data:
                        self.memory.narrative_layer = memory_data['narrative']
            except Exception as e:
                print(f"Warning: Could not load memory: {e}")

        # Load identity
        if os.path.exists(identity_file):
            try:
                with open(identity_file, 'r') as f:
                    identity_data = json.load(f)
                    self.identity.stories = identity_data.get('stories', [])
                    self.identity.paradigm_history = identity_data.get('paradigm_history', [])
                    self.identity.identity_anchors = identity_data.get('identity_anchors', {})
            except Exception as e:
                print(f"Warning: Could not load identity: {e}")

    def _persist_state(self):
        """Persist memory and audit chain state to disk."""
        # Save audit chain
        chain_export = self.audit_chain.export_chain()
        chain_file = os.path.join(self.audit_chain_path, 'chain.json')
        with open(chain_file, 'w') as f:
            json.dump(chain_export, f, indent=2)

        # Save memory
        memory_export = self.memory.export_full_memory()
        memory_file = os.path.join(self.memory_state_path, 'memory.json')
        with open(memory_file, 'w') as f:
            json.dump(memory_export, f, indent=2)

        # Save identity
        identity_export = self.identity.export_identity()
        identity_file = os.path.join(self.memory_state_path, 'identity.json')
        with open(identity_file, 'w') as f:
            json.dump(identity_export, f, indent=2)

    def log_chat_message(self,
                        user_id: str,
                        message: str,
                        role: str = "user",
                        metadata: Dict = None) -> Dict:
        """
        Log a chat message to the audit chain and memory.

        Args:
            user_id: ID of the user sending the message
            message: The message content
            role: "user" or "assistant"
            metadata: Additional metadata (lucidity, emotional_intensity, etc.)

        Returns:
            Dict with audit_entry_id, verified, fallacies detected, etc.
        """
        if metadata is None:
            metadata = {}

        # Log to cryptographic audit chain
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "role": role,
            "message": message,
            "metadata": metadata
        }

        entry_id = self.audit_chain.log(audit_entry)

        # Log to episodic memory
        if role == "user":
            lucidity = metadata.get('lucidity', 0.5)
            emotional_intensity = metadata.get('emotional_intensity', 0.3)
            self.memory.log_event(
                event_type="chat_message",
                description=message[:500],  # Truncate long messages
                lucidity=lucidity,
                emotional_intensity=emotional_intensity,
                tags=["conversation", f"user_{user_id}"]
            )

        # Detect fallacies in user messages
        fallacies = []
        if role == "user":
            fallacies = self.fallacy_detector.detect_fallacies(message)

        # Update semantic memory with key beliefs from the message
        if role == "assistant" and len(message) > 20:
            # Extract simple factual claims (naive approach for MVP)
            belief_key = f"message_{entry_id[:8]}"
            self.memory.update_belief(
                key=belief_key,
                belief_content=message[:200],
                confidence=0.7 if "believe" in message.lower() else 0.5,
                source="chat"
            )

        result = {
            "audit_entry_id": entry_id,
            "timestamp": audit_entry["timestamp"],
            "verified": True,
            "chain_valid": self.audit_chain.verify_chain(),
            "fallacies": fallacies if fallacies else [],
            "memory_logged": True
        }

        # Persist state after logging
        self._persist_state()

        return result

    def verify_conversation_integrity(self) -> Dict:
        """
        Verify the integrity of the entire conversation chain.

        Returns:
            Dict with verification status, entry count, chain valid status, etc.
        """
        chain_valid = self.audit_chain.verify_chain()
        memory_coherence = self.memory.calculate_coherence_score()

        audit_stats = self.audit_chain.get_stats()
        memory_stats = self.memory.get_memory_stats()

        result = {
            "verified": chain_valid and memory_coherence > 0.6,
            "chain_valid": chain_valid,
            "memory_coherence": memory_coherence,
            "total_audit_entries": audit_stats.get('total_entries', 0),
            "memory_entries": memory_stats.get('total_events', 0),
            "verification_timestamp": datetime.now(timezone.utc).isoformat()
        }

        return result

    def get_fallacy_hint(self, message: str) -> Optional[str]:
        """
        Get a conversational hint about potential fallacies in a message.

        Args:
            message: The message to check

        Returns:
            A helpful hint about logical issues, or None if no fallacies detected
        """
        fallacies = self.fallacy_detector.detect_fallacies(message)
        if not fallacies:
            return None

        return self.fallacy_detector.generate_response_hint(fallacies)

    def get_memory_summary(self) -> Dict:
        """
        Get a summary of the memory system state.

        Returns:
            Dict with memory statistics and key information
        """
        memory_export = self.memory.export_full_memory()
        audit_stats = self.audit_chain.get_stats()
        identity_summary = self.identity.get_identity_summary()

        return {
            "memory_state": memory_export,
            "audit_chain_stats": audit_stats,
            "identity": identity_summary,
            "coherence_score": self.memory.calculate_coherence_score()
        }

    def anti_entropy_audit(self) -> Dict:
        """
        Run a comprehensive anti-entropy audit of the memory system.

        Returns:
            Dict with audit results and any detected inconsistencies
        """
        return self.memory.anti_entropy_audit()

    def get_public_key(self) -> str:
        """
        Get the current public key for the audit chain.

        Returns:
            The Ed25519 public key as a hex string
        """
        return self.audit_chain.get_public_key()

    def rotate_audit_key(self) -> Dict:
        """
        Rotate the cryptographic key for the audit chain.

        Returns:
            Dict with rotation status and new key information
        """
        new_key = self.audit_chain.rotate_key()
        self._persist_state()
        return {
            "rotated": True,
            "new_key": new_key[:16] + "..." if new_key else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
