"""Qutrit Delta encoding — amplitude + phase discretization for 3^12 matrices."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import List, Tuple

# A qutrit has 3 basis states |0>, |1>, |2>.
# We discretize amplitude into 8 levels (0-7) and phase into 8 angular sectors.
NUM_DIMENSIONS = 12
TOTAL_POSITIONS = 3 ** NUM_DIMENSIONS  # 531_441


@dataclass(frozen=True, slots=True)
class QutritState:
    """Discretized qutrit state at one dimension."""
    amplitude: int  # 0-7 (0 = none, 7 = full)
    phase: int      # 0-7 (maps to 0, π/4, π/2, ..., 2π)

    def __post_init__(self):
        if not (0 <= self.amplitude <= 7):
            raise ValueError("amplitude must be 0-7")
        if not (0 <= self.phase <= 7):
            raise ValueError("phase must be 0-7")


@dataclass(frozen=True, slots=True)
class QutritDelta:
    """Signed change in one dimension's qutrit state."""
    dim_index: int   # 0-11 (which of the 12 dimensions changed)
    amp_delta: int   # -7 to +7
    phase_delta: int # -7 to +7

    def __post_init__(self):
        if not (0 <= self.dim_index < NUM_DIMENSIONS):
            raise ValueError(f"dim_index must be 0-{NUM_DIMENSIONS - 1}")
        if not (-7 <= self.amp_delta <= 7):
            raise ValueError("amp_delta must be -7 to +7")
        if not (-7 <= self.phase_delta <= 7):
            raise ValueError("phase_delta must be -7 to +7")


# ------------------------------------------------------------------
# Packing: 2 bytes per delta
#   Byte 0: dim_index (4 bits, 0-15) + amp_sign (1 bit) + amp_mag (3 bits, 0-7)
#   Byte 1: phase_sign (1 bit) + phase_mag (3 bits, 0-7) + reserved (4 bits)
# ------------------------------------------------------------------

def _pack_signed(value: int) -> Tuple[int, int]:
    """Return (sign_bit, magnitude) for a signed value in [-7, 7]."""
    if value < 0:
        return 1, -value
    return 0, value


def _unpack_signed(sign: int, mag: int) -> int:
    """Reconstruct signed value from sign bit and magnitude."""
    if sign:
        return -mag
    return mag


def pack_delta(delta: QutritDelta) -> bytes:
    """Pack a single QutritDelta into 2 bytes."""
    amp_sign, amp_mag = _pack_signed(delta.amp_delta)
    phase_sign, phase_mag = _pack_signed(delta.phase_delta)

    byte0 = ((delta.dim_index & 0x0F) << 4) | (amp_sign << 3) | (amp_mag & 0x07)
    byte1 = (phase_sign << 7) | ((phase_mag & 0x07) << 4)

    return bytes([byte0, byte1])


def unpack_delta(data: bytes, offset: int = 0) -> Tuple[QutritDelta, int]:
    """Unpack a QutritDelta from 2 bytes. Returns (delta, new_offset)."""
    b0, b1 = data[offset], data[offset + 1]
    offset += 2

    dim_index = (b0 >> 4) & 0x0F
    amp_sign = (b0 >> 3) & 0x01
    amp_mag = b0 & 0x07
    phase_sign = (b1 >> 7) & 0x01
    phase_mag = (b1 >> 4) & 0x07

    amp_delta = _unpack_signed(amp_sign, amp_mag)
    phase_delta = _unpack_signed(phase_sign, phase_mag)

    return QutritDelta(dim_index, amp_delta, phase_delta), offset


def pack_delta_list(deltas: List[QutritDelta]) -> bytes:
    """Pack a list of deltas: [count:1] + [deltas:2*count]."""
    if len(deltas) > 255:
        raise ValueError("cannot pack more than 255 deltas in one payload")
    buf = bytearray()
    buf.append(len(deltas))
    for d in deltas:
        buf.extend(pack_delta(d))
    return bytes(buf)


def unpack_delta_list(data: bytes, offset: int = 0) -> Tuple[List[QutritDelta], int]:
    """Unpack a list of deltas. Returns (deltas, new_offset)."""
    count = data[offset]
    offset += 1
    deltas = []
    for _ in range(count):
        d, offset = unpack_delta(data, offset)
        deltas.append(d)
    return deltas, offset


# ------------------------------------------------------------------
# Helpers for computing deltas between two full 12-dimensional states
# ------------------------------------------------------------------

def compute_deltas(
    previous: List[QutritState],
    current: List[QutritState],
    amp_threshold: int = 0,
    phase_threshold: int = 0,
) -> List[QutritDelta]:
    """Compare two 12-dimensional qutrit state vectors and return deltas."""
    if len(previous) != NUM_DIMENSIONS or len(current) != NUM_DIMENSIONS:
        raise ValueError(f"both states must have {NUM_DIMENSIONS} dimensions")

    deltas = []
    for i, (p, c) in enumerate(zip(previous, current)):
        amp_d = c.amplitude - p.amplitude
        phase_d = c.phase - p.phase
        # Wrap phase delta to shortest path around the 8-sector ring
        if phase_d > 4:
            phase_d -= 8
        elif phase_d < -4:
            phase_d += 8

        if abs(amp_d) > amp_threshold or abs(phase_d) > phase_threshold:
            deltas.append(QutritDelta(i, amp_d, phase_d))

    return deltas


def apply_deltas(
    baseline: List[QutritState],
    deltas: List[QutritDelta],
) -> List[QutritState]:
    """Apply a list of deltas to a baseline state vector."""
    result = list(baseline)
    for d in deltas:
        old = result[d.dim_index]
        new_amp = max(0, min(7, old.amplitude + d.amp_delta))
        new_phase = (old.phase + d.phase_delta) % 8
        result[d.dim_index] = QutritState(new_amp, new_phase)
    return result
