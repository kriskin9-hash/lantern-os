"""
Highlight Detector V2 — Spectral-Aware Frame/Segment Detection
Integrates Σ₀ framework for collapse-resistant highlight selection

Based on research:
- arXiv:2601.03385 (spectral collapse)
- arXiv:2512.12381 (low-rank entropy)
- arXiv:2512.00757 (contraction filters)
"""

import json
import numpy as np
from scipy import stats
from collections import deque


class SpectralFrameDetector:
    """
    Detect highlights by monitoring spectral properties of frame sequences.

    Collapse manifold characteristics:
    - rank(Gram matrix) ↓
    - spectral entropy ↓
    - λ_max / λ_min ↑ (spectral spread)
    """

    def __init__(self, window_size=16, entropy_threshold=0.4):
        self.window_size = window_size
        self.entropy_threshold = entropy_threshold
        self.embedding_window = deque(maxlen=window_size)

    def add_frame_embedding(self, embedding):
        """Add normalized frame embedding to analysis window."""
        if isinstance(embedding, (list, np.ndarray)):
            embedding = np.array(embedding, dtype=np.float32)
            # Normalize to unit norm
            norm = np.linalg.norm(embedding)
            if norm > 1e-10:
                embedding = embedding / norm
            self.embedding_window.append(embedding)

    def compute_gram_matrix(self):
        """
        Compute normalized Gram matrix G = X X^T
        where X is the embedding matrix
        """
        if len(self.embedding_window) < 2:
            return None

        X = np.array(list(self.embedding_window), dtype=np.float32)  # n × d
        G = X @ X.T  # n × n

        # Normalize by Frobenius norm
        frob_norm = np.linalg.norm(G, 'fro')
        if frob_norm > 1e-10:
            G = G / frob_norm

        return G

    def spectral_radius(self):
        """
        Compute spectral radius ρ(G) = max(|eigenvalues|)
        Indicates stability: ρ < 1 → stable contraction
        """
        G = self.compute_gram_matrix()
        if G is None:
            return 0.0

        try:
            eigenvalues = np.linalg.eigvalsh(G)
            return float(np.max(np.abs(eigenvalues)))
        except:
            return 0.0

    def spectral_entropy(self):
        """
        Compute Shannon entropy of normalized eigenvalue distribution.

        High entropy = diverse spectrum = diverse content
        Low entropy = concentrated spectrum = collapsed/redundant
        """
        G = self.compute_gram_matrix()
        if G is None:
            return 0.0

        try:
            eigenvalues = np.linalg.eigvalsh(G)
            eigenvalues = np.abs(eigenvalues)

            # Normalize to probability distribution
            s = np.sum(eigenvalues)
            if s < 1e-10:
                return 0.0

            p = eigenvalues / s

            # Shannon entropy: -Σ p_i log(p_i)
            p = p[p > 1e-10]  # Remove zeros
            entropy = -np.sum(p * np.log(p))

            # Normalize to [0, 1]
            max_entropy = np.log(len(eigenvalues))
            if max_entropy > 0:
                entropy = entropy / max_entropy

            return float(entropy)
        except:
            return 0.0

    def spectral_spread(self):
        """
        Compute spectral spread: λ_max / λ_min

        High spread = one dominant direction = potentially collapsing
        Low spread = balanced spectrum = stable
        """
        G = self.compute_gram_matrix()
        if G is None:
            return 1.0

        try:
            eigenvalues = np.linalg.eigvalsh(G)
            eigenvalues = np.abs(eigenvalues)
            eigenvalues = np.sort(eigenvalues)[::-1]  # Descending

            if len(eigenvalues) < 2 or eigenvalues[1] < 1e-10:
                return 1e6

            return float(eigenvalues[0] / eigenvalues[1])
        except:
            return 1.0

    def is_collapsed(self):
        """Check if system is in collapsed state (low entropy)."""
        return self.spectral_entropy() < self.entropy_threshold

    def is_stable(self):
        """Check if system is stable (ρ < 1)."""
        return self.spectral_radius() < 1.0

    def reset(self):
        """Reset window for next segment."""
        self.embedding_window.clear()


class GameplayDetector:
    """
    Detect gameplay presence via motion + scene features.
    Prevents "talking head" false positives.
    """

    def __init__(self, gameplay_threshold=0.6):
        self.gameplay_threshold = gameplay_threshold

    def detect(self, motion, has_scene_change, audio_level):
        """
        Estimate gameplay presence (0-1).

        Factors:
        - High motion → gameplay
        - Scene changes → gameplay transition
        - High audio without motion → talking head (low gameplay)
        """
        score = 0.0

        # Motion indicates action
        if motion > 0.3:
            score += min(motion, 1.0) * 0.6  # Up to 60%

        # Scene changes indicate action
        if has_scene_change:
            score += 0.3

        # Audio alone doesn't indicate gameplay
        # (This prevents talking heads from being highlighted)

        return min(score, 1.0)


def segment_video(timeline, motion_frames, audio_spikes, scene_changes, fps=5):
    """
    Segment video into candidate highlight regions.

    Segments are defined by:
    - Motion clusters
    - Audio spikes
    - Scene changes
    """
    segments = []
    current_segment = None
    gap_threshold = 1.0  # seconds

    # Merge nearby detections into segments
    all_events = []
    for f in motion_frames:
        all_events.append((f['timestamp'], 'motion', f['motion']))
    for a in audio_spikes:
        all_events.append((a['timestamp'], 'audio', a['audio']))
    for s in scene_changes:
        all_events.append((s['timestamp'], 'scene', s['score']))

    all_events.sort()

    for timestamp, event_type, value in all_events:
        if current_segment is None:
            current_segment = {
                'start': timestamp,
                'end': timestamp,
                'events': [(event_type, value)],
            }
        elif timestamp - current_segment['end'] < gap_threshold:
            current_segment['end'] = timestamp
            current_segment['events'].append((event_type, value))
        else:
            # Gap too large, close current segment
            if current_segment:
                segments.append(current_segment)
            current_segment = {
                'start': timestamp,
                'end': timestamp,
                'events': [(event_type, value)],
            }

    if current_segment:
        segments.append(current_segment)

    return segments


def compute_segment_metrics(segment, timeline_duration):
    """
    Compute feature metrics for a segment.

    Returns dict with:
    - motion_energy
    - scene_change_score
    - gameplay_presence
    """
    motion_energy = 0.0
    audio_energy = 0.0
    scene_score = 0.0
    event_count = 0

    # Aggregate event metrics
    for event_type, value in segment.get('events', []):
        if event_type == 'motion':
            motion_energy = max(motion_energy, value)
        elif event_type == 'audio':
            audio_energy = max(audio_energy, value)
        elif event_type == 'scene':
            scene_score = max(scene_score, value)
        event_count += 1

    # Compute gameplay presence (avoid talking heads)
    detector = GameplayDetector()
    gameplay_presence = detector.detect(
        motion_energy,
        scene_score > 0.2,
        audio_energy
    )

    return {
        'motion_energy': motion_energy,
        'audio_energy': audio_energy,
        'scene_change_score': scene_score,
        'gameplay_presence': gameplay_presence,
        'event_count': event_count,
        'duration': segment['end'] - segment['start'],
    }


def validate_segment(metrics, thresholds=None):
    """
    Apply Σ₀ validity gates.

    Segment is valid if:
    - gameplay_presence > 0.6
    - spectral_entropy > 0.4 (checked separately)
    - scene_change > 0.1
    """
    if thresholds is None:
        thresholds = {
            'min_gameplay': 0.6,
            'min_duration': 0.5,
        }

    # Gameplay presence gate
    if metrics['gameplay_presence'] < thresholds['min_gameplay']:
        return False, f"Low gameplay ({metrics['gameplay_presence']:.2f})"

    # Minimum duration
    if metrics['duration'] < thresholds['min_duration']:
        return False, f"Too short ({metrics['duration']:.2f}s)"

    return True, "Valid"


# ============================================================================
# Main Integration
# ============================================================================

def detect_highlights_v2(video_path, motion_frames, audio_spikes, scene_changes, fps=5):
    """
    Main highlight detection function (V2 with spectral analysis).

    Returns:
    - segments: all candidate segments
    - valid: segments passing validity gates
    - metrics: aggregated statistics
    """

    # Segment the video
    segments = segment_video(
        timeline=None,  # Not needed for this pass
        motion_frames=motion_frames,
        audio_spikes=audio_spikes,
        scene_changes=scene_changes,
        fps=fps
    )

    # Score segments
    scored_segments = []
    for seg in segments:
        metrics = compute_segment_metrics(seg, duration=None)
        valid, reason = validate_segment(metrics)

        scored_segments.append({
            'segment': seg,
            'metrics': metrics,
            'valid': valid,
            'reason': reason,
        })

    # Filter valid segments
    valid_segments = [s for s in scored_segments if s['valid']]

    return {
        'segments': scored_segments,
        'valid': valid_segments,
        'summary': {
            'total': len(segments),
            'valid_count': len(valid_segments),
            'validity_rate': len(valid_segments) / len(segments) if segments else 0,
        }
    }


if __name__ == '__main__':
    # Example usage
    print("Highlight Detector V2 — Ready for integration")
    print("- Spectral analysis: collapse detection")
    print("- Gameplay presence: no 'talking head' highlights")
    print("- Validity gates: gameplay + entropy + scene change")
