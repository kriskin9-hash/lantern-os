"""
Tests for the Converged Tesseract prototype.

Builds on csf.v07 QuantumDustField; verifies wavefront navigation,
observer collapse, and time dilation without requiring a live server.
"""

import math
import pytest

from converged_tesseract import (
    ConvergedTesseract,
    TimeDilationEngine,
    WavefrontSlice,
    _coords_to_scalar,
    _scalar_to_coords,
    _temporal_axis_position,
    _ternary_distance,
)


def test_scalar_coords_roundtrip():
    for scalar in [0, 1, 3, 9, 80, 531440]:
        coords = _scalar_to_coords(scalar)
        back = _coords_to_scalar(coords)
        assert back == scalar


def test_ternary_distance_identity():
    assert _ternary_distance(0, 0) == 0
    assert _ternary_distance(1, 1) == 0


def test_ternary_distance_one_step():
    # Position 0 = all zeros. Position 1 = first dim = 1.
    assert _ternary_distance(0, 1) == 1
    # Position 3 = second dim = 1.
    assert _ternary_distance(0, 3) == 1


def test_temporal_axis_is_deterministic():
    t = 12345.0
    p1 = _temporal_axis_position(t)
    p2 = _temporal_axis_position(t)
    assert p1 == p2
    assert 0 <= p1 < 3 ** 12


def test_temporal_axis_spreads_over_time():
    # Use 1-second cycle so each second maps to a distinct tick
    positions = {_temporal_axis_position(float(i), cycle_seconds=1.0) for i in range(100)}
    assert len(positions) > 80  # should be well-distributed


class TestTimeDilationEngine:
    def test_default_ratio(self):
        engine = TimeDilationEngine()
        assert engine.calculate_perceived_ratio() == 1.0

    def test_faster_internal_speed(self):
        engine = TimeDilationEngine(internal_ticks_per_second=10.0)
        assert engine.calculate_perceived_ratio() == 10.0
        # More positions per external second
        p_slow = engine.map_time(0.0)
        p_fast = engine.map_time(60.0)
        assert p_fast != p_slow

    def test_slower_internal_speed(self):
        engine = TimeDilationEngine(internal_ticks_per_second=0.1)
        assert engine.calculate_perceived_ratio() == 0.1


class TestWavefrontSlice:
    def test_empty_slice(self):
        slice_obj = WavefrontSlice(center=0, radius=10, precision=0.5)
        assert slice_obj.slice_size == 0
        assert slice_obj.active_count == 0

    def test_slice_with_states(self):
        from csf.v07.qutrit_delta import QutritState

        positions = {
            0: [QutritState(1, 0) for _ in range(12)],
            1: None,
        }
        slice_obj = WavefrontSlice(
            center=0, radius=10, precision=0.5, positions=positions
        )
        assert slice_obj.slice_size == 2
        assert slice_obj.active_count == 1


class TestConvergedTesseract:
    def test_init_requires_csf(self):
        ct = ConvergedTesseract()
        assert ct.active_wavefront is None
        assert ct.observer_focus == 0.92

    def test_set_focus_clamps(self):
        ct = ConvergedTesseract()
        ct.set_focus(1.5)
        assert ct.observer_focus == 1.0
        ct.set_focus(-0.5)
        assert ct.observer_focus == 0.0

    def test_set_dilation_clamps(self):
        ct = ConvergedTesseract()
        ct.set_dilation(100.0)
        assert ct.dilation_engine.internal_ticks_per_second == 100.0
        ct.set_dilation(0.0001)
        assert ct.dilation_engine.internal_ticks_per_second == 0.01

    def test_get_minimal_slice_returns_wavefront(self):
        ct = ConvergedTesseract()
        slice_obj = ct.get_minimal_slice(center=100, radius=50, precision=0.5)
        assert isinstance(slice_obj, WavefrontSlice)
        assert slice_obj.center == 100
        assert slice_obj.radius == 50
        assert 0 < slice_obj.slice_size <= 51  # bounded by radius + precision

    def test_get_minimal_slice_prefers_active_deltas(self):
        from csf.v07.qutrit_delta import QutritDelta

        ct = ConvergedTesseract()
        # Inject an active delta at position 50
        ct.full_matrix.observe(50, [QutritDelta(0, 2, 1)])
        slice_obj = ct.get_minimal_slice(center=50, radius=10, precision=0.5)
        # Position 50 should be in the slice because it has high info density
        assert 50 in slice_obj.positions

    def test_get_minimal_slice_respects_precision(self):
        ct = ConvergedTesseract()
        full = ct.get_minimal_slice(center=1000, radius=100, precision=1.0)
        sparse = ct.get_minimal_slice(center=1000, radius=100, precision=0.1)
        assert sparse.slice_size < full.slice_size

    def test_update_present_sets_wavefront(self):
        ct = ConvergedTesseract()
        result = ct.update_present(external_time=12345.0)
        assert isinstance(result, WavefrontSlice)
        assert ct.active_wavefront is result
        assert result.slice_size > 0

    def test_sensor_update_with_wavefront(self):
        ct = ConvergedTesseract()
        ct.update_present(external_time=12345.0)
        sensors = ct.sensor_update()
        assert sensors["status"] == "coherent"
        assert sensors["slice_size"] > 0
        assert "dilation_ratio" in sensors

    def test_sensor_update_without_wavefront(self):
        ct = ConvergedTesseract()
        sensors = ct.sensor_update()
        assert sensors["status"] == "no_wavefront"
        assert sensors["slice_size"] == 0.0

    def test_dilation_changes_center_mapping(self):
        ct = ConvergedTesseract()
        ct.set_dilation(10.0)
        p_fast = ct.dilation_engine.map_time(60.0)
        ct.set_dilation(0.1)
        p_slow = ct.dilation_engine.map_time(60.0)
        # Fast dilation = shorter effective cycle = more positions traversed
        assert p_fast != p_slow
