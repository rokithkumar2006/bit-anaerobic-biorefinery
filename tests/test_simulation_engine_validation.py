"""Fast, dependency-light validation tests for the shared simulation adapter.

These tests exercise input validation only; they do not run PyADM1ODE or
claim scientific validation of campus-specific predictions.
"""
import math
import unittest

from simulation_engine import run_simulation


BASE = {
    "feed_rate_kg_day": 600,
    "food_share_pct": 55,
    "garden_share_pct": 15,
    "temperature_c": 37,
    "hrt_days": 25,
    "duration_days": 30,
    "timestep_hours": 6,
}


class SimulationInputValidationTests(unittest.TestCase):
    def assert_invalid(self, changes, message_fragment=None):
        payload = {**BASE, **changes}
        with self.assertRaises(ValueError) as caught:
            run_simulation(payload)
        if message_fragment:
            self.assertIn(message_fragment, str(caught.exception))

    def test_rejects_non_finite_numeric_values(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                self.assert_invalid({"feed_rate_kg_day": value}, "feed_rate_kg_day")

    def test_rejects_food_and_garden_shares_over_100_percent(self):
        self.assert_invalid(
            {"food_share_pct": 70, "garden_share_pct": 40},
            "cannot exceed 100%",
        )

    def test_rejects_fractional_duration_and_timestep(self):
        self.assert_invalid({"duration_days": 2.5}, "whole number")
        self.assert_invalid({"timestep_hours": 2.5}, "whole number")

    def test_rejects_out_of_range_inputs(self):
        cases = [
            ({"feed_rate_kg_day": 0}, "feed_rate_kg_day"),
            ({"feed_rate_kg_day": 100001}, "feed_rate_kg_day"),
            ({"food_share_pct": -1}, "food_share_pct"),
            ({"garden_share_pct": 101}, "garden_share_pct"),
            ({"temperature_c": 81}, "temperature_c"),
            ({"hrt_days": 0}, "hrt_days"),
            ({"duration_days": 91}, "duration_days"),
            ({"timestep_hours": 25}, "timestep_hours"),
        ]
        for changes, field in cases:
            with self.subTest(changes=changes):
                self.assert_invalid(changes, field)


if __name__ == "__main__":
    unittest.main()
