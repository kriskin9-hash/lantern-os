"""Pytest configuration for the CIO-SDE test suite.

Registers data-type markers (issue #522) so every test can declare whether it
exercises synthetic, real, or mixed data paths:

    @pytest.mark.synthetic   model trains on its own outputs (real_fraction π=0)
    @pytest.mark.real        every step re-anchored to external observation (π=1)
    @pytest.mark.mixed       real + synthetic blended (0 < π < 1)

Run a single data path, e.g.:   python -m pytest -m synthetic

The markers themselves are registered in pytest.ini (the canonical location).
"""
