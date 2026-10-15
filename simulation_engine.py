"""PyADM1ODE adapter for the BIT Smart Campus prototype.

The model uses documented PyADM1ODE/ADM1da substrate records as proxies.
It does not claim that these proxies are measured BIT food/garden waste.
"""
from __future__ import annotations

import importlib.metadata
import math
import time
from typing import Any


SUBSTRATE_IDS = (
    "onion_waste",                 # proxy for the food-waste fraction
    "grass_silage",                # proxy for the garden/green-waste fraction
    "maize_silage_milk_ripeness",  # explicit residual-share proxy
)
ASSUMED_DENSITY_KG_M3 = 1000.0
GAS_HEADSPACE_RATIO = 150.0 / 1050.0
MAX_DURATION_DAYS = 90


def model_health() -> dict[str, Any]:
    """Return package readiness without executing a simulation."""
    try:
        version = importlib.metadata.version("pyadm1")
        installed = True
    except importlib.metadata.PackageNotFoundError:
        version = None
        installed = False

    return {
        "status": "ok",
        "engine": "PyADM1ODE/ADM1da" if installed else "model-package-not-installed",
        "engine_version": version,
        "model_integrated": installed,
        "simulation_executed": False,
    }


def _number(payload: dict[str, Any], key: str, minimum: float, maximum: float) -> float:
    try:
        value = float(payload[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"'{key}' must be a number.") from exc
    if not math.isfinite(value) or value < minimum or value > maximum:
        raise ValueError(f"'{key}' must be between {minimum:g} and {maximum:g}.")
    return value


def _finite_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def run_simulation(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate request fields, run PyADM1ODE, and return measured model outputs."""
    started = time.perf_counter()

    feed_rate = _number(payload, "feed_rate_kg_day", 0.1, 100000.0)
    food_pct = _number(payload, "food_share_pct", 0.0, 100.0)
    garden_pct = _number(payload, "garden_share_pct", 0.0, 100.0)
    temperature_c = _number(payload, "temperature_c", 0.0, 80.0)
    hrt_days = _number(payload, "hrt_days", 0.1, 365.0)
    duration_value = _number(payload, "duration_days", 1.0, float(MAX_DURATION_DAYS))
    step_value = _number(payload, "timestep_hours", 1.0, 24.0)

    if not duration_value.is_integer():
        raise ValueError("'duration_days' must be a whole number of days.")
    if not step_value.is_integer():
        raise ValueError("'timestep_hours' must be a whole number of hours.")
    if food_pct + garden_pct > 100.0 + 1e-9:
        raise ValueError("'food_share_pct' + 'garden_share_pct' cannot exceed 100%.")

    duration_days = int(duration_value)
    timestep_hours = int(step_value)
    if duration_days * 24 / timestep_hours > 2160:
        raise ValueError("This deployment supports at most 2160 saved simulation steps per request.")

    # The existing UI's kg/day field is converted to volumetric flow using the
    # clearly disclosed 1000 kg/m³ assumption. This is not a measured density.
    total_flow_m3_day = feed_rate / ASSUMED_DENSITY_KG_M3
    residual_pct = max(0.0, 100.0 - food_pct - garden_pct)
    q_substrates = [
        total_flow_m3_day * food_pct / 100.0,
        total_flow_m3_day * garden_pct / 100.0,
        total_flow_m3_day * residual_pct / 100.0,
    ]

    if sum(q_substrates) <= 0:
        raise ValueError("The total substrate flow must be greater than zero.")

    liquid_volume_m3 = total_flow_m3_day * hrt_days
    gas_volume_m3 = liquid_volume_m3 * GAS_HEADSPACE_RATIO
    temperature_k = temperature_c + 273.15
    dt_days = timestep_hours / 24.0

    try:
        from pyadm1 import BiogasPlant, Feedstock
        from pyadm1.configurator.plant_configurator import PlantConfigurator
    except Exception as exc:
        raise RuntimeError(
            "PyADM1ODE could not be imported. Check the pyadm1 dependency and deployment logs."
        ) from exc

    # These are the substrate IDs used by the published PyADM1ODE examples.
    # The remaining share uses maize silage solely as a proxy; it is not a
    # claim that BIT campus waste contains maize silage.
    try:
        feedstock = Feedstock(
            list(SUBSTRATE_IDS),
            feeding_freq=24,
            total_simtime=max(duration_days + 10, 30),
        )
        plant = BiogasPlant("BIT Smart Campus virtual digester")
        configurator = PlantConfigurator(plant, feedstock)
        configurator.add_digester(
            digester_id="main_digester",
            V_liq=liquid_volume_m3,
            V_gas=gas_volume_m3,
            T_ad=temperature_k,
            Q_substrates=q_substrates,
            k_L_a=200.0,
        )
        plant.initialize()
        results = plant.simulate(
            duration=float(duration_days),
            dt=dt_days,
            save_interval=dt_days,
        )
    except Exception as exc:
        raise RuntimeError(
            "PyADM1ODE model execution failed. The request was not replaced with heuristic or fabricated results."
        ) from exc

    if not results:
        raise RuntimeError("PyADM1ODE returned no simulation samples.")

    # Report averages across the final 20% of saved results and retain the
    # final-state variables requested by the website.
    tail_count = max(1, math.ceil(len(results) * 0.20))
    tail = results[-tail_count:]
    component_tail = []
    for row in tail:
        component = (row.get("components") or {}).get("main_digester")
        if component:
            component_tail.append(component)
    if not component_tail:
        raise RuntimeError("PyADM1ODE returned no main_digester outputs.")

    def mean_key(key: str) -> float | None:
        values = [_finite_or_none(row.get(key)) for row in component_tail]
        valid = [value for value in values if value is not None]
        return sum(valid) / len(valid) if valid else None

    biogas_mean = mean_key("Q_gas")
    methane_mean = mean_key("Q_ch4")
    if biogas_mean is None or methane_mean is None:
        raise RuntimeError("PyADM1ODE did not return Q_gas and Q_ch4 for the main digester.")
    methane_pct = (methane_mean / biogas_mean * 100.0) if biogas_mean > 0 else None

    final_component = ((results[-1].get("components") or {}).get("main_digester")) or {}
    elapsed = time.perf_counter() - started

    def final_value(key: str) -> float | None:
        return _finite_or_none(final_component.get(key))

    return {
        "model_status": "PyADM1ODE/ADM1da run completed with reference substrate proxies; not validated against BIT measurements.",
        "model_engine": "PyADM1ODE/ADM1da",
        "model_version": importlib.metadata.version("pyadm1"),
        "runtime_seconds": round(elapsed, 3),
        "samples_returned": len(results),
        "tail_period_mean": {
            "biogas_m3_day": biogas_mean,
            "methane_m3_day": methane_mean,
            "methane_fraction_pct": methane_pct,
        },
        "final": {
            "pH_model_output": final_value("pH"),
            "vfa_g_l": final_value("VFA"),
            "tac_g_l": final_value("TAC"),
        },
        "assumptions": {
            "feed_rate_kg_day": feed_rate,
            "assumed_density_kg_m3": ASSUMED_DENSITY_KG_M3,
            "estimated_total_flow_m3_day": total_flow_m3_day,
            "temperature_input_c": temperature_c,
            "temperature_model_k": temperature_k,
            "requested_hrt_days": hrt_days,
            "liquid_volume_m3": liquid_volume_m3,
            "gas_headspace_m3": gas_volume_m3,
            "timestep_hours": timestep_hours,
            "food_share_pct_to_onion_waste_proxy": food_pct,
            "garden_share_pct_to_grass_silage_proxy": garden_pct,
            "residual_share_pct_to_maize_silage_proxy": residual_pct,
            "substrate_ids": list(SUBSTRATE_IDS),
            "substrate_flows_m3_day": q_substrates,
            "note": "Published model substrate properties are reference proxies, not measured BIT feedstock characteristics. Do not use this output as experimental validation.",
        },
    }
