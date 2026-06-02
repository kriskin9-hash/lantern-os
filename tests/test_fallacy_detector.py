"""
Unit tests for Bayesian Fallacy Detector
"""

import sys
import os
import pytest

# Add the apps directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps'))

from superfleet_memory.bayesian_fallacy_detector import BayesianFallacyDetector


class TestBayesianFallacyDetector:

    @pytest.fixture
    def detector(self):
        """Create a fresh fallacy detector for each test."""
        return BayesianFallacyDetector()

    def test_false_dichotomy_detection(self, detector):
        """Test detection of false dichotomy."""
        statement = "Either you're with us or against us."
        fallacies = detector.detect_fallacies(statement)

        # Should detect false dichotomy
        fallacy_types = [f["fallacy"] for f in fallacies]
        assert "false_dichotomy" in fallacy_types

    def test_appeal_to_emotion_detection(self, detector):
        """Test detection of appeal to emotion."""
        statement = "You have to agree with me because it would be absolutely terrible if you didn't."
        fallacies = detector.detect_fallacies(statement)

        fallacy_types = [f["fallacy"] for f in fallacies]
        assert "appeal_to_emotion" in fallacy_types

    def test_hasty_generalization_detection(self, detector):
        """Test detection of hasty generalization."""
        statement = "All politicians are always corrupt."
        fallacies = detector.detect_fallacies(statement)

        fallacy_types = [f["fallacy"] for f in fallacies]
        assert "hasty_generalization" in fallacy_types

    def test_no_fallacy(self, detector):
        """Test a logically sound statement."""
        statement = "Based on the evidence, the conclusion is that X is true."
        fallacies = detector.detect_fallacies(statement)

        # Should have few or no fallacies
        # The exact number may vary, but it should be reasonable
        assert len(fallacies) <= 3

    def test_fallacy_probability_threshold(self, detector):
        """Test that fallacies above threshold are detected."""
        statement = "Either you're happy or you're sad, and since you're not happy, you must be sad."

        fallacies = detector.detect_fallacies(statement)

        # All detected fallacies should exceed threshold
        for fallacy in fallacies:
            assert fallacy["probability"] >= detector.fallacy_threshold

    def test_fallacy_explanation(self, detector):
        """Test that detected fallacies have explanations."""
        statement = "Either A or B, and not B, so therefore A."
        fallacies = detector.detect_fallacies(statement)

        for fallacy in fallacies:
            assert "explanation" in fallacy
            assert "suggested_reframe" in fallacy
            assert len(fallacy["explanation"]) > 0

    def test_response_hint_generation(self, detector):
        """Test generating response hints."""
        statement = "Everyone always does this, so you will too."
        fallacies = detector.detect_fallacies(statement)

        if fallacies:
            hint = detector.generate_response_hint(fallacies)
            assert len(hint) > 0

    def test_empty_statement(self, detector):
        """Test handling empty statements."""
        fallacies = detector.detect_fallacies("")
        assert isinstance(fallacies, list)

    def test_multiple_fallacies(self, detector):
        """Test detecting multiple fallacies in one statement."""
        statement = "Everyone always says you must either agree with me or you're stupid because of how scary the alternative is."
        fallacies = detector.detect_fallacies(statement)

        # Should detect multiple fallacies
        assert len(fallacies) > 1

    def test_detector_stats(self, detector):
        """Test getting detector statistics."""
        stats = detector.get_stats()

        assert "fallacy_types" in stats
        assert "threshold" in stats
        assert stats["fallacy_types"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
