"""
Cryptographic Audit Chain for Anti-Entropy Memory System

Ed25519-based tamper-evident logging with key rotation support.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey
)
from cryptography.hazmat.primitives import serialization


class CryptographicAuditChain:
    """Ed25519-based tamper-evident audit chain."""

    def __init__(self, private_key: Optional[Ed25519PrivateKey] = None):
        self.private_key = private_key or Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.chain: List[Dict] = []
        self.last_hash = "0" * 64  # Genesis hash
        self.key_history: List[Dict] = []

    def _create_entry(self, action: str, data: Dict, metadata: Dict = None) -> Dict:
        """Create a new audit chain entry."""
        timestamp = datetime.now().isoformat()

        entry = {
            "timestamp": timestamp,
            "action": action,
            "data": data,
            "metadata": metadata or {},
            "previous_hash": self.last_hash
        }

        # Create hash of the entry (excluding signature)
        entry_json = json.dumps(entry, sort_keys=True).encode()
        entry_hash = hashlib.sha256(entry_json).hexdigest()

        # Sign the hash
        signature = self.private_key.sign(entry_json)

        entry["hash"] = entry_hash
        entry["signature"] = signature.hex()

        return entry

    def log(self, action: str, data: Dict, metadata: Dict = None) -> Dict:
        """Add a new entry to the audit chain."""
        entry = self._create_entry(action, data, metadata)
        self.chain.append(entry)
        self.last_hash = entry["hash"]
        return entry

    def verify_chain(self) -> bool:
        """Verify the integrity of the entire chain."""
        if not self.chain:
            return True

        current_hash = "0" * 64

        for entry in self.chain:
            # Reconstruct entry without signature for verification
            entry_copy = {k: v for k, v in entry.items() if k != "signature"}
            entry_json = json.dumps(entry_copy, sort_keys=True).encode()

            # Verify hash chain
            if entry["previous_hash"] != current_hash:
                return False

            # Verify signature
            try:
                signature = bytes.fromhex(entry["signature"])
                self.public_key.verify(signature, entry_json)
            except Exception:
                return False

            current_hash = entry["hash"]

        return True

    def rotate_key(self, new_private_key: Ed25519PrivateKey):
        """Rotate to a new key pair while maintaining chain continuity."""
        old_public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        self.private_key = new_private_key
        self.public_key = new_private_key.public_key()

        self.key_history.append({
            "timestamp": datetime.now().isoformat(),
            "old_public_key": old_public_pem,
            "new_public_key": self.get_public_key_pem()
        })

    def get_public_key_pem(self) -> str:
        """Export public key for verification by others."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def export_chain(self) -> Dict:
        """Export the full chain for storage or sharing."""
        return {
            "entries": self.chain.copy(),
            "key_history": self.key_history,
            "public_key": self.get_public_key_pem(),
            "chain_length": len(self.chain),
            "is_valid": self.verify_chain(),
            "last_hash": self.last_hash
        }

    def get_stats(self) -> Dict:
        """Get audit chain statistics."""
        return {
            "chain_length": len(self.chain),
            "is_valid": self.verify_chain(),
            "last_entry_timestamp": self.chain[-1]["timestamp"] if self.chain else None,
            "key_rotations": len(self.key_history),
            "total_actions": len(self.chain),
            "action_types": list(set(e["action"] for e in self.chain))
        }
