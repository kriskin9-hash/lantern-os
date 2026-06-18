"""Test dream-chat integration with Convergence Kernel.

wq-015: Verify dream-chat can use Kernel instance for Remember + Reason stages.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from convergence.kernel import Kernel
from convergence.objects import Memory


class TestDreamChatKernelIntegration:
    """Test dream-chat's use of Convergence Kernel."""

    @pytest.fixture
    def temp_memory_dir(self):
        """Create temporary memory directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def kernel(self, temp_memory_dir):
        """Initialize Kernel with temp memory."""
        memory_path = Path(temp_memory_dir) / "kernel-memory.jsonl"
        return Kernel(memory_path=str(memory_path))

    def test_kernel_initializes(self, kernel):
        """Test Kernel can be initialized."""
        assert kernel is not None
        assert hasattr(kernel, "memory")
        assert hasattr(kernel, "tools")
        assert hasattr(kernel, "convergence_records")

    def test_kernel_observe_stage(self, kernel):
        """Test Kernel Observe stage (capture state)."""
        # Dream-chat stores user messages via observe()
        mem = kernel.observe(
            source="dream-chat",
            data={"role": "user", "text": "What's your purpose?"},
            confidence=0.95,
        )

        assert mem is not None
        assert isinstance(mem, Memory)
        assert mem.source == "dream-chat"
        assert mem.confidence == 0.95

    def test_kernel_query_memory(self, kernel):
        """Test Kernel Remember stage (query memory)."""
        # Add some memories
        kernel.observe("dream-chat", {"text": "lantern is a steady light"}, 0.95)
        kernel.observe("dream-chat", {"text": "convergence means alignment"}, 0.90)

        # Query memory (Remember stage)
        results = kernel.query_memory(pattern="lantern", min_confidence=0.8, limit=10)

        assert len(results) >= 1
        assert any("lantern" in str(r.content).lower() for r in results)

    def test_kernel_convergence_records(self, kernel):
        """Test Kernel stores ConvergenceRecords for reasoning."""
        # Kernel should have a convergence_records list
        assert isinstance(kernel.convergence_records, list)

        # Emit a ConvergenceRecord (Reason stage)
        from convergence.objects import ConvergenceRecord
        record = ConvergenceRecord(
            id="test-record-1",
            hypothesis="User is asking about purpose",
            evidence_ids=[],  # No supporting memories yet
            result="Response about Lantern's purpose",
            confidence=0.85,
            reasoner="dream-chat",
        )
        kernel.convergence_records.append(record)

        assert len(kernel.convergence_records) >= 1
        assert kernel.convergence_records[0].hypothesis == "User is asking about purpose"

    def test_dream_chat_kernel_integration_contract(self, kernel):
        """Contract test: dream-chat can use Kernel for the Observe-Remember-Reason loop.

        Verifies:
        1. Dream-chat can store user messages via observe()
        2. Dream-chat can query memory for context via query_memory()
        3. Dream-chat can emit ConvergenceRecords for reasoning outcomes
        """
        # Stage 1: Observe — store user message
        user_msg = kernel.observe(
            source="dream-chat",
            data={"role": "user", "text": "Tell me about convergence"},
            confidence=0.95,
        )
        assert user_msg is not None
        assert user_msg.id in kernel.memory

        # Stage 2: Remember — query for relevant context
        context = kernel.query_memory(
            pattern="convergence",
            min_confidence=0.5,
            limit=5,
        )
        # Can be empty, that's OK — testing the interface works
        assert isinstance(context, list)

        # Stage 3: Reason — emit ConvergenceRecord with dream-chat reasoning
        from convergence.objects import ConvergenceRecord
        reasoning_record = ConvergenceRecord(
            id="dream-reasoning-1",
            hypothesis="User wants to understand convergence concept",
            evidence_ids=[user_msg.id],  # Reference the observed user message
            result="Provided explanation about convergence",
            confidence=0.90,
            reasoner="dream-chat",
        )
        kernel.convergence_records.append(reasoning_record)

        # Verify record was stored
        assert len(kernel.convergence_records) >= 1
        assert any(r.hypothesis == "User wants to understand convergence concept"
                   for r in kernel.convergence_records)

    def test_kernel_health_check(self, kernel):
        """Test Kernel has health status (for startup verification)."""
        # Initialize kernel to get health status
        health = kernel.health_check()
        assert health is not None
        assert "ok" in health or "components" in health


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
