import dataclasses
import math

import numpy as np
from fixtures import elevated_structure, finance_defaults, onion_rabi, soybean_kharif, synthetic_physics
from hypothesis import given, settings
from hypothesis import strategies as st

from apv_core import BusinessModel, Season, SweepInputs, run_sweep

TARIFF = st.floats(2.0, 6.0)
CAPEX = st.floats(30000.0, 70000.0)
LIMIT = st.floats(0.5, 0.95)


def _sweep(tariff=3.5, capex=35000.0, limit=0.8):
    f = dataclasses.replace(finance_defaults(), tariff_per_kwh=tariff, capex_per_kwp=capex)
    return run_sweep(
        SweepInputs(
            physics=synthetic_physics(),
            structure=elevated_structure(),
            rotation=(soybean_kharif(), onion_rabi()),
            finance=f,
            business_model=BusinessModel.KUSUM_A,
            policy_limit=limit,
        )
    )


def _irr(v):
    return -math.inf if v is None else v


@settings(max_examples=50, deadline=None)
@given(tariff=TARIFF, capex=CAPEX)
def test_higher_tariff_never_lowers_irr(tariff, capex):
    low = _sweep(tariff, capex).metrics["project_irr"][6].central
    high = _sweep(tariff * 1.2, capex).metrics["project_irr"][6].central
    assert _irr(high) >= _irr(low)


@settings(max_examples=50, deadline=None)
@given(limit=LIMIT)
def test_retention_never_rises_with_gcr(limit):
    r = _sweep(limit=limit)
    for season in (Season.KHARIF, Season.RABI):
        central = np.array([rg.central for rg in r.retention[season]])
        assert np.all(np.diff(central[1:]) <= 1e-12)


@settings(max_examples=50, deadline=None)
@given(limit=LIMIT)
def test_allowed_gcr_never_rises_with_stricter_limit(limit):
    loose = _sweep(limit=limit).allowed_gcr.central
    strict = _sweep(limit=min(limit + 0.05, 1.0)).allowed_gcr.central
    assert (-1 if strict is None else strict) <= (-1 if loose is None else loose)


@settings(max_examples=50, deadline=None)
@given(tariff=TARIFF, capex=CAPEX)
def test_ler_finite(tariff, capex):
    r = _sweep(tariff, capex)
    for rng in r.metrics["ler"]:
        for v in (rng.pessimistic, rng.central, rng.optimistic):
            assert v is not None and math.isfinite(v) and v > 0
