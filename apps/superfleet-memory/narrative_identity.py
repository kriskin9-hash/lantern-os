"""
Narrative Identity Layer

Maintains coherent long-term "who we are" story that survives paradigm shifts.
"""

from typing import Dict, List
from datetime import datetime


class NarrativeIdentity:
    """
    Maintains a coherent long-term identity story.

    This layer prevents identity drift across paradigm shifts,
    agent turnover, and extended time periods.
    """

    def __init__(self):
        self.core_story: List[str] = []
        self.paradigm_history: List[Dict] = []
        self.current_paradigm: str = "emergence"
        self.identity_anchors: Dict[str, str] = {}

    def add_story_element(self, element: str, timestamp: str = None) -> Dict:
        """Add a narrative element to the identity story."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        entry = {
            "element": element,
            "timestamp": timestamp,
            "paradigm": self.current_paradigm
        }

        self.core_story.append(entry)
        return entry

    def set_paradigm(self, new_paradigm: str, reason: str = "") -> Dict:
        """Shift to a new paradigm while recording the transition."""
        transition = {
            "from": self.current_paradigm,
            "to": new_paradigm,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "story_so_far": len(self.core_story)
        }

        self.paradigm_history.append(transition)
        self.current_paradigm = new_paradigm

        return transition

    def set_identity_anchor(self, key: str, value: str) -> Dict:
        """
        Set a stable identity anchor that persists across paradigm shifts.

        Examples:
        - "core_value": "Seeking truth with compassion"
        - "mission": "Improve human flourishing"
        - "ethic": "Never deceive"
        """
        self.identity_anchors[key] = value
        return {
            "anchor": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }

    def get_identity_summary(self) -> str:
        """Get a summary of the identity story so far."""
        summary = f"Paradigm: {self.current_paradigm}\n"
        summary += f"Story elements: {len(self.core_story)}\n"
        summary += f"Paradigm shifts: {len(self.paradigm_history)}\n\n"

        if self.identity_anchors:
            summary += "Core Identity Anchors:\n"
            for key, value in self.identity_anchors.items():
                summary += f"  • {key}: {value}\n"

        summary += "\nRecent Story:\n"
        for element in self.core_story[-5:]:
            summary += f"  • {element['element']}\n"

        return summary

    def has_survived_paradigm_shift(self, paradigm: str) -> bool:
        """Check if identity survived a particular paradigm shift."""
        for shift in self.paradigm_history:
            if shift["to"] == paradigm:
                return True
        return False

    def export_identity(self) -> Dict:
        """Export the full identity story."""
        return {
            "current_paradigm": self.current_paradigm,
            "core_story": self.core_story,
            "paradigm_history": self.paradigm_history,
            "identity_anchors": self.identity_anchors,
            "coherence": len(self.identity_anchors) > 0  # Identity is coherent if it has anchors
        }
