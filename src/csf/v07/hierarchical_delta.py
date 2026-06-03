"""Hierarchical Delta System — 8 levels of confirmation granularity.

Level 0: Coarsest — confirm massive static regions (3-8 bytes each)
Level 1-2: Medium coarse — confirm medium regions
Level 3-5: Fine — sparse qutrit deltas at specific positions
Level 6-7: Finest — individual dimension changes with amplitude+phase

For symbolic data, most observations are Level 0 confirmations
(very cheap), with only rare Level 5-7 actual deltas.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Tuple

from .qutrit_delta import NUM_DIMENSIONS, QutritDelta, pack_delta_list, unpack_delta_list
from .base3_positions import encode_absolute, encode_delta, Base3Codec


class DeltaType(IntEnum):
    LIGHT_CHANGED = 0x0
    NEW_RELATIONSHIP = 0x1
    RELATIONSHIP_DISSOLVED = 0x2
    CHARACTER_APPEARANCE = 0x3
    CHARACTER_DEPARTURE = 0x4
    CONVERGENCE_EVENT = 0x5
    ANCHOR_ACTIVATION = 0x6
    ANCHOR_DEACTIVATION = 0x7


# Bit layout for 1-byte header
#   bit 7:   0 = confirmation, 1 = delta
#   bits 6-4: level (0-7)
#   bits 3-0: delta type (only when bit 7 = 1)

_TYPE_BIT = 0x80
_LEVEL_SHIFT = 4
_LEVEL_MASK = 0x70
_DTYPE_MASK = 0x0F


def _build_header(is_confirmation: bool, level: int, delta_type: int = 0) -> int:
    if not 0 <= level <= 7:
        raise ValueError("level must be 0-7")
    h = (level & 0x07) << _LEVEL_SHIFT
    if not is_confirmation:
        h |= _TYPE_BIT | (delta_type & _DTYPE_MASK)
    return h


def _parse_header(byte: int) -> Tuple[bool, int, int]:
    is_confirmation = (byte & _TYPE_BIT) == 0
    level = (byte & _LEVEL_MASK) >> _LEVEL_SHIFT
    dtype = byte & _DTYPE_MASK if not is_confirmation else 0
    return is_confirmation, level, dtype


@dataclass
class HierarchicalRecord:
    is_confirmation: bool
    level: int
    delta_type: DeltaType
    position: Tuple[int, ...]
    payload: bytes = b""


class HierarchicalDeltaWriter:
    """Write hierarchical records with delta-coded positions."""

    def __init__(self):
        self._codec = Base3Codec()
        self._buf = bytearray()

    def confirm(self, level: int, position: Tuple[int, ...],
                extent: int = 0xFF) -> None:
        """Write a confirmation (heartbeat) record."""
        header = _build_header(True, level)
        pos_bytes = encode_absolute(position)
        self._buf.append(header)
        self._buf.extend(pos_bytes)
        self._buf.append(extent & 0xFF)

    def delta(self, level: int, dtype: DeltaType,
              position: Tuple[int, ...], deltas: List[QutritDelta]) -> None:
        """Write a full delta record with qutrit changes."""
        header = _build_header(False, level, int(dtype))
        pos_bytes = self._codec.encode(position)
        payload = pack_delta_list(deltas)
        self._buf.append(header)
        self._buf.extend(pos_bytes)
        self._buf.append(len(payload))
        self._buf.extend(payload)

    def to_bytes(self) -> bytes:
        return bytes(self._buf)


class HierarchicalDeltaReader:
    """Read hierarchical records with delta-coded positions."""

    def __init__(self, data: bytes):
        self._data = data
        self._offset = 0
        self._codec = Base3Codec()

    def read(self) -> Optional[HierarchicalRecord]:
        if self._offset >= len(self._data):
            return None

        header = self._data[self._offset]
        self._offset += 1
        is_conf, level, dtype = _parse_header(header)

        position, self._offset = self._codec.decode(self._data, self._offset)

        if is_conf:
            extent = self._data[self._offset]
            self._offset += 1
            return HierarchicalRecord(
                is_confirmation=True, level=level, delta_type=DeltaType(dtype),
                position=position, payload=bytes([extent])
            )
        else:
            payload_len = self._data[self._offset]
            self._offset += 1
            payload = self._data[self._offset:self._offset + payload_len]
            self._offset += payload_len
            return HierarchicalRecord(
                is_confirmation=False, level=level, delta_type=DeltaType(dtype),
                position=position, payload=payload
            )

    def read_all(self) -> List[HierarchicalRecord]:
        records = []
        while True:
            rec = self.read()
            if rec is None:
                break
            records.append(rec)
        return records
