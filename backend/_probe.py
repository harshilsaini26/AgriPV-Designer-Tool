"""Temporary deployment probe (plan Task 1): one real sweep with a hard-coded demo scenario.

Removed when the real sweep endpoint exists (plan Task 6).
"""

import time

import numpy as np

from apv_core import (
    BusinessModel,
    CropEconomics,
    CropParams,
    EvidenceGrade,
    FinanceInputs,
    Range,
    Season,
    SeasonCrop,
    Structure,
    SweepInputs,
    run_sweep,
)
from apv_physics import BIFACIAL, Kind, Layout, load_weather, simulate
from backend._paths import REPO_ROOT  # noqa: F401  (puts apv_core and apv_physics on the path)

WHEAT = CropParams("wheat", "Wheat", frozenset({Season.RABI}), "neutral", Range(0.93, 0.89, 0.76),
                   Range(1.36, 1.18, 1.10), EvidenceGrade.A)  # fmt: skip
BAJRA = CropParams("bajra", "Bajra", frozenset({Season.KHARIF}), "sensitive", Range(1.0, 1.0, 0.97),
                   Range(1.5, 1.32, 1.16), EvidenceGrade.C)  # fmt: skip
ROTATION = (
    SeasonCrop(Season.KHARIF, BAJRA, CropEconomics(5.0, 2200.0, 9000.0)),
    SeasonCrop(Season.RABI, WHEAT, CropEconomics(17.18, 2151.0, 15216.0)),
)
FINANCE = FinanceInputs(
    capex_per_kwp=39120.0, om_per_kwp_year=704.0, om_escalation=0.0525, tariff_per_kwh=3.04,
    degradation=0.005, availability=0.99, debt_share=0.70, interest_rate=0.10, loan_years=15,
    discount_rate=0.09, crop_inflation=0.05, lease_per_acre_year=40000.0, lease_escalation=0.05,
    target_irr=0.12,
)  # fmt: skip


def run_probe(pack_path) -> dict:
    t0 = time.perf_counter()
    weather = load_weather(pack_path)
    tilt = float(np.clip(weather.optimum_tilt_deg, 10.0, 25.0))
    layout = Layout(Kind.FIXED, BIFACIAL, height_m=3.0, collector_width_m=4.56, tilt_deg=tilt)
    physics = simulate(weather, layout)
    structure = Structure("elevated_fixed_3m", a_farm=0.92, module_efficiency=BIFACIAL.efficiency)
    result = run_sweep(SweepInputs(physics.table, structure, ROTATION, FINANCE, BusinessModel.KUSUM_A))
    return {
        "engine_ms": round((time.perf_counter() - t0) * 1000, 1),
        "ler_central": [r.central for r in result.metrics["ler"]],
        "allowed_gcr_central": result.allowed_gcr.central,
    }
