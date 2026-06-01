"""
Bayesian Fallacy Detector

Uses probabilistic detection to identify and gently correct logical fallacies.
"""

from typing import Dict, List, Optional


class BayesianFallacyDetector:
    """
    Bayesian-based fallacy detection system.

    Instead of rigid rules, uses probability to detect fallacies
    based on evidence strength and prior probability.
    """

    def __init__(self):
        # Prior probabilities of common fallacies
        self.fallacy_priors = {
            "false_dichotomy": 0.25,
            "appeal_to_emotion": 0.30,
            "straw_man": 0.15,
            "slippery_slope": 0.20,
            "hasty_generalization": 0.35,
            "circular_reasoning": 0.10,
            "ad_hominem": 0.12,
            "begging_the_question": 0.08
        }

        self.fallacy_threshold = 0.65  # Flag if posterior > 65%

        self.explanations = {
            "false_dichotomy": "This presents only two options when more may exist.",
            "appeal_to_emotion": "The reasoning relies on emotional language rather than evidence.",
            "hasty_generalization": "A broad conclusion is drawn from limited examples.",
            "circular_reasoning": "The conclusion is assumed in the premise.",
            "straw_man": "The argument misrepresents the original position.",
            "slippery_slope": "One event will inevitably lead to another without evidence.",
            "ad_hominem": "The argument attacks the person rather than the idea.",
            "begging_the_question": "The premise assumes the conclusion to be proven."
        }

        self.reframes = {
            "false_dichotomy": "What other possibilities exist between these two extremes?",
            "appeal_to_emotion": "What specific evidence supports this feeling?",
            "hasty_generalization": "What additional examples would strengthen this conclusion?",
            "circular_reasoning": "Let's examine the reasoning more carefully.",
            "straw_man": "What was the original position you're responding to?",
            "slippery_slope": "What evidence connects these events causally?",
            "ad_hominem": "What's your response to the actual argument?",
            "begging_the_question": "What evidence supports this claim independently?"
        }

    def _calculate_likelihood(self, statement: str, fallacy: str) -> float:
        """
        Estimate how likely this statement is to contain the fallacy.
        Uses heuristics based on linguistic patterns.
        """
        statement_lower = statement.lower()

        # Pattern matching for each fallacy type
        patterns = {
            "false_dichotomy": ["either", "or", "both", "neither", "only way"],
            "appeal_to_emotion": ["feel", "scary", "beautiful", "terrible", "horrible", "amazing"],
            "hasty_generalization": ["always", "never", "all", "none", "everyone", "nobody"],
            "circular_reasoning": ["because", "since", "as", "therefore"],
            "straw_man": ["you're saying", "that means", "so you believe"],
            "slippery_slope": ["if", "then", "will inevitably", "will lead to"],
            "ad_hominem": ["you're", "you are", "stupid", "idiot", "foolish"],
            "begging_the_question": ["obviously", "clearly", "as we know", "of course"]
        }

        likelihood = 0.35  # Base likelihood

        if fallacy in patterns:
            if any(pattern in statement_lower for pattern in patterns[fallacy]):
                likelihood += 0.40

        return min(likelihood, 0.95)

    def _bayes_update(self, prior: float, likelihood: float) -> float:
        """
        Simple Bayesian update.
        P(H|E) = P(E|H) * P(H) / P(E)

        Assumes P(E|~H) = 0.5 for simplicity.
        """
        not_h_likelihood = 0.5
        evidence = (likelihood * prior) + (not_h_likelihood * (1 - prior))

        if evidence == 0:
            return prior

        return (likelihood * prior) / evidence

    def detect_fallacies(self, statement: str, context: Optional[Dict] = None) -> List[Dict]:
        """
        Detect fallacies in a statement.

        Returns list of detected fallacies with probability and explanation.
        """
        detected = []

        for fallacy, prior in self.fallacy_priors.items():
            likelihood = self._calculate_likelihood(statement, fallacy)
            posterior = self._bayes_update(prior, likelihood)

            if posterior > self.fallacy_threshold:
                detected.append({
                    "fallacy": fallacy,
                    "probability": round(posterior, 3),
                    "explanation": self.explanations.get(fallacy, "Potential logical issue."),
                    "suggested_reframe": self.reframes.get(fallacy, "Let's think about this differently."),
                    "confidence": "high" if posterior > 0.85 else "medium"
                })

        # Sort by probability (highest first)
        detected.sort(key=lambda x: x["probability"], reverse=True)

        return detected

    def generate_response_hint(self, fallacies: List[Dict]) -> str:
        """Generate a conversational hint based on detected fallacies."""
        if not fallacies:
            return ""

        if len(fallacies) == 1:
            f = fallacies[0]
            hint = f"I noticed something: {f['explanation']} {f['suggested_reframe']}"
        else:
            hint = "I noticed a couple of interesting patterns in how you framed that:\n"
            for f in fallacies[:2]:
                hint += f"• {f['suggested_reframe']}\n"

        return hint

    def get_stats(self) -> Dict:
        """Get detector statistics."""
        return {
            "fallacy_types": len(self.fallacy_priors),
            "threshold": self.fallacy_threshold,
            "version": "1.0"
        }
