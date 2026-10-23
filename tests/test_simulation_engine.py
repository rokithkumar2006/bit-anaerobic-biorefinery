import math
import sys
import types
import unittest
from unittest.mock import patch

import simulation_engine

BASE_PAYLOAD = {
    "feed_rate_kg_day": 600, "food_share_pct": 55, "garden_share_pct": 15,
    "temperature_c": 37, "hrt_days": 25, "duration_days": 1, "timestep_hours": 24,
}

class SimulationInputValidationTests(unittest.TestCase):
    def test_rejects_missing_required_value(self):
        payload = dict(BASE_PAYLOAD); del payload["temperature_c"]
        with self.assertRaisesRegex(ValueError, "temperature_c"):
            simulation_engine.run_simulation(payload)

    def test_rejects_non_finite_value(self):
        with self.assertRaisesRegex(ValueError, "temperature_c"):
            simulation_engine.run_simulation(dict(BASE_PAYLOAD, temperature_c=float("nan")))

    def test_rejects_out_of_range_temperature(self):
        with self.assertRaisesRegex(ValueError, "temperature_c"):
            simulation_engine.run_simulation(dict(BASE_PAYLOAD, temperature_c=81))

    def test_rejects_feedstock_shares_over_100_percent(self):
        with self.assertRaisesRegex(ValueError, "cannot exceed 100"):
            simulation_engine.run_simulation(dict(BASE_PAYLOAD, food_share_pct=70, garden_share_pct=40))

    def test_rejects_fractional_duration(self):
        with self.assertRaisesRegex(ValueError, "whole number"):
            simulation_engine.run_simulation(dict(BASE_PAYLOAD, duration_days=1.5))

    def test_rejects_fractional_timestep(self):
        with self.assertRaisesRegex(ValueError, "whole number"):
            simulation_engine.run_simulation(dict(BASE_PAYLOAD, timestep_hours=1.5))

class SimulationOutputTests(unittest.TestCase):
    def test_successful_run_returns_finite_outputs_and_proxy_disclosure(self):
        class FakeFeedstock:
            def __init__(self, *args, **kwargs): pass

        class FakePlant:
            def __init__(self, *args, **kwargs): pass
            def initialize(self): pass
            def simulate(self, **kwargs):
                return [
                    {"components": {"main_digester": {"Q_gas": 2.0, "Q_ch4": 1.1, "pH": 7.1, "VFA": 0.2, "TAC": 4.0}}},
                    {"components": {"main_digester": {"Q_gas": 4.0, "Q_ch4": 2.2, "pH": 7.2, "VFA": 0.3, "TAC": 4.2}}},
                ]

        class FakeConfigurator:
            def __init__(self, plant, feedstock): pass
            def add_digester(self, **kwargs): pass

        pyadm1 = types.ModuleType("pyadm1")
        pyadm1.BiogasPlant = FakePlant
        pyadm1.Feedstock = FakeFeedstock
        configurator_package = types.ModuleType("pyadm1.configurator")
        configurator_module = types.ModuleType("pyadm1.configurator.plant_configurator")
        configurator_module.PlantConfigurator = FakeConfigurator
        modules = {
            "pyadm1": pyadm1,
            "pyadm1.configurator": configurator_package,
            "pyadm1.configurator.plant_configurator": configurator_module,
        }
        with patch.dict(sys.modules, modules), patch("simulation_engine.importlib.metadata.version", return_value="test-version"):
            result = simulation_engine.run_simulation(BASE_PAYLOAD)

        self.assertEqual(result["model_engine"], "PyADM1ODE/ADM1da")
        self.assertEqual(result["model_version"], "test-version")
        self.assertTrue(math.isfinite(result["tail_period_mean"]["biogas_m3_day"]))
        self.assertTrue(math.isfinite(result["tail_period_mean"]["methane_m3_day"]))
        self.assertAlmostEqual(result["tail_period_mean"]["biogas_m3_day"], 3.0)
        self.assertAlmostEqual(result["tail_period_mean"]["methane_m3_day"], 1.65)
        self.assertIn("not validated", result["model_status"])
        self.assertIn("reference proxies", result["assumptions"]["note"])

if __name__ == "__main__":
    unittest.main()
