"""
Unit tests for Cryptographic Audit Chain
"""

import sys
import os
import pytest

# Add the apps directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps'))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from superfleet_memory.anti_entropy_audit import CryptographicAuditChain


class TestCryptographicAuditChain:

    @pytest.fixture
    def chain(self):
        """Create a fresh audit chain for each test."""
        return CryptographicAuditChain()

    def test_basic_logging(self, chain):
        """Test basic entry logging."""
        chain.log("test_action", {"key": "value"})
        assert len(chain.chain) == 1
        assert chain.chain[0]["action"] == "test_action"

    def test_chain_verification(self, chain):
        """Test that a valid chain verifies successfully."""
        chain.log("action1", {"data": 1})
        chain.log("action2", {"data": 2})
        assert chain.verify_chain() is True

    def test_tampering_detection(self, chain):
        """Test that tampering is detected."""
        chain.log("action1", {"data": 1})
        # Tamper with the data
        chain.chain[0]["data"] = {"data": 999}
        assert chain.verify_chain() is False

    def test_signature_verification(self, chain):
        """Test that tampered signatures are detected."""
        chain.log("action1", {"data": 1})
        # Tamper with signature
        chain.chain[0]["signature"] = "a" * 128
        assert chain.verify_chain() is False

    def test_hash_chain_integrity(self, chain):
        """Test that hash chain integrity is verified."""
        chain.log("action1", {"data": 1})
        chain.log("action2", {"data": 2})
        # Tamper with previous hash
        chain.chain[1]["previous_hash"] = "0" * 64
        assert chain.verify_chain() is False

    def test_key_rotation(self, chain):
        """Test key rotation while maintaining chain integrity."""
        chain.log("action1", {"data": 1})

        # Rotate key
        new_key = Ed25519PrivateKey.generate()
        chain.rotate_key(new_key)

        # Chain before rotation should still verify
        assert chain.verify_chain() is True

        # Should have recorded the rotation
        assert len(chain.key_history) == 1

    def test_export_chain(self, chain):
        """Test exporting the full chain."""
        chain.log("action1", {"data": 1})
        export = chain.export_chain()

        assert "entries" in export
        assert "public_key" in export
        assert "is_valid" in export
        assert export["chain_length"] == 1

    def test_get_stats(self, chain):
        """Test getting chain statistics."""
        chain.log("action1", {"data": 1})
        chain.log("action2", {"data": 2})

        stats = chain.get_stats()
        assert stats["chain_length"] == 2
        assert stats["is_valid"] is True

    def test_empty_chain_verification(self):
        """Test that an empty chain is valid."""
        chain = CryptographicAuditChain()
        assert chain.verify_chain() is True

    def test_multiple_entries(self, chain):
        """Test logging multiple entries."""
        for i in range(10):
            chain.log(f"action{i}", {"value": i})

        assert len(chain.chain) == 10
        assert chain.verify_chain() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
