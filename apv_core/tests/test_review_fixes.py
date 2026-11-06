"""Regression tests for the whole-branch review findings I-1..I-5."""

import dataclasses
import math

import numpy as np
import pytest
from fixtures import elevated_structure, finance_defaults, onion_rabi, soybean_kharif, synthetic_physics

from apv_core import BusinessModel, CropEconomics, NoticeCode, PhysicsTable, SweepInputs, run_sweep
from apv_core.cashflow import irr, npv
from apv_core.constants import Season
from apv_core.crops import CropParams, EvidenceGrade
from apv_core.finance import lease_per_acre
from apv_core.ranges import Range


def _inputs(**kw):
    base = {
        "physics": synthetic_physics(),
        "structure": elevated_structure(),
        "rotation": (soybean_kharif(), onion_rabi()),
        "finance": finance_defaults(),
        "business_model": BusinessModel.KUSUM_A,
    }
    base.update(kw)
    return SweepInputs(**base)


# I-1: IRR must be found even when late-year flows turn negative.
def test_irr_found_with_negative_tail():
    flows = [-100, 60, 60, -1]
    r = irr(flows)
    assert r.value is not None and 0.12 < r.value < 0.13
    assert abs(npv(r.value, flows)) < 1e-6


def test_sweep_irr_with_fast_om_escalation():
    f = dataclasses.replace(finance_defaults(), om_escalation=0.09)
    r = run_sweep(_inputs(finance=f))
    assert r.metrics["project_irr"][5].central is not None  # GCR 0.25
    assert not any(n.code is NoticeCode.IRR_UNDEFINED for n in r.notices)


# I-2: no lease is paid where there is no plant.
def test_no_lease_at_zero_capacity():
    assert lease_per_acre(0.0, 0.0, 40000.0, finance_defaults()).farmer_income_year1 == 40000.0
    r = run_sweep(_inputs(business_model=BusinessModel.LEASE))
    assert r.metrics["farmer_net_income"][0].central == r.baseline_farm_income


# I-3: NPV is a P0 output (REQ-FIN-01).
def test_npv_in_metrics():
    r = run_sweep(_inputs())
    assert r.metrics["npv"][0].central == 0.0
    assert r.metrics["npv"][6].central > 0


# I-4: GCR-dependent notices list every offending GCR.
def test_kusum_size_notice_lists_all_offending_gcrs():
    r = run_sweep(_inputs(land_acres=10.0))
    n = next(n for n in r.notices if n.code is NoticeCode.KUSUM_SIZE_OUT_OF_RANGE)
    assert n.gcrs == (0.05, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5)


# I-5: NaN / inf never pass validation.
@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_crop_economics_rejects_non_finite(bad):
    with pytest.raises(ValueError):
        CropEconomics(4.0, bad, 1.0)


@pytest.mark.parametrize("field", ["tariff_per_kwh", "target_irr", "om_escalation", "capex_per_kwp"])
def test_finance_rejects_non_finite(field):
    with pytest.raises(ValueError):
        dataclasses.replace(finance_defaults(), **{field: math.inf})
    with pytest.raises(ValueError):
        dataclasses.replace(finance_defaults(), **{field: math.nan})


def test_physics_rejects_nan():
    p = synthetic_physics()
    e = np.array(p.energy_kwh_per_kwp)
    e[3, 3] = np.nan
    with pytest.raises(ValueError):
        PhysicsTable(e, p.light_fraction, p.ref_energy_kwh_per_acre)
    with pytest.raises(ValueError):
        PhysicsTable(p.energy_kwh_per_kwp, p.light_fraction, math.inf)


def test_sweep_inputs_reject_nan():
    with pytest.raises(ValueError):
        _inputs(apv_cost_premium=math.nan)
    with pytest.raises(ValueError):
        _inputs(land_acres=math.nan)


def test_crop_params_reject_nan_slope():
    with pytest.raises(ValueError):
        CropParams("x", "X", frozenset({Season.RABI}), "neutral", Range(0.8, 0.7, 0.6),
                   Range(math.nan, math.nan, math.nan), EvidenceGrade.B)
