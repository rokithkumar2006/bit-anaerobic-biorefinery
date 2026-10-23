"""Regression tests for request validation in the virtual digester API.

These tests intentionally exercise validation before importing/running PyADM1ODE,
so they can run in a lightweight CI environment without the scientific model installed.
"""
import math

import pytest

from simulation_engine import run_simulation


VALID_PAYLOAD = {
    "feed_rate_kg_day": 600,
    "food_share_pct": 55,
    "garden_share_pct": 15,
    "temperature_c": 37,
    "hrt_days": 25,
    "duration_days": 30,
    "timestep_hours": 6,
}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("feed_rate_kg_day", 0),
        ("feed_rate_kg_day", -1),
        ("feed_rate_kg_day", 100001),
        ("food_share_pct", -1),
        ("food_share_pct", 101),
        ("garden_share_pct", -1),
        ("garden_share_pct", 101),
        ("temperature_c", -1),
        ("temperature_c", 81),
        ("hrt_days", 0),
        ("hrt_days", 366),
        ("duration_days", 0),
        ("duration_days", 91),
        ("timestep_hours", 0),
        ("timestep_hours", 25),
    ],
)
def test_rejects_out_of_range_inputs(field, value):
    payload = {**VALID_PAYLOAD, field: value}
    with pytest.raises(ValueError):
        run_simulation(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("feed_rate_kg_day", math.nan),
        ("feed_rate_kg_day", math.inf),
        ("temperature_c", -math.inf),
        ("food_share_pct", math.nan),
    ],
)
def test_rejects_non_finite_inputs(field, value):
    payload = {**VALID_PAYLOAD, field: value}
    with pytest.raises(ValueError):
        run_simulation(payload)


def test_rejects_food_and_garden_shares_above_total():
    payload = {**VALID_PAYLOAD, "food_share_pct": 70, "garden_share_pct": 40}
    with pytest.raises(ValueError, match="cannot exceed 100%"):
        run_simulation(payload)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("duration_days", 1.5, "whole number of days"),
        ("timestep_hours", 2.5, "whole number of hours"),
    ],
)
def test_rejects_fractional_integer_controls(field, value, message):
    payload = {**VALID_PAYLOAD, field: value}
    with pytest.raises(ValueError, match=message):
        run_simulation(payload)


@pytest.mark.parametrize("payload", [None, [], "not an object", 42])
def test_rejects_non_object_payload(payload):
    with pytest.raises((TypeError, ValueError)):
        run_simulation(payload)
